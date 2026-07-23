import time
from typing import Any


class TTLCache:
    """Tiny in-memory cache with per-key expiry.

    Good enough for local dev and a single-instance deploy. Swap for Redis
    (see settings.redis_url) once you run more than one backend process.
    """

    def __init__(self, default_ttl: int = 300) -> None:
        self.default_ttl = default_ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = (value, time.monotonic() + (ttl or self.default_ttl))


cache = TTLCache()
