# File: migrate_to_db.py
import pandas as pd
import json
from sqlalchemy import create_engine
from getpass import getpass # Used to securely ask for a password

def migrate():
    """
    A one-time script to read data from local files and write it
    to the new cloud database.
    """
    print("Starting cloud migration...")

    # --- Securely Get Connection Details ---
    # The base connection string WITHOUT the password
    base_connection_uri = "postgresql://postgres.eypaunoseudvofjcanmn:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
    
    # Prompt the user to enter the password securely
    db_password = getpass("Please paste your Supabase database password: ")
    
    # Construct the final connection string
    connection_string = base_connection_uri.replace("[YOUR-PASSWORD]", db_password)

    try:
        engine = create_engine(connection_string)
        # Test the connection
        connection = engine.connect()
        print("Successfully connected to cloud database.")
        connection.close()

        # --- Migration Logic ---
        excel_path = 'Project Tracker.xlsx'
        users_path = 'users.json'
        settings_path = 'user_settings.json'

        # (The rest of the migration logic remains the same)
        # ...

        print("\nCloud migration complete!")

    except Exception as e:
        print(f"\nAn error occurred during migration: {e}")

if __name__ == "__main__":
    migrate()