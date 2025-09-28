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
            # This is the most reliable method for reading dates from any source.
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
    # The detailed changelog logic can be re-implemented here later if desired.
    return save_table(updated_df, 'tasks')

# --- Comment & Notification Functions ---

def add_comment_and_notify(task_id, author_email, comment_text, assigned_title):
    """Adds a comment and creates a notification for the assigned user."""
    # 1. Add the comment
    comments_df = load_table('comments')
    if comments_df is None: # If table is empty or fails to load
        comments_df = pd.DataFrame(columns=['comment_id', 'task_id', 'user_email', 'timestamp', 'comment_text'])

    new_comment_id = comments_df['comment_id'].max() + 1 if not comments_df.empty else 1
    
    new_comment = pd.DataFrame([{
        "comment_id": new_comment_id,
        "task_id": task_id,
        "user_email": author_email,
        "timestamp": datetime.now(),
        "comment_text": comment_text
    }])
    
    updated_comments = pd.concat([comments_df, new_comment], ignore_index=True)
    save_table(updated_comments, 'comments')

    # 2. Create a notification for the user assigned to the task
    users_df = load_table('users')
    assigned_user = users_df[users_df['assignment_title'] == assigned_title]
    
    if not assigned_user.empty:
        recipient_email = assigned_user.iloc[0]['email']
        # Don't notify the user if they commented on their own task
        if recipient_email != author_email:
            notifications_df = load_table('notifications')
            if notifications_df is None:
                notifications_df = pd.DataFrame(columns=['notification_id', 'user_email', 'message', 'is_read', 'timestamp'])
            
            new_notification_id = notifications_df['notification_id'].max() + 1 if not notifications_df.empty else 1
            
            # Create a detailed message for the notification
            header = f"New comment from {author_email} on task #{task_id}"
            message = f"{header} |:| {comment_text}"
            
            new_notification = pd.DataFrame([{'notification_id': new_notification_id, 'user_email': recipient_email, 'message': message, 'is_read': False, 'timestamp': datetime.now()}])
            updated_notifications = pd.concat([notifications_df, new_notification], ignore_index=True)
            save_table(updated_notifications, 'notifications')

def get_comments_for_task(task_id):
    """Retrieves all comments for a specific task ID."""
    comments_df = load_table('comments')
    if comments_df is not None:
        # Ensure task_id is the same data type for comparison
        return comments_df[comments_df['task_id'].astype(str) == str(task_id)].sort_values(by='timestamp', ascending=False)
    return pd.DataFrame() # Return empty dataframe if no comments or error

def get_unread_notifications(user_email):
    """Gets a DataFrame of unread notifications for a user."""
    notifications_df = load_table('notifications')
    if notifications_df is not None:
        return notifications_df[(notifications_df['user_email'] == user_email) & (notifications_df['is_read'] == False)]
    return pd.DataFrame()


