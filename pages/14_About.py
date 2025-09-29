# File: pages/14_About.py
import streamlit as st
from datetime import datetime

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="About", layout="wide")
st.title("ℹ️ About This Application")
st.markdown("---")

st.header("Application Details")

# Create two columns for a clean layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Created By")
    st.write("This application was designed and developed by Troy Noeldner in collaboration with Google.")

with col2:
    st.subheader("Version Information")
    st.write(f"**Current Version:** 1.0.0")
    # This will show the date of the last update
    st.write(f"**Last Updated:** September 28, 2025")

st.markdown("---")
st.write("This tool was created to modernize the project tracking process for the Housing & Residence Life department, moving from a traditional spreadsheet to a dynamic, multi-user web application.")
