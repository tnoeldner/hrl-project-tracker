# File: pages/4_Calendar_View.py
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
import data_manager
import ics_export

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Calendar View", layout="wide")
st.title("📅 Calendar View")

df_original = data_manager.load_table('tasks')
icons_df = data_manager.load_table('bucket_icons')

if df_original is not None and icons_df is not None:
    st.info("Tasks are color-coded by Fiscal Year and include an icon for the Planner Bucket. Click any task to edit.")
    
    # --- DYNAMIC ICON MAPPING ---
    # Convert the icons DataFrame to a dictionary for easy lookup
    bucket_icon_map = pd.Series(icons_df.icon.values, index=icons_df.bucket_name).to_dict()
    # Ensure a default icon exists for buckets not in the map
    if 'Default' not in bucket_icon_map:
        bucket_icon_map['Default'] = '📌'
    
    # --- COLOR MAPPING LOGIC ---
    # Ensure Fiscal Year is treated as a number for color mapping
    df_original['Fiscal Year'] = pd.to_numeric(df_original['Fiscal Year'], errors='coerce')
    fiscal_years = sorted(df_original['Fiscal Year'].dropna().unique())
    color_palette = ["#009A44", "#007BA7", "#E69F00", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442"]
    year_color_map = {year: color_palette[i % len(color_palette)] for i, year in enumerate(fiscal_years)}

    # --- Display Legends ---
    st.subheader("Legends")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Fiscal Year Color**")
        if fiscal_years:
            # Ensure there's a max number of columns to prevent layout errors
            cols = st.columns(min(len(fiscal_years), 4)) 
            for i, year in enumerate(fiscal_years):
                with cols[i % len(cols)]:
                    st.markdown(f"<span style='color:{year_color_map.get(year, '#808080')};'>●</span> FY{int(year)}", unsafe_allow_html=True)
    with col2:
        st.write("**Planner Bucket Icon**")
        # Display the icon legend in a scrollable container
        with st.container(height=100):
             for bucket, icon in bucket_icon_map.items():
                 st.markdown(f"{icon} {bucket}")
    st.markdown("---")

    df_cal = df_original.copy()
    # Convert Fiscal Year to string for display purposes in the title
    df_cal['Fiscal Year'] = df_cal['Fiscal Year'].apply(lambda x: int(x) if pd.notna(x) else '').astype(str)

    tasks_for_calendar = []
    for index, row in df_cal.iterrows():
        if pd.notna(row['START']) and pd.notna(row['END']):
            # Use the original numeric fiscal year for the color lookup
            original_year = df_original.loc[index, 'Fiscal Year']
            task_color = year_color_map.get(original_year, "#808080")
            
            # Get the icon for the task's bucket
            bucket = row.get('PLANNER BUCKET', 'Default')
            icon = bucket_icon_map.get(bucket, bucket_icon_map['Default'])
            
            tasks_for_calendar.append({
                "title": f"{icon} {row['TASK']} (FY{row['Fiscal Year']})", # Prepend icon to title
                "start": row['START'].strftime("%Y-%m-%d"), 
                "end": row['END'].strftime("%Y-%m-%d"), 
                "id": index,
                "color": task_color 
            })

    clicked_event = calendar(events=tasks_for_calendar)

    # --- ICS EXPORT CONTROLS ---
    st.markdown("---")
    st.subheader("Export Calendar")
    export_col1, export_col2 = st.columns([1, 1])
    with export_col1:
        if st.button("📥 Download .ics for all visible tasks"):
            # Build a DataFrame of the visible tasks (those with START/END)
            export_df = df_cal.copy()
            # Keep only rows with valid dates
            export_df = export_df[pd.notna(export_df['START']) & pd.notna(export_df['END'])]
            ics_bytes = ics_export.generate_ics_from_df(export_df)
            st.download_button(label="Download calendar.ics", data=ics_bytes, file_name="hrl_project_tracker_calendar.ics", mime="text/calendar")
    with export_col2:
        if 'selected_task_id' in st.session_state and st.session_state['selected_task_id'] is not None:
            task_id = st.session_state['selected_task_id']
            if task_id in df_original.index:
                if st.button("📥 Download .ics for selected task"):
                    single_df = df_original.loc[[task_id]].copy()
                    ics_bytes = ics_export.generate_ics_from_df(single_df)
                    filename = f"task_{int(task_id)}.ics"
                    st.download_button(label=f"Download .ics for task #{int(task_id)}", data=ics_bytes, file_name=filename, mime="text/calendar")

    if clicked_event and clicked_event.get('callback') == 'eventClick':
        task_id = clicked_event['eventClick']['event'].get('id')
        if task_id is not None:
            # Set the selected task ID without forcing a rerun
            st.session_state['selected_task_id'] = int(task_id)

    if 'selected_task_id' in st.session_state and st.session_state['selected_task_id'] is not None:
        task_id = st.session_state['selected_task_id']
        if task_id in df_original.index:
            task_data = df_original.loc[task_id].copy()
            st.subheader(f"✍️ Editing Task: {task_data['TASK']}")
            with st.form("edit_task_form"):
                
                # --- COMPLETE EDITING FORM ---
                assignment_options = sorted([str(item) for item in df_original['ASSIGNMENT TITLE'].unique()])
                progress_options = ["NOT STARTED", "IN PROGRESS", "COMPLETE"]
                bucket_options_form = sorted([str(item) for item in icons_df['bucket_name'].unique()]) # Use icons_df for bucket options
                semester_options = sorted([str(s) for s in df_original['SEMESTER'].unique() if s and pd.notna(s)])
                year_options_form = sorted([int(y) for y in df_original['Fiscal Year'].dropna().unique()])
                
                # Get current indices for dropdowns with error handling
                try: title_index = assignment_options.index(task_data['ASSIGNMENT TITLE'])
                except (ValueError, TypeError): title_index = 0
                try: progress_index = progress_options.index(task_data.get('PROGRESS', 'NOT STARTED'))
                except (ValueError, TypeError): progress_index = 0
                try: bucket_index = bucket_options_form.index(task_data['PLANNER BUCKET'])
                except (ValueError, TypeError): bucket_index = 0
                try: 
                    current_semester = str(task_data.get('SEMESTER', ''))
                    semester_index = semester_options.index(current_semester) if current_semester in semester_options else 0
                except (ValueError, TypeError): semester_index = 0
                try:
                    year_index = year_options_form.index(task_data['Fiscal Year'])
                except (ValueError, TypeError):
                    year_index = 0

                c1, c2 = st.columns(2)
                with c1:
                    new_assignment_title = st.selectbox("Assignment Title", options=assignment_options, index=title_index)
                    new_progress = st.selectbox("Progress", options=progress_options, index=progress_index)
                    new_bucket = st.selectbox("Planner Bucket", options=bucket_options_form, index=bucket_index)
                    new_fiscal_year = st.selectbox("Fiscal Year", options=year_options_form, index=year_index)
                with c2:
                    new_start_date = st.date_input("Start Date", value=pd.to_datetime(task_data['START']))
                    new_end_date = st.date_input("End Date", value=pd.to_datetime(task_data['END']))
                    new_semester = st.selectbox("Semester", options=semester_options, index=semester_index)

                new_task_desc = st.text_area("Task Description", value=task_data['TASK'])

                col_save, col_cancel = st.columns(2)
                with col_save:
                    submitted = st.form_submit_button("Save Changes")
                with col_cancel:
                    cancelled = st.form_submit_button("Cancel")

                if submitted:
                    df_updated = df_original.copy()
                    
                    # --- CRITICAL SAFEGUARD ---
                    if df_updated is None or df_updated.empty:
                        st.error("CRITICAL ERROR: Original data is missing. Save operation aborted to prevent data loss.")
                    else:
                        df_updated.loc[task_id, 'ASSIGNMENT TITLE'] = new_assignment_title
                        df_updated.loc[task_id, 'PROGRESS'] = new_progress
                        df_updated.loc[task_id, 'START'] = pd.to_datetime(new_start_date)
                        df_updated.loc[task_id, 'END'] = pd.to_datetime(new_end_date)
                        df_updated.loc[task_id, 'PLANNER BUCKET'] = new_bucket
                        df_updated.loc[task_id, 'SEMESTER'] = new_semester
                        df_updated.loc[task_id, 'TASK'] = new_task_desc
                        df_updated.loc[task_id, 'Fiscal Year'] = new_fiscal_year
                        
                        user_email = st.session_state.logged_in_user
                        if data_manager.save_and_log_changes(df_original, df_updated, user_email, "Calendar Edit"):
                            st.success("Task updated and logged successfully!")
                            st.session_state['selected_task_id'] = None
                            st.rerun() 
                
                if cancelled:
                    st.session_state['selected_task_id'] = None
                    st.rerun()
else:
    st.warning("Could not load data.")

