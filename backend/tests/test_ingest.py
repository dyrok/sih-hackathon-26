from __future__ import annotations

from tests.conftest import auth_header


def test_json_ingest_quarantines_unknown_and_malformed(client):
    h = auth_header(client, "hr.ingest")
    r = client.post(
        "/ingest/hr/leave",
        headers=h,
        json={
            "batch_id": "hr-test-leave-1",
            "rows": [
                {
                    "personnel_id": "CR-DEMO-01",
                    "leave_type": "casual",
                    "applied_at": "2026-08-01",
                    "denied": True,
                    "denial_reason": "op_commitment",
                },
                {"personnel_id": "NO-SUCH", "leave_type": "casual", "applied_at": "2026-08-02"},
                {"personnel_id": "CR-DEMO-01", "leave_type": "casual"},  # missing applied_at
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rows_in"] == 3
    assert body["rows_written"] == 1
    assert body["rows_quarantined"] == 2
    report = client.get(body["quarantine_report_url"], headers=h)
    assert report.status_code == 200
    assert len(report.json()["rows"]) == 2


def test_duplicate_batch_is_noop(client):
    h = auth_header(client, "hr.ingest")
    payload = {
        "batch_id": "hr-test-leave-dup",
        "rows": [
            {"personnel_id": "CR-DEMO-01", "leave_type": "casual", "applied_at": "2026-05-01"},
        ],
    }
    a = client.post("/ingest/hr/leave", headers=h, json=payload)
    b = client.post("/ingest/hr/leave", headers=h, json=payload)
    assert a.status_code == 200 and b.status_code == 200
    assert b.json()["status"] == "duplicate_noop"


def test_csv_ingest(client):
    h = auth_header(client, "hr.ingest")
    csv = "personnel_id,visit_date,visit_type,injury_flag\nCR-DEMO-01,2026-08-15,sick_report,false\n"
    r = client.post(
        "/ingest/hr/csv",
        headers=h,
        params={"dataset": "medical"},
        files={"file": ("med.csv", csv, "text/csv")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["rows_written"] == 1


def test_group_exposure_is_unit_scoped(client):
    h = auth_header(client, "counsellor.a")
    r = client.get("/signals/group/3BN/exposure", headers=h)
    assert r.status_code == 200
    flags = r.json()["flags"]
    keys = {f["signal_key"] for f in flags}
    assert "unit_incident_exposure" in keys
    for f in flags:
        assert "personnel" not in f
        assert "legal_name" not in f


def test_commander_cannot_ingest(client):
    h = auth_header(client, "commander.3bn")
    r = client.post("/ingest/hr/leave", headers=h, json={"batch_id": "x", "rows": []})
    assert r.status_code == 403
