"""Post-generation validation — the generator refuses to ship bad data.

F09: *"Exit non-zero with a readable report on any validation failure (FK
violations, k < 5 unit, persona-arc mismatch)."* Everything here runs on the
in-memory payload before a single row reaches a database or a CSV file, so a
broken fixture fails at generation time rather than at demo time.

Checks
------
``fk_integrity``       every child row points at a personnel row and a real unit
``natural_keys``       no duplicate natural keys (would break idempotent upsert)
``k_anonymity``        no emitted unit at any level below ``spec.K_ANONYMITY``
``persona_arc``        the F09 day table is reproduced by the generated rows
``no_raw_signals``     no forbidden column names anywhere (ADR-0002)
``date_window``        every date sits inside the seed-anchored epoch
``distributions``      aggregate metrics inside ``spec.TOLERANCES``
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import Dataset, TABLES
from . import persona as P
from . import spec as S


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    skipped: bool = False


@dataclass
class Report:
    checks: List[Check] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "", skipped: bool = False) -> None:
        self.checks.append(Check(name=name, ok=ok, detail=detail, skipped=skipped))

    def failures(self) -> List[Check]:
        return [c for c in self.checks if not c.ok]

    def text(self) -> str:
        lines = ["validation:"]
        for check in self.checks:
            mark = "SKIP" if check.skipped else ("PASS" if check.ok else "FAIL")
            lines.append("  [{0}] {1}{2}".format(
                mark, check.name, " - " + check.detail if check.detail else ""
            ))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

#: payload table -> (person-key column, columns that must name a known unit)
_PERSON_KEYS: Dict[str, str] = {
    "leave": "pseudonym_id",
    "roster": "pseudonym_id",
    "deployment": "pseudonym_id",
    "transfer": "pseudonym_id",
    "training": "pseudonym_id",
    "medical": "pseudonym_id",
    "career": "pseudonym_id",
    "consent": "principal_pseudonym",
    "checkin": "pseudonym_id",
    "instrument": "pseudonym_id",
    "passive": "pseudonym_id",
}

#: payload table -> natural key columns (must match writer_db.PLANS)
_NATURAL_KEYS: Dict[str, Tuple[str, ...]] = {
    "personnel": ("personnel_id",),
    "leave": ("pseudonym_id", "applied_at", "leave_type"),
    "roster": ("pseudonym_id", "duty_date"),
    "deployment": ("pseudonym_id", "start_date", "posting_type"),
    "transfer": ("pseudonym_id", "effective_date", "from_unit", "to_unit"),
    "incident": ("incident_id",),
    "medical": ("pseudonym_id", "visit_date", "visit_type"),
    "career": ("pseudonym_id",),
    "consent": ("principal_pseudonym", "bundle_id"),
    "checkin": ("pseudonym_id", "recorded_at"),
    "instrument": ("pseudonym_id", "instrument", "recorded_at"),
    "passive": ("pseudonym_id", "recorded_at"),
}

_DATE_SUFFIXES = ("_at", "_date", "_from", "_to")


def _is_date_column(name: str) -> bool:
    return name.endswith(_DATE_SUFFIXES) or name in ("applied_at", "recorded_at")


def _parse_any_date(value: str) -> Optional[date]:
    try:
        if len(value) > 10:
            return datetime.fromisoformat(value).date()
        return date.fromisoformat(value)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_fk_integrity(ds: Dataset, report: Report) -> None:
    people = set(row["pseudonym_id"] for row in ds.personnel)
    personnel_ids = set(row["personnel_id"] for row in ds.personnel)
    units = set(row["unit_id"] for row in ds.units)
    problems: List[str] = []

    for table, key in sorted(_PERSON_KEYS.items()):
        for index, row in enumerate(ds.table(table)):
            if row.get(key) not in people:
                problems.append("{0}[{1}].{2}={3!r} has no personnel row".format(
                    table, index, key, row.get(key)))
                break
            pid = row.get("personnel_id")
            if pid is not None and pid not in personnel_ids:
                problems.append("{0}[{1}].personnel_id={2!r} unknown".format(table, index, pid))
                break

    for index, row in enumerate(ds.roster):
        if row["unit_id"] not in units:
            problems.append("roster[{0}].unit_id={1!r} is not an emitted unit".format(
                index, row["unit_id"]))
            break
    for index, row in enumerate(ds.incident):
        if row["unit_id"] not in units:
            problems.append("incident[{0}].unit_id={1!r} is not an emitted unit".format(
                index, row["unit_id"]))
            break

    report.add(
        "fk_integrity",
        not problems,
        "; ".join(problems) if problems else "{0} personnel, {1} units referenced cleanly".format(
            len(people), len(units)),
    )


def check_natural_keys(ds: Dataset, report: Report) -> None:
    problems: List[str] = []
    for table, key_cols in sorted(_NATURAL_KEYS.items()):
        seen = set()
        for row in ds.table(table):
            key = tuple(row.get(c) for c in key_cols)
            if key in seen:
                problems.append("{0} duplicate natural key {1!r}".format(table, key))
                break
            seen.add(key)
    report.add(
        "natural_keys",
        not problems,
        "; ".join(problems) if problems else "all natural keys unique (upsert is idempotent)",
    )


def check_k_anonymity(ds: Dataset, report: Report) -> None:
    if ds.persona_only:
        report.add(
            "k_anonymity", True,
            "skipped: --persona-only does not materialise unit membership",
            skipped=True,
        )
        return
    counts: Dict[str, int] = {}
    for row in ds.personnel:
        for level in ("battalion_id", "company_id", "platoon_id"):
            counts[row[level]] = counts.get(row[level], 0) + 1
    declared = dict((u["unit_id"], u["size"]) for u in ds.units)
    problems = []
    for unit_id, size in sorted(counts.items()):
        if size < S.K_ANONYMITY:
            problems.append("unit {0} has {1} < k={2}".format(unit_id, size, S.K_ANONYMITY))
    for unit_id, size in sorted(declared.items()):
        if size < S.K_ANONYMITY:
            problems.append("declared unit {0} has size {1} < k={2}".format(
                unit_id, size, S.K_ANONYMITY))
        if counts.get(unit_id, 0) != size:
            problems.append("unit {0} declares {1} but holds {2}".format(
                unit_id, size, counts.get(unit_id, 0)))
    smallest = min(counts.values()) if counts else 0
    report.add(
        "k_anonymity",
        not problems,
        "; ".join(problems[:5]) if problems else
        "{0} units, smallest = {1} (k={2})".format(len(counts), smallest, S.K_ANONYMITY),
    )


def check_persona_arc(ds: Dataset, report: Report) -> None:
    pid = S.PERSONA_PSEUDONYM_ID
    identity = [row for row in ds.personnel if row["pseudonym_id"] == pid]
    if not identity:
        report.add("persona_arc", False, "DEMO-PERSONA-01 ({0}) missing".format(pid))
        return
    person = identity[0]
    problems: List[str] = []
    if person["personnel_id"] != S.PERSONA_PERSONNEL_ID:
        problems.append("personnel_id {0} != {1}".format(
            person["personnel_id"], S.PERSONA_PERSONNEL_ID))
    if person["rank"] != S.PERSONA_RANK or person["age"] != S.PERSONA_AGE:
        problems.append("persona is {0}/{1}, expected {2}/{3}".format(
            person["rank"], person["age"], S.PERSONA_RANK, S.PERSONA_AGE))
    if person["unit_id"] != S.PERSONA_UNIT_ID:
        problems.append("unit {0} != {1}".format(person["unit_id"], S.PERSONA_UNIT_ID))

    ev = P.arc_evidence(ds)
    if ev["roster_days"] != S.ARC_DAYS:
        problems.append("roster has {0} days, expected {1}".format(ev["roster_days"], S.ARC_DAYS))
    if ev["cancel_days"] != [S.PERSONA_CANCEL_DAY_1, S.PERSONA_CANCEL_DAY_2]:
        problems.append("cancelled leaves on days {0}, expected {1}".format(
            ev["cancel_days"], [S.PERSONA_CANCEL_DAY_1, S.PERSONA_CANCEL_DAY_2]))
    if ev["night_days"] != ev["night_days_expected"]:
        problems.append("night-heavy rotation on {0}, expected {1}".format(
            _span(ev["night_days"]), _span(ev["night_days_expected"])))
    if ev["streak_at_day_60"] != S.PERSONA_DUTY_STREAK_CHECK_DAY:
        problems.append("consecutive duty at day 60 = {0}, expected {1}".format(
            ev["streak_at_day_60"], S.PERSONA_DUTY_STREAK_CHECK_DAY))
    if abs(ev["sleep_deviation_at_dip"] + 0.30) > 1e-9:
        problems.append("sleep proxy at day {0} is {1:+.1%} vs baseline, expected -30.0%".format(
            S.PERSONA_SLEEP_DIP_START_DAY, ev["sleep_deviation_at_dip"]))
    if ev["masking_mood_score"] < 4 or ev["masking_sleep_hours"] > 4.5:
        problems.append("day {0} masking fixture is mood={1} sleep={2}".format(
            S.PERSONA_MASKING_DAY, ev["masking_mood_score"], ev["masking_sleep_hours"]))
    relief_from, relief_to = S.PERSONA_ROSTER_RELIEF_DAYS
    if ev["relief_rest_days"] != list(range(relief_from, relief_to + 1)):
        problems.append("roster-swap relief days {0}, expected {1}-{2}".format(
            ev["relief_rest_days"], relief_from, relief_to))
    if ev["streak_at_day_90"] >= S.PERSONA_DUTY_STREAK_CHECK_DAY:
        problems.append("duty streak at day 90 is {0}; the arc must close Green".format(
            ev["streak_at_day_90"]))
    if not ev["recovery_monotonic"]:
        problems.append("sleep does not trend up across days {0}-{1}".format(
            *S.PERSONA_RECOVERY_DAYS))
    if abs(ev["sleep_at_green"] - S.PERSONA_RECOVERY_TARGET_HOURS) > 1e-9:
        problems.append("sleep at day 90 is {0}, expected {1}".format(
            ev["sleep_at_green"], S.PERSONA_RECOVERY_TARGET_HOURS))
    if ev["phq9_item9_max"] != 0:
        problems.append("PHQ-9 item 9 is non-zero; the arc would route to Critical")

    report.add(
        "persona_arc",
        not problems,
        "; ".join(problems) if problems else
        "{0} arc steps reproduced (days 1-{1})".format(len(P.ARC), S.ARC_DAYS),
    )


def _span(days: Sequence[int]) -> str:
    if not days:
        return "none"
    return "{0}-{1}".format(days[0], days[-1])


def check_no_raw_signals(ds: Dataset, report: Report) -> None:
    problems: List[str] = []
    for table in TABLES:
        rows = ds.table(table)
        if not rows:
            continue
        for column in sorted(rows[0].keys()):
            lowered = column.lower()
            for banned in S.FORBIDDEN_FIELD_SUBSTRINGS:
                if banned in lowered:
                    problems.append("{0}.{1} looks like raw signal data".format(table, column))
    for row in ds.passive[:1]:
        extra = sorted(set(row.keys()) - set(S.PASSIVE_ALLOWED_FIELDS) - {"id"})
        if extra:
            problems.append("passive rows carry non-derived fields {0}".format(extra))
    report.add(
        "no_raw_signals",
        not problems,
        "; ".join(problems) if problems else "derived features only (ADR-0002)",
    )


def check_date_window(ds: Dataset, report: Report) -> None:
    earliest = S.ARC_START.fromordinal(S.ARC_START.toordinal() - S.PRE_ARC_LOOKBACK_DAYS)
    latest = S.ARC_END.fromordinal(S.ARC_END.toordinal() + S.RAW_TTL_DAYS)
    problems: List[str] = []
    for table in TABLES:
        for row in ds.table(table):
            for column, value in row.items():
                if not isinstance(value, str) or not _is_date_column(column):
                    continue
                parsed = _parse_any_date(value)
                if parsed is None:
                    problems.append("{0}.{1}={2!r} is not a date".format(table, column, value))
                    break
                if parsed < earliest or parsed > latest:
                    problems.append("{0}.{1}={2} outside [{3}, {4}]".format(
                        table, column, value, earliest, latest))
                    break
            if problems:
                break
        if problems:
            break
    report.add(
        "date_window",
        not problems,
        "; ".join(problems) if problems else
        "all dates inside [{0}, {1}] (seed-anchored, no wall clock)".format(earliest, latest),
    )


# ---------------------------------------------------------------------------
# Distributions
# ---------------------------------------------------------------------------


def metrics(ds: Dataset) -> Dict[str, float]:
    out: Dict[str, float] = {}
    people = ds.personnel
    n = len(people)
    if not n:
        return out
    for rank, _ in S.RANK_SHARES:
        out["share.rank.{0}".format(rank)] = sum(1 for p in people if p["rank"] == rank) / n
    out["share.participants"] = sum(1 for p in people if p["participant"]) / n
    out["share.cohort.amber"] = sum(
        1 for p in people if p["cohort"] == S.COHORT_AMBER) / n
    out["mean.age"] = sum(p["age"] for p in people) / n

    current_high_risk = set(
        row["pseudonym_id"] for row in ds.deployment
        if row["end_date"] is None and row["posting_type"] == "high_risk"
    )
    out["share.posting.high_risk"] = len(current_high_risk) / n

    out["mean.roster_rows_per_person"] = len(ds.roster) / n
    worked = [row for row in ds.roster if not row["rest_day"]]
    out["mean.night_shift_ratio"] = (
        sum(1 for row in worked if row["shift_code"] == "night") / len(worked) if worked else 0.0
    )

    participants = sum(1 for p in people if p["participant"])
    out["share.checkin_days_of_participants"] = (
        len(ds.checkin) / (participants * S.ARC_DAYS) if participants else 0.0
    )
    out["share.passive_days"] = len(ds.passive) / (n * S.ARC_DAYS)

    noisy_rows = sum(len(ds.table(name)) for name in S.CSV_NOISE_DATASETS)
    if noisy_rows:
        out["rate.csv_duplicate"] = sum(
            1 for e in ds.csv_noise if e["kind"] == "duplicate") / noisy_rows
        out["rate.csv_malformed"] = sum(
            1 for e in ds.csv_noise if e["kind"] == "malformed") / noisy_rows
    return out


def check_distributions(ds: Dataset, report: Report) -> None:
    if ds.persona_only:
        report.add(
            "distributions", True,
            "skipped: --persona-only is a scripted fixture, not a sample",
            skipped=True,
        )
        return
    report.metrics = metrics(ds)
    n = len(ds.personnel)
    problems: List[str] = []
    for tol in S.TOLERANCES:
        if tol.key not in report.metrics:
            problems.append("{0} not measured".format(tol.key))
            continue
        value = report.metrics[tol.key]
        allowed = S.scaled_tolerance(tol, n)
        if abs(value - tol.target) > allowed:
            problems.append("{0}={1:.4f} outside {2:.4f} +/- {3:.4f} ({4})".format(
                tol.key, value, tol.target, allowed, tol.note))
    scaling = "" if n >= S.TOLERANCE_REFERENCE_N else " (widened x{0:.2f} for n={1})".format(
        (float(S.TOLERANCE_REFERENCE_N) / n) ** 0.5 if n else 1.0, n)
    report.add(
        "distributions",
        not problems,
        "; ".join(problems) if problems else
        "{0} tolerances met{1}".format(len(S.TOLERANCES), scaling),
    )


# ---------------------------------------------------------------------------


def validate(ds: Dataset) -> Report:
    report = Report()
    check_fk_integrity(ds, report)
    check_natural_keys(ds, report)
    check_k_anonymity(ds, report)
    check_persona_arc(ds, report)
    check_no_raw_signals(ds, report)
    check_date_window(ds, report)
    check_distributions(ds, report)
    return report
