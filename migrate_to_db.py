# File: migrate_to_db.py
import pandas as pd
import json
from sqlalchemy import create_engine
import toml
import os
from getpass import getpass

def migrate():
    """
    A one-time script to read data from local files and write it
    to the new cloud database, with robust date parsing.
    """
    print("Starting cloud migration...")

    # --- Securely Get Connection Details ---
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    
    try:
        secrets = toml.load(secrets_path)
        connection_string = secrets["db_connection_string"]
        print("Successfully loaded database credentials from secrets.toml.")
    except (FileNotFoundError, KeyError):
        print(f"ERROR: Could not find or read 'db_connection_string' from {secrets_path}")
        return # Stop execution if secrets are not found

    try:
        engine = create_engine(connection_string)
        connection = engine.connect()
        print("Successfully connected to cloud database.")
        connection.close()

        # --- Migration Logic ---
        excel_path = 'Project Tracker.xlsx'
        
        # --- Migrate Tasks from Excel ---
        print("Migrating tasks from Excel...")
        df_tasks = pd.read_excel(excel_path, sheet_name='DATA')
        
        # --- CRITICAL FIX IS HERE ---
        # This function correctly handles dates saved as 'YYYY-MM-DD (DayName)'
        def robust_date_parse(date_col):
            # Take only the date part of the string, ignoring "(DayName)" or other text
            date_str_series = date_col.astype(str).str.split(' ').str[0]
            # Convert the clean date string to a proper datetime object
            return pd.to_datetime(date_str_series, errors='coerce')

        df_tasks['START'] = robust_date_parse(df_tasks['START'])
        df_tasks['END'] = robust_date_parse(df_tasks['END'])
        # -------------------------

        df_tasks.to_sql('tasks', engine, if_exists='replace', index=False)
        print(f"Successfully migrated {len(df_tasks)} tasks.")

        # (The rest of the migration for users, settings, etc. remains the same)
        users_path = 'users.json'
        settings_path = 'user_settings.json'
        # ... (rest of migration logic)
        
        print("\nCloud migration complete!")

    except Exception as e:
        print(f"\nAn error occurred during migration: {e}")

if __name__ == "__main__":
    migrate()
