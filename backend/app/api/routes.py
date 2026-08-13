"""API routes. Kept thin — validation via Pydantic, work delegated to services."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.ai.provider import ai_enabled, generate_tier_list, patch_digest, review_match, suggest_pick
from app.ratelimit import limiter
from app.ai.review import derive_stats, is_ranked
from app.cache import cache
from app.config import settings
from app.dependencies import (
    get_champion_map,
    get_ddragon_version,
    get_riot_client,
    require_ai,
)
from app.riot.client import RiotAPIError, RiotClient, load_profile
from app.riot.history import MatchResult, MatchRole, MatchSort, build_match_detail, compute_aggregate
from app.riot.matches import analyse_champion_pool, fetch_recent_matches, load_pool_for_riot_id
from app.riot.queues import MatchQueue
from app.riot.regions import PLATFORMS, UnknownRegionError
from app.schemas import (
    Champion,
    ChampionPool,
    DraftRequest,
    DraftResponse,
    LiveGameParticipant,
    LiveGameResponse,
    MatchHistoryResponse,
    MatchReview,
    MatchSummary,
    MultiSearchPlayer,
    MultiSearchRequest,
    MultiSearchResponse,
    PatchDigest,
    Profile,
    TierListResponse,
)

router = APIRouter(prefix="/api", tags=["poropilot"])


@router.get("/regions")
def list_regions() -> dict[str, list[str]]:
    return {"regions": sorted(PLATFORMS)}


@router.get("/config")
def get_config(request: Request) -> dict:
    """Client-facing config — AI availability + the current Data Dragon version."""
    return {
        "ai_enabled": ai_enabled(),
        "auth_enabled": bool(settings.database_url),
        "ddragon_version": getattr(request.app.state, "ddragon_version", None),
    }


@router.get("/champions")
async def list_champions(
    champions: Annotated[dict[int, Champion], Depends(get_champion_map)],
) -> dict[int, Champion]:
    return champions


@router.get("/summoner/{region}/{name}/{tag}", response_model=Profile)
@limiter.limit("20/minute")
async def get_summoner(
    request: Request,
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
@limiter.limit("20/minute")
async def get_pool(
    request: Request,
    region: str,
    name: str,
    tag: str,
    client: Annotated[RiotClient, Depends(get_riot_client)],
    queue: Annotated[MatchQueue, Query(description="Filter matches by queue")] = MatchQueue.ALL,
) -> ChampionPool:
    try:
        return await load_pool_for_riot_id(client, region, name, tag, queue=queue)
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RiotAPIError as exc:
        status = 404 if exc.status_code == 404 else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/live/{region}/{name}/{tag}", response_model=LiveGameResponse)
@limiter.limit("10/minute")
async def get_live_game(
    request: Request,
    region: str,
    name: str,
    tag: str,
    client: Annotated[RiotClient, Depends(get_riot_client)],
    champions: Annotated[dict[int, Champion], Depends(get_champion_map)],
) -> LiveGameResponse:
    """Check if a summoner is in an active game and return participant info."""
    try:
        from app.riot.regions import platform_host, regional_route

        platform = platform_host(region)
        cluster = regional_route(platform)
        account = await client.account_by_riot_id(cluster, name, tag)
        puuid = account["puuid"]
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RiotAPIError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        game = await client.active_game(platform, puuid)
    except RiotAPIError as exc:
        if exc.status_code == 404:
            return LiveGameResponse(in_game=False)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Fetch all participant ranks in parallel (not N+1 serial).
    raw_participants = game.get("participants", [])

    async def _rank_for(p_puuid: str | None) -> str | None:
        if not p_puuid:
            return None
        try:
            entries = await client.league_entries(platform, p_puuid)
            solo = next((e for e in entries if e.get("queueType") == "RANKED_SOLO_5x5"), None)
            if solo:
                return f"{solo['tier']} {solo['rank']} {solo['leaguePoints']} LP"
        except RiotAPIError:
            pass
        return None

    ranks = await asyncio.gather(*(_rank_for(p.get("puuid")) for p in raw_participants))

    participants = []
    for p, rank_str in zip(raw_participants, ranks, strict=True):
        champ_id = p.get("championId", 0)
        champ_info = champions.get(champ_id)
        participants.append(LiveGameParticipant(
            champion_id=champ_id,
            champion_name=champ_info.name if champ_info else f"Champion {champ_id}",
            team_id=p.get("teamId", 0),
            riot_id=p.get("riotId", "") or p.get("summonerName", "Unknown"),
            rank=rank_str,
        ))

    return LiveGameResponse(
        in_game=True,
        game_mode=game.get("gameMode", ""),
        game_length_sec=game.get("gameLength", 0),
        participants=participants,
    )


@router.post("/multi-search", response_model=MultiSearchResponse)
@limiter.limit("10/minute")
async def multi_search(
    request: Request,
    req: MultiSearchRequest,
    client: Annotated[RiotClient, Depends(get_riot_client)],
) -> MultiSearchResponse:
    """Look up multiple summoners in parallel — for champ-select lobby scouting."""
    from app.riot.regions import platform_host, regional_route

    try:
        platform = platform_host(req.region)
        cluster = regional_route(platform)
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Cap at 5 to keep it sane.
    riot_ids = req.riot_ids[:5]

    async def lookup_one(riot_id: str) -> MultiSearchPlayer:
        if "#" not in riot_id:
            return MultiSearchPlayer(riot_id=riot_id, found=False)
        name, tag = riot_id.split("#", 1)
        try:
            account = await client.account_by_riot_id(cluster, name.strip(), tag.strip())
            puuid = account["puuid"]
            summoner = await client.summoner_by_puuid(platform, puuid)
            entries = await client.league_entries(platform, puuid)
            pool = await analyse_champion_pool(
                client, req.region, puuid, count=10, top=3,
            )
            return MultiSearchPlayer(
                riot_id=f"{account['gameName']}#{account['tagLine']}",
                found=True,
                region=req.region.upper(),
                level=summoner.get("summonerLevel"),
                profile_icon_id=summoner.get("profileIconId"),
                ranked=entries,
                top_champions=pool.top,
            )
        except RiotAPIError as exc:
            if exc.status_code == 404:
                return MultiSearchPlayer(riot_id=riot_id, found=False)
            return MultiSearchPlayer(riot_id=riot_id, found=False, error="Lookup failed")

    players = await asyncio.gather(*(lookup_one(rid) for rid in riot_ids))
    return MultiSearchResponse(players=list(players))


@router.get("/patch-digest", response_model=PatchDigest, dependencies=[Depends(require_ai)])
@limiter.limit("5/minute")
async def get_patch_digest(
    request: Request,
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


@router.get("/tier-list", response_model=TierListResponse, dependencies=[Depends(require_ai)])
@limiter.limit("5/minute")
async def get_tier_list(
    request: Request,
    role: Annotated[str, Query(description="Role: TOP, JUNGLE, MID, ADC, SUPPORT")],
    version: Annotated[str, Depends(get_ddragon_version)],
) -> TierListResponse:
    """AI-generated champion tier list for a role in the current patch."""
    role_upper = role.upper()
    key = f"tier-list:{version}:{role_upper}"
    cached = await cache.get(key)
    if cached is not None:
        return TierListResponse(**cached)
    result = await asyncio.to_thread(generate_tier_list, role_upper, version)
    response = {"role": role_upper, "patch": version, "tiers": result.get("tiers", [])}
    await cache.set(key, response, ttl=86400)
    return TierListResponse(**response)


@router.post("/draft", response_model=DraftResponse, dependencies=[Depends(require_ai)])
@limiter.limit("10/minute")
def post_draft(request: Request, req: DraftRequest) -> DraftResponse:
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


@router.get("/matches/{region}/{name}/{tag}", response_model=list[MatchSummary])
@limiter.limit("20/minute")
async def get_recent_matches(
    request: Request,
    region: str,
    name: str,
    tag: str,
    client: Annotated[RiotClient, Depends(get_riot_client)],
    queue: Annotated[MatchQueue, Query(description="Filter matches by queue")] = MatchQueue.SOLO,
) -> list[MatchSummary]:
    """Recent match summaries for a player — used by the review picker."""
    try:
        from app.riot.regions import platform_host, regional_route

        platform = platform_host(region)
        cluster = regional_route(platform)
        account = await client.account_by_riot_id(cluster, name, tag)
        puuid = account["puuid"]
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RiotAPIError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    matches = await fetch_recent_matches(client, region, puuid, count=10, queue=queue)
    summaries = []
    for m in matches:
        for p in m.get("info", {}).get("participants", []):
            if p.get("puuid") == puuid:
                duration = m.get("info", {}).get("gameDuration", 0) / 60
                summaries.append(MatchSummary(
                    match_id=m.get("metadata", {}).get("matchId", ""),
                    champion=p.get("championName", "?"),
                    win=p.get("win", False),
                    kills=p.get("kills", 0),
                    deaths=p.get("deaths", 0),
                    assists=p.get("assists", 0),
                    queue_id=m.get("info", {}).get("queueId", 0),
                    duration_min=round(duration, 1),
                ))
                break
    return summaries


@router.get("/history/{region}/{name}/{tag}", response_model=MatchHistoryResponse)
@limiter.limit("20/minute")
async def get_match_history(
    request: Request,
    region: str,
    name: str,
    tag: str,
    client: Annotated[RiotClient, Depends(get_riot_client)],
    queue: Annotated[MatchQueue, Query(description="Filter matches by queue")] = MatchQueue.ALL,
    count: Annotated[int, Query(ge=1, le=50, description="Number of matches")] = 20,
    start: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    role: Annotated[MatchRole, Query(description="Filter by role")] = MatchRole.ALL,
    result: Annotated[MatchResult, Query(description="Filter by W/L")] = MatchResult.ALL,
    sort: Annotated[MatchSort, Query(description="Sort order")] = MatchSort.NEWEST,
    champion: Annotated[str | None, Query(description="Filter by champion name")] = None,
    opponent: Annotated[str | None, Query(description="Filter by opponent champion")] = None,
) -> MatchHistoryResponse:
    """Rich match history with filtering and sorting."""
    try:
        from app.riot.regions import platform_host, regional_route

        platform = platform_host(region)
        cluster = regional_route(platform)
        account = await client.account_by_riot_id(cluster, name, tag)
        puuid = account["puuid"]
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RiotAPIError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Fetch more than requested to allow for post-fetch filtering by role/result.
    # The queue filter is applied at source by Riot, but role/result are post-fetch.
    fetch_count = count + start + 30  # overfetch to fill the page after filtering
    raw_matches = await fetch_recent_matches(client, region, puuid, count=fetch_count, queue=queue)

    details = []
    for m in raw_matches:
        detail = build_match_detail(m, puuid)
        if detail is None:
            continue
        if role != MatchRole.ALL and detail.role.upper() != role.value.upper():
            continue
        if result == MatchResult.WIN and not detail.win:
            continue
        if result == MatchResult.LOSS and detail.win:
            continue
        if champion and detail.champion.lower() != champion.lower():
            continue
        if opponent and detail.opponent_champion.lower() != opponent.lower():
            continue
        details.append(detail)

    # Sort.
    if sort == MatchSort.OLDEST:
        details.sort(key=lambda d: d.game_start)
    elif sort == MatchSort.CS_MIN:
        details.sort(key=lambda d: d.cs_per_min, reverse=True)
    elif sort == MatchSort.DMG_MIN:
        details.sort(key=lambda d: d.damage_per_min, reverse=True)
    # NEWEST is already the default order from Riot.

    # Aggregate is computed over ALL filtered matches (before pagination).
    aggregate = compute_aggregate(details)

    # Paginate.
    page = details[start : start + count]
    return MatchHistoryResponse(matches=page, total_fetched=len(details), aggregate=aggregate)


@router.get(
    "/review/{region}/{name}/{tag}/{match_id}",
    response_model=MatchReview,
    dependencies=[Depends(require_ai)],
)
@limiter.limit("5/minute")
async def get_review(
    request: Request,
    region: str,
    name: str,
    tag: str,
    match_id: str,
    client: Annotated[RiotClient, Depends(get_riot_client)],
) -> MatchReview:
    """AI review of a specific ranked match for the given player."""
    # Resolve Riot ID → PUUID.
    try:
        from app.riot.regions import platform_host, regional_route

        platform = platform_host(region)
        cluster = regional_route(platform)
        account = await client.account_by_riot_id(cluster, name, tag)
        puuid = account["puuid"]
    except UnknownRegionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RiotAPIError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Check cache first.
    cache_key = f"review:{match_id}:{puuid}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return MatchReview(**cached)

    # Fetch the match.
    try:
        match = await client.match(cluster, match_id)
    except RiotAPIError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not is_ranked(match):
        raise HTTPException(status_code=422, detail="Only ranked games can be reviewed.")

    stats = derive_stats(match, puuid)
    if not stats:
        raise HTTPException(status_code=404, detail="Player not found in this match.")

    # Blocking AI call → offload to thread.
    ai_result = await asyncio.to_thread(review_match, stats)

    result = {
        "match_id": match_id,
        "champion": stats["champion"],
        "win": stats["win"],
        **ai_result,
    }
    await cache.set(cache_key, result, ttl=86400)
    return MatchReview(**result)
