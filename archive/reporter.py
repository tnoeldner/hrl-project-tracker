import pandas as pd
import argparse
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# --- Email Configuration (Update with your details) ---
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def load_data(filepath):
    """Loads and cleans data from the Excel file."""
    try:
        df = pd.read_excel(filepath, sheet_name='DATA')
        # Convert START and END columns to datetime objects
        df['START'] = pd.to_datetime(df['START'])
        df['END'] = pd.to_datetime(df['END'])
        return df
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None
    except KeyError as e:
        print(f"Error: A required column is missing from the Excel file: {e}")
        return None

def generate_report_text(df):
    """Generates a text-based summary of the project data."""
    total_projects = len(df)
    projects_by_bucket = df['PLANNER BUCKET'].value_counts().to_string()
    today = datetime.now()
    # Updated Overdue Logic: Any task with an end date in the past
    overdue_projects_df = df[df['END'] < today]
    
    overdue_projects_str = "No overdue tasks found."
    if not overdue_projects_df.empty:
        # Displaying columns that exist in the user's file
        overdue_projects_str = overdue_projects_df[['ASSIGNMENT TITLE', 'AUDIENCE', 'END']].to_string(index=False)

    report = f"""
=========================================
      PROJECT ANALYSIS REPORT
      Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=========================================

--- Overall Summary ---
Total Number of Tasks: {total_projects}

--- Tasks by Planner Bucket ---
{projects_by_bucket}

--- Overdue Tasks ---
{overdue_projects_str}

=========================================
"""
    return report

def generate_visualizations(df):
    """Creates and saves charts based on the data."""
    chart_files = []
    
    # NEW CHART: Bar chart for tasks per planner bucket
    plt.figure(figsize=(12, 7))
    sns.countplot(y=df['PLANNER BUCKET'], order=df['PLANNER BUCKET'].value_counts().index)
    plt.title('Number of Tasks per Planner Bucket', fontsize=16)
    plt.xlabel('Number of Tasks')
    plt.ylabel('Planner Bucket')
    plt.tight_layout()
    bucket_chart_path = 'tasks_per_bucket.png'
    plt.savefig(bucket_chart_path)
    chart_files.append(bucket_chart_path)
    plt.close()
    print(f"Chart saved: {bucket_chart_path}")
    
    return chart_files

def send_email(recipient_email, report_text, attachments):
    """Sends the report and attachments via email."""
    # (This function remains unchanged)
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Email credentials are not configured. Skipping email.")
        return
    # ... (rest of the email code is the same)
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = f"Project Status Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg.attach(MIMEText(report_text, 'plain'))
        for file_path in attachments:
            with open(file_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(file_path))
            msg.attach(image)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def add_project(filepath, df):
    """Adds a new task to the workbook."""
    print("\n--- Add New Task ---")
    new_task = {}
    new_task['#'] = df['#'].max() + 1
    new_task['Fiscal Year'] = input("Enter Fiscal Year: ")
    new_task['PLANNER BUCKET'] = input("Enter Planner Bucket: ")
    new_task['TASK'] = input("Enter Task Description: ")
    new_task['ASSIGNMENT TITLE'] = input("Enter Assignment Title: ")
    new_task['AUDIENCE'] = input("Enter Audience: ")
    new_task['START'] = pd.to_datetime(input("Enter Start Date (YYYY-MM-DD): "))
    new_task['END'] = pd.to_datetime(input("Enter End Date (YYYY-MM-DD): "))

    # Use pd.concat to append the new row
    new_df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
    new_df.to_excel(filepath, sheet_name='DATA', index=False)
    print(f"Successfully added task '{new_task['ASSIGNMENT TITLE']}' with # {new_task['#']}.")

def query_projects(df, bucket):
    """Filters and displays tasks for a specific planner bucket."""
    result = df[df['PLANNER BUCKET'].str.contains(bucket, case=False, na=False)]
    
    if result.empty:
        print(f"No tasks found for bucket '{bucket}'.")
    else:
        print(f"\n--- Tasks for Planner Bucket: {bucket} ---")
        # Displaying columns that exist in the user's file
        print(result[['#', 'ASSIGNMENT TITLE', 'AUDIENCE', 'END']].to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description="Advanced Project Tracker Tool")
    parser.add_argument("--report", action="store_true", help="Generate and print a summary report.")
    parser.add_argument("--email", type=str, help="Send the report to the specified email address.")
    parser.add_argument("--add", action="store_true", help="Add a new task.")
    # The --update argument has been removed
    parser.add_argument("--query", type=str, help="Query tasks by PLANNER BUCKET.")
    
    args = parser.parse_args()
    
    filepath = 'Project Tracker.xlsx'
    df = load_data(filepath)
    
    if df is None:
        return

    if args.report or args.email:
        print("Generating report...")
        report_text = generate_report_text(df)
        charts = generate_visualizations(df)
        
        if args.report:
            print(report_text)
            
        if args.email:
            send_email(args.email, report_text, charts)

    elif args.add:
        add_project(filepath, df)
        
    elif args.query:
        query_projects(df, args.query)
        
    else:
        print("No action specified. Use --help for options.")

if __name__ == '__main__':
    main()