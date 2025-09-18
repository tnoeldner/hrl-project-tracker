# File: data_manager.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- Database Connection ---
# This safely reads the connection string from Streamlit's Secrets Management.
DB_CONNECTION_STRING = st.secrets["db_connection_string"]
engine = create_engine(DB_CONNECTION_STRING)

def load_data(table_name='tasks'):
    """Loads data from a specified table in the cloud database."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
        
        # Convert date columns after loading from the database
        if 'START' in df.columns:
            df['START'] = pd.to_datetime(df['START'], errors='coerce')
        if 'END' in df.columns:
            df['END'] = pd.to_datetime(df['END'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Failed to load data from database. Is the data migrated? Error: {e}")
        return None

def save_data(df, filepath=None): # Filepath is no longer used but kept for compatibility
    """Saves the updated DataFrame back to the cloud database."""
    try:
        with engine.connect() as conn:
            # Replace the entire 'tasks' table with the updated data.
            df.to_sql('tasks', conn, if_exists='replace', index=False, method='multi')
        return True
    except Exception as e:
        st.error(f"Error saving data to database: {e}")
        return False

# You can expand this later to include logging if you wish
def save_and_log_changes(original_df, updated_df):
    """A placeholder that simply saves the data for now."""
    return save_data(updated_df)