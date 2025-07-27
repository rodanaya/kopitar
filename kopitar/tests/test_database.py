import os
import sys
import unittest
import logging
import pandas as pd
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path to import utility modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the refactored db_utils and the metadata from db_setup
try:
    from database.db_utils import get_db, NHLDatabase
    # Import metadata to create/drop tables. Assumes db_setup defines it globally.
    from database.db_setup import metadata
except ImportError as e:
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"Failed to import database modules: {e}. Ensure paths are correct and db_setup defines metadata.")
    sys.exit(1)

# Set up logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use the actual database configured via .env for testing
# WARNING: This will modify the live database specified in .env!
# Consider using a separate test database configuration in a real-world scenario.
try:
    db_instance = get_db()
    test_engine = db_instance.engine # Use the engine from the singleton instance
except Exception as e:
    logger.error(f"Failed to connect to the test database configured in .env: {e}")
    sys.exit(1)


class TestDatabase(unittest.TestCase):
    """Test cases for the NHL performance database using PostgreSQL"""

    @classmethod
    def setUpClass(cls):
        """Create tables once before all tests."""
        logger.info("Setting up test database schema...")
        try:
            # Drop existing tables (if any) and recreate schema
            metadata.drop_all(bind=test_engine)
            metadata.create_all(bind=test_engine)
            logger.info("Test database schema created.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to set up test database schema: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Drop tables once after all tests are done."""
        logger.info("Tearing down test database schema...")
        try:
            metadata.drop_all(bind=test_engine)
            logger.info("Test database schema dropped.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to tear down test database schema: {e}")
            # Don't raise here, just log the error

    def setUp(self):
        """Add test data before each test."""
        logger.debug(f"Setting up data for test: {self.id()}")
        self.db = db_instance # Use the shared engine instance
        self._add_test_data()

    def tearDown(self):
        """Remove test data after each test by truncating tables."""
        logger.debug(f"Tearing down data for test: {self.id()}")
        try:
            with self.db.engine.connect() as connection:
                with connection.begin(): # Transaction
                    # Truncate tables in reverse order of dependency or use CASCADE
                    for table_name in reversed(metadata.sorted_tables):
                         logger.debug(f"Truncating table: {table_name.name}")
                         # Use TRUNCATE ... RESTART IDENTITY CASCADE for efficiency and FK handling
                         connection.execute(text(f'TRUNCATE TABLE "{table_name.name}" RESTART IDENTITY CASCADE'))
        except SQLAlchemyError as e:
            logger.error(f"Failed to truncate tables during teardown: {e}")
            # Don't raise here to allow other tests to run

    def _add_test_data(self):
        """Add test data to the database using SQLAlchemy"""
        logger.debug("Adding test data...")
        try:
            with self.db.engine.connect() as connection:
                 with connection.begin(): # Use transaction
                    # Add teams
                    teams_data = [
                        {'team_id': 1, 'name': 'Tampa Bay Lightning', 'abbreviation': 'TBL', 'team_name': 'Lightning', 'location': 'Tampa Bay', 'division': 'Atlantic', 'conference': 'Eastern', 'season': 20222023},
                        {'team_id': 2, 'name': 'Florida Panthers', 'abbreviation': 'FLA', 'team_name': 'Panthers', 'location': 'Florida', 'division': 'Atlantic', 'conference': 'Eastern', 'season': 20222023},
                        {'team_id': 3, 'name': 'Los Angeles Kings', 'abbreviation': 'LAK', 'team_name': 'Kings', 'location': 'Los Angeles', 'division': 'Pacific', 'conference': 'Western', 'season': 20222023}
                    ]
                    if teams_data:
                        connection.execute(metadata.tables['teams'].insert(), teams_data)

                    # Add players
                    players_data = [
                        {'player_id': 1, 'full_name': 'Andrei Vasilevskiy', 'position': 'G', 'position_type': 'G', 'team_id': 1, 'season': '20222023', 'is_active': True},
                        {'player_id': 2, 'full_name': 'Sergei Bobrovsky', 'position': 'G', 'position_type': 'G', 'team_id': 2, 'season': '20222023', 'is_active': True},
                        {'player_id': 3, 'full_name': 'Anze Kopitar', 'position': 'C', 'position_type': 'F', 'team_id': 3, 'season': '20222023', 'is_active': True},
                        {'player_id': 4, 'full_name': 'Drew Doughty', 'position': 'D', 'position_type': 'D', 'team_id': 3, 'season': '20222023', 'is_active': True}
                    ]
                    if players_data:
                         connection.execute(metadata.tables['players'].insert(), players_data)

                    # Add games (needed for FK constraints in logs)
                    games_data = [
                        {'game_id': 101, 'season': 20222023, 'game_type': 'R', 'date': '2022-10-01', 'home_team_id': 1, 'away_team_id': 2, 'is_back_to_back': False},
                        {'game_id': 102, 'season': 20222023, 'game_type': 'R', 'date': '2022-10-03', 'home_team_id': 1, 'away_team_id': 3, 'is_back_to_back': True},
                        {'game_id': 103, 'season': 20222023, 'game_type': 'R', 'date': '2022-10-05', 'home_team_id': 1, 'away_team_id': 2, 'is_back_to_back': False},
                        {'game_id': 201, 'season': 20222023, 'game_type': 'P', 'date': '2023-04-15', 'home_team_id': 1, 'away_team_id': 2, 'is_back_to_back': False},
                        {'game_id': 301, 'season': 20222023, 'game_type': 'R', 'date': '2022-10-01', 'home_team_id': 3, 'away_team_id': 1, 'is_back_to_back': False},
                        {'game_id': 302, 'season': 20222023, 'game_type': 'R', 'date': '2022-10-03', 'home_team_id': 3, 'away_team_id': 2, 'is_back_to_back': True},
                        {'game_id': 303, 'season': 20222023, 'game_type': 'R', 'date': '2022-10-05', 'home_team_id': 3, 'away_team_id': 1, 'is_back_to_back': False},
                        {'game_id': 401, 'season': 20222023, 'game_type': 'P', 'date': '2023-04-15', 'home_team_id': 3, 'away_team_id': 1, 'is_back_to_back': False},
                    ]
                    if games_data:
                         connection.execute(metadata.tables['games'].insert(), games_data)


                    # Add goalie game logs
                    goalie_logs_data = [
                        {'player_id': 1, 'game_id': 101, 'team_id': 1, 'opponent_id': 2, 'game_date': '2022-10-01', 'season': '20222023', 'game_type': 'R', 'is_playoff': False, 'save_percentage': 0.923, 'goals_against': 2, 'back_to_back': False, 'home_away': 'Home'},
                        {'player_id': 1, 'game_id': 102, 'team_id': 1, 'opponent_id': 3, 'game_date': '2022-10-03', 'season': '20222023', 'game_type': 'R', 'is_playoff': False, 'save_percentage': 0.900, 'goals_against': 3, 'back_to_back': True, 'home_away': 'Home'},
                        {'player_id': 1, 'game_id': 103, 'team_id': 1, 'opponent_id': 2, 'game_date': '2022-10-05', 'season': '20222023', 'game_type': 'R', 'is_playoff': False, 'save_percentage': 0.950, 'goals_against': 1, 'back_to_back': False, 'home_away': 'Home'},
                        {'player_id': 1, 'game_id': 201, 'team_id': 1, 'opponent_id': 2, 'game_date': '2023-04-15', 'season': '20222023', 'game_type': 'P', 'is_playoff': True, 'save_percentage': 0.933, 'goals_against': 2, 'back_to_back': False, 'home_away': 'Home'}
                    ]
                    if goalie_logs_data:
                         connection.execute(metadata.tables['goalie_game_logs'].insert(), goalie_logs_data)

                    # Add skater game logs
                    skater_logs_data = [
                        {'player_id': 3, 'game_id': 301, 'team_id': 3, 'opponent_id': 1, 'game_date': '2022-10-01', 'season': '20222023', 'game_type': 'R', 'position': 'C', 'is_playoff': False, 'goals': 1, 'assists': 2, 'points': 3, 'back_to_back': False, 'time_on_ice_mins': 18.5, 'home_away': 'Home'},
                        {'player_id': 3, 'game_id': 302, 'team_id': 3, 'opponent_id': 2, 'game_date': '2022-10-03', 'season': '20222023', 'game_type': 'R', 'position': 'C', 'is_playoff': False, 'goals': 0, 'assists': 1, 'points': 1, 'back_to_back': True, 'time_on_ice_mins': 17.2, 'home_away': 'Home'},
                        {'player_id': 3, 'game_id': 303, 'team_id': 3, 'opponent_id': 1, 'game_date': '2022-10-05', 'season': '20222023', 'game_type': 'R', 'position': 'C', 'is_playoff': False, 'goals': 2, 'assists': 0, 'points': 2, 'back_to_back': False, 'time_on_ice_mins': 19.3, 'home_away': 'Home'},
                        {'player_id': 3, 'game_id': 401, 'team_id': 3, 'opponent_id': 1, 'game_date': '2023-04-15', 'season': '20222023', 'game_type': 'P', 'position': 'C', 'is_playoff': True, 'goals': 1, 'assists': 1, 'points': 2, 'back_to_back': False, 'time_on_ice_mins': 20.1, 'home_away': 'Home'}
                    ]
                    if skater_logs_data:
                         connection.execute(metadata.tables['skater_game_logs'].insert(), skater_logs_data)

                 logger.debug("Test data added.")
        except SQLAlchemyError as e:
            logger.error(f"Error adding test data: {e}")
            raise # Re-raise to fail the test setup

    # --- Test Methods ---

    def test_get_teams(self):
        """Test get_teams method"""
        teams = self.db.get_teams()
        self.assertEqual(len(teams), 3)
        # Test with season filter (season is int now)
        teams_season = self.db.get_teams(season=20222023)
        self.assertEqual(len(teams_season), 3)
        self.assertEqual(teams_season.iloc[0]['name'], 'Tampa Bay Lightning')

    def test_get_players(self):
        """Test get_players method"""
        players = self.db.get_players()
        self.assertEqual(len(players), 4)
        goalies = self.db.get_players(position_type='G')
        self.assertEqual(len(goalies), 2)
        forwards = self.db.get_players(position_type='F')
        self.assertEqual(len(forwards), 1)
        kings_players = self.db.get_players(team_id=3)
        self.assertEqual(len(kings_players), 2)
        active_players = self.db.get_players(is_active=True)
        self.assertEqual(len(active_players), 4)

    def test_search_players(self):
        """Test search_players method"""
        # Use the actual method now
        found_kopitar = self.db.search_players('Kopitar')
        self.assertEqual(len(found_kopitar), 1)
        self.assertEqual(found_kopitar.iloc[0]['full_name'], 'Anze Kopitar')

        found_vasi = self.db.search_players('Vasilevskiy', position_type='G')
        self.assertEqual(len(found_vasi), 1)
        self.assertEqual(found_vasi.iloc[0]['full_name'], 'Andrei Vasilevskiy')

        # Test case-insensitivity (PostgreSQL ILIKE)
        found_case = self.db.search_players('kopitar')
        self.assertEqual(len(found_case), 1)

        # Test no results
        found_none = self.db.search_players('NonExistentName')
        self.assertTrue(found_none.empty)

    def test_get_goalie_game_logs(self):
        """Test get_goalie_game_logs method"""
        logs = self.db.get_goalie_game_logs()
        self.assertEqual(len(logs), 4)
        vasy_logs = self.db.get_goalie_game_logs(player_id=1)
        self.assertEqual(len(vasy_logs), 4)
        playoff_logs = self.db.get_goalie_game_logs(is_playoff=True)
        self.assertEqual(len(playoff_logs), 1)
        self.assertEqual(playoff_logs.iloc[0]['game_type'], 'P')
        # Test combined filters
        vasy_playoff = self.db.get_goalie_game_logs(player_id=1, is_playoff=True)
        self.assertEqual(len(vasy_playoff), 1)

    def test_get_skater_game_logs(self):
        """Test get_skater_game_logs method"""
        logs = self.db.get_skater_game_logs()
        self.assertEqual(len(logs), 4)
        kopitar_logs = self.db.get_skater_game_logs(player_id=3)
        self.assertEqual(len(kopitar_logs), 4)
        playoff_logs = self.db.get_skater_game_logs(is_playoff=True)
        self.assertEqual(len(playoff_logs), 1)
        self.assertEqual(playoff_logs.iloc[0]['game_type'], 'P')
        # Test combined filters
        kopitar_playoff = self.db.get_skater_game_logs(player_id=3, is_playoff=True)
        self.assertEqual(len(kopitar_playoff), 1)

    def test_analyze_back_to_back_performance_goalie(self):
        """Test analyze_back_to_back_performance method for Goalies"""
        # Use the actual method
        analysis = self.db.analyze_back_to_back_performance(position_type='G', season='20222023')
        # Our test data might not meet the HAVING clause criteria (5 rested, 3 b2b)
        # Let's check the raw counts first
        vasy_logs = self.db.get_goalie_game_logs(player_id=1, season='20222023')
        rested_count = len(vasy_logs[vasy_logs['back_to_back'] == False])
        b2b_count = len(vasy_logs[vasy_logs['back_to_back'] == True])
        logger.info(f"Vasilevskiy test logs: Rested={rested_count}, B2B={b2b_count}")
        # Based on test data: Rested=3, B2B=1. This won't pass HAVING clause.
        self.assertTrue(analysis.empty, "Expected empty result due to HAVING clause")

        # TODO: Add more test data to satisfy the HAVING clause for a more thorough test

    def test_analyze_playoff_vs_regular_skater(self):
        """Test analyze_playoff_vs_regular method for Skaters"""
        # Use the actual method
        analysis = self.db.analyze_playoff_vs_regular(position_type='F', season='20222023', min_games=1) # Lower min_games for test data
        self.assertEqual(len(analysis), 1) # Kopitar should meet min_games=1
        self.assertEqual(analysis.iloc[0]['player_name'], 'Anze Kopitar')
        self.assertIn('regular_season_points', analysis.columns)
        self.assertIn('playoff_points', analysis.columns)
        self.assertAlmostEqual(analysis.iloc[0]['regular_season_points'], (3+1+2)/3) # Avg points in R games
        self.assertAlmostEqual(analysis.iloc[0]['playoff_points'], 2/1) # Avg points in P games

    def test_get_db_function(self):
        """Test get_db helper function returns a valid NHLDatabase instance"""
        # get_db() now returns the singleton instance connected to PostgreSQL
        db_instance_test = get_db()
        self.assertIsInstance(db_instance_test, NHLDatabase)
        # Check if the engine is connected
        try:
            with db_instance_test.engine.connect() as conn:
                self.assertIsNotNone(conn)
        except SQLAlchemyError as e:
            self.fail(f"get_db() instance failed to connect: {e}")


if __name__ == '__main__':
    # Ensure the script is run from the main project root or adjust paths accordingly
    logger.info("Running database tests...")
    unittest.main()
