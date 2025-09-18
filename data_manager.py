# File: data_manager.py
import pandas as pd
from datetime import datetime
import streamlit as st

FILEPATH = 'Project Tracker.xlsx'

def load_data():
    """A robust function to load and clean data from the Excel file."""
    try:
        df = pd.read_excel(FILEPATH, sheet_name='DATA')
        def robust_date_parse(date_col):
            date_str_series = date_col.astype(str).str.split(' ').str[0]
            return pd.to_datetime(date_str_series, errors='coerce')
        df['START'] = robust_date_parse(df['START'])
        df['END'] = robust_date_parse(df['END'])
        if 'PROGRESS' in df.columns:
            df['PROGRESS'] = df['PROGRESS'].fillna('NOT STARTED')
        else:
            df['PROGRESS'] = 'NOT STARTED'
        return df
    except Exception as e:
        st.error(f"Failed to load or parse Excel file. Error: {e}")
        return None

def save_and_log_changes(original_df, updated_df):
    """Compares two dataframes, logs the changes, and saves the updated data."""
    try:
        # --- LOGGING ---
        log_entries = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Set '#' as index for easy comparison
        original_df.set_index('#', inplace=True, drop=False)
        updated_df.set_index('#', inplace=True, drop=False)

        # 1. Find DELETED tasks
        deleted_ids = original_df.index.difference(updated_df.index)
        for task_id in deleted_ids:
            log_entries.append({
                'Timestamp': timestamp, 'Action': 'DELETE', 'Task ID': task_id,
                'Field Changed': 'ENTIRE TASK', 'Old Value': original_df.loc[task_id]['ASSIGNMENT TITLE'], 'New Value': ''
            })

        # 2. Find ADDED tasks
        added_ids = updated_df.index.difference(original_df.index)
        for task_id in added_ids:
            log_entries.append({
                'Timestamp': timestamp, 'Action': 'ADD', 'Task ID': task_id,
                'Field Changed': 'ENTIRE TASK', 'Old Value': '', 'New Value': updated_df.loc[task_id]['ASSIGNMENT TITLE']
            })

        # 3. Find EDITED tasks
        common_ids = original_df.index.intersection(updated_df.index)
        for task_id in common_ids:
            diff = original_df.loc[task_id].compare(updated_df.loc[task_id], result_names=('old', 'new'))
            for field, values in diff.iterrows():
                log_entries.append({
                    'Timestamp': timestamp, 'Action': 'EDIT', 'Task ID': task_id,
                    'Field Changed': field, 'Old Value': values['old'], 'New Value': values['new']
                })
        
        # Save the log if there are new entries
        if log_entries:
            try:
                log_df = pd.read_excel(FILEPATH, sheet_name='Changelog')
                new_log_df = pd.DataFrame(log_entries)
                combined_log = pd.concat([log_df, new_log_df], ignore_index=True)
            except FileNotFoundError:
                combined_log = pd.DataFrame(log_entries)
            
            with pd.ExcelWriter(FILEPATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                combined_log.to_excel(writer, sheet_name='Changelog', index=False)
        
        # --- SAVING ---
        df_to_save = updated_df.reset_index(drop=True)
        df_to_save['START'] = pd.to_datetime(df_to_save['START']).dt.strftime('%Y-%m-%d (%A)')
        df_to_save['END'] = pd.to_datetime(df_to_save['END']).dt.strftime('%Y-%m-%d (%A)')

        with pd.ExcelWriter(FILEPATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_to_save.to_excel(writer, sheet_name='DATA', index=False)
            
        return True

    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False