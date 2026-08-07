"""Tests for POST /api/multi-search."""

import unittest

import httpx
from fastapi.testclient import TestClient

from app.cache import cache
from app.dependencies import get_riot_client
from app.main import app
from app.riot.client import RiotClient

PUUID_MAP = {
    "Player1#TAG": "puuid-1",
    "Player2#TAG": "puuid-2",
}


class MultiSearchRouteTests(unittest.TestCase):
    def setUp(self):
        cache._store.clear()

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if "/riot/account/v1/accounts/by-riot-id/" in path:
                parts = path.rstrip("/").split("/")
                name, tag = parts[-2], parts[-1]
                key = f"{name}#{tag}"
                if key in PUUID_MAP:
                    return httpx.Response(200, json={
                        "puuid": PUUID_MAP[key], "gameName": name, "tagLine": tag,
                    })
                return httpx.Response(404, json={"status": {"message": "not found"}})
            if "/lol/summoner/v4/summoners/by-puuid/" in path:
                return httpx.Response(200, json={"summonerLevel": 200, "profileIconId": 1})
            if "/lol/league/v4/entries/by-puuid/" in path:
                return httpx.Response(200, json=[
                    {"queueType": "RANKED_SOLO_5x5", "tier": "GOLD", "rank": "I",
                     "leaguePoints": 50, "wins": 30, "losses": 20},
                ])
            if path.endswith("/ids"):
                return httpx.Response(200, json=["M1"])
            if "/lol/match/v5/matches/" in path:
                return httpx.Response(200, json={
                    "metadata": {"matchId": "M1"},
                    "info": {
                        "gameDuration": 1800, "queueId": 420,
                        "participants": [{
                            "puuid": "puuid-1", "championId": 103, "championName": "Ahri",
                            "win": True, "kills": 5, "deaths": 2, "assists": 8,
                            "totalMinionsKilled": 150, "neutralMinionsKilled": 0,
                        }],
                    },
                })
            return httpx.Response(404, json={"status": {"message": "not found"}})

        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        app.dependency_overrides[get_riot_client] = lambda: RiotClient(http, api_key="test")

    def tearDown(self):
        app.dependency_overrides.clear()

    def _post(self, region, riot_ids):
        return TestClient(app).post("/api/multi-search", json={
            "region": region, "riot_ids": riot_ids,
        })

    def test_returns_found_players(self):
        r = self._post("EUW", ["Player1#TAG"])
        self.assertEqual(r.status_code, 200)
        players = r.json()["players"]
        self.assertEqual(len(players), 1)
        self.assertTrue(players[0]["found"])
        self.assertEqual(players[0]["riot_id"], "Player1#TAG")
        self.assertEqual(players[0]["level"], 200)
        self.assertTrue(len(players[0]["ranked"]) > 0)

    def test_not_found_players_marked_as_such(self):
        r = self._post("EUW", ["Unknown#999"])
        players = r.json()["players"]
        self.assertEqual(len(players), 1)
        self.assertFalse(players[0]["found"])

    def test_mixed_found_and_not_found(self):
        r = self._post("EUW", ["Player1#TAG", "Unknown#999"])
        players = r.json()["players"]
        self.assertEqual(len(players), 2)
        self.assertTrue(players[0]["found"])
        self.assertFalse(players[1]["found"])

    def test_invalid_riot_id_without_hash(self):
        r = self._post("EUW", ["nohash"])
        players = r.json()["players"]
        self.assertFalse(players[0]["found"])

    def test_capped_at_five_players(self):
        ids = [f"Player{i}#TAG" for i in range(10)]
        r = self._post("EUW", ids)
        players = r.json()["players"]
        self.assertEqual(len(players), 5)

    def test_unknown_region_returns_400(self):
        r = self._post("MARS", ["Player1#TAG"])
        self.assertEqual(r.status_code, 400)

    def test_top_champions_included(self):
        r = self._post("EUW", ["Player1#TAG"])
        player = r.json()["players"][0]
        self.assertIn("top_champions", player)


if __name__ == "__main__":
    unittest.main()
