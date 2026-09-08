from __future__ import annotations

from datetime import date, timedelta

from ...config import get_settings


def unit_incident_exposure(
    incident_date: date,
    exposure_window_days: int,
    as_of: date,
) -> float:
    until = incident_date + timedelta(days=exposure_window_days)
    return 1.0 if incident_date <= as_of <= until else 0.0


def days_since_unit_incident(incident_date: date, as_of: date) -> float:
    return float((as_of - incident_date).days)


def gated_life_event(_name: str) -> float | None:
    """V1–V3 stay off until kv compliance sign-off (F01)."""
    if not get_settings().life_events_enabled:
        return None
    return None
