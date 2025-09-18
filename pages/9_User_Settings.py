# File: pages/9_User_Settings.py
import streamlit as st
import json

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

# --- FUNCTIONS ---
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

# --- PAGE UI ---
st.set_page_config(page_title="User Settings", layout="wide")
st.title("⚙️ User Settings")

user_email = st.session_state.logged_in_user
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