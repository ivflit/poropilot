import unittest

import httpx
from fastapi.testclient import TestClient

from app.cache import cache
from app.dependencies import get_riot_client
from app.main import app
from app.riot.client import RiotClient

PUUID = "puuid-1"


class ProfileRouteTests(unittest.TestCase):
    def setUp(self):
        cache._store.clear()

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if "/riot/account/v1/accounts/by-riot-id/" in path:
                return httpx.Response(200, json={"puuid": PUUID, "gameName": "PilotSheep", "tagLine": "EUW"})
            if "/lol/summoner/v4/summoners/by-puuid/" in path:
                # Summoner-V4 no longer returns an encrypted `id` — this is the regression guard.
                return httpx.Response(200, json={"profileIconId": 773, "summonerLevel": 128})
            if "/lol/league/v4/entries/by-puuid/" in path:
                return httpx.Response(
                    200,
                    json=[
                        {
                            "queueType": "RANKED_SOLO_5x5",
                            "tier": "GOLD",
                            "rank": "II",
                            "leaguePoints": 6,
                            "wins": 73,
                            "losses": 60,
                        }
                    ],
                )
            if "/lol/champion-mastery/v4/champion-masteries/by-puuid/" in path:
                return httpx.Response(
                    200, json=[{"championId": 134, "championPoints": 246443, "championLevel": 25}]
                )
            return httpx.Response(404, json={"status": {"message": "not found"}})

        self.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        app.dependency_overrides[get_riot_client] = lambda: RiotClient(self.http, api_key="test")

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_profile_loads_without_a_summoner_id(self):
        resp = TestClient(app).get("/api/summoner/EUW/PilotSheep/EUW")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["riot_id"], "PilotSheep#EUW")
        self.assertEqual(body["level"], 128)
        self.assertEqual(body["ranked"][0]["tier"], "GOLD")
        self.assertEqual(body["top_masteries"][0]["champion_id"], 134)


if __name__ == "__main__":
    unittest.main()
