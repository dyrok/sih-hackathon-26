from __future__ import annotations

from datetime import date, timedelta

from ..types import LeaveRow


def _in_window(d: date, window_start: date, as_of: date) -> bool:
    return window_start <= d <= as_of


def days_since_home_leave(records: list[LeaveRow], as_of: date) -> float | None:
    completed = [
        r
        for r in records
        if (r.home_leave or r.leave_type == "home_leave")
        and r.cancelled_at is None
        and r.denial_reason is None
        and r.sanctioned_to is not None
        and r.sanctioned_to <= as_of
    ]
    if not completed:
        return None
    last = max(r.sanctioned_to for r in completed if r.sanctioned_to is not None)
    return float((as_of - last).days)


def leave_cancel_count(records: list[LeaveRow], as_of: date, window_days: int = 90) -> float:
    start = as_of - timedelta(days=window_days)
    n = 0
    for r in records:
        if r.cancelled_at is None:
            continue
        if _in_window(r.cancelled_at, start, as_of) or _in_window(r.applied_at, start, as_of):
            n += 1
    return float(n)


def leave_denial_count(records: list[LeaveRow], as_of: date, window_days: int = 90) -> float:
    start = as_of - timedelta(days=window_days)
    n = 0
    for r in records:
        if not r.denial_reason:
            continue
        if r.cancelled_at is not None:
            continue
        if _in_window(r.applied_at, start, as_of):
            n += 1
    return float(n)


def early_return_days(records: list[LeaveRow], as_of: date, window_days: int = 90) -> float:
    start = as_of - timedelta(days=window_days)
    total = 0
    for r in records:
        if r.sanctioned_from is None or r.sanctioned_to is None or r.actual_return_date is None:
            continue
        if r.cancelled_at is not None:
            continue
        if not _in_window(r.applied_at, start, as_of) and not _in_window(r.actual_return_date, start, as_of):
            continue
        sanctioned = (r.sanctioned_to - r.sanctioned_from).days + 1
        actual = (r.actual_return_date - r.sanctioned_from).days + 1
        if actual < sanctioned:
            total += sanctioned - actual
    return float(total)
