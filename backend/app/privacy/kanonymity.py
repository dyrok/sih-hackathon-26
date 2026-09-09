from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import IdentityMap, RiskScore

TIERS = ("green", "amber", "red", "critical")
ELEVATED = ("amber", "red", "critical")


def _latest_tiers(db: Session, unit_id: str) -> list[str]:
    people = db.query(IdentityMap).filter(IdentityMap.unit_id == unit_id).all()
    tiers = []
    for p in people:
        rs = (
            db.query(RiskScore)
            .filter(RiskScore.pseudonym_id == p.pseudonym_id)
            .order_by(RiskScore.computed_at.desc())
            .first()
        )
        tiers.append(rs.tier if rs else "green")
    return tiers


def _two_sided(count: int, n: int, k: int) -> bool:
    """A group is publishable only if BOTH sides of it clear the floor.

    Publishing "170 of 200 are green" tells anyone who knows the unit strength
    that 30 are not — and 30 is fine, but the same arithmetic on "199 of 200"
    identifies one person. A one-sided k check misses that entirely, which is
    how a suppressed cell of one stayed recoverable (TC-451).
    """
    return count >= k and (n - count) >= k


def aggregate_unit(db: Session, unit_id: str, *, detailed: bool = False) -> dict[str, Any]:
    """Unit aggregate.

    Two projections, because two audiences need different things and only one of
    them is behind the ADR-0003 firewall:

    ``detailed=False`` (**the commander projection**, and the auditor's) returns
    exactly what F07 screen 1 specifies — the share of the unit above their own
    elevated-fatigue threshold — and nothing else. There is deliberately no
    per-tier frequency table here: a table with one small cell is recoverable by
    subtraction the moment the reader knows the unit's strength, and a commander
    always knows their unit's strength. Removing the table removes the attack;
    suppressing cells inside it only moved the attack around.

    ``detailed=True`` (counsellor / welfare officer, who work individual cases
    anyway) adds the per-tier counts under the same two-sided floor.
    """
    k = get_settings().k_anonymity
    tiers = _latest_tiers(db, unit_id)
    n = len(tiers)
    counts = dict(Counter(tiers))

    unit_too_small = n < k
    elevated = sum(counts.get(t, 0) for t in ELEVATED)
    green = counts.get("green", 0)

    publishable = (not unit_too_small) and _two_sided(elevated, n, k)
    elevated_share = round(elevated / n, 3) if publishable else None
    morale_index = round(green / n, 3) if publishable else None

    out: dict[str, Any] = {
        "unit_id": unit_id,
        "k": k,
        # `n` on its own identifies nobody; it is the *combination* of a total
        # with a near-total cell that leaks, and no cell ships unless it is
        # publishable on both sides.
        "n": None if unit_too_small else n,
        "n_suppressed": unit_too_small,
        "elevated_share": elevated_share,
        "morale_index": morale_index,
        "suppressed": elevated_share is None,
        "reason_key": "heat.cell.suppressed" if elevated_share is None else None,
    }

    if detailed:
        # The table is all-or-nothing. Publishing three tiers and hiding the
        # fourth hands the fourth back the moment the reader knows the total.
        # So the per-tier split ships only when every tier clears the two-sided
        # floor; the useful headline (n, the share) survives either way.
        publishable_table = (not unit_too_small) and all(
            counts.get(name, 0) == 0 or _two_sided(counts.get(name, 0), n, k) for name in TIERS
        )
        out["cells"] = {
            name: (
                {"n": counts.get(name, 0), "suppressed": False}
                if publishable_table
                else {"n": None, "suppressed": True}
            )
            for name in TIERS
        }
        out["table_suppressed"] = not publishable_table

    return out
