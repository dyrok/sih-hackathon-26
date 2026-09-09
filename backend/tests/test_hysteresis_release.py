"""The recovery half of the response ladder.

Hysteresis exists so a person does not flicker between tiers on one noisy day.
It must not become a ratchet: F09's persona arc ends Green on days 85-90, and
"the loop closes" is the whole demo. These tests pin the release path.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.db import SessionLocal
from app.models import RiskScore
from app.risk.aggregator import apply_hysteresis
from app.risk.scorer import _downgrade_confirmations
from app.ids import nid


def _write(db, pid, day, *, score, tier, candidate):
    from datetime import datetime, timezone

    db.add(
        RiskScore(
            id=nid("rs"),
            pseudonym_id=pid,
            score=score,
            tier=tier,
            confidence="high",
            engine_version="v1.0",
            ruleset_version=1,
            computed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            as_of=day,
            sources_present=["hr"],
            stale=False,
            hysteresis_held=tier != candidate,
            candidate_tier=candidate,
        )
    )


def test_confirmations_count_the_candidate_not_the_held_tier(client):
    """Two held-Red rows whose *candidate* was Amber must count as two
    confirmations — previously they counted as zero, forever."""
    db = SessionLocal()
    try:
        pid = "ps_hyst_test"
        base = date(2026, 8, 20)
        _write(db, pid, base, score=65, tier="red", candidate="red")
        _write(db, pid, base + timedelta(days=1), score=45, tier="red", candidate="amber")
        _write(db, pid, base + timedelta(days=2), score=40, tier="red", candidate="amber")
        db.commit()
        n = _downgrade_confirmations(db, pid, "red", base + timedelta(days=3))
        assert n == 2, n
        released, held = apply_hysteresis("red", "amber", n, 2)
        assert released == "amber" and held is False
    finally:
        db.close()


def test_the_first_good_day_is_held(client):
    """`downgrade_confirmations: 2` means two consecutive lower readings: the
    prior cycle plus this one. So the very first good day is still held."""
    db = SessionLocal()
    try:
        pid = "ps_hyst_one"
        base = date(2026, 8, 20)
        _write(db, pid, base, score=65, tier="red", candidate="red")
        db.commit()
        n = _downgrade_confirmations(db, pid, "red", base + timedelta(days=1))
        assert n == 0
        tier, held = apply_hysteresis("red", "amber", n, 2)
        assert tier == "red" and held is True
        # …and the second consecutive good day releases it.
        _write(db, pid, base + timedelta(days=1), score=45, tier="red", candidate="amber")
        db.commit()
        n2 = _downgrade_confirmations(db, pid, "red", base + timedelta(days=2))
        assert n2 == 1
        tier2, held2 = apply_hysteresis("red", "amber", n2, 2)
        assert tier2 == "amber" and held2 is False
    finally:
        db.close()


def test_a_relapse_resets_the_confirmation_run(client):
    db = SessionLocal()
    try:
        pid = "ps_hyst_relapse"
        base = date(2026, 8, 20)
        _write(db, pid, base, score=40, tier="red", candidate="amber")
        _write(db, pid, base + timedelta(days=1), score=70, tier="red", candidate="red")
        db.commit()
        assert _downgrade_confirmations(db, pid, "red", base + timedelta(days=2)) == 0
    finally:
        db.close()


def test_an_escalation_is_never_delayed(client):
    """Hysteresis damps recovery, never the alarm."""
    tier, held = apply_hysteresis("green", "critical", 0, 2)
    assert tier == "critical" and held is False


def test_the_persona_recovers_to_green_over_the_arc(client):
    """End-to-end: replay a recovering signal profile and check the tier
    actually comes down instead of ratcheting."""
    from app.clock import as_of, set_as_of
    from app.risk.scorer import score_person
    from app.models import SignalSnapshot
    from datetime import datetime, timezone

    pid = "ps_recover"
    db = SessionLocal()
    try:
        start = date(2026, 8, 1)
        # Day 1-3: a 60-day duty streak and a stale home-leave clock -> elevated.
        # Day 4 onward: the streak is broken and leave is granted -> should fall.
        for i in range(10):
            day = start + timedelta(days=i)
            elevated = i < 3
            profile = {
                "consecutive_duty_days": 62.0 if elevated else 1.0,
                "circadian_disruption_score": 0.7 if elevated else 0.05,
                "days_since_home_leave": 200.0 if elevated else 2.0,
                "leave_cancel_count": 2.0 if elevated else 0.0,
                "family_separation_index": 6000.0 if elevated else 100.0,
                "days_in_high_risk_posting": 40.0 if elevated else 0.0,
                "transfer_count_12m": 2.0 if elevated else 0.0,
            }
            for key, value in profile.items():
                db.add(
                    SignalSnapshot(
                        id=nid("sn"),
                        pseudonym_id=pid,
                        signal_key=key,
                        value=value,
                        window_start=day - timedelta(days=89),
                        window_end=day,
                        computed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                        engine_version="v1.0",
                    )
                )
        db.commit()

        tiers = []
        for i in range(10):
            day = start + timedelta(days=i)
            set_as_of(day)
            row = score_person(db, pid, as_of=day, emit_case=False)
            tiers.append(row.tier)
        db.commit()
    finally:
        set_as_of(None)
        db.close()

    assert tiers[0] != "green", tiers
    assert tiers[-1] == "green", tiers
