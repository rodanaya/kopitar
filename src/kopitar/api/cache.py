"""
Cache Abstraction Layer

Provides a unified cache interface backed by Redis when available,
falling back to an in-memory dict with TTL tracking so the application
runs without a Redis instance.
"""

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_cache_singleton: Optional["KopitarCache"] = None


class _MemoryStore:
    """Thread-safe-enough in-memory store with per-key TTL."""

    def __init__(self) -> None:
        # {key: (value, expires_at)}  — expires_at is None for no-expiry
        self._data: Dict[str, Tuple[Any, Optional[float]]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = time.monotonic() + ttl if ttl is not None else None
        self._data[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def ping(self) -> bool:
        return True

    def close(self) -> None:
        pass


class KopitarCache:
    """
    Cache abstraction used throughout the application.

    Attempts to connect to Redis on first use.  If Redis is unavailable
    the instance falls back to an in-process memory store so nothing
    breaks during local development.
    """

    def __init__(self) -> None:
        self._redis: Any = None
        self._memory: _MemoryStore = _MemoryStore()
        self._use_redis: bool = False
        self._initialised: bool = False

    async def _ensure_initialised(self) -> None:
        if self._initialised:
            return
        self._initialised = True

        redis_url: Optional[str] = os.environ.get("REDIS_URL")
        if not redis_url:
            logger.info("REDIS_URL not set — using in-memory cache")
            return

        try:
            import redis.asyncio as aioredis  # type: ignore[import]

            client = aioredis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await client.ping()
            self._redis = client
            self._use_redis = True
            logger.info("Redis cache connected: %s", redis_url)
        except Exception:
            logger.warning(
                "Could not connect to Redis at %s — using in-memory cache",
                redis_url,
                exc_info=True,
            )

    async def get(self, key: str) -> Optional[Any]:
        await self._ensure_initialised()
        if self._use_redis:
            import pickle

            raw = await self._redis.get(key)
            if raw is None:
                return None
            try:
                return pickle.loads(raw)
            except Exception:
                return raw
        return self._memory.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        await self._ensure_initialised()
        if self._use_redis:
            import pickle

            await self._redis.set(key, pickle.dumps(value), ex=ttl)
        else:
            self._memory.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self._ensure_initialised()
        if self._use_redis:
            await self._redis.delete(key)
        else:
            self._memory.delete(key)

    async def ping(self) -> bool:
        await self._ensure_initialised()
        if self._use_redis:
            return bool(await self._redis.ping())
        return self._memory.ping()

    async def close(self) -> None:
        if self._use_redis and self._redis is not None:
            await self._redis.aclose()
        self._memory.close()


async def get_cache() -> KopitarCache:
    """
    FastAPI dependency / lifespan helper that returns the singleton cache.

    Calling it from the lifespan context initialises the connection once;
    subsequent ``Depends(get_cache)`` calls return the same instance.
    """
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = KopitarCache()
    await _cache_singleton._ensure_initialised()
    return _cache_singleton
