from __future__ import annotations

from datetime import date, timedelta

from ..types import DeploymentRow


def _overlap_days(start: date, end: date | None, window_start: date, as_of: date) -> int:
    lo = max(start, window_start)
    hi = min(end or as_of, as_of)
    if hi < lo:
        return 0
    return (hi - lo).days + 1


def days_in_high_risk_posting(records: list[DeploymentRow], as_of: date, window_days: int = 90) -> float:
    start = as_of - timedelta(days=window_days - 1)
    total = 0
    for r in records:
        if r.posting_type != "high_risk":
            continue
        total += _overlap_days(r.start_date, r.end_date, start, as_of)
    return float(total)


def family_separation_index(records: list[DeploymentRow], as_of: date) -> float | None:
    current = None
    for r in sorted(records, key=lambda x: x.start_date, reverse=True):
        end = r.end_date or as_of
        if r.start_date <= as_of <= end:
            current = r
            break
    if current is None:
        return None
    if current.distance_km is None:
        return None
    months = max(0.0, (as_of - current.start_date).days / 30.0)
    return float(current.distance_km) * months


def deployment_count_12m(records: list[DeploymentRow], as_of: date) -> float:
    start = as_of - timedelta(days=365)
    n = 0
    for r in records:
        if r.start_date <= as_of and (r.end_date is None or r.end_date >= start):
            if r.start_date >= start or (r.end_date or as_of) >= start:
                n += 1
    return float(n)
