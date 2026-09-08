from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...clock import as_of
from ...db import get_db
from ...firewall import forbid_commander
from ...ids import nid
from ...interventions.rebalance import greedy_rebalance
from ...interventions.triage import ranked_queue
from ...models import (
    InterventionAction,
    InterventionOutcome,
    ResponseCase,
    RosterSwapProposal,
    TelemanasReferral,
    User,
)
from ...security import require_roles

router = APIRouter(tags=["interventions"])


class ActionIn(BaseModel):
    catalogue_id: str


class OutcomeIn(BaseModel):
    outcome: str
    action_id: str | None = None


class TelemanasIn(BaseModel):
    mode: str = "facilitated_call"
    outcome_status: str = "referred"


class RebalanceIn(BaseModel):
    unit_id: str
    mode: str = "workload"
    horizon_days: int = 14


@router.get("/interventions/queue")
def queue(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="interventions")
    rows = ranked_queue(db)
    write_audit(db, actor=user, action="interventions.queue", resource_type="response_case")
    out = []
    for case, tri in rows:
        if user.role == "counsellor" and tri.assigned_counsellor_id not in {None, user.id}:
            continue
        if user.role == "welfare_officer" and user.assigned_units and case.unit_id not in (user.assigned_units or []):
            continue
        out.append(
            {
                "case_id": case.id,
                "pseudonym_id": case.pseudonym_id,
                "tier": case.tier,
                "status": case.status,
                "group_case": case.group_case,
                "priority": tri.priority,
                "urgency": tri.urgency,
                "intervenability": tri.intervenability,
                "deferred_until": tri.deferred_until.isoformat() if tri.deferred_until else None,
                "cap_reason": tri.cap_reason,
                "sla_hours": case.sla_hours,
            }
        )
    return {"queue": out}


@router.post("/interventions/{case_id}/actions")
def add_action(
    case_id: str,
    body: ActionIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="interventions", resource_id=case_id)
    case = db.get(ResponseCase, case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    action = InterventionAction(
        id=nid("act"),
        case_id=case_id,
        catalogue_id=body.catalogue_id,
        actor_role=user.role,
        initiated_at=now,
        due_at=None,
        status="open",
    )
    db.add(action)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="interventions.action",
        resource_type="intervention_action",
        resource_id=action.id,
        subject_pseudonym_id=case.pseudonym_id,
        purpose="welfare_intervention",
        reason=body.catalogue_id,
    )
    return {"action_id": action.id, "catalogue_id": body.catalogue_id}


@router.post("/interventions/{case_id}/outcome")
def record_outcome(
    case_id: str,
    body: OutcomeIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="interventions", resource_id=case_id)
    allowed = {"improved", "unchanged", "worsened", "declined", "no_contact"}
    if body.outcome not in allowed:
        raise HTTPException(400, "invalid outcome enum")
    case = db.get(ResponseCase, case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = InterventionOutcome(
        id=nid("oc"),
        case_id=case_id,
        action_id=body.action_id,
        outcome=body.outcome,
        recorded_by_role=user.role,
        recorded_at=now,
        label_exported=True,
    )
    db.add(row)
    if body.outcome in {"improved", "declined", "no_contact"}:
        case.status = "closed"
        case.closed_at = now
    db.flush()
    write_audit(
        db,
        actor=user,
        action="interventions.outcome",
        resource_type="intervention_outcome",
        resource_id=row.id,
        subject_pseudonym_id=case.pseudonym_id,
        purpose="welfare_intervention",
        reason=body.outcome,
    )
    return {
        "outcome_id": row.id,
        "label": {
            "pseudonym_id": case.pseudonym_id,
            "outcome": body.outcome,
            "tier_at_open": case.tier,
            "exported": True,
        },
    }


@router.post("/interventions/{case_id}/telemanas")
def telemanas(
    case_id: str,
    body: TelemanasIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor")),
):
    forbid_commander(user, db=db, resource_type="telemanas", resource_id=case_id)
    case = db.get(ResponseCase, case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = TelemanasReferral(
        id=nid("tm"),
        case_id=case_id,
        referred_at=now,
        mode=body.mode,
        outcome_status=body.outcome_status,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="telemanas.referral",
        resource_type="telemanas_referral",
        resource_id=row.id,
        subject_pseudonym_id=case.pseudonym_id,
        purpose="telemanas_handoff",
        reason=body.mode,
    )
    return {"referral_id": row.id, "outcome_status": row.outcome_status, "clinical_content": None}


@router.post("/roster/rebalance")
def rebalance(
    body: RebalanceIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("welfare_officer", "admin")),
):
    if body.mode not in {"workload", "welfare_weighted"}:
        raise HTTPException(400, "mode must be workload or welfare_weighted")
    result = greedy_rebalance(
        db, unit_id=body.unit_id, mode=body.mode, as_of=as_of(), horizon_days=body.horizon_days
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    proposal = RosterSwapProposal(
        id=nid("rb"),
        unit_id=body.unit_id,
        mode=body.mode,
        input_roster_version=as_of().isoformat(),
        proposed_swaps=result["swaps"],
        max_load_before=result["max_load_before"],
        max_load_after=result["max_load_after"],
        infeasible_shifts=result["infeasible_shifts"],
        status="proposed",
        created_at=now,
    )
    db.add(proposal)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="roster.rebalance",
        resource_type="roster_swap_proposal",
        resource_id=proposal.id,
        purpose="workload_rebalance",
        payload={"mode": body.mode, "unit_id": body.unit_id},
    )
    public = {
        "proposal_id": proposal.id,
        "swaps": result["swaps"],
        "max_load_before": result["max_load_before"],
        "max_load_after": result["max_load_after"],
        "infeasible_shifts": result["infeasible_shifts"],
        "mode": body.mode,
    }
    return public


@router.get("/roster/rebalance/{proposal_id}")
def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("welfare_officer", "commander", "admin", "counsellor")),
):
    row = db.get(RosterSwapProposal, proposal_id)
    if row is None:
        raise HTTPException(404, "proposal not found")
    if user.role == "commander" and row.mode != "workload":
        write_audit(
            db,
            actor=user,
            action="firewall.deny",
            resource_type="roster_swap_proposal",
            resource_id=proposal_id,
            denied=True,
            reason="welfare_weighted hidden from commander",
        )
        raise HTTPException(403, "welfare_weighted proposals are not visible to command")
    return {
        "proposal_id": row.id,
        "unit_id": row.unit_id,
        "mode": row.mode if user.role != "commander" else "workload",
        "swaps": row.proposed_swaps,
        "max_load_before": row.max_load_before,
        "max_load_after": row.max_load_after,
        "status": row.status,
    }


@router.post("/roster/rebalance/{proposal_id}/approve")
def approve_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("welfare_officer", "commander")),
):
    row = db.get(RosterSwapProposal, proposal_id)
    if row is None:
        raise HTTPException(404, "proposal not found")
    if user.role == "commander" and row.mode != "workload":
        raise HTTPException(403, "commander may only approve workload-mode proposals")
    row.status = "approved"
    row.approved_by_role = user.role
    write_audit(
        db,
        actor=user,
        action="roster.approve",
        resource_type="roster_swap_proposal",
        resource_id=proposal_id,
        purpose="roster_authority",
    )
    return {"proposal_id": row.id, "status": row.status}
