# File: pages/3_Timeline_View.py
import streamlit as st
import pandas as pd
from datetime import datetime
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Timeline View", layout="wide")
st.title("🗓️ Timeline View")

# Load both the tasks and the icons data
df = data_manager.load_table('tasks')
icons_df = data_manager.load_table('bucket_icons')

if df is not None and icons_df is not None:
    # --- DYNAMIC ICON MAPPING ---
    # Convert the icons DataFrame to a dictionary for easy lookup
    bucket_icon_map = pd.Series(icons_df.icon.values, index=icons_df.bucket_name).to_dict()
    # Ensure a default icon exists for buckets not in the map
    if 'Default' not in bucket_icon_map:
        bucket_icon_map['Default'] = '📌'
    # --------------------------

    today = pd.to_datetime("today").normalize()
    num_days = st.number_input("Enter number of days to look forward/back:", min_value=1, value=30)
    
    future_date = today + pd.Timedelta(days=num_days)
    past_date = today - pd.Timedelta(days=num_days)
    
    # Filter tasks based on their START date
    upcoming_tasks = df[(df['START'] >= today) & (df['START'] <= future_date)].sort_values(by='START')
    recent_tasks = df[(df['START'] < today) & (df['START'] >= past_date)].sort_values(by='START', ascending=False)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Starting in Next {num_days} Days")
        if not upcoming_tasks.empty:
            # Loop through each task and create an expander
            for index, row in upcoming_tasks.iterrows():
                # Get the icon for the task's bucket
                bucket = row.get('PLANNER BUCKET', 'Default')
                icon = bucket_icon_map.get(bucket, bucket_icon_map['Default'])
                
                status = row.get('PROGRESS', 'NOT STARTED')
                status_colors = {"NOT STARTED": "red", "IN PROGRESS": "orange", "COMPLETE": "green"}
                color = status_colors.get(status, "grey")
                status_display = f":{color}[{status}]"
                
                # UPDATED: Changed the color of the date using markdown
                with st.expander(f"{icon} :blue[**{row['START'].strftime('%m-%d-%Y, %A')}**] - {row['TASK']} - {status_display}"):
                    st.markdown(f"**Assigned To:** {row['ASSIGNMENT TITLE']}")
                    st.markdown(f"**Planner Bucket:** {row['PLANNER BUCKET']}")
                    st.markdown(f"**Audience:** {row['AUDIENCE']}")
        else:
            st.info("No tasks starting in this period.")
            
    with col2:
        st.subheader(f"Started in Past {num_days} Days")
        if not recent_tasks.empty:
            # Loop through each task and create an expander
            for index, row in recent_tasks.iterrows():
                # Get the icon for the task's bucket
                bucket = row.get('PLANNER BUCKET', 'Default')
                icon = bucket_icon_map.get(bucket, bucket_icon_map['Default'])

                status = row.get('PROGRESS', 'NOT STARTED')
                status_colors = {"NOT STARTED": "red", "IN PROGRESS": "orange", "COMPLETE": "green"}
                color = status_colors.get(status, "grey")
                status_display = f":{color}[{status}]"

                # UPDATED: Changed the color of the date using markdown
                with st.expander(f"{icon} :blue[**{row['START'].strftime('%m-%d-%Y, %A')}**] - {row['TASK']} - {status_display}"):
                    st.markdown(f"**Assigned To:** {row['ASSIGNMENT TITLE']}")
                    st.markdown(f"**Planner Bucket:** {row['PLANNER BUCKET']}")
                    st.markdown(f"**Audience:** {row['AUDIENCE']}")
        else:
            st.info("No tasks started in this period.")
else:
    st.warning("Could not load data.")


