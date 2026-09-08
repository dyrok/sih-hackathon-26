from __future__ import annotations

from typing import Any

from ..i18n import t


def format_value(key: str, observed: Any) -> str:
    if observed is None:
        return ""
    if key == "risk.factor.sleep_deviation":
        pct = round(float(observed) * 100)
        return f"{pct}%"
    if isinstance(observed, float):
        if observed == int(observed):
            return str(int(observed))
        return f"{observed:.2f}"
    return str(observed)


def top_factors(factors: list[dict[str, Any]], n: int = 3, lang: str = "en") -> list[dict[str, Any]]:
    ranked = sorted(factors, key=lambda f: float(f.get("weight") or 0), reverse=True)
    out = []
    for f in ranked[:n]:
        display_value = format_value(f["display_key"], f.get("observed_value"))
        out.append(
            {
                "key": f["display_key"],
                "rule_id": f.get("rule_id"),
                "value": display_value,
                "text": t(f["display_key"], lang, value=display_value),
                "weight": f.get("weight"),
            }
        )
    return out
