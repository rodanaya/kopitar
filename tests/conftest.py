"""
Shared pytest fixtures for the Kopitar test suite.
"""

from __future__ import annotations

import os

# Set ENVIRONMENT=test before any application modules are imported so that
# TestSettings are loaded (avoids SECRET_KEY validation and .env conflicts).
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

from datetime import date
from typing import Any
from unittest.mock import AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Game history fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_game_history() -> list[dict[str, Any]]:
    """
    Five games over ten days, with realistic NHL goaltender values.

    Dates: Jan 1, 3, 5, 8, 10  (within a 10-day window ending Jan 10).
    No back-to-back games in this baseline history.
    """
    return [
        {
            "game_date": date(2024, 1, 1),
            "minutes_played": 60.0,
            "shots_faced": 28,
            "miles_traveled": 350.0,
            "timezone_change": 0.0,
            "is_back_to_back": False,
        },
        {
            "game_date": date(2024, 1, 3),
            "minutes_played": 59.5,
            "shots_faced": 32,
            "miles_traveled": 0.0,
            "timezone_change": 0.0,
            "is_back_to_back": False,
        },
        {
            "game_date": date(2024, 1, 5),
            "minutes_played": 60.0,
            "shots_faced": 25,
            "miles_traveled": 1200.0,
            "timezone_change": -1.0,
            "is_back_to_back": False,
        },
        {
            "game_date": date(2024, 1, 8),
            "minutes_played": 58.0,
            "shots_faced": 30,
            "miles_traveled": 1200.0,
            "timezone_change": 1.0,
            "is_back_to_back": False,
        },
        {
            "game_date": date(2024, 1, 10),
            "minutes_played": 60.0,
            "shots_faced": 27,
            "miles_traveled": 0.0,
            "timezone_change": 0.0,
            "is_back_to_back": False,
        },
    ]


@pytest.fixture
def back_to_back_history() -> list[dict[str, Any]]:
    """
    Two consecutive nights (Jan 14 and Jan 15) to simulate a back-to-back.
    """
    return [
        {
            "game_date": date(2024, 1, 10),
            "minutes_played": 60.0,
            "shots_faced": 28,
            "miles_traveled": 0.0,
            "timezone_change": 0.0,
            "is_back_to_back": False,
        },
        {
            "game_date": date(2024, 1, 14),
            "minutes_played": 60.0,
            "shots_faced": 30,
            "miles_traveled": 500.0,
            "timezone_change": 0.0,
            "is_back_to_back": False,
        },
        {
            "game_date": date(2024, 1, 15),
            "minutes_played": 60.0,
            "shots_faced": 33,
            "miles_traveled": 500.0,
            "timezone_change": 0.0,
            "is_back_to_back": True,
        },
    ]


# ---------------------------------------------------------------------------
# Boxscore fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_boxscore() -> dict[str, Any]:
    """
    A minimal NHL API (api-web.nhle.com/v1/) boxscore dict.

    Contains two goalies (one per side) with all standard fields present.
    """
    return {
        "id": 2023020789,
        "gameType": 2,
        "gameDate": "2024-01-15",
        "season": "20232024",
        "gameState": "OFF",
        "awayTeam": {"id": 10, "abbrev": "TOR", "score": 2},
        "homeTeam": {"id": 6, "abbrev": "BOS", "score": 3},
        "venue": {"default": "TD Garden"},
        "playerByGameStats": {
            "awayTeam": {
                "goalies": [
                    {
                        "playerId": 8480045,
                        "savePctg": 0.923,
                        "shotsAgainst": 26,
                        "saves": 24,
                        "goalsAgainst": 2,
                        "toi": "59:12",
                        "decision": "L",
                    }
                ],
                "forwards": [],
                "defense": [],
            },
            "homeTeam": {
                "goalies": [
                    {
                        "playerId": 8479320,
                        "savePctg": 0.957,
                        "shotsAgainst": 23,
                        "saves": 22,
                        "goalsAgainst": 1,
                        "toi": "60:00",
                        "decision": "W",
                    }
                ],
                "forwards": [],
                "defense": [],
            },
        },
    }


@pytest.fixture
def boxscore_missing_toi() -> dict[str, Any]:
    """
    A boxscore where the goalie entry has no 'toi' field.
    Used to verify graceful handling of missing time-on-ice data.
    """
    return {
        "id": 2023020001,
        "gameDate": "2024-01-01",
        "awayTeam": {"id": 5, "abbrev": "PIT", "score": 1},
        "homeTeam": {"id": 3, "abbrev": "NYR", "score": 2},
        "playerByGameStats": {
            "awayTeam": {
                "goalies": [
                    {
                        "playerId": 8471418,
                        "savePctg": 0.900,
                        "shotsAgainst": 30,
                        "saves": 27,
                        "goalsAgainst": 3,
                        # "toi" intentionally omitted
                    }
                ]
            },
            "homeTeam": {"goalies": []},
        },
    }


# ---------------------------------------------------------------------------
# Cache mock
# ---------------------------------------------------------------------------


class MockCache:
    """In-memory async cache stub for use in FastAPI dependency overrides."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        pass


@pytest.fixture
def mock_cache() -> MockCache:
    """Return a fresh :class:`MockCache` instance for each test."""
    return MockCache()
