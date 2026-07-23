"""API routes. Kept thin — validation via Pydantic, work delegated to services."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..ai.draft import suggest_pick
from ..dependencies import get_champion_map, get_riot_client
from ..riot.client import RiotAPIError, RiotClient, load_profile
from ..riot.matches import load_pool_for_riot_id
from ..riot.regions import PLATFORMS, UnknownRegionError
from ..schemas import Champion, ChampionPool, DraftRequest, DraftResponse, Profile

router = APIRouter(prefix="/api", tags=["poropilot"])


@router.get("/regions")
def list_regions() -> dict[str, list[str]]:
    return {"regions": sorted(PLATFORMS)}


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


@router.post("/draft", response_model=DraftResponse)
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
