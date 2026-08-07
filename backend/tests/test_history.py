"""Tests for the match history detail extraction and the /api/history/ route."""

import unittest

import httpx
from fastapi.testclient import TestClient

from app.cache import cache
from app.dependencies import get_riot_client
from app.main import app
from app.riot.client import RiotClient
from app.riot.history import build_match_detail, compute_aggregate

PUUID = "player-1"
SOLO_QUEUE = 420


def _participant(puuid, champion, team, role, win, **kw):
    return {
        "puuid": puuid,
        "championName": champion,
        "teamId": team,
        "teamPosition": role,
        "individualPosition": role,
        "win": win,
        "kills": kw.get("kills", 3),
        "deaths": kw.get("deaths", 2),
        "assists": kw.get("assists", 7),
        "totalMinionsKilled": kw.get("cs", 150),
        "neutralMinionsKilled": kw.get("jungle_cs", 10),
        "totalDamageDealtToChampions": kw.get("damage", 18000),
        "goldEarned": kw.get("gold", 12000),
        "visionScore": kw.get("vision", 25),
    }


def _match(match_id, champion="Ahri", role="MIDDLE", win=True, opponent="Zed",
           start_ts=1700000000000, duration=1800, queue_id=SOLO_QUEUE, **kw):
    return {
        "metadata": {"matchId": match_id},
        "info": {
            "gameDuration": duration,
            "queueId": queue_id,
            "gameStartTimestamp": start_ts,
            "participants": [
                _participant(PUUID, champion, 100, role, win, **kw),
                _participant("enemy-1", opponent, 200, role, not win),
                _participant("ally-2", "Ally2", 100, "TOP", win),
                _participant("ally-3", "Ally3", 100, "JUNGLE", win),
                _participant("ally-4", "Ally4", 100, "BOTTOM", win),
                _participant("enemy-2", "Enemy2", 200, "TOP", not win),
                _participant("enemy-3", "Enemy3", 200, "JUNGLE", not win),
                _participant("enemy-4", "Enemy4", 200, "BOTTOM", not win),
            ],
        },
    }


# --- Unit tests for build_match_detail ---

class BuildMatchDetailTests(unittest.TestCase):
    def test_extracts_basic_fields(self):
        m = _match("M1", champion="Ahri", win=True)
        d = build_match_detail(m, PUUID)
        self.assertIsNotNone(d)
        self.assertEqual(d.match_id, "M1")
        self.assertEqual(d.champion, "Ahri")
        self.assertTrue(d.win)
        self.assertEqual(d.kills, 3)
        self.assertEqual(d.deaths, 2)
        self.assertEqual(d.assists, 7)

    def test_cs_and_cs_per_min(self):
        m = _match("M1", cs=150, jungle_cs=30, duration=1800)
        d = build_match_detail(m, PUUID)
        self.assertEqual(d.cs, 180)
        self.assertAlmostEqual(d.cs_per_min, 6.0, places=1)

    def test_damage_per_min(self):
        m = _match("M1", damage=18000, duration=1800)
        d = build_match_detail(m, PUUID)
        self.assertEqual(d.damage, 18000)
        self.assertAlmostEqual(d.damage_per_min, 600, places=0)

    def test_opponent_detection(self):
        m = _match("M1", role="MIDDLE", opponent="Zed")
        d = build_match_detail(m, PUUID)
        self.assertEqual(d.opponent_champion, "Zed")

    def test_role_extracted(self):
        m = _match("M1", role="BOTTOM")
        d = build_match_detail(m, PUUID)
        self.assertEqual(d.role, "BOTTOM")

    def test_participants_list(self):
        m = _match("M1")
        d = build_match_detail(m, PUUID)
        self.assertEqual(len(d.participants), 8)
        champs = [p.champion for p in d.participants]
        self.assertIn("Ahri", champs)

    def test_participants_have_stats(self):
        m = _match("M1")
        d = build_match_detail(m, PUUID)
        p = d.participants[0]
        self.assertEqual(p.kills, 3)
        self.assertEqual(p.deaths, 2)
        self.assertEqual(p.assists, 7)
        self.assertEqual(p.cs, 160)  # 150 + 10
        self.assertEqual(p.damage, 18000)
        self.assertEqual(p.gold, 12000)

    def test_returns_none_for_missing_puuid(self):
        m = _match("M1")
        self.assertIsNone(build_match_detail(m, "not-in-match"))

    def test_game_start_epoch(self):
        m = _match("M1", start_ts=1700000000000)
        d = build_match_detail(m, PUUID)
        self.assertEqual(d.game_start, 1700000000)

    def test_zero_duration_no_division_error(self):
        m = _match("M1", duration=0)
        d = build_match_detail(m, PUUID)
        self.assertEqual(d.cs_per_min, 0)
        self.assertEqual(d.damage_per_min, 0)


# --- Route tests using httpx.MockTransport (same pattern as test_pool_route) ---

MATCHES = {
    "M1": _match("M1", "Ahri", "MIDDLE", True, "Zed", 1700000003000, 1800,
                  cs=200, jungle_cs=0, damage=20000),
    "M2": _match("M2", "Jinx", "BOTTOM", False, "Kaisa", 1700000002000, 2100,
                  cs=250, jungle_cs=0, damage=25000),
    "M3": _match("M3", "LeeSin", "JUNGLE", True, "Elise", 1700000001000, 1500,
                  cs=50, jungle_cs=120, damage=15000),
}


class HistoryRouteTests(unittest.TestCase):
    def setUp(self):
        cache._store.clear()

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if "/riot/account/v1/accounts/by-riot-id/" in path:
                return httpx.Response(200, json={"puuid": PUUID, "gameName": "Player", "tagLine": "TAG"})
            if path.endswith("/ids"):
                start = int(request.url.params.get("start", 0))
                count = int(request.url.params.get("count", 20))
                ids = list(MATCHES.keys())[start:start + count]
                return httpx.Response(200, json=ids)
            if "/lol/match/v5/matches/" in path:
                mid = path.rsplit("/", 1)[-1]
                if mid in MATCHES:
                    return httpx.Response(200, json=MATCHES[mid])
                return httpx.Response(404, json={"status": {"message": "not found"}})
            return httpx.Response(404, json={"status": {"message": "not found"}})

        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        app.dependency_overrides[get_riot_client] = lambda: RiotClient(http, api_key="test")

    def tearDown(self):
        app.dependency_overrides.clear()

    def _get(self, **params):
        return TestClient(app).get("/api/history/EUW/Player/TAG", params=params)

    def test_returns_all_matches(self):
        r = self._get()
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data["matches"]), 3)

    def test_match_has_rich_fields(self):
        r = self._get()
        m = r.json()["matches"][0]
        for field in ("cs_per_min", "damage_per_min", "opponent_champion",
                      "participants", "game_start", "role", "cs", "damage",
                      "gold", "vision_score"):
            self.assertIn(field, m, f"Missing field: {field}")

    def test_filter_by_role(self):
        r = self._get(role="JUNGLE")
        matches = r.json()["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["champion"], "LeeSin")

    def test_filter_by_result_win(self):
        r = self._get(result="win")
        matches = r.json()["matches"]
        self.assertTrue(all(m["win"] for m in matches))
        self.assertEqual(len(matches), 2)

    def test_filter_by_result_loss(self):
        r = self._get(result="loss")
        matches = r.json()["matches"]
        self.assertEqual(len(matches), 1)
        self.assertFalse(matches[0]["win"])

    def test_sort_oldest(self):
        r = self._get(sort="oldest")
        matches = r.json()["matches"]
        timestamps = [m["game_start"] for m in matches]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_sort_cs_min(self):
        r = self._get(sort="cs_min")
        matches = r.json()["matches"]
        cs_mins = [m["cs_per_min"] for m in matches]
        self.assertEqual(cs_mins, sorted(cs_mins, reverse=True))

    def test_sort_dmg_min(self):
        r = self._get(sort="dmg_min")
        matches = r.json()["matches"]
        dpms = [m["damage_per_min"] for m in matches]
        self.assertEqual(dpms, sorted(dpms, reverse=True))

    def test_pagination_start_and_count(self):
        r = self._get(count=1, start=1)
        matches = r.json()["matches"]
        self.assertEqual(len(matches), 1)

    def test_invalid_role_returns_422(self):
        r = self._get(role="INVALID")
        self.assertEqual(r.status_code, 422)

    def test_invalid_result_returns_422(self):
        r = self._get(result="draw")
        self.assertEqual(r.status_code, 422)

    def test_total_fetched_reflects_post_filter_count(self):
        r = self._get(role="JUNGLE")
        data = r.json()
        self.assertEqual(data["total_fetched"], 1)

    def test_aggregate_stats_included(self):
        r = self._get()
        agg = r.json()["aggregate"]
        self.assertEqual(agg["wins"], 2)
        self.assertEqual(agg["losses"], 1)
        self.assertAlmostEqual(agg["win_rate"], 0.6667, places=3)

    def test_aggregate_kda_ratio(self):
        r = self._get()
        agg = r.json()["aggregate"]
        # Total: kills=3+3+3=9, deaths=2+2+2=6, assists=7+7+7=21
        # KDA = (9+21)/6 = 5.0
        self.assertEqual(agg["kda_ratio"], 5.0)

    def test_aggregate_reflects_filters(self):
        r = self._get(result="win")
        agg = r.json()["aggregate"]
        self.assertEqual(agg["wins"], 2)
        self.assertEqual(agg["losses"], 0)
        self.assertEqual(agg["win_rate"], 1.0)


class ComputeAggregateTests(unittest.TestCase):
    def test_empty_list(self):
        agg = compute_aggregate([])
        self.assertEqual(agg.wins, 0)
        self.assertEqual(agg.losses, 0)
        self.assertEqual(agg.kda_ratio, 0)

    def test_single_match(self):
        m = _match("M1", kills=10, deaths=2, assists=5)
        d = build_match_detail(m, PUUID)
        agg = compute_aggregate([d])
        self.assertEqual(agg.wins, 1)
        self.assertEqual(agg.losses, 0)
        self.assertEqual(agg.avg_kills, 10)
        self.assertEqual(agg.kda_ratio, 7.5)  # (10+5)/2

    def test_zero_deaths(self):
        m = _match("M1", kills=5, deaths=0, assists=3)
        d = build_match_detail(m, PUUID)
        agg = compute_aggregate([d])
        self.assertEqual(agg.kda_ratio, 8.0)  # (5+3)/1 (floored)


if __name__ == "__main__":
    unittest.main()
