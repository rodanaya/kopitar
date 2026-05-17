# Kopitar — NHL Goaltender Fatigue Analysis

> *Named after Anze Kopitar, one of the most durable two-way players in modern NHL history.*

**Live dashboard → [kopitar.vercel.app](https://kopitar.vercel.app)**

---

## What we set out to answer

The conventional wisdom in hockey is simple: back-to-back games hurt goaltenders. But the data tells a more complicated story.

When you look at raw B2B save percentages versus rested save percentages, the effect nearly disappears. Not because fatigue doesn't exist — but because **coaches already know it does**. Starters get protected on the second night of a back-to-back. What looks like "no B2B effect" is actually evidence of selection bias built directly into the data.

The real signal only appears when you remove that protective layer and look at situations where coaches *have* to play their starter anyway: four games in six nights, three in four, extended road trips into altitude changes. That's where fatigue stops being a coaching decision and becomes a physiological fact.

This project attempts to quantify that fact with ten seasons of NHL goaltender data — 28,000+ game logs, 130+ qualified goalies, 33 teams.

---

## Key Findings

### 1. The B2B Paradox
League-wide B2B save percentage shows almost no drop vs. rested (.8992 vs .9000). This is not evidence that back-to-backs don't matter — it's evidence that coaches intervene before the data can capture the true effect. Backup goalies absorb the second-night starts precisely to prevent the performance drop from showing up in the starter's stats.

### 2. The 4-in-6 Threshold
When you condition on four games in six nights — a schedule density that forces starter usage regardless of fatigue — the effect becomes statistically significant (p = 0.035, delta = −0.0069 save percentage points). Translated to real outcomes: **0.20 extra goals allowed per start**, or roughly 1–2 additional goals surrendered per team per season from this schedule pattern alone.

### 3. Recovery Curves
Save percentage recovers non-linearly. Performance with one day of rest (B2B) sits at the baseline. With two days it rebounds sharply. The curve flattens after four days — meaning beyond that point, additional rest produces diminishing returns. Coaches who hold starters for three or four days of rest between starts are operating near the optimal window.

### 4. Goalie Resilience Archetypes
Not all goalies respond to schedule stress the same way. We classify every goalie with ≥5 back-to-back starts into four quadrants based on skill (avg save %) and fatigue resilience (B2B delta):

| Quadrant | Definition |
|---|---|
| **Iron Man** | Elite save % + maintains or improves on B2Bs |
| **Vulnerable Star** | Elite save % + significant B2B drop |
| **Workhorse** | Average save % + fatigue-resistant |
| **High Risk** | Average save % + B2B degradation |

The population splits roughly evenly (~23 / 21 / 20 / 22 across 86 qualified goalies), which suggests these are real archetypes rather than noise.

### 5. Overtime Adds a Hidden Layer
Goaltenders post *higher* save percentages in overtime (.9059 vs .8982 non-OT, p < 0.001) — a selection effect, since only close games reach OT. But playing into OT does not meaningfully change the *following* game's performance, and an OT game followed by a back-to-back shows no additional compound stress versus a regular B2B. The overtime effect is real but isolated.

---

## Team Analysis

### Most Traveled Teams (avg miles per game, 2015–2025)

| Rank | Team | Avg Miles/Game | Total Miles |
|---|---|---|---|
| 1 | SEA Kraken | 783 mi | 276,000 |
| 2 | VAN Canucks | 758 mi | 616,000 |
| 3 | ANA Ducks | 752 mi | 649,000 |
| 4 | UTA Hockey Club | 744 mi | 65,000 |
| 5 | EDM Oilers | 743 mi | 626,000 |
| 6 | SJS Sharks | 728 mi | 614,000 |
| 7 | CGY Flames | 720 mi | 597,000 |
| 8 | VGK Golden Knights | 695 mi | 450,000 |

Western Conference teams dominate — the geography of the Pacific and Central divisions means their goalies log far more air miles than Eastern counterparts, regardless of schedule density.

### Most Back-to-Back Games (by rate)

| Rank | Team | B2B Games | B2B Rate |
|---|---|---|---|
| 1 | CBJ Blue Jackets | 55 | 6.5% |
| 2 | NJD Devils | 51 | 6.0% |
| 3 | PHI Flyers | 48 | 5.6% |
| 4 | FLA Panthers | 42 | 5.0% |
| 5 | NYR Rangers | 41 | 4.9% |

Columbus leads the league in B2B rate — they face back-to-back situations in 6.5% of all goalie starts, nearly double the rate of the most schedule-protected Western teams.

### Teams That Suffer Most from B2Bs (SV% delta)

| Rank | Team | B2B SV% | Rested SV% | Delta |
|---|---|---|---|---|
| 1 | WSH Capitals | .862 | .902 | **−40.1 pts** |
| 2 | ARI Coyotes | .872 | .899 | −27.6 pts |
| 3 | EDM Oilers | .879 | .896 | −17.2 pts |
| 4 | PHI Flyers | .873 | .888 | −15.3 pts |
| 5 | CBJ Blue Jackets | .885 | .899 | −13.2 pts |

Washington's −40 point swing is the largest in the dataset — a combination of goalie instability during the study window and particularly punishing schedule sequences.

### Most Resilient Teams on Back-to-Backs

| Rank | Team | B2B SV% | Rested SV% | Delta |
|---|---|---|---|---|
| 1 | COL Avalanche | .920 | .900 | **+20.2 pts** |
| 2 | NYI Islanders | .927 | .908 | +19.8 pts |
| 3 | WPG Jets | .925 | .907 | +18.7 pts |
| 4 | VGK Golden Knights | .922 | .904 | +17.3 pts |
| 5 | TOR Maple Leafs | .918 | .901 | +16.9 pts |

Colorado and the Islanders actually post *better* numbers on B2Bs than on rested nights — a combination of starter quality in peak years, smart backup deployment, and favorable B2B opponent matchups.

---

## Data & Methods

**Dataset**: NHL Stats API, 10 regular seasons (2015–16 through 2024–25)  
**Scope**: 28,069 goaltender game logs · 131 goalies (≥30 RS games) · 33 teams  
**Travel**: Great-circle distances between arena coordinates; eastward travel penalized 1.5× for timezone asymmetry  
**Statistics**: Welch's t-tests for all comparisons; effect sizes translated to goals-per-start using avg shots faced (31.5/game)  
**Quality**: GSAx supplemented from MoneyPuck for career-level goalie quality adjustment

---

## Stack

| Layer | Technology |
|---|---|
| Data pipeline | Python · Pandas · SQLite |
| Statistics | SciPy · StatsModels · NumPy |
| API sources | NHL Stats API (public) · MoneyPuck |
| Dashboard | React · Recharts · Leaflet |
| Deployment | Vercel |

---

## Project Structure

```
kopitar/
├── scripts/
│   ├── export_dashboard_data.py      # builds all dashboard JSON from DB
│   ├── enrich_ot_score_metro.py      # adds OT/score/metro columns to DB
│   └── fetch_skater_gamelogs.py      # collects per-game skater TOI
├── kopitar/
│   └── dashboard-ui/
│       ├── src/pages/
│       │   ├── Overview.tsx          # hero narrative + league-level findings
│       │   ├── Goalies.tsx           # resilience quadrant lab
│       │   ├── Research.tsx          # statistical deep-dive + effect sizes
│       │   ├── Fatigue.tsx           # schedule stress + OT analysis
│       │   └── Players.tsx           # skater TOI fatigue + leaderboard
│       └── public/data/              # pre-exported JSON served statically
└── data/
    └── scraped/kopitar.db            # SQLite — all game logs + enrichments
```

---

*Concept / research project. All data sourced from publicly available NHL statistics.*
