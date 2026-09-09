"""F07 — commander surface. Aggregates only, k >= 5, no ID parameters.

Every route in this module lives under ``/aggregates`` — the one prefix the
ADR-0003 middleware lets a commander token through — and none of them accepts
a personnel or pseudonym identifier. There is no individual-row response shape
defined anywhere in this file; that is the structural guarantee, not a filter.
"""

from __future__ import annotations

import statistics
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...clock import as_of
from ...config import get_settings
from ...db import get_db
from ...ids import nid
from ...models import (
    HrLeaveRecord,
    IdentityMap,
    InterventionAction,
    InterventionOutcome,
    ResponseCase,
    RiskScore,
    SignalSnapshot,
    SimulationRun,
    UnitPulseRating,
    User,
)
from ...privacy.kanonymity import aggregate_unit
from ...risk.aggregator import TIER_ORDER
from ...security import require_roles
from ...simulate.projection import (
    LEVERS,
    ScenarioError,
    attrition_forecast,
    project_unit,
)
from .pulse import FACETS, period_of

router = APIRouter(prefix="/aggregates", tags=["commander-aggregates"])

AGGREGATE_ROLES = ("commander", "counsellor", "welfare_officer", "auditor")


class SimulationIn(BaseModel):
    unit_id: str
    scenario: dict[str, Any] | None = None


def _guard_unit(user: User, unit_id: str) -> None:
    if user.role == "commander" and user.unit_id and user.unit_id != unit_id:
        raise HTTPException(403, "commander may only view own unit chain")


def _units(db: Session, user: User) -> list[str]:
    rows = db.query(IdentityMap.unit_id).distinct().all()
    units = sorted({r[0] for r in rows if r[0]})
    if user.role == "commander" and user.unit_id:
        units = [u for u in units if u == user.unit_id]
    return units


def _pids(db: Session, unit_id: str) -> list[str]:
    return [
        r.pseudonym_id for r in db.query(IdentityMap).filter(IdentityMap.unit_id == unit_id).all()
    ]


def _signal_values(db: Session, pids: list[str], key: str, day: date) -> list[float]:
    if not pids:
        return []
    rows = (
        db.query(SignalSnapshot)
        .filter(
            SignalSnapshot.pseudonym_id.in_(pids),
            SignalSnapshot.signal_key == key,
            SignalSnapshot.window_end == day,
        )
        .all()
    )
    return [float(r.value) for r in rows if r.value is not None]


def _suppressed(k: int, n: int) -> bool:
    return n < k


def _cell(k: int, values: list[float], round_to: int = 2) -> dict[str, Any]:
    """One aggregate cell. Below k it carries no numbers at all — not a rounded
    number, not a range, not a bucket (RBAC matrix, k>=5 rule 1)."""
    if _suppressed(k, len(values)):
        return {"n": None, "value": None, "suppressed": True, "reason_key": "heat.cell.suppressed"}
    return {
        "n": len(values),
        "value": round(sum(values) / len(values), round_to),
        "suppressed": False,
        "reason_key": None,
    }


@router.get("/units")
def units_overview(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*AGGREGATE_ROLES)),
):
    """F07 screen 1 — the heatmap grid. One cell per unit, k-filtered in the
    service; the client receives nothing it would have to hide."""
    k = get_settings().k_anonymity
    out = []
    for unit_id in _units(db, user):
        agg = aggregate_unit(db, unit_id)
        out.append(
            {
                "unit_id": unit_id,
                "k": k,
                "contributor_count": agg["n"],
                # A cell is suppressed whenever its share is not publishable —
                # not only when the unit itself is under the floor.
                "suppressed": agg["suppressed"],
                "elevated_share": agg["elevated_share"],
                "label_key": "heat.cell.label",
                "reason_key": agg["reason_key"],
            }
        )
    write_audit(
        db,
        actor=user,
        action="aggregates.units.read",
        resource_type="unit_aggregate",
        purpose="unit_welfare_overview",
        payload={"units": len(out)},
    )
    return {
        "as_of": as_of().isoformat(),
        "k": k,
        "units": out,
        "stale_key": "aggregate.stale",
    }


@router.get("/unit/{unit_id}/morale")
def morale(
    unit_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*AGGREGATE_ROLES)),
):
    """F07 screen 2 — a **computed index**, not a survey and not an officer's
    opinion. Components render on tap, so the number is never opaque."""
    _guard_unit(user, unit_id)
    k = get_settings().k_anonymity
    day = as_of()
    period = period_of(day)
    pids = _pids(db, unit_id)

    ratings = (
        db.query(UnitPulseRating)
        .filter(UnitPulseRating.unit_id == unit_id, UnitPulseRating.period == period)
        .all()
    )
    raters = {r.pseudonym_id for r in ratings}
    pulse_component = None
    if len(raters) >= k and ratings:
        # 1..5 → 0..100
        pulse_component = round(((sum(r.rating for r in ratings) / len(ratings)) - 1) / 4 * 100, 1)

    agg = aggregate_unit(db, unit_id)
    fatigue_component = None
    if agg["elevated_share"] is not None:
        fatigue_component = round((1.0 - agg["elevated_share"]) * 100, 1)

    sleep = _signal_values(db, pids, "consecutive_duty_days", day)
    streak_component = None
    if not _suppressed(k, len(sleep)):
        mean_streak = sum(sleep) / len(sleep)
        # 0 days → 100, 60+ days → 0. Linear, stated, not tuned.
        streak_component = round(max(0.0, min(100.0, 100.0 - (mean_streak / 60.0) * 100.0)), 1)

    parts = [p for p in (pulse_component, fatigue_component, streak_component) if p is not None]
    score = round(sum(parts) / len(parts), 1) if parts else None

    write_audit(
        db,
        actor=user,
        action="aggregates.morale.read",
        resource_type="morale_index",
        resource_id=unit_id,
        purpose="unit_welfare_overview",
    )
    return {
        "unit_id": unit_id,
        "week": period,
        "k": k,
        "score": score,
        "suppressed": score is None,
        "reason_key": "heat.cell.suppressed" if score is None else None,
        "computed_not_survey": True,
        "components": {
            "pulse_mean": {
                "value": pulse_component,
                "n": len(raters) if len(raters) >= k else None,
                "suppressed": pulse_component is None,
                "label_key": "morale.component.pulse",
                "facets": list(FACETS),
            },
            "fatigue_pct": {
                "value": fatigue_component,
                "n": agg["n"],
                "suppressed": fatigue_component is None,
                "label_key": "morale.component.fatigue",
            },
            "duty_streak": {
                "value": streak_component,
                "n": len(sleep) if not _suppressed(k, len(sleep)) else None,
                "suppressed": streak_component is None,
                "label_key": "morale.component.streak",
            },
        },
        "formula_key": "morale.formula",
    }


@router.get("/unit/{unit_id}/indicators")
def indicators(
    unit_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*AGGREGATE_ROLES)),
):
    """F07 screen 3 — leading and lagging always render together. The teaching
    point of the screen is that only the left column is actionable."""
    _guard_unit(user, unit_id)
    k = get_settings().k_anonymity
    day = as_of()
    pids = _pids(db, unit_id)

    streaks = _signal_values(db, pids, "consecutive_duty_days", day)
    nights = _signal_values(db, pids, "night_shift_ratio", day)
    exposure = _signal_values(db, pids, "days_in_high_risk_posting", day)

    cancels = 0
    applications = 0
    if pids:
        for row in db.query(HrLeaveRecord).filter(HrLeaveRecord.pseudonym_id.in_(pids)).all():
            applications += 1
            if row.cancelled_at is not None:
                cancels += 1
    cancel_rate = (
        {"n": applications, "value": round(cancels / applications, 3), "suppressed": False}
        if applications and not _suppressed(k, len(pids))
        else {"n": None, "value": None, "suppressed": True, "reason_key": "heat.cell.suppressed"}
    )

    streak_dist = {"n": None, "value": None, "suppressed": True, "reason_key": "heat.cell.suppressed"}
    if not _suppressed(k, len(streaks)):
        buckets = {"0-6": 0, "7-29": 0, "30-59": 0, "60+": 0}
        for v in streaks:
            if v < 7:
                buckets["0-6"] += 1
            elif v < 30:
                buckets["7-29"] += 1
            elif v < 60:
                buckets["30-59"] += 1
            else:
                buckets["60+"] += 1
        # A bucket smaller than k is folded up, never shown as a small count.
        safe = {name: (n if n >= k or n == 0 else None) for name, n in buckets.items()}
        streak_dist = {
            "n": len(streaks),
            "value": round(statistics.median(streaks), 1),
            "buckets": safe,
            "suppressed": False,
            "reason_key": None,
        }

    cases = db.query(ResponseCase).filter(ResponseCase.unit_id == unit_id).all()
    period_start = day - timedelta(days=28)
    opened = [
        c
        for c in cases
        if c.opened_at.date() >= period_start
        and TIER_ORDER.index(c.tier) >= TIER_ORDER.index("red")
    ]
    case_ids = [c.id for c in cases]
    actions = (
        db.query(InterventionAction).filter(InterventionAction.case_id.in_(case_ids)).all()
        if case_ids
        else []
    )
    outcomes = (
        db.query(InterventionOutcome).filter(InterventionOutcome.case_id.in_(case_ids)).all()
        if case_ids
        else []
    )
    first_action_by_case: dict[str, datetime] = {}
    for a in actions:
        prev = first_action_by_case.get(a.case_id)
        if prev is None or a.initiated_at < prev:
            first_action_by_case[a.case_id] = a.initiated_at
    lags = []
    for c in cases:
        first = first_action_by_case.get(c.id)
        if first is not None:
            lags.append(max(0.0, (first - c.opened_at).total_seconds() / 3600.0))

    outcome_counts: dict[str, int] = {}
    for o in outcomes:
        outcome_counts[o.outcome] = outcome_counts.get(o.outcome, 0) + 1
    # Counts below k are folded to None so a rare outcome cannot single anyone out.
    safe_outcomes = {name: (n if n >= k else None) for name, n in outcome_counts.items()}

    def _count_cell(n: int) -> dict[str, Any]:
        if _suppressed(k, len(pids)) or (0 < n < k):
            return {"value": None, "suppressed": True, "reason_key": "heat.cell.suppressed"}
        return {"value": n, "suppressed": False, "reason_key": None}

    write_audit(
        db,
        actor=user,
        action="aggregates.indicators.read",
        resource_type="unit_indicators",
        resource_id=unit_id,
        purpose="unit_welfare_overview",
    )
    return {
        "unit_id": unit_id,
        "as_of": day.isoformat(),
        "k": k,
        "contributor_count": len(pids) if not _suppressed(k, len(pids)) else None,
        "leading": [
            {"key": "ind.lead.duty_streak", **streak_dist},
            {"key": "ind.lead.leave_cancel_rate", **cancel_rate},
            {"key": "ind.lead.night_ratio", **_cell(k, nights, 3)},
            {"key": "ind.lead.deployment_exposure", **_cell(k, exposure, 1)},
        ],
        "lagging": [
            {"key": "ind.lag.red_flags", **_count_cell(len(opened))},
            {"key": "ind.lag.interventions", **_count_cell(len(actions))},
            {
                "key": "ind.lag.time_to_contact_h",
                **(
                    {"value": round(statistics.median(lags), 1), "suppressed": False, "reason_key": None}
                    if len(lags) >= k
                    else {"value": None, "suppressed": True, "reason_key": "heat.cell.suppressed"}
                ),
            },
            {
                "key": "ind.lag.outcomes",
                "value": safe_outcomes or None,
                "suppressed": not safe_outcomes,
                "reason_key": "heat.cell.suppressed" if not safe_outcomes else None,
            },
        ],
        "teaching_key": "ind.teaching",
    }


@router.get("/simulations/levers")
def simulation_levers(
    user: User = Depends(require_roles(*AGGREGATE_ROLES)),
):
    """The validated input ranges, so the UI can refuse bad input with the range
    shown instead of silently clamping it (F07 'Simulation edge')."""
    return {"levers": LEVERS}


@router.post("/simulations")
def run_simulation(
    body: SimulationIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("commander", "welfare_officer")),
):
    """F07 screen 4. A failed or suppressed simulation never mutates the live
    heatmap — nothing here writes a RiskScore."""
    _guard_unit(user, body.unit_id)
    try:
        result = project_unit(db, unit_id=body.unit_id, scenario=body.scenario, as_of=as_of())
    except ScenarioError as exc:
        raise HTTPException(400, str(exc)) from None
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    run = SimulationRun(
        id=nid("sim"),
        unit_id=body.unit_id,
        scenario_params=result["scenario"],
        projected_deltas=result.get("projection") or {},
        assumption_snapshot=result["assumption_snapshot"],
        created_by_role=user.role,
        created_at=now,
        expires_at=now + timedelta(hours=get_settings().jwt_expire_hours),
    )
    db.add(run)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="simulation.run",
        resource_type="simulation_run",
        resource_id=run.id,
        purpose="workload_rebalance",
        payload={"unit_id": body.unit_id, "scenario": result["scenario"]},
    )
    return {"run_id": run.id, **result}


@router.get("/simulations/{run_id}")
def get_simulation(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*AGGREGATE_ROLES)),
):
    row = db.get(SimulationRun, run_id)
    if row is None:
        raise HTTPException(404, "simulation not found")
    _guard_unit(user, row.unit_id)
    return {
        "run_id": row.id,
        "unit_id": row.unit_id,
        "scenario": row.scenario_params,
        "projection": row.projected_deltas,
        "assumption_snapshot": row.assumption_snapshot,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/unit/{unit_id}/forecast")
def forecast(
    unit_id: str,
    horizon_weeks: int = Query(8, ge=1, le=26),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*AGGREGATE_ROLES)),
):
    """F07 screen 5 — a rotation-planning input, not a verdict on anyone."""
    _guard_unit(user, unit_id)
    result = attrition_forecast(db, unit_id=unit_id, horizon_weeks=horizon_weeks, as_of=as_of())
    write_audit(
        db,
        actor=user,
        action="aggregates.forecast.read",
        resource_type="attrition_forecast",
        resource_id=unit_id,
        purpose="unit_welfare_overview",
    )
    return result


@router.get("/unit/{unit_id}/trend")
def unit_trend(
    unit_id: str,
    weeks: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*AGGREGATE_ROLES)),
):
    """Aggregate elevated-share over time. Every weekly point is k-filtered on
    its own — a quiet week cannot be differenced against a busy one."""
    _guard_unit(user, unit_id)
    k = get_settings().k_anonymity
    pids = set(_pids(db, unit_id))
    if not pids:
        return {"unit_id": unit_id, "k": k, "points": [], "suppressed": True}
    day = as_of()
    points = []
    for i in range(weeks - 1, -1, -1):
        end = day - timedelta(days=7 * i)
        start = end - timedelta(days=6)
        rows = (
            db.query(RiskScore)
            .filter(
                RiskScore.pseudonym_id.in_(list(pids)),
                RiskScore.as_of >= start,
                RiskScore.as_of <= end,
            )
            .all()
        )
        latest: dict[str, RiskScore] = {}
        for r in rows:
            prev = latest.get(r.pseudonym_id)
            if prev is None or r.as_of > prev.as_of:
                latest[r.pseudonym_id] = r
        n = len(latest)
        if n < k:
            points.append(
                {
                    "week_end": end.isoformat(),
                    "n": None,
                    "elevated_share": None,
                    "suppressed": True,
                }
            )
            continue
        elevated = sum(
            1 for r in latest.values() if TIER_ORDER.index(r.tier) >= TIER_ORDER.index("amber")
        )
        points.append(
            {
                "week_end": end.isoformat(),
                "n": n,
                "elevated_share": round(elevated / n, 3),
                "suppressed": False,
            }
        )
    return {"unit_id": unit_id, "k": k, "points": points, "stale_key": "aggregate.stale"}
