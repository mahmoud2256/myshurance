import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import urllib.parse

st.set_page_config(page_title="Myshurance - Hub", layout="wide")

# --- PDF CARD FUNCTION ---
def generate_card_pdf(name, staff_id, national_id, plan, dependency, company="Myshurance"):
    from reportlab.lib.pagesizes import landscape, A6
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    buffer = io.BytesIO()
    # كارت بالعرض
    w, h = landscape(A6)  # 420 x 297 تقريبا
    c = canvas.Canvas(buffer, pagesize=landscape(A6))
    # خلفية
    c.setFillColor(HexColor("#0B2C4A"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    # شريط ذهبي
    c.setFillColor(HexColor("#C9A227"))
    c.rect(0, h-8, w, 8, fill=1, stroke=0)
    # اسم الشركة
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20, h-35, "MYSHURANCE")
    c.setFont("Helvetica", 9)
    c.drawString(20, h-48, "Health Insurance Card  |  TPA")
    # بيانات العضو
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20, h-80, f"{name}")
    c.setFont("Helvetica", 10)
    c.drawString(20, h-100, f"Staff ID: {staff_id}")
    c.drawString(20, h-115, f"National ID: {national_id}")
    c.drawString(20, h-130, f"Plan: {plan}  |  {dependency}")
    c.drawString(20, h-145, f"Company: {company}")
    # رقم الكارت والصلاحية
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#C9A227"))
    c.drawString(20, 25, f"Card No: MS-{str(national_id)[-6:] if national_id else '000000'}  |  Valid: 2026")
    c.drawString(20, 12, "In case of emergency call HR / Myshurance Hotline")
    # دائرة زخرفية
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
    login_type = st.radio("Login as:", ["👨‍💼 Admin", "👤 Employee - الموظف"], horizontal=True)
    if login_type == "👨‍💼 Admin":
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
    # زرار طباعة الكارت للموظف
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
    st.subheader("⬆️ My Upgrades")
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
    df_comp = pd.DataFrame(columns=["Company Name", "HR Contact", "HR Phone", "Plan", "Members Count", "Created Date"])

pending = len(df_appr[df_appr["Status"] == "Pending"]) if not df_appr.empty and "Status" in df_appr.columns else 0
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Companies", len(df_comp))
col2.metric("Addition", len(df_add))
col3.metric("Deletion", len(df_del))
col4.metric("Upgrade", len(df_upg))
col5.metric("Pending Approvals", pending)
col6.metric("Total Requests", len(df_add) + len(df_del) + len(df_upg))
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

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏢 Companies", "➕ Addition", "➖ Deletion", "⬆️ Upgrade", "✅ Approvals", "📊 Analytics"])

with tab0:
    st.subheader("Add New Company")
    with st.form("comp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        comp_name = c1.text_input("Company Name *")
        comp_hr = c1.text_input("HR Contact Name")
        comp_phone = c2.text_input("HR Phone / WhatsApp")
        comp_plan = c2.selectbox("Plan", ["Plan A", "Plan B", "Plan C"])
        comp_members = c1.number_input("Members Count", min_value=0, step=1)
        comp_sub = st.form_submit_button("Save Company 🏢", use_container_width=True)
        if comp_sub:
            if not comp_name:
                st.error("Company Name مطلوب")
            else:
                new_comp = {"Company Name": comp_name, "HR Contact": comp_hr, "HR Phone": comp_phone, "Plan": comp_plan, "Members Count": comp_members, "Created Date": datetime.now().strftime("%Y-%m-%d")}
                save_to_sheet_gs("companies", new_comp)
                st.success(f"Company {comp_name} added ✅")
                st.rerun()
    st.divider()
    st.subheader("All Companies")
    if df_comp.empty:
        st.info("No companies yet")
    else:
        st.dataframe(df_comp, use_container_width=True)

with tab1:
    st.subheader("Add New Member")
    comp_options = df_comp["Company Name"].tolist() if not df_comp.empty else ["No Company"]
    selected_comp = st.selectbox("Select Company", comp_options)
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        staff_id = c1.text_input("Staff ID")
        first_name = c1.text_input("* First Name")
        family_name = c2.text_input("* Family Name")
        dependency = c2.selectbox("* Dependency", ["Employee", "Spouse", "Child", "Parent"])
        gender = c1.selectbox("* Gender", ["Male", "Female"])
        dob = c1.date_input("* Date of Birth")
        plan = c2.selectbox("* Plan", ["Plan A", "Plan B", "Plan C"])
        mobile = c2.text_input("* Mobile Number")
        email = c1.text_input("Email ID")
        iban = c2.text_input("* IBAN / Account Number")
        national_id = c1.text_input("* National ID")
        submitted = st.form_submit_button("Save Addition ✅", use_container_width=True)
        if submitted:
            if not first_name or not family_name or not national_id:
                st.error("First Name و Family Name و National ID مطلوبين")
            else:
                new_row = {"Staff ID": staff_id, "* First Name": first_name, "* Family Name": family_name, "* Dependency": dependency, "* Gender": gender, "* Date of Birth": str(dob), "* Plan": plan, "* Mobile Number": mobile, "Email ID": email, "* IBAN/Account Number": iban, "* National ID": national_id}
                save_to_sheet_gs("addition", new_row)
                st.success(f"Added {first_name} {family_name} to {selected_comp} ✅")
                msg = f"New Addition Request - Myshurance:\nCompany: {selected_comp}\nName: {first_name} {family_name}\nStaff ID: {staff_id}\nNational ID: {national_id}\nPlan: {plan}\nMobile: {mobile}"
                st.session_state["last_wa_msg"] = msg
                st.rerun()
    st.divider()
    st.subheader("Addition Requests")
    if df_add.empty:
        st.info("No addition requests yet")
    else:
        st.dataframe(df_add, use_container_width=True)
        st.divider()
        st.subheader("🪪 Print Member Card - طباعة الكارت")
        # اختار عضو بالرقم القومي
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
        d_submitted = st.form_submit_button("Confirm Deletion 🗑️", use_container_width=True)
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
        u_submitted = st.form_submit_button("Confirm Upgrade ⬆️", use_container_width=True)
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
        a_provider = c2.text_input("Hospital / Provider")
        a_amount = c1.number_input("Estimated Amount", min_value=0, step=100)
        a_sub = st.form_submit_button("Submit Approval ✅", use_container_width=True)
        if a_sub:
            if not a_name or not a_national:
                st.error("Name و National ID مطلوبين")
            else:
                new_id = f"AP-{len(df_appr)+1:04d}"
                new_appr = {"ID": new_id, "Name": a_name, "National ID": a_national, "Type": a_type, "Provider": a_provider, "Amount": a_amount, "Status": "Pending", "Date": datetime.now().strftime("%Y-%m-%d %H:%M")}
                save_to_sheet_gs("approvals", new_appr)
                st.success(f"Approval {new_id} created - Pending ✅")
                msg = f"Approval Request - Myshurance:\nID: {new_id}\nName: {a_name}\nType: {a_type}\nProvider: {a_provider}\nAmount: {a_amount}\nStatus: Pending"
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
    else:
        st.info("No approvals yet for chart")
    if not df_comp.empty and "Members Count" in df_comp.columns:
        st.markdown("### Companies by Members Count")
        try:
            chart_df = df_comp.set_index("Company Name")["Members Count"]
            st.bar_chart(chart_df)
        except:
            st.dataframe(df_comp)
