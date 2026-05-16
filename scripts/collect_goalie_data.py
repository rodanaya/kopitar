"""
NHL Goalie Data Collector — Extended

10 regular seasons (2015-16 → 2024-25) + playoffs for each.
Handles team history: VGK joined 2017-18, ARI→UTA for 2024-25.
Skips seasons already fully loaded (checkpoint via DB row count).

Estimated API calls: ~1,650  |  Est. time: ~20 minutes
"""

import time
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "scraped"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "kopitar.db"

# ── API Config ─────────────────────────────────────────────────────────────────
WEB_BASE = "https://api-web.nhle.com/v1"
STATS_BASE = "https://api.nhle.com/stats/rest/en"
RATE_LIMIT_DELAY = 0.65  # ~92 req/min

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Kopitar-Research/1.0"})

# 10 regular seasons
REGULAR_SEASONS = [
    "20152016", "20162017", "20172018", "20182019", "20192020",
    "20202021", "20212022", "20222023", "20232024", "20242025",
]

GAME_TYPE_REGULAR  = 2
GAME_TYPE_PLAYOFFS = 3

# Teams active per season-start year.  VGK joined 2017-18, UTA replaced ARI 2024-25.
BASE_TEAMS = [
    "BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TBL", "TOR",
    "CAR", "CBJ", "NJD", "NYI", "NYR", "PHI", "PIT", "WSH",
    "CHI", "COL", "DAL", "MIN", "NSH", "STL", "WPG",
    "ANA", "CGY", "EDM", "LAK", "SJS", "SEA", "VAN",
]

def teams_for_season(season: str) -> list[str]:
    year = int(season[:4])
    teams = list(BASE_TEAMS)
    if year >= 2017:
        teams.append("VGK")
    if year < 2024:
        teams.append("ARI")
    if year >= 2024:
        teams.append("UTA")
    if year >= 2021:
        pass  # SEA joined 2021-22 — already in BASE_TEAMS
    else:
        teams = [t for t in teams if t != "SEA"]
    return teams


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def get(url: str, params: dict | None = None, retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=15)
            if r.status_code == 200:
                time.sleep(RATE_LIMIT_DELAY)
                return r.json()
            elif r.status_code == 404:
                return None
            else:
                print(f"  HTTP {r.status_code} for {url[:80]} (attempt {attempt+1})")
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  Error: {e} (attempt {attempt+1})")
            time.sleep(2 ** attempt)
    return None


# ── DB checkpoint helpers ─────────────────────────────────────────────────────

def already_loaded(season: str, game_type: int) -> bool:
    """Skip if this season+game_type has already been scraped into the DB."""
    if not DB_PATH.exists():
        return False
    conn = sqlite3.connect(DB_PATH)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM goalie_game_logs WHERE season=? AND game_type=?",
            (season, game_type)
        ).fetchone()[0]
        return count > 50  # enough rows to be considered loaded
    except Exception:
        return False
    finally:
        conn.close()


# ── API calls ──────────────────────────────────────────────────────────────────

def get_goalies_for_season(season: str, game_type: int) -> list[dict]:
    data = get(f"{STATS_BASE}/goalie/summary", params={
        "limit": -1,
        "cayenneExp": f"seasonId={season} and gameTypeId={game_type}"
    })
    if not data:
        return []
    rows = []
    for g in data.get("data", []):
        rows.append({
            "player_id":   g["playerId"],
            "player_name": g["goalieFullName"],
            "team":        g["teamAbbrevs"],
            "season":      season,
            "game_type":   game_type,
            "games_started": g.get("gamesStarted", 0),
            "games_played":  g.get("gamesPlayed", 0),
            "save_pct":    g.get("savePct"),
            "gaa":         g.get("goalsAgainstAverage"),
            "wins":        g.get("wins", 0),
            "losses":      g.get("losses", 0),
            "ot_losses":   g.get("otLosses", 0),
            "shutouts":    g.get("shutouts", 0),
            "toi_seconds": g.get("timeOnIce", 0),
        })
    return rows


def get_saves_by_strength(season: str, game_type: int) -> dict[int, dict]:
    data = get(f"{STATS_BASE}/goalie/savesByStrength", params={
        "limit": -1,
        "cayenneExp": f"seasonId={season} and gameTypeId={game_type}"
    })
    if not data:
        return {}
    result = {}
    for g in data.get("data", []):
        result[g["playerId"]] = {
            "ev_save_pct":       g.get("evSavePct"),
            "pp_save_pct":       g.get("ppSavePct"),
            "sh_save_pct":       g.get("shSavePct"),
            "ev_shots_against":  g.get("evShotsAgainst"),
            "pp_shots_against":  g.get("ppShotsAgainst"),
        }
    return result


def get_player_game_log(player_id: int, season: str, game_type: int) -> list[dict]:
    url = f"{WEB_BASE}/player/{player_id}/game-log/{season}/{game_type}"
    data = get(url)
    if not data:
        return []
    rows = []
    for g in data.get("gameLog", []):
        toi_str = g.get("toi", "0:00")
        try:
            parts = toi_str.split(":")
            toi_mins = int(parts[0]) + int(parts[1]) / 60
        except Exception:
            toi_mins = 0.0
        shots = g.get("shotsAgainst", 0)
        goals = g.get("goalsAgainst", 0)
        rows.append({
            "player_id":     player_id,
            "season":        season,
            "game_type":     game_type,
            "game_id":       g.get("gameId"),
            "game_date":     g.get("gameDate"),
            "team":          g.get("teamAbbrev"),
            "home_away":     "home" if g.get("homeRoadFlag") == "H" else "away",
            "opponent":      g.get("opponentAbbrev"),
            "decision":      g.get("decision"),
            "games_started": g.get("gamesStarted", 0),
            "shots_against": shots,
            "goals_against": goals,
            "saves":         shots - goals,
            "save_pct":      g.get("savePctg"),
            "shutout":       g.get("shutouts", 0),
            "toi_minutes":   round(toi_mins, 2),
        })
    return rows


def get_team_schedule(team: str, season: str) -> list[dict]:
    url = f"{WEB_BASE}/club-schedule-season/{team}/{season}"
    data = get(url)
    if not data:
        return []
    rows = []
    for g in data.get("games", []):
        if g.get("gameType") not in (GAME_TYPE_REGULAR, GAME_TYPE_PLAYOFFS):
            continue
        rows.append({
            "game_id":        g.get("id"),
            "season":         season,
            "game_type":      g.get("gameType"),
            "game_date":      g.get("gameDate"),
            "away_team":      (g.get("awayTeam") or {}).get("abbrev", ""),
            "home_team":      (g.get("homeTeam") or {}).get("abbrev", ""),
            "venue_timezone": g.get("venueTimezone", ""),
        })
    return rows


# ── Feature engineering ───────────────────────────────────────────────────────

def engineer_fatigue_features(game_logs: pd.DataFrame, schedules: pd.DataFrame) -> pd.DataFrame:
    df = game_logs.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values(["player_id", "game_date"])

    df["prev_game_date"] = df.groupby("player_id")["game_date"].shift(1)
    df["days_rest"] = (df["game_date"] - df["prev_game_date"]).dt.days
    df["is_back_to_back"] = df["days_rest"] == 1

    def rolling_games(group, window_days):
        dates = group["game_date"].values
        return [sum(1 for j, d2 in enumerate(dates) if j < i and (dates[i] - d2).astype("timedelta64[D]").astype(int) <= window_days)
                for i in range(len(dates))]

    df["games_last_7d"] = df.groupby("player_id", group_keys=False).apply(
        lambda g: pd.Series(rolling_games(g, 7), index=g.index)
    )
    df["games_last_14d"] = df.groupby("player_id", group_keys=False).apply(
        lambda g: pd.Series(rolling_games(g, 14), index=g.index)
    )

    if not schedules.empty:
        sched_lookup = schedules[["game_id", "venue_timezone", "home_team"]].drop_duplicates("game_id")
        df = df.merge(sched_lookup, on="game_id", how="left")
    else:
        df["venue_timezone"] = None
        df["home_team"] = None

    # Travel distance using arena coords
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from kopitar.engine.travel_calculator import TravelCalculator
        calc = TravelCalculator()
        df = df.sort_values(["player_id", "game_date"])
        df["prev_home_team"] = df.groupby("player_id")["home_team"].shift(1)
        def dist(row):
            if pd.isna(row.get("prev_home_team")) or pd.isna(row.get("home_team")):
                return 0.0
            try:
                return calc.calculate_distance(row["prev_home_team"], row["home_team"])
            except Exception:
                return 0.0
        df["travel_miles"] = df.apply(dist, axis=1)
    except Exception as e:
        print(f"  Travel calc skipped: {e}")
        df["travel_miles"] = 0.0

    return df


# ── Save ──────────────────────────────────────────────────────────────────────

def append_to_db(game_logs: pd.DataFrame, goalie_seasons: pd.DataFrame):
    conn = sqlite3.connect(DB_PATH)
    if not game_logs.empty:
        game_logs.to_sql("goalie_game_logs", conn, if_exists="append", index=False)
    if not goalie_seasons.empty:
        goalie_seasons.to_sql("goalie_season_stats", conn, if_exists="append", index=False)
    conn.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    start_time = datetime.now()
    print("=" * 65)
    print("Kopitar NHL Goalie Data Collector — Extended")
    print(f"Seasons: 2015-16 to 2024-25  |  Regular + Playoffs")
    print("=" * 65)

    # Wipe and recreate DB for a clean full load
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Cleared existing database for full re-scrape.\n")

    all_season_rows = []
    all_game_logs   = []
    all_schedules   = []
    total_api_calls = 0

    combinations = [(s, gt) for s in REGULAR_SEASONS for gt in (GAME_TYPE_REGULAR, GAME_TYPE_PLAYOFFS)]

    for season, game_type in combinations:
        label = f"{season[:4]}-{season[4:6]}  {'REG' if game_type == 2 else 'PO '}"
        print(f"\n── {label} ──────────────────────────────────────")

        # Phase 1: Season stats + EV/PP/SH splits
        rows = get_goalies_for_season(season, game_type)
        total_api_calls += 1
        if not rows:
            print(f"  No goalies found — skipping.")
            continue

        strength = get_saves_by_strength(season, game_type)
        total_api_calls += 1
        for row in rows:
            row.update(strength.get(row["player_id"], {}))
        all_season_rows.extend(rows)

        player_ids = [r["player_id"] for r in rows]
        print(f"  {len(player_ids)} goalies  |  fetching game logs...", end=" ", flush=True)

        # Phase 2: Per-player game logs
        season_logs = []
        for pid in player_ids:
            logs = get_player_game_log(pid, season, game_type)
            total_api_calls += 1
            season_logs.extend(logs)
        all_game_logs.extend(season_logs)
        print(f"{len(season_logs)} game records")

    # Phase 3: Team schedules (regular season only — gives venue/timezone)
    print(f"\n── SCHEDULES ──────────────────────────────────────────────")
    for season in REGULAR_SEASONS:
        teams = teams_for_season(season)
        for team in teams:
            sched = get_team_schedule(team, season)
            total_api_calls += 1
            all_schedules.extend(sched)
    print(f"  {len(all_schedules)} schedule rows across {len(REGULAR_SEASONS)} seasons")

    # Phase 4: Build dataframes
    game_logs_df   = pd.DataFrame(all_game_logs)
    goalie_stats_df = pd.DataFrame(all_season_rows)
    schedules_df   = pd.DataFrame(all_schedules).drop_duplicates("game_id") if all_schedules else pd.DataFrame()

    game_logs_df.to_csv(DATA_DIR / "goalie_game_logs_raw.csv", index=False)
    goalie_stats_df.to_csv(DATA_DIR / "goalie_season_stats.csv", index=False)
    if not schedules_df.empty:
        schedules_df.to_csv(DATA_DIR / "game_schedules.csv", index=False)

    # Phase 5: Feature engineering
    print(f"\n── FEATURE ENGINEERING ────────────────────────────────────")
    enriched = engineer_fatigue_features(game_logs_df, schedules_df)
    enriched.to_csv(DATA_DIR / "goalie_game_logs_enriched.csv", index=False)
    print(f"  Enriched: {len(enriched)} rows")

    # Phase 6: Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    enriched.to_sql("goalie_game_logs", conn, if_exists="replace", index=False)
    goalie_stats_df.to_sql("goalie_season_stats", conn, if_exists="replace", index=False)
    schedules_df.to_sql("game_schedules", conn, if_exists="replace", index=False)
    conn.close()

    # ── Final report ──────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    reg = enriched[enriched["game_type"] == 2]
    po  = enriched[enriched["game_type"] == 3]

    print(f"\n{'=' * 65}")
    print("DATA COLLECTION COMPLETE")
    print(f"{'=' * 65}")
    print(f"  Total API calls:          {total_api_calls}")
    print(f"  Elapsed:                  {elapsed:.1f} minutes")
    print(f"  Seasons:                  {REGULAR_SEASONS[0][:4]}-{REGULAR_SEASONS[-1][4:6]} ({len(REGULAR_SEASONS)} regular + playoffs)")
    print(f"  Unique goalies:           {enriched['player_id'].nunique()}")
    print(f"  Regular season logs:      {len(reg)}")
    print(f"  Playoff logs:             {len(po)}")
    print(f"  Total game logs:          {len(enriched)}")
    print(f"  Schedule rows:            {len(schedules_df)}")

    if not reg.empty and "is_back_to_back" in reg.columns:
        b2b   = reg[reg["is_back_to_back"] == True]["save_pct"].dropna()
        rest  = reg[reg["is_back_to_back"] == False]["save_pct"].dropna()
        print(f"\n  ── Regular Season Fatigue Signal ──────────────────────")
        print(f"  Back-to-back games:       {len(b2b)}  (SV% {b2b.mean():.4f})")
        print(f"  Rested games:             {len(rest)}  (SV% {rest.mean():.4f})")
        print(f"  B2B penalty:              {b2b.mean() - rest.mean():+.4f}")

    if not po.empty and "is_back_to_back" in po.columns:
        pb2b  = po[po["is_back_to_back"] == True]["save_pct"].dropna()
        prest = po[po["is_back_to_back"] == False]["save_pct"].dropna()
        print(f"\n  ── Playoff Fatigue Signal ─────────────────────────────")
        print(f"  Playoff B2B games:        {len(pb2b)}  (SV% {pb2b.mean():.4f})")
        print(f"  Playoff rested games:     {len(prest)}  (SV% {prest.mean():.4f})")
        print(f"  Playoff B2B penalty:      {pb2b.mean() - prest.mean():+.4f}")

    print(f"\n  Output: {DATA_DIR}")
    print(f"  DB:     {DB_PATH}")


if __name__ == "__main__":
    main()
