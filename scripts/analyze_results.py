import sqlite3
import pandas as pd
import scipy.stats as stats

conn = sqlite3.connect("data/scraped/kopitar.db")
df = pd.read_sql("SELECT * FROM goalie_game_logs", conn)
ss = pd.read_sql("SELECT DISTINCT player_id, player_name FROM goalie_season_stats", conn)
df = df.merge(ss, on="player_id", how="left")

# Statistical significance of B2B effect
b2b = df[df["is_back_to_back"] == 1]["save_pct"].dropna()
rest = df[df["is_back_to_back"] == 0]["save_pct"].dropna()
t, p = stats.ttest_ind(b2b, rest)
sig = "SIGNIFICANT (p<0.05)" if p < 0.05 else "not significant"
effect_d = abs(b2b.mean() - rest.mean()) / df["save_pct"].std()

print("=== B2B STATISTICAL SIGNIFICANCE ===")
print(f"B2B n={len(b2b)}, mean={b2b.mean():.4f}")
print(f"Rested n={len(rest)}, mean={rest.mean():.4f}")
print(f"Difference: {b2b.mean()-rest.mean():+.4f}")
print(f"t={t:.3f}, p={p:.4f} ({sig})")
print(f"Cohen's d: {effect_d:.4f}")

# Recovery curve (days 1-10, meaningful n)
print("\n=== RECOVERY CURVE (days 1-10) ===")
rc = df[df["days_rest"] <= 10].groupby("days_rest")["save_pct"].agg(["mean","count"]).round(4)
for idx, row in rc.iterrows():
    bar = "#" * int(row["mean"] * 100 - 87)
    print(f"  {int(idx):2d}d rest: {row['mean']:.4f} (n={int(row['count']):4d}) {bar}")

# Top goalies by sample size
print("\n=== TOP 15 GOALIES BY GAMES (3-season) ===")
top = df.groupby(["player_id","player_name"])["game_id"].count().reset_index()
top = top.rename(columns={"game_id":"games"}).sort_values("games", ascending=False)
for _, r in top.head(15).iterrows():
    sv = df[df["player_id"]==r["player_id"]]["save_pct"].mean()
    print(f"  {r['player_name']:<24} {int(r['games']):3d} games  avg SV%={sv:.4f}")

# B2B leaders
print("\n=== MOST B2B STARTS (3-season) ===")
b2b_counts = df[df["is_back_to_back"]==1].groupby("player_name")["game_id"].count().sort_values(ascending=False)
for name, n in b2b_counts.head(10).items():
    b2b_sv = df[(df["is_back_to_back"]==1) & (df["player_name"]==name)]["save_pct"].mean()
    rest_sv = df[(df["is_back_to_back"]==0) & (df["player_name"]==name)]["save_pct"].mean()
    print(f"  {name:<24} {n:2d} B2B  sv%={b2b_sv:.4f}  rested={rest_sv:.4f}  delta={b2b_sv-rest_sv:+.4f}")

conn.close()
