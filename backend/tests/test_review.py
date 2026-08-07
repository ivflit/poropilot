"""Tests for the post-game review — stat derivation and response shape."""

import unittest

from app.ai.review import _format_stats, derive_stats, is_ranked


def _match(queue_id=420, duration=1800, participants=None):
    """Build a minimal Match-V5 fixture."""
    return {
        "info": {
            "queueId": queue_id,
            "gameDuration": duration,
            "participants": participants or [],
        }
    }


def _player(
    puuid="me",
    champion="Ahri",
    team=100,
    position="MIDDLE",
    win=True,
    kills=5,
    deaths=3,
    assists=7,
    cs=180,
    neutral_cs=20,
    damage=18000,
    gold=12000,
    vision=25,
):
    return {
        "puuid": puuid,
        "championName": champion,
        "teamId": team,
        "individualPosition": position,
        "win": win,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "totalMinionsKilled": cs,
        "neutralMinionsKilled": neutral_cs,
        "totalDamageDealtToChampions": damage,
        "goldEarned": gold,
        "visionScore": vision,
    }


def _opponent(
    puuid="opp",
    champion="Zed",
    team=200,
    position="MIDDLE",
    kills=2,
    deaths=4,
    cs=150,
    neutral_cs=10,
    damage=14000,
    gold=10000,
):
    return _player(
        puuid=puuid,
        champion=champion,
        team=team,
        position=position,
        win=False,
        kills=kills,
        deaths=deaths,
        assists=3,
        cs=cs,
        neutral_cs=neutral_cs,
        damage=damage,
        gold=gold,
        vision=15,
    )


FIXTURE_MATCH = _match(
    queue_id=420,
    duration=1800,  # 30 minutes
    participants=[_player(), _opponent()],
)


class TestIsRanked(unittest.TestCase):
    def test_solo_is_ranked(self):
        self.assertTrue(is_ranked(_match(queue_id=420)))

    def test_flex_is_ranked(self):
        self.assertTrue(is_ranked(_match(queue_id=440)))

    def test_aram_is_not_ranked(self):
        self.assertFalse(is_ranked(_match(queue_id=450)))

    def test_normal_is_not_ranked(self):
        self.assertFalse(is_ranked(_match(queue_id=400)))


class TestDeriveStats(unittest.TestCase):
    def test_returns_none_for_missing_player(self):
        self.assertIsNone(derive_stats(FIXTURE_MATCH, "nobody"))

    def test_champion_and_role(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        self.assertEqual(stats["champion"], "Ahri")
        self.assertEqual(stats["role"], "MIDDLE")

    def test_kda(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        # (5 + 7) / 3 = 4.0
        self.assertEqual(stats["kda"], 4.0)
        self.assertEqual(stats["kills"], 5)
        self.assertEqual(stats["deaths"], 3)
        self.assertEqual(stats["assists"], 7)

    def test_cs_per_min(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        # (180 + 20) / 30 = 6.7
        self.assertEqual(stats["cs"], 200)
        self.assertEqual(stats["cs_per_min"], 6.7)

    def test_damage_share(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        # Player is only member of team 100: 18000 / 18000 = 100%
        self.assertEqual(stats["damage_share"], 100.0)

    def test_opponent_stats(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        opp = stats["opponent"]
        self.assertIsNotNone(opp)
        self.assertEqual(opp["champion"], "Zed")
        # CS diff: 200 - 160 = 40
        self.assertEqual(opp["cs_diff"], 40)
        # Gold diff: 12000 - 10000 = 2000
        self.assertEqual(opp["gold_diff"], 2000)

    def test_vision_per_min(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        # 25 / 30 = 0.8
        self.assertEqual(stats["vision_per_min"], 0.8)

    def test_game_duration(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        self.assertEqual(stats["game_duration_min"], 30.0)

    def test_very_short_game_returns_none(self):
        short = _match(duration=30, participants=[_player()])
        self.assertIsNone(derive_stats(short, "me"))


class TestFormatStats(unittest.TestCase):
    def test_format_includes_key_fields(self):
        stats = derive_stats(FIXTURE_MATCH, "me")
        text = _format_stats(stats)
        self.assertIn("Ahri", text)
        self.assertIn("5/3/7", text)
        self.assertIn("6.7/min", text)
        self.assertIn("Zed", text)


class TestReviewResponseShape(unittest.TestCase):
    """Validate the Pydantic schema can parse a well-shaped AI response."""

    def test_match_review_schema(self):
        from app.schemas import MatchReview

        data = {
            "match_id": "EUW1_12345",
            "champion": "Ahri",
            "win": False,
            "verdict": "Solid laning but too many deaths in mid-game teamfights",
            "issues": [
                {"point": "Died 3 times after laning phase", "stat": "3 of 5 deaths post-15"},
                {"point": "Low vision contribution", "stat": "0.8 vision/min"},
            ],
            "tips": [
                "Place deeper wards before contesting objectives",
                "Group with your team instead of side-laning alone",
            ],
        }
        review = MatchReview(**data)
        self.assertEqual(review.champion, "Ahri")
        self.assertEqual(len(review.issues), 2)
        self.assertEqual(len(review.tips), 2)
