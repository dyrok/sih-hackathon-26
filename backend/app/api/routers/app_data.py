from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...clock import as_of, clamp_capture_date
from ...config import get_settings
from ...consent import has_voluntary_consent
from ...db import get_db
from ...ids import nid
from ...models import CheckIn, InstrumentResult, PassiveFeature, RiskScore, User
from ...security import require_roles

router = APIRouter(prefix="/app", tags=["jawan-app"])


class CheckInIn(BaseModel):
    mood_label: str | None = None
    mood_score: int | None = None
    sleep_hours: float | None = None
    recorded_at: str | None = None


class InstrumentIn(BaseModel):
    instrument: str
    score: int
    item_9: int | None = None
    validity_fail: bool = False
    straight_lining: bool = False
    too_fast: bool = False
    all_max: bool = False
    recorded_at: str | None = None


class PassiveIn(BaseModel):
    sleep_hours_proxy: float
    recorded_at: str | None = None


def _day(raw: str | None):
    """Capture date, clamped to the plausible offline window.

    The client value stays useful as a *reported* timestamp for offline sync,
    but it may never drive retention — see clock.clamp_capture_date.
    """
    return clamp_capture_date(raw, as_of())


@router.post("/checkins")
def post_checkin(
    body: CheckInIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    if not has_voluntary_consent(db, user.pseudonym_id):
        raise HTTPException(403, "voluntary bundle requires consent")
    day = _day(body.recorded_at)
    row = CheckIn(
        id=nid("ck"),
        pseudonym_id=user.pseudonym_id,
        recorded_at=day,
        mood_label=body.mood_label,
        mood_score=body.mood_score,
        sleep_hours=body.sleep_hours,
        expires_at=day + timedelta(days=get_settings().raw_ttl_days),
        purged=False,
    )
    db.add(row)
    db.flush()
    return {"id": row.id}


@router.post("/instruments")
def post_instrument(
    body: InstrumentIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    if not has_voluntary_consent(db, user.pseudonym_id):
        raise HTTPException(403, "voluntary bundle requires consent")
    day = _day(body.recorded_at)
    row = InstrumentResult(
        id=nid("in"),
        pseudonym_id=user.pseudonym_id,
        instrument=body.instrument,
        score=body.score,
        item_9=body.item_9,
        validity_fail=body.validity_fail,
        straight_lining=body.straight_lining,
        too_fast=body.too_fast,
        all_max=body.all_max,
        recorded_at=day,
        expires_at=day + timedelta(days=get_settings().raw_ttl_days),
        purged=False,
    )
    db.add(row)
    db.flush()
    return {"id": row.id}


@router.post("/passive")
def post_passive(
    body: PassiveIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    if not has_voluntary_consent(db, user.pseudonym_id):
        raise HTTPException(403, "voluntary bundle requires consent")
    day = _day(body.recorded_at)
    row = PassiveFeature(
        id=nid("pf"),
        pseudonym_id=user.pseudonym_id,
        sleep_hours_proxy=body.sleep_hours_proxy,
        recorded_at=day,
    )
    db.add(row)
    db.flush()
    return {"id": row.id, "raw_audio": False}


@router.get("/me/trend")
def my_trend(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    rows = (
        db.query(RiskScore)
        .filter(RiskScore.pseudonym_id == user.pseudonym_id)
        .order_by(RiskScore.as_of.asc())
        .all()
    )
    return {
        "disclaimer_key": "instr.not_diagnosis",
        "trend": [{"as_of": r.as_of.isoformat(), "score": r.score, "tier": r.tier} for r in rows],
    }
