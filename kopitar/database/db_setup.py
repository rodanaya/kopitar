import os
import sys
import pandas as pd
import argparse
from datetime import datetime
import logging
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Float, Text,
    DateTime, Boolean, ForeignKey, Index, inspect, text
)
from sqlalchemy.dialects.postgresql import SERIAL # For auto-incrementing PK
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Add the parent directory to path to import utility modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file in the project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kopitar_db_setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database connection details from environment variables
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'kopitar')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')

if not DB_PASSWORD:
    logger.error("POSTGRES_PASSWORD environment variable not set.")
    sys.exit(1)

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=False) # Set echo=True for debugging SQL
metadata = MetaData()

# --- Define Tables ---

teams_table = Table('teams', metadata,
    Column('team_id', Integer, primary_key=True, nullable=False),
    Column('name', Text),
    Column('abbreviation', Text),
    Column('team_name', Text),
    Column('location', Text),
    Column('division', Text),
    Column('conference', Text),
    Column('season', Integer, primary_key=True, nullable=False) # Composite PK with team_id
)

games_table = Table('games', metadata,
    Column('game_id', Integer, primary_key=True, nullable=False),
    Column('season', Integer),
    Column('game_type', Text), # e.g., 'R', 'P'
    Column('date', Text), # Consider using Date type if format is consistent
    Column('home_team_id', Integer, ForeignKey('teams.team_id')),
    Column('away_team_id', Integer, ForeignKey('teams.team_id')),
    Column('venue', Text),
    Column('start_time', Text), # Consider Time or Timestamp
    Column('home_score', Float),
    Column('away_score', Float),
    Column('status', Text),
    Column('attendance', Integer),
    Column('distance_traveled', Float),
    Column('timezone_diff', Integer),
    Column('travel_direction', Text),
    Column('estimated_travel_time', Float),
    Column('days_since_last_game', Integer),
    Column('is_back_to_back', Boolean) # Use Boolean for flags
)

players_table = Table('players', metadata,
    Column('player_id', Integer, primary_key=True, nullable=False),
    Column('full_name', Text),
    Column('first_name', Text),
    Column('last_name', Text),
    Column('nationality', Text),
    Column('birth_date', Text), # Consider Date type
    Column('height', Text), # Format might be inconsistent (e.g., "6' 2\"")
    Column('weight', Integer),
    Column('shoots_catches', Text),
    Column('position', Text),
    Column('position_type', Text), # 'G', 'D', 'F'
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('season', Text), # Should this be Integer like in teams? Check data consistency
    Column('is_active', Boolean)
)

goalie_season_stats_table = Table('goalie_season_stats', metadata,
    Column('id', SERIAL, primary_key=True), # Use SERIAL for auto-increment
    Column('player_id', Integer, ForeignKey('players.player_id')),
    Column('season', Text),
    Column('game_type', Text),
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('games_played', Integer),
    Column('games_started', Integer),
    Column('wins', Integer),
    Column('losses', Integer),
    Column('ties', Integer),
    Column('ot_losses', Integer),
    Column('shutouts', Integer),
    Column('saves', Integer),
    Column('shots_against', Integer),
    Column('goals_against', Integer),
    Column('save_percentage', Float),
    Column('goals_against_average', Float),
    Column('time_on_ice_mins', Integer) # Assuming total minutes for season
)

skater_season_stats_table = Table('skater_season_stats', metadata,
    Column('id', SERIAL, primary_key=True),
    Column('player_id', Integer, ForeignKey('players.player_id')),
    Column('season', Text),
    Column('game_type', Text),
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('games_played', Integer),
    Column('goals', Integer),
    Column('assists', Integer),
    Column('points', Integer),
    Column('plus_minus', Integer),
    Column('penalty_minutes', Integer),
    Column('power_play_goals', Integer),
    Column('power_play_points', Integer),
    Column('shorthanded_goals', Integer),
    Column('shorthanded_points', Integer),
    Column('game_winning_goals', Integer),
    Column('shots', Integer),
    Column('shooting_percentage', Float),
    Column('time_on_ice_mins', Integer), # Assuming total minutes for season
    Column('hits', Integer),
    Column('blocks', Integer)
)

goalie_game_logs_table = Table('goalie_game_logs', metadata,
    Column('id', SERIAL, primary_key=True),
    Column('player_id', Integer, ForeignKey('players.player_id')),
    Column('game_id', Integer, ForeignKey('games.game_id')),
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('opponent_id', Integer, ForeignKey('teams.team_id')),
    Column('game_date', Text), # Consider Date type
    Column('season', Text),
    Column('game_type', Text),
    Column('home_away', Text),
    Column('decision', Text), # 'W', 'L', 'OTL', 'ND'
    Column('started', Boolean),
    Column('shots_against', Integer),
    Column('saves', Integer),
    Column('goals_against', Integer),
    Column('save_percentage', Float),
    Column('time_on_ice', Text), # e.g., "60:00"
    Column('time_on_ice_mins', Float),
    Column('shutout', Boolean),
    Column('days_since_last_game', Integer),
    Column('back_to_back', Boolean),
    Column('travel_distance', Float),
    Column('opponent_strength', Float), # How is this calculated?
    Column('workload_7day', Float), # How is this calculated?
    Column('workload_30day', Float), # How is this calculated?
    Column('is_playoff', Boolean),
    Column('elimination_game', Boolean)
)

skater_game_logs_table = Table('skater_game_logs', metadata,
    Column('id', SERIAL, primary_key=True),
    Column('player_id', Integer, ForeignKey('players.player_id')),
    Column('game_id', Integer, ForeignKey('games.game_id')),
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('opponent_id', Integer, ForeignKey('teams.team_id')),
    Column('game_date', Text), # Consider Date type
    Column('season', Text),
    Column('game_type', Text),
    Column('home_away', Text),
    Column('position', Text),
    Column('goals', Integer),
    Column('assists', Integer),
    Column('points', Integer),
    Column('plus_minus', Integer),
    Column('penalty_minutes', Integer),
    Column('shots', Integer),
    Column('hits', Integer),
    Column('blocks', Integer),
    Column('time_on_ice', Text), # e.g., "18:30"
    Column('time_on_ice_mins', Float),
    Column('power_play_goals', Integer),
    Column('power_play_assists', Integer),
    Column('power_play_points', Integer),
    Column('shorthanded_goals', Integer),
    Column('shorthanded_assists', Integer),
    Column('shorthanded_points', Integer),
    Column('faceoff_wins', Integer),
    Column('faceoff_taken', Integer),
    Column('faceoff_percentage', Float),
    Column('days_since_last_game', Integer),
    Column('back_to_back', Boolean),
    Column('travel_distance', Float),
    Column('opponent_strength', Float), # How is this calculated?
    Column('workload_7day', Float), # How is this calculated?
    Column('workload_30day', Float), # How is this calculated?
    Column('is_playoff', Boolean),
    Column('elimination_game', Boolean)
)

team_game_logs_table = Table('team_game_logs', metadata,
    Column('id', SERIAL, primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('game_id', Integer, ForeignKey('games.game_id')),
    Column('opponent_id', Integer, ForeignKey('teams.team_id')),
    Column('game_date', Text), # Consider Date type
    Column('season', Text),
    Column('game_type', Text),
    Column('home_away', Text),
    Column('goals_for', Integer),
    Column('goals_against', Integer),
    Column('shots_for', Integer),
    Column('shots_against', Integer),
    Column('power_play_goals', Integer),
    Column('power_play_opportunities', Integer),
    Column('power_play_percentage', Float),
    Column('penalty_kill_percentage', Float),
    Column('faceoff_win_percentage', Float),
    Column('blocks', Integer),
    Column('hits', Integer),
    Column('win', Boolean),
    Column('loss', Boolean),
    Column('ot_loss', Boolean),
    Column('regulation_win', Boolean),
    Column('days_since_last_game', Integer),
    Column('back_to_back', Boolean),
    Column('travel_distance', Float),
    Column('is_playoff', Boolean),
    Column('playoff_round', Integer),
    Column('elimination_game', Boolean)
)

analysis_results_table = Table('analysis_results', metadata,
    Column('id', SERIAL, primary_key=True),
    Column('analysis_type', Text),
    Column('player_id', Integer, ForeignKey('players.player_id')),
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('metric_name', Text),
    Column('metric_value', Float),
    Column('sample_size', Integer),
    Column('statistical_significance', Float), # e.g., p-value
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('analysis_parameters', Text) # Consider JSON type if available
)

player_injuries_table = Table('player_injuries', metadata,
    Column('id', SERIAL, primary_key=True),
    Column('player_id', Integer, ForeignKey('players.player_id')),
    Column('team_id', Integer, ForeignKey('teams.team_id')),
    Column('season', Integer),
    Column('start_date', Text), # Consider Date type
    Column('end_date', Text), # Consider Date type
    Column('injury_type', Text),
    Column('injury_note', Text),
    Column('games_missed', Integer),
    Column('status', Text) # e.g., 'Active', 'IR', 'Day-to-day'
)

# --- Define Indexes ---
# (SQLAlchemy creates indexes for primary keys and foreign keys automatically)
# Add custom indexes for frequently queried columns

Index('idx_games_season_type_date', games_table.c.season, games_table.c.game_type, games_table.c.date)
Index('idx_games_teams', games_table.c.home_team_id, games_table.c.away_team_id)
Index('idx_players_team_season', players_table.c.team_id, players_table.c.season)
Index('idx_players_name', players_table.c.full_name) # For searching
Index('idx_goalie_logs_player_game', goalie_game_logs_table.c.player_id, goalie_game_logs_table.c.game_id)
Index('idx_goalie_logs_filters', goalie_game_logs_table.c.team_id, goalie_game_logs_table.c.season, goalie_game_logs_table.c.game_type, goalie_game_logs_table.c.game_date)
Index('idx_skater_logs_player_game', skater_game_logs_table.c.player_id, skater_game_logs_table.c.game_id)
Index('idx_skater_logs_filters', skater_game_logs_table.c.team_id, skater_game_logs_table.c.season, skater_game_logs_table.c.game_type, skater_game_logs_table.c.game_date)
Index('idx_team_logs_team_game', team_game_logs_table.c.team_id, team_game_logs_table.c.game_id)
Index('idx_analysis_type_player_team', analysis_results_table.c.analysis_type, analysis_results_table.c.player_id, analysis_results_table.c.team_id)
Index('idx_injuries_player_season', player_injuries_table.c.player_id, player_injuries_table.c.season)


def create_tables_and_indexes(engine_to_use, reset=False):
    """
    Create all tables and indexes defined in the metadata.
    Optionally drop tables first if reset is True.

    Args:
        engine_to_use: SQLAlchemy engine instance.
        reset (bool): If True, drop all tables before creating.
    """
    try:
        if reset:
            logger.warning("Resetting database: Dropping all known tables...")
            # Drop tables in reverse order of creation (considering dependencies)
            metadata.drop_all(bind=engine_to_use, checkfirst=True)
            logger.info("Tables dropped.")
        logger.info("Creating database tables and indexes...")
        metadata.create_all(bind=engine_to_use)
        logger.info("Database tables and indexes created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables/indexes: {e}")
        raise

def import_csv_to_table(engine_to_use, csv_file, table_name, if_exists='append', chunksize=1000):
    """
    Import data from a CSV file into a database table using pandas and SQLAlchemy.

    Args:
        engine_to_use: SQLAlchemy engine instance.
        csv_file (str): Path to the CSV file.
        table_name (str): Name of the database table to import into.
        if_exists (str): How to behave if the table already exists ('fail', 'replace', 'append').
        chunksize (int): Number of rows to insert per chunk.

    Returns:
        int: Number of rows imported.
    """
    valid_options = ('fail', 'replace', 'append')
    if if_exists.lower() not in valid_options:
        logger.warning(f"Invalid if_exists value '{if_exists}'. Using 'append'.")
        if_exists = 'append'

    try:
        logger.info(f"Reading CSV file: {csv_file}")
        df = pd.read_csv(csv_file)
        logger.info(f"Read {len(df)} rows from {csv_file}")

        if df.empty:
            logger.warning(f"CSV file {csv_file} is empty. Skipping import.")
            return 0

        # Get table object from metadata
        if table_name not in metadata.tables:
             logger.error(f"Table '{table_name}' not found in metadata. Cannot import.")
             return 0
        table = metadata.tables[table_name]

        # Filter DataFrame columns to match table columns
        table_columns = {col.name for col in table.columns}
        df_filtered = df[[col for col in df.columns if col in table_columns]].copy()

        if df_filtered.empty or len(df_filtered.columns) == 0:
            logger.warning(f"No matching columns found between CSV {csv_file} and table {table_name}. Skipping.")
            return 0

        logger.info(f"Importing {len(df_filtered)} rows into table '{table_name}' with if_exists='{if_exists}'...")

        # Handle boolean conversion explicitly if needed (pandas might read as 0/1)
        for col in df_filtered.columns:
            if isinstance(table.columns[col].type, Boolean):
                 # Attempt conversion, handle potential errors if data isn't easily convertible
                 try:
                     # Map common boolean representations
                     bool_map = {'true': True, 'false': False, '1': True, '0': False, 1: True, 0: False, 't': True, 'f': False, 'yes': True, 'no': False}
                     # Apply map only if column is object type, otherwise assume numeric 0/1
                     if df_filtered[col].dtype == 'object':
                         df_filtered[col] = df_filtered[col].str.lower().map(bool_map).astype('boolean') # Use pandas nullable boolean
                     else:
                         df_filtered[col] = df_filtered[col].map(bool_map).astype('boolean')
                 except Exception as e:
                     logger.warning(f"Could not reliably convert column '{col}' to boolean: {e}. Leaving as is.")


        # Handle 'replace': Truncate the table before appending
        if if_exists.lower() == 'replace':
            logger.warning(f"Replacing data in table '{table_name}' by truncating first.")
            try:
                with engine_to_use.connect() as connection:
                    with connection.begin(): # Start transaction
                        # Use TRUNCATE for efficiency, CASCADE if there are FKs pointing TO this table
                        # Be cautious with CASCADE in production
                        connection.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'))
                        # If TRUNCATE fails due to FKs pointing FROM this table, use DELETE
                        # connection.execute(table.delete())
                logger.info(f"Table '{table_name}' truncated.")
                if_exists = 'append' # Now append the new data
            except SQLAlchemyError as e:
                logger.error(f"Error truncating table {table_name}: {e}. Trying DELETE instead.")
                try:
                     with engine_to_use.connect() as connection:
                         with connection.begin():
                             connection.execute(table.delete())
                     logger.info(f"Table '{table_name}' deleted rows.")
                     if_exists = 'append'
                except SQLAlchemyError as e_del:
                    logger.error(f"Error deleting from table {table_name}: {e_del}")
                    raise # Re-raise if delete also fails


        # Import data using pandas.to_sql
        rows_imported = len(df_filtered)
        df_filtered.to_sql(
            name=table_name,
            con=engine_to_use,
            if_exists=if_exists.lower(),
            index=False,
            chunksize=chunksize,
            method='multi' # Generally faster for PostgreSQL
        )
        logger.info(f"Successfully imported {rows_imported} rows into '{table_name}'.")
        return rows_imported

    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        return 0
    except pd.errors.EmptyDataError:
        logger.warning(f"CSV file is empty: {csv_file}")
        return 0
    except SQLAlchemyError as e:
        logger.error(f"Database error importing {csv_file} to {table_name}: {e}")
        raise # Re-raise the exception
    except Exception as e:
        logger.error(f"Unexpected error importing {csv_file} to {table_name}: {e}")
        raise # Re-raise the exception


def import_directory_to_database(engine_to_use, data_dir, season_filter=None, game_type_filter=None, if_exists='append'):
    """
    Import all relevant CSV files from a directory to the database.

    Args:
        engine_to_use: SQLAlchemy engine instance.
        data_dir (str): Path to the directory containing CSV files.
        season_filter (str, optional): Filter data to specific season.
        game_type_filter (str, optional): Filter data to specific game type (R/P).
        if_exists (str): How to handle existing tables ('fail', 'replace', 'append').

    Returns:
        dict: Statistics on the number of rows imported for each data type.
    """
    import_stats = {'teams': 0, 'games': 0, 'players': 0, 'goalie_season_stats': 0,
                    'skater_season_stats': 0, 'goalie_game_logs': 0,
                    'skater_game_logs': 0, 'team_game_logs': 0, 'player_injuries': 0} # Added injuries

    if not os.path.exists(data_dir):
        logger.error(f"Data directory does not exist: {data_dir}")
        return import_stats

    logger.info(f"Importing data from directory: {data_dir}")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    # Define mapping from file patterns to table names
    file_to_table_map = {
        'teams': 'teams',
        'schedule': 'games',
        'goalies': 'players', # Assuming base goalie file contains player info
        'skaters': 'players', # Assuming base skater file contains player info
        'goalies_game_logs': 'goalie_game_logs',
        'skaters_game_logs': 'skater_game_logs',
        'team_game_logs': 'team_game_logs',
        'injuries': 'player_injuries' # Assuming an injuries file exists
        # Add mappings for season stats if they are in separate files
    }

    # Determine import order (optional, but can help with FK constraints if needed)
    import_order = ['teams', 'players', 'games', 'goalie_season_stats', 'skater_season_stats',
                    'goalie_game_logs', 'skater_game_logs', 'team_game_logs', 'player_injuries']

    # --- Import Logic ---
    # This needs refinement based on actual file naming conventions
    # Example: Import teams first
    for file in [f for f in csv_files if 'teams' in f.lower() and 'game_logs' not in f.lower()]:
        file_path = os.path.join(data_dir, file)
        try:
            # Apply filters if necessary (e.g., season in filename)
            if season_filter and season_filter not in file: continue
            rows = import_csv_to_table(engine_to_use, file_path, 'teams', if_exists)
            import_stats['teams'] += rows
        except Exception as e:
            logger.error(f"Failed to import {file} to teams: {e}")

    # Example: Import players (from goalies/skaters files)
    for file in [f for f in csv_files if ('goalies' in f.lower() or 'skaters' in f.lower()) and 'game_logs' not in f.lower() and 'season_stats' not in f.lower()]:
         file_path = os.path.join(data_dir, file)
         try:
             if season_filter and season_filter not in file: continue
             rows = import_csv_to_table(engine_to_use, file_path, 'players', if_exists)
             import_stats['players'] += rows
             # Also try importing to season stats tables if applicable columns exist
             # This assumes season stats are in the same file as player info
             if 'goalies' in file.lower():
                 try:
                     rows_stats = import_csv_to_table(engine_to_use, file_path, 'goalie_season_stats', if_exists)
                     import_stats['goalie_season_stats'] += rows_stats
                 except Exception as e_stat:
                     logger.warning(f"Could not import goalie season stats from {file}: {e_stat}")
             elif 'skaters' in file.lower():
                 try:
                     rows_stats = import_csv_to_table(engine_to_use, file_path, 'skater_season_stats', if_exists)
                     import_stats['skater_season_stats'] += rows_stats
                 except Exception as e_stat:
                     logger.warning(f"Could not import skater season stats from {file}: {e_stat}")
         except Exception as e:
             logger.error(f"Failed to import {file} to players/stats: {e}")

    # Example: Import schedules (games)
    for file in [f for f in csv_files if 'schedule' in f.lower()]:
        file_path = os.path.join(data_dir, file)
        try:
            if season_filter and season_filter not in file: continue
            if game_type_filter and game_type_filter not in file: continue # Check game type in filename if applicable
            rows = import_csv_to_table(engine_to_use, file_path, 'games', if_exists)
            import_stats['games'] += rows
        except Exception as e:
            logger.error(f"Failed to import {file} to games: {e}")

    # Example: Import game logs
    log_types = {
        'goalies_game_logs': 'goalie_game_logs',
        'skaters_game_logs': 'skater_game_logs',
        'team_game_logs': 'team_game_logs'
    }
    for log_key, table_name in log_types.items():
        for file in [f for f in csv_files if log_key in f.lower()]:
             file_path = os.path.join(data_dir, file)
             try:
                 if season_filter and season_filter not in file: continue
                 if game_type_filter and game_type_filter not in file: continue
                 rows = import_csv_to_table(engine_to_use, file_path, table_name, if_exists)
                 import_stats[table_name] += rows
             except Exception as e:
                 logger.error(f"Failed to import {file} to {table_name}: {e}")

    # Example: Import injuries
    for file in [f for f in csv_files if 'injuries' in f.lower()]:
        file_path = os.path.join(data_dir, file)
        try:
            if season_filter and season_filter not in file: continue
            rows = import_csv_to_table(engine_to_use, file_path, 'player_injuries', if_exists)
            import_stats['player_injuries'] += rows
        except Exception as e:
            logger.error(f"Failed to import {file} to player_injuries: {e}")


    logger.info(f"Data import process finished. Stats: {import_stats}")
    return import_stats


def main():
    parser = argparse.ArgumentParser(description='NHL Performance PostgreSQL Database Setup')
    # Remove db_path, use environment variables
    parser.add_argument('--data_dir', type=str, help='Directory containing data CSV files for import')
    parser.add_argument('--reset', action='store_true', help='Drop and recreate all tables before import')
    parser.add_argument('--import_mode', type=str, choices=['append', 'replace'], default='append',
                        help="Mode for importing data ('append' or 'replace')")
    parser.add_argument('--season', type=str, help='Filter data import to specific season (e.g., 20232024)')
    parser.add_argument('--game_type', type=str, help='Filter data import to specific game type (R=Regular, P=Playoffs)')
    parser.add_argument('--skip_import', action='store_true', help='Skip data import, only create/reset tables')

    args = parser.parse_args()

    try:
        # Test connection
        with engine.connect() as connection:
            logger.info("Successfully connected to the PostgreSQL database.")

        # Create tables and indexes (potentially resetting)
        create_tables_and_indexes(engine, reset=args.reset)

        # Import data if directory is provided and not skipping
        if args.data_dir and not args.skip_import:
            import_stats = import_directory_to_database(
                engine,
                args.data_dir,
                args.season,
                args.game_type,
                if_exists=args.import_mode
            )
            logger.info(f"Import statistics: {import_stats}")
        elif not args.skip_import:
             logger.info("No data directory provided (--data_dir). Skipping data import.")
        else:
            logger.info("Skipping data import as requested (--skip_import).")

        logger.info("Database setup script finished successfully.")

    except SQLAlchemyError as e:
        logger.error(f"Database connection or setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
