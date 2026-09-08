from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.clock import set_as_of
from app.config import get_settings
from app.db import SessionLocal, configure_engine, init_db
from app.main import app
from app.seed import DEMO_PASSWORD, seed_demo


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path}/saarthi.db"


@pytest.fixture
def client(db_url):
    configure_engine(db_url)
    init_db()
    set_as_of(get_settings().as_of_date())
    db = SessionLocal()
    try:
        seed_demo(db, score=True)
        db.commit()
    finally:
        db.close()
    with TestClient(app) as c:
        yield c
    set_as_of(None)


def login(client: TestClient, username: str, password: str = DEMO_PASSWORD) -> str:
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth_header(client: TestClient, username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {login(client, username)}"}
