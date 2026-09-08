from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import IdentityMap, RiskScore


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


def aggregate_unit(db: Session, unit_id: str) -> dict[str, Any]:
    """Commander-safe unit aggregate. Cells with 0 < n < k are suppressed with complement."""
    k = get_settings().k_anonymity
    tiers = _latest_tiers(db, unit_id)
    n = len(tiers)
    counts = Counter(tiers)
    cells: dict[str, dict[str, Any]] = {}
    suppressed_keys: list[str] = []
    for name in ("green", "amber", "red", "critical"):
        c = counts.get(name, 0)
        if 0 < c < k:
            cells[name] = {"n": None, "suppressed": True}
            suppressed_keys.append(name)
        else:
            cells[name] = {"n": c, "suppressed": False}

    # Complement suppression: if a cell is hidden, hide the smallest remaining
    # uns-suppressed cell so subtraction cannot recover the small cell.
    if suppressed_keys:
        remaining = [(name, cells[name]["n"]) for name in cells if not cells[name]["suppressed"] and cells[name]["n"]]
        remaining.sort(key=lambda kv: kv[1])
        if remaining:
            name, _ = remaining[0]
            cells[name] = {"n": None, "suppressed": True}
            suppressed_keys.append(name)

    elevated = sum(1 for t in tiers if t in {"amber", "red", "critical"})
    elevated_share = None
    if elevated >= k and n >= k:
        elevated_share = round(elevated / n, 3)
    morale = None
    green = counts.get("green", 0)
    if n >= k and green >= k:
        morale = round(green / n, 3)

    return {
        "unit_id": unit_id,
        "k": k,
        "n": n if n >= k else None,
        "n_suppressed": n < k,
        "cells": cells,
        "elevated_share": elevated_share,
        "morale_index": morale,
        "suppressed_keys": suppressed_keys,
    }
