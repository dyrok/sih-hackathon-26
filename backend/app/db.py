from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def make_engine(url: str | None = None):
    url = url or get_settings().database_url
    engine = create_engine(url, connect_args=_connect_args(url), future=True)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def configure_engine(url: str) -> None:
    global engine
    engine = make_engine(url)
    SessionLocal.configure(bind=engine)


def install_audit_triggers(bind) -> None:
    """Reject UPDATE/DELETE on the append-only audit log (NFR-08 / TC-409)."""
    with bind.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS audit_events_no_update
                BEFORE UPDATE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'audit log is append-only');
                END;
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
                BEFORE DELETE ON audit_events
                BEGIN
                    SELECT RAISE(ABORT, 'audit log is append-only');
                END;
                """
            )
        )


def ensure_sitrep_pause_columns(bind) -> None:
    """SQLite create_all will not ALTER an existing duty_sitreps table."""
    url = str(bind.url) if hasattr(bind, "url") else ""
    if "sqlite" not in url:
        return
    with bind.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(duty_sitreps)")).fetchall()
        if not rows:
            return
        cols = {row[1] for row in rows}
        if "pause_count" not in cols:
            conn.execute(text("ALTER TABLE duty_sitreps ADD COLUMN pause_count INTEGER"))
        if "pause_total" not in cols:
            conn.execute(text("ALTER TABLE duty_sitreps ADD COLUMN pause_total FLOAT"))


def init_db(bind=None) -> None:
    from . import models  # noqa: F401

    bind = bind or engine
    Base.metadata.create_all(bind)
    install_audit_triggers(bind)
    ensure_sitrep_pause_columns(bind)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
