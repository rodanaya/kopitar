import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from geopy.distance import great_circle
import sqlite3
import time

class NHLGoalieAnalyzer:
    """Analyze NHL goaltender performance with fatigue factors"""
    
    def __init__(self):
        self.base_url = "https://statsapi.web.nhl.com/api/v1"
        self.arena_locations = self._load_arena_locations()
        
    def _load_arena_locations(self):
        """NHL arena coordinates for travel calculations"""
        return {
            'Anaheim Ducks': (33.8078, -117.8765),
            'Arizona Coyotes': (33.5318, -112.2612),
            'Boston Bruins': (42.3662, -71.0621),
            'Buffalo Sabres': (42.8750, -78.8764),
            'Calgary Flames': (51.0373, -114.0521),
            'Carolina Hurricanes': (35.8033, -78.7218),
            'Chicago Blackhawks': (41.8807, -87.6742),
            'Colorado Avalanche': (39.7487, -105.0077),
            'Columbus Blue Jackets': (39.9691, -83.0061),
            'Dallas Stars': (32.7903, -96.8103),
            'Detroit Red Wings': (42.3251, -83.0517),
            'Edmonton Oilers': (53.5469, -113.4977),
            'Florida Panthers': (26.1584, -80.3256),
            'Los Angeles Kings': (34.0430, -118.2673),
            'Minnesota Wild': (44.9449, -93.1013),
            'Montreal Canadiens': (45.4963, -73.5698),
            'Nashville Predators': (36.1593, -86.7785),
            'New Jersey Devils': (40.7335, -74.1710),
            'New York Islanders': (40.7225, -73.5903),
            'New York Rangers': (40.7505, -73.9934),
            'Ottawa Senators': (45.2969, -75.9268),
            'Philadelphia Flyers': (39.9012, -75.1720),
            'Pittsburgh Penguins': (40.4393, -79.9894),
            'San Jose Sharks': (37.3327, -121.9013),
            'Seattle Kraken': (47.6221, -122.3540),
            'St. Louis Blues': (38.6270, -90.2025),
            'Tampa Bay Lightning': (27.9428, -82.4519),
            'Toronto Maple Leafs': (43.6435, -79.3791),
            'Vancouver Canucks': (49.2778, -123.1088),
            'Vegas Golden Knights': (36.1029, -115.1784),
            'Washington Capitals': (38.8983, -77.0209),
            'Winnipeg Jets': (49.8928, -97.1434)
        }
    
    def get_goalie_stats(self, player_id, season):
        """Fetch goalie statistics from NHL API"""
        url = f"{self.base_url}/people/{player_id}/stats?stats=gameLog&season={season}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def calculate_travel_distance(self, team1, team2):
        """Calculate distance between two arenas in miles"""
        if team1 in self.arena_locations and team2 in self.arena_locations:
            coord1 = self.arena_locations[team1]
            coord2 = self.arena_locations[team2]
            return great_circle(coord1, coord2).miles
        return 0
    
    def estimate_travel_time(self, distance_miles):
        """Estimate travel time including flight + airport time"""
        if distance_miles < 200:  # Bus trip
            return distance_miles / 50  # 50 mph average
        else:  # Flight
            flight_time = distance_miles / 500  # 500 mph average
            return flight_time + 3  # Add 3 hours for airport
    
    def analyze_back_to_back_performance(self, goalie_data):
        """Analyze performance in back-to-back games"""
        games = pd.DataFrame(goalie_data)
        games['date'] = pd.to_datetime(games['date'])
        games = games.sort_values('date')
        
        # Identify back-to-back games
        games['days_rest'] = games['date'].diff().dt.days.fillna(10)
        games['is_b2b'] = games['days_rest'] == 1
        
        # Calculate performance metrics
        b2b_stats = {
            'regular_sv_pct': games[~games['is_b2b']]['savePercentage'].mean(),
            'b2b_sv_pct': games[games['is_b2b']]['savePercentage'].mean(),
            'regular_gaa': games[~games['is_b2b']]['goalsAgainst'].mean(),
            'b2b_gaa': games[games['is_b2b']]['goalsAgainst'].mean()
        }
        
        return b2b_stats
    
    def calculate_fatigue_index(self, goalie_id, date, game_log):
        """Calculate composite fatigue index for a goalie"""
        # Get games in last 10 days
        recent_games = game_log[
            (game_log['date'] >= date - timedelta(days=10)) &
            (game_log['date'] < date)
        ]
        
        # Calculate components
        games_played = len(recent_games)
        total_minutes = recent_games['timeOnIce'].sum()
        total_shots = recent_games['shots'].sum()
        avg_days_rest = recent_games['days_rest'].mean()
        
        # Weighted fatigue index (0-100 scale)
        fatigue_index = (
            (games_played / 5) * 30 +  # Games in 10 days
            (total_minutes / 300) * 20 +  # Minutes played
            (total_shots / 150) * 20 +  # Shots faced
            ((5 - avg_days_rest) / 5) * 30  # Rest factor
        )
        
        return min(fatigue_index, 100)
    
    def predict_performance(self, fatigue_index, travel_distance, opponent_strength):
        """Simple model to predict save percentage based on factors"""
        # Base save percentage
        base_sv_pct = 0.915
        
        # Adjustments
        fatigue_adjustment = -0.0002 * fatigue_index
        travel_adjustment = -0.00001 * travel_distance
        opponent_adjustment = -0.0001 * opponent_strength
        
        predicted_sv_pct = base_sv_pct + fatigue_adjustment + travel_adjustment + opponent_adjustment
        
        return max(min(predicted_sv_pct, 1.0), 0.0)

# Example usage
if __name__ == "__main__":
    analyzer = NHLGoalieAnalyzer()
    
    # Example: Calculate travel distance
    distance = analyzer.calculate_travel_distance('Toronto Maple Leafs', 'Los Angeles Kings')
    travel_time = analyzer.estimate_travel_time(distance)
    
    print(f"Distance TOR to LAK: {distance:.0f} miles")
    print(f"Estimated travel time: {travel_time:.1f} hours")
    
    # Example fatigue calculation
    fatigue = analyzer.calculate_fatigue_index(
        goalie_id="8471679",  # Example ID
        date=datetime(2024, 1, 15),
        game_log=pd.DataFrame()  # Would be actual game data
    )
    
    print(f"\nFatigue Index: {fatigue:.1f}/100")
    
    # Performance prediction
    predicted_sv = analyzer.predict_performance(
        fatigue_index=65,
        travel_distance=2000,
        opponent_strength=30
    )
    
    print(f"Predicted Save %: {predicted_sv:.3f}")