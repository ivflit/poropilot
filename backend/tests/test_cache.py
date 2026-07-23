import time
import unittest

from app.cache import InMemoryCache, RedisCache


class FakeRedis:
    """Minimal async stand-in for redis.asyncio — enough for the round-trip."""

    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value


class InMemoryCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_set_then_get(self):
        c = InMemoryCache()
        await c.set("k", {"a": 1})
        self.assertEqual(await c.get("k"), {"a": 1})

    async def test_missing_key_is_none(self):
        self.assertIsNone(await InMemoryCache().get("nope"))

    async def test_expired_entry_is_dropped(self):
        c = InMemoryCache()
        await c.set("k", "v", ttl=60)
        c._store["k"] = ("v", time.monotonic() - 1)  # force-expire
        self.assertIsNone(await c.get("k"))


class RedisCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_round_trips_json(self):
        c = RedisCache(client=FakeRedis())
        await c.set("k", {"a": [1, 2, 3]})
        self.assertEqual(await c.get("k"), {"a": [1, 2, 3]})

    async def test_missing_key_is_none(self):
        self.assertIsNone(await RedisCache(client=FakeRedis()).get("nope"))


if __name__ == "__main__":
    unittest.main()
