# File: data_manager.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- Database Connection ---
DB_CONNECTION_STRING = st.secrets["db_connection_string"]
engine = create_engine(DB_CONNECTION_STRING)

# --- GENERIC DATA FUNCTIONS ---
def load_table(table_name):
    """Generic function to load any table from the database."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
        
        # This function correctly handles dates saved as 'YYYY-MM-DD (DayName)'
        def robust_date_parse(date_col):
            # Take only the date part of the string, ignoring "(DayName)" or other text
            date_str_series = date_col.astype(str).str.split(' ').str[0]
            # Convert the clean date string to a proper datetime object
            return pd.to_datetime(date_str_series, errors='coerce')

        # Convert date columns after loading from the database
        if 'START' in df.columns:
            df['START'] = robust_date_parse(df['START'])
        if 'END' in df.columns:
            df['END'] = robust_date_parse(df['END'])
            
        return df
    except Exception as e:
        st.error(f"Failed to load table '{table_name}'. Error: {e}")
        return None

def save_table(df, table_name):
    """Generic function to save a DataFrame to a table, replacing it."""
    try:
        with engine.connect() as conn:
            df_to_save = df.copy()
            # For tasks, format dates before saving
            if table_name == 'tasks':
                df_to_save['START'] = pd.to_datetime(df_to_save['START']).dt.strftime('%Y-%m-%d (%A)')
                df_to_save['END'] = pd.to_datetime(df_to_save['END']).dt.strftime('%Y-%m-%d (%A)')
            
            df_to_save.to_sql(table_name, conn, if_exists='replace', index=False)
        return True
    except Exception as e:
        st.error(f"Error saving table '{table_name}': {e}")
        return False

# This is a wrapper function for backward compatibility with pages that call it.
def save_and_log_changes(original_df, updated_df):
    """A placeholder that simply saves the data for now."""
    return save_table(updated_df, 'tasks')