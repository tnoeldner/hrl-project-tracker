# File: data_manager.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- Database Connection with Debug Check ---
# This checks for the secret and provides a clear error if it's missing locally.
if "db_connection_string" in st.secrets:
    DB_CONNECTION_STRING = st.secrets["db_connection_string"]
    engine = create_engine(DB_CONNECTION_STRING)
else:
    st.error("Database connection string not found in secrets.")
    st.info("""
        **To run this app locally, you must create a secrets file with your database password.**
        1.  In your main `ProjectReporter` folder, create a new folder named `.streamlit`.
        2.  Inside the `.streamlit` folder, create a new file named `secrets.toml`.
        3.  Paste your database connection string into that file, like this:
            ```
            db_connection_string = "postgresql://postgres:[YOUR-PASSWORD]@..."
            ```
        **This file should be listed in your `.gitignore` file to keep it secure.**
    """)
    st.stop() # Stop the app from running further if secrets are missing.

# --- THE STABLE DATA LOADING FUNCTION ---
def load_table(table_name):
    """
    Loads any table from the database and correctly handles dates for the 'tasks' table.
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
        
        if table_name == 'tasks':
            if 'START' in df.columns:
                df['START'] = pd.to_datetime(df['START'], errors='coerce')
            if 'END' in df.columns:
                df['END'] = pd.to_datetime(df['END'], errors='coerce')
            if 'PROGRESS' in df.columns:
                df['PROGRESS'] = df['PROGRESS'].fillna('NOT STARTED')
            else:
                df['PROGRESS'] = 'NOT STARTED'
        return df
    except Exception as e:
        st.error(f"Failed to load table '{table_name}'. Is your database set up? Error: {e}")
        return None

# --- THE STABLE DATA SAVING FUNCTION ---
def save_table(df, table_name):
    """
    Saves any DataFrame to a table, replacing it. It saves raw datetime objects.
    """
    try:
        with engine.connect() as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False, method='multi')
        return True
    except Exception as e:
        st.error(f"Error saving table '{table_name}': {e}")
        return False

# --- Wrapper function for backward compatibility ---
def save_and_log_changes(original_df, updated_df):
    """
    This is a simple wrapper around the main save function.
    """
    return save_table(updated_df, 'tasks')

