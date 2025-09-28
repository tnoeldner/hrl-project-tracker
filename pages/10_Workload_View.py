# File: pages/10_Workload_View.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Workload View", layout="wide")
st.title("⚖️ Resource Management & Workload View")

df = data_manager.load_table('tasks')

if df is not None:
    st.info("Use the filters below to see the distribution of active tasks across different roles within a specific time period.")

    # --- FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        # Default start date is the beginning of the current month
        default_start = datetime.now().date().replace(day=1)
        start_date = st.date_input("Select Start Date", value=default_start)
    with col2:
        # Default end date is 3 months from the start date
        default_end = default_start + timedelta(days=90)
        end_date = st.date_input("Select End Date", value=default_end)

    # Convert date inputs to datetime objects for comparison
    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)

    # Filter for tasks that are active within the selected date range
    # A task is active if its period overlaps with the selected range.
    active_tasks_df = df[
        (df['START'] <= end_date_dt) &
        (df['END'] >= start_date_dt) &
        (df['END'].dt.year > 1901) # Exclude unscheduled tasks
    ].copy()

    st.markdown("---")

    if not active_tasks_df.empty:
        # --- WORKLOAD ANALYSIS ---
        st.subheader(f"Task Workload from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        # Calculate task counts for each assignment title
        workload_counts = active_tasks_df['ASSIGNMENT TITLE'].value_counts()
        
        # Display as a bar chart
        st.bar_chart(workload_counts)

        st.markdown("---")
        
        # Display a detailed breakdown in expanders
        st.subheader("Detailed Task Breakdown")
        for title, count in workload_counts.items():
            with st.expander(f"{title} - ({count} active tasks)"):
                tasks_for_title = active_tasks_df[active_tasks_df['ASSIGNMENT TITLE'] == title]
                
                # Display relevant details for each task
                for _, row in tasks_for_title.iterrows():
                    st.markdown(
                        f"- **{row['TASK']}** (Status: *{row['PROGRESS']}*)"
                    )
                    st.caption(f"  Duration: {row['START'].strftime('%Y-%m-%d')} to {row['END'].strftime('%Y-%m-%d')}")
    else:
        st.warning("No active tasks found for the selected date range.")

else:
    st.warning("Could not load data.")
