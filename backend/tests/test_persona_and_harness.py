from __future__ import annotations

from app.clock import set_as_of
from app.db import SessionLocal
from app.ml.harness import persona_arc, threshold_sweep, v2_readiness
from app.models import RiskScore
from app.seed import PERSONA_PSEUDONYM
from tests.conftest import auth_header


def test_persona_has_explainable_score(client):
    h = auth_header(client, "counsellor.a")
    r = client.get("/risk/ps_demo01/explanation", headers=h)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["top_factors"]
    assert len(data["top_factors"]) <= 3
    for f in data["top_factors"]:
        assert f["key"].startswith("risk.factor.")
        assert f["text"]


def test_persona_arc_harness(client):
    db = SessionLocal()
    try:
        report = persona_arc(db)
        db.commit()
    finally:
        db.close()
        set_as_of(None)
    assert report["ok"], report["diffs"]


def test_threshold_sweep_and_v2_probe(client):
    db = SessionLocal()
    try:
        sweep = threshold_sweep(db)
        ready = v2_readiness(db)
        db.commit()
    finally:
        db.close()
        set_as_of(None)
    assert len(sweep) == 5
    assert "labels" in ready
    assert ready["defensible"] is False or ready["labels"] >= 200


def test_who_viewed_after_counsellor_read(client):
    c = auth_header(client, "counsellor.a")
    client.get("/risk/ps_demo01", headers=c)
    j = auth_header(client, "jawan.demo")
    feed = client.get("/app/who-viewed", headers=j)
    assert feed.status_code == 200
    roles = {e["role"] for e in feed.json()["entries"]}
    assert "counsellor" in roles


def test_i18n_keys_en_and_hi(client):
    en = client.get("/i18n/en").json()
    hi = client.get("/i18n/hi").json()
    required = [
        "whoViewed.title",
        "consent.withdraw.action",
        "instr.not_diagnosis",
        "risk.factor.duty_streak",
        "risk.factor.masking",
    ]
    for k in required:
        assert k in en and k in hi


def test_seeded_scores_in_range(client):
    db = SessionLocal()
    try:
        rows = db.query(RiskScore).filter(RiskScore.pseudonym_id == PERSONA_PSEUDONYM).all()
        assert rows
        for r in rows:
            assert 0 <= r.score <= 100
    finally:
        db.close()
