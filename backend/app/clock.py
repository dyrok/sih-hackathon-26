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
