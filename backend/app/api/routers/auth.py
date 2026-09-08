from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_db
from ...security import authenticate, create_token, get_current_user
from ...models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    unit_id: str | None = None
    pseudonym_id: str | None = None


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/token", response_model=TokenOut)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate(db, form.username, form.password)
    return TokenOut(
        access_token=create_token(user),
        role=user.role,
        unit_id=user.unit_id,
        pseudonym_id=user.pseudonym_id,
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = authenticate(db, body.username, body.password)
    return TokenOut(
        access_token=create_token(user),
        role=user.role,
        unit_id=user.unit_id,
        pseudonym_id=user.pseudonym_id,
    )


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "unit_id": user.unit_id,
        "pseudonym_id": user.pseudonym_id,
        "display_name": user.display_name,
    }
