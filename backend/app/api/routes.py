"""API routes. Kept thin — validation via Pydantic, work delegated to services."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.ai.provider import ai_enabled, patch_digest, suggest_pick
from app.cache import cache
from app.dependencies import (
    get_champion_map,
    get_ddragon_version,
    get_riot_client,
    require_ai,
)
from app.riot.client import RiotAPIError, RiotClient, load_profile
from app.riot.matches import load_pool_for_riot_id
from app.riot.regions import PLATFORMS, UnknownRegionError
from app.schemas import Champion, ChampionPool, DraftRequest, DraftResponse, PatchDigest, Profile

router = APIRouter(prefix="/api", tags=["poropilot"])


@router.get("/regions")
def list_regions() -> dict[str, list[str]]:
    return {"regions": sorted(PLATFORMS)}


@router.get("/config")
def get_config(request: Request) -> dict:
    """Client-facing config — AI availability + the current Data Dragon version."""
    return {
        "ai_enabled": ai_enabled(),
        "ddragon_version": getattr(request.app.state, "ddragon_version", None),
    }


@router.get("/champions")
async def list_champions(
    champions: Annotated[dict[int, Champion], Depends(get_champion_map)],
) -> dict[int, Champion]:
    return champions


@router.get("/summoner/{region}/{name}/{tag}", response_model=Profile)
async def get_summoner(
    region: str,
    name: str,
    tag: str,
    client: Annotated[RiotClient, Depends(get_riot_client)],
) -> Profile:
    try:
        return await load_profile(client, region, name, tag)
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RiotAPIError as exc:
        status = 404 if exc.status_code == 404 else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/pool/{region}/{name}/{tag}", response_model=ChampionPool)
async def get_pool(
    region: str,
    name: str,
    tag: str,
    client: Annotated[RiotClient, Depends(get_riot_client)],
) -> ChampionPool:
    try:
        return await load_pool_for_riot_id(client, region, name, tag)
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RiotAPIError as exc:
        status = 404 if exc.status_code == 404 else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/patch-digest", response_model=PatchDigest, dependencies=[Depends(require_ai)])
async def get_patch_digest(
    champions: Annotated[list[str], Query()],
    version: Annotated[str, Depends(get_ddragon_version)],
) -> PatchDigest:
    key = f"patch-digest:{version}:{','.join(sorted(champions))}"
    cached = await cache.get(key)
    if cached is not None:
        return PatchDigest(**cached)
    # Blocking Anthropic call — offload to a thread so the event loop keeps serving.
    result = await asyncio.to_thread(patch_digest, champions, version)
    await cache.set(key, result, ttl=86400)  # stable for the life of a patch
    return PatchDigest(**result)


@router.post("/draft", response_model=DraftResponse, dependencies=[Depends(require_ai)])
def post_draft(req: DraftRequest) -> DraftResponse:
    # The Anthropic sync client is blocking; declaring this endpoint with plain
    # `def` lets FastAPI run it in its threadpool, so the event loop isn't blocked.
    result = suggest_pick(
        role=req.role,
        champion_pool=req.champion_pool,
        ally_picks=req.ally_picks,
        enemy_bans=req.enemy_bans,
        enemy_picks=req.enemy_picks,
    )
    return DraftResponse(**result)
