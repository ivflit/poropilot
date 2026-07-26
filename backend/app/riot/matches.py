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

from app.riot.analysis import aggregate_champion_stats, top_champions
from app.riot.client import RiotAPIError, RiotClient
from app.riot.queues import MatchQueue, filter_by_queue, queue_id
from app.riot.regions import platform_host, regional_route
from app.schemas import ChampionPool

logger = logging.getLogger(__name__)

RIOT_MAX_IDS_PER_PAGE = 100
MAX_CONCURRENT_MATCH_REQUESTS = 10  # cap in-flight match fetches under the ~20 req/s dev limit


async def recent_match_ids(
    client: RiotClient,
    cluster: str,
    puuid: str,
    count: int,
    queue: MatchQueue = MatchQueue.ALL,
) -> list[str]:
    """The most recent `count` match ids for a PUUID, paged in batches of 100.

    A queue filter is passed to Riot rather than applied afterwards, so a
    solo-only request returns `count` solo games instead of `count` games of
    which a few happen to be solo.
    """
    if count <= 0:
        return []

    riot_queue = queue_id(queue)
    ids: list[str] = []
    start = 0
    while len(ids) < count:
        page = await client.match_ids(
            cluster,
            puuid,
            start=start,
            count=min(RIOT_MAX_IDS_PER_PAGE, count - len(ids)),
            queue=riot_queue,
        )
        if not page:
            break
        ids.extend(page)
        start += len(page)
    return ids[:count]


async def fetch_recent_matches(
    client: RiotClient,
    region_code: str,
    puuid: str,
    count: int = 20,
    queue: MatchQueue = MatchQueue.ALL,
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

    ids = await recent_match_ids(client, cluster, puuid, count, queue=queue)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_MATCH_REQUESTS)

    async def fetch_one(match_id: str) -> dict | None:
        async with semaphore:
            try:
                return await client.match(cluster, match_id)
            except RiotAPIError as exc:
                logger.warning("Skipping match %s: %s", match_id, exc)
                return None

    results = await asyncio.gather(*(fetch_one(match_id) for match_id in ids))
    # Riot already narrowed the ids by queue; re-checking `queueId` costs nothing
    # and keeps a stray match out of the aggregation.
    return filter_by_queue((match for match in results if match is not None), queue)


async def analyse_champion_pool(
    client: RiotClient,
    region_code: str,
    puuid: str,
    count: int = 20,
    top: int = 5,
    queue: MatchQueue = MatchQueue.ALL,
) -> ChampionPool:
    """Fold a PUUID's recent matches into a champion-pool summary.

    Safe for players with few or no ranked games: an empty history yields an
    empty pool (no games, no champions) rather than an error — which is the
    normal case for a filter the player has never queued for.
    """
    matches = await fetch_recent_matches(client, region_code, puuid, count, queue=queue)
    stats = aggregate_champion_stats(matches, puuid)
    return ChampionPool(
        queue=queue,
        total_games=sum(s.games for s in stats),
        champions=stats,
        top=top_champions(stats, limit=top),
    )


async def load_pool_for_riot_id(
    client: RiotClient,
    region_code: str,
    name: str,
    tag: str,
    count: int = 20,
    top: int = 5,
    queue: MatchQueue = MatchQueue.ALL,
) -> ChampionPool:
    """Resolve a Riot ID to a PUUID, then summarise its recent champion pool.

    Match ids and detail are cached by the client, so a repeat call within the
    cache TTL costs no extra Riot requests.
    """
    cluster = regional_route(platform_host(region_code))
    account = await client.account_by_riot_id(cluster, name, tag)
    return await analyse_champion_pool(
        client, region_code, account["puuid"], count=count, top=top, queue=queue
    )
