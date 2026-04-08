# File: Main.py
import streamlit as st
import pandas as pd
import data_manager
from datetime import datetime

# --- PAGE CONFIGURATION (must be first Streamlit command) ---
st.set_page_config(page_title="HRL Project Tracker", layout="wide")

# --- AUTHENTICATION FUNCTIONS (using the database) ---

def check_login(username, password):
    """Checks credentials and user status against the users table."""
    users_df = data_manager.load_table('users')
    if users_df is None:
        return None, "Error loading user data."
    
    user_record = users_df[users_df['email'] == username]
    if not user_record.empty and data_manager.verify_password(password, user_record.iloc[0]['password']):
        # If login succeeded with a legacy plain-text password, upgrade to hashed
        stored = str(user_record.iloc[0]['password'])
        if ':' not in stored or len(stored) != 97:
            users_df.loc[users_df['email'] == username, 'password'] = data_manager.hash_password(password)
            data_manager.save_table(users_df, 'users')
        # Check if the user is active
        if user_record.iloc[0].get('status', 'active') == 'active':
            return user_record.iloc[0].to_dict(), "Login successful."
        else:
            return None, "This user account is inactive. Please contact an administrator."
    return None, "Incorrect email or password."

# --- LOGIN / REGISTRATION LOGIC ---
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    # --- NOT LOGGED IN: Show login/register (no sidebar navigation) ---
    st.title("HRL Project Tracker Login")
    
    tasks_df = data_manager.load_table('tasks')
    
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
                            "email": email, "password": data_manager.hash_password("changeme"), "first_name": first_name,
                            "last_name": last_name, "assignment_title": assignment_title, 
                            "role": "viewer", "status": "active"
                        }])
                        updated_users_df = pd.concat([users_df, new_user], ignore_index=True)
                        if data_manager.save_table(updated_users_df, 'users'):
                            st.success("Registration successful! Please log in using the default password 'changeme'.")
        else:
            st.warning("Could not load Project Tracker data. Registration is temporarily unavailable.")

else:
    # --- LOGGED IN: Build grouped sidebar navigation ---
    user_email = st.session_state.logged_in_user
    user_data = st.session_state.user_data
    user_role = user_data.get('role', '')

    # Notification count for badge
    unread_count = 0
    try:
        unread = data_manager.get_unread_notifications(user_email)
        unread_count = len(unread) if unread is not None else 0
    except AttributeError:
        pass

    notif_icon = "🔔" if unread_count > 0 else "🔕"
    notif_title = f"Notifications ({unread_count})" if unread_count > 0 else "Notifications"

    # --- Home page content ---
    def home_page():
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

    # --- Define navigation structure ---
    pages = {
        "": [
            st.Page(home_page, title="Home", icon="🏠", default=True),
        ],
        "Views": [
            st.Page("pages/01_Dashboard.py", title="Dashboard", icon="📊"),
            st.Page("pages/02_Notifications.py", title=notif_title, icon=notif_icon),
            st.Page("pages/03_Timeline_View.py", title="Timeline View", icon="📅"),
            st.Page("pages/04_Calendar_View.py", title="Calendar View", icon="🗓️"),
            st.Page("pages/05_Gantt_Chart_View.py", title="Gantt Chart", icon="📈"),
            st.Page("pages/07_Workload_View.py", title="Workload View", icon="👥"),
            st.Page("pages/11_Printable_Reports.py", title="Printable Reports", icon="📄"),
        ],
        "Manage Tasks": [
            st.Page("pages/08_Find_and_Filter.py", title="Find & Filter", icon="🔍"),
            st.Page("pages/09_Add_a_New_Task.py", title="Add a New Task", icon="➕"),
            st.Page("pages/10_Bulk_Edit_and_Duplicate.py", title="Bulk Edit & Duplicate", icon="⚙️"),
            st.Page("pages/06_Three_Year_Task_View.py", title="Three Year Task Manager", icon="📆"),
        ],
        "Help": [
            st.Page("pages/13_End_User_Manual.py", title="End User Manual", icon="📖"),
            st.Page("pages/16_Admin_Manual.py", title="Admin Manual", icon="📋"),
            st.Page("pages/14_About.py", title="About", icon="ℹ️"),
        ],
    }

    if user_role == 'admin':
        pages["Admin"] = [
            st.Page("pages/15_Admin_Dashboard.py", title="Admin Dashboard", icon="🛡️"),
            st.Page("pages/12_User_Settings.py", title="User Settings", icon="🔧"),
            st.Page("pages/17_Admin_Presets_Overview.py", title="Presets Overview", icon="📊"),
        ]

    pg = st.navigation(pages)

    # --- Sidebar extras ---
    st.sidebar.success(f"Logged in as: {user_data.get('first_name', '')} {user_data.get('last_name', '')}")

    with st.sidebar.expander("👤 Account"):
        st.write(f"**Assignment Title:** {user_data.get('assignment_title', 'N/A')}")
        new_password = st.text_input("Change Password", type="password", key="new_pw")
        if st.button("Update Password"):
            if new_password:
                users_df = data_manager.load_table('users')
                users_df.loc[users_df['email'] == user_email, 'password'] = data_manager.hash_password(new_password)
                data_manager.save_table(users_df, 'users')
                st.success("Password updated successfully!")
            else:
                st.warning("Please enter a new password.")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.session_state.user_data = None
        st.rerun()

    # --- Run the selected page ---
    pg.run()
