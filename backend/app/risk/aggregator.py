from __future__ import annotations

from typing import Any

TIER_ORDER = ["green", "amber", "red", "critical"]


def aggregate(factors: list[dict[str, Any]], ruleset: dict[str, Any]) -> tuple[int, dict[str, float]]:
    caps = {k: float(v["cap"]) for k, v in ruleset["domains"].items()}
    domain_sums: dict[str, float] = {k: 0.0 for k in caps}
    for f in factors:
        domain_sums[f["domain"]] = domain_sums.get(f["domain"], 0.0) + float(f["weight"])
    capped = {d: min(caps.get(d, total), total) for d, total in domain_sums.items()}
    score = int(round(max(0.0, min(100.0, sum(capped.values())))))
    return score, capped


def tier_for(score: int, ruleset: dict[str, Any]) -> str:
    for name, (lo, hi) in ruleset["tiers"].items():
        if lo <= score <= hi:
            return name
    return "critical" if score > 100 else "green"


def apply_hysteresis(previous: str | None, candidate: str, confirmations: int, needed: int) -> tuple[str, bool]:
    if previous is None:
        return candidate, False
    if TIER_ORDER.index(candidate) >= TIER_ORDER.index(previous):
        return candidate, False
    if confirmations + 1 >= needed:
        return candidate, False
    return previous, True


def floor_tier(current: str, floor: str | None) -> str:
    if floor is None:
        return current
    if TIER_ORDER.index(floor) > TIER_ORDER.index(current):
        return floor
    return current
