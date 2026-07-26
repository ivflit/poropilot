import json
import unittest
from pathlib import Path

from app.riot.analysis import aggregate_champion_stats
from app.riot.queues import QUEUE_IDS, MatchQueue, filter_by_queue, in_queue, queue_id

FIXTURE = Path(__file__).parent / "fixtures" / "champion_pool_matches.json"


def match(queue_id_value: int | None) -> dict:
    info: dict = {"gameDuration": 1200, "participants": []}
    if queue_id_value is not None:
        info["queueId"] = queue_id_value
    return {"info": info}


class QueueIdTests(unittest.TestCase):
    def test_ranked_queues_map_to_riots_ids(self):
        self.assertEqual(queue_id(MatchQueue.SOLO), 420)
        self.assertEqual(queue_id(MatchQueue.FLEX), 440)

    def test_all_has_no_id_so_nothing_is_filtered(self):
        self.assertIsNone(queue_id(MatchQueue.ALL))

    def test_queue_values_are_the_query_string_values(self):
        self.assertEqual([q.value for q in MatchQueue], ["all", "solo", "flex"])

    def test_every_filterable_queue_has_an_id(self):
        self.assertEqual(set(QUEUE_IDS), {MatchQueue.SOLO, MatchQueue.FLEX})


class InQueueTests(unittest.TestCase):
    def test_matches_its_own_queue(self):
        self.assertTrue(in_queue(match(420), MatchQueue.SOLO))
        self.assertTrue(in_queue(match(440), MatchQueue.FLEX))

    def test_rejects_a_different_queue(self):
        self.assertFalse(in_queue(match(440), MatchQueue.SOLO))
        self.assertFalse(in_queue(match(450), MatchQueue.SOLO))  # ARAM

    def test_all_accepts_anything(self):
        for queue_value in (420, 440, 450, None):
            self.assertTrue(in_queue(match(queue_value), MatchQueue.ALL))

    def test_a_match_with_no_queue_id_is_excluded_from_a_filtered_view(self):
        # Better to drop an unlabelled game than to let it inflate ranked stats.
        self.assertFalse(in_queue(match(None), MatchQueue.SOLO))


class FilterByQueueTests(unittest.TestCase):
    def setUp(self):
        self.matches = [match(420), match(450), match(440), match(420)]

    def test_keeps_only_the_requested_queue(self):
        solo = filter_by_queue(self.matches, MatchQueue.SOLO)
        self.assertEqual([m["info"]["queueId"] for m in solo], [420, 420])

    def test_preserves_order(self):
        mixed = [match(420), match(440), match(420)]
        self.assertEqual(len(filter_by_queue(mixed, MatchQueue.SOLO)), 2)

    def test_all_returns_everything(self):
        self.assertEqual(len(filter_by_queue(self.matches, MatchQueue.ALL)), 4)

    def test_no_games_in_the_queue_is_empty_not_an_error(self):
        aram_only = [match(450), match(450)]
        self.assertEqual(filter_by_queue(aram_only, MatchQueue.FLEX), [])

    def test_accepts_any_iterable(self):
        self.assertEqual(len(filter_by_queue(iter(self.matches), MatchQueue.SOLO)), 2)


class FixtureAggregationPerQueueTests(unittest.TestCase):
    """The point of the filter: the same match set gives different — and honest —
    numbers per queue. The fixture holds six games across solo (420), flex (440)
    and ARAM (450), so the ARAM games must not touch the ranked win-rates.
    """

    PUUID = "por-por-por"

    @classmethod
    def setUpClass(cls):
        cls.matches = json.loads(FIXTURE.read_text())

    def stats_for(self, queue: MatchQueue) -> dict:
        kept = filter_by_queue(self.matches, queue)
        return {s.champion_id: s for s in aggregate_champion_stats(kept, self.PUUID)}

    def test_all_queues_folds_every_game(self):
        by_id = self.stats_for(MatchQueue.ALL)
        self.assertEqual(sum(s.games for s in by_id.values()), 6)
        self.assertEqual(set(by_id), {157, 238, 64})

    def test_solo_excludes_the_aram_games(self):
        by_id = self.stats_for(MatchQueue.SOLO)
        # Three solo games: two Yasuo (1W/1L) and one Zed win. LeeSin was ARAM only.
        self.assertEqual(sum(s.games for s in by_id.values()), 3)
        self.assertEqual(set(by_id), {157, 238})
        self.assertEqual(by_id[157].games, 2)
        self.assertEqual(by_id[157].win_rate, 0.5)
        self.assertEqual(by_id[238].games, 1)
        self.assertEqual(by_id[238].win_rate, 1.0)

    def test_flex_is_the_single_flex_game(self):
        by_id = self.stats_for(MatchQueue.FLEX)
        self.assertEqual(set(by_id), {238})
        self.assertEqual(by_id[238].games, 1)
        self.assertEqual(by_id[238].win_rate, 1.0)

    def test_unfiltered_yasuo_winrate_differs_from_solo(self):
        # The headline reason for the feature: an ARAM win was propping up the
        # ranked number (2/3 unfiltered vs a true 1/2 in solo queue).
        self.assertEqual(self.stats_for(MatchQueue.ALL)[157].win_rate, 0.6667)
        self.assertEqual(self.stats_for(MatchQueue.SOLO)[157].win_rate, 0.5)


if __name__ == "__main__":
    unittest.main()
