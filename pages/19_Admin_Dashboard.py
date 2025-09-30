# File: pages/19_Admin_Dashboard.py
import streamlit as st
import pandas as pd
import data_manager

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

# Load all necessary data tables
icons_df_original = data_manager.load_table('bucket_icons')
tasks_df_original = data_manager.load_table('tasks')
users_df_original = data_manager.load_table('users')
settings_df_original = data_manager.load_table('settings')

if icons_df_original is not None and tasks_df_original is not None and users_df_original is not None and settings_df_original is not None:
    
    # Create three tabs for the different admin functions
    tab1, tab2, tab3 = st.tabs(["Manage Planner Buckets", "Manage User Settings", "Manage Assignment Titles"])

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
                        if new_bucket_name in icons_df_original['bucket_name'].values:
                            st.error(f"The bucket '{new_bucket_name}' already exists.")
                        else:
                            new_entry = pd.DataFrame([{"bucket_name": new_bucket_name, "icon": new_icon}])
                            updated_icons_df = pd.concat([icons_df_original, new_entry], ignore_index=True)
                            if data_manager.save_table(updated_icons_df, 'bucket_icons'):
                                st.success(f"Added new bucket: '{new_bucket_name}' with icon {new_icon}")
                                st.rerun()
                    else:
                        st.warning("Please provide both a name and an icon.")

        # --- Edit Existing Icons ---
        st.subheader("Edit or Delete Existing Buckets and Icons")
        edited_icons_df = st.data_editor(icons_df_original, num_rows="dynamic", hide_index=True, key="icon_editor")

        if st.button("Save Icon & Bucket Changes"):
            tasks_df_to_update = tasks_df_original.copy()
            tasks_were_updated = False
            original_names = icons_df_original['bucket_name'].to_dict()

            for index, row in edited_icons_df.iterrows():
                if index in original_names:
                    old_name, new_name = original_names[index], row['bucket_name']
                    if old_name != new_name:
                        tasks_df_to_update['PLANNER BUCKET'] = tasks_df_to_update['PLANNER BUCKET'].replace(old_name, new_name)
                        tasks_were_updated = True
            
            if tasks_were_updated:
                data_manager.save_table(tasks_df_to_update, 'tasks')
            
            if data_manager.save_table(edited_icons_df, 'bucket_icons'):
                st.success("Bucket and icon changes have been saved.")
                st.rerun()

    with tab2:
        st.header("User Account Management")
        
        all_user_emails = sorted(users_df_original['email'].tolist())
        selected_user_for_edit = st.selectbox("Select a User to Edit", options=all_user_emails)

        if selected_user_for_edit:
            user_data = users_df_original[users_df_original['email'] == selected_user_for_edit].iloc[0]
            
            with st.form("admin_edit_user_form"):
                st.write(f"Editing profile for: **{user_data['first_name']} {user_data['last_name']}** (`{user_data['email']}`)")
                
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

    with tab3:
        st.header("Manage Assignment Titles")
        current_titles = sorted([str(item) for item in tasks_df_original['ASSIGNMENT TITLE'].unique()])

        with st.expander("Add a New Assignment Title"):
            with st.form("add_title_form", clear_on_submit=True):
                new_title_to_add = st.text_input("Enter New Assignment Title to Add")
                submitted_add = st.form_submit_button("Add New Title")
                if submitted_add:
                    if new_title_to_add and new_title_to_add not in current_titles:
                        new_task = pd.DataFrame([{'#': tasks_df_original['#'].max() + 1, 'ASSIGNMENT TITLE': new_title_to_add, 'TASK': 'Placeholder task for new title', 'PLANNER BUCKET': 'Admin', 'SEMESTER': 'N/A', 'Fiscal Year': 1900, 'AUDIENCE': 'N/A', 'START': pd.to_datetime('1900-01-01'), 'END': pd.to_datetime('1900-01-01'), 'PROGRESS': 'NOT STARTED'}])
                        updated_tasks_df = pd.concat([tasks_df_original, new_task], ignore_index=True)
                        if data_manager.save_table(updated_tasks_df, 'tasks'):
                            st.success(f"Successfully added '{new_title_to_add}'.")
                            st.rerun()
                    else:
                        st.error(f"Title is empty or already exists.")
        
        st.subheader("Edit or Delete an Existing Assignment Title")
        title_to_manage = st.selectbox("Select an Assignment Title to Manage", options=current_titles)

        if title_to_manage:
            with st.expander(f"Rename '{title_to_manage}'"):
                with st.form("edit_title_form"):
                    new_name = st.text_input("New Title Name", value=title_to_manage)
                    submitted_edit = st.form_submit_button("Update Title")
                    if submitted_edit:
                        if new_name and new_name != title_to_manage:
                            tasks_df_updated = tasks_df_original.copy()
                            users_df_updated = users_df_original.copy()
                            tasks_df_updated['ASSIGNMENT TITLE'] = tasks_df_updated['ASSIGNMENT TITLE'].replace(title_to_manage, new_name)
                            users_df_updated['assignment_title'] = users_df_updated['assignment_title'].replace(title_to_manage, new_name)
                            data_manager.save_table(tasks_df_updated, 'tasks')
                            data_manager.save_table(users_df_updated, 'users')
                            st.success(f"'{title_to_manage}' has been renamed to '{new_name}'.")
                            st.rerun()
                        else:
                            st.warning("Please provide a new, different name.")

            with st.expander(f"Delete '{title_to_manage}'"):
                st.warning(f"**Warning:** Deleting a title is permanent.")
                st.write("**Users currently assigned to this title:**")
                users_assigned = users_df_original[users_df_original['assignment_title'] == title_to_manage]
                if not users_assigned.empty:
                    st.dataframe(users_assigned[['first_name', 'last_name', 'email']])
                else:
                    st.info("No registered users are currently assigned to this title.")
                
                st.write("**Tasks currently assigned to this title (excluding placeholders):**")
                tasks_df_original['Fiscal Year'] = pd.to_numeric(tasks_df_original['Fiscal Year'], errors='coerce').fillna(0)
                tasks_assigned = tasks_df_original[(tasks_df_original['ASSIGNMENT TITLE'] == title_to_manage) & (tasks_df_original['Fiscal Year'] > 1901)]
                if not tasks_assigned.empty:
                    st.dataframe(tasks_assigned[['TASK', 'Fiscal Year']])
                else:
                    st.info("No active tasks are currently assigned to this title.")
                
                if st.button("Delete Title Permanently", type="primary"):
                    if not users_assigned.empty or not tasks_assigned.empty:
                        st.error("Cannot delete. This title is still assigned to users or real tasks. Please reassign them first.")
                    else:
                        tasks_df_after_delete = tasks_df_original[tasks_df_original['ASSIGNMENT TITLE'] != title_to_manage]
                        data_manager.save_table(tasks_df_after_delete, 'tasks')
                        st.success(f"'{title_to_manage}' has been deleted successfully.")
                        st.rerun()
else:
    st.warning("Could not load all necessary data from the database.")

