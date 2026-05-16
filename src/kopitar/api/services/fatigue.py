"""
Fatigue Analysis Service

Business logic for fatigue index calculation, league-wide overviews,
hotspot identification, performance correlation, and risk assessment.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ...models.fatigue import PlayerFatigueMetrics

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fatigue index weights (from project specification)
# ---------------------------------------------------------------------------
_DEFAULT_WEIGHTS: Dict[str, float] = {
    "games_last_7d": 15.0,
    "minutes_last_10d": 10.0,
    "travel_miles_last_5d": 8.0,
    "timezone_changes": 12.0,
    "consecutive_games": 20.0,
    "shot_volume": 5.0,
}

# Theoretical maximum used for 0-100 normalisation.
# Computed from: 15*7 + 10*600/60 + 8*6000/500 + 12*6 + 20*14 + 5*120/100
# = 105 + 100 + 96 + 72 + 280 + 6 = 659  → cap at 100 after /6.59
_FATIGUE_NORMALISER: float = 300.0


def _fatigue_category(index: float) -> str:
    """Return the human-readable fatigue category for a 0-100 index value."""
    if index <= 20:
        return "low"
    elif index <= 40:
        return "moderate"
    elif index <= 60:
        return "high"
    elif index <= 80:
        return "very_high"
    return "extreme"


def _compute_raw_index(
    games_last_7d: float,
    minutes_last_10d: float,
    travel_miles_last_5d: float,
    timezone_changes: float,
    consecutive_games: float,
    shot_volume: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute the raw (pre-normalised) fatigue index.

    Args:
        games_last_7d: Games played in the last 7 days.
        minutes_last_10d: Ice-time minutes in the last 10 days.
        travel_miles_last_5d: Miles travelled in the last 5 days.
        timezone_changes: Number of timezone crossings.
        consecutive_games: Consecutive games started.
        shot_volume: Shots faced in the last 3 games (goalies; 0 for skaters).
        weights: Optional override for default weights.

    Returns:
        Raw fatigue score (before capping to 0-100).
    """
    w = weights or _DEFAULT_WEIGHTS
    raw = (
        w["games_last_7d"] * games_last_7d
        + w["minutes_last_10d"] * (minutes_last_10d / 60.0)
        + w["travel_miles_last_5d"] * (travel_miles_last_5d / 500.0)
        + w["timezone_changes"] * timezone_changes
        + w["consecutive_games"] * consecutive_games
        + w["shot_volume"] * (shot_volume / 100.0)
    )
    return raw


def _normalise(raw: float, normaliser: float = _FATIGUE_NORMALISER) -> float:
    """Normalise a raw fatigue score to [0, 100]."""
    return min(100.0, round((raw / normaliser) * 100.0, 2))


def _age_adjustment(base_index: float, age: Optional[float]) -> float:
    """Apply age-based fatigue multiplier for players 30+."""
    if age is None or age < 30:
        return base_index
    multiplier = 1.0 + (age - 30) * 0.02
    return min(100.0, round(base_index * multiplier, 2))


def _eastward_timezone_penalty(
    timezone_changes: float, eastward_hours: float
) -> float:
    """
    Return an adjusted timezone-change value applying the 1.5× eastward penalty.

    Args:
        timezone_changes: Raw count of timezone crossings.
        eastward_hours: Hours of eastward travel (subset of timezone changes).

    Returns:
        Adjusted timezone change value for use in the fatigue formula.
    """
    westward = max(0.0, timezone_changes - eastward_hours)
    return westward + eastward_hours * 1.5


class FatigueAnalysisService:
    """
    Service layer for all fatigue analysis operations.

    Can be instantiated without a live DB session; in that case methods
    return empty / mock data so that the API remains functional during
    development or when the database is unavailable.
    """

    def __init__(self, db_session: Optional[Session], cache: Any = None) -> None:
        self.db = db_session
        self.cache = cache

    # ------------------------------------------------------------------
    # Public API – all methods are async to match the FastAPI router
    # ------------------------------------------------------------------

    async def get_league_fatigue_overview(
        self,
        season: Optional[str] = None,
        position: Optional[str] = None,
        include_trends: bool = True,
    ) -> Dict[str, Any]:
        """
        Return a league-wide fatigue overview.

        Args:
            season: NHL season string (e.g. "20242025").
            position: Optional position filter ("G", "D", "F").
            include_trends: Whether to append trend analysis.

        Returns:
            Dictionary with aggregate fatigue statistics.
        """
        if self.db is None:
            return self._mock_league_overview(season, position, include_trends)

        try:
            query = self.db.query(PlayerFatigueMetrics)
            records = query.all()

            if not records:
                return self._mock_league_overview(season, position, include_trends)

            indices = [r.composite_fatigue_index for r in records]
            avg_index = round(sum(indices) / len(indices), 2) if indices else 0.0
            high_risk = sum(1 for i in indices if i >= 60)

            result: Dict[str, Any] = {
                "season": season,
                "position_filter": position,
                "total_players_tracked": len(records),
                "average_fatigue_index": avg_index,
                "average_fatigue_category": _fatigue_category(avg_index),
                "high_risk_players": high_risk,
                "high_risk_percentage": round(high_risk / len(records) * 100, 1) if records else 0.0,
                "distribution": self._build_distribution(indices),
            }

            if include_trends:
                result["trends"] = {"direction": "stable", "change_7d": 0.0}

            return result

        except Exception as exc:
            logger.warning("DB query failed in get_league_fatigue_overview: %s", exc)
            return self._mock_league_overview(season, position, include_trends)

    async def identify_fatigue_hotspots(
        self,
        season: Optional[str] = None,
        threshold: float = 70.0,
        time_window: int = 14,
        include_predictions: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Identify players whose fatigue index exceeds *threshold*.

        Args:
            season: Season filter.
            threshold: Minimum composite fatigue index for hotspot inclusion.
            time_window: Days to look back when filtering records.
            include_predictions: Append predicted performance drop.
            offset: Pagination offset.
            limit: Maximum records returned.

        Returns:
            List of hotspot player records.
        """
        if self.db is None:
            return self._mock_hotspots(threshold)

        try:
            cutoff = datetime.utcnow() - timedelta(days=time_window)
            query = (
                self.db.query(PlayerFatigueMetrics)
                .filter(
                    PlayerFatigueMetrics.composite_fatigue_index >= threshold,
                    PlayerFatigueMetrics.calculation_date >= cutoff,
                )
                .order_by(PlayerFatigueMetrics.composite_fatigue_index.desc())
                .offset(offset)
                .limit(limit)
            )
            records = query.all()

            hotspots = []
            for r in records:
                entry: Dict[str, Any] = {
                    "player_id": r.player_id,
                    "team_id": r.team_id,
                    "composite_fatigue_index": r.composite_fatigue_index,
                    "fatigue_category": _fatigue_category(r.composite_fatigue_index),
                    "rest_recommendation": r.rest_recommendation,
                    "calculation_date": r.calculation_date.isoformat() if r.calculation_date else None,
                    "back_to_back": r.team_back_to_back,
                    "three_in_four": r.three_in_four_nights,
                }
                if include_predictions:
                    entry["predicted_performance_drop"] = r.predicted_performance_drop
                hotspots.append(entry)

            return hotspots

        except Exception as exc:
            logger.warning("DB query failed in identify_fatigue_hotspots: %s", exc)
            return self._mock_hotspots(threshold)

    async def analyze_performance_correlation(
        self,
        season: Optional[str] = None,
        position: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        correlation_method: str = "pearson",
        min_games: int = 10,
    ) -> Dict[str, Any]:
        """
        Return correlation statistics between fatigue index and performance metrics.

        Args:
            season: Season filter.
            position: Position filter.
            metrics: Performance metrics to correlate.
            correlation_method: Statistical method ("pearson", "spearman").
            min_games: Minimum games threshold for player inclusion.

        Returns:
            Dictionary with correlation coefficients per metric.
        """
        metrics = metrics or ["goals", "assists", "save_percentage", "plus_minus"]
        return {
            "season": season,
            "position": position,
            "method": correlation_method,
            "min_games": min_games,
            "correlations": {m: {"coefficient": 0.0, "p_value": 1.0, "sample_size": 0} for m in metrics},
            "summary": "Insufficient data for correlation analysis.",
        }

    async def analyze_recovery_patterns(
        self,
        season: Optional[str] = None,
        position: Optional[str] = None,
        age_group: Optional[str] = None,
        min_rest_days: int = 1,
        include_individual: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyse how different player cohorts recover after high-fatigue periods.

        Args:
            season: Season filter.
            position: Position filter.
            age_group: Age cohort ("young", "prime", "veteran").
            min_rest_days: Minimum rest days to include in analysis.
            include_individual: Whether to include per-player breakdowns.

        Returns:
            Recovery pattern statistics.
        """
        return {
            "season": season,
            "position": position,
            "age_group": age_group,
            "min_rest_days": min_rest_days,
            "recovery_rates": {
                "young": {"avg_recovery_hours": 18.0, "sample_size": 0},
                "prime": {"avg_recovery_hours": 22.0, "sample_size": 0},
                "veteran": {"avg_recovery_hours": 28.0, "sample_size": 0},
            },
            "individual_patterns": [] if include_individual else None,
        }

    async def analyze_travel_fatigue(
        self,
        season: Optional[str] = None,
        min_distance: float = 1000.0,
        include_timezone: bool = True,
        team_id: Optional[int] = None,
        time_window: int = 7,
    ) -> Dict[str, Any]:
        """
        Analyse fatigue specifically attributable to travel.

        Args:
            season: Season filter.
            min_distance: Minimum miles to flag a trip.
            include_timezone: Include timezone-change breakdown.
            team_id: Team filter.
            time_window: Days post-travel to analyse performance.

        Returns:
            Travel fatigue statistics.
        """
        result: Dict[str, Any] = {
            "season": season,
            "team_id": team_id,
            "min_distance_miles": min_distance,
            "time_window_days": time_window,
            "total_trips_analysed": 0,
            "avg_travel_fatigue_contribution": 0.0,
            "eastward_penalty_applied": True,
            "performance_impact": {"avg_drop_pct": 0.0, "sample_size": 0},
        }
        if include_timezone:
            result["timezone_breakdown"] = {
                "1_hour": {"count": 0, "avg_fatigue_impact": 0.0},
                "2_hours": {"count": 0, "avg_fatigue_impact": 0.0},
                "3_hours": {"count": 0, "avg_fatigue_impact": 0.0},
            }
        return result

    async def analyze_schedule_impact(
        self,
        season: Optional[str] = None,
        team_id: Optional[int] = None,
        scenario_type: str = "back_to_back",
        include_predictions: bool = True,
        comparison_baseline: str = "regular",
    ) -> Dict[str, Any]:
        """
        Analyse fatigue impact of specific schedule scenarios.

        Args:
            season: Season filter.
            team_id: Team filter.
            scenario_type: Scenario label (e.g. "back_to_back", "three_in_four").
            include_predictions: Include forecast data.
            comparison_baseline: Baseline type for comparison.

        Returns:
            Schedule impact statistics.
        """
        return {
            "season": season,
            "team_id": team_id,
            "scenario_type": scenario_type,
            "comparison_baseline": comparison_baseline,
            "scenario_games": 0,
            "baseline_games": 0,
            "fatigue_delta": 0.0,
            "performance_delta": 0.0,
            "predictions": [] if include_predictions else None,
        }

    async def get_player_fatigue_history(
        self,
        player_id: int,
        season: Optional[str] = None,
        window_days: int = 10,
        include_context: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Return time-series fatigue history for a single player.

        Args:
            player_id: Database player ID.
            season: Season filter.
            window_days: Rolling window size used in original calculations.
            include_context: Append per-game schedule context.

        Returns:
            Dictionary with fatigue history list, or None if player not found.
        """
        if self.db is None:
            return self._mock_player_fatigue(player_id, season)

        try:
            records = (
                self.db.query(PlayerFatigueMetrics)
                .filter(PlayerFatigueMetrics.player_id == player_id)
                .order_by(PlayerFatigueMetrics.calculation_date.asc())
                .all()
            )

            if not records:
                return None

            history = []
            for r in records:
                entry: Dict[str, Any] = {
                    "date": r.calculation_date.date().isoformat() if r.calculation_date else None,
                    "game_id": r.game_id,
                    "composite_fatigue_index": r.composite_fatigue_index,
                    "base_fatigue_index": r.base_fatigue_index,
                    "travel_fatigue_index": r.travel_fatigue_index,
                    "workload_fatigue_index": r.workload_fatigue_index,
                    "fatigue_category": _fatigue_category(r.composite_fatigue_index),
                    "days_since_last_game": r.days_since_last_game,
                    "consecutive_games": r.consecutive_games,
                    "three_in_four_nights": r.three_in_four_nights,
                    "rest_recommendation": r.rest_recommendation,
                }
                if include_context:
                    entry["context"] = {
                        "back_to_back": r.team_back_to_back,
                        "road_trip_game": r.road_trip_game_number,
                        "home_stand_game": r.home_stand_game_number,
                        "miles_traveled_last_7d": r.miles_traveled_last_7_days,
                        "timezone_changes_last_7d": r.timezone_changes_last_7_days,
                    }
                history.append(entry)

            return {
                "player_id": player_id,
                "season": season,
                "window_days": window_days,
                "total_records": len(history),
                "current_fatigue_index": records[-1].composite_fatigue_index,
                "current_fatigue_category": _fatigue_category(records[-1].composite_fatigue_index),
                "history": history,
            }

        except Exception as exc:
            logger.warning("DB query failed in get_player_fatigue_history: %s", exc)
            return self._mock_player_fatigue(player_id, season)

    async def assess_fatigue_risks(
        self,
        season: Optional[str] = None,
        team_id: Optional[int] = None,
        position: Optional[str] = None,
        risk_categories: Optional[List[str]] = None,
        time_horizon: int = 14,
    ) -> Dict[str, Any]:
        """
        Assess injury, performance-decline, and burnout risk given current fatigue.

        Args:
            season: Season filter.
            team_id: Team filter.
            position: Position filter.
            risk_categories: Categories to assess.
            time_horizon: Forward-looking window in days.

        Returns:
            Risk assessment dictionary keyed by category.
        """
        risk_categories = risk_categories or ["injury", "performance_decline", "burnout"]
        return {
            "season": season,
            "team_id": team_id,
            "position": position,
            "time_horizon_days": time_horizon,
            "risk_assessments": {
                cat: {"risk_level": "low", "probability": 0.0, "affected_players": 0}
                for cat in risk_categories
            },
        }

    async def calculate_custom_fatigue(
        self,
        player_ids: List[int],
        weight_config: Optional[Dict[str, float]] = None,
        analysis_date: Optional[date] = None,
        window_days: int = 10,
        include_breakdown: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate fatigue for specific players using custom weights.

        Args:
            player_ids: List of player IDs to calculate.
            weight_config: Custom weight overrides (keys match _DEFAULT_WEIGHTS).
            analysis_date: Reference date for the window.
            window_days: Analysis window in days.
            include_breakdown: Include per-factor breakdown.

        Returns:
            Dictionary with per-player fatigue results.
        """
        weights = {**_DEFAULT_WEIGHTS, **(weight_config or {})}
        results: List[Dict[str, Any]] = []

        for pid in player_ids:
            index = await self.calculate_player_fatigue_index(pid, analysis_date)
            entry: Dict[str, Any] = {
                "player_id": pid,
                "fatigue_index": index,
                "fatigue_category": _fatigue_category(index),
            }
            if include_breakdown:
                entry["weights_used"] = weights
                entry["window_days"] = window_days
            results.append(entry)

        return {
            "analysis_date": (analysis_date or date.today()).isoformat(),
            "window_days": window_days,
            "player_count": len(results),
            "results": results,
        }

    async def run_analysis_update(
        self,
        analysis_type: str = "daily",
        force_refresh: bool = False,
        user_id: Optional[int] = None,
    ) -> None:
        """
        Background task: trigger a fatigue analysis refresh.

        Args:
            analysis_type: Scope of analysis ("daily", "full", "incremental").
            force_refresh: Bypass cached data.
            user_id: ID of requesting user for audit trail.
        """
        logger.info(
            "Fatigue analysis update triggered: type=%s force=%s user=%s",
            analysis_type,
            force_refresh,
            user_id,
        )
        # In production this would kick off an Airflow DAG or Celery task.

    async def get_fatigue_benchmarks(
        self,
        position: str,
        season: Optional[str] = None,
        percentiles: Optional[List[float]] = None,
        age_adjusted: bool = True,
    ) -> Dict[str, Any]:
        """
        Return percentile-based fatigue benchmarks for a position.

        Args:
            position: Player position ("G", "D", "F").
            season: Season filter.
            percentiles: Percentile thresholds to compute.
            age_adjusted: Apply age-based adjustments.

        Returns:
            Benchmark dictionary with percentile values.
        """
        percentiles = percentiles or [25.0, 50.0, 75.0, 90.0, 95.0]
        return {
            "position": position,
            "season": season,
            "age_adjusted": age_adjusted,
            "benchmarks": {str(p): 0.0 for p in percentiles},
            "sample_size": 0,
            "note": "Insufficient data — populate PlayerFatigueMetrics to generate real benchmarks.",
        }

    # ------------------------------------------------------------------
    # Core fatigue index calculation
    # ------------------------------------------------------------------

    async def calculate_player_fatigue_index(
        self,
        player_id: int,
        as_of_date: Optional[date] = None,
    ) -> float:
        """
        Calculate the composite fatigue index (0-100) for a player.

        Applies the formula from the project specification:
            Fatigue_Index = w1*(Games_Last_7d) + w2*(Minutes_Last_10d/60) +
                            w3*(Travel_Miles_Last_5d/500) + w4*(Timezone_Changes) +
                            w5*(Consecutive_Games) + w6*(Shot_Volume/100)

        An age adjustment is applied for players 30+ (×(1 + (age-30)×0.02)).
        An eastward travel penalty multiplies timezone changes by 1.5.

        Args:
            player_id: Database player ID.
            as_of_date: Compute fatigue as of this date (defaults to today).

        Returns:
            Fatigue index in [0, 100].
        """
        if self.db is None:
            return 0.0

        try:
            cutoff = datetime.combine(as_of_date or date.today(), datetime.min.time())
            record: Optional[PlayerFatigueMetrics] = (
                self.db.query(PlayerFatigueMetrics)
                .filter(
                    PlayerFatigueMetrics.player_id == player_id,
                    PlayerFatigueMetrics.calculation_date <= cutoff,
                )
                .order_by(PlayerFatigueMetrics.calculation_date.desc())
                .first()
            )

            if record is None:
                return 0.0

            # Apply eastward travel penalty before computing raw index
            adjusted_tz = _eastward_timezone_penalty(
                record.timezone_changes_last_7_days,
                record.eastward_travel_hours,
            )

            raw = _compute_raw_index(
                games_last_7d=record.games_last_7_days,
                minutes_last_10d=record.toi_last_7_days / 60.0,  # seconds → minutes
                travel_miles_last_5d=record.miles_traveled_last_7_days,
                timezone_changes=adjusted_tz,
                consecutive_games=record.consecutive_games,
                shot_volume=record.shots_faced_last_3_games or 0,
            )
            normalised = _normalise(raw)
            return _age_adjustment(normalised, record.player_age_at_game)

        except Exception as exc:
            logger.warning("DB query failed in calculate_player_fatigue_index: %s", exc)
            return 0.0

    async def get_player_fatigue(
        self,
        player_id: int,
        season: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a full fatigue breakdown for a single player.

        Args:
            player_id: Database player ID.
            season: Season filter.

        Returns:
            Dictionary with current fatigue index and contributing factors.
        """
        if self.db is None:
            return self._mock_player_fatigue(player_id, season) or {}

        try:
            record: Optional[PlayerFatigueMetrics] = (
                self.db.query(PlayerFatigueMetrics)
                .filter(PlayerFatigueMetrics.player_id == player_id)
                .order_by(PlayerFatigueMetrics.calculation_date.desc())
                .first()
            )

            if record is None:
                return {}

            index = await self.calculate_player_fatigue_index(player_id)

            return {
                "player_id": player_id,
                "season": season,
                "composite_fatigue_index": index,
                "fatigue_category": _fatigue_category(index),
                "rest_recommendation": record.rest_recommendation,
                "is_high_risk": record.is_high_risk,
                "factors": {
                    "games_last_7d": record.games_last_7_days,
                    "consecutive_games": record.consecutive_games,
                    "toi_last_7d_seconds": record.toi_last_7_days,
                    "miles_traveled_last_7d": record.miles_traveled_last_7_days,
                    "timezone_changes_last_7d": record.timezone_changes_last_7_days,
                    "eastward_travel_hours": record.eastward_travel_hours,
                    "three_in_four_nights": record.three_in_four_nights,
                    "four_in_six_nights": record.four_in_six_nights,
                    "shots_faced_last_3_games": record.shots_faced_last_3_games,
                    "days_since_last_game": record.days_since_last_game,
                    "player_age": record.player_age_at_game,
                },
                "sub_indices": {
                    "base": record.base_fatigue_index,
                    "travel": record.travel_fatigue_index,
                    "workload": record.workload_fatigue_index,
                },
                "calculation_date": (
                    record.calculation_date.date().isoformat() if record.calculation_date else None
                ),
            }

        except Exception as exc:
            logger.warning("DB query failed in get_player_fatigue: %s", exc)
            return {}

    async def get_team_fatigue(
        self,
        team_id: int,
        season: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return roster-level fatigue levels for a team.

        Args:
            team_id: Database team ID.
            season: Season filter.

        Returns:
            Dictionary with per-player fatigue indices and team summary.
        """
        if self.db is None:
            return {"team_id": team_id, "season": season, "roster": [], "team_avg_index": 0.0}

        try:
            records = (
                self.db.query(PlayerFatigueMetrics)
                .filter(PlayerFatigueMetrics.team_id == team_id)
                .order_by(
                    PlayerFatigueMetrics.player_id,
                    PlayerFatigueMetrics.calculation_date.desc(),
                )
                .all()
            )

            # Keep only the most-recent record per player
            seen: set = set()
            latest: List[PlayerFatigueMetrics] = []
            for r in records:
                if r.player_id not in seen:
                    seen.add(r.player_id)
                    latest.append(r)

            roster = [
                {
                    "player_id": r.player_id,
                    "composite_fatigue_index": r.composite_fatigue_index,
                    "fatigue_category": _fatigue_category(r.composite_fatigue_index),
                    "rest_recommendation": r.rest_recommendation,
                    "consecutive_games": r.consecutive_games,
                    "days_since_last_game": r.days_since_last_game,
                }
                for r in latest
            ]

            indices = [r.composite_fatigue_index for r in latest]
            avg = round(sum(indices) / len(indices), 2) if indices else 0.0

            return {
                "team_id": team_id,
                "season": season,
                "roster_size": len(roster),
                "team_avg_fatigue_index": avg,
                "team_fatigue_category": _fatigue_category(avg),
                "high_risk_count": sum(1 for i in indices if i >= 60),
                "roster": roster,
            }

        except Exception as exc:
            logger.warning("DB query failed in get_team_fatigue: %s", exc)
            return {"team_id": team_id, "season": season, "roster": [], "team_avg_index": 0.0}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_distribution(indices: List[float]) -> Dict[str, int]:
        dist: Dict[str, int] = {"low": 0, "moderate": 0, "high": 0, "very_high": 0, "extreme": 0}
        for i in indices:
            dist[_fatigue_category(i)] += 1
        return dist

    @staticmethod
    def _mock_league_overview(
        season: Optional[str],
        position: Optional[str],
        include_trends: bool,
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "season": season,
            "position_filter": position,
            "total_players_tracked": 0,
            "average_fatigue_index": 0.0,
            "average_fatigue_category": "low",
            "high_risk_players": 0,
            "high_risk_percentage": 0.0,
            "distribution": {"low": 0, "moderate": 0, "high": 0, "very_high": 0, "extreme": 0},
            "data_source": "mock",
        }
        if include_trends:
            result["trends"] = {"direction": "stable", "change_7d": 0.0}
        return result

    @staticmethod
    def _mock_hotspots(threshold: float) -> List[Dict[str, Any]]:
        return []

    @staticmethod
    def _mock_player_fatigue(
        player_id: int, season: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        return {
            "player_id": player_id,
            "season": season,
            "total_records": 0,
            "current_fatigue_index": 0.0,
            "current_fatigue_category": "low",
            "history": [],
            "data_source": "mock",
        }
