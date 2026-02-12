# File: data_manager.py
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from icalendar import Calendar, Event
import uuid
import os
import json
import sqlite3
try:
    import boto3
    from botocore.exceptions import BotoCoreError, NoCredentialsError
    _BOTO3_AVAILABLE = True
except Exception:
    _BOTO3_AVAILABLE = False

def _safe_secret(key, default=None):
    """Return secret value or default without raising if secrets.toml is missing."""
    try:
        # Use indexing to allow Streamlit's secrets mapping to raise if key missing,
        # but catch the 'no secrets file' condition which raises StreamlitSecretNotFoundError.
        return st.secrets[key]
    except StreamlitSecretNotFoundError:
        return default
    except Exception:
        # Any other issue (missing key) -> return default
        return default

# --- Database Connection ---
# Prefer explicit secret access but handle missing secrets.toml gracefully.
DB_CONNECTION_STRING = _safe_secret("db_connection_string")

# Fallback to a local SQLite file for development if no connection string is provided.
if not DB_CONNECTION_STRING:
    base_dir = os.path.dirname(__file__)
    sqlite_path = os.path.join(base_dir, 'project_tracker.db')
    DB_CONNECTION_STRING = f"sqlite:///{sqlite_path}"
    # Avoid raising during import; show a friendly informational message if Streamlit is running
    try:
        st.info(f"No Streamlit secrets found; using local SQLite DB at {sqlite_path}")
    except Exception:
        # If st isn't fully initialized (tests, import-time), don't fail.
        pass

# For sqlite, include connect_args to be safe in multi-threaded contexts
if DB_CONNECTION_STRING.startswith('sqlite'):
    engine = create_engine(DB_CONNECTION_STRING, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DB_CONNECTION_STRING)

# Flag to indicate we auto-created the bucket_icons table on this run
BUCKET_ICONS_AUTO_CREATED = False
# Flag to indicate we auto-created the notifications table on this run
NOTIFICATIONS_AUTO_CREATED = False

def pop_bucket_icons_auto_created():
    """Return True if bucket_icons was auto-created during this process, then reset the flag."""
    global BUCKET_ICONS_AUTO_CREATED
    val = BUCKET_ICONS_AUTO_CREATED
    BUCKET_ICONS_AUTO_CREATED = False
    return val


def pop_notifications_auto_created():
    """Return True if notifications was auto-created during this process, then reset the flag."""
    global NOTIFICATIONS_AUTO_CREATED
    val = NOTIFICATIONS_AUTO_CREATED
    NOTIFICATIONS_AUTO_CREATED = False
    return val

# --- Email Configuration ---
# Use the safe _safe_secret so missing secrets don't raise on import
SENDER_EMAIL = _safe_secret("SENDER_EMAIL")
SENDER_PASSWORD = _safe_secret("SENDER_PASSWORD")
SMTP_SERVER = _safe_secret("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(_safe_secret("SMTP_PORT", 587))

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
        # Auto-create the bucket_icons table if it doesn't exist (common first-run issue)
        msg = str(e).lower()
        if table_name == 'bucket_icons' and ('no such table' in msg or isinstance(e, OperationalError)):
            try:
                # Try to build icons from existing tasks table
                tasks_df = None
                try:
                    tasks_df = load_table('tasks')
                except Exception:
                    tasks_df = None

                if tasks_df is not None and not tasks_df.empty:
                    buckets = sorted(set(tasks_df['PLANNER BUCKET'].dropna().unique()))
                    if buckets:
                        icons_df = pd.DataFrame([{'bucket_name': b, 'icon': '📌'} for b in buckets])
                    else:
                        icons_df = pd.DataFrame([{'bucket_name': 'Default', 'icon': '📌'}])
                else:
                    icons_df = pd.DataFrame([{'bucket_name': 'Default', 'icon': '📌'}])

                # Mark that we auto-created this table during this run
                global BUCKET_ICONS_AUTO_CREATED
                BUCKET_ICONS_AUTO_CREATED = True
                if save_table(icons_df, 'bucket_icons'):
                    append_changelog_entry(action='ADD', source='Auto-Create', field_changed='bucket_icons', old_value='', new_value=f'Created {len(icons_df)} buckets', user='system')
                    return icons_df
                return None
            except Exception as ee:
                # If creation fails, show the original error as well as the creation error
                try:
                    st.error(f"Failed to create default 'bucket_icons' table. Original error: {e}; Creation error: {ee}")
                except Exception:
                    pass
                return None

        # Auto-create a basic notifications table if missing
        if table_name == 'notifications' and ('no such table' in msg or isinstance(e, OperationalError)):
            try:
                notifications_df = pd.DataFrame(columns=['notification_id', 'user_email', 'message', 'is_read', 'timestamp'])
                global NOTIFICATIONS_AUTO_CREATED
                NOTIFICATIONS_AUTO_CREATED = True
                if save_table(notifications_df, 'notifications'):
                    append_changelog_entry(action='ADD', source='Auto-Create', field_changed='notifications', old_value='', new_value='Created notifications table', user='system')
                    return notifications_df
                return None
            except Exception as ee:
                try:
                    st.error(f"Failed to create default 'notifications' table. Original error: {e}; Creation error: {ee}")
                except Exception:
                    pass
                return None
        # Auto-create a basic comments table if missing
        if table_name == 'comments' and ('no such table' in msg or isinstance(e, OperationalError)):
            try:
                comments_df = pd.DataFrame(columns=['comment_id', 'task_id', 'user_email', 'timestamp', 'comment_text'])
                if save_table(comments_df, 'comments'):
                    append_changelog_entry(action='ADD', source='Auto-Create', field_changed='comments', old_value='', new_value='Created comments table', user='system')
                    return comments_df
                return None
            except Exception as ee:
                try:
                    st.error(f"Failed to create default 'comments' table. Original error: {e}; Creation error: {ee}")
                except Exception:
                    pass
                return None

        try:
            st.error(f"Failed to load table '{table_name}'. Is your database set up? Error: {e}")
        except Exception:
            # If Streamlit isn't available, just print to stdout
            print(f"Failed to load table '{table_name}'. Error: {e}")
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


def append_changelog_entry(action, source, field_changed, old_value, new_value, user="system"):
    """Append a single changelog entry to the changelog table."""
    try:
        changelog_df = load_table('changelog')
        if changelog_df is None:
            changelog_df = pd.DataFrame()
        entry = {
            'Timestamp': datetime.now(),
            'Action': action,
            'Task ID': 'N/A',
            'User': user,
            'Source': source,
            'Field Changed': field_changed,
            'Old Value': old_value,
            'New Value': new_value
        }
        combined = pd.concat([changelog_df, pd.DataFrame([entry])], ignore_index=True)
        save_table(combined, 'changelog')
        return True
    except Exception as e:
        try:
            st.error(f"Failed to append changelog entry: {e}")
        except Exception:
            pass
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

        def _ensure_df(selection):
            """Normalize selection to a DataFrame to avoid Series leaking into log payloads."""
            if isinstance(selection, pd.Series):
                return selection.to_frame().T
            return selection if isinstance(selection, pd.DataFrame) else pd.DataFrame()

        def _format_log_value(val):
            if isinstance(val, pd.Timestamp):
                return val.strftime('%Y-%m-%d') if not pd.isna(val) else ''
            if pd.isna(val):
                return ''
            return str(val)

        # Use '#' as the index for comparison
        original_indexed = original_df.set_index('#')
        updated_indexed = updated_df.set_index('#')

        # 1. Find DELETED tasks
        deleted_ids = original_indexed.index.difference(updated_indexed.index)
        for task_id in deleted_ids:
            orig_rows = _ensure_df(original_indexed.loc[task_id])
            for _, orig_row in orig_rows.iterrows():
                fy = orig_row.get('Fiscal Year', '')
                fy_display = _format_log_value(fy)
                task_name = orig_row.get('TASK', '')
                log_entries.append({
                    'Timestamp': timestamp,
                    'Action': 'DELETE',
                    'Task ID': task_id,
                    'User': user_email,
                    'Source': f"{source_page} (FY: {fy_display})" if fy_display else source_page,
                    'Field Changed': 'ENTIRE TASK',
                    'Old Value': _format_log_value(task_name),
                    'New Value': ''
                })

        # 2. Find ADDED tasks
        added_ids = updated_indexed.index.difference(original_indexed.index)
        for task_id in added_ids:
            new_rows = _ensure_df(updated_indexed.loc[task_id])
            for _, new_row in new_rows.iterrows():
                fy = new_row.get('Fiscal Year', '')
                fy_display = _format_log_value(fy)
                task_name = new_row.get('TASK', '')
                log_entries.append({
                    'Timestamp': timestamp,
                    'Action': 'ADD',
                    'Task ID': task_id,
                    'User': user_email,
                    'Source': f"{source_page} (FY: {fy_display})" if fy_display else source_page,
                    'Field Changed': 'ENTIRE TASK',
                    'Old Value': '',
                    'New Value': _format_log_value(task_name)
                })

        # 3. Find EDITED tasks (handle multiple fiscal years per task_id)
        common_ids = original_indexed.index.intersection(updated_indexed.index)
        for task_id in common_ids:
            orig_task_rows = original_indexed.loc[original_indexed.index == task_id]
            updated_task_rows = updated_indexed.loc[updated_indexed.index == task_id]

            for _, orig_row in orig_task_rows.iterrows():
                orig_fy = orig_row.get('Fiscal Year')
                orig_task_name = orig_row.get('TASK')

                updated_row_match = updated_task_rows[
                    (updated_task_rows['Fiscal Year'] == orig_fy) &
                    (updated_task_rows['TASK'] == orig_task_name)
                ]

                if not updated_row_match.empty:
                    updated_row = updated_row_match.iloc[0]
                    for col in original_df.columns:
                        if col not in ['#', 'id']:
                            old_val = orig_row.get(col)
                            new_val = updated_row.get(col)
                            if str(old_val) != str(new_val):
                                log_entries.append({
                                    'Timestamp': timestamp, 'Action': 'EDIT', 'Task ID': task_id,
                                    'User': user_email, 'Source': f"{source_page} (FY: {orig_fy})", 'Field Changed': col, 
                                    'Old Value': _format_log_value(old_val), 'New Value': _format_log_value(new_val)
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
        saved = save_table(updated_df, 'tasks')

        # If save succeeded, regenerate public ICS calendar (best-effort)
        if saved:
            try:
                generate_and_publish_ics(updated_df)
            except Exception as e:
                # Non-fatal: ICS generation/publish should not block data save
                st.warning(f"Calendar (.ics) generation failed: {e}")

        return saved

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


# --- Filter preset helpers (per-user) ---
def get_filter_presets(user_email):
    """Return a DataFrame of saved filter presets for the given user."""
    try:
        df = load_table('filter_presets')
        if df is None or df.empty:
            return pd.DataFrame()
        return df[df['user_email'] == user_email].sort_values(by='created_at', ascending=False)
    except Exception:
        return pd.DataFrame()


def save_filter_preset(user_email, preset_name, years_list, buckets_list):
    """Save or update a named preset for a user. years_list and buckets_list are lists.

    Returns True on success.
    """
    try:
        presets_df = load_table('filter_presets')
        if presets_df is None:
            presets_df = pd.DataFrame(columns=['preset_id','user_email','preset_name','years','buckets','created_at'])

        # JSON-encode lists for storage
        years_json = json.dumps(years_list or [])
        buckets_json = json.dumps(buckets_list or [])

        # If preset exists for user+name, update it; otherwise append
        match = (presets_df['user_email'] == user_email) & (presets_df['preset_name'] == preset_name)
        if not presets_df.empty and match.any():
            presets_df.loc[match, 'years'] = years_json
            presets_df.loc[match, 'buckets'] = buckets_json
            # Store created_at as ISO string to avoid sqlite/binding issues with pandas.Timestamp
            presets_df.loc[match, 'created_at'] = datetime.now().isoformat()
        else:
            new_id = int(presets_df['preset_id'].max()) + 1 if (not presets_df.empty and 'preset_id' in presets_df.columns) else 1
            new_row = {'preset_id': new_id, 'user_email': user_email, 'preset_name': preset_name, 'years': years_json, 'buckets': buckets_json, 'created_at': datetime.now().isoformat()}
            presets_df = pd.concat([presets_df, pd.DataFrame([new_row])], ignore_index=True)

        # Normalize created_at column to ISO strings for all rows to avoid sqlite binding errors
        if 'created_at' in presets_df.columns:
            try:
                presets_df['created_at'] = presets_df['created_at'].apply(
                    lambda v: v.isoformat() if hasattr(v, 'isoformat') else (str(v) if pd.notna(v) else None)
                )
            except Exception:
                # Fallback: cast to string
                presets_df['created_at'] = presets_df['created_at'].astype(str)

        return save_table(presets_df, 'filter_presets')
    except Exception as e:
        try: st.warning(f"Failed to save preset: {e}")
        except Exception: pass
        return False


def delete_filter_preset(user_email, preset_name):
    """Delete a named preset for a user."""
    try:
        presets_df = load_table('filter_presets')
        if presets_df is None or presets_df.empty:
            return False
        updated = presets_df[~((presets_df['user_email'] == user_email) & (presets_df['preset_name'] == preset_name))]
        # Normalize created_at column to strings if present
        if 'created_at' in updated.columns:
            try:
                updated['created_at'] = updated['created_at'].apply(
                    lambda v: v.isoformat() if hasattr(v, 'isoformat') else (str(v) if pd.notna(v) else None)
                )
            except Exception:
                updated['created_at'] = updated['created_at'].astype(str)
        return save_table(updated, 'filter_presets')
    except Exception as e:
        try: st.warning(f"Failed to delete preset: {e}")
        except Exception: pass
        return False


# --- iCalendar generation & publishing ---
def generate_calendar_from_tasks(tasks_df):
    """Return an icalendar.Calendar built from the tasks DataFrame."""
    cal = Calendar()
    cal.add('prodid', '-//HRL Project Tracker//mxm.dk//')
    cal.add('version', '2.0')

    if tasks_df is None or tasks_df.empty:
        return cal

    for _, row in tasks_df.iterrows():
        # Only include tasks with start or end
        start = row.get('START')
        end = row.get('END')
        if pd.isna(start) and pd.isna(end):
            continue

        ev = Event()
        uid_val = str(row.get('#', uuid.uuid4()))
        ev.add('uid', uid_val + '@hrl-project-tracker')
        ev.add('summary', str(row.get('TASK', 'No Title')))
        if pd.notna(start):
            # icalendar expects datetime/date objects
            ev.add('dtstart', start)
        if pd.notna(end):
            # Increment end by one day if it's a date to be inclusive? Keep as-is.
            ev.add('dtend', end)
        # Add description with some helpful fields
        desc = []
        desc.append(f"Planner Bucket: {row.get('PLANNER BUCKET', '')}")
        desc.append(f"Assignment Title: {row.get('ASSIGNMENT TITLE', '')}")
        desc.append(f"Progress: {row.get('PROGRESS', '')}")
        ev.add('description', '\n'.join(desc))
        cal.add_component(ev)

    return cal


def generate_and_publish_ics(tasks_df, local_path='calendar.ics'):
    """Generate an .ics file from tasks_df and either upload to S3 (if configured) or write locally.

    Behavior:
    - If st.secrets contains a section `S3` with keys `BUCKET`, `KEY_PREFIX` (optional),
      `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (or use IAM role), the function will upload
      the generated calendar to that S3 bucket and return the public HTTPS URL.
    - Otherwise, it writes a local `calendar.ics` next to the running script and returns the path.

    This function is best-effort and will not raise on upload errors (it will raise only on programming errors).
    """
    cal = generate_calendar_from_tasks(tasks_df)

    ics_bytes = cal.to_ical()

    # Prefer S3 publish if configured and boto3 available
    s3_info = None
    try:
        s3_info = st.secrets.get('S3')
    except Exception:
        s3_info = None

    if s3_info and _BOTO3_AVAILABLE:
        bucket = s3_info.get('BUCKET')
        key_prefix = s3_info.get('KEY_PREFIX', '')
        key_name = (key_prefix.rstrip('/') + '/' if key_prefix else '') + 'calendar.ics'

        # Build boto3 client using provided credentials if available
        try:
            if s3_info.get('AWS_ACCESS_KEY_ID') and s3_info.get('AWS_SECRET_ACCESS_KEY'):
                s3 = boto3.client('s3', aws_access_key_id=s3_info.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=s3_info.get('AWS_SECRET_ACCESS_KEY'))
            else:
                s3 = boto3.client('s3')

            s3.put_object(Bucket=bucket, Key=key_name, Body=ics_bytes, ContentType='text/calendar', ACL='public-read')
            # Construct URL (note: this may vary by region or hosting settings)
            url = f"https://{bucket}.s3.amazonaws.com/{key_name}"
            return url
        except (BotoCoreError, NoCredentialsError) as e:
            # Fall through to local write
            st.warning(f"S3 upload failed or not configured properly: {e}")
        except Exception as e:
            st.warning(f"S3 upload failed: {e}")

    # Fallback: write local file
    try:
        base_dir = os.path.dirname(__file__)
        out_path = os.path.join(base_dir, local_path)
        with open(out_path, 'wb') as f:
            f.write(ics_bytes)
        return out_path
    except Exception as e:
        raise

# --- Database integrity check (development use) ---
def check_database_integrity():
    """Check and report the number of rows in critical tables."""
    try:
        conn = sqlite3.connect('project_tracker.db')
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        table_info = {}
        for t in ['tasks','bucket_icons','users','settings','changelog']:
            cur.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE name='{t}';")
            count = cur.fetchone()
            table_info[t] = count[0] if count else 0
        conn.close()
        return table_info
    except Exception as e:
        st.error(f"Database integrity check failed: {e}")
        return None

