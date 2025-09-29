# File: pages/12_Help.py
import streamlit as st
import re
from fpdf import FPDF
from datetime import datetime

# --- AUTHENTICATION CHECK ---
if 'logged_in_user' not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("Please log in to access this page.")
    st.stop()
# --------------------------

def create_help_pdf(manual_content):
    """Generates a PDF version of the user manual."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    
    # --- PDF Header ---
    pdf.cell(0, 10, "HRL Project Tracker - User Manual", ln=True, align='C')
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)

    # --- PDF Body ---
    sections = manual_content.split('<details>')
    
    # Introduction part
    intro_content = sections[0].strip().replace("###", "")
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 8, intro_content)
    pdf.ln(5)

    # Loop through the expandable sections
    for section in sections[1:]:
        summary_match = re.search(r'<summary><h3>(.*?)</h3></summary>', section, re.DOTALL)
        if summary_match:
            title = summary_match.group(1).strip()
            content = section.split('</summary>')[1].replace('</details>', '').strip()
            
            # Clean up markdown for the PDF
            content = content.replace("`", "'").replace("**", "").replace("###", "").replace(":red", "").replace(":orange", "").replace(":green", "").replace("[NOT STARTED]", "(Not Started)").replace("[IN PROGRESS]", "(In Progress)").replace("[COMPLETE]", "(Complete)")
            
            # Add section to PDF
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, title, ln=True, border='B')
            pdf.ln(4)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, content)
            pdf.ln(5)

    return bytes(pdf.output())

# --- PAGE UI ---
st.set_page_config(page_title="Help", layout="wide")
st.title("📖 HRL Project Tracker Help & Instructions")

try:
    with open('user_manual.md', 'r', encoding='utf-8') as f:
        manual_content = f.read()
    
    # --- PDF Download Button ---
    pdf_data = create_help_pdf(manual_content)
    st.download_button(
        label="📄 Download PDF Manual",
        data=pdf_data,
        file_name="HRL_Project_Tracker_User_Manual.pdf",
        mime="application/pdf"
    )
    st.markdown("---")

    # Display the manual on the page using expanders
    sections = manual_content.split('<details>')
    intro_content = sections[0]
    st.markdown(intro_content, unsafe_allow_html=True)

    for section in sections[1:]:
        summary_match = re.search(r'<summary><h3>(.*?)</h3></summary>', section, re.DOTALL)
        if summary_match:
            title = summary_match.group(1)
            content = section.split('</summary>')[1].replace('</details>', '').strip()
            
            with st.expander(title):
                st.markdown(content, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("Error: The user manual file (`user_manual.md`) could not be found.")
    st.info("Please ensure the `user_manual.md` file is in the main project folder.")

