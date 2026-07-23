"""Cache backends: in-memory by default, Redis when REDIS_URL is set.

Both share the same async get/set interface, so callers don't care which is
active. Values must be JSON-serialisable (Riot API responses are).
"""

import json
import time

from app.config import settings


class InMemoryCache:
    """Process-local cache with per-key expiry. Fine for one worker / local dev."""

    def __init__(self, default_ttl: int = 300) -> None:
        self.default_ttl = default_ttl
        self._store: dict[str, tuple] = {}

    async def get(self, key: str):
        item = self._store.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value, ttl: int | None = None) -> None:
        self._store[key] = (value, time.monotonic() + (ttl or self.default_ttl))


class RedisCache:
    """Shared cache backed by Redis — survives restarts and scales past one worker."""

    def __init__(self, url: str | None = None, client=None, default_ttl: int = 300) -> None:
        if client is None:
            import redis.asyncio as redis

            client = redis.from_url(url)
        self._redis = client
        self.default_ttl = default_ttl

    async def get(self, key: str):
        raw = await self._redis.get(key)
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value, ttl: int | None = None) -> None:
        await self._redis.set(key, json.dumps(value), ex=ttl or self.default_ttl)


def build_cache():
    """Pick the backend from config: Redis if REDIS_URL is set, else in-memory."""
    if settings.redis_url:
        return RedisCache(settings.redis_url)
    return InMemoryCache()


cache = build_cache()
