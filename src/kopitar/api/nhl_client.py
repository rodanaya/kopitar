"""
NHL API Client

Async client for the current NHL API (post-November 2023 endpoints).
Supports rate limiting, exponential-backoff retries, TTL caching,
and the circuit-breaker pattern.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional, Union

import httpx
from cachetools import TTLCache

from .endpoints import NHLEndpoints
from .rate_limiter import AdaptiveRateLimiter, RateLimitConfig, CircuitBreaker
from .exceptions import (
    NHLAPIError,
    RateLimitError,
    APITimeoutError,
    DataValidationError,
    PlayerNotFoundError,
    GameNotFoundError,
)


@dataclass
class ClientConfig:
    """Configuration for NHLAPIClient."""

    web_base_url: str = "https://api-web.nhle.com/v1"
    stats_base_url: str = "https://api.nhle.com/stats/rest/en"
    timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 2.0
    cache_size: int = 1000
    cache_ttl: int = 300  # seconds
    enable_caching: bool = True
    enable_rate_limiting: bool = True
    enable_circuit_breaker: bool = True
    user_agent: str = "Kopitar-NHL-Analytics/1.0"


class NHLAPIClient:
    """
    Async NHL API client targeting the post-2023 NHL endpoints.

    Handles scheduling, boxscores, player info, rosters, goalie stats,
    standings, and team season schedules with:
    - Adaptive rate limiting (100 req/min ceiling)
    - Exponential-backoff retry (max 3 attempts)
    - TTL response cache
    - Circuit-breaker protection
    """

    def __init__(self, config: Optional[ClientConfig] = None) -> None:
        self.config = config or ClientConfig()
        self.logger = logging.getLogger(__name__)

        self.rate_limiter: Optional[AdaptiveRateLimiter] = None
        if self.config.enable_rate_limiting:
            self.rate_limiter = AdaptiveRateLimiter(RateLimitConfig())

        self.circuit_breaker: Optional[CircuitBreaker] = None
        if self.config.enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker()

        self.cache: Optional[TTLCache] = None
        if self.config.enable_caching:
            self.cache = TTLCache(
                maxsize=self.config.cache_size,
                ttl=self.config.cache_ttl,
            )

        self._http = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={"User-Agent": self.config.user_agent},
        )

        self.stats: Dict[str, int] = {
            "requests_made": 0,
            "cache_hits": 0,
            "rate_limit_errors": 0,
            "total_retry_attempts": 0,
        }

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "NHLAPIClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Core request machinery
    # ------------------------------------------------------------------

    async def get(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """
        GET with caching, rate limiting, and retry.

        Returns the parsed JSON body on success; raises an NHLAPIError
        subclass on failure.
        """
        cache_key = f"{url}:{hash(str(kwargs))}"

        if self.cache is not None and cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]  # type: ignore[return-value]

        if self.rate_limiter is not None:
            await self.rate_limiter.acquire_async()

        last_exc: Optional[Exception] = None
        for attempt in range(self.config.max_retries + 1):
            try:
                if self.circuit_breaker is not None:
                    with self.circuit_breaker:
                        data = await self._make_request(url, **kwargs)
                else:
                    data = await self._make_request(url, **kwargs)

                if self.rate_limiter is not None:
                    self.rate_limiter.on_success()

                if self.cache is not None:
                    self.cache[cache_key] = data

                return data

            except RateLimitError as exc:
                self.stats["rate_limit_errors"] += 1
                if self.rate_limiter is not None:
                    self.rate_limiter.on_rate_limit()
                if attempt < self.config.max_retries:
                    delay = self._backoff(attempt)
                    self.logger.warning("Rate limited — retrying in %.1fs", delay)
                    await asyncio.sleep(delay)
                    self.stats["total_retry_attempts"] += 1
                    last_exc = exc
                    continue
                raise

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                if attempt < self.config.max_retries:
                    delay = self._backoff(attempt)
                    self.logger.warning("Request error (%s) — retrying in %.1fs", exc, delay)
                    await asyncio.sleep(delay)
                    self.stats["total_retry_attempts"] += 1
                    last_exc = exc
                    continue
                raise APITimeoutError(
                    f"Request timed out after {self.config.max_retries} retries"
                ) from exc

            except Exception as exc:
                last_exc = exc
                break

        raise NHLAPIError(
            f"Request failed after {self.config.max_retries} retries"
        ) from last_exc

    async def _make_request(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        self.stats["requests_made"] += 1
        try:
            response = await self._http.get(url, **kwargs)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
            if not isinstance(data, dict):
                raise DataValidationError("Response is not a JSON object")
            return data
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429:
                retry_after = exc.response.headers.get("Retry-After")
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                )
            if status == 404:
                raise NHLAPIError(f"Not found: {url}", status_code=404)
            raise NHLAPIError(
                f"HTTP {status}: {exc.response.text}", status_code=status
            )
        except json.JSONDecodeError as exc:
            raise DataValidationError(f"Invalid JSON response: {exc}") from exc

    def _backoff(self, attempt: int) -> float:
        return min(60.0, self.config.backoff_factor ** attempt)

    # ------------------------------------------------------------------
    # High-level API methods
    # ------------------------------------------------------------------

    async def get_schedule(self, query_date: Union[date, str]) -> Dict[str, Any]:
        """
        Schedule for a single date.

        Response shape: {"gameWeek": [{"date": "YYYY-MM-DD", "games": [...]}]}
        """
        url = NHLEndpoints.schedule(query_date)
        return await self.get(url)

    async def get_game_boxscore(self, game_id: int) -> Dict[str, Any]:
        """
        Boxscore for a completed or in-progress game.

        Response shape: {"id": ..., "playerByGameStats": {"homeTeam": {...}, "awayTeam": {...}}}
        """
        if not NHLEndpoints.validate_game_id(game_id):
            raise GameNotFoundError(game_id)
        url = NHLEndpoints.game_boxscore(game_id)
        try:
            return await self.get(url)
        except NHLAPIError as exc:
            if getattr(exc, "status_code", None) == 404:
                raise GameNotFoundError(game_id) from exc
            raise

    async def get_player(self, player_id: int) -> Dict[str, Any]:
        """
        Player biographical info and career stats.

        Response shape: {"playerId": ..., "firstName": {"default": "..."}, ...}
        """
        url = NHLEndpoints.player_landing(player_id)
        try:
            return await self.get(url)
        except NHLAPIError as exc:
            if getattr(exc, "status_code", None) == 404:
                raise PlayerNotFoundError(player_id) from exc
            raise

    async def get_team_roster(
        self, team_abbrev: str, season: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Current (or season-specific) roster for a team.

        ``team_abbrev`` is the three-letter abbreviation, e.g. "TOR".
        """
        url = NHLEndpoints.team_roster(team_abbrev, season)
        return await self.get(url)

    async def get_goalie_stats(
        self,
        season: str,
        limit: int = 100,
        start: int = 0,
        sort: str = "wins",
    ) -> Dict[str, Any]:
        """
        Goalie summary stats from the Stats API.

        ``season`` must be 8 digits, e.g. "20232024".
        """
        if not NHLEndpoints.validate_season(season):
            raise DataValidationError(f"Invalid season format: {season!r}")
        url = NHLEndpoints.goalie_stats(season, limit=limit, start=start, sort=sort)
        return await self.get(url)

    async def get_standings(self, query_date: Union[date, str]) -> Dict[str, Any]:
        """Standings as of a specific date."""
        url = NHLEndpoints.standings(query_date)
        return await self.get(url)

    async def get_team_schedule(self, team_abbrev: str, season: str) -> Dict[str, Any]:
        """
        Full regular-season schedule for a team.

        ``season`` must be 8 digits, e.g. "20232024".
        """
        if not NHLEndpoints.validate_season(season):
            raise DataValidationError(f"Invalid season format: {season!r}")
        url = NHLEndpoints.team_schedule_season(team_abbrev, season)
        return await self.get(url)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_client_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = dict(self.stats)
        if self.rate_limiter is not None:
            stats["current_rate_limit"] = self.rate_limiter.current_rate
        if self.cache is not None:
            stats["cache_size"] = len(self.cache)
            total = max(1, self.stats["requests_made"])
            stats["cache_hit_rate"] = self.stats["cache_hits"] / total
        if self.circuit_breaker is not None:
            stats["circuit_breaker_state"] = self.circuit_breaker.state
        return stats

    def clear_cache(self) -> None:
        if self.cache is not None:
            self.cache.clear()
            self.logger.info("Cache cleared")

    def reset_stats(self) -> None:
        self.stats = {
            "requests_made": 0,
            "cache_hits": 0,
            "rate_limit_errors": 0,
            "total_retry_attempts": 0,
        }
