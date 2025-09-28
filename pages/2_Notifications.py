# File: pages/11_Notifications.py
import streamlit as st
import pandas as pd
import data_manager
import re

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="Notifications", layout="wide")
st.title("🔔 My Notifications")

user_email = st.session_state.logged_in_user
notifications_df = data_manager.load_table('notifications')
tasks_df = data_manager.load_table('tasks')

if notifications_df is not None and tasks_df is not None:
    # Filter for the current user's notifications
    user_notifications = notifications_df[notifications_df['user_email'] == user_email].sort_values(by='timestamp', ascending=False)

    unread_notifications = user_notifications[user_notifications['is_read'] == False]
    read_notifications = user_notifications[user_notifications['is_read'] == True]

    st.subheader("Unread Notifications")

    if not unread_notifications.empty:
        # Button to mark all as read
        if st.button("Mark All as Read"):
            # Update the original notifications DataFrame
            notifications_df.loc[unread_notifications.index, 'is_read'] = True
            if data_manager.save_table(notifications_df, 'notifications'):
                st.success("All notifications marked as read.")
                st.rerun()

        # Display each unread notification
        for index, notification in unread_notifications.iterrows():
            # The message is now structured as "Header |:| Comment Text"
            parts = notification['message'].split(' |:| ')
            header = parts[0]
            comment_text = parts[1] if len(parts) > 1 else ""

            # Use regex to find the task ID in the header
            match = re.search(r'task #(\d+)', header)
            if match:
                task_id = int(match.group(1))
                task_details = tasks_df[tasks_df['#'] == task_id]
                
                with st.container(border=True):
                    if not task_details.empty:
                        task_name = task_details.iloc[0]['TASK']
                        st.markdown(f"**{header}** on task: *{task_name}*")
                    else:
                        st.markdown(f"**{header}**")

                    st.info(f"**Comment:** {comment_text}")

                    # --- JUMP TO TASK BUTTON ---
                    if st.button("View Task & Add Comment", key=f"jump_{notification['notification_id']}"):
                        # Set the task ID in the session state
                        st.session_state.jump_to_task = task_id
                        # Programmatically switch to the Find and Filter page
                        st.switch_page("pages/2_Find_and_Filter.py")

            else:
                st.info(f"**{notification['message']}**")

    else:
        st.success("You have no unread notifications.")

    st.markdown("---")

    # Show read notifications in an expander
    with st.expander("View Read Notifications"):
        if not read_notifications.empty:
            for index, notification in read_notifications.iterrows():
                st.write(f"_{notification['message'].split(' |:| ')[0]}_") # Show only the header for read notifications
        else:
            st.write("No previously read notifications.")

else:
    st.warning("Could not load notification or task data.")
