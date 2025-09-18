# File: pages/9_User_Settings.py
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

# (The rest of the file remains the same)
# ...def load_users():
    """Loads the main user data from the JSON file."""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_user_settings():
    """Loads notification settings from the JSON file."""
    try:
        with open('user_settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_settings(settings_data):
    """Saves notification settings back to the JSON file."""
    with open('user_settings.json', 'w') as f:
        json.dump(settings_data, f, indent=4)

st.set_page_config(page_title="User Settings", layout="wide")

# Check if user is logged in
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to manage your settings.")
else:
    st.title("⚙️ User Settings")
    
    user_email = st.session_state.logged_in_user
    user_role = st.session_state.user_data.get('role')
    settings = load_user_settings()
    
    # --- Current User's Settings ---
    st.subheader("My Notification Preferences")
    st.write("Select how often you would like to receive an email summary of your tasks starting in the next 7 days.")
    
    current_frequency = settings.get(user_email, {}).get('frequency', 'Never')
    frequency_options = ["Never", "Daily", "Weekly"]
    current_index = frequency_options.index(current_frequency)
    
    new_frequency = st.selectbox(
        "My Email Frequency",
        options=frequency_options,
        index=current_index,
        key="my_frequency_selector"
    )
    
    if st.button("Save My Settings"):
        if user_email not in settings:
            settings[user_email] = {}
        settings[user_email]['frequency'] = new_frequency
        save_user_settings(settings)
        st.success("Your notification settings have been saved!")
        
    st.markdown("---")

    # --- NEW: Administrator Section ---
    if user_role == 'admin':
        st.subheader("👑 Administrator Settings")
        st.write("As an admin, you can view and edit the notification settings for any user.")
        
        all_users = load_users()
        all_user_emails = sorted(list(all_users.keys()))
        
        selected_user_for_edit = st.selectbox("Select a User to Edit", options=all_user_emails)
        
        if selected_user_for_edit:
            # Get the selected user's current setting
            user_current_freq = settings.get(selected_user_for_edit, {}).get('frequency', 'Never')
            user_current_index = frequency_options.index(user_current_freq)
            
            new_user_freq = st.selectbox(
                f"Email Frequency for {selected_user_for_edit}",
                options=frequency_options,
                index=user_current_index,
                key="admin_freq_selector"
            )
            
            if st.button("Save a User's Settings"):
                if selected_user_for_edit not in settings:
                    settings[selected_user_for_edit] = {}
                settings[selected_user_for_edit]['frequency'] = new_user_freq
                save_user_settings(settings)
                st.success(f"Settings for {selected_user_for_edit} have been updated!")