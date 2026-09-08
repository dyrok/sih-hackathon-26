from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...audit import verify_chain
from ...db import get_db
from ...models import AuditEvent, User
from ...security import require_roles

router = APIRouter(tags=["audit"])


@router.get("/audit/verify")
def verify(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("auditor", "admin")),
):
    return verify_chain(db)


@router.get("/audit/events")
def list_events(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("auditor")),
):
    rows = db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(200).all()
    return {
        "events": [
            {
                "id": r.id,
                "at": r.at.isoformat(),
                "actor_role": r.actor_role,
                "action": r.action,
                "resource_type": r.resource_type,
                "denied": r.denied,
                "purpose": r.purpose,
            }
            for r in rows
        ]
    }
