from __future__ import annotations

from app.risk.aggregator import aggregate, apply_hysteresis, floor_tier, tier_for
from app.risk.evaluator import evaluate_rules
from app.risk.masking import detect_masking
from app.risk.ruleset import load_ruleset


def test_ruleset_loads():
    rs = load_ruleset()
    assert rs["version"] == 1
    assert len(rs["rules"]) >= 8


def test_masking_canonical_case():
    rs = load_ruleset()
    flag = detect_masking(
        signals={"consecutive_duty_days": 60, "leave_cancel_count": 2, "sleep_hours": 4.0, "sleep_deviation": -0.30},
        self_report_fine=True,
        validity_fail=False,
        straight_lining=False,
        too_fast=False,
        all_max=False,
        voluntary_present=True,
        ruleset=rs,
    )
    assert flag is not None
    assert flag["tier_floor"] == "red"


def test_masking_suppressed_after_withdrawal():
    rs = load_ruleset()
    flag = detect_masking(
        signals={"consecutive_duty_days": 60, "leave_cancel_count": 2, "sleep_hours": 4.0},
        self_report_fine=True,
        validity_fail=False,
        straight_lining=False,
        too_fast=False,
        all_max=False,
        voluntary_present=False,
        ruleset=rs,
    )
    assert flag is None


def test_domain_caps_and_score_range():
    rs = load_ruleset()
    factors = [
        {"domain": "duty", "weight": 12},
        {"domain": "duty", "weight": 8},
        {"domain": "leave", "weight": 8},
        {"domain": "leave", "weight": 6},
        {"domain": "health", "weight": 10},
    ]
    score, capped = aggregate(factors, rs)
    assert capped["duty"] == 18  # 12+8 capped at 18
    assert 0 <= score <= 100
    assert tier_for(score, rs) in {"green", "amber", "red", "critical"}


def test_hysteresis_holds_downgrade():
    held_tier, held = apply_hysteresis("red", "amber", confirmations=0, needed=2)
    assert held_tier == "red" and held
    released, held2 = apply_hysteresis("red", "amber", confirmations=1, needed=2)
    assert released == "amber" and not held2


def test_evaluate_duty_rule():
    rs = load_ruleset()
    factors = evaluate_rules({"consecutive_duty_days": 60}, rs)
    ids = {f["rule_id"] for f in factors}
    assert "R-DUT-01" in ids


def test_floor_tier():
    assert floor_tier("amber", "red") == "red"
    assert floor_tier("critical", "red") == "critical"
