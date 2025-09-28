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
            # (This section remains the same)
            # ...

        with admin_tab2:
            st.header("Manage Assignment Titles")
            current_titles = sorted([str(item) for item in tasks_df['ASSIGNMENT TITLE'].unique()])

            # (Add New Title section remains the same)
            # ...
            
            # --- Edit or Delete an Existing Title ---
            st.subheader("Edit or Delete an Existing Title")
            title_to_manage = st.selectbox("Select an Assignment Title to Manage", options=current_titles)

            if title_to_manage:
                # (Rename Title section remains the same)
                # ...

                # --- Delete Logic ---
                with st.expander(f"Delete '{title_to_manage}'"):
                    # (Display logic for users and tasks assigned remains the same)
                    # ...
                    
                    submitted_delete = st.button("Delete Title Permanently", type="primary")
                    if submitted_delete:
                        # --- CRITICAL FIX IS HERE ---
                        # Convert Fiscal Year to a numeric type, treating errors as empty (NaN)
                        # Then fill empty values with 0 so the comparison works.
                        tasks_df['Fiscal Year'] = pd.to_numeric(tasks_df['Fiscal Year'], errors='coerce').fillna(0)
                        # -------------------------

                        # Check for dependencies
                        users_assigned = users_df[users_df['assignment_title'] == title_to_manage]
                        tasks_assigned = tasks_df[(tasks_df['ASSIGNMENT TITLE'] == title_to_manage) & (tasks_df['Fiscal Year'] > 1901)]

                        if not users_assigned.empty:
                            st.error(f"Cannot delete. This title is assigned to {len(users_assigned)} user(s). Please reassign them first.")
                        elif not tasks_assigned.empty:
                            st.error(f"Cannot delete. This title is assigned to {len(tasks_assigned)} real task(s). Please reassign them first.")
                        else:
                            # Safe to delete. Remove all tasks with this title (which should only be placeholders)
                            tasks_df_after_delete = tasks_df[tasks_df['ASSIGNMENT TITLE'] != title_to_manage]
                            data_manager.save_table(tasks_df_after_delete, 'tasks')
                            st.success(f"'{title_to_manage}' has been deleted successfully.")
                            st.rerun()
