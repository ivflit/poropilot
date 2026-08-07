"""Tests for GET /api/live/{region}/{name}/{tag}."""

import unittest

import httpx
from fastapi.testclient import TestClient

from app.cache import cache
from app.dependencies import get_champion_map, get_riot_client
from app.main import app
from app.riot.client import RiotClient
from app.schemas import Champion

PUUID = "puuid-1"

CHAMPIONS = {
    103: Champion(champion_id=103, name="Ahri", title="Fox", image_url="http://x/Ahri.png"),
    238: Champion(champion_id=238, name="Zed", title="Shadow", image_url="http://x/Zed.png"),
}

ACTIVE_GAME = {
    "gameMode": "CLASSIC",
    "gameLength": 300,
    "participants": [
        {"puuid": PUUID, "championId": 103, "teamId": 100, "riotId": "Player#TAG"},
        {"puuid": "puuid-2", "championId": 238, "teamId": 200, "riotId": "Enemy#TAG"},
    ],
}


class LiveGameTests(unittest.TestCase):
    def setUp(self):
        cache._store.clear()
        self._in_game = True

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if "/riot/account/v1/accounts/by-riot-id/" in path:
                return httpx.Response(200, json={"puuid": PUUID, "gameName": "Player", "tagLine": "TAG"})
            if "/lol/spectator/v5/active-games/" in path:
                if self._in_game:
                    return httpx.Response(200, json=ACTIVE_GAME)
                return httpx.Response(404, json={"status": {"message": "not in game"}})
            if "/lol/league/v4/entries/" in path:
                return httpx.Response(200, json=[{
                    "queueType": "RANKED_SOLO_5x5", "tier": "GOLD", "rank": "I",
                    "leaguePoints": 50, "wins": 30, "losses": 20,
                }])
            return httpx.Response(404, json={"status": {"message": "not found"}})

        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        app.dependency_overrides[get_riot_client] = lambda: RiotClient(http, api_key="test")
        app.dependency_overrides[get_champion_map] = lambda: CHAMPIONS

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_returns_game_data_when_in_game(self):
        r = TestClient(app).get("/api/live/EUW/Player/TAG")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["in_game"])
        self.assertEqual(data["game_mode"], "CLASSIC")
        self.assertEqual(len(data["participants"]), 2)
        self.assertEqual(data["participants"][0]["champion_name"], "Ahri")
        self.assertEqual(data["participants"][0]["riot_id"], "Player#TAG")

    def test_returns_rank_for_participants(self):
        r = TestClient(app).get("/api/live/EUW/Player/TAG")
        data = r.json()
        self.assertIn("GOLD", data["participants"][0]["rank"])

    def test_not_in_game_returns_false(self):
        self._in_game = False
        r = TestClient(app).get("/api/live/EUW/Player/TAG")
        data = r.json()
        self.assertFalse(data["in_game"])
        self.assertEqual(data["participants"], [])

    def test_unknown_region_returns_400(self):
        r = TestClient(app).get("/api/live/MARS/Player/TAG")
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
