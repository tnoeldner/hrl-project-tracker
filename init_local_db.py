#!/usr/bin/env python3
"""
init_local_db.py

Initialize a local SQLite database (project_tracker.db) for development.
It reads `Project Tracker.xlsx` (sheet 'DATA') for tasks, plus `users.json` and
`user_settings.json` for users/settings. It also creates supportive tables:
`bucket_icons`, `comments`, `changelog`, `notifications` if missing.

Run:
    python init_local_db.py
"""
import os
import json
from sqlalchemy import create_engine
import pandas as pd


def robust_date_parse(date_col):
    # Take only the date part of the string, ignoring "(DayName)" or other text
    date_str_series = date_col.astype(str).str.split(' ').str[0]
    return pd.to_datetime(date_str_series, errors='coerce')


def main():
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, 'project_tracker.db')
    excel_path = os.path.join(base_dir, 'Project Tracker.xlsx')
    users_json_path = os.path.join(base_dir, 'users.json')
    settings_json_path = os.path.join(base_dir, 'user_settings.json')

    print(f"Initializing local DB at: {db_path}")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    # --- Tasks ---
    if os.path.exists(excel_path):
        print(f"Loading tasks from Excel: {excel_path}")
        try:
            df_tasks = pd.read_excel(excel_path, sheet_name='DATA')
        except Exception as e:
            print(f"Failed to read Excel sheet 'DATA': {e}")
            return

        # Ensure dates parsed
        if 'START' in df_tasks.columns:
            df_tasks['START'] = robust_date_parse(df_tasks['START'])
        if 'END' in df_tasks.columns:
            df_tasks['END'] = robust_date_parse(df_tasks['END'])

        # Ensure there is a '#' id column
        if '#' not in df_tasks.columns:
            df_tasks.insert(0, '#', range(1, len(df_tasks) + 1))

        df_tasks.to_sql('tasks', engine, if_exists='replace', index=False)
        print(f"Wrote {len(df_tasks)} tasks to 'tasks' table.")
    else:
        print(f"Excel file not found at {excel_path}. Skipping tasks import.")

    # --- Users ---
    if os.path.exists(users_json_path):
        print(f"Loading users from: {users_json_path}")
        with open(users_json_path, 'r', encoding='utf-8') as f:
            users_raw = json.load(f)

        users_rows = []
        for email, info in users_raw.items():
            users_rows.append({
                'email': email,
                'password': info.get('password', ''),
                'first_name': info.get('first_name', ''),
                'last_name': info.get('last_name', ''),
                'assignment_title': info.get('assignment_title', ''),
                'role': info.get('role', ''),
                'status': info.get('status', 'active')
            })

        df_users = pd.DataFrame(users_rows)
        df_users.to_sql('users', engine, if_exists='replace', index=False)
        print(f"Wrote {len(df_users)} users to 'users' table.")
    else:
        print(f"users.json not found at {users_json_path}. Creating empty 'users' table.")
        pd.DataFrame(columns=['email','password','first_name','last_name','assignment_title','role','status']).to_sql('users', engine, if_exists='replace', index=False)

    # --- Settings ---
    if os.path.exists(settings_json_path):
        print(f"Loading settings from: {settings_json_path}")
        with open(settings_json_path, 'r', encoding='utf-8') as f:
            settings_raw = json.load(f)

        settings_rows = []
        for email, info in settings_raw.items():
            settings_rows.append({'email': email, 'frequency': info.get('frequency', 'Never')})

        df_settings = pd.DataFrame(settings_rows)
        df_settings.to_sql('settings', engine, if_exists='replace', index=False)
        print(f"Wrote {len(df_settings)} rows to 'settings' table.")
    else:
        print(f"user_settings.json not found. Creating empty 'settings' table.")
        pd.DataFrame(columns=['email','frequency']).to_sql('settings', engine, if_exists='replace', index=False)

    # --- Bucket icons (deduce from tasks) ---
    try:
        df_tasks = pd.read_sql_query('SELECT * FROM tasks', engine)
        bucket_names = []
        if 'PLANNER BUCKET' in df_tasks.columns:
            bucket_names = sorted(df_tasks['PLANNER BUCKET'].dropna().unique().tolist())
        else:
            bucket_names = ['Default']

        icons_rows = [{'bucket_name': b, 'icon': '📌'} for b in bucket_names]
        df_icons = pd.DataFrame(icons_rows)
        df_icons.to_sql('bucket_icons', engine, if_exists='replace', index=False)
        print(f"Wrote {len(df_icons)} bucket icons to 'bucket_icons' table.")
    except Exception as e:
        print(f"Could not create bucket_icons: {e}")

    # --- Comments, changelog, notifications (empty skeletons) ---
    pd.DataFrame(columns=['comment_id', 'task_id', 'user_email', 'timestamp', 'comment_text']).to_sql('comments', engine, if_exists='replace', index=False)
    pd.DataFrame(columns=['Timestamp','Action','Task ID','User','Source','Field Changed','Old Value','New Value']).to_sql('changelog', engine, if_exists='replace', index=False)
    pd.DataFrame(columns=['notification_id','user_email','message','is_read','timestamp']).to_sql('notifications', engine, if_exists='replace', index=False)
    # --- Filter presets ---
    pd.DataFrame(columns=['preset_id','user_email','preset_name','years','buckets','created_at']).to_sql('filter_presets', engine, if_exists='replace', index=False)
    print("Created empty 'comments', 'changelog', and 'notifications' tables.")

    print("Local DB initialization complete.")


if __name__ == '__main__':
    main()
