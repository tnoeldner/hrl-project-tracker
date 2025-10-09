# File: pages/7_Gantt_Chart_View.py
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import data_manager
import plotly.express as px
import io

try:
    import kaleido  # noqa: F401
    _KALEIDO_AVAILABLE = True
except Exception:
    _KALEIDO_AVAILABLE = False

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

# (The rest of the file remains the same)
# ...
st.set_page_config(page_title="Gantt Chart", layout="wide")
st.title("📊 Interactive Gantt Chart View")

df = data_manager.load_table('tasks')

if df is not None:
    st.info("Use the filters to set your view. You can also use your mouse to zoom and pan the chart.")

    # --- Filter ---
    year_options = ['All'] + sorted(df['Fiscal Year'].unique().tolist())
    selected_year = st.selectbox(
        "Select Fiscal Year",
        options=year_options
    )

    # Additional quick filters to focus the Gantt view
    colf1, colf2, colf3, colf4 = st.columns([2,2,2,2])
    with colf1:
        assignees = sorted([str(x) for x in df['ASSIGNMENT TITLE'].dropna().unique()]) if 'ASSIGNMENT TITLE' in df.columns else []
        selected_assignees = st.multiselect("Filter by Assignment Title (Assignee)", options=assignees, default=assignees)
    with colf2:
        progress_options = sorted([str(x) for x in df['PROGRESS'].dropna().unique()]) if 'PROGRESS' in df.columns else ["NOT STARTED","IN PROGRESS","COMPLETE"]
        selected_progress = st.multiselect("Filter by Progress", options=progress_options, default=progress_options)
    with colf3:
        color_by = st.selectbox("Color items by", options=["PLANNER BUCKET","PROGRESS"], index=0)
    with colf4:
        # Choose swimlane grouping
        y_axis_option = st.selectbox("Group swimlanes by", options=["PLANNER BUCKET"] + (["ASSIGNMENT TITLE"] if 'ASSIGNMENT TITLE' in df.columns else []))

    if selected_year == 'All':
        chart_df = df
    else:
        chart_df = df[df['Fiscal Year'] == selected_year]

    # Apply additional filters
    if 'ASSIGNMENT TITLE' in chart_df.columns and selected_assignees:
        chart_df = chart_df[chart_df['ASSIGNMENT TITLE'].isin(selected_assignees)]
    if 'PROGRESS' in chart_df.columns and selected_progress:
        chart_df = chart_df[chart_df['PROGRESS'].isin(selected_progress)]
    
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
        
        # Create the Gantt chart; color by the selected field and group by swimlane choice
        color_field = color_by if color_by in gantt_df.columns else 'PLANNER BUCKET'
        y_field = y_axis_option if y_axis_option in gantt_df.columns else 'PLANNER BUCKET'
        fig = px.timeline(
            gantt_df,
            x_start="START",
            x_end="END",
            y=y_field,
            color=color_field,
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

        # If there are dependency columns, add arrows between dependent tasks
        if 'PREDECESSOR' in gantt_df.columns:
            # Build maps for quick lookup
            try:
                category_order = list(gantt_df[y_field].unique())
                # map category name to y position index (plotly uses category axis)
                cat_index = {cat: i for i, cat in enumerate(category_order)}
                for _, row in gantt_df.iterrows():
                    preds = row.get('PREDECESSOR')
                    if pd.isna(preds) or not preds:
                        continue
                    try:
                        pred_list = [int(x.strip()) for x in str(preds).split(',') if x.strip().isdigit()]
                    except Exception:
                        pred_list = []
                    for pid in pred_list:
                        prev_rows = gantt_df[gantt_df['#'] == pid]
                        if prev_rows.empty:
                            continue
                        prev = prev_rows.iloc[0]
                        # annotation from end of predecessor to start of current
                        fig.add_annotation(
                            x=row['START'], y=row[y_field], xref='x', yref='y',
                            ax=prev['END'], ay=prev[y_field], axref='x', ayref='y',
                            showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1, arrowcolor='black', opacity=0.6
                        )
            except Exception:
                pass

        # If percent-complete is available, add markers on the bars
        pct_candidates = [c for c in gantt_df.columns if 'PERCENT' in c.upper() or 'PCT' in c.upper()]
        pct_col = pct_candidates[0] if pct_candidates else None
        if pct_col:
            try:
                pct_vals = gantt_df[pct_col].astype(float).fillna(0)
                # Compute marker positions
                marker_x = gantt_df['START'] + (gantt_df['END'] - gantt_df['START']) * (pct_vals / 100.0)
                fig.add_scatter(x=marker_x, y=gantt_df[y_field], mode='markers', marker=dict(symbol='diamond', size=8, color='black'), name='Percent Complete')
            except Exception:
                pass

        # If a task is selected, show the chart and task detail side-by-side
        visible_df = gantt_df.copy()
        selected_task_id = st.session_state.get('selected_task_id', None)
        if selected_task_id is not None:
            left_col, right_col = st.columns([3,2])
            with left_col:
                st.plotly_chart(fig, use_container_width=True)
            with right_col:
                st.markdown("### Task detail (selected)")
                # Find the task row
                try:
                    task_row = df[df['#'] == int(selected_task_id)].iloc[0]
                except Exception:
                    st.error("Selected task not found in the dataset.")
                    task_row = None

                if task_row is not None:
                    with st.form("gantt_task_detail_form"):
                        st.write(f"Editing task #{int(task_row['#'])}")
                        assignment_options = sorted([str(item) for item in df['ASSIGNMENT TITLE'].unique()]) if 'ASSIGNMENT TITLE' in df.columns else []
                        progress_options = ["NOT STARTED", "IN PROGRESS", "COMPLETE"]
                        bucket_options = sorted([str(item) for item in df['PLANNER BUCKET'].unique()]) if 'PLANNER BUCKET' in df.columns else []

                        new_assignment = st.selectbox("Assignment Title", options=assignment_options, index=assignment_options.index(task_row['ASSIGNMENT TITLE']) if task_row['ASSIGNMENT TITLE'] in assignment_options else 0)
                        new_progress = st.selectbox("Progress", options=progress_options, index=progress_options.index(task_row.get('PROGRESS','NOT STARTED')) if task_row.get('PROGRESS','NOT STARTED') in progress_options else 0)
                        new_bucket = st.selectbox("Planner Bucket", options=bucket_options, index=bucket_options.index(task_row['PLANNER BUCKET']) if task_row['PLANNER BUCKET'] in bucket_options else 0)
                        new_fy = st.number_input("Fiscal Year", value=int(task_row.get('Fiscal Year', datetime.now().year)))
                        new_start = st.date_input("Start Date", value=task_row['START'].date() if pd.notna(task_row['START']) else datetime.now().date())
                        new_end = st.date_input("End Date", value=task_row['END'].date() if pd.notna(task_row['END']) else datetime.now().date())
                        new_semester = st.text_input("Semester", value=str(task_row.get('SEMESTER','')))
                        new_task_desc = st.text_area("Task Description", value=str(task_row.get('TASK','')))

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            submitted = st.form_submit_button("Save Changes")
                        with col_cancel:
                            cancelled = st.form_submit_button("Cancel")

                    if submitted:
                        df_updated = df.copy()
                        idx = df_updated[df_updated['#'] == int(task_row['#'])].index
                        if not idx.empty:
                            i = idx[0]
                            df_updated.at[i, 'ASSIGNMENT TITLE'] = new_assignment
                            df_updated.at[i, 'PROGRESS'] = new_progress
                            df_updated.at[i, 'PLANNER BUCKET'] = new_bucket
                            df_updated.at[i, 'Fiscal Year'] = new_fy
                            df_updated.at[i, 'START'] = pd.to_datetime(new_start)
                            df_updated.at[i, 'END'] = pd.to_datetime(new_end)
                            df_updated.at[i, 'SEMESTER'] = new_semester
                            df_updated.at[i, 'TASK'] = new_task_desc

                            if data_manager.save_and_log_changes(df, df_updated, st.session_state.get('logged_in_user','system'), source_page='Gantt - Task Edit'):
                                st.success("Task updated and logged successfully.")
                                st.session_state['selected_task_id'] = None
                                st.rerun()
                        else:
                            st.error("Could not find the task index to update.")

                    if cancelled:
                        st.session_state['selected_task_id'] = None
                        st.rerun()
        else:
            st.plotly_chart(fig, use_container_width=True)
            # --- Export visible tasks and quick edit selector ---
            st.write("---")
            st.subheader("Visible tasks & quick edit")
        # Provide a CSV download of the currently visible tasks
        try:
            csv_bytes = visible_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download visible tasks (CSV)", data=csv_bytes, file_name=f"gantt_visible_tasks_{selected_year}.csv", mime='text/csv')
        except Exception:
            pass

        # Export chart as PNG / SVG if kaleido available
        if _KALEIDO_AVAILABLE:
            # Ensure the figure has traces before exporting
            if not fig.data or len(fig.data) == 0:
                st.warning("Chart has no visible traces to export.")
            else:
                # Use a fixed image size for reliable rendering
                try:
                    fig.update_layout(autosize=False, width=1200, height=800)
                except Exception:
                    pass

                try:
                    # PNG export
                    img_bytes = fig.to_image(format='png', engine='kaleido', width=1200, height=800, scale=2)
                    st.download_button("Export chart as PNG", data=img_bytes, file_name=f"gantt_{selected_year}.png", mime='image/png')

                    # SVG export
                    svg_bytes = fig.to_image(format='svg', engine='kaleido', width=1200, height=800)
                    st.download_button("Export chart as SVG", data=svg_bytes, file_name=f"gantt_{selected_year}.svg", mime='image/svg+xml')
                except Exception as e:
                    st.warning(f"Could not export chart images: {e}")
        else:
            st.info("Install 'kaleido' to enable PNG/SVG export of the chart.")

        # Always offer an interactive HTML export as a reliable fallback
        try:
            html = fig.to_html(include_plotlyjs='cdn')
            st.download_button("Download interactive HTML", data=html, file_name=f"gantt_{selected_year}.html", mime='text/html')
        except Exception as e:
            st.warning(f"Could not prepare interactive HTML export: {e}")

        # Allow selecting a task to edit
        if not visible_df.empty:
            visible_df['display_label'] = visible_df.apply(lambda r: f"#{int(r['#'])} — {str(r.get('TASK',''))[:80]}", axis=1)
            options = visible_df.set_index('display_label')['#'].to_dict()
            chosen_label = st.selectbox("Select a task to open in the editor", options=['--'] + list(options.keys()))
            if st.button("Open selected task"):
                if chosen_label and chosen_label != '--':
                    task_id = int(options[chosen_label])
                    st.session_state['selected_task_id'] = task_id
                    st.rerun()
    else:
        st.warning(f"No valid tasks to display for the selected Fiscal Year ({selected_year}).")

else:
    st.warning("Could not load data.")