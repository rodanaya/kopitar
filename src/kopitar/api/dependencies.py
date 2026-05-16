"""
API Dependencies

Dependency injection functions for FastAPI endpoints.
Provides database sessions, caching, authentication, and other shared resources.
"""

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status

from .database import get_db_session
from .cache import KopitarCache, get_cache
from .config import get_settings

settings = get_settings()


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Return the user context attached to the request by AuthMiddleware.

    Falls back to an anonymous context when the middleware is absent
    (e.g. during unit tests that call endpoints directly).
    """
    return getattr(
        request.state,
        "user",
        {"user_id": "anonymous", "authenticated": False},
    )


def get_pagination_params(offset: int = 0, limit: int = 50) -> Dict[str, int]:
    """
    Validate and return pagination parameters.

    Raises:
        HTTPException: If parameters are out of range.
    """
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be non-negative",
        )
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 1000",
        )
    return {"offset": offset, "limit": limit}


def validate_season_format(season: Optional[str] = None) -> Optional[str]:
    """
    Validate an NHL season string in YYYYYYYY format (e.g. 20232024).

    Raises:
        HTTPException: If the format is invalid.
    """
    if season is None:
        return None

    if len(season) != 8 or not season.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Season must be in YYYYYYYY format (e.g., 20232024)",
        )

    start_year = int(season[:4])
    end_year = int(season[4:])

    if end_year != start_year + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid season: end year must be start year + 1",
        )

    if start_year < 1917 or start_year > 2050:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Season year must be between 1917 and 2050",
        )

    return season


def validate_position(position: Optional[str] = None) -> Optional[str]:
    """
    Validate a player position code (G, D, or F).

    Raises:
        HTTPException: If the position code is unrecognised.
    """
    if position is None:
        return None

    valid_positions = {"G", "D", "F"}
    if position not in valid_positions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Position must be one of: G (Goalie), D (Defense), F (Forward)",
        )
    return position


class RateLimiter:
    """
    Per-endpoint rate limiter that uses the shared KopitarCache.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ) -> None:
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    async def __call__(
        self,
        request: Request,
        cache: KopitarCache = Depends(get_cache),
    ) -> None:
        client_id = (
            request.client.host if request.client else "unknown"
        )

        minute_key = f"rate_limit:minute:{client_id}"
        hour_key = f"rate_limit:hour:{client_id}"

        minute_count: int = (await cache.get(minute_key)) or 0
        if minute_count >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many requests per minute",
            )

        hour_count: int = (await cache.get(hour_key)) or 0
        if hour_count >= self.requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many requests per hour",
            )

        await cache.set(minute_key, minute_count + 1, ttl=60)
        await cache.set(hour_key, hour_count + 1, ttl=3600)


class CacheManager:
    """
    Helper for cache-aside pattern: get from cache or fetch-and-store.
    """

    def __init__(self, default_ttl: int = 300) -> None:
        self.default_ttl = default_ttl

    async def get_or_set(
        self,
        key: str,
        fetch_func,
        ttl: Optional[int] = None,
        cache: Optional[KopitarCache] = None,
    ) -> Any:
        if cache is None:
            return await fetch_func()

        cached = await cache.get(key)
        if cached is not None:
            return cached

        fresh = await fetch_func()
        await cache.set(key, fresh, ttl=ttl or self.default_ttl)
        return fresh

    async def invalidate(self, key: str, cache: Optional[KopitarCache] = None) -> None:
        if cache is not None:
            await cache.delete(key)


standard_rate_limit = RateLimiter(requests_per_minute=60, requests_per_hour=1000)
heavy_rate_limit = RateLimiter(requests_per_minute=10, requests_per_hour=100)
cache_manager = CacheManager()

__all__ = [
    "get_db_session",
    "get_cache",
    "get_current_user",
    "get_pagination_params",
    "validate_season_format",
    "validate_position",
    "RateLimiter",
    "CacheManager",
    "standard_rate_limit",
    "heavy_rate_limit",
    "cache_manager",
]
