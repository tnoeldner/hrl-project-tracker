# File: Main.py
import streamlit as st
import pandas as pd
import data_manager

def check_login(username, password, users_df):
    """Checks credentials against the users DataFrame."""
    user_record = users_df[users_df['email'] == username]
    if not user_record.empty and user_record.iloc[0]['password'] == password:
        return user_record.iloc[0].to_dict()
    return None

st.set_page_config(page_title="HRL Project Tracker", layout="wide")

# Load project data for the registration dropdown
tasks_df = data_manager.load_table('tasks')

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
                users_df = data_manager.load_table('users')
                if users_df is not None:
                    user_data = check_login(username, password, users_df)
                    if user_data:
                        st.session_state.logged_in_user = username
                        st.session_state.user_data = user_data
                        st.rerun()
                    else:
                        st.error("Incorrect email or password")
    
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
                            "last_name": last_name, "assignment_title": assignment_title, "role": "viewer"
                        }])
                        updated_users_df = pd.concat([users_df, new_user], ignore_index=True)
                        if data_manager.save_table(updated_users_df, 'users'):
                            st.success("Registration successful! Please log in using the default password 'changeme'.")
        else:
            st.warning("Could not load Project Tracker data. Registration is temporarily unavailable.")

else:
    user_data = st.session_state.user_data
    st.sidebar.success(f"Logged in as: {user_data['first_name']} {user_data['last_name']}")
    
    with st.sidebar.expander("👤 Account"):
        st.write(f"**Assignment Title:** {user_data['assignment_title']}")
        new_password = st.text_input("Change Password", type="password", key="new_pw")
        if st.button("Update Password"):
            if new_password:
                users_df = data_manager.load_table('users')
                users_df.loc[users_df['email'] == st.session_state.logged_in_user, 'password'] = new_password
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
    st.markdown("Use the navigation menu in the sidebar to select a view.")