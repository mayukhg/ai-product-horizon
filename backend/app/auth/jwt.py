from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import settings


class AuthError(Exception):
    pass


def _require_secret() -> str:
    if not settings.auth_jwt_secret.strip():
        raise AuthError("AUTH_JWT_SECRET is not configured")
    return settings.auth_jwt_secret


def create_access_token(subject: str, *, expires_minutes: int = 60, role: str = "operator") -> str:
    secret = _require_secret()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "aud": settings.auth_jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm=settings.auth_jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    secret = _require_secret()
    return jwt.decode(
        token,
        secret,
        algorithms=[settings.auth_jwt_algorithm],
        audience=settings.auth_jwt_audience,
    )
