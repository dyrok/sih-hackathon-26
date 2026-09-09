from __future__ import annotations

from .conftest import auth_header


def test_client_surface_end_to_end(client):
    jawan = auth_header(client, "jawan.demo")
    counsellor = auth_header(client, "counsellor.a")
    welfare = auth_header(client, "welfare.a")
    commander = auth_header(client, "commander.3bn")

    # --- jawan self-service ---
    for path in ["/app/consent", "/app/roster", "/app/leave", "/app/payslip",
                 "/app/signals/summary", "/app/me/checkins", "/app/me/instruments",
                 "/app/notifications", "/app/pulse/me", "/app/buddy", "/app/who-viewed",
                 "/app/me/trend"]:
        r = client.get(path, headers=jawan)
        assert r.status_code == 200, (path, r.status_code, r.text)

    # sync batch: consent then checkin, idempotent replay
    batch = {"items": [
        {"table": "consent", "client_uuid": "u-consent-1", "payload": {"bundle_id": "checkin"}},
        {"table": "checkin", "client_uuid": "u-check-1",
         "payload": {"mood_label": "ok", "mood_score": 6, "recorded_at": "2026-09-01"}},
    ]}
    r = client.post("/app/sync", json=batch, headers=jawan)
    assert r.status_code == 200, r.text
    first = r.json()
    r2 = client.post("/app/sync", json=batch, headers=jawan)
    assert r2.status_code == 200
    assert all(x["status"] == "duplicate" for x in r2.json()["results"]), r2.json()
    assert first["accepted"] == 2

    # voice: feature vector only; audio field rejected
    bad = {"items": [{"table": "voice", "client_uuid": "u-v-bad",
                      "payload": {"schema_version": "v1", "duration_s": 10, "audio": "AAAA"}}]}
    client.post("/app/sync", json={"items": [
        {"table": "consent", "client_uuid": "u-consent-v", "payload": {"bundle_id": "voice"}}]},
        headers=jawan)
    rv = client.post("/app/sync", json=bad, headers=jawan)
    assert rv.json()["results"][0]["status"] == "rejected", rv.json()

    # pulse
    client.post("/app/sync", json={"items": [
        {"table": "consent", "client_uuid": "u-consent-p", "payload": {"bundle_id": "unit_pulse"}}]},
        headers=jawan)
    rp = client.post("/app/pulse", json={"ratings": [{"facet": "leadership", "rating": 4}]},
                     headers=jawan)
    assert rp.status_code == 200, rp.text

    # buddy
    client.post("/app/sync", json={"items": [
        {"table": "consent", "client_uuid": "u-consent-b", "payload": {"bundle_id": "buddy"}}]},
        headers=jawan)
    rb = client.post("/app/buddy/pair", json={"buddy_pseudonym": "ps_3bn02"}, headers=jawan)
    assert rb.status_code == 200, rb.text
    assert client.post("/app/buddy/state", json={"state": "quiet"}, headers=jawan).status_code == 200
    assert client.get("/app/buddy", headers=jawan).json()["paired"] is True

    # --- counsellor console ---
    q = client.get("/interventions/queue", headers=counsellor)
    assert q.status_code == 200, q.text
    cases = q.json()["queue"]
    assert cases, "expected at least one case from the seeded persona arc"
    case_id = cases[0]["case_id"]
    pid = cases[0]["pseudonym_id"]
    assert client.get("/interventions/catalogue", headers=counsellor).status_code == 200
    d = client.get(f"/interventions/case/{case_id}", headers=counsellor)
    assert d.status_code == 200, d.text
    assert "legal_name" not in d.text
    assert client.get(f"/interventions/case/{case_id}/timeline", headers=counsellor).status_code == 200
    n = client.post(f"/interventions/case/{case_id}/notes",
                    json={"modality": "in_person", "themes": ["sleep"], "risk_reestimate": 55,
                          "free_text": "confidential"}, headers=counsellor)
    assert n.status_code == 200, n.text
    notes = client.get(f"/interventions/case/{case_id}/notes", headers=counsellor).json()
    assert notes["notes"][0]["free_text"] == "confidential"
    # welfare officer sees the session happened but not the free text (RBAC DT-08)
    wnotes = client.get(f"/interventions/case/{case_id}/notes", headers=welfare).json()
    assert wnotes["notes"][0]["free_text"] is None
    assert wnotes["notes"][0]["free_text_withheld"] is True
    if pid:
        t = client.get(f"/risk/{pid}/trend", headers=counsellor)
        assert t.status_code == 200, t.text

    # --- commander aggregates ---
    for path in ["/aggregates/units", "/aggregates/unit/3BN/morale",
                 "/aggregates/unit/3BN/indicators", "/aggregates/unit/3BN/pulse",
                 "/aggregates/unit/3BN/trend", "/aggregates/simulations/levers",
                 "/aggregates/unit/3BN/forecast?horizon_weeks=4"]:
        r = client.get(path, headers=commander)
        assert r.status_code == 200, (path, r.status_code, r.text)
        assert "legal_name" not in r.text and "ps_demo01" not in r.text, path

    sim = client.post("/aggregates/simulations",
                      json={"unit_id": "3BN", "scenario": {"extend_deployment_days": 30}},
                      headers=commander)
    assert sim.status_code == 200, sim.text
    body = sim.json()
    assert body["suppressed"] is False
    assert "fatigue_index_delta" in body["projection"]
    assert client.get(f"/aggregates/simulations/{body['run_id']}", headers=commander).status_code == 200

    bad_sim = client.post("/aggregates/simulations",
                          json={"unit_id": "3BN", "scenario": {"extend_deployment_days": 9999}},
                          headers=commander)
    assert bad_sim.status_code == 400 and "validated range" in bad_sim.text

    # --- firewall still absolute for every new individual route ---
    for path in ["/app/consent", "/app/roster", "/app/buddy", "/app/pulse/me",
                 "/app/signals/summary", f"/interventions/case/{case_id}",
                 f"/interventions/case/{case_id}/notes", "/interventions/catalogue"]:
        r = client.get(path, headers=commander)
        assert r.status_code == 403, (path, r.status_code, r.text)

    # commander's own check-in works, outside /app, self-scope only
    own = client.post("/me/checkins", json={"mood_label": "ok", "mood_score": 7,
                                            "recorded_at": "2026-09-01"}, headers=commander)
    assert own.status_code == 200, own.text
    assert own.json()["self_scope"] is True
    assert client.get("/me/checkins", headers=commander).status_code == 200

    # a tiny unit stays suppressed everywhere
    tiny = client.get("/aggregates/unit/TINY/morale", headers=counsellor).json()
    assert tiny["suppressed"] is True and tiny["score"] is None
    tiny_sim = client.post("/aggregates/simulations",
                           json={"unit_id": "TINY", "scenario": {}}, headers=welfare).json()
    assert tiny_sim["suppressed"] is True and tiny_sim.get("projection") is None
