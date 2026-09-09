from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...audit import write_audit, write_deny
from ...clock import as_of
from ...config import get_settings
from ...consent import active_consent, has_voluntary_consent, withdraw_all
from ...db import get_db
from ...firewall import forbid_commander
from ...consent import artefact_hash
from ...ids import nid
from ...models import (
    BreakGlassEvent,
    ConsentArtefact,
    IdentityMap,
    Notification,
    UnmaskRequest,
    User,
)
from ...privacy.expiry import expire_raw
from ...privacy.kanonymity import aggregate_unit
from ...security import require_roles

router = APIRouter(tags=["privacy"])

PURPOSE_VOCAB = {
    "case_review",
    "counsellor_outreach",
    "welfare_intervention",
    "imminent_harm",
    "telemanas_handoff",
}


class UnmaskIn(BaseModel):
    pseudonym_id: str
    reason: str
    purpose_string: str = "case_review"


class BreakGlassIn(BaseModel):
    pseudonym_id: str
    reason: str
    #: Required only past the weekly cap: an explicit statement that the
    #: counsellor accepts oversight review for an above-cap disclosure.
    acknowledge_oversight: bool = False


class ConsentIn(BaseModel):
    bundle_id: str
    purpose_string: str
    data_categories: list[str]
    language: str = "en"


@router.get("/aggregates/unit/{unit_id}")
def unit_aggregate(
    unit_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("commander", "counsellor", "welfare_officer", "auditor")),
):
    if user.role == "commander" and user.unit_id and user.unit_id != unit_id:
        raise HTTPException(403, "commander may only view own unit chain")
    detailed = user.role in {"counsellor", "welfare_officer"}
    data = aggregate_unit(db, unit_id, detailed=detailed)
    write_audit(
        db,
        actor=user,
        action="aggregates.read",
        resource_type="unit_aggregate",
        resource_id=unit_id,
        purpose="unit_welfare_overview",
    )
    return data


@router.post("/privacy/unmask")
def open_unmask(
    body: UnmaskIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="identity_map", resource_id=body.pseudonym_id)
    if body.purpose_string not in PURPOSE_VOCAB:
        raise HTTPException(400, "purpose not in vocabulary")
    if not active_consent(db, body.pseudonym_id):
        write_deny(
            db,
            actor=user,
            action="unmask.deny",
            resource_type="identity_map",
            resource_id=body.pseudonym_id,
            subject_pseudonym_id=body.pseudonym_id,
            denied=True,
            reason="no active consent artefact",
        )
        raise HTTPException(403, "unmask requires an active consent artefact")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    req = UnmaskRequest(
        id=nid("um"),
        pseudonym_id=body.pseudonym_id,
        reason=body.reason,
        purpose_string=body.purpose_string,
        counsellor_user_id=user.id if user.role == "counsellor" else None,
        welfare_user_id=user.id if user.role == "welfare_officer" else None,
        status="pending",
        created_at=now,
    )
    db.add(req)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="unmask.request",
        resource_type="unmask_request",
        resource_id=req.id,
        subject_pseudonym_id=body.pseudonym_id,
        purpose=body.purpose_string,
        reason=body.reason,
    )
    return {"request_id": req.id, "status": req.status}


@router.post("/privacy/unmask/{request_id}/approve")
def approve_unmask(
    request_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="identity_map", resource_id=request_id)
    req = db.get(UnmaskRequest, request_id)
    if req is None:
        raise HTTPException(404, "request not found")
    if user.role == "admin":
        raise HTTPException(403, "admin cannot be a keyholder")
    # One person holding both roles ≠ two keys.
    other = req.counsellor_user_id if user.role == "welfare_officer" else req.welfare_user_id
    if other == user.id:
        write_deny(
            db,
            actor=user,
            action="unmask.deny",
            resource_type="unmask_request",
            resource_id=request_id,
            subject_pseudonym_id=req.pseudonym_id,
            denied=True,
            reason="same principal cannot supply both keys",
        )
        raise HTTPException(403, "two distinct human principals required")
    if user.role == "counsellor":
        if req.counsellor_user_id and req.counsellor_user_id != user.id:
            raise HTTPException(409, "counsellor key already set")
        req.counsellor_user_id = user.id
    elif user.role == "welfare_officer":
        if req.welfare_user_id and req.welfare_user_id != user.id:
            raise HTTPException(409, "welfare key already set")
        req.welfare_user_id = user.id
    else:
        raise HTTPException(403, "role cannot hold a key")

    if req.counsellor_user_id and req.welfare_user_id:
        if req.counsellor_user_id == req.welfare_user_id:
            req.status = "denied"
            write_audit(
                db,
                actor=user,
                action="unmask.deny",
                resource_type="unmask_request",
                resource_id=request_id,
                subject_pseudonym_id=req.pseudonym_id,
                denied=True,
                reason="same principal cannot supply both keys",
            )
            raise HTTPException(403, "two distinct human principals required")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        req.status = "granted"
        req.granted_at = now
        req.expires_at = now + timedelta(hours=get_settings().unmask_session_hours)
        write_audit(
            db,
            actor=user,
            action="unmask.grant",
            resource_type="identity_map",
            resource_id=req.pseudonym_id,
            subject_pseudonym_id=req.pseudonym_id,
            purpose=req.purpose_string,
            reason=req.reason,
        )
    db.flush()
    return {"request_id": req.id, "status": req.status, "expires_at": req.expires_at}


@router.get("/privacy/unmask/{request_id}/identity")
def read_identity(
    request_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="identity_map", resource_id=request_id)
    req = db.get(UnmaskRequest, request_id)
    if req is None:
        raise HTTPException(404, "request not found")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if req.status != "granted" or req.expires_at is None or req.expires_at < now:
        raise HTTPException(403, "no active unmask grant")
    if user.id not in {req.counsellor_user_id, req.welfare_user_id}:
        raise HTTPException(403, "not a keyholder on this grant")
    ident = db.query(IdentityMap).filter(IdentityMap.pseudonym_id == req.pseudonym_id).one_or_none()
    if ident is None:
        raise HTTPException(404, "identity not found")
    write_audit(
        db,
        actor=user,
        action="identity.read",
        resource_type="identity_map",
        resource_id=ident.personnel_id,
        subject_pseudonym_id=req.pseudonym_id,
        purpose=req.purpose_string,
        reason=req.reason,
    )
    return {
        "personnel_id": ident.personnel_id,
        "legal_name": ident.legal_name,
        "rank": ident.rank,
        "unit_id": ident.unit_id,
        "session_expires_at": req.expires_at.isoformat(),
    }


@router.post("/privacy/break-glass")
def break_glass(
    body: BreakGlassIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor")),
):
    forbid_commander(user, db=db, resource_type="break_glass", resource_id=body.pseudonym_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    settings = get_settings()

    # Break-glass is meant to be the expensive path. Before this, it was the
    # cheap one: unlimited, un-countersigned identity disclosure (TC-438).
    # It is never hard-blocked — waiting for a second key can be the costlier
    # failure — but past the weekly cap it demands an explicit oversight
    # acknowledgement, a substantive reason, and it notifies every welfare
    # officer rather than one.
    week_start = now - timedelta(days=7)
    recent = (
        db.query(BreakGlassEvent)
        .filter(
            BreakGlassEvent.counsellor_user_id == user.id,
            BreakGlassEvent.opened_at >= week_start,
        )
        .count()
    )
    above_cap = recent >= settings.break_glass_weekly_cap
    if above_cap and not (body.acknowledge_oversight and len(body.reason.strip()) >= 20):
        write_deny(
            db,
            actor=user,
            action="break_glass.throttled",
            resource_type="break_glass_event",
            resource_id=body.pseudonym_id,
            subject_pseudonym_id=body.pseudonym_id,
            denied=True,
            reason="weekly break-glass cap reached",
            payload={"used": recent, "cap": settings.break_glass_weekly_cap},
        )
        raise HTTPException(
            429,
            "break-glass cap reached (%d this week). Use the dual-key path, or resend with "
            "acknowledge_oversight=true and a reason of at least 20 characters — the request "
            "will be countersigned by welfare oversight." % recent,
        )
    event = BreakGlassEvent(
        id=nid("bg"),
        counsellor_user_id=user.id,
        pseudonym_id=body.pseudonym_id,
        reason=body.reason,
        opened_at=now,
        expires_at=now + timedelta(hours=settings.break_glass_hours),
        notified_subject=True,
        notified_welfare=True,
        oversight_flag=True,
    )
    db.add(event)
    db.add(
        Notification(
            id=nid("nt"),
            recipient_pseudonym=body.pseudonym_id,
            kind="break_glass",
            body_key="notify.breakglass.subject",
            payload={"reason": body.reason, "expires_at": event.expires_at.isoformat()},
            created_at=now,
        )
    )
    welfare_officers = db.query(User).filter(User.role == "welfare_officer").all()
    # Above the cap every welfare officer is notified, not just the first one.
    recipients = welfare_officers if above_cap else welfare_officers[:1]
    for welfare in recipients:
        db.add(
            Notification(
                id=nid("nt"),
                recipient_user_id=welfare.id,
                kind="break_glass_oversight",
                body_key="notify.breakglass.welfare",
                payload={"pseudonym_id": body.pseudonym_id, "above_cap": above_cap},
                created_at=now,
            )
        )
    db.flush()
    write_audit(
        db,
        actor=user,
        action="break_glass.open",
        resource_type="break_glass_event",
        resource_id=event.id,
        subject_pseudonym_id=body.pseudonym_id,
        purpose="imminent_harm",
        reason=body.reason,
        payload={"used_this_week": recent + 1, "above_cap": above_cap},
    )
    ident = db.query(IdentityMap).filter(IdentityMap.pseudonym_id == body.pseudonym_id).one_or_none()
    return {
        "break_glass_id": event.id,
        "used_this_week": recent + 1,
        "weekly_cap": settings.break_glass_weekly_cap,
        "above_cap": above_cap,
        "expires_at": event.expires_at.isoformat(),
        "notified_subject": True,
        "notified_welfare": True,
        "oversight_flag": True,
        "identity": {
            "personnel_id": ident.personnel_id if ident else None,
            "legal_name": ident.legal_name if ident else None,
        },
    }


@router.post("/app/consent")
def grant_consent(
    body: ConsentIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    if not user.pseudonym_id:
        raise HTTPException(400, "jawan missing pseudonym")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    artefact = ConsentArtefact(
        consent_id=nid("cn"),
        principal_pseudonym=user.pseudonym_id,
        bundle_id=body.bundle_id,
        purpose_string=body.purpose_string,
        data_categories=body.data_categories,
        language=body.language,
        consent_version="v1",
        granted_at=now,
        artefact_hash=artefact_hash(
            principal=user.pseudonym_id,
            bundle_id=body.bundle_id,
            purpose=body.purpose_string,
            categories=body.data_categories,
            language=body.language,
            version="v1",
            granted_at=now,
        ),
    )
    db.add(artefact)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="consent.grant",
        resource_type="consent_artefact",
        resource_id=artefact.consent_id,
        subject_pseudonym_id=user.pseudonym_id,
        purpose=body.purpose_string,
    )
    return {"consent_id": artefact.consent_id, "bundle_id": body.bundle_id}


@router.post("/app/consent/withdraw")
def withdraw(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    n = withdraw_all(db, user.pseudonym_id, now)
    write_audit(
        db,
        actor=user,
        action="consent.withdraw",
        resource_type="consent_artefact",
        subject_pseudonym_id=user.pseudonym_id,
        purpose="principal_rights",
        reason="silent_withdrawal",
    )
    return {"withdrawn": n, "command_visible": False}


@router.get("/app/who-viewed")
def who_viewed(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    from ...models import AuditEvent

    rows = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.subject_pseudonym_id == user.pseudonym_id,
            AuditEvent.denied.is_(False),
            AuditEvent.action.in_(
                {
                    "risk.read",
                    "risk.explanation",
                    "signals.read",
                    "identity.read",
                    "unmask.grant",
                    "break_glass.open",
                    "interventions.action",
                    "interventions.outcome",
                    "telemanas.referral",
                }
            ),
        )
        .order_by(AuditEvent.at.desc())
        .limit(100)
        .all()
    )
    return {
        "title_key": "whoViewed.title",
        "entries": [
            {
                "role": r.actor_role,
                "when": r.at.isoformat(),
                "why": r.reason or r.purpose,
                "action": r.action,
            }
            for r in rows
        ],
    }


@router.post("/jobs/expire-raw")
def run_expiry(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    result = expire_raw(db, as_of())
    write_audit(db, actor=user, action="jobs.expire_raw", resource_type="checkins", payload=result)
    return result


@router.get("/welfare/personnel/{personnel_id}")
def trap_personnel_lookup(
    personnel_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("commander", "counsellor", "welfare_officer", "admin", "jawan", "auditor")),
):
    """Explicit no-route for the judge's attack (TC-401). Always 403."""
    write_audit(
        db,
        actor=user,
        action="firewall.deny",
        resource_type="personnel",
        resource_id=personnel_id,
        denied=True,
        reason="no personnel-id welfare lookup exists",
    )
    raise HTTPException(403, "no personnel-id welfare lookup exists (ADR-0003)")
