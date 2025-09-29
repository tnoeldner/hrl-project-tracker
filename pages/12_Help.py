# File: pages/12_Help.py
import streamlit as st

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Help", layout="wide")
st.title("📖 HRL Project Tracker Help & Instructions")
st.markdown("---")

# --- Manual Content ---
# The content is read from the user_manual.md file you provided.
# This ensures that any future updates to the markdown file are automatically reflected here.
try:
    with open('user_manual.md', 'r', encoding='utf-8') as f:
        manual_content = f.read()
    
    # We use unsafe_allow_html=True to render the color tags for the status indicators.
    st.markdown(manual_content, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("Error: The user manual file (`user_manual.md`) could not be found.")
    st.info("Please ensure the `user_manual.md` file is in the main project folder.")


