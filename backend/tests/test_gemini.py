import json
import unittest

from app.ai import gemini
from app.ai.provider import active_provider
from app.config import settings


def fake_client(payload):
    """A stand-in for the genai client whose interactions.create returns `payload` as JSON."""
    interaction = type("Interaction", (), {"output_text": json.dumps(payload)})()
    interactions = type("Interactions", (), {"create": lambda self, **kwargs: interaction})()
    return type("Client", (), {"interactions": interactions})()


class GeminiBackendTests(unittest.TestCase):
    def test_suggest_pick_returns_suggestions(self):
        client = fake_client(
            {"suggestions": [{"champion": "Ahri", "reason": "Strong pick.", "confidence": "high"}]}
        )
        result = gemini.suggest_pick(
            role="MID", champion_pool=["Ahri"], ally_picks=[], enemy_bans=[], client=client
        )
        self.assertEqual(result["suggestions"][0]["champion"], "Ahri")

    def test_patch_digest_returns_patch_and_notes(self):
        client = fake_client({"notes": [{"champion": "Aatrox", "summary": "Buffed Q."}]})
        result = gemini.patch_digest(["Aatrox"], "14.1.1", client=client)
        self.assertEqual(result["patch"], "14.1.1")
        self.assertEqual(result["notes"][0]["champion"], "Aatrox")


class ProviderSelectionTests(unittest.TestCase):
    def setUp(self):
        self._orig = (settings.ai_provider, settings.anthropic_api_key, settings.gemini_api_key)

    def tearDown(self):
        settings.ai_provider, settings.anthropic_api_key, settings.gemini_api_key = self._orig

    def _set(self, provider="", anthropic="", gemini=""):
        settings.ai_provider = provider
        settings.anthropic_api_key = anthropic
        settings.gemini_api_key = gemini

    def test_none_when_no_keys(self):
        self._set()
        self.assertIsNone(active_provider())

    def test_auto_detects_anthropic(self):
        self._set(anthropic="sk-test")
        self.assertEqual(active_provider(), "anthropic")

    def test_auto_detects_gemini(self):
        self._set(gemini="g-test")
        self.assertEqual(active_provider(), "gemini")

    def test_explicit_provider_overrides_detection(self):
        self._set(provider="gemini", anthropic="sk-test", gemini="g-test")
        self.assertEqual(active_provider(), "gemini")

    def test_explicit_provider_without_its_key_disables_ai(self):
        # Naming a provider you have no key for used to report AI as enabled, so
        # the UI offered the draft board and the call failed mid-request. Off is
        # the honest answer — and it's what the 503 guard relies on.
        self._set(provider="gemini", anthropic="sk-test")
        self.assertIsNone(active_provider())

    def test_explicit_provider_ignores_case_and_stray_whitespace(self):
        self._set(provider=" Gemini ", gemini="g-test")
        self.assertEqual(active_provider(), "gemini")

    def test_an_unknown_provider_name_disables_ai(self):
        self._set(provider="openai", anthropic="sk-test")
        self.assertIsNone(active_provider())


if __name__ == "__main__":
    unittest.main()
