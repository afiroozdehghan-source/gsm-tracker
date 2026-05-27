import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
# Replace this with your Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qGJ-7uyv1_T3GvynT3HYKVDSn8GYLbPVbhBMNhMovjU/edit?usp=sharing"

USER_CREDENTIALS = {
    "alireza": "admin2026",
    "keno": "keno123",
    "mbina": "mbina123"
}

st.set_page_config(page_title="GSM Systems Cloud", page_icon="📶")

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("📶 GSM Systems Cloud Login")
    with st.form("login"):
        u = st.text_input("Username").lower()
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u in USER_CREDENTIALS and USER_CREDENTIALS[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop()

# --- APP INTERFACE ---
st.title("📶 GSM Systems Tracker (Global)")
st.write(f"Technician: **{st.session_state['username'].capitalize()}**")

with st.form("tracking_form", clear_on_submit=True):
    barcode = st.text_input("Scan Barcode")
    activity = st.radio("Activity", ["Screen Test", "Repair", "Soak Test"], horizontal=True)
    status = st.selectbox("Status", ["Started", "Passed", "Failed", "BER"])
    comment = st.text_input("Notes")
    submit = st.form_submit_button("Submit to Cloud")

if submit:
    if barcode:
        now = datetime.now()
        # Create a dictionary for the new row
        new_row = {
            "Timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%H:%M:%S"),
            "Technician": st.session_state["username"].capitalize(),
            "Unit_Barcode": barcode.upper(),
            "Activity_Type": activity,
            "Status": status,
            "Technician_Comment": comment
        }
        
        # Get existing data
        existing_data = conn.read(spreadsheet=SHEET_URL)
        # Update Data
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
        # Write back to Google Sheets
        conn.update(spreadsheet=SHEET_URL, data=updated_df)
        
        st.success(f"✅ Data synced to Global Database! Unit: {barcode.upper()}")
    else:
        st.error("Barcode is required!")

# Admin View
if st.sidebar.text_input("Admin Access", type="password") == "GSM2026":
    st.write("### Live Data from Google Sheets")
    data = conn.read(spreadsheet=SHEET_URL)
    st.dataframe(data)
