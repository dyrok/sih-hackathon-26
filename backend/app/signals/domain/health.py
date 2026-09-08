from __future__ import annotations

from datetime import date, timedelta

from ..types import DutyRow, MedicalRow


def sick_report_freq(records: list[MedicalRow], as_of: date, window_days: int = 30) -> float:
    start = as_of - timedelta(days=window_days - 1)
    n = sum(1 for r in records if start <= r.visit_date <= as_of and r.visit_type == "sick_report")
    return float(n)


def pt_absence_unexplained(
    medical: list[MedicalRow],
    duty: list[DutyRow],
    as_of: date,
    window_days: int = 30,
) -> float:
    start = as_of - timedelta(days=window_days - 1)
    med_days = {r.visit_date for r in medical if start <= r.visit_date <= as_of}
    n = 0
    for r in duty:
        if not (start <= r.duty_date <= as_of):
            continue
        if r.shift_code == "pt_absent" and r.duty_date not in med_days:
            n += 1
    return float(n)


def medical_visit_trend(records: list[MedicalRow], as_of: date) -> float | None:
    months: dict[tuple[int, int], int] = {}
    start = as_of - timedelta(days=90)
    for r in records:
        if r.visit_date < start or r.visit_date > as_of:
            continue
        key = (r.visit_date.year, r.visit_date.month)
        months[key] = months.get(key, 0) + 1
    if len(months) < 2:
        return None
    keys = sorted(months)
    ys = [months[k] for k in keys]
    n = len(ys)
    xs = list(range(n))
    xbar = sum(xs) / n
    ybar = sum(ys) / n
    num = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    den = sum((x - xbar) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return float(num / den)


def days_since_injury(records: list[MedicalRow], as_of: date) -> float | None:
    injured = [r.visit_date for r in records if r.injury_flag and r.visit_date <= as_of]
    if not injured:
        return None
    return float((as_of - max(injured)).days)
