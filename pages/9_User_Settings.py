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
# ... (This section remains the same)
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
    if users_df is not None:
        
        admin_tab1, admin_tab2 = st.tabs(["Manage User Settings", "Manage Assignment Titles"])

        with admin_tab1:
            # --- Manage User Settings ---
            all_user_emails = sorted(users_df['email'].tolist())
            selected_user_for_edit = st.selectbox("Select a User to Edit", options=all_user_emails)
            
            if selected_user_for_edit:
                # (Password reset and frequency settings for other users remain the same)
                st.write(f"**Notification Settings for {selected_user_for_edit}**")
                # ...
                st.write("---")
                st.write(f"**Password Management for {selected_user_for_edit}**")
                # ...

        with admin_tab2:
            # --- NEW: Manage Assignment Titles ---
            st.write("The list of Assignment Titles available during user registration is pulled from the main tasks table. Here, you can add a new title to that list.")
            
            tasks_df = data_manager.load_table('tasks')
            if tasks_df is not None:
                # Convert all items to string to handle mixed data types, then sort
                current_titles = sorted([str(item) for item in tasks_df['ASSIGNMENT TITLE'].unique()])
                with st.expander("View Current Assignment Titles"):
                    st.write(current_titles)

                with st.form("add_title_form", clear_on_submit=True):
                    new_title = st.text_input("Enter New Assignment Title to Add")
                    submitted = st.form_submit_button("Add New Title")

                    if submitted:
                        if new_title and new_title not in current_titles:
                            # To add a title, we must add a placeholder task row
                            new_task = pd.DataFrame([{
                                '#': tasks_df['#'].max() + 1,
                                'ASSIGNMENT TITLE': new_title,
                                'TASK': 'Placeholder task for new title',
                                'PLANNER BUCKET': 'Admin',
                                'SEMESTER': 'N/A',
                                'Fiscal Year': 1900,
                                'AUDIENCE': 'N/A',
                                'START': pd.to_datetime('1900-01-01'),
                                'END': pd.to_datetime('1900-01-01'),
                                'PROGRESS': 'NOT STARTED'
                            }])
                            
                            updated_tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
                            if data_manager.save_table(updated_tasks_df, 'tasks'):
                                st.success(f"Successfully added the new title: '{new_title}'. It will now be available on the registration page.")
                                st.rerun()
                        elif not new_title:
                            st.warning("Please enter a title.")
                        else:
                            st.error(f"The title '{new_title}' already exists.")