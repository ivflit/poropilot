"""Match-history fetching for champion-pool analysis.

Riot's Match-V5 `by-puuid/ids` endpoint returns at most 100 ids per request, so
fetching the last N matches means paging in batches of 100. Match detail is
cached per match id by the client (a finished game is immutable), so repeat
analysis costs no extra Riot calls.

Detail for the paged ids is fetched concurrently but capped by a semaphore, so
a big history is analysed quickly while in-flight Riot calls stay well under the
dev key's ~20 req/s budget — batched and cached, never a burst.
"""

import asyncio
import logging

from ..schemas import ChampionPool
from .analysis import aggregate_champion_stats, top_champions
from .client import RiotAPIError, RiotClient
from .regions import platform_host, regional_route

logger = logging.getLogger(__name__)

RIOT_MAX_IDS_PER_PAGE = 100
MAX_CONCURRENT_MATCH_REQUESTS = 10  # cap in-flight match fetches under the ~20 req/s dev limit


async def recent_match_ids(client: RiotClient, cluster: str, puuid: str, count: int) -> list[str]:
    """The most recent `count` match ids for a PUUID, paged in batches of 100."""
    if count <= 0:
        return []

    ids: list[str] = []
    start = 0
    while len(ids) < count:
        page = await client.match_ids(
            cluster,
            puuid,
            start=start,
            count=min(RIOT_MAX_IDS_PER_PAGE, count - len(ids)),
        )
        if not page:
            break
        ids.extend(page)
        start += len(page)
    return ids[:count]


async def fetch_recent_matches(
    client: RiotClient, region_code: str, puuid: str, count: int = 20
) -> list[dict]:
    """Fetch full match detail for the PUUID's last `count` games.

    Ids are paged, then their detail is fetched concurrently under a semaphore so
    at most `MAX_CONCURRENT_MATCH_REQUESTS` calls are ever in flight — batched for
    speed, capped to respect Riot's rate limit. Each fetch goes through the
    client's per-match cache, so a repeat analysis costs no Riot calls at all.

    A single match that can't be fetched (deleted, or a transient Riot error) is
    skipped rather than sinking the whole analysis — important for players with
    only a handful of games, where one bad match would otherwise erase the lot.
    Results keep the recent-first order of the ids.
    """
    platform = platform_host(region_code)
    cluster = regional_route(platform)

    ids = await recent_match_ids(client, cluster, puuid, count)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_MATCH_REQUESTS)

    async def fetch_one(match_id: str) -> dict | None:
        async with semaphore:
            try:
                return await client.match(cluster, match_id)
            except RiotAPIError as exc:
                logger.warning("Skipping match %s: %s", match_id, exc)
                return None

    results = await asyncio.gather(*(fetch_one(match_id) for match_id in ids))
    return [match for match in results if match is not None]


async def analyse_champion_pool(
    client: RiotClient, region_code: str, puuid: str, count: int = 20, top: int = 5
) -> ChampionPool:
    """Fold a PUUID's recent matches into a champion-pool summary.

    Safe for players with few or no ranked games: an empty history yields an
    empty pool (no games, no champions) rather than an error.
    """
    matches = await fetch_recent_matches(client, region_code, puuid, count)
    stats = aggregate_champion_stats(matches, puuid)
    return ChampionPool(
        total_games=sum(s.games for s in stats),
        champions=stats,
        top=top_champions(stats, limit=top),
    )
