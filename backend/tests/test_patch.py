import json
import unittest

from fastapi.testclient import TestClient

import app.ai.patch as patch_mod
from app.ai.patch import patch_digest
from app.cache import cache
from app.config import settings
from app.dependencies import get_ddragon_version
from app.main import app


class FakeMessages:
    def __init__(self):
        self.calls = 0
        self.last_kwargs = None

    def create(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        payload = {"notes": [{"champion": "Aatrox", "summary": "Buffed Q base damage."}]}
        block = type("Block", (), {"type": "text", "text": json.dumps(payload)})()
        return type("Resp", (), {"content": [block]})()


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


class PatchDigestServiceTests(unittest.TestCase):
    def test_returns_patch_and_notes_shape(self):
        fake = FakeClient()
        result = patch_digest(["Aatrox"], "14.1.1", client=fake)
        self.assertEqual(result["patch"], "14.1.1")
        self.assertEqual(result["notes"][0]["champion"], "Aatrox")

    def test_scopes_prompt_to_the_given_champions(self):
        fake = FakeClient()
        patch_digest(["Aatrox", "Ahri"], "14.1.1", client=fake)
        prompt = fake.messages.last_kwargs["messages"][0]["content"]
        self.assertIn("Aatrox", prompt)
        self.assertIn("Ahri", prompt)


class PatchDigestRouteTests(unittest.TestCase):
    def setUp(self):
        cache._store.clear()
        self.fake = FakeClient()
        patch_mod._client = self.fake
        self._orig_key = settings.anthropic_api_key
        settings.anthropic_api_key = "sk-test"  # so the require_ai guard passes
        app.dependency_overrides[get_ddragon_version] = lambda: "14.1.1"

    def tearDown(self):
        settings.anthropic_api_key = self._orig_key
        app.dependency_overrides.clear()

    def test_digest_is_cached_for_the_patch(self):
        client = TestClient(app)
        first = client.get("/api/patch-digest?champions=Aatrox&champions=Ahri")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["patch"], "14.1.1")
        calls_after_first = self.fake.messages.calls

        client.get("/api/patch-digest?champions=Aatrox&champions=Ahri")
        self.assertEqual(self.fake.messages.calls, calls_after_first)  # cache hit, no new AI call


if __name__ == "__main__":
    unittest.main()
