"""
export_dashboard_data.py
Exports pre-aggregated data from kopitar.db to JSON files for the React dashboard.
"""

import json
import math
import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DB_PATH = Path("D:/Python/Kopitar/data/scraped/kopitar.db")
OUT_DIR = Path("D:/Python/Kopitar/kopitar/dashboard-ui/public/data")

# ---------------------------------------------------------------------------
# Arena coordinates and division/conference mappings
# ---------------------------------------------------------------------------
ARENA_COORDS = {
    "BOS": (42.3662, -71.0621), "BUF": (42.8749, -78.8765), "DET": (42.3410, -83.0551),
    "FLA": (26.1584, -80.3258), "MTL": (45.4961, -73.5694), "OTT": (45.2965, -75.9270),
    "TBL": (27.9428, -82.4519), "TOR": (43.6435, -79.3791), "CAR": (35.8031, -78.7228),
    "CBJ": (39.9693, -83.0061), "NJD": (40.7335, -74.1712), "NYI": (40.7228, -73.5903),
    "NYR": (40.7505, -73.9934), "PHI": (39.9012, -75.1720), "PIT": (40.4396, -79.9892),
    "WSH": (38.8981, -77.0209), "CHI": (41.8807, -87.6742), "COL": (39.7486, -105.0078),
    "DAL": (32.7905, -96.8100), "MIN": (44.9449, -93.1010), "NSH": (36.1591, -86.7785),
    "STL": (38.6267, -90.2028), "WPG": (49.8928, -97.1439), "ANA": (33.8078, -117.8763),
    "UTA": (40.7683, -111.9011), "ARI": (33.5320, -112.0607), "CGY": (51.0375, -114.0514),
    "EDM": (53.5461, -113.4938), "LAK": (34.0430, -118.2673), "SJS": (37.3329, -121.9010),
    "SEA": (47.6216, -122.3544), "VGK": (36.1028, -115.1784), "VAN": (49.2778, -123.1088),
}

DIVISIONS = {
    "Atlantic":      ["BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TBL", "TOR"],
    "Metropolitan":  ["CAR", "CBJ", "NJD", "NYI", "NYR", "PHI", "PIT", "WSH"],
    "Central":       ["CHI", "COL", "DAL", "MIN", "NSH", "STL", "WPG", "UTA", "ARI"],
    "Pacific":       ["ANA", "CGY", "EDM", "LAK", "SJS", "SEA", "VGK", "VAN"],
}

CONFERENCES = {
    "Eastern": ["Atlantic", "Metropolitan"],
    "Western": ["Central", "Pacific"],
}

# Lookup: team -> division, conference
TEAM_DIVISION = {}
TEAM_CONFERENCE = {}
for div, teams in DIVISIONS.items():
    conf = next(c for c, divs in CONFERENCES.items() if div in divs)
    for t in teams:
        TEAM_DIVISION[t] = div
        TEAM_CONFERENCE[t] = conf

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def nan_to_none(value):
    """Convert NaN / numpy scalars to Python-native types safe for JSON."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    return value


def safe_round(value, decimals=4):
    """Round a value; return None if NaN/None."""
    v = nan_to_none(value)
    if v is None:
        return None
    return round(float(v), decimals)


def b2b_stats(df, sv_col="save_pct", b2b_col="is_back_to_back"):
    """Return (b2b_sv, rest_sv, delta, p_value, significant) for a dataframe."""
    b2b = df.loc[df[b2b_col] == 1, sv_col].dropna()
    rest = df.loc[df[b2b_col] == 0, sv_col].dropna()
    b2b_mean = float(b2b.mean()) if len(b2b) > 0 else None
    rest_mean = float(rest.mean()) if len(rest) > 0 else None
    delta = (b2b_mean - rest_mean) if (b2b_mean is not None and rest_mean is not None) else None
    if len(b2b) >= 2 and len(rest) >= 2:
        _, p = stats.ttest_ind(b2b, rest, equal_var=False)
        p_value = float(p)
    else:
        p_value = None
    significant = (p_value is not None and p_value < 0.05)
    return b2b_mean, rest_mean, delta, p_value, significant


def season_label(s: str) -> str:
    """'20152016' -> '2015-16'"""
    return f"{s[:4]}-{s[6:]}"


def load_db() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load both tables from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    gl = pd.read_sql("SELECT * FROM goalie_game_logs", conn)
    ss = pd.read_sql("SELECT * FROM goalie_season_stats", conn)
    conn.close()
    # Parse game_date
    gl["game_date"] = pd.to_datetime(gl["game_date"])
    return gl, ss


def write_json(path: Path, data, label: str):
    """Write data as JSON and print file size."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, default=nan_to_none, indent=2)
    size = path.stat().st_size
    print(f"  [{label}] -> {path.name}  ({size:,} bytes)")
    return size


# ---------------------------------------------------------------------------
# 1. overview.json
# ---------------------------------------------------------------------------

def export_overview(gl: pd.DataFrame) -> dict:
    print("\n[1/7] Building overview.json ...")
    total_games = len(gl)
    unique_goalies = gl["player_id"].nunique()
    seasons = gl["season"].nunique()
    b2b_games = int((gl["is_back_to_back"] == 1).sum())
    b2b_rate = round(b2b_games / total_games, 4) if total_games > 0 else 0.0

    rs = gl[gl["game_type"] == 2].copy()
    b2b_sv, rest_sv, delta, p_value, significant = b2b_stats(rs)

    data = {
        "kpis": {
            "total_games": total_games,
            "unique_goalies": unique_goalies,
            "seasons": seasons,
            "b2b_games": b2b_games,
            "b2b_rate": b2b_rate,
        },
        "league_b2b": {
            "b2b_sv": safe_round(b2b_sv),
            "rest_sv": safe_round(rest_sv),
            "delta": safe_round(delta),
            "p_value": safe_round(p_value),
            "significant": significant,
        },
    }
    return data


# ---------------------------------------------------------------------------
# 2. teams.json
# ---------------------------------------------------------------------------

def export_teams(gl: pd.DataFrame) -> list:
    print("\n[2/7] Building teams.json ...")
    rs = gl[gl["game_type"] == 2].copy()

    records = []
    for team, grp in rs.groupby("team"):
        if team not in ARENA_COORDS:
            continue
        if len(grp) < 10:
            continue

        b2b_grp = grp[grp["is_back_to_back"] == 1]
        rest_grp = grp[grp["is_back_to_back"] == 0]

        b2b_sv_val = safe_round(b2b_grp["save_pct"].mean()) if len(b2b_grp) >= 3 else None
        rest_sv_val = safe_round(rest_grp["save_pct"].mean())
        b2b_delta = safe_round(b2b_sv_val - rest_sv_val) if b2b_sv_val is not None and rest_sv_val is not None else None

        lat, lon = ARENA_COORDS[team]
        records.append({
            "team": team,
            "division": TEAM_DIVISION.get(team, "Unknown"),
            "conference": TEAM_CONFERENCE.get(team, "Unknown"),
            "total_games": int(len(grp)),
            "avg_sv": safe_round(grp["save_pct"].mean()),
            "b2b_starts": int(len(b2b_grp)),
            "b2b_sv": b2b_sv_val,
            "rest_sv": rest_sv_val,
            "b2b_delta": b2b_delta,
            "avg_travel_miles": safe_round(grp["travel_miles"].mean(), 1),
            "lat": lat,
            "lon": lon,
        })

    records.sort(key=lambda x: x["team"])
    return records


# ---------------------------------------------------------------------------
# 3. goalies.json
# ---------------------------------------------------------------------------

def export_goalies(gl: pd.DataFrame, ss: pd.DataFrame) -> list:
    print("\n[3/7] Building goalies.json ...")
    rs = gl[gl["game_type"] == 2].copy()

    # Build player_name lookup from season_stats (most recent season per player)
    name_lookup = (
        ss[ss["game_type"] == 2]
        .sort_values("season", ascending=False)
        .drop_duplicates("player_id")
        .set_index("player_id")["player_name"]
        .to_dict()
    )

    # avg GAA from season_stats (regular season, weighted by games_played)
    ss_rs = ss[ss["game_type"] == 2].copy()
    gaa_lookup = (
        ss_rs.groupby("player_id")
        .apply(lambda d: (d["gaa"] * d["games_played"]).sum() / d["games_played"].sum(), include_groups=False)
        .to_dict()
    )

    # Career GSAx and HDSV% from season_stats
    career_gsax_lookup = ss_rs.groupby("player_id")["gsax"].sum().to_dict() if "gsax" in ss_rs.columns else {}

    def _weighted_hdsv(g):
        if "hd_shots_ag" not in g.columns or "hdsv_pct" not in g.columns:
            return None
        shots = g["hd_shots_ag"].fillna(0)
        total = float(shots.sum())
        if total == 0:
            return None
        return float((shots * g["hdsv_pct"].fillna(0)).sum() / total)

    career_hdsv_lookup = (
        ss_rs.groupby("player_id").apply(_weighted_hdsv, include_groups=False).to_dict()
        if "hdsv_pct" in ss_rs.columns and "hd_shots_ag" in ss_rs.columns else {}
    )

    records = []
    for pid, grp in rs.groupby("player_id"):
        if len(grp) < 30:
            continue

        b2b_grp = grp[grp["is_back_to_back"] == 1]
        rest_grp = grp[grp["is_back_to_back"] == 0]

        b2b_sv_val = safe_round(b2b_grp["save_pct"].mean()) if len(b2b_grp) >= 3 else None
        rest_sv_val = safe_round(rest_grp["save_pct"].mean())
        b2b_delta = safe_round(b2b_sv_val - rest_sv_val) if b2b_sv_val is not None and rest_sv_val is not None else None

        teams = sorted(grp["team"].unique().tolist())
        records.append({
            "player_id": int(pid),
            "player_name": name_lookup.get(pid, f"Player {pid}"),
            "teams": teams,
            "total_games": int(len(grp)),
            "avg_sv": safe_round(grp["save_pct"].mean()),
            "avg_gaa": safe_round(gaa_lookup.get(pid), 4),
            "b2b_games": int(len(b2b_grp)),
            "b2b_sv": b2b_sv_val,
            "rest_sv": rest_sv_val,
            "b2b_delta": b2b_delta,
            "avg_travel_miles": safe_round(grp["travel_miles"].mean(), 1),
            "career_gsax": safe_round(career_gsax_lookup.get(pid), 2),
            "career_hdsv_pct": safe_round(career_hdsv_lookup.get(pid)),
        })

    records.sort(key=lambda x: x["total_games"], reverse=True)
    return records


# ---------------------------------------------------------------------------
# 4. recovery.json
# ---------------------------------------------------------------------------

def export_recovery(gl: pd.DataFrame) -> list:
    print("\n[4/7] Building recovery.json ...")
    rs = gl[(gl["game_type"] == 2) & (gl["days_rest"].notna())].copy()
    rs["days_rest"] = rs["days_rest"].astype(int)
    rs = rs[rs["days_rest"].between(0, 14)]

    records = []
    for dr, grp in rs.groupby("days_rest"):
        sv = grp["save_pct"].dropna()
        n = len(sv)
        if n < 30:
            continue
        mean = float(sv.mean())
        std = float(sv.std())
        se = std / math.sqrt(n)
        records.append({
            "days_rest": int(dr),
            "mean_sv": safe_round(mean),
            "count": n,
            "std": safe_round(std),
            "ci_lower": safe_round(mean - 1.96 * se),
            "ci_upper": safe_round(mean + 1.96 * se),
        })

    records.sort(key=lambda x: x["days_rest"])
    return records


# ---------------------------------------------------------------------------
# 5. seasons.json
# ---------------------------------------------------------------------------

def export_seasons(gl: pd.DataFrame) -> list:
    print("\n[5/7] Building seasons.json ...")
    rs = gl[gl["game_type"] == 2].copy()

    records = []
    for season, grp in rs.groupby("season"):
        b2b_sv, rest_sv, delta, p_value, significant = b2b_stats(grp)
        b2b_n = int((grp["is_back_to_back"] == 1).sum())
        records.append({
            "season": season,
            "label": season_label(season),
            "total_games": int(len(grp)),
            "b2b_n": b2b_n,
            "b2b_sv": safe_round(b2b_sv),
            "rest_sv": safe_round(rest_sv),
            "delta": safe_round(delta),
            "p_value": safe_round(p_value),
            "significant": significant,
        })

    records.sort(key=lambda x: x["season"])
    return records


# ---------------------------------------------------------------------------
# 6. divisions.json
# ---------------------------------------------------------------------------

def export_divisions(gl: pd.DataFrame) -> list:
    print("\n[6/7] Building divisions.json ...")
    rs = gl[gl["game_type"] == 2].copy()

    # Map each row's team to a division
    rs["division"] = rs["team"].map(TEAM_DIVISION)
    rs = rs[rs["division"].notna()]

    div_records = []
    for div, grp in rs.groupby("division"):
        b2b_sv_val, rest_sv_val, delta, _, _ = b2b_stats(grp)
        b2b_count = int((grp["is_back_to_back"] == 1).sum())
        b2b_rate = round(b2b_count / len(grp), 4) if len(grp) > 0 else 0.0
        div_records.append({
            "division": div,
            "total_games": int(len(grp)),
            "b2b_rate": b2b_rate,
            "avg_sv": safe_round(grp["save_pct"].mean()),
            "b2b_sv": safe_round(b2b_sv_val),
            "rest_sv": safe_round(rest_sv_val),
            "b2b_delta": safe_round(delta),
            "avg_travel_miles": safe_round(grp["travel_miles"].mean(), 1),
        })

    # Sort by avg_travel_miles descending (Pacific, Central, Metropolitan, Atlantic)
    div_records.sort(key=lambda x: (x["avg_travel_miles"] or 0), reverse=True)
    return div_records


# ---------------------------------------------------------------------------
# 8. players.json
# ---------------------------------------------------------------------------

def export_players(conn) -> list:
    print("\n[8/10] Building players.json ...")
    try:
        df = pd.read_sql(
            "SELECT * FROM skater_season_stats WHERE game_type=2 ORDER BY season, points DESC",
            conn,
        )
    except Exception as e:
        print(f"  skater_season_stats not found: {e}")
        return []

    records = []
    for _, row in df.iterrows():
        pos = row.get("position", "")
        pos_label = "Forward" if pos in ("C", "L", "R") else ("Defenseman" if pos == "D" else pos)
        records.append({
            "player_id": int(row["player_id"]) if pd.notna(row["player_id"]) else None,
            "player_name": row["player_name"],
            "position": pos,
            "position_label": pos_label,
            "team": row["team"],
            "season": row["season"],
            "season_label": season_label(row["season"]),
            "games_played": int(row.get("games_played", 0) or 0),
            "goals": int(row.get("goals", 0) or 0),
            "assists": int(row.get("assists", 0) or 0),
            "points": int(row.get("points", 0) or 0),
            "plus_minus": int(row.get("plus_minus", 0) or 0),
            "pim": int(row.get("pim", 0) or 0),
            "shots": int(row.get("shots", 0) or 0),
            "toi_per_game": safe_round(row.get("toi_per_game"), 2),
            "pp_points": int(row.get("pp_points", 0) or 0),
            "sh_points": int(row.get("sh_points", 0) or 0),
            "points_per_game": safe_round(row.get("points_per_game"), 3),
        })

    return records


# ---------------------------------------------------------------------------
# 9. gsax.json
# ---------------------------------------------------------------------------

def export_gsax(ss: pd.DataFrame) -> list:
    print("\n[8/9] Building gsax.json ...")
    ss_rs = ss[(ss["game_type"] == 2) & ss["gsax"].notna()].copy() if "gsax" in ss.columns else pd.DataFrame()
    if ss_rs.empty:
        print("  No GSAx data available")
        return []

    name_lookup = (
        ss_rs.sort_values("season", ascending=False)
        .drop_duplicates("player_id")
        .set_index("player_id")["player_name"]
        .to_dict()
    )

    records = []
    for pid, grp in ss_rs.groupby("player_id"):
        career_gsax = float(grp["gsax"].sum())
        career_gsax_per60 = float(grp["gsax_per60"].mean()) if "gsax_per60" in grp.columns and grp["gsax_per60"].notna().any() else None

        if "hd_shots_ag" in grp.columns and "hdsv_pct" in grp.columns:
            shots = grp["hd_shots_ag"].fillna(0)
            total_shots = float(shots.sum())
            career_hdsv = float((shots * grp["hdsv_pct"].fillna(0)).sum() / total_shots) if total_shots > 0 else None
        else:
            career_hdsv = None

        seasons_data = []
        for _, row in grp.sort_values("season").iterrows():
            gp = row.get("games_played", None)
            seasons_data.append({
                "season": row["season"],
                "label": season_label(row["season"]),
                "gsax": safe_round(row.get("gsax"), 2),
                "gsax_per60": safe_round(row.get("gsax_per60"), 4),
                "hdsv_pct": safe_round(row.get("hdsv_pct")),
                "games": int(gp) if gp is not None and pd.notna(gp) else 0,
            })

        records.append({
            "player_id": int(pid),
            "player_name": name_lookup.get(pid, f"Player {pid}"),
            "career_gsax": safe_round(career_gsax, 2),
            "career_gsax_per60": safe_round(career_gsax_per60, 4),
            "career_hdsv_pct": safe_round(career_hdsv),
            "seasons_with_gsax": len(grp),
            "seasons": seasons_data,
        })

    records.sort(key=lambda x: x["career_gsax"] if x["career_gsax"] is not None else -9999, reverse=True)
    print(f"  GSAx leaders: {len(records)} goalies")
    return records


# ---------------------------------------------------------------------------
# 9. schedule_stress.json
# ---------------------------------------------------------------------------

def export_schedule_stress(gl: pd.DataFrame) -> dict:
    print("\n[9/9] Building schedule_stress.json ...")
    rs = gl[gl["game_type"] == 2].copy()
    sv = "save_pct"
    result: dict = {}

    # 4-in-6 and 3-in-4
    for key, col, label in [("four_in_six", "is_4_in_6", "4-in-6"), ("three_in_four", "is_3_in_4", "3-in-4")]:
        if col not in rs.columns:
            continue
        with_f = rs[rs[col] == 1][sv].dropna()
        without_f = rs[rs[col] == 0][sv].dropna()
        if len(with_f) > 5 and len(without_f) > 5:
            _, p = stats.ttest_ind(with_f, without_f)
            delta = float(with_f.mean() - without_f.mean())
            result[key] = {
                "label": label,
                "mean_with": safe_round(float(with_f.mean())),
                "mean_without": safe_round(float(without_f.mean())),
                "delta": safe_round(delta),
                "p_value": safe_round(float(p)),
                "n_with": int(len(with_f)),
                "n_without": int(len(without_f)),
                "significant": bool(p < 0.05),
            }
            print(f"  {label}: delta={delta:+.5f}  p={p:.4f}  n_with={len(with_f)}")

    # Road trip legs
    if "road_trip_leg" in rs.columns:
        legs = []
        for leg in sorted(rs["road_trip_leg"].dropna().unique()):
            leg_i = int(leg)
            g = rs[rs["road_trip_leg"] == leg_i][sv].dropna()
            if len(g) < 50:
                continue
            legs.append({
                "leg": leg_i,
                "label": "Home" if leg_i == 0 else f"Road Leg {leg_i}",
                "mean_sv": safe_round(float(g.mean())),
                "count": int(len(g)),
            })
        result["road_trip_legs"] = legs
        print(f"  Road trip legs: {len(legs)} groups")

    # Altitude bins
    if "venue_altitude_ft" in rs.columns:
        alt_bins = [
            ("Sea Level (<100ft)", rs["venue_altitude_ft"] < 100),
            ("Low (100–999ft)", (rs["venue_altitude_ft"] >= 100) & (rs["venue_altitude_ft"] < 1000)),
            ("Mid (1000–1999ft)", (rs["venue_altitude_ft"] >= 1000) & (rs["venue_altitude_ft"] < 2000)),
            ("High (≥2000ft)", rs["venue_altitude_ft"] >= 2000),
        ]
        alt_records = []
        for label, mask in alt_bins:
            sub = rs[mask][sv].dropna()
            if len(sub) < 50:
                continue
            alt_records.append({
                "label": label,
                "mean_sv": safe_round(float(sub.mean())),
                "count": int(len(sub)),
            })
        result["altitude"] = alt_records
        print(f"  Altitude bins: {len(alt_records)} groups")

    # Season phase
    if "season_phase" in rs.columns:
        phase_labels = {"early": "Early (Gm 1–20)", "mid": "Mid (Gm 21–60)", "stretch": "Stretch (Gm 61+)"}
        phase_records = []
        for phase in ["early", "mid", "stretch"]:
            g = rs[rs["season_phase"] == phase][sv].dropna()
            if len(g) < 50:
                continue
            phase_records.append({
                "phase": phase,
                "label": phase_labels[phase],
                "mean_sv": safe_round(float(g.mean())),
                "count": int(len(g)),
            })
        result["season_phase"] = phase_records
        print(f"  Season phases: {len(phase_records)} groups")

    return result


# ---------------------------------------------------------------------------
# 10. team_logs/{TEAM}.json
# ---------------------------------------------------------------------------

def export_team_logs(gl: pd.DataFrame, ss: pd.DataFrame):
    print("\n[7/7] Building team_logs/ ...")
    rs = gl[gl["game_type"] == 2].copy()

    # Build player_name lookup: prefer season-matching record, fallback to any
    ss_rs = ss[ss["game_type"] == 2][["player_id", "season", "player_name"]].copy()
    name_by_pid_season = ss_rs.set_index(["player_id", "season"])["player_name"].to_dict()
    name_fallback = (
        ss_rs.sort_values("season", ascending=False)
        .drop_duplicates("player_id")
        .set_index("player_id")["player_name"]
        .to_dict()
    )

    logs_dir = OUT_DIR / "team_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    files_written = 0
    for team, grp in rs.groupby("team"):
        if team not in ARENA_COORDS:
            continue

        rows = []
        for _, row in grp.sort_values("game_date").iterrows():
            pid = row["player_id"]
            season = row["season"]
            name = name_by_pid_season.get((pid, season), name_fallback.get(pid, f"Player {pid}"))
            rows.append({
                "date": row["game_date"].strftime("%Y-%m-%d"),
                "opponent": row["opponent"],
                "home_away": row["home_away"],
                "save_pct": safe_round(row["save_pct"]),
                "shots_against": nan_to_none(row["shots_against"]),
                "goals_against": nan_to_none(row["goals_against"]),
                "days_rest": nan_to_none(row["days_rest"]),
                "is_b2b": int(row["is_back_to_back"]) if pd.notna(row["is_back_to_back"]) else None,
                "travel_miles": safe_round(row["travel_miles"], 1),
                "goalie": name,
                "season": season,
                "decision": nan_to_none(row["decision"]),
            })

        out_path = logs_dir / f"{team}.json"
        write_json(out_path, rows, f"team_logs/{team}")
        files_written += 1

    print(f"  Written {files_written} team log files.")
    return files_written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Kopitar Dashboard Data Export")
    print("=" * 60)
    print(f"DB    : {DB_PATH}")
    print(f"OutDir: {OUT_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nLoading database ...")
    gl, ss = load_db()
    print(f"  goalie_game_logs  : {len(gl):,} rows")
    print(f"  goalie_season_stats: {len(ss):,} rows")

    sizes = {}

    # 1. overview.json
    overview = export_overview(gl)
    sizes["overview.json"] = write_json(OUT_DIR / "overview.json", overview, "overview")

    # 2. teams.json
    teams = export_teams(gl)
    sizes["teams.json"] = write_json(OUT_DIR / "teams.json", teams, "teams")
    print(f"  Teams exported: {len(teams)}")

    # 3. goalies.json
    goalies = export_goalies(gl, ss)
    sizes["goalies.json"] = write_json(OUT_DIR / "goalies.json", goalies, "goalies")
    print(f"  Goalies exported (>=30 RS games): {len(goalies)}")

    # 4. recovery.json
    recovery = export_recovery(gl)
    sizes["recovery.json"] = write_json(OUT_DIR / "recovery.json", recovery, "recovery")
    print(f"  Recovery day groups: {len(recovery)}")

    # 5. seasons.json
    seasons = export_seasons(gl)
    sizes["seasons.json"] = write_json(OUT_DIR / "seasons.json", seasons, "seasons")
    print(f"  Seasons: {len(seasons)}")

    # 6. divisions.json
    divisions = export_divisions(gl)
    sizes["divisions.json"] = write_json(OUT_DIR / "divisions.json", divisions, "divisions")
    print(f"  Divisions: {len(divisions)}")

    # 7. team_logs/
    n_team_logs = export_team_logs(gl, ss)

    # 8. players.json (skater season stats)
    players_data = export_players(conn_raw := sqlite3.connect(DB_PATH))
    conn_raw.close()
    sizes["players.json"] = write_json(OUT_DIR / "players.json", players_data, "players")
    print(f"  Players exported: {len(players_data)}")

    # 9. gsax.json
    gsax_data = export_gsax(ss)
    sizes["gsax.json"] = write_json(OUT_DIR / "gsax.json", gsax_data, "gsax")
    print(f"  GSAx entries: {len(gsax_data)}")

    # 9. schedule_stress.json
    stress_data = export_schedule_stress(gl)
    sizes["schedule_stress.json"] = write_json(OUT_DIR / "schedule_stress.json", stress_data, "schedule_stress")

    print("\n" + "=" * 60)
    print("Export complete!")
    print("=" * 60)
    total = sum(sizes.values())
    for name, sz in sizes.items():
        print(f"  {name:<20} {sz:>10,} bytes")
    print(f"  team_logs/           {n_team_logs} files")
    print(f"\n  Total top-level size: {total:,} bytes")
    print(f"  Output directory    : {OUT_DIR}")


if __name__ == "__main__":
    main()
