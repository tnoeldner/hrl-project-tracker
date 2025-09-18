# File: pages/9_User_Settings.py
import streamlit as st

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="User Settings", layout="wide")
st.title("⚙️ User Settings")

st.write("This is the User Settings page. Content will be added here.")
