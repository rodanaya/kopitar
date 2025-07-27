import sqlite3
import os
import pandas as pd

def check_database(db_path):
    """Check if the database exists and print its content"""
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Database file does not exist: {db_path}")
        return
    
    print(f"Database file exists: {db_path}")
    print(f"File size: {os.path.getsize(db_path)} bytes")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nFound {len(tables)} tables in the database:")
        
        # For each table, print its schema and count records
        for table in tables:
            table_name = table[0]
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            print(f"\n-- Table: {table_name} ({count} records, {len(columns)} columns) --")
            print("SCHEMA:")
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({col[2]}){' PRIMARY KEY' if col[5]==1 else ''}")
            
            # Print sample data (first row) if table has records
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                sample = cursor.fetchone()
                print("\nSAMPLE DATA (first row):")
                for i, col in enumerate(columns):
                    print(f"  {col[1]}: {sample[i]}")
        
        conn.close()
    except Exception as e:
        print(f"Error connecting to the database: {e}")

if __name__ == "__main__":
    db_path = "kopitar/database/nhl_performance.db"
    check_database(db_path) 