# File: Main.py
import streamlit as st
import pandas as pd
import data_manager
from datetime import datetime

# --- AUTHENTICATION FUNCTIONS (using the database) ---

def check_login(username, password):
    """Checks credentials and user status against the users table."""
    users_df = data_manager.load_table('users')
    if users_df is None:
        return None, "Error loading user data."
    
    user_record = users_df[users_df['email'] == username]
    if not user_record.empty and user_record.iloc[0]['password'] == password:
        # Check if the user is active
        if user_record.iloc[0].get('status', 'active') == 'active':
            return user_record.iloc[0].to_dict(), "Login successful."
        else:
            return None, "This user account is inactive. Please contact an administrator."
    return None, "Incorrect email or password."

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="HRL Project Tracker", layout="wide")

# Load project data for the registration dropdown
tasks_df = data_manager.load_table('tasks')

# --- LOGIN / REGISTRATION LOGIC ---
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    st.title("HRL Project Tracker Login")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Outlook Email Address")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                user_data, message = check_login(username, password)
                if user_data:
                    st.session_state.logged_in_user = username
                    st.session_state.user_data = user_data
                    st.rerun()
                else:
                    st.error(message)
    
    with register_tab:
        if tasks_df is not None:
            st.write("New users can register here. Select your name from the Assignment Title dropdown.")
            with st.form("register_form", clear_on_submit=True):
                email = st.text_input("Outlook Email Address")
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                assignment_options = sorted([str(item) for item in tasks_df['ASSIGNMENT TITLE'].unique()])
                assignment_title = st.selectbox("Assignment Title", options=assignment_options)
                
                reg_submitted = st.form_submit_button("Register")
                if reg_submitted:
                    users_df = data_manager.load_table('users')
                    if email in users_df['email'].values:
                        st.error("This email address is already registered.")
                    elif not all([email, first_name, last_name, assignment_title]):
                        st.warning("Please fill out all fields.")
                    else:
                        new_user = pd.DataFrame([{
                            "email": email, "password": "changeme", "first_name": first_name,
                            "last_name": last_name, "assignment_title": assignment_title, 
                            "role": "viewer", "status": "active"
                        }])
                        updated_users_df = pd.concat([users_df, new_user], ignore_index=True)
                        if data_manager.save_table(updated_users_df, 'users'):
                            st.success("Registration successful! Please log in using the default password 'changeme'.")
        else:
            st.warning("Could not load Project Tracker data. Registration is temporarily unavailable.")

else:
    # --- MAIN APP UI (if logged in) ---
    user_email = st.session_state.logged_in_user
    user_data = st.session_state.user_data
    
    st.sidebar.success(f"Logged in as: {user_data.get('first_name', '')} {user_data.get('last_name', '')}")
    
    # --- Notification Bell ---
    # This part requires 'get_unread_notifications' in data_manager.py
    try:
        unread_notifications = data_manager.get_unread_notifications(user_email)
        unread_count = len(unread_notifications) if unread_notifications is not None else 0
        
        # This should be the correct, numbered filename for your notifications page
        notifications_page_path = "pages/2_Notifications.py" 
        
        if unread_count > 0:
            st.sidebar.page_link(notifications_page_path, label=f"🔔 Notifications ({unread_count})")
        else:
            st.sidebar.page_link(notifications_page_path, label="🔕 Notifications")
    except AttributeError:
        st.sidebar.warning("Notification function not found in data manager.")

    
    with st.sidebar.expander("👤 Account"):
        st.write(f"**Assignment Title:** {user_data.get('assignment_title', 'N/A')}")
        new_password = st.text_input("Change Password", type="password", key="new_pw")
        if st.button("Update Password"):
            if new_password:
                users_df = data_manager.load_table('users')
                users_df.loc[users_df['email'] == user_email, 'password'] = new_password
                data_manager.save_table(users_df, 'users')
                st.success("Password updated successfully!")
            else:
                st.warning("Please enter a new password.")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.session_state.user_data = None
        st.rerun()

    st.image("und_logo.png", width=200)
    st.title("Housing & Residence Life Project Tracker")
    st.markdown("---")
    
    st.header("Welcome to the Central Hub for HRL Projects")
    st.markdown("""
    This application serves as the single source of truth for all departmental projects, tasks, and timelines, moving beyond static spreadsheets into a dynamic and collaborative environment.

    #### Key Capabilities at Your Fingertips:
    -   **Visualize Timelines:** Use the **Calendar** and interactive **Gantt Chart** to see how projects overlap and map out your year.
    -   **Track Progress in Real-Time:** The **Dashboard** provides an at-a-glance overview of key metrics, including overdue and upcoming tasks.
    -   **Collaborate Effectively:** Leave comments on tasks, receive in-app and email **Notifications**, and ensure everyone is on the same page.
    -   **Manage Data Efficiently:** Use the **Find & Filter**, **Bulk Edit**, and **Duplicate** tools to quickly manage large sets of tasks.
    -   **Generate Insights:** Create professional, printable **PDF Reports** for meetings and archival purposes.

    **To get started, please select a view from the navigation menu in the sidebar on the left.**
    """)
    
st.write("App loaded at:", datetime.now().isoformat())
