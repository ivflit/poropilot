import unittest

import httpx

from app.cache import cache
from app.riot.client import RiotClient
from app.riot.matches import fetch_recent_matches, recent_match_ids


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
