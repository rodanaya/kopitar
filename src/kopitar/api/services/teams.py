"""
Team Service

Handles team lookups, roster data, schedule analysis, fatigue analysis,
back-to-back game analysis, standings, and line combinations.
Falls back to plausible mock data when no database session is provided.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Union

_CACHE_TTL = 300

# Full 32-team NHL roster with realistic metadata
_MOCK_TEAMS: List[Dict[str, Any]] = [
    # Eastern Conference — Atlantic
    {"id": 6,  "nhl_id": 6,  "name": "Boston Bruins",          "abbreviation": "BOS", "tricode": "BOS", "location": "Boston",       "team_name": "Bruins",     "conference": "Eastern", "division": "Atlantic",    "active": True},
    {"id": 7,  "nhl_id": 7,  "name": "Buffalo Sabres",          "abbreviation": "BUF", "tricode": "BUF", "location": "Buffalo",       "team_name": "Sabres",     "conference": "Eastern", "division": "Atlantic",    "active": True},
    {"id": 17, "nhl_id": 17, "name": "Detroit Red Wings",       "abbreviation": "DET", "tricode": "DET", "location": "Detroit",       "team_name": "Red Wings",  "conference": "Eastern", "division": "Atlantic",    "active": True},
    {"id": 13, "nhl_id": 13, "name": "Florida Panthers",        "abbreviation": "FLA", "tricode": "FLA", "location": "Florida",       "team_name": "Panthers",   "conference": "Eastern", "division": "Atlantic",    "active": True},
    {"id": 8,  "nhl_id": 8,  "name": "Montreal Canadiens",      "abbreviation": "MTL", "tricode": "MTL", "location": "Montreal",      "team_name": "Canadiens",  "conference": "Eastern", "division": "Atlantic",    "active": True},
    {"id": 9,  "nhl_id": 9,  "name": "Ottawa Senators",         "abbreviation": "OTT", "tricode": "OTT", "location": "Ottawa",        "team_name": "Senators",   "conference": "Eastern", "division": "Atlantic",    "active": True},
    {"id": 14, "nhl_id": 14, "name": "Tampa Bay Lightning",     "abbreviation": "TBL", "tricode": "TBL", "location": "Tampa Bay",     "team_name": "Lightning",  "conference": "Eastern", "division": "Atlantic",    "active": True},
    {"id": 10, "nhl_id": 10, "name": "Toronto Maple Leafs",     "abbreviation": "TOR", "tricode": "TOR", "location": "Toronto",       "team_name": "Maple Leafs","conference": "Eastern", "division": "Atlantic",    "active": True},
    # Eastern Conference — Metropolitan
    {"id": 12, "nhl_id": 12, "name": "Carolina Hurricanes",     "abbreviation": "CAR", "tricode": "CAR", "location": "Carolina",      "team_name": "Hurricanes", "conference": "Eastern", "division": "Metropolitan","active": True},
    {"id": 29, "nhl_id": 29, "name": "Columbus Blue Jackets",   "abbreviation": "CBJ", "tricode": "CBJ", "location": "Columbus",      "team_name": "Blue Jackets","conference": "Eastern","division": "Metropolitan","active": True},
    {"id": 1,  "nhl_id": 1,  "name": "New Jersey Devils",       "abbreviation": "NJD", "tricode": "NJD", "location": "New Jersey",    "team_name": "Devils",     "conference": "Eastern", "division": "Metropolitan","active": True},
    {"id": 2,  "nhl_id": 2,  "name": "New York Islanders",      "abbreviation": "NYI", "tricode": "NYI", "location": "New York",      "team_name": "Islanders",  "conference": "Eastern", "division": "Metropolitan","active": True},
    {"id": 3,  "nhl_id": 3,  "name": "New York Rangers",        "abbreviation": "NYR", "tricode": "NYR", "location": "New York",      "team_name": "Rangers",    "conference": "Eastern", "division": "Metropolitan","active": True},
    {"id": 4,  "nhl_id": 4,  "name": "Philadelphia Flyers",     "abbreviation": "PHI", "tricode": "PHI", "location": "Philadelphia",  "team_name": "Flyers",     "conference": "Eastern", "division": "Metropolitan","active": True},
    {"id": 5,  "nhl_id": 5,  "name": "Pittsburgh Penguins",     "abbreviation": "PIT", "tricode": "PIT", "location": "Pittsburgh",    "team_name": "Penguins",   "conference": "Eastern", "division": "Metropolitan","active": True},
    {"id": 15, "nhl_id": 15, "name": "Washington Capitals",     "abbreviation": "WSH", "tricode": "WSH", "location": "Washington",    "team_name": "Capitals",   "conference": "Eastern", "division": "Metropolitan","active": True},
    # Western Conference — Central
    {"id": 53, "nhl_id": 53, "name": "Arizona Coyotes",         "abbreviation": "ARI", "tricode": "ARI", "location": "Arizona",       "team_name": "Coyotes",    "conference": "Western", "division": "Central",     "active": True},
    {"id": 16, "nhl_id": 16, "name": "Chicago Blackhawks",      "abbreviation": "CHI", "tricode": "CHI", "location": "Chicago",       "team_name": "Blackhawks", "conference": "Western", "division": "Central",     "active": True},
    {"id": 21, "nhl_id": 21, "name": "Colorado Avalanche",      "abbreviation": "COL", "tricode": "COL", "location": "Colorado",      "team_name": "Avalanche",  "conference": "Western", "division": "Central",     "active": True},
    {"id": 25, "nhl_id": 25, "name": "Dallas Stars",            "abbreviation": "DAL", "tricode": "DAL", "location": "Dallas",        "team_name": "Stars",      "conference": "Western", "division": "Central",     "active": True},
    {"id": 30, "nhl_id": 30, "name": "Minnesota Wild",          "abbreviation": "MIN", "tricode": "MIN", "location": "Minnesota",     "team_name": "Wild",       "conference": "Western", "division": "Central",     "active": True},
    {"id": 18, "nhl_id": 18, "name": "Nashville Predators",     "abbreviation": "NSH", "tricode": "NSH", "location": "Nashville",     "team_name": "Predators",  "conference": "Western", "division": "Central",     "active": True},
    {"id": 19, "nhl_id": 19, "name": "St. Louis Blues",         "abbreviation": "STL", "tricode": "STL", "location": "St. Louis",     "team_name": "Blues",      "conference": "Western", "division": "Central",     "active": True},
    {"id": 52, "nhl_id": 52, "name": "Winnipeg Jets",           "abbreviation": "WPG", "tricode": "WPG", "location": "Winnipeg",      "team_name": "Jets",       "conference": "Western", "division": "Central",     "active": True},
    # Western Conference — Pacific
    {"id": 24, "nhl_id": 24, "name": "Anaheim Ducks",           "abbreviation": "ANA", "tricode": "ANA", "location": "Anaheim",       "team_name": "Ducks",      "conference": "Western", "division": "Pacific",     "active": True},
    {"id": 20, "nhl_id": 20, "name": "Calgary Flames",          "abbreviation": "CGY", "tricode": "CGY", "location": "Calgary",       "team_name": "Flames",     "conference": "Western", "division": "Pacific",     "active": True},
    {"id": 22, "nhl_id": 22, "name": "Edmonton Oilers",         "abbreviation": "EDM", "tricode": "EDM", "location": "Edmonton",      "team_name": "Oilers",     "conference": "Western", "division": "Pacific",     "active": True},
    {"id": 26, "nhl_id": 26, "name": "Los Angeles Kings",       "abbreviation": "LAK", "tricode": "LAK", "location": "Los Angeles",   "team_name": "Kings",      "conference": "Western", "division": "Pacific",     "active": True},
    {"id": 28, "nhl_id": 28, "name": "San Jose Sharks",         "abbreviation": "SJS", "tricode": "SJS", "location": "San Jose",      "team_name": "Sharks",     "conference": "Western", "division": "Pacific",     "active": True},
    {"id": 55, "nhl_id": 55, "name": "Seattle Kraken",          "abbreviation": "SEA", "tricode": "SEA", "location": "Seattle",       "team_name": "Kraken",     "conference": "Western", "division": "Pacific",     "active": True},
    {"id": 23, "nhl_id": 23, "name": "Vancouver Canucks",       "abbreviation": "VAN", "tricode": "VAN", "location": "Vancouver",     "team_name": "Canucks",    "conference": "Western", "division": "Pacific",     "active": True},
    {"id": 54, "nhl_id": 54, "name": "Vegas Golden Knights",    "abbreviation": "VGK", "tricode": "VGK", "location": "Vegas",         "team_name": "Golden Knights","conference":"Western","division": "Pacific",     "active": True},
]

_TEAM_BY_ID: Dict[int, Dict[str, Any]] = {t["id"]: t for t in _MOCK_TEAMS}
_TEAM_BY_ABBREV: Dict[str, Dict[str, Any]] = {t["abbreviation"]: t for t in _MOCK_TEAMS}

_POSITIONS = ["C", "LW", "RW", "D", "D", "G"]  # weighted toward D


def _seed(*args: Any) -> int:
    return hash(tuple(str(a) for a in args)) & 0xFFFFFFFF


def _rng(*args: Any) -> random.Random:
    return random.Random(_seed(*args))


def _current_season() -> str:
    today = date.today()
    return f"{today.year}{today.year + 1}" if today.month >= 9 else f"{today.year - 1}{today.year}"


def _mock_roster(team_id: int, season: str, include_stats: bool = True) -> List[Dict[str, Any]]:
    r = _rng(team_id, season, "roster")
    n_players = 23
    positions = ["C"] * 4 + ["LW"] * 4 + ["RW"] * 4 + ["D"] * 8 + ["G"] * 2 + ["C"]
    roster = []
    for i, pos in enumerate(positions[:n_players]):
        pid = team_id * 1000 + i
        player: Dict[str, Any] = {
            "player_id": pid,
            "full_name": f"Player {pid}",
            "position": pos,
            "jersey_number": str(r.randint(1, 99)),
            "age": r.randint(22, 37),
            "team_id": team_id,
        }
        if include_stats:
            if pos == "G":
                sv = round(r.gauss(0.912, 0.010), 4)
                player["save_pct"] = max(0.880, min(0.940, sv))
                player["gaa"] = round(r.gauss(2.75, 0.35), 2)
                player["games_played"] = r.randint(20, 55)
            else:
                gp = r.randint(40, 82)
                g = r.randint(0, 40)
                a = r.randint(0, 55)
                player["games_played"] = gp
                player["goals"] = g
                player["assists"] = a
                player["points"] = g + a
                player["plus_minus"] = r.randint(-15, 20)
        roster.append(player)
    return roster


def _mock_schedule(team_id: int, season: str, n_games: int = 20) -> List[Dict[str, Any]]:
    r = _rng(team_id, season, "schedule")
    opponents = [t["abbreviation"] for t in _MOCK_TEAMS if t["id"] != team_id]
    schedule = []
    game_date = date(int(season[:4]), 10, 7)
    for i in range(n_games):
        game_date += timedelta(days=r.randint(1, 5))
        schedule.append({
            "game_id": team_id * 10000 + i,
            "game_date": game_date.isoformat(),
            "home_away": r.choice(["home", "away"]),
            "opponent": r.choice(opponents),
            "result": r.choice(["W", "W", "L", "OT", None]),
            "home_score": r.randint(0, 6),
            "away_score": r.randint(0, 6),
            "back_to_back": r.random() < 0.15,
            "travel_miles": round(r.uniform(0, 1500), 1),
        })
    return schedule


class TeamService:
    """
    Service for NHL team data operations.

    Parameters
    ----------
    db_session:
        SQLAlchemy async session, or ``None`` for mock-data mode.
    cache:
        Async cache client with ``get``/``set`` methods, or ``None``.
    """

    def __init__(self, db_session: Any = None, cache: Any = None) -> None:
        self._db = db_session
        self._cache = cache

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    async def _cache_get(self, key: str) -> Optional[Any]:
        if self._cache is None:
            return None
        try:
            return await self._cache.get(key)
        except Exception:
            return None

    async def _cache_set(self, key: str, value: Any) -> None:
        if self._cache is None:
            return
        try:
            await self._cache.set(key, value, ex=_CACHE_TTL)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_all_teams(self, season: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all NHL teams for a given season."""
        season = season or _current_season()
        cache_key = f"teams:all:{season}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed get_all_teams not yet implemented")

        result = list(_MOCK_TEAMS)
        await self._cache_set(cache_key, result)
        return result

    async def get_teams(
        self,
        active_only: bool = True,
        conference: Optional[str] = None,
        division: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return a filtered, paginated list of teams."""
        cache_key = f"teams:list:{active_only}:{conference}:{division}:{offset}:{limit}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed get_teams not yet implemented")

        teams = list(_MOCK_TEAMS)
        if active_only:
            teams = [t for t in teams if t.get("active", True)]
        if conference:
            teams = [t for t in teams if t.get("conference", "").lower() == conference.lower()]
        if division:
            teams = [t for t in teams if t.get("division", "").lower() == division.lower()]

        result = teams[offset: offset + limit]
        await self._cache_set(cache_key, result)
        return result

    async def get_team_by_id(self, team_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Return a team dict by numeric ID or abbreviation."""
        cache_key = f"teams:by_id:{team_id}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed get_team_by_id not yet implemented")

        if isinstance(team_id, str):
            team = _TEAM_BY_ABBREV.get(team_id.upper())
        else:
            team = _TEAM_BY_ID.get(team_id)

        if team is None:
            return None

        await self._cache_set(cache_key, team)
        return team

    async def get_team_profile(self, team_id_or_abbrev: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Return team dict enriched with a current-season roster."""
        season = _current_season()
        cache_key = f"teams:profile:{team_id_or_abbrev}:{season}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        team = await self.get_team_by_id(team_id_or_abbrev)
        if team is None:
            return None

        profile = dict(team)
        profile["roster"] = _mock_roster(team["id"], season, include_stats=True)
        await self._cache_set(cache_key, profile)
        return profile

    async def get_team_stats(
        self,
        team_id: int,
        season: Optional[str] = None,
        stat_type: str = "regular",
        include_fatigue: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Return seasonal stats for a team."""
        season = season or _current_season()
        cache_key = f"teams:stats:{team_id}:{season}:{stat_type}:{include_fatigue}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        team = await self.get_team_by_id(team_id)
        if team is None:
            return None

        r = _rng(team_id, season, stat_type)
        gp = r.randint(60, 82)
        stats: Dict[str, Any] = {
            "team_id": team_id,
            "team": team.get("abbreviation"),
            "season": season,
            "stat_type": stat_type,
            "games_played": gp,
            "wins": r.randint(25, 55),
            "losses": r.randint(15, 40),
            "ot_losses": r.randint(3, 15),
            "goals_for": r.randint(180, 310),
            "goals_against": r.randint(180, 310),
            "goals_for_per_game": round(r.uniform(2.5, 3.8), 2),
            "goals_against_per_game": round(r.uniform(2.4, 3.6), 2),
            "save_percentage": round(r.gauss(0.912, 0.008), 4),
            "power_play_pct": round(r.uniform(0.15, 0.28), 3),
            "penalty_kill_pct": round(r.uniform(0.76, 0.88), 3),
            "shots_for_per_game": round(r.uniform(28.0, 34.0), 1),
            "shots_against_per_game": round(r.uniform(27.5, 33.5), 1),
            "faceoff_win_pct": round(r.uniform(0.47, 0.54), 3),
        }
        if include_fatigue:
            stats["fatigue_metrics"] = {
                "avg_fatigue_index": round(r.uniform(35.0, 58.0), 2),
                "back_to_back_record_wins": r.randint(3, 10),
                "back_to_back_record_losses": r.randint(3, 10),
                "total_travel_miles": round(r.uniform(30000, 75000), 0),
            }
        await self._cache_set(cache_key, stats)
        return stats

    async def get_roster(
        self,
        team_id: int,
        season: Optional[str] = None,
        include_prospects: bool = False,
        include_stats: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return team roster with optional stats."""
        season = season or _current_season()
        cache_key = f"teams:roster:{team_id}:{season}:{include_prospects}:{include_stats}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed get_roster not yet implemented")

        roster = _mock_roster(team_id, season, include_stats)
        if include_prospects:
            r = _rng(team_id, season, "prospects")
            for i in range(3):
                pid = team_id * 10000 + i
                roster.append({
                    "player_id": pid,
                    "full_name": f"Prospect {pid}",
                    "position": r.choice(["C", "LW", "D"]),
                    "jersey_number": None,
                    "age": r.randint(18, 22),
                    "team_id": team_id,
                    "prospect": True,
                })
        await self._cache_set(cache_key, roster)
        return roster

    async def get_team_schedule(
        self,
        team_id: int,
        season: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return team schedule as a list of game dicts."""
        season = season or _current_season()
        cache_key = f"teams:schedule:{team_id}:{season}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed get_team_schedule not yet implemented")

        schedule = _mock_schedule(team_id, season, n_games=30)
        await self._cache_set(cache_key, schedule)
        return schedule

    async def get_team_goalie_rotation(
        self,
        team_id: int,
        season: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return goalie usage breakdown for the season."""
        season = season or _current_season()
        cache_key = f"teams:goalie_rotation:{team_id}:{season}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed goalie rotation not yet implemented")

        r = _rng(team_id, season, "goalie_rotation")
        total_gp = r.randint(72, 82)
        starter_gp = r.randint(int(total_gp * 0.55), int(total_gp * 0.75))
        backup_gp = total_gp - starter_gp

        def _goalie_stats(pid: int, gp: int) -> Dict[str, Any]:
            gr = _rng(pid, season)
            sv = round(gr.gauss(0.912, 0.010), 4)
            return {
                "player_id": pid,
                "games_played": gp,
                "games_started": gp,
                "wins": gr.randint(int(gp * 0.45), int(gp * 0.65)),
                "save_pct": max(0.880, min(0.940, sv)),
                "gaa": round(gr.gauss(2.75, 0.35), 2),
                "shutouts": gr.randint(0, 6),
                "quality_start_pct": round(gr.uniform(0.45, 0.68), 3),
            }

        starter_id = team_id * 100 + 1
        backup_id = team_id * 100 + 2
        result: Dict[str, Any] = {
            "team_id": team_id,
            "season": season,
            "total_games": total_gp,
            "starter": _goalie_stats(starter_id, starter_gp),
            "backup": _goalie_stats(backup_id, backup_gp),
            "starter_share_pct": round(starter_gp / total_gp, 3),
        }
        await self._cache_set(cache_key, result)
        return result

    async def get_fatigue_analysis(
        self,
        team_id: int,
        analysis_date: Optional[date] = None,
        window_days: int = 14,
        include_predictions: bool = False,
    ) -> Dict[str, Any]:
        """Return team-wide fatigue analysis."""
        analysis_date = analysis_date or date.today()
        cache_key = f"teams:fatigue:{team_id}:{analysis_date}:{window_days}:{include_predictions}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        r = _rng(team_id, str(analysis_date), window_days)
        player_fatigue = [
            {
                "player_id": team_id * 100 + i,
                "position": r.choice(["C", "LW", "RW", "D", "G"]),
                "fatigue_index": round(r.uniform(20.0, 80.0), 2),
                "games_in_window": r.randint(3, 10),
                "travel_miles_in_window": round(r.uniform(0, 5000), 0),
                "back_to_back_count": r.randint(0, 3),
                "risk_level": r.choice(["low", "low", "medium", "medium", "high"]),
            }
            for i in range(20)
        ]
        result: Dict[str, Any] = {
            "team_id": team_id,
            "analysis_date": analysis_date.isoformat(),
            "window_days": window_days,
            "avg_team_fatigue_index": round(sum(p["fatigue_index"] for p in player_fatigue) / len(player_fatigue), 2),
            "high_fatigue_players": sum(1 for p in player_fatigue if p["risk_level"] == "high"),
            "player_fatigue": player_fatigue,
        }
        if include_predictions:
            result["predictions"] = {
                "fatigue_trend_7d": r.choice(["increasing", "stable", "decreasing"]),
                "expected_performance_impact": round(r.uniform(-0.015, 0.005), 4),
            }
        await self._cache_set(cache_key, result)
        return result

    async def get_back_to_back_analysis(
        self,
        team_id: int,
        season: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return back-to-back game performance analysis for a team."""
        season = season or _current_season()
        cache_key = f"teams:b2b:{team_id}:{season}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        r = _rng(team_id, season, "b2b")
        b2b_count = r.randint(10, 16)
        b2b_wins = r.randint(3, b2b_count - 1)
        result: Dict[str, Any] = {
            "team_id": team_id,
            "season": season,
            "back_to_back_games": b2b_count,
            "b2b_wins": b2b_wins,
            "b2b_losses": b2b_count - b2b_wins,
            "b2b_win_pct": round(b2b_wins / b2b_count, 3),
            "regular_win_pct": round(r.uniform(0.48, 0.58), 3),
            "save_pct_b2b": round(r.gauss(0.907, 0.009), 4),
            "save_pct_regular": round(r.gauss(0.913, 0.008), 4),
            "goals_against_avg_b2b": round(r.gauss(3.10, 0.35), 2),
            "goals_against_avg_regular": round(r.gauss(2.80, 0.30), 2),
        }
        await self._cache_set(cache_key, result)
        return result

    async def get_standings_info(
        self,
        team_id: int,
        season: Optional[str] = None,
        include_projections: bool = False,
    ) -> Dict[str, Any]:
        """Return standings information for a team."""
        season = season or _current_season()
        cache_key = f"teams:standings:{team_id}:{season}:{include_projections}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        team = await self.get_team_by_id(team_id)
        r = _rng(team_id, season)
        gp = r.randint(60, 82)
        wins = r.randint(25, 52)
        losses = r.randint(15, 40)
        otl = gp - wins - losses
        points = wins * 2 + max(0, otl)
        standings: Dict[str, Any] = {
            "team_id": team_id,
            "team": team.get("abbreviation") if team else None,
            "season": season,
            "games_played": gp,
            "wins": wins,
            "losses": losses,
            "ot_losses": max(0, otl),
            "points": points,
            "points_pct": round(points / (gp * 2), 3),
            "division_rank": r.randint(1, 8),
            "conference_rank": r.randint(1, 16),
            "league_rank": r.randint(1, 32),
            "playoff_position": r.choice(["In", "In", "Bubble", "Out"]),
        }
        if include_projections:
            remaining = 82 - gp
            standings["projections"] = {
                "projected_final_points": points + r.randint(int(remaining * 0.35), int(remaining * 0.65)) * 2,
                "playoff_probability": round(r.uniform(0.20, 0.90), 3),
                "model_confidence": round(r.uniform(0.65, 0.85), 3),
            }
        await self._cache_set(cache_key, standings)
        return standings

    async def get_performance_trends(
        self,
        team_id: int,
        season: Optional[str] = None,
        window_size: int = 10,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return rolling performance trends for a team."""
        season = season or _current_season()
        metrics = metrics or ["goals_for", "goals_against", "shots_for", "save_percentage"]
        cache_key = f"teams:perf_trends:{team_id}:{season}:{window_size}:{','.join(metrics)}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        r = _rng(team_id, season, "perf_trends")
        n_windows = r.randint(6, 10)
        windows = []
        for w in range(n_windows):
            entry: Dict[str, Any] = {"window": w + 1, "games": f"{w * window_size + 1}-{(w + 1) * window_size}"}
            for metric in metrics:
                if metric == "save_percentage":
                    entry[metric] = round(r.gauss(0.912, 0.009), 4)
                elif metric in ("goals_for", "goals_against"):
                    entry[metric] = round(r.uniform(2.3, 3.8), 2)
                elif metric == "shots_for":
                    entry[metric] = round(r.uniform(28.0, 34.0), 1)
                else:
                    entry[metric] = round(r.uniform(0.40, 0.80), 3)
            windows.append(entry)

        result: Dict[str, Any] = {
            "team_id": team_id,
            "season": season,
            "window_size": window_size,
            "metrics": metrics,
            "trend_data": windows,
        }
        await self._cache_set(cache_key, result)
        return result

    async def get_line_combinations(
        self,
        team_id: int,
        season: Optional[str] = None,
        include_performance: bool = True,
    ) -> Dict[str, Any]:
        """Return forward line, defensive pairing, and PP/PK unit data."""
        season = season or _current_season()
        cache_key = f"teams:lines:{team_id}:{season}:{include_performance}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        r = _rng(team_id, season, "lines")
        base_pid = team_id * 100

        def _line(players: List[int], label: str) -> Dict[str, Any]:
            entry: Dict[str, Any] = {"label": label, "player_ids": players}
            if include_performance:
                entry["toi_per_game"] = round(r.uniform(5.0, 22.0), 1)
                entry["corsi_pct"] = round(r.uniform(0.44, 0.58), 3)
                entry["xg_for_per_60"] = round(r.uniform(1.5, 4.5), 2)
                entry["goals_for_per_60"] = round(r.uniform(1.0, 4.0), 2)
            return entry

        result: Dict[str, Any] = {
            "team_id": team_id,
            "season": season,
            "forward_lines": [
                _line([base_pid + 1, base_pid + 2, base_pid + 3], "Line 1"),
                _line([base_pid + 4, base_pid + 5, base_pid + 6], "Line 2"),
                _line([base_pid + 7, base_pid + 8, base_pid + 9], "Line 3"),
                _line([base_pid + 10, base_pid + 11, base_pid + 12], "Line 4"),
            ],
            "defensive_pairings": [
                _line([base_pid + 13, base_pid + 14], "Pair 1"),
                _line([base_pid + 15, base_pid + 16], "Pair 2"),
                _line([base_pid + 17, base_pid + 18], "Pair 3"),
            ],
            "power_play_units": [
                _line([base_pid + 1, base_pid + 2, base_pid + 4, base_pid + 13, base_pid + 14], "PP1"),
                _line([base_pid + 5, base_pid + 7, base_pid + 9, base_pid + 15, base_pid + 16], "PP2"),
            ],
            "penalty_kill_units": [
                _line([base_pid + 3, base_pid + 6, base_pid + 13, base_pid + 15], "PK1"),
                _line([base_pid + 8, base_pid + 10, base_pid + 14, base_pid + 17], "PK2"),
            ],
        }
        await self._cache_set(cache_key, result)
        return result

    async def refresh_team_data(
        self,
        team_id: int,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Trigger a data refresh for the team. Returns update metadata."""
        # In production this would call the NHL Stats API and update the DB.
        return {
            "team_id": team_id,
            "forced": force,
            "updated_at": date.today().isoformat(),
            "status": "success",
        }
