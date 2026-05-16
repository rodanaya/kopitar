"""
Tests for ScheduleAnalyzer

Verifies back-to-back detection, three-in-four / four-in-six pattern
detection, schedule density calculation, and rest-day computation.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.kopitar.engine.schedule_analyzer import ScheduleAnalyzer


class TestScheduleAnalyzer:
    """Unit tests for ScheduleAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> ScheduleAnalyzer:
        return ScheduleAnalyzer()

    # ------------------------------------------------------------------
    # Back-to-back detection
    # ------------------------------------------------------------------

    def test_back_to_back_detection(self, analyzer: ScheduleAnalyzer) -> None:
        """Jan 15 and Jan 16 → both dates are flagged as back-to-back."""
        dates = [date(2024, 1, 15), date(2024, 1, 16)]
        b2b = analyzer.detect_back_to_back(dates)

        assert date(2024, 1, 15) in b2b
        assert date(2024, 1, 16) in b2b

    def test_not_back_to_back_with_day_off(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """Jan 15 and Jan 17 (one day off in between) → no back-to-back."""
        dates = [date(2024, 1, 15), date(2024, 1, 17)]
        b2b = analyzer.detect_back_to_back(dates)

        assert b2b == []

    def test_back_to_back_only_marks_consecutive_pair(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """[Jan 1, Jan 3, Jan 4] → only Jan 3 and Jan 4 are flagged."""
        dates = [date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 4)]
        b2b = analyzer.detect_back_to_back(dates)

        assert date(2024, 1, 1) not in b2b
        assert date(2024, 1, 3) in b2b
        assert date(2024, 1, 4) in b2b

    def test_back_to_back_single_game_no_flags(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """A single game date cannot form a back-to-back."""
        assert analyzer.detect_back_to_back([date(2024, 1, 15)]) == []

    def test_back_to_back_empty_list(self, analyzer: ScheduleAnalyzer) -> None:
        """Empty input → empty result."""
        assert analyzer.detect_back_to_back([]) == []

    def test_back_to_back_result_is_sorted(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """Returned dates are in ascending chronological order."""
        dates = [date(2024, 1, 16), date(2024, 1, 15)]  # unsorted input
        b2b = analyzer.detect_back_to_back(dates)

        assert b2b == sorted(b2b)

    # ------------------------------------------------------------------
    # Three-in-four detection
    # ------------------------------------------------------------------

    def test_three_in_four_detection(self, analyzer: ScheduleAnalyzer) -> None:
        """Jan 15, 16, 18 — three games in the Jan 15-18 window → three_in_four."""
        dates = [date(2024, 1, 15), date(2024, 1, 16), date(2024, 1, 18)]
        result = analyzer.detect_three_in_four(dates)

        assert len(result) >= 3
        for d in dates:
            assert d in result

    def test_not_three_in_four_with_spread_games(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """Jan 1, Jan 5, Jan 9 — each 4 days apart → no three-in-four window."""
        dates = [date(2024, 1, 1), date(2024, 1, 5), date(2024, 1, 9)]
        result = analyzer.detect_three_in_four(dates)

        assert result == []

    def test_three_in_four_empty_list(self, analyzer: ScheduleAnalyzer) -> None:
        """Empty input → empty result."""
        assert analyzer.detect_three_in_four([]) == []

    def test_three_in_four_two_games(self, analyzer: ScheduleAnalyzer) -> None:
        """Only two games → cannot form a three-in-four."""
        dates = [date(2024, 1, 15), date(2024, 1, 16)]
        assert analyzer.detect_three_in_four(dates) == []

    # ------------------------------------------------------------------
    # Four-in-six detection
    # ------------------------------------------------------------------

    def test_four_in_six_detection(self, analyzer: ScheduleAnalyzer) -> None:
        """Jan 1, 2, 4, 6 — four games within a 6-night window → four_in_six."""
        dates = [
            date(2024, 1, 1),
            date(2024, 1, 2),
            date(2024, 1, 4),
            date(2024, 1, 6),
        ]
        result = analyzer.detect_four_in_six(dates)

        assert len(result) >= 4

    def test_not_four_in_six_with_spread_games(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """Jan 1, 7, 13, 19 — each 6 days apart → no four-in-six window."""
        dates = [
            date(2024, 1, 1),
            date(2024, 1, 7),
            date(2024, 1, 13),
            date(2024, 1, 19),
        ]
        result = analyzer.detect_four_in_six(dates)

        assert result == []

    # ------------------------------------------------------------------
    # Schedule density
    # ------------------------------------------------------------------

    def test_schedule_density_basic(self, analyzer: ScheduleAnalyzer) -> None:
        """15 games spread over 30 days → 15 / (30/7) = 3.5 games/week."""
        from datetime import timedelta

        base = date(2024, 1, 30)
        # 15 games spaced 2 days apart (0, 2, 4, … 28 days ago)
        dates = [base - timedelta(days=i * 2) for i in range(15)]
        density = analyzer.calculate_schedule_density(dates, window_days=30)

        assert density == pytest.approx(3.5, rel=0.05)

    def test_schedule_density_empty_list(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """Empty input → 0.0 density."""
        assert analyzer.calculate_schedule_density([]) == pytest.approx(0.0)

    def test_schedule_density_single_game(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """A single game in the window → density > 0."""
        density = analyzer.calculate_schedule_density(
            [date(2024, 1, 15)], window_days=30
        )
        assert density > 0.0

    def test_schedule_density_window_respected(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """Games outside the window should not be counted."""
        from datetime import timedelta

        base = date(2024, 1, 30)
        # 3 games in the last 7 days; 10 games 60+ days ago (outside window)
        recent = [base - timedelta(days=i) for i in range(1, 4)]
        old = [base - timedelta(days=60 + i) for i in range(10)]

        density_with_old = analyzer.calculate_schedule_density(
            recent + old, window_days=30
        )
        density_recent_only = analyzer.calculate_schedule_density(
            recent, window_days=30
        )

        assert density_with_old == pytest.approx(density_recent_only, rel=0.01)

    # ------------------------------------------------------------------
    # Rest days
    # ------------------------------------------------------------------

    def test_rest_days_calculation(self, analyzer: ScheduleAnalyzer) -> None:
        """[Jan 1, Jan 3, Jan 6] → gaps of 2 and 3 days."""
        dates = [date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 6)]
        rest = analyzer.get_rest_days(dates)

        assert rest == [2, 3]

    def test_rest_days_back_to_back(self, analyzer: ScheduleAnalyzer) -> None:
        """[Jan 14, Jan 15] → gap of 1 day (back-to-back)."""
        rest = analyzer.get_rest_days([date(2024, 1, 14), date(2024, 1, 15)])
        assert rest == [1]

    def test_rest_days_single_game(self, analyzer: ScheduleAnalyzer) -> None:
        """Single game → empty list (no gaps)."""
        assert analyzer.get_rest_days([date(2024, 1, 15)]) == []

    def test_rest_days_empty_list(self, analyzer: ScheduleAnalyzer) -> None:
        """Empty input → empty list."""
        assert analyzer.get_rest_days([]) == []

    def test_rest_days_deduplicates_dates(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """Duplicate dates are collapsed before calculating gaps."""
        dates = [date(2024, 1, 1), date(2024, 1, 1), date(2024, 1, 3)]
        rest = analyzer.get_rest_days(dates)

        # Unique dates: Jan 1, Jan 3 → single gap of 2
        assert rest == [2]

    # ------------------------------------------------------------------
    # summarise() helper
    # ------------------------------------------------------------------

    def test_summarise_contains_all_keys(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """summarise() returns a dict with all documented keys."""
        dates = [
            date(2024, 1, 1),
            date(2024, 1, 3),
            date(2024, 1, 5),
        ]
        summary = analyzer.summarise(dates)

        expected_keys = {
            "total_games",
            "back_to_back_dates",
            "three_in_four_dates",
            "four_in_six_dates",
            "schedule_density_30d",
            "rest_days",
            "avg_rest_days",
            "min_rest_days",
        }
        assert set(summary.keys()) == expected_keys

    def test_summarise_total_games_count(
        self, analyzer: ScheduleAnalyzer
    ) -> None:
        """total_games reflects the raw count (including duplicates)."""
        dates = [date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 5)]
        summary = analyzer.summarise(dates)
        assert summary["total_games"] == 3
