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
    valid_tasks = filtered_df[filtered_df['Fiscal Year'].isin(years_to_show)]['TASK']
    valid_tasks = valid_tasks[pd.notna(valid_tasks)]
    all_tasks = sorted(valid_tasks.unique())
    st.markdown("---")
    st.subheader("Three-Year Task Comparison Table (Editable)")
    # Build a table for st.data_editor
    columns = ["PLANNER BUCKET", "TASK"]
    for year in years_to_show:
        columns += [f"{year} START", f"{year} END", f"{year} ASSIGNMENT TITLE", f"{year} PROGRESS", f"{year} SEMESTER"]
    table_rows = []
    for task in all_tasks:
        first_row = filtered_df[filtered_df['TASK'] == task].iloc[0] if not filtered_df[filtered_df['TASK'] == task].empty else None
        planner_bucket = first_row['PLANNER BUCKET'] if first_row is not None and 'PLANNER BUCKET' in first_row else ''
        row = {"PLANNER BUCKET": planner_bucket, "TASK": task}
        for year in years_to_show:
            match = filtered_df[(filtered_df['TASK'] == task) & (filtered_df['Fiscal Year'] == year)]
            if not match.empty:
                r = match.iloc[0]
                row[f"{year} START"] = r['START'].date() if pd.notna(r['START']) else pd.Timestamp.today().date()
                row[f"{year} END"] = r['END'].date() if pd.notna(r['END']) else pd.Timestamp.today().date()
                row[f"{year} ASSIGNMENT TITLE"] = r['ASSIGNMENT TITLE'] if 'ASSIGNMENT TITLE' in r else ''
                row[f"{year} PROGRESS"] = r['PROGRESS'] if 'PROGRESS' in r else ''
                row[f"{year} SEMESTER"] = r['SEMESTER'] if 'SEMESTER' in r else ''
            else:
                row[f"{year} START"] = pd.Timestamp.today().date()
                row[f"{year} END"] = pd.Timestamp.today().date()
                row[f"{year} ASSIGNMENT TITLE"] = ''
                row[f"{year} PROGRESS"] = ''
                row[f"{year} SEMESTER"] = ''
        table_rows.append(row)
    table_df = pd.DataFrame(table_rows, columns=columns)

    edited_df = st.data_editor(
        table_df,
        column_config={
            **{col: st.column_config.SelectboxColumn(options=all_buckets) for col in ["PLANNER BUCKET"]},
            **{col: st.column_config.SelectboxColumn(options=all_assignments) for col in [f"{year} ASSIGNMENT TITLE" for year in years_to_show]},
            **{col: st.column_config.SelectboxColumn(options=["NOT STARTED", "IN PROGRESS", "COMPLETE"]) for col in [f"{year} PROGRESS" for year in years_to_show]},
            **{col: st.column_config.SelectboxColumn(options=all_semesters) for col in [f"{year} SEMESTER" for year in years_to_show]},
        },
        num_rows="dynamic",
        use_container_width=True,
        key="three_year_table_editor"
    )

    if st.button("Save All Changes"):
        updated_df = df_original.copy()
        for idx, row in edited_df.iterrows():
            task = row["TASK"]
            updated_df.loc[updated_df['TASK'] == task, 'PLANNER BUCKET'] = row["PLANNER BUCKET"]
            updated_df.loc[updated_df['TASK'] == task, 'TASK'] = row["TASK"]
            for year in years_to_show:
                mask = (updated_df['TASK'] == task) & (updated_df['Fiscal Year'] == year)
                updated_df.loc[mask, 'START'] = row[f"{year} START"]
                updated_df.loc[mask, 'END'] = row[f"{year} END"]
                updated_df.loc[mask, 'ASSIGNMENT TITLE'] = row[f"{year} ASSIGNMENT TITLE"]
                updated_df.loc[mask, 'PROGRESS'] = row[f"{year} PROGRESS"]
                updated_df.loc[mask, 'SEMESTER'] = row[f"{year} SEMESTER"]
        import data_manager
        user_email = st.session_state.get('logged_in_user', 'system')
        data_manager.save_and_log_changes(df_original, updated_df, user_email, source_page="Three-Year Task View")
        st.success("All changes saved!")
else:
    st.warning("Could not load tasks data.")
