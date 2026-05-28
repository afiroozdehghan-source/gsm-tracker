import streamlit as st
import requests
from datetime import datetime

# --- CONFIGURATION ---
# TODO: Paste your Google Web App URL here
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbya-PN_qZ20dy1RMX4utbyI6ozjMJ80mdVJb0398_pJ4KK48mLhmhAzGnaJdlL4Avqu/exec"

USER_CREDENTIALS = {
    "alireza": "admin2026",
    "keno": "keno123",
    "mbina": "mbina123",
    "john":"admin123",
    "thabang":"thabang123",
    "khanyisani":"khanyisani123",
    "tshepo":"tshepo123",
    "dennis":"dennis123"
}

st.set_page_config(page_title="GSM Systems Cloud", page_icon="📶")

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
st.title("📶 GSM Systems Tracker")
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
        # Prepare data payload
        payload = {
            "Timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%H:%M:%S"),
            "Technician": st.session_state["username"].capitalize(),
            "Unit_Barcode": barcode.upper(),
            "Activity_Type": activity,
            "Status": status,
            "Technician_Comment": comment
        }
        
        # Send data straight to Google Sheet via Web App
        with st.spinner("Syncing to database..."):
            try:
                response = requests.post(WEBAPP_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"✅ Data successfully synced! Unit: {barcode.upper()}")
                else:
                    st.error("⚠️ Connection successful but Sheet rejected the data.")
            except Exception as e:
                st.error(f"Error connecting to Cloud: {e}")
    else:
        st.error("Barcode is required!")
