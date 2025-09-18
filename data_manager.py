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
        # Convert date columns if they exist in the loaded table
        if 'START' in df.columns:
            df['START'] = pd.to_datetime(df['START'])
        if 'END' in df.columns:
            df['END'] = pd.to_datetime(df['END'])
        return df
    except Exception as e:
        st.error(f"Failed to load table '{table_name}'. Error: {e}")
        return None

def save_table(df, table_name):
    """Generic function to save a DataFrame to a table, replacing it."""
    try:
        with engine.connect() as conn:
            # For tasks, format dates before saving
            if table_name == 'tasks':
                df['START'] = pd.to_datetime(df['START']).dt.strftime('%Y-%m-%d (%A)')
                df['END'] = pd.to_datetime(df['END']).dt.strftime('%Y-%m-%d (%A)')
            
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        return True
    except Exception as e:
        st.error(f"Error saving table '{table_name}': {e}")
        return False

# --- TASK-SPECIFIC FUNCTIONS (for logging) ---
def save_and_log_changes(original_df, updated_df):
    """Compares, logs changes, and saves updated tasks."""
    # This can be expanded later to re-implement detailed logging
    return save_table(updated_df, 'tasks')