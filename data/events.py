"""90-day HR event streams: leaves, duty rosters, deployments, transfers, training.

Row shapes are the backend's tables (``backend/app/models.py``) with the CSV
column names from ``backend/app/ingest/schemas.py`` — one shape serves both
writers. Everything is drawn from per-personnel RNG streams namespaced by
purpose (``"roster"``, ``"leave"``, ...) so a change to one stream cannot move
another.

Training courses are emitted both as their own event list (for the run summary)
and as roster rows with ``rest_day=true`` — that is what makes a course "reset
the duty streak" for ``consecutive_duty_days`` (F01), without inventing a table
the backend does not have.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from . import did, rng_for
from . import spec as S
from .population import Person, Population, pick_index, pick_weighted


@dataclass
class PersonHr:
    leave: List[Dict[str, Any]] = field(default_factory=list)
    roster: List[Dict[str, Any]] = field(default_factory=list)
    deployment: List[Dict[str, Any]] = field(default_factory=list)
    transfer: List[Dict[str, Any]] = field(default_factory=list)
    training: List[Dict[str, Any]] = field(default_factory=list)
    medical: List[Dict[str, Any]] = field(default_factory=list)
    career: List[Dict[str, Any]] = field(default_factory=list)
    #: arc day number -> roster row, for the passive/self-report models
    roster_by_day: Dict[int, Dict[str, Any]] = field(default_factory=dict)


def _iso(value: Optional[date]) -> Optional[str]:
    return value.isoformat() if value is not None else None


def leave_row(person: Person, **kw: Any) -> Dict[str, Any]:
    row = {
        "personnel_id": person.personnel_id,
        "pseudonym_id": person.pseudonym_id,
        "leave_type": kw["leave_type"],
        "home_leave": bool(kw.get("home_leave", kw["leave_type"] == "home_leave")),
        "applied_at": _iso(kw["applied_at"]),
        "sanctioned_from": _iso(kw.get("sanctioned_from")),
        "sanctioned_to": _iso(kw.get("sanctioned_to")),
        "cancelled_at": _iso(kw.get("cancelled_at")),
        "denial_reason": kw.get("denial_reason"),
        "actual_return_date": _iso(kw.get("actual_return_date")),
    }
    row["id"] = did("lv", person.pseudonym_id, row["applied_at"], row["leave_type"])
    return row


def roster_row(person: Person, duty_date: date, shift_code: str, rest_day: bool) -> Dict[str, Any]:
    return {
        "id": did("dt", person.pseudonym_id, duty_date.isoformat()),
        "personnel_id": person.personnel_id,
        "pseudonym_id": person.pseudonym_id,
        "unit_id": person.unit_id,
        "duty_date": duty_date.isoformat(),
        "shift_code": shift_code,
        "rest_day": rest_day,
    }


# ---------------------------------------------------------------------------
# Duty roster
# ---------------------------------------------------------------------------


def _shift_blocks(rng, n_blocks: int) -> List[str]:
    shift = pick_weighted(rng, S.SHIFT_BLOCK_SHARES)
    blocks = [shift]
    idx = S.SHIFT_CODES.index(shift)
    for _ in range(1, n_blocks):
        if rng.random() < S.SHIFT_BLOCK_CHANGE_PROB_BY_SHIFT[S.SHIFT_CODES[idx]]:
            step = -1 if rng.random() < S.BACKWARD_ROTATION_PROB else 1
            idx = (idx + step) % len(S.SHIFT_CODES)
        blocks.append(S.SHIFT_CODES[idx])
    return blocks


def build_roster(seed: int, person: Person) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Set[int]]:
    """Return ``(roster_rows, training_rows, leave_days)`` for the 90-day arc."""
    rng = rng_for(seed, "roster", person.pseudonym_id)
    amber = person.cohort == S.COHORT_AMBER

    n_blocks = (S.ARC_DAYS + S.ROTATION_BLOCK_DAYS - 1) // S.ROTATION_BLOCK_DAYS
    blocks = _shift_blocks(rng, n_blocks)
    rest_offset = rng.randrange(S.ROTATION_BLOCK_DAYS)

    # In-window leave (baseline only) — days off the roster.
    leave_days: Set[int] = set()
    if not amber and rng.random() < S.IN_WINDOW_LEAVE_PROB:
        start = rng.randint(*S.IN_WINDOW_LEAVE_START_DAY_RANGE)
        length = rng.randint(*S.IN_WINDOW_LEAVE_LENGTH_RANGE)
        leave_days = set(range(start, min(S.ARC_DAYS, start + length - 1) + 1))

    # Training course — resets the duty streak.
    training_days: Set[int] = set()
    training_rows: List[Dict[str, Any]] = []
    if not amber and rng.random() < S.TRAINING_PROB:
        start = rng.randint(*S.TRAINING_START_DAY_RANGE)
        length = rng.randint(*S.TRAINING_DAYS_RANGE)
        end = min(S.ARC_DAYS, start + length - 1)
        training_days = set(range(start, end + 1))
        if training_days & leave_days:
            training_days = set()
        else:
            course = rng.choice(S.TRAINING_COURSES)
            training_rows.append(
                {
                    "id": did("tr", person.pseudonym_id, S.day(start).isoformat()),
                    "personnel_id": person.personnel_id,
                    "pseudonym_id": person.pseudonym_id,
                    "unit_id": person.unit_id,
                    "course": course,
                    "start_date": S.day(start).isoformat(),
                    "end_date": S.day(end).isoformat(),
                }
            )

    # Amber cohort: an unbroken stretch ending at day 90 plus a night-heavy block.
    streak_from = S.ARC_DAYS + 1
    night_days: Set[int] = set()
    if amber:
        streak_from = S.ARC_DAYS - rng.randint(*S.AMBER_STREAK_DAYS_RANGE) + 1
        n_start = rng.randint(*S.AMBER_NIGHT_BLOCK_START_DAY_RANGE)
        n_len = rng.randint(*S.AMBER_NIGHT_BLOCK_DAYS_RANGE)
        night_days = set(range(n_start, min(S.ARC_DAYS, n_start + n_len - 1) + 1))

    rows: List[Dict[str, Any]] = []
    for n in range(1, S.ARC_DAYS + 1):
        if rng.random() < S.ROSTER_MISSING_DAY_RATE:
            continue                                    # connectivity gap (ADR-0005)
        d = S.day(n)
        if n in leave_days or n in training_days:
            rows.append(roster_row(person, d, "day", True))
            continue
        scheduled_rest = ((n + rest_offset) % S.ROTATION_BLOCK_DAYS) == 0
        if scheduled_rest and n < streak_from and rng.random() >= S.REST_DAY_CANCELLED_PROB:
            rows.append(roster_row(person, d, "day", True))
            continue
        shift = "night" if n in night_days else blocks[(n - 1) // S.ROTATION_BLOCK_DAYS]
        if rng.random() < S.PT_ABSENT_RATE:
            shift = "pt_absent"
        rows.append(roster_row(person, d, shift, False))
    return rows, training_rows, leave_days


# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------


def build_leave(seed: int, person: Person, leave_days: Set[int]) -> List[Dict[str, Any]]:
    rng = rng_for(seed, "leave", person.pseudonym_id)
    amber = person.cohort == S.COHORT_AMBER
    rows: List[Dict[str, Any]] = []
    used: Set[Tuple[str, str]] = set()

    def add(**kw: Any) -> None:
        row = leave_row(person, **kw)
        key = (row["applied_at"], row["leave_type"])
        if key in used:
            return                                       # natural key collision
        used.add(key)
        rows.append(row)

    # 1. The last completed home leave, before day 1 (sets days_since_home_leave).
    gap = rng.randint(*S.HOME_LEAVE_GAP_DAYS_RANGE)
    if amber:
        gap = max(gap, S.HOME_LEAVE_GAP_DAYS_RANGE[1] - 40)
    length = rng.randint(*S.HOME_LEAVE_LENGTH_DAYS_RANGE)
    sanctioned_to = S.ARC_START - timedelta(days=gap)
    sanctioned_from = sanctioned_to - timedelta(days=length - 1)
    applied_at = sanctioned_from - timedelta(days=rng.randint(*S.LEAVE_APPLY_LEAD_DAYS_RANGE))
    returned = sanctioned_to
    if rng.random() < S.EARLY_RETURN_PROB:
        returned = sanctioned_to - timedelta(days=rng.randint(*S.EARLY_RETURN_DAYS_RANGE))
    add(
        leave_type="home_leave",
        applied_at=applied_at,
        sanctioned_from=sanctioned_from,
        sanctioned_to=sanctioned_to,
        actual_return_date=returned,
    )

    # 2. The in-window leave the roster already carved out.
    if leave_days:
        start_n, end_n = min(leave_days), max(leave_days)
        leave_type = pick_weighted(rng, S.IN_WINDOW_LEAVE_TYPE_SHARES)
        s_from, s_to = S.day(start_n), S.day(end_n)
        applied = s_from - timedelta(days=rng.randint(*S.LEAVE_APPLY_LEAD_DAYS_RANGE))
        returned = s_to
        if rng.random() < S.EARLY_RETURN_PROB:
            returned = s_to - timedelta(days=rng.randint(*S.EARLY_RETURN_DAYS_RANGE))
        add(
            leave_type=leave_type,
            applied_at=applied,
            sanctioned_from=s_from,
            sanctioned_to=s_to,
            actual_return_date=returned,
        )

    # 3. Cancellations — the silent HR signal (F09 persona day 31 / day 55).
    shares = S.CANCEL_SHARES_AMBER if amber else S.CANCEL_SHARES_BASELINE
    for _ in range(pick_index(rng, shares)):
        n = rng.randint(*S.CANCEL_DAY_RANGE)
        applied = S.day(n)
        cancelled = applied + timedelta(days=rng.randint(*S.CANCEL_LAG_DAYS_RANGE))
        add(leave_type="home_leave", applied_at=applied, cancelled_at=cancelled)

    # 4. Denials.
    denial_prob = S.DENIAL_PROB_AMBER if amber else S.DENIAL_PROB_BASELINE
    if rng.random() < denial_prob:
        applied = S.day(rng.randint(*S.DENIAL_DAY_RANGE))
        add(
            leave_type="casual",
            applied_at=applied,
            denial_reason=rng.choice(S.DENIAL_REASONS),
        )
    return rows


# ---------------------------------------------------------------------------
# Deployment / transfer / medical / career
# ---------------------------------------------------------------------------


def build_deployments(seed: int, person: Person) -> List[Dict[str, Any]]:
    rng = rng_for(seed, "deployment", person.pseudonym_id)
    posting = pick_weighted(rng, S.POSTING_TYPE_SHARES)
    if person.cohort == S.COHORT_AMBER and posting == "static":
        posting = "internal_security"
    start = S.ARC_START - timedelta(days=rng.randint(*S.POSTING_START_BEFORE_ARC_DAYS_RANGE))
    rows = [
        {
            "id": did("dp", person.pseudonym_id, start.isoformat(), posting),
            "personnel_id": person.personnel_id,
            "pseudonym_id": person.pseudonym_id,
            "unit_id": person.unit_id,
            "posting_type": posting,
            "start_date": start.isoformat(),
            "end_date": None,
            "distance_km": person.home_distance_km,
        }
    ]
    if rng.random() < S.PRIOR_POSTING_PROB:
        prior_end = start - timedelta(days=rng.randint(5, 40))
        prior_len = rng.randint(*S.PRIOR_POSTING_LENGTH_DAYS_RANGE)
        prior_start = prior_end - timedelta(days=prior_len)
        prior_type = "static" if posting != "static" else "internal_security"
        if (S.ARC_START - prior_start).days <= S.PRE_ARC_LOOKBACK_DAYS:
            rows.append(
                {
                    "id": did("dp", person.pseudonym_id, prior_start.isoformat(), prior_type),
                    "personnel_id": person.personnel_id,
                    "pseudonym_id": person.pseudonym_id,
                    "unit_id": person.unit_id,
                    "posting_type": prior_type,
                    "start_date": prior_start.isoformat(),
                    "end_date": prior_end.isoformat(),
                    "distance_km": round(person.home_distance_km * 0.6, 0),
                }
            )
    return rows


def build_transfers(seed: int, person: Person) -> List[Dict[str, Any]]:
    rng = rng_for(seed, "transfer", person.pseudonym_id)
    count = pick_index(rng, S.TRANSFER_COUNT_SHARES)
    others = [b for b in S.BATTALION_IDS if b != person.battalion_id]
    rows: List[Dict[str, Any]] = []
    used: Set[Tuple[str, str, str]] = set()
    to_unit = person.battalion_id
    for _ in range(count):
        effective = S.ARC_END - timedelta(days=rng.randint(1, S.TRANSFER_WITHIN_DAYS))
        from_unit = rng.choice(others)
        key = (effective.isoformat(), from_unit, to_unit)
        if key in used:
            continue
        used.add(key)
        rows.append(
            {
                "id": did("xf", person.pseudonym_id, *key),
                "personnel_id": person.personnel_id,
                "pseudonym_id": person.pseudonym_id,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "effective_date": effective.isoformat(),
                "reason_code": rng.choice(S.TRANSFER_REASON_CODES),
            }
        )
        to_unit = from_unit                              # walk the chain backwards
    return rows


def build_medical(seed: int, person: Person) -> List[Dict[str, Any]]:
    rng = rng_for(seed, "medical", person.pseudonym_id)
    n = pick_index(rng, S.MEDICAL_VISITS_SHARES)
    if person.cohort == S.COHORT_AMBER:
        n += S.AMBER_MEDICAL_VISIT_BONUS
    rows: List[Dict[str, Any]] = []
    used: Set[Tuple[str, str]] = set()
    for _ in range(n):
        d = S.day(rng.randint(1, S.ARC_DAYS))
        visit_type = pick_weighted(rng, S.MEDICAL_VISIT_TYPE_SHARES)
        key = (d.isoformat(), visit_type)
        if key in used:
            continue
        used.add(key)
        rows.append(
            {
                "id": did("md", person.pseudonym_id, *key),
                "personnel_id": person.personnel_id,
                "pseudonym_id": person.pseudonym_id,
                "visit_date": d.isoformat(),
                "visit_type": visit_type,
                "injury_flag": visit_type == "injury",
            }
        )
    return rows


def build_career(seed: int, person: Person) -> List[Dict[str, Any]]:
    rng = rng_for(seed, "career", person.pseudonym_id)
    amber = person.cohort == S.COHORT_AMBER
    pending_months = float(S.CAREER_NUMERIC_NULL_SUBSTITUTE)
    if rng.random() < S.PROMOTION_PENDING_PROB:
        pending_months = round(rng.uniform(*S.PROMOTION_PENDING_MONTHS_RANGE), 1)
    inquiry_prob = S.INQUIRY_PENDING_PROB_AMBER if amber else S.INQUIRY_PENDING_PROB_BASELINE
    inquiry = rng.random() < inquiry_prob
    return [
        {
            "personnel_id": person.personnel_id,
            "pseudonym_id": person.pseudonym_id,
            "promotion_board_pending_months": pending_months,
            "inquiry_court_pending": inquiry,
            "inquiry_age_days": (
                rng.randint(*S.INQUIRY_AGE_DAYS_RANGE)
                if inquiry
                else S.CAREER_NUMERIC_NULL_SUBSTITUTE
            ),
            "denied_training_count_12m": pick_index(rng, S.DENIED_TRAINING_SHARES),
        }
    ]


def generate_person_hr(seed: int, person: Person) -> PersonHr:
    roster, training, leave_days = build_roster(seed, person)
    hr = PersonHr(
        leave=build_leave(seed, person, leave_days),
        roster=roster,
        deployment=build_deployments(seed, person),
        transfer=build_transfers(seed, person),
        training=training,
        medical=build_medical(seed, person),
        career=build_career(seed, person),
    )
    hr.roster_by_day = dict(
        (S.day_number(date.fromisoformat(r["duty_date"])), r) for r in roster
    )
    return hr


# ---------------------------------------------------------------------------
# Unit-level incidents (FR-08) — attached to a unit, never to a person
# ---------------------------------------------------------------------------


def build_incidents(seed: int, population: Population) -> List[Dict[str, Any]]:
    rng = rng_for(seed, "incident")
    units = sorted({p.battalion_id for p in population.people})
    if not units:
        return []
    rows: List[Dict[str, Any]] = []
    for i in range(min(S.INCIDENT_COUNT, len(units))):
        unit_id = units[i % len(units)]
        n = rng.randint(*S.INCIDENT_DAY_RANGE)
        incident_type = rng.choice(S.INCIDENT_TYPES)
        rows.append(
            {
                "incident_id": S.INCIDENT_ID_FORMAT.format(unit=unit_id, seq=i + 1),
                "unit_id": unit_id,
                "incident_type": incident_type,
                "severity_band": rng.choice(S.INCIDENT_SEVERITY_BANDS),
                "incident_date": S.day(n).isoformat(),
                "exposure_window_days": S.INCIDENT_EXPOSURE_WINDOW_DAYS,
            }
        )
    return rows
