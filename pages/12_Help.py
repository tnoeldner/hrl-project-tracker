# File: pages/12_Help.py
import streamlit as st

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Help", layout="wide")
st.title("ℹ️ Help & Instructions")
st.markdown("---")

st.header("Welcome to the HRL Project Tracker!")
st.write("This guide will walk you through all the features of the application, from logging in to managing your project tasks.")

with st.expander("1. Getting Started: Login & Account Management"):
    st.markdown("""
    Access to the tracker is secured through a user account system.

    **Logging In:**
    -   Enter your full Outlook email address and password, then click **Login**.

    **New User Registration:**
    1.  On the login screen, select the **Register** tab.
    2.  Fill in your information.
    3.  **Assignment Title:** This is critical. Select your name/title from the dropdown to link your account to your tasks.
    4.  Click **Register**. Your initial password will be **`changeme`**, which you should change immediately after your first login.

    **Account Management (Post-Login):**
    -   In the sidebar, click the **Account** expander to change your password.
    -   Click the **Logout** button at the bottom of the sidebar to sign out.
    """)

with st.expander("2. Module: Dashboard"):
    st.markdown("""
    The Dashboard is your "at-a-glance" view of the project landscape, filtered by the **Fiscal Year** you select at the top.

    -   **Metric Cards:** Show key numbers for the selected year: Total, Overdue, Unscheduled, and Upcoming Tasks.
    -   **Charts:** Provide visual breakdowns of tasks by Planner Bucket and Progress.
    -   **Editable Tables:** At the bottom, you can directly edit the **Progress** status for Overdue, Unscheduled, and Upcoming tasks. Click the **Save Changes** button below each table to apply your edits.
    """)

with st.expander("3. Module: Find and Filter"):
    st.markdown("""
    This page is a powerful tool for searching, viewing, and editing the entire task list.

    -   **Filters:** Use the dropdowns and search bar at the top to filter the table by Planner Bucket, Fiscal Year, or Task Name.
    -   **Editable Table:** The main table is an **editable data editor**. You can click on any cell to change its value. Columns like `PROGRESS` are dropdowns for easy status updates.
    -   **Saving:** After making changes, click the **Save Changes** button.
    """)

with st.expander("4. Module: Calendar View & Gantt Chart View"):
    st.markdown("""
    **Calendar View:**
    -   Provides a traditional monthly calendar of all tasks.
    -   **Click on any task** to open an **"Editing Task"** form below the calendar, where you can modify details and save changes.

    **Gantt Chart View:**
    -   Offers a visual project timeline.
    -   Use the filters to set your initial view.
    -   The chart is fully interactive: **zoom** with your mouse, **pan** by clicking and dragging, and **hover** over bars to see details.
    """)

with st.expander("5. Module: Bulk Edit & Duplicate"):
    st.markdown("""
    This is an efficiency tool for managing large groups of tasks.

    -   First, select a **Planner Bucket** and **Fiscal Year** to load the set of tasks you want to manage.
    -   **Tab 1: Export & Import Changes:**
        1.  Click **Download Filtered Tasks**.
        2.  Edit the downloaded Excel file offline. **Do not change the '#' column.**
        3.  Drag and drop the saved file into the **file uploader** on the app.
        4.  Click **Apply and Save Uploaded Changes**.
    -   **Tab 2: Duplicate Tasks:**
        1.  Enter the **New Fiscal Year**.
        2.  Set the **Days to shift dates forward** (default is 364 to maintain the day of the week).
        3.  Click **Duplicate Tasks** to create new copies of all filtered tasks.
    """)

st.markdown("---")
st.info("This manual was last updated on September 28, 2025.")
