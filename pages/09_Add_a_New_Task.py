# File: pages/5_Add_a_New_Task.py
import streamlit as st
import pandas as pd
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.title("📝 Add a New Task")

df_original = data_manager.load_table('tasks')

if df_original is not None:
    with st.form("new_task_form", clear_on_submit=True):
        st.write("Fill out the details below to add a new task. Use the 'Or enter a new value' field to create a category that doesn't exist yet.")

        # --- Assignment Title ---
        st.markdown("**Assignment Title**")
        assignment_title_sel = st.selectbox(
            "Select existing Assignment Title",
            options=sorted(df_original['ASSIGNMENT TITLE'].dropna().unique().tolist()),
            key="at_sel"
        )
        assignment_title_new = st.text_input("Or enter a new Assignment Title (overrides selection above if filled):", key="at_new")

        task_desc = st.text_area("Task Description")

        # --- Planner Bucket ---
        st.markdown("**Planner Bucket**")
        planner_bucket_sel = st.selectbox(
            "Select existing Planner Bucket",
            options=sorted(df_original['PLANNER BUCKET'].dropna().unique().tolist()),
            key="pb_sel"
        )
        planner_bucket_new = st.text_input("Or enter a new Planner Bucket (overrides selection above if filled):", key="pb_new")

        # --- Semester ---
        st.markdown("**Semester**")
        semester_sel = st.selectbox(
            "Select existing Semester",
            options=sorted(df_original['SEMESTER'].dropna().unique().tolist()),
            key="sem_sel"
        )
        semester_new = st.text_input("Or enter a new Semester value (overrides selection above if filled):", key="sem_new")

        fiscal_year = st.selectbox(
            "Fiscal Year",
            options=sorted(df_original['Fiscal Year'].dropna().unique().tolist()),
            format_func=lambda x: data_manager.format_fy(x)
        )

        # --- Audience ---
        st.markdown("**Audience**")
        audience_sel = st.selectbox(
            "Select existing Audience",
            options=sorted(df_original['AUDIENCE'].dropna().unique().tolist()),
            key="aud_sel"
        )
        audience_new = st.text_input("Or enter a new Audience value (overrides selection above if filled):", key="aud_new")

        start_date = st.date_input("Start Date", format="MM-DD-YYYY")
        end_date = st.date_input("End Date", format="MM-DD-YYYY")
        progress = st.selectbox("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"])

        submitted = st.form_submit_button("Save Task")
        if submitted:
            # Resolve final values: new input overrides dropdown if non-empty
            assignment_title = assignment_title_new.strip() if assignment_title_new.strip() else assignment_title_sel
            planner_bucket = planner_bucket_new.strip() if planner_bucket_new.strip() else planner_bucket_sel
            semester = semester_new.strip() if semester_new.strip() else semester_sel
            audience = audience_new.strip() if audience_new.strip() else audience_sel

            if not all([assignment_title, task_desc, planner_bucket, semester, fiscal_year, audience]):
                st.warning("Please fill out all fields before saving.")
            else:
                # Create a dictionary for the new task
                new_task = {
                    '#': df_original['#'].max() + 1,
                    'ASSIGNMENT TITLE': assignment_title,
                    'TASK': task_desc,
                    'PLANNER BUCKET': planner_bucket,
                    'SEMESTER': semester,
                    'Fiscal Year': fiscal_year,
                    'AUDIENCE': audience,
                    'START': pd.to_datetime(start_date),
                    'END': pd.to_datetime(end_date),
                    'PROGRESS': progress
                }

                # Create the updated dataframe by adding the new task
                df_updated = pd.concat([df_original, pd.DataFrame([new_task])], ignore_index=True)

                # Call the new logging function
                if data_manager.save_and_log_changes(df_original, df_updated):
                    st.success("Task added successfully!")
                else:
                    st.error("Failed to add task.")
else:
    st.warning("Could not load data.")

