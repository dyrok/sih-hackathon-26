"""F09 harness config — every distribution, constant and correlation, named.

F09 rule: *"Any constant, distribution or correlation in this doc must appear in
the harness config — no magic numbers in code that aren't in the spec."* So this
module is the single place a number is allowed to be written down. Every other
module in ``data/`` imports from here.

**Provenance discipline** (AGENTS.md rule 7 — no invented statistics): none of
the numbers below is presented as a measured fact about CRPF or any real force.
Each carries a ``confidence`` note. They are *shape* assumptions chosen to make
a demo dataset behave plausibly against the F04 ruleset thresholds
(``backend/config/rulesets/v1.yaml``). Where a real distribution is needed for a
claim, it must come from ayush's ML-005/006 sourced research, not from here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import Dict, Tuple

GENERATOR_VERSION = "1.0.0"
SPEC_DOC = "docs/features/F09-synthetic-data-generator.md"
RULESET_DOC = "backend/config/rulesets/v1.yaml"

# ---------------------------------------------------------------------------
# Calendar — seed-anchored epoch. NEVER datetime.now()/date.today().
# ---------------------------------------------------------------------------

#: Day 1 of the 90-day arc. Must equal ``backend/app/seed.py::ARC_START`` or the
#: generator and kv's demo seed disagree about what "day 62" means.
ARC_START = date(2026, 6, 4)
ARC_DAYS = 90
#: Day 90 == 2026-09-01 == ``Settings.demo_as_of``.
ARC_END = ARC_START + timedelta(days=ARC_DAYS - 1)

#: IST is a fixed offset — no DST anywhere in this generator (F09 edge cases).
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_LABEL = "+05:30"
#: Nominal local time stamped on datetime columns (consent artefacts).
CONSENT_LOCAL_TIME = time(9, 0)

#: How far before day 1 the generator is allowed to place history (completed
#: home leave, postings, transfers). Bounds the date-window validation check.
PRE_ARC_LOOKBACK_DAYS = 420

#: Weekday numbers (Mon=0) treated as a rest/low-participation day. CAPF duty
#: runs 7 days; Sunday is the realistic check-in gap. confidence: Low.
WEEKEND_DAYS = (6,)

#: Gazetted/observed holidays that fall inside the arc window, used only to
#: create realistic self-report gaps. 2026-08-15 (Independence Day) is certain;
#: the lunar-calendar entries are approximate. confidence: Low — used for gap
#: shape only, never for any claim.
HOLIDAYS: Tuple[date, ...] = (
    date(2026, 6, 26),   # Muharram (approx., lunar)
    date(2026, 8, 15),   # Independence Day
    date(2026, 8, 28),   # Raksha Bandhan (approx., lunar)
)

# ---------------------------------------------------------------------------
# Identity namespaces
# ---------------------------------------------------------------------------

#: Generated population uses its own namespace so it can never collide with the
#: hand-written fixtures in backend/app/seed.py (CR-3BN-xx, CR-TINY-x).
PERSONNEL_ID_FORMAT = "CR-GEN-{seq:05d}"
PSEUDONYM_ID_FORMAT = "ps_gen{seq:05d}"

#: The scripted persona keeps kv's exact ids so re-seeding is idempotent.
PERSONA_PERSONNEL_ID = "CR-DEMO-01"
PERSONA_PSEUDONYM_ID = "ps_demo01"
PERSONA_UNIT_ID = "3BN"
PERSONA_RANK = "Constable"
PERSONA_AGE = 34
PERSONA_LEGAL_NAME = "Demo Constable"
PERSONA_SKILL_TAGS = ("general",)

# ---------------------------------------------------------------------------
# Unit structure — battalion > company > platoon (F09 population model)
# ---------------------------------------------------------------------------

#: F09: "4-6 battalions (3rd Bn featured)".
BATTALION_IDS: Tuple[str, ...] = ("1BN", "2BN", "3BN", "4BN", "5BN")
FEATURED_BATTALION = "3BN"
COMPANY_LETTERS: Tuple[str, ...] = ("A", "B", "C", "D")
PLATOONS_PER_COMPANY = 3

#: ADR-0003 k. No emitted unit at any level may hold fewer than this (TC-504).
K_ANONYMITY = 5
MIN_PLATOON_SIZE = K_ANONYMITY
MIN_COMPANY_SIZE = MIN_PLATOON_SIZE * PLATOONS_PER_COMPANY          # 15
MIN_BATTALION_SIZE = MIN_COMPANY_SIZE * len(COMPANY_LETTERS)        # 60

#: ``unit_id`` written to the DB / CSV is the **battalion**, because the
#: commander aggregate surface groups on ``IdentityMap.unit_id``
#: (backend/app/api/routers/commander.py). Company/platoon live in the
#: population model and are k-checked there.
UNIT_LEVEL_FOR_DB = "battalion"

# ---------------------------------------------------------------------------
# Rank / age / tenure / family
# ---------------------------------------------------------------------------

#: Shape of the CAPF rank pyramid (Constable -> Inspector). confidence: Med
#: (pyramid shape is structural); the exact shares are an assumption.
RANK_SHARES: Tuple[Tuple[str, float], ...] = (
    ("Constable", 0.62),
    ("Head Constable", 0.20),
    ("ASI", 0.08),
    ("SI", 0.07),
    ("Inspector", 0.03),
)

#: F09: "age 22-50, tenure correlated with rank". confidence: Med.
AGE_RANGE_BY_RANK: Dict[str, Tuple[int, int]] = {
    "Constable": (22, 38),
    "Head Constable": (28, 45),
    "ASI": (32, 48),
    "SI": (33, 50),
    "Inspector": (36, 50),
}
#: Age at joining, so tenure = age - entry_age (the "tenure correlated with
#: rank" correlation comes via the rank-conditioned age range). confidence: Med.
ENTRY_AGE_RANGE = (20, 25)
MIN_TENURE_YEARS = 1

#: P(married | age band). confidence: Low — drives the family-separation story.
MARRIED_PROB_BY_AGE: Tuple[Tuple[int, float], ...] = (
    (25, 0.22),
    (30, 0.62),
    (35, 0.84),
    (99, 0.91),
)
#: P(n dependents | married). Index = number of dependents. confidence: Low.
DEPENDENTS_SHARES_MARRIED: Tuple[float, ...] = (0.10, 0.22, 0.38, 0.20, 0.10)
DEPENDENTS_SHARES_SINGLE: Tuple[float, ...] = (0.62, 0.24, 0.10, 0.03, 0.01)

#: Distance home -> current posting, km. Drives family_separation_index
#: (= distance_km * months_in_posting, F01). confidence: Low.
HOME_DISTANCE_KM_RANGE = (60.0, 2400.0)
HOME_DISTANCE_KM_ROUND = 0

#: Synthetic Indian name pool. These are generated identities in the identity
#: vault only; welfare tables never carry them (F08 / ADR-0003).
GIVEN_NAMES: Tuple[str, ...] = (
    "Aakash", "Abhishek", "Ajay", "Amit", "Anil", "Arun", "Ashok", "Balwinder",
    "Bhupendra", "Chandan", "Deepak", "Dinesh", "Gagandeep", "Ganesh", "Gopal",
    "Harish", "Hemant", "Jagdish", "Jitendra", "Kamlesh", "Karan", "Lakshman",
    "Mahesh", "Manoj", "Naveen", "Nitin", "Omprakash", "Pankaj", "Pradeep",
    "Prem", "Rajesh", "Rakesh", "Ramesh", "Ranjit", "Ravi", "Sandeep",
    "Sanjay", "Satish", "Shyam", "Sunil", "Suresh", "Tarun", "Umesh",
    "Vijay", "Vikram", "Vinod", "Yogesh",
)
SURNAMES: Tuple[str, ...] = (
    "Chauhan", "Chettri", "Das", "Deshmukh", "Dhillon", "Gowda", "Gupta",
    "Jadhav", "Jat", "Kumar", "Kushwaha", "Mahato", "Meena", "Nair", "Nayak",
    "Pandey", "Patel", "Patil", "Pillai", "Prasad", "Rana", "Rathore", "Reddy",
    "Sahu", "Saini", "Sharma", "Shekhawat", "Singh", "Thakur", "Tomar",
    "Verma", "Yadav",
)

# ---------------------------------------------------------------------------
# Cohorts
# ---------------------------------------------------------------------------

COHORT_BASELINE = "baseline"
COHORT_AMBER = "amber"
COHORT_PERSONA = "persona"

#: F09: "a low background rate of naturally-occurring Amber trajectories so
#: dashboards look organic, not staged." confidence: Low (product choice).
AMBER_BACKGROUND_RATE = 0.06

#: F09 / PRD: participation is a parameter, default aligned to the >= 30%
#: voluntary-adoption target.
PARTICIPATION_RATE_DEFAULT = 0.35

# ---------------------------------------------------------------------------
# Duty roster
# ---------------------------------------------------------------------------

SHIFT_CODES: Tuple[str, ...] = ("day", "evening", "night")
#: Shift mix for a normal rotation block. confidence: Low.
SHIFT_BLOCK_SHARES: Tuple[Tuple[str, float], ...] = (
    ("day", 0.58),
    ("evening", 0.24),
    ("night", 0.18),
)
#: A rotation block is one week of the same shift; rotation speed and direction
#: feed the circadian-disruption score (F01).
ROTATION_BLOCK_DAYS = 7
#: P(a block rotates away to a different shift), by the shift being left. Night
#: blocks turn over fastest, day blocks persist, which is what pins the
#: long-run shift mix near SHIFT_BLOCK_SHARES (stationary share of a two-state
#: hold/leave chain is proportional to 1/leave-probability: ~0.51 day /
#: 0.28 evening / 0.21 night). confidence: Low.
SHIFT_BLOCK_CHANGE_PROB_BY_SHIFT: Dict[str, float] = {
    "day": 0.30,
    "evening": 0.55,
    "night": 0.75,
}
#: P(the next block rotates backwards, day <- night, the disruptive direction).
#: Backward rotation is weighted 1.3x in the F01 circadian score.
BACKWARD_ROTATION_PROB = 0.30

#: Weekly rest day: normal populations "hover at short stretches" (F09).
REST_DAYS_PER_WEEK = 1
#: P(a scheduled rest day is cancelled and worked anyway). confidence: Low.
REST_DAY_CANCELLED_PROB = 0.18
#: P(the roster row for a day is simply missing — bad connectivity, ADR-0005).
ROSTER_MISSING_DAY_RATE = 0.008
#: "pt_absent" days feed pt_absence_unexplained (F01).
PT_ABSENT_RATE = 0.010

#: Training courses: short offline events that reset duty streaks (F09).
TRAINING_PROB = 0.22
TRAINING_DAYS_RANGE = (4, 10)
TRAINING_START_DAY_RANGE = (12, 74)
TRAINING_COURSES: Tuple[str, ...] = (
    "weapon_handling", "first_aid", "riot_drill", "map_reading", "cyber_hygiene",
)

#: Amber-trajectory cohort: a long unbroken duty stretch ending at day 90, so
#: consecutive_duty_days crosses the R-DUT-01 threshold (60) for some of them.
AMBER_STREAK_DAYS_RANGE = (35, 78)
#: Amber cohort night-heavy block length (drives circadian score up).
AMBER_NIGHT_BLOCK_DAYS_RANGE = (12, 24)
AMBER_NIGHT_BLOCK_START_DAY_RANGE = (35, 66)

# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------

LEAVE_TYPES: Tuple[str, ...] = ("home_leave", "casual", "earned", "medical")
#: Days between the *end* of the last completed home leave and day 1. The
#: R-LVE-01 threshold is 180 days since home leave, so the upper part of this
#: range is what produces "long time since home" flags. confidence: Low.
HOME_LEAVE_GAP_DAYS_RANGE = (20, 330)
HOME_LEAVE_LENGTH_DAYS_RANGE = (10, 25)
#: Lead time between applying and the sanctioned start.
LEAVE_APPLY_LEAD_DAYS_RANGE = (7, 30)

#: P(a person takes an in-window leave at all).
IN_WINDOW_LEAVE_PROB = 0.34
IN_WINDOW_LEAVE_LENGTH_RANGE = (4, 14)
IN_WINDOW_LEAVE_START_DAY_RANGE = (10, 70)
IN_WINDOW_LEAVE_TYPE_SHARES: Tuple[Tuple[str, float], ...] = (
    ("casual", 0.44),
    ("earned", 0.34),
    ("home_leave", 0.22),
)
#: Amber cohort never takes in-window leave (that is the point of the cohort).

#: Cancellations. The persona has exactly 2 (scripted); the base population
#: "sees occasional cancellations" (F09).
CANCEL_SHARES_BASELINE: Tuple[float, ...] = (0.86, 0.115, 0.025)   # 0,1,2 cancels
CANCEL_SHARES_AMBER: Tuple[float, ...] = (0.10, 0.25, 0.65)
CANCEL_DAY_RANGE = (10, 85)
CANCEL_LAG_DAYS_RANGE = (0, 3)
#: Denials (leave_denial_count).
DENIAL_PROB_BASELINE = 0.06
DENIAL_PROB_AMBER = 0.28
DENIAL_DAY_RANGE = (10, 85)
DENIAL_REASONS: Tuple[str, ...] = (
    "operational_requirement", "strength_shortage", "election_duty",
)
#: Early return from sanctioned leave (early_return_days, R-LVE-03 >= 3 days).
EARLY_RETURN_PROB = 0.09
EARLY_RETURN_DAYS_RANGE = (2, 7)

# ---------------------------------------------------------------------------
# Deployment / transfer
# ---------------------------------------------------------------------------

POSTING_TYPES: Tuple[str, ...] = ("static", "internal_security", "high_risk")
#: Share currently on a high-risk (field/CI) posting. R-DEP-02 fires at >= 30
#: days in a high-risk posting. confidence: Low.
POSTING_TYPE_SHARES: Tuple[Tuple[str, float], ...] = (
    ("static", 0.46),
    ("internal_security", 0.32),
    ("high_risk", 0.22),
)
#: How long before day 1 the current posting started.
POSTING_START_BEFORE_ARC_DAYS_RANGE = (30, 400)
#: A prior, closed posting for some people (deployment_count_12m).
PRIOR_POSTING_PROB = 0.30
PRIOR_POSTING_LENGTH_DAYS_RANGE = (60, 180)

#: Transfers in the last 12 months (transfer_count_12m, R-CAR-02 at >= 2).
TRANSFER_COUNT_SHARES: Tuple[float, ...] = (0.55, 0.30, 0.12, 0.03)
TRANSFER_WITHIN_DAYS = 360
TRANSFER_REASON_CODES: Tuple[str, ...] = ("posting", "compassionate", "promotion", "administrative")

# ---------------------------------------------------------------------------
# Medical / career
# ---------------------------------------------------------------------------

MEDICAL_VISIT_TYPES: Tuple[str, ...] = ("sick_report", "opd", "injury", "annual")
#: Expected medical visits per person over the 90-day window. confidence: Low.
MEDICAL_VISITS_SHARES: Tuple[float, ...] = (0.42, 0.30, 0.17, 0.08, 0.03)
MEDICAL_VISIT_TYPE_SHARES: Tuple[Tuple[str, float], ...] = (
    ("sick_report", 0.46),
    ("opd", 0.36),
    ("injury", 0.10),
    ("annual", 0.08),
)
AMBER_MEDICAL_VISIT_BONUS = 1          # extra visits for the amber cohort

PROMOTION_PENDING_PROB = 0.28
PROMOTION_PENDING_MONTHS_RANGE = (1.0, 42.0)
#: ``CareerIn`` in backend/app/ingest/schemas.py has no empty-string coercion on
#: its optional numeric fields, so an empty CSV cell is a schema rejection. The
#: generator therefore emits 0 (= "nothing pending") rather than NULL for these
#: two columns, in the payload as well as the CSV, so DB and CSV never diverge.
#: Neither value is read by any rule in v1.yaml, and F01's ``inquiry_age_days``
#: already returns None whenever no inquiry is pending.
CAREER_NUMERIC_NULL_SUBSTITUTE = 0
INQUIRY_PENDING_PROB_BASELINE = 0.020
INQUIRY_PENDING_PROB_AMBER = 0.12
INQUIRY_AGE_DAYS_RANGE = (20, 500)
DENIED_TRAINING_SHARES: Tuple[float, ...] = (0.78, 0.16, 0.05, 0.01)

# ---------------------------------------------------------------------------
# Unit incidents (FR-08 / TC-103) — group-scoped, never individual
# ---------------------------------------------------------------------------

INCIDENT_TYPES: Tuple[str, ...] = ("casualty", "ied", "riot_control", "accident")
INCIDENT_SEVERITY_BANDS: Tuple[str, ...] = ("low", "medium", "high")
#: One incident per this many battalions, placed inside the arc window.
INCIDENT_COUNT = 3
INCIDENT_DAY_RANGE = (35, 82)
INCIDENT_EXPOSURE_WINDOW_DAYS = 30
#: Generated incidents live in their own id namespace so they can never collide
#: with the hand-written INC-3BN-01 fixture in backend/app/seed.py.
INCIDENT_ID_FORMAT = "INC-GEN-{unit}-{seq:02d}"

# ---------------------------------------------------------------------------
# Passive features (derived only — NEVER raw audio, ADR-0002)
# ---------------------------------------------------------------------------

#: Fields a passive row is allowed to carry. validate.py enforces this list, so
#: "we accidentally shipped raw audio" is a test failure, not a code review.
PASSIVE_ALLOWED_FIELDS: Tuple[str, ...] = (
    "pseudonym_id", "recorded_at", "sleep_hours_proxy", "activity_index", "source",
)
#: Substrings that must never appear in any emitted column name (ADR-0002).
FORBIDDEN_FIELD_SUBSTRINGS: Tuple[str, ...] = (
    "audio", "waveform", "pcm", "raw_voice", "recording", "mfcc_raw", "transcript",
)

SLEEP_BASELINE_HOURS_RANGE = (6.2, 7.8)
SLEEP_DAILY_NOISE_HOURS = 0.55
#: A night shift costs roughly this much sleep. confidence: Low.
NIGHT_SHIFT_SLEEP_PENALTY_HOURS = 1.05
EVENING_SHIFT_SLEEP_PENALTY_HOURS = 0.35
#: On a rest day people catch up.
REST_DAY_SLEEP_BONUS_HOURS = 0.6
SLEEP_HOURS_CLAMP = (2.5, 10.0)
SLEEP_ROUND_DP = 2

#: Amber cohort sleep dip: multiplier applied from the dip start day. The F04
#: baseline rule R-HEA-01 fires at a deviation <= -0.30.
AMBER_SLEEP_DIP_MULTIPLIER = 0.70
AMBER_SLEEP_DIP_START_DAY_RANGE = (48, 70)

#: Derived activity index (0-1), inversely related to fatigue. Not persisted by
#: the backend (PassiveFeature has no column) — CSV export only.
ACTIVITY_INDEX_BASE_RANGE = (0.45, 0.85)
ACTIVITY_INDEX_NOISE = 0.08
ACTIVITY_INDEX_CLAMP = (0.05, 1.0)

#: P(no passive row for a day — device off / no sync, ADR-0005).
PASSIVE_MISSING_DAY_RATE = 0.06

# ---------------------------------------------------------------------------
# Self-report (consent-gated)
# ---------------------------------------------------------------------------

CONSENT_BUNDLES: Tuple[str, ...] = ("checkin", "instruments", "passive")
CONSENT_PURPOSE_BY_BUNDLE: Dict[str, str] = {
    "checkin": "wellness_self_report",
    "instruments": "wellness_self_report",
    "passive": "on_device_features",
}
CONSENT_DATA_CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "checkin": ("checkin", "sleep"),
    "instruments": ("PHQ-9", "GAD-7", "PSS-10", "ISI"),
    "passive": ("sleep_proxy", "activity"),
}
CONSENT_LANGUAGES: Tuple[Tuple[str, float], ...] = (("hi", 0.72), ("en", 0.28))
CONSENT_VERSION = "v1"
#: How long before day 1 consent was granted (seed-anchored, never now()).
CONSENT_GRANT_BEFORE_ARC_DAYS_RANGE = (2, 45)

#: TC-407 fixture: a slice of participants silently withdraw consent mid-arc.
SILENT_WITHDRAWAL_RATE = 0.04
SILENT_WITHDRAWAL_DAY_RANGE = (40, 80)

#: Daily 10-s check-in participation, given the person is a participant.
CHECKIN_BASE_SKIP_RATE = 0.18
CHECKIN_WEEKEND_EXTRA_SKIP = 0.22
CHECKIN_HOLIDAY_EXTRA_SKIP = 0.35
#: Long connectivity blackout (ADR-0005): probability and length.
CHECKIN_BLACKOUT_PROB = 0.16
CHECKIN_BLACKOUT_DAYS_RANGE = (3, 9)

#: mood_score is 1..5, higher = "I'm fine" (the backend scorer treats >= 4 as
#: a "fine" self-report — backend/app/risk/scorer.py::_self_report_state).
MOOD_LABELS: Dict[int, str] = {1: "low", 2: "tired", 3: "ok", 4: "good", 5: "fine"}
MOOD_SLEEP_PIVOT_HOURS = 6.2
MOOD_SLEEP_GAIN = 0.8
MOOD_NOISE = 0.9
MOOD_CLAMP = (1, 5)
#: A self-reported sleep figure is the same night, remembered imprecisely.
SELF_REPORT_SLEEP_NOISE_HOURS = 0.3
SELF_REPORT_SLEEP_ROUND_DP = 1
#: P(an amber-cohort participant reports "fine" anyway on a bad day) — the
#: naturally occurring masking rate the discrepancy rule exists for (FR-07).
NATURAL_MASKING_PROB = 0.22

#: Monthly full instruments, on these arc days.
INSTRUMENT_DAYS: Tuple[int, ...] = (15, 45, 75)
INSTRUMENTS: Tuple[str, ...] = ("PHQ-9", "GAD-7", "PSS-10", "ISI")
#: Score ranges mirror the instrument specs referenced in F02.
INSTRUMENT_SCORE_RANGE: Dict[str, Tuple[int, int]] = {
    "PHQ-9": (0, 27),
    "GAD-7": (0, 21),
    "PSS-10": (0, 40),
    "ISI": (0, 28),
}
#: (mean, sd) by cohort. confidence: Low — plausible severity shape only, NOT
#: an epidemiological claim. Any published prevalence must come from ML-005.
INSTRUMENT_MEAN_SD_BASELINE: Dict[str, Tuple[float, float]] = {
    "PHQ-9": (4.2, 3.4),
    "GAD-7": (3.6, 3.0),
    "PSS-10": (14.0, 5.5),
    "ISI": (7.0, 4.2),
}
INSTRUMENT_MEAN_SD_AMBER: Dict[str, Tuple[float, float]] = {
    "PHQ-9": (12.0, 4.0),
    "GAD-7": (10.5, 3.6),
    "PSS-10": (24.0, 5.0),
    "ISI": (16.0, 4.5),
}
#: P(a participant actually completes the monthly instrument set).
INSTRUMENT_COMPLETION_RATE = 0.62
#: PHQ-9 item 9 (self-harm ideation) — any non-zero routes to Critical in F04,
#: so this stays deliberately rare and is a demo of the crisis path only.
CRISIS_ITEM9_RATE = 0.004
#: Validity-scale item failure rates (F02 validity items).
VALIDITY_FAIL_RATE = 0.05
STRAIGHT_LINING_RATE = 0.06
TOO_FAST_RATE = 0.05
ALL_MAX_RATE = 0.01

#: Raw self-report TTL (mirrors Settings.raw_ttl_days) — sets ``expires_at``.
RAW_TTL_DAYS = 90

# ---------------------------------------------------------------------------
# CSV realism noise (F01 rejection path must be exercised, TC-102)
# ---------------------------------------------------------------------------

#: Fraction of rows re-emitted verbatim -> ingest quarantines "duplicate
#: natural key". Applied to the CSV export only; the DB payload stays clean.
CSV_DUPLICATE_RATE = 0.004
#: Fraction of rows emitted broken -> ingest quarantines with a schema error.
CSV_MALFORMED_RATE = 0.003
#: Each kind is chosen because the backend ingest path actually rejects it:
#: a blank/garbled date fails the pydantic schema, an unknown personnel_id fails
#: the identity lookup. Both land in ``quarantine_row`` with a reason (TC-102).
CSV_MALFORM_KINDS: Tuple[str, ...] = (
    "blank_required_date",
    "bad_date_format",
    "unknown_personnel_id",
)
CSV_UNKNOWN_PERSONNEL_ID = "CR-GEN-99999"
CSV_BAD_DATE_LITERAL = "04-06-2026"
#: Only these datasets get noise (they carry a per-person natural key, so the
#: duplicate path is exercised as well as the schema path).
CSV_NOISE_DATASETS: Tuple[str, ...] = ("leave", "roster", "deployment", "transfer", "medical")
CSV_LINE_TERMINATOR = "\n"

#: Column order per ingest dataset — copied from backend/app/ingest/schemas.py.
#: writer_csv emits exactly these, in this order, and nothing else.
INGEST_COLUMNS: Dict[str, Tuple[str, ...]] = {
    "leave": (
        "personnel_id", "leave_type", "home_leave", "applied_at", "sanctioned_from",
        "sanctioned_to", "cancelled_at", "denial_reason", "actual_return_date",
    ),
    "roster": ("personnel_id", "unit_id", "duty_date", "shift_code", "rest_day"),
    "deployment": (
        "personnel_id", "unit_id", "posting_type", "start_date", "end_date", "distance_km",
    ),
    "transfer": ("personnel_id", "from_unit", "to_unit", "effective_date", "reason_code"),
    "incident": (
        "incident_id", "unit_id", "incident_type", "severity_band", "incident_date",
        "exposure_window_days",
    ),
    "medical": ("personnel_id", "visit_date", "visit_type", "injury_flag"),
    "career": (
        "personnel_id", "promotion_board_pending_months", "inquiry_court_pending",
        "inquiry_age_days", "denied_training_count_12m",
    ),
}
#: The required date column the "blank"/"bad format" malformers attack.
REQUIRED_DATE_COLUMN: Dict[str, str] = {
    "leave": "applied_at",
    "roster": "duty_date",
    "deployment": "start_date",
    "transfer": "effective_date",
    "medical": "visit_date",
    "incident": "incident_date",
}

#: Reference exports — NOT part of the ingest contract. They exist so the
#: fixture is inspectable and so app-side tables (check-ins, instruments,
#: passive, consent) can be diffed outside a database.
REFERENCE_COLUMNS: Dict[str, Tuple[str, ...]] = {
    "personnel": (
        "personnel_id", "pseudonym_id", "unit_id", "battalion_id", "company_id",
        "platoon_id", "rank", "age", "entry_age", "tenure_years", "marital_status",
        "dependents", "home_distance_km", "legal_name", "participant", "cohort",
    ),
    "units": ("unit_id", "level", "parent_id", "size"),
    "training": ("personnel_id", "unit_id", "course", "start_date", "end_date"),
    "consent": (
        "principal_pseudonym", "bundle_id", "purpose_string", "language",
        "consent_version", "granted_at", "withdrawn_at",
    ),
    "checkin": (
        "pseudonym_id", "recorded_at", "mood_label", "mood_score", "sleep_hours",
        "expires_at", "purged",
    ),
    "instrument": (
        "pseudonym_id", "instrument", "score", "item_9", "validity_fail",
        "straight_lining", "too_fast", "all_max", "recorded_at", "expires_at", "purged",
    ),
    "passive": ("pseudonym_id", "recorded_at", "sleep_hours_proxy", "activity_index", "source"),
}

# ---------------------------------------------------------------------------
# DEMO-PERSONA-01 — the scripted arc (F09 §"The scripted persona")
#
# Days 1-67 reproduce backend/app/seed.py::seed_persona_hr row for row (same
# natural keys, same values) so re-seeding either way is idempotent and kv's
# ML-002 harness (which asserts days 30/62/64/65) is unaffected. Days 68-90 add
# the recovery half of the F09 arc, which seed.py does not model.
# ---------------------------------------------------------------------------

#: The completed home leave that sets days_since_home_leave. F09's arc text says
#: "1-30: one leave taken and returned"; it is modelled immediately BEFORE day 1
#: because a leave inside days 1-30 would break the day-58-60 "60 consecutive
#: duty days" clause of the same table. Same choice as backend/app/seed.py.
PERSONA_HOME_LEAVE_APPLIED = date(2025, 11, 1)
PERSONA_HOME_LEAVE_FROM = date(2025, 11, 10)
PERSONA_HOME_LEAVE_TO = date(2025, 11, 24)

PERSONA_CANCEL_DAY_1 = 31
PERSONA_CANCEL_DAY_2 = 55
PERSONA_NIGHT_DAYS = (40, 50)
PERSONA_DUTY_STREAK_CHECK_DAY = 60          # "60 consecutive duty days"
PERSONA_AMBER_DAY = 62
PERSONA_MASKING_DAY = 64
PERSONA_RED_DAY = 65
PERSONA_UNMASK_DAY = 66
PERSONA_ROSTER_RELIEF_DAYS = (68, 70)
PERSONA_RECOVERY_DAYS = (75, 85)
PERSONA_GREEN_DAYS = (85, 90)

PERSONA_DEPLOYMENT_START = date(2025, 12, 1)
PERSONA_DEPLOYMENT_TYPE = "high_risk"
PERSONA_DEPLOYMENT_DISTANCE_KM = 850.0
PERSONA_TRANSFERS: Tuple[Tuple[str, str, date, str], ...] = (
    ("2BN", "1BN", date(2025, 10, 1), "posting"),
    ("1BN", "3BN", date(2026, 1, 15), "posting"),
)
#: kv's group-exposure fixture. Reproduced verbatim (same incident_id) so the
#: generator upserts it rather than creating a second one.
PERSONA_INCIDENT_ID = "INC-3BN-01"
PERSONA_INCIDENT_TYPE = "casualty"
PERSONA_INCIDENT_SEVERITY = "high"
PERSONA_INCIDENT_DAY = 80

#: Sleep script. 4.9 h is exactly 7.0 h - 30%, which is the F09 arc's
#: "sleep proxy -30% vs baseline" and the R-HEA-01 threshold in v1.yaml.
PERSONA_SLEEP_BASELINE_HOURS = 7.0
PERSONA_SLEEP_DIP_START_DAY = 56
PERSONA_SLEEP_DIP_HOURS = 4.9
PERSONA_MASKING_SLEEP_HOURS = 4.0           # day 64, the "I'm fine" night
PERSONA_RECOVERY_TARGET_HOURS = 7.0
#: Weekly rest resumes after the approved roster swap.
PERSONA_WEEKLY_REST_FROM_DAY = 71
PERSONA_REST_EVERY_N_DAYS = 7

PERSONA_MOOD_SCORE_NORMAL = 3               # "ok"
PERSONA_MOOD_SCORE_MASKING = 5              # "fine" despite the signals
PERSONA_MOOD_SCORE_RECOVERED = 4            # "good"
PERSONA_RECOVERY_MOOD_SWITCH_DAY = 80

PERSONA_ACTIVITY_BASE = 0.45
PERSONA_ACTIVITY_SLEEP_GAIN = 0.05

#: Scripted instrument results: day -> instrument -> score. item_9 is 0 on every
#: occasion — the F09 arc tops out at Red, and any non-zero item 9 would route
#: the persona to Critical (crisis path in v1.yaml) and break "85-90 green".
PERSONA_INSTRUMENT_SCRIPT: Dict[int, Dict[str, int]] = {
    15: {"PHQ-9": 4, "GAD-7": 3, "PSS-10": 12, "ISI": 6},
    45: {"PHQ-9": 11, "GAD-7": 9, "PSS-10": 22, "ISI": 14},
    75: {"PHQ-9": 6, "GAD-7": 5, "PSS-10": 16, "ISI": 9},
}
PERSONA_CONSENT_LANGUAGE = "hi"
PERSONA_CONSENT_GRANTED_BEFORE_ARC_DAYS = 1

# ---------------------------------------------------------------------------
# Validation tolerances (TC-503). README repeats this table.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Tolerance:
    """One post-generation distribution assertion.

    ``kind`` says where ``target`` comes from:

    * ``declared`` — the target is a spec constant above, so the check proves the
      generator honours its own configuration.
    * ``emergent`` — the target is the value measured on the reference run
      (``--seed 42 --personnel 1000``). These are regression guards: they catch
      "somebody changed the roster model and nobody noticed", not correctness.
    """

    key: str
    target: float
    abs_tol: float
    note: str
    kind: str = "declared"


TOLERANCES: Tuple[Tolerance, ...] = (
    Tolerance("share.rank.Constable", 0.62, 0.06, "rank pyramid base"),
    Tolerance("share.rank.Head Constable", 0.20, 0.05, "rank pyramid"),
    Tolerance("share.rank.ASI", 0.08, 0.04, "rank pyramid"),
    Tolerance("share.rank.SI", 0.07, 0.04, "rank pyramid"),
    Tolerance("share.rank.Inspector", 0.03, 0.03, "rank pyramid apex"),
    Tolerance("share.participants", PARTICIPATION_RATE_DEFAULT, 0.06,
              "voluntary check-in participation (--participation)"),
    Tolerance("share.cohort.amber", AMBER_BACKGROUND_RATE, 0.035,
              "background amber trajectories"),
    Tolerance("share.posting.high_risk", 0.22, 0.06,
              "share currently on an open high-risk posting"),
    Tolerance("mean.age", 33.0, 2.5, "population mean age, given the rank pyramid",
              "emergent"),
    Tolerance("mean.roster_rows_per_person", 89.2, 1.5,
              "90 days minus ROSTER_MISSING_DAY_RATE gaps", "emergent"),
    Tolerance("mean.night_shift_ratio", 0.21, 0.06,
              "worked days on night shift; stationary mix of the rotation chain",
              "emergent"),
    Tolerance("share.checkin_days_of_participants", 0.75, 0.08,
              "check-in days / arc days for participants (skips, gaps, blackouts)",
              "emergent"),
    Tolerance("share.passive_days", 0.94, 0.05,
              "passive rows / arc days across the whole population"),
    Tolerance("rate.csv_duplicate", CSV_DUPLICATE_RATE, 0.004,
              "duplicate CSV rows (TC-102 rejection path)"),
    Tolerance("rate.csv_malformed", CSV_MALFORMED_RATE, 0.004,
              "malformed CSV rows (TC-102 rejection path)"),
)

#: Headcount the tolerances above were calibrated at.
TOLERANCE_REFERENCE_N = 1000


def scaled_tolerance(tol: "Tolerance", personnel: int) -> float:
    """Widen a tolerance for small populations.

    The standard error of every share above falls as 1/sqrt(n), so a 60-person
    run is legitimately noisier than the 1,000-person reference run. Scaling by
    sqrt(reference_n / n) keeps the check meaningful at demo scale instead of
    turning it into a lottery. Tolerances are never tightened for larger runs.
    """
    if personnel >= TOLERANCE_REFERENCE_N or personnel <= 0:
        return tol.abs_tol
    return tol.abs_tol * ((float(TOLERANCE_REFERENCE_N) / personnel) ** 0.5)


def day(n: int) -> date:
    """Arc day number (1-based) -> calendar date. Mirrors backend seed.day()."""
    return ARC_START + timedelta(days=n - 1)


def day_number(value: date) -> int:
    """Calendar date -> arc day number (1-based)."""
    return (value - ARC_START).days + 1


def is_gap_day(value: date) -> bool:
    """True on weekends/holidays — the realistic self-report gap days."""
    return value.weekday() in WEEKEND_DAYS or value in HOLIDAYS
