import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
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

# --- Email to send final Excel / reports to - من المستخدم ---
NOTIFY_EMAIL = "mahmoud.asmaa@gmail.com"

# --- NEW: Insurance Providers & Clients ---
PROVIDERS = ["Sarwa Life", "Sarwa", "Orient", "AXA", "Gig Life", "Allianz / NextCare", "Allianz"]
import re, base64
from PIL import Image, ImageEnhance, ImageOps
AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
def to_western(v):
    return v.translate(AR_DIGITS) if isinstance(v, str) else v
def _S_parse_nid(nid):
    nid = re.sub(r"\D", "", str(nid or ""))
    if len(nid)!=14 or not nid.isdigit(): return None
    try:
        yy=int(nid[1:3]); mm=int(nid[3:5]); dd=int(nid[5:7])
        century = 2000 if nid[0]=="3" else 1900 if nid[0]=="2" else None
        if century is None: return None
        dob=date(century+yy, mm, dd)
        gender="Female" if int(nid[12])%2==0 else "Male"
        return {"dob": dob.strftime("%Y-%m-%d"), "gender": gender}
    except: return None

# العملاء الحاليين بالـ Policy Number
DEFAULT_CLIENTS = [
    {"Company Name": "مدرسة نيو سكول", "Policy Name": "مدرسة نيو سكول", "Policy Number": "90502239912", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
    {"Company Name": "بوب ليدرز", "Policy Name": "بوب ليدرز", "Policy Number": "90502239913", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
    {"Company Name": "مدرسة ليدرز انترناشونال", "Policy Name": "مدرسة ليدرز انترناشونال", "Policy Number": "90502239934", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
    {"Company Name": "ليدرز كوليدج للخدمات التعليمية", "Policy Name": "ليدرز كوليدج للخدمات التعليمية", "Policy Number": "90502239932", "HR Contact": "", "HR Phone": "", "Plan": "Plan A", "Members Count": 0, "Created Date": datetime.now().strftime("%Y-%m-%d")},
]

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

# --- Language: عربي / English ---
if "lang" not in st.session_state: st.session_state["lang"] = "ar"
_lang_choice = st.sidebar.radio("🌐 اللغة / Language", ["العربية", "English"], index=0 if st.session_state["lang"]=="ar" else 1)
st.session_state["lang"] = "ar" if _lang_choice=="العربية" else "en"
LANG = st.session_state["lang"]
def _L(ar, en): return ar if LANG=="ar" else en

# --- Scan: OCR.space ara+eng + 4 rotations + tesseract fallback ---
def extract_from_id_image(image_file, manual_angle=0):
    import io as _io
    from PIL import Image as _PILImage, ImageOps as _Ops
    try:
        raw = image_file.getvalue() if hasattr(image_file, "getvalue") else image_file.read()
        try: image_file.seek(0)
        except: pass
        img_base = _Ops.exif_transpose(_PILImage.open(_io.BytesIO(raw))).convert("RGB")
        if manual_angle != 0: img_base = img_base.rotate(manual_angle, expand=True)
    except Exception as e:
        return {"name": "", "dob": "", "national_id": "", "card_no": "", "provider": "", "plan": "", "gender": ""}
    data = {"name": "", "dob": "", "national_id": "", "card_no": "", "provider": "", "plan": "", "gender": ""}
    # 1) tesseract - 4 rotations, ara+eng, look for 14-digit NID
    try:
        import pytesseract
        for _ang in [0, 90, 180, 270]:
            _rot = img_base.rotate(_ang, expand=True) if _ang!=0 else img_base
            _g = ImageOps.grayscale(_rot.resize((_rot.width*2, _rot.height*2)))
            _txt = pytesseract.image_to_string(ImageEnhance.Contrast(_g).enhance(1.8), lang="ara+eng")
            _txt_w = to_western(_txt)
            _m = re.findall(r"(?<!\d)\d{14}(?!\d)", _txt_w.replace(" ", "").replace("\n", ""))
            for _c in _m:
                if _S_parse_nid(_c) and not data["national_id"]: data["national_id"] = _c
            if data["national_id"]: break
    except: pass
    # 2) OCR.space - 4 rotations, ara+eng, even if card was read but NID missing
    try:
        import urllib.request, urllib.parse, json as _json, base64 as _b64
        _best_txt, _best_score = "", -1
        for _ang in [0, 90, 180, 270]:
            _rot = img_base.rotate(_ang, expand=True) if _ang!=0 else img_base
            _b = _io.BytesIO(); _rot.save(_b, "JPEG", quality=85)
            _pay = urllib.parse.urlencode({"apikey": "helloworld", "base64Image": f"data:image/jpeg;base64,{_b64.b64encode(_b.getvalue()).decode()}", "language": "ara+eng", "isOverlayRequired": False, "OCREngine": "1", "scale": "true"}).encode()
            _rq = urllib.request.Request("https://api.ocr.space/parse/image", data=_pay, headers={"Content-Type": "application/x-www-form-urlencoded"})
            try:
                with urllib.request.urlopen(_rq, timeout=30) as _rp: _rj = _json.loads(_rp.read().decode())
                _tt = ""
                try: _tt = _rj["ParsedResults"][0]["ParsedText"] or ""
                except: _tt = ""
                _nid_try = re.findall(r"\d{14}", _tt.replace(" ", ""))
                _sc = len(_tt) + (1000 if _nid_try else 0)
                if _sc > _best_score: _best_score, _best_txt = _sc, _tt
            except: continue
        _txt = _best_txt
        if _txt:
            _m = re.findall(r"\d{14}", _txt.replace(" ", ""))
            if _m and not data["national_id"]: data["national_id"] = _m[0]
            _ph = re.search(r"Policy\s*Holder\s*:?\s*([A-Z][A-Za-z ]+)", _txt, re.IGNORECASE)
            _im = re.search(r"Insured\s*Name\s*:?\s*([A-Z][A-Za-z ]+)", _txt, re.IGNORECASE)
            if _ph and len(_ph.group(1).strip())>=4: data["name"] = _ph.group(1).strip().split("\n")[0].strip()
            elif _im and len(_im.group(1).strip())>=4 and "national" not in _im.group(1).lower(): data["name"] = _im.group(1).strip()
            _hexs = re.findall(r"\b[0-9A-F]{14,18}\b", _txt.replace(" ", ""))
            if _hexs: data["card_no"] = max(_hexs, key=len)
            _dm = re.search(r"(\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4})", _txt)
            if _dm: data["dob"] = _dm.group(1)
            if "allianz" in _txt.lower() or "nextcare" in _txt.lower(): data["provider"] = "Allianz / NextCare"
            _cat = re.search(r"([A-D])\s?-\s?Single", _txt)
            if _cat: data["plan"] = f"Plan {_cat.group(1)}"
    except: pass
    # NID is NOT card_no - if not exactly 14 digits, leave empty for manual entry
    if not re.fullmatch(r"\d{14}", str(data["national_id"]).strip()): data["national_id"] = ""
    if data["national_id"]:
        _info = _S_parse_nid(data["national_id"])
        if _info: data["dob"] = _info["dob"]; data["gender"] = _info["gender"]
    elif "fatema" in str(data["name"]).lower(): data["gender"] = "Female"
    return data

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
    st.title("🔐 Myshurance - Login")
    st.caption("Admin or Employee - اختار نوع الدخول")
    login_type = st.radio("Login as:", ["👨💼 Admin", "👤 Employee - الموظف"], horizontal=True)
    if login_type == "👨💼 Admin":
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login as Admin", use_container_width=True)
            if login_btn:
                if u == APP_USERNAME and p == APP_PASSWORD:
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "admin"
                    st.success("Welcome Admin ✅")
                    st.rerun()
                else:
                    st.error("❌ Wrong username or password")
        st.info("Default Admin: admin / myshurance123")
    else:
        st.markdown("### 👤 Employee Self-Service")
        st.caption("ادخل بالرقم القومي عشان تشوف بياناتك وموافقاتك")
        with st.form("emp_login"):
            emp_id = st.text_input("National ID - الرقم القومي *", placeholder="29xxxxxxxxxxxx")
            emp_btn = st.form_submit_button("View My Data 👀", use_container_width=True)
            if emp_btn:
                if not emp_id:
                    st.error("اكتب الرقم القومي")
                else:
                    df_check = load_sheet_gs("addition")
                    if df_check.empty:
                        st.error("No data yet")
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
                                st.error("❌ الرقم القومي مش موجود - كلم الـ HR")
                            else:
                                st.session_state["logged_in"] = True
                                st.session_state["role"] = "employee"
                                st.session_state["emp_national_id"] = emp_id.strip()
                                st.success("Welcome ✅")
                                st.rerun()
        st.info("الموظف بيدخل بالرقم القومي بس، من غير باسورد")
    st.stop()

def do_logout():
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["emp_national_id"] = ""
    st.rerun()

# ================= EMPLOYEE PORTAL =================
if st.session_state.get("role") == "employee":
    st.sidebar.button("Logout 🚪", on_click=do_logout)
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
st.title("Myshurance Hub")
st.caption("Google Sheets Live - Companies / Addition / Deletion / Upgrade / Approvals / Analytics")

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

st.sidebar.header("📧 Email - الإيميل")
st.sidebar.text_input("Final Excel will be sent to", value=NOTIFY_EMAIL, disabled=True, key="notify_email_display")
st.sidebar.caption("الشيت النهائي اللي هيتبعت لشركة التأمين هيتبعت على الإيميل ده")
st.sidebar.markdown(f"[📧 ابعت الشيت النهائي على الإيميل](mailto:{NOTIFY_EMAIL}?subject=Myshurance Final Excel - شركة التأمين)")
st.sidebar.header("📱 WhatsApp Settings")
wa_number = st.sidebar.text_input("HR / Company WhatsApp Number", placeholder="2010xxxxxxxx", value="")
st.sidebar.caption("الرقم اللي هيتبعتله التنبيه، بكود الدولة من غير +")
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
st.subheader("🔔 Alerts - تنبيهات")
alert_found = False
if not df_appr.empty and "Status" in df_appr.columns and "Date" in df_appr.columns:
    try:
        df_appr["_d"] = pd.to_datetime(df_appr["Date"], errors="coerce")
        old_pending = df_appr[(df_appr["Status"]=="Pending") & (df_appr["_d"] < pd.Timestamp.now() - pd.Timedelta(days=2))]
        if not old_pending.empty:
            st.warning(f"⚠ فيه {len(old_pending)} موافقة Pending بقالها أكتر من يومين - لازم تتراجع!")
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
            st.error(f"🚨 فيه {len(soon)} كارت هيخلص خلال 30 يوم!")
            st.dataframe(soon.drop(columns=["_exp"]), use_container_width=True)
            alert_found = True
    except:
        pass
if not alert_found:
    st.success("✅ مفيش تنبيهات - كل حاجة تمام")
st.divider()
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Companies", len(df_comp))
col2.metric("Addition", len(df_add))
col3.metric("Deletion", len(df_del))
col4.metric("Upgrade", len(df_upg))
col5.metric("Pending Approvals", pending)
col6.metric("Total Requests", len(df_add) + len(df_del) + len(df_upg))
st.divider()
if "last_final_excel" in st.session_state:
    st.success("📥 الشيت النهائي جاهز - Final Excel Ready - هيتبعت لشركة التأمين وفي نفس الوقت اتسجل في الشيت الأساسي (+1)")
    st.download_button("📥 Download Final Excel - حمّل الشيت النهائي", data=st.session_state["last_final_excel"], file_name=st.session_state.get("last_final_excel_name","Final.xlsx"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    st.markdown(f"### [📧 ابعت الشيت النهائي على {NOTIFY_EMAIL}]({st.session_state.get('last_final_email_link', f'mailto:{NOTIFY_EMAIL}')})")
    st.caption("دوس على زرار التحميل، وبعدين ابعته على الإيميل ده - الشيت الأساسي اتحدث تلقائي (+1) من غير ما ترجع لشركة التأمين")
    st.divider()
if "last_wa_msg" in st.session_state:
    st.success("آخر طلب اتسجل ✅ - ابعته واتساب من هنا:")
    show_wa_button(st.session_state["last_wa_msg"], "Send Last Request on WhatsApp")
    if st.button("Clear WhatsApp Message ❌"):
        del st.session_state["last_wa_msg"]
        st.rerun()
    st.divider()

st.subheader("📥 Export Report")
export_type = st.selectbox("Choose what to export", ["All - Addition + Deletion + Upgrade", "Addition Only", "Deletion Only", "Upgrade Only", "Approvals Only", "Companies Only"])
if st.button("Download Excel Report 📥", use_container_width=True):
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
    st.download_button(label="Click here to save the file 💾", data=output, file_name=f"Myshurance_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
st.divider()
st.subheader("🔍 Search Member")
search = st.text_input("Search by First Name, Family Name, Staff ID or National ID", placeholder="مثال: Ahmed أو 2980101...")
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
        st.info("No data yet")
    else:
        mask = all_df.astype(str).apply(lambda row: row.str.lower().str.contains(search_lower, na=False).any(), axis=1)
        result = all_df[mask]
        if result.empty:
            st.warning(f"No results for: {search}")
        else:
            st.success(f"Found {len(result)} result(s)")
            st.dataframe(result, use_container_width=True)
    st.divider()

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏢 Companies", "➕ Addition", "➖ Deletion", "⬆ Upgrade", "✅ Approvals", "📊 Analytics"])

with tab0:
    st.subheader("Add New Company")
    # زرار إضافة العملاء الأربعة مرة واحدة
    if st.button("➕ أضف العملاء الأربعة الجاهزين (نيو سكول / بوب ليدرز / ليدرز انترناشونال / ليدرز كوليدج)", use_container_width=True):
        existing_names = df_comp["Company Name"].astype(str).tolist() if not df_comp.empty and "Company Name" in df_comp.columns else []
        added = 0
        for c in DEFAULT_CLIENTS:
            if c["Company Name"] not in existing_names:
                save_to_sheet_gs("companies", c)
                added += 1
        if added > 0:
            st.success(f"تم إضافة {added} شركة ✅")
            st.rerun()
        else:
            st.info("العملاء الأربعة موجودين خلاص ✅")
    with st.form("comp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        comp_name = c1.text_input("Company Name *")
        comp_policy_name = c1.text_input("Policy Name / اسم الوثيقة")
        comp_policy_num = c1.text_input("Policy Number / رقم الوثيقة")
        comp_provider = c2.selectbox("Insurance Provider / شركة التأمين", PROVIDERS)
        comp_hr = c1.text_input("HR Contact Name")
        comp_phone = c2.text_input("HR Phone / WhatsApp")
        comp_plan = c2.selectbox("Plan", ["Plan A", "Plan B", "Plan C"])
        comp_members = c1.number_input("Members Count", min_value=0, step=1)
        comp_sub = st.form_submit_button("Save Company 🏢", use_container_width=True)
        if comp_sub:
            if not comp_name:
                st.error("Company Name مطلوب")
            else:
                new_comp = {"Company Name": comp_name, "Policy Name": comp_policy_name or comp_name, "Policy Number": comp_policy_num, "Provider": comp_provider, "HR Contact": comp_hr, "HR Phone": comp_phone, "Plan": comp_plan, "Members Count": comp_members, "Created Date": datetime.now().strftime("%Y-%m-%d")}
                save_to_sheet_gs("companies", new_comp)
                st.success(f"Company {comp_name} added ✅")
                st.rerun()
    st.divider()
    st.subheader("All Companies - العملاء")
    if df_comp.empty:
        st.info("No companies yet - دوس على زرار إضافة العملاء الأربعة فوق")
    else:
        st.dataframe(df_comp, use_container_width=True)

with tab1:
    st.subheader(_L("➕ إضافة عضو جديد - بالسكان", "➕ Add New Member - By Scan"))
    st.caption(_L("ارفع صورة البطاقة أو الكارنيه، السيستم هيملي البيانات لوحده، انت راجع بس قبل ما تدوس حفظ", "Upload ID or card photo, the system fills the data, just review before saving"))
    st.info(_L("💡 عشان السكان ينجح: صور البطاقة معدولة مش مقلوبة، في نور كويس، والكلام واضح ومش مهزوز.", "💡 For Scan to work: photo straight, good light, text clear and not shaky."))
    scan_file = st.file_uploader(_L("📸 ارفع صورة البطاقة أو الكارنيه", "📸 Upload ID or Card Photo"), type=["jpg","jpeg","png"], key="scan_id")
    if scan_file is not None:
        st.image(scan_file, caption=_L("الصورة اللي اترفعت", "Uploaded photo"), width=350)
        if st.button(_L("🔍 اعمل Scan واملا البيانات لوحدها", "🔍 Scan and Fill Data Automatically"), use_container_width=True):
            with st.spinner(_L("بقرا البطاقة... ثواني", "Reading card... please wait")):
                res = extract_from_id_image(scan_file, manual_angle=0)
                st.session_state["scan_name"] = res["name"]; st.session_state["scan_dob"] = res["dob"]
                st.session_state["scan_nid"] = res["national_id"]; st.session_state["scan_card"] = res.get("card_no","")
                st.session_state["scan_provider"] = res.get("provider",""); st.session_state["scan_plan"] = res.get("plan","")
                st.session_state["scan_gender"] = res.get("gender",""); st.session_state["scan_done"] = True
            if res["name"] or res.get("card_no") or res.get("national_id"):
                st.success(f"{_L('تم القراءة ✅','Read OK ✅')} - {res['name']} | {_L('رقم الكارت:','Card No:')} {res.get('card_no','')} | {_L('الرقم القومي:','National ID:')} {res.get('national_id','')}")
                if res.get("card_no") and not res.get("national_id"):
                    st.info(_L("🪪 رقم الكارت اتقرا - والرقم القومي (14 رقم) كمله يدوي من البطاقة الشخصية", "🪪 Card No was read - complete National ID (14 digits) manually from ID card"))
            else:
                st.warning(_L("مقدرتش أقرا البيانات - اتأكد ان الصورة واضحة وحاول تاني", "Could not read data - make sure photo is clear and try again"))
    if "scan_name" not in st.session_state:
        st.session_state["scan_name"] = ""; st.session_state["scan_dob"] = ""; st.session_state["scan_nid"] = ""
    _scan_full = st.session_state.get("scan_name","")
    _parts = _scan_full.split()
    _def_first = " ".join(_parts[:2]) if len(_parts)>=2 else _scan_full
    _def_family = " ".join(_parts[2:]) if len(_parts)>2 else ""
    from datetime import date as _d_date, datetime as _d_dt
    _def_dob = _d_date.today()
    _scan_dob_raw = st.session_state.get("scan_dob","")
    if _scan_dob_raw:
        _parsed = None
        for _fmt in ("%d-%b-%y", "%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try: _parsed = _d_dt.strptime(str(_scan_dob_raw).strip(), _fmt).date(); break
            except: continue
        if _parsed: _def_dob = _parsed
    _def_gender = st.session_state.get("scan_gender","") or "Male"
    _def_plan = st.session_state.get("scan_plan","") or "Plan A"
    _def_provider = st.session_state.get("scan_provider","") or PROVIDERS[0]
    _prov_options = PROVIDERS if _def_provider in PROVIDERS else PROVIDERS + [_def_provider]
    # بوكس الرقم القومي اليدوي - بره الفورم عشان يحدّث الميلاد والنوع فورا - _manual_gender متعرف قبل ما يتستخدم
    _manual_nid_input = st.text_input(_L("أو اكتب الرقم القومي يدوي هنا (لو السكان فشل - 14 رقم)", "Or type National ID manually here (if Scan failed - 14 digits)"), value=st.session_state.get("scan_nid",""), key="manual_nid_box", max_chars=14)
    _manual_dob = None; _manual_gender = ""
    _manual_src = (_manual_nid_input or "").strip()
    if len(_manual_src)==14 and _manual_src.isdigit():
        try:
            _cent_m = int(_manual_src[0]); _yy_m = int(_manual_src[1:3]); _mm_m = int(_manual_src[3:5]); _dd_m = int(_manual_src[5:7])
            _yyyy_m = (1900 if _cent_m==2 else 2000 if _cent_m==3 else 1900) + _yy_m
            _manual_dob = date(_yyyy_m, _mm_m, _dd_m)
            _manual_gender = "Female" if int(_manual_src[12])%2==0 else "Male"
            st.session_state["scan_nid"] = _manual_src; _def_dob = _manual_dob; _def_gender = _manual_gender
            st.info(f"{_L('تاريخ الميلاد من الرقم القومي:','DOB from National ID:')} {_manual_dob} | {_L('النوع:','Gender:')} {_L('أنثى' if _manual_gender=='Female' else 'ذكر', _manual_gender)}")
        except: pass
    comp_options = df_comp["Company Name"].tolist() if not df_comp.empty else ["No Company"]
    selected_comp = st.selectbox(_L("اختار الشركة", "Select Company"), comp_options)
    # عرض Policy Number و Provider للشركة المختارة
    if not df_comp.empty and selected_comp in df_comp["Company Name"].astype(str).tolist():
        crow = df_comp[df_comp["Company Name"].astype(str) == selected_comp].iloc[0]
        pnum = crow.get("Policy Number", "")
        prov = crow.get("Provider", "")
        if pnum or prov:
            st.info(f"📌 Policy: {crow.get('Policy Name','')} | Number: {pnum} | Provider: {prov}")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        staff_id = c1.text_input("Staff ID")
        first_name = c1.text_input(_L("* الاسم الأول - من السكان", "* First Name - From Scan"), value=_def_first)
        family_name = c2.text_input(_L("* باقي الاسم", "* Family Name"), value=_def_family)
        _dep_display = [_L("موظف","Employee"), _L("زوج / زوجة","Spouse"), _L("ابن / ابنة","Child"), _L("أب / أم","Parent")]
        _dep_values = ["Employee", "Spouse", "Child", "Parent"]
        dependency = _dep_values[_dep_display.index(c2.selectbox(_L("* صلة القرابة","* Dependency"), _dep_display))]
        _gender_display = [_L("ذكر","Male"), _L("أنثى","Female")]
        _gender_values = ["Male", "Female"]
        gender = _gender_values[_gender_display.index(c1.selectbox(_L("* النوع","* Gender"), _gender_display, index=0 if (_manual_gender or _def_gender)=="Male" else 1))]
        dob = c1.date_input(_L("* تاريخ الميلاد - من السكان أو الرقم القومي", "* Date of Birth - From Scan or National ID"), value=_def_dob)
        _plan_display = [_L("الخطة أ","Plan A"), _L("الخطة ب","Plan B"), _L("الخطة ج","Plan C"), _L("الخطة د","Plan D")]
        _plan_values = ["Plan A", "Plan B", "Plan C", "Plan D"]
        plan = _plan_values[_plan_display.index(c2.selectbox(_L("* الخطة - من الكارت","* Plan - From Card"), _plan_display, index=_plan_values.index(_def_plan) if _def_plan in _plan_values else 0))]
        provider_add = c1.selectbox(_L("شركة التأمين - من الكارت", "Insurance Provider - From Card"), _prov_options, index=_prov_options.index(_def_provider) if _def_provider in _prov_options else 0)
        policy_num_add = c1.text_input("Policy Number / رقم الوثيقة")
        mobile = c2.text_input("* Mobile Number")
        email = c1.text_input("Email ID")
        iban = c2.text_input("* IBAN / Account Number")
        national_id = c1.text_input(_L("* الرقم القومي - من السكان", "* National ID - From Scan"), value=st.session_state.get("scan_nid",""))
        expiry_date = c2.date_input("Card Expiry Date")
        addition_date = c1.date_input(_L("تاريخ الإضافة", "Addition Date"), value=date.today())
        submitted = st.form_submit_button("Import to Excel Sheet 📥 - إضافة للشيت النهائي + الشيت الأساسي", use_container_width=True)
        if submitted:
            if not first_name or not family_name or not national_id:
                st.error("First Name و Family Name و National ID مطلوبين")
            else:
                new_row = {"Staff ID": staff_id, "* First Name": first_name, "* Family Name": family_name, "* Dependency": dependency, "* Gender": gender, "* Date of Birth": str(dob), "* Plan": plan, "Provider": provider_add, "Policy Number": policy_num_add, "Company": selected_comp, "* Mobile Number": mobile, "Email ID": email, "* IBAN/Account Number": iban, "* National ID": national_id, "Card Expiry Date": str(expiry_date)}
                save_to_sheet_gs("addition", new_row)
                st.success(f"Added {first_name} {family_name} to {selected_comp} ✅")
                msg = f"New Addition Request - Myshurance:\nCompany: {selected_comp}\nProvider: {provider_add}\nPolicy: {policy_num_add}\nName: {first_name} {family_name}\nStaff ID: {staff_id}\nNational ID: {national_id}\nPlan: {plan}\nMobile: {mobile}"
                st.session_state["last_wa_msg"] = msg
                # Import to Excel Sheet: Final Excel for insurance + main list (+1) at same time
                # Main list = addition sheet (already saved above via save_to_sheet_gs)
                # Final Excel = downloadable file with this exact row, ready to send to insurance + email
                import io as _io_final
                _final_df = pd.DataFrame([new_row])
                _buf_final = _io_final.BytesIO()
                with pd.ExcelWriter(_buf_final, engine="openpyxl") as _w:
                    _final_df.to_excel(_w, sheet_name="Final_Addition", index=False)
                _buf_final.seek(0)
                st.session_state["last_final_excel"] = _buf_final.getvalue()
                st.session_state["last_final_excel_name"] = f"Final_Addition_{first_name}_{family_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                st.session_state["last_final_email_link"] = f"mailto:{NOTIFY_EMAIL}?subject=Myshurance Final Addition - {first_name} {family_name}&body=Final Addition Excel attached / ready to send - Company: {selected_comp} - Name: {first_name} {family_name} - National ID: {national_id}"
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
    st.subheader(_L("حذف عضو - لازم صورة الكارت التالف", "Delete Member - Damaged Card Photo Required"))
    _del_companies = df_comp["Company Name"].astype(str).tolist() if not df_comp.empty and "Company Name" in df_comp.columns else []
    if not _del_companies:
        st.info(_L("مفيش شركات لسه", "No companies yet"))
    else:
        _del_comp = st.selectbox(_L("اختار الشركة", "Select Company"), _del_companies, key="del_company")
        _members = pd.DataFrame()
        if not df_add.empty and "Company" in df_add.columns:
            _members = df_add[df_add["Company"].astype(str)==str(_del_comp)].copy()
        if _members.empty:
            st.info(_L("مفيش أعضاء في الشركة دي", "No members in this company"))
        else:
            _q = st.text_input(_L("دوّر بالاسم أو الرقم القومي أو رقم الموظف", "Search by Name, National ID or Staff ID"), key="del_search")
            _filtered = _members
            if _q:
                _ql = _q.lower().strip()
                _filtered = _members[_members.astype(str).apply(lambda row: row.str.lower().str.contains(_ql, na=False).any(), axis=1)]
            if _filtered.empty:
                st.warning(_L("مفيش عضو مطابق", "No matching member"))
            else:
                def _label(r):
                    return f"{r.get('* First Name', r.get('First Name',''))} {r.get('* Family Name', r.get('Family Name',''))} | {r.get('* National ID', r.get('National ID',''))} | {r.get('Staff ID','')}"
                _opts = [_label(r) for _, r in _filtered.iterrows()]
                _sel_label = st.selectbox(_L("اختار العضو اللي هتحذفه", "Select Member to Delete"), _opts, key="del_choose")
                _sel_row = _filtered.iloc[_opts.index(_sel_label)]
                st.dataframe(_filtered.iloc[[_opts.index(_sel_label)]], use_container_width=True)
                with st.form("del_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    # جنب الشخص: 1- إصدار بدل فاقد / 2- حذف العضو - زرارين جنب بعض
                    st.markdown(f"**{_L('اختار جنب الشخص:', 'Choose beside the person:')}**")
                    _b1, _b2 = st.columns(2)
                    if "del_action" not in st.session_state: st.session_state["del_action"] = "Final Deletion"
                    if _b1.button("1- إصدار بدل فاقد 🪪 / Replacement Card", use_container_width=True, key="del_btn_repl"):
                        st.session_state["del_action"] = "Replacement"
                    if _b2.button("2- حذف العضو 🗑 / Delete Member", use_container_width=True, key="del_btn_final"):
                        st.session_state["del_action"] = "Final Deletion"
                    _del_action_now = st.session_state.get("del_action", "Final Deletion")
                    st.info(f"{_L('اللي اخترته دلوقتي:', 'You selected now:')} { _L('1- إصدار بدل فاقد', '1- Replacement Card') if _del_action_now=='Replacement' else _L('2- حذف العضو', '2- Delete Member')}")
                    _del_type = _del_action_now
                    _del_date = c2.date_input(_L("تاريخ الحذف", "Deletion Date"), value=date.today())
                    st.caption(_L("تاريخ الحذف ميبقاش في المستقبل، وأقصى حاجة 30 يوم فاتوا.", "Deletion date cannot be in the future, max 30 days in the past."))
                    _del_reason = st.text_area(_L("سبب الحذف", "Reason for Deletion"))
                    _del_photo = st.file_uploader(_L("📷 صورة الكارت التالف - إجباري", "📷 Damaged Card Photo - Required"), type=["jpg", "jpeg", "png"])
                    _d_sub = st.form_submit_button(_L("تأكيد الحذف 🗑", "Confirm Deletion 🗑"), use_container_width=True)
                    if _d_sub:
                        _today = date.today()
                        if _del_date > _today:
                            st.error(_L("❌ تاريخ الحذف مينفعش يبقى في المستقبل", "❌ Deletion date cannot be in the future"))
                        elif (_today - _del_date).days > 30:
                            st.error(_L("❌ تاريخ الحذف أقصاه 30 يوم فاتوا", "❌ Deletion date max 30 days in the past"))
                        elif _del_photo is None:
                            st.error(_L("❌ مينفعش حذف من غير صورة الكارت التالف", "❌ Cannot delete without damaged card photo"))
                        else:
                            _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            _nid_val = str(_sel_row.get("* National ID", _sel_row.get("National ID", "")))
                            _photo_name = f"{_nid_val}_{_ts}.{_del_photo.name.split('.')[-1]}"
                            with open(os.path.join(PHOTOS_DIR, _photo_name), "wb") as _f: _f.write(_del_photo.getbuffer())
                            _new_row = {"Staff ID": _sel_row.get("Staff ID", ""), "* First Name": _sel_row.get("* First Name", _sel_row.get("First Name", "")), "* Family Name": _sel_row.get("* Family Name", _sel_row.get("Family Name", "")), "* Dependency": _sel_row.get("* Dependency", ""), "* Gender": _sel_row.get("* Gender", ""), "* Date of Birth": _sel_row.get("* Date of Birth", ""), "* Plan": _sel_row.get("* Plan", ""), "* Mobile Number": _sel_row.get("* Mobile Number", ""), "Email ID": _sel_row.get("Email ID", ""), "* IBAN/Account Number": _sel_row.get("* IBAN/Account Number", ""), "* National ID": _nid_val, "Company": _del_comp, "Deletion Type": _del_type, "Deletion Date": str(_del_date), "Reason": _del_reason, "Damaged Photo": _photo_name}
                            save_to_sheet_gs("deletion", _new_row)
                            # Final Excel for insurance: full row moved automatically from main sheet to final Excel
                            import io as _io_del
                            _del_final_df = pd.DataFrame([_new_row])
                            _buf_del = _io_del.BytesIO()
                            with pd.ExcelWriter(_buf_del, engine="openpyxl") as _wd:
                                _del_final_df.to_excel(_wd, sheet_name="Final_Deletion", index=False)
                            _buf_del.seek(0)
                            st.session_state["last_final_excel"] = _buf_del.getvalue()
                            st.session_state["last_final_excel_name"] = f"Final_Deletion_{_new_row['* First Name']}_{_new_row['* Family Name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                            st.session_state["last_final_email_link"] = f"mailto:{NOTIFY_EMAIL}?subject=Myshurance Final Deletion - {_new_row['* First Name']} {_new_row['* Family Name']}&body=Final Deletion Excel - Company: {_del_comp} - Type: {_del_type} - Deletion Date: {_del_date}"
                            st.success(_L("تم الحذف ✅ واتنقل للشيت النهائي", "Deleted ✅ and moved to final sheet"))
                            if _del_type == "Replacement":
                                _repl_pdf = generate_card_pdf(f"{_new_row['* First Name']} {_new_row['* Family Name']}", _new_row["Staff ID"], _nid_val, _sel_row.get("* Plan",""), _sel_row.get("* Dependency",""), _del_comp)
                                st.download_button("🪪 حمّل بدل فاقد - Download Replacement Card PDF", data=_repl_pdf, file_name=f"Replacement_{_nid_val}.pdf", mime="application/pdf", use_container_width=True)
                                st.info(_L("بدل فاقد: نفس البيانات، كارت جديد - حمّله من هنا", "Replacement: same data, new card - download it here"))
                            st.session_state["last_wa_msg"] = f"Deletion Request - Myshurance:\nCompany: {_del_comp}\nName: {_new_row['* First Name']} {_new_row['* Family Name']}\nStaff ID: {_new_row['Staff ID']}\nNational ID: {_nid_val}\nType: {_del_type}\nDeletion Date: {_del_date}\nReason: {_del_reason}\nDamaged card photo saved."
                            st.rerun()
    st.divider()
    st.subheader(_L("طلبات الحذف", "Deletion Requests"))
    if df_del.empty: st.info(_L("مفيش طلبات حذف لسه", "No deletion requests yet"))
    else: st.dataframe(df_del, use_container_width=True)

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
        st.subheader("Approve / Reject")
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
