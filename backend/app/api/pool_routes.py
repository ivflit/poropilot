"""Saved champion pool presets — CRUD scoped to the authenticated user."""

from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db import get_session
from app.models import SavedPool, User

router = APIRouter(prefix="/api/me/pools", tags=["pools"])


class Role(StrEnum):
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MID = "MID"
    BOT = "BOT"
    SUPPORT = "SUPPORT"


class SavePoolRequest(BaseModel):
    champions: list[str]


class PoolResponse(BaseModel):
    role: str
    champions: list[str]


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[PoolResponse])
async def list_pools(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PoolResponse]:
    result = await session.execute(
        select(SavedPool).where(SavedPool.user_id == user.id)
    )
    return [PoolResponse(role=p.role, champions=p.champions) for p in result.scalars()]


@router.put("/{role}", response_model=PoolResponse)
async def save_pool(
    role: Role,
    body: SavePoolRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PoolResponse:
    result = await session.execute(
        select(SavedPool).where(SavedPool.user_id == user.id, SavedPool.role == role.value)
    )
    pool = result.scalar_one_or_none()

    if pool:
        pool.champions = body.champions
    else:
        pool = SavedPool(user_id=user.id, role=role.value, champions=body.champions)
        session.add(pool)

    await session.commit()
    await session.refresh(pool)
    return PoolResponse(role=pool.role, champions=pool.champions)


@router.delete("/{role}", status_code=204)
async def delete_pool(
    role: Role,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    await session.execute(
        delete(SavedPool).where(SavedPool.user_id == user.id, SavedPool.role == role.value)
    )
    await session.commit()
