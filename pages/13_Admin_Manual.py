# File: pages/13_Admin_Manual.py
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

st.set_page_config(page_title="Admin Manual", layout="wide")
st.title("🛠️ Administrator & Programmer's Manual")
st.info("This manual provides a technical overview of the HRL Project Tracker for maintenance and updates.")
st.markdown("---")

# --- Manual Content ---

with st.expander("1. Application Architecture"):
    st.markdown("""
    This application is built on a modern, cloud-based architecture designed for multi-user access and stability.

    -   **Frontend & Backend**: Python with the **Streamlit** library.
    -   **Data Manipulation**: **Pandas** for handling data tables.
    -   **Database**: A cloud-hosted **PostgreSQL** database provided by **Supabase**. This is the single source of truth for all data.
    -   **Version Control**: **Git**, with the code hosted on **GitHub**.
    -   **Deployment**: The live application is hosted on **Streamlit Community Cloud**.
    """)

with st.expander("2. Project File Structure"):
    st.markdown("""
    Understanding the project's file structure is key to making updates.

    -   **`Main.py`**: The main entry point of the application. It contains the login logic and the welcome page.
    -   **`pages/`**: This directory contains all the other pages of the application. Streamlit automatically turns each `.py` file in this folder into a navigation link in the sidebar, sorted by filename.
    -   **`data_manager.py`**: This is a critical custom module that acts as the **single source of truth for all database interactions**. All loading and saving of data is handled by functions in this file.
    -   **`requirements.txt`**: A list of all Python libraries required by the app. Streamlit Cloud uses this file to build the application's environment. **You must add any new libraries to this file.**
    -   **`migrate_to_db.py`**: A one-time script used to upload data from the local `Project Tracker.xlsx` and `.json` files to the cloud database.
    -   **`.streamlit/secrets.toml`**: A **local, private file** that stores your database password so you can run the app on your own computer. **This file must never be uploaded to GitHub.**
    -   **`.gitignore`**: A configuration file that tells Git to ignore certain files, such as `secrets.toml`.
    """)

with st.expander("3. How to Make and Deploy Updates (The Workflow)"):
    st.markdown("""
    This is the standard operating procedure for making a change to the app and publishing it for all users to see.

    **Step 1: Make Changes Locally**
    -   Edit the `.py` files on your local computer to add a new feature or fix a bug.

    **Step 2: Test Your Changes Locally**
    -   Before deploying, always test your changes on your own machine.
    -   Open **Git Bash**, navigate to your project folder, and run:
    """)
    st.code("python -m streamlit run Main.py", language="bash")
    st.markdown("""
    -   Thoroughly test the new feature in your web browser to ensure it works as expected.

    **Step 3: Add, Commit, and Push with Git**
    -   Once you are satisfied, push your changes to GitHub. This is what triggers Streamlit Cloud to update the live application.
    -   In your Git Bash terminal, press `Ctrl + C` to stop the local app.
    -   Run the following three commands:
    """)
    st.code("""
# 1. Add all the files you've changed
git add .

# 2. Commit the changes with a descriptive message
git commit -m "Add a short description of your changes here"

# 3. Push the changes to GitHub
git push
    """, language="bash")
    st.markdown("""
    **Step 4: Monitor Deployment on Streamlit Cloud**
    -   Go to your Streamlit Community Cloud dashboard at `share.streamlit.io`.
    -   You will see your application's status change to "Rebooting" or "Updating."
    -   The process usually takes a few minutes. Once it's done, your changes are live on your public URL.
    """)

with st.expander("4. Managing the Live Application"):
    st.markdown("""
    **Streamlit Community Cloud (`share.streamlit.io`)**
    -   **Viewing Logs:** If your live app shows an error, click the **Manage app** button in the lower-right corner of the app screen. This will open a log viewer that provides detailed error tracebacks to help you debug.
    -   **Managing Secrets:** The database connection string and email credentials are stored as "Secrets." If your database password ever changes, you must update it here:
        1.  Go to your app's settings in the Streamlit dashboard.
        2.  Navigate to the **Secrets** section.
        3.  Update the `db_connection_string` value.
    -   **Rebooting:** If the app ever becomes unresponsive, you can manually restart it by clicking the **Reboot app** option in the "Manage app" menu.

    **Supabase (Cloud Database)**
    -   **Viewing Data:** You can view and even manually edit your live data by logging into your Supabase project and using the **Table Editor**.
    -   **Backups:** Supabase automatically creates daily backups of your database, which can be restored if needed.
    """)
