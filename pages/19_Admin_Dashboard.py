# File: pages/0_Admin_Dashboard.py
import streamlit as st
import pandas as pd
import data_manager
from datetime import datetime

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
user_role = st.session_state.user_data.get('role')
if user_role != 'admin':
    st.error("You do not have permission to view this page. This page is for administrators only.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("👑 Admin Dashboard")
st.info("This dashboard provides tools for managing application-wide settings.")

# Notify admin if bucket_icons was auto-created on startup
try:
    created = []
    if data_manager.pop_bucket_icons_auto_created():
        created.append("bucket_icons")
    # check notifications flag too (we added a similar flag)
    try:
        if data_manager.pop_notifications_auto_created():
            created.append('notifications')
    except Exception:
        # If the flag doesn't exist, ignore
        pass

    if created:
        st.info(f"The following tables were missing and have been auto-created: {', '.join(created)}. You can review and edit them below.")
except Exception:
    # If for some reason the flag isn't available, silently ignore
    pass

# Load all necessary data tables at the beginning
icons_df_original = data_manager.load_table('bucket_icons')
tasks_df_original = data_manager.load_table('tasks')
users_df_original = data_manager.load_table('users')
settings_df_original = data_manager.load_table('settings')
changelog_df_original = data_manager.load_table('changelog')


if all(df is not None for df in [icons_df_original, tasks_df_original, users_df_original, settings_df_original, changelog_df_original]):
    
    user_email = st.session_state.logged_in_user

    # Create four tabs for the different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["Manage Planner Buckets", "Manage User Settings", "Manage Assignment Titles", "View Changelog"])

    with tab1:
        st.header("Planner Bucket Icon Management")
        
        # --- SYNCHRONIZE BUCKETS ---
        all_buckets_in_use = set(tasks_df_original['PLANNER BUCKET'].dropna().unique())
        buckets_with_icons = set(icons_df_original['bucket_name'].dropna().unique())
        new_buckets_to_add = all_buckets_in_use - buckets_with_icons
        
        if new_buckets_to_add:
            st.info(f"Found {len(new_buckets_to_add)} new Planner Bucket(s). Adding them to the list with a default icon.")
            new_entries_df = pd.DataFrame([{"bucket_name": bucket, "icon": "📌"} for bucket in new_buckets_to_add])
            icons_df_updated = pd.concat([icons_df_original, new_entries_df], ignore_index=True)
            data_manager.save_table(icons_df_updated, 'bucket_icons')
            st.rerun()

        # --- Add New Bucket Icon ---
        with st.expander("Add New Planner Bucket and Icon"):
            with st.form("new_bucket_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    new_bucket_name = st.text_input("New Planner Bucket Name")
                with col2:
                    new_icon = st.text_input("Associated Icon (Emoji)", "📌")
                
                submitted_add = st.form_submit_button("Add New Bucket")
                if submitted_add:
                    if new_bucket_name and new_icon:
                        current_icons_df = data_manager.load_table('bucket_icons')
                        if new_bucket_name in current_icons_df['bucket_name'].values:
                            st.error(f"The bucket '{new_bucket_name}' already exists.")
                        else:
                            new_entry = pd.DataFrame([{"bucket_name": new_bucket_name, "icon": new_icon}])
                            updated_icons_df = pd.concat([current_icons_df, new_entry], ignore_index=True)
                            if data_manager.save_table(updated_icons_df, 'bucket_icons'):
                                st.success(f"Added new bucket: '{new_bucket_name}' with icon {new_icon}")
                                st.rerun()
                    else:
                        st.warning("Please provide both a name and an icon.")

        # --- Edit Existing Icons ---
        st.subheader("Edit or Delete Existing Buckets and Icons")
        edited_icons_df = st.data_editor(icons_df_original, num_rows="dynamic", hide_index=True, key="icon_editor")

        if st.button("Save Icon & Bucket Changes"):
            log_entries = []
            timestamp = datetime.now()
            tasks_df_to_update = tasks_df_original.copy()
            tasks_were_updated = False

            # --- CORRECTED LOGIC TO HANDLE ALL CHANGES ---
            # Iterate through the original indices to reliably detect all changes
            for index in icons_df_original.index:
                # Check if the row still exists in the edited dataframe (it wasn't deleted)
                if index in edited_icons_df.index:
                    old_row = icons_df_original.loc[index]
                    new_row = edited_icons_df.loc[index]

                    # Check for a bucket name change
                    if old_row['bucket_name'] != new_row['bucket_name']:
                        old_name, new_name = old_row['bucket_name'], new_row['bucket_name']
                        tasks_df_to_update['PLANNER BUCKET'] = tasks_df_to_update['PLANNER BUCKET'].replace(old_name, new_name)
                        tasks_were_updated = True
                        log_entries.append({
                            'Timestamp': timestamp, 'Action': 'EDIT', 'Task ID': 'N/A', 'User': user_email,
                            'Source': 'Admin - Planner Buckets', 'Field Changed': 'Planner Bucket Name', 
                            'Old Value': old_name, 'New Value': new_name
                        })
                    
                    # Check for an icon change
                    if old_row['icon'] != new_row['icon']:
                        log_entries.append({
                            'Timestamp': timestamp, 'Action': 'EDIT', 'Task ID': 'N/A', 'User': user_email,
                            'Source': 'Admin - Planner Buckets', 'Field Changed': 'Planner Bucket Icon', 
                            'Old Value': f"{new_row['bucket_name']}: {old_row['icon']}", 
                            'New Value': f"{new_row['bucket_name']}: {new_row['icon']}"
                        })
            
            # --- END OF CORRECTED LOGIC ---

            # --- CORRECTED SAVE AND LOGGING SEQUENCE ---
            # 1. Save the tasks table if it was modified by a rename, using the logging function
            if tasks_were_updated:
                if not data_manager.save_and_log_changes(tasks_df_original, tasks_df_to_update, user_email, "Admin - Planner Buckets"):
                    st.error("Failed to update tasks table. Aborting save.")
                    st.stop()
            
            # 2. Save any administrative log entries we created for icon-only changes
            if log_entries and not tasks_were_updated:
                new_log_df = pd.DataFrame(log_entries)
                changelog_updated = pd.concat([changelog_df_original, new_log_df], ignore_index=True)
                data_manager.save_table(changelog_updated, 'changelog')
            
            # 3. Save the final state of the icons table
            if data_manager.save_table(edited_icons_df, 'bucket_icons'):
                st.success("Bucket and icon changes have been saved and logged successfully.")
                st.rerun()
            else:
                st.error("Failed to save bucket and icon changes.")
            # --- END OF CORRECTED SEQUENCE ---

    with tab2:
        st.header("User Account Management")
        all_user_emails = sorted(users_df_original['email'].tolist())
        selected_user_for_edit = st.selectbox("Select a User to Edit", options=all_user_emails)

        if selected_user_for_edit:
            user_data = users_df_original[users_df_original['email'] == selected_user_for_edit].iloc[0]
            
            with st.form("admin_edit_user_form"):
                st.write(f"Editing profile for: **{user_data['first_name']} {user_data['last_name']}**")
                
                status_options = ["active", "inactive"]
                current_status_index = status_options.index(user_data.get('status', 'active'))
                new_status = st.selectbox("User Status", options=status_options, index=current_status_index)

                assignment_options = sorted([str(item) for item in tasks_df_original['ASSIGNMENT TITLE'].unique()])
                current_title_index = assignment_options.index(user_data['assignment_title']) if user_data['assignment_title'] in assignment_options else 0
                new_assignment_title = st.selectbox("Assignment Title", options=assignment_options, index=current_title_index)
                
                frequency_options = ["Never", "Daily", "Weekly"]
                user_current_freq = settings_df_original[settings_df_original['email'] == selected_user_for_edit]['frequency'].values[0] if selected_user_for_edit in settings_df_original['email'].values else 'Never'
                user_current_index = frequency_options.index(user_current_freq)
                new_user_freq = st.selectbox(f"Email Frequency", options=frequency_options, index=user_current_index)
                
                new_password = st.text_input("Reset Password (leave blank to keep current)", type="password")

                if st.form_submit_button("Save User Changes"):
                    users_df_updated = users_df_original.copy()
                    users_df_updated.loc[users_df_updated['email'] == selected_user_for_edit, 'status'] = new_status
                    users_df_updated.loc[users_df_updated['email'] == selected_user_for_edit, 'assignment_title'] = new_assignment_title
                    if new_password:
                        users_df_updated.loc[users_df_updated['email'] == selected_user_for_edit, 'password'] = new_password
                    
                    settings_df_updated = settings_df_original.copy()
                    if selected_user_for_edit not in settings_df_updated['email'].values:
                        new_setting = pd.DataFrame([{'email': selected_user_for_edit, 'frequency': new_user_freq}])
                        settings_df_updated = pd.concat([settings_df_updated, new_setting], ignore_index=True)
                    else:
                        settings_df_updated.loc[settings_df_updated['email'] == selected_user_for_edit, 'frequency'] = new_user_freq

                    user_save_success = data_manager.save_table(users_df_updated, 'users')
                    settings_save_success = data_manager.save_table(settings_df_updated, 'settings')
                    
                    if user_save_success and settings_save_success:
                        st.success(f"User details for {selected_user_for_edit} have been updated.")
                        st.rerun()

            with st.expander("Delete User"):
                st.warning(f"**Danger Zone:** Deleting a user is permanent and cannot be undone.")
                tasks_assigned = tasks_df_original[tasks_df_original['ASSIGNMENT TITLE'] == user_data['assignment_title']]
                if not tasks_assigned.empty:
                    st.error(f"This user's assignment title is linked to {len(tasks_assigned)} task(s). Please reassign these tasks before deleting the user.")
                else:
                    confirm_delete = st.checkbox(f"I understand that I am permanently deleting the user {selected_user_for_edit}.")
                    if st.button("Delete User Permanently", type="primary", disabled=(not confirm_delete)):
                        users_df_after_delete = users_df_original[users_df_original['email'] != selected_user_for_edit]
                        settings_df_after_delete = settings_df_original[settings_df_original['email'] != selected_user_for_edit]
                        
                        user_delete_success = data_manager.save_table(users_df_after_delete, 'users')
                        settings_delete_success = data_manager.save_table(settings_df_after_delete, 'settings')
                        
                        if user_delete_success and settings_delete_success:
                            st.success(f"User {selected_user_for_edit} has been permanently deleted.")
                            st.rerun()

    with tab3:
        st.header("Manage Assignment Titles")
        current_titles = sorted([str(item) for item in tasks_df_original['ASSIGNMENT TITLE'].unique()])

        with st.expander("Add a New Assignment Title"):
            with st.form("add_title_form", clear_on_submit=True):
                new_title_to_add = st.text_input("Enter New Assignment Title to Add")
                if st.form_submit_button("Add New Title"):
                    if new_title_to_add and new_title_to_add not in current_titles:
                        new_task = pd.DataFrame([{'#': tasks_df_original['#'].max() + 1, 'ASSIGNMENT TITLE': new_title_to_add, 'TASK': 'Placeholder task for new title', 'PLANNER BUCKET': 'Admin', 'SEMESTER': 'N/A', 'Fiscal Year': 1900, 'AUDIENCE': 'N/A', 'START': pd.to_datetime('1900-01-01'), 'END': pd.to_datetime('1900-01-01'), 'PROGRESS': 'NOT STARTED'}])
                        updated_tasks_df = pd.concat([tasks_df_original, new_task], ignore_index=True)
                        if data_manager.save_and_log_changes(tasks_df_original, updated_tasks_df, user_email, source_page="Admin - Add Title"):
                            st.success(f"Successfully added '{new_title_to_add}'.")
                            st.rerun()
        
        st.subheader("Edit or Delete an Existing Assignment Title")
        title_to_manage = st.selectbox("Select an Assignment Title to Manage", options=current_titles)

        if title_to_manage:
            with st.expander(f"Rename '{title_to_manage}'"):
                with st.form("edit_title_form"):
                    new_name = st.text_input("New Title Name", value=title_to_manage)
                    if st.form_submit_button("Update Title"):
                        if new_name and new_name != title_to_manage:
                            tasks_df_updated = tasks_df_original.copy()
                            users_df_updated = users_df_original.copy()
                            tasks_df_updated['ASSIGNMENT TITLE'] = tasks_df_updated['ASSIGNMENT TITLE'].replace(title_to_manage, new_name)
                            users_df_updated['assignment_title'] = users_df_updated['assignment_title'].replace(title_to_manage, new_name)
                            data_manager.save_and_log_changes(tasks_df_original, tasks_df_updated, user_email, source_page="Admin - Rename Title")
                            data_manager.save_table(users_df_updated, 'users')
                            st.success(f"'{title_to_manage}' has been renamed to '{new_name}'.")
                            st.rerun()

            with st.expander(f"Delete '{title_to_manage}'"):
                if st.button("Delete Title Permanently", type="primary"):
                    users_assigned = users_df_original[users_df_original['assignment_title'] == title_to_manage]
                    tasks_df_original['Fiscal Year'] = pd.to_numeric(tasks_df_original['Fiscal Year'], errors='coerce').fillna(0)
                    tasks_assigned = tasks_df_original[(tasks_df_original['ASSIGNMENT TITLE'] == title_to_manage) & (tasks_df_original['Fiscal Year'] > 1901)]
                    if not users_assigned.empty or not tasks_assigned.empty:
                        st.error("Cannot delete. This title is still assigned to users or real tasks.")
                    else:
                        tasks_df_after_delete = tasks_df_original[tasks_df_original['ASSIGNMENT TITLE'] != title_to_manage]
                        if data_manager.save_and_log_changes(tasks_df_original, tasks_df_after_delete, user_email, source_page="Admin - Delete Title"):
                            st.success(f"'{title_to_manage}' has been deleted successfully.")
                            st.rerun()
                            
    with tab4:
        st.header("📜 View Changelog")
        st.write("This log shows all data changes made within the application.")

    with st.expander("Calendar Subscription (Outlook)"):
        st.write("You can run a small local server that serves a dynamic .ics subscription endpoint compatible with Outlook.")
        st.markdown("- Start the server: `python calendar_server.py` (installs: Flask required).")
        st.markdown("- Default subscription URL: `http://localhost:5005/calendar.ics`")
        st.info("To include only a specific planner bucket, append `?bucket=YourBucketName` to the URL. To filter by fiscal year, append `?year=2025`.")
        
        if not changelog_df_original.empty:
            changelog_df_original['Timestamp'] = pd.to_datetime(changelog_df_original['Timestamp'])
            
            st.subheader("Filter Changelog")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                action_options = ['All'] + changelog_df_original['Action'].unique().tolist()
                selected_action = st.selectbox("Filter by Action", options=action_options)
            with col2:
                source_options = ['All'] + changelog_df_original['Source'].unique().tolist()
                selected_source = st.selectbox("Filter by Source", options=source_options)
            with col3:
                min_date = changelog_df_original['Timestamp'].min().date()
                start_date = st.date_input("Start Date", value=min_date)
            with col4:
                max_date = changelog_df_original['Timestamp'].max().date()
                end_date = st.date_input("End Date", value=max_date)

            filtered_log = changelog_df_original.copy()
            
            if selected_action != 'All':
                filtered_log = filtered_log[filtered_log['Action'] == selected_action]
            if selected_source != 'All':
                filtered_log = filtered_log[filtered_log['Source'] == selected_source]
                
            start_date_dt = pd.to_datetime(start_date)
            end_date_dt = pd.to_datetime(end_date)
            
            filtered_log = filtered_log[
                (filtered_log['Timestamp'] >= start_date_dt) & 
                (filtered_log['Timestamp'] < end_date_dt + pd.Timedelta(days=1))
            ]

            st.markdown("---")
            st.dataframe(filtered_log.sort_values(by='Timestamp', ascending=False), use_container_width=True)
        else:
            st.info("The changelog is currently empty.")

else:
    st.warning("Could not load all necessary data from the database.")

