# Data Dictionary - Kopitar Project

## Table of Contents
1. [Core Entities](#core-entities)
2. [Performance Metrics](#performance-metrics)
3. [Fatigue Metrics](#fatigue-metrics)
4. [API Response Schemas](#api-response-schemas)
5. [Calculated Fields](#calculated-fields)
6. [Data Quality Rules](#data-quality-rules)

---

## Core Entities

### teams
**Description**: NHL team information including arena locations for travel calculations

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal team ID | 1 |
| nhl_id | INTEGER | UNIQUE, NOT NULL | Official NHL team ID | 10 |
| name | VARCHAR(100) | NOT NULL | Full team name | "Toronto Maple Leafs" |
| abbreviation | VARCHAR(3) | NOT NULL | Team abbreviation | "TOR" |
| arena_name | VARCHAR(200) | | Arena name | "Scotiabank Arena" |
| arena_lat | DECIMAL(10,8) | | Arena latitude | 43.6435 |
| arena_lon | DECIMAL(11,8) | | Arena longitude | -79.3791 |
| timezone | VARCHAR(50) | NOT NULL | Team timezone | "America/Toronto" |
| conference | VARCHAR(20) | | Conference name | "Eastern" |
| division | VARCHAR(20) | | Division name | "Atlantic" |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation time | 2024-01-15 10:30:00 |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update time | 2024-01-15 10:30:00 |

### players
**Description**: Player information with focus on goaltenders

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal player ID | 1 |
| nhl_id | INTEGER | UNIQUE, NOT NULL | Official NHL player ID | 8476899 |
| first_name | VARCHAR(100) | NOT NULL | Player first name | "Andrei" |
| last_name | VARCHAR(100) | NOT NULL | Player last name | "Vasilevskiy" |
| full_name | VARCHAR(200) | GENERATED | Full player name | "Andrei Vasilevskiy" |
| position | VARCHAR(2) | CHECK IN ('G','D','F') | Player position | "G" |
| jersey_number | INTEGER | | Current jersey number | 88 |
| birth_date | DATE | | Date of birth | 1994-07-25 |
| birth_country | VARCHAR(3) | | ISO country code | "RUS" |
| height_cm | INTEGER | | Height in centimeters | 191 |
| weight_kg | INTEGER | | Weight in kilograms | 102 |
| catches | VARCHAR(1) | CHECK IN ('L','R') | Catching hand (goalies) | "L" |
| current_team_id | INTEGER | FK teams(id) | Current team | 14 |
| is_active | BOOLEAN | DEFAULT TRUE | Active player flag | true |
| nhl_debut_date | DATE | | NHL debut date | 2014-12-20 |

### games
**Description**: NHL game information and metadata

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal game ID | 1 |
| nhl_id | INTEGER | UNIQUE, NOT NULL | Official NHL game ID | 2023020001 |
| season | VARCHAR(8) | NOT NULL | Season identifier | "20232024" |
| game_type | VARCHAR(2) | CHECK IN ('PR','R','P','A') | Game type code | "R" |
| date_time | TIMESTAMP WITH TIME ZONE | NOT NULL | Game start time (UTC) | 2024-01-15 00:00:00+00 |
| home_team_id | INTEGER | FK teams(id) | Home team | 10 |
| away_team_id | INTEGER | FK teams(id) | Away team | 14 |
| venue | VARCHAR(200) | | Game venue | "Scotiabank Arena" |
| game_state | VARCHAR(20) | | Current state | "Final" |
| home_score | INTEGER | | Home team score | 4 |
| away_score | INTEGER | | Away team score | 3 |
| overtime | BOOLEAN | DEFAULT FALSE | Went to overtime | false |
| shootout | BOOLEAN | DEFAULT FALSE | Went to shootout | false |
| attendance | INTEGER | | Game attendance | 18819 |

**Game Type Codes**:
- PR: Preseason
- R: Regular Season  
- P: Playoffs
- A: All-Star

### goalie_game_stats
**Description**: Individual goaltender performance statistics per game

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal record ID | 1 |
| game_id | INTEGER | FK games(id) | Game reference | 1001 |
| player_id | INTEGER | FK players(id) | Goalie reference | 25 |
| team_id | INTEGER | FK teams(id) | Team playing for | 10 |
| is_home | BOOLEAN | NOT NULL | Home/away indicator | true |
| is_starter | BOOLEAN | NOT NULL | Started the game | true |
| decision | VARCHAR(1) | CHECK IN ('W','L','O','N') | Game decision | "W" |
| time_on_ice | INTERVAL | | Total ice time | 60:00:00 |
| time_on_ice_seconds | INTEGER | GENERATED | TOI in seconds | 3600 |
| periods_played | INTEGER | | Number of periods | 3 |
| shots_against | INTEGER | NOT NULL | Total shots faced | 35 |
| saves | INTEGER | NOT NULL | Total saves made | 32 |
| goals_against | INTEGER | NOT NULL | Goals allowed | 3 |
| save_percentage | DECIMAL(5,3) | GENERATED | Save percentage | 0.914 |
| goals_against_average | DECIMAL(5,2) | GENERATED | GAA for game | 3.00 |
| shutout | BOOLEAN | DEFAULT FALSE | Shutout achieved | false |
| power_play_saves | INTEGER | | PP saves made | 8 |
| power_play_shots | INTEGER | | PP shots faced | 10 |
| even_strength_saves | INTEGER | | ES saves made | 22 |
| even_strength_shots | INTEGER | | ES shots faced | 23 |
| penalty_minutes | INTEGER | DEFAULT 0 | PIMs taken | 0 |
| assist_1 | BOOLEAN | DEFAULT FALSE | Primary assist | false |
| assist_2 | BOOLEAN | DEFAULT FALSE | Secondary assist | false |
| goals | INTEGER | DEFAULT 0 | Goals scored | 0 |
| pulled_time | INTERVAL | | Time pulled | 00:01:30 |

**Decision Codes**:
- W: Win
- L: Loss
- O: Overtime/Shootout Loss
- N: No Decision

---

## Performance Metrics

### goalie_advanced_stats
**Description**: Advanced analytics and derived metrics for goaltenders

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal record ID | 1 |
| player_id | INTEGER | FK players(id) | Goalie reference | 25 |
| game_id | INTEGER | FK games(id) | Game reference | 1001 |
| expected_goals_against | DECIMAL(5,2) | | xGA based on shot quality | 3.45 |
| goals_saved_above_expected | DECIMAL(5,2) | GENERATED | GSAx (saves - xGA) | -0.45 |
| high_danger_shots | INTEGER | | HD shots faced | 12 |
| high_danger_saves | INTEGER | | HD saves made | 10 |
| high_danger_save_pct | DECIMAL(5,3) | GENERATED | HD save percentage | 0.833 |
| medium_danger_shots | INTEGER | | MD shots faced | 15 |
| medium_danger_saves | INTEGER | | MD saves made | 14 |
| low_danger_shots | INTEGER | | LD shots faced | 8 |
| low_danger_saves | INTEGER | | LD saves made | 8 |
| rebound_attempts | INTEGER | | Rebounds allowed | 7 |
| rebound_goals | INTEGER | | Goals on rebounds | 1 |
| cross_crease_shots | INTEGER | | Cross-crease faced | 5 |
| cross_crease_saves | INTEGER | | Cross-crease saved | 3 |
| rush_attempts | INTEGER | | Rush shots faced | 6 |
| rush_saves | INTEGER | | Rush saves made | 5 |
| quality_start | BOOLEAN | GENERATED | QS (SV% > .917 or > avg) | true |
| really_bad_start | BOOLEAN | GENERATED | RBS (SV% < .850) | false |
| goals_saved_above_average | DECIMAL(5,2) | | GSAA calculation | 0.8 |

### goalie_season_stats
**Description**: Aggregated season statistics for goaltenders

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal record ID | 1 |
| player_id | INTEGER | FK players(id) | Goalie reference | 25 |
| season | VARCHAR(8) | NOT NULL | Season identifier | "20232024" |
| team_id | INTEGER | FK teams(id) | Primary team | 10 |
| games_played | INTEGER | | Total games | 58 |
| games_started | INTEGER | | Games as starter | 57 |
| wins | INTEGER | | Total wins | 35 |
| losses | INTEGER | | Total losses | 16 |
| ot_losses | INTEGER | | OT/SO losses | 7 |
| save_percentage | DECIMAL(5,3) | | Overall save % | 0.915 |
| goals_against_average | DECIMAL(5,2) | | Season GAA | 2.64 |
| shutouts | INTEGER | | Total shutouts | 4 |
| total_shots_faced | INTEGER | | Season shots | 1687 |
| total_saves | INTEGER | | Season saves | 1543 |
| total_minutes | INTEGER | | Total TOI minutes | 3245 |
| quality_starts | INTEGER | | QS count | 38 |
| really_bad_starts | INTEGER | | RBS count | 3 |
| gsax_total | DECIMAL(6,2) | | Season GSAx | 12.4 |
| high_danger_save_pct | DECIMAL(5,3) | | Season HDSV% | 0.825 |

---

## Fatigue Metrics

### goalie_fatigue_metrics
**Description**: Calculated fatigue indicators and workload metrics

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal record ID | 1 |
| player_id | INTEGER | FK players(id) | Goalie reference | 25 |
| game_id | INTEGER | FK games(id) | Game reference | 1001 |
| calculation_date | DATE | NOT NULL | Calculation date | 2024-01-15 |
| games_last_3d | INTEGER | | Games in 3 days | 2 |
| games_last_5d | INTEGER | | Games in 5 days | 3 |
| games_last_7d | INTEGER | | Games in 7 days | 4 |
| games_last_10d | INTEGER | | Games in 10 days | 5 |
| minutes_last_7d | INTEGER | | Minutes in 7 days | 240 |
| minutes_last_10d | INTEGER | | Minutes in 10 days | 360 |
| shots_faced_last_7d | INTEGER | | Shots in 7 days | 142 |
| days_since_last_game | INTEGER | | Rest days | 1 |
| is_back_to_back | BOOLEAN | | B2B game flag | false |
| is_three_in_four | BOOLEAN | | 3-in-4 flag | true |
| consecutive_games | INTEGER | | Games in row | 2 |
| season_games_played | INTEGER | | Season GP to date | 35 |
| season_workload_pct | DECIMAL(5,2) | | % of team games | 0.875 |
| fatigue_index | DECIMAL(5,2) | | Composite score (0-100) | 67.5 |
| physical_fatigue_score | DECIMAL(5,2) | | Physical component | 72.3 |
| mental_fatigue_score | DECIMAL(5,2) | | Mental component | 62.7 |
| recovery_score | DECIMAL(5,2) | | Recovery rating (0-100) | 45.0 |

### travel_metrics
**Description**: Travel-related fatigue factors

| Field | Type | Constraints | Description | Example |
|-------|------|-------------|-------------|---------|
| id | SERIAL | PRIMARY KEY | Internal record ID | 1 |
| team_id | INTEGER | FK teams(id) | Team reference | 10 |
| game_id | INTEGER | FK games(id) | Game reference | 1001 |
| previous_game_id | INTEGER | FK games(id) | Prior game | 998 |
| origin_city | VARCHAR(100) | | Departure city | "Tampa" |
| destination_city | VARCHAR(100) | | Arrival city | "Toronto" |
| distance_miles | DECIMAL(8,2) | | Travel distance | 1053.45 |
| distance_km | DECIMAL(8,2) | GENERATED | Distance in km | 1695.23 |
| travel_method | VARCHAR(20) | | Travel type | "flight" |
| estimated_travel_hours | DECIMAL(4,2) | | Travel time | 5.5 |
| timezone_change | INTEGER | | TZ difference | 0 |
| is_eastward | BOOLEAN | | Eastward travel | true |
| altitude_change_ft | INTEGER | | Altitude delta | -750 |
| arrival_day | VARCHAR(20) | | Arrival timing | "game_day" |
| rest_hours_available | INTEGER | | Rest time | 16 |
| cumulative_miles_5d | DECIMAL(10,2) | | 5-day total | 3421.5 |
| cumulative_miles_10d | DECIMAL(10,2) | | 10-day total | 5234.8 |

---

## API Response Schemas

### FatigueAnalysisResponse
```json
{
  "goalie": {
    "id": 8476899,
    "name": "Andrei Vasilevskiy",
    "team": "TBL",
    "age": 29
  },
  "current_fatigue": {
    "fatigue_index": 67.5,
    "physical_score": 72.3,
    "mental_score": 62.7,
    "recovery_score": 45.0,
    "status": "moderate_fatigue"
  },
  "recent_workload": {
    "games_last_7d": 4,
    "minutes_last_7d": 240,
    "save_pct_last_7d": 0.908,
    "back_to_backs": 1,
    "travel_miles": 2145.6
  },
  "performance_trend": {
    "baseline_save_pct": 0.918,
    "fatigued_save_pct": 0.905,
    "performance_drop": -1.42
  },
  "recommendations": [
    {
      "priority": "high",
      "action": "rest_recommended",
      "reasoning": "4 games in 7 days with declining save percentage"
    }
  ],
  "next_game_prediction": {
    "opponent": "BOS",
    "predicted_save_pct": 0.902,
    "confidence_interval": [0.885, 0.919],
    "risk_level": "elevated"
  }
}
```

### PerformancePredictionRequest
```json
{
  "goalie_id": 8476899,
  "game_date": "2024-01-20",
  "opponent_team_id": 6,
  "is_home_game": true,
  "model_version": "v2.3",
  "include_confidence_intervals": true,
  "fatigue_override": null
}
```

### TeamFatigueSnapshot
```json
{
  "team": {
    "id": 14,
    "name": "Tampa Bay Lightning",
    "abbreviation": "TBL"
  },
  "snapshot_date": "2024-01-15",
  "goalies": [
    {
      "id": 8476899,
      "name": "Andrei Vasilevskiy",
      "role": "starter",
      "fatigue_index": 67.5,
      "availability": "questionable",
      "last_game": "2024-01-14",
      "projected_start_probability": 0.65
    },
    {
      "id": 8478048,
      "name": "Jonas Johansson", 
      "role": "backup",
      "fatigue_index": 22.1,
      "availability": "available",
      "last_game": "2024-01-08",
      "projected_start_probability": 0.35
    }
  ],
  "upcoming_schedule": [
    {
      "date": "2024-01-16",
      "opponent": "BOS",
      "location": "home",
      "back_to_back": false,
      "recommended_starter": 8478048
    }
  ]
}
```

---

## Calculated Fields

### Fatigue Index Formula
```python
def calculate_fatigue_index(metrics: Dict) -> float:
    """
    Composite fatigue score from 0-100
    
    Components:
    - Recent games (30%): games_last_7d
    - Workload intensity (25%): minutes + shots faced
    - Travel (20%): distance + timezone changes  
    - Recovery (15%): days rest + age factor
    - Cumulative (10%): season workload
    """
    
    # Normalize each component to 0-100 scale
    games_score = min(metrics['games_last_7d'] / 5 * 100, 100)
    
    workload_score = (
        (metrics['minutes_last_7d'] / 420) * 50 +  # 7 hours = 100%
        (metrics['shots_last_7d'] / 210) * 50      # 30/game = 100%
    )
    
    travel_score = (
        (metrics['travel_miles_5d'] / 5000) * 70 + # 5000 miles = 100%
        (abs(metrics['timezone_changes']) / 3) * 30 # 3 zones = 100%
    )
    
    recovery_score = 100 - (
        (metrics['days_rest'] / 3) * 50 +          # 3+ days = full recovery
        ((35 - metrics['age']) / 15) * 50          # Age penalty
    )
    
    cumulative_score = (
        metrics['season_workload_pct'] * 100        # % of team games
    )
    
    # Weighted average
    fatigue_index = (
        games_score * 0.30 +
        workload_score * 0.25 +
        travel_score * 0.20 +
        recovery_score * 0.15 +
        cumulative_score * 0.10
    )
    
    return round(fatigue_index, 2)
```

### Goals Saved Above Expected (GSAx)
```python
def calculate_gsax(shots_data: List[Dict]) -> float:
    """
    GSAx = Actual Saves - Expected Saves
    Expected Saves based on shot quality model
    """
    expected_goals = sum(shot['xG'] for shot in shots_data)
    actual_goals = sum(1 for shot in shots_data if shot['is_goal'])
    
    gsax = expected_goals - actual_goals
    return round(gsax, 2)
```

### Quality Start Determination
```python
def is_quality_start(save_pct: float, saves: int, league_avg_saves: float) -> bool:
    """
    Quality Start if:
    1. Save % >= .917, OR
    2. Saves > League average for that game
    """
    return save_pct >= 0.917 or saves > league_avg_saves
```

---

## Data Quality Rules

### Validation Rules

1. **Goalie Stats Validation**
   - `saves <= shots_against` (saves cannot exceed shots)
   - `save_percentage = saves / shots_against` (must match)
   - `time_on_ice <= game_duration` (cannot exceed game length)
   - `goals_against >= 0` (non-negative)

2. **Travel Validation**
   - `distance_miles >= 0` (non-negative distance)
   - `travel_hours <= 24` (reasonable travel time)
   - `arrival_day IN ('two_days_before', 'day_before', 'game_day')`

3. **Fatigue Metrics Validation**
   - `fatigue_index BETWEEN 0 AND 100`
   - `games_last_Xd` counts must be consistent
   - `is_back_to_back = true` only if `days_rest = 0`

4. **Game Data Validation**
   - `home_score >= 0 AND away_score >= 0`
   - `game_state IN ('Scheduled', 'In Progress', 'Final')`
   - `date_time` must be valid timestamp

### Data Freshness Requirements

| Data Type | Maximum Lag | Update Frequency |
|-----------|-------------|------------------|
| Live game stats | 30 seconds | Real-time |
| Final game stats | 1 hour | Post-game |
| Travel calculations | 6 hours | Twice daily |
| Fatigue metrics | 15 minutes | Every 15 min |
| Season aggregates | 1 hour | Hourly |
| Predictions | 5 minutes | On-demand + cache |

### Missing Data Handling

1. **Required Fields**: Fail validation if missing
2. **Optional Fields**: Use NULL, not empty strings
3. **Derived Fields**: Recalculate if source data updates
4. **Historical Gaps**: Flag in data quality reports

### Audit Trail Requirements

All data modifications must track:
- `created_at`: Record creation timestamp
- `updated_at`: Last modification timestamp  
- `updated_by`: User/system that made change
- `version`: Record version number
- `change_reason`: Optional change justification