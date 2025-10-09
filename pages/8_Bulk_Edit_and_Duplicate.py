# File: pages/6_Bulk_Edit_and_Duplicate.py
import streamlit as st
import pandas as pd
from io import BytesIO
import data_manager 
from datetime import datetime

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Bulk Edit & Duplicate", layout="wide")
st.title("⚙️ Bulk Edit & Duplicate Tasks")

df_original = data_manager.load_table('tasks')

if df_original is not None:
    st.info("Select a Planner Bucket and Fiscal Year to filter the data you want to manage.")
    
    # --- 1. FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        bucket_options = sorted(df_original['PLANNER BUCKET'].dropna().unique().tolist())
        selected_bucket = st.selectbox("Filter by Planner Bucket", options=bucket_options)
    with col2:
        # Ensure only valid integer years are in the options
        year_values = pd.to_numeric(df_original['Fiscal Year'], errors='coerce').dropna().unique()
        year_options = sorted([int(y) for y in year_values])
        selected_year = st.selectbox("Filter by Fiscal Year", options=year_options, index=len(year_options)-1 if year_options else 0)

    # Ensure the 'Fiscal Year' column is numeric before filtering
    df_original['Fiscal Year'] = pd.to_numeric(df_original['Fiscal Year'], errors='coerce')
    
    filtered_df = df_original[(df_original['PLANNER BUCKET'] == selected_bucket) & (df_original['Fiscal Year'] == selected_year)].copy()

    if not filtered_df.empty:
        # Create tabs for the different actions
        tab1, tab2 = st.tabs(["Quick Edit & Delete", "Export & Import Changes"])

        with tab1:
            # --- QUICK EDIT & DELETE SECTION ---
            st.subheader(f"Quick Edit or Delete for {selected_bucket} - FY{selected_year}")
            filtered_df['Delete'] = False
            column_order = ['Delete', 'ASSIGNMENT TITLE', 'PROGRESS', 'TASK', 'SEMESTER', 'AUDIENCE', 'START', 'END']
            edited_df = st.data_editor(filtered_df[column_order], hide_index=True, key="quick_edit_table", column_config={
                "Delete": st.column_config.CheckboxColumn(required=True),
                "PROGRESS": st.column_config.SelectboxColumn("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"], required=True),
                "START": st.column_config.DateColumn("Start Date", format="MM-DD-YYYY, dddd"),
                "END": st.column_config.DateColumn("End Date", format="MM-DD-YYYY, dddd")
            })
            
            col_save, col_delete = st.columns(2)
            with col_save:
                if st.button("Save Quick Changes"):
                    df_updated = df_original.copy()
                    df_updated.update(edited_df.drop(columns=['Delete']))
                    if data_manager.save_and_log_changes(df_original, df_updated):
                        st.success("Changes saved and logged successfully!")
                        st.rerun()
            with col_delete:
                if st.button("❌ Delete Selected Tasks", type="primary"):
                    rows_to_delete = edited_df[edited_df['Delete'] == True]
                    if not rows_to_delete.empty:
                        indices_to_delete = rows_to_delete.index
                        df_after_delete = df_original.drop(indices_to_delete)
                        if data_manager.save_and_log_changes(df_original, df_after_delete):
                            st.success(f"Successfully deleted and logged {len(indices_to_delete)} task(s)!")
                            st.rerun()
                    else:
                        st.warning("No tasks were selected for deletion.")

        with tab2:
            # --- EXPORT AND IMPORT SECTION ---
            st.subheader(f"Export and Import for {selected_bucket} - FY{selected_year}")
            
            @st.cache_data
            def to_excel(df_export):
                output = BytesIO()
                df_formatted = df_export.copy()
                df_formatted['START'] = pd.to_datetime(df_formatted['START']).dt.strftime('%m-%d-%Y')
                df_formatted['END'] = pd.to_datetime(df_formatted['END']).dt.strftime('%m-%d-%Y')
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_formatted.to_excel(writer, index=False, sheet_name='Sheet1')
                return output.getvalue()

            st.download_button(
                label="📥 Download Filtered Tasks (.xlsx)",
                data=to_excel(filtered_df),
                file_name=f"{selected_bucket}_FY{selected_year}_tasks.xlsx"
            )
            
            st.write("---")
            st.write("After editing, upload the file here to save the changes.")
            uploaded_file = st.file_uploader("Choose an XLSX file to upload", type="xlsx")

            if uploaded_file is not None:
                uploaded_raw = pd.read_excel(uploaded_file)
                # Show uploaded columns and allow mapping
                st.subheader("Column mapping (optional)")
                uploaded_cols = uploaded_raw.columns.tolist()
                st.write("Detected columns:", uploaded_cols)

                expected_fields = ['#','ASSIGNMENT TITLE','PROGRESS','TASK','SEMESTER','AUDIENCE','START','END','PLANNER BUCKET','Fiscal Year']

                auto_match = st.checkbox("Auto-match column names where possible", value=True)

                mapping = {}
                with st.form("column_mapping_form"):
                    colmap_cols = {}
                    for field in expected_fields:
                        default_sel = '(none)'
                        if auto_match:
                            # try case-insensitive exact match or partial match
                            lower_cols = {c.lower(): c for c in uploaded_cols}
                            if field.lower() in lower_cols:
                                default_sel = lower_cols[field.lower()]
                            else:
                                # partial match: find any uploaded col containing the field token
                                matches = [c for c in uploaded_cols if field.lower() in c.lower()]
                                if matches:
                                    default_sel = matches[0]
                        colmap_cols[field] = st.selectbox(f"Map uploaded column to '{field}'", options=['(none)'] + uploaded_cols, index=(0 if default_sel=='(none)' else (uploaded_cols.index(default_sel)+1)))

                    submitted_map = st.form_submit_button("Apply mapping")

                if submitted_map:
                    # build rename dict: uploaded_col -> expected_field
                    rename_dict = {}
                    for field, sel in colmap_cols.items():
                        if sel and sel != '(none)':
                            rename_dict[sel] = field

                    # create a mapped copy
                    uploaded_mapped = uploaded_raw.rename(columns=rename_dict).copy()
                else:
                    uploaded_mapped = uploaded_raw.copy()

                # Normalize dates if present
                if 'START' in uploaded_mapped.columns:
                    uploaded_mapped['START'] = pd.to_datetime(uploaded_mapped['START'], errors='coerce')
                if 'END' in uploaded_mapped.columns:
                    uploaded_mapped['END'] = pd.to_datetime(uploaded_mapped['END'], errors='coerce')

                st.markdown("---")
                st.write("Upload preview & options:")

                # Basic validation: require '#' column to map rows
                if '#' not in uploaded_mapped.columns:
                    st.error("Uploaded file (after mapping) must include the '#' column (task id) so rows can be safely matched. If you want to add new tasks, include rows without '#' and use the 'Append new rows' option.")
                else:
                    updated_df_from_upload = uploaded_mapped
                    existing_ids = set(df_original['#'].astype(str).tolist())
                    uploaded_ids_all = updated_df_from_upload['#'].dropna().astype(str).tolist()
                    uploaded_ids = set(uploaded_ids_all)
                    matched_ids = uploaded_ids.intersection(existing_ids)
                    new_ids = uploaded_ids.difference(existing_ids)
                    rows_without_id_count = len(updated_df_from_upload[updated_df_from_upload['#'].isna()])

                    st.write(f"Rows in uploaded file: {len(updated_df_from_upload)}")
                    st.write(f"Rows matching existing tasks by '#': {len(matched_ids)}")
                    st.write(f"Rows with new '#'(not matching existing ids): {len(new_ids)}")
                    st.write(f"Rows without '#': {rows_without_id_count}")

                    st.write("Choose how to apply the uploaded data:")
                    update_existing = st.checkbox("Update only matching existing tasks (safe, default)", value=True)
                    append_new = st.checkbox("Append new rows (rows with new or missing '#')", value=False)

                    # Show a small preview of the first few matching updates
                    if matched_ids:
                        preview_matches = updated_df_from_upload[updated_df_from_upload['#'].astype(str).isin(list(matched_ids))].head(10)
                        st.subheader("Preview: Matching rows (will be used to update existing tasks)")
                        st.dataframe(preview_matches, use_container_width=True)

                    if append_new:
                        st.info("New rows will be appended. IDs from the uploaded file will be ignored for appended rows and new IDs will be assigned to avoid collisions.")
                        preview_new = updated_df_from_upload[updated_df_from_upload['#'].astype(str).isin(list(new_ids))].head(10)
                        st.subheader("Preview: New rows to append")
                        st.dataframe(preview_new, use_container_width=True)

                    # Compute proposed updated DataFrame for preview (dry-run)
                    def build_proposed_df():
                        df_proposed = df_original.copy()
                        uploaded = updated_df_from_upload.copy()
                        if '#' in uploaded.columns and uploaded['#'].notna().any():
                            uploaded['#'] = uploaded['#'].astype('Int64')

                        # Update existing rows
                        if update_existing and matched_ids:
                            df_proposed.set_index('#', inplace=True)
                            uploaded.set_index('#', inplace=True)
                            uploaded_matched = uploaded.loc[uploaded.index.intersection(df_proposed.index)]
                            if not uploaded_matched.empty:
                                df_proposed.update(uploaded_matched)
                            df_proposed.reset_index(inplace=True)

                        # Append new rows if requested
                        if append_new:
                            to_append = updated_df_from_upload[~updated_df_from_upload['#'].astype(str).isin(existing_ids)].copy()
                            to_append = pd.concat([to_append, updated_df_from_upload[updated_df_from_upload['#'].isna()]], ignore_index=True).drop_duplicates()
                            if not to_append.empty:
                                next_id = int(df_original['#'].max()) if pd.notna(df_original['#'].max()) else 0
                                new_rows = []
                                for _, row in to_append.iterrows():
                                    next_id += 1
                                    row_copy = row.copy()
                                    row_copy['#'] = next_id
                                    new_rows.append(row_copy)
                                new_rows_df = pd.DataFrame(new_rows)
                                if 'START' in new_rows_df.columns:
                                    new_rows_df['START'] = pd.to_datetime(new_rows_df['START'], errors='coerce')
                                if 'END' in new_rows_df.columns:
                                    new_rows_df['END'] = pd.to_datetime(new_rows_df['END'], errors='coerce')
                                df_proposed = pd.concat([df_proposed, new_rows_df], ignore_index=True)

                        return df_proposed

                    if st.button("Preview changes (dry-run)"):
                        proposed = build_proposed_df()
                        # Build a row-by-row diff: for updated rows, show fields that changed
                        diffs = []
                        key = '#'
                        compare_cols = [c for c in df_original.columns if c != key]

                        # Build dicts for quick lookup
                        orig_map = df_original.set_index(key).to_dict(orient='index')
                        prop_map = proposed.set_index(key).to_dict(orient='index')

                        # Check for updates and appends
                        for pid, prow in prop_map.items():
                            pid_str = str(pid)
                            if pid_str in [str(x) for x in orig_map.keys()]:
                                orig = orig_map[pid]
                                for col in compare_cols:
                                    o = orig.get(col, None)
                                    n = prow.get(col, None)
                                    # Normalize datetimes to strings for comparison
                                    try:
                                        if hasattr(o, 'to_pydatetime'):
                                            o = str(o)
                                    except Exception:
                                        pass
                                    try:
                                        if hasattr(n, 'to_pydatetime'):
                                            n = str(n)
                                    except Exception:
                                        pass
                                    if pd.isna(o) and pd.isna(n):
                                        continue
                                    if (o is None and n is None) or (o == n):
                                        continue
                                    diffs.append({'#': pid, 'action': 'UPDATE', 'field': col, 'old': o, 'new': n})
                            else:
                                # New appended row
                                for col in compare_cols:
                                    n = prow.get(col, None)
                                    if n is not None and not (pd.isna(n)):
                                        diffs.append({'#': pid, 'action': 'APPEND', 'field': col, 'old': '', 'new': n})

                        diffs_df = pd.DataFrame(diffs)
                        st.subheader("Preview of changes")
                        if diffs_df.empty:
                            st.info("No changes detected between current data and uploaded file (with selected options).")
                        else:
                            st.write(f"Total changed fields: {len(diffs_df)}; Updated rows: {len(diffs_df[diffs_df['action']=='UPDATE']['#'].unique())}; Appended rows: {len(diffs_df[diffs_df['action']=='APPEND']['#'].unique())}")
                            st.dataframe(diffs_df.sort_values(by=['action','#']).head(1000), use_container_width=True)

                        # Save proposed CSV to session_state for Confirm & Apply
                        try:
                            st.session_state['bulk_upload_proposed_csv'] = proposed.to_csv(index=False)
                        except Exception:
                            st.warning('Could not cache proposed CSV in session state; you can still re-run apply.')

                    # If a proposed CSV is cached, show Confirm & Apply button and download
                    if 'bulk_upload_proposed_csv' in st.session_state:
                        st.markdown("---")
                        st.subheader("Confirm & Apply")
                        st.write("You have a proposed set of changes ready. You can download the proposed dataset, or confirm to apply these changes to the database.")
                        st.download_button("Download proposed dataset (CSV)", data=st.session_state['bulk_upload_proposed_csv'], file_name='proposed_tasks_upload.csv', mime='text/csv')
                        if st.button("Confirm and Apply Proposed Changes"):
                            # Make a backup before applying
                            try:
                                backup_df = df_original.copy()
                                backup_path = f"backups/tasks_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                                import os
                                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                                backup_df.to_csv(backup_path, index=False)
                                st.info(f"Backup of current tasks saved to: {backup_path}")
                            except Exception as e:
                                st.warning(f"Could not write backup file: {e}")

                            # Load proposed and save
                            try:
                                proposed_df = pd.read_csv(pd.compat.StringIO(st.session_state['bulk_upload_proposed_csv']))
                            except Exception:
                                # fallback parse
                                import io
                                proposed_df = pd.read_csv(io.StringIO(st.session_state['bulk_upload_proposed_csv']))

                            if data_manager.save_and_log_changes(df_original, proposed_df):
                                st.success("Proposed changes applied and logged successfully!")
                                # clear preview cache
                                del st.session_state['bulk_upload_proposed_csv']
                                st.rerun()

        st.markdown("---")
        # --- 3. DUPLICATION SECTION ---
        st.subheader(f"Duplicate Tasks for a New Fiscal Year")
        st.write(f"This will copy all **{len(filtered_df)}** tasks from your current filter ({selected_bucket} - FY{selected_year}).")

        col1, col2 = st.columns(2)
        with col1:
            default_new_fy = selected_year + 1 if isinstance(selected_year, int) else datetime.now().year + 1
            new_fy = st.number_input("Enter New Fiscal Year:", min_value=2020, value=default_new_fy)
        with col2:
            days_to_shift = st.number_input("Days to shift dates forward:", value=364)

        if st.button(f"Duplicate Tasks to FY{new_fy}"):
            duplicated_tasks = filtered_df.copy()
            
            duplicated_tasks['Fiscal Year'] = new_fy
            time_delta = pd.Timedelta(days=days_to_shift)
            duplicated_tasks['START'] = duplicated_tasks['START'] + time_delta
            duplicated_tasks['END'] = duplicated_tasks['END'] + time_delta
            
            last_id = df_original['#'].max()
            duplicated_tasks['#'] = range(last_id + 1, last_id + 1 + len(duplicated_tasks))
            
            df_after_duplication = pd.concat([df_original, duplicated_tasks], ignore_index=True)
            
            if data_manager.save_and_log_changes(df_original, df_after_duplication):
                st.success(f"Successfully duplicated and logged {len(duplicated_tasks)} tasks to FY{new_fy}!")
                st.balloons()
                st.rerun()
    else:
        st.warning("No tasks found for the selected Planner Bucket and Fiscal Year.")
else:
    st.warning("Could not load data.")

