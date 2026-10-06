import math
import numbers
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st
from sqlalchemy import inspect, text

import data_manager


if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()

if st.session_state.user_data.get('role') != 'admin':
    st.error("You do not have permission to view this page.")
    st.stop()


def _normalize(value):
    if pd.isna(value):
        return ""
    normalized = str(value).strip().casefold()
    return "" if normalized in {"", "none", "nan", "null", "n/a"} else normalized


def _normalize_id(value):
    if pd.isna(value):
        return ""
    if isinstance(value, numbers.Integral):
        return str(int(value))
    if isinstance(value, numbers.Real) and math.isfinite(value) and float(value).is_integer():
        return str(int(value))
    normalized = str(value).strip()
    return "" if normalized.casefold() in {"", "none", "nan", "null", "n/a"} else normalized


def _semester_from_start(value):
    start_date = pd.to_datetime(value, errors="coerce")
    if pd.isna(start_date) or start_date.year <= 1901:
        return ""

    month_day = (start_date.month, start_date.day)
    if (8, 20) <= month_day <= (12, 20):
        return "Fall"
    if (1, 5) <= month_day < (5, 15):
        return "Spring"
    if (5, 15) <= month_day <= (8, 7):
        return "Summer"
    return ""


st.title("Task Integrity Audit")
st.caption("Read-only report. No task, comment, or database records are changed.")

try:
    with data_manager.engine.connect() as connection:
        if data_manager.engine.dialect.name == "postgresql":
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        elif data_manager.engine.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA query_only=ON")

        database_inspector = inspect(connection)
        if not database_inspector.has_table("tasks"):
            st.error("The configured database does not contain a tasks table.")
            st.stop()

        tasks_df = pd.read_sql_query(text("SELECT * FROM tasks"), connection)
        comments_df = None
        if database_inspector.has_table("comments"):
            comments_df = pd.read_sql_query(text("SELECT task_id FROM comments"), connection)

        primary_key = database_inspector.get_pk_constraint("tasks").get("constrained_columns") or []
        unique_constraints = [
            item.get("column_names") or []
            for item in database_inspector.get_unique_constraints("tasks")
        ]
        unique_indexes = [
            item.get("column_names") or []
            for item in database_inspector.get_indexes("tasks")
            if item.get("unique")
        ]
except Exception as error:
    st.error("Unable to read the configured task database. Check the Streamlit app logs for details.")
    st.stop()


series_col = "#"
key_cols = ["TASK", "PLANNER BUCKET", "SEMESTER", "Fiscal Year"]
missing_columns = [column for column in [series_col, *key_cols] if column not in tasks_df.columns]
if missing_columns:
    st.error(f"The task table is missing expected columns: {', '.join(missing_columns)}")
    st.stop()

normalized_ids = tasks_df[series_col].map(_normalize_id)
id_counts = Counter(value for value in normalized_ids if value)
reused_ids = {value for value, count in id_counts.items() if count > 1}

years_by_id = defaultdict(set)
id_year_counts = Counter()
for series_id, fiscal_year in zip(normalized_ids, tasks_df["Fiscal Year"]):
    if series_id:
        years_by_id[series_id].add(_normalize(fiscal_year))
        id_year_counts[(series_id, _normalize(fiscal_year))] += 1

cross_year_series = sum(len(years) > 1 for years in years_by_id.values())
same_year_id_groups = {
    pair for pair, count in id_year_counts.items() if pair[0] and pair[1] and count > 1
}

normalized_keys = tasks_df[key_cols].apply(lambda column: column.map(_normalize))
complete_key_mask = normalized_keys.ne("").all(axis=1)
duplicate_key_mask = pd.Series(False, index=tasks_df.index)
duplicate_key_groups = 0
if complete_key_mask.any():
    complete_keys = normalized_keys.loc[complete_key_mask]
    duplicate_key_mask.loc[complete_key_mask] = complete_keys.duplicated(keep=False)
    duplicate_key_groups = int(
        complete_keys.loc[complete_keys.duplicated(keep=False)].drop_duplicates().shape[0]
    )

projected_keys = normalized_keys.copy()
if "START" in tasks_df.columns:
    proposed_semesters = tasks_df["START"].map(_semester_from_start)
else:
    proposed_semesters = pd.Series("", index=tasks_df.index)

missing_semester_mask = normalized_keys["SEMESTER"].eq("")
semester_inference_mask = missing_semester_mask & proposed_semesters.ne("")
projected_keys.loc[semester_inference_mask, "SEMESTER"] = proposed_semesters.loc[
    semester_inference_mask
].map(_normalize)
projected_complete_mask = projected_keys.ne("").all(axis=1)
projected_duplicate_mask = pd.Series(False, index=tasks_df.index)
projected_duplicate_groups = 0
projected_duplicate_rows = 0
if projected_complete_mask.any():
    projected_complete_keys = projected_keys.loc[projected_complete_mask]
    projected_duplicate_mask.loc[projected_complete_mask] = projected_complete_keys.duplicated(keep=False)
    projected_duplicate_rows = int(projected_duplicate_mask.sum())
    projected_duplicate_groups = int(
        projected_complete_keys.loc[projected_complete_keys.duplicated(keep=False)]
        .drop_duplicates()
        .shape[0]
    )

semester_key_conflicts = semester_inference_mask & projected_duplicate_mask
valid_start_mask = tasks_df["START"].map(
    lambda value: pd.notna(pd.to_datetime(value, errors="coerce"))
    and pd.to_datetime(value, errors="coerce").year > 1901
) if "START" in tasks_df.columns else pd.Series(False, index=tasks_df.index)
semester_start_gaps = missing_semester_mask & valid_start_mask & proposed_semesters.eq("")
semester_no_valid_start = missing_semester_mask & ~valid_start_mask
existing_semester_conflicts = (
    ~missing_semester_mask
    & proposed_semesters.ne("")
    & normalized_keys["SEMESTER"].ne(proposed_semesters.map(_normalize))
)

missing_by_field = {
    column: int(normalized_keys[column].eq("").sum())
    for column in key_cols
}
missing_id_rows = int(normalized_ids.eq("").sum())

comments_on_reused_ids = 0
if comments_df is not None and "task_id" in comments_df.columns and reused_ids:
    comments_on_reused_ids = int(
        comments_df["task_id"].map(_normalize_id).isin(reused_ids).sum()
    )

st.subheader("Summary")
metric_columns = st.columns(4)
metric_columns[0].metric("Task rows", len(tasks_df))
metric_columns[1].metric("Series numbers reused across years", cross_year_series)
metric_columns[2].metric("Number + year collisions", len(same_year_id_groups))
metric_columns[3].metric("Complete duplicate occurrence keys", duplicate_key_groups)

st.subheader("Semester Projection")
st.caption(
    "Date windows are suggestions, not authoritative semester assignments. A June 10 start can be Fall preparation, "
    "for example bookstore charging opening for the upcoming term. Confirm the task's intended academic period. "
    "The stored Fiscal Year is preserved; it is not derived from START because the task may begin before its FY."
)
projection_columns = st.columns(4)
projection_columns[0].metric("Date-window suggestions to review", int(semester_inference_mask.sum()))
projection_columns[1].metric("Held for duplicate-key review", int(semester_key_conflicts.sum()))
projection_columns[2].metric("Start date in a term gap", int(semester_start_gaps.sum()))
projection_columns[3].metric("No valid start date", int(semester_no_valid_start.sum()))
st.write(
    f"If every date-window suggestion were accepted, projected complete-key conflicts would be "
    f"{projected_duplicate_groups} groups / "
    f"{projected_duplicate_rows} rows. Existing semester values that disagree with START: "
    f"{int(existing_semester_conflicts.sum())}. Missing Fiscal Year values are left for review: "
    f"{missing_by_field['Fiscal Year']}."
)

if semester_inference_mask.any():
    projection_df = tasks_df.loc[
        semester_inference_mask,
        [column for column in ["#", "Fiscal Year", "SEMESTER", "TASK", "PLANNER BUCKET", "START"] if column in tasks_df.columns],
    ].copy()
    projection_df["Proposed Semester"] = proposed_semesters.loc[semester_inference_mask]
    projection_df["Projection Status"] = "Review task meaning before assigning semester"
    projection_df.loc[semester_key_conflicts, "Projection Status"] = "Review: conflicts if date suggestion is accepted"
    incomplete_projection = semester_inference_mask & ~projected_complete_mask
    projection_df.loc[incomplete_projection, "Projection Status"] = "Hold: missing identity field"
    st.dataframe(projection_df, hide_index=True, use_container_width=True)
    st.download_button(
        "Download semester projection CSV",
        data=projection_df.to_csv(index=False).encode("utf-8"),
        file_name="semester_projection_review.csv",
        mime="text/csv",
    )

st.write("Missing or blank proposed identity fields:")
st.dataframe(
    pd.DataFrame(
        [{"Field": field, "Rows missing": count} for field, count in missing_by_field.items()]
        + [{"Field": "#", "Rows missing": missing_id_rows}]
    ),
    hide_index=True,
    use_container_width=True,
)

st.write("Task table constraints:")
st.json({
    "primary_key_columns": primary_key,
    "unique_constraints": unique_constraints,
    "unique_indexes": unique_indexes,
})

st.write(f"Comments attached to a reused number: {comments_on_reused_ids}")
st.caption(
    "Numbers reused across fiscal years may represent recurring series. Number + year collisions "
    "need review. Complete occurrence keys use Task, Planner Bucket, Semester, and Fiscal Year; "
    "rows missing any of those fields are excluded from that duplicate count."
)
if "Delete" in tasks_df.columns:
    st.warning("The stored tasks table includes a `Delete` column. It is reported here but not removed.")

issue_mask = normalized_ids.isin(reused_ids) | ~complete_key_mask | duplicate_key_mask
detail_columns = [
    column for column in ["#", "Fiscal Year", "SEMESTER", "TASK", "PLANNER BUCKET", "START", "END"]
    if column in tasks_df.columns
]
issues_df = tasks_df.loc[issue_mask, detail_columns].copy()
if not issues_df.empty:
    st.subheader("Rows to review")
    st.dataframe(issues_df, hide_index=True, use_container_width=True)
    st.download_button(
        "Download review CSV",
        data=issues_df.to_csv(index=False).encode("utf-8"),
        file_name="task_integrity_review.csv",
        mime="text/csv",
    )
else:
    st.success("No reused numbers, incomplete proposed keys, or duplicate occurrence keys found.")