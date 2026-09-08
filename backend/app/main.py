from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import app_data, audit_api, auth, ingest, interventions, privacy, risk, signals
from .db import init_db
from .firewall import CommanderFirewallMiddleware
from .i18n import STRINGS


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SAARTHI Core API",
    description="AI-based predictive personnel stress & welfare monitoring. Welfare, not discipline.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CommanderFirewallMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(signals.router)
app.include_router(risk.router)
app.include_router(interventions.router)
app.include_router(privacy.router)
app.include_router(app_data.router)
app.include_router(audit_api.router)


@app.get("/health")
def health():
    return {"ok": True, "service": "saarthi", "welfare_not_discipline": True}


@app.get("/i18n/{lang}")
def i18n(lang: str):
    return STRINGS.get(lang) or STRINGS["en"]
