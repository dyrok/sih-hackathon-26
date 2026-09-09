"""PRIV-003 — regression tests for every RED finding in
docs/quality/security-test-cases.md that has been fixed.

Each test names its TC id. A test here failing means a closed hole reopened.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.clock import clamp_capture_date, OFFLINE_WINDOW_DAYS
from app.config import Settings, get_settings
from app.consent import artefact_hash, verify_artefact
from app.db import SessionLocal
from app.firewall import path_denied_to_commander
from app.models import (
    BreakGlassEvent,
    CheckIn,
    ConsentArtefact,
    PassiveFeature,
    ResponseCase,
    TriageEntry,
    User,
)
from app.passwords import hash_password
from app.security import reset_login_throttle
from tests.conftest import DEMO_PASSWORD, auth_header

PERSONA = "ps_demo01"
UNRELATED = "ps_3bn05"


# ---------------------------------------------------------------------------
# Section C — IDOR / curiosity browsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        f"/risk/{UNRELATED}",
        f"/risk/{UNRELATED}/explanation",
        f"/risk/{UNRELATED}/trend",
        f"/signals/{UNRELATED}",
    ],
)
def test_tc418_tc419_counsellor_cannot_browse_an_unrelated_subject(client, path):
    """A counsellor may read the people the engine put on their caseload, and
    nobody else. Before the fix every one of these returned 200."""
    r = client.get(path, headers=auth_header(client, "counsellor.a"))
    assert r.status_code == 403, (path, r.status_code, r.text[:200])
    assert "caseload" in r.text


def test_tc418_the_assigned_subject_is_still_readable(client):
    """The guard must not break the actual job."""
    for path in (f"/risk/{PERSONA}", f"/risk/{PERSONA}/explanation", f"/signals/{PERSONA}"):
        r = client.get(path, headers=auth_header(client, "counsellor.a"))
        assert r.status_code == 200, (path, r.text[:200])


def test_tc418_a_refused_browse_is_audited(client):
    client.get(f"/risk/{UNRELATED}", headers=auth_header(client, "counsellor.a"))
    events = client.get("/audit/events", headers=auth_header(client, "auditor")).json()["events"]
    assert any(e["action"] == "scope.deny" and e["denied"] for e in events)


def _second_counsellor() -> str:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "counsellor.b").one_or_none() is None:
            db.add(
                User(
                    id="usr_counsellor_b",
                    username="counsellor.b",
                    password_hash=hash_password(DEMO_PASSWORD),
                    role="counsellor",
                    display_name="Counsellor B",
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()
    return "counsellor.b"


def test_tc420_a_counsellor_cannot_act_on_another_counsellors_case(client):
    """The queue was filtered and the item routes were not — the classic
    'list is scoped, detail is not' IDOR. All three writes must refuse."""
    owner = auth_header(client, "counsellor.a")
    queue = client.get("/interventions/queue", headers=owner).json()["queue"]
    assert queue
    case_id = queue[0]["case_id"]
    other = auth_header(client, _second_counsellor())

    a = client.post(
        f"/interventions/{case_id}/actions", json={"catalogue_id": "INT-BUDDY"}, headers=other
    )
    assert a.status_code == 403, a.text
    o = client.post(
        f"/interventions/{case_id}/outcome", json={"outcome": "declined"}, headers=other
    )
    assert o.status_code == 403, o.text
    t = client.post(f"/interventions/{case_id}/telemanas", json={}, headers=other)
    assert t.status_code == 403, t.text

    # …and the case is still open: a refused action must not have side effects.
    db = SessionLocal()
    try:
        assert db.get(ResponseCase, case_id).status != "closed"
    finally:
        db.close()


def test_tc420b_empty_assigned_units_means_none_not_all(client):
    db = SessionLocal()
    try:
        wo = db.query(User).filter(User.username == "welfare.a").one()
        wo.assigned_units = []
        db.commit()
    finally:
        db.close()
    h = auth_header(client, "welfare.a")
    assert client.get("/interventions/queue", headers=h).json()["queue"] == []
    assert client.get(f"/risk/{PERSONA}", headers=h).status_code == 403


# ---------------------------------------------------------------------------
# Section D — firewall defence in depth
# ---------------------------------------------------------------------------


def test_tc428_middleware_covers_the_admin_and_audit_prefixes():
    for path in ("/jobs/expire-raw", "/audit/events", "/audit/verify"):
        assert path_denied_to_commander(path) is True, path
    # …without swallowing the commander's own self-scope check-in (F07 screen 6)
    assert path_denied_to_commander("/me/checkins") is False
    assert path_denied_to_commander("/me/sitreps") is False
    assert path_denied_to_commander("/aggregates/units") is False


def test_tc429_path_mutations_never_leak(client):
    h = auth_header(client, "commander.3bn")
    for path in (
        f"/risk/{PERSONA}",
        f"/risk//{PERSONA}",
        f"/risk/{PERSONA}/",
        f"/aggregates/../risk/{PERSONA}",
    ):
        r = client.get(path, headers=h)
        assert r.status_code >= 400, (path, r.status_code)
        assert PERSONA not in r.text or r.status_code == 403


# ---------------------------------------------------------------------------
# Section H — k-anonymity, the §4 must-pass gate
# ---------------------------------------------------------------------------


def _set_tiers(distribution: dict[str, int]) -> None:
    """Force the latest score tier for 3BN's twelve people."""
    from app.models import IdentityMap, RiskScore

    db = SessionLocal()
    try:
        pids = [
            r.pseudonym_id
            for r in db.query(IdentityMap).filter(IdentityMap.unit_id == "3BN").all()
        ]
        wanted: list[str] = []
        for tier, n in distribution.items():
            wanted.extend([tier] * n)
        assert len(wanted) == len(pids), (len(wanted), len(pids))
        for pid, tier in zip(pids, wanted):
            row = (
                db.query(RiskScore)
                .filter(RiskScore.pseudonym_id == pid)
                .order_by(RiskScore.computed_at.desc())
                .first()
            )
            row.tier = tier
        db.commit()
    finally:
        db.close()


@pytest.mark.parametrize(
    "distribution",
    [
        {"green": 11, "amber": 1, "red": 0, "critical": 0},
        {"green": 9, "amber": 3, "red": 0, "critical": 0},
        {"green": 12, "amber": 0, "red": 0, "critical": 0},
        {"green": 0, "amber": 0, "red": 12, "critical": 0},
        {"green": 6, "amber": 5, "red": 1, "critical": 0},
        {"green": 7, "amber": 5, "red": 0, "critical": 0},
    ],
)
def test_tc451_the_commander_projection_cannot_be_differenced(client, distribution):
    """The finding that blocked the §4 gate: `round(morale_index * n)` recovered
    a suppressed cell of one person.

    The fix is structural rather than arithmetic — command sees the elevated
    share and no per-tier table — so this test asserts the absence of the table
    as well as the two-sided floor on the share that remains.
    """
    _set_tiers(distribution)
    d = client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn")).json()

    assert "cells" not in d, "a per-tier table is a differencing surface"
    assert "suppressed_keys" not in d, "naming the small tier is itself a disclosure"

    n = sum(distribution.values())
    elevated = n - distribution["green"]
    if d["elevated_share"] is None:
        assert d["morale_index"] is None
        assert d["suppressed"] is True and d["reason_key"] == "heat.cell.suppressed"
    else:
        # Published only when neither side of the split is small.
        assert elevated >= 5 and (n - elevated) >= 5, distribution
        assert round(d["elevated_share"] * n) == elevated


@pytest.mark.parametrize(
    "distribution",
    [
        {"green": 11, "amber": 1, "red": 0, "critical": 0},
        {"green": 6, "amber": 5, "red": 1, "critical": 0},
    ],
)
def test_tc452_the_detailed_table_never_leaves_one_cell_derivable(client, distribution):
    """Complement suppression, done by removing the total rather than guessing
    which second cell to hide — an earlier version filtered on a truthy count,
    so a unit whose other cells were empty left exactly one hidden cell beside a
    published total."""
    _set_tiers(distribution)
    d = client.get("/aggregates/unit/3BN", headers=auth_header(client, "counsellor.a")).json()
    cells = d["cells"]
    hidden = [name for name, c in cells.items() if c["suppressed"]]
    published = [c["n"] for c in cells.values() if not c["suppressed"]]

    # All or nothing: three published tiers and one hidden hands the hidden one
    # back by subtraction, so a table with any small tier ships as no table.
    assert len(hidden) in (0, len(cells)), hidden
    for value in published:
        assert value == 0 or value >= 5
    if hidden:
        assert d["table_suppressed"] is True
        assert all(c["n"] is None for c in cells.values())


def test_tc451_a_healthy_unit_still_publishes_its_number(client):
    """Suppression that never lets anything through is not privacy, it is a
    broken screen. A unit with both sides above the floor shows its share."""
    _set_tiers({"green": 6, "amber": 5, "red": 1, "critical": 0})
    d = client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn")).json()
    assert d["elevated_share"] == 0.5, d
    assert d["suppressed"] is False


def test_tc450b_every_aggregate_surface_suppresses_a_tiny_unit(client):
    h = auth_header(client, "welfare.a")
    for path in (
        "/aggregates/unit/TINY",
        "/aggregates/unit/TINY/morale",
        "/aggregates/unit/TINY/indicators",
        "/aggregates/unit/TINY/pulse",
        "/aggregates/unit/TINY/forecast",
    ):
        body = client.get(path, headers=h).json()
        blob = str(body)
        assert "ps_tiny" not in blob and "Tiny 1" not in blob, path


# ---------------------------------------------------------------------------
# Section G — audit chain
# ---------------------------------------------------------------------------


def test_tc442_backdating_an_event_breaks_the_chain(client):
    client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn"))
    db = SessionLocal()
    try:
        # The trigger blocks a normal UPDATE, so simulate a DBA who has dropped
        # it — the chain must still notice.
        db.execute(text("DROP TRIGGER IF EXISTS audit_events_no_update"))
        db.execute(text("UPDATE audit_events SET at = '2020-01-01 00:00:00' WHERE id = 1"))
        db.commit()
    finally:
        db.close()
    r = client.get("/audit/verify", headers=auth_header(client, "auditor"))
    assert r.json()["ok"] is False, r.json()


def test_tc443_truncating_the_tail_breaks_the_chain(client):
    client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn"))
    db = SessionLocal()
    try:
        db.execute(text("DROP TRIGGER IF EXISTS audit_events_no_delete"))
        last = db.execute(text("SELECT MAX(id) FROM audit_events")).scalar()
        db.execute(text("DELETE FROM audit_events WHERE id = :i"), {"i": last})
        db.commit()
    finally:
        db.close()
    r = client.get("/audit/verify", headers=auth_header(client, "auditor"))
    assert r.json()["ok"] is False, r.json()


# ---------------------------------------------------------------------------
# Section I — consent artefact integrity
# ---------------------------------------------------------------------------


def test_tc449_consent_artefact_hashes_its_own_content(client):
    h = auth_header(client, "jawan.demo")
    r = client.post(
        "/app/consent",
        json={
            "bundle_id": "instruments",
            "purpose_string": "monthly anchor",
            "data_categories": ["phq9"],
            "language": "en",
        },
        headers=h,
    )
    assert r.status_code == 200
    consent_id = r.json()["consent_id"]
    db = SessionLocal()
    try:
        row = db.get(ConsentArtefact, consent_id)
        assert verify_artefact(row) is True
        row.purpose_string = "something else entirely"
        db.commit()
        db.refresh(row)
        assert verify_artefact(row) is False, "an edited artefact must not verify"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Section J — retention
# ---------------------------------------------------------------------------


def test_tc455_a_future_recorded_at_cannot_outrun_the_ttl(client):
    h = auth_header(client, "jawan.demo")
    r = client.post(
        "/app/checkins",
        json={"mood_label": "ok", "mood_score": 3, "recorded_at": "2099-01-01"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    db = SessionLocal()
    try:
        rows = db.query(CheckIn).filter(CheckIn.recorded_at > date(2030, 1, 1)).all()
        assert rows == [], "a client date must never create an immortal row"
    finally:
        db.close()


def test_tc455_clamp_keeps_a_genuinely_offline_capture(client):
    today = date(2026, 9, 1)
    old = (today - timedelta(days=5)).isoformat()
    assert clamp_capture_date(old, today) == date(2026, 8, 27)
    assert clamp_capture_date("2099-01-01", today) == today
    assert clamp_capture_date("2020-01-01", today) == today - timedelta(days=OFFLINE_WINDOW_DAYS)
    assert clamp_capture_date(None, today) == today
    assert clamp_capture_date("not-a-date", today) == today


def test_tc454_expiry_covers_passive_features(client):
    db = SessionLocal()
    try:
        db.add(
            PassiveFeature(
                id="pf_qa1",
                pseudonym_id=PERSONA,
                sleep_hours_proxy=4.1,
                recorded_at=date(2026, 1, 1),
            )
        )
        db.commit()
    finally:
        db.close()
    r = client.post("/jobs/expire-raw", headers=auth_header(client, "admin"))
    assert r.status_code == 200, r.text
    assert r.json()["passive_purged"] >= 1
    db = SessionLocal()
    try:
        assert db.get(PassiveFeature, "pf_qa1") is None
    finally:
        db.close()
    # …and it stays idempotent
    again = client.post("/jobs/expire-raw", headers=auth_header(client, "admin")).json()
    assert again["passive_purged"] == 0


# ---------------------------------------------------------------------------
# Section F — break-glass economics
# ---------------------------------------------------------------------------


def test_tc438_break_glass_is_capped_then_demands_oversight(client):
    h = auth_header(client, "counsellor.a")
    cap = get_settings().break_glass_weekly_cap
    for i in range(cap):
        r = client.post(
            "/privacy/break-glass",
            json={"pseudonym_id": PERSONA, "reason": f"imminent harm {i}"},
            headers=h,
        )
        assert r.status_code == 200, r.text
    blocked = client.post(
        "/privacy/break-glass",
        json={"pseudonym_id": PERSONA, "reason": "again"},
        headers=h,
    )
    assert blocked.status_code == 429, blocked.text
    assert "legal_name" not in blocked.text

    # It is never hard-blocked — imminent harm must still be reachable, but only
    # with an explicit oversight acknowledgement and a substantive reason.
    allowed = client.post(
        "/privacy/break-glass",
        json={
            "pseudonym_id": PERSONA,
            "reason": "subject disclosed a plan during outreach; contacting now",
            "acknowledge_oversight": True,
        },
        headers=h,
    )
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["above_cap"] is True
    assert allowed.json()["notified_subject"] is True


def test_tc438_the_throttle_is_audited(client):
    h = auth_header(client, "counsellor.a")
    for i in range(get_settings().break_glass_weekly_cap + 1):
        client.post(
            "/privacy/break-glass",
            json={"pseudonym_id": PERSONA, "reason": f"r{i}"},
            headers=h,
        )
    events = client.get("/audit/events", headers=auth_header(client, "auditor")).json()["events"]
    assert any(e["action"] == "break_glass.throttled" for e in events)


# ---------------------------------------------------------------------------
# Section A/K — auth throttling, CORS, upload bounds, deployment guard
# ---------------------------------------------------------------------------


def test_tc457_login_is_rate_limited(client):
    reset_login_throttle()
    try:
        limit = get_settings().login_max_attempts
        codes = []
        for _ in range(limit + 3):
            codes.append(
                client.post(
                    "/auth/login", json={"username": "counsellor.a", "password": "wrong"}
                ).status_code
            )
        assert 429 in codes, codes
        assert codes.count(401) <= limit, codes
    finally:
        reset_login_throttle()


def test_tc457_a_good_password_still_works_after_a_few_misses(client):
    reset_login_throttle()
    try:
        for _ in range(3):
            client.post("/auth/login", json={"username": "counsellor.a", "password": "wrong"})
        r = client.post(
            "/auth/login", json={"username": "counsellor.a", "password": DEMO_PASSWORD}
        )
        assert r.status_code == 200
    finally:
        reset_login_throttle()


def test_tc456_cors_does_not_reflect_an_arbitrary_origin(client):
    r = client.options(
        "/auth/login",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert r.headers.get("access-control-allow-origin") != "https://evil.example"


def test_tc458_an_oversized_upload_is_refused(client):
    limit = get_settings().max_ingest_bytes
    payload = b"pseudonym_id,duty_date,shift_code,rest_day,unit_id\n" + b"x" * (limit + 1024)
    r = client.post(
        "/ingest/hr/csv?dataset=roster",
        files={"file": ("big.csv", payload, "text/csv")},
        headers=auth_header(client, "hr.ingest"),
    )
    assert r.status_code == 413, r.status_code


def test_tc415_production_refuses_to_start_on_the_committed_secret():
    prod = Settings(env="production")
    with pytest.raises(RuntimeError) as exc:
        prod.assert_deployable()
    message = str(exc.value)
    assert "dev value" in message
    assert "SQLite" in message
    # …and the demo default must still start with zero configuration.
    Settings().assert_deployable()


# ---------------------------------------------------------------------------
# Section C — TC-424: the quarantine report
# ---------------------------------------------------------------------------


def test_tc424_quarantine_is_scoped_to_its_submitter_and_content_blind(client):
    """A rejected row is still an HR row about a person, and batch ids are
    caller-chosen and therefore guessable."""
    hr = auth_header(client, "hr.ingest")
    r = client.post(
        "/ingest/hr/leave",
        json={
            "batch_id": "b-tc424",
            "rows": [{"pseudonym_id": "ps_demo01", "leave_type": "casual"}],  # missing applied_at
        },
        headers=hr,
    )
    assert r.status_code == 200, r.text
    assert r.json()["rows_quarantined"] >= 1

    # The submitting principal sees its own rejected rows, payload included.
    own = client.get("/ingest/hr/batches/b-tc424/quarantine", headers=hr)
    assert own.status_code == 200, own.text
    assert own.json()["payload_included"] is True
    assert "payload" in own.json()["rows"][0]

    # Admin operates pipelines and the auditor is content-blind: both may see
    # that rows were rejected and why, never what was in them.
    for username in ("admin", "auditor"):
        blind = client.get("/ingest/hr/batches/b-tc424/quarantine", headers=auth_header(client, username))
        assert blind.status_code == 200, (username, blind.text)
        body = blind.json()
        assert body["payload_included"] is False
        assert all("payload" not in row for row in body["rows"]), username
        assert "ps_demo01" not in blind.text, username
        assert body["rows"] and body["rows"][0]["reason"]

    # An unknown batch is a 404, not an empty success that confirms nothing.
    assert client.get("/ingest/hr/batches/b-guessed/quarantine", headers=hr).status_code == 404


def test_tc424_another_ingest_principal_is_refused(client):
    from app.db import SessionLocal
    from app.models import User
    from app.passwords import hash_password

    client.post(
        "/ingest/hr/leave",
        json={"batch_id": "b-mine", "rows": [{"pseudonym_id": "ps_demo01"}]},
        headers=auth_header(client, "hr.ingest"),
    )
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "hr.other").one_or_none() is None:
            db.add(
                User(
                    id="usr_hr_other",
                    username="hr.other",
                    password_hash=hash_password(DEMO_PASSWORD),
                    role="hr_ingest",
                    display_name="Other ingest",
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()
    other = client.get("/ingest/hr/batches/b-mine/quarantine", headers=auth_header(client, "hr.other"))
    assert other.status_code == 403, other.text
    assert "another ingest principal" in other.text
