# File: pages/1_Dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Dashboard Report")

df_original = data_manager.load_table('tasks')

if df_original is not None:
    # --- GLOBAL CONTROLS ---
    col1, col2 = st.columns(2)
    with col1:
        year_options = ['All'] + sorted(df_original['Fiscal Year'].unique().tolist())
        st.selectbox(
            "Select Fiscal Year for Dashboard View", 
            options=year_options,
            key="dashboard_year_filter"
        )
    with col2:
        st.number_input("Days to look forward for 'Upcoming Tasks':", min_value=1, value=30, key="days_forward")

    # --- DATA FILTERING ---
    if st.session_state.dashboard_year_filter == 'All':
        display_df = df_original
    else:
        display_df = df_original[df_original['Fiscal Year'] == st.session_state.dashboard_year_filter]
    
    today = pd.to_datetime("today").normalize()
    future_date = today + pd.Timedelta(days=st.session_state.days_forward)
    
    # All calculations are now based on the filtered display_df
    overdue_df = display_df[(display_df['END'] < today) & (display_df['PROGRESS'] != 'COMPLETE') & (display_df['END'].dt.year > 1901)].copy()
    unscheduled_df = display_df[display_df['END'].dt.year <= 1901].copy()
    upcoming_tasks = display_df[(display_df['START'] >= today) & (display_df['START'] <= future_date)]
    
    st.markdown("---")
    
    # --- METRICS DISPLAY ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Total Tasks (FY {st.session_state.dashboard_year_filter})", len(display_df))
    col2.metric("Overdue Tasks", len(overdue_df))
    col3.metric("Unscheduled Tasks", len(unscheduled_df))
    col4.metric(f"Upcoming Tasks (Next {st.session_state.days_forward} Days)", len(upcoming_tasks))

    st.markdown("---")
    
    # --- CHARTS ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Tasks by Planner Bucket (FY {st.session_state.dashboard_year_filter})")
        st.dataframe(display_df['PLANNER BUCKET'].value_counts())
    with col2:
        st.subheader(f"Tasks by Progress (FY {st.session_state.dashboard_year_filter})")
        progress_counts = display_df['PROGRESS'].value_counts()
        if not progress_counts.empty:
            fig, ax = plt.subplots()
            ax.pie(progress_counts, labels=progress_counts.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.info("No tasks to display in the progress chart.")
            
    st.markdown("---")
    
    # --- EDITABLE TABLES ---
    st.subheader("Overdue Tasks")
    if not overdue_df.empty:
        edited_overdue = st.data_editor(overdue_df, hide_index=True, key="overdue_editor", column_config={"PROGRESS": st.column_config.SelectboxColumn("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"], required=True), "START": st.column_config.DateColumn("Start Date", format="MM-DD-YYYY"),"END": st.column_config.DateColumn("End Date", format="MM-DD-YYYY")})
        if st.button("Save Overdue Task Changes"):
            df_updated = df_original.copy()
            df_updated.update(edited_overdue)
            if data_manager.save_and_log_changes(df_original, df_updated):
                st.success("Changes saved successfully!")
                st.rerun()
    else:
        st.success(f"No overdue tasks found for FY {st.session_state.dashboard_year_filter}.")

    st.markdown("---")

    st.subheader("Unscheduled Tasks (Placeholder Dates)")
    if not unscheduled_df.empty:
        edited_unscheduled = st.data_editor(unscheduled_df, hide_index=True, key="unscheduled_editor", column_config={"PROGRESS": st.column_config.SelectboxColumn("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"], required=True), "START": st.column_config.DateColumn("Start Date", format="MM-DD-YYYY"), "END": st.column_config.DateColumn("End Date", format="MM-DD-YYYY")})
        if st.button("Save Unscheduled Task Changes"):
            df_updated = df_original.copy()
            df_updated.update(edited_unscheduled)
            if data_manager.save_and_log_changes(df_original, df_updated):
                st.success("Changes saved successfully!")
                st.rerun()
    else:
        st.info(f"No unscheduled tasks found for FY {st.session_state.dashboard_year_filter}.")
        
    st.markdown("---")

    st.subheader(f"Upcoming Tasks (Next {st.session_state.days_forward} Days)")
    if not upcoming_tasks.empty:
        edited_upcoming = st.data_editor(upcoming_tasks, hide_index=True, key="upcoming_editor", column_config={"PROGRESS": st.column_config.SelectboxColumn("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"], required=True), "START": st.column_config.DateColumn("Start Date", format="MM-DD-YYYY"), "END": st.column_config.DateColumn("End Date", format="MM-DD-YYYY")})
        if st.button("Save Upcoming Task Changes"):
            df_updated = df_original.copy()
            df_updated.update(edited_upcoming)
            if data_manager.save_and_log_changes(df_original, df_updated):
                st.success("Changes saved successfully!")
                st.rerun()
    else:
        st.info(f"No upcoming tasks found for FY {st.session_state.dashboard_year_filter}.")

else:
    st.warning("Could not load data.")

