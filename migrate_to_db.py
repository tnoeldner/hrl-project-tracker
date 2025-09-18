# File: migrate_to_db.py
import pandas as pd
import json
from sqlalchemy import create_engine

# --- IMPORTANT ---
# Paste the connection string you copied from Supabase here.
# Make sure to replace [YOUR-PASSWORD] with your actual database password.
CONNECTION_STRING = "postgresql://postgres.eypaunoseudvofjcanmn:9G%ep?Qi-nihbYx@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

def migrate():
    """
    A one-time script to read data from local files and write it
    to the new cloud database.
    """
    print("Starting cloud migration...")
    excel_path = 'Project Tracker.xlsx'
    users_path = 'users.json'
    settings_path = 'user_settings.json'

    try:
        engine = create_engine(CONNECTION_STRING)
        print("Successfully connected to cloud database.")

        # --- Migrate Tasks from Excel ---
        print("Migrating tasks from Excel...")
        df_tasks = pd.read_excel(excel_path, sheet_name='DATA')
        # Ensure date columns are proper datetime objects
        df_tasks['START'] = pd.to_datetime(df_tasks['START'].astype(str).str.split(' ').str[0], errors='coerce')
        df_tasks['END'] = pd.to_datetime(df_tasks['END'].astype(str).str.split(' ').str[0], errors='coerce')
        df_tasks.to_sql('tasks', engine, if_exists='replace', index=False)
        print(f"Successfully migrated {len(df_tasks)} tasks.")

        # --- Migrate Users from JSON ---
        print("Migrating users from users.json...")
        with open(users_path, 'r') as f:
            users_data = json.load(f)
        users_list = [{'email': email, **data} for email, data in users_data.items()]
        df_users = pd.DataFrame(users_list)
        df_users.to_sql('users', engine, if_exists='replace', index=False)
        print(f"Successfully migrated {len(df_users)} users.")

        # --- Migrate Settings from JSON ---
        print("Migrating settings from user_settings.json...")
        with open(settings_path, 'r') as f:
            settings_data = json.load(f)
        settings_list = [{'email': email, **data} for email, data in settings_data.items()]
        df_settings = pd.DataFrame(settings_list)
        df_settings.to_sql('settings', engine, if_exists='replace', index=False)
        print(f"Successfully migrated {len(df_settings)} user settings.")
        
        # --- Create Changelog Table ---
        print("Creating empty changelog table...")
        df_changelog = pd.DataFrame(columns=['Timestamp', 'Action', 'Task ID', 'Field Changed', 'Old Value', 'New Value'])
        df_changelog.to_sql('changelog', engine, if_exists='replace', index=False)
        print("Changelog table created.")

        print("\nCloud migration complete!")

    except Exception as e:
        print(f"\nAn error occurred during migration: {e}")

if __name__ == "__main__":
    migrate()