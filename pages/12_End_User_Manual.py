# File: End_User_Manual.py
import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

def create_help_pdf(sections):
    """Generates a PDF version of the user manual from the section data."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PDF Header ---
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "HRL Project Tracker - User Manual", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)

    # --- PDF Body ---
    for title, content in sections.items():
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, title, ln=True, border='B')
        pdf.ln(4)
        pdf.set_font("Arial", "", 11)
        # Clean up markdown and emojis for the PDF
        content = content.replace("`", "'").replace("**", "").replace("####", "- ").replace("*", "  -")
        content = content.replace("<span style='color:blue;'>", "").replace("</span>", "")
        # Remove emojis as they are not supported by the default font
        content = content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, content)
        pdf.ln(5)

    return bytes(pdf.output())

# --- PAGE UI ---
st.set_page_config(page_title="End User Manual", layout="wide")
st.title("📖 HRL Project Tracker End User Manual")

# --- MANUAL CONTENT ---
manual_sections = {
    "1. Introduction": """
    Welcome to the Housing & Residence Life (HRL) Project Tracker! This application is a powerful, centralized tool for tracking departmental projects, events, and tasks. It provides a fast, interactive, and multi-user environment for managing project timelines, updating progress, collaborating with comments, and generating insightful reports.
    """,
    "2. Getting Started: Login & Account Management": """
    Access to the tracker is secured through a user account system.

    #### **2.1. Logging In**
    * **For Existing Users:**
      1. Enter your full Outlook email address in the **Username** field.
      2. Enter your password in the **Password** field.
      3. Click **Login**.

    #### **2.2. New User Registration**
    1. On the login screen, select the **Register** tab.
    2. Fill in your information, selecting your name from the **Assignment Title** dropdown menu. This links your account to tasks assigned to you.
    3. Click **Register**. Your initial password will be **`changeme`**. You should change it immediately after your first login.

    #### **2.3. Account Management (Post-Login)**
    Once logged in, you can manage your account from the sidebar on the left.
    * **Changing Your Password:** In the sidebar, click the **Account** expander, enter a new password, and click **Update Password**.
    * **Notifications:** Manage your email notification preferences on the **User Settings** page.
    * **Logging Out:** Click the **Logout** button at the bottom of the sidebar.
    """,
    "3. Notifications & Commenting": """
    The application includes a built-in system for collaboration.

    #### **3.1. The Notification Bell**
    * Located in the sidebar, the bell icon (🔔) will show a count of your unread notifications. Click on it to go to the **Notifications** page.

    #### **3.2. Commenting on a Task**
    1. Navigate to the **Find and Filter** page.
    2. Find the task you wish to comment on and check its **Details** box.
    3. A "Comments" section will appear below the table. Here you can view existing comments and post new ones.
    4. When you post a comment, the user assigned to the task is automatically notified (both in-app and via email). You can also use the **"Additionally notify"** box to tag other users who should receive a notification.

    #### **3.3. The Notifications Page**
    * This page displays a list of your unread notifications. Each notification shows the comment and the task it's related to.
    * Click the **"View Task & Add Comment"** button to jump directly to that task's detail view on the "Find and Filter" page, where you can reply.
    * Click **"Mark All as Read"** to clear your unread notifications.
    """,
    "4. Dashboard": """
    The Dashboard is your "at-a-glance" view of the project landscape, filtered by the **Fiscal Year** you select at the top.
    * **Metric Cards**: Show key numbers for the selected year: Total Tasks, Overdue Tasks, Unscheduled Tasks, and Upcoming Tasks.
    * **Charts**: Visual breakdowns of tasks by **Planner Bucket** and by **Progress**.
    * **Editable Tables**: The bottom half of the dashboard contains tables for tasks that need immediate attention. You can directly edit the **Progress** status and other fields and click the **Save...Changes** button below each table.
    """,
    "5. Timeline View": """
    This page gives a quick look at near-term tasks.
    * **Visual Indicators**: Each task in the timeline provides several at-a-glance details in its title:
      * **Icon**: An emoji representing the task's **Planner Bucket**.
      * <span style='color:blue;'>**Date**</span>: The start date and day of the week are highlighted in blue.
      * **Progress Status**: The current status is color-coded for quick reference.
    * **Expanders**: Click on any task summary to expand it and see full details.
    """,
    "6. Find and Filter": """
    This is a powerful tool for searching, viewing, and editing the entire task list.
    * **Filters**: Use the dropdown menus and search bar to find specific tasks.
    * **Editable Table**: The main table is an **editable data editor**. You can click on any cell to change its value. The **Progress** and other fields are dropdown menus.
    * **Saving**: After making changes, click the **Save Edits** or **Delete Selected Tasks** buttons.
    """,
    "7. Admin Dashboard (Administrators Only)": """
    This is the central control panel for managing the application.
    * **Manage Planner Buckets**: Add new buckets, edit names, and assign icons. Renaming a bucket here automatically updates all associated tasks.
    * **Manage User Settings**: View all registered users, reset their passwords, change their assignment titles, and set their email notification frequency. You can also inactivate or permanently delete user accounts.
    * **Manage Assignment Titles**: Add, rename, or safely delete the "Assignment Titles" that appear in dropdown menus across the app.
    * **View Changelog**: A filterable, searchable log of every data change made in the application.
    """
}

# --- PDF Download Button ---
pdf_data = create_help_pdf(manual_sections)
st.download_button(
    label="📄 Download PDF Manual",
    data=pdf_data,
    file_name="HRL_Project_Tracker_User_Manual.pdf",
    mime="application/pdf"
)
st.markdown("---")

# --- Display the manual on the page using expanders ---
for title, content in manual_sections.items():
    with st.expander(title, expanded=(title.startswith("1."))):
        st.markdown(content, unsafe_allow_html=True)
