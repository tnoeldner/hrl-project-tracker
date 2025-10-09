import streamlit as st
import pandas as pd
import json
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
user_role = st.session_state.user_data.get('role') if 'user_data' in st.session_state else None
if user_role != 'admin':
    st.error("You do not have permission to view this page. This page is for administrators only.")
    st.stop()

st.set_page_config(page_title="Admin — Presets Overview", layout="wide")
st.title("🔍 Presets Overview (Read-only)")
st.markdown("This page provides a read-only overview of saved filter presets and related usage statistics.")

# Load tables
presets_df = data_manager.load_table('filter_presets')
users_df = data_manager.load_table('users')
tasks_df = data_manager.load_table('tasks')

if presets_df is None or presets_df.empty:
    st.info("No saved filter presets found in the database.")
else:
    # Normalize created_at
    if 'created_at' in presets_df.columns:
        try:
            presets_df['created_at_dt'] = pd.to_datetime(presets_df['created_at'], errors='coerce')
        except Exception:
            presets_df['created_at_dt'] = None
    else:
        presets_df['created_at_dt'] = None

    # Basic metrics
    st.subheader("Summary Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total presets", len(presets_df))
    with col2:
        unique_users = presets_df['user_email'].nunique()
        st.metric("Users with presets", unique_users)
    with col3:
        avg_per_user = (len(presets_df) / unique_users) if unique_users else 0
        st.metric("Avg presets / user", f"{avg_per_user:.2f}")

    st.markdown("---")

    # Presets per user
    st.subheader("Presets per user")
    presets_by_user = presets_df.groupby('user_email').size().sort_values(ascending=False).rename('preset_count').reset_index()
    st.dataframe(presets_by_user, use_container_width=True)
    st.bar_chart(presets_by_user.set_index('user_email')['preset_count'])

    st.markdown("---")

    # Recent presets
    st.subheader("Most recent presets")
    recent = presets_df.copy()
    if 'created_at_dt' in recent.columns:
        recent = recent.sort_values(by='created_at_dt', ascending=False)
    else:
        recent = recent.sort_values(by='preset_id', ascending=False)

    show_count = st.number_input("Show how many recent presets?", min_value=1, max_value=100, value=10, step=1)
    st.dataframe(recent.head(show_count).assign(years_display=lambda df: df['years'].fillna('[]')).loc[:, ['preset_id','user_email','preset_name','years_display','buckets','created_at']].rename(columns={'years_display':'years'}), use_container_width=True)

    st.markdown("---")

    # Search and detail viewer
    st.subheader("Search & Inspect")
    search_user = st.text_input("Filter by user email (partial)")
    search_name = st.text_input("Filter by preset name (partial)")

    filtered = presets_df.copy()
    if search_user:
        filtered = filtered[filtered['user_email'].str.contains(search_user, case=False, na=False)]
    if search_name:
        filtered = filtered[filtered['preset_name'].str.contains(search_name, case=False, na=False)]

    st.write(f"{len(filtered)} presets match the filters")
    st.dataframe(filtered.sort_values(by='created_at_dt', ascending=False).loc[:, ['preset_id','user_email','preset_name','years','buckets','created_at']], use_container_width=True)

    st.markdown("---")
    st.subheader("Preset detail")
    preset_ids = filtered['preset_id'].astype(str).tolist()
    if preset_ids:
        chosen = st.selectbox("Choose preset_id to inspect", options=['--'] + preset_ids)
        if chosen and chosen != '--':
            row = filtered[filtered['preset_id'].astype(str) == chosen].iloc[0]
            st.markdown(f"**Preset:** {row['preset_name']} — **User:** {row['user_email']}")
            st.write("Created:", row.get('created_at'))
            try:
                yrs = json.loads(row.get('years') or '[]')
            except Exception:
                yrs = []
            try:
                bks = json.loads(row.get('buckets') or '[]')
            except Exception:
                bks = []
            st.write("Years:", yrs)
            st.write("Buckets:", bks)
    else:
        st.info("No presets match the current search filters.")

    st.markdown("---")
    st.subheader("Export")
    if st.button("Download presets as CSV"):
        csv = presets_df.to_csv(index=False)
        st.download_button("Download CSV", data=csv, file_name="filter_presets_export.csv", mime='text/csv')

# Additional related info: quick task counts per bucket/year
st.markdown("---")
st.subheader("Related Task Metrics")
if tasks_df is not None and not tasks_df.empty:
    tasks_df['Fiscal Year'] = pd.to_numeric(tasks_df.get('Fiscal Year', pd.Series()), errors='coerce')
    counts_by_year = tasks_df.groupby('Fiscal Year').size().sort_index()
    counts_by_bucket = tasks_df.groupby('PLANNER BUCKET').size().sort_values(ascending=False).head(20)

    c1, c2 = st.columns(2)
    with c1:
        st.write("Tasks by Fiscal Year")
        st.bar_chart(counts_by_year)
    with c2:
        st.write("Top Planner Buckets (by task count)")
        st.bar_chart(counts_by_bucket)
else:
    st.info("No tasks table available to compute related metrics.")
