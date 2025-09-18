# File: Main.py
import streamlit as st
import json
import data_manager # Import the central data manager

# --- USER MANAGEMENT FUNCTIONS ---
def load_users():
    """Loads the users from the JSON file."""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users_data):
    """Saves the users dictionary back to the JSON file."""
    with open('users.json', 'w') as f:
        json.dump(users_data, f, indent=4)

def check_login(username, password, users):
    """Checks if the username and password are valid."""
    if username in users and users[username]['password'] == password:
        return users[username]
    return None

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="HRL Project Tracker", layout="wide")

# Load the main project data to populate the dropdown
df = data_manager.load_data()

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
                users = load_users()
                user_data = check_login(username, password, users)
                if user_data:
                    st.session_state.logged_in_user = username
                    st.session_state.user_data = user_data
                    st.rerun()
                else:
                    st.error("Incorrect email or password")
    
    with register_tab:
        if df is not None:
            st.write("New users can register here. Select your name from the Assignment Title dropdown.")
            with st.form("register_form", clear_on_submit=True):
                email = st.text_input("Outlook Email Address")
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                
                # UPDATED: Changed from text_input to selectbox
                # Convert all items to string to handle mixed data types, then sort
                assignment_options = sorted([str(item) for item in df['ASSIGNMENT TITLE'].unique()])
                assignment_title = st.selectbox("Assignment Title", options=assignment_options)
                
                reg_submitted = st.form_submit_button("Register")
                if reg_submitted:
                    users = load_users()
                    if email in users:
                        st.error("This email address is already registered.")
                    elif not all([email, first_name, last_name, assignment_title]):
                        st.warning("Please fill out all fields.")
                    else:
                        users[email] = {
                            "password": "changeme", # Default password
                            "first_name": first_name,
                            "last_name": last_name,
                            "assignment_title": assignment_title
                        }
                        save_users(users)
                        st.success("Registration successful! Please log in using the default password 'changeme'.")
        else:
            st.warning("Could not load Project Tracker data. Registration is temporarily unavailable.")

else:
    # --- MAIN APP UI (if logged in) ---
    user_email = st.session_state.logged_in_user
    user_data = st.session_state.user_data
    
    st.sidebar.success(f"Logged in as: {user_data['first_name']} {user_data['last_name']}")
    
    with st.sidebar.expander("👤 Account"):
        st.write(f"**Assignment Title:** {user_data['assignment_title']}")
        new_password = st.text_input("Change Password", type="password", key="new_pw")
        if st.button("Update Password"):
            if new_password:
                users = load_users()
                users[user_email]['password'] = new_password
                save_users(users)
                st.success("Password updated successfully!")
            else:
                st.warning("Please enter a new password.")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.session_state.user_data = None
        st.rerun()

    # Main welcome page content
    st.image("und_logo.png", width=200)
    st.title("Housing & Residence Life Project Tracker")
    st.markdown("Use the navigation menu in the sidebar to select a view.")