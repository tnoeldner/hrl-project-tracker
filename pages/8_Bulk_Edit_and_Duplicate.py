# File: pages/6_Bulk_Edit_and_Duplicate.py
import streamlit as st
import pandas as pd
from io import BytesIO
import data_manager 

st.set_page_config(page_title="Bulk Edit & Duplicate", layout="wide")
st.title("⚙️ Bulk Edit & Duplicate Tasks")

df_original = data_manager.load_table('tasks')

if df_original is not None:
    st.info("Select a Planner Bucket and Fiscal Year to filter the data you want to manage.")
    
    # --- 1. FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        bucket_options = sorted(df_original['PLANNER BUCKET'].unique().tolist())
        selected_bucket = st.selectbox("Filter by Planner Bucket", options=bucket_options)
    with col2:
        year_options = sorted(df_original['Fiscal Year'].unique().tolist())
        selected_year = st.selectbox("Filter by Fiscal Year", options=year_options, index=len(year_options)-1)

    filtered_df = df_original[(df_original['PLANNER BUCKET'] == selected_bucket) & (df_original['Fiscal Year'] == selected_year)].copy()

    if not filtered_df.empty:
        # Create tabs for the different actions
        tab1, tab2 = st.tabs(["Quick Edit & Delete", "Export & Import Changes"])

        with tab1:
            # --- QUICK EDIT & DELETE SECTION ---
            st.subheader(f"Quick Edit or Delete for {selected_bucket} - FY{selected_year}")
            # ... (This section remains the same)
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
                # Read the uploaded file
                updated_df_from_upload = pd.read_excel(uploaded_file)
                
                # --- CRITICAL FIX IS HERE ---
                # Apply robust date parsing to the uploaded file
                updated_df_from_upload['START'] = pd.to_datetime(updated_df_from_upload['START'], errors='coerce')
                updated_df_from_upload['END'] = pd.to_datetime(updated_df_from_upload['END'], errors='coerce')
                # -------------------------

                if st.button("Apply and Save Uploaded Changes"):
                    df_updated_upload = df_original.copy()
                    df_updated_upload.set_index('#', inplace=True)
                    updated_df_from_upload.set_index('#', inplace=True)
                    
                    df_updated_upload.update(updated_df_from_upload)
                    
                    df_updated_upload.reset_index(inplace=True)
                    
                    if data_manager.save_and_log_changes(df_original, df_updated_upload):
                        st.success("Uploaded changes have been saved and logged successfully!")
                        st.rerun()

        st.markdown("---")
        # --- DUPLICATION SECTION ---
        # ... (This section remains the same)
        st.subheader(f"Duplicate Tasks for a New Fiscal Year")
        st.write(f"This will copy all **{len(filtered_df)}** tasks from your current filter ({selected_bucket} - FY{selected_year}).")
        col1, col2 = st.columns(2)
        with col1:
            new_fy = st.number_input("Enter New Fiscal Year:", min_value=2020, value=selected_year + 1)
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