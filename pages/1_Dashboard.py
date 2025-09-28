# File: pages/1_Dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import data_manager
from fpdf import FPDF

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

# (The rest of the file remains the same)
# ...
def create_pdf_report(metrics, overdue_df, unscheduled_df):
    """Generates a PDF report from the dashboard data."""
    pdf = FPDF()
    pdf.add_page()
    
    # --- 1. EDIT THE TITLE ---
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Your Custom Report Title Here", ln=True, align='C')
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Report Generated on: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    # --------------------------

    # --- 2. EDIT THE METRICS ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Key Metrics Summary", ln=True)
    pdf.set_font("Helvetica", "", 12)
    # You can customize which metrics are included by editing the 'metrics_data'
    # dictionary before this function is called.
    for key, value in metrics.items():
        pdf.cell(0, 8, f"- {key}: {value}", ln=True)
    pdf.ln(10)
    # --------------------------

    # --- 3. EDIT THE OVERDUE TASKS TABLE ---
    if not overdue_df.empty:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Overdue Tasks", ln=True)
        
        # To change columns: update the headers and the 'row' accessors below
        pdf.set_font("Helvetica", "B", 10)
        headers = ["Task", "Fiscal Year", "End Date", "Progress"]
        col_widths = [80, 25, 35, 35]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for index, row in overdue_df.iterrows():
            # Make sure these row['...'] match your headers
            pdf.cell(col_widths[0], 10, row['TASK'], border=1)
            pdf.cell(col_widths[1], 10, str(row['Fiscal Year']), border=1)
            pdf.cell(col_widths[2], 10, row['END'].strftime('%Y-%m-%d'), border=1)
            pdf.cell(col_widths[3], 10, row['PROGRESS'], border=1)
            pdf.ln()
        pdf.ln(10)
    # ------------------------------------
    
    # --- 4. EXAMPLE: ADD A NEW TABLE ---
    # To add the 'Unscheduled Tasks' table, you can copy the block above
    # and change the variables from overdue_df to unscheduled_df.
    if not unscheduled_df.empty:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Unscheduled Tasks", ln=True)
        # ... (add table header and row logic here) ...
    # ------------------------------------

    return bytes(pdf.output())


st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Dashboard Report")
df = data_manager.load_table('tasks')

if df is not None:
    # --- GLOBAL CONTROLS ---
    col1, col2 = st.columns(2)
    with col1:
        year_options = ['All'] + sorted(df['Fiscal Year'].unique().tolist())
        st.selectbox("Select Fiscal Year for Dashboard View", options=year_options, key="dashboard_year_filter")
    with col2:
        st.number_input("Days to look forward for 'Upcoming Tasks':", min_value=1, value=30, key="days_forward")

    # --- DATA FILTERING ---
    display_df = df if st.session_state.dashboard_year_filter == 'All' else df[df['Fiscal Year'] == st.session_state.dashboard_year_filter]
    today = pd.to_datetime("today").normalize()
    future_date = today + pd.Timedelta(days=st.session_state.days_forward)
    
    overdue_df = display_df[(display_df['END'] < today) & (display_df['PROGRESS'] != 'COMPLETE') & (display_df['END'].dt.year > 1901)].copy()
    unscheduled_df = display_df[display_df['END'].dt.year <= 1901].copy()
    upcoming_tasks = display_df[(display_df['START'] >= today) & (display_df['START'] <= future_date)]

    # --- METRICS ---
    metrics_data = {
        f"Total Tasks (FY {st.session_state.dashboard_year_filter})": len(display_df),
        "Overdue Tasks": len(overdue_df),
        "Unscheduled Tasks": len(unscheduled_df),
        f"Upcoming Tasks (Next {st.session_state.days_forward} Days)": len(upcoming_tasks)
    }

    # --- PDF DOWNLOAD BUTTON ---
    pdf_data = create_pdf_report(metrics_data, overdue_df, unscheduled_df)
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_data,
        file_name=f"HRL_Project_Report_{datetime.now().strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf"
    )
    st.markdown("---")

    # --- METRICS DISPLAY ---
    cols = st.columns(len(metrics_data))
    for i, (key, value) in enumerate(metrics_data.items()):
        cols[i].metric(key, value)

    st.markdown("---")
    
    # --- CHARTS & TABLES ---
    # ... (The rest of the dashboard UI remains the same)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Tasks by Planner Bucket (FY {st.session_state.dashboard_year_filter})")
        st.dataframe(display_df['PLANNER BUCKET'].value_counts())
    with col2:
        st.subheader(f"Tasks by Progress (FY {st.session_state.dashboard_year_filter})")
        progress_counts = display_df['PROGRESS'].value_counts()
        if not progress_counts.empty:
            fig, ax = plt.subplots()
            ax.pie(progress_counts, labels=progress_counts.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.info("No tasks to display in the progress chart.")
            
    # (Editable tables for Overdue and Unscheduled tasks remain the same)

else:
    st.warning("Could not load data. Please check 'Project Tracker.xlsx'.")