from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..clock import as_of as clock_as_of
from ..config import get_settings
from ..consent import has_voluntary_consent
from ..ids import nid
from ..models import (
    CheckIn,
    InstrumentResult,
    MaskingFlag,
    PassiveFeature,
    PersonBaseline,
    ResponseCase,
    RiskFactor,
    RiskScore,
    SignalGroupFlag,
    SignalSnapshot,
    IdentityMap,
)
from ..interventions.cases import open_or_update_case, open_group_case
from .aggregator import TIER_ORDER, aggregate, apply_hysteresis, floor_tier, tier_for
from .baseline import sleep_baseline_and_dev
from .evaluator import evaluate_rules
from .explainer import format_value
from .masking import detect_masking
from .ruleset import load_ruleset


def _latest_snapshots(db: Session, pid: str, as_of: date) -> dict[str, Any]:
    rows = (
        db.query(SignalSnapshot)
        .filter(SignalSnapshot.pseudonym_id == pid, SignalSnapshot.window_end == as_of)
        .all()
    )
    return {r.signal_key: r.value for r in rows}


def _sleep_series(db: Session, pid: str) -> list[tuple[date, float]]:
    series: list[tuple[date, float]] = []
    for row in db.query(CheckIn).filter(CheckIn.pseudonym_id == pid, CheckIn.purged.is_(False)).all():
        if row.sleep_hours is not None:
            series.append((row.recorded_at, float(row.sleep_hours)))
    for row in db.query(PassiveFeature).filter(PassiveFeature.pseudonym_id == pid).all():
        if row.sleep_hours_proxy is not None:
            series.append((row.recorded_at, float(row.sleep_hours_proxy)))
    series.sort()
    return series


def _self_report_state(db: Session, pid: str, as_of: date, voluntary: bool) -> dict[str, Any]:
    if not voluntary:
        return {
            "fine": False,
            "validity_fail": False,
            "straight_lining": False,
            "too_fast": False,
            "all_max": False,
            "phq9": None,
            "item_9": None,
            "sleep_hours": None,
            "mood_label": None,
        }
    checkin = (
        db.query(CheckIn)
        .filter(CheckIn.pseudonym_id == pid, CheckIn.purged.is_(False), CheckIn.recorded_at <= as_of)
        .order_by(CheckIn.recorded_at.desc())
        .first()
    )
    inst = (
        db.query(InstrumentResult)
        .filter(
            InstrumentResult.pseudonym_id == pid,
            InstrumentResult.purged.is_(False),
            InstrumentResult.instrument == "PHQ-9",
            InstrumentResult.recorded_at <= as_of,
        )
        .order_by(InstrumentResult.recorded_at.desc())
        .first()
    )
    fine = False
    if checkin is not None:
        label = (checkin.mood_label or "").lower()
        fine = label in {"fine", "good", "great"} or (checkin.mood_score is not None and checkin.mood_score >= 4)
    return {
        "fine": fine,
        "validity_fail": bool(inst.validity_fail) if inst else False,
        "straight_lining": bool(inst.straight_lining) if inst else False,
        "too_fast": bool(inst.too_fast) if inst else False,
        "all_max": bool(inst.all_max) if inst else False,
        "phq9": inst.score if inst else None,
        "item_9": inst.item_9 if inst else None,
        "sleep_hours": checkin.sleep_hours if checkin else None,
        "mood_label": checkin.mood_label if checkin else None,
    }


def _previous_tier(db: Session, pid: str, as_of: date) -> str | None:
    row = (
        db.query(RiskScore)
        .filter(RiskScore.pseudonym_id == pid, RiskScore.as_of < as_of)
        .order_by(RiskScore.as_of.desc(), RiskScore.computed_at.desc())
        .first()
    )
    return row.tier if row else None


def _downgrade_confirmations(db: Session, pid: str, previous: str, as_of: date) -> int:
    """How many consecutive recent cycles the *rules* said "lower than this".

    Counts the pre-hysteresis candidate, not the published tier. Counting the
    published tier is circular: hysteresis holds the old tier, the hold is
    stored, the next cycle reads the hold as evidence that nothing improved, and
    the person never comes down however much their signals recover. That is the
    opposite of welfare — the arc has to be able to close (F09 days 75-90).
    """
    rows = (
        db.query(RiskScore)
        .filter(RiskScore.pseudonym_id == pid, RiskScore.as_of < as_of)
        .order_by(RiskScore.as_of.desc(), RiskScore.computed_at.desc())
        .limit(5)
        .all()
    )
    n = 0
    for r in rows:
        observed = r.candidate_tier or r.tier
        if TIER_ORDER.index(observed) < TIER_ORDER.index(previous):
            n += 1
        else:
            break
    return n


def score_person(db: Session, pid: str, as_of: date | None = None, emit_case: bool = True) -> RiskScore:
    as_of = as_of or clock_as_of()
    settings = get_settings()
    ruleset = load_ruleset()
    signals = _latest_snapshots(db, pid, as_of)
    voluntary = has_voluntary_consent(db, pid)
    report = _self_report_state(db, pid, as_of, voluntary)
    series = _sleep_series(db, pid) if voluntary else []
    base, sleep_dev, cp, history_days = sleep_baseline_and_dev(
        series,
        as_of,
        window_days=int(ruleset.get("baseline", {}).get("window_days", 60)),
        min_history_days=int(ruleset.get("baseline", {}).get("min_history_days", 14)),
    )
    existing_b = (
        db.query(PersonBaseline)
        .filter(PersonBaseline.pseudonym_id == pid, PersonBaseline.signal_key == "sleep_hours")
        .one_or_none()
    )
    if existing_b:
        existing_b.baseline_mean = base
        existing_b.deviation = sleep_dev
        existing_b.change_point_at = cp
        existing_b.history_days = history_days
    else:
        db.add(
            PersonBaseline(
                id=nid("bl"),
                pseudonym_id=pid,
                signal_key="sleep_hours",
                window_days=60,
                baseline_mean=base,
                deviation=sleep_dev,
                change_point_at=cp,
                history_days=history_days,
            )
        )

    ctx = dict(signals)
    ctx["sleep_deviation"] = sleep_dev
    ctx["sleep_hours"] = report["sleep_hours"]
    ctx["phq9"] = report["phq9"] if voluntary else None

    sources = ["hr"]
    if voluntary and (report["sleep_hours"] is not None or report["mood_label"] or report["phq9"] is not None):
        sources.append("self")
    if voluntary and db.query(PassiveFeature).filter(PassiveFeature.pseudonym_id == pid).first():
        sources.append("passive")

    confidence = "high"
    if history_days < int(ruleset.get("baseline", {}).get("min_history_days", 14)):
        confidence = "low"
    if "self" not in sources:
        confidence = "medium" if confidence == "high" else confidence

    factors = evaluate_rules(ctx, ruleset)
    mask = detect_masking(
        signals=ctx,
        self_report_fine=report["fine"],
        validity_fail=report["validity_fail"],
        straight_lining=report["straight_lining"],
        too_fast=report["too_fast"],
        all_max=report["all_max"],
        voluntary_present=voluntary,
        ruleset=ruleset,
    )
    if mask:
        factors.append(
            {
                "rule_id": "R-MAS-01",
                "domain": "psych",
                "weight": mask["extra_weight"],
                "observed_value": ",".join(mask["matched_conditions"]),
                "display_key": "risk.factor.masking",
            }
        )

    score, _capped = aggregate(factors, ruleset)
    candidate = tier_for(score, ruleset)
    if mask:
        candidate = floor_tier(candidate, mask["tier_floor"])
    crisis = voluntary and report["item_9"] is not None and report["item_9"] >= int(
        ruleset.get("crisis", {}).get("phq9_item_9_min", 1)
    )
    if crisis:
        candidate = "critical"

    ident = db.query(IdentityMap).filter(IdentityMap.pseudonym_id == pid).one_or_none()
    unit_id = ident.unit_id if ident else None
    group_incident = None
    if unit_id:
        flag = (
            db.query(SignalGroupFlag)
            .filter(
                SignalGroupFlag.unit_id == unit_id,
                SignalGroupFlag.signal_key == "unit_incident_exposure",
                SignalGroupFlag.value == 1,
            )
            .first()
        )
        if flag:
            group_incident = flag.incident_id
            if (flag.valid_until is None or flag.valid_until >= as_of) and flag.valid_from <= as_of:
                # group case is opened separately; do not stack into individual score (F04 R-GRP-01)
                pass

    previous = _previous_tier(db, pid, as_of)
    needed = int(ruleset.get("hysteresis", {}).get("downgrade_confirmations", 2))
    confs = _downgrade_confirmations(db, pid, previous, as_of) if previous else 0
    raw_candidate = candidate
    candidate, held = apply_hysteresis(previous, candidate, confs, needed)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = RiskScore(
        id=nid("rs"),
        pseudonym_id=pid,
        score=score,
        tier=candidate,
        confidence=confidence,
        engine_version=settings.engine_version,
        ruleset_version=int(ruleset["version"]),
        computed_at=now,
        as_of=as_of,
        sources_present=sources,
        stale=False,
        hysteresis_held=held,
        candidate_tier=raw_candidate,
    )
    db.add(row)
    db.flush()
    for f in factors:
        db.add(
            RiskFactor(
                id=nid("rf"),
                score_id=row.id,
                rule_id=f["rule_id"],
                domain=f["domain"],
                weight=f["weight"],
                observed_value=format_value(f["display_key"], f.get("observed_value")),
                display_key=f["display_key"],
                display_value=format_value(f["display_key"], f.get("observed_value")),
            )
        )
    if mask:
        db.add(
            MaskingFlag(
                id=nid("msk"),
                score_id=row.id,
                matched_conditions=mask["matched_conditions"],
                tier_floor=mask["tier_floor"],
            )
        )
    db.flush()
    if emit_case and TIER_ORDER.index(candidate) >= TIER_ORDER.index("amber"):
        open_or_update_case(db, pid, row, unit_id=unit_id)
    if emit_case and group_incident:
        open_group_case(db, unit_id=unit_id, incident_id=group_incident, score_id=row.id)
    return row


def recompute_many(db: Session, pids: list[str] | None, as_of: date | None = None) -> int:
    as_of = as_of or clock_as_of()
    if pids is None:
        pids = [r.pseudonym_id for r in db.query(IdentityMap).all()]
    n = 0
    for pid in pids:
        score_person(db, pid, as_of=as_of)
        n += 1
    return n
