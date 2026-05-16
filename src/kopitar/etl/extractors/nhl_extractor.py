"""
NHL Data Extractor

Primary extractor for current NHL data using the post-2023 NHL API.
Handles games, players, teams, and real-time data extraction.
"""

import asyncio
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Union

from .base_extractor import BaseExtractor, ExtractionResult
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class NHLDataExtractor(BaseExtractor):
    """
    Extractor for the current NHL API (web + stats endpoints).

    Handles:
    - Game data (schedule, boxscores)
    - Player data (biographical info, stats)
    - Team rosters
    - Goalie summary stats
    - Standings
    """

    def __init__(self) -> None:
        super().__init__(
            rate_limit_key="nhl_api",
            requests_per_minute=settings.NHL_API_RATE_LIMIT,
            timeout=settings.NHL_API_TIMEOUT,
        )

        self.web_base_url: str = settings.NHL_WEB_API_BASE_URL
        self.stats_base_url: str = settings.NHL_STATS_API_BASE_URL

        # Endpoint templates — keyed names used by the dispatch table in extract()
        self.endpoints: Dict[str, str] = {
            "schedule": f"{self.web_base_url}/schedule/{{date}}",
            "game_boxscore": f"{self.web_base_url}/gamecenter/{{game_id}}/boxscore",
            "player": f"{self.web_base_url}/player/{{player_id}}/landing",
            "team_roster": f"{self.web_base_url}/roster/{{team_abbrev}}/{{season_or_current}}",
            "goalie_stats": (
                f"{self.stats_base_url}/goalie/summary"
                "?limit={limit}&start={start}&sort={sort}&cayenneExp=seasonId={{season}}"
            ),
            "standings": f"{self.web_base_url}/standings/{{date}}",
            "team_schedule_season": f"{self.web_base_url}/club-schedule-season/{{team_abbrev}}/{{season}}",
        }

    async def extract(self, data_type: str, **kwargs: Any) -> ExtractionResult:
        """Route extraction requests to the appropriate method."""
        dispatch = {
            "teams": self.extract_teams,
            "schedule": self.extract_schedule,
            "game": self.extract_game,
            "player": self.extract_player,
            "team_roster": self.extract_team_roster,
            "goalie_stats": self.extract_goalie_stats,
            "standings": self.extract_standings,
            "team_schedule": self.extract_team_schedule,
        }

        handler = dispatch.get(data_type)
        if handler is None:
            return self.create_result(
                success=False, error=f"Unknown data type: {data_type}"
            )

        try:
            return await handler(**kwargs)
        except Exception as exc:
            logger.error("Extraction failed for %s: %s", data_type, exc)
            return self.create_result(success=False, error=str(exc))

    # ------------------------------------------------------------------
    # extract_teams — uses roster endpoint for each known abbreviation
    # since the new API has no single "list all teams" endpoint.
    # Callers should prefer extract_team_roster() for individual teams.
    # ------------------------------------------------------------------

    async def extract_teams(self, season: Optional[str] = None) -> ExtractionResult:
        """
        Return a lightweight list of known NHL team abbreviations.

        The new NHL API does not have a single /teams list endpoint.
        We return the canonical 32 active franchises; use extract_team_roster()
        to get full roster details for any individual team.
        """
        nhl_teams = [
            "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ",
            "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NSH",
            "NJD", "NYI", "NYR", "OTT", "PHI", "PIT", "SJS", "SEA",
            "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WSH", "WPG",
        ]
        teams = [{"abbreviation": abbrev} for abbrev in nhl_teams]
        return self.create_result(
            success=True,
            data=teams,
            metadata={"count": len(teams), "season": season},
        )

    # ------------------------------------------------------------------
    # extract_schedule
    # ------------------------------------------------------------------

    async def extract_schedule(
        self,
        start_date: date,
        end_date: date,
        team_abbrev: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Extract games for every date in [start_date, end_date].

        New API returns one date at a time via /schedule/{YYYY-MM-DD}.
        When team_abbrev is provided only games involving that team are kept.
        """
        games: List[Dict[str, Any]] = []
        current = start_date

        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            url = self.endpoints["schedule"].format(date=date_str)
            data = await self.extract_json(url)

            for week_entry in data.get("gameWeek", []):
                for game in week_entry.get("games", []):
                    away = game.get("awayTeam", {})
                    home = game.get("homeTeam", {})

                    if team_abbrev and team_abbrev not in (
                        away.get("abbrev"),
                        home.get("abbrev"),
                    ):
                        continue

                    games.append(
                        {
                            "nhl_id": game.get("id"),
                            "season": game.get("season"),
                            "game_type": game.get("gameType"),
                            "date_time": game.get("startTimeUTC"),
                            "venue": game.get("venue", {}).get("default"),
                            "away_team": {
                                "abbrev": away.get("abbrev"),
                                "id": away.get("id"),
                                "name": away.get("name", {}).get("default"),
                                "score": away.get("score"),
                            },
                            "home_team": {
                                "abbrev": home.get("abbrev"),
                                "id": home.get("id"),
                                "name": home.get("name", {}).get("default"),
                                "score": home.get("score"),
                            },
                            "game_state": game.get("gameState"),
                        }
                    )

            current += timedelta(days=1)
            await asyncio.sleep(0.1)  # polite pacing between date calls

        return self.create_result(
            success=True,
            data=games,
            metadata={
                "count": len(games),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "team_abbrev": team_abbrev,
            },
        )

    # ------------------------------------------------------------------
    # extract_game  (boxscore)
    # ------------------------------------------------------------------

    async def extract_game(self, game_id: int) -> ExtractionResult:
        """
        Extract boxscore data for a completed or in-progress game.

        New API response: {"id": ..., "gameDate": "...",
        "playerByGameStats": {"homeTeam": {"goalies": [...]}, "awayTeam": {...}}}
        """
        url = self.endpoints["game_boxscore"].format(game_id=game_id)
        data = await self.extract_json(url)

        player_stats = data.get("playerByGameStats", {})
        home_goalies = (
            player_stats.get("homeTeam", {}).get("goalies", [])
        )
        away_goalies = (
            player_stats.get("awayTeam", {}).get("goalies", [])
        )

        def _parse_goalie(raw: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "player_id": raw.get("playerId"),
                "name": raw.get("name", {}).get("default"),
                "saves": raw.get("saves"),
                "shots_against": raw.get("shotsAgainst"),
                "save_pct": raw.get("savePctg"),
                "goals_against": raw.get("goalsAgainst"),
                "toi": raw.get("toi"),
                "starter": raw.get("starter", False),
            }

        game_data = {
            "nhl_id": data.get("id"),
            "game_date": data.get("gameDate"),
            "game_type": data.get("gameType"),
            "game_state": data.get("gameState"),
            "period": data.get("period"),
            "away_team": data.get("awayTeam", {}),
            "home_team": data.get("homeTeam", {}),
            "home_goalies": [_parse_goalie(g) for g in home_goalies],
            "away_goalies": [_parse_goalie(g) for g in away_goalies],
            "raw": data,
        }

        return self.create_result(
            success=True,
            data=game_data,
            metadata={
                "game_id": game_id,
                "game_state": game_data["game_state"],
            },
        )

    # ------------------------------------------------------------------
    # extract_player
    # ------------------------------------------------------------------

    async def extract_player(
        self, player_id: int, season: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract player biographical info and career stats.

        New API response uses nested localised strings:
        {"playerId": ..., "firstName": {"default": "..."}, ...}
        """
        url = self.endpoints["player"].format(player_id=player_id)
        data = await self.extract_json(url)

        player_data = {
            "player_id": data.get("playerId"),
            "first_name": data.get("firstName", {}).get("default"),
            "last_name": data.get("lastName", {}).get("default"),
            "position": data.get("position"),
            "shoots_catches": data.get("shootsCatches"),
            "birth_date": data.get("birthDate"),
            "birth_city": data.get("birthCity", {}).get("default"),
            "birth_country": data.get("birthCountryCode"),
            "height_inches": data.get("heightInInches"),
            "weight_pounds": data.get("weightInPounds"),
            "current_team_abbrev": data.get("currentTeamAbbrev"),
            "jersey_number": data.get("sweaterNumber"),
            "season_stats": data.get("seasonTotals", []),
        }

        return self.create_result(
            success=True,
            data=player_data,
            metadata={"player_id": player_id, "season": season},
        )

    # ------------------------------------------------------------------
    # extract_team_roster
    # ------------------------------------------------------------------

    async def extract_team_roster(
        self, team_abbrev: str, season: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract team roster.

        ``team_abbrev`` is the three-letter code, e.g. "TOR".
        When no season is provided the current roster is returned.
        """
        season_or_current = season if season else "current"
        url = self.endpoints["team_roster"].format(
            team_abbrev=team_abbrev,
            season_or_current=season_or_current,
        )
        data = await self.extract_json(url)

        def _parse_player(raw: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "player_id": raw.get("id"),
                "first_name": raw.get("firstName", {}).get("default"),
                "last_name": raw.get("lastName", {}).get("default"),
                "jersey_number": raw.get("sweaterNumber"),
                "position": raw.get("positionCode"),
                "shoots_catches": raw.get("shootsCatches"),
                "height_inches": raw.get("heightInInches"),
                "weight_pounds": raw.get("weightInPounds"),
            }

        roster: List[Dict[str, Any]] = []
        for group in ("forwards", "defensemen", "goalies"):
            for raw_player in data.get(group, []):
                entry = _parse_player(raw_player)
                entry["roster_group"] = group
                roster.append(entry)

        return self.create_result(
            success=True,
            data=roster,
            metadata={
                "team_abbrev": team_abbrev,
                "season": season,
                "player_count": len(roster),
            },
        )

    # ------------------------------------------------------------------
    # extract_goalie_stats
    # ------------------------------------------------------------------

    async def extract_goalie_stats(
        self,
        season: str,
        limit: int = 100,
        start: int = 0,
        sort: str = "wins",
    ) -> ExtractionResult:
        """Extract goalie summary stats from the Stats API."""
        url = self.endpoints["goalie_stats"].format(
            limit=limit, start=start, sort=sort, season=season
        )
        data = await self.extract_json(url)

        goalies: List[Dict[str, Any]] = []
        for raw in data.get("data", []):
            goalies.append(
                {
                    "player_id": raw.get("playerId"),
                    "player_name": raw.get("skaterFullName"),
                    "team_abbrev": raw.get("teamAbbrevs"),
                    "season_id": raw.get("seasonId"),
                    "games_played": raw.get("gamesPlayed"),
                    "games_started": raw.get("gamesStarted"),
                    "wins": raw.get("wins"),
                    "losses": raw.get("losses"),
                    "ot_losses": raw.get("otLosses"),
                    "save_pct": raw.get("savePct"),
                    "gaa": raw.get("goalsAgainstAverage"),
                    "shutouts": raw.get("shutouts"),
                    "time_on_ice": raw.get("timeOnIce"),
                }
            )

        return self.create_result(
            success=True,
            data=goalies,
            metadata={
                "season": season,
                "count": len(goalies),
                "total": data.get("total"),
            },
        )

    # ------------------------------------------------------------------
    # extract_standings
    # ------------------------------------------------------------------

    async def extract_standings(
        self, query_date: Optional[Union[date, str]] = None
    ) -> ExtractionResult:
        """
        Extract league standings.

        Defaults to today's date when query_date is not provided.
        """
        if query_date is None:
            query_date = date.today()
        if isinstance(query_date, date):
            query_date = query_date.strftime("%Y-%m-%d")

        url = self.endpoints["standings"].format(date=query_date)
        data = await self.extract_json(url)

        return self.create_result(
            success=True,
            data=data.get("standings", []),
            metadata={
                "date": query_date,
                "team_count": len(data.get("standings", [])),
            },
        )

    # ------------------------------------------------------------------
    # extract_team_schedule
    # ------------------------------------------------------------------

    async def extract_team_schedule(
        self, team_abbrev: str, season: str
    ) -> ExtractionResult:
        """Extract the full regular-season schedule for one team."""
        url = self.endpoints["team_schedule_season"].format(
            team_abbrev=team_abbrev, season=season
        )
        data = await self.extract_json(url)

        games: List[Dict[str, Any]] = []
        for game in data.get("games", []):
            away = game.get("awayTeam", {})
            home = game.get("homeTeam", {})
            games.append(
                {
                    "nhl_id": game.get("id"),
                    "game_date": game.get("gameDate"),
                    "game_type": game.get("gameType"),
                    "game_state": game.get("gameState"),
                    "away_team": away.get("abbrev"),
                    "home_team": home.get("abbrev"),
                    "away_score": away.get("score"),
                    "home_score": home.get("score"),
                    "venue": game.get("venue", {}).get("default"),
                }
            )

        return self.create_result(
            success=True,
            data=games,
            metadata={
                "team_abbrev": team_abbrev,
                "season": season,
                "game_count": len(games),
            },
        )

    # ------------------------------------------------------------------
    # Convenience: batch-extract multiple games concurrently
    # ------------------------------------------------------------------

    async def extract_multiple_games(
        self, game_ids: List[int]
    ) -> List[ExtractionResult]:
        tasks = [self.extract_game(gid) for gid in game_ids]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: List[ExtractionResult] = []
        for gid, result in zip(game_ids, raw_results):
            if isinstance(result, Exception):
                results.append(
                    self.create_result(
                        success=False,
                        error=f"Exception extracting game {gid}: {result}",
                    )
                )
            else:
                results.append(result)  # type: ignore[arg-type]

        return results
