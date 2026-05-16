"""
Fatigue Transformer

Pure dict→dict helper that converts raw game and travel history into
``PlayerFatigueMetrics``-compatible records.

No database dependencies — callers are responsible for persisting the
returned dicts.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_FATIGUE_WEIGHTS = {
    "games_last_7d": 10.0,
    "minutes_last_10d": 0.05,   # per minute
    "travel_miles_last_5d": 0.005,  # per mile
    "timezone_changes": 5.0,
    "consecutive_games": 8.0,
    "shot_volume": 0.15,        # per shot (goalie-specific)
}


def _parse_date(value: Any) -> Optional[datetime]:
    """Convert a date string or datetime to a datetime object."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def _toi_to_minutes(toi: Any) -> float:
    """
    Convert a time-on-ice value to minutes.

    Accepts:
    - float/int already in minutes
    - "MM:SS" string
    """
    if toi is None:
        return 0.0
    if isinstance(toi, (int, float)):
        return float(toi)
    if isinstance(toi, str):
        parts = toi.split(":")
        try:
            minutes = int(parts[0])
            seconds = int(parts[1]) if len(parts) > 1 else 0
            return round(minutes + seconds / 60.0, 4)
        except (ValueError, IndexError):
            logger.warning("Could not parse toi: %r", toi)
    return 0.0


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class FatigueTransformer:
    """
    Builds ``PlayerFatigueMetrics``-compatible dicts from raw history data.

    All methods are stateless and have no database dependencies.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_fatigue_record(
        self,
        player_id: int,
        game_id: int,
        game_date: str,
        game_history: list[dict[str, Any]],
        travel_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Build a ``PlayerFatigueMetrics``-compatible dict for a single
        player/game combination.

        Args:
            player_id: NHL player ID.
            game_id: Internal game ID for the game being assessed.
            game_date: Date of the game (``YYYY-MM-DD``).
            game_history: List of previous game dicts for this player.
                Each dict should contain at least:
                  - ``game_date`` (str, ``YYYY-MM-DD``)
                  - ``minutes_played`` (float or "MM:SS")
                  - ``shots_against`` (int, goalies only)
                  - ``team_id`` (int)
            travel_history: List of travel leg dicts for this player's team.
                Each dict should contain at least:
                  - ``departure_date`` (str, ``YYYY-MM-DD``)
                  - ``distance_miles`` (float)
                  - ``timezone_change_hours`` (float)
                  - ``eastward_travel`` (bool)

        Returns:
            dict: All columns of ``PlayerFatigueMetrics`` populated from
                  the supplied history.  team_id is taken from the most
                  recent game in history (or 0 if history is empty).
        """
        game_dt = _parse_date(game_date)
        if game_dt is None:
            raise ValueError(f"Cannot parse game_date: {game_date!r}")

        # Sort histories chronologically (oldest first)
        sorted_games = sorted(
            game_history,
            key=lambda g: _parse_date(g.get("game_date")) or datetime.min,
        )
        sorted_travel = sorted(
            travel_history,
            key=lambda t: _parse_date(t.get("departure_date")) or datetime.min,
        )

        # --- Team context ---
        team_id: int = (
            sorted_games[-1].get("team_id", 0) if sorted_games else 0
        )

        # --- Trailing workload stats ---
        stats_7 = self.calculate_trailing_stats(sorted_games, window_days=7, anchor=game_dt)
        stats_10 = self.calculate_trailing_stats(sorted_games, window_days=10, anchor=game_dt)
        stats_14 = self.calculate_trailing_stats(sorted_games, window_days=14, anchor=game_dt)
        stats_30 = self.calculate_trailing_stats(sorted_games, window_days=30, anchor=game_dt)
        stats_3g = self._last_n_games_stats(sorted_games, n=3, anchor=game_dt)

        # --- Rest / recovery ---
        days_since_last = self._days_since_last_game(sorted_games, game_dt)
        consecutive = self._consecutive_games(sorted_games, game_dt)
        back_to_backs_14 = self._count_back_to_backs(sorted_games, window_days=14, anchor=game_dt)

        # --- Schedule density ---
        three_in_four = self._has_three_in_four(sorted_games, game_dt)
        four_in_six = self._has_four_in_six(sorted_games, game_dt)

        # --- Travel factors ---
        travel_7 = self._travel_stats(sorted_travel, window_days=7, anchor=game_dt)
        travel_14 = self._travel_stats(sorted_travel, window_days=14, anchor=game_dt)

        # --- Back-to-back for team ---
        team_b2b = back_to_backs_14 > 0 and days_since_last <= 1.0

        # --- Road / home stand number ---
        road_trip_num, home_stand_num = self._stand_numbers(sorted_games, game_dt)

        # --- Fatigue indices ---
        base_fi = self._calc_base_fatigue(
            games_last_7=stats_7["games"],
            minutes_last_10=stats_10["minutes"],
            consecutive_games=consecutive,
        )
        travel_fi = self._calc_travel_fatigue(travel_7)
        workload_fi = self._calc_workload_fatigue(
            shots_last_3=stats_3g.get("shots_against", 0),
            back_to_backs=back_to_backs_14,
            three_in_four=three_in_four,
        )
        composite_fi = min(100.0, round(base_fi + travel_fi + workload_fi, 2))

        return {
            # Identity
            "player_id": player_id,
            "game_id": game_id,
            "team_id": team_id,
            "calculation_date": game_dt,
            # Workload (trailing windows)
            "games_last_7_days": stats_7["games"],
            "games_last_14_days": stats_14["games"],
            "games_last_30_days": stats_30["games"],
            # Time on ice (seconds for DB compat)
            "toi_last_3_games": int(stats_3g.get("minutes", 0.0) * 60),
            "toi_last_7_days": int(stats_7["minutes"] * 60),
            "toi_last_14_days": int(stats_14["minutes"] * 60),
            # Rest
            "days_since_last_game": days_since_last,
            "consecutive_games": consecutive,
            "back_to_back_games": back_to_backs_14,
            # Travel
            "miles_traveled_last_7_days": travel_7["miles"],
            "miles_traveled_last_14_days": travel_14["miles"],
            "timezone_changes_last_7_days": travel_7["tz_changes"],
            "eastward_travel_hours": travel_7["eastward_hours"],
            # Schedule density
            "three_in_four_nights": three_in_four,
            "four_in_six_nights": four_in_six,
            "games_in_last_10_days": stats_10["games"],
            # Goalie-specific performance context
            "shots_faced_last_3_games": stats_3g.get("shots_against"),
            "high_danger_shots_last_3_games": stats_3g.get("high_danger_shots"),
            "save_attempts_last_3_games": stats_3g.get("saves"),
            # Age / experience — left None; caller should enrich
            "player_age_at_game": None,
            "nhl_experience_years": None,
            # Injury / health — left None; caller enriches
            "injury_report_status": None,
            "missed_practice_last_week": False,
            # Fatigue indices
            "base_fatigue_index": round(base_fi, 2),
            "travel_fatigue_index": round(travel_fi, 2),
            "workload_fatigue_index": round(workload_fi, 2),
            "composite_fatigue_index": composite_fi,
            # Position adjustments — caller sets for non-goalies
            "position_adjustment": 1.0,
            "goalie_workload_multiplier": self._goalie_multiplier(stats_3g),
            # Team context
            "team_back_to_back": team_b2b,
            "home_stand_game_number": home_stand_num,
            "road_trip_game_number": road_trip_num,
            # Environmental — left None; caller enriches
            "altitude_change": None,
            "temperature_change": None,
            # Model predictions — populated by ML pipeline
            "predicted_performance_drop": None,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
        }

    def calculate_trailing_stats(
        self,
        game_history: list[dict[str, Any]],
        window_days: int,
        anchor: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Aggregate game stats that fall within a trailing window.

        Args:
            game_history: Chronologically sorted list of past game dicts.
                Each dict may contain: ``game_date``, ``minutes_played``,
                ``shots_against``, ``saves``, ``high_danger_shots``.
            window_days: How many days before ``anchor`` to look back.
            anchor: End of the window (exclusive).  Defaults to ``datetime.utcnow()``.

        Returns:
            dict with keys:
              - ``games`` (int): number of games in window
              - ``minutes`` (float): total TOI in minutes
              - ``shots_against`` (int): total shots faced (goalies)
              - ``saves`` (int): total saves
              - ``high_danger_shots`` (int): total high-danger shots
        """
        if anchor is None:
            anchor = datetime.utcnow()

        cutoff = anchor - timedelta(days=window_days)

        total_games = 0
        total_minutes = 0.0
        total_shots = 0
        total_saves = 0
        total_hd_shots = 0

        for game in game_history:
            gdt = _parse_date(game.get("game_date"))
            if gdt is None:
                continue
            if not (cutoff <= gdt < anchor):
                continue

            total_games += 1
            total_minutes += _toi_to_minutes(game.get("minutes_played"))
            total_shots += int(game.get("shots_against", 0) or 0)
            total_saves += int(game.get("saves", 0) or 0)
            total_hd_shots += int(game.get("high_danger_shots", 0) or 0)

        return {
            "games": total_games,
            "minutes": round(total_minutes, 2),
            "shots_against": total_shots,
            "saves": total_saves,
            "high_danger_shots": total_hd_shots,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _last_n_games_stats(
        self,
        sorted_games: list[dict[str, Any]],
        n: int,
        anchor: datetime,
    ) -> dict[str, Any]:
        """Return aggregate stats for the last *n* games before *anchor*."""
        past = [
            g for g in sorted_games
            if (_parse_date(g.get("game_date")) or datetime.min) < anchor
        ]
        last_n = past[-n:] if len(past) >= n else past

        total_minutes = sum(_toi_to_minutes(g.get("minutes_played")) for g in last_n)
        total_shots = sum(int(g.get("shots_against", 0) or 0) for g in last_n)
        total_saves = sum(int(g.get("saves", 0) or 0) for g in last_n)
        total_hd = sum(int(g.get("high_danger_shots", 0) or 0) for g in last_n)

        return {
            "games": len(last_n),
            "minutes": round(total_minutes, 2),
            "shots_against": total_shots if last_n else None,
            "saves": total_saves if last_n else None,
            "high_danger_shots": total_hd if last_n else None,
        }

    def _days_since_last_game(
        self,
        sorted_games: list[dict[str, Any]],
        anchor: datetime,
    ) -> float:
        """Days elapsed since the most recent game before *anchor*."""
        past = [
            _parse_date(g.get("game_date"))
            for g in sorted_games
            if _parse_date(g.get("game_date")) is not None
            and _parse_date(g.get("game_date")) < anchor
        ]
        if not past:
            return 99.0  # No prior game data — treat as fully rested
        last_dt = max(past)
        delta = anchor - last_dt
        return round(delta.total_seconds() / 86400.0, 2)

    def _consecutive_games(
        self,
        sorted_games: list[dict[str, Any]],
        anchor: datetime,
    ) -> int:
        """
        Count the number of consecutive days-in-a-row games ending at *anchor*
        (i.e. the current streak of back-to-back-to-back… games).
        """
        past_dates = sorted(
            [
                _parse_date(g.get("game_date"))
                for g in sorted_games
                if _parse_date(g.get("game_date")) is not None
                and _parse_date(g.get("game_date")) < anchor
            ],
            reverse=True,
        )

        streak = 0
        expected = anchor - timedelta(days=1)
        for gdt in past_dates:
            # Allow same-day or one-day-prior match
            diff = (expected - gdt).days
            if 0 <= diff <= 1:
                streak += 1
                expected = gdt - timedelta(days=1)
            else:
                break
        return streak

    def _count_back_to_backs(
        self,
        sorted_games: list[dict[str, Any]],
        window_days: int,
        anchor: datetime,
    ) -> int:
        """Count B2B game pairs within the trailing window."""
        cutoff = anchor - timedelta(days=window_days)
        dates = sorted(
            [
                _parse_date(g.get("game_date"))
                for g in sorted_games
                if _parse_date(g.get("game_date")) is not None
                and cutoff <= (_parse_date(g.get("game_date")) or datetime.min) < anchor
            ]
        )

        b2b_count = 0
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                b2b_count += 1
        return b2b_count

    def _has_three_in_four(
        self,
        sorted_games: list[dict[str, Any]],
        anchor: datetime,
    ) -> bool:
        """Return True if the player played (or will play) 3 games in 4 nights."""
        window_start = anchor - timedelta(days=3)
        window_dates = [
            _parse_date(g.get("game_date"))
            for g in sorted_games
            if _parse_date(g.get("game_date")) is not None
            and window_start <= (_parse_date(g.get("game_date")) or datetime.min) <= anchor
        ]
        return len(window_dates) >= 3

    def _has_four_in_six(
        self,
        sorted_games: list[dict[str, Any]],
        anchor: datetime,
    ) -> bool:
        """Return True if the player played (or will play) 4 games in 6 nights."""
        window_start = anchor - timedelta(days=5)
        window_dates = [
            _parse_date(g.get("game_date"))
            for g in sorted_games
            if _parse_date(g.get("game_date")) is not None
            and window_start <= (_parse_date(g.get("game_date")) or datetime.min) <= anchor
        ]
        return len(window_dates) >= 4

    def _travel_stats(
        self,
        sorted_travel: list[dict[str, Any]],
        window_days: int,
        anchor: datetime,
    ) -> dict[str, Any]:
        """Aggregate travel metrics within the trailing window."""
        cutoff = anchor - timedelta(days=window_days)
        total_miles = 0.0
        tz_changes = 0
        eastward_hours = 0.0

        for leg in sorted_travel:
            dep_dt = _parse_date(leg.get("departure_date"))
            if dep_dt is None:
                continue
            if not (cutoff <= dep_dt < anchor):
                continue

            total_miles += float(leg.get("distance_miles", 0.0) or 0.0)
            tz_abs = abs(float(leg.get("timezone_change_hours", 0.0) or 0.0))
            if tz_abs >= 1.0:
                tz_changes += 1
            if leg.get("eastward_travel"):
                eastward_hours += tz_abs

        return {
            "miles": round(total_miles, 1),
            "tz_changes": tz_changes,
            "eastward_hours": round(eastward_hours, 2),
        }

    def _stand_numbers(
        self,
        sorted_games: list[dict[str, Any]],
        anchor: datetime,
    ) -> tuple[Optional[int], Optional[int]]:
        """
        Return (road_trip_game_number, home_stand_game_number) for the game
        on *anchor*.

        Uses ``is_home`` field on game dicts (bool).  If not present, returns
        (None, None).
        """
        past = [
            g for g in sorted_games
            if _parse_date(g.get("game_date")) is not None
            and _parse_date(g.get("game_date")) < anchor
            and "is_home" in g
        ]
        if not past:
            return None, None

        last_type: Optional[bool] = past[-1].get("is_home")
        streak = 1
        for g in reversed(past[:-1]):
            if g.get("is_home") == last_type:
                streak += 1
            else:
                break

        if last_type is True:
            return None, streak
        elif last_type is False:
            return streak, None
        return None, None

    # ------------------------------------------------------------------
    # Fatigue index calculations
    # ------------------------------------------------------------------

    def _calc_base_fatigue(
        self,
        games_last_7: int,
        minutes_last_10: float,
        consecutive_games: int,
    ) -> float:
        """Workload component of the fatigue index (0–100)."""
        score = (
            _FATIGUE_WEIGHTS["games_last_7d"] * games_last_7
            + _FATIGUE_WEIGHTS["minutes_last_10d"] * minutes_last_10
            + _FATIGUE_WEIGHTS["consecutive_games"] * consecutive_games
        )
        return min(50.0, round(score, 2))

    def _calc_travel_fatigue(self, travel_stats: dict[str, Any]) -> float:
        """Travel component of the fatigue index (0–30)."""
        score = (
            _FATIGUE_WEIGHTS["travel_miles_last_5d"] * travel_stats["miles"]
            + _FATIGUE_WEIGHTS["timezone_changes"] * travel_stats["tz_changes"]
            # Eastward travel penalised 1.5x per the domain model
            + _FATIGUE_WEIGHTS["timezone_changes"] * travel_stats["eastward_hours"] * 0.5
        )
        return min(30.0, round(score, 2))

    def _calc_workload_fatigue(
        self,
        shots_last_3: Optional[int],
        back_to_backs: int,
        three_in_four: bool,
    ) -> float:
        """Goalie-workload and schedule-density component (0–20)."""
        score = 0.0
        if shots_last_3:
            score += _FATIGUE_WEIGHTS["shot_volume"] * shots_last_3
        score += back_to_backs * 3.0
        if three_in_four:
            score += 5.0
        return min(20.0, round(score, 2))

    def _goalie_multiplier(self, stats_3g: dict[str, Any]) -> Optional[float]:
        """
        Derive a goalie workload multiplier from recent shot volume.

        Returns None if no shot data available (skaters).
        The multiplier scales linearly: 1.0 at 0 shots → 1.5 at 150 shots.
        """
        shots = stats_3g.get("shots_against")
        if shots is None:
            return None
        return round(1.0 + min(shots / 300.0, 0.5), 3)
