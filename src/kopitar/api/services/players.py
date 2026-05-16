"""
Player Service

Handles player search, profiles, game logs, career analysis, and predictions.
Falls back to plausible mock data when no database session is provided.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

_CACHE_TTL = 300

# Realistic mock pool of NHL goalies and skaters
_MOCK_PLAYERS = [
    {"id": 8478402, "nhl_id": 8478402, "full_name": "Connor McDavid",   "first_name": "Connor",  "last_name": "McDavid",   "position": "C",  "team": "EDM", "team_id": 22, "active": True,  "age": 28, "shoots": "L", "height": "6'1\"", "weight": 193},
    {"id": 8477934, "nhl_id": 8477934, "full_name": "Nathan MacKinnon",  "first_name": "Nathan",  "last_name": "MacKinnon", "position": "C",  "team": "COL", "team_id": 21, "active": True,  "age": 29, "shoots": "R", "height": "6'0\"", "weight": 205},
    {"id": 8479318, "nhl_id": 8479318, "full_name": "David Pastrnak",    "first_name": "David",   "last_name": "Pastrnak",  "position": "RW", "team": "BOS", "team_id": 6,  "active": True,  "age": 28, "shoots": "R", "height": "6'0\"", "weight": 194},
    {"id": 8480069, "nhl_id": 8480069, "full_name": "Auston Matthews",   "first_name": "Auston",  "last_name": "Matthews",  "position": "C",  "team": "TOR", "team_id": 10, "active": True,  "age": 27, "shoots": "L", "height": "6'3\"", "weight": 215},
    {"id": 8476468, "nhl_id": 8476468, "full_name": "Sidney Crosby",     "first_name": "Sidney",  "last_name": "Crosby",    "position": "C",  "team": "PIT", "team_id": 5,  "active": True,  "age": 37, "shoots": "L", "height": "5'11\"","weight": 200},
    {"id": 8476389, "nhl_id": 8476389, "full_name": "Alex Ovechkin",     "first_name": "Alex",    "last_name": "Ovechkin",  "position": "LW", "team": "WSH", "team_id": 15, "active": True,  "age": 39, "shoots": "R", "height": "6'3\"", "weight": 236},
    # Goalies
    {"id": 8478009, "nhl_id": 8478009, "full_name": "Andrei Vasilevskiy","first_name": "Andrei",  "last_name": "Vasilevskiy","position": "G",  "team": "TBL", "team_id": 14, "active": True,  "age": 30, "catches": "L", "height": "6'3\"", "weight": 225},
    {"id": 8475311, "nhl_id": 8475311, "full_name": "Marc-Andre Fleury", "first_name": "Marc-Andre","last_name":"Fleury",   "position": "G",  "team": "MTL", "team_id": 8,  "active": True,  "age": 39, "catches": "L", "height": "6'2\"", "weight": 185},
    {"id": 8477465, "nhl_id": 8477465, "full_name": "Thatcher Demko",    "first_name": "Thatcher","last_name": "Demko",     "position": "G",  "team": "VAN", "team_id": 23, "active": True,  "age": 29, "catches": "L", "height": "6'4\"", "weight": 192},
    {"id": 8479979, "nhl_id": 8479979, "full_name": "Igor Shesterkin",   "first_name": "Igor",    "last_name": "Shesterkin","position": "G",  "team": "NYR", "team_id": 3,  "active": True,  "age": 29, "catches": "L", "height": "6'1\"", "weight": 182},
    {"id": 8477293, "nhl_id": 8477293, "full_name": "Sergei Bobrovsky",  "first_name": "Sergei",  "last_name": "Bobrovsky", "position": "G",  "team": "FLA", "team_id": 13, "active": True,  "age": 36, "catches": "L", "height": "6'2\"", "weight": 182},
    {"id": 8475831, "nhl_id": 8475831, "full_name": "Tuukka Rask",       "first_name": "Tuukka",  "last_name": "Rask",      "position": "G",  "team": "BOS", "team_id": 6,  "active": False, "age": 37, "catches": "L", "height": "6'3\"", "weight": 176},
]

_GOALIE_IDS = {p["id"] for p in _MOCK_PLAYERS if p["position"] == "G"}

_SEASONS = ["20252026", "20242025", "20232024", "20222023", "20212022"]


def _seed(*args: Any) -> int:
    return hash(tuple(str(a) for a in args)) & 0xFFFFFFFF


def _rng(*args: Any) -> random.Random:
    return random.Random(_seed(*args))


def _current_season() -> str:
    today = date.today()
    return f"{today.year}{today.year + 1}" if today.month >= 9 else f"{today.year - 1}{today.year}"


def _goalie_season_stats(player_id: int, season: str) -> Dict[str, Any]:
    r = _rng(player_id, season, "goalie_season")
    gp = r.randint(32, 65)
    sv_pct = round(r.gauss(0.913, 0.010), 4)
    sv_pct = max(0.880, min(0.940, sv_pct))
    gaa = round(r.gauss(2.75, 0.40), 2)
    gaa = max(1.80, min(4.20, gaa))
    gsax = round(r.gauss(4.0, 6.5), 2)
    hdsv = round(r.gauss(0.830, 0.025), 3)
    hdsv = max(0.770, min(0.890, hdsv))
    wins = r.randint(int(gp * 0.40), int(gp * 0.65))
    losses = r.randint(int((gp - wins) * 0.50), gp - wins)
    otl = gp - wins - losses
    return {
        "player_id": player_id,
        "season": season,
        "games_played": gp,
        "wins": wins,
        "losses": losses,
        "ot_losses": max(0, otl),
        "save_pct": sv_pct,
        "gaa": gaa,
        "gsax": gsax,
        "hdsv_pct": hdsv,
        "shutouts": r.randint(0, 7),
        "quality_start_pct": round(r.uniform(0.45, 0.68), 3),
        "really_bad_start_pct": round(r.uniform(0.05, 0.18), 3),
        "shots_against_per_game": round(r.uniform(27.5, 33.5), 1),
    }


def _skater_season_stats(player_id: int, season: str) -> Dict[str, Any]:
    r = _rng(player_id, season, "skater_season")
    gp = r.randint(45, 82)
    return {
        "player_id": player_id,
        "season": season,
        "games_played": gp,
        "goals": r.randint(5, 55),
        "assists": r.randint(10, 75),
        "points": 0,  # filled below
        "plus_minus": r.randint(-20, 30),
        "penalty_minutes": r.randint(4, 80),
        "shots": r.randint(60, 300),
        "shooting_pct": round(r.uniform(0.06, 0.20), 3),
        "toi_per_game": f"{r.randint(13, 22)}:{r.randint(0, 59):02d}",
        "power_play_points": r.randint(0, 30),
        "short_handed_points": r.randint(0, 5),
    }


def _player_to_dict(p: Dict[str, Any]) -> Dict[str, Any]:
    """Return a sanitised player response dict."""
    return {k: v for k, v in p.items()}


class PlayerService:
    """
    Service for player data operations.

    Parameters
    ----------
    db_session:
        SQLAlchemy async session, or ``None`` for mock-data mode.
    cache:
        Async cache client, or ``None``.
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

    async def get_players(
        self,
        position: Optional[str] = None,
        team_id: Optional[int] = None,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return a filtered, paginated list of players."""
        cache_key = f"players:list:{position}:{team_id}:{active_only}:{offset}:{limit}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed get_players not yet implemented")

        players = list(_MOCK_PLAYERS)
        if position:
            # "F" matches LW / RW / C / F
            if position == "F":
                players = [p for p in players if p["position"] in ("LW", "RW", "C", "F")]
            else:
                players = [p for p in players if p["position"] == position]
        if team_id is not None:
            players = [p for p in players if p.get("team_id") == team_id]
        if active_only:
            players = [p for p in players if p.get("active", True)]

        result = [_player_to_dict(p) for p in players[offset: offset + limit]]
        await self._cache_set(cache_key, result)
        return result

    async def search_players(
        self,
        query: str,
        position: Optional[str] = None,
        season: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search players by name or team.

        Returns
        -------
        List of player dicts matching the query.
        """
        cache_key = f"players:search:{query}:{position}:{season}:{limit}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed search not yet implemented")

        q = query.lower()
        results = [
            p for p in _MOCK_PLAYERS
            if q in p["full_name"].lower() or q in p.get("team", "").lower()
        ]
        if position:
            if position == "F":
                results = [p for p in results if p["position"] in ("LW", "RW", "C", "F")]
            else:
                results = [p for p in results if p["position"] == position]

        out = [_player_to_dict(p) for p in results[:limit]]
        await self._cache_set(cache_key, out)
        return out

    async def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Return a single player dict by internal or NHL ID."""
        cache_key = f"players:by_id:{player_id}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed get_player_by_id not yet implemented")

        match = next((p for p in _MOCK_PLAYERS if p["id"] == player_id or p["nhl_id"] == player_id), None)
        if match is None:
            # Return a synthetic player so the API doesn't 404 during dev
            r = _rng(player_id, "profile")
            match = {
                "id": player_id,
                "nhl_id": player_id,
                "full_name": f"Player {player_id}",
                "first_name": "Player",
                "last_name": str(player_id),
                "position": r.choice(["G", "C", "LW", "RW", "D"]),
                "team": r.choice(["BOS", "TOR", "EDM", "MTL", "NYR"]),
                "team_id": r.randint(1, 32),
                "active": True,
                "age": r.randint(22, 38),
                "height": "6'2\"",
                "weight": r.randint(180, 230),
            }

        result = _player_to_dict(match)
        await self._cache_set(cache_key, result)
        return result

    async def get_player_profile(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Return a full player profile including career stats."""
        base = await self.get_player_by_id(player_id)
        if base is None:
            return None

        is_goalie = base.get("position") == "G"
        seasons_played = [
            (_goalie_season_stats if is_goalie else _skater_season_stats)(player_id, s)
            for s in _SEASONS[:4]
        ]
        # Fix points for skaters
        if not is_goalie:
            for s in seasons_played:
                s["points"] = s["goals"] + s["assists"]

        r = _rng(player_id, "profile")
        profile = dict(base)
        profile["career_games_played"] = sum(s["games_played"] for s in seasons_played)
        profile["seasons"] = seasons_played
        profile["draft_year"] = r.randint(2004, 2020)
        profile["draft_round"] = r.randint(1, 7)
        profile["draft_pick"] = r.randint(1, 30)
        return profile

    async def get_player_stats(
        self,
        player_id: int,
        season: Optional[str] = None,
        stat_type: str = "regular",
    ) -> Optional[Dict[str, Any]]:
        """Return seasonal stats for a player."""
        season = season or _current_season()
        cache_key = f"players:stats:{player_id}:{season}:{stat_type}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        player = await self.get_player_by_id(player_id)
        if player is None:
            return None

        is_goalie = player.get("position") == "G"
        if is_goalie:
            stats = _goalie_season_stats(player_id, season)
        else:
            stats = _skater_season_stats(player_id, season)
            stats["points"] = stats["goals"] + stats["assists"]

        stats["stat_type"] = stat_type
        await self._cache_set(cache_key, stats)
        return stats

    async def get_player_game_log(
        self,
        player_id: int,
        season: Optional[str] = None,
        game_type: str = "regular",
        limit: int = 50,
        include_advanced: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return game-by-game stats for a player."""
        season = season or _current_season()
        cache_key = f"players:game_log:{player_id}:{season}:{game_type}:{limit}:{include_advanced}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        if self._db is not None:
            raise NotImplementedError("DB-backed game log not yet implemented")

        player = await self.get_player_by_id(player_id)
        is_goalie = player.get("position") == "G" if player else player_id in _GOALIE_IDS
        r = _rng(player_id, season, game_type)
        n_games = min(limit, r.randint(40, 82))
        opponents = ["BOS", "TOR", "EDM", "MTL", "NYR", "TBL", "COL", "VGK", "CAR", "FLA"]
        entries = []
        game_date = date(int(season[:4]), 10, 1)
        for i in range(n_games):
            game_date += timedelta(days=r.randint(1, 4))
            if is_goalie:
                sv_pct = round(r.gauss(0.912, 0.018), 4)
                sv_pct = max(0.820, min(0.980, sv_pct))
                entry: Dict[str, Any] = {
                    "game_date": game_date.isoformat(),
                    "opponent": r.choice(opponents),
                    "home_away": r.choice(["home", "away"]),
                    "decision": r.choice(["W", "W", "L", "OT", None]),
                    "shots_against": r.randint(20, 45),
                    "goals_against": r.randint(0, 6),
                    "save_pct": sv_pct,
                    "toi": f"{r.randint(40, 65)}:{r.randint(0, 59):02d}",
                    "quality_start": sv_pct >= 0.885,
                    "fatigue_index": round(r.uniform(20.0, 75.0), 2),
                    "back_to_back": r.random() < 0.15,
                }
                if include_advanced:
                    entry["gsax"] = round(r.gauss(0.0, 1.5), 2)
                    entry["hdsv_pct"] = round(r.gauss(0.830, 0.040), 3)
            else:
                entry = {
                    "game_date": game_date.isoformat(),
                    "opponent": r.choice(opponents),
                    "home_away": r.choice(["home", "away"]),
                    "goals": r.randint(0, 3),
                    "assists": r.randint(0, 3),
                    "points": 0,
                    "plus_minus": r.randint(-3, 4),
                    "shots": r.randint(0, 8),
                    "toi": f"{r.randint(10, 24)}:{r.randint(0, 59):02d}",
                    "fatigue_index": round(r.uniform(20.0, 70.0), 2),
                    "back_to_back": r.random() < 0.15,
                }
                entry["points"] = entry["goals"] + entry["assists"]
                if include_advanced:
                    entry["corsi_pct"] = round(r.uniform(0.40, 0.65), 3)
                    entry["xg_for"] = round(r.uniform(0.0, 3.0), 2)
            entries.append(entry)

        await self._cache_set(cache_key, entries)
        return entries

    async def get_goalie_stats(
        self,
        player_id: int,
        season: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return goalie-specific stats dict for a season."""
        season = season or _current_season()
        cache_key = f"players:goalie_stats:{player_id}:{season}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        stats = _goalie_season_stats(player_id, season)
        await self._cache_set(cache_key, stats)
        return stats

    async def get_career_analysis(
        self,
        player_id: int,
        include_projections: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Return career trajectory and peak performance analysis."""
        cache_key = f"players:career:{player_id}:{include_projections}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        player = await self.get_player_by_id(player_id)
        if player is None:
            return None

        is_goalie = player.get("position") == "G"
        seasons = [
            (_goalie_season_stats if is_goalie else _skater_season_stats)(player_id, s)
            for s in _SEASONS
        ]
        if not is_goalie:
            for s in seasons:
                s["points"] = s["goals"] + s["assists"]

        best_season = max(
            seasons,
            key=lambda s: s.get("save_pct", 0) if is_goalie else s.get("points", 0),
        )
        r = _rng(player_id, "career")
        career: Dict[str, Any] = {
            "player_id": player_id,
            "player": player,
            "seasons": seasons,
            "career_games_played": sum(s["games_played"] for s in seasons),
            "peak_season": best_season["season"],
            "age_at_peak": player.get("age", 28) - (len(_SEASONS) // 2),
        }
        if include_projections:
            career["projections"] = {
                "next_season_games": r.randint(50, 82),
                "projected_save_pct": round(r.gauss(0.912, 0.008), 4) if is_goalie else None,
                "projected_points": None if is_goalie else r.randint(30, 90),
                "confidence": round(r.uniform(0.60, 0.82), 3),
            }
        await self._cache_set(cache_key, career)
        return career

    async def get_game_log(
        self,
        player_id: int,
        season: Optional[str] = None,
        limit: int = 50,
        include_advanced: bool = False,
    ) -> List[Dict[str, Any]]:
        """Alias that matches the router call signature."""
        return await self.get_player_game_log(
            player_id=player_id,
            season=season,
            limit=limit,
            include_advanced=include_advanced,
        )

    async def compare_players(
        self,
        player_ids: List[int],
        season: Optional[str] = None,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return a comparison object for multiple players."""
        season = season or _current_season()
        metrics = metrics or ["goals", "assists", "points"]
        cache_key = f"players:compare:{','.join(str(p) for p in player_ids)}:{season}:{','.join(metrics)}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        rows = []
        for pid in player_ids:
            stats = await self.get_player_stats(pid, season)
            player = await self.get_player_by_id(pid)
            row: Dict[str, Any] = {"player_id": pid, "player_name": player.get("full_name", "") if player else ""}
            for m in metrics:
                row[m] = stats.get(m) if stats else None
            rows.append(row)

        result = {"season": season, "metrics": metrics, "comparison": rows}
        await self._cache_set(cache_key, result)
        return result

    async def find_similar_players(
        self,
        player_id: int,
        limit: int = 10,
        criteria: str = "performance",
    ) -> List[Dict[str, Any]]:
        """Return players similar to the given player."""
        cache_key = f"players:similar:{player_id}:{limit}:{criteria}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        player = await self.get_player_by_id(player_id)
        target_pos = player.get("position", "G") if player else "G"

        candidates = [p for p in _MOCK_PLAYERS if p["id"] != player_id and p["position"] == target_pos]
        r = _rng(player_id, criteria)
        r.shuffle(candidates)
        result = [_player_to_dict(p) for p in candidates[:limit]]
        await self._cache_set(cache_key, result)
        return result

    async def get_predictions(
        self,
        player_id: int,
        prediction_type: str = "performance",
        horizon_days: int = 7,
    ) -> Optional[Dict[str, Any]]:
        """Return ML-based predictions for a player."""
        cache_key = f"players:predictions:{player_id}:{prediction_type}:{horizon_days}"
        cached = await self._cache_get(cache_key)
        if cached is not None:
            return cached

        player = await self.get_player_by_id(player_id)
        is_goalie = player.get("position") == "G" if player else False
        r = _rng(player_id, prediction_type, horizon_days)

        preds = []
        for d in range(horizon_days):
            entry: Dict[str, Any] = {
                "date": (date.today() + timedelta(days=d + 1)).isoformat(),
                "confidence": round(r.uniform(0.62, 0.90), 3),
                "fatigue_index_predicted": round(r.uniform(25.0, 70.0), 2),
            }
            if prediction_type == "performance":
                if is_goalie:
                    entry["save_pct_predicted"] = round(r.gauss(0.912, 0.010), 4)
                    entry["gaa_predicted"] = round(r.gauss(2.75, 0.35), 2)
                else:
                    entry["points_predicted"] = round(r.uniform(0.0, 2.5), 2)
            elif prediction_type == "fatigue":
                entry["high_fatigue_risk"] = r.random() < 0.30
            elif prediction_type == "injury":
                entry["injury_risk_score"] = round(r.uniform(0.05, 0.40), 3)
            preds.append(entry)

        result = {
            "player_id": player_id,
            "prediction_type": prediction_type,
            "horizon_days": horizon_days,
            "predictions": preds,
            "model_version": "1.2.0",
        }
        await self._cache_set(cache_key, result)
        return result

    async def refresh_player_data(self, player_id: int, force: bool = False) -> Dict[str, Any]:
        """Background task stub: refresh player data from NHL API."""
        # In production this would call the NHL Stats API and update the DB.
        return {"player_id": player_id, "status": "refreshed", "forced": force}
