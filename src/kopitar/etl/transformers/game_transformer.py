"""
Game Transformer

Pure transformation functions for converting raw NHL API (api-web.nhle.com/v1/)
responses into normalized dicts ready for database insertion.

No database dependencies — all methods are dict→dict.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _parse_toi(toi_str: Optional[str]) -> float:
    """
    Convert a MM:SS time-on-ice string to fractional minutes.

    Args:
        toi_str: Time string in "MM:SS" format, or None.

    Returns:
        float: Minutes played (e.g. "59:12" → 59.2).
    """
    if not toi_str:
        return 0.0
    try:
        parts = toi_str.split(":")
        minutes = int(parts[0])
        seconds = int(parts[1]) if len(parts) > 1 else 0
        return round(minutes + seconds / 60.0, 4)
    except (ValueError, IndexError):
        logger.warning("Could not parse toi value: %r", toi_str)
        return 0.0


class GameTransformer:
    """
    Transforms raw NHL API (api-web.nhle.com/v1/) responses into normalized
    dicts suitable for database insertion.

    All methods are stateless and free of DB dependencies.
    """

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def transform_game(self, raw_game: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize a raw boxscore/game response into a flat game record.

        Expected top-level keys from the new NHL API boxscore endpoint:
          id, gameType, gameDate, season, awayTeam, homeTeam,
          awayTeam.score / homeTeam.score, venue, gameState

        Args:
            raw_game: Raw dict from ``GET /v1/gamecenter/{game_id}/boxscore``
                      or a schedule game object.

        Returns:
            dict: Normalized game record ready for the ``games`` table.
        """
        away_team: dict = raw_game.get("awayTeam", {})
        home_team: dict = raw_game.get("homeTeam", {})

        return {
            "nhl_id": raw_game.get("id"),
            "season": raw_game.get("season"),
            # gameType: 1=preseason, 2=regular, 3=playoffs
            "game_type": raw_game.get("gameType"),
            "game_date": raw_game.get("gameDate"),
            "game_state": raw_game.get("gameState"),  # "OFF" = final
            "away_team_id": away_team.get("id"),
            "away_team_abbrev": away_team.get("abbrev"),
            "away_score": away_team.get("score"),
            "home_team_id": home_team.get("id"),
            "home_team_abbrev": home_team.get("abbrev"),
            "home_score": home_team.get("score"),
            "venue": raw_game.get("venue", {}).get("default"),
            "period": raw_game.get("period"),
            "period_descriptor": raw_game.get("periodDescriptor"),
        }

    def transform_goalie_stats(
        self,
        raw_boxscore: dict[str, Any],
        game_id: int,
    ) -> list[dict[str, Any]]:
        """
        Extract per-goalie performance records from a boxscore response.

        New API boxscore structure (``playerByGameStats``):
        .. code-block:: json

            {
              "id": 2023020789,
              "gameDate": "2024-01-15",
              "awayTeam": {"abbrev": "TOR", "id": 10},
              "homeTeam": {"abbrev": "BOS", "id": 6},
              "playerByGameStats": {
                "awayTeam": {
                  "goalies": [{"playerId": 8480045, "savePctg": 0.923,
                               "shotsAgainst": 26, "saves": 24,
                               "goalsAgainst": 2, "toi": "59:12",
                               "decision": "L"}]
                },
                "homeTeam": {
                  "goalies": [{"playerId": 8479320, "savePctg": 0.957,
                               "shotsAgainst": 23, "saves": 22,
                               "goalsAgainst": 1, "toi": "60:00",
                               "decision": "W"}]
                }
              }
            }

        Args:
            raw_boxscore: Full boxscore dict from the new API.
            game_id: Internal (NHL API) game ID to embed in each record.

        Returns:
            list[dict]: One record per goalie entry.  Fields:
                ``player_id``, ``game_id``, ``team_id``, ``saves``,
                ``shots_against``, ``save_pct``, ``goals_against``,
                ``minutes_played``, ``decision``.
        """
        records: list[dict[str, Any]] = []

        player_stats: dict = raw_boxscore.get("playerByGameStats", {})

        side_map = {
            "awayTeam": raw_boxscore.get("awayTeam", {}),
            "homeTeam": raw_boxscore.get("homeTeam", {}),
        }

        for side_key, team_meta in side_map.items():
            team_id: Optional[int] = team_meta.get("id")
            side_stats: dict = player_stats.get(side_key, {})
            goalies: list = side_stats.get("goalies", [])

            for goalie in goalies:
                shots_against: int = goalie.get("shotsAgainst", 0)
                saves: int = goalie.get("saves", 0)

                # Prefer API-provided save pct; fall back to computing it
                if goalie.get("savePctg") is not None:
                    save_pct = round(float(goalie["savePctg"]), 4)
                elif shots_against > 0:
                    save_pct = round(saves / shots_against, 4)
                else:
                    save_pct = 0.0

                records.append(
                    {
                        "player_id": goalie.get("playerId"),
                        "game_id": game_id,
                        "team_id": team_id,
                        "saves": saves,
                        "shots_against": shots_against,
                        "save_pct": save_pct,
                        "goals_against": goalie.get("goalsAgainst", 0),
                        "minutes_played": _parse_toi(goalie.get("toi")),
                        "decision": goalie.get("decision"),
                    }
                )

        return records

    def transform_schedule(
        self,
        raw_schedule: dict[str, Any],
        date: str,
    ) -> list[dict[str, Any]]:
        """
        Parse a schedule response from ``GET /v1/schedule/{date}`` into a list
        of game dicts.

        New API schedule structure:
        .. code-block:: json

            {
              "gameWeek": [
                {
                  "date": "2024-01-15",
                  "games": [
                    {
                      "id": 2023020789,
                      "gameType": 2,
                      "season": "20232024",
                      "gameDate": "2024-01-15T00:00:00Z",
                      "gameState": "OFF",
                      "awayTeam": {"id": 10, "abbrev": "TOR", "score": 2},
                      "homeTeam": {"id": 6,  "abbrev": "BOS", "score": 3},
                      "venue": {"default": "TD Garden"}
                    }
                  ]
                }
              ]
            }

        Args:
            raw_schedule: Dict returned by the schedule endpoint.
            date: The date string (``YYYY-MM-DD``) whose games are requested.
                  Used to find the matching day inside ``gameWeek``.

        Returns:
            list[dict]: One normalized game dict per game on that date.
        """
        games: list[dict[str, Any]] = []

        # The /v1/schedule/{date} response can use either "gameWeek" (weekly
        # view) or a flat "games" list (single-day view).  Handle both shapes.
        if "games" in raw_schedule:
            raw_games = raw_schedule["games"]
        else:
            raw_games = []
            for week_day in raw_schedule.get("gameWeek", []):
                if week_day.get("date") == date:
                    raw_games = week_day.get("games", [])
                    break

        for raw_game in raw_games:
            try:
                games.append(self.transform_game(raw_game))
            except Exception:
                logger.exception(
                    "Failed to transform schedule game %r", raw_game.get("id")
                )

        return games
