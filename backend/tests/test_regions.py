import unittest

from app.riot.regions import (
    UnknownRegionError,
    platform_host,
    regional_route,
)


class RegionRoutingTests(unittest.TestCase):
    def test_platform_host_is_case_insensitive(self):
        self.assertEqual(platform_host("euw"), "euw1")
        self.assertEqual(platform_host("EUW"), "euw1")

    def test_platform_maps_to_regional_cluster(self):
        self.assertEqual(regional_route("euw1"), "europe")
        self.assertEqual(regional_route("na1"), "americas")
        self.assertEqual(regional_route("kr"), "asia")

    def test_unknown_region_raises(self):
        with self.assertRaises(UnknownRegionError):
            platform_host("MARS")

    def test_unknown_platform_raises(self):
        with self.assertRaises(UnknownRegionError):
            regional_route("mars1")


if __name__ == "__main__":
    unittest.main()
