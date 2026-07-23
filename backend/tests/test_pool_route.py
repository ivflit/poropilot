import unittest

import httpx
from fastapi.testclient import TestClient

from app.cache import cache
from app.dependencies import get_riot_client
from app.main import app
from app.riot.client import RiotClient

PUUID = "puuid-1"


def _match(champ_id, champ_name, win, kills, deaths, assists, cs, minutes):
    return {
        "info": {
            "gameDuration": int(minutes * 60),
            "participants": [
                {
                    "puuid": PUUID,
                    "championId": champ_id,
                    "championName": champ_name,
                    "win": win,
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "totalMinionsKilled": cs,
                    "neutralMinionsKilled": 0,
                },
                {"puuid": "other", "championId": 1, "championName": "Annie", "win": not win},
            ],
        }
    }


MATCHES = {
    "M1": _match(266, "Aatrox", True, 10, 2, 5, 200, 25),
    "M2": _match(266, "Aatrox", False, 3, 6, 4, 150, 30),
    "M3": _match(103, "Ahri", True, 8, 1, 9, 220, 28),
}


class PoolRouteTests(unittest.TestCase):
    def setUp(self):
        cache._store.clear()
        self.requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            self.requests.append(path)
            if "/riot/account/v1/accounts/by-riot-id/" in path:
                return httpx.Response(200, json={"puuid": PUUID, "gameName": "Faker", "tagLine": "KR1"})
            if path.endswith("/ids"):
                start = int(request.url.params.get("start", 0))
                count = int(request.url.params.get("count", 20))
                all_ids = list(MATCHES.keys())
                return httpx.Response(200, json=all_ids[start : start + count])
            if "/lol/match/v5/matches/" in path:
                return httpx.Response(200, json=MATCHES[path.rsplit("/", 1)[-1]])
            return httpx.Response(404, json={"status": {"message": "not found"}})

        self.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        app.dependency_overrides[get_riot_client] = lambda: RiotClient(self.http, api_key="test")

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_pool_returns_aggregated_champions(self):
        resp = TestClient(app).get("/api/pool/EUW/Faker/KR1")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["total_games"], 3)
        self.assertEqual({c["champion_name"] for c in body["champions"]}, {"Aatrox", "Ahri"})
        self.assertGreaterEqual(len(body["top"]), 1)

    def test_repeat_call_makes_no_extra_riot_requests(self):
        client = TestClient(app)
        client.get("/api/pool/EUW/Faker/KR1")
        after_first = len(self.requests)
        client.get("/api/pool/EUW/Faker/KR1")
        self.assertEqual(len(self.requests), after_first)  # everything served from cache

    def test_unknown_region_is_a_400(self):
        resp = TestClient(app).get("/api/pool/MARS/Faker/KR1")
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
