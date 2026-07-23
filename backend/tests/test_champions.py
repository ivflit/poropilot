import unittest

from app.champions import build_champion_map

# A stubbed slice of Data Dragon's champion.json `data` block.
STUB = {
    "Aatrox": {
        "key": "266",
        "id": "Aatrox",
        "name": "Aatrox",
        "title": "the Darkin Blade",
        "image": {"full": "Aatrox.png"},
    },
    "Ahri": {
        "key": "103",
        "id": "Ahri",
        "name": "Ahri",
        "title": "the Nine-Tailed Fox",
        "image": {"full": "Ahri.png"},
    },
}


class BuildChampionMapTests(unittest.TestCase):
    def test_maps_numeric_id_to_name_and_title(self):
        champions = build_champion_map("14.1.1", STUB)
        self.assertEqual(champions[266].name, "Aatrox")
        self.assertEqual(champions[103].title, "the Nine-Tailed Fox")

    def test_keys_are_integers(self):
        champions = build_champion_map("14.1.1", STUB)
        self.assertIn(266, champions)
        self.assertNotIn("266", champions)

    def test_builds_image_url_from_version(self):
        champions = build_champion_map("14.1.1", STUB)
        self.assertEqual(
            champions[266].image_url,
            "https://ddragon.leagueoflegends.com/cdn/14.1.1/img/champion/Aatrox.png",
        )

    def test_includes_every_champion(self):
        champions = build_champion_map("14.1.1", STUB)
        self.assertEqual(len(champions), 2)


if __name__ == "__main__":
    unittest.main()
