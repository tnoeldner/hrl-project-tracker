# File: pages/8_Printable_Reports.py
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
# --- PDF Generation Functions ---

def create_summary_report(df):
    """Creates a high-level summary PDF with overdue tasks."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Project Summary Report", ln=True, align='C')
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)

    today = pd.to_datetime("today").normalize()
    overdue_df = df[(df['END'] < today) & (df['PROGRESS'] != 'COMPLETE') & (df['END'].dt.year > 1901)]
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Overdue Tasks ({len(overdue_df)} total)", ln=True)
    
    if not overdue_df.empty:
        # Prepare data for the table
        table_data = [["Task", "Planner Bucket", "End Date", "Progress"]] # Headers
        for _, row in overdue_df.iterrows():
            table_data.append([
                str(row['TASK']),
                str(row['PLANNER BUCKET']),
                row['END'].strftime('%Y-%m-%d'),
                str(row['PROGRESS'])
            ])
        
        # Create the table
        pdf.set_font("Helvetica", "", 9)
        with pdf.table(col_widths=(80, 40, 30, 35), text_align="LEFT", borders_layout="ALL") as table:
            for data_row in table_data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)
    else:
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "No overdue tasks found.", ln=True)

    return bytes(pdf.output())

def create_full_list_report(df):
    """Creates a PDF with a complete list of all tasks."""
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Full Project Task List", ln=True, align='C')
    pdf.ln(5)

    # Prepare data for the table
    table_data = [["ID", "Task", "Bucket", "Semester", "FY", "Audience", "Start", "End", "Progress"]]
    for _, row in df.iterrows():
        table_data.append([
            str(row['#']), str(row['TASK']), str(row['PLANNER BUCKET']),
            str(row['SEMESTER']), str(row['Fiscal Year']), str(row['AUDIENCE']),
            row['START'].strftime('%Y-%m-%d'), row['END'].strftime('%Y-%m-%d'), str(row['PROGRESS'])
        ])

    pdf.set_font("Helvetica", "", 7)
    with pdf.table(col_widths=(10, 70, 30, 30, 15, 30, 25, 25, 30), text_align="LEFT", borders_layout="ALL") as table:
        for data_row in table_data:
            row = table.row()
            for datum in data_row:
                row.cell(datum)

    return bytes(pdf.output())

def create_bucket_report(df, selected_bucket, selected_year):
    """Creates a PDF listing all tasks for a specific Planner Bucket and Fiscal Year."""
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Report for {selected_bucket} - FY {selected_year}", ln=True, align='C')
    pdf.ln(10)

    bucket_df = df[(df['PLANNER BUCKET'] == selected_bucket) & (df['Fiscal Year'] == selected_year)]
    
    # Prepare data for the table
    table_data = [["Task", "Semester", "Fiscal Year", "Start Date", "End Date", "Progress"]]
    for _, row in bucket_df.iterrows():
        table_data.append([
            str(row['TASK']), str(row['SEMESTER']), str(row['Fiscal Year']),
            row['START'].strftime('%m-%d-%Y, %A'), row['END'].strftime('%m-%d-%Y, %A'), str(row['PROGRESS'])
        ])

    # Create the table automatically
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(
        col_widths=(95, 35, 20, 45, 45, 30), 
        text_align="LEFT", 
        borders_layout="ALL",
        line_height=6
    ) as table:
        for data_row in table_data:
            row = table.row()
            for datum in data_row:
                row.cell(datum)
    
    return bytes(pdf.output())

# --- Page UI ---
st.set_page_config(page_title="Printable Reports", layout="wide")
st.title("📄 Printable Reports")
df = data_manager.load_data()

if df is not None:
    # (UI section remains the same)
    st.subheader("Summary Report")
    st.write("A high-level summary including all overdue tasks.")
    summary_pdf = create_summary_report(df)
    st.download_button("📥 Download Summary PDF", summary_pdf, "Project_Summary_Report.pdf", "application/pdf", key="summary_pdf")
    st.markdown("---")

    st.subheader("Full Project List")
    st.write("A detailed, landscape-oriented report with all columns for every task.")
    full_list_pdf = create_full_list_report(df)
    st.download_button("📥 Download Full List PDF", full_list_pdf, "Full_Project_List.pdf", "application/pdf", key="full_list_pdf")
    st.markdown("---")

    st.subheader("Planner Bucket Breakdown")
    st.write("Generate a report for a specific Planner Bucket and Fiscal Year.")
    
    col1, col2 = st.columns(2)
    with col1:
        bucket_options = sorted(df['PLANNER BUCKET'].unique().tolist())
        selected_bucket = st.selectbox("Select a Planner Bucket", options=bucket_options)
    with col2:
        year_options = sorted(df['Fiscal Year'].unique().tolist())
        selected_year = st.selectbox("Select a Fiscal Year", options=year_options)
    
    if selected_bucket and selected_year:
        bucket_pdf = create_bucket_report(df, selected_bucket, selected_year)
        st.download_button(
            label=f"📥 Download {selected_bucket} - FY{selected_year} Report",
            data=bucket_pdf,
            file_name=f"{selected_bucket}_{selected_year}_Report.pdf",
            mime="application/pdf",
            key="bucket_pdf"
        )
else:
    st.warning("Could not load data.")