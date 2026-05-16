"""
Enrich the goalie game log dataset with Tier 1 additional variables:
  - road_trip_leg (game # on current road trip)
  - venue_altitude_ft + altitude_delta_from_prev
  - is_3_in_4 / is_4_in_6 flags
  - consecutive_starts_streak
  - eastward_travel_flag
  - season_phase (early/mid/stretch)

Reads from kopitar.db, writes enriched CSV + updates DB.
"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/scraped/kopitar.db")
CSV_OUT = Path("data/scraped/goalie_game_logs_enriched_v2.csv")

ARENA_ALTITUDE = {
    "BOS": 20, "BUF": 570, "DET": 580, "FLA": 10, "MTL": 100,
    "OTT": 283, "TBL": 15, "TOR": 249, "CAR": 435, "CBJ": 754,
    "NJD": 16, "NYI": 20, "NYR": 55, "PHI": 39, "PIT": 730,
    "WSH": 25, "CHI": 594, "COL": 5280, "DAL": 430, "MIN": 815,
    "NSH": 440, "STL": 455, "WPG": 760, "ANA": 157, "UTA": 4226,
    "ARI": 1082, "CGY": 3438, "EDM": 2200, "LAK": 285, "SJS": 87,
    "SEA": 175, "VGK": 2001, "VAN": 14,
}

# Longitudes for east/west detection (negative = west of prime meridian)
ARENA_LON = {
    "BOS": -71.06, "BUF": -78.88, "DET": -83.06, "FLA": -80.33,
    "MTL": -73.57, "OTT": -75.93, "TBL": -82.45, "TOR": -79.38,
    "CAR": -78.72, "CBJ": -83.01, "NJD": -74.17, "NYI": -73.59,
    "NYR": -73.99, "PHI": -75.17, "PIT": -79.99, "WSH": -77.02,
    "CHI": -87.67, "COL": -105.01, "DAL": -96.81, "MIN": -93.10,
    "NSH": -86.78, "STL": -90.20, "WPG": -97.14, "ANA": -117.88,
    "UTA": -111.90, "ARI": -112.07, "CGY": -114.05, "EDM": -113.49,
    "LAK": -118.27, "SJS": -121.90, "SEA": -122.35, "VGK": -115.18,
    "VAN": -123.11,
}


def compute_road_trip_leg(g: pd.DataFrame) -> pd.Series:
    """Count consecutive away games (resets to 0 on home game, counts from 1 on road)."""
    result = []
    streak = 0
    for _, row in g.iterrows():
        if row.get("home_away", "home") == "away":
            streak += 1
        else:
            streak = 0
        result.append(streak)
    return pd.Series(result, index=g.index)


def compute_rolling_games_in_window(g: pd.DataFrame, days: int) -> pd.Series:
    """Count how many games each goalie played in the trailing `days` days (inclusive)."""
    dates = g["game_date"].sort_values()
    result = []
    for dt in dates:
        window_start = dt - pd.Timedelta(days=days - 1)
        count = ((dates >= window_start) & (dates <= dt)).sum()
        result.append(int(count))
    return pd.Series(result, index=dates.index)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.sort_values(["player_id", "game_date"]).reset_index(drop=True)
    # DB stores team abbreviation as 'team'
    if "team_abbrev" not in df.columns:
        df["team_abbrev"] = df["team"]

    # --- Altitude ---
    df["venue_altitude_ft"] = df["team_abbrev"].map(ARENA_ALTITUDE).fillna(0).astype(int)
    df["prev_venue_altitude"] = df.groupby("player_id")["venue_altitude_ft"].shift(1)
    df["altitude_delta"] = (df["venue_altitude_ft"] - df["prev_venue_altitude"]).fillna(0).astype(int)

    # --- Eastward travel ---
    prev_lon = df.groupby("player_id")["team_abbrev"].shift(1).map(ARENA_LON)
    curr_lon = df["team_abbrev"].map(ARENA_LON)
    df["eastward_travel"] = ((curr_lon - prev_lon) > 0).astype(int)
    df.loc[prev_lon.isna(), "eastward_travel"] = 0

    # --- Road trip leg ---
    print("  Computing road trip legs...")
    road_legs = (
        df.groupby("player_id", group_keys=False)
          .apply(lambda g: compute_road_trip_leg(g.sort_values("game_date")))
    )
    df["road_trip_leg"] = road_legs.values

    # --- 3-in-4 and 4-in-6 ---
    print("  Computing 3-in-4 and 4-in-6 flags...")
    games_4d = (
        df.groupby("player_id", group_keys=False)
          .apply(lambda g: compute_rolling_games_in_window(g.sort_values("game_date"), days=4))
    )
    games_6d = (
        df.groupby("player_id", group_keys=False)
          .apply(lambda g: compute_rolling_games_in_window(g.sort_values("game_date"), days=6))
    )
    df["is_3_in_4"] = (games_4d.values >= 3).astype(int)
    df["is_4_in_6"] = (games_6d.values >= 4).astype(int)

    # --- Consecutive starts streak ---
    print("  Computing consecutive starts streak...")
    def streak_counter(g):
        g = g.sort_values("game_date").copy()
        streak, result = 0, []
        for _ in g.iterrows():
            streak += 1
            result.append(streak)
        return pd.Series(result, index=g.index)

    cons = df.groupby("player_id", group_keys=False).apply(streak_counter)
    df["consecutive_starts_streak"] = cons.values

    # --- Season phase ---
    def season_game_num(g):
        g = g.sort_values("game_date").copy()
        g["season_game_number"] = range(1, len(g) + 1)
        return g["season_game_number"]

    sgn = df.groupby(["player_id", "season"], group_keys=False).apply(season_game_num)
    df["season_game_number"] = sgn.values

    def phase(n):
        if n <= 20:
            return "early"
        elif n <= 60:
            return "mid"
        else:
            return "stretch"

    df["season_phase"] = df["season_game_number"].apply(phase)

    # --- Shots faced previous game ---
    df["shots_prev_game"] = df.groupby("player_id")["shots_against"].shift(1).fillna(0).astype(int)

    return df


def main():
    print(f"Loading {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM goalie_game_logs", conn)
    conn.close()
    print(f"  {len(df):,} records loaded")

    print("Enriching with Tier-1 variables...")
    df_enriched = enrich(df)

    new_cols = [
        "venue_altitude_ft", "altitude_delta", "eastward_travel",
        "road_trip_leg", "is_3_in_4", "is_4_in_6",
        "consecutive_starts_streak", "season_game_number", "season_phase",
        "shots_prev_game",
    ]
    print(f"  Added columns: {', '.join(new_cols)}")

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.to_csv(CSV_OUT, index=False)
    print(f"  Saved to {CSV_OUT}")

    # Write back to DB (add new columns if they don't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(goalie_game_logs)")}
    for col in new_cols:
        if col not in existing:
            dtype = "TEXT" if col == "season_phase" else "INTEGER"
            cursor.execute(f"ALTER TABLE goalie_game_logs ADD COLUMN {col} {dtype}")
    conn.commit()

    # Update rows
    for col in new_cols:
        if col == "season_phase":
            for phase_val in ("early", "mid", "stretch"):
                ids = df_enriched[df_enriched["season_phase"] == phase_val]["id"].tolist() if "id" in df_enriched.columns else []
                if ids:
                    cursor.execute(
                        f"UPDATE goalie_game_logs SET {col}=? WHERE id IN ({','.join('?'*len(ids))})",
                        [phase_val] + ids
                    )
        else:
            rows = df_enriched[["id", col]].dropna() if "id" in df_enriched.columns else pd.DataFrame()
            if not rows.empty:
                cursor.executemany(
                    f"UPDATE goalie_game_logs SET {col}=? WHERE id=?",
                    [(int(r[col]), int(r["id"])) for _, r in rows.iterrows()]
                )
    conn.commit()
    conn.close()
    print("  DB updated.")

    # Quick validation
    print("\nNew variable distributions:")
    for col in ["is_3_in_4", "is_4_in_6", "road_trip_leg", "venue_altitude_ft"]:
        print(f"  {col}: {df_enriched[col].value_counts().head(5).to_dict()}")


if __name__ == "__main__":
    main()
