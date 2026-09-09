from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import CheckIn, InstrumentResult, PassiveFeature, VoiceFeature


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
    # Passive and voice rows are derived, not raw audio — but they are still
    # behavioural data collected under a voluntary bundle, and F08 promises the
    # same 90-day TTL for that bundle. A promise the code does not keep is worse
    # than a narrower promise (TC-454).
    n_p = 0
    for row in (
        db.query(PassiveFeature).filter(PassiveFeature.recorded_at <= cutoff).all()
    ):
        db.delete(row)
        n_p += 1
    n_v = 0
    for row in (
        db.query(VoiceFeature)
        .filter(VoiceFeature.purged.is_(False), VoiceFeature.recorded_at <= cutoff)
        .all()
    ):
        for field in (
            "f0_mean", "f0_sd", "speech_rate", "pause_count", "pause_total",
            "voiced_ratio", "loudness_var", "jitter", "shimmer",
        ):
            setattr(row, field, None)
        row.purged = True
        n_v += 1
    db.flush()
    return {
        "checkins_purged": n_c,
        "instruments_purged": n_i,
        "passive_purged": n_p,
        "voice_purged": n_v,
        "cutoff": cutoff.isoformat(),
    }
