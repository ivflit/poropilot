import unittest

from app.riot.analysis import aggregate_champion_stats, top_champions

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


class FormScoreTests(unittest.TestCase):
    def test_proven_winrate_outranks_tiny_perfect_sample(self):
        # A single 100% game must not beat a well-evidenced 12-of-20 (60%).
        matches = [match(238, "Zed", True, 5, 1, 2, 100, 1200)]  # 1-1, 100%
        matches += [match(157, "Yasuo", True, 5, 3, 5, 200, 1200) for _ in range(12)]
        matches += [match(157, "Yasuo", False, 2, 6, 3, 160, 1200) for _ in range(8)]
        top = top_champions(aggregate_champion_stats(matches, PUUID))
        self.assertEqual(top[0].champion_id, 157)
        self.assertGreater(top[0].form_score, top[1].form_score)

    def test_kda_breaks_ties_between_equal_winrates(self):
        # Two champions, identical 3-of-4 win-rate; the higher KDA ranks first.
        carry = [match(64, "LeeSin", True, 12, 1, 8, 100, 1200) for _ in range(3)]
        carry += [match(64, "LeeSin", False, 6, 3, 4, 100, 1200)]
        even = [match(238, "Zed", True, 3, 3, 3, 100, 1200) for _ in range(3)]
        even += [match(238, "Zed", False, 1, 4, 1, 100, 1200)]
        by_id = {s.champion_id: s for s in aggregate_champion_stats(carry + even, PUUID)}
        self.assertEqual(by_id[64].win_rate, by_id[238].win_rate)
        self.assertGreater(by_id[64].form_score, by_id[238].form_score)

    def test_no_games_has_zero_form_and_top_of_empty_is_empty(self):
        self.assertEqual(top_champions([]), [])

    def test_top_champions_respects_limit(self):
        matches = [match(cid, str(cid), True, 5, 2, 3, 100, 1200) for cid in range(1, 6)]
        self.assertEqual(len(top_champions(aggregate_champion_stats(matches, PUUID), limit=3)), 3)


if __name__ == "__main__":
    unittest.main()
