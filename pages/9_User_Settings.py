# File: pages/9_User_Settings.py
import streamlit as st
import pandas as pd
import data_manager

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

st.set_page_config(page_title="User Settings", layout="wide")
st.title("⚙️ User Settings")

user_email = st.session_state.logged_in_user
user_role = st.session_state.user_data.get('role')
settings_df = data_manager.load_table('settings')
if settings_df is None:
    settings_df = pd.DataFrame(columns=['email', 'frequency']) # Create empty df if table doesn't exist

# --- Current User's Settings ---
st.subheader("My Notification Preferences")
# ... (This section remains the same, but we will add logic to save to the database)

st.markdown("---")

# --- Administrator Section ---
if user_role == 'admin':
    st.subheader("👑 Administrator Settings")
    st.write("As an admin, you can manage user notification settings and reset passwords.")
    
    users_df = data_manager.load_table('users')
    if users_df is not None:
        all_user_emails = sorted(users_df['email'].tolist())
        
        selected_user_for_edit = st.selectbox("Select a User to Edit", options=all_user_emails)
        
        if selected_user_for_edit:
            # --- Edit Notification Frequency ---
            st.write(f"**Notification Settings for {selected_user_for_edit}**")
            current_user_settings = settings_df[settings_df['email'] == selected_user_for_edit]
            current_freq = current_user_settings.iloc[0]['frequency'] if not current_user_settings.empty else 'Never'
            
            frequency_options = ["Never", "Daily", "Weekly"]
            new_freq = st.selectbox("Email Frequency", options=frequency_options, index=frequency_options.index(current_freq))

            if st.button("Save Frequency Setting"):
                if not current_user_settings.empty:
                    settings_df.loc[settings_df['email'] == selected_user_for_edit, 'frequency'] = new_freq
                else:
                    new_setting = pd.DataFrame([{'email': selected_user_for_edit, 'frequency': new_freq}])
                    settings_df = pd.concat([settings_df, new_setting], ignore_index=True)
                
                if data_manager.save_table(settings_df, 'settings'):
                    st.success(f"Frequency for {selected_user_for_edit} updated!")

            st.write("---")

            # --- Reset Password ---
            st.write(f"**Password Management for {selected_user_for_edit}**")
            new_password = st.text_input("Enter a new password to reset", type="password", key="admin_pw_reset")
            if st.button("Reset User's Password"):
                if new_password:
                    users_df.loc[users_df['email'] == selected_user_for_edit, 'password'] = new_password
                    if data_manager.save_table(users_df, 'users'):
                        st.success(f"Password for {selected_user_for_edit} has been reset!")
                else:
                    st.warning("Please enter a password.")