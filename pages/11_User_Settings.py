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
st.title("⚙️ My Settings")

# --- Load Data ---
user_email = st.session_state.logged_in_user
settings_df = data_manager.load_table('settings')
if settings_df is None:
    settings_df = pd.DataFrame(columns=['email', 'frequency'])

# --- Current User's Notification Preferences ---
st.subheader("My Notification Preferences")
st.write("Select how often you would like to receive an email summary of your tasks starting in the next 7 days.")

# Get the current user's setting, or default to 'Never'
current_frequency = settings_df[settings_df['email'] == user_email]['frequency'].values[0] if user_email in settings_df['email'].values else 'Never'
frequency_options = ["Never", "Daily", "Weekly"]

# Find the index of the current setting to set the default in the selectbox
try:
    current_index = frequency_options.index(current_frequency)
except ValueError:
    current_index = 0 # Default to 'Never' if the value is somehow invalid

new_frequency = st.selectbox(
    "My Email Frequency",
    options=frequency_options,
    index=current_index
)

if st.button("Save My Settings"):
    settings_df_updated = settings_df.copy()
    
    # Check if the user already has a setting entry
    if user_email not in settings_df_updated['email'].values:
        # If not, create a new entry
        new_setting = pd.DataFrame([{'email': user_email, 'frequency': new_frequency}])
        settings_df_updated = pd.concat([settings_df_updated, new_setting], ignore_index=True)
    else:
        # If they do, update the existing entry
        settings_df_updated.loc[settings_df_updated['email'] == user_email, 'frequency'] = new_frequency
    
    if data_manager.save_table(settings_df_updated, 'settings'):
        st.success("Your notification settings have been saved!")
        st.rerun()