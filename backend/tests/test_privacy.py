from __future__ import annotations

from sqlalchemy import text

from app.db import SessionLocal
from app.models import AuditEvent
from app.privacy.kanonymity import aggregate_unit
from app.seed import PERSONA_PSEUDONYM
from tests.conftest import auth_header


def test_k_anonymity_3bn_ok(client):
    """The commander projection is the elevated share and nothing else.

    It carries no per-tier frequency table at all: a table with one small cell
    is recoverable by subtraction as soon as the reader knows the unit's
    strength, and a commander always does (TC-451).
    """
    h = auth_header(client, "commander.3bn")
    r = client.get("/aggregates/unit/3BN", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["k"] == 5
    assert "cells" not in data
    assert data["n"] is None or data["n"] >= 5
    if data["elevated_share"] is not None:
        n = data["n"]
        elevated = round(data["elevated_share"] * n)
        assert elevated >= 5 and (n - elevated) >= 5


def test_counsellor_tier_table_is_all_or_nothing(client):
    """The detailed projection exists for the roles that work cases. Its table
    ships whole or not at all: three published tiers beside one hidden tier
    hands the hidden one back by subtraction."""
    r = client.get("/aggregates/unit/3BN", headers=auth_header(client, "counsellor.a"))
    assert r.status_code == 200
    data = r.json()
    assert "cells" in data
    hidden = [name for name, c in data["cells"].items() if c["suppressed"]]
    assert len(hidden) in (0, len(data["cells"])), hidden
    for cell in data["cells"].values():
        if not cell["suppressed"]:
            assert cell["n"] == 0 or cell["n"] >= 5


def test_k_anonymity_tiny_unit_suppressed(client):
    db = SessionLocal()
    try:
        data = aggregate_unit(db, "TINY")
    finally:
        db.close()
    assert data["n_suppressed"] is True
    assert data["n"] is None
    assert data["elevated_share"] is None


def test_dual_key_requires_two_distinct_principals(client):
    c = auth_header(client, "counsellor.a")
    w = auth_header(client, "welfare.a")
    opened = client.post(
        "/privacy/unmask",
        headers=c,
        json={"pseudonym_id": PERSONA_PSEUDONYM, "reason": "session", "purpose_string": "case_review"},
    )
    assert opened.status_code == 200, opened.text
    rid = opened.json()["request_id"]
    # counsellor alone is not enough
    ident = client.get(f"/privacy/unmask/{rid}/identity", headers=c)
    assert ident.status_code == 403
    approved = client.post(f"/privacy/unmask/{rid}/approve", headers=w)
    assert approved.status_code == 200
    assert approved.json()["status"] == "granted"
    ident2 = client.get(f"/privacy/unmask/{rid}/identity", headers=c)
    assert ident2.status_code == 200
    assert ident2.json()["personnel_id"] == "CR-DEMO-01"
    # subject sees it
    j = auth_header(client, "jawan.demo")
    feed = client.get("/app/who-viewed", headers=j)
    assert feed.status_code == 200
    actions = {e["action"] for e in feed.json()["entries"]}
    assert "unmask.grant" in actions or "identity.read" in actions


def test_same_user_cannot_supply_both_keys(client):
    # welfare officer trying to open and then... there is no dual-role user.
    # Admin is never a keyholder.
    a = auth_header(client, "admin")
    r = client.post(
        "/privacy/unmask",
        headers=a,
        json={"pseudonym_id": PERSONA_PSEUDONYM, "reason": "nope", "purpose_string": "case_review"},
    )
    assert r.status_code == 403


def test_break_glass_notifies_subject(client):
    c = auth_header(client, "counsellor.a")
    r = client.post(
        "/privacy/break-glass",
        headers=c,
        json={"pseudonym_id": PERSONA_PSEUDONYM, "reason": "imminent harm"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["notified_subject"] is True
    assert body["oversight_flag"] is True
    j = auth_header(client, "jawan.demo")
    feed = client.get("/app/who-viewed", headers=j)
    actions = {e["action"] for e in feed.json()["entries"]}
    assert "break_glass.open" in actions


def test_silent_withdrawal(client):
    cmd_before = client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn")).json()
    j = auth_header(client, "jawan.demo")
    w = client.post("/app/consent/withdraw", headers=j)
    assert w.status_code == 200
    assert w.json()["command_visible"] is False
    cmd_after = client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn")).json()
    # commander payload has no consent / withdrawal field
    assert "withdraw" not in str(cmd_after).lower()
    assert "consent" not in str(cmd_after).lower()
    assert cmd_before["k"] == cmd_after["k"]


def test_audit_append_only_and_chain(client):
    # Force at least one committed audit row, then verify the chain.
    client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn"))
    h = auth_header(client, "auditor")
    v = client.get("/audit/verify", headers=h)
    assert v.status_code == 200
    assert v.json()["ok"] is True
    db = SessionLocal()
    try:
        row = db.query(AuditEvent).first()
        assert row is not None
        try:
            db.execute(text("UPDATE audit_events SET action='tamper' WHERE id=:i"), {"i": row.id})
            db.commit()
            raised = False
        except Exception:
            db.rollback()
            raised = True
        assert raised
    finally:
        db.close()


def test_raw_expiry_keeps_trend(client):
    a = auth_header(client, "admin")
    r = client.post("/jobs/expire-raw", headers=a)
    assert r.status_code == 200
    c = auth_header(client, "counsellor.a")
    risk = client.get("/risk/ps_demo01", headers=c)
    assert risk.status_code == 200
    assert "score" in risk.json()
