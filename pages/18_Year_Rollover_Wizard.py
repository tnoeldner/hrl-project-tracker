# File: pages/18_Year_Rollover_Wizard.py
import streamlit as st
import pandas as pd
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.title("🔄 Year Rollover Wizard")
st.write("Use this wizard to carry tasks forward from one fiscal year into the next.")

df_original = data_manager.load_table('tasks')

if df_original is None:
    st.warning("Could not load task data.")
    st.stop()

df_original['Fiscal Year'] = pd.to_numeric(df_original['Fiscal Year'], errors='coerce')
available_years = sorted(df_original['Fiscal Year'].dropna().unique().tolist())
available_years_int = [int(y) for y in available_years]

# --- SESSION STATE INIT ---
if 'rollover_step' not in st.session_state:
    st.session_state.rollover_step = 1
if 'rollover_source_year' not in st.session_state:
    st.session_state.rollover_source_year = None
if 'rollover_selected_ids' not in st.session_state:
    st.session_state.rollover_selected_ids = []
if 'rollover_shift_days' not in st.session_state:
    st.session_state.rollover_shift_days = 364

# --- PROGRESS INDICATOR ---
step_labels = ["1 · Choose Source Year", "2 · Select Tasks", "3 · Set Date Shift", "4 · Review & Save"]
step_cols = st.columns(4)
for i, label in enumerate(step_labels):
    with step_cols[i]:
        if st.session_state.rollover_step == i + 1:
            st.markdown(f"**:blue[{label}]**")
        elif st.session_state.rollover_step > i + 1:
            st.markdown(f"~~{label}~~ ✅")
        else:
            st.markdown(f":gray[{label}]")
st.markdown("---")

# ============================================================
# STEP 1 — Choose source fiscal year
# ============================================================
if st.session_state.rollover_step == 1:
    st.subheader("Step 1: Choose the Source Fiscal Year")
    st.write("Select the fiscal year you want to copy tasks *from*. The wizard will carry them forward into the next fiscal year.")

    if not available_years_int:
        st.error("No fiscal years found in the task data.")
        st.stop()

    default_idx = len(available_years_int) - 1
    source_year = st.selectbox(
        "Source Fiscal Year",
        options=available_years_int,
        index=default_idx,
        format_func=lambda x: data_manager.format_fy(x),
        key="step1_source_year"
    )
    target_year = source_year + 1
    st.info(f"Tasks will be copied from **{data_manager.format_fy(source_year)}** → **{data_manager.format_fy(target_year)}**")

    source_count = len(df_original[df_original['Fiscal Year'] == source_year])
    st.write(f"Tasks available in {data_manager.format_fy(source_year)}: **{source_count}**")

    if st.button("Next: Select Tasks →", disabled=(source_count == 0)):
        st.session_state.rollover_source_year = source_year
        st.session_state.rollover_step = 2
        st.rerun()

# ============================================================
# STEP 2 — Select which tasks to carry forward
# ============================================================
elif st.session_state.rollover_step == 2:
    source_year = st.session_state.rollover_source_year
    target_year = source_year + 1
    st.subheader(f"Step 2: Select Tasks to Roll Over to {data_manager.format_fy(target_year)}")

    source_df = df_original[df_original['Fiscal Year'] == source_year].copy()

    # Check which tasks already exist in the target year
    target_df = df_original[df_original['Fiscal Year'] == target_year]
    existing_tasks_in_target = set(target_df['TASK'].dropna().unique())

    # Add a "Select" checkbox column
    source_df = source_df.reset_index(drop=True)
    source_df['Roll Over?'] = ~source_df['TASK'].isin(existing_tasks_in_target)

    st.write("Tasks already present in the target year are unchecked by default. You can check/uncheck any row.")

    display_cols = ['Roll Over?', '#', 'PLANNER BUCKET', 'ASSIGNMENT TITLE', 'TASK', 'SEMESTER', 'PROGRESS', 'START', 'END']
    available_cols = [c for c in display_cols if c in source_df.columns]

    edited = st.data_editor(
        source_df[available_cols],
        hide_index=True,
        key="step2_task_selector",
        column_config={
            "Roll Over?": st.column_config.CheckboxColumn(required=True),
            "#": st.column_config.NumberColumn(disabled=True),
            "PLANNER BUCKET": st.column_config.TextColumn(disabled=True),
            "ASSIGNMENT TITLE": st.column_config.TextColumn(disabled=True),
            "TASK": st.column_config.TextColumn(disabled=True),
            "SEMESTER": st.column_config.TextColumn(disabled=True),
            "PROGRESS": st.column_config.TextColumn(disabled=True),
            "START": st.column_config.DateColumn("Start Date", format="MM-DD-YYYY", disabled=True),
            "END": st.column_config.DateColumn("End Date", format="MM-DD-YYYY", disabled=True),
        }
    )

    selected_count = edited['Roll Over?'].sum()
    st.write(f"**{selected_count}** task(s) selected to roll over.")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Back"):
            st.session_state.rollover_step = 1
            st.rerun()
    with col_next:
        if st.button("Next: Set Date Shift →", disabled=(selected_count == 0)):
            selected_ids = source_df.loc[edited['Roll Over?'] == True, '#'].tolist()
            st.session_state.rollover_selected_ids = selected_ids
            st.session_state.rollover_step = 3
            st.rerun()

# ============================================================
# STEP 3 — Configure date shifting
# ============================================================
elif st.session_state.rollover_step == 3:
    source_year = st.session_state.rollover_source_year
    target_year = source_year + 1
    count = len(st.session_state.rollover_selected_ids)

    st.subheader("Step 3: Configure Date Shifting")
    st.write(f"You selected **{count}** task(s). Choose how to adjust their dates for {data_manager.format_fy(target_year)}.")

    shift_option = st.radio(
        "Date shift method:",
        options=["Shift by days (recommended)", "Shift by exact calendar year (+1 year)", "Clear dates (set to unscheduled)"],
        key="step3_shift_option"
    )

    days_shift = 364
    if shift_option == "Shift by days (recommended)":
        days_shift = st.number_input(
            "Days to shift forward:",
            min_value=1,
            value=364,
            help="364 days keeps weekdays aligned. 365 shifts by one calendar year exactly.",
            key="step3_days_shift"
        )
        st.caption("Tip: 364 days (52 weeks) keeps tasks on the same day of the week. Use 365 for exact calendar year alignment.")
    elif shift_option == "Shift by exact calendar year (+1 year)":
        st.info("Dates will shift exactly one calendar year forward (e.g. March 15 → March 15 next year). Leap year dates will shift to Feb 28.")
        days_shift = None  # handled specially
    else:
        st.warning("Tasks will be copied with no dates set (START and END will be blank/unscheduled).")
        days_shift = -1  # sentinel for "clear"

    st.session_state.rollover_shift_days = days_shift
    st.session_state.rollover_shift_option = shift_option

    reset_progress = st.checkbox(
        "Reset progress to 'NOT STARTED' for all rolled-over tasks",
        value=True,
        key="step3_reset_progress"
    )
    st.session_state.rollover_reset_progress = reset_progress

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Back"):
            st.session_state.rollover_step = 2
            st.rerun()
    with col_next:
        if st.button("Next: Review & Save →"):
            st.session_state.rollover_step = 4
            st.rerun()

# ============================================================
# STEP 4 — Review and save
# ============================================================
elif st.session_state.rollover_step == 4:
    source_year = st.session_state.rollover_source_year
    target_year = source_year + 1
    selected_ids = st.session_state.rollover_selected_ids
    shift_option = st.session_state.get('rollover_shift_option', 'Shift by days (recommended)')
    days_shift = st.session_state.rollover_shift_days
    reset_progress = st.session_state.get('rollover_reset_progress', True)

    source_tasks = df_original[df_original['#'].isin(selected_ids)].copy()

    # Build the new rows
    def _shift_date(dt, option, days):
        if pd.isna(dt):
            return pd.NaT
        try:
            dt = pd.Timestamp(dt)
            if dt.year <= 1901:
                return pd.NaT
        except Exception:
            return pd.NaT
        if option == "Clear dates (set to unscheduled)":
            return pd.NaT
        elif option == "Shift by exact calendar year (+1 year)":
            try:
                return dt.replace(year=dt.year + 1)
            except ValueError:
                return dt.replace(year=dt.year + 1, day=28)
        else:
            return dt + pd.Timedelta(days=int(days))

    new_rows = source_tasks.copy()
    new_rows['Fiscal Year'] = target_year
    new_rows['START'] = new_rows['START'].apply(lambda d: _shift_date(d, shift_option, days_shift))
    new_rows['END'] = new_rows['END'].apply(lambda d: _shift_date(d, shift_option, days_shift))

    if reset_progress:
        new_rows['PROGRESS'] = 'NOT STARTED'

    # Assign new IDs
    max_id = int(df_original['#'].max()) if not df_original.empty else 0
    new_rows['#'] = range(max_id + 1, max_id + 1 + len(new_rows))
    new_rows = new_rows.reset_index(drop=True)

    st.subheader(f"Step 4: Review — {len(new_rows)} Task(s) to Add to {data_manager.format_fy(target_year)}")
    preview_cols = ['PLANNER BUCKET', 'ASSIGNMENT TITLE', 'TASK', 'SEMESTER', 'PROGRESS', 'START', 'END']
    available_preview = [c for c in preview_cols if c in new_rows.columns]
    st.dataframe(new_rows[available_preview], hide_index=True)

    st.markdown("---")
    col_back, col_save = st.columns(2)
    with col_back:
        if st.button("← Back"):
            st.session_state.rollover_step = 3
            st.rerun()
    with col_save:
        if st.button(f"✅ Save {len(new_rows)} Tasks to {data_manager.format_fy(target_year)}", type="primary"):
            df_updated = pd.concat([df_original, new_rows], ignore_index=True)
            user_email = st.session_state.get('logged_in_user', 'system')
            if data_manager.save_and_log_changes(df_original, df_updated, user_email, source_page="Year Rollover Wizard"):
                st.success(f"Successfully added {len(new_rows)} task(s) to {data_manager.format_fy(target_year)}!")
                st.balloons()
                # Reset wizard
                for key in ['rollover_step', 'rollover_source_year', 'rollover_selected_ids',
                            'rollover_shift_days', 'rollover_shift_option', 'rollover_reset_progress']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            else:
                st.error("Failed to save changes.")
