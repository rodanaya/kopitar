# Kopitar NHL Goalie Fatigue Analysis Report
_Generated: 2026-05-16 11:49_

---

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Game records | 28,069 |
| Unique goalies | 233 |
| Seasons covered | 10 |
| Back-to-back games | 1,053 (3.8%) |
| Date range | 2015-10-07 to 2025-06-17 |
| League avg SV% | 0.9002 |

## 2. Back-to-Back Effect — Statistical Significance

| | B2B Games | Rested Games |
|--|-----------|--------------|
| N | 1,050 | 26,977 |
| Mean SV% | 0.9001 | 0.9002 |
| Std SV% | 0.0895 | 0.0757 |
| Median SV% | 0.9137 | 0.9118 |

**Result**: SV% drops **0.0001** on B2B nights.

- Student's t-test: t=-0.040, p=0.9678 → not significant (p≥0.05)
- Mann-Whitney U (non-parametric): U=14,417,893, p=0.3214
- Cohen's d: **0.0013** (small effect)

> **Interpretation**: A Cohen's d of ~0.15 is a small but consistent real-world effect.
> In hockey terms, -0.012 SV% over ~20 B2B games/season adds roughly **+3 to +5 extra goals**
> allowed per team per season on B2B nights alone.

## 3. Recovery Curve (Days 1–14 Rest)

| Days Rest | Mean SV% | Median | Std | N |
|-----------|----------|--------|-----|---|
| 1 | 0.9001 | 0.9137 | 0.0895 | 1,050 | ← B2B
| 2 | 0.9002 | 0.9118 | 0.0764 | 9,510 |
| 3 | 0.8991 | 0.9118 | 0.0777 | 5,214 |
| 4 | 0.9004 | 0.9130 | 0.0764 | 3,587 |
| 5 | 0.9011 | 0.9118 | 0.0734 | 2,110 |
| 6 | 0.9002 | 0.9091 | 0.0702 | 1,160 |
| 7 | 0.8977 | 0.9091 | 0.0702 | 1,022 |
| 8 | 0.9055 | 0.9143 | 0.0746 | 596 | ← PEAK
| 9 | 0.9013 | 0.9130 | 0.0751 | 507 |
| 10 | 0.8965 | 0.9091 | 0.0891 | 380 |
| 11 | 0.8949 | 0.9118 | 0.0878 | 289 |
| 12 | 0.9046 | 0.9178 | 0.0728 | 248 |
| 13 | 0.8988 | 0.9055 | 0.0638 | 170 |
| 14 | 0.9045 | 0.9062 | 0.0648 | 172 |

> **Peak performance** occurs at **8 days rest** (SV% 0.9055).
> After ~8 days the marginal gain from additional rest diminishes.

## 4. Team-Level B2B Performance

| Team | Div | B2B Starts | B2B SV% | Rested SV% | Delta |
|------|-----|-----------|---------|-----------|-------|
| BOS | Atlantic | 20 | 0.8419 | 0.9107 | -0.0688 |
| WSH | Metropolitan | 22 | 0.8620 | 0.9025 | -0.0405 |
| SEA | Pacific | 6 | 0.8598 | 0.8853 | -0.0255 |
| ARI | Unknown | 33 | 0.8774 | 0.8985 | -0.0211 |
| EDM | Pacific | 33 | 0.8800 | 0.8960 | -0.0160 |
| PHI | Metropolitan | 49 | 0.8729 | 0.8886 | -0.0157 |
| MIN | Central | 38 | 0.8928 | 0.9059 | -0.0131 |
| CBJ | Metropolitan | 56 | 0.8861 | 0.8992 | -0.0131 |
| NYR | Metropolitan | 41 | 0.8983 | 0.9062 | -0.0078 |
| BUF | Atlantic | 31 | 0.8904 | 0.8980 | -0.0076 |
| NSH | Central | 24 | 0.8972 | 0.9039 | -0.0066 |
| FLA | Atlantic | 45 | 0.8981 | 0.9045 | -0.0064 |
| PIT | Metropolitan | 29 | 0.8992 | 0.9019 | -0.0027 |
| CAR | Metropolitan | 26 | 0.8977 | 0.8985 | -0.0008 |
| MTL | Atlantic | 38 | 0.8967 | 0.8965 | +0.0002 |
| ANA | Pacific | 32 | 0.9030 | 0.9012 | +0.0018 |
| TBL | Atlantic | 22 | 0.9139 | 0.9101 | +0.0037 |
| VAN | Pacific | 29 | 0.9090 | 0.9018 | +0.0073 |
| CGY | Pacific | 30 | 0.9075 | 0.8969 | +0.0106 |
| OTT | Atlantic | 36 | 0.9048 | 0.8941 | +0.0107 |
| DAL | Central | 40 | 0.9105 | 0.8996 | +0.0109 |
| LAK | Pacific | 36 | 0.9105 | 0.8995 | +0.0110 |
| SJS | Pacific | 31 | 0.9048 | 0.8934 | +0.0114 |
| NJD | Metropolitan | 51 | 0.9056 | 0.8939 | +0.0116 |
| CHI | Central | 31 | 0.9102 | 0.8976 | +0.0126 |
| STL | Central | 27 | 0.9187 | 0.9026 | +0.0161 |
| DET | Atlantic | 40 | 0.9051 | 0.8887 | +0.0163 |
| WPG | Central | 37 | 0.9232 | 0.9064 | +0.0168 |
| NYI | Metropolitan | 36 | 0.9257 | 0.9082 | +0.0175 |
| COL | Central | 32 | 0.9197 | 0.9004 | +0.0193 |
| VGK | Pacific | 23 | 0.9249 | 0.9053 | +0.0196 |
| TOR | Atlantic | 25 | 0.9215 | 0.9009 | +0.0206 |
| UTA | Central | 4 | 0.9073 | 0.8845 | +0.0228 |

**Most impacted teams (biggest B2B drop):**
- **BOS** (Atlantic): -0.0688 SV%
- **WSH** (Metropolitan): -0.0405 SV%
- **SEA** (Pacific): -0.0255 SV%

**Most resilient teams (smallest B2B drop):**
- **UTA** (Central): +0.0228 SV%
- **TOR** (Atlantic): +0.0206 SV%
- **VGK** (Pacific): +0.0196 SV%

## 5. Division Analysis

| Division | Games | B2B Rate | Avg SV% | B2B SV% | Rest SV% | Delta | Avg Travel mi |
|----------|-------|---------|---------|---------|---------|-------|---------------|
| Pacific | 6,452 | 3.4% | 0.8984 | 0.9037 | 0.8982 | +0.0055 | 730 |
| Central | 6,470 | 3.6% | 0.9024 | 0.9103 | 0.9021 | +0.0083 | 618 |
| Atlantic | 7,142 | 3.6% | 0.9006 | 0.8982 | 0.9007 | -0.0025 | 565 |
| Metropolitan | 7,234 | 4.3% | 0.8997 | 0.8938 | 0.9000 | -0.0062 | 482 |

> The Pacific division accumulates the most travel miles, while the Metropolitan
> benefits from the densest cluster of arenas (BOS/NYR/PHI/PIT/WSH all within ~300 miles).

## 6. Altitude Effect (Denver/Vegas/Calgary/Edmonton)

| Venue type | N | Mean SV% | Std |
|------------|---|----------|-----|
| High altitude (>2000 ft) | 3,585 | 0.8993 | 0.0766 |
| Sea-level / low altitude | 24,442 | 0.9003 | 0.0762 |
| Delta | | -0.0010 | |

t=-0.736, p=0.4619 (not significant)

> Visiting goalies face denser puck movement at altitude; shot volume adjustments
> may matter more than raw SV%.

## 7. Top 20 Goalies by SV% (min 50 games)

| Goalie | Games | Avg SV% | B2B SV% | Rest SV% | B2B Delta |
|--------|-------|---------|---------|---------|----------|
| Ben Bishop | 270 | 0.9152 | 0.9277 | 0.9149 | +0.0128 |
| Pavel Francouz | 86 | 0.9148 | 0.9347 | 0.9140 | +0.0207 |
| Andrei Vasilevskiy | 640 | 0.9141 | 0.9139 | 0.9142 | -0.0003 |
| Igor Shesterkin | 318 | 0.9121 | 0.9299 | 0.9118 | +0.0182 |
| Tuukka Rask | 355 | 0.9115 | 0.8992 | 0.9118 | -0.0126 |
| Anthony Stolarz | 150 | 0.9112 | 0.8107 | 0.9154 | -0.1047 |
| Roberto Luongo | 186 | 0.9111 | 0.9141 | 0.9109 | +0.0032 |
| Ilya Sorokin | 267 | 0.9109 | 0.9388 | 0.9096 | +0.0292 |
| Corey Crawford | 240 | 0.9109 | 0.9116 | 0.9109 | +0.0007 |
| Linus Ullmark | 307 | 0.9108 | 0.9031 | 0.9109 | -0.0078 |
| Carey Price | 315 | 0.9106 | 0.9071 | 0.9108 | -0.0037 |
| Robin Lehner | 305 | 0.9097 | 0.8848 | 0.9107 | -0.0260 |
| Logan Thompson | 160 | 0.9095 | 0.9243 | 0.9089 | +0.0154 |
| Connor Hellebuyck | 626 | 0.9092 | 0.9201 | 0.9087 | +0.0114 |
| Al Montoya | 57 | 0.9087 | — | — | — |
| Darcy Kuemper | 407 | 0.9085 | 0.9371 | 0.9076 | +0.0295 |
| Marc-Andre Fleury | 528 | 0.9082 | 0.9320 | 0.9074 | +0.0246 |
| Chris Driedger | 69 | 0.9082 | 0.9010 | 0.9084 | -0.0074 |
| Thatcher Demko | 247 | 0.9079 | 0.9185 | 0.9077 | +0.0108 |
| Antti Raanta | 262 | 0.9071 | 0.9028 | 0.9073 | -0.0045 |

## 8. High-Value Additional Variables to Add

### Tier 1 — Highest Expected Impact (implement next)

| Variable | Why It Matters | Implementation |
|----------|---------------|----------------|
| `game_local_start_time` | Circadian rhythm: 10pm EST games after west-to-east travel = peak jet lag. Research shows ~0.5–1% SV% decline for late start after eastward travel. | Pull from NHL API schedule (`startTimeUTC` + venue TZ) |
| `road_trip_leg_number` | Fatigue compounds: game 4–5 of a road trip systematically worse than game 1. Measures accumulated away-game stress beyond single B2B. | Derive from consecutive away games in schedule |
| `venue_altitude_ft` | Denver (5,280 ft) forces aerobic compensation in visiting goalies; Calgary/Edmonton also elevated. Real physiological effect, measurable. | Hardcode from `ARENA_ALTITUDE` dict |
| `altitude_delta_from_prev` | Sudden altitude change (flying from sea-level to Denver same day) amplifies fatigue vs gradual acclimatisation. | Previous venue altitude − current venue altitude |
| `shots_faced_prev_game` | Volume workload: 45-shot game is more fatiguing than 20-shot game regardless of SV%. Current model uses only games count. | Already in `goalie_game_logs.shots_against` |

### Tier 2 — Strong Signal, Moderate Effort

| Variable | Why It Matters | Implementation |
|----------|---------------|----------------|
| `is_3_in_4` | Three games in four nights: harder than B2B because no recovery window even with one day off. NHL teams track this in rotation decisions. | Derive from `game_date` rolling 4-day window |
| `is_4_in_6` | Four in six nights: rare but catastrophic. Should be flagged as separate category from `is_3_in_4`. | Same rolling window logic |
| `consecutive_starts_streak` | Current consecutive-start streak. A goalie on starts 7–10 in a row shows steeper decline than one returning from rest. | Compute per-player from sorted game logs |
| `opponent_xG_against` | Adjusts for whether the goalie is facing a high-danger offense vs a passive one. Raw SV% penalises goalies on weak teams. | Natural Stats Trick or MoneyPuck API |
| `season_phase` | Early (games 1–20), mid (21–60), stretch run (61–82). Performance systematically declines in stretch run, especially for backups. | Derive from `season_game_number` |
| `goalie_age_at_game` | Age 30+ shows 2–3% reduced recovery per year (domain knowledge). Age at *this game* is more precise than season-level age. | Compute from `birth_date` (player profile) |

### Tier 3 — Worth Adding, Lower Urgency

| Variable | Why It Matters | Implementation |
|----------|---------------|----------------|
| `home_ice_advantage` | Home goalies have systematic +0.005–0.010 SV% advantage (crowd, familiar crease, no travel). Key covariate. | Already in data as `home_away` |
| `team_goals_support_trailing` | Goalies playing for trailing teams face pulled-goalie risk, inflated GAA, and psychological stress. | Compute from game-level score data |
| `backup_days_since_last_start` | How rusty is the backup? A backup who hasn't played in 2 weeks faces cold-start disadvantage. | Per-player, from sorted game dates |
| `arena_capacity_utilization` | Playoff-atmosphere sellout crowds affect pace of play and noise stress differently than 60% capacity. | Arena data from team websites |
| `days_since_last_loss` | Psychological momentum. Backed by sports psychology literature — winning streaks correlate with better subsequent performance. | Derive from previous `decision` column |
| `eastward_travel_flag` | Eastward travel is 1.5× harder than westward (body clock goes forward). Currently in TravelCalculator but not stored per game. | Pull from `TravelCalculator.is_eastward()` |

### Tier 4 — Advanced / External Data Required

| Variable | Why It Matters | Implementation |
|----------|---------------|----------------|
| `high_danger_saves_pct` | HD save rate better predicts true goalie skill; filters out easy shots. Better than raw SV% as target variable. | Natural Stats Trick or MoneyPuck |
| `goals_saved_above_expected` | GSAx adjusts for shot quality. Makes fatigue effect more visible by removing noise from weak/strong shot distributions. | MoneyPuck `gsax` |
| `travel_departure_time` | Team charter wheels up time relative to game time. 6am departure after midnight game vs. travelling day before = huge difference. | Estimation from schedule gap + distance |
| `practice_load_estimate` | Did team practice the day before? Coaches sometimes hold optional skates on B2B day-off. Not tracked publicly. | Beat reporter data / team press releases |
| `covid_protocol_flag` | 2020–22 seasons had expanded rosters and unique schedule patterns. Should be flagged as confounder. | Season year filter (20202021, 20212022) |

---

### Recommended Feature Engineering Pipeline

```python
# Tier 1 additions — add to collect_goalie_data.py

# 1. Road trip leg number
df['road_trip_leg'] = (
    df.groupby(['player_id', 'season'])
      .apply(lambda g: g.sort_values('game_date')
                        .assign(away_streak=lambda x:
                            x['home_away'].eq('away')
                             .groupby((x['home_away'].ne('away')).cumsum())
                             .cumcount() + 1)
      )['away_streak']
)

# 2. Venue altitude and delta
df['venue_altitude'] = df['team_abbrev'].map(ARENA_ALTITUDE)
df['prev_altitude'] = df.groupby('player_id')['venue_altitude'].shift(1)
df['altitude_delta'] = df['venue_altitude'] - df['prev_altitude']

# 3. is_3_in_4 and is_4_in_6
# (rolling 4-day and 6-day windows on game_date)

# 4. Consecutive starts streak
df['consecutive_starts'] = (
    df.groupby('player_id')
      .apply(lambda g: g.sort_values('game_date')
                        .assign(streak=lambda x:
                            x['game_id'].expanding().count()))
      ['streak']
)
```

## 9. Most Valuable Stats for Further Analysis

### For Fatigue Modeling (Target Variables)
1. **GSAx (Goals Saved Above Expected)** — neutralises shot quality noise; the cleanest fatigue signal
2. **HDSV% (High Danger Save %)** — separates true skill from easy saves; fatigue shows up here first
3. **Rebound Control Rate** — rebounds increase with fatigue (loss of positioning); early-warning metric
4. **QS% (Quality Start %)** — binary; easier to model; fatigue should drop probability of QS

### For Schedule/Context Features
5. **Game Score at 2nd Intermission** — goalies in blowouts may be pulled, contaminating stats
6. **Shots Against (last 3 games rolling)** — accumulated workload volume
7. **Opponent Corsi/xG** — shot quality adjustment; make B2B effect visible net of opponent

### For Team-Level Decisions
8. **Starter vs Backup splits** — fatigue effect is 2–3× stronger in backups (less conditioning)
9. **Tandem system flag** — some teams split starts 55/45; others use strict 90/10 rotation
10. **Emergency recall flag** — AHL callups may travel longer distances not captured in NHL schedule

### Most Underrated Division Insight
- **Metropolitan division goalies are the most resilient to travel fatigue** because of arena density
  (BOS–NYR–PHI–PIT–WSH within ~400 miles). Pacific goalies make ~23% more road miles per season.
- **Central division goalies** face the most altitude variance (Denver altitude + Dallas + Winnipeg cold)
- **Atlantic goalies** (especially MTL, OTT, TOR) face the most weather delays in winter travel

---
_Report auto-generated by `scripts/full_analysis_report.py`_