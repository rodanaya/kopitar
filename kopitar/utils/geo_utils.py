import pandas as pd
import numpy as np
from geopy.distance import great_circle
import pytz
from datetime import datetime

# Dictionary of NHL team venues with coordinates (latitude, longitude)
NHL_VENUES = {
    "Amalie Arena": (27.9428, -82.4519),  # Tampa Bay Lightning
    "American Airlines Center": (32.7905, -96.8103),  # Dallas Stars
    "Ball Arena": (39.7487, -105.0077),  # Colorado Avalanche
    "Bridgestone Arena": (36.1592, -86.7785),  # Nashville Predators
    "Canada Life Centre": (49.8926, -97.1437),  # Winnipeg Jets
    "Canadian Tire Centre": (45.2969, -75.9273),  # Ottawa Senators
    "Capital One Arena": (38.8981, -77.0209),  # Washington Capitals
    "Centre Bell": (45.4961, -73.5693),  # Montreal Canadiens
    "Climate Pledge Arena": (47.6219, -122.3539),  # Seattle Kraken
    "Nationwide Arena": (39.9694, -83.0060),  # Columbus Blue Jackets
    "Crypto.com Arena": (34.0430, -118.2673),  # Los Angeles Kings
    "Enterprise Center": (38.6268, -90.2026),  # St. Louis Blues
    "Gila River Arena": (33.5328, -112.2611),  # Arizona Coyotes
    "Honda Center": (33.8078, -117.8765),  # Anaheim Ducks
    "KeyBank Center": (42.8750, -78.8761),  # Buffalo Sabres
    "Little Caesars Arena": (42.3412, -83.0553),  # Detroit Red Wings
    "Madison Square Garden": (40.7505, -73.9934),  # New York Rangers
    "Mullett Arena": (33.4255, -111.9400),  # Arizona Coyotes (temp)
    "Nassau Veterans Memorial Coliseum": (40.7228, -73.5902),  # NY Islanders
    "Nationwide Arena": (39.9694, -83.0060),  # Columbus Blue Jackets
    "PNC Arena": (35.8033, -78.7218),  # Carolina Hurricanes
    "PPG Paints Arena": (40.4395, -79.9893),  # Pittsburgh Penguins
    "Prudential Center": (40.7334, -74.1710),  # New Jersey Devils
    "Rogers Arena": (49.2778, -123.1088),  # Vancouver Canucks
    "Rogers Place": (53.5472, -113.4978),  # Edmonton Oilers
    "SAP Center at San Jose": (37.3328, -121.9012),  # San Jose Sharks
    "Scotiabank Arena": (43.6435, -79.3791),  # Toronto Maple Leafs
    "Scotiabank Saddledome": (51.0374, -114.0519),  # Calgary Flames
    "TD Garden": (42.3662, -71.0621),  # Boston Bruins
    "UBS Arena": (40.7233, -73.5962),  # New York Islanders
    "Wells Fargo Center": (39.9012, -75.1720),  # Philadelphia Flyers
    "Xcel Energy Center": (44.9448, -93.1009),  # Minnesota Wild
}

# Timezone information for NHL cities
NHL_TIMEZONES = {
    "Amalie Arena": "America/New_York",  # Tampa Bay
    "American Airlines Center": "America/Chicago",  # Dallas
    "Ball Arena": "America/Denver",  # Colorado
    "Bridgestone Arena": "America/Chicago",  # Nashville
    "Canada Life Centre": "America/Winnipeg",  # Winnipeg
    "Canadian Tire Centre": "America/Toronto",  # Ottawa
    "Capital One Arena": "America/New_York",  # Washington
    "Centre Bell": "America/Montreal",  # Montreal
    "Climate Pledge Arena": "America/Los_Angeles",  # Seattle
    "Crypto.com Arena": "America/Los_Angeles",  # Los Angeles
    "Enterprise Center": "America/Chicago",  # St. Louis
    "Gila River Arena": "America/Phoenix",  # Arizona
    "Honda Center": "America/Los_Angeles",  # Anaheim
    "KeyBank Center": "America/New_York",  # Buffalo
    "Little Caesars Arena": "America/Detroit",  # Detroit
    "Madison Square Garden": "America/New_York",  # NY Rangers
    "Mullett Arena": "America/Phoenix",  # Arizona
    "Nassau Veterans Memorial Coliseum": "America/New_York",  # NY Islanders
    "Nationwide Arena": "America/New_York",  # Columbus
    "PNC Arena": "America/New_York",  # Carolina
    "PPG Paints Arena": "America/New_York",  # Pittsburgh
    "Prudential Center": "America/New_York",  # New Jersey
    "Rogers Arena": "America/Vancouver",  # Vancouver
    "Rogers Place": "America/Edmonton",  # Edmonton
    "SAP Center at San Jose": "America/Los_Angeles",  # San Jose
    "Scotiabank Arena": "America/Toronto",  # Toronto
    "Scotiabank Saddledome": "America/Edmonton",  # Calgary
    "TD Garden": "America/New_York",  # Boston
    "UBS Arena": "America/New_York",  # NY Islanders
    "Wells Fargo Center": "America/New_York",  # Philadelphia
    "Xcel Energy Center": "America/Chicago",  # Minnesota
}

def get_venue_coordinates(venue_name):
    """
    Get coordinates (latitude, longitude) for an NHL venue
    
    Args:
        venue_name (str): Name of the NHL venue
        
    Returns:
        tuple: (latitude, longitude) or None if venue not found
    """
    return NHL_VENUES.get(venue_name, None)

def calculate_distance(venue1, venue2):
    """
    Calculate distance in kilometers between two NHL venues
    
    Args:
        venue1 (str): Name of the first venue
        venue2 (str): Name of the second venue
        
    Returns:
        float: Distance in kilometers or None if venues not found
    """
    coords1 = get_venue_coordinates(venue1)
    coords2 = get_venue_coordinates(venue2)
    
    if coords1 and coords2:
        return great_circle(coords1, coords2).kilometers
    return None

def get_timezone_diff(venue1, venue2):
    """
    Calculate timezone difference between two NHL venues
    
    Args:
        venue1 (str): Name of the first venue
        venue2 (str): Name of the second venue
        
    Returns:
        int: Timezone difference in hours (negative means traveling west, positive means traveling east)
    """
    tz1 = NHL_TIMEZONES.get(venue1)
    tz2 = NHL_TIMEZONES.get(venue2)
    
    if not (tz1 and tz2):
        return 0
    
    now = datetime.now()
    zone1 = pytz.timezone(tz1)
    zone2 = pytz.timezone(tz2)
    
    diff = zone2.utcoffset(now) - zone1.utcoffset(now)
    return diff.total_seconds() / 3600  # Convert to hours

def determine_travel_direction(venue1, venue2):
    """
    Determine if travel is eastward or westward
    
    Args:
        venue1 (str): Name of the first venue (origin)
        venue2 (str): Name of the second venue (destination)
        
    Returns:
        str: 'eastward', 'westward', or 'same' if no substantial change
    """
    coords1 = get_venue_coordinates(venue1)
    coords2 = get_venue_coordinates(venue2)
    
    if not (coords1 and coords2):
        return 'unknown'
    
    # Longitude difference (negative means eastward travel)
    long_diff = coords2[1] - coords1[1]
    
    # Handle wraparound at the international date line
    if long_diff > 180:
        long_diff -= 360
    elif long_diff < -180:
        long_diff += 360
    
    if abs(long_diff) < 3:  # Less than 3 degrees is roughly equivalent to no substantial change
        return 'same'
    elif long_diff < 0:
        return 'eastward'
    else:
        return 'westward'

def estimate_travel_time(distance_km):
    """
    Estimate travel time based on distance
    
    Args:
        distance_km (float): Distance in kilometers
        
    Returns:
        float: Estimated travel time in hours
    """
    if distance_km is None:
        return None
    
    # Simple model: assume team charter flights at ~800 km/h cruise speed
    # Add 1.5 hours for takeoff, landing, and ground transportation
    if distance_km <= 0:
        return 0
    elif distance_km < 100:  # Very close, likely bus
        return distance_km / 65  # Average bus speed ~65 km/h
    else:
        return (distance_km / 800) + 1.5  # Flight time + ground logistics

def add_travel_data(schedule_df):
    """
    Add travel-related metrics to a game schedule DataFrame
    
    Args:
        schedule_df (DataFrame): DataFrame with game schedule information,
                                 must contain 'date', 'venue' columns
    
    Returns:
        DataFrame: Original DataFrame with added travel columns
    """
    if 'venue' not in schedule_df.columns:
        return schedule_df
    
    # Sort by date for correct sequencing
    schedule_df = schedule_df.sort_values('date').copy()
    
    # Convert date to datetime
    schedule_df['date'] = pd.to_datetime(schedule_df['date'])
    
    # Initialize new columns
    schedule_df['distance_traveled'] = np.nan
    schedule_df['timezone_diff'] = np.nan
    schedule_df['travel_direction'] = None
    schedule_df['estimated_travel_time'] = np.nan
    
    # Iterate through games chronologically for each team
    for team_id in schedule_df['home_team_id'].unique():
        # Get games for this team (both home and away)
        team_games = schedule_df[
            (schedule_df['home_team_id'] == team_id) | 
            (schedule_df['away_team_id'] == team_id)
        ].sort_values('date')
        
        prev_venue = None
        
        for idx, game in team_games.iterrows():
            current_venue = game['venue']
            
            if prev_venue and current_venue:
                # Calculate travel metrics
                distance = calculate_distance(prev_venue, current_venue)
                timezone_diff = get_timezone_diff(prev_venue, current_venue)
                direction = determine_travel_direction(prev_venue, current_venue)
                travel_time = estimate_travel_time(distance)
                
                # Update the main dataframe
                schedule_df.loc[idx, 'distance_traveled'] = distance
                schedule_df.loc[idx, 'timezone_diff'] = timezone_diff
                schedule_df.loc[idx, 'travel_direction'] = direction
                schedule_df.loc[idx, 'estimated_travel_time'] = travel_time
            
            prev_venue = current_venue
    
    # Calculate days between games
    schedule_df['days_since_last_game'] = schedule_df.groupby(['home_team_id', 'away_team_id'])\
        ['date'].diff().dt.days
    
    # Flag back-to-back games (0 or 1 days between games)
    schedule_df['is_back_to_back'] = schedule_df['days_since_last_game'].apply(
        lambda x: 1 if x is not None and x <= 1 else 0
    )
    
    return schedule_df 