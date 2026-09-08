from __future__ import annotations

from tests.conftest import auth_header


def test_queue_and_telemanas_and_outcome(client):
    h = auth_header(client, "counsellor.a")
    q = client.get("/interventions/queue", headers=h)
    assert q.status_code == 200, q.text
    queue = q.json()["queue"]
    individual = next((item for item in queue if item["pseudonym_id"] == "ps_demo01"), None)
    assert individual is not None, queue
    case_id = individual["case_id"]
    act = client.post(f"/interventions/{case_id}/actions", headers=h, json={"catalogue_id": "INT-COUNSEL"})
    assert act.status_code == 200
    tm = client.post(
        f"/interventions/{case_id}/telemanas",
        headers=h,
        json={"mode": "facilitated_call", "outcome_status": "referred"},
    )
    assert tm.status_code == 200
    assert tm.json()["clinical_content"] is None
    out = client.post(
        f"/interventions/{case_id}/outcome",
        headers=h,
        json={"outcome": "improved", "action_id": act.json()["action_id"]},
    )
    assert out.status_code == 200
    assert out.json()["label"]["exported"] is True


def test_rebalance_workload_visible_to_commander(client):
    w = auth_header(client, "welfare.a")
    r = client.post(
        "/roster/rebalance",
        headers=w,
        json={"unit_id": "3BN", "mode": "workload", "horizon_days": 14},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "max_load_before" in body and "max_load_after" in body
    assert "tier" not in body and "score" not in body
    pid = body["proposal_id"]
    c = auth_header(client, "commander.3bn")
    g = client.get(f"/roster/rebalance/{pid}", headers=c)
    assert g.status_code == 200
    ap = client.post(f"/roster/rebalance/{pid}/approve", headers=c)
    assert ap.status_code == 200


def test_rebalance_welfare_weighted_hidden_from_commander(client):
    w = auth_header(client, "welfare.a")
    r = client.post(
        "/roster/rebalance",
        headers=w,
        json={"unit_id": "3BN", "mode": "welfare_weighted", "horizon_days": 14},
    )
    assert r.status_code == 200, r.text
    pid = r.json()["proposal_id"]
    c = auth_header(client, "commander.3bn")
    g = client.get(f"/roster/rebalance/{pid}", headers=c)
    assert g.status_code == 403


def test_caps_never_drop_silently(client):
    h = auth_header(client, "counsellor.a")
    q = client.get("/interventions/queue", headers=h).json()["queue"]
    # deferred items still listed
    for item in q:
        assert item["status"] in {"open", "deferred"}
        if item["status"] == "deferred":
            assert item["cap_reason"]
