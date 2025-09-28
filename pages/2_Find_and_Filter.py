# File: pages/2_Find_and_Filter.py
import streamlit as st
import pandas as pd
import data_manager

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
    # --- JUMP TO TASK LOGIC ---
    if 'jump_to_task' in st.session_state and st.session_state.jump_to_task is not None:
        jump_id = st.session_state.jump_to_task
        task_to_show = df_original[df_original['#'] == jump_id]
        
        if not task_to_show.empty:
            st.info("Showing details for the task selected from your notifications.")
            
            selected_task = task_to_show.iloc[0]

            # --- EDITING FORM FOR JUMPED-TO TASK ---
            st.subheader(f"Editing Task: {selected_task['TASK']}")
            with st.form(f"edit_jumped_task_form"):
                
                # Prepare dropdown options
                assignment_options = sorted([str(item) for item in df_original['ASSIGNMENT TITLE'].unique()])
                progress_options = ["NOT STARTED", "IN PROGRESS", "COMPLETE"]
                bucket_options_form = sorted([str(item) for item in df_original['PLANNER BUCKET'].unique()])
                semester_options = sorted([str(item) for item in df_original['SEMESTER'].unique() if pd.notna(item)])

                # Get current indices for dropdowns, with error handling for blank values
                try:
                    title_index = assignment_options.index(selected_task['ASSIGNMENT TITLE'])
                except (ValueError, TypeError):
                    title_index = 0
                try:
                    progress_index = progress_options.index(selected_task['PROGRESS'])
                except (ValueError, TypeError):
                    progress_index = 0
                try:
                    bucket_index = bucket_options_form.index(selected_task['PLANNER BUCKET'])
                except (ValueError, TypeError):
                    bucket_index = 0
                try:
                    current_semester = str(selected_task.get('SEMESTER', ''))
                    semester_index = semester_options.index(current_semester) if current_semester in semester_options else 0
                except (ValueError, TypeError):
                    semester_index = 0
                
                # Form layout
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_assignment_title = st.selectbox("Assignment Title", options=assignment_options, index=title_index)
                    new_progress = st.selectbox("Progress", options=progress_options, index=progress_index)
                with c2:
                    new_start_date = st.date_input("Start Date", value=pd.to_datetime(selected_task['START']))
                    new_end_date = st.date_input("End Date", value=pd.to_datetime(selected_task['END']))
                with c3:
                    new_bucket = st.selectbox("Planner Bucket", options=bucket_options_form, index=bucket_index)
                    new_semester = st.selectbox("Semester", options=semester_options, index=semester_index)

                submitted_edit = st.form_submit_button("Save Task Changes")
                if submitted_edit:
                    df_updated = df_original.copy()
                    df_updated.loc[df_updated['#'] == jump_id, 'ASSIGNMENT TITLE'] = new_assignment_title
                    df_updated.loc[df_updated['#'] == jump_id, 'PROGRESS'] = new_progress
                    df_updated.loc[df_updated['#'] == jump_id, 'START'] = pd.to_datetime(new_start_date)
                    df_updated.loc[df_updated['#'] == jump_id, 'END'] = pd.to_datetime(new_end_date)
                    df_updated.loc[df_updated['#'] == jump_id, 'PLANNER BUCKET'] = new_bucket
                    df_updated.loc[df_updated['#'] == jump_id, 'SEMESTER'] = new_semester
                    
                    if data_manager.save_and_log_changes(df_original, df_updated):
                        st.success("Task updated successfully!")
                        st.rerun()

            st.markdown("---")
            # --- END OF NEW EDITING FORM ---

            st.subheader(f"Comments for Task: {selected_task['TASK']}")
            comments = data_manager.get_comments_for_task(jump_id)
            if not comments.empty:
                for _, comment in comments.iterrows():
                    ts = pd.to_datetime(comment['timestamp']).strftime('%Y-%m-%d %H:%M')
                    st.info(f"**{comment['user_email']}** ({ts}):\n\n{comment['comment_text']}")
            else:
                st.write("No comments yet for this task.")

            with st.form(f"comment_form_{jump_id}", clear_on_submit=True):
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
                        data_manager.add_comment_and_notify(jump_id, author_email, comment_text, assigned_title, additional_recipients)
                        st.success("Comment posted!")
                        st.rerun()

            if st.button("Back to Full List"):
                # Clear the jump state and rerun to show the main page
                st.session_state.jump_to_task = None
                st.rerun()
            st.markdown("---")
        
        # Stop the rest of the page from rendering to keep the view focused
        st.stop()
    # ------------------------------------

    # --- FILTERS AND MAIN DATA EDITOR ---
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
    if st.session_state.find_bucket_filter != 'All':
        filtered_df = filtered_df[filtered_df['PLANNER BUCKET'] == st.session_state.find_bucket_filter]
    if st.session_state.find_year_filter != 'All':
        filtered_df = filtered_df[filtered_df['Fiscal Year'].astype(str) == st.session_state.find_year_filter]
    if search_term:
        filtered_df = filtered_df[filtered_df['TASK'].astype(str).str.contains(search_term, case=False, na=False)]

    st.markdown("---")
    
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

    if st.button("Save Edits to Table"):
        df_updated = df_original.copy()
        edited_df_for_save = edited_df.drop(columns=['Details'])
        
        df_updated.set_index('#', inplace=True)
        edited_df_indexed = edited_df_for_save.set_index('#')
        df_updated.update(edited_df_indexed)
        df_updated.reset_index(inplace=True)
        
        if data_manager.save_and_log_changes(df_original, df_updated):
            st.success("Edits saved successfully!")
            st.rerun()
        else:
            st.error("Failed to save edits.")
else:
    st.warning("Could not load data from the database.")

