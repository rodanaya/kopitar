"""
Schedule Analyzer Engine

Detects fatigue-relevant NHL schedule patterns such as back-to-back games,
three-in-four nights, and schedule density.  Pure Python + stdlib only.
"""

from __future__ import annotations

from datetime import date, timedelta


class ScheduleAnalyzer:
    """
    Detects fatigue-relevant schedule patterns from a list of game dates.

    All methods are stateless and operate on plain :class:`datetime.date`
    objects, making them easy to test and compose with other engine modules.
    """

    # ------------------------------------------------------------------
    # Pattern detection
    # ------------------------------------------------------------------

    def detect_back_to_back(self, game_dates: list[date]) -> list[date]:
        """
        Return every game date that is part of a back-to-back situation.

        A back-to-back occurs when two games are played on consecutive
        calendar days (gap of exactly 1 day).  Both the first and the
        second game of the pair are included in the returned list so that
        callers can flag either game as risky.

        Parameters
        ----------
        game_dates:
            Unsorted or sorted list of game dates for a single player/team.

        Returns
        -------
        list[date]
            Sorted, de-duplicated list of dates that are back-to-back games.
        """
        if len(game_dates) < 2:
            return []

        sorted_dates = sorted(set(game_dates))
        b2b: set[date] = set()

        for i in range(1, len(sorted_dates)):
            delta = (sorted_dates[i] - sorted_dates[i - 1]).days
            if delta == 1:
                b2b.add(sorted_dates[i - 1])
                b2b.add(sorted_dates[i])

        return sorted(b2b)

    def detect_three_in_four(self, game_dates: list[date]) -> list[date]:
        """
        Return game dates that fall within any window of 3 games in 4 nights.

        A "three-in-four" window is any span of 4 consecutive calendar days
        (inclusive of the start day) that contains at least 3 game dates.

        Parameters
        ----------
        game_dates:
            Unsorted or sorted list of game dates.

        Returns
        -------
        list[date]
            Sorted, de-duplicated list of dates involved in a 3-in-4 window.
        """
        return self._detect_n_in_window(game_dates, n=3, window_days=4)

    def detect_four_in_six(self, game_dates: list[date]) -> list[date]:
        """
        Return game dates that fall within any window of 4 games in 6 nights.

        A "four-in-six" window is any span of 6 consecutive calendar days
        (inclusive of the start day) that contains at least 4 game dates.

        Parameters
        ----------
        game_dates:
            Unsorted or sorted list of game dates.

        Returns
        -------
        list[date]
            Sorted, de-duplicated list of dates involved in a 4-in-6 window.
        """
        return self._detect_n_in_window(game_dates, n=4, window_days=6)

    # ------------------------------------------------------------------
    # Density & spacing metrics
    # ------------------------------------------------------------------

    def calculate_schedule_density(
        self,
        game_dates: list[date],
        window_days: int = 30,
    ) -> float:
        """
        Calculate the games-per-week rate over the *window_days* trailing
        window measured from the most recent game date in the list.

        Parameters
        ----------
        game_dates:
            Unsorted or sorted list of game dates.
        window_days:
            Size of the look-back window in days.  Default 30.

        Returns
        -------
        float
            Games per week rate.  Returns 0.0 if *game_dates* is empty.
        """
        if not game_dates:
            return 0.0

        sorted_dates = sorted(set(game_dates))
        most_recent = sorted_dates[-1]
        cutoff = most_recent - timedelta(days=window_days)

        window_games = [d for d in sorted_dates if d > cutoff]
        if not window_games:
            return 0.0

        weeks = window_days / 7.0
        return round(len(window_games) / weeks, 4)

    def get_rest_days(self, game_dates: list[date]) -> list[int]:
        """
        Return the number of days between each consecutive pair of games.

        The returned list has ``len(unique_game_dates) - 1`` elements (or 0
        if fewer than 2 unique dates are provided).  The first element is the
        gap between the first and second game, and so on.

        Parameters
        ----------
        game_dates:
            Unsorted or sorted list of game dates.

        Returns
        -------
        list[int]
            Days between consecutive games in chronological order.
        """
        sorted_dates = sorted(set(game_dates))
        if len(sorted_dates) < 2:
            return []

        return [
            (sorted_dates[i] - sorted_dates[i - 1]).days
            for i in range(1, len(sorted_dates))
        ]

    # ------------------------------------------------------------------
    # Convenience summary
    # ------------------------------------------------------------------

    def summarise(self, game_dates: list[date]) -> dict[str, object]:
        """
        Return a summary dict of all fatigue-relevant schedule metrics.

        Keys
        ----
        ``total_games``             : int
        ``back_to_back_dates``      : list[date]
        ``three_in_four_dates``     : list[date]
        ``four_in_six_dates``       : list[date]
        ``schedule_density_30d``    : float  (games per week in last 30 days)
        ``rest_days``               : list[int]
        ``avg_rest_days``           : float  (mean days between games, or 0.0)
        ``min_rest_days``           : int    (shortest gap, or 0)
        """
        rest = self.get_rest_days(game_dates)
        return {
            "total_games":          len(game_dates),
            "back_to_back_dates":   self.detect_back_to_back(game_dates),
            "three_in_four_dates":  self.detect_three_in_four(game_dates),
            "four_in_six_dates":    self.detect_four_in_six(game_dates),
            "schedule_density_30d": self.calculate_schedule_density(game_dates),
            "rest_days":            rest,
            "avg_rest_days":        round(sum(rest) / len(rest), 2) if rest else 0.0,
            "min_rest_days":        min(rest) if rest else 0,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_n_in_window(
        self,
        game_dates: list[date],
        n: int,
        window_days: int,
    ) -> list[date]:
        """
        Generic detector: return dates involved in any window of *window_days*
        calendar days that contains at least *n* game dates.

        The window is defined as [anchor, anchor + window_days - 1] inclusive.
        We anchor at each game date and check whether *n* games fall within it.

        Parameters
        ----------
        game_dates:
            List of game dates to examine.
        n:
            Minimum number of games that must appear in the window.
        window_days:
            Width of the window in calendar days (inclusive of the start day).

        Returns
        -------
        list[date]
            Sorted, de-duplicated list of dates inside any qualifying window.
        """
        if len(game_dates) < n:
            return []

        sorted_dates = sorted(set(game_dates))
        flagged: set[date] = set()

        for i, anchor in enumerate(sorted_dates):
            window_end = anchor + timedelta(days=window_days - 1)
            in_window = [d for d in sorted_dates if anchor <= d <= window_end]
            if len(in_window) >= n:
                flagged.update(in_window)

        return sorted(flagged)
