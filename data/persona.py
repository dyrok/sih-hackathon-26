"""DEMO-PERSONA-01 — the scripted 90-day arc (F09 §"The scripted persona").

Constable, 34, 3rd Bn. Script-driven, not sampled: the flag days are a contract
the rules engine must hit ([ADR-0001] validation), so nothing in this module
consumes an RNG at all — the persona is byte-identical for every seed.

Agreement with ``backend/app/seed.py``
--------------------------------------
Ids (``CR-DEMO-01`` / ``ps_demo01``), unit (``3BN``), rank, age, the three leave
records, the deployment, both transfers, the incident and the day 1-67 duty /
sleep / check-in series are reproduced **verbatim** from kv's seed, on the same
natural keys, so writing either way is idempotent and kv's ML-002 harness
(days 30 / 62 / 64 / 65) is untouched.

Days 68-90 add the half of the F09 arc kv's seed does not model: the approved
roster swap relieves the duty load, sleep trends back to baseline over days
75-85, and the arc closes Green at days 85-90.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from . import Dataset, did
from . import spec as S
from .population import persona_person


@dataclass(frozen=True)
class ArcStep:
    """One row of the F09 arc table."""

    day_from: int
    day_to: int
    event: str
    expected: str

    @property
    def day_label(self) -> str:
        if self.day_from == self.day_to:
            return str(self.day_from)
        return "{0}-{1}".format(self.day_from, self.day_to)

    @property
    def date_label(self) -> str:
        if self.day_from == self.day_to:
            return S.day(self.day_from).isoformat()
        return "{0}..{1}".format(S.day(self.day_from).isoformat(), S.day(self.day_to).isoformat())

    def as_tuple(self) -> Tuple[int, int, str, str]:
        return (self.day_from, self.day_to, self.event, self.expected)


#: The F09 table, transcribed. TC-502 diffs this against the doc, day for day.
ARC: Tuple[ArcStep, ...] = (
    ArcStep(1, 30, "Normal roster; one leave taken and returned",
            "Green; baselines established"),
    ArcStep(S.PERSONA_CANCEL_DAY_1, S.PERSONA_CANCEL_DAY_1,
            "Leave application cancelled (#1)", "silent HR signal"),
    ArcStep(S.PERSONA_NIGHT_DAYS[0], S.PERSONA_NIGHT_DAYS[1],
            "Rotation to night-heavy duty", "circadian score rises"),
    ArcStep(S.PERSONA_CANCEL_DAY_2, S.PERSONA_CANCEL_DAY_2,
            "Leave cancelled (#2)", "silent HR signal"),
    ArcStep(58, 60, "60 consecutive duty days; sleep proxy -30% vs baseline",
            "baseline breach accumulates"),
    ArcStep(S.PERSONA_AMBER_DAY, S.PERSONA_AMBER_DAY,
            "Amber flag -> buddy nudge + JCO informal check",
            "first visible intervention (F05)"),
    ArcStep(S.PERSONA_MASKING_DAY, S.PERSONA_MASKING_DAY,
            "Voluntary check-in says \"I'm fine\" despite signals",
            "masking flag (FR-07)"),
    ArcStep(S.PERSONA_RED_DAY, S.PERSONA_RED_DAY,
            "Red flag with explanation factors", "counsellor outreach task, <= 24 h SLA"),
    ArcStep(S.PERSONA_UNMASK_DAY, S.PERSONA_UNMASK_DAY,
            "Dual-key unmask (counsellor + welfare officer) - logged",
            "subject sees it in who-viewed-my-data"),
    ArcStep(S.PERSONA_ROSTER_RELIEF_DAYS[0], S.PERSONA_ROSTER_RELIEF_DAYS[1],
            "Roster swap proposed & approved; duty load drops",
            "intervention recorded (F06)"),
    ArcStep(S.PERSONA_RECOVERY_DAYS[0], S.PERSONA_RECOVERY_DAYS[1],
            "Trend down; check-ins stabilize", "risk trend decreases"),
    ArcStep(S.PERSONA_GREEN_DAYS[0], S.PERSONA_GREEN_DAYS[1],
            "Green", "loop closed - arc printed in the run summary"),
)


# ---------------------------------------------------------------------------
# Scripted series
# ---------------------------------------------------------------------------


def is_night_day(n: int) -> bool:
    lo, hi = S.PERSONA_NIGHT_DAYS
    return lo <= n <= hi


def is_rest_day(n: int) -> bool:
    """Rest only after the approved roster swap — a cancelled leave never rests."""
    lo, hi = S.PERSONA_ROSTER_RELIEF_DAYS
    if lo <= n <= hi:
        return True
    if n >= S.PERSONA_WEEKLY_REST_FROM_DAY and n % S.PERSONA_REST_EVERY_N_DAYS == 0:
        return True
    return False


def sleep_hours(n: int) -> float:
    """The scripted sleep proxy: 7.0 h baseline, -30% from day 56, recovery 75-85."""
    if n == S.PERSONA_MASKING_DAY:
        return S.PERSONA_MASKING_SLEEP_HOURS
    if n < S.PERSONA_SLEEP_DIP_START_DAY:
        return S.PERSONA_SLEEP_BASELINE_HOURS
    r_from, r_to = S.PERSONA_RECOVERY_DAYS
    if n < r_from:
        return S.PERSONA_SLEEP_DIP_HOURS
    if n >= r_to:
        return S.PERSONA_RECOVERY_TARGET_HOURS
    span = r_to - (r_from - 1)
    step = (S.PERSONA_RECOVERY_TARGET_HOURS - S.PERSONA_SLEEP_DIP_HOURS) / span
    return round(S.PERSONA_SLEEP_DIP_HOURS + step * (n - (r_from - 1)), S.SLEEP_ROUND_DP)


def mood_score(n: int) -> int:
    if n == S.PERSONA_MASKING_DAY:
        return S.PERSONA_MOOD_SCORE_MASKING
    if n >= S.PERSONA_RECOVERY_MOOD_SWITCH_DAY:
        return S.PERSONA_MOOD_SCORE_RECOVERED
    return S.PERSONA_MOOD_SCORE_NORMAL


def consecutive_duty_days(n: int) -> int:
    """Duty-streak length on arc day ``n``, mirroring F01's definition."""
    run = 0
    cur = n
    while cur >= 1 and not is_rest_day(cur):
        run += 1
        cur -= 1
    return run


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------


def _leave(pid: str, personnel_id: str, **kw: Any) -> Dict[str, Any]:
    applied = kw["applied_at"].isoformat()
    leave_type = kw.get("leave_type", "home_leave")
    return {
        "id": did("lv", pid, applied, leave_type),
        "personnel_id": personnel_id,
        "pseudonym_id": pid,
        "leave_type": leave_type,
        "home_leave": True,
        "applied_at": applied,
        "sanctioned_from": kw["sanctioned_from"].isoformat() if kw.get("sanctioned_from") else None,
        "sanctioned_to": kw["sanctioned_to"].isoformat() if kw.get("sanctioned_to") else None,
        "cancelled_at": kw["cancelled_at"].isoformat() if kw.get("cancelled_at") else None,
        "denial_reason": None,
        "actual_return_date": (
            kw["actual_return_date"].isoformat() if kw.get("actual_return_date") else None
        ),
    }


def build_persona() -> Dataset:
    """The complete scripted persona payload."""
    person = persona_person()
    pid = person.pseudonym_id
    personnel_id = person.personnel_id
    ds = Dataset(persona_only=True)
    ds.personnel.append(person.to_row())
    ds.units.append(
        {"unit_id": person.battalion_id, "level": "battalion", "parent_id": None, "size": 1}
    )

    # --- duty roster: 90 days, night-heavy 40-50, relief 68-70 ------------
    for n in range(1, S.ARC_DAYS + 1):
        d = S.day(n)
        ds.roster.append(
            {
                "id": did("dt", pid, d.isoformat()),
                "personnel_id": personnel_id,
                "pseudonym_id": pid,
                "unit_id": person.unit_id,
                "duty_date": d.isoformat(),
                "shift_code": "night" if is_night_day(n) else "day",
                "rest_day": is_rest_day(n),
            }
        )

    # --- leave: one completed home leave + two cancellations --------------
    ds.leave.append(
        _leave(
            pid,
            personnel_id,
            applied_at=S.PERSONA_HOME_LEAVE_APPLIED,
            sanctioned_from=S.PERSONA_HOME_LEAVE_FROM,
            sanctioned_to=S.PERSONA_HOME_LEAVE_TO,
            actual_return_date=S.PERSONA_HOME_LEAVE_TO,
        )
    )
    for cancel_day in (S.PERSONA_CANCEL_DAY_1, S.PERSONA_CANCEL_DAY_2):
        ds.leave.append(
            _leave(
                pid,
                personnel_id,
                applied_at=S.day(cancel_day),
                cancelled_at=S.day(cancel_day),
            )
        )

    # --- deployment + transfers ------------------------------------------
    ds.deployment.append(
        {
            "id": did("dp", pid, S.PERSONA_DEPLOYMENT_START.isoformat(), S.PERSONA_DEPLOYMENT_TYPE),
            "personnel_id": personnel_id,
            "pseudonym_id": pid,
            "unit_id": person.unit_id,
            "posting_type": S.PERSONA_DEPLOYMENT_TYPE,
            "start_date": S.PERSONA_DEPLOYMENT_START.isoformat(),
            "end_date": None,
            "distance_km": S.PERSONA_DEPLOYMENT_DISTANCE_KM,
        }
    )
    for from_unit, to_unit, effective, reason in S.PERSONA_TRANSFERS:
        ds.transfer.append(
            {
                "id": did("xf", pid, effective.isoformat(), from_unit, to_unit),
                "personnel_id": personnel_id,
                "pseudonym_id": pid,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "effective_date": effective.isoformat(),
                "reason_code": reason,
            }
        )

    # --- unit incident (group-scoped, FR-08) ------------------------------
    ds.incident.append(
        {
            "incident_id": S.PERSONA_INCIDENT_ID,
            "unit_id": person.unit_id,
            "incident_type": S.PERSONA_INCIDENT_TYPE,
            "severity_band": S.PERSONA_INCIDENT_SEVERITY,
            "incident_date": S.day(S.PERSONA_INCIDENT_DAY).isoformat(),
            "exposure_window_days": S.INCIDENT_EXPOSURE_WINDOW_DAYS,
        }
    )

    # --- career state ------------------------------------------------------
    ds.career.append(
        {
            "personnel_id": personnel_id,
            "pseudonym_id": pid,
            "promotion_board_pending_months": float(S.CAREER_NUMERIC_NULL_SUBSTITUTE),
            "inquiry_court_pending": False,
            "inquiry_age_days": S.CAREER_NUMERIC_NULL_SUBSTITUTE,
            "denied_training_count_12m": 0,
        }
    )

    # --- consent (all three voluntary bundles) ----------------------------
    granted = datetime.combine(
        S.ARC_START - timedelta(days=S.PERSONA_CONSENT_GRANTED_BEFORE_ARC_DAYS),
        S.CONSENT_LOCAL_TIME,
    ).isoformat()
    for bundle in S.CONSENT_BUNDLES:
        ds.consent.append(
            {
                "consent_id": did("cn", pid, bundle),
                "principal_pseudonym": pid,
                "bundle_id": bundle,
                "purpose_string": S.CONSENT_PURPOSE_BY_BUNDLE[bundle],
                "data_categories": list(S.CONSENT_DATA_CATEGORIES[bundle]),
                "language": S.PERSONA_CONSENT_LANGUAGE,
                "consent_version": S.CONSENT_VERSION,
                "granted_at": granted,
                "withdrawn_at": None,
                "artefact_hash": did("h", pid, bundle, granted),
            }
        )

    # --- daily check-ins + passive series ---------------------------------
    for n in range(1, S.ARC_DAYS + 1):
        d = S.day(n)
        hours = sleep_hours(n)
        score = mood_score(n)
        ds.checkin.append(
            {
                "id": did("ck", pid, d.isoformat()),
                "pseudonym_id": pid,
                "recorded_at": d.isoformat(),
                "mood_label": S.MOOD_LABELS[score],
                "mood_score": score,
                "sleep_hours": hours,
                "expires_at": (d + timedelta(days=S.RAW_TTL_DAYS)).isoformat(),
                "purged": False,
            }
        )
        activity = round(
            S.PERSONA_ACTIVITY_BASE
            + (hours - S.PERSONA_SLEEP_BASELINE_HOURS) * S.PERSONA_ACTIVITY_SLEEP_GAIN,
            3,
        )
        ds.passive.append(
            {
                "id": did("pf", pid, d.isoformat()),
                "pseudonym_id": pid,
                "recorded_at": d.isoformat(),
                "sleep_hours_proxy": hours,
                "activity_index": activity,
                "source": "on_device_derived",
            }
        )

    # --- monthly instruments ----------------------------------------------
    for n in sorted(S.PERSONA_INSTRUMENT_SCRIPT):
        d = S.day(n)
        for instrument in S.INSTRUMENTS:
            ds.instrument.append(
                {
                    "id": did("ir", pid, instrument, d.isoformat()),
                    "pseudonym_id": pid,
                    "instrument": instrument,
                    "score": S.PERSONA_INSTRUMENT_SCRIPT[n][instrument],
                    "item_9": 0 if instrument == "PHQ-9" else None,
                    "validity_fail": False,
                    "straight_lining": False,
                    "too_fast": False,
                    "all_max": False,
                    "recorded_at": d.isoformat(),
                    "expires_at": (d + timedelta(days=S.RAW_TTL_DAYS)).isoformat(),
                    "purged": False,
                }
            )
    return ds


# ---------------------------------------------------------------------------
# Arc evidence — what the generated rows actually prove (used by validate.py)
# ---------------------------------------------------------------------------


def arc_evidence(ds: Dataset) -> Dict[str, Any]:
    """Facts the scripted rows must support, keyed by arc claim."""
    pid = S.PERSONA_PSEUDONYM_ID
    roster = dict(
        (S.day_number(_date(r["duty_date"])), r) for r in ds.roster if r["pseudonym_id"] == pid
    )
    checkins = dict(
        (S.day_number(_date(c["recorded_at"])), c) for c in ds.checkin if c["pseudonym_id"] == pid
    )
    passive = dict(
        (S.day_number(_date(p["recorded_at"])), p) for p in ds.passive if p["pseudonym_id"] == pid
    )
    cancels = sorted(
        S.day_number(_date(row["cancelled_at"]))
        for row in ds.leave
        if row["pseudonym_id"] == pid and row["cancelled_at"]
    )
    lo, hi = S.PERSONA_NIGHT_DAYS
    night_days = sorted(n for n, r in roster.items() if r["shift_code"] == "night")
    r_lo, r_hi = S.PERSONA_ROSTER_RELIEF_DAYS
    baseline = S.PERSONA_SLEEP_BASELINE_HOURS
    dip = passive[S.PERSONA_SLEEP_DIP_START_DAY]["sleep_hours_proxy"]
    return {
        "roster_days": len(roster),
        "cancel_days": cancels,
        "night_days": night_days,
        "night_days_expected": list(range(lo, hi + 1)),
        "streak_at_day_60": consecutive_duty_days(S.PERSONA_DUTY_STREAK_CHECK_DAY),
        "sleep_deviation_at_dip": round((dip - baseline) / baseline, 4),
        "masking_mood_score": checkins[S.PERSONA_MASKING_DAY]["mood_score"],
        "masking_mood_label": checkins[S.PERSONA_MASKING_DAY]["mood_label"],
        "masking_sleep_hours": checkins[S.PERSONA_MASKING_DAY]["sleep_hours"],
        "relief_rest_days": [n for n in range(r_lo, r_hi + 1) if roster[n]["rest_day"]],
        "streak_at_day_90": consecutive_duty_days(S.ARC_DAYS),
        "sleep_at_green": passive[S.ARC_DAYS]["sleep_hours_proxy"],
        "recovery_monotonic": _monotonic(
            [passive[n]["sleep_hours_proxy"] for n in range(*_inclusive(S.PERSONA_RECOVERY_DAYS))]
        ),
        "phq9_item9_max": max(
            [
                row["item_9"] or 0
                for row in ds.instrument
                if row["pseudonym_id"] == pid and row["instrument"] == "PHQ-9"
            ]
            or [0]
        ),
    }


def _inclusive(pair: Tuple[int, int]) -> Tuple[int, int]:
    return (pair[0], pair[1] + 1)


def _monotonic(values: List[float]) -> bool:
    return all(b >= a for a, b in zip(values, values[1:]))


def _date(value: str):
    from datetime import date as _d

    return _d.fromisoformat(value)


def arc_table_text(width: int = 78) -> str:
    """The arc table, rendered for ``--dry-run`` (F09 definition of done)."""
    header = "DEMO-PERSONA-01 - {rank}, {age}, 3rd Bn ({pid}) - arc {a}..{b}".format(
        rank=S.PERSONA_RANK,
        age=S.PERSONA_AGE,
        pid=S.PERSONA_PSEUDONYM_ID,
        a=S.ARC_START.isoformat(),
        b=S.ARC_END.isoformat(),
    )
    lines = [header, "-" * max(width, len(header))]
    lines.append(
        "{0:<8} {1:<24} {2:<56} {3}".format("Day(s)", "Date(s)", "Event", "Expected behaviour")
    )
    for step in ARC:
        lines.append(
            "{0:<8} {1:<24} {2:<56} {3}".format(
                step.day_label, step.date_label, step.event, step.expected
            )
        )
    return "\n".join(lines)
