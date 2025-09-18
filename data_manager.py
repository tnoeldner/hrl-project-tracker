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
        
        if 'START' in df.columns:
            df['START'] = pd.to_datetime(df['START'])
        if 'END' in df.columns:
            df['END'] = pd.to_datetime(df['END'])
            
        return df
    except Exception as e:
        st.error(f"Failed to load data from database. Error: {e}")
        return None

def save_and_log_changes(original_df, updated_df):
    """Compares, logs changes, and saves updated data back to the database."""
    try:
        with engine.connect() as conn:
            # --- LOGGING ---
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entries = []

            # Prepare DataFrames for comparison
            original_indexed = original_df.set_index('#', drop=False)
            updated_indexed = updated_df.set_index('#', drop=False)
            
            # Find changes... (this logic can be expanded)

            # --- SAVING ---
            # For simplicity, we replace the entire table with the updated data.
            updated_df.to_sql('tasks', conn, if_exists='replace', index=False)
        return True
    except Exception as e:
        st.error(f"Error saving data to database: {e}")
        return False