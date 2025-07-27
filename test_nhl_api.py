#!/usr/bin/env python
"""
Test script for NHL API wrapper
"""
import os
import sys
from datetime import datetime
import pandas as pd
import json

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our NHL API wrapper
from kopitar.utils.nhl_api import test_api, get_api_client, get_teams, get_schedule, get_standings

print("Starting NHL API test...")

try:
    # Test the built-in test function first
    print("Testing the API using test_api function...")
    test_success = test_api()
    print(f"Test API function result: {'Success' if test_success else 'Failed'}")

    # Create a client directly
    print("\nCreating NHL API client...")
    client = get_api_client(verbose=True)
    print(f"Current season: {client.current_season}")

    # Test getting teams
    print("\nTesting get_teams()...")
    teams = get_teams()
    print(f"Retrieved {len(teams)} teams")
    if not teams.empty:
        print("First 3 teams:")
        print(teams.head(3)[['team_id', 'name', 'division', 'conference']].to_string())

    # Test getting schedule
    print("\nTesting get_schedule()...")
    schedule = get_schedule()
    print(f"Retrieved {len(schedule)} games from schedule")
    if not schedule.empty:
        print("First 3 games:")
        print(schedule.head(3)[['date', 'home_team_id', 'away_team_id', 'status']].to_string())

    # Test getting standings
    print("\nTesting get_standings()...")
    standings = get_standings()
    print(f"Retrieved {len(standings)} teams from standings")
    if not standings.empty:
        print("First 3 teams in standings:")
        print(standings.head(3)[['team_id', 'division', 'points', 'wins', 'losses']].to_string())

    print("\nAll tests completed!")
except Exception as e:
    print(f"\nError during testing: {e}")
    import traceback
    traceback.print_exc() 