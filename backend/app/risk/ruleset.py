from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ..config import RULESET_PATH


class RulesetError(RuntimeError):
    pass


def _validate(data: dict[str, Any]) -> dict[str, Any]:
    if "version" not in data or "rules" not in data or "tiers" not in data:
        raise RulesetError("ruleset missing version/rules/tiers")
    for rule in data["rules"]:
        for key in ("id", "domain", "weight", "inputs", "op", "threshold", "explain_key"):
            if key not in rule:
                raise RulesetError(f"rule missing {key}: {rule}")
    return data


@lru_cache
def load_ruleset(path: str | None = None) -> dict[str, Any]:
    p = Path(path) if path else RULESET_PATH
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RulesetError(f"cannot load ruleset: {exc}") from exc
    return _validate(data)


def clear_ruleset_cache() -> None:
    load_ruleset.cache_clear()
