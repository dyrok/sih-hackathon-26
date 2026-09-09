from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import (
    app_data,
    audit_api,
    auth,
    buddy,
    commander,
    counsellor,
    ingest,
    interventions,
    privacy,
    pulse,
    risk,
    self_service,
    signals,
)
from .config import get_settings
from .db import init_db
from .firewall import CommanderFirewallMiddleware
from .i18n import STRINGS


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_settings().assert_deployable()
    init_db()
    yield


app = FastAPI(
    title="SAARTHI Core API",
    description="AI-based predictive personnel stress & welfare monitoring. Welfare, not discipline.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CommanderFirewallMiddleware)
# An origin allow-list, not a wildcard: "*" with credentials lets any page a
# counsellor happens to open ride their session (TC-456). The demo default lists
# the three local console ports; production must set SAARTHI_CORS_ORIGINS.
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(signals.router)
app.include_router(risk.router)
app.include_router(interventions.router)
app.include_router(privacy.router)
app.include_router(app_data.router)
app.include_router(audit_api.router)
# Client-surface routers (neel — APP-002..010). Additive: the routes above
# are unchanged, and every route below is either self-scoped or k-filtered.
app.include_router(self_service.router)
app.include_router(pulse.router)
app.include_router(buddy.router)
app.include_router(counsellor.router)
app.include_router(commander.router)


@app.get("/health")
def health():
    settings = get_settings()
    return {
        "ok": True,
        "service": "saarthi",
        "welfare_not_discipline": True,
        "env": settings.env,
        "engine_version": settings.engine_version,
        "ruleset_version": settings.ruleset_version,
        "k_anonymity": settings.k_anonymity,
    }


@app.get("/i18n/{lang}")
def i18n(lang: str):
    return STRINGS.get(lang) or STRINGS["en"]
