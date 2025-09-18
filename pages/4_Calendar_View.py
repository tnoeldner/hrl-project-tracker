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

# (The rest of the file remains the same)
# ...
st.set_page_config(page_title="Calendar View", layout="wide")
st.title("📅 Calendar View")

df_original = data_manager.load_data()

if df_original is not None:
    df_cal = df_original.fillna('')
    tasks_for_calendar = []
    for index, row in df_cal.iterrows():
        tasks_for_calendar.append({
            "title": f"{row['TASK']} (FY{row['Fiscal Year']})",
            "start": row['START'].strftime("%Y-%m-%d"), "end": row['END'].strftime("%Y-%m-%d"), "id": index
        })

    clicked_event = calendar(events=tasks_for_calendar)

    if clicked_event and clicked_event.get('callback') == 'eventClick':
        task_id = clicked_event['eventClick']['event'].get('id')
        if task_id is not None:
            st.session_state['selected_task_id'] = int(task_id)

    if 'selected_task_id' in st.session_state and st.session_state['selected_task_id'] is not None:
        task_id = st.session_state['selected_task_id']
        if task_id in df_original.index:
            task_data = df_original.loc[task_id].copy()
            st.subheader(f"✍️ Editing Task: {task_data['ASSIGNMENT TITLE']}")
            with st.form("edit_task_form"):
                # Form fields...
                assignment_title = st.text_input("Assignment Title", value=task_data['ASSIGNMENT TITLE'])
                task_desc = st.text_area("Task Description", value=task_data['TASK'])
                planner_bucket = st.selectbox("Planner Bucket", options=sorted(df_original['PLANNER BUCKET'].unique()), index=sorted(df_original['PLANNER BUCKET'].unique()).index(task_data['PLANNER BUCKET']))
                semester = st.text_input("Semester", value=task_data.get('SEMESTER', ''))
                fiscal_year = st.text_input("Fiscal Year", value=task_data['Fiscal Year'])
                audience = st.text_input("Audience", value=task_data['AUDIENCE'])
                start_date = st.date_input("Start Date", value=task_data['START'])
                end_date = st.date_input("End Date", value=task_data['END'])
                progress_options = ["NOT STARTED", "IN PROGRESS", "COMPLETE"]
                current_progress = task_data.get('PROGRESS', "NOT STARTED")
                if pd.isna(current_progress): current_progress = "NOT STARTED"
                current_progress_index = progress_options.index(current_progress)
                progress = st.selectbox("Progress", options=progress_options, index=current_progress_index)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Save Changes")
                with col2:
                    cancelled = st.form_submit_button("Clear Selection")

                if submitted:
                    df_updated = df_original.copy()
                    df_updated.loc[task_id, 'ASSIGNMENT TITLE'] = assignment_title
                    df_updated.loc[task_id, 'TASK'] = task_desc
                    df_updated.loc[task_id, 'PLANNER BUCKET'] = planner_bucket
                    df_updated.loc[task_id, 'SEMESTER'] = semester
                    df_updated.loc[task_id, 'Fiscal Year'] = fiscal_year
                    df_updated.loc[task_id, 'AUDIENCE'] = audience
                    df_updated.loc[task_id, 'START'] = pd.to_datetime(start_date)
                    df_updated.loc[task_id, 'END'] = pd.to_datetime(end_date)
                    df_updated.loc[task_id, 'PROGRESS'] = progress
                    
                    if data_manager.save_and_log_changes(df_original, df_updated):
                        st.success("Task updated and logged successfully!")
                        st.session_state['selected_task_id'] = None
                        st.rerun() 
                
                if cancelled:
                    st.session_state['selected_task_id'] = None
                    st.rerun()
else:
    st.warning("Could not load data.")