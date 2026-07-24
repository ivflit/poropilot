import unittest

from fastapi.testclient import TestClient

from app.config import settings
from app.dependencies import get_ddragon_version
from app.main import app


class FeatureFlagTests(unittest.TestCase):
    def setUp(self):
        self._orig_key = settings.anthropic_api_key

    def tearDown(self):
        settings.anthropic_api_key = self._orig_key
        app.dependency_overrides.clear()

    def test_config_reports_ai_disabled_without_key(self):
        settings.anthropic_api_key = ""
        resp = TestClient(app).get("/api/config")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["ai_enabled"])

    def test_config_reports_ai_enabled_with_key(self):
        settings.anthropic_api_key = "sk-test"
        resp = TestClient(app).get("/api/config")
        self.assertTrue(resp.json()["ai_enabled"])

    def test_draft_is_503_when_disabled(self):
        settings.anthropic_api_key = ""
        resp = TestClient(app).post(
            "/api/draft",
            json={"role": "MID", "champion_pool": ["Ahri"]},
        )
        self.assertEqual(resp.status_code, 503)

    def test_patch_digest_is_503_when_disabled(self):
        settings.anthropic_api_key = ""
        app.dependency_overrides[get_ddragon_version] = lambda: "14.1.1"
        resp = TestClient(app).get("/api/patch-digest?champions=Ahri")
        self.assertEqual(resp.status_code, 503)


if __name__ == "__main__":
    unittest.main()
