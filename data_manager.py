# File: data_manager.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- Database Connection ---
DB_CONNECTION_STRING = st.secrets["db_connection_string"]
engine = create_engine(DB_CONNECTION_STRING)

# --- Email Configuration ---
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL")
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

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

# --- FULLY IMPLEMENTED CHANGELOG FUNCTION ---
def save_and_log_changes(original_df, updated_df, user_email="system", source_page="Unknown"):
    """
    Compares two dataframes, logs the changes to the 'changelog' table,
    and then saves the updated 'tasks' table.
    """
    try:
        timestamp = datetime.now()
        log_entries = []

        # Use '#' as the index for comparison
        original_indexed = original_df.set_index('#')
        updated_indexed = updated_df.set_index('#')

        # 1. Find DELETED tasks
        deleted_ids = original_indexed.index.difference(updated_indexed.index)
        for task_id in deleted_ids:
            log_entries.append({
                'Timestamp': timestamp, 'Action': 'DELETE', 'Task ID': task_id,
                'User': user_email, 'Source': source_page, 'Field Changed': 'ENTIRE TASK', 
                'Old Value': original_indexed.loc[task_id]['TASK'], 'New Value': ''
            })

        # 2. Find ADDED tasks
        added_ids = updated_indexed.index.difference(original_indexed.index)
        for task_id in added_ids:
            log_entries.append({
                'Timestamp': timestamp, 'Action': 'ADD', 'Task ID': task_id,
                'User': user_email, 'Source': source_page, 'Field Changed': 'ENTIRE TASK', 
                'Old Value': '', 'New Value': updated_indexed.loc[task_id]['TASK']
            })

        # 3. Find EDITED tasks
        common_ids = original_indexed.index.intersection(updated_indexed.index)
        for task_id in common_ids:
            # align the columns before comparing to handle any reordering
            orig_series, updated_series = original_indexed.loc[task_id].align(updated_indexed.loc[task_id])
            # Fill NaN values to avoid errors on comparison
            diff = orig_series.fillna('').compare(updated_series.fillna(''), result_names=('old', 'new'))
            
            for field, values in diff.iterrows():
                # Don't log changes if both old and new values are empty
                if pd.notna(values['old']) or pd.notna(values['new']):
                    log_entries.append({
                        'Timestamp': timestamp, 'Action': 'EDIT', 'Task ID': task_id,
                        'User': user_email, 'Source': source_page, 'Field Changed': field, 
                        'Old Value': str(values['old']), 'New Value': str(values['new'])
                    })
        
        # Save the log if there are new entries
        if log_entries:
            changelog_df = load_table('changelog')
            new_log_df = pd.DataFrame(log_entries)
            if changelog_df is None:
                changelog_df = pd.DataFrame()
            
            combined_log = pd.concat([changelog_df, new_log_df], ignore_index=True)
            save_table(combined_log, 'changelog')
        
        # Finally, save the updated tasks table
        return save_table(updated_df, 'tasks')

    except Exception as e:
        st.error(f"Error during save and log operation: {e}")
        return False

# --- UPDATED Email Sending Function ---
def send_comment_email(recipient_email, author_email, task_details, comment_text):
    """Constructs and sends a single comment notification email with more details."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        st.error("Email credentials are not configured in secrets. Email cannot be sent.")
        return

    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = recipient_email
    message['Subject'] = f"New Comment on Task: {task_details['TASK']}"

    # Format dates for display
    start_date = pd.to_datetime(task_details['START']).strftime('%m-%d-%Y') if pd.notna(task_details['START']) else 'N/A'
    end_date = pd.to_datetime(task_details['END']).strftime('%m-%d-%Y') if pd.notna(task_details['END']) else 'N/A'

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; }}
            .comment {{ background-color: #f9f9f9; border-left: 5px solid #009A44; padding: 15px; margin-top: 15px; }}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ padding-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>New Comment Notification</h2>
            <p>Hi,</p>
            <p><b>{author_email}</b> left a new comment on a task assigned to you.</p>
            
            <h4>Task Details:</h4>
            <ul>
                <li><b>Task:</b> {task_details['TASK']}</li>
                <li><b>Planner Bucket:</b> {task_details['PLANNER BUCKET']}</li>
                <li><b>Fiscal Year:</b> {task_details['Fiscal Year']}</li>
                <li><b>Start Date:</b> {start_date}</li>
                <li><b>End Date:</b> {end_date}</li>
            </ul>

            <div class="comment">
                <p><b>Comment:</b></p>
                <p><i>"{comment_text}"</i></p>
            </div>
            <p>You can view this comment and reply in the HRL Project Tracker application.</p>
        </div>
    </body>
    </html>
    """
    message.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [recipient_email], message.as_string())
        server.quit()
    except Exception as e:
        st.error(f"Failed to send email to {recipient_email}: {e}")

# --- Comment & Notification Functions (no changes needed here) ---
def add_comment_and_notify(task_id, author_email, comment_text, assigned_title, additional_recipients_emails=None):
    # This function's logic remains the same, it will now call the updated send_comment_email function.
    comments_df = load_table('comments')
    if comments_df is None:
        comments_df = pd.DataFrame(columns=['comment_id', 'task_id', 'user_email', 'timestamp', 'comment_text'])
    
    new_comment_id = comments_df['comment_id'].max() + 1 if not comments_df.empty else 1
    new_comment = pd.DataFrame([{'comment_id': new_comment_id, 'task_id': task_id, 'user_email': author_email, 'timestamp': datetime.now(), 'comment_text': comment_text}])
    updated_comments = pd.concat([comments_df, new_comment], ignore_index=True)
    save_table(updated_comments, 'comments')

    users_df = load_table('users')
    tasks_df = load_table('tasks')
    task_details = tasks_df[tasks_df['#'] == task_id].iloc[0]
    recipients_to_notify = set()

    assigned_user = users_df[users_df['assignment_title'] == assigned_title]
    if not assigned_user.empty:
        primary_recipient_email = assigned_user.iloc[0]['email']
        if primary_recipient_email != author_email:
            recipients_to_notify.add(primary_recipient_email)

    if additional_recipients_emails:
        for email in additional_recipients_emails:
            if email != author_email:
                recipients_to_notify.add(email)
    
    if recipients_to_notify:
        notifications_df = load_table('notifications')
        if notifications_df is None:
            notifications_df = pd.DataFrame(columns=['notification_id', 'user_email', 'message', 'is_read', 'timestamp'])
        
        new_notifications = []
        last_id = notifications_df['notification_id'].max() if not notifications_df.empty else 0

        for recipient_email in recipients_to_notify:
            send_comment_email(recipient_email, author_email, task_details, comment_text)
            
            last_id += 1
            header = f"New comment from {author_email} on task #{task_id}"
            message = f"{header} |:| {comment_text}"
            new_notifications.append({'notification_id': last_id, 'user_email': recipient_email, 'message': message, 'is_read': False, 'timestamp': datetime.now()})
        
        if new_notifications:
            new_notifications_df = pd.DataFrame(new_notifications)
            updated_notifications = pd.concat([notifications_df, new_notifications_df], ignore_index=True)
            save_table(updated_notifications, 'notifications')

def get_comments_for_task(task_id):
    comments_df = load_table('comments')
    if comments_df is not None:
        return comments_df[comments_df['task_id'].astype(str) == str(task_id)].sort_values(by='timestamp', ascending=False)
    return pd.DataFrame()

def get_unread_notifications(user_email):
    notifications_df = load_table('notifications')
    if notifications_df is not None:
        return notifications_df[(notifications_df['user_email'] == user_email) & (notifications_df['is_read'] == False)]
    return pd.DataFrame()

