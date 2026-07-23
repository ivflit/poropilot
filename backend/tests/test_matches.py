import asyncio
import unittest

import httpx

from app.cache import cache
from app.riot.client import RiotAPIError, RiotClient
from app.riot.matches import (
    MAX_CONCURRENT_MATCH_REQUESTS,
    analyse_champion_pool,
    fetch_recent_matches,
    recent_match_ids,
)


class FakePagingClient:
    """Stands in for RiotClient, serving match ids from an in-memory list."""

    def __init__(self, total: int) -> None:
        self.all_ids = [f"M{i}" for i in range(total)]
        self.pages: list[tuple[int, int]] = []
        self.fetched: list[str] = []

    async def match_ids(self, cluster, puuid, start=0, count=20):
        self.pages.append((start, count))
        return self.all_ids[start : start + count]

    async def match(self, cluster, match_id):
        self.fetched.append(match_id)
        return {"id": match_id}


def _match(match_id, puuid, champion_id, win, duration=1200):
    """A minimal Match-V5 detail keyed by id, with our PUUID as a participant."""
    return {
        "metadata": {"matchId": match_id},
        "info": {
            "gameDuration": duration,
            "participants": [
                {
                    "puuid": puuid,
                    "championId": champion_id,
                    "championName": f"C{champion_id}",
                    "win": win,
                    "kills": 5,
                    "deaths": 2,
                    "assists": 5,
                    "totalMinionsKilled": 100,
                    "neutralMinionsKilled": 0,
                }
            ],
        },
    }


class FakeMatchClient:
    """Serves match detail from a dict; an Exception value is raised on fetch."""

    def __init__(self, matches_by_id: dict) -> None:
        self.matches_by_id = matches_by_id

    async def match_ids(self, cluster, puuid, start=0, count=20):
        return list(self.matches_by_id)[start : start + count]

    async def match(self, cluster, match_id):
        detail = self.matches_by_id[match_id]
        if isinstance(detail, Exception):
            raise detail
        return detail


class RecentMatchIdsTests(unittest.IsolatedAsyncioTestCase):
    async def test_pages_in_batches_of_100(self):
        client = FakePagingClient(total=500)
        ids = await recent_match_ids(client, "europe", "puuid", 250)
        self.assertEqual(len(ids), 250)
        self.assertEqual(ids[0], "M0")
        self.assertEqual(client.pages, [(0, 100), (100, 100), (200, 50)])

    async def test_stops_when_history_shorter_than_requested(self):
        client = FakePagingClient(total=30)
        ids = await recent_match_ids(client, "europe", "puuid", 250)
        self.assertEqual(ids, [f"M{i}" for i in range(30)])

    async def test_zero_count_makes_no_calls(self):
        client = FakePagingClient(total=50)
        ids = await recent_match_ids(client, "europe", "puuid", 0)
        self.assertEqual(ids, [])
        self.assertEqual(client.pages, [])


class FetchRecentMatchesTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_detail_for_each_id(self):
        client = FakePagingClient(total=5)
        matches = await fetch_recent_matches(client, "EUW", "puuid", count=3)
        self.assertEqual(matches, [{"id": "M0"}, {"id": "M1"}, {"id": "M2"}])
        self.assertEqual(client.fetched, ["M0", "M1", "M2"])


class FetchResilienceTests(unittest.IsolatedAsyncioTestCase):
    async def test_skips_a_match_that_fails_to_fetch(self):
        # A player with only three games, one of which Riot can't serve.
        client = FakeMatchClient(
            {
                "M0": _match("M0", "puuid", 157, True),
                "M1": RiotAPIError(404, "match not found"),
                "M2": _match("M2", "puuid", 238, True),
            }
        )
        matches = await fetch_recent_matches(client, "EUW", "puuid", count=3)
        self.assertEqual([m["metadata"]["matchId"] for m in matches], ["M0", "M2"])


class ConcurrencyTrackingClient:
    """Records the peak number of match fetches in flight at once."""

    def __init__(self, total: int) -> None:
        self.all_ids = [f"M{i}" for i in range(total)]
        self.in_flight = 0
        self.peak_in_flight = 0

    async def match_ids(self, cluster, puuid, start=0, count=20):
        return self.all_ids[start : start + count]

    async def match(self, cluster, match_id):
        self.in_flight += 1
        self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        await asyncio.sleep(0)  # yield so concurrent fetches pile up
        self.in_flight -= 1
        return {"id": match_id}


class RateLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_in_flight_fetches_are_capped(self):
        # More matches than the cap, so an uncapped fetch would burst past it.
        total = MAX_CONCURRENT_MATCH_REQUESTS * 3
        client = ConcurrencyTrackingClient(total=total)
        matches = await fetch_recent_matches(client, "EUW", "puuid", count=total)
        self.assertEqual(len(matches), total)
        self.assertEqual(client.peak_in_flight, MAX_CONCURRENT_MATCH_REQUESTS)

    async def test_fetches_are_batched_not_serial(self):
        client = ConcurrencyTrackingClient(total=5)
        await fetch_recent_matches(client, "EUW", "puuid", count=5)
        # Fewer matches than the cap: all five run concurrently, not one-by-one.
        self.assertEqual(client.peak_in_flight, 5)


class AnalyseChampionPoolTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_games_yields_an_empty_pool_not_an_error(self):
        pool = await analyse_champion_pool(FakePagingClient(total=0), "EUW", "puuid")
        self.assertEqual(pool.total_games, 0)
        self.assertEqual(pool.champions, [])
        self.assertEqual(pool.top, [])

    async def test_few_games_aggregate_without_erroring(self):
        client = FakeMatchClient(
            {
                "M0": _match("M0", "puuid", 157, True),
                "M1": _match("M1", "puuid", 157, False),
            }
        )
        pool = await analyse_champion_pool(client, "EUW", "puuid", count=2)
        self.assertEqual(pool.total_games, 2)
        self.assertEqual(len(pool.champions), 1)
        self.assertEqual(pool.champions[0].champion_id, 157)
        self.assertEqual(pool.top[0].champion_id, 157)

    async def test_pool_survives_a_player_whose_only_game_fails_to_fetch(self):
        client = FakeMatchClient({"M0": RiotAPIError(503, "service unavailable")})
        pool = await analyse_champion_pool(client, "EUW", "puuid", count=1)
        self.assertEqual(pool.total_games, 0)
        self.assertEqual(pool.champions, [])


class MatchDetailCachingTests(unittest.IsolatedAsyncioTestCase):
    async def test_match_detail_cached_per_id(self):
        cache._store.clear()
        calls = {"count": 0}

        def handler(request):
            calls["count"] += 1
            return httpx.Response(200, json={"metadata": {"matchId": "M1"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http:
            client = RiotClient(http, api_key="test")
            first = await client.match("europe", "M1")
            second = await client.match("europe", "M1")

        self.assertEqual(first, second)
        self.assertEqual(calls["count"], 1)  # second read served from cache


if __name__ == "__main__":
    unittest.main()
