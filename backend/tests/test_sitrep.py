"""Officer voice sitrep — self-scope only, never a channel for another person."""

from __future__ import annotations

from tests.conftest import auth_header


SAMPLE = (
    "Morning inspection of the lines at 0530. Parade and PT until 0700. "
    "Two sections on the eastern fence, no incident. Long day. Voice is going."
)


def test_commander_can_file_and_reread_own_sitrep(client):
    h = auth_header(client, "commander.3bn")
    r = client.post(
        "/me/sitreps",
        headers=h,
        json={"transcript": SAMPLE, "duration_s": 28, "rms_mean": 0.03, "rms_var": 0.006},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["self_scope"] is True
    assert body["heuristic"] is True
    assert "work_summary" in body
    assert body["tone_label"] in {"calm", "strained", "flat"}
    assert 1 <= body["mood_score"] <= 9
    listed = client.get("/me/sitreps", headers=h)
    assert listed.status_code == 200
    ids = [s["id"] for s in listed.json()["sitreps"]]
    assert body["id"] in ids


def test_seeded_dummy_sitreps_exist_for_the_demo_officer(client):
    h = auth_header(client, "commander.3bn")
    r = client.get("/me/sitreps", headers=h)
    assert r.status_code == 200
    rows = r.json()["sitreps"]
    assert len(rows) >= 6
    joined = " ".join(s["transcript"] for s in rows)
    assert "ps_demo01" not in joined
    assert "Demo Constable" not in joined
    assert "legal_name" not in joined


def test_another_commander_cannot_read_those_rows(client):
    owner = auth_header(client, "commander.3bn")
    other = auth_header(client, "commander.tiny")
    mine = client.get("/me/sitreps", headers=owner).json()["sitreps"]
    theirs = client.get("/me/sitreps", headers=other).json()["sitreps"]
    assert mine
    mine_ids = {s["id"] for s in mine}
    their_ids = {s["id"] for s in theirs}
    assert mine_ids.isdisjoint(their_ids)


def test_jawan_and_counsellor_are_refused(client):
    r = client.get("/me/sitreps", headers=auth_header(client, "jawan.demo"))
    assert r.status_code == 403
    r = client.post(
        "/me/sitreps",
        headers=auth_header(client, "counsellor.a"),
        json={"transcript": SAMPLE},
    )
    assert r.status_code == 403


def test_questions_surface_for_a_long_day(client):
    from app.sitrep_analyze import pick_questions

    qs = pick_questions(SAMPLE)
    assert "hours" in qs or "sleep" in qs
    assert len(qs) <= 2
