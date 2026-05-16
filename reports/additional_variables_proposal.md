# Additional Variables Proposal — Goalie Fatigue Model

_Deep analysis of what data would most improve predictive power_

---

## Executive Summary

The current model captures **when** a goalie is tired (B2B, days rest, travel miles, games in 7/14 days).
What it **cannot yet see** is:

1. **How tired** from a specific game (volume + quality of work)
2. **Circadian disruption** (jet lag direction + game start time)
3. **Accumulated road trip fatigue** beyond single B2B
4. **Altitude stress** for visiting teams in Denver/Vegas/Calgary
5. **Age-adjusted recovery** per individual game

These five factors are estimated to explain an additional **25–40%** of residual SV% variance
left after the base fatigue model.

---

## Tier 1 — Implement Now (High Impact, Low Effort)

### 1. `road_trip_leg` — Road Trip Game Number
**What**: Ordinal counter of how many consecutive away games the goalie has played (resets on home game).
**Why**: Single B2B treats game 2-of-2 the same as game 5-of-5. Empirical data from other sports
shows cumulative fatigue is non-linear — the 4th road game in 6 days is not the same as the 2nd.

| Road trip leg | Expected SV% vs rested |
|---|---|
| 1 (first road game) | −0.002 |
| 2 | −0.006 |
| 3 | −0.010 |
| 4+ | −0.015 to −0.020 |

**Implementation**: Derive from sorted game dates per player per season. ~30 lines of pandas.

---

### 2. `venue_altitude_ft` + `altitude_delta`
**What**: Absolute altitude of the arena (ft above sea level) and delta from previous game.
**Why**: Denver at 5,280 ft forces ~15% more oxygen consumption per skating stride.
Visiting goalies face faster puck movement and their own aerobic fatigue.
The *change* matters more than the absolute — flying sea-level → Denver same day is severe.

| Arena | Altitude |
|---|---|
| Pepsi Center (COL) | 5,280 ft |
| Delta Center (UTA) | 4,226 ft |
| T-Mobile Arena (VGK) | 2,001 ft |
| Scotiabank Saddledome (CGY) | 3,438 ft |
| Rogers Place (EDM) | 2,200 ft |
| All others | < 1,000 ft |

**Implementation**: `ARENA_ALTITUDE` dict already drafted in `enrich_variables.py`.

---

### 3. `is_3_in_4` / `is_4_in_6`
**What**: Boolean flags for three games in four nights or four games in six nights.
**Why**: NHL team doctors track these explicitly in rotation decisions. Three-in-four means
no two-day recovery exists even with a day off. Four-in-six is the threshold for mandatory backup use
on most tandem-rotation teams.

**Expected effect**: `is_3_in_4` → −0.008 to −0.012 SV%; `is_4_in_6` → −0.015 SV%

**Implementation**: Rolling 4-day and 6-day game count windows per player.

---

### 4. `eastward_travel_flag`
**What**: Binary flag — did this game require eastward travel from the previous game location?
**Why**: The body clock adapts faster to westward travel (phase delay = natural sleep tendency).
Eastward travel (phase advance) causes the classic "jet lag" — can't fall asleep early enough.
Research shows eastward travel causes ~0.5–1.5× more fatigue per time zone vs westward.
Already coded in `TravelCalculator.is_eastward()` but not stored per game.

---

### 5. `shots_prev_game`
**What**: Shots against the goalie faced in their previous appearance.
**Why**: Days rest tells you *when* the goalie last played; shots tells you *how hard* they worked.
A goalie who faced 47 shots and made 44 saves is more fatigued entering a B2B than one who
faced 19 shots in a 6-2 blowout. This single variable upgrades the workload signal substantially.

---

## Tier 2 — Quarter Two Priority (Strong Signal, Moderate Effort)

### 6. `game_local_start_time`
**Why it's important**: Circadian research shows performance peaks at ~6pm local body-clock time
and drops ~8% by midnight. For east-coast goalies playing a 10pm EST game in Anaheim after flying west,
body clock thinks it's 1am. This is measurable and controllable.

**Data source**: NHL API `schedule` endpoint has `startTimeUTC` for every game.
Combine with venue timezone to get local start time.

**Expected effect on model**: May explain 5–10% of residual B2B variance.

---

### 7. `consecutive_starts_streak`
**Why**: Being on starts 7–10 in a row is qualitatively different from starts 1–3.
Muscular fatigue accumulates in ways not captured by days-between-starts alone.
Also captures tandem vs starter systems — starters have longer streaks.

---

### 8. `season_phase`
**Why**: NHL goalies in their 70th+ game show systematic SV% decline vs games 1–20.
This is partly accumulated fatigue, partly score effects (playoff races = more pressure),
partly opponent adjustment to their tendencies.

| Phase | Games | Avg SV% (estimated) |
|---|---|---|
| Early (1–20) | 20 | +0.003 vs mean |
| Mid (21–60) | 40 | baseline |
| Stretch (61–82) | 22 | −0.005 vs mean |
| Playoffs | varies | +0.010 (higher stakes, more rest) |

---

### 9. `opponent_xG_for`
**Why**: The hardest part of SV% as a fatigue target variable is that a goalie facing
Edmonton's first line vs Florida's is a different job. Expected Goals Against adjusts for
shot quality — it tells us what an average goalie would have allowed, making the fatigue
signal cleaner.

**Data source**: MoneyPuck (moneypuck.com) publishes game-level xG data via CSV download.

---

## Tier 3 — Later (Valuable, External Data Required)

| Variable | Signal Strength | Data Source |
|---|---|---|
| `gsax_prev_game` | High — quality-adjusted workload | MoneyPuck |
| `hdsv_pct` | High — fatigue shows in HD saves first | Natural Stats Trick |
| `home_ice` | Medium — already partially captured | Already in data |
| `age_at_game` | Medium — need precise DOB per goalie | NHL player API |
| `days_since_last_loss` | Low–Medium | Compute from `decision` column |
| `rebound_rate` | High but hard — not in standard logs | Play-by-play data |
| `team_goal_support` | Medium — psychological pressure | Game scores |

---

## Model Impact Projection

If we add **Tier 1 + Tier 2 variables** (all derivable from existing data sources):

| Model version | Features | Expected R² | MAE (SV%) |
|---|---|---|---|
| Current (base) | B2B, days_rest, travel_miles, games_7d/14d | ~0.04 | ~0.022 |
| + Tier 1 additions | + altitude, road_trip_leg, is_3_in_4, eastward, shots_prev | ~0.07 | ~0.019 |
| + Tier 2 additions | + start_time, streak, phase, opponent_xG | ~0.12 | ~0.017 |
| + Tier 3 (xG/HD) | + GSAx, HDSV%, rebound | ~0.18 | ~0.014 |

> Note: SV% is notoriously high-variance (σ ≈ 0.025). An R² of 0.18 is strong for this target.
> The real value is in relative rankings (who is most fatigued tonight) not absolute predictions.

---

## Which Teams/Divisions Are Most Valuable to Study

### Highest research value:
1. **Pacific division teams** (LAK, VAN, SEA, ANA, VGK, SJS, CGY, EDM): Most travel miles,
   3 time zones from eastern opponents, altitude variance. Biggest opportunity for fatigue optimization.
2. **Colorado Avalanche**: Only team that plays at genuine altitude. Opponents face a unique stressor.
3. **Toronto Maple Leafs + Montreal Canadiens**: Most scrutinized in media; most public data available.
   Both have history of tandem systems with measurable B2B decisions.

### Most analytically interesting stats by team:
- **COL**: Do visiting goalies systematically underperform SV% expectations at altitude?
- **WPG**: Travel disadvantage — furthest from most opponents in the west
- **FLA/TBL**: Back-to-back performance on Florida road trips (two cities, one trip, different distances)
- **Metropolitan teams**: Control group — low travel, predictable schedule

---

_Proposal generated May 2026 | `reports/additional_variables_proposal.md`_
