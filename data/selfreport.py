"""Voluntary self-report series — daily check-ins + monthly instruments.

Consent-gated by construction: a person who is not a participant gets **no**
consent artefact, **no** check-in and **no** instrument result. Their HR and
passive series still exist (F09: the dashboard must stay alive), and the
backend's ``has_voluntary_consent`` gate keeps those out of a risk score.

Instrument score ranges mirror the instrument specs referenced in F02 (PHQ-9
0-27, GAD-7 0-21, PSS-10 0-40, ISI 0-28) and every validity-scale item
(``validity_fail`` / ``straight_lining`` / ``too_fast`` / ``all_max``) is
emitted so the F04 masking overlay has something to detect.

TC-407 fixture: a slice of participants silently withdraw consent mid-arc —
their artefacts carry ``withdrawn_at`` while their earlier rows stay put, which
is exactly the "nothing changes visually" case the firewall suite tests.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from . import did, rng_for
from . import spec as S
from .population import Person, pick_weighted


def _consent_datetime(offset_days: int) -> str:
    stamp = datetime.combine(S.ARC_START - timedelta(days=offset_days), S.CONSENT_LOCAL_TIME)
    return stamp.isoformat()


def build_consent(seed: int, person: Person) -> List[Dict[str, Any]]:
    """One artefact per voluntary bundle. Non-participants get none."""
    if not person.participant:
        return []
    rng = rng_for(seed, "consent", person.pseudonym_id)
    language = pick_weighted(rng, S.CONSENT_LANGUAGES)
    granted = _consent_datetime(rng.randint(*S.CONSENT_GRANT_BEFORE_ARC_DAYS_RANGE))
    withdrawn: Optional[str] = None
    if person.cohort != S.COHORT_PERSONA and rng.random() < S.SILENT_WITHDRAWAL_RATE:
        n = rng.randint(*S.SILENT_WITHDRAWAL_DAY_RANGE)
        withdrawn = datetime.combine(S.day(n), S.CONSENT_LOCAL_TIME).isoformat()
    rows: List[Dict[str, Any]] = []
    for bundle in S.CONSENT_BUNDLES:
        rows.append(
            {
                "consent_id": did("cn", person.pseudonym_id, bundle),
                "principal_pseudonym": person.pseudonym_id,
                "bundle_id": bundle,
                "purpose_string": S.CONSENT_PURPOSE_BY_BUNDLE[bundle],
                "data_categories": list(S.CONSENT_DATA_CATEGORIES[bundle]),
                "language": language,
                "consent_version": S.CONSENT_VERSION,
                "granted_at": granted,
                "withdrawn_at": withdrawn,
                "artefact_hash": did("h", person.pseudonym_id, bundle, granted),
            }
        )
    return rows


def withdrawal_day(consent_rows: List[Dict[str, Any]]) -> Optional[int]:
    for row in consent_rows:
        if row["withdrawn_at"]:
            return S.day_number(datetime.fromisoformat(row["withdrawn_at"]).date())
    return None


def _blackout_days(rng) -> Set[int]:
    if rng.random() >= S.CHECKIN_BLACKOUT_PROB:
        return set()
    start = rng.randint(1, S.ARC_DAYS)
    length = rng.randint(*S.CHECKIN_BLACKOUT_DAYS_RANGE)
    return set(range(start, min(S.ARC_DAYS, start + length - 1) + 1))


def build_checkins(
    seed: int,
    person: Person,
    series: Dict[int, float],
    stop_after_day: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if not person.participant:
        return []
    rng = rng_for(seed, "checkin", person.pseudonym_id)
    blackout = _blackout_days(rng)
    amber = person.cohort == S.COHORT_AMBER
    rows: List[Dict[str, Any]] = []
    for n in range(1, S.ARC_DAYS + 1):
        if stop_after_day is not None and n > stop_after_day:
            break
        d = S.day(n)
        skip = S.CHECKIN_BASE_SKIP_RATE
        if d.weekday() in S.WEEKEND_DAYS:
            skip += S.CHECKIN_WEEKEND_EXTRA_SKIP
        if d in S.HOLIDAYS:
            skip += S.CHECKIN_HOLIDAY_EXTRA_SKIP
        if n in blackout:
            skip = 1.0
        if rng.random() < skip:
            continue
        actual = series[n]
        reported = round(
            actual + rng.gauss(0.0, S.SELF_REPORT_SLEEP_NOISE_HOURS),
            S.SELF_REPORT_SLEEP_ROUND_DP,
        )
        raw = 3.0 + (actual - S.MOOD_SLEEP_PIVOT_HOURS) * S.MOOD_SLEEP_GAIN
        raw += rng.gauss(0.0, S.MOOD_NOISE)
        score = int(max(S.MOOD_CLAMP[0], min(S.MOOD_CLAMP[1], round(raw))))
        if amber and rng.random() < S.NATURAL_MASKING_PROB:
            score = max(score, 4)                        # "I'm fine" (FR-07)
        rows.append(
            {
                "id": did("ck", person.pseudonym_id, d.isoformat()),
                "pseudonym_id": person.pseudonym_id,
                "recorded_at": d.isoformat(),
                "mood_label": S.MOOD_LABELS[score],
                "mood_score": score,
                "sleep_hours": reported,
                "expires_at": (d + timedelta(days=S.RAW_TTL_DAYS)).isoformat(),
                "purged": False,
            }
        )
    return rows


def _instrument_score(rng, instrument: str, amber: bool) -> int:
    table = S.INSTRUMENT_MEAN_SD_AMBER if amber else S.INSTRUMENT_MEAN_SD_BASELINE
    mean, sd = table[instrument]
    lo, hi = S.INSTRUMENT_SCORE_RANGE[instrument]
    return int(max(lo, min(hi, round(rng.gauss(mean, sd)))))


def build_instruments(
    seed: int,
    person: Person,
    stop_after_day: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if not person.participant:
        return []
    rng = rng_for(seed, "instrument", person.pseudonym_id)
    amber = person.cohort == S.COHORT_AMBER
    rows: List[Dict[str, Any]] = []
    for n in S.INSTRUMENT_DAYS:
        if stop_after_day is not None and n > stop_after_day:
            break
        if rng.random() >= S.INSTRUMENT_COMPLETION_RATE:
            continue
        d = S.day(n)
        straight = rng.random() < S.STRAIGHT_LINING_RATE
        fast = rng.random() < S.TOO_FAST_RATE
        all_max = rng.random() < S.ALL_MAX_RATE
        fail = straight or fast or all_max or rng.random() < S.VALIDITY_FAIL_RATE
        for instrument in S.INSTRUMENTS:
            score = _instrument_score(rng, instrument, amber)
            item_9 = None
            if instrument == "PHQ-9":
                item_9 = 1 if rng.random() < S.CRISIS_ITEM9_RATE else 0
            rows.append(
                {
                    "id": did("ir", person.pseudonym_id, instrument, d.isoformat()),
                    "pseudonym_id": person.pseudonym_id,
                    "instrument": instrument,
                    "score": score,
                    "item_9": item_9,
                    "validity_fail": fail,
                    "straight_lining": straight,
                    "too_fast": fast,
                    "all_max": all_max,
                    "recorded_at": d.isoformat(),
                    "expires_at": (d + timedelta(days=S.RAW_TTL_DAYS)).isoformat(),
                    "purged": False,
                }
            )
    return rows


def generate_self_report(
    seed: int,
    person: Person,
    series: Dict[int, float],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return ``(consent, checkins, instruments)`` for one person."""
    consent = build_consent(seed, person)
    stop = withdrawal_day(consent)
    return (
        consent,
        build_checkins(seed, person, series, stop_after_day=stop),
        build_instruments(seed, person, stop_after_day=stop),
    )
