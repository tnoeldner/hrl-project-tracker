# File: pages/4_Calendar_View.py
import streamlit as st
import pandas as pd
import json

def _safe_rerun():
    """Call Streamlit rerun in a way that's tolerant of older/newer Streamlit versions."""
    try:
        # Preferred API
        st.experimental_rerun()
    except Exception:
        try:
            # Older versions may not have experimental_rerun; use stop to force refresh on next interaction
            st.session_state['_needs_rerun'] = True
            st.stop()
        except Exception:
            pass
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

# --- Filters: Fiscal Year and Planner Bucket ---
df_filtered = None
if df_original is not None:
    # ensure fiscal year numeric for filter options
    df_original['Fiscal Year'] = pd.to_numeric(df_original.get('Fiscal Year', pd.Series()), errors='coerce')
    available_years = sorted(df_original['Fiscal Year'].dropna().unique().tolist())
    available_years_str = [int(y) for y in available_years]

    # Planner buckets from icons_df if available, otherwise from tasks
    if icons_df is not None and 'bucket_name' in icons_df.columns:
        available_buckets = sorted(icons_df['bucket_name'].dropna().unique().tolist())
    else:
        available_buckets = sorted(df_original['PLANNER BUCKET'].dropna().unique().tolist())

    # Presets: show apply/clear controls BEFORE the filter widgets so we can set session_state safely
    user_email = st.session_state.logged_in_user
    presets_df = data_manager.get_filter_presets(user_email)

    # Ensure a persistent key for the preset choice so it survives reruns
    preset_key = 'calendar_preset_choice'
    if preset_key not in st.session_state:
        st.session_state[preset_key] = '--'

    # If there's a pending apply/clear action from the previous run, perform it now BEFORE creating widgets
    if '__apply_preset_action__' in st.session_state:
        try:
            action = st.session_state.pop('__apply_preset_action__')
            year_key = 'calendar_selected_years'
            bucket_key = 'calendar_selected_buckets'
            if action == '__CLEAR__':
                st.session_state[year_key] = available_years_str
                st.session_state[bucket_key] = available_buckets
                # ensure the Filters expander is open so users see the cleared selection
                st.session_state['calendar_filters_open'] = True
                # set the preset selector to '--' before widgets are created
                st.session_state[preset_key] = '--'
            else:
                preset_rows = presets_df[presets_df['preset_name'] == action]
                if not preset_rows.empty:
                    preset_row = preset_rows.iloc[0]
                    yrs_raw = preset_row.get('years', None)
                    bks_raw = preset_row.get('buckets', None)
                    yrs = json.loads(yrs_raw) if (yrs_raw is not None and not pd.isna(yrs_raw) and yrs_raw != '') else []
                    bks = json.loads(bks_raw) if (bks_raw is not None and not pd.isna(bks_raw) and bks_raw != '') else []
                    st.session_state[year_key] = yrs
                    st.session_state[bucket_key] = bks
                    # set the preset choice key value BEFORE widget creation
                    st.session_state[preset_key] = action
                    # open the Filters expander so the applied preset is visible immediately
                    st.session_state['calendar_filters_open'] = True
                    # (no rerun here; widgets are created after this block and will read session_state)
        except Exception as e:
            st.error(f"Failed to apply pending preset action: {e}")

    apply_col1, apply_col2 = st.columns([3,1])
    with apply_col1:
        preset_choice = st.selectbox("Apply Preset", options=['--'] + presets_df['preset_name'].tolist() if not presets_df.empty else ['--'], key=preset_key)
    with apply_col2:
        # Apply button (schedules the preset application on next run)
        if st.button("Apply", key='preset_apply_btn'):
            # If '--' selected, clear filters (select all) on next run
            if preset_choice == '--':
                st.session_state['__apply_preset_action__'] = '__CLEAR__'
            else:
                # schedule apply of this preset on next run
                st.session_state['__apply_preset_action__'] = preset_choice
        # Explicit clear button so users don't need to select '--' then Apply
        if st.button("Clear Filters", key='preset_clear_btn'):
            # schedule the clear action; the pending-action handler will set the preset key
            st.session_state['__apply_preset_action__'] = '__CLEAR__'

    # UI controls (session_state-backed so presets can change widget values)
    year_key = 'calendar_selected_years'
    bucket_key = 'calendar_selected_buckets'
    if year_key not in st.session_state:
        st.session_state[year_key] = available_years_str
    if bucket_key not in st.session_state:
        st.session_state[bucket_key] = available_buckets

    # Track whether the Filters expander should be open (preset apply/clear will set this)
    if 'calendar_filters_open' not in st.session_state:
        st.session_state['calendar_filters_open'] = False

    with st.expander("Filters (affect display & .ics download)", expanded=st.session_state.get('calendar_filters_open', False)):
        cols = st.columns(2)
        with cols[0]:
            selected_years = st.multiselect("Fiscal Year", options=available_years_str, default=st.session_state[year_key], key=year_key)
        with cols[1]:
            selected_buckets = st.multiselect("Planner Bucket", options=available_buckets, default=st.session_state[bucket_key], key=bucket_key)

    # Apply filters to create df_filtered
    df_filtered = df_original.copy()
    if selected_years:
        df_filtered = df_filtered[df_filtered['Fiscal Year'].isin(selected_years)]
    if selected_buckets:
        df_filtered = df_filtered[df_filtered['PLANNER BUCKET'].isin(selected_buckets)]

    # --- Show number of events included in the filtered download ---
    try:
        cal_preview = data_manager.generate_calendar_from_tasks(df_filtered)
        event_count = sum(1 for c in cal_preview.walk() if c.name == 'VEVENT')
    except Exception:
        event_count = 0

    st.write(f"Events in current filter: **{event_count}**")

    # --- Preset management UI ---
    user_email = st.session_state.logged_in_user
    presets_df = data_manager.get_filter_presets(user_email)

    cols_presets = st.columns([3,3,2])
    with cols_presets[0]:
        st.write("**Saved presets:**")
        if not presets_df.empty:
            for name in presets_df['preset_name'].tolist():
                st.write(f"- {name}")
        else:
            st.write("(no presets)")
    with cols_presets[1]:
        new_preset_name = st.text_input("Save current filters as...", key='preset_name_input')
    with cols_presets[2]:
        if st.button("Save Preset") and new_preset_name:
            years_to_save = selected_years if 'selected_years' in locals() else []
            buckets_to_save = selected_buckets if 'selected_buckets' in locals() else []
            try:
                saved = data_manager.save_filter_preset(user_email, new_preset_name, years_to_save, buckets_to_save)
            except Exception as e:
                st.error(f"Failed to save preset (exception): {e}")
                saved = False

            if saved:
                st.success("Preset saved")
                # Schedule this preset to be applied so the user sees the result immediately
                st.session_state['__apply_preset_action__'] = new_preset_name
                st.session_state['calendar_filters_open'] = True

    # Delete preset
    if not presets_df.empty:
        del_col1, del_col2 = st.columns([3,1])
        with del_col1:
            del_choice = st.selectbox("Delete Preset", options=['--'] + presets_df['preset_name'].tolist())
        with del_col2:
            if st.button("Delete") and del_choice and del_choice != '--':
                if data_manager.delete_filter_preset(user_email, del_choice):
                    st.success("Preset deleted")
                    _safe_rerun()

    # (Preset application is handled by the Apply control above, which sets a temp session key and reruns.)

    # --- Export / Download .ics for users (uses filtered data) ---
    try:
        cal = data_manager.generate_calendar_from_tasks(df_filtered)
        ics_bytes = cal.to_ical()
        st.download_button(label="Download calendar (.ics)", data=ics_bytes, file_name="hrl_project_tracker.ics", mime="text/calendar")
    except Exception as e:
        st.warning(f"Could not prepare calendar download: {e}")

if df_filtered is not None and icons_df is not None:
    if df_filtered.empty:
        st.info("No tasks match the selected filters.")
    else:
        st.info("Tasks are color-coded by Fiscal Year and include an icon for the Planner Bucket. Click any task to edit.")

    # --- DYNAMIC ICON MAPPING ---
    # Convert the icons DataFrame to a dictionary for easy lookup
    bucket_icon_map = pd.Series(icons_df.icon.values, index=icons_df.bucket_name).to_dict()
    # Ensure a default icon exists for buckets not in the map
    if 'Default' not in bucket_icon_map:
        bucket_icon_map['Default'] = '📌'
    
    # --- COLOR MAPPING LOGIC ---
    # Ensure Fiscal Year is treated as a number for color mapping
    df_filtered['Fiscal Year'] = pd.to_numeric(df_filtered['Fiscal Year'], errors='coerce')
    fiscal_years = sorted(df_filtered['Fiscal Year'].dropna().unique())
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

    df_cal = df_filtered.copy()
    # Convert Fiscal Year to string for display purposes in the title
    df_cal['Fiscal Year'] = df_cal['Fiscal Year'].apply(lambda x: int(x) if pd.notna(x) else '').astype(str)

    tasks_for_calendar = []
    for index, row in df_cal.iterrows():
        if pd.notna(row['START']) and pd.notna(row['END']):
            # Use the original numeric fiscal year for the color lookup
            # If the original index exists in the unfiltered df, use it; otherwise use the row value
            try:
                original_year = df_original.loc[index, 'Fiscal Year']
            except Exception:
                original_year = row.get('Fiscal Year')
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

