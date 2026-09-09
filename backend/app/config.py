from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RULESET_PATH = BACKEND_ROOT / "config" / "rulesets" / "v1.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SAARTHI_",
        extra="ignore",
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
    )

    database_url: str = "sqlite:///./saarthi.db"
    #: "demo" (laptop / air-gapped jury demo) or "production". The value gates
    #: the checks below: a demo must start with zero configuration, a production
    #: deployment must refuse to start on a committed secret (TC-415).
    env: str = "demo"
    jwt_secret: str = "saarthi-dev-secret-change-me-32b+"
    #: Comma-separated allowed browser origins. "*" is accepted only in demo
    #: mode; with credentials enabled it is a CSRF surface (TC-456).
    cors_origins: str = "http://localhost:3100,http://localhost:3200,http://localhost:3300,http://127.0.0.1:3100,http://127.0.0.1:3200,http://127.0.0.1:3300"
    login_max_attempts: int = 10
    login_window_seconds: int = 300
    break_glass_weekly_cap: int = 3
    max_ingest_bytes: int = 8 * 1024 * 1024
    jwt_expire_hours: int = 12
    life_events_enabled: bool = False
    k_anonymity: int = 5
    counsellor_weekly_cap: int = 15
    unit_weekly_cap: int = 40
    demo_as_of: str = "2026-09-01"
    engine_version: str = "v1.0"
    ruleset_version: int = 1
    break_glass_hours: int = 24
    unmask_session_hours: int = 8
    raw_ttl_days: int = 90
    triage_w_urgency: float = 0.6
    triage_w_intervenability: float = 0.4
    #: OpenRouter key for the officer sitrep LLM. Empty = heuristic only.
    #: Never commit this; it lives in backend/.env (gitignored).
    openrouter_api_key: str = ""
    openrouter_model: str = "poolside/laguna-s-2.1:free"

    DEV_SECRET: ClassVar[str] = "saarthi-dev-secret-change-me-32b+"

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"prod", "production"}

    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def assert_deployable(self) -> None:
        """Fail fast rather than run a pilot on the committed dev secret."""
        if not self.is_production:
            return
        problems = []
        if self.jwt_secret == self.DEV_SECRET:
            problems.append("SAARTHI_JWT_SECRET is still the committed dev value")
        if len(self.jwt_secret) < 32:
            problems.append("SAARTHI_JWT_SECRET must be at least 32 bytes")
        if "*" in self.allowed_origins():
            problems.append("SAARTHI_CORS_ORIGINS must not be '*' in production")
        if self.database_url.startswith("sqlite"):
            problems.append("SAARTHI_DATABASE_URL must not be SQLite in production (ADR-0006)")
        if problems:
            raise RuntimeError("refusing to start: " + "; ".join(problems))

    def as_of_date(self) -> date:
        y, m, d = (int(p) for p in self.demo_as_of.split("-"))
        return date(y, m, d)


@lru_cache
def get_settings() -> Settings:
    return Settings()
