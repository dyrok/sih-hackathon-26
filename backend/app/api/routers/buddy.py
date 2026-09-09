"""F02 screen 7 — battle buddy.

Coarse state only (ok | quiet | sos), visible to exactly one other principal.
Command sees neither side of any pairing: the whole module lives under /app,
which the ADR-0003 middleware denies to a commander token outright, and every
handler additionally resolves the subject from the token.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...consent import active_consent
from ...db import get_db
from ...ids import nid
from ...models import BuddyPair, BuddyState, IdentityMap, Notification, User
from ...security import require_roles

router = APIRouter(prefix="/app/buddy", tags=["battle-buddy"])

STATES = ("ok", "quiet", "sos")
BUDDY_BUNDLE = "buddy"
TELEMANAS_LINE = "14416"


class PairIn(BaseModel):
    buddy_pseudonym: str


class StateIn(BaseModel):
    state: str


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _active_pair(db: Session, pid: str) -> BuddyPair | None:
    return (
        db.query(BuddyPair)
        .filter(
            BuddyPair.ended_at.is_(None),
            (BuddyPair.a_pseudonym == pid) | (BuddyPair.b_pseudonym == pid),
        )
        .first()
    )


def _state_of(db: Session, pid: str) -> str:
    row = db.get(BuddyState, pid)
    return row.state if row else "ok"


@router.get("")
def my_buddy(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    pair = _active_pair(db, user.pseudonym_id)
    if pair is None:
        return {
            "paired": False,
            "my_state": _state_of(db, user.pseudonym_id),
            "empty_key": "buddy.empty",
            "helpline": TELEMANAS_LINE,
        }
    other = pair.b_pseudonym if pair.a_pseudonym == user.pseudonym_id else pair.a_pseudonym
    ident = db.query(IdentityMap).filter(IdentityMap.pseudonym_id == other).one_or_none()
    buddy_state = _state_of(db, other)
    return {
        "paired": True,
        "pair_id": pair.id,
        "my_state": _state_of(db, user.pseudonym_id),
        "buddy": {
            # Coarse state and unit only. No name, no score, no tier, ever.
            "pseudonym_id": other,
            "unit_id": ident.unit_id if ident else None,
            "state": buddy_state,
            "state_key": "buddy.state.%s" % buddy_state,
        },
        "sos": (
            {
                "helpline": TELEMANAS_LINE,
                "helpline_key": "buddy.sos.helpline",
                "jco_key": "buddy.sos.jco",
            }
            if buddy_state == "sos"
            else None
        ),
        "helpline": TELEMANAS_LINE,
    }


@router.post("/pair")
def pair(
    body: PairIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    if not active_consent(db, user.pseudonym_id, BUDDY_BUNDLE):
        raise HTTPException(403, "battle buddy requires the buddy consent bundle")
    if body.buddy_pseudonym == user.pseudonym_id:
        raise HTTPException(400, "cannot pair with yourself")
    target = (
        db.query(IdentityMap).filter(IdentityMap.pseudonym_id == body.buddy_pseudonym).one_or_none()
    )
    if target is None:
        raise HTTPException(404, "no such buddy code")
    if _active_pair(db, user.pseudonym_id):
        raise HTTPException(409, "already paired — end the current pairing first")
    if _active_pair(db, body.buddy_pseudonym):
        raise HTTPException(409, "that buddy is already paired")
    row = BuddyPair(
        id=nid("bp"),
        a_pseudonym=user.pseudonym_id,
        b_pseudonym=body.buddy_pseudonym,
        created_at=_now(),
    )
    db.add(row)
    db.add(
        Notification(
            id=nid("nt"),
            recipient_pseudonym=body.buddy_pseudonym,
            kind="buddy_pair",
            body_key="buddy.notify.paired",
            payload={},
            created_at=_now(),
        )
    )
    db.flush()
    write_audit(
        db,
        actor=user,
        action="buddy.pair",
        resource_type="buddy_pair",
        resource_id=row.id,
        subject_pseudonym_id=user.pseudonym_id,
        purpose="peer_support",
    )
    return {"pair_id": row.id, "paired": True}


@router.delete("")
def unpair(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    pair_row = _active_pair(db, user.pseudonym_id)
    if pair_row is None:
        raise HTTPException(404, "not paired")
    pair_row.ended_at = _now()
    db.flush()
    write_audit(
        db,
        actor=user,
        action="buddy.unpair",
        resource_type="buddy_pair",
        resource_id=pair_row.id,
        subject_pseudonym_id=user.pseudonym_id,
        purpose="peer_support",
    )
    return {"paired": False}


@router.post("/state")
def set_state(
    body: StateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    if body.state not in STATES:
        raise HTTPException(400, "state must be one of %s" % ", ".join(STATES))
    row = db.get(BuddyState, user.pseudonym_id)
    if row is None:
        row = BuddyState(pseudonym_id=user.pseudonym_id, state=body.state, updated_at=_now())
        db.add(row)
    else:
        row.state = body.state
        row.updated_at = _now()
    pair_row = _active_pair(db, user.pseudonym_id)
    if pair_row is not None and body.state == "sos":
        other = (
            pair_row.b_pseudonym if pair_row.a_pseudonym == user.pseudonym_id else pair_row.a_pseudonym
        )
        db.add(
            Notification(
                id=nid("nt"),
                recipient_pseudonym=other,
                kind="buddy_sos",
                body_key="buddy.notify.sos",
                payload={},
                created_at=_now(),
            )
        )
    db.flush()
    write_audit(
        db,
        actor=user,
        action="buddy.state",
        resource_type="buddy_state",
        subject_pseudonym_id=user.pseudonym_id,
        purpose="peer_support",
        reason=body.state,
    )
    return {"state": body.state, "helpline": TELEMANAS_LINE}
