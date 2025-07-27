import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
# Note: RandomForestRegressor, train_test_split, metrics not used in current analysis functions
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_squared_error, r2_score
import pickle
import argparse
import logging

logger = logging.getLogger(__name__)

# Add the parent directory to the path to import utility modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database utility
try:
    from kopitar.database.db_utils import get_db
except ImportError:
    logger.error("Failed to import get_db from kopitar.database.db_utils. Ensure db_utils.py exists and path is correct.")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Removed load_or_create_analysis_dataset function as we now load from DB

def get_key_metrics_by_position(position_type):
    """
    Get the key performance metrics (using snake_case) for analysis based on position type.

    Args:
        position_type (str): 'G' for goalies, 'D' for defensemen, 'F' for forwards

    Returns:
        dict: Dictionary with metric names (snake_case) and labels
    """
    if position_type == 'G':
        return {
            'save_percentage': 'Save Percentage',
            'goals_against': 'Goals Against',
            'saves': 'Saves',
            'time_on_ice_mins': 'Time on Ice (mins)'
        }
    elif position_type == 'D':
        return {
            'points': 'Points',
            'goals': 'Goals',
            'assists': 'Assists',
            'plus_minus': 'Plus/Minus',
            'time_on_ice_mins': 'Time on Ice (mins)',
            'blocks': 'Blocked Shots',
            'hits': 'Hits'
        }
    elif position_type == 'F':
        return {
            'points': 'Points',
            'goals': 'Goals',
            'assists': 'Assists',
            'shots': 'Shots',
            'time_on_ice_mins': 'Time on Ice (mins)',
            'hits': 'Hits',
            'faceoff_percentage': 'Faceoff Win %' # Note: DB schema uses faceoff_percentage
        }
    else:
        # Default metrics for unknown/all skaters
        logger.warning(f"Unknown position_type '{position_type}', using default skater metrics.")
        return {
            'points': 'Points',
            'goals': 'Goals',
            'assists': 'Assists',
            'plus_minus': 'Plus/Minus',
            'time_on_ice_mins': 'Time on Ice (mins)'
        }

def exploratory_analysis(df, position_type, output_dir):
    """
    Perform exploratory analysis on player performance data.
    Uses snake_case column names.

    Args:
        df (DataFrame): Analysis dataset (game logs)
        position_type (str): 'G' for goalies, 'D' for defensemen, 'F' for forwards
        output_dir (str): Directory to save figures
    """
    os.makedirs(output_dir, exist_ok=True)

    if df.empty:
        logger.warning(f"Empty dataset provided for {position_type} players. Skipping exploratory analysis.")
        return

    metrics = get_key_metrics_by_position(position_type)
    available_metrics = [m for m in metrics.keys() if m in df.columns]

    if not available_metrics:
        logger.warning(f"No relevant metrics found in dataset for {position_type} players. Skipping visualizations.")
        summary_file = os.path.join(output_dir, 'dataset_summary.txt')
        with open(summary_file, 'w') as f:
            f.write(f"Dataset Summary for {position_type} players\n")
            f.write(f"Number of records: {len(df)}\n")
            f.write(f"Available columns: {', '.join(df.columns)}\n")
            f.write(f"Required metrics: {', '.join(metrics.keys())}\n")
        logger.info(f"Saved dataset summary to {summary_file}")
        return

    logger.info(f"Creating visualizations for {len(available_metrics)} metrics: {', '.join(available_metrics)}")

    # --- Visualizations (using snake_case columns) ---

    # 1. Distribution
    for metric in available_metrics:
        label = metrics[metric]
        if df[metric].notna().sum() > 0:
            plt.figure(figsize=(10, 6))
            sns.histplot(df[metric].dropna(), kde=True)
            plt.title(f'Distribution of {label}')
            plt.xlabel(label)
            plt.ylabel('Frequency')
            plt.savefig(os.path.join(output_dir, f"{metric}_distribution.png"))
            plt.close()

    # 2. Performance vs. distance traveled
    if 'travel_distance' in df.columns:
        for metric in available_metrics:
            label = metrics[metric]
            # Ensure both columns have enough non-null data points for a meaningful plot
            if df[metric].notna().sum() > 1 and df['travel_distance'].notna().sum() > 1:
                plt.figure(figsize=(10, 6))
                # Add alpha for potentially overlapping points
                sns.scatterplot(x='travel_distance', y=metric, data=df, alpha=0.6)
                plt.title(f'{label} vs. Travel Distance')
                plt.xlabel('Travel Distance (km)')
                plt.ylabel(label)
                plt.savefig(os.path.join(output_dir, f"{metric}_vs_distance.png"))
                plt.close()

    # 3. Performance by home/away
    if 'home_away' in df.columns:
        for metric in available_metrics:
            label = metrics[metric]
            if df[metric].notna().sum() > 0:
                plt.figure(figsize=(10, 6))
                sns.boxplot(x='home_away', y=metric, data=df)
                plt.title(f'{label} by Game Location')
                plt.xlabel('Game Location')
                plt.ylabel(label)
                plt.savefig(os.path.join(output_dir, f"{metric}_by_location.png"))
                plt.close()

    # 4. Performance by back-to-back status
    # Ensure back_to_back column is boolean type for correct plotting
    if 'back_to_back' in df.columns:
        df['back_to_back'] = df['back_to_back'].astype(bool) # Convert if not already boolean
        for metric in available_metrics:
            label = metrics[metric]
            if df[metric].notna().sum() > 0:
                plt.figure(figsize=(10, 6))
                sns.boxplot(x='back_to_back', y=metric, data=df)
                plt.title(f'{label} by Back-to-Back Status')
                plt.xlabel('Is Back-to-Back Game (True/False)')
                plt.ylabel(label)
                plt.savefig(os.path.join(output_dir, f"{metric}_by_b2b.png"))
                plt.close()

    # 5. Regular Season vs Playoff Performance
    if 'is_playoff' in df.columns:
         df['is_playoff'] = df['is_playoff'].astype(bool) # Convert if not already boolean
         for metric in available_metrics:
            label = metrics[metric]
            if df[metric].notna().sum() > 0:
                plt.figure(figsize=(10, 6))
                sns.boxplot(x='is_playoff', y=metric, data=df)
                plt.title(f'{label} - Regular Season (False) vs Playoffs (True)')
                plt.xlabel('Playoff Game (True/False)')
                plt.ylabel(label)
                plt.savefig(os.path.join(output_dir, f"{metric}_reg_vs_playoff.png"))
                plt.close()

    # 6. Performance in elimination games (only for playoff games)
    if 'elimination_game' in df.columns and 'is_playoff' in df.columns:
        playoff_df = df[df['is_playoff'] == True].copy()
        if not playoff_df.empty and playoff_df['elimination_game'].notna().sum() > 0:
            playoff_df['elimination_game'] = playoff_df['elimination_game'].astype(bool)
            for metric in available_metrics:
                label = metrics[metric]
                if playoff_df[metric].notna().sum() > 0:
                    plt.figure(figsize=(10, 6))
                    sns.boxplot(x='elimination_game', y=metric, data=playoff_df)
                    plt.title(f'{label} in Elimination (True) vs Non-Elimination (False) Games')
                    plt.xlabel('Elimination Game (True/False)')
                    plt.ylabel(label)
                    plt.savefig(os.path.join(output_dir, f"{metric}_elimination_games.png"))
                    plt.close()

    logger.info(f"Exploratory analysis complete for {position_type}. Figures saved to {output_dir}")


def statistical_analysis(df, position_type):
    """
    Perform statistical analysis on player performance data.
    Uses snake_case column names.

    Args:
        df (DataFrame): Analysis dataset
        position_type (str): 'G' for goalies, 'D' for defensemen, 'F' for forwards

    Returns:
        dict: Dictionary of analysis results
    """
    results = {}
    if df.empty:
        logger.warning(f"Empty dataset provided for {position_type} players. Skipping statistical analysis.")
        return results

    metrics = get_key_metrics_by_position(position_type)
    available_metrics = [m for m in metrics.keys() if m in df.columns and df[m].notna().sum() > 1] # Need at least 2 points for stats

    if not available_metrics:
        logger.warning(f"No relevant metrics with sufficient data found for {position_type} players. Skipping statistical analysis.")
        return results

    primary_metric = available_metrics[0]
    logger.info(f"Using {primary_metric} ({metrics[primary_metric]}) as primary metric for statistical tests")

    # Ensure boolean columns are boolean type
    if 'back_to_back' in df.columns: df['back_to_back'] = df['back_to_back'].astype(bool)
    if 'is_playoff' in df.columns: df['is_playoff'] = df['is_playoff'].astype(bool)

    # 1. T-test: Back-to-back vs. Rested
    if 'back_to_back' in df.columns:
        b2b_games = df[df['back_to_back'] == True][primary_metric].dropna()
        rested_games = df[df['back_to_back'] == False][primary_metric].dropna()
        if len(b2b_games) >= 2 and len(rested_games) >= 2: # Need at least 2 samples per group for t-test
            t_stat, p_value = stats.ttest_ind(b2b_games, rested_games, equal_var=False, nan_policy='omit')
            results['b2b_vs_rested'] = {
                'metric': primary_metric, 't_statistic': t_stat, 'p_value': p_value,
                'b2b_mean': b2b_games.mean(), 'rested_mean': rested_games.mean(),
                'difference': b2b_games.mean() - rested_games.mean()
            }
            logger.info(f"\nT-test (B2B vs Rested) for {metrics[primary_metric]}: p-value={p_value:.4f}, diff={results['b2b_vs_rested']['difference']:.4f}")

    # 2. T-test: Playoff vs. Regular Season
    if 'is_playoff' in df.columns:
        playoff_games = df[df['is_playoff'] == True][primary_metric].dropna()
        regular_games = df[df['is_playoff'] == False][primary_metric].dropna()
        if len(playoff_games) >= 2 and len(regular_games) >= 2:
            t_stat, p_value = stats.ttest_ind(playoff_games, regular_games, equal_var=False, nan_policy='omit')
            results['playoff_vs_regular'] = {
                'metric': primary_metric, 't_statistic': t_stat, 'p_value': p_value,
                'playoff_mean': playoff_games.mean(), 'regular_mean': regular_games.mean(),
                'difference': playoff_games.mean() - regular_games.mean()
            }
            logger.info(f"T-test (Playoff vs Regular) for {metrics[primary_metric]}: p-value={p_value:.4f}, diff={results['playoff_vs_regular']['difference']:.4f}")

    # 3. T-test: Home vs. Away
    if 'home_away' in df.columns:
        home_games = df[df['home_away'] == 'Home'][primary_metric].dropna()
        away_games = df[df['home_away'] == 'Away'][primary_metric].dropna()
        if len(home_games) >= 2 and len(away_games) >= 2:
            t_stat, p_value = stats.ttest_ind(home_games, away_games, equal_var=False, nan_policy='omit')
            results['home_vs_away'] = {
                'metric': primary_metric, 't_statistic': t_stat, 'p_value': p_value,
                'home_mean': home_games.mean(), 'away_mean': away_games.mean(),
                'difference': home_games.mean() - away_games.mean()
            }
            logger.info(f"T-test (Home vs Away) for {metrics[primary_metric]}: p-value={p_value:.4f}, diff={results['home_vs_away']['difference']:.4f}")

    # 4. Correlation: Travel Distance vs. Primary Metric
    if 'travel_distance' in df.columns:
        valid_data = df[['travel_distance', primary_metric]].dropna()
        if len(valid_data) >= 2:
            # Use Pearson correlation
            correlation, p_value = stats.pearsonr(valid_data['travel_distance'], valid_data[primary_metric])
            results['travel_correlation'] = {
                'metric': primary_metric, 'correlation': correlation, 'p_value': p_value
            }
            logger.info(f"Correlation (Travel vs {metrics[primary_metric]}): r={correlation:.4f}, p-value={p_value:.4f}")

    logger.info(f"\nCompleted statistical analysis for {position_type} position ({len(results)} tests)")
    return results


def analyze_player_trends(df, position_type, min_games=10):
    """
    Analyze individual player trends. Uses snake_case column names.

    Args:
        df (DataFrame): Analysis dataset
        position_type (str): 'G' for goalies, 'D' for defensemen, 'F' for forwards
        min_games (int): Minimum number of games played to include a player

    Returns:
        DataFrame: Player statistics summary
    """
    if df.empty:
        logger.warning(f"Empty dataset provided for {position_type} players. Skipping player trends analysis.")
        return pd.DataFrame()
    if 'player_id' not in df.columns:
        logger.warning("No player_id column found. Cannot analyze individual player trends.")
        return pd.DataFrame()

    metrics = get_key_metrics_by_position(position_type)
    available_metrics = [m for m in metrics.keys() if m in df.columns and df[m].notna().sum() > 0]

    if not available_metrics:
        logger.warning(f"No relevant metrics found for {position_type} players. Skipping player trends analysis.")
        return pd.DataFrame()

    logger.info(f"Analyzing trends for {position_type} players using {len(available_metrics)} metrics")

    # Ensure boolean columns are boolean type
    if 'back_to_back' in df.columns: df['back_to_back'] = df['back_to_back'].astype(bool)
    if 'is_playoff' in df.columns: df['is_playoff'] = df['is_playoff'].astype(bool)

    player_stats = []
    grouped_data = df.groupby('player_id')

    for player_id, player_df in grouped_data:
        if len(player_df) < min_games:
            continue

        player_name = player_df['player_name'].iloc[0] if 'player_name' in player_df.columns else f"Player {player_id}"
        team_name = player_df['team_name'].iloc[0] if 'team_name' in player_df.columns else None

        player_data = {
            'player_id': player_id, 'player_name': player_name, 'team_name': team_name,
            'position_type': position_type, 'games_played': len(player_df)
        }

        for metric in available_metrics:
            metric_data = player_df[metric].dropna()
            if metric_data.empty: continue

            player_data[f'{metric}_mean'] = metric_data.mean()

            if 'home_away' in player_df.columns:
                home_val = player_df.loc[player_df['home_away'] == 'Home', metric].mean()
                away_val = player_df.loc[player_df['home_away'] == 'Away', metric].mean()
                player_data[f'{metric}_home'] = home_val
                player_data[f'{metric}_away'] = away_val
                if pd.notna(home_val) and pd.notna(away_val):
                    player_data[f'{metric}_home_away_diff'] = home_val - away_val

            if 'back_to_back' in player_df.columns:
                b2b_val = player_df.loc[player_df['back_to_back'] == True, metric].mean()
                rested_val = player_df.loc[player_df['back_to_back'] == False, metric].mean()
                player_data[f'{metric}_b2b'] = b2b_val
                player_data[f'{metric}_rested'] = rested_val
                if pd.notna(b2b_val) and pd.notna(rested_val):
                    player_data[f'{metric}_b2b_effect'] = b2b_val - rested_val

            if 'is_playoff' in player_df.columns:
                regular_val = player_df.loc[player_df['is_playoff'] == False, metric].mean()
                playoff_games = player_df[player_df['is_playoff'] == True]
                playoff_val = playoff_games[metric].mean() if len(playoff_games) >= 3 else np.nan # Require min 3 playoff games

                player_data[f'{metric}_regular'] = regular_val
                player_data[f'{metric}_playoff'] = playoff_val
                if pd.notna(regular_val) and pd.notna(playoff_val):
                    player_data[f'{metric}_playoff_diff'] = playoff_val - regular_val

        player_stats.append(player_data)

    if not player_stats:
        logger.warning(f"No players with at least {min_games} games found for position type {position_type}")
        return pd.DataFrame()

    player_stats_df = pd.DataFrame(player_stats)

    # Sort by primary metric mean (desc for most, asc for goals_against) and games played
    primary_metric = available_metrics[0]
    sort_ascending = True if primary_metric == 'goals_against' else False
    sort_cols = [f"{primary_metric}_mean", 'games_played']
    if f"{primary_metric}_mean" in player_stats_df.columns:
         player_stats_df = player_stats_df.sort_values(
             sort_cols, ascending=[sort_ascending, False]
         ).reset_index(drop=True)

    logger.info(f"Analyzed {len(player_stats_df)} {position_type} players with at least {min_games} games")
    return player_stats_df


def main():
    """Main function to run the player performance analysis from database"""
    parser = argparse.ArgumentParser(description='Analyze NHL player performance from Database')
    # Removed --data-file, added DB filters
    parser.add_argument('--position', type=str, choices=['G', 'D', 'F'], required=True,
                        help='Position type to analyze: G (goalies), D (defensemen), F (forwards)')
    parser.add_argument('--season', type=str, help='Filter analysis by season (e.g., 20232024)')
    parser.add_argument('--game_type', type=str, choices=['R', 'P'], help='Filter analysis by game type (R=Regular, P=Playoffs)')
    parser.add_argument('--output-dir', type=str, default='../results', # Changed default relative path
                        help='Directory to save analysis results')
    parser.add_argument('--min-games', type=int, default=10,
                        help='Minimum number of games played to include a player in individual analysis')
    parser.add_argument('--save-results', action='store_true',
                        help='Save analysis results (plots, stats) to files')

    args = parser.parse_args()

    # --- Database Connection ---
    try:
        db = get_db()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # --- Fetch Data ---
    logger.info(f"Fetching data for position: {args.position}, season: {args.season}, game_type: {args.game_type}")
    position_df = pd.DataFrame() # Initialize empty DataFrame
    try:
        if args.position == 'G':
            position_df = db.get_goalie_game_logs(
                season=args.season,
                game_type=args.game_type
                # Add other filters like date_from, date_to if needed later
            )
        elif args.position in ['D', 'F']:
             # Fetch all skaters first, then filter by position if needed,
             # or modify get_skater_game_logs to accept position_type
             skater_df = db.get_skater_game_logs(
                 season=args.season,
                 game_type=args.game_type
             )
             # Filter by specific position if needed (D or F)
             # This requires the 'position' column from the DB query
             if 'position' in skater_df.columns:
                 if args.position == 'D':
                     position_df = skater_df[skater_df['position'] == 'D'].copy()
                 elif args.position == 'F':
                     # Forwards can be C, L, R
                     position_df = skater_df[skater_df['position'].isin(['C', 'L', 'R'])].copy()
             else:
                 logger.warning("Could not filter by specific D/F position, 'position' column missing from get_skater_game_logs result.")
                 position_df = skater_df # Use all skaters if position column is missing

        else:
             logger.error(f"Invalid position specified: {args.position}")
             sys.exit(1)

    except Exception as e:
        logger.error(f"Error fetching data from database: {e}")
        sys.exit(1)

    if position_df.empty:
        logger.warning(f"No data found for the specified criteria (Position: {args.position}, Season: {args.season}, Type: {args.game_type}). Exiting.")
        sys.exit(0)

    logger.info(f"Fetched {len(position_df)} game log records for analysis.")

    # --- Analysis ---
    # Create position-specific output directory relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_output_dir = os.path.abspath(os.path.join(script_dir, args.output_dir))
    position_output_dir = os.path.join(base_output_dir, args.position)
    os.makedirs(position_output_dir, exist_ok=True)
    logger.info(f"Results will be saved to: {position_output_dir}")


    # Exploratory analysis
    exploratory_analysis(position_df, args.position, position_output_dir)

    # Statistical analysis
    results = statistical_analysis(position_df, args.position)

    # Player trends analysis
    player_stats = analyze_player_trends(position_df, args.position, args.min_games)

    # Save results if requested
    if args.save_results:
        # Save player stats
        if not player_stats.empty:
            player_stats_file = os.path.join(position_output_dir, 'player_stats.csv')
            try:
                player_stats.to_csv(player_stats_file, index=False)
                logger.info(f"Saved player stats to {player_stats_file}")
            except Exception as e:
                logger.error(f"Error saving player stats CSV: {e}")

        # Save statistical analysis results
        if results:
            results_file = os.path.join(position_output_dir, 'statistical_analysis.pkl')
            try:
                with open(results_file, 'wb') as f:
                    pickle.dump(results, f)
                logger.info(f"Saved statistical analysis results to {results_file}")
            except Exception as e:
                logger.error(f"Error saving statistical analysis pickle: {e}")

    logger.info("\nAnalysis complete!")

if __name__ == "__main__":
    main()
