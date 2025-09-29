# File: pages/14_About.py
import streamlit as st
from datetime import datetime
import requests
import pandas as pd

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

# --- GITHUB API FUNCTION ---
@st.cache_data(ttl=3600) # Cache the result for 1 hour to avoid making too many API calls
def get_commit_history():
    """Fetches the last 5 commit messages from the GitHub repository."""
    # These should match your GitHub username and repository name
    REPO_OWNER = "tnoeldner"
    REPO_NAME = "hrl-project-tracker"
    
    # Safely get the token from Streamlit's secrets management
    TOKEN = st.secrets.get("GITHUB_TOKEN")
    
    # Check if the token was found
    if not TOKEN:
        return ["GitHub token not found. Please configure it in your Streamlit secrets."]

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    headers = {"Authorization": f"token {TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers, params={"per_page": 5})
        response.raise_for_status() # Will raise an error for bad responses (4xx or 5xx)
        commits = response.json()
        
        history = []
        for commit in commits:
            message = commit['commit']['message']
            author = commit['commit']['author']['name']
            # Use pandas for robust date parsing and formatting
            date = pd.to_datetime(commit['commit']['author']['date']).strftime('%Y-%m-%d %H:%M')
            history.append(f"**{date}** - {message} *(by {author})*")
        return history
    except requests.exceptions.RequestException as e:
        return [f"Error fetching commit history: {e}"]
    except Exception as e:
        return [f"An unexpected error occurred: {e}"]

# --- Function to read version.txt ---
def get_version_info():
    try:
        with open('version.txt', 'r') as f:
            lines = f.readlines()
            version = lines[0].split(':')[1].strip()
            last_updated = lines[1].split(':')[1].strip()
            return version, last_updated
    except (FileNotFoundError, IndexError):
        return "1.0.0", "N/A"

# --- PAGE UI ---
st.set_page_config(page_title="About", layout="wide")
st.title("ℹ️ About This Application")
st.markdown("---")

st.header("Application Details")

version, last_updated = get_version_info()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Created By")
    st.write("This application was designed and developed by Troy Noeldner in collaboration with Google.")
with col2:
    st.subheader("Version Information")
    st.write(f"**Current Version:** {version}")
    st.write(f"**Last Updated:** {last_updated}")

st.markdown("---")

# --- RECENT UPDATES SECTION ---
st.header("Recent Updates (from GitHub)")
st.info("This section shows the last 5 changes made to the application's source code.")

commit_history = get_commit_history()
for entry in commit_history:
    st.markdown(f"- {entry}")

st.markdown("---")
st.write("This tool was created to modernize the project tracking process for the Housing & Residence Life department.")

