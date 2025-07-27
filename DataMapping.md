# NHL Data Mapping and Schema Documentation

This document provides a comprehensive mapping of data variables collected from the NHL API, how they're processed through our data pipeline, and the database schema used for storage.

## Data Sources

Our primary data source is the NHL Stats API (`https://statsapi.web.nhl.com/api/v1`), which provides:

1. Team information
2. Game schedules (regular season and playoffs)
3. Player information
4. Game statistics
5. Season statistics

## Data Collection Process

Data is collected in the following sequence:

1. **Teams**: Basic information about all NHL teams
2. **Schedule**: Game schedules for specified seasons and game types (regular/playoffs)
3. **Players**: Information about players, categorized by position
4. **Game Logs**: Game-by-game statistics for each player

## Primary Entities and Variables

### Teams

| Variable | Data Type | Description | Source Field | Processing Notes |
|----------|-----------|-------------|-------------|------------------|
| team_id | INTEGER | Unique identifier for the team | id | Primary key |
| name | TEXT | Full team name | name | - |
| abbreviation | TEXT | Team abbreviation | abbreviation | - |
| team_name | TEXT | Team name | name | - |
| location | TEXT | Team location/city | venue.city | - |
| venue_name | TEXT | Name of home venue | venue.name | - |
| venue_city | TEXT | City of home venue | venue.city | - |
| venue_lat | REAL | Venue latitude | - | Added during geo processing |
| venue_long | REAL | Venue longitude | - | Added during geo processing |
| division | TEXT | Division name | division.name | - |
| conference | TEXT | Conference name | conference.name | - |
| first_year_of_play | INTEGER | First year team played | firstYearOfPlay | - |
| season | TEXT | Season identifier (YYYYYYYY format) | - | Added during processing |

### Games

| Variable | Data Type | Description | Source Field | Processing Notes |
|----------|-----------|-------------|-------------|------------------|
| game_id | INTEGER | Unique identifier for the game | gamePk | Primary key |
| season | TEXT | Season identifier (YYYYYYYY format) | season | - |
| game_type | TEXT | Game type (R=Regular, P=Playoff) | gameType | - |
| date | TEXT | Game date | date | - |
| datetime | TEXT | Game date with time | - | Constructed from date and time fields |
| away_team_id | INTEGER | ID of away team | teams.away.team.id | Foreign key to teams |
| home_team_id | INTEGER | ID of home team | teams.home.team.id | Foreign key to teams |
| away_score | INTEGER | Final score of away team | teams.away.score | - |
| home_score | INTEGER | Final score of home team | teams.home.score | - |
| status | TEXT | Game status | status.detailedState | - |
| venue | TEXT | Game venue | venue.name | - |
| venue_lat | REAL | Venue latitude | - | Added during geo processing |
| venue_long | REAL | Venue longitude | - | Added during geo processing |
| travel_distance | REAL | Distance between venues (km) | - | Calculated during geo processing |
| travel_time | REAL | Estimated travel time | - | Calculated during geo processing |
| days_since_last_game | INTEGER | Days since team's last game | - | Calculated during feature engineering |
| back_to_back | INTEGER | Flag for back-to-back games (0/1) | - | Calculated during feature engineering |
| is_playoff | INTEGER | Flag for playoff games (0/1) | - | Based on game_type |
| playoff_round | INTEGER | Playoff round number | seriesSummary.round | Only for playoff games |
| playoff_series | TEXT | Series identifier | seriesSummary.seriesCode | Only for playoff games |
| playoff_game_number | INTEGER | Game number in series | seriesSummary.gameNumber | Only for playoff games |
| elimination_game | INTEGER | Flag for elimination games (0/1) | - | Calculated during feature engineering |

### Players

| Variable | Data Type | Description | Source Field | Processing Notes |
|----------|-----------|-------------|-------------|------------------|
| player_id | INTEGER | Unique identifier for player | id | Primary key |
| full_name | TEXT | Player's full name | fullName | - |
| first_name | TEXT | Player's first name | firstName | - |
| last_name | TEXT | Player's last name | lastName | - |
| nationality | TEXT | Player's nationality | nationality | - |
| birth_date | TEXT | Player's birth date | birthDate | ISO format |
| height | TEXT | Player's height | height | - |
| weight | INTEGER | Player's weight in pounds | weight | - |
| shoots_catches | TEXT | Handedness | shootsCatches | - |
| position | TEXT | Position code (G, D, L, R, C) | primaryPosition.abbreviation | - |
| position_type | TEXT | Position category (G, D, F) | - | Derived from position |
| team_id | INTEGER | Current team ID | currentTeam.id | Foreign key to teams |
| season | TEXT | Season identifier | - | Added during processing |
| is_active | INTEGER | Active status flag (0/1) | active | - |

### Goalie Game Logs

| Variable | Data Type | Description | Source Field | Processing Notes |
|----------|-----------|-------------|-------------|------------------|
| id | INTEGER | Unique record identifier | - | Auto-increment primary key |
| player_id | INTEGER | Player identifier | player_id | Foreign key to players |
| game_id | INTEGER | Game identifier | game.gamePk | Foreign key to games |
| team_id | INTEGER | Team identifier | team.id | Foreign key to teams |
| opponent_id | INTEGER | Opponent team identifier | opponent.id | Foreign key to teams |
| game_date | TEXT | Date of game | date | ISO format |
| season | TEXT | Season identifier | season | - |
| game_type | TEXT | Game type (R/P) | game_type | - |
| home_away | TEXT | Home or away game (H/A) | - | Based on isHome |
| decision | TEXT | Game decision (W/L/O) | decision | - |
| started | INTEGER | Whether goalie started (0/1) | - | Based on game data |
| shots_against | INTEGER | Shots faced | shots | - |
| saves | INTEGER | Saves made | saves | - |
| goals_against | INTEGER | Goals allowed | goalsAgainst | - |
| save_percentage | REAL | Save percentage | savePercentage | - |
| time_on_ice | TEXT | Time on ice (MM:SS) | timeOnIce | - |
| time_on_ice_mins | REAL | Time on ice in minutes | - | Converted from timeOnIce |
| shutout | INTEGER | Shutout flag (0/1) | - | Based on goalsAgainst |
| days_since_last_game | INTEGER | Days since last game | - | Calculated during feature engineering |
| back_to_back | INTEGER | Back-to-back game flag (0/1) | - | Calculated during feature engineering |
| travel_distance | REAL | Distance traveled (km) | - | From games table |
| opponent_strength | REAL | Opponent strength metric | - | Calculated during feature engineering |
| workload_7day | REAL | 7-day workload metric | - | Calculated during feature engineering |
| workload_30day | REAL | 30-day workload metric | - | Calculated during feature engineering |
| is_playoff | INTEGER | Playoff game flag (0/1) | - | Based on game_type |
| elimination_game | INTEGER | Elimination game flag (0/1) | - | Calculated during feature engineering |

### Skater Game Logs

| Variable | Data Type | Description | Source Field | Processing Notes |
|----------|-----------|-------------|-------------|------------------|
| id | INTEGER | Unique record identifier | - | Auto-increment primary key |
| player_id | INTEGER | Player identifier | player_id | Foreign key to players |
| game_id | INTEGER | Game identifier | game.gamePk | Foreign key to games |
| team_id | INTEGER | Team identifier | team.id | Foreign key to teams |
| opponent_id | INTEGER | Opponent team identifier | opponent.id | Foreign key to teams |
| game_date | TEXT | Date of game | date | ISO format |
| season | TEXT | Season identifier | season | - |
| game_type | TEXT | Game type (R/P) | game_type | - |
| home_away | TEXT | Home or away game (H/A) | - | Based on isHome |
| position | TEXT | Position played | position | - |
| goals | INTEGER | Goals scored | goals | - |
| assists | INTEGER | Assists | assists | - |
| points | INTEGER | Total points | points | - |
| plus_minus | INTEGER | Plus/minus rating | plusMinus | - |
| penalty_minutes | INTEGER | Penalty minutes | pim | - |
| shots | INTEGER | Shots on goal | shots | - |
| hits | INTEGER | Hits delivered | hits | - |
| blocks | INTEGER | Shots blocked | blocked | - |
| time_on_ice | TEXT | Time on ice (MM:SS) | timeOnIce | - |
| time_on_ice_mins | REAL | Time on ice in minutes | - | Converted from timeOnIce |
| power_play_goals | INTEGER | Power play goals | powerPlayGoals | - |
| power_play_assists | INTEGER | Power play assists | powerPlayAssists | - |
| power_play_points | INTEGER | Power play points | - | Calculated during processing |
| shorthanded_goals | INTEGER | Shorthanded goals | shortHandedGoals | - |
| shorthanded_assists | INTEGER | Shorthanded assists | shortHandedAssists | - |
| shorthanded_points | INTEGER | Shorthanded points | - | Calculated during processing |
| faceoff_wins | INTEGER | Faceoff wins | faceOffWins | - |
| faceoff_taken | INTEGER | Faceoffs taken | faceoffTaken | - |
| faceoff_percentage | REAL | Faceoff win percentage | faceOffPct | - |
| days_since_last_game | INTEGER | Days since last game | - | Calculated during feature engineering |
| back_to_back | INTEGER | Back-to-back game flag (0/1) | - | Calculated during feature engineering |
| travel_distance | REAL | Distance traveled (km) | - | From games table |
| opponent_strength | REAL | Opponent strength metric | - | Calculated during feature engineering |
| workload_7day | REAL | 7-day workload metric | - | Calculated during feature engineering |
| workload_30day | REAL | 30-day workload metric | - | Calculated during feature engineering |
| is_playoff | INTEGER | Playoff game flag (0/1) | - | Based on game_type |
| elimination_game | INTEGER | Elimination game flag (0/1) | - | Calculated during feature engineering |

## Derived and Calculated Features

### Workload Metrics

Workload metrics are calculated during feature engineering:

1. **days_since_last_game**: Number of days since player's last game
2. **is_back_to_back**: Flag for games played on consecutive days (0/1)
3. **games_last_7d**: Count of games played in the last 7 days
4. **games_last_14d**: Count of games played in the last 14 days
4. **games_last_30d**: Count of games played in the last 30 days
5. **minutes_last_7d**: Total minutes played in the last 7 days
6. **minutes_last_14d**: Total minutes played in the last 14 days
7. **minutes_last_30d**: Total minutes played in the last 30 days
8. **season_game_num**: Cumulative count of games played in the season

### Performance Relative to Rest

Performance metrics relative to rest are calculated during feature engineering:

1. **rest_category**: Categorization of rest between games
   - "first_game": First game of season/dataset
   - "back_to_back": 0-1 days between games
   - "short_rest": 2-3 days between games
   - "long_rest": 4+ days between games
   
2. **{metric}_avg**: Player's average for the metric across all games
3. **{metric}_vs_avg**: Difference between game performance and player's average
4. **{metric}_by_rest**: Average performance within each rest category
5. **{metric}_b2b_vs_rest**: Difference between back-to-back and long rest performance

### Playoff Metrics

Playoff-specific metrics calculated during feature engineering:

1. **is_playoff**: Flag for playoff games (0/1)
2. **is_elimination_game**: Flag for potential elimination games (0/1)
3. **{metric}_vs_reg_season**: Playoff game performance relative to regular season average

## Database Schema

The database uses SQLite with the following key tables and relationships:

```sql
-- Teams table
CREATE TABLE teams (
    team_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL,
    team_name TEXT NOT NULL,
    location TEXT NOT NULL,
    venue_name TEXT,
    venue_city TEXT,
    venue_lat REAL,
    venue_long REAL,
    division TEXT,
    conference TEXT,
    first_year_of_play INTEGER,
    season TEXT
);

-- Games table
CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    season TEXT NOT NULL,
    game_type TEXT NOT NULL,
    date TEXT NOT NULL,
    datetime TEXT,
    away_team_id INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_score INTEGER,
    home_score INTEGER,
    status TEXT,
    venue TEXT,
    venue_lat REAL,
    venue_long REAL,
    travel_distance REAL,
    travel_time REAL,
    days_since_last_game INTEGER,
    back_to_back INTEGER,
    is_playoff INTEGER,
    playoff_round INTEGER,
    playoff_series TEXT,
    playoff_game_number INTEGER,
    elimination_game INTEGER,
    FOREIGN KEY (away_team_id) REFERENCES teams (team_id),
    FOREIGN KEY (home_team_id) REFERENCES teams (team_id)
);

-- Players table
CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    nationality TEXT,
    birth_date TEXT,
    height TEXT,
    weight INTEGER,
    shoots_catches TEXT,
    position TEXT NOT NULL,
    position_type TEXT NOT NULL,
    team_id INTEGER,
    season TEXT NOT NULL,
    is_active INTEGER,
    FOREIGN KEY (team_id) REFERENCES teams (team_id)
);

-- Goalie Season Stats table
CREATE TABLE goalie_season_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season TEXT NOT NULL,
    game_type TEXT NOT NULL,
    team_id INTEGER,
    games_played INTEGER,
    games_started INTEGER,
    wins INTEGER,
    losses INTEGER,
    ties INTEGER,
    ot_losses INTEGER,
    shutouts INTEGER,
    saves INTEGER,
    shots_against INTEGER,
    goals_against INTEGER,
    save_percentage REAL,
    goals_against_average REAL,
    time_on_ice_mins INTEGER,
    FOREIGN KEY (player_id) REFERENCES players (player_id),
    FOREIGN KEY (team_id) REFERENCES teams (team_id)
);

-- Skater Season Stats table
CREATE TABLE skater_season_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season TEXT NOT NULL,
    game_type TEXT NOT NULL,
    team_id INTEGER,
    games_played INTEGER,
    goals INTEGER,
    assists INTEGER,
    points INTEGER,
    plus_minus INTEGER,
    penalty_minutes INTEGER,
    power_play_goals INTEGER,
    power_play_points INTEGER,
    shorthanded_goals INTEGER,
    shorthanded_points INTEGER,
    game_winning_goals INTEGER,
    shots INTEGER,
    shooting_percentage REAL,
    time_on_ice_mins INTEGER,
    hits INTEGER,
    blocks INTEGER,
    FOREIGN KEY (player_id) REFERENCES players (player_id),
    FOREIGN KEY (team_id) REFERENCES teams (team_id)
);

-- Goalie Game Logs table
CREATE TABLE goalie_game_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    opponent_id INTEGER NOT NULL,
    game_date TEXT NOT NULL,
    season TEXT NOT NULL,
    game_type TEXT NOT NULL,
    home_away TEXT NOT NULL,
    decision TEXT,
    started INTEGER,
    shots_against INTEGER,
    saves INTEGER,
    goals_against INTEGER,
    save_percentage REAL,
    time_on_ice TEXT,
    time_on_ice_mins REAL,
    shutout INTEGER,
    days_since_last_game INTEGER,
    back_to_back INTEGER,
    travel_distance REAL,
    opponent_strength REAL,
    workload_7day REAL,
    workload_30day REAL,
    is_playoff INTEGER,
    elimination_game INTEGER,
    FOREIGN KEY (player_id) REFERENCES players (player_id),
    FOREIGN KEY (game_id) REFERENCES games (game_id),
    FOREIGN KEY (team_id) REFERENCES teams (team_id),
    FOREIGN KEY (opponent_id) REFERENCES teams (team_id)
);

-- Skater Game Logs table
CREATE TABLE skater_game_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    opponent_id INTEGER NOT NULL,
    game_date TEXT NOT NULL,
    season TEXT NOT NULL,
    game_type TEXT NOT NULL,
    home_away TEXT NOT NULL,
    position TEXT NOT NULL,
    goals INTEGER,
    assists INTEGER,
    points INTEGER,
    plus_minus INTEGER,
    penalty_minutes INTEGER,
    shots INTEGER,
    hits INTEGER,
    blocks INTEGER,
    time_on_ice TEXT,
    time_on_ice_mins REAL,
    power_play_goals INTEGER,
    power_play_assists INTEGER,
    power_play_points INTEGER,
    shorthanded_goals INTEGER,
    shorthanded_assists INTEGER,
    shorthanded_points INTEGER,
    faceoff_wins INTEGER,
    faceoff_taken INTEGER,
    faceoff_percentage REAL,
    days_since_last_game INTEGER,
    back_to_back INTEGER,
    travel_distance REAL,
    opponent_strength REAL,
    workload_7day REAL,
    workload_30day REAL,
    is_playoff INTEGER,
    elimination_game INTEGER,
    FOREIGN KEY (player_id) REFERENCES players (player_id),
    FOREIGN KEY (game_id) REFERENCES games (game_id),
    FOREIGN KEY (team_id) REFERENCES teams (team_id),
    FOREIGN KEY (opponent_id) REFERENCES teams (team_id)
);

-- Team Game Logs table
CREATE TABLE team_game_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    opponent_id INTEGER NOT NULL,
    game_date TEXT NOT NULL,
    season TEXT NOT NULL,
    game_type TEXT NOT NULL,
    home_away TEXT NOT NULL,
    goals_for INTEGER,
    goals_against INTEGER,
    shots_for INTEGER,
    shots_against INTEGER,
    power_play_goals INTEGER,
    power_play_opportunities INTEGER,
    power_play_percentage REAL,
    penalty_kill_percentage REAL,
    faceoff_win_percentage REAL,
    blocks INTEGER,
    hits INTEGER,
    win INTEGER,
    loss INTEGER,
    ot_loss INTEGER,
    regulation_win INTEGER,
    days_since_last_game INTEGER,
    back_to_back INTEGER,
    travel_distance REAL,
    is_playoff INTEGER,
    playoff_round INTEGER,
    elimination_game INTEGER,
    FOREIGN KEY (team_id) REFERENCES teams (team_id),
    FOREIGN KEY (game_id) REFERENCES games (game_id),
    FOREIGN KEY (opponent_id) REFERENCES teams (team_id)
);

-- Analysis Results table
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,
    player_id INTEGER,
    team_id INTEGER,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    sample_size INTEGER,
    statistical_significance REAL,
    created_at TEXT NOT NULL,
    analysis_parameters TEXT,
    FOREIGN KEY (player_id) REFERENCES players (player_id),
    FOREIGN KEY (team_id) REFERENCES teams (team_id)
);
```

## Entity-Relationship Diagram

The database has the following key relationships:

1. **Teams** - Central entity with relationships to:
   - Games (home_team_id, away_team_id)
   - Players (team_id)
   - Game logs (team_id, opponent_id)

2. **Players** - Player entity with relationships to:
   - Teams (team_id)
   - Game logs (player_id)
   - Season stats (player_id)

3. **Games** - Game entity with relationships to:
   - Teams (home_team_id, away_team_id)
   - Game logs (game_id)

4. **Game Logs** - Detailed game statistics with relationships to:
   - Players (player_id)
   - Teams (team_id, opponent_id)
   - Games (game_id)

## Data Processing Pipeline

1. **Data Collection**:
   - Fetch raw data from NHL API
   - Store in CSV files for each entity type

2. **Geographical Enhancement**:
   - Add venue coordinates
   - Calculate travel distances and times

3. **Feature Engineering**:
   - Calculate workload metrics
   - Calculate performance relative to rest
   - Add playoff-specific metrics
   - Calculate opponent strength

4. **Database Storage**:
   - Import processed data into SQLite database
   - Create indexes for performance optimization

5. **Analysis**:
   - Generate performance statistics
   - Analyze back-to-back vs. rested performance
   - Compare playoff vs. regular season performance
   - Study travel impact

## Using the Data

The data structure is optimized for different types of analysis:

1. **Game-by-game analysis**: Using game logs tables
2. **Season-level analysis**: Using season stats tables
3. **Player-specific analysis**: Filtering by player_id
4. **Team-specific analysis**: Filtering by team_id
5. **Situation-specific analysis**: Using derived metrics (back-to-back, travel, etc.)
6. **Playoff analysis**: Using playoff flags and metrics

## Notes for Data Scientists

When working with this data:

1. **Time Series Analysis**: Game logs are naturally time-series data. Consider using appropriate time-series methods.
2. **Feature Importance**: There are many features that could explain performance variations; use feature importance techniques to identify the most significant ones.
3. **Missing Data**: Some older games might have fewer metrics available; handle missing data appropriately.
4. **Player Changes**: Players might change teams during a season; account for team_id changes in analysis.
5. **Normalization**: Consider normalizing metrics when comparing players with different workloads or roles.
6. **Sample Size**: Be aware of sample size issues, especially for backups and playoff-specific analysis.

## Notes for Data Engineers

When working with this dataset:

1. **Database Indexing**: The provided schema includes indexes on common query fields, but additional indexes might be needed based on query patterns.
2. **Storage Requirements**: Expect approximately 50-100MB per season for full game-by-game logs including all derived metrics.
3. **API Rate Limiting**: The NHL API has rate limits; the code includes delay mechanisms to respect these limits.
4. **Update Frequency**: Consider implementing a daily or weekly update process during active seasons.
5. **Backup Strategy**: Implement regular backup of the SQLite database, especially after major data imports.
6. **Validation**: Validate important metrics against official NHL statistics as a sanity check. 