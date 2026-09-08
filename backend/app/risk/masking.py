from __future__ import annotations

from typing import Any


def detect_masking(
    *,
    signals: dict[str, Any],
    self_report_fine: bool,
    validity_fail: bool,
    straight_lining: bool,
    too_fast: bool,
    all_max: bool,
    voluntary_present: bool,
    ruleset: dict[str, Any],
) -> dict[str, Any] | None:
    """Discrepancy overlay. Null voluntary sources after withdrawal never manufacture a flag."""
    if not voluntary_present:
        return None
    cfg = ruleset.get("masking") or {}
    adv = cfg.get("adverse") or {}
    duty = float(signals.get("consecutive_duty_days") or 0)
    cancels = float(signals.get("leave_cancel_count") or 0)
    sleep_hours = signals.get("sleep_hours")
    sleep_dev = signals.get("sleep_deviation")
    adverse = duty >= float(adv.get("consecutive_duty_days", 60)) and cancels >= float(
        adv.get("leave_cancel_count", 2)
    )
    sleep_adverse = False
    if sleep_hours is not None and sleep_hours <= float(adv.get("sleep_hours", 4.5)):
        sleep_adverse = True
    if sleep_dev is not None and sleep_dev <= float(adv.get("sleep_deviation", -0.30)):
        sleep_adverse = True
    if not (adverse and sleep_adverse):
        return None
    matched = []
    if self_report_fine:
        matched.append("self_report_fine")
    if validity_fail:
        matched.append("validity_fail")
    if straight_lining:
        matched.append("straight_lining")
    if too_fast:
        matched.append("too_fast")
    if all_max:
        matched.append("all_max")
    if not matched:
        return None
    return {
        "matched_conditions": matched,
        "tier_floor": cfg.get("tier_floor", "red"),
        "extra_weight": float(cfg.get("extra_weight", 10)),
    }
