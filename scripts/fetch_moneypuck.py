"""
Fetch MoneyPuck goalie data and merge into kopitar.db.

Season-level: GSAx, HDSV%, xG_against, danger-zone breakdown.
Game-level:   per-game GSAx and HDSV% via per-season game CSV.

MoneyPuck season integer maps to our season_code:
  2015 -> "20152016" ... 2024 -> "20242025"
"""

import sqlite3
import sys
import time
import unicodedata
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

DB_PATH = Path("data/scraped/kopitar.db")
MP_DIR  = Path("data/moneypuck")
MP_DIR.mkdir(parents=True, exist_ok=True)

# MoneyPuck year (first year of season) -> our season code
SEASON_MAP = {
    2015: "20152016", 2016: "20162017", 2017: "20172018",
    2018: "20182019", 2019: "20192020", 2020: "20202021",
    2021: "20212022", 2022: "20222023", 2023: "20232024",
    2024: "20242025",
}

HEADERS = {"User-Agent": "KopitarResearch/1.0 (rod.anaya@gmail.com)"}

SEASON_URL  = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/regular/goalies.csv"
SKATER_URL  = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/regular/skaters.csv"

# MoneyPuck game-by-game URLs (per season)
GAME_URL_TEMPLATE = "https://moneypuck.com/moneypuck/playerData/gamescores/{year}/regular/goalies.csv"


def fetch_csv(url: str) -> pd.DataFrame | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text))
    except Exception as e:
        print(f"    WARN: {e}")
        return None


def norm_name(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(name).lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ---------------------------------------------------------------------------
# Season-level data
# ---------------------------------------------------------------------------

def build_season_df() -> pd.DataFrame:
    """Download or load cached season summaries for all 10 seasons."""
    cache = MP_DIR / "season_summaries_v2.csv"
    if cache.exists():
        df = pd.read_csv(cache)
        print(f"  Loaded {len(df):,} rows from cache")
        return df

    frames = []
    for mp_year, season_code in SEASON_MAP.items():
        print(f"  {mp_year}/{mp_year+1}...", end=" ", flush=True)
        raw = fetch_csv(SEASON_URL.format(year=mp_year))
        if raw is None:
            print("skipped")
            continue
        # Keep goalies, all-situation totals
        raw = raw[(raw["position"] == "G") & (raw["situation"] == "all")].copy()
        raw["season_code"] = season_code
        raw["mp_year"] = mp_year
        frames.append(raw)
        print(f"{len(raw)} goalies")
        time.sleep(0.4)

    df = pd.concat(frames, ignore_index=True)
    df.to_csv(cache, index=False)
    print(f"  Cached {len(df):,} rows to {cache}")
    return df


def compute_season_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    From MoneyPuck goalie season CSV derive:
      - gsax         = xGoals - goals  (expected GA minus actual GA)
      - hdsv_pct     = (highDangerShots - highDangerGoals) / highDangerShots
      - mdsv_pct     = medium-danger save %
      - xgoals_ag    = xGoals (expected goals against)
      - hd_shots_ag  = highDangerShots
      - hd_goals_ag  = highDangerGoals
      - shots_on_goal= ongoal
    """
    out = df[["name", "playerId", "team", "season_code", "games_played", "icetime"]].copy()
    out.rename(columns={"name": "mp_name", "playerId": "mp_player_id",
                        "team": "mp_team", "games_played": "mp_games"}, inplace=True)

    out["xgoals_ag"]  = df["xGoals"].round(3)
    out["goals_ag"]   = df["goals"]
    out["shots_og"]   = df["ongoal"]

    out["gsax"] = (df["xGoals"] - df["goals"]).round(3)
    # GSAx per 60 min (icetime is in seconds)
    out["gsax_per60"] = (out["gsax"] / (df["icetime"] / 3600)).round(4)

    hd_shots = df["highDangerShots"].replace(0, float("nan"))
    hd_goals = df["highDangerGoals"]
    out["hd_shots_ag"] = df["highDangerShots"]
    out["hd_goals_ag"] = df["highDangerGoals"]
    out["hdsv_pct"]    = ((hd_shots - hd_goals) / hd_shots).round(4)

    md_shots = df["mediumDangerShots"].replace(0, float("nan"))
    md_goals = df["mediumDangerGoals"]
    out["mdsv_pct"]    = ((md_shots - md_goals) / md_shots).round(4)

    ld_shots = df["lowDangerShots"].replace(0, float("nan"))
    ld_goals = df["lowDangerGoals"]
    out["ldsv_pct"]    = ((ld_shots - ld_goals) / ld_shots).round(4)

    out["xgoals_against_per60"] = (df["xGoals"] / (df["icetime"] / 3600)).round(4)

    out["name_norm"] = out["mp_name"].apply(norm_name)
    return out


# ---------------------------------------------------------------------------
# Game-level data
# ---------------------------------------------------------------------------

def build_game_df() -> pd.DataFrame:
    """Attempt to download per-season game-log CSVs from MoneyPuck."""
    cache = MP_DIR / "game_logs_v2.csv"
    if cache.exists():
        df = pd.read_csv(cache, low_memory=False)
        print(f"  Loaded {len(df):,} game rows from cache")
        return df

    frames = []
    for mp_year, season_code in SEASON_MAP.items():
        print(f"  game logs {mp_year}...", end=" ", flush=True)
        raw = fetch_csv(GAME_URL_TEMPLATE.format(year=mp_year))
        if raw is None:
            print("not found")
            continue
        if "position" in raw.columns:
            raw = raw[raw["position"] == "G"].copy()
        raw["season_code"] = season_code
        frames.append(raw)
        print(f"{len(raw)} rows")
        time.sleep(0.4)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df.to_csv(cache, index=False)
    print(f"  Cached {len(df):,} rows")
    return df


def compute_game_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Derive per-game GSAx and HDSV% from raw MoneyPuck game CSV."""
    if df.empty:
        return df

    cols_needed = ["name", "playerId", "season_code", "gameId", "gameDate",
                   "xGoals", "goals", "highDangerShots", "highDangerGoals"]
    present = [c for c in cols_needed if c in df.columns]
    out = df[present].copy()

    if "situation" in df.columns:
        out = df[df["situation"] == "all"][present].copy() if "situation" in df.columns else out

    out.rename(columns={"name": "mp_name", "playerId": "mp_player_id",
                        "gameId": "mp_game_id", "gameDate": "mp_game_date"}, inplace=True)

    if "xGoals" in df.columns and "goals" in df.columns:
        out["gsax_game"] = (df["xGoals"] - df["goals"]).round(4)

    if "highDangerShots" in df.columns and "highDangerGoals" in df.columns:
        hds = df["highDangerShots"].replace(0, float("nan"))
        hdg = df["highDangerGoals"]
        out["hdsv_pct_game"] = ((hds - hdg) / hds).round(4)

    out["name_norm"] = out["mp_name"].apply(norm_name)
    return out


# ---------------------------------------------------------------------------
# DB merge helpers
# ---------------------------------------------------------------------------

def _add_columns(conn, table: str, col_types: dict[str, str]):
    cursor = conn.cursor()
    existing = {r[1] for r in cursor.execute(f"PRAGMA table_info({table})")}
    for col, dtype in col_types.items():
        if col not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")
    conn.commit()


def merge_into_season_stats(conn, season_metrics: pd.DataFrame) -> int:
    _add_columns(conn, "goalie_season_stats", {
        "xgoals_ag": "REAL", "gsax": "REAL", "gsax_per60": "REAL",
        "hdsv_pct": "REAL", "mdsv_pct": "REAL", "ldsv_pct": "REAL",
        "hd_shots_ag": "INTEGER", "hd_goals_ag": "INTEGER",
        "xgoals_against_per60": "REAL",
    })

    our = pd.read_sql(
        "SELECT player_id, player_name, season FROM goalie_season_stats WHERE game_type=2", conn
    )
    our["name_norm"] = our["player_name"].apply(norm_name)

    merged = our.merge(
        season_metrics, left_on=["name_norm", "season"],
        right_on=["name_norm", "season_code"], how="inner"
    )
    print(f"  Matched {len(merged)} player-season rows")

    cursor = conn.cursor()
    metric_cols = ["xgoals_ag", "gsax", "gsax_per60", "hdsv_pct",
                   "mdsv_pct", "ldsv_pct", "hd_shots_ag", "hd_goals_ag",
                   "xgoals_against_per60"]
    n = 0
    for _, row in merged.iterrows():
        sets, vals = [], []
        for col in metric_cols:
            if col in row and pd.notna(row[col]):
                sets.append(f"{col}=?")
                vals.append(float(row[col]) if col not in ("hd_shots_ag", "hd_goals_ag") else int(row[col]))
        if sets:
            vals += [int(row["player_id"]), row["season"]]
            cursor.execute(
                f"UPDATE goalie_season_stats SET {','.join(sets)} "
                "WHERE player_id=? AND season=? AND game_type=2",
                vals
            )
            n += 1
    conn.commit()
    return n


def merge_into_game_logs(conn, game_metrics: pd.DataFrame) -> int:
    if game_metrics.empty:
        return 0

    _add_columns(conn, "goalie_game_logs", {
        "gsax_game": "REAL", "hdsv_pct_game": "REAL",
        "xgoals_against": "REAL",
    })

    cursor = conn.cursor()

    # Build a name → player_id lookup
    ss = pd.read_sql("SELECT DISTINCT player_id, player_name FROM goalie_season_stats", conn)
    name_to_id = {norm_name(n): pid for pid, n in zip(ss["player_id"], ss["player_name"])}

    # Build a (player_id, game_date) → rowid lookup from our logs
    our = pd.read_sql("SELECT rowid, player_id, game_date FROM goalie_game_logs", conn)
    our["game_date"] = pd.to_datetime(our["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    lookup = {(int(row["player_id"]), row["game_date"]): int(row["rowid"])
              for _, row in our.iterrows()}

    game_metrics["player_id_mp"] = game_metrics["name_norm"].map(name_to_id)
    game_metrics["game_date_str"] = pd.to_datetime(
        game_metrics.get("mp_game_date", pd.NaT), errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    metric_cols = [c for c in ("gsax_game", "hdsv_pct_game", "xgoals_against") if c in game_metrics.columns]
    n = 0
    for _, row in game_metrics.iterrows():
        pid = row.get("player_id_mp")
        gdate = row.get("game_date_str")
        if pd.isna(pid) or pd.isna(gdate):
            continue
        rowid = lookup.get((int(pid), gdate))
        if rowid is None:
            continue
        sets, vals = [], []
        for col in metric_cols:
            v = row.get(col)
            if v is not None and pd.notna(v):
                sets.append(f"{col}=?")
                vals.append(float(v))
        if sets:
            vals.append(rowid)
            cursor.execute(f"UPDATE goalie_game_logs SET {','.join(sets)} WHERE rowid=?", vals)
            n += 1

    conn.commit()
    return n


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # ── Season-level ──────────────────────────────────────────────────────────
    print("\n=== Season-level MoneyPuck data ===")
    raw_season = build_season_df()
    season_metrics = compute_season_metrics(raw_season)
    print(f"  Computed metrics for {len(season_metrics)} goalie-seasons")
    print(f"  Sample GSAx range: {season_metrics['gsax'].min():.1f} to {season_metrics['gsax'].max():.1f}")
    n = merge_into_season_stats(conn, season_metrics)
    print(f"  Updated {n} season-stat rows with GSAx + HDSV%")

    # ── Game-level ────────────────────────────────────────────────────────────
    print("\n=== Game-level MoneyPuck data ===")
    raw_game = build_game_df()
    if not raw_game.empty:
        game_metrics = compute_game_metrics(raw_game)
        n2 = merge_into_game_logs(conn, game_metrics)
        print(f"  Updated {n2} game-log rows with per-game GSAx")
    else:
        print("  No game-level data available from MoneyPuck")

    conn.close()

    # ── Validation ────────────────────────────────────────────────────────────
    conn2 = sqlite3.connect(DB_PATH)
    s1 = pd.read_sql(
        "SELECT COUNT(*) n, AVG(gsax) avg_gsax, AVG(hdsv_pct) avg_hdsv "
        "FROM goalie_season_stats WHERE gsax IS NOT NULL", conn2
    )
    s2 = pd.read_sql(
        "SELECT player_name, SUM(gsax) total_gsax, AVG(hdsv_pct) avg_hdsv "
        "FROM goalie_season_stats WHERE gsax IS NOT NULL "
        "GROUP BY player_name ORDER BY total_gsax DESC LIMIT 10", conn2
    )
    conn2.close()

    print(f"\n=== Validation ===")
    print(f"  Season-stat rows with GSAx: {int(s1['n'].iloc[0]):,}")
    if s1['avg_gsax'].iloc[0] is not None:
        print(f"  League avg GSAx/season: {s1['avg_gsax'].iloc[0]:+.2f}")
        print(f"  League avg HDSV%: {s1['avg_hdsv'].iloc[0]:.4f}")
        print("\n  Top 10 goalies by career GSAx:")
        for _, r in s2.iterrows():
            print(f"    {r['player_name']:<28} GSAx={r['total_gsax']:+.1f}  HDSV%={r['avg_hdsv']:.4f}")


if __name__ == "__main__":
    main()
