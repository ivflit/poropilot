"""Auth routes — signup, login, logout, refresh, me, link Riot ID."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_refresh_user
from app.auth.service import authenticate, create_user, get_user_by_email, link_riot_id
from app.auth.tokens import create_access_token, create_refresh_token
from app.config import settings
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas (kept local — only these routes use them) ──────────────────────────


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    riot_region: str | None = None
    riot_name: str | None = None
    riot_tag: str | None = None


class LinkRiotIdRequest(BaseModel):
    region: str
    name: str
    tag: str


# ── Helpers ────────────────────────────────────────────────────────────────────


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="refresh_token", path="/api/auth")


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        riot_region=user.riot_region,
        riot_name=user.riot_name,
        riot_tag=user.riot_tag,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    body: SignupRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    if await get_user_by_email(session, body.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = await create_user(session, body.email, body.password)
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    user = await authenticate(session, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    _clear_refresh_cookie(response)
    return {"detail": "Logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    user: Annotated[User, Depends(get_refresh_user)],
) -> TokenResponse:
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return _user_response(user)


@router.put("/me/riot-id", response_model=UserResponse)
async def link_riot(
    body: LinkRiotIdRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    updated = await link_riot_id(session, user, body.region, body.name, body.tag)
    return _user_response(updated)
