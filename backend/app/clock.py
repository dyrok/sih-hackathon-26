from __future__ import annotations

from datetime import date

from .config import get_settings

_override: date | None = None


def set_as_of(value: date | None) -> None:
    global _override
    _override = value


def as_of() -> date:
    if _override is not None:
        return _override
    return get_settings().as_of_date()


#: How far back a legitimately offline device may have been (ADR-0005). A
#: capture date outside this window is clamped, never trusted: `expires_at` is
#: derived from the clamped date, so a client cannot mint an immortal row by
#: posting a future `recorded_at` (TC-455).
OFFLINE_WINDOW_DAYS = 30


def clamp_capture_date(raw, today):
    from datetime import date as _date, timedelta as _timedelta

    if not raw:
        return today
    try:
        value = _date.fromisoformat(str(raw)[:10])
    except ValueError:
        return today
    earliest = today - _timedelta(days=OFFLINE_WINDOW_DAYS)
    if value > today:
        return today
    if value < earliest:
        return earliest
    return value
