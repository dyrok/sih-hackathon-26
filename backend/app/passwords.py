from __future__ import annotations

import hashlib
import hmac
import secrets

_ROUNDS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _ROUNDS)
    return f"pbkdf2${_ROUNDS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds_s, salt, digest = stored.split("$", 3)
    except ValueError:
        return False
    if scheme != "pbkdf2":
        return False
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds_s)
    )
    return hmac.compare_digest(dk.hex(), digest)
