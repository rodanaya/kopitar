import sys
import os
import pandas as pd
from datetime import datetime
import argparse
import pickle
import time
from tqdm import tqdm
import logging

# Add the parent directory to the path to import utility modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our updated NHL API wrapper
from utils.nhl_api import (
    get_api_client, get_teams, get_schedule, get_player_stats,
    get_player, get_team_roster, get_standings, get_game_details
)
from utils.geo_utils import add_travel_data
from utils.feature_engineering import create_analysis_dataset

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kopitar_data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def collect_data(seasons, game_types=['R'], player_types=['G', 'D', 'F'], output_dir="../data"):
    """
    Collect and process NHL data for specific seasons, game types, and player types
    
    Args:
        seasons (list): List of seasons in format YYYYYYYY (e.g., ['20212022', '20222023'])
        game_types (list): List of game types (R=Regular Season, P=Playoffs)
        player_types (list): List of player types (G=Goalie, D=Defense, F=Forward)
        output_dir (str): Directory to save data files
    """
    logger.info(f"Collecting data for NHL seasons: {seasons}, game types: {game_types}, player types: {player_types}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create API client
    api_client = get_api_client()
    
    all_data = {
        'teams': [],
        'schedules': [],
        'player_info': [],
        'game_logs': [],
        'injuries': []
    }
    
    for season in seasons:
        logger.info(f"Processing season {season}...")
        
        # Step 1: Get team information
        logger.info("Fetching team information...")
        teams_df = get_teams()
        if not teams_df.empty:
            teams_df['season'] = season  # Add season column
            teams_df.to_csv(f"{output_dir}/teams_{season}.csv", index=False)
            all_data['teams'].append(teams_df)
            logger.info(f"Saved team information for {len(teams_df)} teams")
        else:
            logger.warning(f"No team information found for season {season}")
            # Fallback: manually create team info using standings data
            standings_df = get_standings()
            if not standings_df.empty:
                teams_df = standings_df[['team_id', 'division', 'conference']].copy()
                teams_df['season'] = season
                teams_df.to_csv(f"{output_dir}/teams_{season}.csv", index=False)
                all_data['teams'].append(teams_df)
                logger.info(f"Saved basic team information from standings for {len(teams_df)} teams")
        
        for game_type in game_types:
            game_type_label = 'regular_season' if game_type == 'R' else 'playoffs'
            logger.info(f"Processing {game_type_label} games...")
            
            # Step 2: Get season schedule
            logger.info(f"Fetching {game_type_label} schedule...")
            schedule_df = get_schedule(season=season)
            
            # Filter schedule by game type if needed
            if game_type == 'P':
                schedule_df = schedule_df[schedule_df['game_type'] == 'P']
            elif game_type == 'R':
                schedule_df = schedule_df[schedule_df['game_type'] == 'R']
            
            if not schedule_df.empty:
                # Step 3: Add travel-related information to schedule
                logger.info("Adding travel data to schedule...")
                schedule_with_travel_df = add_travel_data(schedule_df)
                
                # Step 4: Add attendance information for games
                logger.info("Adding attendance data to games...")
                attendance_data = []
                
                for _, game in tqdm(schedule_with_travel_df.iterrows(), 
                                    total=len(schedule_with_travel_df),
                                    desc="Fetching attendance"):
                    game_id = game['game_id']
                    try:
                        # Get game details including attendance
                        game_details = get_game_details(game_id)
                        
                        if game_details and 'attendance' in game_details:
                            attendance_data.append({
                                'game_id': game_id,
                                'attendance': game_details.get('attendance')
                            })
                        
                        # Brief pause to prevent API rate limiting
                        time.sleep(0.1)
                    except Exception as e:
                        logger.warning(f"Error fetching attendance for game {game_id}: {e}")
                
                # Create attendance DataFrame
                if attendance_data:
                    attendance_df = pd.DataFrame(attendance_data)
                    
                    # Merge attendance data with schedule
                    schedule_with_travel_df = schedule_with_travel_df.merge(
                        attendance_df, on='game_id', how='left'
                    )
                    
                    logger.info(f"Added attendance data for {len(attendance_data)} games")
                
                # Save the final schedule with travel and attendance data
                schedule_with_travel_df.to_csv(f"{output_dir}/schedule_{game_type}_{season}.csv", index=False)
                all_data['schedules'].append(schedule_with_travel_df)
                logger.info(f"Saved {game_type_label} schedule with travel and attendance data for {len(schedule_with_travel_df)} games")
            else:
                logger.warning(f"No {game_type_label} schedule data found for season {season}")
            
            # Step 5: Process each player type
            # Get all teams first
            if not teams_df.empty:
                all_player_info = []
                all_game_logs = []
                all_injuries = []
                
                # Process team by team
                for _, team in tqdm(teams_df.iterrows(), total=len(teams_df), desc="Processing teams"):
                    team_id = team.get('team_id')
                    if not team_id:
                        continue
                    
                    # Get team roster
                    roster_df = get_team_roster(team_id, season)
                    
                    if not roster_df.empty:
                        # Filter by player type if needed
                        if player_types and 'position_type' in roster_df.columns:
                            roster_df = roster_df[roster_df['position_type'].isin(player_types)]
                            
                        all_player_info.append(roster_df)
                        
                        # Process player game logs
                        for _, player in roster_df.iterrows():
                            player_id = player.get('player_id')
                            if not player_id:
                                continue
                                
                            # Get player stats for the season
                            player_stats = get_player_stats(player_id, season)
                            
                            # TODO: Process player stats into game logs format
                            # This would require additional processing based on the structure
                            # of the player_stats response from the updated NHL API
                            
                            # For now, we'll just log that we got the player stats
                            if player_stats:
                                logger.info(f"Retrieved stats for player {player.get('full_name')} (ID: {player_id})")
                            
                            # Pause to avoid API rate limits
                            time.sleep(0.2)
                
                # Save player info
                if all_player_info:
                    players_df = pd.concat(all_player_info, ignore_index=True)
                    
                    # Save by position type
                    for pt in player_types:
                        pt_label = 'goalies' if pt == 'G' else ('defensemen' if pt == 'D' else 'forwards')
                        pt_players = players_df[players_df['position_type'] == pt]
                        
                        if not pt_players.empty:
                            pt_players.to_csv(f"{output_dir}/{pt_label}_{game_type}_{season}.csv", index=False)
                            all_data['player_info'].append(pt_players)
                            logger.info(f"Saved information for {len(pt_players)} {pt_label}")
                
                # For now, game logs are limited due to API structure changes
                logger.warning("Game log collection is limited due to API structure changes")
                
            else:
                logger.warning(f"Cannot process players: no team information available for season {season}")
    
    # Combine all data
    combined_data = {}
    for key, data_list in all_data.items():
        if data_list:
            combined_data[key] = pd.concat(data_list).reset_index(drop=True)
        else:
            combined_data[key] = pd.DataFrame()
    
    # Create a combined dataset name based on inputs
    seasons_str = "_".join(seasons)
    game_types_str = "".join(game_types)
    player_types_str = "".join(player_types)
    dataset_name = f"nhl_data_{seasons_str}_{game_types_str}_{player_types_str}"
    
    # Save combined data
    for key, df in combined_data.items():
        if not df.empty:
            df.to_csv(f"{output_dir}/{dataset_name}_{key}.csv", index=False)
            with open(f"{output_dir}/{dataset_name}_{key}.pkl", 'wb') as f:
                pickle.dump(df, f)
    
    logger.info("Data collection complete!")
    
    return combined_data

def collect_data_efficient(seasons, output_dir="../data"):
    """
    Collect NHL data for multiple seasons using a more efficient method
    
    Args:
        seasons (list): List of seasons in format YYYYYYYY (e.g., ['20212022', '20222023'])
        output_dir (str): Directory to save data files
    
    Returns:
        dict: Dictionary with DataFrames for each data type
    """
    logger.info(f"Collecting data for NHL seasons: {seasons} (efficient method)")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # With the updated API, we'll use a simplified approach
    all_data = {
        'teams': [],
        'schedules': [],
        'player_info': [],
        'standings': []
    }
    
    # Create API client
    api_client = get_api_client()
    
    # Process each season
    for season in seasons:
        logger.info(f"Processing season {season}...")
        
        # Get teams
        teams_df = get_teams()
        if not teams_df.empty:
            teams_df['season'] = season
            all_data['teams'].append(teams_df)
            
            # Save teams data
            teams_df.to_csv(f"{output_dir}/teams_{season}.csv", index=False)
            logger.info(f"Saved information for {len(teams_df)} teams")
        
        # Get schedule
        schedule_df = get_schedule(season=season)
        if not schedule_df.empty:
            all_data['schedules'].append(schedule_df)
            
            # Add travel data
            schedule_with_travel_df = add_travel_data(schedule_df)
            
            # Save schedule data
            schedule_with_travel_df.to_csv(f"{output_dir}/schedule_{season}.csv", index=False)
            logger.info(f"Saved schedule with {len(schedule_with_travel_df)} games")
        
        # Get standings
        standings_df = get_standings()
        if not standings_df.empty:
            standings_df['season'] = season
            all_data['standings'].append(standings_df)
            
            # Save standings data
            standings_df.to_csv(f"{output_dir}/standings_{season}.csv", index=False)
            logger.info(f"Saved standings for {len(standings_df)} teams")
    
    # Combine all data
    combined_data = {}
    for key, data_list in all_data.items():
        if data_list:
            combined_data[key] = pd.concat(data_list).reset_index(drop=True)
        else:
            combined_data[key] = pd.DataFrame()
    
    # Create a combined dataset name based on seasons
    seasons_str = "_".join(seasons)
    dataset_name = f"nhl_data_{seasons_str}"
    
    # Save combined data
    for key, df in combined_data.items():
        if not df.empty:
            combined_file = f"{output_dir}/{dataset_name}_{key}.csv"
            df.to_csv(combined_file, index=False)
            
            # Save pickle version
            with open(f"{output_dir}/{dataset_name}_{key}.pkl", 'wb') as f:
                pickle.dump(df, f)
            
            logger.info(f"Saved combined {key} data to {combined_file}")
    
    logger.info("Data collection complete!")
    
    return combined_data

def main():
    parser = argparse.ArgumentParser(description='Collect NHL player data')
    parser.add_argument('--seasons', type=str, nargs='+', default=['20232024'], 
                       help='NHL seasons in format YYYYYYYY (e.g., 20232024 20222023)')
    parser.add_argument('--game_types', type=str, nargs='+', default=['R'],
                       help='Game types (R=Regular Season, P=Playoffs, A=All)')
    parser.add_argument('--player_types', type=str, nargs='+', default=['G', 'D', 'F'],
                       help='Player types (G=Goalie, D=Defense, F=Forward)')
    parser.add_argument('--output_dir', type=str, default='../data',
                       help='Directory to save data files')
    parser.add_argument('--efficient', action='store_true', 
                       help='Use more efficient multi-season data collection method')
    
    args = parser.parse_args()
    
    # Convert 'A' game type to both R and P
    if 'A' in args.game_types:
        args.game_types = ['R', 'P']
    
    if args.efficient:
        collect_data_efficient(args.seasons, args.output_dir)
    else:
        collect_data(args.seasons, args.game_types, args.player_types, args.output_dir)

if __name__ == "__main__":
    main() 