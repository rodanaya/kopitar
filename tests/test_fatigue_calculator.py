"""
Tests for FatigueCalculator

Covers the core business logic of the fatigue engine: workload indexing,
travel indexing, composite scoring, age adjustments, fatigue categories,
and risk-flag generation.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest

from src.kopitar.engine.fatigue_calculator import FatigueCalculator, FatigueResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_game(
    game_date: date,
    minutes_played: float = 60.0,
    shots_faced: int = 28,
    miles_traveled: float = 0.0,
    timezone_change: float = 0.0,
    is_back_to_back: bool = False,
) -> dict[str, Any]:
    """Return a minimal game-history dict."""
    return {
        "game_date": game_date,
        "minutes_played": minutes_played,
        "shots_faced": shots_faced,
        "miles_traveled": miles_traveled,
        "timezone_change": timezone_change,
        "is_back_to_back": is_back_to_back,
    }


# ---------------------------------------------------------------------------
# TestFatigueCalculator
# ---------------------------------------------------------------------------


class TestFatigueCalculator:
    """Unit tests for FatigueCalculator."""

    @pytest.fixture
    def calc(self) -> FatigueCalculator:
        return FatigueCalculator()

    # ------------------------------------------------------------------
    # Fresh / empty history
    # ------------------------------------------------------------------

    def test_fresh_goalie_has_low_fatigue(self, calc: FatigueCalculator) -> None:
        """Player with no history → fatigue index near 0."""
        result = calc.calculate([], as_of_date=date(2024, 1, 15))

        assert result.composite_index == pytest.approx(0.0)
        assert result.workload_index == pytest.approx(0.0)
        assert result.travel_index == pytest.approx(0.0)
        assert result.fatigue_category == "low"

    def test_future_games_not_counted_in_composite(
        self, calc: FatigueCalculator
    ) -> None:
        """A future-dated game (after as_of_date) must not be included in the calculation."""
        as_of = date(2024, 1, 10)
        past_game = _make_game(date(2024, 1, 8))
        future_game = _make_game(date(2024, 1, 15))  # after as_of

        result_past_only = calc.calculate([past_game], as_of_date=as_of)
        result_both = calc.calculate([past_game, future_game], as_of_date=as_of)

        # Including the future game should not change anything
        assert result_past_only.composite_index == pytest.approx(
            result_both.composite_index
        )

    # ------------------------------------------------------------------
    # Back-to-back
    # ------------------------------------------------------------------

    def test_back_to_back_increases_fatigue(self, calc: FatigueCalculator) -> None:
        """B2B game history produces a higher composite index than a rested baseline."""
        as_of = date(2024, 1, 16)

        # Rested baseline: one game 5 days ago
        rested = [_make_game(date(2024, 1, 11))]
        rested_result = calc.calculate(rested, as_of_date=as_of)

        # Back-to-back: games on Jan 15 and Jan 16 (consecutive nights)
        b2b = [
            _make_game(date(2024, 1, 15), is_back_to_back=False),
            _make_game(date(2024, 1, 16), is_back_to_back=True),
        ]
        b2b_result = calc.calculate(b2b, as_of_date=as_of)

        assert b2b_result.composite_index > rested_result.composite_index

    def test_back_to_back_risk_flag_raised(self, calc: FatigueCalculator) -> None:
        """Most-recent game is a B2B → 'back_to_back' appears in risk_flags."""
        as_of = date(2024, 1, 16)
        history = [
            _make_game(date(2024, 1, 15)),
            _make_game(date(2024, 1, 16), is_back_to_back=True),
        ]
        result = calc.calculate(history, as_of_date=as_of)

        assert "back_to_back" in result.risk_flags

    # ------------------------------------------------------------------
    # Travel
    # ------------------------------------------------------------------

    def test_cross_country_travel_adds_fatigue(self, calc: FatigueCalculator) -> None:
        """A 3000-mile trip in the last 5 days raises the travel_index well above 0."""
        as_of = date(2024, 1, 15)
        history = [
            _make_game(
                date(2024, 1, 13),
                miles_traveled=3000.0,
                timezone_change=-3.0,  # westward
            )
        ]
        result = calc.calculate(history, as_of_date=as_of)

        assert result.travel_index > 20.0

    def test_cross_country_travel_risk_flag(self, calc: FatigueCalculator) -> None:
        """More than 2000 miles in 7 days → 'cross_country_travel' flag."""
        as_of = date(2024, 1, 15)
        history = [
            _make_game(date(2024, 1, 12), miles_traveled=1100.0),
            _make_game(date(2024, 1, 14), miles_traveled=1100.0),
        ]
        result = calc.calculate(history, as_of_date=as_of)

        assert "cross_country_travel" in result.risk_flags

    # ------------------------------------------------------------------
    # Eastward penalty
    # ------------------------------------------------------------------

    def test_eastward_penalty_applied(self, calc: FatigueCalculator) -> None:
        """Eastward timezone change should produce a higher travel_index than equivalent westward."""
        as_of = date(2024, 1, 15)
        base_game = {
            "game_date": date(2024, 1, 13),
            "minutes_played": 60.0,
            "shots_faced": 28,
            "miles_traveled": 2500.0,
        }

        # Eastward trip (positive tz_change = moved east → penalty)
        eastward = [{**base_game, "timezone_change": 3.0, "is_back_to_back": False}]
        eastward_result = calc.calculate_travel_index(eastward, window_days=7)

        # Westward trip (negative tz_change = moved west → no penalty)
        westward = [{**base_game, "timezone_change": -3.0, "is_back_to_back": False}]
        westward_result = calc.calculate_travel_index(westward, window_days=7)

        assert eastward_result > westward_result

    # ------------------------------------------------------------------
    # Composite cap
    # ------------------------------------------------------------------

    def test_fatigue_capped_at_100(self, calc: FatigueCalculator) -> None:
        """Extreme workload and travel scenario → composite_index <= 100."""
        as_of = date(2024, 1, 10)
        # Build a maximally loaded history: 5 games in 7 days, all B2B,
        # heavy travel, eastward timezone changes, maximum shots
        history = [
            _make_game(
                as_of - timedelta(days=i),
                minutes_played=65.0,
                shots_faced=50,
                miles_traveled=3000.0,
                timezone_change=3.0,  # eastward
                is_back_to_back=True,
            )
            for i in range(5)
        ]
        result = calc.calculate(history, as_of_date=as_of)

        assert result.composite_index <= 100.0
        assert result.workload_index <= 100.0
        assert result.travel_index <= 100.0

    # ------------------------------------------------------------------
    # Age adjustment
    # ------------------------------------------------------------------

    def test_age_adjustment_increases_recovery(self, calc: FatigueCalculator) -> None:
        """A 35-year-old with the same workload needs more recovery hours than a 25-year-old."""
        as_of = date(2024, 1, 15)
        history = [
            _make_game(date(2024, 1, 13)),
            _make_game(date(2024, 1, 14), is_back_to_back=True),
        ]

        young_result = calc.calculate(history, as_of_date=as_of, player_age=25.0)
        veteran_result = calc.calculate(history, as_of_date=as_of, player_age=35.0)

        assert veteran_result.recovery_hours_needed > young_result.recovery_hours_needed

    def test_age_risk_flag_at_threshold(self, calc: FatigueCalculator) -> None:
        """Player at or above the age threshold (default 30) → 'age_recovery_risk' flag."""
        as_of = date(2024, 1, 15)
        history = [_make_game(date(2024, 1, 14))]

        result_young = calc.calculate(history, as_of_date=as_of, player_age=29.0)
        result_old = calc.calculate(history, as_of_date=as_of, player_age=31.0)

        assert "age_recovery_risk" not in result_young.risk_flags
        assert "age_recovery_risk" in result_old.risk_flags

    # ------------------------------------------------------------------
    # Fatigue categories
    # ------------------------------------------------------------------

    def test_fatigue_category_low(self, calc: FatigueCalculator) -> None:
        """Empty history → category 'low'."""
        result = calc.calculate([], as_of_date=date(2024, 1, 15))
        assert result.fatigue_category == "low"

    def test_fatigue_category_boundaries(self, calc: FatigueCalculator) -> None:
        """All five categories can be reached with appropriate composite indices."""
        from src.kopitar.engine.fatigue_calculator import _categorise

        assert _categorise(0.0) == "low"
        assert _categorise(19.9) == "low"
        assert _categorise(20.0) == "moderate"
        assert _categorise(39.9) == "moderate"
        assert _categorise(40.0) == "high"
        assert _categorise(59.9) == "high"
        assert _categorise(60.0) == "very_high"
        assert _categorise(79.9) == "very_high"
        assert _categorise(80.0) == "extreme"
        assert _categorise(100.0) == "extreme"

    # ------------------------------------------------------------------
    # Workload index
    # ------------------------------------------------------------------

    def test_workload_index_increases_with_game_load(
        self, calc: FatigueCalculator
    ) -> None:
        """More games in the window → higher workload index."""
        base = date(2024, 1, 15)
        one_game = [_make_game(base - timedelta(days=1))]
        four_games = [_make_game(base - timedelta(days=i)) for i in range(1, 5)]

        low_wl = calc.calculate_workload_index(one_game, window_days=10)
        high_wl = calc.calculate_workload_index(four_games, window_days=10)

        assert high_wl > low_wl

    def test_workload_index_empty_history(self, calc: FatigueCalculator) -> None:
        """No games → workload index is 0."""
        assert calc.calculate_workload_index([]) == pytest.approx(0.0)

    # ------------------------------------------------------------------
    # FatigueResult structure
    # ------------------------------------------------------------------

    def test_result_contains_expected_keys(self, calc: FatigueCalculator) -> None:
        """FatigueResult has all required fields populated."""
        result = calc.calculate(
            [_make_game(date(2024, 1, 14))],
            as_of_date=date(2024, 1, 15),
        )

        assert isinstance(result, FatigueResult)
        assert isinstance(result.breakdown, dict)
        assert isinstance(result.risk_flags, list)
        assert isinstance(result.recovery_hours_needed, float)
        assert result.as_of_date == date(2024, 1, 15)

        expected_breakdown_keys = {
            "games_last_7d",
            "minutes_last_10d",
            "miles_last_5d",
            "timezone_changes",
            "consecutive_games",
            "shot_volume",
        }
        assert set(result.breakdown.keys()) == expected_breakdown_keys

    def test_future_games_excluded(self, calc: FatigueCalculator) -> None:
        """Games after as_of_date must not affect the calculation."""
        as_of = date(2024, 1, 10)
        history = [
            _make_game(date(2024, 1, 8)),   # included
            _make_game(date(2024, 1, 15)),  # in the future → excluded
        ]
        result_with_future = calc.calculate(history, as_of_date=as_of)
        result_without = calc.calculate([history[0]], as_of_date=as_of)

        assert result_with_future.composite_index == pytest.approx(
            result_without.composite_index
        )
