import streamlit as st
import requests
from datetime import datetime
import pytz

# --- CONFIGURATION ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbya-PN_qZ20dy1RMX4utbyI6ozjMJ80mdVJb0398_pJ4KK48mLhmhAzGnaJdlL4Avqu/exec" 

USER_CREDENTIALS = {
    "alireza": "admin2026",
    "keno": "keno123",
    "mbina": "mbina123",
    "john": "admin123",
    "thabang": "thabang123",
    "khanyisani": "khanyisani123",
    "tshepo": "tshepo123",
    "dennis": "dennis123",
    "malcom": "malcom123"
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

# ایجاد و مدیریت کلیدهای حافظه برای تمام فیلدها
if "barcode_input" not in st.session_state:
    st.session_state["barcode_input"] = ""
if "activity_input" not in st.session_state:
    st.session_state["activity_input"] = "Screen Test"
if "status_input" not in st.session_state:
    st.session_state["status_input"] = "Started"
if "notes_input" not in st.session_state:
    st.session_state["notes_input"] = ""

# تابع بازنشانی تمام فیلدها به حالت اولیه بعد از کلیک روی دکمه
def clear_all_fields():
    st.session_state["barcode_to_submit"] = st.session_state["barcode_input"]
    st.session_state["barcode_input"] = ""
    st.session_state["activity_input"] = "Screen Test"  # ریست به گزینه اول
    st.session_state["status_input"] = "Started"      # ریست به گزینه اول
    st.session_state["notes_input"] = ""              # خالی کردن کادر یادداشت

# کادر اسکن بارکد
barcode = st.text_input("Scan Barcode (Place cursor here and scan)", key="barcode_input")

# گزینه‌های فعالیت، وضعیت و یادداشت‌ها (همگی متصل به سیستم ریست هوشمند)
activity = st.radio("Activity", ["Screen Test", "Repair", "Soak Test"], horizontal=True, key="activity_input")
status = st.selectbox("Status", ["Started", "Passed", "Failed", "BER"], key="status_input")
comment = st.text_input("Notes", key="notes_input")

# دکمه ثبت مستقل مجهز به تابع ریست کلی
submit = st.button("Submit to Cloud", type="primary", on_click=clear_all_fields)

# پردازش اطلاعات
if submit:
    # خواندن بارکد از متغیر موقت امن
    target_barcode = st.session_state.get("barcode_to_submit", "").upper().strip()
    
    if target_barcode:
        # تنظیم دقیق منطقه زمانی آفریقای جنوبی (SAST)
        sa_tz = pytz.timezone('Africa/Johannesburg')
        now_sa = datetime.now(sa_tz)
        
        payload = {
            "Timestamp": now_sa.strftime("%Y-%m-%d %H:%M:%S"),
            "Date": now_sa.strftime("%Y-%m-%d"),
            "Time": now_sa.strftime("%H:%M:%S"),
            "Technician": st.session_state["username"].capitalize(),
            "Unit_Barcode": target_barcode,
            "Activity_Type": activity,
            "Status": status,
            "Technician_Comment": comment
        }
        
        with st.spinner("Syncing to database..."):
            try:
                response = requests.post(WEBAPP_URL, json=payload)
                if response.status_code == 200:
                    st.toast(f"✅ Unit {target_barcode} successfully synced!")
                    st.success(f"✅ Data successfully synced! Unit: {target_barcode}")
                else:
                    st.error("⚠️ Connection successful but Sheet rejected the data.")
            except Exception as e:
                st.error(f"Error connecting to Cloud: {e}")
    else:
        st.error("Barcode is required! Please scan a unit first.")
