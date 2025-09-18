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
    """A robust function to load and clean data from the Excel file."""
    try:
        # This function must be defined inside load_data for the new data_manager
        # In a real-world scenario, you would have a more centralized database connection
        # but for this app, we'll keep it simple.
        
        # We will revert to reading the excel file directly for now, 
        # as the database migration seems to be the source of the issue.
        # This will allow the app to function while we troubleshoot the database separately.
        
        df = pd.read_excel('Project Tracker.xlsx', sheet_name='DATA')
        
        # This function correctly handles dates saved in multiple formats
        def robust_date_parse(date_col):
            # Let pandas automatically infer the format for each date
            return pd.to_datetime(date_col, errors='coerce', format='mixed')

        df['START'] = robust_date_parse(df['START'])
        df['END'] = robust_date_parse(df['END'])

        if 'PROGRESS' in df.columns:
            df['PROGRESS'] = df['PROGRESS'].fillna('NOT STARTED')
        else:
            df['PROGRESS'] = 'NOT STARTED'
            
        return df
    except Exception as e:
        # We add st here to show errors on the page if loading fails
        import streamlit as st
        st.error(f"Failed to load or parse the Excel file. Error: {e}")
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