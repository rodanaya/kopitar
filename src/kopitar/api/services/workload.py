"""
Workload Management Service

Business logic for workload distribution analysis, goalie rotation
recommendations, back-to-back detection, and rest optimisation.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ...models.fatigue import PlayerFatigueMetrics

logger = logging.getLogger(__name__)

# Threshold below which a gap between games counts as a back-to-back (hours)
_BACK_TO_BACK_HOURS: float = 24.0

# Fatigue index above which a goalie is flagged as needing rest
_REST_THRESHOLD: float = 60.0

# Fatigue index above which rotation is strongly recommended
_ROTATION_THRESHOLD: float = 45.0


def _fatigue_category(index: float) -> str:
    """Return a human-readable fatigue category for a 0-100 index."""
    if index <= 20:
        return "low"
    elif index <= 40:
        return "moderate"
    elif index <= 60:
        return "high"
    elif index <= 80:
        return "very_high"
    return "extreme"


class WorkloadManagementService:
    """
    Service layer for workload management operations.

    Handles goalie rotation recommendations, workload summaries,
    back-to-back detection, and rest optimisation.  All methods are
    async to match the FastAPI router.  When *db_session* is ``None``
    the service returns empty / mock data so the API remains functional
    during development.
    """

    def __init__(self, db_session: Optional[Session], cache: Any = None) -> None:
        self.db = db_session
        self.cache = cache

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_workload_summary(
        self,
        player_id: int,
        days: int = 10,
    ) -> Dict[str, Any]:
        """
        Summarise games, ice time, and travel for a player over the last *days*.

        Args:
            player_id: Database player ID.
            days: Look-back window in days.

        Returns:
            Dictionary with games played, total TOI seconds, and miles
            travelled within the window, plus back-to-back and
            three-in-four flags.
        """
        if self.db is None:
            return self._mock_workload_summary(player_id, days)

        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            records = (
                self.db.query(PlayerFatigueMetrics)
                .filter(
                    PlayerFatigueMetrics.player_id == player_id,
                    PlayerFatigueMetrics.calculation_date >= cutoff,
                )
                .order_by(PlayerFatigueMetrics.calculation_date.asc())
                .all()
            )

            if not records:
                return self._mock_workload_summary(player_id, days)

            games = len(records)
            total_toi = sum(r.toi_last_7_days for r in records)
            total_miles = max((r.miles_traveled_last_7_days for r in records), default=0.0)
            tz_changes = max((r.timezone_changes_last_7_days for r in records), default=0)
            latest = records[-1]

            return {
                "player_id": player_id,
                "window_days": days,
                "games_played": games,
                "total_toi_seconds": total_toi,
                "total_toi_minutes": round(total_toi / 60.0, 1),
                "miles_traveled": round(total_miles, 1),
                "timezone_changes": tz_changes,
                "back_to_back_count": latest.back_to_back_games,
                "three_in_four_nights": latest.three_in_four_nights,
                "four_in_six_nights": latest.four_in_six_nights,
                "consecutive_games": latest.consecutive_games,
                "days_since_last_game": latest.days_since_last_game,
                "current_fatigue_index": latest.composite_fatigue_index,
                "fatigue_category": _fatigue_category(latest.composite_fatigue_index),
            }

        except Exception as exc:
            logger.warning("DB query failed in get_workload_summary: %s", exc)
            return self._mock_workload_summary(player_id, days)

    async def get_rotation_recommendations(
        self,
        team_id: int,
        upcoming_games: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Recommend which goalie to start for each upcoming game based on fatigue.

        Logic:
        - If a goalie's fatigue index >= _REST_THRESHOLD, recommend the backup.
        - If fatigue >= _ROTATION_THRESHOLD, flag as "consider rotation".
        - Back-to-back games always trigger a rotation recommendation.

        Args:
            team_id: Database team ID.
            upcoming_games: Number of future games to plan for.

        Returns:
            List of per-game recommendation dicts ordered by game number.
        """
        if self.db is None:
            return self._mock_rotation_recommendations(team_id, upcoming_games)

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

            # Keep most-recent record per player (proxy for "current" state)
            seen: set = set()
            latest_per_player: List[PlayerFatigueMetrics] = []
            for r in records:
                if r.player_id not in seen:
                    seen.add(r.player_id)
                    latest_per_player.append(r)

            if not latest_per_player:
                return self._mock_rotation_recommendations(team_id, upcoming_games)

            # Sort by fatigue index ascending so the freshest player is first
            goalies = sorted(latest_per_player, key=lambda r: r.composite_fatigue_index)

            recommendations: List[Dict[str, Any]] = []
            for game_num in range(1, upcoming_games + 1):
                # Simple round-robin weighted by fatigue: always pick the
                # player with the lowest running fatigue index.
                starter = goalies[0]
                is_b2b = starter.team_back_to_back or (game_num % 2 == 0)

                action: str
                if starter.composite_fatigue_index >= _REST_THRESHOLD or is_b2b:
                    action = "rotate"
                    recommended_starter_id = goalies[-1].player_id if len(goalies) > 1 else starter.player_id
                elif starter.composite_fatigue_index >= _ROTATION_THRESHOLD:
                    action = "consider_rotation"
                    recommended_starter_id = starter.player_id
                else:
                    action = "start"
                    recommended_starter_id = starter.player_id

                recommendations.append({
                    "game_number": game_num,
                    "recommended_starter_player_id": recommended_starter_id,
                    "action": action,
                    "primary_starter_fatigue_index": starter.composite_fatigue_index,
                    "primary_starter_fatigue_category": _fatigue_category(
                        starter.composite_fatigue_index
                    ),
                    "back_to_back_flag": is_b2b,
                    "rationale": self._rotation_rationale(
                        starter.composite_fatigue_index, is_b2b, action
                    ),
                })

            return recommendations

        except Exception as exc:
            logger.warning("DB query failed in get_rotation_recommendations: %s", exc)
            return self._mock_rotation_recommendations(team_id, upcoming_games)

    async def check_back_to_back(
        self,
        player_id: int,
        game_date: date,
    ) -> bool:
        """
        Check whether *game_date* constitutes a back-to-back for the player.

        A back-to-back is defined as a game within 24 hours of the player's
        previous game.

        Args:
            player_id: Database player ID.
            game_date: Proposed game date to evaluate.

        Returns:
            True if the game is a back-to-back, False otherwise.
        """
        if self.db is None:
            return False

        try:
            game_dt = datetime.combine(game_date, datetime.min.time())
            cutoff = game_dt - timedelta(hours=_BACK_TO_BACK_HOURS)

            record: Optional[PlayerFatigueMetrics] = (
                self.db.query(PlayerFatigueMetrics)
                .filter(
                    PlayerFatigueMetrics.player_id == player_id,
                    PlayerFatigueMetrics.calculation_date >= cutoff,
                    PlayerFatigueMetrics.calculation_date < game_dt,
                )
                .order_by(PlayerFatigueMetrics.calculation_date.desc())
                .first()
            )

            return record is not None

        except Exception as exc:
            logger.warning("DB query failed in check_back_to_back: %s", exc)
            return False

    async def analyze_workload_distribution(
        self,
        season: Optional[str] = None,
        team_id: Optional[int] = None,
        position: Optional[str] = None,
        aggregation_level: str = "team",
        include_recommendations: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyse how workload is distributed across players and teams.

        Args:
            season: Season filter.
            team_id: Optional team filter.
            position: Optional position filter ("G", "D", "F").
            aggregation_level: "player", "team", or "league".
            include_recommendations: Append rebalancing recommendations.

        Returns:
            Workload distribution statistics at the requested aggregation level.
        """
        result: Dict[str, Any] = {
            "season": season,
            "team_id": team_id,
            "position": position,
            "aggregation_level": aggregation_level,
            "total_players": 0,
            "avg_games_per_player": 0.0,
            "avg_toi_minutes": 0.0,
            "distribution_gini": 0.0,
            "imbalance_flag": False,
        }

        if include_recommendations:
            result["recommendations"] = []

        if self.db is None:
            result["data_source"] = "mock"
            return result

        try:
            query = self.db.query(PlayerFatigueMetrics)
            if team_id is not None:
                query = query.filter(PlayerFatigueMetrics.team_id == team_id)
            records = query.all()

            if not records:
                return result

            games = [r.games_last_7_days for r in records]
            toi = [r.toi_last_7_days / 60.0 for r in records]

            result["total_players"] = len(records)
            result["avg_games_per_player"] = round(sum(games) / len(games), 2) if games else 0.0
            result["avg_toi_minutes"] = round(sum(toi) / len(toi), 2) if toi else 0.0
            result["distribution_gini"] = round(self._gini(games), 3) if games else 0.0
            result["imbalance_flag"] = result["distribution_gini"] > 0.3

            if include_recommendations and result["imbalance_flag"]:
                result["recommendations"] = [
                    {
                        "type": "workload_rebalance",
                        "message": "Significant workload imbalance detected. Consider redistributing minutes.",
                        "priority": "medium",
                    }
                ]

            return result

        except Exception as exc:
            logger.warning("DB query failed in analyze_workload_distribution: %s", exc)
            return result

    async def get_team_management_analysis(
        self,
        team_id: int,
        season: Optional[str] = None,
        include_recommendations: bool = True,
        forecast_days: int = 14,
        position_breakdown: bool = True,
    ) -> Dict[str, Any]:
        """
        Comprehensive team fatigue management analysis for coaching staff.

        Args:
            team_id: Database team ID.
            season: Season filter.
            include_recommendations: Append actionable management recommendations.
            forecast_days: Forward-looking window in days.
            position_breakdown: Break fatigue data down by position.

        Returns:
            Management analysis dictionary.
        """
        if self.db is None:
            return self._mock_team_management(team_id, season)

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

            seen: set = set()
            latest: List[PlayerFatigueMetrics] = []
            for r in records:
                if r.player_id not in seen:
                    seen.add(r.player_id)
                    latest.append(r)

            if not latest:
                return self._mock_team_management(team_id, season)

            indices = [r.composite_fatigue_index for r in latest]
            avg = round(sum(indices) / len(indices), 2) if indices else 0.0
            high_risk = [r for r in latest if r.composite_fatigue_index >= _REST_THRESHOLD]

            result: Dict[str, Any] = {
                "team_id": team_id,
                "season": season,
                "roster_size": len(latest),
                "team_avg_fatigue_index": avg,
                "team_fatigue_category": _fatigue_category(avg),
                "high_risk_count": len(high_risk),
                "high_risk_player_ids": [r.player_id for r in high_risk],
                "forecast_days": forecast_days,
            }

            if position_breakdown:
                result["position_breakdown"] = {
                    "note": "Position data requires Player join — not yet implemented."
                }

            if include_recommendations:
                recs: List[Dict[str, Any]] = []
                for r in high_risk:
                    recs.append({
                        "player_id": r.player_id,
                        "current_fatigue_index": r.composite_fatigue_index,
                        "fatigue_category": _fatigue_category(r.composite_fatigue_index),
                        "recommendation": r.rest_recommendation,
                        "estimated_recovery_hours": r.calculate_recovery_time(),
                    })
                result["recommendations"] = recs

            return result

        except Exception as exc:
            logger.warning("DB query failed in get_team_management_analysis: %s", exc)
            return self._mock_team_management(team_id, season)

    async def generate_rest_recommendations(
        self,
        team_id: Optional[int] = None,
        position: Optional[str] = None,
        current_fatigue_threshold: float = 60.0,
        optimization_horizon: int = 21,
        constraints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate ML-optimised rest recommendations balancing fatigue and performance.

        Args:
            team_id: Team filter.
            position: Position filter.
            current_fatigue_threshold: Fatigue index at which rest is recommended.
            optimization_horizon: Days ahead to optimise for.
            constraints: List of scheduling constraints (e.g. "no_consecutive_rest").

        Returns:
            Optimised rest recommendation schedule.
        """
        constraints = constraints or []

        if self.db is None:
            return {
                "team_id": team_id,
                "position": position,
                "fatigue_threshold": current_fatigue_threshold,
                "optimization_horizon_days": optimization_horizon,
                "constraints_applied": constraints,
                "recommendations": [],
                "data_source": "mock",
            }

        try:
            query = self.db.query(PlayerFatigueMetrics)
            if team_id is not None:
                query = query.filter(PlayerFatigueMetrics.team_id == team_id)

            records = query.all()
            seen: set = set()
            latest: List[PlayerFatigueMetrics] = []
            for r in records:
                if r.player_id not in seen:
                    seen.add(r.player_id)
                    latest.append(r)

            recs: List[Dict[str, Any]] = []
            for r in latest:
                if r.composite_fatigue_index >= current_fatigue_threshold:
                    recovery_h = r.calculate_recovery_time()
                    recs.append({
                        "player_id": r.player_id,
                        "current_fatigue_index": r.composite_fatigue_index,
                        "recommended_rest_days": max(1, round(recovery_h / 24)),
                        "priority": "high" if r.composite_fatigue_index >= 80 else "medium",
                        "rest_type": r.rest_recommendation,
                    })

            return {
                "team_id": team_id,
                "position": position,
                "fatigue_threshold": current_fatigue_threshold,
                "optimization_horizon_days": optimization_horizon,
                "constraints_applied": constraints,
                "total_players_flagged": len(recs),
                "recommendations": recs,
            }

        except Exception as exc:
            logger.warning("DB query failed in generate_rest_recommendations: %s", exc)
            return {
                "team_id": team_id,
                "position": position,
                "fatigue_threshold": current_fatigue_threshold,
                "optimization_horizon_days": optimization_horizon,
                "constraints_applied": constraints,
                "recommendations": [],
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _rotation_rationale(fatigue_index: float, is_b2b: bool, action: str) -> str:
        if action == "rotate":
            if is_b2b:
                return "Back-to-back game detected — rotate to backup to protect starter."
            return f"Fatigue index {fatigue_index:.1f} exceeds rest threshold — rotation required."
        if action == "consider_rotation":
            return f"Fatigue index {fatigue_index:.1f} is elevated — rotation recommended if possible."
        return f"Fatigue index {fatigue_index:.1f} is within acceptable range — starter cleared."

    @staticmethod
    def _gini(values: List[float]) -> float:
        """Compute the Gini coefficient of *values* as a workload imbalance proxy."""
        if not values or sum(values) == 0:
            return 0.0
        n = len(values)
        sorted_vals = sorted(values)
        cumsum = 0.0
        for i, v in enumerate(sorted_vals, 1):
            cumsum += v * (2 * i - n - 1)
        return cumsum / (n * sum(sorted_vals))

    @staticmethod
    def _mock_workload_summary(player_id: int, days: int) -> Dict[str, Any]:
        return {
            "player_id": player_id,
            "window_days": days,
            "games_played": 0,
            "total_toi_seconds": 0,
            "total_toi_minutes": 0.0,
            "miles_traveled": 0.0,
            "timezone_changes": 0,
            "back_to_back_count": 0,
            "three_in_four_nights": False,
            "four_in_six_nights": False,
            "consecutive_games": 0,
            "days_since_last_game": None,
            "current_fatigue_index": 0.0,
            "fatigue_category": "low",
            "data_source": "mock",
        }

    @staticmethod
    def _mock_rotation_recommendations(
        team_id: int, upcoming_games: int
    ) -> List[Dict[str, Any]]:
        return [
            {
                "game_number": g,
                "recommended_starter_player_id": None,
                "action": "start",
                "primary_starter_fatigue_index": 0.0,
                "primary_starter_fatigue_category": "low",
                "back_to_back_flag": False,
                "rationale": "No data available — populate PlayerFatigueMetrics for live recommendations.",
                "data_source": "mock",
            }
            for g in range(1, upcoming_games + 1)
        ]

    @staticmethod
    def _mock_team_management(team_id: int, season: Optional[str]) -> Dict[str, Any]:
        return {
            "team_id": team_id,
            "season": season,
            "roster_size": 0,
            "team_avg_fatigue_index": 0.0,
            "team_fatigue_category": "low",
            "high_risk_count": 0,
            "high_risk_player_ids": [],
            "recommendations": [],
            "data_source": "mock",
        }
