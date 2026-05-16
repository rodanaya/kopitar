"""
NHL API Endpoints

Defines all available NHL API endpoints with proper URL construction
and parameter validation. Uses the current NHL API (post-November 2023).

Web API base:   https://api-web.nhle.com/v1/
Stats API base: https://api.nhle.com/stats/rest/en/
"""

from typing import Optional, Union
from datetime import date


class NHLEndpoints:
    """NHL API endpoint definitions and URL builders."""

    # Base URLs
    WEB_BASE_URL = "https://api-web.nhle.com/v1"
    STATS_BASE_URL = "https://api.nhle.com/stats/rest/en"

    # Keep for backwards-compatibility references within the package
    BASE_URL = WEB_BASE_URL

    # ------------------------------------------------------------------ #
    # Web API path fragments
    # ------------------------------------------------------------------ #
    SCHEDULE = "/schedule"
    GAMECENTER = "/gamecenter"
    PLAYER = "/player"
    ROSTER = "/roster"
    STANDINGS = "/standings"
    CLUB_SCHEDULE_SEASON = "/club-schedule-season"

    # ------------------------------------------------------------------ #
    # Stats API path fragments
    # ------------------------------------------------------------------ #
    GOALIE_SUMMARY = "/goalie/summary"

    # ------------------------------------------------------------------ #
    # URL builders — Web API
    # ------------------------------------------------------------------ #

    @classmethod
    def schedule(cls, query_date: Union[date, str]) -> str:
        """Schedule for a single date: GET /schedule/{date}."""
        if isinstance(query_date, date):
            query_date = query_date.strftime("%Y-%m-%d")
        return f"{cls.WEB_BASE_URL}{cls.SCHEDULE}/{query_date}"

    @classmethod
    def game_boxscore(cls, game_id: int) -> str:
        """Boxscore for a finished or in-progress game."""
        return f"{cls.WEB_BASE_URL}{cls.GAMECENTER}/{game_id}/boxscore"

    @classmethod
    def player_landing(cls, player_id: int) -> str:
        """Player biographical info and career stats."""
        return f"{cls.WEB_BASE_URL}{cls.PLAYER}/{player_id}/landing"

    @classmethod
    def team_roster(cls, team_abbrev: str, season: Optional[str] = None) -> str:
        """
        Team roster endpoint.

        Uses /roster/{teamAbbrev}/current when no season is given, otherwise
        /roster/{teamAbbrev}/{season}.
        """
        segment = season if season else "current"
        return f"{cls.WEB_BASE_URL}{cls.ROSTER}/{team_abbrev}/{segment}"

    @classmethod
    def standings(cls, query_date: Union[date, str]) -> str:
        """Standings as of a specific date: GET /standings/{date}."""
        if isinstance(query_date, date):
            query_date = query_date.strftime("%Y-%m-%d")
        return f"{cls.WEB_BASE_URL}{cls.STANDINGS}/{query_date}"

    @classmethod
    def team_schedule_season(cls, team_abbrev: str, season: str) -> str:
        """Full team schedule for a season: GET /club-schedule-season/{teamAbbrev}/{season}."""
        return f"{cls.WEB_BASE_URL}{cls.CLUB_SCHEDULE_SEASON}/{team_abbrev}/{season}"

    # ------------------------------------------------------------------ #
    # URL builders — Stats API
    # ------------------------------------------------------------------ #

    @classmethod
    def goalie_stats(
        cls,
        season: str,
        limit: int = 100,
        start: int = 0,
        sort: str = "wins",
    ) -> str:
        """
        Goalie summary stats.

        Builds: GET /goalie/summary?limit=N&start=N&sort=X&cayenneExp=seasonId=SSSSSSSS
        """
        cayen = f"seasonId={season}"
        return (
            f"{cls.STATS_BASE_URL}{cls.GOALIE_SUMMARY}"
            f"?limit={limit}&start={start}&sort={sort}&cayenneExp={cayen}"
        )

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #

    @classmethod
    def validate_season(cls, season: str) -> bool:
        """Return True when season is a valid 8-digit string like '20232024'."""
        if not season or len(season) != 8:
            return False
        try:
            start_year = int(season[:4])
            end_year = int(season[4:])
            return end_year == start_year + 1 and start_year >= 1917
        except ValueError:
            return False

    @classmethod
    def validate_game_id(cls, game_id: int) -> bool:
        """Return True when game_id is a valid 10-digit NHL game identifier."""
        return isinstance(game_id, int) and 1_000_000_000 <= game_id <= 9_999_999_999
