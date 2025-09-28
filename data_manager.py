# File: data_manager.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- Database Connection ---
# This safely reads the connection string from Streamlit's Secrets Management.
DB_CONNECTION_STRING = st.secrets["db_connection_string"]
engine = create_engine(DB_CONNECTION_STRING)

# --- THE STABLE DATA LOADING FUNCTION ---
def load_table(table_name):
    """
    Loads any table from the database and correctly handles dates for the 'tasks' table.
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
        
        # This logic applies only to the 'tasks' table
        if table_name == 'tasks':
            # Use pandas' powerful to_datetime, coercing any errors to NaT (Not a Time).
            if 'START' in df.columns:
                df['START'] = pd.to_datetime(df['START'], errors='coerce')
            if 'END' in df.columns:
                df['END'] = pd.to_datetime(df['END'], errors='coerce')
            
            # Handle the PROGRESS column, defaulting blank values
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
    Saves any DataFrame to a table, replacing it. It saves raw datetime objects,
    which is the correct and most stable method.
    """
    try:
        with engine.connect() as conn:
            # We no longer apply string formatting here. We save the proper datetime objects.
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

# --- NEW: Comment & Notification Functions ---

def add_comment(task_id, user_email, comment_text):
    """Adds a new comment to the database."""
    comments_df = load_table('comments')
    if comments_df is None: # If table is empty or fails to load
        comments_df = pd.DataFrame(columns=['comment_id', 'task_id', 'user_email', 'timestamp', 'comment_text'])

    new_comment_id = comments_df['comment_id'].max() + 1 if not comments_df.empty else 1
    
    new_comment = pd.DataFrame([{
        "comment_id": new_comment_id,
        "task_id": task_id,
        "user_email": user_email,
        "timestamp": datetime.now(),
        "comment_text": comment_text
    }])
    
    updated_comments = pd.concat([comments_df, new_comment], ignore_index=True)
    return save_table(updated_comments, 'comments')

def get_comments_for_task(task_id):
    """Retrieves all comments for a specific task ID."""
    comments_df = load_table('comments')
    if comments_df is not None:
        # Ensure task_id is the same data type for comparison
        return comments_df[comments_df['task_id'].astype(str) == str(task_id)].sort_values(by='timestamp')
    return pd.DataFrame() # Return empty dataframe if no comments or error



