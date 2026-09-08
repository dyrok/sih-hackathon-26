from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RULESET_PATH = BACKEND_ROOT / "config" / "rulesets" / "v1.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAARTHI_", extra="ignore")

    database_url: str = "sqlite:///./saarthi.db"
    jwt_secret: str = "saarthi-dev-secret-change-me-32b+"
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

    def as_of_date(self) -> date:
        y, m, d = (int(p) for p in self.demo_as_of.split("-"))
        return date(y, m, d)


@lru_cache
def get_settings() -> Settings:
    return Settings()
