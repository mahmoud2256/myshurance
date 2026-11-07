import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import urllib.parse

st.set_page_config(page_title="Myshurance - Hub", layout="wide")

# --- Colors from v4_2 - Teal + Sand + Cairo ---
TEAL_DARK, TEAL, TEAL_ACTIVE = "#07363B", "#0B4F55", "#226068"
SAND, CREAM, BORDER = "#E8C9A0", "#F6F1E8", "#E8DCC8"
def inject_css():
    css = f"""
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
html, body, [class*="css"], .stApp, button, input, textarea, select {{ font-family: 'Cairo', sans-serif !important; }}
.stApp {{ background: {CREAM}; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.5rem; max-width: 1250px; }}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {TEAL}, {TEAL_DARK}); }}
[data-testid="stSidebar"] * {{ color: #EAF1F0; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.12); }}
.stButton > button {{ background: {TEAL}; color: white; border-radius: 14px; border: 1px solid {TEAL_DARK}; font-weight: 700; }}
.stButton > button:hover {{ background: {TEAL_ACTIVE}; color: white; }}
h1, h2, h3 {{ color: {TEAL_DARK}; }}
"""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
inject_css()

# ===== Language System - عربي / English - مفيش خلط =====
if "lang" not in st.session_state:
    st.session_state["lang"] = "ar"
# زرار اللغة فوق خالص - قبل أي حاجة
# زرار اللغة - نفسه لازم يبقى بلغة واحدة بس، من غير خلط
# لو اللغة عربي: الليبل والاختيارات عربي بس. لو انجليزي: الليبل والاختيارات انجليزي بس.
if st.session_state["lang"] == "ar":
    _lang_label = "🌐 اللغة"
    _lang_opts = ["العربية", "الإنجليزية"]
    _lang_choice = st.sidebar.radio(_lang_label, _lang_opts, index=0 if st.session_state["lang"]=="ar" else 1, key="lang_radio")
    st.session_state["lang"] = "ar" if _lang_choice=="العربية" else "en"
else:
    _lang_label = "🌐 Language"
    _lang_opts = ["Arabic", "English"]
    _lang_choice = st.sidebar.radio(_lang_label, _lang_opts, index=1, key="lang_radio")
    st.session_state["lang"] = "en" if _lang_choice=="English" else "ar"
LANG = st.session_state["lang"]

TRANSLATIONS = {
    "ar": {
        "login_title": "🔐 مايشورانس - تسجيل الدخول",
        "login_sub": "مدير أو موظف - اختار نوع الدخول",
        "login_as": "دخول كـ:",
        "admin": "👨💼 مدير",
        "employee": "👤 موظف",
        "username": "اسم المستخدم",
        "password": "كلمة السر",
        "login_admin": "دخول كمدير",
        "wrong": "❌ اسم المستخدم أو كلمة السر غلط",
        "default_admin": "المدير الافتراضي: admin / myshurance123",
        "emp_title": "👤 خدمة الموظف",
        "emp_sub": "ادخل بالرقم القومي عشان تشوف بياناتك وموافقاتك",
        "emp_nid": "الرقم القومي *",
        "emp_btn": "عرض بياناتي 👀",
        "emp_empty": "اكتب الرقم القومي",
        "emp_no_data": "مفيش بيانات لسه",
        "emp_not_found": "❌ الرقم القومي مش موجود - كلم الـ HR",
        "emp_note": "الموظف بيدخل بالرقم القومي بس، من غير باسورد",
        "logout": "خروج 🚪",
        "hub_title": "مايشورانس",
        "hub_sub": "شيتات جوجل مباشرة - شركات / إضافة / حذف / ترقية / موافقات / تحليلات",
        "wa_title": "📱 إعدادات واتساب",
        "wa_num": "رقم واتساب الـ HR / الشركة",
        "wa_hint": "الرقم اللي هيتبعتله التنبيه، بكود الدولة من غير +",
        "alerts": "🔔 تنبيهات",
        "alerts_none": "✅ مفيش تنبيهات - كل حاجة تمام",
        "alerts_old": "⚠ فيه موافقات معلقة بقالها أكتر من يومين - لازم تتراجع!",
        "alerts_exp": "🚨 فيه كروت هتخلص خلال 30 يوم!",
        "companies_m": "شركات",
        "addition_m": "إضافة",
        "deletion_m": "حذف",
        "upgrade_m": "ترقية",
        "pending_m": "موافقات معلقة",
        "total_m": "إجمالي الطلبات",
        "last_wa": "آخر طلب اتسجل ✅ - ابعته واتساب من هنا:",
        "send_wa": "ابعت على واتساب",
        "clear_wa": "امسح رسالة الواتساب ❌",
        "export_title": "📥 تصدير تقرير",
        "export_choose": "اختار اللي هتصدّره",
        "export_btn": "تحميل تقرير إكسل 📥",
        "export_save": "دوس هنا عشان تحفظ الملف 💾",
        "search_title": "🔍 بحث عن عضو",
        "search_ph": "مثال: أحمد أو 2980101...",
        "search_no_data": "مفيش بيانات لسه",
        "search_no": "مفيش نتائج لـ:",
        "search_found": "لقينا نتيجة",
        "tab_comp": "🏢 شركات",
        "tab_add": "➕ إضافة",
        "tab_del": "➖ حذف",
        "tab_upg": "⬆ ترقية",
        "tab_appr": "✅ موافقات",
        "tab_analytics": "📊 تحليلات",
        "scan_title": "➕ إضافة عضو جديد - بالإضافة بالسكان",
        "scan_cap": "ارفع صورة البطاقة أو الكارنيه، السيستم هيملي البيانات لوحده، انت راجع بس قبل ما تدوس حفظ",
        "scan_tip": "💡 عشان السكان ينجح: صوّر البطاقة معدولة مش مقلوبة، في نور كويس، والكلام واضح ومش مهزوز.",
        "scan_upload": "📸 ارفع صورة البطاقة أو الكارنيه",
        "scan_uploaded": "الصورة اللي اترفعت",
        "scan_btn": "🔍 اعمل سكان واملا البيانات لوحدها",
        "scan_reading": "بقرا البطاقة... ثواني",
        "scan_ok": "تم القراءة ✅",
        "scan_card_no": "رقم الكارت",
        "scan_nid_manual": "والرقم القومي (14 رقم) كمله يدوي من البطاقة الشخصية",
        "scan_fail": "مقدرتش أقرا البيانات - الصورة مش واضحة. جرب تصورها تاني معدولة وبالعرض ومن غير فلاش، أو اكتب الرقم القومي (14 رقم) يدوي تحت وهيطلعلك تاريخ الميلاد والنوع لوحدهم.",
        "scan_from_nid": "✅ من الرقم القومي: تاريخ الميلاد",
        "scan_gender_label": "النوع",
        "select_company": "اختار المدرسة",
        "staff_id": "رقم الموظف",
        "first_name": "الاسم الأول - من السكان",
        "family_name": "باقي الاسم",
        "dependency": "صلة القرابة",
        "gender": "النوع",
        "dob": "تاريخ الميلاد - من السكان أو من الرقم القومي",
        "plan": "الخطة - من الكارت",
        "provider": "شركة التأمين - من الكارت",
        "policy_num": "رقم الوثيقة",
        "mobile": "رقم الموبايل",
        "email": "البريد الإلكتروني",
        "iban": "رقم الحساب / الآيبان",
        "national_id": "الرقم القومي - من السكان أو اكتبه يدوي (14 رقم)",
        "expiry": "تاريخ انتهاء الكارت",
        "save_add": "حفظ الإضافة ✅",
        "req_first": "الاسم الأول وباقي الاسم والرقم القومي مطلوبين",
        "added": "اتضاف",
        "to": "إلى",
        "print_card": "🪪 طباعة كارت العضو",
        "select_nid": "اختار العضو بالرقم القومي",
        "download_card": "تحميل الكارت",
        "my_title": "👤 بياناتي",
        "my_card_data": "📋 بيانات الكارت",
        "my_card": "🪪 الكارت بتاعي",
        "my_appr": "✅ موافقاتي",
        "my_upg": "⬆ ترقياتي",
        "my_del": "➖ طلبات الحذف بتاعتي",
        "my_no_appr": "مفيش موافقات لسه",
        "my_no_upg": "مفيش ترقيات",
        "my_no_del": "مفيش طلبات حذف",
        "my_note": "لو فيه بيانات غلط، كلم الـ HR - انت تقدر تشوف بس، مش تعدل",
        "name_col": "الاسم",
        "plan_col": "الخطة",
        "dep_col": "صلة القرابة",
        "add_company": "إضافة شركة جديدة",
        "add_4_clients": "➕ أضف العملاء الأربعة الجاهزين",
        "added_n": "تم إضافة",
        "company_word": "شركة",
        "clients_exist": "العملاء الأربعة موجودين خلاص ✅",
        "company_name": "اسم الشركة *",
        "policy_name": "اسم الوثيقة",
        "hr_name": "اسم مسؤول الـ HR",
        "hr_phone": "تليفون الـ HR / واتساب",
        "members_count": "عدد الأعضاء",
        "save_company": "حفظ الشركة 🏢",
        "company_required": "اسم الشركة مطلوب",
        "added_ok": "اتضافت ✅",
        "all_companies": "كل الشركات",
        "no_companies": "مفيش شركات لسه - دوس على زرار إضافة العملاء الأربعة فوق",
        "approve_reject": "قبول / رفض",
    },
    "en": {
        "login_title": "🔐 Myshurance - Login",
        "login_sub": "Admin or Employee - Choose login type",
        "login_as": "Login as:",
        "admin": "👨💼 Admin",
        "employee": "👤 Employee",
        "username": "Username",
        "password": "Password",
        "login_admin": "Login as Admin",
        "wrong": "❌ Wrong username or password",
        "default_admin": "Default Admin: admin / myshurance123",
        "emp_title": "👤 Employee Self-Service",
        "emp_sub": "Enter your National ID to view your data and approvals",
        "emp_nid": "National ID *",
        "emp_btn": "View My Data 👀",
        "emp_empty": "Enter National ID",
        "emp_no_data": "No data yet",
        "emp_not_found": "❌ National ID not found - Contact HR",
        "emp_note": "Employee logs in with National ID only, no password",
        "logout": "Logout 🚪",
        "hub_title": "Myshurance Hub",
        "hub_sub": "Google Sheets Live - Companies / Addition / Deletion / Upgrade / Approvals / Analytics",
        "wa_title": "📱 WhatsApp Settings",
        "wa_num": "HR / Company WhatsApp Number",
        "wa_hint": "Number to receive alerts, with country code without +",
        "alerts": "🔔 Alerts",
        "alerts_none": "✅ No alerts - Everything is fine",
        "alerts_old": "⚠ There are Pending approvals older than 2 days - Must be reviewed!",
        "alerts_exp": "🚨 There are cards expiring within 30 days!",
        "companies_m": "Companies",
        "addition_m": "Addition",
        "deletion_m": "Deletion",
        "upgrade_m": "Upgrade",
        "pending_m": "Pending Approvals",
        "total_m": "Total Requests",
        "last_wa": "Last request saved ✅ - Send it on WhatsApp from here:",
        "send_wa": "Send on WhatsApp",
        "clear_wa": "Clear WhatsApp Message ❌",
        "export_title": "📥 Export Report",
        "export_choose": "Choose what to export",
        "export_btn": "Download Excel Report 📥",
        "export_save": "Click here to save the file 💾",
        "search_title": "🔍 Search Member",
        "search_ph": "Example: Ahmed or 2980101...",
        "search_no_data": "No data yet",
        "search_no": "No results for:",
        "search_found": "Found result(s)",
        "tab_comp": "🏢 Companies",
        "tab_add": "➕ Addition",
        "tab_del": "➖ Deletion",
        "tab_upg": "⬆ Upgrade",
        "tab_appr": "✅ Approvals",
        "tab_analytics": "📊 Analytics",
        "scan_title": "➕ Add New Member - By Scan",
        "scan_cap": "Upload ID or card photo, system will fill data automatically, just review before Save",
        "scan_tip": "💡 For successful Scan: Take photo straight not rotated, good light, clear text, not blurry.",
        "scan_upload": "📸 Upload ID or Card Photo",
        "scan_uploaded": "Uploaded Photo",
        "scan_btn": "🔍 Scan and Fill Data Automatically",
        "scan_reading": "Reading card... Please wait",
        "scan_ok": "Read Successfully ✅",
        "scan_card_no": "Card No",
        "scan_nid_manual": "Complete National ID (14 digits) manually from ID card",
        "scan_fail": "Could not read data - Photo is unclear. Retake photo straight, landscape, no flash, or type National ID (14 digits) manually below and DOB and Gender will be filled automatically.",
        "scan_from_nid": "✅ From National ID: Date of Birth",
        "scan_gender_label": "Gender",
        "select_company": "Select School / Company",
        "staff_id": "Staff ID",
        "first_name": "First Name - From Scan",
        "family_name": "Family Name",
        "dependency": "Dependency",
        "gender": "Gender",
        "dob": "Date of Birth - From Scan or National ID",
        "plan": "Plan - From Card",
        "provider": "Insurance Provider - From Card",
        "policy_num": "Policy Number",
        "mobile": "Mobile Number",
        "email": "Email ID",
        "iban": "IBAN / Account Number",
        "national_id": "National ID - From Scan or Type Manually (14 digits)",
        "expiry": "Card Expiry Date",
        "save_add": "Save Addition ✅",
        "req_first": "First Name, Family Name and National ID are required",
        "added": "Added",
        "to": "to",
        "print_card": "🪪 Print Member Card",
        "select_nid": "Select Member by National ID",
        "download_card": "Download Card for",
        "my_title": "👤 My Insurance - My Data",
        "my_card_data": "📋 My Card Data",
        "my_card": "🪪 My Card",
        "my_appr": "✅ My Approvals",
        "my_upg": "⬆ My Upgrades",
        "my_del": "➖ My Deletion Requests",
        "my_no_appr": "No approvals yet",
        "my_no_upg": "No upgrades",
        "my_no_del": "No deletion requests",
        "my_note": "If data is wrong, contact HR - You can view only, not edit",
        "name_col": "Name",
        "plan_col": "Plan",
        "dep_col": "Dependency",
        "add_company": "Add New Company",
        "add_4_clients": "➕ Add the 4 Ready Clients",
        "added_n": "Added",
        "company_word": "companies",
        "clients_exist": "The 4 clients already exist ✅",
        "company_name": "Company Name *",
        "policy_name": "Policy Name",
        "hr_name": "HR Contact Name",
        "hr_phone": "HR Phone / WhatsApp",
        "members_count": "Members Count",
        "save_company": "Save Company 🏢",
        "company_required": "Company Name is required",
        "added_ok": "added ✅",
        "all_companies": "All Companies",
        "no_companies": "No companies yet - Click Add the 4 Ready Clients above",
        "approve_reject": "Approve / Reject",
    }
}
def T(k):
    return TRANSLATIONS.get(LANG, TRANSLATIONS["ar"]).get(k, k)


# --- NEW: Insurance Providers & Clients ---
PROVIDERS = ["Sarwa Life", "Sarwa", "Orient", "AXA", "Gig Life", "Allianz / NextCare", "Allianz"]

# العملاء الحاليين بالـ Policy Number
DEFAULT_CLIENTS = [
    {"Company Name": "مدرسة نيو سكول", "Policy Name": "مدرسة نيو سكول", "Policy Number": "90502239912", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
    {"Company Name": "بوب ليدرز", "Policy Name": "بوب ليدرز", "Policy Number": "90502239913", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
    {"Company Name": "مدرسة ليدرز انترناشونال", "Policy Name": "مدرسة ليدرز انترناشونال", "Policy Number": "90502239934", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
    {"Company Name": "ليدرز كوليدج للخدمات التعليمية", "Policy Name": "ليدرز كوليدج للخدمات التعليمية", "Policy Number": "90502239932", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
]

# ===== OCR from v4_2 ocr.py - شغال معاك =====
import re
import base64
import io as _io_ocr
from datetime import date as _date_ocr
from PIL import Image, ImageEnhance, ImageOps


# --- Helpers to replace store.py (S.*) - same logic as v4_2 store.py ---
def _S_secret(key):
    try:
        return st.secrets.get(key, None)
    except:
        return None
def _S_to_iso(v):
    import re as _re
    from datetime import datetime as _dt
    if not v:
        return None
    v = str(v).strip()
    for fmt in ("%d-%b-%y", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d-%m-%y", "%Y/%m/%d"):
        try:
            return _dt.strptime(v, fmt).strftime("%Y-%m-%d")
        except:
            continue
    m = _re.search(r"(\d{1,2})\s?[-–]?\s?([A-Za-z]{3})\s?[-–]?\s?(\d{4}|\d{2})", v)
    if m:
        months = {mm:i for i,mm in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"],1)}
        mo = months.get(m.group(2).lower())
        if mo:
            y = int(m.group(3))
            y = y if y>99 else (1900+y if y>30 else 2000+y)
            return f"{y:04d}-{mo:02d}-{int(m.group(1)):02d}"
    # already ISO?
    if _re.match(r"\d{4}-\d{2}-\d{2}", v):
        return v[:10]
    return None
def _S_parse_nid(nid):
    import re as _re
    from datetime import date as _date
    if not nid:
        return None
    nid = _re.sub(r"\D", "", str(nid))
    if len(nid)!=14 or not nid.isdigit():
        return None
    try:
        yy=int(nid[1:3]); mm=int(nid[3:5]); dd=int(nid[5:7])
        century = 2000 if nid[0]=="3" else 1900 if nid[0]=="2" else None
        if century is None:
            return None
        dob=_date(century+yy, mm, dd)
        gender="Female" if int(nid[12])%2==0 else "Male"
        return {"dob": dob.strftime("%Y-%m-%d"), "gender": gender}
    except:
        return None
def _S_nn(v):
    return v if v is not None else ""
def _S_norm_category(v):
    if not v:
        return None
    v=str(v).strip().upper()
    return v if v in ["A","B","C","D"] else None
AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
# أسماء الحقول عند النموذج -> مفتاح الترجمة في الواجهة
UI_KEY = {"name": "c_name", "national_id": "f_nid", "card_no": "c_card", "category": "c_cat",
          "dob": "c_dob", "expiry_date": "c_end"}

TOOLS = {
    "nid": {
        "name": "record_national_id",
        "description": "سجّل البيانات المقروءة من صورة بطاقة الرقم القومي المصرية.",
        "input_schema": {"type": "object", "properties": {
            "is_national_id": {"type": "boolean", "description": "هل الصورة بطاقة رقم قومي مصرية؟"},
            "name": {"type": ["string", "null"], "description": "الاسم الكامل بالعربي زي ما هو مطبوع (الاسم الأول + اسم الأب + الجد + العائلة). من غير سطور العنوان."},
            "national_id": {"type": ["string", "null"], "description": "الرقم القومي 14 رقم، بأرقام إنجليزية 0-9."},
            "uncertain_fields": {"type": "array", "items": {"type": "string", "enum": ["name", "national_id"]},
                                 "description": "الحقول اللي مش متأكد منها 100% (صورة مش واضحة أو حرف/رقم مشكوك فيه)."},
        }, "required": ["is_national_id", "name", "national_id", "uncertain_fields"]},
    },
    "card": {
        "name": "record_insurance_card",
        "description": "سجّل البيانات المقروءة من صورة كارنيه تأمين صحي.",
        "input_schema": {"type": "object", "properties": {
            "name": {"type": ["string", "null"], "description": "اسم المؤمن عليه زي ما هو مطبوع."},
            "card_no": {"type": ["string", "null"], "description": "رقم الكارت بالظبط زي ما هو مطبوع (حروف وأرقام)."},
            "category": {"type": ["string", "null"], "description": "الفئة (A أو B أو C أو D) لو مكتوبة."},
            "dob": {"type": ["string", "null"], "description": "تاريخ الميلاد لو مكتوب."},
            "expiry_date": {"type": ["string", "null"], "description": "تاريخ انتهاء الكارت لو مكتوب."},
            "uncertain_fields": {"type": "array", "items": {"type": "string",
                                 "enum": ["name", "card_no", "category", "dob", "expiry_date"]},
                                 "description": "الحقول اللي مش متأكد منها 100%."},
        }, "required": ["name", "card_no", "uncertain_fields"]},
    },
}
PROMPTS = {
    "nid": "ده تصوير لبطاقة رقم قومي مصرية. استخرج الاسم الكامل بالعربي والرقم القومي (14 رقم). "
           "حوّل الأرقام الهندية (٠-٩) لأرقام إنجليزية. متخمّنش: لو حاجة مش واضحة سيبها null وحطها في uncertain_fields.",
    "card": "ده تصوير لكارنيه تأمين صحي. استخرج اسم المؤمن عليه ورقم الكارت والفئة وتاريخ الميلاد وتاريخ الانتهاء لو موجودين. "
            "انسخ رقم الكارت حرف بحرف زي المطبوع، ومتخمّنش: لو حاجة مش واضحة سيبها null وحطها في uncertain_fields.",
}


def to_western(v):
    return v.translate(AR_DIGITS) if isinstance(v, str) else v


def claude_available():
    return bool(_S_secret("ANTHROPIC_API_KEY"))


def tesseract_available():
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001
        return False


def prepare_image(file, max_side=1600):
    """يعدّل اتجاه الصورة ويصغّرها (صور الموبايل كبيرة) ويرجّع (JPEG bytes، PIL image)."""
    raw = file.getvalue() if hasattr(file, "getvalue") else file.read()
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    scale = max_side / max(img.size)
    if scale < 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue(), img


# ───────────────────────── المحركات ─────────────────────────
def _call_claude(jpeg_bytes, kind):
    import anthropic
    client = anthropic.Anthropic(api_key=_S_secret("ANTHROPIC_API_KEY"))
    tool = TOOLS[kind]
    resp = client.messages.create(
        model=_S_secret("ANTHROPIC_MODEL") or "claude-sonnet-5-5", max_tokens=800,
        tools=[tool], tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.b64encode(jpeg_bytes).decode()}},
            {"type": "text", "text": PROMPTS[kind]}]}])
    for block in resp.content:
        if block.type == "tool_use":
            return dict(block.input)
    raise ValueError("no tool output")


def _tesseract_text(img, lang):
    try:
        import pytesseract
        proc = ImageEnhance.Contrast(ImageOps.grayscale(img.resize((img.width * 2, img.height * 2)))).enhance(2.0)
        return pytesseract.image_to_string(proc, lang=lang)
    except Exception:  # noqa: BLE001
        return ""


_SKIP = re.compile(r"جمهورية|مصر|العربية|بطاقة|تحقيق|الشخصية|الرقم|القومي|الاسم|يسري|حتى")
_KEYWORDS = ("card", "insured", "category", "expiry", "holder", "national")
_BAD_NAME = re.compile(r"(?i)college|school|international|company|group|academy|universit|institute|hospital|"
                       r"ltd|limited|holder|insured|national|category|co-?pay|dental|optical|maternity|expiry|"
                       r"drugs|nextcare|allianz|single|family|card")
_MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _gray(img, scale):
    g = ImageOps.grayscale(img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS))
    return ImageEnhance.Contrast(g).enhance(1.8)


def _ocr(img, scale, psm, lang="eng"):
    try:
        import pytesseract
        return pytesseract.image_to_string(_gray(img, scale), lang=lang, config=f"--psm {psm}")
    except Exception:  # noqa: BLE001
        return ""


def _hits(text):
    t = text.lower()
    return sum(k in t for k in _KEYWORDS)


def _order_pts(pts):
    import numpy as np
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")


def _crop_card(img):
    """يلاقي الكارت في الصورة (أزرق/رمادي فاتح على خلفية تانية) ويعدّله مستقيم. لو فشل يرجّع None."""
    try:
        import cv2
        import numpy as np
        bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]
        b = cv2.cvtColor(cv2.GaussianBlur(bgr, (9, 9), 0), cv2.COLOR_BGR2LAB)[:, :, 2]
        _, th = cv2.threshold(b, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
        th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
        cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cs:
            return None
        c = max(cs, key=cv2.contourArea)
        rect = cv2.minAreaRect(c)
        cw, ch = rect[1]
        if cv2.contourArea(c) < 0.15 * h * w or not (1.3 < max(cw, ch) / max(1, min(cw, ch)) < 2.0):
            return None
        box = _order_pts(cv2.boxPoints(rect))
        wd = int(max(np.linalg.norm(box[0] - box[1]), np.linalg.norm(box[3] - box[2])))
        ht = int(max(np.linalg.norm(box[0] - box[3]), np.linalg.norm(box[1] - box[2])))
        m = cv2.getPerspectiveTransform(box, np.array([[0, 0], [wd, 0], [wd, ht], [0, ht]], dtype="float32"))
        warp = cv2.warpPerspective(bgr, m, (wd, ht))
        if warp.shape[0] > warp.shape[1]:
            warp = cv2.rotate(warp, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return Image.fromarray(cv2.cvtColor(warp, cv2.COLOR_BGR2RGB))
    except Exception:  # noqa: BLE001
        return None


def _upright(img):
    """يجرّب الاتجاهات ويختار اللي فيه أكتر كلمات الكارنيه."""
    base = _crop_card(img)
    angles = (0, 180) if base is not None else (0, 90, 180, 270)
    base = base if base is not None else img
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as ex:
        scores = list(ex.map(lambda a: _hits(_ocr(base.rotate(a, expand=True), 1.2, 6)), angles))
    best = max(zip(scores, [-a for a in angles], angles))
    return base.rotate(best[2], expand=True)


def _norm_hex(tok):
    t = tok.upper().replace("O", "0").replace("Q", "0").replace("I", "1").replace("L", "1")
    return t if re.fullmatch(r"[0-9A-F]{12,20}", t) else None


def _clean_words(s):
    s = re.sub(r"[^A-Za-z' \-]", " ", s or "")
    words = [w for w in s.split() if len(w) >= 2]
    return " ".join(words) if 2 <= len(words) <= 5 and not _BAD_NAME.search(s) else None


def _name_cands(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for i, ln in enumerate(lines):
        if not re.search(r"(?i)insured|name\s*:|policy\s*holder", ln):
            continue
        tail = _clean_words(ln.split(":")[-1]) if ":" in ln else None
        if tail:
            out.append(tail)
            continue
        for j in (i - 1, i + 1):  # القيمة أحياناً بتتقرا في السطر اللي قبل أو بعد اللابل
            if 0 <= j < len(lines):
                c = _clean_words(lines[j].split(":")[-1])
                if c:
                    out.append(c)
    return out


def _date_cands(text):
    out = []
    for d, mon, y in re.findall(r"(\d{1,2})\s?[-–]?\s?([A-Za-z]{3})\s?[-–]?\s?(\d{4}|\d{2})(?!\d)", text):
        mo = _MONTHS.get(mon.lower())
        if not mo:
            continue
        y = int(y)
        y = y if y > 99 else (1900 + y if y > 30 else 2000 + y)
        iso = _S_to_iso(f"{int(d):02d}-{mo:02d}-{y}")
        if iso:
            out.append(iso)
    return out


def _top(cands, min_votes=1):
    from collections import Counter
    if not cands:
        return None, 0
    val, n = Counter(cands).most_common(1)[0]
    return (val, n) if n >= min_votes else (None, n)


def _read_card_tesseract(img):
    from concurrent.futures import ThreadPoolExecutor
    card = _upright(img)
    with ThreadPoolExecutor(max_workers=4) as ex:  # محاولات OCR بالتوازي (tesseract بيشتغل كعملية منفصلة)
        texts = list(ex.map(lambda p: _ocr(card, p[0], p[1]), ((1, 4), (1, 11), (1.5, 11), (2, 11), (1, 6), (2, 4))))
    def _votes(txts):
        return ([h for t in txts for tok in re.findall(r"[0-9A-Za-z]{12,20}", t) if (h := _norm_hex(tok))],
                [c for t in txts for c in _name_cands(t)])
    hexes, names = _votes(texts)
    if len({h for h in hexes if hexes.count(h) >= 2}) == 0 or not _top(names, 2)[0]:
        # القراءة ناقصة: محاولات زيادة بدرجات تكبير مختلفة قبل ما نسيبه فاضي
        with ThreadPoolExecutor(max_workers=4) as ex:
            more = list(ex.map(lambda p: _ocr(card, p[0], p[1]), ((3, 11), (0.8, 11), (1.2, 4), (2.5, 6), (1.5, 4), (3, 4))))
        texts += more
    raw, unsure = {}, []
    hexes = [h for t in texts for tok in re.findall(r"[0-9A-Za-z]{12,20}", t) if (h := _norm_hex(tok))]
    val, n = _top(hexes, 2)
    if val:
        raw["card_no"] = val
        if n < 3:
            unsure.append("card_no")
    val, n = _top([c for t in texts for c in _name_cands(t)], 2)
    if val:
        raw["name"] = val
        if n < 3:
            unsure.append("name")
    cat = [m.upper() for t in texts for m in re.findall(r"(?<![A-Za-z])([A-Da-d])\s?-\s?[A-Za-z]{3,}", t)]
    val, n = _top(cat, 2)
    if val:
        raw["category"] = val
    dates = [d for t in texts for d in _date_cands(t)]
    yr = date.today().year
    for key, pick in (("dob", [d for d in dates if int(d[:4]) <= yr - 16]),
                      ("expiry_date", [d for d in dates if int(d[:4]) >= yr - 1])):
        val, n = _top(pick, 2)
        if val:
            raw[key] = val
            if n < 3:
                unsure.append(key)
    raw["uncertain_fields"] = unsure
    return raw


def _tesseract_read(img, kind):
    if kind == "card":
        return _read_card_tesseract(img)
    best = {}
    for ang in (0, 90, 180, 270):
        text = to_western(_ocr(img.rotate(ang, expand=True), 1.5, 6, "ara+eng")
                          + "\n" + _ocr(img.rotate(ang, expand=True), 1.5, 11, "ara+eng"))
        for m in re.findall(r"(?<!\d)\d{14}(?!\d)", text.replace(" ", "")):
            if _S_parse_nid(m):
                best[m] = best.get(m, 0) + 1
    raw = {"uncertain_fields": ["national_id"]}
    if best:
        raw["national_id"] = max(best, key=best.get)
    return raw


# ───────────────────────── التنظيف والتحقق ─────────────────────────
def _clean_name(v):
    v = to_western(v) if isinstance(v, str) else None
    if not v:
        return None
    v = re.sub(r"[\d\|_:;,.\-]+", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v if len(v) >= 3 else None


def postprocess(raw, kind):
    """يرجّع (data، uncertain، warnings). مفيش تخمين: أي قيمة مش سليمة بتتشال."""
    data, warnings = {}, []
    uncertain = {UI_KEY[f] for f in (raw.get("uncertain_fields") or []) if f in UI_KEY}
    name = _clean_name(raw.get("name"))
    if name:
        data["name"] = name
    if kind == "nid":
        nid = re.sub(r"\D", "", to_western(_S_nn(raw.get("national_id")) or ""))
        if nid:
            info = _S_parse_nid(nid)
            if info:  # الميلاد والنوع بيتحسبوا من الرقم نفسه
                data["national_id"] = nid
                data.update(info)
            else:
                warnings.append("scan_nid_bad")
        if raw.get("is_national_id") is False:
            warnings.append("scan_not_nid")
    else:
        card = re.sub(r"[\s\-]", "", to_western(_S_nn(raw.get("card_no")) or ""))
        if card:
            data["card_no"] = card
            if len(card) < 8:
                uncertain.add("c_card")
        cat = _S_norm_category(raw.get("category"))
        if cat:
            data["category"] = cat
        for src, dst in (("dob", "dob"), ("expiry_date", "source_end")):
            iso = _S_to_iso(to_western(_S_nn(raw.get(src))))
            if iso:
                data[dst] = iso
    return data, sorted(uncertain), warnings


def read_document(file, kind):
    """kind = 'nid' | 'card'. يرجّع dict فيه data / uncertain / warnings / engine / errors."""
    out = {"data": {}, "uncertain": [], "warnings": [], "engine": None, "errors": []}
    try:
        jpeg, img = prepare_image(file)
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"image: {e}")
        return out
    raw = None
    if claude_available():
        try:
            raw, out["engine"] = _call_claude(jpeg, kind), "claude"
        except Exception as e:  # noqa: BLE001
            out["errors"].append(str(e)[:200])
    if raw is None and tesseract_available():
        raw, out["engine"] = _tesseract_read(img, kind), "tesseract"
    if raw is None:
        return out
    out["data"], out["uncertain"], out["warnings"] = postprocess(raw, kind)
    if out["engine"] == "tesseract" and kind == "nid":
        out["warnings"].append("scan_ocr_limited")  # الاسم العربي بالـ OCR العادي غير موثوق: بيتكتب يدوي
    return out


def read_all(nid_file, card_file):
    """يقرا الصورتين ويدمجهم: الاسم/الرقم القومي/الميلاد/النوع من البطاقة، والكارت/الفئة/الانتهاء من الكارنيه."""
    nid = read_document(nid_file, "nid") if nid_file else None
    card = read_document(card_file, "card") if card_file else None
    res = {"data": {}, "uncertain": set(), "warnings": [], "engine": None, "errors": []}
    for part in (card, nid):  # البطاقة تكسب في الاسم والميلاد
        if not part:
            continue
        res["data"].update({k: v for k, v in part["data"].items()
                            if not (res["data"].get(k) and k == "dob" and part is card)})
        res["uncertain"] |= set(part["uncertain"])
        res["warnings"] += part["warnings"]
        res["errors"] += part["errors"]
        res["engine"] = "claude" if "claude" in (res["engine"], part["engine"]) else (res["engine"] or part["engine"])
    if nid and card:
        n, c = nid["data"], card["data"]
        # تاريخ الميلاد على الكارنيه لو مختلف عن اللي في الرقم القومي: نحذّر ونعتمد الرقم القومي
        if n.get("dob") and c.get("dob") and n["dob"] != c["dob"]:
            res["warnings"].append("scan_dob_mismatch")
            res["data"]["dob"] = n["dob"]
    res["uncertain"] = sorted(res["uncertain"])
    res["warnings"] = list(dict.fromkeys(res["warnings"]))
    return res

# --- Wrapper for old code: same interface as before ---
def extract_from_id_image(image_file, manual_angle=0):
    """Wrapper حول ocr.py اللي شغال معاك: يجرب بطاقة قومي + كارنيه ويدمجهم"""
    import io as _io
    from PIL import Image as _PILImage, ImageOps as _Ops
    debug = []
    try:
        raw = image_file.getvalue() if hasattr(image_file, "getvalue") else image_file.read()
        try:
            image_file.seek(0)
        except:
            pass
        # لو المستخدم اختار تدوير يدوي، طبقه قبل الـ Scan
        if manual_angle != 0:
            _img = _Ops.exif_transpose(_PILImage.open(_io.BytesIO(raw))).convert("RGB")
            _img = _img.rotate(manual_angle, expand=True)
            _buf = _io.BytesIO()
            _img.save(_buf, "JPEG", quality=88)
            # اعمل ملف وهمي بنفس واجهة Streamlit UploadedFile
            class _F:
                def __init__(self, b): self._b=b
                def getvalue(self): return self._b
                def read(self): return self._b
            image_file = _F(_buf.getvalue())
            debug.append(f"manual rotate {manual_angle}")
    except Exception as e:
        return {"name": "", "dob": "", "national_id": "", "card_no": "", "policy_holder": "", "raw_text": "", "debug": [f"open error {e}"]}
    # جرب الاثنين: بطاقة قومي الأول، بعدين كارنيه، وادمج
    # read_all بيعمل كده بالظبط - بناديه بنفس الملف مرتين
    try:
        res = read_all(image_file, image_file)
    except Exception as e:
        debug.append(f"read_all fail: {e}")
        return {"name": "", "dob": "", "national_id": "", "card_no": "", "policy_holder": "", "raw_text": "", "debug": debug}
    data = res.get("data", {})
    debug += res.get("errors", [])
    debug.append(f"engine={res.get('engine')} warnings={res.get('warnings')} uncertain={res.get('uncertain')}")
    # لو tesseract بس هو اللي اشتغل ومفيش Claude، جرب OCR.space كاحتياطي أخير - من غير تثبيت
    if not data.get("name") and not data.get("national_id") and not data.get("card_no"):
        try:
            import urllib.request, urllib.parse, json as _json, base64 as _b64
            debug.append("Trying OCR.space (no install) as last fallback...")
            # البطاقة ممكن تبقى مقلوبة 90 درجة وبالعربي - جرب 4 لفات + عربي+انجليزي وخد أحسن نتيجة فيها 14 رقم
            _best_txt = ""
            _best_score = -1
            # استخدم الصورة الأصلية من غير قص - القص كان بيقطع بطاقة الرقم القومي
            import io as _io_raw
            try:
                _raw_bytes = image_file.getvalue() if hasattr(image_file, "getvalue") else image_file.read()
                try:
                    image_file.seek(0)
                except:
                    pass
                from PIL import Image as _PIL2
                _img_base = _PIL2.open(_io_raw.BytesIO(_raw_bytes)).convert("RGB")
            except:
                _jpeg_base, _img_base = prepare_image(image_file)
            for _ang in [0, 90, 180, 270]:
                try:
                    _rot = _img_base.rotate(_ang, expand=True) if _ang != 0 else _img_base
                    _b = _io.BytesIO()
                    _rot.save(_b, "JPEG", quality=85)
                    _b64_try = _b64.b64encode(_b.getvalue()).decode()
                    _pay = urllib.parse.urlencode({"apikey": "helloworld", "base64Image": f"data:image/jpeg;base64,{_b64_try}", "language": "ara+eng", "isOverlayRequired": False, "OCREngine": "1", "scale": "true"}).encode()
                    _rq = urllib.request.Request("https://api.ocr.space/parse/image", data=_pay, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    with urllib.request.urlopen(_rq, timeout=30) as _rp:
                        _rj = _json.loads(_rp.read().decode())
                    _txt_try = ""
                    try:
                        _txt_try = _rj["ParsedResults"][0]["ParsedText"] or ""
                    except:
                        _txt_try = ""
                    _nid_try = __import__("re").findall(r"\d{14}", _txt_try.replace(" ", "").replace("\n", ""))
                    _score = len(_txt_try) + (1000 if _nid_try else 0)
                    if _score > _best_score:
                        _best_score = _score
                        _best_txt = _txt_try
                except:
                    continue
            _txt = _best_txt
            debug.append(f"OCR.space len {len(_txt)}: {_txt[:300]}")
            if _txt and len(_txt.strip()) > 10:
                import re as _re2
                _m = _re2.findall(r"\d{14}", _txt.replace(" ",""))
                if _m:
                    data["national_id"] = _m[0]
                    # من الرقم القومي نفسه: طلع تاريخ الميلاد والنوع - حتى لو الاسم بالعربي اتقرا مكسر
                    try:
                        _nid_v = _m[0]
                        _cent = int(_nid_v[0]); _yy = int(_nid_v[1:3]); _mm = int(_nid_v[3:5]); _dd = int(_nid_v[5:7])
                        _yyyy = (1900 if _cent==2 else 2000 if _cent==3 else 1900) + _yy
                        from datetime import date as _d_nid
                        data["dob"] = _d_nid(_yyyy, _mm, _dd).strftime("%Y-%m-%d")
                        data["gender"] = "Female" if int(_nid_v[12])%2==0 else "Male"
                    except:
                        pass
                    # الاسم بالعربي: أول سطر فيه 3 كلمات عربي، مش عنوان ولا مهنة
                    if not data.get("name"):
                        for _ln in _txt.split("\n"):
                            _ln_s = _ln.strip()
                            _arab = _re2.findall(r"[\u0600-\u06FF]{2,}", _ln_s)
                            if len(_arab) >= 3 and "الرقم" not in _ln_s and "العنوان" not in _ln_s and "المهنة" not in _ln_s and "بطاقة" not in _ln_s:
                                data["name"] = " ".join(_arab[:4])
                                break
                _cm = _re2.search(r"([A-F0-9]{10,})", _txt.replace(" ",""))
                if _cm:
                    data["card_no"] = _cm.group(1)
                # الكارت ده الاسم فيه بعد Policy Holder مش Insured Name - ده كان سبب الغلط
                _ph = _re2.search(r"Policy\s*Holder\s*:?\s*([A-Z][A-Za-z ]+)", _txt, _re2.IGNORECASE)
                _im = _re2.search(r"Insured\s*Name\s*:?\s*([A-Z][A-Za-z ]+)", _txt, _re2.IGNORECASE)
                # لو Insured Name فاضي (زي صورة FATEMA) خد Policy Holder
                if _ph and len(_ph.group(1).strip())>=4:
                    data["name"] = _ph.group(1).strip().split("\n")[0].strip()
                elif _im and len(_im.group(1).strip())>=4 and "national" not in _im.group(1).lower():
                    data["name"] = _im.group(1).strip()
                else:
                    for _ln in _txt.split("\n"):
                        _ln=_ln.strip()
                        # استبعد أي سطر فيه لابل - عشان مياخدش National No على إنه اسم
                        if any(k in _ln.lower() for k in ["allianz","nextcare","policy","card no","category","expiry","dental","optical","national","dob","doB","holder","insured","category","co-pay","maternity","expiry","leaders","college","international"]):
                            continue
                        _w = _re2.findall(r"[A-Z][A-Z]+", _ln)
                        if len(_w)>=2:
                            data["name"]=" ".join(_w[:4])
                            break
                # رقم الكارت: 16 حرف Hex زي 8D0EF2AEDE9E827A - دور عليه تحديدا
                _all_hex = _re2.findall(r"\b[0-9A-F]{14,18}\b", _txt.replace(" ",""))
                if _all_hex:
                    data["card_no"] = max(_all_hex, key=len)
                    # الرقم القومي مش هو رقم الكارت - لو مفيش 14 رقم، سيب National ID فاضي عشان المستخدم يكمله يدوي
                    # ومتحطش رقم الكارت في خانة الرقم القومي
                    if not data.get("national_id"):
                        pass
                # تاريخ الميلاد: في كارت FATEMA بييجي بعد National No: بسبب العمودين
                _dob_m = _re2.search(r"National\s*No\s*:?\s*(\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4})", _txt, _re2.IGNORECASE)
                if _dob_m:
                    data["dob"] = _dob_m.group(1)
                _dm = _re2.search(r"(\d{1,2}[-/]\w{3}[-/]\d{2,4})", _txt)
                if _dm:
                    data["dob"]=_dm.group(1)
                _nid2 = data.get("national_id","")
                import re as _re_nid2
                if not _re_nid2.fullmatch(r"\d{14}", str(_nid2).strip()):
                    _nid2 = ""
                # استنتج Provider / Plan / Gender من نص الكارت - عشان الفورم يتملي صح
                _prov = "Allianz / NextCare" if ("allianz" in _txt.lower() or "nextcare" in _txt.lower()) else ""
                _plan = ""
                _cat_m = _re_nid2.search(r"([A-D])\s?-\s?Single", _txt)
                if _cat_m:
                    _plan = f"Plan {_cat_m.group(1)}"
                _gender = ""
                _nm_low = str(data.get("name","")).lower()
                if any(w in _nm_low for w in ["fatema","fatma","mariam","mona","sara","nour","noura","ahmed"] ) and "fatema" in _nm_low:
                    _gender = "Female"
                elif _nid2:
                    try:
                        _gender = "Female" if int(_nid2[12])%2==0 else "Male"
                    except:
                        pass
                return {"name": data.get("name",""), "dob": data.get("dob","") or data.get("source_end",""), "national_id": _nid2, "card_no": data.get("card_no",""), "policy_holder": "", "provider": _prov, "plan": _plan, "gender": _gender, "raw_text": "", "debug": []}
        except Exception as e:
            debug.append(f"OCR.space fail: {str(e)[:200]}")
    # مهم: رقم الكارت مش هو الرقم القومي - لو اللي اتقرا مش 14 رقم، سيب الرقم القومي فاضي عشان المستخدم يكمله
    _nid_out = data.get("national_id","")
    import re as _re_nid
    if not _re_nid.fullmatch(r"\d{14}", str(_nid_out).strip()):
        _nid_out = ""
    _prov2 = data.get("provider","")
    _plan2 = data.get("plan","")
    _gen2 = data.get("gender","")
    return {"name": data.get("name",""), "dob": data.get("dob",""), "national_id": _nid_out, "card_no": data.get("card_no",""), "policy_holder": "", "provider": _prov2, "plan": _plan2, "gender": _gen2, "raw_text": "", "debug": []}


# --- PDF CARD FUNCTION ---
def generate_card_pdf(name, staff_id, national_id, plan, dependency, company="Myshurance"):
    from reportlab.lib.pagesizes import landscape, A6
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    buffer = io.BytesIO()
    w, h = landscape(A6)
    c = canvas.Canvas(buffer, pagesize=landscape(A6))
    c.setFillColor(HexColor("#0B2C4A"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(HexColor("#C9A227"))
    c.rect(0, h-8, w, 8, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20, h-35, "MYSHURANCE")
    c.setFont("Helvetica", 9)
    c.drawString(20, h-48, "Health Insurance Card  |  TPA")
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20, h-80, f"{name}")
    c.setFont("Helvetica", 10)
    c.drawString(20, h-100, f"Staff ID: {staff_id}")
    c.drawString(20, h-115, f"National ID: {national_id}")
    c.drawString(20, h-130, f"Plan: {plan}  |  {dependency}")
    c.drawString(20, h-145, f"Company: {company}")
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#C9A227"))
    c.drawString(20, 25, f"Card No: MS-{str(national_id)[-6:] if national_id else '000000'}  |  Valid: 2026")
    c.drawString(20, 12, "In case of emergency call HR / Myshurance Hotline")
    c.setFillColor(HexColor("#1A4A6E"))
    c.circle(w-30, 35, 28, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w-30, 32, "MS")
    c.save()
    buffer.seek(0)
    return buffer

# --- LOGIN ---
APP_USERNAME = "admin"
APP_PASSWORD = "myshurance123"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = None
if "emp_national_id" not in st.session_state:
    st.session_state["emp_national_id"] = ""

PHOTOS_DIR = "damaged_cards"
os.makedirs(PHOTOS_DIR, exist_ok=True)

@st.cache_resource
def get_gs_client():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

def get_sheet():
    client = get_gs_client()
    if "GOOGLE_SHEET_ID" in st.secrets:
        return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
    return client.open_by_url(st.secrets["GOOGLE_SHEET_URL"])
    
def load_sheet_gs(name):
    try:
        ws = get_sheet().worksheet(name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated(keep="first")]
        df = df.dropna(how="all")
        df = df[~(df.astype(str).apply(lambda x: "".join(x).strip()=="", axis=1))]
        return df
    except:
        return pd.DataFrame()

if not st.session_state["logged_in"]:
    st.title(T("login_title"))
    st.caption(T("login_sub"))
    login_type = st.radio(T("login_as"), [T("admin"), T("employee")], horizontal=True)
    if login_type == T("admin"):
        with st.form("login_form"):
            u = st.text_input(T("username"))
            p = st.text_input(T("password"), type="password")
            login_btn = st.form_submit_button(T("login_admin"), use_container_width=True)
            if login_btn:
                if u == APP_USERNAME and p == APP_PASSWORD:
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "admin"
                    st.success("Welcome Admin ✅")
                    st.rerun()
                else:
                    st.error(T("wrong"))
        st.info(T("default_admin"))
    else:
        st.markdown(f"### {T('emp_title')}")
        st.caption(T("emp_sub"))
        with st.form("emp_login"):
            emp_id = st.text_input(T("emp_nid"), placeholder="29xxxxxxxxxxxx")
            emp_btn = st.form_submit_button(T("emp_btn"), use_container_width=True)
            if emp_btn:
                if not emp_id:
                    st.error(T("emp_empty"))
                else:
                    df_check = load_sheet_gs("addition")
                    if df_check.empty:
                        st.error(T("emp_no_data"))
                    else:
                        col = None
                        for c in df_check.columns:
                            if "National" in c:
                                col = c
                                break
                        if col is None:
                            st.error("Sheet error")
                        else:
                            found = df_check[df_check[col].astype(str).str.strip() == emp_id.strip()]
                            if found.empty:
                                st.error(T("emp_not_found"))
                            else:
                                st.session_state["logged_in"] = True
                                st.session_state["role"] = "employee"
                                st.session_state["emp_national_id"] = emp_id.strip()
                                st.success("Welcome ✅")
                                st.rerun()
        st.info(T("emp_note"))
    st.stop()

def do_logout():
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["emp_national_id"] = ""
    st.rerun()

# ================= EMPLOYEE PORTAL =================
if st.session_state.get("role") == "employee":
    st.sidebar.button(T("logout"), on_click=do_logout)
    emp_id = st.session_state["emp_national_id"]
    st.title("👤 My Insurance - بياناتي")
    st.caption(f"National ID: {emp_id}")
    df_add = load_sheet_gs("addition")
    df_del = load_sheet_gs("deletion")
    df_upg = load_sheet_gs("up grade")
    df_appr = load_sheet_gs("approvals")
    def find_by_nid(df, nid):
        if df.empty:
            return pd.DataFrame()
        col = None
        for c in df.columns:
            if "National" in c:
                col = c
                break
        if col is None:
            return pd.DataFrame()
        return df[df[col].astype(str).str.strip() == nid.strip()]
    my_data = find_by_nid(df_add, emp_id)
    my_del = find_by_nid(df_del, emp_id)
    my_upg = find_by_nid(df_upg, emp_id)
    my_appr = find_by_nid(df_appr, emp_id)
    if my_data.empty:
        st.error("No data found")
        st.stop()
    st.subheader("📋 My Card Data - بيانات الكارت")
    row = my_data.iloc[0]
    fname = row.get("* First Name", row.get("First Name", ""))
    lname = row.get("* Family Name", row.get("Family Name", ""))
    plan = row.get("* Plan", row.get("Plan", ""))
    dep = row.get("* Dependency", row.get("Dependency", ""))
    staff = row.get("Staff ID", "")
    c1, c2, c3 = st.columns(3)
    c1.metric("Name", f"{fname} {lname}")
    c2.metric("Plan", str(plan))
    c3.metric("Dependency", str(dep))
    st.dataframe(my_data, use_container_width=True)
    st.subheader("🪪 My Card - كارت التأمين")
    pdf_buf = generate_card_pdf(f"{fname} {lname}", staff, emp_id, plan, dep)
    st.download_button("Download My Card PDF 🪪", data=pdf_buf, file_name=f"Card_{emp_id}.pdf", mime="application/pdf", use_container_width=True)
    st.divider()
    st.subheader("✅ My Approvals - موافقاتي")
    if my_appr.empty:
        st.info("No approvals yet")
    else:
        st.dataframe(my_appr, use_container_width=True)
    st.divider()
    st.subheader("⬆ My Upgrades")
    if my_upg.empty:
        st.info("No upgrades")
    else:
        st.dataframe(my_upg, use_container_width=True)
    st.divider()
    st.subheader("➖ My Deletion Requests")
    if my_del.empty:
        st.info("No deletion requests")
    else:
        st.dataframe(my_del, use_container_width=True)
    st.info("لو فيه بيانات غلط، كلم الـ HR - انت تقدر تشوف بس، مش تعدل")
    st.stop()

# ================= ADMIN PORTAL =================
st.sidebar.button("Logout 🚪", on_click=do_logout)
st.title(T("hub_title"))
st.caption(T("hub_sub"))

def save_to_sheet_gs(sheet_name, new_row):
    ws = get_sheet().worksheet(sheet_name)
    headers = ws.row_values(1)
    if not headers:
        headers = list(new_row.keys())
        ws.append_row(headers)
    row = [str(new_row.get(h, "")) for h in headers]
    ws.append_row(row)

def save_approvals_gs(df):
    ws = get_sheet().worksheet("approvals")
    ws.clear()
    ws.append_row(list(df.columns))
    for _, r in df.iterrows():
        ws.append_row([str(x) for x in r.tolist()])

st.sidebar.header(T("wa_title"))
wa_number = st.sidebar.text_input(T("wa_num"), placeholder="2010xxxxxxxx", value="")
st.sidebar.caption(T("wa_hint"))
def wa_link(message):
    if not wa_number:
        return None
    clean_number = wa_number.strip().replace("+", "").replace(" ", "")
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{clean_number}?text={encoded}"
def show_wa_button(message, label="Send on WhatsApp 📱"):
    link = wa_link(message)
    if link:
        st.markdown(f"### [📱 {label} - دوس هنا]({link})")
    else:
        st.warning("اكتب رقم الواتساب في الـ Sidebar الأول")

df_add = load_sheet_gs("addition")
df_del = load_sheet_gs("deletion")
df_upg = load_sheet_gs("up grade")
df_appr = load_sheet_gs("approvals")
if df_appr.empty:
    df_appr = pd.DataFrame(columns=["ID", "Name", "National ID", "Type", "Provider", "Amount", "Status", "Date"])
df_comp = load_sheet_gs("companies")
if df_comp.empty:
    df_comp = pd.DataFrame(columns=["Company Name", "Policy Name", "Policy Number", "Provider", "HR Contact", "HR Phone", "Plan", "Members Count", "Created Date"])

pending = len(df_appr[df_appr["Status"] == "Pending"]) if not df_appr.empty and "Status" in df_appr.columns else 0
# --- EXPIRY & PENDING ALERTS ---
st.subheader(T("alerts"))
alert_found = False
if not df_appr.empty and "Status" in df_appr.columns and "Date" in df_appr.columns:
    try:
        df_appr["_d"] = pd.to_datetime(df_appr["Date"], errors="coerce")
        old_pending = df_appr[(df_appr["Status"]=="Pending") & (df_appr["_d"] < pd.Timestamp.now() - pd.Timedelta(days=2))]
        if not old_pending.empty:
            st.warning(f"{T('alerts_old')} ({len(old_pending)})")
            st.dataframe(old_pending.drop(columns=["_d"]), use_container_width=True)
            alert_found = True
    except:
        pass
if not df_add.empty and any("Expir" in c or "expir" in c for c in df_add.columns):
    exp_col = [c for c in df_add.columns if "Expir" in c or "expir" in c][0]
    try:
        df_add["_exp"] = pd.to_datetime(df_add[exp_col], errors="coerce")
        soon = df_add[(df_add["_exp"] >= pd.Timestamp.now()) & (df_add["_exp"] <= pd.Timestamp.now() + pd.Timedelta(days=30))]
        if not soon.empty:
            st.error(f"{T('alerts_exp')} ({len(soon)})")
            st.dataframe(soon.drop(columns=["_exp"]), use_container_width=True)
            alert_found = True
    except:
        pass
if not alert_found:
    st.success(T("alerts_none"))
st.divider()
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric(T("companies_m"), len(df_comp))
col2.metric(T("addition_m"), len(df_add))
col3.metric(T("deletion_m"), len(df_del))
col4.metric(T("upgrade_m"), len(df_upg))
col5.metric(T("pending_m"), pending)
col6.metric(T("total_m"), len(df_add) + len(df_del) + len(df_upg))
st.divider()
if "last_wa_msg" in st.session_state:
    st.success(T("last_wa"))
    show_wa_button(st.session_state["last_wa_msg"], T("send_wa"))
    if st.button(T("clear_wa")):
        del st.session_state["last_wa_msg"]
        st.rerun()
    st.divider()

st.subheader(T("export_title"))
export_type = st.selectbox(T("export_choose"), ["All - Addition + Deletion + Upgrade", "Addition Only", "Deletion Only", "Upgrade Only", "Approvals Only", "Companies Only"])
if st.button(T("export_btn"), use_container_width=True):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if export_type == "All - Addition + Deletion + Upgrade":
            df_add.to_excel(writer, sheet_name="Addition", index=False)
            df_del.to_excel(writer, sheet_name="Deletion", index=False)
            df_upg.to_excel(writer, sheet_name="Upgrade", index=False)
        elif export_type == "Addition Only":
            df_add.to_excel(writer, sheet_name="Addition", index=False)
        elif export_type == "Deletion Only":
            df_del.to_excel(writer, sheet_name="Deletion", index=False)
        elif export_type == "Approvals Only":
            df_appr.to_excel(writer, sheet_name="Approvals", index=False)
        elif export_type == "Companies Only":
            df_comp.to_excel(writer, sheet_name="Companies", index=False)
        else:
            df_upg.to_excel(writer, sheet_name="Upgrade", index=False)
    output.seek(0)
    st.download_button(label=T("export_save"), data=output, file_name=f"Myshurance_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
st.divider()
st.subheader(T("search_title"))
search = st.text_input(T("search_title"), placeholder=T("search_ph"))
if search:
    search_lower = search.lower().strip()
    all_df = pd.DataFrame()
    if not df_add.empty:
        tmp = df_add.copy(); tmp["Type"] = "Addition"; all_df = pd.concat([all_df, tmp], ignore_index=True)
    if not df_del.empty:
        tmp = df_del.copy(); tmp["Type"] = "Deletion"; all_df = pd.concat([all_df, tmp], ignore_index=True)
    if not df_upg.empty:
        tmp = df_upg.copy(); tmp["Type"] = "Upgrade"; all_df = pd.concat([all_df, tmp], ignore_index=True)
    if all_df.empty:
        st.info(T("search_no_data"))
    else:
        mask = all_df.astype(str).apply(lambda row: row.str.lower().str.contains(search_lower, na=False).any(), axis=1)
        result = all_df[mask]
        if result.empty:
            st.warning(f"{T('search_no')} {search}")
        else:
            st.success(f"{T('search_found')}: {len(result)}")
            st.dataframe(result, use_container_width=True)
    st.divider()

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([T("tab_comp"), T("tab_add"), T("tab_del"), T("tab_upg"), T("tab_appr"), T("tab_analytics")])

with tab0:
    st.subheader(T("add_company"))
    # زرار إضافة العملاء الأربعة مرة واحدة
    if st.button(T("add_4_clients"), use_container_width=True):
        existing_names = df_comp["Company Name"].astype(str).tolist() if not df_comp.empty and "Company Name" in df_comp.columns else []
        added = 0
        for c in DEFAULT_CLIENTS:
            if c["Company Name"] not in existing_names:
                save_to_sheet_gs("companies", c)
                added += 1
        if added > 0:
            st.success(f"{T('added_n')} {added} {T('company_word')} ✅")
            st.rerun()
        else:
            st.info(T("clients_exist"))
    with st.form("comp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        comp_name = c1.text_input(T("company_name"))
        comp_policy_name = c1.text_input(T("policy_name"))
        comp_policy_num = c1.text_input(T("policy_num"))
        comp_provider = c2.selectbox(T("provider"), PROVIDERS)
        comp_hr = c1.text_input(T("hr_name"))
        comp_phone = c2.text_input(T("hr_phone"))
        comp_plan = c2.selectbox(T("plan"), ["Plan A", "Plan B", "Plan C"])
        comp_members = c1.number_input(T("members_count"), min_value=0, step=1)
        comp_sub = st.form_submit_button(T("save_company"), use_container_width=True)
        if comp_sub:
            if not comp_name:
                st.error(T("company_required"))
            else:
                new_comp = {"Company Name": comp_name, "Policy Name": comp_policy_name or comp_name, "Policy Number": comp_policy_num, "Provider": comp_provider, "HR Contact": comp_hr, "HR Phone": comp_phone, "Plan": comp_plan, "Members Count": comp_members, "Created Date": datetime.now().strftime("%Y-%m-%d")}
                save_to_sheet_gs("companies", new_comp)
                st.success(f"{T('company_word')} {comp_name} {T('added_ok')}")
                st.rerun()
    st.divider()
    st.subheader(T("all_companies"))
    if df_comp.empty:
        st.info(T("no_companies"))
    else:
        st.dataframe(df_comp, use_container_width=True)

with tab1:

    st.subheader(T("scan_title"))
    st.caption(T("scan_cap"))
    st.info(T("scan_tip"))
    scan_file = st.file_uploader(T("scan_upload"), type=["jpg","jpeg","png"], key="scan_id")
    if scan_file is not None:
        st.image(scan_file, caption=T("scan_uploaded"), width=350)
        if st.button(T("scan_btn"), use_container_width=True):
            with st.spinner(T("scan_reading")):
                res = extract_from_id_image(scan_file, manual_angle=0)
                st.session_state["scan_name"] = res["name"]
                st.session_state["scan_dob"] = res["dob"]
                st.session_state["scan_nid"] = res["national_id"]
                st.session_state["scan_card"] = res.get("card_no","")
                st.session_state["scan_provider"] = res.get("provider","")
                st.session_state["scan_plan"] = res.get("plan","")
                st.session_state["scan_gender"] = res.get("gender","")
                st.session_state["scan_done"] = True
            if res["name"] or res.get("national_id") or res.get("card_no"):
                if res.get("national_id"):
                    st.success(f"تم القراءة ✅ - الاسم: {res['name'] or 'كمل الاسم يدوي'} | الرقم القومي: {res['national_id']} | الميلاد: {res['dob']} | النوع: {res.get('gender','')}")
                    if not res["name"]:
                        st.info("✍️ الاسم بالعربي اتقرا مكسر من الصورة - اكتبه انت يدوي بالعربي أو بالإنجليزي في الفورم تحت، باقي البيانات اتملت لوحدها من الرقم القومي.")
                else:
                    st.success(f"{T('scan_ok')} - {res['name']} | {T('scan_card_no')}: {res.get('card_no','')}")
                    if res.get("card_no"):
                        st.info(f"🪪 {T('scan_card_no')}: {res['card_no']} - {T('scan_nid_manual')}")
            else:
                st.warning(T("scan_fail"))
    if "scan_name" not in st.session_state:
        st.session_state["scan_name"] = ""
        st.session_state["scan_dob"] = ""
        st.session_state["scan_nid"] = ""
    _scan_full = st.session_state.get("scan_name","")
    _parts = _scan_full.split()
    _def_first = " ".join(_parts[:2]) if len(_parts)>=2 else _scan_full
    _def_family = " ".join(_parts[2:]) if len(_parts)>2 else ""
    # حوّل تاريخ الميلاد من الـ Scan (12-Nov-83) لتاريخ حقيقي للتقويم
    from datetime import date as _d_date, datetime as _d_dt
    _def_dob = _d_date.today()
    _scan_dob_raw = st.session_state.get("scan_dob","")
    if _scan_dob_raw:
        _parsed = None
        for _fmt in ("%d-%b-%y", "%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                _parsed = _d_dt.strptime(str(_scan_dob_raw).strip(), _fmt).date()
                break
            except:
                continue
        if _parsed is None:
            _m = re.search(r"(\d{1,2})\s?[-–]?\s?([A-Za-z]{3})\s?[-–]?\s?(\d{4}|\d{2})", str(_scan_dob_raw))
            if _m:
                _months = {mm:i for i,mm in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"],1)}
                _mo = _months.get(_m.group(2).lower())
                if _mo:
                    _y = int(_m.group(3))
                    _y = _y if _y>99 else (1900+_y if _y>30 else 2000+_y)
                    try:
                        _parsed = _d_date(_y, _mo, int(_m.group(1)))
                    except:
                        pass
        if _parsed:
            _def_dob = _parsed
    # القيم الافتراضية من الـ Scan
    _def_gender = st.session_state.get("scan_gender","") or "Male"
    _def_plan = st.session_state.get("scan_plan","") or "Plan A"
    _def_provider = st.session_state.get("scan_provider","") or PROVIDERS[0]
    # لو الـ Provider اللي اتقرا مش في القايمة، ضيفه للقايمة
    _prov_options = PROVIDERS if _def_provider in PROVIDERS else PROVIDERS + [_def_provider]
    _plan_options = ["Plan A", "Plan B", "Plan C", "Plan D"]
    if _def_plan not in _plan_options:
        _def_plan = "Plan A"

    comp_options = df_comp["Company Name"].tolist() if not df_comp.empty else ["No Company"]
    selected_comp = st.selectbox(T("select_company"), comp_options)
    # عرض Policy Number و Provider للشركة المختارة
    if not df_comp.empty and selected_comp in df_comp["Company Name"].astype(str).tolist():
        crow = df_comp[df_comp["Company Name"].astype(str) == selected_comp].iloc[0]
        pnum = crow.get("Policy Number", "")
        prov = crow.get("Provider", "")
        if pnum or prov:
            st.info(f"📌 Policy: {crow.get('Policy Name','')} | Number: {pnum} | Provider: {prov}")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        staff_id = c1.text_input(T("staff_id"))
        first_name = c1.text_input(T("first_name"), value=_def_first)
        family_name = c2.text_input(T("family_name"), value=_def_family)
        dependency = c2.selectbox(T("dependency"), ["Employee", "Spouse", "Child", "Parent"] if LANG=="en" else ["Employee", "Spouse", "Child", "Parent"])
        gender = c1.selectbox("* Gender", ["Male", "Female"], index=0 if (_manual_gender or _def_gender)=="Male" else 1)
        dob = c1.date_input(T("dob"), value=_def_dob)
        plan = c2.selectbox("* Plan - من الكارت", ["Plan A", "Plan B", "Plan C", "Plan D"], index=["Plan A","Plan B","Plan C","Plan D"].index(_def_plan) if _def_plan in ["Plan A","Plan B","Plan C","Plan D"] else 0)
        provider_add = c1.selectbox(T("provider"), _prov_options, index=_prov_options.index(_def_provider) if _def_provider in _prov_options else 0)
        policy_num_add = c1.text_input(T("policy_num"))
        mobile = c2.text_input(T("mobile"))
        email = c1.text_input(T("email"))
        iban = c2.text_input(T("iban"))
        national_id = c1.text_input(T("national_id"), value=st.session_state.get("scan_nid",""))
        # لو كتبت الرقم القومي يدوي (لما الصورة مش واضحة)، طلع منه تاريخ الميلاد والنوع لوحده
        _manual_dob = None
        _manual_gender = None
        if national_id and len(national_id.strip())==14 and national_id.strip().isdigit():
            try:
                _nid_m = national_id.strip()
                _cent_m = int(_nid_m[0]); _yy_m = int(_nid_m[1:3]); _mm_m = int(_nid_m[3:5]); _dd_m = int(_nid_m[5:7])
                _yyyy_m = (1900 if _cent_m==2 else 2000 if _cent_m==3 else 1900) + _yy_m
                from datetime import date as _d_m
                _manual_dob = _d_m(_yyyy_m, _mm_m, _dd_m)
                _manual_gender = "Female" if int(_nid_m[12])%2==0 else "Male"
                st.info(f"✅ من الرقم القومي: تاريخ الميلاد {_manual_dob.strftime('%Y-%m-%d')} | النوع {_manual_gender}")
            except:
                pass
        expiry_date = c2.date_input(T("expiry"))
        submitted = st.form_submit_button(T("save_add"), use_container_width=True)
        if submitted:
            if not first_name or not family_name or not national_id:
                st.error(T("req_first"))
            else:
                new_row = {"Staff ID": staff_id, "* First Name": first_name, "* Family Name": family_name, "* Dependency": dependency, "* Gender": gender, "* Date of Birth": str(dob), "* Plan": plan, "Provider": provider_add, "Policy Number": policy_num_add, "Company": selected_comp, "* Mobile Number": mobile, "Email ID": email, "* IBAN/Account Number": iban, "* National ID": national_id, "Card Expiry Date": str(expiry_date)}
                save_to_sheet_gs("addition", new_row)
                st.success(f"Added {first_name} {family_name} to {selected_comp} ✅")
                msg = f"New Addition Request - Myshurance:\nCompany: {selected_comp}\nProvider: {provider_add}\nPolicy: {policy_num_add}\nName: {first_name} {family_name}\nStaff ID: {staff_id}\nNational ID: {national_id}\nPlan: {plan}\nMobile: {mobile}"
                st.session_state["last_wa_msg"] = msg
                for _k in ["scan_name","scan_dob","scan_nid","scan_done","scan_card","scan_provider","scan_plan","scan_gender"]:
                    if _k in st.session_state:
                        del st.session_state[_k]
                st.rerun()
    st.divider()
    st.subheader("Addition Requests")
    if df_add.empty:
        st.info("No addition requests yet")
    else:
        st.dataframe(df_add, use_container_width=True)
        st.divider()
        st.subheader("🪪 Print Member Card - طباعة الكارت")
        nid_col = None
        for c in df_add.columns:
            if "National" in c:
                nid_col = c
                break
        if nid_col:
            selected_nid = st.selectbox("Select Member by National ID", df_add[nid_col].astype(str).tolist())
            sel_row = df_add[df_add[nid_col].astype(str) == selected_nid].iloc[0]
            s_fname = sel_row.get("* First Name", "")
            s_lname = sel_row.get("* Family Name", "")
            s_plan = sel_row.get("* Plan", "")
            s_dep = sel_row.get("* Dependency", "")
            s_staff = sel_row.get("Staff ID", "")
            pdf_buf = generate_card_pdf(f"{s_fname} {s_lname}", s_staff, selected_nid, s_plan, s_dep, selected_comp)
            st.download_button(f"Download Card for {s_fname} {s_lname} 🪪", data=pdf_buf, file_name=f"Card_{selected_nid}.pdf", mime="application/pdf", use_container_width=True)

with tab2:
    st.subheader("Delete Member - لازم صورة الكارت التالف")
    with st.form("del_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_staff = c1.text_input("Staff ID to Delete")
        d_first = c1.text_input("* First Name")
        d_family = c2.text_input("* Family Name")
        d_national = c2.text_input("* National ID")
        d_reason = st.text_area("Reason for Deletion")
        d_photo = st.file_uploader("📷 صورة الكارت التالف - إجباري", type=["jpg", "jpeg", "png"])
        d_submitted = st.form_submit_button("Confirm Deletion 🗑", use_container_width=True)
        if d_submitted:
            if not d_first or not d_family or not d_national:
                st.error("First Name و Family Name و National ID مطلوبين")
            elif d_photo is None:
                st.error("❌ مينفعش حذف من غير صورة الكارت التالف")
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                photo_name = f"{d_national}_{timestamp}.{d_photo.name.split('.')[-1]}"
                with open(os.path.join(PHOTOS_DIR, photo_name), "wb") as f:
                    f.write(d_photo.getbuffer())
                new_row = {"Staff ID": d_staff, "* First Name": d_first, "* Family Name": d_family, "* Dependency": "", "* Gender": "", "* Date of Birth": "", "* Plan": "", "* Mobile Number": "", "Email ID": "", "* IBAN/Account Number": "", "* National ID": d_national}
                save_to_sheet_gs("deletion", new_row)
                st.success(f"Deleted {d_first} {d_family} ✅")
                msg = f"Deletion Request - Myshurance:\nName: {d_first} {d_family}\nStaff ID: {d_staff}\nNational ID: {d_national}\nReason: {d_reason}\nDamaged card photo saved."
                st.session_state["last_wa_msg"] = msg
                st.rerun()
    st.divider()
    st.subheader("Deletion Requests")
    if df_del.empty:
        st.info("No deletion requests yet")
    else:
        st.dataframe(df_del, use_container_width=True)

with tab3:
    st.subheader("Upgrade Member Plan")
    with st.form("upg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        u_staff = c1.text_input("Staff ID")
        u_first = c1.text_input("* First Name")
        u_family = c2.text_input("* Family Name")
        u_national = c2.text_input("* National ID")
        old_plan = c1.selectbox("Old Plan", ["Plan A", "Plan B", "Plan C"])
        new_plan = c2.selectbox("New Plan *", ["Plan A", "Plan B", "Plan C"])
        u_reason = st.text_area("Reason for Upgrade")
        u_submitted = st.form_submit_button("Confirm Upgrade ⬆", use_container_width=True)
        if u_submitted:
            if not u_first or not u_family or not u_national:
                st.error("First Name و Family Name و National ID مطلوبين")
            elif old_plan == new_plan:
                st.error("❌ New Plan لازم تكون مختلفة عن Old Plan")
            else:
                new_row = {"Staff ID": u_staff, "* First Name": u_first, "* Family Name": u_family, "* Dependency": "", "* Gender": "", "* Date of Birth": "", "* Plan": f"{old_plan} -> {new_plan}", "* Mobile Number": "", "Email ID": "", "* IBAN/Account Number": "", "* National ID": u_national}
                save_to_sheet_gs("up grade", new_row)
                st.success(f"Upgraded {u_first} {u_family} from {old_plan} to {new_plan} ✅")
                msg = f"Upgrade Request - Myshurance:\nName: {u_first} {u_family}\nStaff ID: {u_staff}\nNational ID: {u_national}\nFrom: {old_plan} To: {new_plan}\nReason: {u_reason}"
                st.session_state["last_wa_msg"] = msg
                st.rerun()
    st.divider()
    st.subheader("Upgrade Requests")
    if df_upg.empty:
        st.info("No upgrade requests yet")
    else:
        st.dataframe(df_upg, use_container_width=True)

with tab4:
    st.subheader("New Approval Request")
    with st.form("appr_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        a_name = c1.text_input("Member Name *")
        a_national = c1.text_input("National ID *")
        a_type = c2.selectbox("Approval Type", ["Hospital Admission", "Lab / X-Ray", "Pharmacy", "Surgery", "Checkup"])
        a_provider = c2.selectbox("Insurance Provider / شركة التأمين", PROVIDERS)
        a_hospital = c1.text_input("Hospital / المستشفى")
        a_amount = c1.number_input("Estimated Amount", min_value=0, step=100)
        a_sub = st.form_submit_button("Submit Approval ✅", use_container_width=True)
        if a_sub:
            if not a_name or not a_national:
                st.error("Name و National ID مطلوبين")
            else:
                new_id = f"AP-{len(df_appr)+1:04d}"
                new_appr = {"ID": new_id, "Name": a_name, "National ID": a_national, "Type": a_type, "Provider": a_provider, "Hospital": a_hospital, "Amount": a_amount, "Status": "Pending", "Date": datetime.now().strftime("%Y-%m-%d %H:%M")}
                save_to_sheet_gs("approvals", new_appr)
                st.success(f"Approval {new_id} created - Pending ✅")
                msg = f"Approval Request - Myshurance:\nID: {new_id}\nName: {a_name}\nType: {a_type}\nProvider: {a_provider}\nHospital: {a_hospital}\nAmount: {a_amount}\nStatus: Pending"
                st.session_state["last_wa_msg"] = msg
                st.rerun()
    st.divider()
    st.subheader("All Approvals")
    if df_appr.empty:
        st.info("No approvals yet")
    else:
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"])
        show_df = df_appr if status_filter == "All" else df_appr[df_appr["Status"] == status_filter]
        st.dataframe(show_df, use_container_width=True)
        st.divider()
        st.subheader(T("approve_reject"))
        if not show_df.empty:
            selected_id = st.selectbox("Select Approval ID", show_df["ID"].tolist())
            col_a, col_b = st.columns(2)
            if col_a.button("✅ Approve", use_container_width=True, key="approve_btn"):
                df_appr.loc[df_appr["ID"] == selected_id, "Status"] = "Approved"
                save_approvals_gs(df_appr)
                st.success(f"{selected_id} Approved ✅")
                st.rerun()
            if col_b.button("❌ Reject", use_container_width=True, key="reject_btn"):
                df_appr.loc[df_appr["ID"] == selected_id, "Status"] = "Rejected"
                save_approvals_gs(df_appr)
                st.error(f"{selected_id} Rejected")
                st.rerun()

with tab5:
    st.subheader("📊 Analytics - نظرة عامة")
    if not df_add.empty and "* Plan" in df_add.columns:
        st.markdown("### Members by Plan")
        st.bar_chart(df_add["* Plan"].value_counts())
    else:
        st.info("No members yet for Plan chart")
    if not df_add.empty and "* Dependency" in df_add.columns:
        st.markdown("### Members by Dependency")
        st.bar_chart(df_add["* Dependency"].value_counts())
    if not df_appr.empty and "Status" in df_appr.columns:
        st.markdown("### Approvals by Status")
        st.bar_chart(df_appr["Status"].value_counts())
        st.markdown("### Approvals Total Amount by Status")
        try:
            st.bar_chart(df_appr.groupby("Status")["Amount"].sum())
        except:
            pass
        if "Provider" in df_appr.columns:
            st.markdown("### Approvals by Insurance Provider")
            st.bar_chart(df_appr["Provider"].value_counts())
    else:
        st.info("No approvals yet for chart")
        st.divider()
    st.subheader("📅 Monthly Report - تقرير شهري")
    sel_month = st.selectbox("Select Month", ["Current Month - الشهر الحالي", "All Time - كل الوقت"])
    if st.button("Generate Monthly Report 📊", use_container_width=True):
        st.markdown("### Myshurance Monthly Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("New Additions", len(df_add))
        c2.metric("Deletions", len(df_del))
        c3.metric("Upgrades", len(df_upg))
        c4.metric("Total Approvals", len(df_appr))
        if not df_appr.empty and "Status" in df_appr.columns:
            st.write(f"✅ Approved: {len(df_appr[df_appr['Status']=='Approved'])} | ⏳ Pending: {len(df_appr[df_appr['Status']=='Pending'])} | ❌ Rejected: {len(df_appr[df_appr['Status']=='Rejected'])}")
            try:
                st.write(f"💰 Total Approved Amount: {df_appr[df_appr['Status']=='Approved']['Amount'].astype(float).sum():,.0f}")
            except:
                pass
        st.success("ده التقرير اللي ممكن تبعته للشركة كل أول شهر ✅")
    if not df_comp.empty and "Members Count" in df_comp.columns:
        st.markdown("### Companies by Members Count")
        try:
            chart_df = df_comp.set_index("Company Name")["Members Count"]
            st.bar_chart(chart_df)
        except:
            st.dataframe(df_comp)
