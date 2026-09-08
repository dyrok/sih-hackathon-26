from __future__ import annotations

from datetime import date, timedelta

from ..types import DutyRow

_SHIFT_ORDER = {"day": 0, "evening": 1, "night": 2}


def consecutive_duty_days(records: list[DutyRow], as_of: date) -> float:
    by_day = {r.duty_date: r for r in records}
    cur = as_of
    run = 0
    while True:
        row = by_day.get(cur)
        if row is None or row.rest_day:
            break
        run += 1
        cur = cur - timedelta(days=1)
    return float(run)


def night_shift_ratio(records: list[DutyRow], as_of: date, window_days: int = 30) -> float | None:
    start = as_of - timedelta(days=window_days - 1)
    rows = [r for r in records if start <= r.duty_date <= as_of and not r.rest_day]
    if not rows:
        return None
    nights = sum(1 for r in rows if r.shift_code == "night")
    return nights / len(rows)


def rotation_speed_direction(records: list[DutyRow], as_of: date, window_days: int = 30) -> float | None:
    start = as_of - timedelta(days=window_days - 1)
    rows = sorted(
        (r for r in records if start <= r.duty_date <= as_of and not r.rest_day),
        key=lambda r: r.duty_date,
    )
    if len(rows) < 2:
        return None
    changes = 0
    forward = 0
    backward = 0
    prev = rows[0].shift_code
    for r in rows[1:]:
        if r.shift_code != prev:
            changes += 1
            a = _SHIFT_ORDER.get(prev, 0)
            b = _SHIFT_ORDER.get(r.shift_code, 0)
            delta = (b - a) % 3
            if delta == 1:
                forward += 1
            elif delta == 2:
                backward += 1
            prev = r.shift_code
        else:
            prev = r.shift_code
    weeks = window_days / 7.0
    speed = changes / weeks
    sign = -1.0 if backward > forward else 1.0
    return sign * speed


def circadian_disruption_score(
    records: list[DutyRow],
    as_of: date,
    backward_weight: float = 1.3,
) -> float | None:
    nr = night_shift_ratio(records, as_of)
    rot = rotation_speed_direction(records, as_of)
    if nr is None or rot is None:
        return None
    speed = abs(rot)
    norm_night = min(1.0, nr)
    norm_rot = min(1.0, speed / 4.0)
    direction_weight = backward_weight if rot < 0 else 1.0
    return max(0.0, min(1.0, norm_night * norm_rot * direction_weight))
