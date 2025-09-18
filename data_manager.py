# File: data_manager.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- Database Connection ---
# This safely reads the connection string from Streamlit's Secrets Management.
DB_CONNECTION_STRING = st.secrets["db_connection_string"]
engine = create_engine(DB_CONNECTION_STRING)

# --- THE SINGLE SOURCE OF TRUTH FOR LOADING DATA ---
def load_table(table_name):
    """
    The official function to load any table from the database.
    It includes robust parsing for dates and default values for other columns.
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
        
        # This logic applies only to the 'tasks' table
        if table_name == 'tasks':
            # This function correctly handles dates saved as 'YYYY-MM-DD (DayName)' or any other format
            def robust_date_parse(date_col):
                # Take only the date part of the string, ignoring "(DayName)" or other text
                date_str_series = date_col.astype(str).str.split(' ').str[0]
                # Convert the clean date string to a proper datetime object, coercing errors
                return pd.to_datetime(date_str_series, errors='coerce')

            # Apply the robust parsing to the date columns
            if 'START' in df.columns:
                df['START'] = robust_date_parse(df['START'])
            if 'END' in df.columns:
                df['END'] = robust_date_parse(df['END'])
            
            # Handle the PROGRESS column, defaulting any blank values to 'NOT STARTED'
            if 'PROGRESS' in df.columns:
                df['PROGRESS'] = df['PROGRESS'].fillna('NOT STARTED')
            else:
                df['PROGRESS'] = 'NOT STARTED'
            
        return df
    except Exception as e:
        st.error(f"Failed to load table '{table_name}'. Is your database set up correctly? Error: {e}")
        return None

# --- THE SINGLE SOURCE OF TRUTH FOR SAVING DATA ---
def save_table(df, table_name):
    """
    The official function to save any DataFrame to a table, replacing it.
    It correctly formats dates for the 'tasks' table before saving.
    """
    try:
        with engine.connect() as conn:
            df_to_save = df.copy()
            # For tasks, format dates to the consistent 'YYYY-MM-DD (DayName)' format before saving
            if table_name == 'tasks':
                df_to_save['START'] = pd.to_datetime(df_to_save['START']).dt.strftime('%Y-%m-%d (%A)')
                df_to_save['END'] = pd.to_datetime(df_to_save['END']).dt.strftime('%Y-%m-%d (%A)')
            
            df_to_save.to_sql(table_name, conn, if_exists='replace', index=False, method='multi')
        return True
    except Exception as e:
        st.error(f"Error saving table '{table_name}': {e}")
        return False

# --- Wrapper function for backward compatibility ---
def save_and_log_changes(original_df, updated_df):
    """
    This is now a simple wrapper around the main save function.
    The detailed logging logic can be re-implemented here later if needed.
    """
    return save_table(updated_df, 'tasks')