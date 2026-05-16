"""
Tests for GameTransformer (ETL layer)

Verifies that the transformer correctly maps raw NHL API responses into
normalized dicts, handles edge cases (missing fields, malformed TOI, etc.),
and produces correct output structure.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.kopitar.etl.transformers.game_transformer import GameTransformer


class TestGameTransformer:
    """Unit tests for GameTransformer."""

    @pytest.fixture
    def transformer(self) -> GameTransformer:
        return GameTransformer()

    # ------------------------------------------------------------------
    # transform_goalie_stats
    # ------------------------------------------------------------------

    def test_transform_goalie_stats_extracts_save_pct(
        self, transformer: GameTransformer, sample_boxscore: dict[str, Any]
    ) -> None:
        """save_pct is extracted from savePctg when present."""
        records = transformer.transform_goalie_stats(sample_boxscore, game_id=2023020789)

        assert len(records) == 2  # one per side

        # Away goalie: savePctg = 0.923
        away = next(r for r in records if r["player_id"] == 8480045)
        assert away["save_pct"] == pytest.approx(0.923, abs=0.001)
        assert away["saves"] == 24
        assert away["shots_against"] == 26
        assert away["goals_against"] == 2
        assert away["decision"] == "L"
        assert away["game_id"] == 2023020789
        assert away["team_id"] == 10  # TOR

    def test_transform_goalie_stats_toi_parsed_correctly(
        self, transformer: GameTransformer, sample_boxscore: dict[str, Any]
    ) -> None:
        """TOI '59:12' is parsed to 59.2 minutes (59 + 12/60)."""
        records = transformer.transform_goalie_stats(sample_boxscore, game_id=2023020789)
        away = next(r for r in records if r["player_id"] == 8480045)

        expected_minutes = 59.0 + 12 / 60.0
        assert away["minutes_played"] == pytest.approx(expected_minutes, rel=1e-3)

    def test_transform_goalie_stats_home_goalie(
        self, transformer: GameTransformer, sample_boxscore: dict[str, Any]
    ) -> None:
        """Home goalie stats are correctly extracted."""
        records = transformer.transform_goalie_stats(sample_boxscore, game_id=2023020789)
        home = next(r for r in records if r["player_id"] == 8479320)

        assert home["save_pct"] == pytest.approx(0.957, abs=0.001)
        assert home["decision"] == "W"
        assert home["team_id"] == 6  # BOS
        assert home["minutes_played"] == pytest.approx(60.0, abs=0.01)

    def test_transform_handles_missing_toi(
        self,
        transformer: GameTransformer,
        boxscore_missing_toi: dict[str, Any],
    ) -> None:
        """Boxscore with no toi field → minutes_played defaults to 0.0, no crash."""
        records = transformer.transform_goalie_stats(
            boxscore_missing_toi, game_id=2023020001
        )

        assert len(records) == 1  # only away goalie
        assert records[0]["minutes_played"] == pytest.approx(0.0)

    def test_transform_goalie_stats_empty_goalies(
        self, transformer: GameTransformer
    ) -> None:
        """Boxscore with no goalies on either side → empty list, no crash."""
        boxscore: dict[str, Any] = {
            "id": 2023020001,
            "awayTeam": {"id": 1, "abbrev": "NJD"},
            "homeTeam": {"id": 2, "abbrev": "NYR"},
            "playerByGameStats": {
                "awayTeam": {"goalies": []},
                "homeTeam": {"goalies": []},
            },
        }
        records = transformer.transform_goalie_stats(boxscore, game_id=2023020001)
        assert records == []

    def test_transform_goalie_stats_computes_save_pct_fallback(
        self, transformer: GameTransformer
    ) -> None:
        """If savePctg is absent, save_pct is computed from saves/shotsAgainst."""
        boxscore: dict[str, Any] = {
            "id": 2023020002,
            "awayTeam": {"id": 5, "abbrev": "PIT"},
            "homeTeam": {"id": 3, "abbrev": "CBJ"},
            "playerByGameStats": {
                "awayTeam": {
                    "goalies": [
                        {
                            "playerId": 8471418,
                            # savePctg intentionally omitted
                            "shotsAgainst": 30,
                            "saves": 27,
                            "goalsAgainst": 3,
                            "toi": "58:00",
                        }
                    ]
                },
                "homeTeam": {"goalies": []},
            },
        }
        records = transformer.transform_goalie_stats(boxscore, game_id=2023020002)
        assert len(records) == 1
        # 27 / 30 = 0.9
        assert records[0]["save_pct"] == pytest.approx(0.9, abs=0.001)

    def test_transform_goalie_stats_zero_shots_against(
        self, transformer: GameTransformer
    ) -> None:
        """Zero shots against with no savePctg → save_pct = 0.0 (no division by zero)."""
        boxscore: dict[str, Any] = {
            "id": 2023020003,
            "awayTeam": {"id": 5, "abbrev": "TBL"},
            "homeTeam": {"id": 6, "abbrev": "FLA"},
            "playerByGameStats": {
                "awayTeam": {
                    "goalies": [
                        {
                            "playerId": 9999,
                            "shotsAgainst": 0,
                            "saves": 0,
                            "goalsAgainst": 0,
                            "toi": "00:00",
                        }
                    ]
                },
                "homeTeam": {"goalies": []},
            },
        }
        records = transformer.transform_goalie_stats(boxscore, game_id=2023020003)
        assert records[0]["save_pct"] == pytest.approx(0.0)

    # ------------------------------------------------------------------
    # transform_schedule
    # ------------------------------------------------------------------

    def test_transform_schedule_returns_game_list(
        self, transformer: GameTransformer
    ) -> None:
        """A valid gameWeek schedule → list of normalized game dicts."""
        raw_schedule: dict[str, Any] = {
            "gameWeek": [
                {
                    "date": "2024-01-15",
                    "games": [
                        {
                            "id": 2023020789,
                            "gameType": 2,
                            "season": "20232024",
                            "gameDate": "2024-01-15T00:00:00Z",
                            "gameState": "OFF",
                            "awayTeam": {"id": 10, "abbrev": "TOR", "score": 2},
                            "homeTeam": {"id": 6, "abbrev": "BOS", "score": 3},
                            "venue": {"default": "TD Garden"},
                        },
                        {
                            "id": 2023020790,
                            "gameType": 2,
                            "season": "20232024",
                            "gameDate": "2024-01-15T00:00:00Z",
                            "gameState": "OFF",
                            "awayTeam": {"id": 7, "abbrev": "MTL", "score": 1},
                            "homeTeam": {"id": 8, "abbrev": "OTT", "score": 4},
                            "venue": {"default": "Canadian Tire Centre"},
                        },
                    ],
                }
            ]
        }
        games = transformer.transform_schedule(raw_schedule, date="2024-01-15")

        assert len(games) == 2
        game_ids = {g["nhl_id"] for g in games}
        assert 2023020789 in game_ids
        assert 2023020790 in game_ids

    def test_transform_schedule_flat_games_key(
        self, transformer: GameTransformer
    ) -> None:
        """Schedule response with flat 'games' key (single-day view) is handled."""
        raw_schedule: dict[str, Any] = {
            "games": [
                {
                    "id": 2023020100,
                    "gameType": 2,
                    "season": "20232024",
                    "gameDate": "2024-01-20T00:00:00Z",
                    "gameState": "OFF",
                    "awayTeam": {"id": 4, "abbrev": "CHI", "score": 0},
                    "homeTeam": {"id": 11, "abbrev": "DAL", "score": 3},
                    "venue": {"default": "American Airlines Center"},
                }
            ]
        }
        games = transformer.transform_schedule(raw_schedule, date="2024-01-20")

        assert len(games) == 1
        assert games[0]["nhl_id"] == 2023020100

    def test_transform_schedule_wrong_date_returns_empty(
        self, transformer: GameTransformer
    ) -> None:
        """When the schedule has no games on the requested date → empty list."""
        raw_schedule: dict[str, Any] = {
            "gameWeek": [
                {
                    "date": "2024-01-15",
                    "games": [
                        {
                            "id": 2023020789,
                            "gameType": 2,
                            "season": "20232024",
                            "gameDate": "2024-01-15",
                            "gameState": "OFF",
                            "awayTeam": {"id": 10, "abbrev": "TOR", "score": 2},
                            "homeTeam": {"id": 6, "abbrev": "BOS", "score": 3},
                        }
                    ],
                }
            ]
        }
        games = transformer.transform_schedule(raw_schedule, date="2024-01-16")
        assert games == []

    def test_transform_schedule_empty_response(
        self, transformer: GameTransformer
    ) -> None:
        """Completely empty schedule response → empty list, no crash."""
        games = transformer.transform_schedule({}, date="2024-01-15")
        assert games == []

    # ------------------------------------------------------------------
    # transform_game (single game record)
    # ------------------------------------------------------------------

    def test_transform_game_extracts_core_fields(
        self, transformer: GameTransformer
    ) -> None:
        """transform_game produces a flat record with all expected fields."""
        raw: dict[str, Any] = {
            "id": 2023020789,
            "gameType": 2,
            "season": "20232024",
            "gameDate": "2024-01-15",
            "gameState": "OFF",
            "awayTeam": {"id": 10, "abbrev": "TOR", "score": 2},
            "homeTeam": {"id": 6, "abbrev": "BOS", "score": 3},
            "venue": {"default": "TD Garden"},
            "period": 3,
        }
        game = transformer.transform_game(raw)

        assert game["nhl_id"] == 2023020789
        assert game["season"] == "20232024"
        assert game["game_type"] == 2
        assert game["game_date"] == "2024-01-15"
        assert game["game_state"] == "OFF"
        assert game["away_team_abbrev"] == "TOR"
        assert game["away_score"] == 2
        assert game["home_team_abbrev"] == "BOS"
        assert game["home_score"] == 3
        assert game["venue"] == "TD Garden"

    def test_transform_game_handles_missing_venue(
        self, transformer: GameTransformer
    ) -> None:
        """Missing venue key → venue is None, no crash."""
        raw: dict[str, Any] = {
            "id": 2023020001,
            "awayTeam": {},
            "homeTeam": {},
        }
        game = transformer.transform_game(raw)
        assert game["venue"] is None
