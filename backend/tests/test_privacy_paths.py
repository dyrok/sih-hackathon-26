"""Coverage for the paths that only run when something has gone wrong.

The test-plan §7 gate asks for >= 90% on the rules engine and the firewall
routes. The lines that were missing were exactly the ones worth having: the
refusal branches in the caseload guard, the retention job's purge bodies, the
individual masking conditions, and the ruleset loader's validation errors —
i.e. everything that only executes on a bad day.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app import authz
from app.db import SessionLocal
from app.ids import nid
from app.models import (
    CheckIn,
    InstrumentResult,
    PassiveFeature,
    ResponseCase,
    User,
    VoiceFeature,
)
from app.privacy.expiry import expire_raw
from app.risk.masking import detect_masking
from app.risk.ruleset import RulesetError, clear_ruleset_cache, load_ruleset
from tests.conftest import auth_header

PERSONA = "ps_demo01"


# ---------------------------------------------------------------------------
# authz — the refusal branches
# ---------------------------------------------------------------------------


def _user(role: str, **kw) -> User:
    return User(
        id="u_" + role,
        username=role,
        password_hash="x",
        role=role,
        display_name=role,
        is_active=True,
        **kw,
    )


def _case(unit_id: str | None = "3BN") -> ResponseCase:
    return ResponseCase(
        id=nid("cs"),
        pseudonym_id=PERSONA,
        unit_id=unit_id,
        tier="red",
        opened_at=datetime.now(timezone.utc).replace(tzinfo=None),
        status="open",
        group_case=False,
        sla_hours=24,
    )


def test_a_subject_with_no_case_is_invisible_to_everyone(client):
    """The base case of "curiosity browsing is structurally impossible":
    no case, no read — for either role that has a caseload."""
    db = SessionLocal()
    try:
        for role in ("counsellor", "welfare_officer"):
            user = _user(role, assigned_units=["3BN"] if role == "welfare_officer" else None)
            assert authz.may_read_subject(db, user, "ps_nobody_has_a_case_for_this") is False
    finally:
        db.close()


def test_a_role_without_a_caseload_can_never_read_a_subject(client):
    db = SessionLocal()
    try:
        for role in ("admin", "auditor", "commander", "jawan", "hr_ingest"):
            assert authz.may_read_subject(db, _user(role), PERSONA) is False
    finally:
        db.close()


def test_welfare_officer_scope_follows_the_case_unit(client):
    db = SessionLocal()
    try:
        case = db.query(ResponseCase).filter(ResponseCase.pseudonym_id == PERSONA).first()
        assert case is not None and case.unit_id == "3BN"
        assert authz.may_read_subject(db, _user("welfare_officer", assigned_units=["3BN"]), PERSONA) is True
        assert authz.may_read_subject(db, _user("welfare_officer", assigned_units=["OTHER"]), PERSONA) is False
        # Unset must never widen: an officer with no assignment sees nothing.
        assert authz.may_read_subject(db, _user("welfare_officer", assigned_units=[]), PERSONA) is False
        assert authz.may_read_subject(db, _user("welfare_officer"), PERSONA) is False
    finally:
        db.close()


def test_assert_case_scope_refuses_a_welfare_officer_outside_their_units(client):
    from fastapi import HTTPException

    db = SessionLocal()
    try:
        case = _case("ELSEWHERE")
        user = _user("welfare_officer", assigned_units=["3BN"])
        with pytest.raises(HTTPException) as exc:
            authz.assert_case_scope(db, user, case)
        assert exc.value.status_code == 403
        assert "assigned units" in str(exc.value.detail)
        # …and permits one inside them.
        authz.assert_case_scope(db, user, _case("3BN"))
    finally:
        db.close()


def test_assert_case_scope_refuses_a_role_that_has_no_caseload_at_all(client):
    from fastapi import HTTPException

    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as exc:
            authz.assert_case_scope(db, _user("admin"), _case())
        assert exc.value.status_code == 403
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Retention — the purge bodies
# ---------------------------------------------------------------------------


def test_expiry_nulls_raw_content_and_keeps_the_row(client):
    """FR-18: raws are purged, derived trends persist. Content is nulled in
    place rather than the row deleted, so the trend keeps its shape."""
    as_of = date(2026, 9, 1)
    old = as_of - timedelta(days=200)
    db = SessionLocal()
    try:
        db.add(
            CheckIn(
                id="ck_old",
                pseudonym_id=PERSONA,
                recorded_at=old,
                mood_label="fine",
                mood_score=8,
                sleep_hours=4.0,
                expires_at=old + timedelta(days=90),
                purged=False,
            )
        )
        db.add(
            InstrumentResult(
                id="in_old",
                pseudonym_id=PERSONA,
                instrument="PHQ-9",
                score=17,
                item_9=1,
                recorded_at=old,
                expires_at=old + timedelta(days=90),
                purged=False,
            )
        )
        db.add(
            VoiceFeature(
                id="vf_old",
                pseudonym_id=PERSONA,
                recorded_at=old,
                f0_mean=140.0,
                speech_rate=3.2,
                duration_s=12.0,
                model_version="web-prosody-v1",
                schema_version="v1",
                expires_at=old + timedelta(days=90),
                purged=False,
            )
        )
        db.add(
            PassiveFeature(
                id="pf_old", pseudonym_id=PERSONA, sleep_hours_proxy=4.4, recorded_at=old
            )
        )
        db.commit()

        result = expire_raw(db, as_of)
        db.commit()
        assert result["checkins_purged"] >= 1
        assert result["instruments_purged"] >= 1
        assert result["voice_purged"] >= 1
        assert result["passive_purged"] >= 1

        ck = db.get(CheckIn, "ck_old")
        assert ck is not None and ck.purged is True
        assert ck.mood_label is None and ck.mood_score is None and ck.sleep_hours is None

        inst = db.get(InstrumentResult, "in_old")
        assert inst is not None and inst.purged is True and inst.item_9 is None

        vf = db.get(VoiceFeature, "vf_old")
        assert vf is not None and vf.purged is True
        assert vf.f0_mean is None and vf.speech_rate is None
        # The shape of the record survives — only its content goes.
        assert vf.duration_s == 12.0

        assert db.get(PassiveFeature, "pf_old") is None

        # Idempotent: a second run finds nothing left to do.
        again = expire_raw(db, as_of)
        db.commit()
        assert again == {
            "checkins_purged": 0,
            "instruments_purged": 0,
            "passive_purged": 0,
            "voice_purged": 0,
            "cutoff": again["cutoff"],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Masking — each condition, one at a time
# ---------------------------------------------------------------------------


ADVERSE = {"consecutive_duty_days": 62.0, "leave_cancel_count": 2.0, "sleep_deviation": -0.35}

#: detect_masking takes all five response-style flags; helper keeps callers short.
NO_FLAGS = {
    "self_report_fine": False,
    "validity_fail": False,
    "straight_lining": False,
    "too_fast": False,
    "all_max": False,
}


@pytest.mark.parametrize(
    "flag",
    ["self_report_fine", "validity_fail", "straight_lining", "too_fast", "all_max"],
)
def test_each_masking_condition_fires_on_its_own(flag):
    """"The faking is the finding" has five different faces; each must be
    enough on adverse signals, and none may fire without them."""
    ruleset = load_ruleset()
    kwargs = dict(NO_FLAGS)
    kwargs[flag] = True
    hit = detect_masking(signals=ADVERSE, voluntary_present=True, ruleset=ruleset, **kwargs)
    assert hit is not None, flag
    assert hit["matched_conditions"] == [flag]
    assert hit["tier_floor"] == "red"


def test_masking_needs_a_low_absolute_sleep_or_a_baseline_breach():
    ruleset = load_ruleset()
    base = dict(consecutive_duty_days=62.0, leave_cancel_count=2.0)
    # Neither sleep signal present: no masking, however "fine" the self-report.
    assert (
        detect_masking(
            signals=base, voluntary_present=True, ruleset=ruleset,
            **dict(NO_FLAGS, self_report_fine=True),
        )
        is None
    )
    # A low absolute sleep_hours is enough on its own…
    assert (
        detect_masking(
            signals=dict(base, sleep_hours=4.0),
            voluntary_present=True,
            ruleset=ruleset,
            **dict(NO_FLAGS, self_report_fine=True),
        )
        is not None
    )
    # …and so is a deviation from the person's own baseline.
    assert (
        detect_masking(
            signals=dict(base, sleep_deviation=-0.4),
            voluntary_present=True,
            ruleset=ruleset,
            **dict(NO_FLAGS, self_report_fine=True),
        )
        is not None
    )


def test_masking_never_fires_without_an_adverse_signal_picture():
    ruleset = load_ruleset()
    calm = {"consecutive_duty_days": 3.0, "leave_cancel_count": 0.0, "sleep_deviation": -0.35}
    assert (
        detect_masking(
            signals=calm, voluntary_present=True, ruleset=ruleset,
            **dict(NO_FLAGS, self_report_fine=True, all_max=True),
        )
        is None
    )


def test_masking_is_suppressed_when_no_voluntary_data_exists():
    """Withdrawal must never look like concealment (FR-17)."""
    ruleset = load_ruleset()
    assert (
        detect_masking(
            signals=ADVERSE, voluntary_present=False, ruleset=ruleset,
            **dict(NO_FLAGS, self_report_fine=True),
        )
        is None
    )


# ---------------------------------------------------------------------------
# Ruleset loader — the validation errors
# ---------------------------------------------------------------------------


def test_a_ruleset_missing_a_required_section_is_refused(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\nrules: []\n", encoding="utf-8")
    clear_ruleset_cache()
    try:
        with pytest.raises(RulesetError) as exc:
            load_ruleset(str(bad))
        assert "version/rules/tiers" in str(exc.value)
    finally:
        clear_ruleset_cache()


def test_a_rule_missing_a_field_is_refused(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "version: 1\ntiers: {green: [0, 100]}\nrules:\n  - id: R-X\n    domain: duty\n",
        encoding="utf-8",
    )
    clear_ruleset_cache()
    try:
        with pytest.raises(RulesetError) as exc:
            load_ruleset(str(bad))
        assert "rule missing" in str(exc.value)
    finally:
        clear_ruleset_cache()


def test_an_unreadable_ruleset_is_refused(tmp_path):
    clear_ruleset_cache()
    try:
        with pytest.raises(RulesetError) as exc:
            load_ruleset(str(tmp_path / "does-not-exist.yaml"))
        assert "cannot load ruleset" in str(exc.value)
    finally:
        clear_ruleset_cache()
