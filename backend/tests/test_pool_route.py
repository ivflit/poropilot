import unittest
import unittest.mock

import httpx
from fastapi.testclient import TestClient

from app.cache import cache
from app.dependencies import get_riot_client
from app.main import app
from app.riot.client import RiotClient

PUUID = "puuid-1"


SOLO_QUEUE = 420
FLEX_QUEUE = 440
ARAM_QUEUE = 450


def _match(champ_id, champ_name, win, kills, deaths, assists, cs, minutes, queue=SOLO_QUEUE):
    return {
        "info": {
            "queueId": queue,
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
    "M4": _match(64, "LeeSin", True, 12, 3, 7, 180, 22, queue=FLEX_QUEUE),
    "M5": _match(103, "Ahri", True, 20, 8, 20, 90, 15, queue=ARAM_QUEUE),
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
                # Riot narrows by queue at the source, so the stub does too.
                wanted = request.url.params.get("queue")
                all_ids = [
                    mid
                    for mid, m in MATCHES.items()
                    if wanted is None or m["info"]["queueId"] == int(wanted)
                ]
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
        self.assertEqual(body["total_games"], 5)  # every queue
        self.assertEqual(
            {c["champion_name"] for c in body["champions"]}, {"Aatrox", "Ahri", "LeeSin"}
        )
        self.assertGreaterEqual(len(body["top"]), 1)
        self.assertEqual(body["queue"], "all")  # the default filter is echoed back

    def test_repeat_call_makes_no_extra_riot_requests(self):
        client = TestClient(app)
        client.get("/api/pool/EUW/Faker/KR1")
        after_first = len(self.requests)
        client.get("/api/pool/EUW/Faker/KR1")
        self.assertEqual(len(self.requests), after_first)  # everything served from cache

    def test_unknown_region_is_a_400(self):
        resp = TestClient(app).get("/api/pool/MARS/Faker/KR1")
        self.assertEqual(resp.status_code, 400)


class PoolQueueFilterTests(PoolRouteTests):
    """The queue filter, end to end through the route."""

    def test_solo_filter_excludes_flex_and_aram(self):
        body = TestClient(app).get("/api/pool/EUW/Faker/KR1?queue=solo").json()
        self.assertEqual(body["queue"], "solo")
        self.assertEqual(body["total_games"], 3)
        self.assertEqual({c["champion_name"] for c in body["champions"]}, {"Aatrox", "Ahri"})

    def test_flex_filter_returns_only_the_flex_game(self):
        body = TestClient(app).get("/api/pool/EUW/Faker/KR1?queue=flex").json()
        self.assertEqual(body["queue"], "flex")
        self.assertEqual(body["total_games"], 1)
        self.assertEqual([c["champion_name"] for c in body["champions"]], ["LeeSin"])

    def test_aram_game_does_not_inflate_the_solo_winrate(self):
        # Ahri has a 20/8/20 ARAM stomp; it must not touch her ranked numbers.
        solo = TestClient(app).get("/api/pool/EUW/Faker/KR1?queue=solo").json()
        ahri = next(c for c in solo["champions"] if c["champion_name"] == "Ahri")
        self.assertEqual(ahri["games"], 1)
        self.assertEqual(ahri["avg_kda"], 17.0)  # (8+9)/1, not the ARAM game's numbers

    def test_the_filter_is_asked_of_riot_not_applied_afterwards(self):
        TestClient(app).get("/api/pool/EUW/Faker/KR1?queue=solo")
        ids_requests = [p for p in self.requests if p.endswith("/ids")]
        self.assertTrue(ids_requests)
        # A filtered request must never fetch the ARAM match detail at all.
        self.assertNotIn("/lol/match/v5/matches/M5", self.requests)

    def test_switching_filter_does_not_serve_the_previous_filters_numbers(self):
        client = TestClient(app)
        everything = client.get("/api/pool/EUW/Faker/KR1").json()
        solo = client.get("/api/pool/EUW/Faker/KR1?queue=solo").json()
        self.assertNotEqual(everything["total_games"], solo["total_games"])

    def test_switching_back_reuses_cached_match_detail(self):
        client = TestClient(app)
        client.get("/api/pool/EUW/Faker/KR1")
        client.get("/api/pool/EUW/Faker/KR1?queue=solo")
        before = len(self.requests)
        client.get("/api/pool/EUW/Faker/KR1?queue=solo")
        self.assertEqual(len(self.requests), before)  # nothing re-fetched

    def test_a_queue_with_no_games_is_an_empty_pool_not_an_error(self):
        MATCHES_WITHOUT_FLEX = {k: v for k, v in MATCHES.items() if k != "M4"}
        with unittest.mock.patch.dict(MATCHES, MATCHES_WITHOUT_FLEX, clear=True):
            body = TestClient(app).get("/api/pool/EUW/Faker/KR1?queue=flex").json()
        self.assertEqual(body["total_games"], 0)
        self.assertEqual(body["champions"], [])
        self.assertEqual(body["top"], [])

    def test_an_unknown_queue_is_a_422(self):
        resp = TestClient(app).get("/api/pool/EUW/Faker/KR1?queue=aram")
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
