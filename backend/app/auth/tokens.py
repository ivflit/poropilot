"""JWT access and refresh token creation / verification."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

_SECRET = settings.jwt_secret
_ALGO = settings.jwt_algorithm


def create_access_token(user_id: int) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires, "type": "access"}, _SECRET, algorithm=_ALGO)


def create_refresh_token(user_id: int) -> str:
    expires = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode({"sub": str(user_id), "exp": expires, "type": "refresh"}, _SECRET, algorithm=_ALGO)


def decode_token(token: str, expected_type: str = "access") -> int | None:
    """Return the user_id if the token is valid, else None."""
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGO])
        if payload.get("type") != expected_type:
            return None
        user_id = payload.get("sub")
        return int(user_id) if user_id is not None else None
    except (JWTError, ValueError):
        return None
