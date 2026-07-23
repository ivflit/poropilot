import unittest

from app.riot.analysis import aggregate_champion_stats

PUUID = "me"


def match(champion_id, name, win, k, d, a, cs, duration):
    """A minimal Match-V5 detail with our PUUID plus one other participant."""
    return {
        "info": {
            "gameDuration": duration,
            "participants": [
                {"puuid": "someone-else", "championId": 999, "championName": "Other"},
                {
                    "puuid": PUUID,
                    "championId": champion_id,
                    "championName": name,
                    "win": win,
                    "kills": k,
                    "deaths": d,
                    "assists": a,
                    "totalMinionsKilled": cs,
                    "neutralMinionsKilled": 0,
                },
            ],
        }
    }


class AggregateChampionStatsTests(unittest.TestCase):
    def test_aggregates_games_wins_and_winrate(self):
        matches = [
            match(157, "Yasuo", True, 5, 3, 7, 200, 1200),
            match(157, "Yasuo", False, 2, 8, 4, 160, 1200),
            match(238, "Zed", True, 10, 2, 3, 180, 900),
        ]
        stats = {s.champion_id: s for s in aggregate_champion_stats(matches, PUUID)}

        self.assertEqual(stats[157].games, 2)
        self.assertEqual(stats[157].wins, 1)
        self.assertEqual(stats[157].win_rate, 0.5)
        self.assertEqual(stats[238].games, 1)
        self.assertEqual(stats[238].win_rate, 1.0)

    def test_kda_sums_across_games_and_floors_deaths(self):
        matches = [
            match(157, "Yasuo", True, 5, 3, 7, 0, 60),
            match(157, "Yasuo", False, 2, 0, 4, 0, 60),  # deathless game
        ]
        stats = aggregate_champion_stats(matches, PUUID)[0]
        # (5+2 kills + 7+4 assists) / (3 deaths, floored at 1) = 18/3 = 6.0
        self.assertEqual(stats.avg_kda, 6.0)

    def test_perfect_kda_when_never_died(self):
        stats = aggregate_champion_stats([match(238, "Zed", True, 4, 0, 2, 0, 60)], PUUID)[0]
        # deaths floored at 1 → (4+2)/1 = 6.0
        self.assertEqual(stats.avg_kda, 6.0)

    def test_cs_per_min_uses_lane_and_jungle_cs_over_total_minutes(self):
        m = match(64, "LeeSin", True, 3, 3, 6, 100, 1200)  # 20 minutes
        m["info"]["participants"][1]["neutralMinionsKilled"] = 80  # jungle CS
        stats = aggregate_champion_stats([m], PUUID)[0]
        # (100 + 80) / 20 minutes = 9.0
        self.assertEqual(stats.avg_cs_per_min, 9.0)

    def test_zero_duration_does_not_divide_by_zero(self):
        stats = aggregate_champion_stats([match(1, "Annie", True, 1, 1, 1, 50, 0)], PUUID)[0]
        self.assertEqual(stats.avg_cs_per_min, 0.0)

    def test_skips_matches_missing_the_puuid(self):
        m = match(157, "Yasuo", True, 5, 3, 7, 200, 1200)
        m["info"]["participants"] = m["info"]["participants"][:1]  # drop our row
        self.assertEqual(aggregate_champion_stats([m], PUUID), [])

    def test_empty_match_list_returns_empty(self):
        self.assertEqual(aggregate_champion_stats([], PUUID), [])

    def test_sorted_by_games_then_champion_id(self):
        matches = [
            match(238, "Zed", True, 1, 1, 1, 10, 600),
            match(157, "Yasuo", True, 1, 1, 1, 10, 600),
            match(157, "Yasuo", True, 1, 1, 1, 10, 600),
        ]
        order = [s.champion_id for s in aggregate_champion_stats(matches, PUUID)]
        self.assertEqual(order, [157, 238])


if __name__ == "__main__":
    unittest.main()
