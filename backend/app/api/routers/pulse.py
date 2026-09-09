"""FR-19 anonymous unit pulse (F02 screen 8 → F07 screen 2).

The rating rows carry a pseudonym so that "one rating per member per period"
can be enforced — but **no read path returns it**. The only exit from this
module is a k-filtered per-facet aggregate. That asymmetry is the feature.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...clock import as_of
from ...config import get_settings
from ...consent import active_consent
from ...db import get_db
from ...firewall import forbid_commander
from ...ids import nid
from ...models import IdentityMap, UnitPulseRating, User
from ...security import require_roles

router = APIRouter(tags=["unit-pulse"])

FACETS = ("leadership", "fairness", "family_support", "facilities")
PULSE_BUNDLE = "unit_pulse"


def period_of(day: date) -> str:
    """ISO week label — the fixed cell definition (no ad-hoc slicing, RBAC §k>=5.3)."""
    year, week, _ = day.isocalendar()
    return "%04d-W%02d" % (year, week)


class PulseIn(BaseModel):
    facet: str
    rating: int = Field(ge=1, le=5)
    period: str | None = None


class PulseBatchIn(BaseModel):
    ratings: list[PulseIn]


def _unit_of(db: Session, pseudonym_id: str) -> str | None:
    row = db.query(IdentityMap).filter(IdentityMap.pseudonym_id == pseudonym_id).one_or_none()
    return row.unit_id if row else None


def _record(db: Session, user: User, item: PulseIn, day: date) -> dict:
    if item.facet not in FACETS:
        raise HTTPException(400, "facet must be one of %s" % ", ".join(FACETS))
    period = item.period or period_of(day)
    unit_id = _unit_of(db, user.pseudonym_id)
    if unit_id is None:
        raise HTTPException(409, "no unit on file for this principal")
    existing = (
        db.query(UnitPulseRating)
        .filter(
            UnitPulseRating.pseudonym_id == user.pseudonym_id,
            UnitPulseRating.period == period,
            UnitPulseRating.facet == item.facet,
        )
        .one_or_none()
    )
    if existing:
        # One rating per member per period (F02 screen 8). Re-rating replaces
        # your own answer; it never creates a second contributor.
        existing.rating = item.rating
        existing.recorded_at = day
        return {"facet": item.facet, "period": period, "replaced": True}
    db.add(
        UnitPulseRating(
            id=nid("pl"),
            pseudonym_id=user.pseudonym_id,
            unit_id=unit_id,
            period=period,
            facet=item.facet,
            rating=item.rating,
            recorded_at=day,
        )
    )
    return {"facet": item.facet, "period": period, "replaced": False}


@router.post("/app/pulse")
def submit_pulse(
    body: PulseBatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    if not active_consent(db, user.pseudonym_id, PULSE_BUNDLE):
        raise HTTPException(403, "unit pulse requires the unit_pulse consent bundle")
    day = as_of()
    results = [_record(db, user, item, day) for item in body.ratings]
    db.flush()
    write_audit(
        db,
        actor=user,
        action="pulse.submit",
        resource_type="unit_pulse_rating",
        subject_pseudonym_id=user.pseudonym_id,
        purpose="unit_climate",
        payload={"facets": [r["facet"] for r in results]},
    )
    return {"recorded": results, "aggregate_only": True}


@router.get("/app/pulse/me")
def my_pulse(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    """What *I* rated this period — so the app can show 'already rated'.
    Self-scope only; there is no query shape that reaches another principal."""
    period = period_of(as_of())
    rows = (
        db.query(UnitPulseRating)
        .filter(
            UnitPulseRating.pseudonym_id == user.pseudonym_id,
            UnitPulseRating.period == period,
        )
        .all()
    )
    return {
        "period": period,
        "facets": FACETS,
        "mine": {r.facet: r.rating for r in rows},
    }


@router.get("/aggregates/unit/{unit_id}/pulse")
def unit_pulse_aggregate(
    unit_id: str,
    period: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("commander", "counsellor", "welfare_officer", "auditor")),
):
    """k >= 5 per facet. A facet with fewer than k raters returns no numbers —
    no interpolation, no partial mean (RBAC matrix, k>=5 rule 1)."""
    if user.role == "commander" and user.unit_id and user.unit_id != unit_id:
        raise HTTPException(403, "commander may only view own unit chain")
    k = get_settings().k_anonymity
    period = period or period_of(as_of())
    rows = (
        db.query(UnitPulseRating)
        .filter(UnitPulseRating.unit_id == unit_id, UnitPulseRating.period == period)
        .all()
    )
    by_facet: dict[str, list[int]] = {f: [] for f in FACETS}
    raters: set[str] = set()
    for r in rows:
        by_facet.setdefault(r.facet, []).append(r.rating)
        raters.add(r.pseudonym_id)

    facets = {}
    for facet in FACETS:
        values = by_facet.get(facet, [])
        if len(values) < k:
            facets[facet] = {"n": None, "mean": None, "suppressed": True}
        else:
            facets[facet] = {
                "n": len(values),
                "mean": round(sum(values) / len(values), 2),
                "suppressed": False,
            }
    contributors = len(raters)
    write_audit(
        db,
        actor=user,
        action="pulse.aggregate.read",
        resource_type="unit_pulse_aggregate",
        resource_id=unit_id,
        purpose="unit_welfare_overview",
        payload={"period": period},
    )
    return {
        "unit_id": unit_id,
        "period": period,
        "k": k,
        "contributor_count": contributors if contributors >= k else None,
        "suppressed": contributors < k,
        "reason_key": "heat.cell.suppressed" if contributors < k else None,
        "facets": facets,
    }
