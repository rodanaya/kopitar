import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import pickle
import argparse
import logging

# Add the parent directory to the path to import utility modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database utility
try:
    from kopitar.database.db_utils import get_db
except ImportError:
    # Use basic logging if full setup hasn't happened yet
    logging.basicConfig(level=logging.ERROR)
    logging.error("Failed to import get_db from kopitar.database.db_utils. Ensure db_utils.py exists and path is correct.")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Consider renaming log file specific to this script
        logging.FileHandler("goalie_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Removed load_analysis_dataset function

def basic_exploratory_analysis(df, output_dir):
    """
    Perform basic exploratory analysis on goalie performance data.
    Uses snake_case column names.

    Args:
        df (DataFrame): Analysis dataset (goalie game logs)
        output_dir (str): Directory to save figures
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Starting exploratory analysis for goalies. Saving figures to {output_dir}")

    # Use the primary metric: save_percentage
    primary_metric = 'save_percentage'
    metric_label = 'Save Percentage'

    # Filter out rows with missing primary metric
    df_filtered = df.dropna(subset=[primary_metric]).copy() # Use copy to avoid SettingWithCopyWarning

    if df_filtered.empty:
        logger.warning("No valid goalie data (with save_percentage) found. Skipping exploratory analysis.")
        return

    # Ensure boolean columns are boolean type
    if 'is_back_to_back' in df_filtered.columns: df_filtered['is_back_to_back'] = df_filtered['is_back_to_back'].astype(bool)
    if 'is_playoff' in df_filtered.columns: df_filtered['is_playoff'] = df_filtered['is_playoff'].astype(bool)

    # 1. Distribution of save percentage
    plt.figure(figsize=(10, 6))
    sns.histplot(df_filtered[primary_metric], kde=True)
    plt.title(f'Distribution of Goalie {metric_label}')
    plt.xlabel(metric_label)
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, f"{primary_metric}_distribution.png"))
    plt.close()

    # 2. Save percentage vs. distance traveled
    if 'distance_traveled' in df_filtered.columns and df_filtered['distance_traveled'].notna().sum() > 1:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='distance_traveled', y=primary_metric, data=df_filtered, alpha=0.6)
        plt.title(f'{metric_label} vs. Distance Traveled')
        plt.xlabel('Distance Traveled (km)')
        plt.ylabel(metric_label)
        plt.savefig(os.path.join(output_dir, f"{primary_metric}_vs_distance.png"))
        plt.close()

    # 3. Save percentage by home/away (using home_away column)
    if 'home_away' in df_filtered.columns:
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='home_away', y=primary_metric, data=df_filtered)
        plt.title(f'{metric_label} by Game Location')
        plt.xlabel('Game Location (Home/Away)')
        plt.ylabel(metric_label)
        plt.savefig(os.path.join(output_dir, f"{primary_metric}_by_location.png"))
        plt.close()

    # 4. Save percentage by back-to-back status (using is_back_to_back)
    if 'is_back_to_back' in df_filtered.columns:
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='is_back_to_back', y=primary_metric, data=df_filtered)
        plt.title(f'{metric_label} by Back-to-Back Status')
        plt.xlabel('Is Back-to-Back Game (True/False)')
        plt.ylabel(metric_label)
        plt.savefig(os.path.join(output_dir, f"{primary_metric}_by_b2b.png"))
        plt.close()

    # 5. Save percentage vs. workload (e.g., workload_7day)
    if 'workload_7day' in df_filtered.columns and df_filtered['workload_7day'].notna().sum() > 1:
        plt.figure(figsize=(10, 6))
        # Use scatterplot for continuous workload metric
        sns.scatterplot(x='workload_7day', y=primary_metric, data=df_filtered, alpha=0.6)
        plt.title(f'{metric_label} vs. Workload (Last 7 Days)')
        plt.xlabel('Workload Metric (Last 7 Days)') # Clarify what this metric represents if possible
        plt.ylabel(metric_label)
        plt.savefig(os.path.join(output_dir, f"{primary_metric}_vs_workload_7d.png"))
        plt.close()

    # 6. Save percentage by timezone change direction (using timezone_diff)
    if 'timezone_diff' in df_filtered.columns and df_filtered['timezone_diff'].notna().sum() > 0:
        # Create timezone direction category
        df_filtered['timezone_direction'] = 'None'
        df_filtered.loc[df_filtered['timezone_diff'] > 0, 'timezone_direction'] = 'Eastward'
        df_filtered.loc[df_filtered['timezone_diff'] < 0, 'timezone_direction'] = 'Westward'

        plt.figure(figsize=(10, 6))
        sns.boxplot(x='timezone_direction', y=primary_metric, data=df_filtered)
        plt.title(f'{metric_label} by Timezone Change Direction')
        plt.xlabel('Timezone Change Direction')
        plt.ylabel(metric_label)
        plt.savefig(os.path.join(output_dir, f"{primary_metric}_by_timezone_direction.png"))
        plt.close()

    # 7. Save percentage by travel direction
    if 'travel_direction' in df_filtered.columns and df_filtered['travel_direction'].notna().nunique() > 1:
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='travel_direction', y=primary_metric, data=df_filtered)
        plt.title(f'{metric_label} by Travel Direction')
        plt.xlabel('Travel Direction')
        plt.ylabel(metric_label)
        plt.savefig(os.path.join(output_dir, f"{primary_metric}_by_travel_direction.png"))
        plt.close()

    logger.info(f"Exploratory analysis complete. Figures saved to {output_dir}")


def statistical_analysis(df):
    """
    Perform statistical analysis on goalie performance data.
    Uses snake_case column names.

    Args:
        df (DataFrame): Analysis dataset (goalie game logs)

    Returns:
        dict: Dictionary of analysis results
    """
    results = {}
    primary_metric = 'save_percentage'
    metric_label = 'Save Percentage'

    # Filter out rows with missing primary metric and ensure enough data
    df_filtered = df.dropna(subset=[primary_metric]).copy()
    if len(df_filtered) < 5: # Need some minimum data for meaningful stats
        logger.warning(f"Insufficient valid goalie data (n={len(df_filtered)}) for statistical analysis.")
        return results

    logger.info(f"Starting statistical analysis for goalies using '{primary_metric}'")

    # Ensure boolean columns are boolean type
    if 'is_back_to_back' in df_filtered.columns: df_filtered['is_back_to_back'] = df_filtered['is_back_to_back'].astype(bool)
    if 'is_playoff' in df_filtered.columns: df_filtered['is_playoff'] = df_filtered['is_playoff'].astype(bool)

    # 1. T-test: Back-to-back vs. Rested (using is_back_to_back)
    if 'is_back_to_back' in df_filtered.columns:
        b2b_games = df_filtered[df_filtered['is_back_to_back'] == True][primary_metric].dropna()
        rested_games = df_filtered[df_filtered['is_back_to_back'] == False][primary_metric].dropna()
        if len(b2b_games) >= 2 and len(rested_games) >= 2:
            t_stat, p_value = stats.ttest_ind(b2b_games, rested_games, equal_var=False, nan_policy='omit')
            results['b2b_vs_rested'] = {
                'metric': primary_metric, 't_statistic': t_stat, 'p_value': p_value,
                'b2b_mean': b2b_games.mean(), 'rested_mean': rested_games.mean(),
                'difference': b2b_games.mean() - rested_games.mean()
            }
            logger.info(f"\nT-test (B2B vs Rested) for {metric_label}: p-value={p_value:.4f}, diff={results['b2b_vs_rested']['difference']:.4f}")

    # 2. Correlation analysis (using snake_case columns)
    corr_columns = [
        primary_metric, 'days_since_last_game', 'distance_traveled',
        'timezone_diff', 'workload_7day', 'workload_30day' # Use workload columns if available
    ]
    corr_columns = [col for col in corr_columns if col in df_filtered.columns and df_filtered[col].notna().sum() > 1]

    if len(corr_columns) > 1:
        try:
            corr_matrix = df_filtered[corr_columns].corr()
            results['correlation_matrix'] = corr_matrix.to_dict()
            logger.info(f"\nCorrelation Matrix with {metric_label}:")
            logger.info(corr_matrix[primary_metric].sort_values(ascending=False))
        except Exception as e:
            logger.warning(f"Could not compute correlation matrix: {e}")


    # 3. Linear regression model for save percentage (using snake_case)
    features = []
    if 'is_back_to_back' in df_filtered.columns: features.append('is_back_to_back')
    if 'distance_traveled' in df_filtered.columns: features.append('distance_traveled')
    if 'days_since_last_game' in df_filtered.columns: features.append('days_since_last_game')
    if 'home_away' in df_filtered.columns:
        # Create dummy variable for home/away
        df_filtered['is_home'] = (df_filtered['home_away'] == 'Home').astype(int)
        features.append('is_home')
    if 'workload_7day' in df_filtered.columns: features.append('workload_7day')
    if 'timezone_diff' in df_filtered.columns: features.append('timezone_diff')
    if 'opponent_strength' in df_filtered.columns: features.append('opponent_strength') # Add if available

    # Keep only features that actually exist in the DataFrame
    features = [f for f in features if f in df_filtered.columns and df_filtered[f].notna().sum() > 0]

    if features:
        formula = f"{primary_metric} ~ " + ' + '.join(features)
        # Drop rows with NaNs in any of the model's columns
        model_data = df_filtered[[primary_metric] + features].dropna()

        if len(model_data) > len(features) + 1: # Need enough data points
            try:
                model = ols(formula, data=model_data).fit()
                results['regression_model'] = {
                    'formula': formula, 'r_squared': model.rsquared, 'adjusted_r_squared': model.rsquared_adj,
                    'p_value': model.f_pvalue,
                    'coefficients': model.params.to_dict(),
                    'p_values': model.pvalues.to_dict()
                }
                logger.info(f"\nLinear Regression Analysis (Formula: {formula}):")
                logger.info(f"R-squared: {model.rsquared:.4f}, Adj. R-squared: {model.rsquared_adj:.4f}, Model p-value: {model.f_pvalue:.4f}")
                logger.info(f"Coefficients:\n{model.params}")
            except Exception as e:
                logger.error(f"Error fitting regression model ({formula}): {e}")
        else:
            logger.warning(f"Insufficient data (n={len(model_data)}) to fit regression model: {formula}")
    else:
        logger.warning("No valid features found for regression model.")

    logger.info(f"\nCompleted statistical analysis for goalies ({len(results)} tests)")
    return results


def analyze_top_goalies(df, min_games=20):
    """
    Analyze performance of top goalies under different conditions.
    Uses snake_case column names.

    Args:
        df (DataFrame): Analysis dataset (goalie game logs)
        min_games (int): Minimum number of games played to be included
    """
    primary_metric = 'save_percentage'
    metric_label = 'Save Percentage'

    if df.empty or 'player_name' not in df.columns or primary_metric not in df.columns:
        logger.warning("Insufficient data for top goalie analysis.")
        return

    logger.info(f"\nAnalyzing top goalies (min {min_games} games)")

    # Filter out goalies with too few games
    goalie_counts = df['player_name'].value_counts()
    qualified_goalies = goalie_counts[goalie_counts >= min_games].index.tolist()
    df_qualified = df[df['player_name'].isin(qualified_goalies)].copy()

    if df_qualified.empty:
        logger.warning(f"No goalies found with at least {min_games} games.")
        return

    # Ensure boolean columns are boolean type
    if 'is_back_to_back' in df_qualified.columns: df_qualified['is_back_to_back'] = df_qualified['is_back_to_back'].astype(bool)

    # Calculate average save percentage for each goalie
    goalie_overall = df_qualified.groupby('player_name')[primary_metric].agg(['mean', 'count']).reset_index()
    goalie_overall = goalie_overall.rename(columns={'mean': f'{primary_metric}_mean', 'count': 'games_played'})
    goalie_overall = goalie_overall.sort_values(f'{primary_metric}_mean', ascending=False)

    logger.info(f"Top Goalies by Overall {metric_label} (min {min_games} games):")
    for i, row in goalie_overall.head(10).iterrows():
        logger.info(f"{i+1}. {row['player_name']}: {row[f'{primary_metric}_mean']:.4f} ({row['games_played']} games)")

    # Calculate back-to-back vs. rested performance
    if 'is_back_to_back' in df_qualified.columns:
        try:
            b2b_performance = df_qualified.pivot_table(
                index='player_name', columns='is_back_to_back', values=primary_metric, aggfunc='mean'
            ).reset_index()
            # Rename columns (False -> rested, True -> back_to_back)
            b2b_performance = b2b_performance.rename(columns={False: 'rested', True: 'back_to_back'})

            if 'rested' in b2b_performance.columns and 'back_to_back' in b2b_performance.columns:
                b2b_performance['difference'] = b2b_performance['back_to_back'] - b2b_performance['rested']
                b2b_performance = b2b_performance.sort_values('difference', ascending=False, na_position='last')

                logger.info(f"\nGoalies Who Perform Best in Back-to-Back Games (vs. Rested, {metric_label}):")
                for i, row in b2b_performance.head(5).iterrows():
                    if pd.notna(row['difference']):
                        logger.info(f"{i+1}. {row['player_name']}: +{row['difference']:.4f} ({row['back_to_back']:.4f} vs {row['rested']:.4f})")

                b2b_performance = b2b_performance.sort_values('difference', ascending=True, na_position='last')
                logger.info(f"\nGoalies Who Struggle Most in Back-to-Back Games (vs. Rested, {metric_label}):")
                for i, row in b2b_performance.head(5).iterrows():
                     if pd.notna(row['difference']):
                        logger.info(f"{i+1}. {row['player_name']}: {row['difference']:.4f} ({row['back_to_back']:.4f} vs {row['rested']:.4f})")
            else:
                 logger.warning("Could not calculate B2B difference, missing 'rested' or 'back_to_back' columns after pivot.")

        except Exception as e:
            logger.warning(f"Could not calculate back-to-back performance breakdown: {e}")


    # Analyze performance by travel distance
    if 'distance_traveled' in df_qualified.columns and df_qualified['distance_traveled'].notna().sum() > 0:
        try:
            # Create distance categories
            df_qualified['distance_category'] = pd.cut(
                df_qualified['distance_traveled'],
                bins=[-1, 500, 1500, 3000, float('inf')], # Start bin at -1 to include 0
                labels=['Short (<500km)', 'Medium (500-1500km)', 'Long (1500-3000km)', 'Very Long (>3000km)']
            )

            distance_performance = df_qualified.pivot_table(
                index='player_name', columns='distance_category', values=primary_metric, aggfunc='mean'
            ).reset_index()

            # Calculate performance drop for long travel vs short
            long_col = 'Long (1500-3000km)'
            short_col = 'Short (<500km)'
            if long_col in distance_performance.columns and short_col in distance_performance.columns:
                distance_performance['long_vs_short_diff'] = distance_performance[long_col] - distance_performance[short_col]
                distance_performance = distance_performance.sort_values('long_vs_short_diff', ascending=False, na_position='last')

                logger.info(f"\nGoalies Who Handle Long Travel Best ({long_col} vs. {short_col}, {metric_label}):")
                for i, row in distance_performance.head(5).iterrows():
                    if pd.notna(row['long_vs_short_diff']):
                        logger.info(f"{i+1}. {row['player_name']}: {row['long_vs_short_diff']:.4f}")
            else:
                logger.warning(f"Could not calculate long vs short travel difference, missing '{long_col}' or '{short_col}' columns after pivot.")

        except Exception as e:
            logger.warning(f"Could not calculate performance by travel distance: {e}")


def main():
    """Main function to run the goalie performance analysis from database"""
    parser = argparse.ArgumentParser(description='Analyze NHL Goaltender performance from Database')
    # Removed --data_file, added DB filters
    # Position is implicitly 'G' for this script
    parser.add_argument('--season', type=str, help='Filter analysis by season (e.g., 20232024)')
    parser.add_argument('--game_type', type=str, choices=['R', 'P'], help='Filter analysis by game type (R=Regular, P=Playoffs)')
    parser.add_argument('--output-dir', type=str, default='../results/G', # Specific default for goalies
                        help='Directory to save analysis results')
    parser.add_argument('--min-games', type=int, default=20, # Default min games for goalie analysis
                        help='Minimum number of games played to include a goalie in individual analysis')
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
    logger.info(f"Fetching goalie data for season: {args.season}, game_type: {args.game_type}")
    try:
        goalie_df = db.get_goalie_game_logs(
            season=args.season,
            game_type=args.game_type
        )
    except Exception as e:
        logger.error(f"Error fetching goalie data from database: {e}")
        sys.exit(1)

    if goalie_df.empty:
        logger.warning(f"No goalie data found for the specified criteria (Season: {args.season}, Type: {args.game_type}). Exiting.")
        sys.exit(0)

    logger.info(f"Fetched {len(goalie_df)} goalie game log records for analysis.")

    # --- Analysis ---
    # Create output directory relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.abspath(os.path.join(script_dir, args.output_dir))
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Results will be saved to: {output_dir}")

    # Basic exploratory analysis
    basic_exploratory_analysis(goalie_df, output_dir)

    # Statistical analysis
    results = statistical_analysis(goalie_df)

    # Analyze top goalies
    analyze_top_goalies(goalie_df, min_games=args.min_games)

    # Save statistical results if requested and available
    if args.save_results and results:
        results_file = os.path.join(output_dir, 'goalie_statistical_analysis.pkl')
        try:
            with open(results_file, 'wb') as f:
                pickle.dump(results, f)
            logger.info(f"Saved statistical analysis results to {results_file}")
        except Exception as e:
            logger.error(f"Error saving statistical analysis pickle: {e}")

    logger.info("\nGoalie analysis complete!")

if __name__ == "__main__":
    main()
