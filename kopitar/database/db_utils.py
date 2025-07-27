import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from contextlib import contextmanager

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
        logging.FileHandler("kopitar_db_utils.log"),
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
    # Decide how to handle this - exit or raise? Raising might be better for library use.
    raise ValueError("POSTGRES_PASSWORD environment variable not set.")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class NHLDatabase:
    """Class to interact with the NHL performance database using SQLAlchemy"""

    def __init__(self):
        """Initialize the database engine"""
        try:
            # Consider connection pooling options for production
            self.engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
            # Test connection during initialization
            with self.engine.connect() as connection:
                logger.info(f"Successfully connected to database: {DB_NAME} on {DB_HOST}:{DB_PORT}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database engine or connecting: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Provides a connection from the pool."""
        connection = None
        try:
            connection = self.engine.connect()
            yield connection
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
                # logger.debug("Database connection returned to pool") # Optional

    def execute_query(self, query, params=None):
        """
        Execute a SQL query and return the results as a DataFrame.

        Args:
            query (str): SQL query to execute (use standard SQL placeholders like :param).
            params (dict, optional): Parameters for the query (using named parameters is recommended).

        Returns:
            pd.DataFrame: Query results as a DataFrame.
        """
        logger.debug(f"Executing query: {query} with params: {params}")
        try:
            # Use pandas read_sql_query directly with the engine
            # Pandas handles connection management when passed an engine
            return pd.read_sql_query(sql=text(query), con=self.engine, params=params)
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        except Exception as e: # Catch other potential pandas errors
             logger.error(f"Unexpected error during query execution: {e}")
             logger.error(f"Query: {query}")
             logger.error(f"Params: {params}")
             raise

    def execute_update(self, query, params=None):
        """
        Execute a SQL update/insert/delete query within a transaction.

        Args:
            query (str): SQL query to execute (use standard SQL placeholders like :param).
            params (dict, optional): Parameters for the query (using named parameters is recommended).

        Returns:
            int: Number of rows affected (Note: may not be reliable for all statements/DBs).
                 Returns -1 if rowcount is not supported or available.
        """
        logger.debug(f"Executing update: {query} with params: {params}")
        try:
            # Use context manager for connection handling
            with self.get_connection() as connection:
                with connection.begin(): # Start transaction
                    result = connection.execute(text(query), params)
                    # rowcount might not be available for all statements (e.g., INSERT RETURNING)
                    rows_affected = result.rowcount if hasattr(result, 'rowcount') else -1
                logger.debug(f"Update executed successfully. Rows affected: {rows_affected}")
                return rows_affected
        except SQLAlchemyError as e:
            logger.error(f"Error executing update: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            # Transaction is automatically rolled back by connection.begin() context manager on error
            raise
        except Exception as e:
             logger.error(f"Unexpected error during update execution: {e}")
             logger.error(f"Query: {query}")
             logger.error(f"Params: {params}")
             raise

    # --- Data Retrieval Methods (Adapted for SQLAlchemy) ---
    # Note: Using f-strings for building WHERE clauses can be risky if inputs aren't sanitized.
    # Using bind parameters (:param_name) with SQLAlchemy's text() is safer.

    def get_teams(self, season=None):
        """Get all teams, optionally filtered by season"""
        query = "SELECT * FROM teams"
        params = {}
        if season:
            query += " WHERE season = :season"
            params['season'] = int(season) # Ensure correct type if needed
        return self.execute_query(query, params)

    def get_team_by_id(self, team_id):
        """Get team by ID"""
        query = "SELECT * FROM teams WHERE team_id = :team_id"
        return self.execute_query(query, {'team_id': team_id})

    def get_players(self, position_type=None, team_id=None, season=None, is_active=None):
        """Get all players, optionally filtered"""
        query = "SELECT * FROM players"
        conditions = []
        params = {}
        if position_type:
            conditions.append("position_type = :position_type")
            params['position_type'] = position_type
        if team_id:
            conditions.append("team_id = :team_id")
            params['team_id'] = team_id
        if season:
            conditions.append("season = :season")
            params['season'] = season
        if is_active is not None:
            conditions.append("is_active = :is_active")
            params['is_active'] = bool(is_active) # Ensure boolean
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        return self.execute_query(query, params if params else None)

    def get_player_by_id(self, player_id):
        """Get player by ID"""
        query = "SELECT * FROM players WHERE player_id = :player_id"
        return self.execute_query(query, {'player_id': player_id})

    def search_players(self, name_query, position_type=None):
        """Search players by name (case-insensitive)"""
        # Use ILIKE for case-insensitive search in PostgreSQL
        query = "SELECT * FROM players WHERE full_name ILIKE :name_query"
        params = {'name_query': f"%{name_query}%"}
        if position_type:
            query += " AND position_type = :position_type"
            params['position_type'] = position_type
        return self.execute_query(query, params)

    def get_games(self, season=None, team_id=None, is_playoff=None, date_from=None, date_to=None):
        """Get games, optionally filtered"""
        query = "SELECT * FROM games"
        conditions = []
        params = {}
        if season:
            conditions.append("season = :season")
            params['season'] = int(season)
        if team_id:
            conditions.append("(home_team_id = :team_id OR away_team_id = :team_id)")
            params['team_id'] = team_id
        if is_playoff is not None:
            conditions.append("is_playoff = :is_playoff")
            params['is_playoff'] = bool(is_playoff)
        if date_from:
            conditions.append("date >= :date_from") # Assuming 'date' column is text YYYY-MM-DD
            params['date_from'] = date_from
        if date_to:
            conditions.append("date <= :date_to")
            params['date_to'] = date_to
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date, game_id"
        return self.execute_query(query, params if params else None)

    def get_game_by_id(self, game_id):
        """Get game by ID"""
        query = "SELECT * FROM games WHERE game_id = :game_id"
        return self.execute_query(query, {'game_id': game_id})

    # --- Game Log Methods ---
    # These methods join multiple tables. Ensure table/column names match the new schema.

    def get_goalie_game_logs(self, player_id=None, team_id=None, season=None, game_type=None,
                            is_playoff=None, date_from=None, date_to=None, limit=None):
        """Get goalie game logs, optionally filtered"""
        query = """
        SELECT g.*, p.full_name as player_name, t.name as team_name, opp.name as opponent_name
        FROM goalie_game_logs g
        JOIN players p ON g.player_id = p.player_id
        JOIN teams t ON g.team_id = t.team_id
        JOIN teams opp ON g.opponent_id = opp.team_id
        """
        conditions = []
        params = {}
        if player_id:
            conditions.append("g.player_id = :player_id")
            params['player_id'] = player_id
        if team_id:
            conditions.append("g.team_id = :team_id")
            params['team_id'] = team_id
        if season:
            conditions.append("g.season = :season")
            params['season'] = season
        if game_type:
            conditions.append("g.game_type = :game_type")
            params['game_type'] = game_type
        if is_playoff is not None:
            conditions.append("g.is_playoff = :is_playoff")
            params['is_playoff'] = bool(is_playoff)
        if date_from:
            conditions.append("g.game_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            conditions.append("g.game_date <= :date_to")
            params['date_to'] = date_to
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY g.game_date DESC, g.game_id"
        if limit:
            query += " LIMIT :limit"
            params['limit'] = int(limit)
        return self.execute_query(query, params if params else None)

    def get_skater_game_logs(self, player_id=None, team_id=None, position=None, season=None,
                           game_type=None, is_playoff=None, date_from=None, date_to=None, limit=None):
        """Get skater game logs, optionally filtered"""
        query = """
        SELECT s.*, p.full_name as player_name, t.name as team_name, opp.name as opponent_name
        FROM skater_game_logs s
        JOIN players p ON s.player_id = p.player_id
        JOIN teams t ON s.team_id = t.team_id
        JOIN teams opp ON s.opponent_id = opp.team_id
        """
        conditions = []
        params = {}
        if player_id:
            conditions.append("s.player_id = :player_id")
            params['player_id'] = player_id
        if team_id:
            conditions.append("s.team_id = :team_id")
            params['team_id'] = team_id
        if position:
            conditions.append("s.position = :position")
            params['position'] = position
        if season:
            conditions.append("s.season = :season")
            params['season'] = season
        if game_type:
            conditions.append("s.game_type = :game_type")
            params['game_type'] = game_type
        if is_playoff is not None:
            conditions.append("s.is_playoff = :is_playoff")
            params['is_playoff'] = bool(is_playoff)
        if date_from:
            conditions.append("s.game_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            conditions.append("s.game_date <= :date_to")
            params['date_to'] = date_to
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY s.game_date DESC, s.game_id"
        if limit:
            query += " LIMIT :limit"
            params['limit'] = int(limit)
        return self.execute_query(query, params if params else None)

    # --- Analysis Methods ---
    # These methods perform aggregations. Check column names and logic.
    # Consider moving complex analysis logic out of db_utils if it grows.

    def analyze_back_to_back_performance(self, position_type=None, season=None, is_playoff=None):
        """Analyze performance in back-to-back games compared to rested games"""
        params = {}
        conditions = []

        if position_type == 'G':
            query = """
            SELECT
                p.full_name as player_name, p.position, t.name as team_name,
                COUNT(CASE WHEN g.back_to_back = false THEN 1 END) as rested_games,
                COUNT(CASE WHEN g.back_to_back = true THEN 1 END) as b2b_games,
                AVG(CASE WHEN g.back_to_back = false THEN g.save_percentage END) as rested_save_pct,
                AVG(CASE WHEN g.back_to_back = true THEN g.save_percentage END) as b2b_save_pct,
                AVG(CASE WHEN g.back_to_back = false THEN g.goals_against END) as rested_goals_against,
                AVG(CASE WHEN g.back_to_back = true THEN g.goals_against END) as b2b_goals_against
            FROM goalie_game_logs g
            JOIN players p ON g.player_id = p.player_id
            JOIN teams t ON g.team_id = t.team_id
            """
            if season:
                conditions.append("g.season = :season")
                params['season'] = season
            if is_playoff is not None:
                conditions.append("g.is_playoff = :is_playoff")
                params['is_playoff'] = bool(is_playoff)
            order_by = "ORDER BY (AVG(CASE WHEN g.back_to_back = true THEN g.save_percentage END) - AVG(CASE WHEN g.back_to_back = false THEN g.save_percentage END)) DESC NULLS LAST"

        elif position_type in ('D', 'F'):
            query = """
            SELECT
                p.full_name as player_name, p.position, t.name as team_name,
                COUNT(CASE WHEN s.back_to_back = false THEN 1 END) as rested_games,
                COUNT(CASE WHEN s.back_to_back = true THEN 1 END) as b2b_games,
                AVG(CASE WHEN s.back_to_back = false THEN s.points END) as rested_points,
                AVG(CASE WHEN s.back_to_back = true THEN s.points END) as b2b_points,
                AVG(CASE WHEN s.back_to_back = false THEN s.shots END) as rested_shots,
                AVG(CASE WHEN s.back_to_back = true THEN s.shots END) as b2b_shots,
                AVG(CASE WHEN s.back_to_back = false THEN s.time_on_ice_mins END) as rested_toi,
                AVG(CASE WHEN s.back_to_back = true THEN s.time_on_ice_mins END) as b2b_toi
            FROM skater_game_logs s
            JOIN players p ON s.player_id = p.player_id
            JOIN teams t ON s.team_id = t.team_id
            """
            conditions.append("p.position_type = :position_type")
            params['position_type'] = position_type
            if season:
                conditions.append("s.season = :season")
                params['season'] = season
            if is_playoff is not None:
                conditions.append("s.is_playoff = :is_playoff")
                params['is_playoff'] = bool(is_playoff)
            order_by = "ORDER BY (AVG(CASE WHEN s.back_to_back = true THEN s.points END) - AVG(CASE WHEN s.back_to_back = false THEN s.points END)) DESC NULLS LAST"
        else:
            logger.error(f"Invalid position_type for back-to-back analysis: {position_type}")
            return pd.DataFrame() # Return empty DataFrame

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            GROUP BY p.player_id, p.full_name, p.position, t.name
            HAVING (COUNT(CASE WHEN {alias}.back_to_back = false THEN 1 END) >= 5
                AND COUNT(CASE WHEN {alias}.back_to_back = true THEN 1 END) >= 3)
        """.format(alias='g' if position_type == 'G' else 's')
        query += order_by

        return self.execute_query(query, params)


    def analyze_playoff_vs_regular(self, position_type=None, season=None, min_games=5):
        """Compare playoff performance to regular season performance"""
        params = {'min_games': min_games}
        conditions = []

        if position_type == 'G':
            query = """
            SELECT
                p.full_name as player_name, p.position, t.name as team_name,
                COUNT(CASE WHEN g.is_playoff = false THEN 1 END) as regular_season_games,
                COUNT(CASE WHEN g.is_playoff = true THEN 1 END) as playoff_games,
                AVG(CASE WHEN g.is_playoff = false THEN g.save_percentage END) as regular_season_save_pct,
                AVG(CASE WHEN g.is_playoff = true THEN g.save_percentage END) as playoff_save_pct,
                AVG(CASE WHEN g.is_playoff = false THEN g.goals_against END) as regular_season_goals_against,
                AVG(CASE WHEN g.is_playoff = true THEN g.goals_against END) as playoff_goals_against
            FROM goalie_game_logs g
            JOIN players p ON g.player_id = p.player_id
            JOIN teams t ON g.team_id = t.team_id
            """
            if season:
                conditions.append("g.season = :season")
                params['season'] = season
            order_by = "ORDER BY (AVG(CASE WHEN g.is_playoff = true THEN g.save_percentage END) - AVG(CASE WHEN g.is_playoff = false THEN g.save_percentage END)) DESC NULLS LAST"

        elif position_type in ('D', 'F'):
            query = """
            SELECT
                p.full_name as player_name, p.position, t.name as team_name,
                COUNT(CASE WHEN s.is_playoff = false THEN 1 END) as regular_season_games,
                COUNT(CASE WHEN s.is_playoff = true THEN 1 END) as playoff_games,
                AVG(CASE WHEN s.is_playoff = false THEN s.points END) as regular_season_points,
                AVG(CASE WHEN s.is_playoff = true THEN s.points END) as playoff_points,
                AVG(CASE WHEN s.is_playoff = false THEN s.goals END) as regular_season_goals,
                AVG(CASE WHEN s.is_playoff = true THEN s.goals END) as playoff_goals,
                AVG(CASE WHEN s.is_playoff = false THEN s.time_on_ice_mins END) as regular_season_toi,
                AVG(CASE WHEN s.is_playoff = true THEN s.time_on_ice_mins END) as playoff_toi
            FROM skater_game_logs s
            JOIN players p ON s.player_id = p.player_id
            JOIN teams t ON s.team_id = t.team_id
            """
            conditions.append("p.position_type = :position_type")
            params['position_type'] = position_type
            if season:
                conditions.append("s.season = :season")
                params['season'] = season
            order_by = "ORDER BY (AVG(CASE WHEN s.is_playoff = true THEN s.points END) - AVG(CASE WHEN s.is_playoff = false THEN s.points END)) DESC NULLS LAST"
        else:
            logger.error(f"Invalid position_type for playoff analysis: {position_type}")
            return pd.DataFrame()

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            GROUP BY p.player_id, p.full_name, p.position, t.name
            HAVING (COUNT(CASE WHEN {alias}.is_playoff = false THEN 1 END) >= :min_games
                AND COUNT(CASE WHEN {alias}.is_playoff = true THEN 1 END) >= :min_games)
        """.format(alias='g' if position_type == 'G' else 's')
        query += order_by

        return self.execute_query(query, params)

    def store_analysis_result(self, analysis_type, player_id=None, team_id=None,
                             metric_name=None, metric_value=None, sample_size=None,
                             statistical_significance=None, analysis_parameters=None):
        """Store analysis result in the database"""
        query = """
        INSERT INTO analysis_results
        (analysis_type, player_id, team_id, metric_name, metric_value,
         sample_size, statistical_significance, created_at, analysis_parameters)
        VALUES (:analysis_type, :player_id, :team_id, :metric_name, :metric_value,
                :sample_size, :statistical_significance, :created_at, :analysis_parameters)
        RETURNING id; -- Optionally return the new ID
        """
        params = {
            'analysis_type': analysis_type,
            'player_id': player_id,
            'team_id': team_id,
            'metric_name': metric_name,
            'metric_value': metric_value,
            'sample_size': sample_size,
            'statistical_significance': statistical_significance,
            'created_at': datetime.utcnow(), # Use UTC time
            'analysis_parameters': analysis_parameters # Should be JSON string or use JSON type
        }

        try:
            with self.get_connection() as connection:
                 with connection.begin(): # Start transaction
                    result = connection.execute(text(query), params)
                    inserted_id = result.scalar_one_or_none() # Get the returned ID
                    logger.info(f"Stored analysis result with ID: {inserted_id}")
                    return inserted_id
        except SQLAlchemyError as e:
            logger.error(f"Error storing analysis result: {e}")
            logger.error(f"Params: {params}")
            raise


# --- Singleton Pattern for DB Instance ---
# This ensures only one engine is created per application lifecycle.
_db_instance = None

def get_db():
    """
    Get a singleton instance of the NHLDatabase.
    """
    global _db_instance
    if _db_instance is None:
        logger.info("Creating new NHLDatabase instance.")
        try:
            _db_instance = NHLDatabase()
        except Exception as e:
            logger.error(f"Failed to initialize NHLDatabase: {e}")
            # Depending on application needs, you might exit or return None
            sys.exit(1) # Exit if DB connection is critical
    return _db_instance

# Example usage (for testing purposes)
if __name__ == "__main__":
    try:
        db = get_db() # Get the singleton instance

        # Example: Get all teams for the 20222023 season
        teams = db.get_teams(season='20222023')
        print(f"\nFound {len(teams)} teams for the 2022-2023 season")
        if not teams.empty:
            print(teams.head())

        # Example: Get all goalies
        goalies = db.get_players(position_type='G')
        print(f"\nFound {len(goalies)} goalies in the database")
        if not goalies.empty:
            print(goalies.head())

        # Example: Get goalie game logs for a specific player (e.g., Andrei Vasilevskiy)
        # Search first (case-insensitive)
        vasilevskiy_search = db.search_players('Vasilevskiy', position_type='G')
        if not vasilevskiy_search.empty:
            player_id = vasilevskiy_search.iloc[0]['player_id']
            print(f"\nFound Vasilevskiy with player_id: {player_id}")
            logs = db.get_goalie_game_logs(player_id=player_id, limit=5)
            print(f"Found {len(logs)} game logs for Vasilevskiy (showing 5)")
            if not logs.empty:
                print(logs.head())
        else:
            print("\nCould not find player 'Vasilevskiy'")

        # Example: Analyze back-to-back performance for goalies
        b2b_analysis = db.analyze_back_to_back_performance(position_type='G', season='20222023')
        print(f"\nBack-to-back analysis completed for {len(b2b_analysis)} goalies (Season 20222023)")
        if not b2b_analysis.empty:
            print(b2b_analysis.head())

        # Example: Store a dummy analysis result
        # dummy_id = db.store_analysis_result(
        #     analysis_type='test_b2b',
        #     player_id=8476883, # Example player ID
        #     metric_name='save_percentage_diff',
        #     metric_value=-0.015,
        #     sample_size=20,
        #     statistical_significance=0.04,
        #     analysis_parameters='{"season": "20222023"}'
        # )
        # print(f"\nStored dummy analysis result with ID: {dummy_id}")

    except Exception as e:
        logger.exception(f"An error occurred during example usage: {e}")
