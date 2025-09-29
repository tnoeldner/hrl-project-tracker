# File: pages/12_Help.py
import streamlit as st
import re

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Help", layout="wide")
st.title("📖 HRL Project Tracker Help & Instructions")
st.markdown("---")

# --- Manual Content ---
# This script now reads the user_manual.md file and renders it using
# Streamlit's native expander components for a cleaner look.
try:
    with open('user_manual.md', 'r', encoding='utf-8') as f:
        manual_content = f.read()
    
    # Split the content into sections based on the <details> tag
    # The first part is the intro, the rest are the expandable sections
    sections = manual_content.split('<details>')
    
    # Render the intro part of the manual
    intro_content = sections[0]
    st.markdown(intro_content, unsafe_allow_html=True)

    # Loop through and render each expandable section
    for section in sections[1:]:
        # Use regex to find the title within the <summary> tag
        summary_match = re.search(r'<summary><h3>(.*?)</h3></summary>', section, re.DOTALL)
        if summary_match:
            title = summary_match.group(1)
            
            # The content is what's left after the summary tag and before the closing details tag
            content = section.split('</summary>')[1].replace('</details>', '').strip()
            
            with st.expander(title):
                # We use unsafe_allow_html=True to render the color tags for the status indicators
                st.markdown(content, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("Error: The user manual file (`user_manual.md`) could not be found.")
    st.info("Please ensure the `user_manual.md` file is in the main project folder.")

