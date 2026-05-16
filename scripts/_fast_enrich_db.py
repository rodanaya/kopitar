"""
Fast re-write: load enriched CSV and patch goalie_game_logs in-place via temp table + SQL UPDATE.
Avoids row-by-row Python loops — uses a single SQL UPDATE...FROM join.
"""
import sqlite3
import pandas as pd

DB  = "data/scraped/kopitar.db"
CSV = "data/scraped/goalie_game_logs_enriched_v2.csv"

NEW_COLS = [
    "venue_altitude_ft", "altitude_delta", "eastward_travel",
    "road_trip_leg", "is_3_in_4", "is_4_in_6",
    "consecutive_starts_streak", "season_game_number",
    "season_phase", "shots_prev_game",
]

print(f"Loading {CSV}...")
df = pd.read_csv(CSV, low_memory=False)
print(f"  {len(df):,} rows, {len(df.columns)} columns")

conn = sqlite3.connect(DB)
cursor = conn.cursor()

# Add new columns to game_logs if missing
existing = {r[1] for r in cursor.execute("PRAGMA table_info(goalie_game_logs)")}
for col in NEW_COLS:
    if col not in existing:
        dtype = "TEXT" if col == "season_phase" else "INTEGER"
        cursor.execute(f"ALTER TABLE goalie_game_logs ADD COLUMN {col} {dtype}")
conn.commit()

# Write a slim temp table: just keys + new cols
key_cols = ["player_id", "game_id"]
present = [c for c in NEW_COLS if c in df.columns]
temp_df = df[key_cols + present].copy()
temp_df["game_id"] = temp_df["game_id"].astype(str)

print(f"Writing temp table ({len(temp_df):,} rows)...")
temp_df.to_sql("_enrich_tmp", conn, if_exists="replace", index=False)

# Single SQL UPDATE using a correlated subquery (works in all SQLite versions)
print("Running bulk SQL update...")
for col in present:
    cursor.execute(f"""
        UPDATE goalie_game_logs
        SET {col} = (
            SELECT t.{col}
            FROM _enrich_tmp t
            WHERE t.player_id = goalie_game_logs.player_id
              AND t.game_id   = CAST(goalie_game_logs.game_id AS TEXT)
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM _enrich_tmp t
            WHERE t.player_id = goalie_game_logs.player_id
              AND t.game_id   = CAST(goalie_game_logs.game_id AS TEXT)
        )
    """)
    print(f"  {col}: {cursor.rowcount:,} rows updated")
    conn.commit()

# Drop temp table
cursor.execute("DROP TABLE IF EXISTS _enrich_tmp")
conn.commit()
conn.close()

# Validate
import scipy.stats as stats

conn2 = sqlite3.connect(DB)
df2 = pd.read_sql("SELECT * FROM goalie_game_logs WHERE game_type=2", conn2)
conn2.close()

print(f"\n=== New variable effects (regular season) ===")
for label, col in [("3-in-4", "is_3_in_4"), ("4-in-6", "is_4_in_6")]:
    hi = df2[df2[col]==1]["save_pct"].dropna()
    lo = df2[df2[col]==0]["save_pct"].dropna()
    if len(hi) > 5:
        t, p = stats.ttest_ind(hi, lo)
        d = (hi.mean()-lo.mean())/df2["save_pct"].std()
        print(f"{label:8s}: {hi.mean():.4f} (n={len(hi):,}) vs {lo.mean():.4f}  delta={hi.mean()-lo.mean():+.5f}  p={p:.4f}  d={d:.3f}")

print("\nRoad trip leg:")
for leg in range(6):
    g = df2[df2["road_trip_leg"]==leg]["save_pct"].dropna()
    if len(g) > 50:
        print(f"  Leg {leg}: {g.mean():.4f}  n={len(g):,}")

print("\nSeason phase:")
for phase in ["early", "mid", "stretch"]:
    g = df2[df2["season_phase"]==phase]["save_pct"].dropna()
    if len(g) > 50:
        print(f"  {phase}: {g.mean():.4f}  n={len(g):,}")

print("\nAltitude:")
hi = df2[df2["venue_altitude_ft"]>=2000]["save_pct"].dropna()
lo = df2[df2["venue_altitude_ft"]<500]["save_pct"].dropna()
if len(hi) > 50 and len(lo) > 50:
    t, p = stats.ttest_ind(hi, lo)
    print(f"  >=2000ft: {hi.mean():.4f} (n={len(hi):,})  <500ft: {lo.mean():.4f} (n={len(lo):,})  delta={hi.mean()-lo.mean():+.5f}  p={p:.4f}")

print("\nDone.")
