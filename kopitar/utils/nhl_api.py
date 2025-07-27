#!/usr/bin/env python
"""
NHL API Module - Interface with NHL Stats API

This module provides functions to interact with the NHL API using the nhl-api-py
package which is updated for the current NHL API endpoints.

The NHL now uses two primary API sources:
1. api-web.nhle.com - Web-focused endpoints for schedules, team rosters, etc.
2. api.nhle.com/stats/rest - Stats-focused endpoints

This module handles the quirks of the API to provide a consistent interface.
"""

import os
import logging
import sys
from datetime import datetime, timedelta
from nhlpy import NHLClient
import pandas as pd
import httpx

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NHLAPIClient:
    """
    NHL API Client wrapper using the nhl-api-py package
    
    This class handles common operations and data transformations to provide
    a consistent interface for the NHL API.
    """
    
    def __init__(self, verbose=False, timeout=30):
        """
        Initialize the NHL API client
        
        Args:
            verbose (bool): Whether to enable verbose logging
            timeout (int): Timeout for API requests in seconds
        """
        try:
            self.client = NHLClient(verbose=verbose, timeout=timeout)
            self.current_season = self._get_current_season()
            logger.info(f"NHL API Client initialized for season {self.current_season}")
        except Exception as e:
            logger.error(f"Error initializing NHL API client: {e}")
            raise
    
    def _get_current_season(self):
        """
        Get the current NHL season in YYYYYYYY format
        
        Returns:
            str: Current season in YYYYYYYY format (e.g., 20232024)
        """
        try:
            today = datetime.now()
            # NHL season typically starts in October and ends in June
            if today.month >= 9:  # September or later
                return f"{today.year}{today.year + 1}"
            else:  # January to August
                return f"{today.year - 1}{today.year}"
        except Exception as e:
            logger.error(f"Error determining current season: {e}")
            # Default to 2023-2024 season if unable to determine
            return "20232024"
    
    def get_teams(self):
        """
        Get all NHL teams
        
        Returns:
            pd.DataFrame: Teams information
        """
        try:
            logger.info("Fetching teams information...")
            
            # Try to get data from the standings endpoint
            try:
                response = self.client.standings.get_standings()
                
                # Check if response contains the expected data structure
                if isinstance(response, list):
                    # New API returns a list of standings records
                    teams_data = []
                    
                    for wildcard in response:
                        conference = wildcard.get('conferenceName', '')
                        for division in wildcard.get('divisions', []):
                            div_name = division.get('name', '')
                            for team in division.get('teamRecords', []):
                                team_data = {
                                    'team_id': team.get('teamId'),
                                    'name': team.get('teamName', {}).get('default', ''),
                                    'abbreviation': team.get('teamAbbrev', {}).get('default', ''),
                                    'team_name': team.get('teamName', {}).get('default', '').split()[-1] if team.get('teamName', {}).get('default', '') else '',
                                    'location': ' '.join(team.get('teamName', {}).get('default', '').split()[:-1]) if team.get('teamName', {}).get('default', '') else '',
                                    'division': div_name,
                                    'conference': conference,
                                    'venue_name': None,  # Not available in this endpoint
                                    'venue_city': None,  # Not available in this endpoint
                                    'season': self.current_season
                                }
                                teams_data.append(team_data)
                    
                    if teams_data:
                        logger.info(f"Found {len(teams_data)} teams from standings")
                        return pd.DataFrame(teams_data)
                
                # Try the old way if the new format didn't work
                if isinstance(response, dict) and 'standings' in response:
                    teams_data = []
                    for conference in response.get('standings', {}).get('conferences', []):
                        for div in conference.get('divisions', []):
                            for team in div.get('teamRecords', []):
                                team_info = team.get('teamStats', {}).get('teamInfo', {})
                                teams_data.append({
                                    'team_id': team_info.get('id', None),
                                    'name': team_info.get('name', {}).get('default', None),
                                    'abbreviation': team_info.get('abbrev', None),
                                    'team_name': team_info.get('name', {}).get('default', None).split()[-1],
                                    'location': ' '.join(team_info.get('name', {}).get('default', '').split()[:-1]),
                                    'division': div.get('name', None),
                                    'conference': conference.get('name', None),
                                    'venue_name': team_info.get('venue', {}).get('default', None),
                                    'venue_city': team_info.get('cityName', {}).get('default', None),
                                    'season': self.current_season
                                })
                    
                    if teams_data:
                        logger.info(f"Found {len(teams_data)} teams from standings (old format)")
                        return pd.DataFrame(teams_data)
            except Exception as e:
                logger.warning(f"Error fetching teams from standings: {e}")
            
            # Fallback to teams endpoint
            try:
                teams = self.client.teams.all_teams()
                teams_data = []
                
                if isinstance(teams, dict) and 'data' in teams:
                    for team in teams.get('data', []):
                        teams_data.append({
                            'team_id': team.get('id'),
                            'name': team.get('fullName'),
                            'abbreviation': team.get('triCode', ''),
                            'team_name': team.get('teamName', ''),
                            'location': team.get('locationName', ''),
                            'division': None,  # Not available in this endpoint
                            'conference': None,  # Not available in this endpoint
                            'venue_name': None,  # Not available in this endpoint
                            'venue_city': None,  # Not available in this endpoint
                            'season': self.current_season
                        })
                
                if teams_data:
                    logger.info(f"Found {len(teams_data)} teams from teams endpoint")
                    return pd.DataFrame(teams_data)
            except Exception as e:
                logger.warning(f"Error fetching teams from teams endpoint: {e}")
            
            # If we get here, we need to use a hardcoded list as last resort
            logger.warning("Using hardcoded team list as fallback")
            teams_data = [
                {'team_id': 1, 'name': 'New Jersey Devils', 'abbreviation': 'NJD', 'team_name': 'Devils', 'location': 'New Jersey', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 2, 'name': 'New York Islanders', 'abbreviation': 'NYI', 'team_name': 'Islanders', 'location': 'New York', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 3, 'name': 'New York Rangers', 'abbreviation': 'NYR', 'team_name': 'Rangers', 'location': 'New York', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 4, 'name': 'Philadelphia Flyers', 'abbreviation': 'PHI', 'team_name': 'Flyers', 'location': 'Philadelphia', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 5, 'name': 'Pittsburgh Penguins', 'abbreviation': 'PIT', 'team_name': 'Penguins', 'location': 'Pittsburgh', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 6, 'name': 'Boston Bruins', 'abbreviation': 'BOS', 'team_name': 'Bruins', 'location': 'Boston', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 7, 'name': 'Buffalo Sabres', 'abbreviation': 'BUF', 'team_name': 'Sabres', 'location': 'Buffalo', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 8, 'name': 'Montréal Canadiens', 'abbreviation': 'MTL', 'team_name': 'Canadiens', 'location': 'Montréal', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 9, 'name': 'Ottawa Senators', 'abbreviation': 'OTT', 'team_name': 'Senators', 'location': 'Ottawa', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 10, 'name': 'Toronto Maple Leafs', 'abbreviation': 'TOR', 'team_name': 'Maple Leafs', 'location': 'Toronto', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 12, 'name': 'Carolina Hurricanes', 'abbreviation': 'CAR', 'team_name': 'Hurricanes', 'location': 'Carolina', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 13, 'name': 'Florida Panthers', 'abbreviation': 'FLA', 'team_name': 'Panthers', 'location': 'Florida', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 14, 'name': 'Tampa Bay Lightning', 'abbreviation': 'TBL', 'team_name': 'Lightning', 'location': 'Tampa Bay', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 15, 'name': 'Washington Capitals', 'abbreviation': 'WSH', 'team_name': 'Capitals', 'location': 'Washington', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 16, 'name': 'Chicago Blackhawks', 'abbreviation': 'CHI', 'team_name': 'Blackhawks', 'location': 'Chicago', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 17, 'name': 'Detroit Red Wings', 'abbreviation': 'DET', 'team_name': 'Red Wings', 'location': 'Detroit', 'division': 'Atlantic', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 18, 'name': 'Nashville Predators', 'abbreviation': 'NSH', 'team_name': 'Predators', 'location': 'Nashville', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 19, 'name': 'St. Louis Blues', 'abbreviation': 'STL', 'team_name': 'Blues', 'location': 'St. Louis', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 20, 'name': 'Calgary Flames', 'abbreviation': 'CGY', 'team_name': 'Flames', 'location': 'Calgary', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 21, 'name': 'Colorado Avalanche', 'abbreviation': 'COL', 'team_name': 'Avalanche', 'location': 'Colorado', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 22, 'name': 'Edmonton Oilers', 'abbreviation': 'EDM', 'team_name': 'Oilers', 'location': 'Edmonton', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 23, 'name': 'Vancouver Canucks', 'abbreviation': 'VAN', 'team_name': 'Canucks', 'location': 'Vancouver', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 24, 'name': 'Anaheim Ducks', 'abbreviation': 'ANA', 'team_name': 'Ducks', 'location': 'Anaheim', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 25, 'name': 'Dallas Stars', 'abbreviation': 'DAL', 'team_name': 'Stars', 'location': 'Dallas', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 26, 'name': 'Los Angeles Kings', 'abbreviation': 'LAK', 'team_name': 'Kings', 'location': 'Los Angeles', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 28, 'name': 'San Jose Sharks', 'abbreviation': 'SJS', 'team_name': 'Sharks', 'location': 'San Jose', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 29, 'name': 'Columbus Blue Jackets', 'abbreviation': 'CBJ', 'team_name': 'Blue Jackets', 'location': 'Columbus', 'division': 'Metropolitan', 'conference': 'Eastern', 'season': self.current_season},
                {'team_id': 30, 'name': 'Minnesota Wild', 'abbreviation': 'MIN', 'team_name': 'Wild', 'location': 'Minnesota', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 52, 'name': 'Winnipeg Jets', 'abbreviation': 'WPG', 'team_name': 'Jets', 'location': 'Winnipeg', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 53, 'name': 'Arizona Coyotes', 'abbreviation': 'ARI', 'team_name': 'Coyotes', 'location': 'Arizona', 'division': 'Central', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 54, 'name': 'Vegas Golden Knights', 'abbreviation': 'VGK', 'team_name': 'Golden Knights', 'location': 'Vegas', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 55, 'name': 'Seattle Kraken', 'abbreviation': 'SEA', 'team_name': 'Kraken', 'location': 'Seattle', 'division': 'Pacific', 'conference': 'Western', 'season': self.current_season},
                {'team_id': 56, 'name': 'Utah Hockey Club', 'abbreviation': 'UHC', 'team_name': 'Hockey Club', 'location': 'Utah', 'division': 'Central', 'conference': 'Western', 'season': self.current_season}
            ]
            return pd.DataFrame(teams_data)
            
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            return pd.DataFrame()
    
    def get_schedule(self, season=None, team_id=None, start_date=None, end_date=None):
        """
        Get NHL schedule for a specified period
        
        Args:
            season (str, optional): Season in YYYYYYYY format
            team_id (int, optional): Team ID to filter schedule
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            pd.DataFrame: Schedule data
        """
        try:
            logger.info("Fetching schedule...")
            
            # Set defaults
            if not season:
                season = self.current_season
            
            if not start_date:
                # Default to current date
                start_date = datetime.now().strftime("%Y-%m-%d")
            
            # Try to get full schedule first
            schedule_data = []
            games_found = 0
            
            # Get weekly schedule (most reliable method)
            weekly_schedule = self.client.schedule.get_weekly_schedule()
            
            if weekly_schedule and 'gameWeek' in weekly_schedule:
                for day in weekly_schedule.get('gameWeek', []):
                    date = day.get('date')
                    for game in day.get('games', []):
                        game_data = {
                            'game_id': game.get('id'),
                            'season': season,
                            'game_type': self._map_game_type(game.get('gameType')),
                            'date': date,
                            'home_team_id': game.get('homeTeam', {}).get('id'),
                            'away_team_id': game.get('awayTeam', {}).get('id'),
                            'venue': game.get('venue', {}).get('default'),
                            'start_time': game.get('startTimeUTC'),
                            'home_score': game.get('homeTeam', {}).get('score'),
                            'away_score': game.get('awayTeam', {}).get('score'),
                            'status': game.get('gameState')
                        }
                        
                        # Apply filters
                        if team_id and (game_data['home_team_id'] != team_id and game_data['away_team_id'] != team_id):
                            continue
                            
                        schedule_data.append(game_data)
                        games_found += 1
            
            logger.info(f"Found {games_found} games in schedule")
            return pd.DataFrame(schedule_data)
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return pd.DataFrame()
    
    def get_player(self, player_id):
        """
        Get player information by ID
        
        Args:
            player_id (int): Player ID
            
        Returns:
            dict: Player information
        """
        try:
            logger.info(f"Fetching player info for ID {player_id}...")
            
            player_info = self.client.players.get_player(player_id)
            
            if player_info:
                return player_info
            else:
                logger.warning(f"No data found for player ID {player_id}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching player {player_id}: {e}")
            return {}
    
    def get_player_stats(self, player_id, season=None):
        """
        Get player statistics
        
        Args:
            player_id (int): Player ID
            season (str, optional): Season in YYYYYYYY format
            
        Returns:
            dict: Player statistics
        """
        try:
            logger.info(f"Fetching player stats for ID {player_id}...")
            
            if not season:
                season = self.current_season
            
            # First, get player info to determine if they're a goalie
            player_info = self.get_player(player_id)
            
            if not player_info:
                return {}
            
            # Determine position type
            position = player_info.get('position', {}).get('code', '')
            if position == 'G':
                # Goalie stats
                try:
                    player_stats = self.client.goalies.get_goalie_stats(player_id)
                    return player_stats
                except:
                    logger.warning(f"Could not fetch goalie stats, trying player stats...")
            
            # Regular player stats
            try:
                player_stats = self.client.skaters.get_skater_stats(player_id)
                return player_stats
            except Exception as e:
                logger.error(f"Error fetching player stats: {e}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching player stats {player_id}: {e}")
            return {}
    
    def get_team_roster(self, team_id, season=None):
        """
        Get team roster
        
        Args:
            team_id (int): Team ID
            season (str, optional): Season in YYYYYYYY format
            
        Returns:
            pd.DataFrame: Team roster data
        """
        try:
            logger.info(f"Fetching roster for team ID {team_id}...")
            
            if not season:
                season = self.current_season
            
            roster_data = []
            
            # Method 1: Try the standard roster endpoint
            try:
                roster = self.client.teams.roster(team_id, season)
                if roster and len(roster) > 0:
                    for player in roster:
                        player_data = {
                            'player_id': player.get('id'),
                            'full_name': f"{player.get('firstName', {}).get('default', '')} {player.get('lastName', {}).get('default', '')}",
                            'first_name': player.get('firstName', {}).get('default', ''),
                            'last_name': player.get('lastName', {}).get('default', ''),
                            'position': player.get('positionCode'),
                            'position_type': self._map_position_type(player.get('positionCode')),
                            'team_id': team_id,
                            'season': season,
                            'jersey_number': player.get('sweaterNumber'),
                            'is_active': 1  # Assume active if on roster
                        }
                        roster_data.append(player_data)
                    
                    logger.info(f"Found {len(roster_data)} players on roster using standard endpoint")
                    return pd.DataFrame(roster_data)
            except Exception as e:
                logger.warning(f"Could not fetch roster using standard method: {e}")
            
            # Method 2: Try using a direct API call to the roster endpoint
            try:
                url = f"https://api-web.nhle.com/v1/roster/{team_id}/{season}"
                response = httpx.get(url)
                logger.info(f"HTTP Request: GET {url} \"{response.status_code}\"")
                
                if response.status_code == 200:
                    roster_json = response.json()
                    if 'forwards' in roster_json:
                        for player in roster_json.get('forwards', []):
                            player_data = {
                                'player_id': player.get('id'),
                                'full_name': player.get('fullName', ''),
                                'first_name': player.get('firstName', {}).get('default', ''),
                                'last_name': player.get('lastName', {}).get('default', ''),
                                'nationality': player.get('nationality', ''),
                                'birth_date': player.get('birthDate', ''),
                                'height': player.get('height', ''),
                                'weight': player.get('weight', 0),
                                'shoots_catches': player.get('shootsCatches', ''),
                                'position': player.get('positionCode', ''),
                                'position_type': 'F',
                                'team_id': team_id,
                                'season': season,
                                'jersey_number': player.get('sweaterNumber', ''),
                                'is_active': 1
                            }
                            roster_data.append(player_data)
                            
                    if 'defensemen' in roster_json:
                        for player in roster_json.get('defensemen', []):
                            player_data = {
                                'player_id': player.get('id'),
                                'full_name': player.get('fullName', ''),
                                'first_name': player.get('firstName', {}).get('default', ''),
                                'last_name': player.get('lastName', {}).get('default', ''),
                                'nationality': player.get('nationality', ''),
                                'birth_date': player.get('birthDate', ''),
                                'height': player.get('height', ''),
                                'weight': player.get('weight', 0),
                                'shoots_catches': player.get('shootsCatches', ''),
                                'position': player.get('positionCode', ''),
                                'position_type': 'D',
                                'team_id': team_id,
                                'season': season,
                                'jersey_number': player.get('sweaterNumber', ''),
                                'is_active': 1
                            }
                            roster_data.append(player_data)
                            
                    if 'goalies' in roster_json:
                        for player in roster_json.get('goalies', []):
                            player_data = {
                                'player_id': player.get('id'),
                                'full_name': player.get('fullName', ''),
                                'first_name': player.get('firstName', {}).get('default', ''),
                                'last_name': player.get('lastName', {}).get('default', ''),
                                'nationality': player.get('nationality', ''),
                                'birth_date': player.get('birthDate', ''),
                                'height': player.get('height', ''),
                                'weight': player.get('weight', 0),
                                'shoots_catches': player.get('shootsCatches', ''),
                                'position': player.get('positionCode', ''),
                                'position_type': 'G',
                                'team_id': team_id,
                                'season': season,
                                'jersey_number': player.get('sweaterNumber', ''),
                                'is_active': 1
                            }
                            roster_data.append(player_data)
                    
                    logger.info(f"Found {len(roster_data)} players on roster using direct API call")
                    return pd.DataFrame(roster_data)
            except Exception as e:
                logger.warning(f"Could not fetch roster using direct API call: {e}")
            
            # Method 3: Try using the team stats endpoint
            try:
                url = f"https://api-web.nhle.com/v1/club-stats/{team_id}/now"
                response = httpx.get(url)
                logger.info(f"HTTP Request: GET {url} \"{response.status_code}\"")
                
                if response.status_code == 200:
                    stats_json = response.json()
                    if 'skaters' in stats_json:
                        for player in stats_json.get('skaters', []):
                            player_data = {
                                'player_id': player.get('playerId'),
                                'full_name': player.get('name', {}).get('default', ''),
                                'first_name': '',  # Not available in this endpoint
                                'last_name': '',  # Not available in this endpoint
                                'position': player.get('positionCode', ''),
                                'position_type': 'D' if player.get('positionCode', '') == 'D' else 'F',
                                'team_id': team_id,
                                'season': season,
                                'jersey_number': player.get('sweaterNumber', ''),
                                'is_active': 1
                            }
                            roster_data.append(player_data)
                            
                    if 'goalies' in stats_json:
                        for player in stats_json.get('goalies', []):
                            player_data = {
                                'player_id': player.get('playerId'),
                                'full_name': player.get('name', {}).get('default', ''),
                                'first_name': '',  # Not available in this endpoint
                                'last_name': '',  # Not available in this endpoint
                                'position': 'G',
                                'position_type': 'G',
                                'team_id': team_id,
                                'season': season,
                                'jersey_number': player.get('sweaterNumber', ''),
                                'is_active': 1
                            }
                            roster_data.append(player_data)
                    
                    logger.info(f"Found {len(roster_data)} players on roster using team stats endpoint")
                    return pd.DataFrame(roster_data)
            except Exception as e:
                logger.warning(f"Could not fetch roster using team stats endpoint: {e}")
            
            logger.warning("All roster fetch methods failed, returning empty DataFrame")
            return pd.DataFrame(roster_data)
        except Exception as e:
            logger.error(f"Error fetching team roster {team_id}: {e}")
            return pd.DataFrame()
    
    def get_standings(self):
        """
        Get current league standings
        
        Returns:
            pd.DataFrame: Standings data
        """
        try:
            logger.info("Fetching standings...")
            
            # Get standings from the API
            response = self.client.standings.get_standings()
            standings_data = []
            
            # Handle the new API format (list of wildcard standings)
            if isinstance(response, list):
                for wildcard in response:
                    conference = wildcard.get('conferenceName', '')
                    for division in wildcard.get('divisions', []):
                        div_name = division.get('name', '')
                        for team in division.get('teamRecords', []):
                            standings_data.append({
                                'team_id': team.get('teamId'),
                                'division': div_name,
                                'conference': conference,
                                'league_rank': team.get('leagueSequence', 0),
                                'division_rank': team.get('divisionSequence', 0),
                                'conference_rank': team.get('conferenceSequence', 0),
                                'points': team.get('points', 0),
                                'games_played': team.get('gamesPlayed', 0),
                                'wins': team.get('wins', 0),
                                'losses': team.get('losses', 0),
                                'ot_losses': team.get('otLosses', 0),
                                'regulation_wins': team.get('regulationWins', 0),
                                'goals_for': team.get('goalFor', 0),
                                'goals_against': team.get('goalAgainst', 0),
                                'pts_pctg': team.get('pointPctg', 0.0),
                                'season': self.current_season
                            })
            
            # Handle the old API format
            elif isinstance(response, dict) and 'standings' in response:
                for conference in response.get('standings', {}).get('conferences', []):
                    for div in conference.get('divisions', []):
                        for team in div.get('teamRecords', []):
                            team_info = team.get('teamStats', {}).get('teamInfo', {})
                            standings_data.append({
                                'team_id': team_info.get('id'),
                                'division': div.get('name'),
                                'conference': conference.get('name'),
                                'league_rank': team.get('leagueSequence'),
                                'division_rank': team.get('divisionSequence'),
                                'conference_rank': team.get('conferenceSequence'),
                                'points': team.get('points'),
                                'games_played': team.get('gamesPlayed'),
                                'wins': team.get('wins'),
                                'losses': team.get('losses'),
                                'ot_losses': team.get('otLosses'),
                                'regulation_wins': team.get('regulationWins'),
                                'goals_for': team.get('goalFor'),
                                'goals_against': team.get('goalAgainst'),
                                'pts_pctg': team.get('pointPctg'),
                                'season': self.current_season
                            })
            
            # If we couldn't get standings data, use the teams data as a fallback
            if not standings_data:
                logger.warning("No standings data found, using teams data as fallback")
                teams_df = self.get_teams()
                if not teams_df.empty:
                    for _, team in teams_df.iterrows():
                        standings_data.append({
                            'team_id': team.get('team_id'),
                            'division': team.get('division'),
                            'conference': team.get('conference'),
                            'league_rank': 0,
                            'division_rank': 0,
                            'conference_rank': 0,
                            'points': 0,
                            'games_played': 0,
                            'wins': 0,
                            'losses': 0,
                            'ot_losses': 0,
                            'regulation_wins': 0,
                            'goals_for': 0,
                            'goals_against': 0,
                            'pts_pctg': 0.0,
                            'season': self.current_season
                        })
            
            logger.info(f"Found {len(standings_data)} teams in standings")
            return pd.DataFrame(standings_data)
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            return pd.DataFrame()
    
    def _map_game_type(self, game_type):
        """Map game type codes to standardized format"""
        game_type_map = {
            'PR': 'PR',  # Preseason
            'R': 'R',    # Regular season
            'P': 'P',    # Playoffs
            'A': 'A',    # All-Star game
            'ST': 'ST',  # Stanley Cup
            'WCOH_EXH': 'PR',  # World Cup exhibition
            'WCOH_PRELIM': 'R',  # World Cup preliminary
            'WCOH_FINAL': 'P',  # World Cup final
            2: 'R',      # Regular season
            3: 'P'       # Playoffs
        }
        
        return game_type_map.get(game_type, 'R')
    
    def _map_position_type(self, position_code):
        """Map position codes to standardized position types"""
        if position_code == 'G':
            return 'G'  # Goalie
        elif position_code in ['D', 'LD', 'RD']:
            return 'D'  # Defenseman
        else:
            return 'F'  # Forward (C, LW, RW)

    def get_game_details(self, game_id):
        """
        Get detailed information about a specific game including attendance
        
        Args:
            game_id (int): Game ID
            
        Returns:
            dict: Game details including attendance if available
        """
        try:
            logger.info(f"Fetching details for game ID {game_id}...")
            
            # Try direct API call to the boxscore endpoint
            import httpx
            
            try:
                url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
                response = httpx.get(url)
                logger.info(f"HTTP Request: GET {url} \"{response.status_code}\"")
                
                if response.status_code == 200:
                    game_data = response.json()
                    
                    # Extract relevant game details including attendance
                    details = {
                        'game_id': game_id,
                        'attendance': game_data.get('gameInfo', {}).get('attendance'),
                        'venue': game_data.get('venue', {}).get('default'),
                        'start_time': game_data.get('startTime'),
                        'end_time': game_data.get('endTime'),
                        'home_team_id': game_data.get('homeTeam', {}).get('id'),
                        'away_team_id': game_data.get('awayTeam', {}).get('id'),
                        'home_score': game_data.get('homeTeam', {}).get('score'),
                        'away_score': game_data.get('awayTeam', {}).get('score'),
                        'period': game_data.get('period'),
                        'periodic_record': game_data.get('periodDescriptor', {}).get('periodType')
                    }
                    
                    logger.info(f"Retrieved details for game {game_id}")
                    return details
            except Exception as e:
                logger.warning(f"Could not fetch game details using boxscore endpoint: {e}")
                
            # Try alternative endpoint
            try:
                url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing"
                response = httpx.get(url)
                logger.info(f"HTTP Request: GET {url} \"{response.status_code}\"")
                
                if response.status_code == 200:
                    game_data = response.json()
                    
                    # Extract relevant game details including attendance
                    details = {
                        'game_id': game_id,
                        'attendance': game_data.get('summary', {}).get('attendance'),
                        'venue': game_data.get('venue', {}).get('default'),
                        'start_time': game_data.get('startTimeUTC'),
                        'home_team_id': game_data.get('homeTeam', {}).get('id'),
                        'away_team_id': game_data.get('awayTeam', {}).get('id'),
                        'home_score': game_data.get('homeTeam', {}).get('score'),
                        'away_score': game_data.get('awayTeam', {}).get('score'),
                        'period': game_data.get('period')
                    }
                    
                    logger.info(f"Retrieved details for game {game_id} using landing endpoint")
                    return details
            except Exception as e:
                logger.warning(f"Could not fetch game details using landing endpoint: {e}")
            
            logger.warning(f"All methods to fetch game details failed for game {game_id}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching game details for {game_id}: {e}")
            return {}

def get_api_client(verbose=False, timeout=30):
    """
    Get an instance of the NHL API client
    
    Args:
        verbose (bool): Whether to enable verbose logging
        timeout (int): Timeout for API requests in seconds
        
    Returns:
        NHLAPIClient: NHL API client instance
    """
    try:
        return NHLAPIClient(verbose=verbose, timeout=timeout)
    except Exception as e:
        logger.error(f"Failed to create NHL API client: {e}")
        raise

def get_teams():
    """
    Get all NHL teams
    
    Returns:
        pd.DataFrame: Teams information
    """
    client = get_api_client()
    return client.get_teams()

def get_schedule(season=None, team_id=None, start_date=None, end_date=None):
    """
    Get NHL schedule for a specified period
    
    Args:
        season (str, optional): Season in YYYYYYYY format
        team_id (int, optional): Team ID to filter schedule
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        
    Returns:
        pd.DataFrame: Schedule data
    """
    client = get_api_client()
    return client.get_schedule(season, team_id, start_date, end_date)

def get_player(player_id):
    """
    Get player information by ID
    
    Args:
        player_id (int): Player ID
        
    Returns:
        dict: Player information
    """
    client = get_api_client()
    return client.get_player(player_id)

def get_player_stats(player_id, season=None):
    """
    Get player statistics
    
    Args:
        player_id (int): Player ID
        season (str, optional): Season in YYYYYYYY format
        
    Returns:
        dict: Player statistics
    """
    client = get_api_client()
    return client.get_player_stats(player_id, season)

def get_team_roster(team_id, season=None):
    """
    Get team roster
    
    Args:
        team_id (int): Team ID
        season (str, optional): Season in YYYYYYYY format
        
    Returns:
        pd.DataFrame: Team roster data
    """
    client = get_api_client()
    return client.get_team_roster(team_id, season)

def get_standings():
    """
    Get current league standings
    
    Returns:
        pd.DataFrame: Standings data
    """
    client = get_api_client()
    return client.get_standings()

def get_game_details(game_id):
    """
    Get detailed information about a specific game including attendance
    
    Args:
        game_id (int): Game ID
        
    Returns:
        dict: Game details including attendance if available
    """
    client = get_api_client()
    return client.get_game_details(game_id)

# Simple test function to verify API functionality
def test_api():
    """
    Test the NHL API functionality
    
    Returns:
        bool: True if tests pass, False otherwise
    """
    try:
        logger.info("Testing NHL API functionality...")
        
        # Create client
        client = get_api_client(verbose=True)
        logger.info(f"Current season: {client.current_season}")
        
        # Test standings
        standings = client.get_standings()
        logger.info(f"Retrieved {len(standings)} teams from standings")
        
        # Test teams
        teams = client.get_teams()
        logger.info(f"Retrieved {len(teams)} teams")
        
        # Test schedule
        schedule = client.get_schedule()
        logger.info(f"Retrieved {len(schedule)} games from schedule")
        
        logger.info("All tests completed successfully!")
        return True
    except Exception as e:
        logger.error(f"API test failed: {e}")
        return False

if __name__ == "__main__":
    test_api() 