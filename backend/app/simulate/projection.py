"""F07 §4 — what-if deployment simulator.

Three properties make this defensible in front of a jury:

1. It is **not** ML (ADR-0001). It re-runs the *same* ``evaluate_rules`` +
   ``aggregate`` functions the live engine uses, over a scenario-modified copy
   of each person's HR signal vector.
2. It **never touches live scores**: nothing is persisted against a person, and
   no ``RiskScore`` row is written. Only a unit-scoped ``SimulationRun`` is kept.
3. It is **HR-signal-only**. Voluntary self-report (check-ins, instruments) is
   deliberately excluded from the commander-visible projection, so a scenario
   can never become a channel for individual welfare data (ADR-0003).

Output is a unit aggregate behind the k-anonymity floor. Scenario objects carry
unit IDs exclusively (F07 privacy note).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import HrDeployment, IdentityMap, SignalSnapshot
from ..risk.aggregator import TIER_ORDER, aggregate, tier_for
from ..risk.evaluator import evaluate_rules
from ..risk.ruleset import load_ruleset

#: Every lever, its unit, and its validated range. Inputs outside the range are
#: rejected with the range shown — never silently clamped (F07 "Simulation edge").
LEVERS: dict[str, dict[str, Any]] = {
    "extend_deployment_days": {
        "unit": "days",
        "min": 0,
        "max": 180,
        "default": 0,
        "affects": ["days_in_high_risk_posting", "family_separation_index", "consecutive_duty_days"],
        "explain_key": "sim.lever.extend_deployment",
    },
    "grant_leave_block_days": {
        "unit": "days",
        "min": 0,
        "max": 60,
        "default": 0,
        "affects": ["days_since_home_leave", "consecutive_duty_days"],
        "explain_key": "sim.lever.leave_block",
    },
    "leave_block_coverage_pct": {
        "unit": "percent of unit",
        "min": 0,
        "max": 100,
        "default": 100,
        "affects": ["days_since_home_leave", "consecutive_duty_days"],
        "explain_key": "sim.lever.leave_coverage",
    },
    "night_duty_rebalance_pct": {
        "unit": "percent reduction in night load",
        "min": 0,
        "max": 100,
        "default": 0,
        "affects": ["night_shift_ratio", "circadian_disruption_score"],
        "explain_key": "sim.lever.night_rebalance",
    },
}

#: Stated, reviewable modelling assumptions. These are snapshotted with every
#: run so an old projection can always be re-read against the rules it used.
ASSUMPTIONS: dict[str, Any] = {
    "signals_used": "hr_only",
    "voluntary_self_report_excluded": True,
    "family_separation_index_formula": "current_posting_distance_km * months_on_posting",
    "extend_deployment_adds_duty_days": True,
    "leave_block_resets_home_leave_clock": True,
    "leave_block_resets_duty_streak": True,
    "night_rebalance_scales_circadian_linearly": True,
    "no_person_row_is_returned": True,
}


class ScenarioError(ValueError):
    """Raised for a lever value outside its validated range."""


def validate_scenario(raw: dict[str, Any] | None) -> dict[str, float]:
    raw = raw or {}
    unknown = sorted(set(raw) - set(LEVERS))
    if unknown:
        raise ScenarioError(
            "unknown scenario lever(s): %s; valid levers: %s" % (", ".join(unknown), ", ".join(sorted(LEVERS)))
        )
    out: dict[str, float] = {}
    for name, spec in LEVERS.items():
        value = raw.get(name, spec["default"])
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ScenarioError("%s must be a number in [%s, %s]" % (name, spec["min"], spec["max"])) from None
        if value < spec["min"] or value > spec["max"]:
            raise ScenarioError(
                "%s=%s is outside the validated range [%s, %s] (%s)"
                % (name, value, spec["min"], spec["max"], spec["unit"])
            )
        out[name] = value
    return out


def _current_posting_distance_km(db: Session, pid: str, as_of: date) -> float | None:
    rows = (
        db.query(HrDeployment)
        .filter(HrDeployment.pseudonym_id == pid, HrDeployment.start_date <= as_of)
        .order_by(HrDeployment.start_date.desc())
        .all()
    )
    for r in rows:
        end = r.end_date or as_of
        if r.start_date <= as_of <= end:
            return float(r.distance_km) if r.distance_km is not None else None
    return None


def _hr_signals(db: Session, pid: str, as_of: date) -> dict[str, float]:
    rows = (
        db.query(SignalSnapshot)
        .filter(SignalSnapshot.pseudonym_id == pid, SignalSnapshot.window_end == as_of)
        .all()
    )
    return {r.signal_key: r.value for r in rows if r.value is not None}


def apply_levers(
    signals: dict[str, float],
    scenario: dict[str, float],
    *,
    distance_km: float | None,
    include_in_leave_block: bool,
) -> dict[str, float]:
    """Pure function: signal vector in, scenario-modified signal vector out."""
    out = dict(signals)

    extend = scenario["extend_deployment_days"]
    if extend:
        if "days_in_high_risk_posting" in out:
            out["days_in_high_risk_posting"] = min(90.0, out["days_in_high_risk_posting"] + extend)
        if "consecutive_duty_days" in out:
            out["consecutive_duty_days"] = out["consecutive_duty_days"] + extend
        if distance_km is not None:
            added = distance_km * (extend / 30.0)
            out["family_separation_index"] = out.get("family_separation_index", 0.0) + added

    block = scenario["grant_leave_block_days"]
    if block and include_in_leave_block:
        out["days_since_home_leave"] = 0.0
        out["consecutive_duty_days"] = 0.0

    rebalance = scenario["night_duty_rebalance_pct"] / 100.0
    if rebalance:
        factor = 1.0 - rebalance
        if "night_shift_ratio" in out:
            out["night_shift_ratio"] = out["night_shift_ratio"] * factor
        if "circadian_disruption_score" in out:
            out["circadian_disruption_score"] = out["circadian_disruption_score"] * factor
    return out


def _score(signals: dict[str, float], ruleset: dict[str, Any]) -> tuple[int, str, list[str]]:
    factors = evaluate_rules(signals, ruleset)
    score, _ = aggregate(factors, ruleset)
    return score, tier_for(score, ruleset), [f["rule_id"] for f in factors]


def project_unit(
    db: Session,
    *,
    unit_id: str,
    scenario: dict[str, Any] | None,
    as_of: date,
) -> dict[str, Any]:
    """Unit-level projection. Returns aggregates only — never a person row."""
    params = validate_scenario(scenario)
    ruleset = load_ruleset()
    k = get_settings().k_anonymity

    people = db.query(IdentityMap).filter(IdentityMap.unit_id == unit_id).all()
    pids = [p.pseudonym_id for p in people]

    # Deterministic, stable membership of the leave block: the first N% of the
    # unit by pseudonym. Rotating it randomly would make two runs of the same
    # scenario disagree, which would make the projection untrustworthy.
    coverage = params["leave_block_coverage_pct"] / 100.0
    ordered = sorted(pids)
    n_in_block = int(round(len(ordered) * coverage))
    in_block = set(ordered[:n_in_block])

    before_scores: list[int] = []
    after_scores: list[int] = []
    before_tiers: list[str] = []
    after_tiers: list[str] = []
    rule_before: dict[str, int] = {}
    rule_after: dict[str, int] = {}
    contributors = 0

    for pid in pids:
        base = _hr_signals(db, pid, as_of)
        if not base:
            continue
        contributors += 1
        distance = _current_posting_distance_km(db, pid, as_of)
        after = apply_levers(
            base, params, distance_km=distance, include_in_leave_block=pid in in_block
        )
        b_score, b_tier, b_rules = _score(base, ruleset)
        a_score, a_tier, a_rules = _score(after, ruleset)
        before_scores.append(b_score)
        after_scores.append(a_score)
        before_tiers.append(b_tier)
        after_tiers.append(a_tier)
        for rid in b_rules:
            rule_before[rid] = rule_before.get(rid, 0) + 1
        for rid in a_rules:
            rule_after[rid] = rule_after.get(rid, 0) + 1

    suppressed = contributors < k
    assumptions = dict(ASSUMPTIONS)
    assumptions.update(
        {
            "ruleset_version": int(ruleset["version"]),
            "engine_version": get_settings().engine_version,
            "as_of": as_of.isoformat(),
            "k_anonymity": k,
            "levers": {name: dict(spec) for name, spec in LEVERS.items()},
        }
    )

    if suppressed:
        return {
            "unit_id": unit_id,
            "suppressed": True,
            "k": k,
            "contributor_count": None,
            "reason_key": "heat.cell.suppressed",
            "scenario": params,
            "assumption_snapshot": assumptions,
        }

    def _elevated(tiers: list[str]) -> float:
        return round(
            sum(1 for t in tiers if TIER_ORDER.index(t) >= TIER_ORDER.index("amber")) / len(tiers), 4
        )

    fatigue_before = round(sum(before_scores) / len(before_scores), 2)
    fatigue_after = round(sum(after_scores) / len(after_scores), 2)
    elevated_before = _elevated(before_tiers)
    elevated_after = _elevated(after_tiers)

    rule_deltas = []
    for rid in sorted(set(rule_before) | set(rule_after)):
        b = rule_before.get(rid, 0)
        a = rule_after.get(rid, 0)
        if a != b:
            rule_deltas.append({"rule_id": rid, "before": b, "after": a, "delta": a - b})

    return {
        "unit_id": unit_id,
        "suppressed": False,
        "k": k,
        "contributor_count": contributors,
        "scenario": params,
        "projection": {
            "fatigue_index_before": fatigue_before,
            "fatigue_index_after": fatigue_after,
            "fatigue_index_delta": round(fatigue_after - fatigue_before, 2),
            "fatigue_index_delta_pct": (
                round(((fatigue_after - fatigue_before) / fatigue_before) * 100, 1)
                if fatigue_before
                else None
            ),
            "elevated_share_before": elevated_before,
            "elevated_share_after": elevated_after,
            "elevated_share_delta": round(elevated_after - elevated_before, 4),
        },
        "rule_deltas": rule_deltas,
        "assumption_snapshot": assumptions,
    }


def attrition_forecast(
    db: Session,
    *,
    unit_id: str,
    horizon_weeks: int,
    as_of: date,
) -> dict[str, Any]:
    """F07 screen 5 — rule-based forward trend of the composite pressure index.

    Not ML (ADR-0001): the horizon is the same projection function run with a
    'nothing changes' scenario, extrapolating the duty/deployment clocks that
    keep ticking on their own. Drivers are named so it reads as a planning
    input, not a verdict.
    """
    k = get_settings().k_anonymity
    points = []
    for week in range(0, horizon_weeks + 1):
        scenario = {"extend_deployment_days": min(180, week * 7)}
        run = project_unit(db, unit_id=unit_id, scenario=scenario, as_of=as_of)
        if run["suppressed"]:
            return {
                "unit_id": unit_id,
                "suppressed": True,
                "k": k,
                "reason_key": "heat.cell.suppressed",
            }
        points.append(
            {
                "week": week,
                "as_of": (as_of + timedelta(days=7 * week)).isoformat(),
                "index": run["projection"]["fatigue_index_after"],
                "elevated_share": run["projection"]["elevated_share_after"],
            }
        )

    first = points[0]["index"] if points else 0.0
    last = points[-1]["index"] if points else 0.0
    drivers = []
    baseline = project_unit(db, unit_id=unit_id, scenario={}, as_of=as_of)
    horizon = project_unit(
        db, unit_id=unit_id, scenario={"extend_deployment_days": min(180, horizon_weeks * 7)}, as_of=as_of
    )
    for row in horizon.get("rule_deltas", []):
        drivers.append(row)
    return {
        "unit_id": unit_id,
        "suppressed": False,
        "k": k,
        "horizon_weeks": horizon_weeks,
        "contributor_count": baseline.get("contributor_count"),
        "points": points,
        "index_now": first,
        "index_horizon": last,
        "index_delta": round(last - first, 2),
        "drivers": drivers,
        "assumption_snapshot": horizon.get("assumption_snapshot"),
        "disclaimer_key": "forecast.disclaimer",
    }
