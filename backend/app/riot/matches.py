"""Match-history fetching for champion-pool analysis.

Riot's Match-V5 `by-puuid/ids` endpoint returns at most 100 ids per request, so
fetching the last N matches means paging in batches of 100. Match detail is
cached per match id by the client (a finished game is immutable), so repeat
analysis costs no extra Riot calls.
"""

import logging

from ..schemas import ChampionPool
from .analysis import aggregate_champion_stats, top_champions
from .client import RiotAPIError, RiotClient
from .regions import platform_host, regional_route

logger = logging.getLogger(__name__)

RIOT_MAX_IDS_PER_PAGE = 100


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

    Ids are paged; each match is fetched via the client's per-match cache. A
    single match that can't be fetched (deleted, or a transient Riot error) is
    skipped rather than sinking the whole analysis — important for players with
    only a handful of games, where one bad match would otherwise erase the lot.
    """
    platform = platform_host(region_code)
    cluster = regional_route(platform)

    ids = await recent_match_ids(client, cluster, puuid, count)
    matches: list[dict] = []
    for match_id in ids:
        try:
            matches.append(await client.match(cluster, match_id))
        except RiotAPIError as exc:
            logger.warning("Skipping match %s: %s", match_id, exc)
    return matches


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
