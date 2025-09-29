# File: pages/15_Admin_Changelog.py
import streamlit as st
import pandas as pd
import data_manager

# --- AUTHENTICATION CHECK ---
# Ensure user is logged in
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()

# Ensure user is an administrator
user_role = st.session_state.user_data.get('role')
if user_role != 'admin':
    st.error("You do not have permission to view this page. This page is for administrators only.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Changelog", layout="wide")
st.title("📜 Application Changelog")
st.info("This page displays a log of all data changes made within the application.")

changelog_df = data_manager.load_table('changelog')

if changelog_df is not None:
    # Ensure Timestamp is a datetime object for proper sorting
    changelog_df['Timestamp'] = pd.to_datetime(changelog_df['Timestamp'])
    
    # --- FILTERS ---
    st.subheader("Filter Changelog")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filter by Action Type
        action_options = ['All'] + changelog_df['Action'].unique().tolist()
        selected_action = st.selectbox("Filter by Action", options=action_options)

    with col2:
        # Filter by Date Range (Start)
        start_date = st.date_input("Start Date", value=changelog_df['Timestamp'].min().date())
    
    with col3:
        # Filter by Date Range (End)
        end_date = st.date_input("End Date", value=changelog_df['Timestamp'].max().date())

    # Apply filters
    filtered_log = changelog_df
    
    if selected_action != 'All':
        filtered_log = filtered_log[filtered_log['Action'] == selected_action]
        
    # Convert dates for comparison
    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)
    
    filtered_log = filtered_log[
        (filtered_log['Timestamp'] >= start_date_dt) & 
        (filtered_log['Timestamp'] <= end_date_dt + pd.Timedelta(days=1)) # Add 1 day to include the end date
    ]

    st.markdown("---")
    
    # Display the filtered log, sorted by most recent first
    st.dataframe(filtered_log.sort_values(by='Timestamp', ascending=False), use_container_width=True)

else:
    st.warning("Could not load changelog data from the database.")