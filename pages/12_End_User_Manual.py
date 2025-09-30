# File: pages/12_Help.py
import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

# --- PDF GENERATION FUNCTION ---
def create_help_pdf(sections):
    """Generates a PDF version of the user manual from the section data."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PDF Header ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "HRL Project Tracker - User Manual", ln=True, align='C')
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)

    # --- PDF Body ---
    for title, content in sections.items():
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, title, ln=True, border='B')
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 11)
        # Clean up markdown for the PDF
        content = content.replace("`", "'").replace("**", "").replace("####", "- ").replace("*", "  -")
        content = content.replace("<span style='color:blue;'>", "").replace("<span style='color:red;'>", "").replace("<span style='color:orange;'>", "").replace("<span style='color:green;'>", "").replace("</span>", "")
        pdf.multi_cell(0, 7, content)
        pdf.ln(5)

    return bytes(pdf.output())

# --- PAGE UI ---
st.set_page_config(page_title="Help", layout="wide")
st.title("📖 HRL Project Tracker Help & Instructions")

# --- MANUAL CONTENT ---
# The content is now stored directly in the script for reliability
manual_sections = {
    "1. Introduction": """
    Welcome to the Housing & Residence Life (HRL) Project Tracker! This application is a powerful, centralized tool designed to replace the traditional Excel workbook for tracking departmental projects, events, and tasks. It provides a fast, interactive, and multi-user environment for managing project timelines, updating progress, and generating insightful reports.

    This manual will guide you through every feature of the application, from your first login to advanced bulk editing and reporting.
    """,
    "2. Getting Started: Login & Account Management": """
    Access to the tracker is secured through a user account system.

    #### **2.1. Logging In**
    * **For Existing Users:**
      1. Enter your full Outlook email address in the **Username** field.
      2. Enter your password in the **Password** field.
      3. Click **Login**.

    #### **2.2. New User Registration**
    If you are a new user, you must register for an account.
    1. On the login screen, select the **Register** tab.
    2. Fill in your information:
       * **Outlook Email Address:** Your official university email.
       * **First Name & Last Name:** Your full name.
       * **Assignment Title:** This is a critical step. Click the dropdown menu and select your name/title as it appears in the project tracker data. This directly links your account to the tasks assigned to you.
    3. Click **Register**.
    4. Your account is now created with a default password: **`changeme`**. You should log in immediately and change this password.

    #### **2.3. Account Management (Post-Login)**
    Once logged in, you can manage your account from the sidebar on the left.
    * **Changing Your Password:** In the sidebar, click the **Account** expander, enter a new password, and click **Update Password**.
    * **Logging Out:** Click the **Logout** button at the bottom of the sidebar.
    """,
    "3. Dashboard": """
    The Dashboard is your "at-a-glance" view of the entire project landscape. It is fully interactive and filters all its data based on the **Fiscal Year** you select at the top.
    * **Global Controls**: At the top, you can select a **Fiscal Year** and set the number of **Days to look forward** for the "Upcoming Tasks" metric.
    * **Metric Cards**: These cards show key numbers for the selected fiscal year: Total Tasks, Overdue Tasks, Unscheduled Tasks, and Upcoming Tasks.
    * **Charts**: Visual breakdowns of tasks by **Planner Bucket** and by **Progress** for the selected year.
    * **Editable Tables**: The bottom half of the dashboard contains tables for tasks that need immediate attention. You can directly edit the **Progress** status and other fields in these tables and click the **Save...Changes** button below each table.
    """,
    "4. Timeline View": """
    This page gives you a quick look at what's starting soon and what started recently.
    * **Controls**: Use the number input at the top to set how many days forward and back you want to view.
    * **Visual Indicators**: Each task in the timeline provides several at-a-glance details in its title:
      * **Icon**: An emoji representing the task's **Planner Bucket**.
      * <span style='color:blue;'>**Date**</span>: The start date and day of the week are highlighted in blue.
      * **Progress Status**: The current status is color-coded for quick reference: <span style='color:red;'>NOT STARTED</span>, <span style='color:orange;'>IN PROGRESS</span>, <span style='color:green;'>COMPLETE</span>.
    * **Expanders**: Click on any task summary to expand it and see full details, including the Planner Bucket and Audience.
    """,
    "5. Find and Filter": """
    This page is a powerful tool for searching, viewing, and editing the entire task list.
    * **Filters**: Use the dropdown menus at the top to filter the table by **Planner Bucket** and/or **Fiscal Year**. A search bar also allows you to find tasks by name.
    * **Editable Table**: The main table is an **editable data editor**. You can click on any cell to change its value. The **Progress** and other fields are dropdowns for easy status updates.
    * **Saving**: After making your changes, click the **Save Changes** button at the bottom.
    """,
    "6. Calendar View": """
    This page provides a full monthly calendar of all tasks.
    * **Navigation**: Use the arrows at the top of the calendar to move between months.
    * **Click to Edit**: Click on any task in the calendar. An **"Editing Task"** form will appear below the calendar, pre-filled with that task's details. You can make changes and click **Save Changes** to update the task or **Cancel** to close the form.
    """,
    "7. Bulk Edit & Duplicate": """
    This is an efficiency tool for managing large groups of tasks.
    * **Filtering**: First, select a **Planner Bucket** and **Fiscal Year** to load the set of tasks you want to manage.
    * The page is divided into two tabs:
        * **Tab 1: Quick Edit & Delete:** A table where you can directly edit task details or select multiple tasks for deletion.
        * **Tab 2: Export & Import Changes:** This workflow is for making numerous edits offline. Download the filtered tasks, edit the file, and upload it to apply the changes. **Do not change the '#' column**.
    * **Duplication**: A section at the bottom allows you to roll tasks over to a new year.
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
    with st.expander(title):
        st.markdown(content, unsafe_allow_html=True)

