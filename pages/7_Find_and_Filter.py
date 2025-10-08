# File: pages/2_Find_and_Filter.py
import streamlit as st
import pandas as pd
import data_manager
import ics_export

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Find & Filter", layout="wide")
st.title("🔍 Find, Filter & Comment on Tasks")

df_original = data_manager.load_table('tasks')
users_df = data_manager.load_table('users')

if df_original is not None and users_df is not None:
    # --- FILTERS ---
    st.write("Use the controls below to filter the data. The table will update as you type or make a selection.")
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        bucket_options = ['All'] + sorted([str(item) for item in df_original['PLANNER BUCKET'].unique()])
        st.selectbox("Filter by Planner Bucket", options=bucket_options, key="find_bucket_filter")
    with col2:
        year_options = ['All'] + sorted([str(item) for item in df_original['Fiscal Year'].unique()])
        st.selectbox("Filter by Fiscal Year", options=year_options, key="find_year_filter")
    with col3:
        search_term = st.text_input("Search by Task Name (case-insensitive)")

    # Apply filters sequentially
    filtered_df = df_original.copy()
    if 'find_bucket_filter' in st.session_state and st.session_state.find_bucket_filter != 'All':
        filtered_df = filtered_df[filtered_df['PLANNER BUCKET'] == st.session_state.find_bucket_filter]
    if 'find_year_filter' in st.session_state and st.session_state.find_year_filter != 'All':
        filtered_df = filtered_df[filtered_df['Fiscal Year'].astype(str) == st.session_state.find_year_filter]
    if search_term:
        filtered_df = filtered_df[filtered_df['TASK'].astype(str).str.contains(search_term, case=False, na=False)]

    st.markdown("---")
    
    # --- DATA EDITOR ---
    st.info("Select a single task's 'Details' checkbox to view its comment history and add new comments.")
    
    # Add a 'Details' column for the UI
    filtered_df['Details'] = False
    
    edited_df = st.data_editor(
        filtered_df, 
        hide_index=True,
        column_order=("#", "Details", "ASSIGNMENT TITLE", "TASK", "PROGRESS", "START", "END"),
        column_config={
            "Details": st.column_config.CheckboxColumn("View Details", help="Select a task to view its comments below. Only one task can be selected at a time."),
            "PROGRESS": st.column_config.SelectboxColumn("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"], required=True),
            "START": st.column_config.DateColumn("Start Date", format="MM-DD-YYYY"),
            "END": st.column_config.DateColumn("End Date", format="MM-DD-YYYY")
        }
    )
    
    # --- DETAILS & COMMENTS SECTION ---
    selected_task_rows = edited_df[edited_df['Details'] == True]
    
    if len(selected_task_rows) > 1:
        st.warning("Please select only one task at a time to view details and comments.")
    elif not selected_task_rows.empty:
        selected_task = selected_task_rows.iloc[0]
        task_id = selected_task['#']
        
        st.subheader(f"Comments for Task: {selected_task['TASK']}")
        
        comments = data_manager.get_comments_for_task(task_id)
        if not comments.empty:
            for _, comment in comments.iterrows():
                ts = pd.to_datetime(comment['timestamp']).strftime('%Y-%m-%d %H:%M')
                st.info(f"**{comment['user_email']}** ({ts}):\n\n{comment['comment_text']}")
        else:
            st.write("No comments yet for this task.")

        with st.form(f"comment_form_{task_id}", clear_on_submit=True):
            comment_text = st.text_area("Add a new comment:")
            
            all_user_emails = users_df['email'].tolist()
            author_email = st.session_state.logged_in_user
            other_users = [email for email in all_user_emails if email != author_email]
            
            additional_recipients = st.multiselect(
                "Additionally notify:",
                options=other_users,
                help="Select other users to notify. The person assigned to the task will be notified automatically."
            )

            submitted = st.form_submit_button("Post Comment")
            if submitted:
                if comment_text:
                    assigned_title = selected_task['ASSIGNMENT TITLE']
                    data_manager.add_comment_and_notify(task_id, author_email, comment_text, assigned_title, additional_recipients)
                    st.success("Comment posted!")
                    st.rerun()
                else:
                    st.warning("Please enter a comment before posting.")
    
    st.markdown("---")

    # --- SAVE EDITS BUTTON ---
    if st.button("Save Edits to Table"):
        df_updated = df_original.copy()
        edited_df_for_save = edited_df.drop(columns=['Details'])
        
        df_updated.set_index('#', inplace=True)
        edited_df_indexed = edited_df_for_save.set_index('#')
        df_updated.update(edited_df_indexed)
        df_updated.reset_index(inplace=True)
        
        user_email = st.session_state.logged_in_user
        if data_manager.save_and_log_changes(df_original, df_updated, user_email, "Find and Filter"):
            st.success("Edits saved successfully!")
            st.rerun()
        else:
            st.error("Failed to save edits.")
    
    # --- ICS EXPORT FOR FILTERED TASKS / SELECTED TASK ---
    st.markdown("---")
    st.subheader("Export to Calendar (.ics)")
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        if st.button("📥 Download .ics for filtered tasks"):
            export_df = filtered_df.copy()
            # Keep only rows with valid start and end dates
            export_df = export_df[pd.notna(export_df['START']) & pd.notna(export_df['END'])]
            ics_bytes = ics_export.generate_ics_from_df(export_df)
            st.download_button(label="Download filtered_tasks.ics", data=ics_bytes, file_name="filtered_tasks_calendar.ics", mime="text/calendar", key="download_filtered_ics")
    with exp_col2:
        if 'selected_task_rows' in locals() and not selected_task_rows.empty and len(selected_task_rows) == 1:
            sel = selected_task_rows.iloc[0]
            if st.button("📥 Download .ics for selected task"):
                single_df = df_original[df_original['#'] == sel['#']].copy()
                ics_bytes = ics_export.generate_ics_from_df(single_df)
                filename = f"task_{int(sel['#'])}.ics"
                st.download_button(label=f"Download .ics for task #{int(sel['#'])}", data=ics_bytes, file_name=filename, mime="text/calendar", key=f"download_task_ics_{int(sel['#'])}")
        else:
            st.write("Select a task's 'Details' checkbox to enable single-task .ics download.")
else:
    st.warning("Could not load data from the database.")


