# Kopitar: NHL Performance Analysis Framework

![NHL](https://nhl.bamcontent.com/images/photos/324131200/1024x576/cut.jpg)

A comprehensive framework for analyzing NHL player performance data across different game conditions, with a focus on situational performance analytics.

## Project Overview

Kopitar is a data analytics framework that collects, processes, and analyzes NHL player performance data to identify patterns across different game conditions, such as:

- Regular season vs. playoff performance
- Back-to-back game impact
- Home vs. away differences
- Travel impact on performance

The framework includes a full data pipeline from API data collection to interactive visualization via a Streamlit dashboard.

## NHL API Information

**Important**: The NHL API used by this project has undergone significant changes. The old API endpoint (`statsapi.web.nhl.com/api/v1`) has been deprecated and replaced with two new endpoints:

1. `api-web.nhle.com` - Web-focused endpoints for schedules, team rosters, etc.
2. `api.nhle.com/stats/rest` - Stats-focused endpoints for detailed statistics

This project uses the `nhl-api-py` library (version 2.18.0+) which has been updated to work with the new NHL API endpoints. However, due to the undocumented nature of the NHL API, some endpoints may require adjustments as the API continues to evolve.

For the most up-to-date API documentation, refer to:
- [NHL-API-Reference](https://github.com/Zmalski/NHL-API-Reference) - Community-maintained reference

## Features

- **Comprehensive Data Collection**: Gather data from the NHL Stats API for teams, players, and game-by-game performance.
- **Robust Database**: Store structured data in PostgreSQL (managed via Docker) with optimized schemas for performance analytics.
- **Advanced Analysis**: Run statistical tests to identify performance patterns across various conditions.
- **Interactive Dashboard**: Visualize performance trends and metrics with a user-friendly Streamlit interface.

## Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Docker and Docker Compose

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kopitar.git
cd kopitar
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root directory with your PostgreSQL credentials:
```dotenv
# .env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=Kopitar
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secret_password
```
   *(Replace `your_secret_password` with a strong password, like the `Cr1ms0n_K1ng` provided, or your own. The default user/db name can be kept or changed here and in `docker-compose.yml`)*

## Usage

### 1. Start the Database Container

First, start the PostgreSQL database using Docker Compose:
```bash
docker compose up -d db
```
Wait a few moments for the database to initialize. You can check its status with `docker compose ps`. The database will persist data in a Docker volume named `postgres_data`.

### 2. Run Individual Components or Full Pipeline

#### Database Setup (and Initial Data Import)

This script now connects using the credentials in the `.env` file. It creates tables and optionally imports data.

To create tables and import data from `kopitar/data` (appending to existing data):
```bash
python kopitar/database/db_setup.py --data_dir kopitar/data --import_mode append
```

To **reset** the database (drop all tables) and then import data:
```bash
python kopitar/database/db_setup.py --data_dir kopitar/data --reset --import_mode replace
```

To only create/reset tables without importing:
```bash
python kopitar/database/db_setup.py --reset --skip_import
```

#### Data Collection

```bash
python kopitar/analysis/data_collection.py --seasons 20232024 20222023 --game_types R P --player_types G D F
```
*(Note: Ensure the database is set up before running collection if it saves directly to DB)*

#### Performance Analysis

*(Note: Ensure the database is populated before running analysis)*
```bash
python kopitar/analysis/player_performance_analysis.py --data-file <path_to_data_or_use_db> --output-dir kopitar/results
```
*(Update analysis scripts if they need to read directly from the PostgreSQL DB via `db_utils.py`)*

#### Launch Dashboard

*(Note: Ensure the dashboard app reads from the PostgreSQL DB via `db_utils.py`)*
```bash
streamlit run kopitar/dashboard/app.py
```

### Run the Full Pipeline (Example)

*(Note: The `run_analysis.py` script would need to be updated to orchestrate these steps correctly with the new DB setup)*

```bash
# Example sequence (adapt run_analysis.py or run manually)
# 1. Start DB (if not running)
docker compose up -d db
# 2. Setup/Reset DB and Import Data
python kopitar/database/db_setup.py --data_dir kopitar/data --reset --import_mode replace
# 3. Run Analysis (assuming it reads from DB)
python kopitar/analysis/player_performance_analysis.py --output-dir kopitar/results
# 4. Launch Dashboard (assuming it reads from DB)
streamlit run kopitar/dashboard/app.py
```

## Data Workflow

1. **Data Collection**: Raw data is fetched from the NHL Stats API
2. **Data Processing**: Raw data is cleaned and transformed (potentially saved as intermediate files or loaded directly)
3. **Database Storage**: Processed data is stored in a PostgreSQL database (managed by Docker) using `db_setup.py`.
4. **Analysis**: Statistical tests are run on the stored data, reading from PostgreSQL via `db_utils.py`.
5. **Visualization**: Results are displayed in an interactive dashboard, reading from PostgreSQL via `db_utils.py`.

## Testing

Run the database tests to ensure database functionality:
*(Note: `test_database.py` needs to be updated to connect to PostgreSQL)*
```bash
# Update test_database.py first!
# python kopitar/tests/test_database.py
```

Test the NHL API functionality:
```bash
python test_nhl_api.py
```

## Project Structure

```
kopitar/
├── .env                     # Environment variables (DB credentials) - DO NOT COMMIT
├── docker-compose.yml       # Docker configuration for PostgreSQL
├── analysis/                # Analysis modules
│   ├── data_collection.py   # Fetches data from NHL API
│   ├── player_performance_analysis.py  # General player analysis
│   └── goalie_performance_analysis.py  # Goalie-specific analysis
├── database/                # Database related code
│   ├── db_setup.py          # Database setup and schema creation (PostgreSQL)
│   └── db_utils.py          # Database utility functions (PostgreSQL)
├── dashboard/               # Visualization components
│   └── app.py               # Streamlit dashboard application
├── scripts/                 # Utility scripts
│   └── run_analysis.py      # Main pipeline runner script (Needs update)
├── tests/                   # Test modules
│   └── test_database.py     # Database tests (Needs update)
├── utils/                   # Utility modules
│   └── nhl_api.py           # NHL API wrapper
├── data/                    # Storage for raw and processed data CSVs
├── results/                 # Output directory for analysis results
└── requirements.txt         # Project dependencies
```

## Database Schema

*(Note: The SQL examples below illustrate the general structure. The definitive schema is defined using SQLAlchemy in `kopitar/database/db_setup.py` and is designed for PostgreSQL.)*

### Main Tables

#### Teams Table
```sql
-- Example structure (see db_setup.py for exact definition)
CREATE TABLE teams (
    team_id INTEGER NOT NULL,
    name TEXT,
    abbreviation TEXT,
    team_name TEXT,
    location TEXT,
    division TEXT,
    conference TEXT,
    season INTEGER NOT NULL,
    PRIMARY KEY (team_id, season)
);
```

#### Players Table
```sql
-- Example structure
CREATE TABLE players (
    player_id INTEGER PRIMARY KEY NOT NULL,
    full_name TEXT,
    position TEXT,
    position_type TEXT, -- 'G', 'D', 'F'
    team_id INTEGER REFERENCES teams(team_id),
    season TEXT,
    is_active BOOLEAN
);
```

#### Games Table
```sql
-- Example structure
CREATE TABLE games (
    game_id INTEGER PRIMARY KEY NOT NULL,
    season INTEGER,
    game_type TEXT, -- 'R', 'P'
    date TEXT, -- Consider DATE type
    home_team_id INTEGER REFERENCES teams(team_id),
    away_team_id INTEGER REFERENCES teams(team_id),
    venue TEXT,
    home_score REAL,
    away_score REAL,
    is_playoff BOOLEAN,
    is_back_to_back BOOLEAN
);
```

#### Goalie Game Logs
```sql
-- Example structure
CREATE TABLE goalie_game_logs (
    id SERIAL PRIMARY KEY, -- Auto-incrementing
    player_id INTEGER REFERENCES players(player_id),
    game_id INTEGER REFERENCES games(game_id),
    team_id INTEGER REFERENCES teams(team_id),
    opponent_id INTEGER REFERENCES teams(team_id),
    game_date TEXT, -- Consider DATE type
    season TEXT,
    game_type TEXT,
    is_playoff BOOLEAN,
    save_percentage REAL,
    goals_against INTEGER,
    back_to_back BOOLEAN
);
```

#### Skater Game Logs
```sql
-- Example structure
CREATE TABLE skater_game_logs (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    game_id INTEGER REFERENCES games(game_id),
    team_id INTEGER REFERENCES teams(team_id),
    opponent_id INTEGER REFERENCES teams(team_id),
    game_date TEXT,
    season TEXT,
    game_type TEXT,
    position TEXT,
    is_playoff BOOLEAN,
    goals INTEGER,
    assists INTEGER,
    points INTEGER,
    back_to_back BOOLEAN,
    time_on_ice_mins REAL
);
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NHL Stats API for providing the data
- Players like Anze Kopitar who demonstrate exceptional performance in all game situations
