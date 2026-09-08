"""Backtest the v1 rules engine on the scripted persona + a synthetic population.

ML-002. Consumes the same seed-42 / DEMO-PERSONA-01 fixture the tests use.
QA-001 (neel, F09 CLI) should converge on this seed; this harness does not wait on it.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from ..clock import set_as_of
from ..models import MaskingFlag, RiskScore
from ..risk.scorer import score_person
from ..seed import PERSONA_PSEUDONYM, day, seed_demo
from ..signals.snapshot import recompute_all

# Scripted arc (F09) — flag days the engine must hit.
EXPECTED = {
    30: {"max_tier": "green"},
    62: {"min_tier": "amber"},
    64: {"masking": True, "min_tier": "red"},
    65: {"min_tier": "red"},
}

TIER_ORDER = ["green", "amber", "red", "critical"]


def _tier_at_least(actual: str, minimum: str) -> bool:
    return TIER_ORDER.index(actual) >= TIER_ORDER.index(minimum)


def _tier_at_most(actual: str, maximum: str) -> bool:
    return TIER_ORDER.index(actual) <= TIER_ORDER.index(maximum)


def score_on_day(db: Session, n: int) -> RiskScore:
    as_of = day(n)
    set_as_of(as_of)
    recompute_all(db, as_of, only=[PERSONA_PSEUDONYM])
    return score_person(db, PERSONA_PSEUDONYM, as_of=as_of, emit_case=True)


def persona_arc(db: Session) -> dict[str, Any]:
    diffs = []
    timeline = []
    for n, spec in EXPECTED.items():
        row = score_on_day(db, n)
        mask = db.query(MaskingFlag).filter(MaskingFlag.score_id == row.id).one_or_none()
        point = {
            "day": n,
            "as_of": row.as_of.isoformat(),
            "score": row.score,
            "tier": row.tier,
            "masking": bool(mask),
            "factors": [
                {"key": f.display_key, "value": f.display_value, "weight": f.weight} for f in row.factors
            ],
        }
        timeline.append(point)
        if "min_tier" in spec and not _tier_at_least(row.tier, spec["min_tier"]):
            diffs.append({"day": n, "field": "tier", "expected_min": spec["min_tier"], "actual": row.tier})
        if "max_tier" in spec and not _tier_at_most(row.tier, spec["max_tier"]):
            diffs.append({"day": n, "field": "tier", "expected_max": spec["max_tier"], "actual": row.tier})
        if spec.get("masking") and not mask:
            diffs.append({"day": n, "field": "masking", "expected": True, "actual": False})
    return {"timeline": timeline, "diffs": diffs, "ok": not diffs}


def threshold_sweep(db: Session, day_n: int = 65) -> list[dict[str, Any]]:
    """TC-801: report flags across a duty-day threshold sweep (documented, not vibes)."""
    as_of = day(day_n)
    set_as_of(as_of)
    recompute_all(db, as_of, only=[PERSONA_PSEUDONYM])
    row = score_person(db, PERSONA_PSEUDONYM, as_of=as_of, emit_case=False)
    out = []
    for thresh in (40, 50, 60, 70, 80):
        flagged = row.score >= thresh
        out.append(
            {
                "score_threshold": thresh,
                "persona_score": row.score,
                "flagged": flagged,
                "fp_cost": "one cup of tea with a counsellor" if flagged else None,
                "fn_cost": "a life" if not flagged else None,
            }
        )
    return out


def v2_readiness(db: Session) -> dict[str, Any]:
    from ..models import InterventionOutcome

    n = db.query(InterventionOutcome).filter(InterventionOutcome.label_exported.is_(True)).count()
    return {
        "labels": n,
        "defensible": n >= 200,
        "note": "ML v2 trains only on counsellor outcome labels (ADR-0001). Rules stay the product until then.",
    }


def run(db: Session) -> dict[str, Any]:
    seed_demo(db, score=False)
    arc = persona_arc(db)
    sweep = threshold_sweep(db)
    ready = v2_readiness(db)
    return {
        "seed": 42,
        "persona": "DEMO-PERSONA-01 Constable 34 3rd Bn",
        "arc": arc,
        "threshold_sweep": sweep,
        "v2_readiness": ready,
    }


def main() -> None:
    from ..db import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        report = run(db)
        db.commit()
        print(json.dumps(report, indent=2, default=str))
        if not report["arc"]["ok"]:
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
