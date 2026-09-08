"""ADR-0003 architectural firewall — individual welfare data never reaches command."""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from .audit import write_audit
from .db import SessionLocal
from .models import User
from .security import decode_token

# Prefixes a commander JWT must never read. Route handlers also 403; this is belt-and-braces.
COMMANDER_DENIED_PREFIXES = (
    "/signals",
    "/risk",
    "/interventions",
    "/ingest",
    "/privacy/unmask",
    "/privacy/break-glass",
    "/app",
    "/welfare",
    "/admin",
)

COMMANDER_ALLOWED_EXACT = {
    "/health",
    "/auth/token",
    "/auth/me",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def path_denied_to_commander(path: str) -> bool:
    if path in COMMANDER_ALLOWED_EXACT:
        return False
    if path.startswith("/aggregates/"):
        return False
    if path.startswith("/roster/rebalance"):
        return False  # handler enforces workload-mode only
    if path.startswith("/auth/"):
        return False
    return any(path == p or path.startswith(p + "/") or path.startswith(p + "?") for p in COMMANDER_DENIED_PREFIXES) or any(
        path.startswith(p) for p in COMMANDER_DENIED_PREFIXES
    )


def forbid_commander(user: User, *, db: Session, resource_type: str, resource_id: str | None = None) -> None:
    if user.role != "commander":
        return
    write_audit(
        db,
        actor=user,
        action="firewall.deny",
        resource_type=resource_type,
        resource_id=resource_id,
        denied=True,
        reason="ADR-0003 commander cannot access individual welfare data",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="commander identity cannot access individual welfare data (ADR-0003)",
    )


class CommanderFirewallMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        auth = request.headers.get("authorization") or ""
        if not auth.lower().startswith("bearer "):
            return await call_next(request)
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except Exception:
            return await call_next(request)
        if payload.get("role") != "commander":
            return await call_next(request)
        if not path_denied_to_commander(path):
            return await call_next(request)
        db = SessionLocal()
        try:
            user = db.get(User, payload.get("sub"))
            write_audit(
                db,
                actor=user,
                action="firewall.deny",
                resource_type="route",
                resource_id=path,
                denied=True,
                reason="ADR-0003 middleware",
                payload={"method": request.method, "path": path},
            )
            db.commit()
        finally:
            db.close()
        return JSONResponse(
            status_code=403,
            content={"detail": "commander identity cannot access individual welfare data (ADR-0003)"},
        )
