from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .models import AuditCheckpoint, AuditEvent, User


def _canonical(payload: dict[str, Any] | None) -> str:
    return json.dumps(payload or {}, sort_keys=True, default=str, separators=(",", ":"))


def _hash(prev: str | None, body: dict[str, Any]) -> str:
    """The chain covers the timestamp and the sequence number too.

    Hashing only the event content left two holes a DBA could walk through:
    back-dating an event kept the chain valid (TC-442), and truncating the tail
    left a shorter but still self-consistent chain (TC-443). Including ``at``
    closes the first; including ``seq`` means a missing tail is detectable
    because the last entry no longer matches the row count.
    """
    raw = (prev or "GENESIS") + "|" + _canonical(body)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def last_hash(db: Session) -> str | None:
    row = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    return row.entry_hash if row else None


def _seq(db: Session) -> int:
    return db.query(AuditEvent).count() + 1


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
    at = datetime.now(timezone.utc).replace(tzinfo=None)
    body = {
        "at": at.isoformat(),
        "seq": _seq(db),
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
        at=at,
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
    _advance_checkpoint(db, event)
    return event


def _advance_checkpoint(db: Session, event: AuditEvent) -> None:
    row = db.get(AuditCheckpoint, 1)
    if row is None:
        row = AuditCheckpoint(id=1, entry_count=0, head_hash=None, updated_at=event.at)
        db.add(row)
    row.entry_count = (row.entry_count or 0) + 1
    row.head_hash = event.entry_hash
    row.updated_at = event.at
    db.flush()


def verify_chain(db: Session) -> dict[str, Any]:
    rows = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    prev = None
    for i, row in enumerate(rows, start=1):
        body = {
            "at": row.at.isoformat(),
            "seq": i,
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
            return {"ok": False, "broken_at": row.id, "reason": "entry_modified"}
        prev = row.entry_hash

    checkpoint = db.get(AuditCheckpoint, 1)
    if checkpoint is not None:
        if checkpoint.entry_count != len(rows):
            # Rows were removed (or added out of band) since the last write.
            return {
                "ok": False,
                "reason": "entry_count_mismatch",
                "expected_entries": checkpoint.entry_count,
                "entries": len(rows),
            }
        if checkpoint.head_hash != prev:
            return {"ok": False, "reason": "head_mismatch", "entries": len(rows)}
    return {"ok": True, "entries": len(rows), "head": prev}


def write_deny(db: Session, **kwargs) -> AuditEvent:
    """Record a refusal, and make it survive.

    A denial raises ``HTTPException``, which unwinds through ``get_db`` and
    rolls the session back — taking the audit row with it. Deny-by-default is
    only trustworthy if the denial is *recorded*, so the deny path commits
    immediately. It is safe to commit here because a refused request performs no
    other state change: the row is the whole outcome.
    """
    kwargs.setdefault("denied", True)
    event = write_audit(db, **kwargs)
    db.commit()
    return event
