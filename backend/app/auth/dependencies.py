"""Auth dependencies for protecting routes."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_user_by_id
from app.auth.tokens import decode_token
from app.db import get_session
from app.models import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Extracts and validates the JWT from the Authorization header.

    Returns the User or raises 401 — never 500.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = decode_token(credentials.credentials, expected_type="access")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_refresh_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """Validates the refresh token from an httpOnly cookie."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    user_id = decode_token(refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
