from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import AuthError, decode_access_token
from app.config import settings

_bearer = HTTPBearer(auto_error=False)


async def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any] | None:
    if credentials is None:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except AuthError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth is misconfigured")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_current_user(user: dict[str, Any] | None = Depends(optional_user)) -> dict[str, Any]:
    if not settings.auth_required:
        return user or {"sub": "anonymous", "role": "operator"}
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")
    return user
