from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...authz import assert_subject_scope
from ...clock import as_of
from ...db import get_db
from ...firewall import forbid_commander
from ...models import SignalGroupFlag, SignalSnapshot, User
from ...security import require_roles

router = APIRouter(tags=["signals"])


@router.get("/signals/group/{unit_id}/exposure")
def group_exposure(
    unit_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer", "admin")),
):
    forbid_commander(user, db=db, resource_type="group_flag", resource_id=unit_id)
    flags = db.query(SignalGroupFlag).filter(SignalGroupFlag.unit_id == unit_id).all()
    return {
        "unit_id": unit_id,
        "flags": [
            {
                "signal_key": f.signal_key,
                "value": f.value,
                "incident_id": f.incident_id,
                "valid_from": f.valid_from.isoformat(),
                "valid_until": f.valid_until.isoformat() if f.valid_until else None,
            }
            for f in flags
        ],
    }


@router.get("/signals/{pseudonym_id}")
def get_signals(
    pseudonym_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer", "admin")),
):
    forbid_commander(user, db=db, resource_type="signals", resource_id=pseudonym_id)
    if user.role == "admin":
        raise HTTPException(403, "admin has no read grant on individual signals")
    assert_subject_scope(db, user, pseudonym_id, resource_type="signal_snapshot")
    rows = (
        db.query(SignalSnapshot)
        .filter(SignalSnapshot.pseudonym_id == pseudonym_id, SignalSnapshot.window_end == as_of())
        .all()
    )
    write_audit(
        db,
        actor=user,
        action="signals.read",
        resource_type="signal_snapshot",
        resource_id=pseudonym_id,
        subject_pseudonym_id=pseudonym_id,
        purpose="case_review",
        reason="signal evidence behind a case",
    )
    return {
        "pseudonym_id": pseudonym_id,
        "as_of": as_of().isoformat(),
        "signals": {r.signal_key: r.value for r in rows},
    }
