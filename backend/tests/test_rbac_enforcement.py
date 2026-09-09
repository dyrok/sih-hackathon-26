"""PRIV-002 — RBAC/ABAC enforcement tests.

Every cell of docs/compliance/rbac-matrix.md, asserted against the running API
rather than against the documentation. Two things make this suite worth having:

1. It enumerates the **whole** route table per role (TC-403), so a route added
   later without a role guard fails here instead of in front of a jury.
2. It asserts the negative cells, not just the positive ones. "Counsellor can
   read a case" is easy; "admin cannot read DT-01..DT-04" is the claim the
   dual-key design actually rests on.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import User
from app.passwords import hash_password
from tests.conftest import DEMO_PASSWORD, auth_header, login

ROLES = {
    "jawan": "jawan.demo",
    "counsellor": "counsellor.a",
    "welfare_officer": "welfare.a",
    "commander": "commander.3bn",
    "admin": "admin",
    "auditor": "auditor",
    "hr_ingest": "hr.ingest",
}

PERSONA = "ps_demo01"
OTHER_JAWAN = "ps_tiny1"


# ---------------------------------------------------------------------------
# Route enumeration — the shape of the whole API, per role
# ---------------------------------------------------------------------------


def _get_routes() -> list[str]:
    out = []
    for r in app.routes:
        methods = getattr(r, "methods", None) or set()
        path = getattr(r, "path", "")
        if "GET" not in methods:
            continue
        if path.startswith(("/docs", "/redoc", "/openapi")):
            continue
        out.append(path)
    return sorted(set(out))


def _fill(path: str) -> str:
    return (
        path.replace("{pseudonym_id}", PERSONA)
        .replace("{personnel_id}", "CR-DEMO-01")
        .replace("{unit_id}", "3BN")
        .replace("{case_id}", "cs_missing")
        .replace("{request_id}", "um_missing")
        .replace("{batch_id}", "b1")
        .replace("{proposal_id}", "rb_missing")
        .replace("{run_id}", "sim_missing")
        .replace("{lang}", "en")
        .replace("{bundle_id}", "checkin")
    )


#: Substrings that must never appear in a response to a role that has no
#: individual read grant. `legal_name` is the identity vault; the persona
#: pseudonym is the individual key everything else hangs off.
INDIVIDUAL_MARKERS = ("legal_name", "Demo Constable", PERSONA)


@pytest.mark.parametrize("role,username", sorted(ROLES.items()))
def test_no_route_returns_a_server_error_for_any_role(client, role, username):
    """A 500 is an unguarded code path. There must not be one, for any role."""
    h = auth_header(client, username)
    failures = []
    for path in _get_routes():
        r = client.get(_fill(path), headers=h)
        if r.status_code >= 500:
            failures.append((path, r.status_code, r.text[:200]))
    assert not failures, failures


def test_tc403_commander_scrape_reveals_no_individual(client):
    """Enumerate every readable route with a commander token and scrape the
    bodies. Nothing may carry a pseudonym-to-identity link or a person's score."""
    h = auth_header(client, "commander.3bn")
    leaks = []
    for path in _get_routes():
        r = client.get(_fill(path), headers=h)
        if r.status_code != 200:
            continue
        body = r.text
        for marker in INDIVIDUAL_MARKERS:
            if marker in body:
                leaks.append((path, marker))
    assert not leaks, leaks


def test_admin_and_auditor_never_see_individual_content(client):
    """RBAC matrix: admin has no read grant on DT-01..DT-04; the auditor is
    content-blind on DT-01/02/08 and sees events only."""
    for username in ("admin", "auditor"):
        h = auth_header(client, username)
        leaks = []
        for path in _get_routes():
            if path.startswith("/audit"):
                continue  # the auditor's own surface: events, not content
            r = client.get(_fill(path), headers=h)
            if r.status_code != 200:
                continue
            for marker in ("legal_name", "Demo Constable"):
                if marker in r.text:
                    leaks.append((username, path, marker))
        assert not leaks, leaks


# ---------------------------------------------------------------------------
# DT-by-DT matrix cells
# ---------------------------------------------------------------------------


DENIED_INDIVIDUAL_RISK = ["commander.3bn", "admin", "auditor", "jawan.demo", "hr.ingest"]


@pytest.mark.parametrize("username", DENIED_INDIVIDUAL_RISK)
def test_dt02_only_counsellor_and_welfare_read_a_score(client, username):
    r = client.get(f"/risk/{PERSONA}", headers=auth_header(client, username))
    assert r.status_code == 403, (username, r.status_code, r.text)


@pytest.mark.parametrize("username", ["counsellor.a", "welfare.a"])
def test_dt02_counsellor_and_welfare_can_read_a_score(client, username):
    r = client.get(f"/risk/{PERSONA}", headers=auth_header(client, username))
    assert r.status_code == 200, r.text


def test_dt01_jawan_reads_only_own_self_report(client):
    """There is no route shape that takes another principal's id, so the
    strongest assertion available is that no such route exists at all."""
    subject_routes = [p for p in _get_routes() if p.startswith("/app") and "{" in p]
    # /app/consent/withdraw/{bundle_id} is a scope selector, not a subject one.
    assert subject_routes == [] or all(
        "{bundle_id}" in p for p in subject_routes
    ), subject_routes
    r = client.get("/app/me/checkins", headers=auth_header(client, "jawan.demo"))
    assert r.status_code == 200
    assert OTHER_JAWAN not in r.text


def test_dt03_case_queue_denied_to_everyone_but_counsellor_and_welfare(client):
    for username in ("jawan.demo", "commander.3bn", "admin", "auditor", "hr.ingest"):
        r = client.get("/interventions/queue", headers=auth_header(client, username))
        assert r.status_code == 403, (username, r.status_code)


def test_dt04_admin_can_never_be_a_keyholder(client):
    """Not a policy statement: the endpoint refuses the admin role outright."""
    r = client.post(
        "/privacy/unmask",
        json={"pseudonym_id": PERSONA, "reason": "r", "purpose_string": "case_review"},
        headers=auth_header(client, "admin"),
    )
    assert r.status_code == 403


def test_dt05_commander_confined_to_own_unit_chain(client):
    h = auth_header(client, "commander.3bn")
    assert client.get("/aggregates/unit/3BN", headers=h).status_code == 200
    r = client.get("/aggregates/unit/TINY", headers=h)
    assert r.status_code == 403, r.text
    for path in ("/aggregates/unit/TINY/morale", "/aggregates/unit/TINY/indicators",
                 "/aggregates/unit/TINY/pulse", "/aggregates/unit/TINY/forecast",
                 "/aggregates/unit/TINY/trend"):
        assert client.get(path, headers=h).status_code == 403, path


def test_dt05_commander_units_list_shows_only_own_unit(client):
    r = client.get("/aggregates/units", headers=auth_header(client, "commander.3bn"))
    assert r.status_code == 200
    units = [u["unit_id"] for u in r.json()["units"]]
    assert units == ["3BN"], units


def test_dt07_audit_log_read_is_auditor_only(client):
    assert client.get("/audit/events", headers=auth_header(client, "auditor")).status_code == 200
    for username in ("jawan.demo", "counsellor.a", "welfare.a", "commander.3bn", "hr.ingest"):
        r = client.get("/audit/events", headers=auth_header(client, username))
        assert r.status_code == 403, (username, r.status_code)


def test_dt09_who_viewed_is_jawan_self_scope_only(client):
    assert client.get("/app/who-viewed", headers=auth_header(client, "jawan.demo")).status_code == 200
    for username in ("counsellor.a", "welfare.a", "commander.3bn", "admin", "auditor"):
        r = client.get("/app/who-viewed", headers=auth_header(client, username))
        assert r.status_code == 403, (username, r.status_code)


def test_dt10_hr_signals_are_not_readable_by_command(client):
    assert client.get("/signals/" + PERSONA, headers=auth_header(client, "commander.3bn")).status_code == 403
    assert client.get("/app/roster", headers=auth_header(client, "commander.3bn")).status_code == 403


def test_ingest_is_service_account_only(client):
    for username in ("jawan.demo", "counsellor.a", "welfare.a", "commander.3bn", "auditor"):
        r = client.post(
            "/ingest/hr/leave",
            json={"batch_id": "b-rbac", "rows": []},
            headers=auth_header(client, username),
        )
        assert r.status_code == 403, (username, r.status_code)


# ---------------------------------------------------------------------------
# ABAC: caseload and unit assignment
# ---------------------------------------------------------------------------


def _make_second_counsellor() -> str:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "counsellor.b").one_or_none()
        if existing is None:
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


def test_abac_counsellor_cannot_open_another_counsellors_case(client):
    owner = auth_header(client, "counsellor.a")
    queue = client.get("/interventions/queue", headers=owner).json()["queue"]
    assert queue, "the seeded persona arc must produce at least one case"
    case_id = queue[0]["case_id"]

    other = auth_header(client, _make_second_counsellor())
    # The case is assigned to counsellor.a by triage, so B is refused.
    r = client.get(f"/interventions/case/{case_id}", headers=other)
    assert r.status_code in (403, 404), r.text
    if r.status_code == 403:
        assert "assigned" in r.text


def test_abac_welfare_officer_confined_to_assigned_units(client):
    db = SessionLocal()
    try:
        wo = db.query(User).filter(User.username == "welfare.a").one()
        wo.assigned_units = ["SOMEWHERE-ELSE"]
        db.commit()
    finally:
        db.close()
    h = auth_header(client, "welfare.a")
    queue = client.get("/interventions/queue", headers=h).json()["queue"]
    assert queue == [], queue


# ---------------------------------------------------------------------------
# Token integrity — the guard in front of every cell above
# ---------------------------------------------------------------------------


def test_no_token_is_rejected(client):
    for path in ("/auth/me", "/app/consent", "/interventions/queue", "/aggregates/units"):
        assert client.get(path).status_code in (401, 403), path


def test_garbage_token_is_rejected(client):
    h = {"Authorization": "Bearer not-a-jwt"}
    assert client.get("/auth/me", headers=h).status_code == 401


def test_token_signed_with_the_wrong_secret_is_rejected(client):
    payload = {
        "sub": "usr_jawan_demo",
        "role": "jawan",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    forged = jwt.encode(payload, "not-the-real-secret", algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_alg_none_token_is_rejected(client):
    """The classic JWT bypass: an unsigned token claiming a privileged role."""
    payload = {
        "sub": "usr_jawan_demo",
        "role": "counsellor",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    unsigned = jwt.encode(payload, key="", algorithm="none")
    r = client.get(f"/risk/{PERSONA}", headers={"Authorization": f"Bearer {unsigned}"})
    assert r.status_code == 401, r.text


def test_expired_token_is_rejected(client):
    settings = get_settings()
    payload = {
        "sub": "usr_counsellor_a",
        "role": "counsellor",
        "exp": int((datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp()),
        "iat": int(time.time()) - 100,
    }
    expired = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_role_claim_in_the_token_cannot_widen_access(client):
    """A validly-signed token whose `role` claim is escalated must not work:
    authorisation reads the role off the User row, not off the claim."""
    settings = get_settings()
    payload = {
        "sub": "usr_jawan_demo",  # really a jawan
        "role": "counsellor",  # claims otherwise
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    forged = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    r = client.get(f"/risk/{PERSONA}", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 403, r.text


def test_deactivated_user_token_stops_working(client):
    token = login(client, "counsellor.a")
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/auth/me", headers=h).status_code == 200
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.username == "counsellor.a").one()
        u.is_active = False
        db.commit()
    finally:
        db.close()
    assert client.get("/auth/me", headers=h).status_code == 401


def test_denied_attempts_are_audited(client):
    """Deny-by-default is only trustworthy if the denial is recorded."""
    client.get(f"/risk/{PERSONA}", headers=auth_header(client, "commander.3bn"))
    events = client.get("/audit/events", headers=auth_header(client, "auditor")).json()["events"]
    denied = [e for e in events if e["denied"]]
    assert denied, "a refused commander read must leave an audit entry"
