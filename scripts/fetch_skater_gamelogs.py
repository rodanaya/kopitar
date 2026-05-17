"""
Fetch per-game logs for all skaters in skater_season_stats and store in
skater_game_logs table. Adds fatigue variables (rest_days, back-to-back,
3-in-4, road trip leg) computed from game dates.

API: https://api-web.nhle.com/v1/player/{playerId}/game-log/{season}/2
     homeRoadFlag values: 'H' (home) or 'R' (road/away)
"""

import sqlite3
import time
import urllib.request
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("D:/Python/Kopitar/data/scraped/kopitar.db")
API_BASE = "https://api-web.nhle.com/v1/player/{pid}/game-log/{season}/2"
HEADERS = {"User-Agent": "Mozilla/5.0 (Kopitar Research Project)"}
DELAY = 0.25  # seconds between requests


def parse_toi(toi_str: str) -> int:
    """Convert 'MM:SS' to total seconds."""
    if not toi_str:
        return 0
    parts = toi_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def compute_fatigue_vars(games: list[dict]) -> list[dict]:
    """
    Given a list of game dicts (sorted by date, single player),
    add rest_days, is_back_to_back, is_3_in_4, road_trip_leg.
    """
    dates = [datetime.strptime(g["game_date"], "%Y-%m-%d") for g in games]
    road_leg = 0
    for i, g in enumerate(games):
        if i == 0:
            rest = None
            b2b = 0
            three_in_4 = 0
        else:
            delta = (dates[i] - dates[i - 1]).days
            rest = delta
            b2b = 1 if delta == 1 else 0
            # count games in past 4 calendar days (including today)
            cutoff = dates[i] - timedelta(days=3)
            window = sum(1 for d in dates[:i] if d >= cutoff)
            three_in_4 = 1 if window >= 2 else 0  # this game + 2 prior = 3-in-4

        if g["home_road"] == "R":
            road_leg += 1
        else:
            road_leg = 0

        g["rest_days"] = rest
        g["is_back_to_back"] = b2b
        g["is_3_in_4"] = three_in_4
        g["road_trip_leg"] = road_leg

    return games


def fetch_game_log(player_id: int, season: str) -> list[dict]:
    url = API_BASE.format(pid=player_id, season=season)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
    except Exception as e:
        print(f"    ERROR fetching {player_id}/{season}: {e}")
        return []

    rows = []
    for g in data.get("gameLog", []):
        rows.append({
            "player_id": player_id,
            "season": season,
            "game_id": g["gameId"],
            "game_date": g["gameDate"],
            "team": g.get("teamAbbrev", ""),
            "opponent": g.get("opponentAbbrev", ""),
            "home_road": g.get("homeRoadFlag", ""),
            "goals": g.get("goals", 0),
            "assists": g.get("assists", 0),
            "points": g.get("points", 0),
            "plus_minus": g.get("plusMinus", 0),
            "pim": g.get("pim", 0),
            "shots": g.get("shots", 0),
            "shifts": g.get("shifts", 0),
            "toi": g.get("toi", "0:00"),
            "toi_seconds": parse_toi(g.get("toi", "0:00")),
            "pp_points": g.get("powerPlayPoints", 0),
            "sh_points": g.get("shorthandedPoints", 0),
            "ot_goals": g.get("otGoals", 0),
            "gw_goals": g.get("gameWinningGoals", 0),
        })

    rows.sort(key=lambda r: r["game_date"])
    rows = compute_fatigue_vars(rows)
    return rows


def create_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skater_game_logs (
            player_id     INTEGER,
            season        TEXT,
            game_id       INTEGER,
            game_date     TEXT,
            team          TEXT,
            opponent      TEXT,
            home_road     TEXT,
            goals         INTEGER,
            assists       INTEGER,
            points        INTEGER,
            plus_minus    INTEGER,
            pim           INTEGER,
            shots         INTEGER,
            shifts        INTEGER,
            toi           TEXT,
            toi_seconds   INTEGER,
            pp_points     INTEGER,
            sh_points     INTEGER,
            ot_goals      INTEGER,
            gw_goals      INTEGER,
            rest_days     INTEGER,
            is_back_to_back INTEGER DEFAULT 0,
            is_3_in_4     INTEGER DEFAULT 0,
            road_trip_leg INTEGER DEFAULT 0,
            PRIMARY KEY (player_id, game_id)
        )
    """)
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    # Get player-season combos, joined with name for logging
    combos = conn.execute("""
        SELECT DISTINCT player_id, player_name, season
        FROM skater_season_stats
        ORDER BY season, player_name
    """).fetchall()
    print(f"Fetching {len(combos)} player-season game logs...")

    # Track already-fetched combos to allow resuming
    done = {(r[0], r[1]) for r in conn.execute(
        "SELECT DISTINCT player_id, season FROM skater_game_logs"
    )}
    print(f"  Already in DB: {len(done)} combos, skipping those")

    total_rows = 0
    for i, (pid, name, season) in enumerate(combos):
        if (pid, season) in done:
            continue

        rows = fetch_game_log(pid, season)
        if rows:
            conn.executemany("""
                INSERT OR REPLACE INTO skater_game_logs
                (player_id, season, game_id, game_date, team, opponent, home_road,
                 goals, assists, points, plus_minus, pim, shots, shifts,
                 toi, toi_seconds, pp_points, sh_points, ot_goals, gw_goals,
                 rest_days, is_back_to_back, is_3_in_4, road_trip_leg)
                VALUES
                (:player_id, :season, :game_id, :game_date, :team, :opponent, :home_road,
                 :goals, :assists, :points, :plus_minus, :pim, :shots, :shifts,
                 :toi, :toi_seconds, :pp_points, :sh_points, :ot_goals, :gw_goals,
                 :rest_days, :is_back_to_back, :is_3_in_4, :road_trip_leg)
            """, rows)
            conn.commit()
            total_rows += len(rows)

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(combos)}] {total_rows:,} rows so far...")

        time.sleep(DELAY)

    conn.close()
    print(f"Done. {total_rows:,} game rows inserted.")


if __name__ == "__main__":
    main()
