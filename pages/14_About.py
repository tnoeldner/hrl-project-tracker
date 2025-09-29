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

# --- GITHUB API FUNCTIONS ---
@st.cache_data(ttl=3600) # Cache the result for 1 hour
def get_api_data(endpoint):
    """Generic function to fetch data from the GitHub API."""
    REPO_OWNER = "tnoeldner"
    REPO_NAME = "hrl-project-tracker"
    TOKEN = st.secrets.get("GITHUB_TOKEN")
    
    if not TOKEN:
        return None, "GitHub token not found. Please configure it in your Streamlit secrets."

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/{endpoint}"
    headers = {"Authorization": f"token {TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"Error fetching from GitHub: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

def get_latest_release():
    """Fetches the latest release information from GitHub."""
    data, error = get_api_data("releases/latest")
    if error:
        return "N/A", "N/A", error
    
    if not data: # Handles case where there are no releases
        return "No releases found", "N/A", "Please create a release on GitHub to see version info."
    
    version = data.get("tag_name", "N/A")
    last_updated = pd.to_datetime(data.get("published_at")).strftime('%Y-%m-%d')
    release_notes = data.get("body", "No release notes provided for this version.")
    
    return version, last_updated, release_notes

def get_commit_history():
    """Fetches the last 5 commit messages from the GitHub repository."""
    data, error = get_api_data("commits?per_page=5")
    if error:
        return [error]
        
    history = []
    for commit in data:
        message = commit['commit']['message']
        author = commit['commit']['author']['name']
        date = pd.to_datetime(commit['commit']['author']['date']).strftime('%Y-%m-%d %H:%M')
        history.append(f"**{date}** - {message} *(by {author})*")
    return history

# --- PAGE UI ---
st.set_page_config(page_title="About", layout="wide")
st.title("ℹ️ About This Application")
st.markdown("---")

st.header("Application Details")

# Get version info from GitHub Releases
version, last_updated, release_notes = get_latest_release()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Created By")
    st.write("This application was designed and developed by Troy Noeldner in collaboration with Google.")
with col2:
    st.subheader("Version Information")
    st.write(f"**Current Version:** {version}")
    st.write(f"**Last Updated:** {last_updated}")

# Display release notes if they exist
if release_notes:
    st.subheader("Release Notes")
    st.markdown(release_notes)

st.markdown("---")

# --- RECENT UPDATES SECTION ---
st.header("Recent Code Changes")
st.info("This section shows the last 5 code commits pushed to the repository.")

commit_history = get_commit_history()
for entry in commit_history:
    st.markdown(f"- {entry}")

st.markdown("---")
st.write("This tool was created to modernize the project tracking process for the Housing & Residence Life department.")

