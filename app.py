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

# --- حافظه میانی (بافر زنده استریملیت برای کنترل خطا) ---
# این بافر لیست قطعات فعال کارگاه را که دکمه استارت آن‌ها زده شده مدیریت می‌کند
if "active_buffer" not in st.session_state:
    st.session_state["active_buffer"] = {}  # ساختار به صورت {barcode: {"activity": activity, "tech": tech}}

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

# تابع بازنشانی هوشمند: ابتدا دیتا را امن ذخیره می‌کند، سپس ظاهر فیلدها را ریست می‌کند
def clear_all_fields():
    # ۱. پشتیبان‌گیری از تمام فیلدها قبل از پاک شدن
    st.session_state["barcode_to_submit"] = st.session_state["barcode_input"]
    st.session_state["activity_to_submit"] = st.session_state["activity_input"]
    st.session_state["status_to_submit"] = st.session_state["status_input"]
    st.session_state["notes_to_submit"] = st.session_state["notes_input"]
    
    # ۲. حالا با خیال راحت ظاهر فیلدها را ریست و سفید می‌کنیم
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

# دکمه ثبت مجهز به تابع بک‌آ‌پ و ریست
submit = st.button("Submit to Cloud", type="primary", on_click=clear_all_fields)

# پردازش اطلاعات
if submit:
    # خواندن دیتا از متغیرهای پشتیبان‌گیری شده‌ی امن
    target_barcode = st.session_state.get("barcode_to_submit", "").upper().strip()
    target_activity = st.session_state.get("activity_to_submit", "Screen Test")
    target_status = st.session_state.get("status_to_submit", "Started")
    target_comment = st.session_state.get("notes_to_submit", "")
    
    if target_barcode:
        current_tech = st.session_state["username"].capitalize()
        
        # ----------------- فیلتر هوشمند ضدخطا (بافر) -----------------
        is_error = False
        
        if target_status == "Started":
            # اگر قطعه از قبل استارت شده باشد و دوباره دکمه استارت زده شود
            if target_barcode in st.session_state["active_buffer"]:
                existing_job = st.session_state["active_buffer"][target_barcode]
                st.error(f"❌ Error: Unit {target_barcode} is already IN PROGRESS! Started by {existing_job['tech']} for '{existing_job['activity']}'.")
                is_error = True
            else:
                # اگر مشکلی نبود، قطعه به بافر کارهای فعال اضافه می‌شود
                st.session_state["active_buffer"][target_barcode] = {
                    "activity": target_activity,
                    "tech": current_tech,
                    "start_time": datetime.now().strftime("%H:%M:%S")
                }
                
        else:  # وضعیت‌های پایانی: Passed, Failed, BER
            # خطای حیاتی: اگر قطعه اصلاً در بافر استارت نشده باشد
            if target_barcode not in st.session_state["active_buffer"]:
                st.error(f"❌ CRITICAL ERROR: No 'Started' log found for unit {target_barcode}. You cannot record a completion status without starting the task first!")
                is_error = True
            else:
                # اگر استارت شده بود، کار با موفقیت انجام شده و از بافر زنده حذف (پاک) می‌شود
                del st.session_state["active_buffer"][target_barcode]
        
        # -------------------------------------------------------------
        
        # اگر خطایی وجود نداشت، دیتا به گوگل‌شیت ارسال می‌شود
        if not is_error:
            # تنظیم دقیق منطقه زمانی آفریقای جنوبی (SAST)
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
            
            with st.spinner("Syncing to database..."):
                try:
                    response = requests.post(WEBAPP_URL, json=payload)
                    if response.status_code == 200:
                        st.toast(f"✅ Unit {target_barcode} successfully synced!")
                        st.success(f"✅ Data successfully synced! Unit: {target_barcode}")
                    else:
                        st.error("⚠️ Connection successful but Sheet rejected the data.")
                        # در صورت ریجکت شدن توسط کلود، بافر را به حالت قبل برمی‌گردانیم
                        if target_status == "Started":
                            if target_barcode in st.session_state["active_buffer"]:
                                del st.session_state["active_buffer"][target_barcode]
                        else:
                            st.session_state["active_buffer"][target_barcode] = {"activity": target_activity, "tech": current_tech}
                except Exception as e:
                    st.error(f"Error connecting to Cloud: {e}")
                    # در صورت خطای شبکه نیز بافر را برای امنیت دیتا ریست می‌کنیم
                    if target_status == "Started" and target_barcode in st.session_state["active_buffer"]:
                        del st.session_state["active_buffer"][target_barcode]
    else:
        st.error("Barcode is required! Please scan a unit first.")

# --- مانیتورینگ زنده کارگاه (Active Buffer) ---
# نمایش بردهایی که هم‌اکنون زیر دست تکنسین‌ها باز هستند در پایین صفحه
st.markdown("---")
st.subheader("⏳ Units Currently In Progress (Live Workshop Buffer)")

if not st.session_state["active_buffer"]:
    st.info("No active units currently in progress. All clear!")
else:
    # تبدیل بافر به یک جدول زیبا برای نمایش به تکنسین‌ها و علیرضا
    buffer_display = []
    for bc, info in st.session_state["active_buffer"].items():
        buffer_display.append({
            "Unit Barcode": bc,
            "Technician": info["tech"],
            "Activity": info["activity"],
            "Started At": info.get("start_time", "N/A")
        })
    st.dataframe(pd.DataFrame(buffer_display), use_container_width=True)
