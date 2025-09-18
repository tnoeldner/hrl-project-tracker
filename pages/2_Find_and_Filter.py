import streamlit as st
import pandas as pd
import data_manager

st.set_page_config(page_title="Find & Filter", layout="wide")
st.title("🔍 Find and Filter Tasks")

df_original = data_manager.load_data()

if df_original is not None:
    col1, col2 = st.columns(2)
    with col1:
        bucket_options = ['All'] + sorted(df_original['PLANNER BUCKET'].unique().tolist())
        st.selectbox("Filter by Planner Bucket", options=bucket_options, key="find_bucket_filter")
    with col2:
        year_options = ['All'] + sorted(df_original['Fiscal Year'].unique().tolist())
        st.selectbox("Filter by Fiscal Year", options=year_options, key="find_year_filter")

    filtered_df = df_original
    if st.session_state.find_bucket_filter != 'All':
        filtered_df = filtered_df[filtered_df['PLANNER BUCKET'] == st.session_state.find_bucket_filter]
    if st.session_state.find_year_filter != 'All':
        filtered_df = filtered_df[filtered_df['Fiscal Year'] == st.session_state.find_year_filter]

    st.markdown("---")
    st.info("You can edit data in the table below. Click 'Save Changes' to update the master file.")
    
    edited_df = st.data_editor(filtered_df, hide_index=True, column_config={
        "PROGRESS": st.column_config.SelectboxColumn("Progress", options=["NOT STARTED", "IN PROGRESS", "COMPLETE"], required=True)
    })
    
    if st.button("Save Changes"):
        df_updated = df_original.copy()
        df_updated.update(edited_df)
        if data_manager.save_and_log_changes(df_original, df_updated):
            st.success("Changes saved and logged successfully!")
            st.rerun()
else:
    st.warning("Could not load data.")