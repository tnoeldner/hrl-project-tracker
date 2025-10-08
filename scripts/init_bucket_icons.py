"""Create or populate the `bucket_icons` table if it's missing.

This script uses the project's `data_manager` to save the table so it respects
the configured DB connection (Streamlit secrets or fallback sqlite).
"""
import pandas as pd
import data_manager


def main():
    print('Checking for existing bucket_icons table...')
    icons_df = data_manager.load_table('bucket_icons')
    if icons_df is not None and not icons_df.empty:
        print('bucket_icons already exists with', len(icons_df), 'rows. Nothing to do.')
        return

    # Try to derive buckets from tasks table
    tasks_df = data_manager.load_table('tasks')
    if tasks_df is None or tasks_df.empty:
        print('No tasks table or no tasks found. Creating a default bucket_icons table.')
        icons_df = pd.DataFrame([{'bucket_name': 'Default', 'icon': '📌'}])
    else:
        buckets = sorted(set(tasks_df['PLANNER BUCKET'].dropna().unique()))
        if not buckets:
            icons_df = pd.DataFrame([{'bucket_name': 'Default', 'icon': '📌'}])
        else:
            icons_df = pd.DataFrame([{'bucket_name': b, 'icon': '📌'} for b in buckets])

    saved = data_manager.save_table(icons_df, 'bucket_icons')
    if saved:
        print('bucket_icons table created/populated with', len(icons_df), 'rows.')
    else:
        print('Failed to create bucket_icons table. Check logs for details.')


if __name__ == '__main__':
    main()
