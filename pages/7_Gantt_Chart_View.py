# File: pages/7_Gantt_Chart_View.py
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import data_manager
import plotly.express as px

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

# (The rest of the file remains the same)
# ...
st.set_page_config(page_title="Gantt Chart", layout="wide")
st.title("📊 Interactive Gantt Chart View")

df = data_manager.load_data()

if df is not None:
    st.info("Use the filters to set your view. You can also use your mouse to zoom and pan the chart.")

    # --- Filter ---
    year_options = ['All'] + sorted(df['Fiscal Year'].unique().tolist())
    selected_year = st.selectbox(
        "Select Fiscal Year",
        options=year_options
    )

    if selected_year == 'All':
        chart_df = df
    else:
        chart_df = df[df['Fiscal Year'] == selected_year]
    
    chart_df = chart_df[chart_df['END'].dt.year > 1901].dropna(subset=['START', 'END'])

    st.markdown("---")

    if not chart_df.empty:
        # --- Date Pickers for Date Range ---
        min_date = chart_df['START'].min().to_pydatetime()
        max_date = chart_df['END'].max().to_pydatetime()

        # NEW: Button to set date pickers to today
        if st.button("Set Range to Today"):
            st.session_state.start_date_picker = datetime.now().date()
            st.session_state.end_date_picker = datetime.now().date()
            st.rerun() # Rerun to apply the new date values

        col1, col2 = st.columns(2)
        with col1:
            start_range = st.date_input("Select Start Date:", value=min_date, min_value=min_date, max_value=max_date, key="start_date_picker")
        with col2:
            end_range = st.date_input("Select End Date:", value=max_date, min_value=min_date, max_value=max_date, key="end_date_picker")
            
        # Adjust for single-day tasks
        gantt_df = chart_df.copy()
        mask = gantt_df['START'] == gantt_df['END']
        gantt_df.loc[mask, 'END'] = gantt_df.loc[mask, 'END'] + pd.Timedelta(hours=12)
        
        # Create the Gantt chart
        fig = px.timeline(
            gantt_df,
            x_start="START",
            x_end="END",
            y="PLANNER BUCKET",
            color="PLANNER BUCKET",
            hover_name="TASK",
            title=f"Project Timeline for FY {selected_year}"
        )

        # Improve the layout and set the initial zoom from the date pickers
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            height=800,
            xaxis_title="Date",
            yaxis_title="Planner Bucket",
            xaxis_range=[start_range, end_range]
        )
        
        fig.update_xaxes(
            tickformat="%b %d\n%Y",
            showgrid=True
        )

        # Conditionally add daily ticks for small date ranges
        # Convert date objects to datetime objects for subtraction
        date_difference = datetime.combine(end_range, datetime.min.time()) - datetime.combine(start_range, datetime.min.time())
        if date_difference.days < 32:
            fig.update_xaxes(dtick=86400000) # Force a tick every day

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No valid tasks to display for the selected Fiscal Year ({selected_year}).")

else:
    st.warning("Could not load data.")