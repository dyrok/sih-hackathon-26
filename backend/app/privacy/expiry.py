from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import CheckIn, InstrumentResult


def expire_raw(db: Session, as_of: date) -> dict[str, int]:
    cutoff = as_of - timedelta(days=get_settings().raw_ttl_days)
    n_c = 0
    n_i = 0
    for row in db.query(CheckIn).filter(CheckIn.purged.is_(False), CheckIn.recorded_at <= cutoff).all():
        row.mood_label = None
        row.mood_score = None
        row.sleep_hours = None
        row.purged = True
        n_c += 1
    for row in db.query(InstrumentResult).filter(InstrumentResult.purged.is_(False), InstrumentResult.recorded_at <= cutoff).all():
        row.score = 0
        row.item_9 = None
        row.purged = True
        n_i += 1
    db.flush()
    return {"checkins_purged": n_c, "instruments_purged": n_i, "cutoff": cutoff.isoformat()}
