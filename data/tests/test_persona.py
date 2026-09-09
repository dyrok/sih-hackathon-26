"""TC-502 — DEMO-PERSONA-01 reproduces the F09 arc, day for day.

`Given defaults, when seeding completes, then the persona "Constable, 34, 3rd
Bn" exists with the exact scripted 90-day arc from F09.`  (test-plan.md §3)

The arc table below is transcribed independently from
``docs/features/F09-synthetic-data-generator.md`` §"The scripted persona". If
the doc and the generator ever drift, this test fails — which is the point.
"""

from __future__ import annotations

from datetime import date

import pytest

from data import spec as S
from data.gen import build
from data.persona import ARC, arc_evidence, consecutive_duty_days, sleep_hours

#: F09 §"The scripted persona", transcribed: (day_from, day_to, event, expected).
F09_ARC_TABLE = (
    (1, 30, "Normal roster; one leave taken and returned",
     "Green; baselines established"),
    (31, 31, "Leave application cancelled (#1)", "silent HR signal"),
    (40, 50, "Rotation to night-heavy duty", "circadian score rises"),
    (55, 55, "Leave cancelled (#2)", "silent HR signal"),
    (58, 60, "60 consecutive duty days; sleep proxy -30% vs baseline",
     "baseline breach accumulates"),
    (62, 62, "Amber flag -> buddy nudge + JCO informal check",
     "first visible intervention (F05)"),
    (64, 64, "Voluntary check-in says \"I'm fine\" despite signals",
     "masking flag (FR-07)"),
    (65, 65, "Red flag with explanation factors",
     "counsellor outreach task, <= 24 h SLA"),
    (66, 66, "Dual-key unmask (counsellor + welfare officer) - logged",
     "subject sees it in who-viewed-my-data"),
    (68, 70, "Roster swap proposed & approved; duty load drops",
     "intervention recorded (F06)"),
    (75, 85, "Trend down; check-ins stabilize", "risk trend decreases"),
    (85, 90, "Green", "loop closed - arc printed in the run summary"),
)


@pytest.fixture(scope="module")
def persona_ds():
    return build(seed=42, persona_only=True)


@pytest.fixture(scope="module")
def by_day(persona_ds):
    return {
        "roster": dict(
            (S.day_number(date.fromisoformat(r["duty_date"])), r) for r in persona_ds.roster
        ),
        "checkin": dict(
            (S.day_number(date.fromisoformat(r["recorded_at"])), r) for r in persona_ds.checkin
        ),
        "passive": dict(
            (S.day_number(date.fromisoformat(r["recorded_at"])), r) for r in persona_ds.passive
        ),
    }


# ---------------------------------------------------------------------------
# The table itself
# ---------------------------------------------------------------------------


def test_arc_table_matches_f09_day_for_day():
    assert tuple(step.as_tuple() for step in ARC) == F09_ARC_TABLE


def test_arc_days_are_inside_the_window_and_ordered():
    previous = 0
    for step in ARC:
        assert 1 <= step.day_from <= step.day_to <= S.ARC_DAYS
        assert step.day_from >= previous, "arc steps must be chronological"
        previous = step.day_from


# ---------------------------------------------------------------------------
# Identity — must agree with backend/app/seed.py
# ---------------------------------------------------------------------------


def test_identity_matches_backend_seed(persona_ds, backend_seed):
    assert S.PERSONA_PERSONNEL_ID == backend_seed.PERSONA_PERSONNEL
    assert S.PERSONA_PSEUDONYM_ID == backend_seed.PERSONA_PSEUDONYM
    assert S.PERSONA_UNIT_ID == backend_seed.UNIT_3BN
    assert S.ARC_START == backend_seed.ARC_START
    assert S.day(1) == backend_seed.day(1)
    assert S.day(S.ARC_DAYS) == backend_seed.day(90)

    person = persona_ds.personnel[0]
    assert person["personnel_id"] == "CR-DEMO-01"
    assert person["pseudonym_id"] == "ps_demo01"
    assert person["rank"] == "Constable"
    assert person["age"] == 34
    assert person["unit_id"] == "3BN"


def test_days_1_to_67_reproduce_the_backend_seed_shapes(by_day):
    """kv's seed writes days 1-90; days 1-67 must be identical row for row."""
    for n in range(1, 68):
        roster = by_day["roster"][n]
        assert roster["shift_code"] == ("night" if 40 <= n <= 50 else "day"), n
        assert roster["rest_day"] is False, n
        checkin = by_day["checkin"][n]
        expected_hours = 4.0 if n == 64 else (4.9 if n >= 56 else 7.0)
        assert checkin["sleep_hours"] == expected_hours, n
        assert checkin["mood_label"] == ("fine" if n == 64 else "ok"), n
        assert checkin["mood_score"] == (5 if n == 64 else 3), n
        assert by_day["passive"][n]["sleep_hours_proxy"] == expected_hours, n


# ---------------------------------------------------------------------------
# The arc, claim by claim
# ---------------------------------------------------------------------------


def test_day_31_and_55_cancelled_leaves(persona_ds):
    cancelled = sorted(
        S.day_number(date.fromisoformat(row["cancelled_at"]))
        for row in persona_ds.leave
        if row["cancelled_at"]
    )
    assert cancelled == [31, 55]
    for row in persona_ds.leave:
        if row["cancelled_at"]:
            assert row["sanctioned_from"] is None, "a cancelled leave is never taken"


def test_days_40_to_50_are_night_heavy(by_day):
    nights = sorted(n for n, row in by_day["roster"].items() if row["shift_code"] == "night")
    assert nights == list(range(40, 51))


def test_day_58_to_60_streak_and_sleep_minus_30_percent(by_day):
    assert consecutive_duty_days(58) == 58
    assert consecutive_duty_days(60) == 60
    baseline = S.PERSONA_SLEEP_BASELINE_HOURS
    for n in (58, 59, 60):
        proxy = by_day["passive"][n]["sleep_hours_proxy"]
        assert (proxy - baseline) / baseline == pytest.approx(-0.30, abs=1e-9), n


def test_cancelled_leave_does_not_reset_the_duty_streak():
    """F09 edge case: the cancellation is the point — the streak must survive it."""
    assert consecutive_duty_days(S.PERSONA_CANCEL_DAY_1) == S.PERSONA_CANCEL_DAY_1
    assert consecutive_duty_days(S.PERSONA_CANCEL_DAY_2) == S.PERSONA_CANCEL_DAY_2


def test_day_62_amber_preconditions(by_day):
    """At day 62 the duty streak and cancellations have both crossed F04's bar."""
    assert consecutive_duty_days(62) >= 60
    assert len([1 for n in (31, 55) if n <= 62]) == 2


def test_day_64_masking_fixture(by_day):
    checkin = by_day["checkin"][64]
    assert checkin["mood_label"] == "fine"
    assert checkin["mood_score"] >= 4                     # scorer reads >= 4 as "fine"
    assert checkin["sleep_hours"] <= 4.5                  # v1.yaml masking.adverse
    assert consecutive_duty_days(64) >= 60


def test_day_65_red_has_no_crisis_escalation(persona_ds):
    """PHQ-9 item 9 stays 0: any non-zero routes to Critical and breaks 85-90 Green."""
    item9 = [row["item_9"] for row in persona_ds.instrument if row["instrument"] == "PHQ-9"]
    assert item9 and set(item9) == {0}


def test_days_68_to_70_roster_swap_drops_the_load(by_day):
    for n in range(68, 71):
        assert by_day["roster"][n]["rest_day"] is True, n
    assert consecutive_duty_days(67) == 67
    assert consecutive_duty_days(71) == 1


def test_days_75_to_85_trend_down(by_day):
    values = [by_day["passive"][n]["sleep_hours_proxy"] for n in range(75, 86)]
    assert values == sorted(values), "sleep must trend up (risk trends down)"
    assert values[0] > S.PERSONA_SLEEP_DIP_HOURS
    assert values[-1] == S.PERSONA_RECOVERY_TARGET_HOURS


def test_days_85_to_90_green(by_day):
    for n in range(85, 91):
        assert by_day["passive"][n]["sleep_hours_proxy"] == S.PERSONA_RECOVERY_TARGET_HOURS, n
        assert by_day["checkin"][n]["mood_score"] >= S.PERSONA_MOOD_SCORE_RECOVERED, n
    assert consecutive_duty_days(90) < 60, "a 60-day streak cannot be Green"


def test_full_run_contains_the_same_persona_rows(persona_ds):
    """--persona-only and the full population emit identical persona rows."""
    from data import TABLES, canonical

    full = build(seed=42, personnel=120)
    pid = S.PERSONA_PSEUDONYM_ID
    for table in TABLES:
        if table in ("units", "csv_noise"):
            continue
        want = [canonical(r) for r in persona_ds.table(table)]
        got = [
            canonical(r)
            for r in full.table(table)
            if pid in (r.get("pseudonym_id"), r.get("principal_pseudonym"))
            or r.get("incident_id") == S.PERSONA_INCIDENT_ID
        ]
        assert want == got, table


def test_arc_evidence_is_complete(persona_ds):
    evidence = arc_evidence(persona_ds)
    assert evidence["roster_days"] == S.ARC_DAYS
    assert evidence["streak_at_day_60"] == 60
    assert evidence["sleep_deviation_at_dip"] == -0.30
    assert evidence["recovery_monotonic"] is True
    assert sleep_hours(S.ARC_DAYS) == S.PERSONA_RECOVERY_TARGET_HOURS
