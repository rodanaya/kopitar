"""Write enriched variables from CSV back to DB via player_id + game_id."""
import sqlite3
import pandas as pd

DB  = "data/scraped/kopitar.db"
CSV = "data/scraped/goalie_game_logs_enriched_v2.csv"

df = pd.read_csv(CSV, low_memory=False)
print(f"CSV: {len(df):,} rows")

conn = sqlite3.connect(DB)
cursor = conn.cursor()

existing = {r[1] for r in cursor.execute("PRAGMA table_info(goalie_game_logs)")}
NEW_COLS = {
    "venue_altitude_ft": "INTEGER", "altitude_delta": "INTEGER",
    "eastward_travel": "INTEGER",   "road_trip_leg": "INTEGER",
    "is_3_in_4": "INTEGER",         "is_4_in_6": "INTEGER",
    "consecutive_starts_streak": "INTEGER", "season_game_number": "INTEGER",
    "season_phase": "TEXT",         "shots_prev_game": "INTEGER",
}
for col, dtype in NEW_COLS.items():
    if col not in existing:
        cursor.execute(f"ALTER TABLE goalie_game_logs ADD COLUMN {col} {dtype}")
conn.commit()

total = 0
for col in NEW_COLS:
    if col not in df.columns:
        print(f"  SKIP {col} (not in CSV)")
        continue
    sub = df[["player_id", "game_id", col]].dropna(subset=[col])
    rows = []
    for _, r in sub.iterrows():
        val = str(r[col]) if col == "season_phase" else int(r[col])
        rows.append((val, int(r["player_id"]), str(r["game_id"])))
    cursor.executemany(
        f"UPDATE goalie_game_logs SET {col}=? WHERE player_id=? AND game_id=?", rows
    )
    total += len(rows)
    print(f"  {col}: {len(rows):,}")

conn.commit()
conn.close()
print(f"\nTotal updates: {total:,}")

# Validate
conn2 = sqlite3.connect(DB)
check = pd.read_sql(
    "SELECT is_3_in_4, is_4_in_6, road_trip_leg, season_phase, venue_altitude_ft "
    "FROM goalie_game_logs WHERE game_type=2 LIMIT 5", conn2
)
conn2.close()
print("\nSample rows from DB:")
print(check)

# Quick fatigue analysis with new variables
conn3 = sqlite3.connect(DB)
df2 = pd.read_sql("SELECT * FROM goalie_game_logs WHERE game_type=2", conn3)
conn3.close()

import scipy.stats as stats

for label, col, val in [("3-in-4", "is_3_in_4", 1), ("4-in-6", "is_4_in_6", 1)]:
    hi = df2[df2[col]==val]["save_pct"].dropna()
    lo = df2[df2[col]==0]["save_pct"].dropna()
    if len(hi) > 5 and len(lo) > 5:
        t, p = stats.ttest_ind(hi, lo)
        print(f"{label}: {hi.mean():.4f} (n={len(hi)}) vs {lo.mean():.4f}  delta={hi.mean()-lo.mean():+.4f}  p={p:.4f}")

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

print("\nAltitude (home team perspective):")
hi = df2[df2["venue_altitude_ft"]>=2000]["save_pct"].dropna()
lo = df2[df2["venue_altitude_ft"]<2000]["save_pct"].dropna()
if len(hi) > 50 and len(lo) > 50:
    t, p = stats.ttest_ind(hi, lo)
    print(f"  >=2000ft: {hi.mean():.4f} (n={len(hi):,})")
    print(f"  <2000ft:  {lo.mean():.4f} (n={len(lo):,})")
    print(f"  delta={hi.mean()-lo.mean():+.4f}  p={p:.4f}")
