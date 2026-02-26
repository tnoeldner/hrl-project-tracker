# File: pages/8_Printable_Reports.py
import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import data_manager
import calendar as py_calendar

# --- Helpers ---
def format_date(value, fmt='%Y-%m-%d'):
    """Safely format dates, returning a placeholder when missing."""
    if pd.isna(value):
        return "N/A"
    try:
        return pd.to_datetime(value).strftime(fmt)
    except Exception:
        return str(value)

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
                format_date(row['END'], '%Y-%m-%d'),
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
            format_date(row['START'], '%Y-%m-%d'), format_date(row['END'], '%Y-%m-%d'), str(row['PROGRESS'])
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
            format_date(row['START'], '%m-%d-%Y, %A'), format_date(row['END'], '%m-%d-%Y, %A'), str(row['PROGRESS'])
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
                    format_date(details['START'], '%m-%d-%Y, %A'), format_date(details['END'], '%m-%d-%Y, %A')
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
                pdf.cell(0, 6, f"  FY{year1}: {format_date(task1['START'], '%m-%d-%Y')} to {format_date(task1['END'], '%m-%d-%Y')}", ln=True)
                pdf.cell(0, 6, f"  FY{year2}: {format_date(task2['START'], '%m-%d-%Y')} to {format_date(task2['END'], '%m-%d-%Y')}", ln=True)
                pdf.ln(4)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, "None", ln=True)

    return bytes(pdf.output())

def create_bucket_multi_year_report(df, years):
    """Creates a bucket-grouped PDF showing start/end dates across three years."""
    years = sorted(years)
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Bucket Task Timeline (FY {years[0]}, {years[1]}, {years[2]})", ln=True, align='C')
    pdf.ln(8)

    buckets = sorted(df['PLANNER BUCKET'].dropna().unique())
    any_data = False

    for bucket in buckets:
        bucket_df = df[(df['PLANNER BUCKET'] == bucket) & (df['Fiscal Year'].isin(years))]
        if bucket_df.empty:
            continue

        any_data = True
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Bucket: {bucket}", ln=True)

        headers = ["Task"]
        for y in years:
            headers.extend([f"FY{y} Start", f"FY{y} End"])

        table_data = [headers]
        tasks = sorted(bucket_df['TASK'].dropna().unique())
        for task_name in tasks:
            row = [str(task_name)]
            for y in years:
                match = bucket_df[(bucket_df['TASK'] == task_name) & (bucket_df['Fiscal Year'] == y)]
                if not match.empty:
                    start_val = format_date(match.iloc[0]['START'], '%m-%d-%Y')
                    end_val = format_date(match.iloc[0]['END'], '%m-%d-%Y')
                else:
                    start_val = "—"
                    end_val = "—"
                row.extend([start_val, end_val])
            table_data.append(row)

        pdf.set_font("Helvetica", "", 8)
        # Width: task column wider, date columns compact
        col_widths = [70] + [25] * 6
        with pdf.table(col_widths=tuple(col_widths), text_align="LEFT", borders_layout="ALL", line_height=5) as table:
            for data_row in table_data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)

        pdf.ln(6)

    if not any_data:
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "No tasks found for the selected years.", ln=True, align='C')

    return bytes(pdf.output())

def find_task_bucket_duplicates(df):
    """Return rows that share the same Task + Planner Bucket + Fiscal Year."""
    required = {'TASK', 'PLANNER BUCKET', 'Fiscal Year'}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    subset_cols = ['TASK', 'PLANNER BUCKET', 'Fiscal Year']
    dupes = df[df.duplicated(subset=subset_cols, keep=False)].copy()
    sort_cols = [col for col in ['PLANNER BUCKET', 'TASK', 'Fiscal Year', '#'] if col in dupes.columns]
    return dupes.sort_values(sort_cols) if not dupes.empty else dupes

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
    
    st.markdown("---")
    st.subheader("Bucket Task Timeline (3 Years)")
    year_options_timeline = sorted(df['Fiscal Year'].unique().tolist())
    default_years = year_options_timeline[-3:] if len(year_options_timeline) >= 3 else year_options_timeline
    selected_years = st.multiselect("Pick exactly three fiscal years", options=year_options_timeline, default=default_years)
    if len(selected_years) == 3:
        timeline_pdf = create_bucket_multi_year_report(df, selected_years)
        st.download_button(
            label=f"📥 Download Bucket Timeline for FY {selected_years[0]}, {selected_years[1]}, {selected_years[2]}",
            data=timeline_pdf,
            file_name=f"Bucket_Timeline_FY_{selected_years[0]}_{selected_years[1]}_{selected_years[2]}.pdf",
            mime="application/pdf",
            key="bucket_timeline_pdf"
        )
    else:
        st.info("Select three years to enable the download.")

    st.markdown("---")
    st.subheader("Duplicate Task Checker (Task + Bucket + Fiscal Year)")
    dup_df = find_task_bucket_duplicates(df)
    if dup_df.empty:
        st.info("No duplicate Task + Bucket combinations found.")
    else:
        st.caption(f"Found {len(dup_df)} duplicate rows across {dup_df[['TASK','PLANNER BUCKET','Fiscal Year']].drop_duplicates().shape[0]} task/bucket/year combos. The first column below is the row index; select that to delete.")
        dup_display = dup_df.reset_index().rename(columns={'index': 'ROW'})
        st.dataframe(dup_display[['ROW', '#', 'TASK', 'PLANNER BUCKET', 'Fiscal Year', 'START', 'END', 'PROGRESS']], use_container_width=True)
        selected_rows = st.multiselect("Select row indexes to delete", options=dup_display['ROW'].tolist())
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Delete selected duplicates", type="primary", disabled=len(selected_rows) == 0):
                updated_df = df.drop(index=selected_rows).copy()
                user_email = getattr(st.session_state, 'logged_in_user', 'system')
                if data_manager.save_and_log_changes(df, updated_df, user_email=user_email, source_page="Duplicate Task Cleaner"):
                    st.success(f"Deleted {len(selected_rows)} duplicate task(s).")
                    st.rerun()
                else:
                    st.error("Failed to delete duplicates. Please try again.")
        with col_b:
            if st.button("Auto-remove all duplicates", type="secondary"):
                # keep the first occurrence of each Task/Bucket/FY combo
                cleaned_df = df.drop_duplicates(subset=['TASK','PLANNER BUCKET','Fiscal Year'], keep='first').copy()
                removed_count = len(df) - len(cleaned_df)
                if removed_count > 0:
                    user_email = getattr(st.session_state, 'logged_in_user', 'system')
                    if data_manager.save_and_log_changes(df, cleaned_df, user_email=user_email, source_page="Duplicate Task Cleaner (auto)"):
                        st.success(f"Automatically removed {removed_count} duplicate row(s).")
                        st.rerun()
                    else:
                        st.error("Failed to remove duplicates automatically. Please try again.")
                else:
                    st.info("No duplicates to remove.")
else:
    st.warning("Could not load data.")






