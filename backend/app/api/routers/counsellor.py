"""F06 — counsellor console read/write surface.

The only place an individual score exists, and only as a consent-gated,
pseudonymised clinical workbench. Every route here is denied to a commander
token twice: once by the ADR-0003 middleware (the ``/interventions`` and
``/risk`` prefixes) and once by ``require_roles`` in the handler.

Curiosity browsing is structurally impossible: there is no "list personnel"
route. A case exists only because the engine raised one.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...audit import write_audit, write_deny
from ...authz import assert_subject_scope
from ...db import get_db
from ...firewall import forbid_commander
from ...ids import nid
from ...interventions.ladder import LADDER
from ...models import (
    BreakGlassEvent,
    InterventionAction,
    InterventionOutcome,
    MaskingFlag,
    ResponseCase,
    RiskFactor,
    RiskScore,
    SessionNote,
    TelemanasReferral,
    TriageEntry,
    UnmaskRequest,
    User,
)
from ...risk.explainer import top_factors
from ...security import require_roles

router = APIRouter(tags=["counsellor-console"])

CASE_ROLES = ("counsellor", "welfare_officer")
MODALITIES = ("in_person", "tele", "telemanas")
OUTCOME_CODES = ("improved", "unchanged", "worsened", "declined", "no_contact")

#: F06 — closed enum. Free-form unmask reasons are rejected at the API.
UNMASK_REASON_CODES = {
    "red_outreach_24h": "Red-tier outreach inside the SLA window",
    "critical_contact": "Critical-tier immediate contact",
    "welfare_scheme_eligibility": "Family-welfare scheme check for the parivaar",
    "subject_request": "The jawan asked for contact through the app",
}


class NoteIn(BaseModel):
    session_at: str | None = None
    modality: str
    themes: list[str] = Field(default_factory=list)
    risk_reestimate: int | None = Field(default=None, ge=0, le=100)
    free_text: str | None = None


def _case_or_404(db: Session, case_id: str) -> ResponseCase:
    case = db.get(ResponseCase, case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    return case


def _assert_assigned(db: Session, user: User, case: ResponseCase) -> None:
    """The server refuses any case the token is not assigned to (F06).

    Delegates to the shared guard so /risk, /signals and the item routes cannot
    drift apart. Reading an unassigned case is triage; acting on one is not
    (see authz.assert_case_scope).
    """
    if user.role == "counsellor":
        tri = db.query(TriageEntry).filter(TriageEntry.case_id == case.id).one_or_none()
        assigned = tri.assigned_counsellor_id if tri else None
        if assigned not in (None, user.id):
            write_deny(
                db,
                actor=user,
                action="case.deny",
                resource_type="response_case",
                resource_id=case.id,
                denied=True,
                reason="not the assigned counsellor",
            )
            raise HTTPException(403, "case is assigned to another counsellor")
        return
    if user.role == "welfare_officer":
        # An empty assignment list means NO units. "Unset" must never read as
        # "all" — that is how a scoping bug becomes a privacy incident.
        units = user.assigned_units or []
        if not units or (case.unit_id is not None and case.unit_id not in units):
            write_deny(
                db,
                actor=user,
                action="case.deny",
                resource_type="response_case",
                resource_id=case.id,
                denied=True,
                reason="unit not assigned to this welfare officer",
            )
            raise HTTPException(403, "case is outside your assigned units")
        return
    raise HTTPException(403, "role cannot open a case")


def _latest_score(db: Session, pid: str | None) -> RiskScore | None:
    if not pid:
        return None
    return (
        db.query(RiskScore)
        .filter(RiskScore.pseudonym_id == pid)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )


@router.get("/interventions/catalogue")
def catalogue(
    user: User = Depends(require_roles(*CASE_ROLES)),
):
    """The response ladder as data, so the console never hardcodes a tier."""
    return {
        "ladder": LADDER,
        "outcome_codes": list(OUTCOME_CODES),
        "modalities": list(MODALITIES),
        "unmask_reason_codes": UNMASK_REASON_CODES,
    }


@router.get("/interventions/case/{case_id}")
def case_detail(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*CASE_ROLES)),
):
    """F06 screen 2 — evidence card. The person is a pseudonym + unit until an
    unmask grant exists; this response never carries a name."""
    forbid_commander(user, db=db, resource_type="response_case", resource_id=case_id)
    case = _case_or_404(db, case_id)
    _assert_assigned(db, user, case)
    tri = db.query(TriageEntry).filter(TriageEntry.case_id == case.id).one_or_none()
    score = db.get(RiskScore, case.score_id) if case.score_id else _latest_score(db, case.pseudonym_id)
    factors = []
    masking = False
    if score is not None:
        factors = [
            {
                "rule_id": f.rule_id,
                "domain": f.domain,
                "display_key": f.display_key,
                "display_value": f.display_value,
                "observed_value": f.observed_value,
                "weight": f.weight,
            }
            for f in db.query(RiskFactor).filter(RiskFactor.score_id == score.id).all()
        ]
        masking = (
            db.query(MaskingFlag).filter(MaskingFlag.score_id == score.id).one_or_none() is not None
        )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    hours_open = round(max(0.0, (now - case.opened_at).total_seconds() / 3600.0), 1)
    overdue = case.sla_hours is not None and hours_open > case.sla_hours

    write_audit(
        db,
        actor=user,
        action="risk.read",
        resource_type="response_case",
        resource_id=case.id,
        subject_pseudonym_id=case.pseudonym_id,
        purpose="case_review",
        reason="case detail opened",
    )
    return {
        "case_id": case.id,
        "pseudonym_id": case.pseudonym_id,
        "unit_id": case.unit_id,
        "tier": case.tier,
        "status": case.status,
        "group_case": case.group_case,
        "incident_id": case.incident_id,
        "opened_at": case.opened_at.isoformat(),
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "sla_hours": case.sla_hours,
        "hours_open": hours_open,
        "overdue": overdue,
        "triage": (
            {
                "priority": tri.priority,
                "urgency": tri.urgency,
                "intervenability": tri.intervenability,
                "deferred_until": tri.deferred_until.isoformat() if tri.deferred_until else None,
                "cap_reason": tri.cap_reason,
            }
            if tri
            else None
        ),
        "score": (
            {
                "score": score.score,
                "tier": score.tier,
                "confidence": score.confidence,
                "sources_present": score.sources_present,
                "engine_version": score.engine_version,
                "ruleset_version": score.ruleset_version,
                "as_of": score.as_of.isoformat(),
                "hysteresis_held": score.hysteresis_held,
            }
            if score
            else None
        ),
        "masking": masking,
        "factors": factors,
        "top_factors": top_factors(factors, n=3) if factors else [],
        "ladder": LADDER.get(case.tier, {}),
        "disclaimer_key": "instr.not_diagnosis",
    }


@router.get("/interventions/case/{case_id}/timeline")
def case_timeline(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*CASE_ROLES)),
):
    """Ladder transitions, actions, outcomes, referrals, notes and identity
    events on one axis — 'why didn't this get seen' is always answerable."""
    forbid_commander(user, db=db, resource_type="response_case", resource_id=case_id)
    case = _case_or_404(db, case_id)
    _assert_assigned(db, user, case)
    events: list[dict] = [
        {
            "at": case.opened_at.isoformat(),
            "kind": "case_opened",
            "key": "timeline.case_opened",
            "detail": {"tier": case.tier},
        }
    ]
    for a in db.query(InterventionAction).filter(InterventionAction.case_id == case_id).all():
        events.append(
            {
                "at": a.initiated_at.isoformat(),
                "kind": "action",
                "key": "timeline.action",
                "detail": {"catalogue_id": a.catalogue_id, "actor_role": a.actor_role, "status": a.status},
            }
        )
    for o in db.query(InterventionOutcome).filter(InterventionOutcome.case_id == case_id).all():
        events.append(
            {
                "at": o.recorded_at.isoformat(),
                "kind": "outcome",
                "key": "timeline.outcome",
                "detail": {"outcome": o.outcome, "recorded_by_role": o.recorded_by_role},
            }
        )
    for r in db.query(TelemanasReferral).filter(TelemanasReferral.case_id == case_id).all():
        events.append(
            {
                "at": r.referred_at.isoformat(),
                "kind": "telemanas",
                "key": "timeline.telemanas",
                "detail": {"mode": r.mode, "outcome_status": r.outcome_status},
            }
        )
    for n in db.query(SessionNote).filter(SessionNote.case_id == case_id).all():
        events.append(
            {
                "at": n.session_at.isoformat(),
                "kind": "note",
                "key": "timeline.note",
                # Confidential (MHCA §23): the timeline shows that a session
                # happened, never its content.
                "detail": {"modality": n.modality, "themes": n.themes, "has_free_text": bool(n.free_text)},
            }
        )
    if case.pseudonym_id:
        for u in (
            db.query(UnmaskRequest)
            .filter(UnmaskRequest.pseudonym_id == case.pseudonym_id)
            .all()
        ):
            events.append(
                {
                    "at": (u.granted_at or u.created_at).isoformat(),
                    "kind": "unmask",
                    "key": "timeline.unmask",
                    "detail": {"status": u.status, "purpose": u.purpose_string},
                }
            )
        for b in (
            db.query(BreakGlassEvent)
            .filter(BreakGlassEvent.pseudonym_id == case.pseudonym_id)
            .all()
        ):
            events.append(
                {
                    "at": b.opened_at.isoformat(),
                    "kind": "break_glass",
                    "key": "timeline.break_glass",
                    "detail": {"notified_subject": b.notified_subject},
                }
            )
    events.sort(key=lambda e: e["at"])
    return {"case_id": case_id, "events": events}


@router.get("/interventions/case/{case_id}/notes")
def list_notes(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*CASE_ROLES)),
):
    forbid_commander(user, db=db, resource_type="session_note", resource_id=case_id)
    case = _case_or_404(db, case_id)
    _assert_assigned(db, user, case)
    rows = (
        db.query(SessionNote)
        .filter(SessionNote.case_id == case_id)
        .order_by(SessionNote.session_at.desc())
        .all()
    )
    out = []
    for n in rows:
        # RBAC DT-08: a counsellor reads notes they wrote; a welfare officer on
        # an assigned case sees that a session happened, never its free text.
        own = n.author_user_id == user.id
        out.append(
            {
                "note_id": n.id,
                "session_at": n.session_at.isoformat(),
                "modality": n.modality,
                "themes": n.themes,
                "risk_reestimate": n.risk_reestimate,
                "free_text": n.free_text if own else None,
                "free_text_withheld": bool(n.free_text) and not own,
                "own": own,
            }
        )
    write_audit(
        db,
        actor=user,
        action="notes.read",
        resource_type="session_note",
        resource_id=case_id,
        subject_pseudonym_id=case.pseudonym_id,
        purpose="case_review",
    )
    return {"case_id": case_id, "notes": out, "confidential_key": "note.confidential"}


@router.post("/interventions/case/{case_id}/notes")
def add_note(
    case_id: str,
    body: NoteIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor")),
):
    """F06 screen 4. Notes never leave this table — they are not an ML label
    input (ADR-0001) and there is no export route."""
    forbid_commander(user, db=db, resource_type="session_note", resource_id=case_id)
    if body.modality not in MODALITIES:
        raise HTTPException(400, "modality must be one of %s" % ", ".join(MODALITIES))
    case = _case_or_404(db, case_id)
    _assert_assigned(db, user, case)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session_at = now
    if body.session_at:
        try:
            session_at = datetime.fromisoformat(body.session_at.replace("Z", "")).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(400, "session_at must be an ISO-8601 timestamp") from None
    row = SessionNote(
        id=nid("nt"),
        case_id=case_id,
        author_user_id=user.id,
        session_at=session_at,
        modality=body.modality,
        themes=body.themes,
        risk_reestimate=body.risk_reestimate,
        free_text=body.free_text,
        created_at=now,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="notes.write",
        resource_type="session_note",
        resource_id=row.id,
        subject_pseudonym_id=case.pseudonym_id,
        purpose="welfare_intervention",
        reason=body.modality,
    )
    return {"note_id": row.id, "confidential": True, "exportable": False}


@router.get("/risk/{pseudonym_id}/trend")
def risk_trend(
    pseudonym_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*CASE_ROLES)),
):
    """F06 screen 2 — the before/after-intervention chart (TC-304). Score history
    plus the intervention markers that should explain its shape."""
    forbid_commander(user, db=db, resource_type="risk", resource_id=pseudonym_id)
    assert_subject_scope(db, user, pseudonym_id, resource_type="risk_score")
    rows = (
        db.query(RiskScore)
        .filter(RiskScore.pseudonym_id == pseudonym_id)
        .order_by(RiskScore.as_of.asc(), RiskScore.computed_at.asc())
        .all()
    )
    if not rows:
        raise HTTPException(404, "no score history")
    cases = db.query(ResponseCase).filter(ResponseCase.pseudonym_id == pseudonym_id).all()
    case_ids = [c.id for c in cases]
    markers = []
    if case_ids:
        for a in db.query(InterventionAction).filter(InterventionAction.case_id.in_(case_ids)).all():
            markers.append(
                {
                    "at": a.initiated_at.date().isoformat(),
                    "kind": "action",
                    "label_key": "trend.marker.action",
                    "detail": a.catalogue_id,
                }
            )
        for o in db.query(InterventionOutcome).filter(InterventionOutcome.case_id.in_(case_ids)).all():
            markers.append(
                {
                    "at": o.recorded_at.date().isoformat(),
                    "kind": "outcome",
                    "label_key": "trend.marker.outcome",
                    "detail": o.outcome,
                }
            )
    markers.sort(key=lambda m: m["at"])
    write_audit(
        db,
        actor=user,
        action="risk.read",
        resource_type="risk_score",
        resource_id=pseudonym_id,
        subject_pseudonym_id=pseudonym_id,
        purpose="case_review",
        reason="risk trend chart",
    )
    return {
        "pseudonym_id": pseudonym_id,
        "points": [
            {
                "as_of": r.as_of.isoformat(),
                "score": r.score,
                "tier": r.tier,
                "confidence": r.confidence,
            }
            for r in rows
        ],
        "markers": markers,
        "disclaimer_key": "instr.not_diagnosis",
    }
