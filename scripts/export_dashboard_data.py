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

    # ── Resilience scoring ─────────────────────────────────────────────────────
    qualifiers = [r for r in records if r["b2b_delta"] is not None and r["b2b_games"] >= 5]
    if len(qualifiers) >= 10:
        deltas = [r["b2b_delta"] for r in qualifiers]
        svs = [r["avg_sv"] for r in qualifiers]
        mean_delta = float(np.mean(deltas))
        std_delta = float(np.std(deltas))
        median_sv = float(np.median(svs))
        for r in records:
            if r["b2b_delta"] is not None and r["b2b_games"] >= 5:
                r["resilience_z"] = safe_round((r["b2b_delta"] - mean_delta) / std_delta, 2) if std_delta > 0 else 0.0
                is_elite = r["avg_sv"] > median_sv
                is_resilient = r["b2b_delta"] >= 0
                r["quadrant"] = (
                    "iron_man" if is_elite and is_resilient else
                    "vulnerable_star" if is_elite and not is_resilient else
                    "workhorse" if not is_elite and is_resilient else
                    "high_risk"
                )
            else:
                r["resilience_z"] = None
                r["quadrant"] = None
        counts = {}
        for r in qualifiers:
            counts[r["quadrant"]] = counts.get(r["quadrant"], 0) + 1
        print(f"  Resilience quadrants: {counts}")

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

    # League-average shots against per game (for effect size calculations)
    avg_shots = float(rs["shots_against"].mean()) if "shots_against" in rs.columns and rs["shots_against"].notna().any() else 31.5
    seasons_span = rs["season"].nunique() if "season" in rs.columns else 10

    # 4-in-6 and 3-in-4
    for key, col, label in [("four_in_six", "is_4_in_6", "4-in-6"), ("three_in_four", "is_3_in_4", "3-in-4")]:
        if col not in rs.columns:
            continue
        with_f = rs[rs[col] == 1][sv].dropna()
        without_f = rs[rs[col] == 0][sv].dropna()
        if len(with_f) > 5 and len(without_f) > 5:
            _, p = stats.ttest_ind(with_f, without_f)
            delta = float(with_f.mean() - without_f.mean())
            goals_cost = abs(delta) * avg_shots
            result[key] = {
                "label": label,
                "mean_with": safe_round(float(with_f.mean())),
                "mean_without": safe_round(float(without_f.mean())),
                "delta": safe_round(delta),
                "p_value": safe_round(float(p)),
                "n_with": int(len(with_f)),
                "n_without": int(len(without_f)),
                "significant": bool(p < 0.05),
                "goals_cost_per_game": safe_round(goals_cost, 3),
                "total_extra_goals": safe_round(goals_cost * len(with_f), 1),
                "extra_goals_per_team_season": safe_round(goals_cost * len(with_f) / (32 * seasons_span), 2),
            }
            print(f"  {label}: delta={delta:+.5f}  p={p:.4f}  n_with={len(with_f)}  goals_cost={goals_cost:.3f}/game")

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
# 11. ot_analysis.json
# ---------------------------------------------------------------------------

def export_ot_analysis(gl: pd.DataFrame) -> dict:
    print("\n[11/12] Building ot_analysis.json ...")
    rs = gl[gl["game_type"] == 2].copy()
    sv = "save_pct"
    result: dict = {}

    # OT game performance
    if "ot_flag" in rs.columns:
        ot = rs[rs["ot_flag"] == 1][sv].dropna()
        non_ot = rs[rs["ot_flag"] == 0][sv].dropna()
        if len(ot) > 5 and len(non_ot) > 5:
            _, p = stats.ttest_ind(ot, non_ot)
            result["ot_vs_non_ot"] = {
                "ot_sv": safe_round(float(ot.mean())),
                "non_ot_sv": safe_round(float(non_ot.mean())),
                "delta": safe_round(float(ot.mean() - non_ot.mean())),
                "n_ot": int(len(ot)),
                "n_non_ot": int(len(non_ot)),
                "p_value": safe_round(float(p)),
                "significant": bool(p < 0.05),
            }
            print(f"  OT sv={ot.mean():.4f} vs non-OT sv={non_ot.mean():.4f}  p={p:.4f}")

    # Performance after OT game (compound fatigue)
    if "prev_game_ot" in rs.columns:
        after_ot = rs[rs["prev_game_ot"] == 1][sv].dropna()
        after_non_ot = rs[rs["prev_game_ot"] == 0][sv].dropna()
        if len(after_ot) > 5 and len(after_non_ot) > 5:
            _, p = stats.ttest_ind(after_ot, after_non_ot)
            result["after_ot"] = {
                "after_ot_sv": safe_round(float(after_ot.mean())),
                "after_non_ot_sv": safe_round(float(after_non_ot.mean())),
                "delta": safe_round(float(after_ot.mean() - after_non_ot.mean())),
                "n_after_ot": int(len(after_ot)),
                "n_after_non_ot": int(len(after_non_ot)),
                "p_value": safe_round(float(p)),
                "significant": bool(p < 0.05),
            }
            print(f"  After OT sv={after_ot.mean():.4f} vs after non-OT sv={after_non_ot.mean():.4f}  p={p:.4f}")

        # Compound: OT game + next game is B2B
        if "is_back_to_back" in rs.columns:
            compound = rs[(rs["prev_game_ot"] == 1) & (rs["is_back_to_back"] == 1)][sv].dropna()
            regular_b2b = rs[(rs["prev_game_ot"] == 0) & (rs["is_back_to_back"] == 1)][sv].dropna()
            if len(compound) > 5 and len(regular_b2b) > 5:
                _, p = stats.ttest_ind(compound, regular_b2b)
                result["compound_stress"] = {
                    "ot_then_b2b_sv": safe_round(float(compound.mean())),
                    "regular_b2b_sv": safe_round(float(regular_b2b.mean())),
                    "delta": safe_round(float(compound.mean() - regular_b2b.mean())),
                    "n_compound": int(len(compound)),
                    "n_regular_b2b": int(len(regular_b2b)),
                    "p_value": safe_round(float(p)),
                    "significant": bool(p < 0.05),
                }
                print(f"  OT->B2B sv={compound.mean():.4f} vs regular B2B sv={regular_b2b.mean():.4f}  p={p:.4f}")

    # Score differential buckets: how does margin affect SV%?
    if "score_diff" in rs.columns:
        bins = [
            ("Blowout Loss (≤-4)", rs["score_diff"] <= -4),
            ("Loss (-3 to -1)", rs["score_diff"].between(-3, -1)),
            ("Tie/OT (0)", rs["score_diff"] == 0),
            ("Win (+1 to +3)", rs["score_diff"].between(1, 3)),
            ("Blowout Win (≥+4)", rs["score_diff"] >= 4),
        ]
        score_bins = []
        for label, mask in bins:
            sub = rs[mask][sv].dropna()
            if len(sub) < 30:
                continue
            score_bins.append({
                "label": label,
                "mean_sv": safe_round(float(sub.mean())),
                "count": int(len(sub)),
            })
        result["score_diff_bins"] = score_bins
        print(f"  Score diff bins: {len(score_bins)}")

    # Same-metro correction: B2B delta with vs without same-metro trips
    if "same_metro" in rs.columns and "is_back_to_back" in rs.columns:
        # Standard B2B (all)
        b2b_all = rs[rs["is_back_to_back"] == 1][sv].dropna()
        rest_all = rs[rs["is_back_to_back"] == 0][sv].dropna()
        # Metro-corrected B2B (exclude same-metro)
        b2b_corrected = rs[(rs["is_back_to_back"] == 1) & (rs["same_metro"] == 0)][sv].dropna()
        same_metro_only = rs[(rs["is_back_to_back"] == 1) & (rs["same_metro"] == 1)][sv].dropna()

        _, p_all = stats.ttest_ind(b2b_all, rest_all) if (len(b2b_all) > 2 and len(rest_all) > 2) else (None, None)
        _, p_corr = stats.ttest_ind(b2b_corrected, rest_all) if (len(b2b_corrected) > 2 and len(rest_all) > 2) else (None, None)

        result["metro_correction"] = {
            "b2b_all_sv": safe_round(float(b2b_all.mean())) if len(b2b_all) > 0 else None,
            "b2b_corrected_sv": safe_round(float(b2b_corrected.mean())) if len(b2b_corrected) > 0 else None,
            "same_metro_sv": safe_round(float(same_metro_only.mean())) if len(same_metro_only) > 0 else None,
            "rest_sv": safe_round(float(rest_all.mean())) if len(rest_all) > 0 else None,
            "delta_all": safe_round(float(b2b_all.mean() - rest_all.mean())) if len(b2b_all) > 0 else None,
            "delta_corrected": safe_round(float(b2b_corrected.mean() - rest_all.mean())) if len(b2b_corrected) > 0 else None,
            "n_b2b_all": int(len(b2b_all)),
            "n_b2b_corrected": int(len(b2b_corrected)),
            "n_same_metro": int(len(same_metro_only)),
            "p_all": safe_round(float(p_all)) if p_all is not None else None,
            "p_corrected": safe_round(float(p_corr)) if p_corr is not None else None,
        }
        print(f"  Metro correction: {len(same_metro_only)} same-metro B2B starts excluded")

    return result


# ---------------------------------------------------------------------------
# 12. skater_fatigue.json
# ---------------------------------------------------------------------------

def export_skater_fatigue(conn) -> dict:
    print("\n[12/12] Building skater_fatigue.json ...")
    try:
        df = pd.read_sql("""
            SELECT sg.player_id, sg.season, ss.player_name, ss.position,
                   sg.game_date, sg.toi_seconds, sg.is_back_to_back, sg.is_3_in_4,
                   sg.rest_days, sg.road_trip_leg, sg.home_road,
                   sg.goals, sg.assists, sg.points, sg.shots
            FROM skater_game_logs sg
            JOIN skater_season_stats ss
              ON sg.player_id = ss.player_id AND sg.season = ss.season
            WHERE ss.game_type = 2
        """, conn)
    except Exception as e:
        print(f"  skater_game_logs not available yet: {e}")
        return {}

    if df.empty:
        print("  No skater game log data yet")
        return {}

    print(f"  {len(df):,} skater game rows loaded")
    df["toi_min"] = df["toi_seconds"] / 60.0
    df["pos_group"] = df["position"].map(lambda p: "Forward" if p in ("C", "L", "R") else "Defense" if p == "D" else "Other")

    result: dict = {}

    # TOI by rest days (capped at 10)
    rested = df[(df["rest_days"].notna()) & (df["rest_days"] <= 10)].copy()
    rested["rest_days"] = rested["rest_days"].astype(int)
    toi_by_rest = []
    for dr, grp in rested.groupby("rest_days"):
        toi = grp["toi_min"].dropna()
        if len(toi) < 50:
            continue
        toi_by_rest.append({
            "rest_days": int(dr),
            "mean_toi": safe_round(float(toi.mean()), 2),
            "count": int(len(toi)),
        })
    result["toi_by_rest"] = sorted(toi_by_rest, key=lambda x: x["rest_days"])

    # B2B TOI delta overall and by position
    b2b_grp = df[df["is_back_to_back"] == 1]["toi_min"].dropna()
    rest_grp = df[df["is_back_to_back"] == 0]["toi_min"].dropna()
    if len(b2b_grp) > 5 and len(rest_grp) > 5:
        _, p = stats.ttest_ind(b2b_grp, rest_grp)
        result["b2b_overall"] = {
            "b2b_toi": safe_round(float(b2b_grp.mean()), 2),
            "rest_toi": safe_round(float(rest_grp.mean()), 2),
            "delta": safe_round(float(b2b_grp.mean() - rest_grp.mean()), 2),
            "p_value": safe_round(float(p)),
            "significant": bool(p < 0.05),
            "n_b2b": int(len(b2b_grp)),
            "n_rest": int(len(rest_grp)),
        }
        print(f"  B2B TOI: {b2b_grp.mean():.2f} vs rested {rest_grp.mean():.2f} min  p={p:.4f}")

    # By position
    pos_records = []
    for pos_group, pgrp in df.groupby("pos_group"):
        if pos_group == "Other":
            continue
        b2b = pgrp[pgrp["is_back_to_back"] == 1]["toi_min"].dropna()
        rest = pgrp[pgrp["is_back_to_back"] == 0]["toi_min"].dropna()
        if len(b2b) < 5 or len(rest) < 5:
            continue
        _, p = stats.ttest_ind(b2b, rest)
        pos_records.append({
            "position": pos_group,
            "b2b_toi": safe_round(float(b2b.mean()), 2),
            "rest_toi": safe_round(float(rest.mean()), 2),
            "delta": safe_round(float(b2b.mean() - rest.mean()), 2),
            "p_value": safe_round(float(p)),
            "n_b2b": int(len(b2b)),
            "n_rest": int(len(rest)),
        })
    result["by_position"] = pos_records

    # Top players by avg TOI (min 50 games, regular season only)
    player_stats = []
    for pid, pgrp in df.groupby("player_id"):
        if len(pgrp) < 50:
            continue
        name = pgrp["player_name"].iloc[0]
        pos = pgrp["pos_group"].iloc[0]
        avg_toi = float(pgrp["toi_min"].mean())
        b2b = pgrp[pgrp["is_back_to_back"] == 1]["toi_min"].dropna()
        rest = pgrp[pgrp["is_back_to_back"] == 0]["toi_min"].dropna()
        b2b_toi = float(b2b.mean()) if len(b2b) > 0 else None
        rest_toi = float(rest.mean()) if len(rest) > 0 else None
        delta = (b2b_toi - rest_toi) if (b2b_toi is not None and rest_toi is not None) else None
        player_stats.append({
            "player_id": int(pid),
            "player_name": name,
            "position": pos,
            "avg_toi": safe_round(avg_toi, 2),
            "b2b_toi": safe_round(b2b_toi, 2),
            "rest_toi": safe_round(rest_toi, 2),
            "b2b_delta": safe_round(delta, 2),
            "games": int(len(pgrp)),
            "b2b_games": int(len(b2b)),
        })
    player_stats.sort(key=lambda x: x["avg_toi"] or 0, reverse=True)
    result["top_players"] = player_stats[:50]
    print(f"  Player TOI profiles: {len(player_stats)} players (top 50 exported)")

    return result


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

    # 10. ot_analysis.json
    ot_data = export_ot_analysis(gl)
    sizes["ot_analysis.json"] = write_json(OUT_DIR / "ot_analysis.json", ot_data, "ot_analysis")

    # 11. skater_fatigue.json (requires skater_game_logs table)
    conn2 = sqlite3.connect(DB_PATH)
    skater_fat = export_skater_fatigue(conn2)
    conn2.close()
    if skater_fat:
        sizes["skater_fatigue.json"] = write_json(OUT_DIR / "skater_fatigue.json", skater_fat, "skater_fatigue")

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
