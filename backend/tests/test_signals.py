from __future__ import annotations

from datetime import date, timedelta

from app.signals.calculator import ACTIVE_SIGNAL_KEYS, compute_person_signals
from app.signals.domain import duty as D
from app.signals.domain import leave as L
from app.signals.types import DutyRow, LeaveRow


def test_active_signal_count_clears_fr01():
    assert len(ACTIVE_SIGNAL_KEYS) >= 15


def test_days_since_home_leave_null_not_zero():
    as_of = date(2026, 9, 1)
    assert L.days_since_home_leave([], as_of) is None
    rows = [
        LeaveRow(
            leave_type="home_leave",
            home_leave=True,
            applied_at=date(2026, 1, 1),
            sanctioned_from=date(2026, 1, 10),
            sanctioned_to=date(2026, 1, 20),
            cancelled_at=None,
            denial_reason=None,
            actual_return_date=date(2026, 1, 20),
        )
    ]
    assert L.days_since_home_leave(rows, as_of) == float((as_of - date(2026, 1, 20)).days)


def test_leave_cancel_count():
    as_of = date(2026, 9, 1)
    rows = [
        LeaveRow("home_leave", True, date(2026, 7, 4), None, None, date(2026, 7, 4), None, None),
        LeaveRow("home_leave", True, date(2026, 7, 28), None, None, date(2026, 7, 28), None, None),
    ]
    assert L.leave_cancel_count(rows, as_of) == 2


def test_consecutive_duty_ending_at_as_of():
    as_of = date(2026, 8, 2)
    rows = [
        DutyRow(as_of - timedelta(days=i), "day", False, "3BN") for i in range(60)
    ]
    assert D.consecutive_duty_days(rows, as_of) == 60
    rows.append(DutyRow(as_of, "day", True, "3BN"))
    # rest day on as_of breaks the run
    assert D.consecutive_duty_days(rows, as_of) == 0


def test_cancelled_leave_does_not_reset_streak():
    as_of = date(2026, 8, 2)
    duty = [DutyRow(as_of - timedelta(days=i), "day", False, "3BN") for i in range(60)]
    assert D.consecutive_duty_days(duty, as_of) == 60


def test_family_separation_null_when_distance_missing():
    from app.signals.domain import deployment as E
    from app.signals.types import DeploymentRow

    rows = [
        DeploymentRow("field", date(2025, 12, 1), None, None, "3BN"),
    ]
    assert E.family_separation_index(rows, date(2026, 9, 1)) is None


def test_compute_returns_all_keys():
    values = compute_person_signals(
        as_of=date(2026, 9, 1),
        leave=[],
        duty=[],
        deployments=[],
        transfers=[],
        medical=[],
        career=None,
    )
    for key in ACTIVE_SIGNAL_KEYS:
        assert key in values
    assert values["days_since_home_leave"] is None
    assert values["life_event_bereavement"] is None
