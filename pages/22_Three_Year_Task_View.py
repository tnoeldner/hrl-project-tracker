# File: pages/22_Three_Year_Task_View.py
import streamlit as st
import pandas as pd
import data_manager

st.set_page_config(page_title="Three-Year Task View", layout="wide")
st.title("📊 Three-Year Task Table View")

df_original = data_manager.load_table('tasks')

if df_original is not None:
    # --- FILTERS ---
    all_buckets = sorted(df_original['PLANNER BUCKET'].dropna().unique())
    all_assignments = sorted(df_original['ASSIGNMENT TITLE'].dropna().unique())
    all_semesters = sorted(df_original['SEMESTER'].dropna().unique())
    selected_bucket = st.selectbox("Filter by Planner Bucket", options=['All'] + all_buckets, key="filter_bucket")
    selected_assignment = st.selectbox("Filter by Assignment Title", options=['All'] + all_assignments, key="filter_assignment")

    filtered_df = df_original.copy()
    if selected_bucket != 'All':
        filtered_df = filtered_df[filtered_df['PLANNER BUCKET'] == selected_bucket]
    if selected_assignment != 'All':
        filtered_df = filtered_df[filtered_df['ASSIGNMENT TITLE'] == selected_assignment]

    df_original['Fiscal Year'] = pd.to_numeric(df_original.get('Fiscal Year', pd.Series()), errors='coerce')
    available_years = sorted(df_original['Fiscal Year'].dropna().unique().tolist())
    available_years_str = [int(y) for y in available_years]

    if available_years_str:
        default_year = max(available_years_str)
        selected_year = st.selectbox(
            "Select Center Year",
            options=available_years_str,
            index=available_years_str.index(default_year) if default_year in available_years_str else 0,
            key="three_year_center_year"
        )
        years_to_show = [selected_year - 1, selected_year, selected_year + 1]
    else:
        selected_year = None
        years_to_show = []

    st.markdown("---")
    st.subheader("Three-Year Task Comparison Table")
    # Get all unique tasks across the three years
    # Filter out None/NaN tasks before sorting
    # Show all tasks for the selected years
    # Show all tasks for the three selected years, even if some are missing for a year
    tasks_in_years = filtered_df[filtered_df['Fiscal Year'].isin(years_to_show)]
    valid_tasks = tasks_in_years['TASK'] if not tasks_in_years.empty else pd.Series(dtype=str)
    valid_tasks = valid_tasks[pd.notna(valid_tasks)]
    all_tasks = sorted(valid_tasks.unique())
    # If no tasks found, try to show all tasks in the database for those years
    if not all_tasks:
        all_tasks = sorted(df_original[df_original['Fiscal Year'].isin(years_to_show)]['TASK'].dropna().unique())
    if not all_tasks:
        st.info("No tasks found for the selected years.")
    st.markdown("---")
    st.subheader("Three-Year Task Comparison Table (Editable)")
    # Build a table for st.data_editor
    columns = ["#", "PLANNER BUCKET", "TASK"]
    for year in years_to_show:
        columns += [f"{year} START", f"{year} END", f"{year} ASSIGNMENT TITLE", f"{year} PROGRESS", f"{year} SEMESTER"]
    table_rows = []
    used_ids = set(df_original['#']) if not df_original.empty and '#' in df_original.columns else set()
    next_id = int(df_original['#'].max()) + 1 if not df_original.empty and '#' in df_original.columns else 1
    for task in all_tasks:
        row = {"#": None, "PLANNER BUCKET": '', "TASK": task}
        for year in years_to_show:
            # Ensure 'Fiscal Year' is compared as int
            match = filtered_df[(filtered_df['TASK'] == task) & (filtered_df['Fiscal Year'].astype(int) == int(year))]
            if not match.empty:
                r = match.iloc[0]
                if row["#"] is None:
                    row["#"] = r['#'] if '#' in r else next_id
                    if '#' not in r:
                        while next_id in used_ids:
                            next_id += 1
                        row["#"] = next_id
                        used_ids.add(next_id)
                        next_id += 1
                row["PLANNER BUCKET"] = r['PLANNER BUCKET'] if 'PLANNER BUCKET' in r and pd.notna(r['PLANNER BUCKET']) else row["PLANNER BUCKET"]
                row[f"{year} START"] = r['START'].strftime('%Y-%m-%d') if 'START' in r and pd.notna(r['START']) else ''
                row[f"{year} END"] = r['END'].strftime('%Y-%m-%d') if 'END' in r and pd.notna(r['END']) else ''
                row[f"{year} ASSIGNMENT TITLE"] = r['ASSIGNMENT TITLE'] if 'ASSIGNMENT TITLE' in r and pd.notna(r['ASSIGNMENT TITLE']) else ''
                row[f"{year} PROGRESS"] = r['PROGRESS'] if 'PROGRESS' in r and pd.notna(r['PROGRESS']) else ''
                row[f"{year} SEMESTER"] = r['SEMESTER'] if 'SEMESTER' in r and pd.notna(r['SEMESTER']) else ''
            else:
                row[f"{year} START"] = ''
                row[f"{year} END"] = ''
                row[f"{year} ASSIGNMENT TITLE"] = ''
                row[f"{year} PROGRESS"] = ''
                row[f"{year} SEMESTER"] = ''
        if row["#"] is None:
            while next_id in used_ids:
                next_id += 1
            row["#"] = next_id
            used_ids.add(next_id)
            next_id += 1
        table_rows.append(row)
    table_df = pd.DataFrame(table_rows, columns=columns)

    edited_df = st.data_editor(
        table_df,
        column_config={
            "#": st.column_config.TextColumn(disabled=True),
            **{col: st.column_config.SelectboxColumn(options=all_buckets) for col in ["PLANNER BUCKET"]},
            **{col: st.column_config.SelectboxColumn(options=all_assignments) for col in [f"{year} ASSIGNMENT TITLE" for year in years_to_show]},
            **{col: st.column_config.SelectboxColumn(options=["NOT STARTED", "IN PROGRESS", "COMPLETE"]) for col in [f"{year} PROGRESS" for year in years_to_show]},
            **{col: st.column_config.SelectboxColumn(options=all_semesters) for col in [f"{year} SEMESTER" for year in years_to_show]},
            **{col: st.column_config.TextColumn() for col in [f"{year} START" for year in years_to_show]},
            **{col: st.column_config.TextColumn() for col in [f"{year} END" for year in years_to_show]},
        },
        num_rows="dynamic",
        use_container_width=True,
        key="three_year_table_editor"
    )
    st.caption("Enter dates in YYYY-MM-DD format for START and END columns.")
    if st.button("Save All Changes"):
        updated_df = df_original.copy()
        next_id = int(updated_df['#'].max()) + 1 if not updated_df.empty and '#' in updated_df.columns else 1

        def _parse_date(value):
            value = value if pd.notna(value) else ''
            if isinstance(value, str) and value.strip() == '':
                return pd.NaT
            return pd.to_datetime(value, errors='coerce')

        for idx, row in edited_df.iterrows():
            row_id = row["#"]
            task = row["TASK"]
            for year in years_to_show:
                mask = (updated_df['#'] == row_id) & (updated_df['TASK'] == task) & (updated_df['Fiscal Year'] == year)
                if updated_df[mask].empty:
                    # Auto-generate # if missing
                    if pd.isna(row_id) or row_id == '' or row_id is None:
                        row_id = next_id
                        next_id += 1
                    new_row = {col: row.get(col, None) for col in updated_df.columns}
                    new_row['#'] = row_id
                    new_row['TASK'] = task
                    new_row['PLANNER BUCKET'] = row["PLANNER BUCKET"]
                    new_row['Fiscal Year'] = year
                    new_row['START'] = _parse_date(row[f"{year} START"])
                    new_row['END'] = _parse_date(row[f"{year} END"])
                    new_row['ASSIGNMENT TITLE'] = row[f"{year} ASSIGNMENT TITLE"]
                    new_row['PROGRESS'] = row[f"{year} PROGRESS"]
                    new_row['SEMESTER'] = row[f"{year} SEMESTER"]
                    updated_df = pd.concat([updated_df, pd.DataFrame([new_row])], ignore_index=True)
                else:
                    updated_df.loc[mask, 'PLANNER BUCKET'] = row["PLANNER BUCKET"]
                    updated_df.loc[mask, 'TASK'] = task
                    updated_df.loc[mask, 'START'] = _parse_date(row[f"{year} START"])
                    updated_df.loc[mask, 'END'] = _parse_date(row[f"{year} END"])
                    updated_df.loc[mask, 'ASSIGNMENT TITLE'] = row[f"{year} ASSIGNMENT TITLE"]
                    updated_df.loc[mask, 'PROGRESS'] = row[f"{year} PROGRESS"]
                    updated_df.loc[mask, 'SEMESTER'] = row[f"{year} SEMESTER"]
        import data_manager
        user_email = st.session_state.get('logged_in_user', 'system')
        data_manager.save_and_log_changes(df_original, updated_df, user_email, source_page="Three-Year Task View")
        st.success("All changes saved!")
else:
    st.warning("Could not load tasks data.")
