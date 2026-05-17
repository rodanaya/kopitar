"""
Add four new columns to goalie_game_logs (no API calls needed):

  ot_flag       — 1 if the game went to overtime/shootout
  score_diff    — goalie's team margin (positive = win, negative = loss)
  same_metro    — 1 if the road trip is a same-metro bus trip (LAK-ANA, NY trio)
  prev_game_ot  — 1 if the PREVIOUS start was an OT game (compound stress flag)

OT detection: game went OT if any goalie in that game has decision='O'
              OR any goalie played > 60.5 minutes.
Score diff:   home_score = sum(away_goalie GA), away_score = sum(home_goalie GA)
              Works even when teams use multiple goalies in a game.
"""

import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path

DB_PATH = Path("D:/Python/Kopitar/data/scraped/kopitar.db")

# Same-metro pairs: teams within ~50 miles of each other (bus trips, no real travel fatigue)
SAME_METRO = {
    frozenset({"LAK", "ANA"}),  # Los Angeles / Anaheim — ~30 miles
    frozenset({"NYR", "NJD"}),  # Manhattan / Newark — ~15 miles
    frozenset({"NYR", "NYI"}),  # Manhattan / Elmont — ~25 miles
    frozenset({"NJD", "NYI"}),  # Newark / Elmont — ~35 miles
}


def main():
    conn = sqlite3.connect(DB_PATH)
    print("Loading goalie_game_logs...")
    df = pd.read_sql("""
        SELECT player_id, game_id, game_date, team, opponent,
               home_away, toi_minutes, decision, goals_against
        FROM goalie_game_logs
    """, conn, parse_dates=["game_date"])
    print(f"  {len(df):,} rows loaded")

    # ── Add columns if missing ────────────────────────────────────────────────
    cur = conn.cursor()
    existing = {r[1] for r in cur.execute("PRAGMA table_info(goalie_game_logs)")}
    for col, dtype in [
        ("ot_flag",      "INTEGER"),
        ("score_diff",   "INTEGER"),
        ("same_metro",   "INTEGER"),
        ("prev_game_ot", "INTEGER"),
    ]:
        if col not in existing:
            cur.execute(f"ALTER TABLE goalie_game_logs ADD COLUMN {col} {dtype} DEFAULT 0")
            print(f"  Added column: {col}")
    conn.commit()

    # ── OT flag ───────────────────────────────────────────────────────────────
    ot_games = set(
        df[
            (df["decision"] == "O") | (df["toi_minutes"].fillna(0) > 60.5)
        ]["game_id"].unique()
    )
    df["ot_flag"] = df["game_id"].isin(ot_games).astype(int)
    print(f"  OT/SO games: {len(ot_games):,}  ({df['ot_flag'].mean()*100:.1f}% of all starts)")

    # ── Score diff ────────────────────────────────────────────────────────────
    # home_score = what home team scored = away goalies' total GA
    # away_score = what away team scored = home goalies' total GA
    game_scores = (
        df.groupby("game_id")
        .apply(lambda g: pd.Series({
            "home_score": g.loc[g["home_away"] == "away", "goals_against"].sum(),
            "away_score": g.loc[g["home_away"] == "home", "goals_against"].sum(),
        }))
        .reset_index()
    )
    df = df.merge(game_scores, on="game_id", how="left")
    df["score_diff"] = df.apply(
        lambda r: int(r["home_score"] - r["away_score"]) if r["home_away"] == "home"
                  else int(r["away_score"] - r["home_score"]) if r["home_away"] == "away"
                  else np.nan,
        axis=1,
    )
    valid = df["score_diff"].dropna()
    print(f"  Score diff range: {valid.min():.0f} to {valid.max():.0f}")
    print(f"  Blowouts (±4+): {(valid.abs() >= 4).sum():,} starts")

    # ── Same metro ────────────────────────────────────────────────────────────
    df["same_metro"] = df.apply(
        lambda r: 1 if frozenset({r["team"], r["opponent"]}) in SAME_METRO else 0, axis=1
    )
    print(f"  Same-metro trips: {df['same_metro'].sum():,} starts  "
          f"({df[df['same_metro']==1]['team'].value_counts().to_dict()})")

    # ── Prev game OT (compound stress: OT then next-day B2B) ─────────────────
    df = df.sort_values(["player_id", "game_date"])
    df["prev_game_ot"] = (
        df.groupby("player_id")["ot_flag"].shift(1).fillna(0).astype(int)
    )
    compound_stress = ((df["prev_game_ot"] == 1) & (df["toi_minutes"].notna())).sum()
    print(f"  Starts after an OT game: {compound_stress:,}")

    # ── Write back ────────────────────────────────────────────────────────────
    print("Writing to DB...")
    updates = df[["player_id", "game_id", "ot_flag", "score_diff", "same_metro", "prev_game_ot"]].copy()

    batch = []
    for _, row in updates.iterrows():
        sd = row["score_diff"]
        batch.append((
            int(row["ot_flag"]),
            int(sd) if pd.notna(sd) else None,
            int(row["same_metro"]),
            int(row["prev_game_ot"]),
            int(row["player_id"]),
            int(row["game_id"]),
        ))

    cur.executemany("""
        UPDATE goalie_game_logs
        SET ot_flag=?, score_diff=?, same_metro=?, prev_game_ot=?
        WHERE player_id=? AND game_id=?
    """, batch)
    conn.commit()
    conn.close()
    print(f"  Done. {len(batch):,} rows updated.")


if __name__ == "__main__":
    main()
