import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

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

# --- تابع دریافت زنده دیتای بافر از گوگل شیت ---
@st.cache_data(ttl=5) # کاهش زمان کش به ۵ ثانیه برای همگام‌سازی سریع‌تر
def fetch_live_buffer():
    try:
        response = requests.get(WEBAPP_URL)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# خواندن دیتای زنده کارگاه از گوگل شیت
live_tasks = fetch_live_buffer()

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

def clear_all_fields():
    st.session_state["barcode_to_submit"] = st.session_state["barcode_input"]
    st.session_state["activity_to_submit"] = st.session_state["activity_input"]
    st.session_state["status_to_submit"] = st.session_state["status_input"]
    st.session_state["notes_to_submit"] = st.session_state["notes_input"]
    
    st.session_state["barcode_input"] = ""
    st.session_state["activity_input"] = "Screen Test"
    st.session_state["status_input"] = "Started"
    st.session_state["notes_input"] = ""

# کادر اسکن بارکد
barcode = st.text_input("Scan Barcode (Place cursor here and scan)", key="barcode_input")

# گزینه‌های فعالیت، وضعیت و یادداشت‌ها
activity = st.radio("Activity", ["Screen Test", "Repair", "Soak Test"], horizontal=True, key="activity_input")
status = st.selectbox("Status", ["Started", "Passed", "Failed", "BER"], key="status_input")
comment = st.text_input("Notes", key="notes_input")

submit = st.button("Submit to Cloud", type="primary", on_click=clear_all_fields)

# پردازش اطلاعات
if submit:
    target_barcode = st.session_state.get("barcode_to_submit", "").upper().strip()
    target_activity = st.session_state.get("activity_to_submit", "Screen Test")
    target_status = st.session_state.get("status_to_submit", "Started")
    target_comment = st.session_state.get("notes_to_submit", "")
    
    if target_barcode:
        current_tech = st.session_state["username"].capitalize()
        is_error = False
        
        # ----------------- سیستم کنترل خطای زنده و دو قفله متصل به گوگل شیت -----------------
        
        # پیدا کردن اینکه آیا این بارکد دقیقاً با همین نوع فعالیت در حال حاضر باز است یا خیر
        matching_job = next((item for item in live_tasks if 
                             item["Unit_Barcode"].upper().strip() == target_barcode and 
                             item["Activity_Type"].lower().strip() == target_activity.lower().strip()), None)
        
        if target_status == "Started":
            # اگر این بارکد دقیقاً برای همین فعالیت از قبل استارت شده باشد
            if matching_job:
                st.error(f"❌ Error: Unit {target_barcode} is already IN PROGRESS for '{target_activity}' by {matching_job['Technician']}.")
                is_error = True
        else:
            # برای وضعیت‌های پایانی (Passed, Failed, BER)، باید حتماً همان فعالیت استارت شده باشد
            if not matching_job:
                # چک می‌کنیم آیا برای یک فعالیت دیگر باز است که راهنمایی دقیق‌تری بکنیم
                any_job_for_barcode = next((item for item in live_tasks if item["Unit_Barcode"].upper().strip() == target_barcode), None)
                if any_job_for_barcode:
                    st.error(f"❌ CRITICAL ERROR: Unit {target_barcode} is currently open for '{any_job_for_barcode['Activity_Type']}'. You cannot submit a status for '{target_activity}'!")
                else:
                    st.error(f"❌ CRITICAL ERROR: No 'Started' log found in Google Sheets for unit {target_barcode} under '{target_activity}'. You must start the task first!")
                is_error = True
        # -------------------------------------------------------------------------------------
        
        if not is_error:
            sa_tz = pytz.timezone('Africa/Johannesburg')
            now_sa = datetime.now(sa_tz)
            
            payload = {
                "Timestamp": now_sa.strftime("%Y-%m-%d %H:%M:%S"),
                "Date": now_sa.strftime("%Y-%m-%d"),
                "Time": now_sa.strftime("%H:%M:%S"),
                "Technician": current_tech,
                "Unit_Barcode": target_barcode,
                "Activity_Type": target_activity,  
                "Status": target_status,          
                "Technician_Comment": target_comment  
            }
            
            with st.spinner("Syncing to cloud database..."):
                try:
                    response = requests.post(WEBAPP_URL, json=payload)
                    if response.status_code == 200:
                        st.toast(f"✅ Unit {target_barcode} successfully synced!")
                        st.success(f"✅ Data successfully synced! Unit: {target_barcode}")
                        st.cache_data.clear() # خالی کردن فوری کش برای آپدیت زنده جدول
                        st.rerun()
                    else:
                        st.error("⚠️ Connection successful but Cloud rejected the data.")
                except Exception as e:
                    st.error(f"Error connecting to Cloud: {e}")
    else:
        st.error("Barcode is required! Please scan a unit first.")

# --- مانیتورینگ زنده کارگاه (نمایش مستقیم اطلاعات شیت Active_Tasks) ---
st.markdown("---")
st.subheader("⏳ Live Workshop Monitor (Active Tasks from Cloud)")

if not live_tasks:
    st.info("No active units currently in progress. All clear in the workshop!")
else:
    # تبدیل مستقیم اطلاعات دریافتی به جدول شیک استریملیت
    df_display = pd.DataFrame(live_tasks)
    df_display.columns = ["Unit Barcode", "Technician", "Current Activity", "Started At"]
    st.dataframe(df_display, use_container_width=True)
