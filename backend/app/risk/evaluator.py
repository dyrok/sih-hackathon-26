from __future__ import annotations

import operator
from typing import Any

OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}


def _present(value: Any) -> bool:
    return value is not None


def evaluate_rules(signals: dict[str, Any], ruleset: dict[str, Any]) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    for rule in ruleset["rules"]:
        key = rule["inputs"][0]
        observed = signals.get(key)
        if not _present(observed):
            continue
        op = OPS[rule["op"]]
        if not op(float(observed), float(rule["threshold"])):
            continue
        factors.append(
            {
                "rule_id": rule["id"],
                "domain": rule["domain"],
                "weight": float(rule["weight"]),
                "observed_value": observed,
                "display_key": rule["explain_key"],
            }
        )
    return factors
