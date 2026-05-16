"""
Fatigue Calculator Engine

Calculates composite fatigue indices for NHL goaltenders from raw game and
travel history data.  All logic is pure Python + stdlib only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class FatigueResult:
    """Holds the full output of a fatigue calculation."""

    composite_index: float        # 0-100 overall fatigue score
    workload_index: float         # 0-100 workload sub-score
    travel_index: float           # 0-100 travel sub-score
    schedule_density_index: float # 0-100 schedule density sub-score
    breakdown: dict[str, float]   # per-component raw scores before weighting
    fatigue_category: str         # "low"/"moderate"/"high"/"very_high"/"extreme"
    risk_flags: list[str]         # list of active risk flag strings
    recovery_hours_needed: float  # estimated recovery hours required
    as_of_date: date              # date for which this result was computed


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

# Expected "normal" upper-bounds used for normalisation to a 0-100 scale.
_MAX_GAMES_7D: int = 5          # ≥5 games in 7 days → max workload
_MAX_MINUTES_10D: float = 600.0 # ≥600 mins in 10 days → max (≈10×60 min games)
_MAX_MILES_5D: float = 8000.0   # ≥8 000 miles in 5 days → max travel
_MAX_TZ_CHANGES: int = 6        # ≥6 timezone change-hours → max
_MAX_CONSECUTIVE: int = 10      # ≥10 consecutive games → max
_MAX_SHOTS_3G: int = 150        # ≥150 shots faced across last 3 games → max


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* to [lo, hi]."""
    return max(lo, min(hi, value))


def _norm(value: float, maximum: float) -> float:
    """Normalise *value* against *maximum*, returning a 0-1 ratio."""
    if maximum <= 0:
        return 0.0
    return min(1.0, value / maximum)


# ---------------------------------------------------------------------------
# Main calculator
# ---------------------------------------------------------------------------

class FatigueCalculator:
    """
    Calculates composite fatigue indices from player workload and travel history.

    Formula weights (calibrated via regression):
      w1=15  (games last 7 days)
      w2=10  (minutes last 10 days, normalised)
      w3=8   (miles last 5 days, normalised)
      w4=12  (timezone changes / hours)
      w5=20  (consecutive games, normalised)
      w6=5   (shot volume, normalised)

    Each component is first normalised to [0, 1] before the weight is applied,
    so the raw composite index lives on [0, ~70].  It is then scaled to [0, 100]
    by dividing by the sum of all weights (70) and multiplying by 100.

    Parameters
    ----------
    age_recovery_threshold : float
        Player age above which the age-recovery risk flag is raised (default 30).
    """

    # Weight vector – order must match _compute_raw_components
    _WEIGHTS: dict[str, float] = {
        "games_last_7d":      15.0,
        "minutes_last_10d":   10.0,
        "miles_last_5d":       8.0,
        "timezone_changes":   12.0,
        "consecutive_games":  20.0,
        "shot_volume":         5.0,
    }
    _WEIGHT_SUM: float = sum(_WEIGHTS.values())  # 70.0

    def __init__(self, age_recovery_threshold: float = 30.0) -> None:
        self.age_recovery_threshold = age_recovery_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(
        self,
        player_history: list[dict[str, Any]],
        as_of_date: date,
        player_age: float | None = None,
    ) -> FatigueResult:
        """
        Compute a full FatigueResult for a player as of *as_of_date*.

        Parameters
        ----------
        player_history:
            List of game-event dicts, each containing:
              - game_date          : date
              - minutes_played     : float  (minutes on ice)
              - shots_faced        : int    (shots faced in game)
              - miles_traveled     : float  (miles traveled *to* this game)
              - timezone_change    : float  (timezone hours changed for this trip)
              - is_back_to_back    : bool
        as_of_date:
            The reference date.  Only history *before or on* this date is used.
        player_age:
            Optional player age in years; used for risk-flag evaluation and
            recovery-time adjustment.

        Returns
        -------
        FatigueResult
        """
        # Filter to history on or before as_of_date
        history = [
            g for g in player_history
            if _to_date(g["game_date"]) <= as_of_date
        ]

        workload_idx = self.calculate_workload_index(history, window_days=10)
        travel_idx = self.calculate_travel_index(history, window_days=7)
        schedule_idx = self._calculate_schedule_density_index(history, as_of_date)

        breakdown = self._compute_raw_components(history, as_of_date)
        composite = self._compute_composite(breakdown)

        category = _categorise(composite)
        recovery_hours = self._estimate_recovery(composite, player_age)

        result = FatigueResult(
            composite_index=round(composite, 2),
            workload_index=round(workload_idx, 2),
            travel_index=round(travel_idx, 2),
            schedule_density_index=round(schedule_idx, 2),
            breakdown={k: round(v, 4) for k, v in breakdown.items()},
            fatigue_category=category,
            risk_flags=[],
            recovery_hours_needed=round(recovery_hours, 1),
            as_of_date=as_of_date,
        )
        result.risk_flags = self.get_risk_flags(result, player_age or 0.0, history)
        return result

    def calculate_workload_index(
        self,
        games: list[dict[str, Any]],
        window_days: int = 10,
    ) -> float:
        """
        Compute a 0-100 workload score based on game frequency and ice time
        within the trailing *window_days* window.

        Parameters
        ----------
        games:
            List of game dicts (see :meth:`calculate` for keys).
        window_days:
            Look-back window in days from the most recent game date.

        Returns
        -------
        float
            Workload index in [0, 100].
        """
        if not games:
            return 0.0

        cutoff = _most_recent_date(games) - timedelta(days=window_days)
        window_games = [g for g in games if _to_date(g["game_date"]) > cutoff]

        if not window_games:
            return 0.0

        game_count = len(window_games)
        total_minutes = sum(float(g.get("minutes_played", 0)) for g in window_games)

        # Normalise each factor to [0, 1] and weight
        game_factor = _norm(game_count, _MAX_GAMES_7D)
        minute_factor = _norm(total_minutes, _MAX_MINUTES_10D)

        # Simple weighted average: games factor weighted more heavily
        raw = (game_factor * 0.6 + minute_factor * 0.4)
        return _clamp(raw * 100.0)

    def calculate_travel_index(
        self,
        travel_logs: list[dict[str, Any]],
        window_days: int = 7,
    ) -> float:
        """
        Compute a 0-100 travel fatigue score within the trailing *window_days* window.

        Applies a 1.5x penalty for eastward travel segments.

        Parameters
        ----------
        travel_logs:
            List of game dicts with at minimum:
              - game_date       : date
              - miles_traveled  : float
              - timezone_change : float  (positive = moved east)
        window_days:
            Look-back window in days from the most recent game date.

        Returns
        -------
        float
            Travel index in [0, 100].
        """
        if not travel_logs:
            return 0.0

        cutoff = _most_recent_date(travel_logs) - timedelta(days=window_days)
        window_logs = [g for g in travel_logs if _to_date(g["game_date"]) > cutoff]

        if not window_logs:
            return 0.0

        total_miles = 0.0
        adjusted_tz = 0.0

        for log in window_logs:
            miles = float(log.get("miles_traveled", 0))
            tz_change = float(log.get("timezone_change", 0))
            eastward = tz_change > 0  # positive tz_change = travelling east

            total_miles += miles
            adjusted_tz += abs(tz_change) * (1.5 if eastward else 1.0)

        miles_factor = _norm(total_miles, _MAX_MILES_5D)
        tz_factor = _norm(adjusted_tz, _MAX_TZ_CHANGES)

        raw = miles_factor * 0.55 + tz_factor * 0.45
        return _clamp(raw * 100.0)

    def get_risk_flags(
        self,
        result: FatigueResult,
        player_age: float,
        history: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        """
        Return a list of active risk flag strings for a player.

        Possible flags:
          ``back_to_back``          – most recent game was a back-to-back
          ``three_in_four``         – 3 games in any 4-night window in history
          ``four_in_six``           – 4 games in any 6-night window in history
          ``cross_country_travel``  – travelled >2 000 miles in last 7 days
          ``high_timezone_stress``  – ≥3 hours of adjusted eastward timezone change
          ``age_recovery_risk``     – player older than the age threshold
          ``extreme_workload``      – workload_index ≥ 80
          ``very_high_fatigue``     – composite_index ≥ 80

        Parameters
        ----------
        result:
            A :class:`FatigueResult` already computed for the player.
        player_age:
            Player age in years.
        history:
            Optional raw history list (needed for schedule-pattern flags).

        Returns
        -------
        list[str]
        """
        flags: list[str] = []
        history = history or []

        # Back-to-back: most recent game entry
        if history:
            most_recent = max(history, key=lambda g: _to_date(g["game_date"]))
            if most_recent.get("is_back_to_back", False):
                flags.append("back_to_back")

        # Schedule patterns — reuse ScheduleAnalyzer logic inline to avoid circular import
        if history:
            from .schedule_analyzer import ScheduleAnalyzer
            analyzer = ScheduleAnalyzer()
            game_dates = sorted(_to_date(g["game_date"]) for g in history)
            if analyzer.detect_three_in_four(game_dates):
                flags.append("three_in_four")
            if analyzer.detect_four_in_six(game_dates):
                flags.append("four_in_six")

        # Cross-country travel (>2 000 miles in last 7 days)
        if history:
            cutoff = _most_recent_date(history) - timedelta(days=7)
            recent_miles = sum(
                float(g.get("miles_traveled", 0))
                for g in history
                if _to_date(g["game_date"]) > cutoff
            )
            if recent_miles > 2000:
                flags.append("cross_country_travel")

        # High timezone stress
        if result.breakdown.get("timezone_changes", 0) >= 0.25:
            # breakdown value is a normalised [0-1] ratio; 0.25 ≈ 3 adjusted hours
            flags.append("high_timezone_stress")

        # Age recovery risk
        if player_age >= self.age_recovery_threshold:
            flags.append("age_recovery_risk")

        # Extreme workload
        if result.workload_index >= 80:
            flags.append("extreme_workload")

        # Very high overall fatigue
        if result.composite_index >= 80:
            flags.append("very_high_fatigue")

        return flags

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_raw_components(
        self,
        history: list[dict[str, Any]],
        as_of_date: date,
    ) -> dict[str, float]:
        """
        Compute each formula component as a normalised [0, 1] value.

        Keys match :attr:`_WEIGHTS`.
        """
        if not history:
            return {k: 0.0 for k in self._WEIGHTS}

        # --- games_last_7d ---
        cutoff_7d = as_of_date - timedelta(days=7)
        games_7d = sum(
            1 for g in history if _to_date(g["game_date"]) > cutoff_7d
        )

        # --- minutes_last_10d ---
        cutoff_10d = as_of_date - timedelta(days=10)
        mins_10d = sum(
            float(g.get("minutes_played", 0))
            for g in history
            if _to_date(g["game_date"]) > cutoff_10d
        )

        # --- miles_last_5d with eastward penalty ---
        cutoff_5d = as_of_date - timedelta(days=5)
        adjusted_miles = 0.0
        adjusted_tz = 0.0
        for g in history:
            if _to_date(g["game_date"]) > cutoff_5d:
                miles = float(g.get("miles_traveled", 0))
                adjusted_miles += miles

        # --- timezone_changes (last 7 days) with eastward penalty ---
        for g in history:
            if _to_date(g["game_date"]) > cutoff_7d:
                tz = float(g.get("timezone_change", 0))
                eastward = tz > 0
                adjusted_tz += abs(tz) * (1.5 if eastward else 1.0)

        # --- consecutive_games ---
        sorted_dates = sorted(_to_date(g["game_date"]) for g in history)
        consecutive = _count_consecutive(sorted_dates, as_of_date)

        # --- shot_volume (last 3 games) ---
        last_3 = sorted(history, key=lambda g: _to_date(g["game_date"]))[-3:]
        shots_3g = sum(int(g.get("shots_faced", 0)) for g in last_3)

        return {
            "games_last_7d":     _norm(games_7d, _MAX_GAMES_7D),
            "minutes_last_10d":  _norm(mins_10d, _MAX_MINUTES_10D),
            "miles_last_5d":     _norm(adjusted_miles, _MAX_MILES_5D),
            "timezone_changes":  _norm(adjusted_tz, _MAX_TZ_CHANGES),
            "consecutive_games": _norm(consecutive, _MAX_CONSECUTIVE),
            "shot_volume":       _norm(shots_3g, _MAX_SHOTS_3G),
        }

    def _compute_composite(self, breakdown: dict[str, float]) -> float:
        """
        Combine normalised component scores into a single 0-100 index.
        """
        weighted_sum = sum(
            breakdown[k] * w for k, w in self._WEIGHTS.items()
        )
        return _clamp((weighted_sum / self._WEIGHT_SUM) * 100.0)

    def _calculate_schedule_density_index(
        self,
        history: list[dict[str, Any]],
        as_of_date: date,
        window_days: int = 30,
    ) -> float:
        """
        Return a 0-100 index representing games-per-week rate over *window_days*.

        A "fully packed" schedule of 4 games/week → 100.
        """
        if not history:
            return 0.0

        cutoff = as_of_date - timedelta(days=window_days)
        window_games = [
            g for g in history if _to_date(g["game_date"]) > cutoff
        ]
        if not window_games:
            return 0.0

        games_per_week = len(window_games) / (window_days / 7.0)
        # 4 games/week is the practical NHL maximum → saturates at 100
        return _clamp((games_per_week / 4.0) * 100.0)

    def _estimate_recovery(
        self,
        composite_index: float,
        player_age: float | None,
    ) -> float:
        """
        Estimate recovery hours needed from composite fatigue index.

        Base: composite_index * 0.1 hours.
        Age adjustment: +5% per year above threshold.
        """
        base = composite_index * 0.1
        if player_age and player_age > self.age_recovery_threshold:
            age_multiplier = 1.0 + (player_age - self.age_recovery_threshold) * 0.05
            base *= age_multiplier
        return base


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

def _to_date(value: Any) -> date:
    """Coerce *value* to a :class:`datetime.date`."""
    if isinstance(value, date):
        return value
    # Support ISO strings like "2024-01-15"
    from datetime import datetime as _dt
    return _dt.fromisoformat(str(value)).date()


def _most_recent_date(games: list[dict[str, Any]]) -> date:
    return max(_to_date(g["game_date"]) for g in games)


def _count_consecutive(sorted_dates: list[date], as_of_date: date) -> int:
    """
    Count how many consecutive games (games on back-to-back nights, i.e.
    separated by exactly 1 calendar day) end at *as_of_date* or before.

    We walk backwards from the most recent game and stop when a gap > 1 day
    is found.
    """
    relevant = [d for d in sorted_dates if d <= as_of_date]
    if not relevant:
        return 0

    consecutive = 1
    for i in range(len(relevant) - 1, 0, -1):
        delta = (relevant[i] - relevant[i - 1]).days
        if delta <= 1:
            consecutive += 1
        else:
            break
    return consecutive


def _categorise(composite_index: float) -> str:
    """Map a composite index value to a human-readable fatigue category."""
    if composite_index < 20:
        return "low"
    elif composite_index < 40:
        return "moderate"
    elif composite_index < 60:
        return "high"
    elif composite_index < 80:
        return "very_high"
    else:
        return "extreme"
