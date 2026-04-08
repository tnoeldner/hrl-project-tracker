# File: 13_Admin_Manual.py
import streamlit as st

# --- AUTHENTICATION CHECK ---
# Ensure user is logged in
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()

# Ensure user is an administrator
user_role = st.session_state.user_data.get('role')
if user_role != 'admin':
    st.error("You do not have permission to view this page. This page is for administrators only.")
    st.stop()
# --------------------------

# --- PAGE UI ---
st.set_page_config(page_title="Admin Manual", layout="wide")
st.title("🛠️ Administrator & Programmer's Manual")
st.info("This manual provides a technical overview of the HRL Project Tracker for maintenance and updates.")
st.markdown("---")

# --- MANUAL CONTENT ---
manual_sections = {
    "1. Application Architecture": """
    This application is built on a modern, cloud-based architecture designed for multi-user access and stability.

    -   **Frontend & Backend**: Python with the **Streamlit** library.
    -   **Data Manipulation**: **Pandas** for handling data tables.
    -   **Database**: A cloud-hosted **PostgreSQL** database provided by **Supabase**. This is the single source of truth for all data.
    -   **Version Control**: **Git**, with the code hosted on **GitHub**.
    -   **Deployment**: The live application is hosted on **Streamlit Community Cloud**.
    """,
    "2. Project File Structure": """
    Understanding the project's file structure is key to making updates.

    -   **`Main.py`**: The main entry point of the application. It contains the login logic and the welcome page.
    -   **`pages/`**: This directory contains all the other pages of the application.
    -   **`data_manager.py`**: This is a critical custom module that acts as the **single source of truth for all database interactions**.
    -   **`requirements.txt`**: A list of all Python libraries required by the app.
    -   **`migrate_to_db.py`**: A local script used to upload data from local files to the cloud database.
    -   **`.streamlit/secrets.toml`**: A **local, private file** that stores your database password for local testing. **This file must never be uploaded to GitHub.**
    -   **`.gitignore`**: A configuration file that tells Git to ignore certain files, such as `secrets.toml`.
    """,
    "3. How to Make and Deploy Updates (The Workflow)": """
    This is the standard operating procedure for making a change to the app and publishing it for all users to see.

    #### **Step 1: Test Your Changes Locally**
    -   Before deploying, always test your changes on your own machine.
    -   Open **Git Bash**, navigate to your project folder, and run:
        ```bash
        python -m streamlit run Main.py
        ```
    -   Thoroughly test the new feature in your web browser to ensure it works as expected.

    #### **Step 2: Add, Commit, and Push with Git**
    -   Once you are satisfied, push your changes to GitHub. This is what triggers Streamlit Cloud to update the live application.
    -   In your Git Bash terminal, press `Ctrl + C` to stop the local app.
    -   Run the following three commands:
        ```bash
        # 1. Add all the files you've changed
        git add .

        # 2. Commit the changes with a descriptive message
        git commit -m "Your commit message"

        # 3. Push the changes to GitHub
        git push
        ```

    #### **Step 3: Monitor Deployment on Streamlit Cloud**
    -   Go to your Streamlit Community Cloud dashboard at `share.streamlit.io`.
    -   You will see your application's status change to "Rebooting" or "Updating."
    -   The process usually takes a few minutes. Once it's done, your changes are live on your public URL.
    """,
    "4. Managing the Live Application": """
    #### **Streamlit Community Cloud (`share.streamlit.io`)**
    -   **Viewing Logs:** If your live app shows an error, click the **Manage app** button in the lower-right corner of the app screen. This will open a log viewer that provides detailed error tracebacks to help you debug.
    -   **Managing Secrets:** The database connection string and email credentials are stored as "Secrets." If your database password ever changes, you must update it in your app's settings.
    -   **Rebooting:** If the app ever becomes unresponsive or isn't showing the latest data, you can force a complete refresh. In the "Manage app" menu, click the three dots (...) and select **Reboot app**.

    #### **Supabase (Cloud Database)**
    -   **Viewing Data:** You can view and even manually edit your live data by logging into your Supabase project and using the **Table Editor**.
    -   **Backups:** Supabase automatically creates daily backups of your database.
    """
}

# --- Display the manual on the page using expanders ---
for title, content in manual_sections.items():
    with st.expander(title, expanded=(title.startswith("1."))):
        st.markdown(content, unsafe_allow_html=True)