"""Queue filtering — ranked solo/duo, ranked flex, or everything.

Lumping every game together lets ARAM and normals pollute the ranked numbers, so
the champion pool and win-rates can be narrowed to a single ranked queue.

Riot identifies a queue by a numeric id on `info.queueId`, and Match-V5's ids
endpoint also accepts a `queue` parameter — so a filtered search is narrowed at
the source rather than fetched and thrown away. We still re-check `queueId` on
the fetched matches: it costs nothing, keeps the aggregation honest if Riot ever
ignores the parameter, and makes the filter a pure function we can test directly.
"""

from collections.abc import Iterable
from enum import StrEnum


class MatchQueue(StrEnum):
    """The queue filters the API offers. Values double as the query-string values,
    so FastAPI validates them for us and rejects anything else with a 422."""

    ALL = "all"
    SOLO = "solo"
    FLEX = "flex"


# Riot's numeric queue ids — https://static.developer.riotgames.com/docs/lol/queues.json
QUEUE_IDS: dict[MatchQueue, int] = {
    MatchQueue.SOLO: 420,  # 5v5 Ranked Solo/Duo
    MatchQueue.FLEX: 440,  # 5v5 Ranked Flex
}

# The matching League-V4 `queueType`, so a filtered view can show the right rank.
QUEUE_TYPES: dict[MatchQueue, str] = {
    MatchQueue.SOLO: "RANKED_SOLO_5x5",
    MatchQueue.FLEX: "RANKED_FLEX_SR",
}


def queue_id(queue: MatchQueue) -> int | None:
    """The Riot queue id to filter on, or None for "all queues" (no filtering)."""
    return QUEUE_IDS.get(queue)


def in_queue(match: dict, queue: MatchQueue) -> bool:
    """Whether a Match-V5 match belongs to the requested queue."""
    wanted = queue_id(queue)
    if wanted is None:
        return True
    return match.get("info", {}).get("queueId") == wanted


def filter_by_queue(matches: Iterable[dict], queue: MatchQueue) -> list[dict]:
    """Keep only the matches in the requested queue, preserving order."""
    if queue_id(queue) is None:
        return list(matches)
    return [match for match in matches if in_queue(match, queue)]
