#!/usr/bin/env python
"""
NHL Performance Analysis - Main Runner Script

This script orchestrates the entire data pipeline:
1. (Optional) Data collection from NHL API
2. (Optional) Database setup and population (PostgreSQL)
3. (Optional) Analysis execution
4. (Optional) Dashboard launch

Author: Your Name / Cline
Date: 2023 / 2025
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import subprocess
import time

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir) # This should be the 'kopitar' directory
# Go one level up for the main project root where .env and docker-compose.yml reside
main_project_root = os.path.dirname(project_root)
sys.path.append(project_root) # Add 'kopitar' to path
sys.path.append(main_project_root) # Add main project root to path

# Configure logging
log_file_path = os.path.join(main_project_root, "kopitar_pipeline.log") # Log in main root
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Helper Function to Run Subprocess ---
def run_script(cmd, step_name, continue_on_error=False):
    """Runs a script using subprocess and logs the outcome."""
    logger.info(f"Starting {step_name}...")
    # Ensure command elements are strings
    cmd_str = [str(c) for c in cmd]
    logger.info(f"Executing: {' '.join(cmd_str)}")
    start_time = time.time()
    try:
        # Run from the main project root directory for consistent paths and .env access
        result = subprocess.run(cmd_str, check=True, text=True, capture_output=True, cwd=main_project_root, encoding='utf-8')
        logger.info(f"{step_name} STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"{step_name} STDERR:\n{result.stderr}")
        elapsed = time.time() - start_time
        logger.info(f"{step_name} completed successfully in {elapsed:.2f} seconds.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{step_name} failed with exit code {e.returncode}")
        # Log stdout/stderr safely, handling potential encoding issues if needed
        stdout_log = e.stdout.strip() if e.stdout else "N/A"
        stderr_log = e.stderr.strip() if e.stderr else "N/A"
        logger.error(f"STDOUT:\n{stdout_log}")
        logger.error(f"STDERR:\n{stderr_log}")
        elapsed = time.time() - start_time
        logger.info(f"{step_name} failed after {elapsed:.2f} seconds.")
        if not continue_on_error:
            logger.error(f"Pipeline aborted after {step_name} failure.")
            sys.exit(1) # Exit pipeline if step fails and continue_on_error is False
        return False
    except FileNotFoundError:
        logger.error(f"Error: Script or Python interpreter not found for {step_name}. Command: {' '.join(cmd_str)}")
        if not continue_on_error:
            sys.exit(1)
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during {step_name}: {e}")
        if not continue_on_error:
            sys.exit(1)
        return False

# --- Pipeline Step Functions ---

def run_data_collection(args):
    """Run the data collection script"""
    cmd = [
        sys.executable, # Use sys.executable to ensure correct python interpreter
        os.path.join(project_root, "analysis", "data_collection.py"),
        "--seasons", *args.seasons,
        "--game_types", *args.game_types,
        "--player_types", *args.player_types,
        # Output relative to main project root where script is run
        "--output_dir", os.path.join("kopitar", "data")
    ]
    if args.efficient:
        cmd.append("--efficient")
    return run_script(cmd, "Data Collection", args.continue_on_error)

def setup_database(args):
    """Set up and populate the PostgreSQL database"""
    cmd = [
        sys.executable,
        os.path.join(project_root, "database", "db_setup.py"),
        # data_dir relative to main project root
        "--data_dir", os.path.join("kopitar", "data"),
        "--import_mode", "replace" if args.reset_db else "append"
    ]
    if args.reset_db:
        cmd.append("--reset")
    if args.skip_import:
        cmd.append("--skip_import")
    # Pass season/game_type filters if provided for targeted import
    # Use the main --seasons and --game_types args for filtering import
    if args.seasons:
        cmd.extend(["--season", *args.seasons])
    if args.game_types:
         cmd.extend(["--game_type", *args.game_types])

    return run_script(cmd, "Database Setup", args.continue_on_error)

def run_analysis(args):
    """Run the analysis scripts based on selected position"""
    logger.info("Running performance analysis...")
    overall_success = True

    positions_to_analyze = []
    if args.position == 'all' or args.position is None:
        # Default to analyzing all if not specified or 'all'
        positions_to_analyze = ['G', 'D', 'F']
    else:
        positions_to_analyze = [args.position]

    # Use --seasons and --game_types arguments for analysis filtering
    analysis_seasons = args.seasons
    analysis_game_types = args.game_types

    for pos in positions_to_analyze:
        logger.info(f"--- Running analysis for position: {pos} ---")
        script_path = ""
        cmd_base = [sys.executable]

        if pos == 'G':
            script_path = os.path.join(project_root, "analysis", "goalie_performance_analysis.py")
            cmd_base.append(script_path)
            # Goalie script doesn't take --position arg
        elif pos in ['D', 'F']:
            script_path = os.path.join(project_root, "analysis", "player_performance_analysis.py")
            cmd_base.extend([script_path, "--position", pos])
        else:
            logger.warning(f"Skipping analysis for unknown position: {pos}")
            continue

        # Add common arguments
        if analysis_seasons:
            cmd_base.extend(["--season", *analysis_seasons])
        if analysis_game_types:
            cmd_base.extend(["--game_type", *analysis_game_types])
        if args.min_games:
            cmd_base.extend(["--min-games", str(args.min_games)])

        # Output dir relative to main project root
        output_dir = os.path.join("kopitar", "results", pos) # e.g., kopitar/results/G
        cmd_base.extend(["--output-dir", output_dir])

        if args.save_analysis_results:
             cmd_base.append("--save-results")

        # Run the analysis script for the current position
        success = run_script(cmd_base, f"Analysis ({pos})", args.continue_on_error)
        if not success:
            overall_success = False
            if not args.continue_on_error:
                return False # Stop if any analysis fails and we're not continuing

    logger.info(f"Analysis step finished. Overall success: {overall_success}")
    return overall_success


def launch_dashboard(args):
    """Launch the Streamlit dashboard"""
    if not args.dashboard:
        logger.info("Skipping dashboard launch.")
        return True

    logger.info("Launching dashboard...")
    cmd = [
        "streamlit", "run",
        os.path.join(project_root, "dashboard", "app.py")
    ]
    logger.info(f"Executing: {' '.join(cmd)}")

    try:
        # Run streamlit from the main project root
        if args.background_dashboard:
            # Launch in background, don't wait
            process = subprocess.Popen(cmd, cwd=main_project_root)
            logger.info(f"Dashboard launched in background with PID {process.pid}")
            logger.info("Access the dashboard at http://localhost:8501 (may take a moment to start)")
        else:
            # Launch and wait (blocks pipeline until dashboard is closed)
            logger.info("Dashboard will run in the foreground. Press Ctrl+C in the terminal to stop.")
            subprocess.run(cmd, check=True, cwd=main_project_root)
            logger.info("Dashboard closed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Dashboard execution failed: {e}")
        return False
    except FileNotFoundError:
         logger.error("Error: 'streamlit' command not found. Is Streamlit installed and in PATH?")
         return False
    except Exception as e:
        logger.error(f"Dashboard launch failed: {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description='NHL Performance Analysis Pipeline')

    # Data collection parameters
    parser.add_argument('--seasons', type=str, nargs='+', default=['20232024'], # Default to most recent likely season
                      help='NHL seasons in format YYYYYYYY (e.g., 20232024 20222023)')
    parser.add_argument('--game_types', type=str, nargs='+', default=['R'], # Default to Regular season
                      help='Game types (R=Regular Season, P=Playoffs)')
    parser.add_argument('--player_types', type=str, nargs='+', default=['G', 'D', 'F'],
                      help='Player types for data collection (G=Goalie, D=Defense, F=Forward)')
    parser.add_argument('--efficient', action='store_true',
                      help='Use efficient data collection method (if implemented)')
    parser.add_argument('--skip_data_collection', action='store_true',
                      help='Skip data collection step')

    # Database parameters
    parser.add_argument('--reset_db', action='store_true',
                      help='Reset database (drop tables) before importing data')
    parser.add_argument('--skip_db_setup', action='store_true',
                      help='Skip database setup/import step')
    parser.add_argument('--skip_import', action='store_true',
                      help='Skip data import during DB setup (only create/reset tables)')
    # Removed specific import filters, use main --seasons/--game_types for db_setup filtering

    # Analysis parameters
    parser.add_argument('--skip_analysis', action='store_true',
                      help='Skip analysis step')
    parser.add_argument('--position', type=str, choices=['G', 'D', 'F', 'all'], default='all',
                      help='Position type to analyze (G, D, F, or all)')
    parser.add_argument('--min_games', type=int, default=10, # Default min games for analysis
                      help='Minimum number of games played to include a player in analysis')
    parser.add_argument('--save_analysis_results', action='store_true', default=True, # Save by default
                      help='Save analysis results (plots, stats) to files')

    # Dashboard parameters
    parser.add_argument('--dashboard', action='store_true',
                      help='Launch the Streamlit dashboard after pipeline completion')
    parser.add_argument('--background_dashboard', action='store_true',
                      help='Launch the dashboard in the background and continue')

    # Other parameters
    parser.add_argument('--continue_on_error', action='store_true',
                      help='Continue pipeline execution even if a step fails')

    args = parser.parse_args()

    # --- Pre-run Checks ---
    # Check if docker-compose.yml and .env exist
    if not os.path.exists(os.path.join(main_project_root, 'docker-compose.yml')):
         logger.warning("docker-compose.yml not found in project root. Database container might not be running.")
    if not os.path.exists(os.path.join(main_project_root, '.env')):
         logger.warning(".env file not found in project root. Database connection will likely fail.")


    # Create output directories if they don't exist (relative to main project root)
    os.makedirs(os.path.join(main_project_root, "kopitar", "data"), exist_ok=True)
    os.makedirs(os.path.join(main_project_root, "kopitar", "results"), exist_ok=True)
    # DB files are handled by docker volume now

    logger.info("Starting NHL Performance Analysis Pipeline")
    logger.info(f"Seasons: {args.seasons}")
    logger.info(f"Game types: {args.game_types}")
    logger.info(f"Analysis Position(s): {args.position}")

    # --- Execute Pipeline Steps ---
    pipeline_successful = True

    # Step 1: Data Collection
    if not args.skip_data_collection:
        if not run_data_collection(args):
            pipeline_successful = False
            if not args.continue_on_error: return 1 # Exit if failed and not continuing
    else:
        logger.info("Skipping data collection step.")

    # Step 2: Database Setup
    if not args.skip_db_setup:
        if not setup_database(args):
             pipeline_successful = False
             if not args.continue_on_error: return 1
    else:
        logger.info("Skipping database setup step.")

    # Step 3: Analysis
    if not args.skip_analysis:
        if not run_analysis(args):
             pipeline_successful = False
             if not args.continue_on_error: return 1
    else:
        logger.info("Skipping analysis step.")

    # Step 4: Launch Dashboard (optional)
    # Run dashboard even if previous steps failed, if continue_on_error is set
    if args.dashboard:
        if not launch_dashboard(args):
             pipeline_successful = False
             # Don't necessarily exit if only dashboard fails, but log it
             logger.error("Dashboard launch failed.")

    if pipeline_successful:
        logger.info("NHL Performance Analysis Pipeline finished successfully.")
        return 0
    else:
        logger.warning("NHL Performance Analysis Pipeline finished with one or more errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
