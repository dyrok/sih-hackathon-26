"""Passive signal series — derived features ONLY (ADR-0002).

A passive row may carry a sleep proxy and an activity index. It may never carry
raw audio, a waveform, a recording handle or a transcript: those never leave the
device, so they never exist here either. ``data.spec.PASSIVE_ALLOWED_FIELDS``
and ``FORBIDDEN_FIELD_SUBSTRINGS`` make that a validated property
(``validate.check_no_raw_signals``) rather than a code-review promise.

The sleep series is generated once per person and shared: ``selfreport`` reads
the same series so a jawan's self-reported sleep and the device-derived proxy
agree to within reporting noise, which is what makes the F04 baseline/deviation
rule meaningful.

Passive rows are generated for **everyone**, participants or not — F09 requires
non-participants to still light up the dashboards. The backend's scorer gates
them behind consent anyway (``has_voluntary_consent``), so a non-consenting
person's passive rows never reach a risk score.
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import did, rng_for
from . import spec as S
from .population import Person


def _clamp(value: float, bounds) -> float:
    lo, hi = bounds
    return max(lo, min(hi, value))


def sleep_series(seed: int, person: Person, roster_by_day: Dict[int, Dict[str, Any]]) -> Dict[int, float]:
    """Arc day -> sleep hours, for all 90 days."""
    rng = rng_for(seed, "sleep", person.pseudonym_id)
    baseline = rng.uniform(*S.SLEEP_BASELINE_HOURS_RANGE)
    dip_start = S.ARC_DAYS + 1
    if person.cohort == S.COHORT_AMBER:
        dip_start = rng.randint(*S.AMBER_SLEEP_DIP_START_DAY_RANGE)

    out: Dict[int, float] = {}
    for n in range(1, S.ARC_DAYS + 1):
        hours = baseline + rng.gauss(0.0, S.SLEEP_DAILY_NOISE_HOURS)
        row = roster_by_day.get(n)
        if row is not None:
            if row["rest_day"]:
                hours += S.REST_DAY_SLEEP_BONUS_HOURS
            elif row["shift_code"] == "night":
                hours -= S.NIGHT_SHIFT_SLEEP_PENALTY_HOURS
            elif row["shift_code"] == "evening":
                hours -= S.EVENING_SHIFT_SLEEP_PENALTY_HOURS
        if n >= dip_start:
            hours *= S.AMBER_SLEEP_DIP_MULTIPLIER
        out[n] = round(_clamp(hours, S.SLEEP_HOURS_CLAMP), S.SLEEP_ROUND_DP)
    return out


def activity_index(hours: float, base: float, rng) -> float:
    """Derived 0-1 activity feature — falls with sleep debt."""
    value = base + (hours - 7.0) * 0.05 + rng.gauss(0.0, S.ACTIVITY_INDEX_NOISE)
    return round(_clamp(value, S.ACTIVITY_INDEX_CLAMP), 3)


def build_passive(seed: int, person: Person, series: Dict[int, float]) -> List[Dict[str, Any]]:
    rng = rng_for(seed, "passive", person.pseudonym_id)
    base = rng.uniform(*S.ACTIVITY_INDEX_BASE_RANGE)
    rows: List[Dict[str, Any]] = []
    for n in range(1, S.ARC_DAYS + 1):
        if rng.random() < S.PASSIVE_MISSING_DAY_RATE:
            continue                                     # device off / no sync
        d = S.day(n)
        hours = series[n]
        rows.append(
            {
                "id": did("pf", person.pseudonym_id, d.isoformat()),
                "pseudonym_id": person.pseudonym_id,
                "recorded_at": d.isoformat(),
                "sleep_hours_proxy": hours,
                "activity_index": activity_index(hours, base, rng),
                "source": "on_device_derived",
            }
        )
    return rows
