from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .models import AuditEvent, User


def _canonical(payload: dict[str, Any] | None) -> str:
    return json.dumps(payload or {}, sort_keys=True, default=str, separators=(",", ":"))


def _hash(prev: str | None, body: dict[str, Any]) -> str:
    raw = (prev or "GENESIS") + "|" + _canonical(body)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def last_hash(db: Session) -> str | None:
    row = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    return row.entry_hash if row else None


def write_audit(
    db: Session,
    *,
    actor: User | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    purpose: str | None = None,
    reason: str | None = None,
    subject_pseudonym_id: str | None = None,
    denied: bool = False,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    prev = last_hash(db)
    body = {
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "purpose": purpose,
        "reason": reason,
        "subject_pseudonym_id": subject_pseudonym_id,
        "denied": denied,
        "actor_id": actor.id if actor else None,
        "actor_role": actor.role if actor else None,
        "payload": payload or {},
    }
    event = AuditEvent(
        at=datetime.now(timezone.utc).replace(tzinfo=None),
        actor_id=actor.id if actor else None,
        actor_role=actor.role if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        purpose=purpose,
        reason=reason,
        subject_pseudonym_id=subject_pseudonym_id,
        denied=denied,
        prev_hash=prev,
        entry_hash=_hash(prev, body),
        payload=payload,
    )
    db.add(event)
    db.flush()
    return event


def verify_chain(db: Session) -> dict[str, Any]:
    rows = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    prev = None
    for row in rows:
        body = {
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "purpose": row.purpose,
            "reason": row.reason,
            "subject_pseudonym_id": row.subject_pseudonym_id,
            "denied": row.denied,
            "actor_id": row.actor_id,
            "actor_role": row.actor_role,
            "payload": row.payload or {},
        }
        expected = _hash(prev, body)
        if row.prev_hash != prev or row.entry_hash != expected:
            return {"ok": False, "broken_at": row.id}
        prev = row.entry_hash
    return {"ok": True, "entries": len(rows)}
