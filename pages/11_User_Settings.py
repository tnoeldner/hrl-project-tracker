# File: pages/9_User_Settings.py
import streamlit as st
import pandas as pd
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="User Settings", layout="wide")
st.title("⚙️ User Settings")

user_email = st.session_state.logged_in_user
user_role = st.session_state.user_data.get('role')
settings_df = data_manager.load_table('settings')
if settings_df is None:
    settings_df = pd.DataFrame(columns=['email', 'frequency'])

# --- Current User's Settings ---
st.subheader("My Notification Preferences")
current_frequency = settings_df[settings_df['email'] == user_email]['frequency'].values[0] if user_email in settings_df['email'].values else 'Never'
frequency_options = ["Never", "Daily", "Weekly"]
new_frequency = st.selectbox(
    "My Email Frequency",
    options=frequency_options,
    index=frequency_options.index(current_frequency),
    key="my_frequency_selector"
)
if st.button("Save My Settings"):
    if user_email not in settings_df['email'].values:
        new_setting = pd.DataFrame([{'email': user_email, 'frequency': new_frequency}])
        settings_df = pd.concat([settings_df, new_setting], ignore_index=True)
    else:
        settings_df.loc[settings_df['email'] == user_email, 'frequency'] = new_frequency
    if data_manager.save_table(settings_df, 'settings'):
        st.success("Your notification settings have been saved!")

st.markdown("---")

# --- Administrator Section ---
if user_role == 'admin':
    st.subheader("👑 Administrator Settings")
    st.write("As an admin, you can manage user settings and available assignment titles.")
    
    users_df = data_manager.load_table('users')
    tasks_df = data_manager.load_table('tasks')

    if users_df is not None and tasks_df is not None:
        
        admin_tab1, admin_tab2 = st.tabs(["Manage User Settings", "Manage Assignment Titles"])

        with admin_tab1:
            st.header("Edit User Details")
            all_user_emails = sorted(users_df['email'].tolist())
            selected_user_for_edit = st.selectbox("Select a User to Edit", options=all_user_emails)

            if selected_user_for_edit:
                user_data = users_df[users_df['email'] == selected_user_for_edit].iloc[0]
                
                with st.form("admin_edit_user_form"):
                    st.write(f"Editing profile for: **{user_data['first_name']} {user_data['last_name']}**")
                    
                    # --- Edit Assignment Title ---
                    assignment_options = sorted([str(item) for item in tasks_df['ASSIGNMENT TITLE'].unique()])
                    current_title_index = assignment_options.index(user_data['assignment_title']) if user_data['assignment_title'] in assignment_options else 0
                    new_assignment_title = st.selectbox("Assignment Title", options=assignment_options, index=current_title_index)
                    
                    # --- Reset Password ---
                    new_password = st.text_input("Reset Password (leave blank to keep current)", type="password")

                    submitted_admin_edit = st.form_submit_button("Save User Changes")
                    if submitted_admin_edit:
                        users_df.loc[users_df['email'] == selected_user_for_edit, 'assignment_title'] = new_assignment_title
                        if new_password:
                            users_df.loc[users_df['email'] == selected_user_for_edit, 'password'] = new_password
                        
                        if data_manager.save_table(users_df, 'users'):
                            st.success(f"User details for {selected_user_for_edit} have been updated.")
                            st.rerun()

        with admin_tab2:
            st.header("Manage Assignment Titles")
            current_titles = sorted([str(item) for item in tasks_df['ASSIGNMENT TITLE'].unique()])

            with st.expander("Add a New Title"):
                with st.form("add_title_form", clear_on_submit=True):
                    new_title_to_add = st.text_input("Enter New Assignment Title to Add")
                    submitted_add = st.form_submit_button("Add New Title")
                    if submitted_add:
                        if new_title_to_add and new_title_to_add not in current_titles:
                            new_task = pd.DataFrame([{'#': tasks_df['#'].max() + 1, 'ASSIGNMENT TITLE': new_title_to_add, 'TASK': 'Placeholder task for new title', 'PLANNER BUCKET': 'Admin', 'SEMESTER': 'N/A', 'Fiscal Year': 1900, 'AUDIENCE': 'N/A', 'START': pd.to_datetime('1900-01-01'), 'END': pd.to_datetime('1900-01-01'), 'PROGRESS': 'NOT STARTED'}])
                            updated_tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
                            if data_manager.save_table(updated_tasks_df, 'tasks'):
                                st.success(f"Successfully added '{new_title_to_add}'.")
                                st.rerun()
                        else:
                            st.error(f"Title is empty or already exists.")
            
            st.subheader("Edit or Delete an Existing Title")
            title_to_manage = st.selectbox("Select an Assignment Title to Manage", options=current_titles)

            if title_to_manage:
                with st.expander(f"Rename '{title_to_manage}'"):
                    with st.form("edit_title_form"):
                        new_name = st.text_input("New Title Name", value=title_to_manage)
                        submitted_edit = st.form_submit_button("Update Title")
                        if submitted_edit:
                            if new_name and new_name != title_to_manage:
                                tasks_df['ASSIGNMENT TITLE'] = tasks_df['ASSIGNMENT TITLE'].replace(title_to_manage, new_name)
                                users_df['assignment_title'] = users_df['assignment_title'].replace(title_to_manage, new_name)
                                data_manager.save_table(tasks_df, 'tasks')
                                data_manager.save_table(users_df, 'users')
                                st.success(f"'{title_to_manage}' has been renamed to '{new_name}'.")
                                st.rerun()
                            else:
                                st.warning("Please provide a new, different name.")

                with st.expander(f"Delete '{title_to_manage}'"):
                    st.warning(f"**Warning:** Deleting a title is permanent.")
                    
                    st.write("**Users currently assigned to this title:**")
                    users_assigned_to_title = users_df[users_df['assignment_title'] == title_to_manage]
                    if not users_assigned_to_title.empty:
                        st.dataframe(users_assigned_to_title[['first_name', 'last_name', 'email']])
                    else:
                        st.info("No registered users are currently assigned to this title.")
                    
                    st.write("**Tasks currently assigned to this title (excluding placeholders):**")
                    tasks_df['Fiscal Year'] = pd.to_numeric(tasks_df['Fiscal Year'], errors='coerce').fillna(0)
                    tasks_assigned_to_title = tasks_df[(tasks_df['ASSIGNMENT TITLE'] == title_to_manage) & (tasks_df['Fiscal Year'] > 1901)]
                    if not tasks_assigned_to_title.empty:
                        st.dataframe(tasks_assigned_to_title[['TASK', 'Fiscal Year']])
                    else:
                        st.info("No active tasks are currently assigned to this title.")
                    
                    submitted_delete = st.button("Delete Title Permanently", type="primary")
                    if submitted_delete:
                        users_assigned = users_df[users_df['assignment_title'] == title_to_manage]
                        tasks_assigned = tasks_df[(tasks_df['ASSIGNMENT TITLE'] == title_to_manage) & (tasks_df['Fiscal Year'] > 1901)]

                        if not users_assigned.empty:
                            st.error(f"Cannot delete. This title is assigned to {len(users_assigned)} user(s). Please reassign them first.")
                        elif not tasks_assigned.empty:
                            st.error(f"Cannot delete. This title is assigned to {len(tasks_assigned)} real task(s). Please reassign them first.")
                        else:
                            tasks_df_after_delete = tasks_df[tasks_df['ASSIGNMENT TITLE'] != title_to_manage]
                            data_manager.save_table(tasks_df_after_delete, 'tasks')
                            st.success(f"'{title_to_manage}' has been deleted successfully.")
                            st.rerun()

