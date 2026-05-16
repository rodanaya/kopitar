"""
Fetch NHL skater season stats via NHL Stats REST API.
Stores top 200 skaters per season (by points) in skater_season_stats table.
"""
import sqlite3
import time
import requests
from pathlib import Path

DB_PATH = Path("data/scraped/kopitar.db")
HEADERS = {"User-Agent": "KopitarResearch/1.0 (rod.anaya@gmail.com)"}

SEASONS = [
    "20152016", "20162017", "20172018", "20182019", "20192020",
    "20202021", "20212022", "20222023", "20232024", "20242025",
]

URL = "https://api.nhle.com/stats/rest/en/skater/summary"


def fetch_season(season_code: str, limit: int = 200) -> list:
    params = {
        "isAggregate": "false",
        "isGame": "false",
        "sort": '[{"property":"points","direction":"DESC"}]',
        "start": 0,
        "limit": limit,
        "cayenneExp": f"seasonId={season_code} and gameTypeId=2",
    }
    try:
        r = requests.get(URL, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"  Error: {e}")
        return []


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skater_season_stats (
            player_id  INTEGER,
            player_name TEXT,
            position   TEXT,
            team       TEXT,
            season     TEXT,
            game_type  INTEGER DEFAULT 2,
            games_played INTEGER,
            goals      INTEGER,
            assists    INTEGER,
            points     INTEGER,
            plus_minus INTEGER,
            pim        INTEGER,
            shots      INTEGER,
            toi_per_game REAL,
            pp_points  INTEGER,
            sh_points  INTEGER,
            points_per_game REAL,
            PRIMARY KEY (player_id, season, game_type)
        )
    """)
    conn.commit()

    total = 0
    for season in SEASONS:
        print(f"Season {season}...", end=" ", flush=True)
        players = fetch_season(season)
        if not players:
            print("no data")
            continue

        rows = []
        for p in players:
            pos = p.get("positionCode", "")
            if pos == "G":
                continue

            team_raw = p.get("teamAbbrevs", "") or ""
            team = team_raw.split(",")[0].strip()

            toi = float(p.get("timeOnIcePerGame", 0) or 0)
            if toi > 60:  # API sometimes returns seconds
                toi /= 60

            rows.append((
                p.get("playerId"),
                p.get("skaterFullName", ""),
                pos,
                team,
                season,
                2,
                p.get("gamesPlayed", 0),
                p.get("goals", 0),
                p.get("assists", 0),
                p.get("points", 0),
                p.get("plusMinus", 0),
                p.get("penaltyMinutes", 0),
                p.get("shots", 0),
                round(toi, 2),
                p.get("ppPoints", 0),
                p.get("shPoints", 0),
                round(float(p.get("pointsPerGame", 0) or 0), 3),
            ))

        cursor.executemany("""
            INSERT OR REPLACE INTO skater_season_stats
            (player_id, player_name, position, team, season, game_type,
             games_played, goals, assists, points, plus_minus, pim,
             shots, toi_per_game, pp_points, sh_points, points_per_game)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()
        print(f"{len(rows)} skaters")
        total += len(rows)
        time.sleep(0.5)

    conn.close()
    print(f"\nTotal: {total} skater-season rows inserted")

    # Validate
    conn2 = sqlite3.connect(DB_PATH)
    rows_check = conn2.execute(
        "SELECT season, COUNT(*) n, MAX(points) max_pts FROM skater_season_stats GROUP BY season ORDER BY season"
    ).fetchall()
    conn2.close()
    print("\nPer-season breakdown:")
    for r in rows_check:
        print(f"  {r[0]}: {r[1]} players, top pts={r[2]}")


if __name__ == "__main__":
    main()
