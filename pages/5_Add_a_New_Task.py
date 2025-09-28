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
# ...st.set_page_config(page_title="Add Task", layout="wide")
st.title("📝 Add a New Task")

df_original = data_manager.load_table('tasks')

if df_original is not None:
    with st.form("new_task_form", clear_on_submit=True):
        st.write("Fill out the details below to add a new task.")
        assignment_title = st.text_input("Assignment Title")
        task_desc = st.text_area("Task Description")
        planner_bucket = st.selectbox("Planner Bucket", options=sorted(df_original['PLANNER BUCKET'].unique()))
        semester = st.text_input("Semester (e.g., Fall 2025)")
        fiscal_year = st.text_input("Fiscal Year")
        audience = st.text_input("Audience")
        start_date = st.date_input("Start Date", format="MM-DD-YYYY")
        end_date = st.date_input("End Date", format="MM-DD-YYYY")
        progress = st.selectbox("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"])
        
        submitted = st.form_submit_button("Save Task")
        if submitted:
            if not all([assignment_title, task_desc, planner_bucket, semester, fiscal_year, audience]):
                st.warning("Please fill out all fields before saving.")
            else:
                new_task = {
                    '#': df_original['#'].max() + 1, 'ASSIGNMENT TITLE': assignment_title, 'TASK': task_desc,
                    'PLANNER BUCKET': planner_bucket, 'SEMESTER': semester, 'Fiscal Year': fiscal_year,
                    'AUDIENCE': audience, 'START': pd.to_datetime(start_date), 'END': pd.to_datetime(end_date),
                    'PROGRESS': progress
                }
                df_updated = pd.concat([df_original, pd.DataFrame([new_task])], ignore_index=True)
                if data_manager.save_and_log_changes(df_original, df_updated):
                    st.success("Task added and logged successfully!")
else:
    st.warning("Could not load data.")