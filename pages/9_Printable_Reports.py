# File: pages/8_Printable_Reports.py
import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import data_manager
import calendar as py_calendar

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

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
        
        # Create the table automatically
        pdf.set_font("Helvetica", "", 9)
        with pdf.table(col_widths=(80, 40, 30, 35), text_align="LEFT", borders_layout="ALL", line_height=6) as table:
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
    with pdf.table(col_widths=(10, 70, 30, 30, 15, 30, 25, 25, 30), text_align="LEFT", borders_layout="ALL", line_height=5) as table:
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

    pdf.set_font("Helvetica", "", 9)
    with pdf.table(col_widths=(95, 35, 20, 45, 45, 30), text_align="LEFT", borders_layout="ALL", line_height=6) as table:
        for data_row in table_data:
            row = table.row()
            for datum in data_row:
                row.cell(datum)
    
    return bytes(pdf.output())

def add_month_to_pdf(pdf, df, year, month):
    """Helper function to add a single month's data to a PDF object."""
    month_name = py_calendar.month_name[month]
    month_df = df[(df['START'].dt.year == year) & (df['START'].dt.month == month)]

    if not month_df.empty:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"{month_name} {year}", ln=True, align='C')
        pdf.ln(10)
        _, num_days = py_calendar.monthrange(year, month)
        for day in range(1, num_days + 1):
            day_date = datetime(year, month, day)
            tasks_on_day = month_df[month_df['START'].dt.date == day_date.date()]
            if not tasks_on_day.empty:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 10, day_date.strftime('%A, %B %d, %Y'), ln=True, border='B')
                pdf.ln(2)
                pdf.set_font("Helvetica", "", 10)
                for _, task in tasks_on_day.iterrows():
                    pdf.multi_cell(0, 8, f"- {task['TASK']} (Assigned to: {task['ASSIGNMENT TITLE']})", ln=True)
                pdf.ln(5)

def create_calendar_list_report(df, year, month):
    """Creates a printable, list-based calendar report for a single month."""
    pdf = FPDF()
    add_month_to_pdf(pdf, df, year, month)
    if not pdf.page_no():
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        month_name = py_calendar.month_name[month]
        pdf.cell(0, 10, f"Calendar Report for {month_name} {year}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "No tasks found for this month.", ln=True)
    return bytes(pdf.output())

def create_full_year_report(df, year):
    """Creates a printable report for an entire year, month by month."""
    pdf = FPDF()
    for month in range(1, 13):
        add_month_to_pdf(pdf, df, year, month)
    if not pdf.page_no():
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Calendar Report for {year}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "No tasks found for this year.", ln=True)
    return bytes(pdf.output())

def create_comparison_report(df, year1, year2):
    """Creates a PDF comparing the tasks between two fiscal years."""
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Task Comparison Report: FY{year1} vs. FY{year2}", ln=True, align='C')
    pdf.ln(10)

    df_year1 = df[df['Fiscal Year'] == year1].dropna(subset=['TASK'])
    df_year2 = df[df['Fiscal Year'] == year2].dropna(subset=['TASK'])
    tasks_year1 = set(df_year1['TASK'])
    tasks_year2 = set(df_year2['TASK'])
    added_tasks = sorted(list(tasks_year2 - tasks_year1))
    removed_tasks = sorted(list(tasks_year1 - tasks_year2))
    common_tasks = sorted(list(tasks_year1.intersection(tasks_year2)))

    def write_task_table(pdf, title, tasks, df_source):
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"{title} ({len(tasks)} total)", ln=True)
        if tasks:
            table_data = [["Task", "Planner Bucket", "Start Date", "End Date"]]
            for task_name in tasks:
                details = df_source[df_source['TASK'] == task_name].iloc[0]
                table_data.append([
                    str(details['TASK']), str(details['PLANNER BUCKET']),
                    details['START'].strftime('%m-%d-%Y, %A'), details['END'].strftime('%m-%d-%Y, %A')
                ])
            pdf.set_font("Helvetica", "", 8)
            with pdf.table(col_widths=(120, 50, 45, 45), text_align="LEFT", borders_layout="ALL", line_height=5) as table:
                for data_row in table_data:
                    row = table.row()
                    for datum in data_row:
                        row.cell(datum)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 8, "None", ln=True)
        pdf.ln(10)

    write_task_table(pdf, f"Tasks Added in FY{year2}", added_tasks, df_year2)
    write_task_table(pdf, f"Tasks Removed from FY{year1}", removed_tasks, df_year1)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Tasks Common to Both Years ({len(common_tasks)} total)", ln=True)
    
    if common_tasks:
        # Group common tasks by Planner Bucket
        common_tasks_df = df_year2[df_year2['TASK'].isin(common_tasks)]
        grouped_tasks = common_tasks_df.groupby('PLANNER BUCKET')

        for bucket_name, group in grouped_tasks:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, f"Planner Bucket: {bucket_name}", ln=True)
            
            for task_name in sorted(group['TASK'].tolist()):
                task1 = df_year1[df_year1['TASK'] == task_name].iloc[0]
                task2 = df_year2[df_year2['TASK'] == task_name].iloc[0]
                
                pdf.set_font("Helvetica", "B", 9)
                pdf.multi_cell(0, 8, f"- {task_name}", ln=True)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(0, 6, f"  FY{year1}: {task1['START'].strftime('%m-%d-%Y')} to {task1['END'].strftime('%m-%d-%Y')}", ln=True)
                pdf.cell(0, 6, f"  FY{year2}: {task2['START'].strftime('%m-%d-%Y')} to {task2['END'].strftime('%m-%d-%Y')}", ln=True)
                pdf.ln(4)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, "None", ln=True)

    return bytes(pdf.output())

# --- Page UI ---
st.set_page_config(page_title="Printable Reports", layout="wide")
st.title("📄 Printable Reports")
df = data_manager.load_table('tasks')

if df is not None:
    st.subheader("Summary Report")
    st.download_button("📥 Download Summary PDF", create_summary_report(df), "Project_Summary_Report.pdf", "application/pdf", key="summary_pdf")
    st.markdown("---")
    st.subheader("Full Project List")
    st.download_button("📥 Download Full List PDF", create_full_list_report(df), "Full_Project_List.pdf", "application/pdf", key="full_list_pdf")
    st.markdown("---")
    st.subheader("Planner Bucket Breakdown")
    col1, col2 = st.columns(2)
    with col1:
        bucket_options = sorted(df['PLANNER BUCKET'].unique().tolist())
        selected_bucket = st.selectbox("Select a Planner Bucket", options=bucket_options)
    with col2:
        year_options_bucket = sorted(df['Fiscal Year'].unique().tolist())
        selected_year_bucket = st.selectbox("Select a Fiscal Year", options=year_options_bucket)
    if selected_bucket and selected_year_bucket:
        st.download_button(
            label=f"📥 Download {selected_bucket} - FY{selected_year_bucket} Report",
            data=create_bucket_report(df, selected_bucket, selected_year_bucket),
            file_name=f"{selected_bucket}_{selected_year_bucket}_Report.pdf",
            mime="application/pdf"
        )
    st.markdown("---")
    st.subheader("Calendar Report (List Format)")
    col1, col2 = st.columns(2)
    with col1:
        year_options = sorted(df['Fiscal Year'].unique().tolist())
        selected_year_cal = st.selectbox("Select a Year", options=year_options, index=len(year_options)-1)
    with col2:
        month_names = [py_calendar.month_name[i] for i in range(1, 13)]
        month_options = ["Full Year"] + month_names
        selected_month_name = st.selectbox("Select a Month", options=month_options)
    if selected_year_cal and selected_month_name:
        if selected_month_name == "Full Year":
            calendar_pdf = create_full_year_report(df, selected_year_cal)
            st.download_button(
                label=f"📥 Download Full Year PDF for {selected_year_cal}",
                data=calendar_pdf,
                file_name=f"Full_Year_Report_{selected_year_cal}.pdf",
                mime="application/pdf",
                key="full_year_pdf"
            )
        else:
            selected_month_num = month_names.index(selected_month_name) + 1
            calendar_pdf = create_calendar_list_report(df, selected_year_cal, selected_month_num)
            st.download_button(
                label=f"📥 Download Calendar PDF for {selected_month_name} {selected_year_cal}",
                data=calendar_pdf,
                file_name=f"Calendar_Report_{selected_year_cal}_{selected_month_name}.pdf",
                mime="application/pdf",
                key="monthly_cal_pdf"
            )
    st.markdown("---")
    st.subheader("Fiscal Year Comparison Report")
    col1, col2 = st.columns(2)
    with col1:
        year_options_comp = sorted(df['Fiscal Year'].unique().tolist())
        year1 = st.selectbox("Select the first year (older)", options=year_options_comp, index=0)
    with col2:
        year2 = st.selectbox("Select the second year (newer)", options=year_options_comp, index=len(year_options_comp)-1)
    if year1 and year2 and year1 != year2:
        comparison_pdf = create_comparison_report(df, year1, year2)
        st.download_button(
            label=f"📥 Download Comparison PDF for FY{year1} vs. FY{year2}",
            data=comparison_pdf,
            file_name=f"Comparison_Report_{year1}_vs_{year2}.pdf",
            mime="application/pdf",
            key="comparison_pdf"
        )
    elif year1 == year2:
        st.warning("Please select two different fiscal years to compare.")
else:
    st.warning("Could not load data.")






