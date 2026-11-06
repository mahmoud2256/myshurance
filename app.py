import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import urllib.parse

st.set_page_config(page_title="Myshurance - Hub", layout="wide")
st.title("Myshurance Hub")
st.caption("Census List - Companies / Addition / Deletion / Upgrade / Approvals / Analytics")

FILE = "Census_List.xlsx"
APPROVALS_FILE = "approvals.xlsx"
COMPANIES_FILE = "companies.xlsx"
PHOTOS_DIR = "damaged_cards"
os.makedirs(PHOTOS_DIR, exist_ok=True)

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

def clean_df(df):
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    df = df.dropna(how="all")
    return df

def load_sheet(name):
    try:
        df = pd.read_excel(FILE, sheet_name=name)
        return clean_df(df)
    except:
        return pd.DataFrame()

def save_to_sheet(sheet_name, new_row):
    new_row = {str(k).strip(): v for k, v in new_row.items()}
    all_sheets = pd.read_excel(FILE, sheet_name=None)
    cleaned = {}
    for s_name, df_sheet in all_sheets.items():
        cleaned[s_name] = clean_df(df_sheet)
    df = cleaned.get(sheet_name, pd.DataFrame())
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df = clean_df(df)
    cleaned[sheet_name] = df
    with pd.ExcelWriter(FILE, engine="openpyxl") as writer:
        for s_name, df_sheet in cleaned.items():
            df_sheet.to_excel(writer, sheet_name=s_name, index=False)

def load_approvals():
    if os.path.exists(APPROVALS_FILE):
        try:
            return clean_df(pd.read_excel(APPROVALS_FILE))
        except:
            return pd.DataFrame(columns=["ID", "Name", "National ID", "Type", "Provider", "Amount", "Status", "Date"])
    return pd.DataFrame(columns=["ID", "Name", "National ID", "Type", "Provider", "Amount", "Status", "Date"])

def save_approvals(df):
    df.to_excel(APPROVALS_FILE, index=False)

def load_companies():
    if os.path.exists(COMPANIES_FILE):
        try:
            return clean_df(pd.read_excel(COMPANIES_FILE))
        except:
            return pd.DataFrame(columns=["Company Name", "HR Contact", "HR Phone", "Plan", "Members Count", "Created Date"])
    return pd.DataFrame(columns=["Company Name", "HR Contact", "HR Phone", "Plan", "Members Count", "Created Date"])

def save_companies(df):
    df.to_excel(COMPANIES_FILE, index=False)

if not os.path.exists(FILE):
    st.warning("Census_List.xlsx not found - حط الملف جنب app.py")
    st.stop()

df_add = load_sheet("addition ")
df_del = load_sheet("deletion ")
df_upg = load_sheet("up grade ")
df_appr = load_approvals()
df_comp = load_companies()

pending = len(df_appr[df_appr["Status"] == "Pending"]) if not df_appr.empty else 0

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
        all_df = clean_df(all_df)
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
                df_comp = pd.concat([df_comp, pd.DataFrame([new_comp])], ignore_index=True)
                save_companies(df_comp)
                st.success(f"Company {comp_name} added ✅")
                st.rerun()
    st.divider()
    st.subheader("All Companies")
    if df_comp.empty:
        st.info("No companies yet - ضيف أول شركة، زي 【entity-Allianz¦canonical_name=Allianz】")
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
                save_to_sheet("addition ", new_row)
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
                save_to_sheet("deletion ", new_row)
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
                save_to_sheet("up grade ", new_row)
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
                df_appr = pd.concat([df_appr, pd.DataFrame([new_appr])], ignore_index=True)
                save_approvals(df_appr)
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
                save_approvals(df_appr)
                st.success(f"{selected_id} Approved ✅")
                st.rerun()
            if col_b.button("❌ Reject", use_container_width=True, key="reject_btn"):
                df_appr.loc[df_appr["ID"] == selected_id, "Status"] = "Rejected"
                save_approvals(df_appr)
                st.error(f"{selected_id} Rejected")
                st.rerun()

with tab5:
    st.subheader("📊 Analytics - نظرة عامة")
    # Members by Plan
    if not df_add.empty and "* Plan" in df_add.columns:
        st.markdown("### Members by Plan")
        st.bar_chart(df_add["* Plan"].value_counts())
    else:
        st.info("No members yet for Plan chart")

    # Members by Dependency
    if not df_add.empty and "* Dependency" in df_add.columns:
        st.markdown("### Members by Dependency")
        st.bar_chart(df_add["* Dependency"].value_counts())

    # Approvals by Status
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

    # Companies Members
    if not df_comp.empty and "Members Count" in df_comp.columns:
        st.markdown("### Companies by Members Count")
        try:
            chart_df = df_comp.set_index("Company Name")["Members Count"]
            st.bar_chart(chart_df)
        except:
            st.dataframe(df_comp)
