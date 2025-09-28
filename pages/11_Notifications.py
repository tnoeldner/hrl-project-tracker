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
            notifications_df.loc[unread_notifications.index, 'is_read'] = True
            if data_manager.save_table(notifications_df, 'notifications'):
                st.success("All notifications marked as read.")
                st.rerun()

        # Display each unread notification
        for index, notification in unread_notifications.iterrows():
            message = str(notification['message'])
            
            # --- UPDATED LOGIC TO PARSE AND DISPLAY FULL COMMENT ---
            # The message is now expected to be in the format: "Header |:| Comment Text"
            parts = message.split(' |:| ')
            if len(parts) == 2:
                header_part, comment_part = parts
                match = re.search(r'task #(\d+)', header_part)
                if match:
                    task_id = int(match.group(1))
                    task_details = tasks_df[tasks_df['#'] == task_id]
                    
                    if not task_details.empty:
                        task_name = task_details.iloc[0]['TASK']
                        
                        # Display notification in a bordered container
                        with st.container(border=True):
                            st.markdown(f"**{header_part}**")
                            st.markdown(f"> {comment_part}") # Display the comment text
                            st.caption(f"Task: {task_name}")
                            
                            # Button to jump to the task on the Find and Filter page
                            if st.button("View Task & Add Comment", key=f"goto_{notification['notification_id']}"):
                                st.session_state['jump_to_task'] = task_id
                                st.switch_page("pages/2_Find_and_Filter.py")
                    else:
                        st.info(f"**{header_part}**\n\n*Task details not found.*")
            else:
                # Fallback for old or simple notification formats
                st.info(f"**{message}**")
            # ------------------------------------

    else:
        st.success("You have no unread notifications.")

    st.markdown("---")

    # Show read notifications in an expander
    with st.expander("View Read Notifications"):
        if not read_notifications.empty:
            for index, notification in read_notifications.iterrows():
                st.write(f"_{notification['message']}_")
        else:
            st.write("No previously read notifications.")

else:
    st.warning("Could not load notification or task data.")