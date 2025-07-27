import sqlite3
import pandas as pd
import os
import random

# Database path
db_path = 'kopitar/database/nhl_performance.db'

# Check if database exists
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check actual table creation SQL
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='games'")
sql_creation = cursor.fetchone()[0]
print("Games table creation SQL:")
print(sql_creation)

# Check games table structure
cursor.execute("PRAGMA table_info(games)")
print("\nGames table columns:")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[0]}: {col[1]} ({col[2]})")

# Check if attendance column exists
attendance_column = next((col for col in columns if col[1] == 'attendance'), None)
if attendance_column:
    print(f"\nAttendance column exists with type: {attendance_column[2]}")
else:
    print("\nAttendance column does not exist in games table")

# Check player_injuries table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_injuries'")
if cursor.fetchone():
    print("\nPlayer injuries table exists")
    cursor.execute("PRAGMA table_info(player_injuries)")
    print("\nPlayer injuries table columns:")
    for col in cursor.fetchall():
        print(f"  {col[0]}: {col[1]} ({col[2]})")
else:
    print("\nPlayer injuries table does not exist")

# Retrieve all row from CSV import
print("\nCSV files in the data directory:")
for file in os.listdir("data"):
    if file.endswith(".csv"):
        print(f"  {file}")

# Show the first few rows of a schedule CSV to check columns
if os.path.exists("data/schedule_20232024.csv"):
    print("\nColumns in schedule_20232024.csv:")
    df = pd.read_csv("data/schedule_20232024.csv")
    print(df.columns.tolist())
    print("\nFirst row:")
    print(df.iloc[0].to_dict())

# Test adding attendance data to a few games
print("\nAdding sample attendance data to the database...")

# Get 5 random game_ids from the games table
cursor.execute("SELECT game_id FROM games ORDER BY RANDOM() LIMIT 5")
game_ids = [row[0] for row in cursor.fetchall()]

# Generate random attendance figures (between 12,000 and 20,000)
for game_id in game_ids:
    attendance = random.randint(12000, 20000)
    cursor.execute("UPDATE games SET attendance = ? WHERE game_id = ?", (attendance, game_id))
    print(f"  Game {game_id}: attendance set to {attendance}")

# Commit the changes
conn.commit()

# Verify the data was added correctly
print("\nChecking updated attendance data:")
cursor.execute("SELECT COUNT(*) FROM games WHERE attendance IS NOT NULL")
games_with_attendance = cursor.fetchone()[0]
print(f"Games with attendance data: {games_with_attendance}")

# Show the updated games
print("\nGames with attendance data:")
cursor.execute("""
SELECT game_id, date, venue, home_team_id, away_team_id, attendance 
FROM games 
WHERE attendance IS NOT NULL
""")
for row in cursor.fetchall():
    print(f"Game {row[0]} on {row[1]} at {row[2]}: {row[5]} attendees (Home: {row[3]} vs Away: {row[4]})")

# Close connection
conn.close()

print("\nDatabase check completed successfully.") 