import pandas as pd
import numpy as np
from datetime import timedelta

def add_goalie_workload_metrics(goalie_games_df):
    """
    Add workload metrics for goalies
    
    Args:
        goalie_games_df (DataFrame): DataFrame with goalie game logs
                                    Must have 'player_id', 'date', 'timeOnIce' columns
    
    Returns:
        DataFrame: Original DataFrame with added workload columns
    """
    # Ensure date is datetime
    goalie_games_df = goalie_games_df.copy()
    goalie_games_df['date'] = pd.to_datetime(goalie_games_df['date'])
    
    # Sort by goalie and date
    goalie_games_df = goalie_games_df.sort_values(['player_id', 'date'])
    
    # Calculate days since last game for each goalie
    goalie_games_df['days_since_last_game'] = goalie_games_df.groupby('player_id')['date'].diff().dt.days
    
    # Create back-to-back flag (0 or 1 days between games)
    goalie_games_df['is_back_to_back'] = goalie_games_df['days_since_last_game'].apply(
        lambda x: 1 if x is not None and x <= 1 else 0
    )
    
    # Create a function to convert time string to minutes
    def time_to_minutes(time_str):
        if pd.isna(time_str):
            return 0
        parts = time_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    
    # Convert time on ice to minutes
    if 'timeOnIce' in goalie_games_df.columns:
        goalie_games_df['minutes_played'] = goalie_games_df['timeOnIce'].apply(time_to_minutes)
    
    # Create rolling workload metrics for each goalie
    for player_id in goalie_games_df['player_id'].unique():
        player_mask = goalie_games_df['player_id'] == player_id
        player_data = goalie_games_df.loc[player_mask].copy()
        
        # Calculate games in the last 7, 14, and 30 days
        for idx, row in player_data.iterrows():
            current_date = row['date']
            
            # Last 7 days
            seven_days_ago = current_date - timedelta(days=7)
            games_7d = player_data[
                (player_data['date'] < current_date) & 
                (player_data['date'] >= seven_days_ago)
            ].shape[0]
            goalie_games_df.loc[idx, 'games_last_7d'] = games_7d
            
            # Last 14 days
            fourteen_days_ago = current_date - timedelta(days=14)
            games_14d = player_data[
                (player_data['date'] < current_date) & 
                (player_data['date'] >= fourteen_days_ago)
            ].shape[0]
            goalie_games_df.loc[idx, 'games_last_14d'] = games_14d
            
            # Last 30 days
            thirty_days_ago = current_date - timedelta(days=30)
            games_30d = player_data[
                (player_data['date'] < current_date) & 
                (player_data['date'] >= thirty_days_ago)
            ].shape[0]
            goalie_games_df.loc[idx, 'games_last_30d'] = games_30d
            
            # Minutes played in last 7, 14, and 30 days
            if 'minutes_played' in player_data.columns:
                mins_7d = player_data.loc[
                    (player_data['date'] < current_date) & 
                    (player_data['date'] >= seven_days_ago),
                    'minutes_played'
                ].sum()
                goalie_games_df.loc[idx, 'minutes_last_7d'] = mins_7d
                
                mins_14d = player_data.loc[
                    (player_data['date'] < current_date) & 
                    (player_data['date'] >= fourteen_days_ago),
                    'minutes_played'
                ].sum()
                goalie_games_df.loc[idx, 'minutes_last_14d'] = mins_14d
                
                mins_30d = player_data.loc[
                    (player_data['date'] < current_date) & 
                    (player_data['date'] >= thirty_days_ago),
                    'minutes_played'
                ].sum()
                goalie_games_df.loc[idx, 'minutes_last_30d'] = mins_30d
    
    # Cumulative season games per goalie
    goalie_games_df['season_game_num'] = goalie_games_df.groupby(['player_id', 'season', 'game_type']).cumcount() + 1
    
    # Calculate 5-game rolling average for key metrics
    key_metrics = ['savePercentage', 'evenStrengthSavePercentage', 'powerPlaySavePercentage', 'shortHandedSavePercentage']
    for metric in key_metrics:
        if metric in goalie_games_df.columns:
            goalie_games_df[f'{metric}_5game_avg'] = goalie_games_df.groupby('player_id')[metric].transform(
                lambda x: x.rolling(5, min_periods=1).mean()
            )
    
    return goalie_games_df

def add_skater_workload_metrics(skater_games_df):
    """
    Add workload metrics for skaters (forwards and defensemen)
    
    Args:
        skater_games_df (DataFrame): DataFrame with skater game logs
                                    Must have 'player_id', 'date', 'timeOnIce' columns
    
    Returns:
        DataFrame: Original DataFrame with added workload columns
    """
    # Ensure date is datetime
    skater_games_df = skater_games_df.copy()
    skater_games_df['date'] = pd.to_datetime(skater_games_df['date'])
    
    # Sort by player and date
    skater_games_df = skater_games_df.sort_values(['player_id', 'date'])
    
    # Calculate days since last game for each player
    skater_games_df['days_since_last_game'] = skater_games_df.groupby('player_id')['date'].diff().dt.days
    
    # Create back-to-back flag (0 or 1 days between games)
    skater_games_df['is_back_to_back'] = skater_games_df['days_since_last_game'].apply(
        lambda x: 1 if x is not None and x <= 1 else 0
    )
    
    # Create a function to convert time string to minutes
    def time_to_minutes(time_str):
        if pd.isna(time_str):
            return 0
        parts = time_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    
    # Convert time on ice to minutes
    if 'timeOnIce' in skater_games_df.columns:
        skater_games_df['minutes_played'] = skater_games_df['timeOnIce'].apply(time_to_minutes)
    
    # Create rolling workload metrics for each player
    for player_id in skater_games_df['player_id'].unique():
        player_mask = skater_games_df['player_id'] == player_id
        player_data = skater_games_df.loc[player_mask].copy()
        
        # Calculate games in the last 7, 14, and 30 days
        for idx, row in player_data.iterrows():
            current_date = row['date']
            
            # Last 7 days
            seven_days_ago = current_date - timedelta(days=7)
            games_7d = player_data[
                (player_data['date'] < current_date) & 
                (player_data['date'] >= seven_days_ago)
            ].shape[0]
            skater_games_df.loc[idx, 'games_last_7d'] = games_7d
            
            # Last 14 days
            fourteen_days_ago = current_date - timedelta(days=14)
            games_14d = player_data[
                (player_data['date'] < current_date) & 
                (player_data['date'] >= fourteen_days_ago)
            ].shape[0]
            skater_games_df.loc[idx, 'games_last_14d'] = games_14d
            
            # Last 30 days
            thirty_days_ago = current_date - timedelta(days=30)
            games_30d = player_data[
                (player_data['date'] < current_date) & 
                (player_data['date'] >= thirty_days_ago)
            ].shape[0]
            skater_games_df.loc[idx, 'games_last_30d'] = games_30d
            
            # Minutes played in last 7, 14, and 30 days
            if 'minutes_played' in player_data.columns:
                mins_7d = player_data.loc[
                    (player_data['date'] < current_date) & 
                    (player_data['date'] >= seven_days_ago),
                    'minutes_played'
                ].sum()
                skater_games_df.loc[idx, 'minutes_last_7d'] = mins_7d
                
                mins_14d = player_data.loc[
                    (player_data['date'] < current_date) & 
                    (player_data['date'] >= fourteen_days_ago),
                    'minutes_played'
                ].sum()
                skater_games_df.loc[idx, 'minutes_last_14d'] = mins_14d
                
                mins_30d = player_data.loc[
                    (player_data['date'] < current_date) & 
                    (player_data['date'] >= thirty_days_ago),
                    'minutes_played'
                ].sum()
                skater_games_df.loc[idx, 'minutes_last_30d'] = mins_30d
    
    # Cumulative season games per player
    skater_games_df['season_game_num'] = skater_games_df.groupby(['player_id', 'season', 'game_type']).cumcount() + 1
    
    # Calculate 5-game rolling average for key metrics
    key_metrics = ['goals', 'assists', 'points', 'plusMinus', 'shots', 'hits', 'blocked']
    for metric in key_metrics:
        if metric in skater_games_df.columns:
            skater_games_df[f'{metric}_5game_avg'] = skater_games_df.groupby('player_id')[metric].transform(
                lambda x: x.rolling(5, min_periods=1).mean()
            )
    
    return skater_games_df

def add_performance_relative_to_rest(player_games_df):
    """
    Calculate performance metrics relative to rest days
    
    Args:
        player_games_df (DataFrame): DataFrame with player game logs and workload metrics
                                    Must have 'player_id', 'days_since_last_game', 'position' columns
    
    Returns:
        DataFrame: Original DataFrame with added relative performance columns
    """
    # Create rest day categories
    player_games_df = player_games_df.copy()
    
    def categorize_rest(days):
        if pd.isna(days):
            return 'first_game'
        elif days <= 1:
            return 'back_to_back'
        elif days <= 3:
            return 'short_rest'
        else:
            return 'long_rest'
    
    player_games_df['rest_category'] = player_games_df['days_since_last_game'].apply(categorize_rest)
    
    # Calculate metrics based on position
    for position in player_games_df['position'].unique():
        position_mask = player_games_df['position'] == position
        
        if position == 'G':
            # Goalie metrics
            key_metrics = [
                'savePercentage', 'evenStrengthSavePercentage', 
                'powerPlaySavePercentage', 'shortHandedSavePercentage',
                'shots', 'saves', 'goalsAgainst'
            ]
        elif position in ['D', 'F', 'L', 'R', 'C']:
            # Skater metrics
            key_metrics = [
                'goals', 'assists', 'points', 'plusMinus', 
                'shots', 'hits', 'blocked', 'takeaways', 'giveaways'
            ]
        else:
            continue
        
        # Only use metrics that are present in the dataset
        key_metrics = [m for m in key_metrics if m in player_games_df.columns]
        
        for metric in key_metrics:
            metric_mask = ~player_games_df[metric].isna()
            combined_mask = position_mask & metric_mask
            
            if combined_mask.sum() > 0:
                # Calculate overall average for each player
                player_games_df.loc[combined_mask, f'{metric}_avg'] = player_games_df.loc[combined_mask].groupby('player_id')[metric].transform('mean')
                
                # Calculate performance relative to player's average
                player_games_df.loc[combined_mask, f'{metric}_vs_avg'] = player_games_df.loc[combined_mask, metric] - player_games_df.loc[combined_mask, f'{metric}_avg']
                
                # Calculate average by rest category for each player
                rest_avgs = player_games_df.loc[combined_mask].groupby(['player_id', 'rest_category'])[metric].transform('mean')
                player_games_df.loc[combined_mask, f'{metric}_by_rest'] = rest_avgs
                
                # Calculate performance in back-to-back games vs. long rest
                back_to_back_mask = player_games_df['rest_category'] == 'back_to_back'
                long_rest_mask = player_games_df['rest_category'] == 'long_rest'
                
                for player_id in player_games_df.loc[combined_mask, 'player_id'].unique():
                    player_mask = player_games_df['player_id'] == player_id
                    
                    # Only calculate if player has both back-to-back and long rest games
                    if (back_to_back_mask & player_mask & combined_mask).any() and (long_rest_mask & player_mask & combined_mask).any():
                        b2b_avg = player_games_df.loc[back_to_back_mask & player_mask & combined_mask, metric].mean()
                        long_rest_avg = player_games_df.loc[long_rest_mask & player_mask & combined_mask, metric].mean()
                        
                        player_games_df.loc[player_mask & combined_mask, f'{metric}_b2b_vs_rest'] = b2b_avg - long_rest_avg
    
    return player_games_df

def add_playoff_metrics(player_games_df):
    """
    Add playoff-specific metrics to player game logs
    
    Args:
        player_games_df (DataFrame): DataFrame with player game logs
                                   Must have 'game_type' column
    
    Returns:
        DataFrame: Original DataFrame with added playoff metrics
    """
    player_games_df = player_games_df.copy()
    
    # Create playoff flag
    player_games_df['is_playoff'] = (player_games_df['game_type'] == 'P').astype(int)
    
    # For playoff games, add elimination game flag if available
    if 'playoff_series_status' in player_games_df.columns:
        # Check if it's an elimination game for either team
        player_games_df['is_elimination_game'] = player_games_df['playoff_series_status'].apply(
            lambda x: 1 if isinstance(x, str) and ('leads 3-' in x.lower() or 'tied 3-3' in x.lower()) else 0
        )
    
    # Calculate playoff performance relative to regular season
    # Group by player_id and position
    for player_id in player_games_df['player_id'].unique():
        player_mask = player_games_df['player_id'] == player_id
        player_data = player_games_df.loc[player_mask]
        
        if 'position' not in player_data.columns:
            continue
            
        position = player_data['position'].iloc[0]
        
        # Define metrics based on position
        if position == 'G':
            key_metrics = ['savePercentage', 'goalsAgainst']
        elif position in ['D', 'F', 'L', 'R', 'C']:
            key_metrics = ['goals', 'assists', 'points', 'plusMinus']
        else:
            continue
        
        # Only use metrics that are present in the dataset
        key_metrics = [m for m in key_metrics if m in player_data.columns]
        
        # Calculate regular season averages
        reg_mask = player_data['game_type'] == 'R'
        playoff_mask = player_data['game_type'] == 'P'
        
        if reg_mask.sum() > 0 and playoff_mask.sum() > 0:
            for metric in key_metrics:
                if metric in player_data.columns:
                    reg_avg = player_data.loc[reg_mask, metric].mean()
                    # Add comparison to regular season performance
                    player_games_df.loc[player_mask & playoff_mask, f'{metric}_vs_reg_season'] = player_data.loc[playoff_mask, metric] - reg_avg
    
    return player_games_df

def add_opponent_strength(player_games_df, team_stats_df):
    """
    Add opponent strength metrics
    
    Args:
        player_games_df (DataFrame): DataFrame with player game logs
                                    Must have 'opponent' column
        team_stats_df (DataFrame): DataFrame with team season stats
                                  Must have 'team_name', 'goals_per_game', 'shots_per_game' columns
    
    Returns:
        DataFrame: player_games_df with added opponent strength columns
    """
    player_games_df = player_games_df.copy()
    
    # Ensure team names match between dataframes
    team_stats_df = team_stats_df.copy()
    
    # Map opponent stats to player games
    player_games_df = pd.merge(
        player_games_df,
        team_stats_df,
        left_on=['opponent', 'season', 'game_type'],
        right_on=['team_name', 'season', 'game_type'],
        how='left',
        suffixes=('', '_opponent')
    )
    
    return player_games_df

def add_workload_metrics(player_games_df):
    """
    Add workload metrics for all players based on position
    
    Args:
        player_games_df (DataFrame): DataFrame with player game logs
    
    Returns:
        DataFrame: Original DataFrame with added workload columns
    """
    player_games_df = player_games_df.copy()
    
    # Separate by position
    if 'position' not in player_games_df.columns:
        print("Warning: 'position' column not found. Cannot add position-specific workload metrics.")
        return player_games_df
    
    # Process goalies
    goalie_mask = player_games_df['position'] == 'G'
    if goalie_mask.sum() > 0:
        goalie_df = add_goalie_workload_metrics(player_games_df[goalie_mask])
        
    # Process skaters
    skater_mask = player_games_df['position'].isin(['D', 'F', 'L', 'R', 'C'])
    if skater_mask.sum() > 0:
        skater_df = add_skater_workload_metrics(player_games_df[skater_mask])
    
    # Combine results
    result_dfs = []
    
    if goalie_mask.sum() > 0:
        result_dfs.append(goalie_df)
    
    if skater_mask.sum() > 0:
        result_dfs.append(skater_df)
    
    # Include any other positions that weren't processed
    other_mask = ~(goalie_mask | skater_mask)
    if other_mask.sum() > 0:
        result_dfs.append(player_games_df[other_mask])
    
    if result_dfs:
        return pd.concat(result_dfs).sort_values(['player_id', 'date']).reset_index(drop=True)
    else:
        return player_games_df

def create_analysis_dataset(player_games_df, schedule_df, team_stats_df=None):
    """
    Combine all features into a comprehensive analysis dataset
    
    Args:
        player_games_df (DataFrame): DataFrame with player game logs
        schedule_df (DataFrame): DataFrame with game schedule and travel info
        team_stats_df (DataFrame, optional): DataFrame with team stats
    
    Returns:
        DataFrame: Combined dataset for analysis
    """
    # Step 1: Add workload metrics to player data
    enhanced_player_df = add_workload_metrics(player_games_df)
    
    # Step 2: Add performance relative to rest
    enhanced_player_df = add_performance_relative_to_rest(enhanced_player_df)
    
    # Step 3: Add playoff-specific metrics if applicable
    if 'game_type' in enhanced_player_df.columns:
        enhanced_player_df = add_playoff_metrics(enhanced_player_df)
    
    # Step 4: Add opponent strength if team stats are provided
    if team_stats_df is not None:
        enhanced_player_df = add_opponent_strength(enhanced_player_df, team_stats_df)
    
    # Step 5: Merge with schedule data to add travel information
    if 'game_id' in enhanced_player_df.columns and 'game_id' in schedule_df.columns:
        # Ensure we have matching columns for merging
        merge_cols = ['game_id']
        if 'season' in enhanced_player_df.columns and 'season' in schedule_df.columns:
            merge_cols.append('season')
            
        analysis_df = pd.merge(
            enhanced_player_df,
            schedule_df,
            on=merge_cols,
            how='left',
            suffixes=('', '_schedule')
        )
    else:
        analysis_df = enhanced_player_df
    
    return analysis_df 