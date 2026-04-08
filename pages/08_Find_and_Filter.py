# File: pages/7_Find_and_Filter.py
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
st.title("🔍 Find, Filter & Edit Tasks")

df_original = data_manager.load_table('tasks')
users_df = data_manager.load_table('users')

if df_original is not None and users_df is not None:
    # --- FILTERS ---
    st.write("Use the controls below to filter, then click a task to edit or comment on it.")
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        bucket_options = ['All'] + sorted([str(item) for item in df_original['PLANNER BUCKET'].unique()])
        st.selectbox("Filter by Planner Bucket", options=bucket_options, key="find_bucket_filter")
    with col2:
        year_options = ['All'] + sorted([str(item) for item in df_original['Fiscal Year'].unique()])
        st.selectbox("Filter by Fiscal Year", options=year_options, key="find_year_filter", format_func=lambda x: data_manager.format_fy(x))
    with col3:
        search_term = st.text_input("Search across all fields (case-insensitive)")

    # Apply filters sequentially
    filtered_df = df_original.copy()
    if 'find_bucket_filter' in st.session_state and st.session_state.find_bucket_filter != 'All':
        filtered_df = filtered_df[filtered_df['PLANNER BUCKET'] == st.session_state.find_bucket_filter]
    if 'find_year_filter' in st.session_state and st.session_state.find_year_filter != 'All':
        filtered_df = filtered_df[filtered_df['Fiscal Year'].astype(str) == st.session_state.find_year_filter]
    if search_term:
        mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
        filtered_df = filtered_df[mask]

    st.markdown("---")

    # --- RESULTS TABLE (read-only summary) ---
    st.subheader(f"Results ({len(filtered_df)} tasks)")

    if filtered_df.empty:
        st.info("No tasks match your filters.")
    else:
        # Build display labels for the selectbox
        task_labels = {}
        for _, row in filtered_df.iterrows():
            label = f"#{int(row['#'])} — {row['TASK']} ({row['PLANNER BUCKET']}, {data_manager.format_fy(row['Fiscal Year'])})"
            task_labels[label] = int(row['#'])

        # Show a compact table overview
        display_df = filtered_df[['#', 'TASK', 'ASSIGNMENT TITLE', 'PLANNER BUCKET', 'PROGRESS', 'START', 'END']].copy()
        display_df['START'] = pd.to_datetime(display_df['START']).dt.strftime('%m-%d-%Y')
        display_df['END'] = pd.to_datetime(display_df['END']).dt.strftime('%m-%d-%Y')
        st.dataframe(display_df, hide_index=True, use_container_width=True)

        # --- TASK SELECTOR ---
        st.markdown("---")
        selected_label = st.selectbox(
            "Select a task to edit, delete, or comment on",
            options=['--'] + list(task_labels.keys()),
            key="find_task_selector"
        )

        if selected_label != '--':
            task_id = task_labels[selected_label]
            task_row = df_original[df_original['#'] == task_id].iloc[0]

            # =========================================================
            # EDIT & DELETE SECTION
            # =========================================================
            st.subheader(f"Edit Task #{task_id}")

            edit_tab, delete_tab = st.tabs(["✏️ Edit All Fields", "🗑️ Delete Task"])

            with edit_tab:
                with st.form(f"edit_form_{task_id}"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        assignment_options = sorted(df_original['ASSIGNMENT TITLE'].dropna().unique().tolist())
                        current_assignment = task_row['ASSIGNMENT TITLE']
                        assignment_idx = assignment_options.index(current_assignment) if current_assignment in assignment_options else 0
                        edit_assignment = st.selectbox("Assignment Title", options=assignment_options, index=assignment_idx)

                        bucket_opts = sorted(df_original['PLANNER BUCKET'].dropna().unique().tolist())
                        current_bucket = task_row['PLANNER BUCKET']
                        bucket_idx = bucket_opts.index(current_bucket) if current_bucket in bucket_opts else 0
                        edit_bucket = st.selectbox("Planner Bucket", options=bucket_opts, index=bucket_idx)

                        semester_opts = sorted(df_original['SEMESTER'].dropna().unique().tolist())
                        current_semester = task_row['SEMESTER']
                        semester_idx = semester_opts.index(current_semester) if current_semester in semester_opts else 0
                        edit_semester = st.selectbox("Semester", options=semester_opts, index=semester_idx)

                        fy_opts = sorted(df_original['Fiscal Year'].dropna().unique().tolist())
                        current_fy = task_row['Fiscal Year']
                        fy_idx = fy_opts.index(current_fy) if current_fy in fy_opts else 0
                        edit_fy = st.selectbox("Fiscal Year", options=fy_opts, index=fy_idx, format_func=lambda x: data_manager.format_fy(x))

                    with e_col2:
                        edit_task_desc = st.text_area("Task Description", value=str(task_row['TASK']))

                        audience_opts = sorted(df_original['AUDIENCE'].dropna().unique().tolist())
                        current_audience = task_row['AUDIENCE']
                        audience_idx = audience_opts.index(current_audience) if current_audience in audience_opts else 0
                        edit_audience = st.selectbox("Audience", options=audience_opts, index=audience_idx)

                        progress_opts = ["NOT STARTED", "IN PROGRESS", "COMPLETE"]
                        current_progress = task_row['PROGRESS']
                        progress_idx = progress_opts.index(current_progress) if current_progress in progress_opts else 0
                        edit_progress = st.selectbox("Progress", options=progress_opts, index=progress_idx)

                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        start_val = pd.to_datetime(task_row['START'])
                        edit_start = st.date_input("Start Date", value=start_val.date() if pd.notna(start_val) else None, format="MM-DD-YYYY")
                    with d_col2:
                        end_val = pd.to_datetime(task_row['END'])
                        edit_end = st.date_input("End Date", value=end_val.date() if pd.notna(end_val) else None, format="MM-DD-YYYY")

                    save_edit = st.form_submit_button("💾 Save Changes", type="primary")
                    if save_edit:
                        df_updated = df_original.copy()
                        mask = df_updated['#'] == task_id
                        df_updated.loc[mask, 'ASSIGNMENT TITLE'] = edit_assignment
                        df_updated.loc[mask, 'TASK'] = edit_task_desc
                        df_updated.loc[mask, 'PLANNER BUCKET'] = edit_bucket
                        df_updated.loc[mask, 'SEMESTER'] = edit_semester
                        df_updated.loc[mask, 'Fiscal Year'] = edit_fy
                        df_updated.loc[mask, 'AUDIENCE'] = edit_audience
                        df_updated.loc[mask, 'PROGRESS'] = edit_progress
                        df_updated.loc[mask, 'START'] = pd.to_datetime(edit_start)
                        df_updated.loc[mask, 'END'] = pd.to_datetime(edit_end)

                        user_email = st.session_state.logged_in_user
                        if data_manager.save_and_log_changes(df_original, df_updated, user_email, "Find and Filter"):
                            st.success("Task updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to save changes.")

            with delete_tab:
                st.warning(f"**Permanently delete** task #{task_id}: *{task_row['TASK']}*?")
                st.caption("This action cannot be undone. The deletion will be recorded in the changelog.")
                if st.button("🗑️ Confirm Delete", type="primary", key=f"delete_{task_id}"):
                    df_updated = df_original[df_original['#'] != task_id].copy()
                    user_email = st.session_state.logged_in_user
                    if data_manager.save_and_log_changes(df_original, df_updated, user_email, "Find and Filter"):
                        st.success(f"Task #{task_id} deleted and logged.")
                        st.rerun()
                    else:
                        st.error("Failed to delete task.")

            # =========================================================
            # COLLABORATION & COMMENTS SECTION
            # =========================================================
            st.markdown("---")
            st.subheader("💬 Task Discussion")
            st.caption("Use comments to coordinate with your team. The person assigned to the task is notified automatically when a comment is posted.")

            comments = data_manager.get_comments_for_task(task_id)
            if not comments.empty:
                for _, comment in comments.iterrows():
                    ts = pd.to_datetime(comment['timestamp']).strftime('%b %d, %Y at %I:%M %p')
                    with st.chat_message("user"):
                        st.markdown(f"**{comment['user_email']}** &nbsp;·&nbsp; {ts}")
                        st.markdown(comment['comment_text'])
            else:
                st.info("No comments yet — start the conversation below.")

            with st.form(f"comment_form_{task_id}", clear_on_submit=True):
                comment_text = st.text_area("Write a comment", placeholder="Share an update, ask a question, or note a decision...")

                all_user_emails = users_df['email'].tolist()
                author_email = st.session_state.logged_in_user
                other_users = [email for email in all_user_emails if email != author_email]

                additional_recipients = st.multiselect(
                    "Notify additional team members",
                    options=other_users,
                    help="The assigned person is always notified. Select others who should also receive an email and in-app notification."
                )

                submitted = st.form_submit_button("📨 Post Comment")
                if submitted:
                    if comment_text:
                        assigned_title = task_row['ASSIGNMENT TITLE']
                        data_manager.add_comment_and_notify(task_id, author_email, comment_text, assigned_title, additional_recipients)
                        st.success("Comment posted and notifications sent!")
                        st.rerun()
                    else:
                        st.warning("Please enter a comment before posting.")

            # --- ICS EXPORT FOR SELECTED TASK ---
            st.markdown("---")
            st.subheader("📅 Export to Calendar")
            single_df = df_original[df_original['#'] == task_id].copy()
            single_df = single_df[pd.notna(single_df['START']) & pd.notna(single_df['END'])]
            if not single_df.empty:
                ics_bytes = ics_export.generate_ics_from_df(single_df)
                st.download_button(
                    label=f"📥 Download .ics for task #{task_id}",
                    data=ics_bytes,
                    file_name=f"task_{task_id}.ics",
                    mime="text/calendar"
                )

    # --- ICS EXPORT FOR ALL FILTERED TASKS ---
    st.markdown("---")
    st.subheader("📅 Export Filtered Tasks to Calendar")
    export_df = filtered_df.copy()
    export_df = export_df[pd.notna(export_df['START']) & pd.notna(export_df['END'])]
    if not export_df.empty:
        ics_bytes = ics_export.generate_ics_from_df(export_df)
        st.download_button(
            label=f"📥 Download .ics for all {len(export_df)} filtered tasks",
            data=ics_bytes,
            file_name="filtered_tasks_calendar.ics",
            mime="text/calendar",
            key="download_filtered_ics"
        )
    else:
        st.caption("No tasks with valid dates to export.")
else:
    st.warning("Could not load data from the database.")


