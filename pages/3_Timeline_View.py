# File: pages/3_Timeline_View.py
import streamlit as st
import pandas as pd
from datetime import datetime
import data_manager

st.set_page_config(page_title="Timeline View", layout="wide")
st.title("🗓️ Timeline View")

df = data_manager.load_data()

if df is not None:
    today = pd.to_datetime("today").normalize()
    num_days = st.number_input("Enter number of days to look forward/back:", min_value=1, value=30)
    
    future_date = today + pd.Timedelta(days=num_days)
    past_date = today - pd.Timedelta(days=num_days)
    
    upcoming_tasks = df[(df['START'] >= today) & (df['START'] <= future_date)].sort_values(by='START')
    recent_tasks = df[(df['START'] < today) & (df['START'] >= past_date)].sort_values(by='START', ascending=False)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Starting in Next {num_days} Days")
        if not upcoming_tasks.empty:
            for index, row in upcoming_tasks.iterrows():
                # CORRECTED TYPO IN THE LINE BELOW
                with st.expander(f"{row['START'].strftime('%m-%d-%Y, %A')} - {row['TASK']}"):
                    st.markdown(f"**Assigned To:** {row['ASSIGNMENT TITLE']}")
                    st.markdown(f"**Planner Bucket:** {row['PLANNER BUCKET']}")
                    st.markdown(f"**Audience:** {row['AUDIENCE']}")
        else:
            st.info("No tasks starting in this period.")
            
    with col2:
        st.subheader(f"Started in Past {num_days} Days")
        if not recent_tasks.empty:
            for index, row in recent_tasks.iterrows():
                # CORRECTED TYPO IN THE LINE BELOW
                with st.expander(f"{row['START'].strftime('%m-%d-%Y, %A')} - {row['TASK']}"):
                    st.markdown(f"**Assigned To:** {row['ASSIGNMENT TITLE']}")
                    st.markdown(f"**Planner Bucket:** {row['PLANNER BUCKET']}")
                    st.markdown(f"**Audience:** {row['AUDIENCE']}")
        else:
            st.info("No tasks started in this period.")
else:
    st.warning("Could not load data.")