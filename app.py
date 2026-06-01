import streamlit as st
import requests
from datetime import datetime
import pytz

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
    "dennis":"dennis123",
    "malcom":"malcom123"
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

# ایجاد یک کلید در حافظه برای مدیریت خالی کردن کادر بارکد
if "barcode_input" not in st.session_state:
    st.session_state["barcode_input"] = ""

# کادر بارکد متصل به حافظه موقت (st.session_state)
barcode = st.text_input("Scan Barcode (Place cursor here and scan)", key="barcode_input")

with st.form("activity_form", clear_on_submit=True):
    activity = st.radio("Activity", ["Screen Test", "Repair", "Soak Test"], horizontal=True)
    status = st.selectbox("Status", ["Started", "Passed", "Failed", "BER"])
    comment = st.text_input("Notes")
    submit = st.form_submit_button("Submit to Cloud")

if submit:
    if barcode:
        sa_tz = pytz.timezone('Africa/Johannesburg')
        now_sa = datetime.now(sa_tz)
        
        payload = {
            "Timestamp": now_sa.strftime("%Y-%m-%d %H:%M:%S"),
            "Date": now_sa.strftime("%Y-%m-%d"),
            "Time": now_sa.strftime("%H:%M:%S"),
            "Technician": st.session_state["username"].capitalize(),
            "Unit_Barcode": barcode.upper().strip(),
            "Activity_Type": activity,
            "Status": status,
            "Technician_Comment": comment
        }
        
        with st.spinner("Syncing to database..."):
            try:
                response = requests.post(WEBAPP_URL, json=payload)
                if response.status_code == 200:
                    # نمایش دائم پیغام موفقیت
                    st.success(f"✅ Data successfully synced! Unit: {barcode.upper().strip()}")
                    
                    # خالی کردن کادر بارکد در حافظه برای اسکن بعدی بدون حذف شدن پیغام بالا
                    st.session_state["barcode_input"] = ""
                    st.rerun()
                else:
                    st.error("⚠️ Connection successful but Sheet rejected the data.")
            except Exception as e:
                st.error(f"Error connecting to Cloud: {e}")
    else:
        st.error("Barcode is required! Please scan a unit first.")
