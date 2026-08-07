"""Tests for GET /api/tier-list."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.cache import cache
from app.dependencies import get_ddragon_version, require_ai
from app.main import app

MOCK_TIER_RESULT = {
    "tiers": [
        {"tier": "S", "champions": [{"name": "Ahri", "reason": "Strong roaming mid"}]},
        {"tier": "A", "champions": [{"name": "Zed", "reason": "High kill pressure"}]},
    ],
}


def _require_ai_pass():
    pass


def _require_ai_fail():
    raise HTTPException(status_code=503, detail="AI disabled")


class TierListRouteTests(unittest.TestCase):
    def setUp(self):
        cache._store.clear()
        app.dependency_overrides[get_ddragon_version] = lambda: "14.1.1"
        app.dependency_overrides[require_ai] = _require_ai_pass

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.api.routes.generate_tier_list", return_value=MOCK_TIER_RESULT)
    def test_returns_tier_list(self, _gen):
        r = TestClient(app).get("/api/tier-list?role=MID")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["role"], "MID")
        self.assertEqual(data["patch"], "14.1.1")
        self.assertEqual(len(data["tiers"]), 2)
        self.assertEqual(data["tiers"][0]["tier"], "S")

    @patch("app.api.routes.generate_tier_list", return_value=MOCK_TIER_RESULT)
    def test_cached_on_second_call(self, gen_mock):
        client = TestClient(app)
        client.get("/api/tier-list?role=MID")
        client.get("/api/tier-list?role=MID")
        gen_mock.assert_called_once()

    def test_returns_503_when_ai_disabled(self):
        app.dependency_overrides[require_ai] = _require_ai_fail
        r = TestClient(app).get("/api/tier-list?role=MID")
        self.assertEqual(r.status_code, 503)

    @patch("app.api.routes.generate_tier_list", return_value=MOCK_TIER_RESULT)
    def test_role_normalised_to_uppercase(self, gen_mock):
        TestClient(app).get("/api/tier-list?role=mid")
        gen_mock.assert_called_once_with("MID", "14.1.1")


if __name__ == "__main__":
    unittest.main()
