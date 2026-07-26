import unittest

from fastapi.testclient import TestClient

from app.config import settings
from app.dependencies import get_ddragon_version
from app.main import app

AI_SETTINGS = ("anthropic_api_key", "gemini_api_key", "ai_provider")


class FeatureFlagTests(unittest.TestCase):
    """AI is off unless a key is set — every key, not just Anthropic.

    These tests must clear *every* AI setting, not one of them. Clearing only the
    Anthropic key left the app AI-enabled for a developer with a real `.env`, so
    the "disabled" assertions failed and, worse, the endpoints made live billable
    API calls. CI has no `.env`, so it only ever bit locally.
    """

    def setUp(self):
        self._orig = {name: getattr(settings, name) for name in AI_SETTINGS}
        for name in AI_SETTINGS:
            setattr(settings, name, "")

    def tearDown(self):
        for name, value in self._orig.items():
            setattr(settings, name, value)
        app.dependency_overrides.clear()

    def test_config_reports_ai_disabled_without_key(self):
        resp = TestClient(app).get("/api/config")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["ai_enabled"])

    def test_config_reports_ai_enabled_with_key(self):
        settings.anthropic_api_key = "sk-test"
        resp = TestClient(app).get("/api/config")
        self.assertTrue(resp.json()["ai_enabled"])

    def test_config_reports_ai_enabled_with_only_a_gemini_key(self):
        settings.gemini_api_key = "gemini-test"
        resp = TestClient(app).get("/api/config")
        self.assertTrue(resp.json()["ai_enabled"])

    def test_draft_is_503_when_disabled(self):
        resp = TestClient(app).post(
            "/api/draft",
            json={"role": "MID", "champion_pool": ["Ahri"]},
        )
        self.assertEqual(resp.status_code, 503)

    def test_patch_digest_is_503_when_disabled(self):
        app.dependency_overrides[get_ddragon_version] = lambda: "14.1.1"
        resp = TestClient(app).get("/api/patch-digest?champions=Ahri")
        self.assertEqual(resp.status_code, 503)


    def test_naming_a_provider_without_its_key_leaves_ai_off(self):
        # Otherwise /api/config claims AI works, the UI shows the draft board,
        # and the call fails mid-request instead of returning a clean 503.
        settings.ai_provider = "gemini"
        self.assertFalse(TestClient(app).get("/api/config").json()["ai_enabled"])


if __name__ == "__main__":
    unittest.main()
