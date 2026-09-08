from __future__ import annotations

from tests.conftest import auth_header, login


def test_login_and_me(client):
    token = login(client, "commander.3bn")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["role"] == "commander"


def test_tc401_personnel_lookup_always_403(client):
    h = auth_header(client, "commander.3bn")
    r = client.get("/welfare/personnel/CR-DEMO-01", headers=h)
    assert r.status_code == 403


def test_commander_denied_individual_risk(client):
    h = auth_header(client, "commander.3bn")
    r = client.get("/risk/ps_demo01", headers=h)
    assert r.status_code == 403
    r2 = client.get("/risk/ps_demo01/explanation", headers=h)
    assert r2.status_code == 403
    r3 = client.get("/signals/ps_demo01", headers=h)
    assert r3.status_code == 403


def test_commander_denied_unmask_and_break_glass(client):
    h = auth_header(client, "commander.3bn")
    assert client.post("/privacy/unmask", headers=h, json={"pseudonym_id": "ps_demo01", "reason": "x"}).status_code == 403
    assert client.post("/privacy/break-glass", headers=h, json={"pseudonym_id": "ps_demo01", "reason": "x"}).status_code == 403


def test_tc403_commander_scrape_has_no_individual_score(client):
    h = auth_header(client, "commander.3bn")
    denied = []
    allowed_bodies = []
    for route in client.app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set()) or set()
        if not path or path.startswith("/docs") or path in {"/openapi.json", "/redoc"}:
            continue
        sample = (
            path.replace("{pseudonym_id}", "ps_demo01")
            .replace("{personnel_id}", "CR-DEMO-01")
            .replace("{unit_id}", "3BN")
            .replace("{case_id}", "cs_x")
            .replace("{proposal_id}", "rb_x")
            .replace("{request_id}", "um_x")
            .replace("{batch_id}", "b1")
            .replace("{dataset}", "leave")
            .replace("{lang}", "en")
        )
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            fn = getattr(client, method.lower())
            kwargs = {"headers": h}
            if method in {"POST", "PUT", "PATCH"}:
                kwargs["json"] = {}
            resp = fn(sample, **kwargs)
            if resp.status_code == 403:
                denied.append((method, sample))
                continue
            if resp.status_code >= 400:
                continue
            body = resp.text
            allowed_bodies.append((method, sample, body))
            assert "ps_demo01" not in body or "/aggregates" in sample or sample.startswith("/auth")
            assert '"score"' not in body or "/aggregates" in sample
            assert "Demo Constable" not in body
    assert denied, "commander should be denied somewhere"
    # no identity map leak
    for _, _, body in allowed_bodies:
        assert "CR-DEMO-01" not in body


def test_counsellor_can_read_risk(client):
    h = auth_header(client, "counsellor.a")
    r = client.get("/risk/ps_demo01", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert 0 <= data["score"] <= 100
    assert data["tier"] in {"green", "amber", "red", "critical"}


def test_admin_cannot_read_individual_signals(client):
    h = auth_header(client, "admin")
    r = client.get("/signals/ps_demo01", headers=h)
    assert r.status_code == 403
