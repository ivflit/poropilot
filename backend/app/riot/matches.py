"""Match-history fetching for champion-pool analysis.

Riot's Match-V5 `by-puuid/ids` endpoint returns at most 100 ids per request, so
fetching the last N matches means paging in batches of 100. Match detail is
cached per match id by the client (a finished game is immutable), so repeat
analysis costs no extra Riot calls.
"""

from .client import RiotClient
from .regions import platform_host, regional_route

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

    Ids are paged; each match is fetched via the client's per-match cache.
    """
    platform = platform_host(region_code)
    cluster = regional_route(platform)

    ids = await recent_match_ids(client, cluster, puuid, count)
    return [await client.match(cluster, match_id) for match_id in ids]
