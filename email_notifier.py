# File: email_notifier.py
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMIMultipart
from email.mime.text import MIMEText
import json
import data_manager

# --- CONFIGURATION ---
SENDER_EMAIL = "your_sending_email@gmail.com"
SENDER_PASSWORD = "your_app_password" # Use an App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- HELPER FUNCTIONS ---
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_user_settings():
    try:
        with open('user_settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def send_weekly_email(user_email, user_data, tasks_df):
    """Constructs and sends a personalized weekly task summary."""
    if tasks_df.empty:
        return # Don't send an email if there are no upcoming tasks

    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = user_email
    message['Subject'] = "Your Upcoming Tasks for the Week"

    html = f"""
    <html><body>
        <h2>Hi {user_data['first_name']},</h2>
        <p>Here are your tasks starting in the next 7 days:</p>
        {tasks_df.to_html(index=False)}
    </body></html>
    """
    message.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [user_email], message.as_string())
        server.quit()
        print(f"Successfully sent weekly summary to {user_email}")
    except Exception as e:
        print(f"Failed to send email to {user_email}: {e}")

# --- MAIN SCRIPT ---
def main():
    print("Starting notification process...")
    df = data_manager.load_data()
    users = load_users()
    settings = load_user_settings()

    if df is None or not users or not settings:
        print("Could not load data, users, or settings. Exiting.")
        return

    today = pd.to_datetime("today").normalize()
    one_week_from_now = today + timedelta(days=7)
    
    # Loop through all registered users who have a setting
    for email, prefs in settings.items():
        frequency = prefs.get('frequency')
        
        # Check if we should send an email based on the schedule
        # For a real app, you'd check if today is the correct day of the week for 'Weekly'
        if frequency == "Daily" or (frequency == "Weekly" and today.weekday() == 0): # 0 = Monday
            
            if email in users:
                user_data = users[email]
                assignment_title = user_data.get('assignment_title')
                
                # Find tasks for this specific user starting in the next week
                user_tasks = df[
                    (df['ASSIGNMENT TITLE'] == assignment_title) &
                    (df['START'] >= today) &
                    (df['START'] <= one_week_from_now)
                ].copy()

                if not user_tasks.empty:
                    report_cols = {'TASK': 'Task', 'START': 'Start Date', 'PROGRESS': 'Status'}
                    user_tasks_report = user_tasks[report_cols.keys()].rename(columns=report_cols)
                    user_tasks_report['Start Date'] = user_tasks_report['Start Date'].dt.strftime('%m-%d-%Y, %A')
                    
                    send_weekly_email(email, user_data, user_tasks_report)

    print("Notification process finished.")

if __name__ == "__main__":
    main()