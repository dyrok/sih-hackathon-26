from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import User
from .passwords import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

ROLES = (
    "jawan",
    "counsellor",
    "welfare_officer",
    "commander",
    "admin",
    "auditor",
    "hr_ingest",
)

COMMANDER = "commander"
ADMIN = "admin"


def create_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "role": user.role,
        "unit_id": user.unit_id,
        "pseudonym_id": user.pseudonym_id,
        "username": user.username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.jwt_expire_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc


#: Failed-login timestamps per username. In-process on purpose: SAARTHI is an
#: on-prem, single-instance deployment (NFR-03), so a shared store would add a
#: dependency for no gain. A multi-instance deployment must move this to the
#: database or a cache — recorded in security-model.md.
_FAILURES: dict[str, deque] = defaultdict(deque)


def _throttle(username: str) -> None:
    """Refuse a password guess once the window budget is spent (TC-457).

    Keyed on username rather than IP: the threat is credential stuffing against
    a known account list, and every console sits behind the same LAN NAT, where
    an IP key would throttle a whole unit for one attacker.
    """
    settings = get_settings()
    now = time.monotonic()
    window = settings.login_window_seconds
    attempts = _FAILURES[username]
    while attempts and now - attempts[0] > window:
        attempts.popleft()
    if len(attempts) >= settings.login_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many failed sign-in attempts; try again later",
            headers={"Retry-After": str(window)},
        )


def _record_failure(username: str) -> None:
    _FAILURES[username].append(time.monotonic())


def reset_login_throttle() -> None:
    """Test seam — the counter is process-global by design."""
    _FAILURES.clear()


def authenticate(db: Session, username: str, password: str) -> User:
    _throttle(username)
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        _record_failure(username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")
    _FAILURES.pop(username, None)
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown user")
    return user


def require_roles(*roles: str):
    def _inner(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
        return user

    return _inner
