import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

# 📱 เติม CSS จัดการตารางดั้งเดิมให้รองรับหน้าจอโทรศัพท์มือถือแบบมีแถบเลื่อนแนวนอน ไม่แตกกระจัดกระจาย
st.markdown("""
    <style>
    /* บังคับให้พื้นที่ตารางรองรับการเลื่อนซ้าย-ขวาบนมือถืออย่างสมบูรณ์ */
    .stTable, [data-testid="stTable"] {
        display: block !important;
        width: 100% !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        -webkit-overflow-scrolling: touch !important;
    }
    /* ปรับแต่งความกว้างของปุ่มในตารางให้กดง่ายบนหน้าจอมือถือ */
    .stButton > button {
        padding: 4px 10px !important;
        font-size: 14px !important;
    }
    </style>
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;font-size:24px;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# 🔗 1. ลิงก์ยิงฟอร์มหลังบ้าน
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSckbSH3a337W8yknYgAsAw7esyGyEv55lgK8g6QWCv_q2HtFg/formResponse"

# 🔑 2. แผนผังรหัสกล่องข้อความ Google Form
ENTRY_MAP = {
    "doc": "entry.1277005650",       # เลขที่หนังสือรับ
    "name": "entry.921566157",       # ชื่อ-สกุล ผู้ขอตรวจ
    "dept": "entry.1915980561",      # หน่วยงานต้นสังกัด
    "status": "entry.1882399362",    # Status ปัจจุบัน
    "note": "entry.1501544296",      # หมายเหตุ
    "s1": "entry.1914699467",        # step1
    "s2": "entry.1895799813",        # step2
    "s3": "entry.1846523425",        # step3
    "s4": "entry.452301442",         # step4
    "s5": "entry.1142071523",        # step5
    "s6": "entry.20673364",          # step6
    "s7": "entry.1786061219",        # step7
}

# รายชื่อขั้นตอนทั้งหมด (ชื่อเต็ม)
step_labels = [
    "1. รับหนังสือจากต้นสังกัด",
    "2. กรอกประวัติ พิมพ์ลายนิ้วมือกลิ้งหมึก 2 ชุด",
    "3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง",
    "4. ไปส่ง พฐ. ตรวจที่ ภ.จว. แล้วนำกลับมา",
    "5. ถ่ายเอกสารผลตรวจ 1 ชุด ไว้ในสำเนาคู่ฉับ",
    "6. ทำหนังสือส่ง รายงานผลกลับต้นสังกัด (2 ชุด)",
    "7. ต้นสังกัดเซ็นรับตัวจริงและคู่สำเนา เรียบร้อย"
]

# 🔄 3. ฟังก์ชันดึงลิงก์อ่านข้อมูลโดยตรงผ่านสิทธิ์แชร์
def get_sheet_urls():
    try:
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sheet_id = base_url.split("/d/")[1].split("/edit")[0] if "/edit" in base_url else base_url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    except:
        return None

read_url = get_sheet_urls()

# Initialize Session States
if "db_dict" not in st.session_state:
    st.session_state.db_dict = {}
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "selected_dashboard_step" not in st.session_state:
    st.session_state.selected_dashboard_step = None
if "form_key_index" not in st.session_state:
    st.session_state.form_key_index = 0

# ดึงข้อมูลจาก Sheets มาอัปเดตลงตาราง
if read_url and not st.session_state.get("prevent_reloading", False):
    try:
        df = pd.read_csv(read_url)
        if not df.empty:
            new_db = {}
            for _, row in df.iterrows():
                if len(row) >= 6:
                    k = str(row.iloc[1]).strip()
                    current_status = str(row.iloc[4]) if pd.notna(row.iloc[4]) else "⚪ ยังไม่ได้เริ่ม"
                    
                    if "❌ ลบข้อมูลแล้ว" in current_status:
                        continue
                        
                    if k and k != "nan" and k != "":
                        new_db[k] = {
                            "name": str(row.iloc[2]) if pd.notna(row.iloc[2]) else "",
                            "dept": str(row.iloc[3]) if pd.notna(row.iloc[3]) else "",
                            "status": current_status,
                            "note": str(row.iloc[5]) if pd.notna(row.iloc[5]) else "",
                            "steps": [bool(row.iloc[i]) if i < len(row) and pd.notna(row.iloc[i]) else False for i in range(6, 13)]
                        }
            st.session_state.db_dict = new_db
    except:
        pass

st.session_state["prevent_reloading"] = False

# บล็อกป็อปอัพแจ้งเตือนการลบข้อมูล
@st.dialog("⚠️ ยืนยันการลบข้อมูลถาวรบนหน้าจอ")
def confirm_delete_dialog(doc_id, name, current_item):
    st.write(f"คุณแน่ใจหรือไม่ว่าต้องการลบข้อมูลของ **{name}** (เลขที่หนังสือ: {doc_id}) ออกจากระบบหน้าเว็บ?")
    st.error("🚨 เมื่อกดยืนยัน ระบบจะอัปเดตสถานะการลบไปหลังบ้าน")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚨 ยืนยันลบข้อมูล", type="primary", use_container_width=True):
            form_data = {
                ENTRY_MAP["doc"]: doc_id,
                ENTRY_MAP["name"]: name,
                ENTRY_MAP["dept"]: current_item["dept"],
                ENTRY_MAP["status"]: "❌ ลบข้อมูลแล้ว",
                ENTRY_MAP["note"]: current_item["note"],
                ENTRY_MAP["s1"]: "False", ENTRY_MAP["s2"]: "False",
                ENTRY_MAP["s3"]: "False", ENTRY_MAP["s4"]: "False",
                ENTRY_MAP["s5"]: "False", ENTRY_MAP["s6"]: "False",
                ENTRY_MAP["s7"]: "False"
            }
            try:
                requests.post(FORM_URL, data=form_data, timeout=30)
                if doc_id in st.session_state.db_dict:
                    del st.session_state.db_dict[doc_id]
                st.session_state["prevent_reloading"] = True
                st.rerun()
            except:
                st.error("❌ เกิดข้อผิดพลาดทางเครือข่าย ไม่สามารถส่งคำสั่งลบได้")
    with c2:
        if st.button("❌ ยกเลิก", use_container_width=True):
            st.rerun()

# ตั้งค่าเริ่มต้นของฟอร์มกรอกข้อมูลตามสัญญากลไกดั้งเดิม
default_doc, default_name, default_dept, default_note = "", "", "", ""
loaded_steps = [False] * 7

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    default_name = item["name"]
    default_dept = item["dept"]
    default_note = item["note"]
    loaded_steps = item["steps"] if len(item["steps"]) == 7 else [False]*7

def on_step_change(index):
    w_key = f"step_idx_{index}_{st.session_state.form_key_index}"
    if st.session_state.get(w_key, False):
        for i in range(index + 1):
            st.session_state[f"step_idx_{i}_{st.session_state.form_key_index}"] = True
    else:
        for i in range(index, 7):
            st.session_state[f"step_idx_{i}_{st.session_state.form_key_index}"] = False

col1, col2 = st.columns([1, 1.8])

# ==================== ฝั่งซ้าย: ฟอร์มกรอกและแก้ไขข้อมูล ====================
with col1:
    st.subheader("📝 บันทึก / แก้ไขข้อมูล")
    
    if st.session_state.edit_id:
        st.warning(f"⚠️ กำลังแก้ไขเลขที่หนังสือ: {st.session_state.edit_id}")
    else:
        st.info("➕ กำลังเพิ่มข้อมูลรายใหม่")

    doc_num = st.text_input("เลขที่หนังสือรับ:", value=default_doc, key=f"doc_inp_{st.session_state.form_key_index}")
    name = st.text_input("ชื่อ-สกุล ผู้ขอตรวจสอบประวัติ:", value=default_name, key=f"name_inp_{st.session_state.form_key_index}")
    dept = st.text_input("หน่วยงานต้นสังกัด (ที่ส่งมา):", value=default_dept, key=f"dept_inp_{st.session_state.form_key_index}")
    note = st.text_area("หมายเหตุ:", value=default_note, height=70, key=f"note_inp_{st.session_state.form_key_index}")
    
    st.write("**ติ๊กเลือกขั้นตอนที่ทำเสร็จแล้ว:**")
    
    for idx, label in enumerate(step_labels):
        st.checkbox(
            label,
            value=loaded_steps[idx],
            key=f"step_idx_{idx}_{st.session_state.form_key_index}",
            on_change=on_step_change,
            args=(idx,)
        )

    checks = [st.session_state.get(f"step_idx_{i}_{st.session_state.form_key_index}", False) for i in range(7)]
    
    status_text = "⚪ ยังไม่ได้เริ่ม"
    if checks[6]:
        status_text = f"🟢 {step_labels[6]}"
    else:
        for idx in range(6, -1, -1):
            if checks[idx]:
                status_text = f"🟡 {step_labels[idx]}"
                break

    btn_label = "💾 อัปเดตข้อมูลและบันทึกลงระบบ" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงระบบ"
    
    # 🎯 กล่องรับการแจ้งเตือน
    msg_slot = st.empty()
    
    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        if st.button(btn_label, type="primary", use_container_width=True):
            # 🎯 บังคับเคลียร์พื้นที่หน้าจอให้ว่างเปล่าทันทีที่กดปุ่ม เพื่อทำลาย Error ที่ตกค้างอยู่เดิมออกไปก่อน
            msg_slot.empty()
            
            if doc_num and name:
                form_data = {
                    ENTRY_MAP["doc"]: doc_num,
                    ENTRY_MAP["name"]: name,
                    ENTRY_MAP["dept"]: dept,
                    ENTRY_MAP["status"]: status_text,
                    ENTRY_MAP["note"]: note,
                    ENTRY_MAP["s1"]: str(checks[0]), ENTRY_MAP["s2"]: str(checks[1]), ENTRY_MAP["s3"]: str(checks[2]),
                    ENTRY_MAP["s4"]: str(checks[3]), ENTRY_MAP["s5"]: str(checks[4]), ENTRY_MAP["s6"]: str(checks[5]), ENTRY_MAP["s7"]: str(checks[6])
                }
                try:
                    # พยายามส่งข้อมูลและเปิดเวลารอนานสูงสุด 30 วินาที
                    requests.post(FORM_URL, data=form_data, timeout=30)
                    st.session_state.db_dict[str(doc_num)] = {"name": name, "dept": dept, "status": status_text, "note": note, "steps": checks}
                    st.session_state.edit_id = None
                    st.session_state["prevent_reloading"] = True
                    st.session_state.form_key_index += 1
                    msg_slot.success("🎉 บันทึกข้อมูลสำเร็จแล้วครับพี่!")
                    st.rerun()
                except:
                    # หากเน็ตหน่วงจริง ๆ ค่อยยอมให้แสดงข้อความดักจำข้อมูลขึ้นมาใหม่
                    msg_slot.error("❌ เกิดข้อผิดพลาดทางเครือข่าย (แต่ระบบจำข้อมูลบนหน้าเว็บไว้แล้ว)")
            else:
                msg_slot.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")
                
    with btn_col2:
        if st.session_state.edit_id:
            if st.button("❌ ยกเลิก", use_container_width=True):
                st.session_state.edit_id = None
                st.session_state["prevent_reloading"] = True
                st.session_state.form_key_index += 1
                st.rerun()

# ==================== ฝั่งขวา: แดชบอร์ดปุ่มกดและโครงสร้างตารางข้อมูล ====================
with col2:
    st.subheader("📊 ระบบติดตามสถานะภาพรวม")
    
    counts = [0] * 8  
    for k, v in st.session_state.db_dict.items():
        v_status = v["status"]
        if "❌ ลบข้อมูลแล้ว" in v_status:
            continue
        if "ยังไม่ได้เริ่ม" in v_status:
            counts[7] += 1
        else:
            for idx, label in enumerate(step_labels):
                if label in v_status:
                    counts[idx] += 1
                    break

    st.write("**📌 กระดานสรุปสถานะปัจจุบัน (คลิกเพื่อกรองดูรายชื่อ):**")
    
    d_row1_c1, d_row1_c2 = st.columns(2)
    with d_row1_c1:
        if st.button(f"📁 ทำถึงขั้นตอน: {step_labels[0]} ({counts[0]} เรื่อง)", key="b1", type="primary" if st.session_state.selected_dashboard_step == 0 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 0 else 0; st.rerun()
    with d_row1_c2:
        if st.button(f"📝 ทำถึงขั้นตอน: {step_labels[1]} ({counts[1]} เรื่อง)", key="b2", type="primary" if st.session_state.selected_dashboard_step == 1 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 1 else 1; st.rerun()

    d_row2_c1, d_row2_c2 = st.columns(2)
    with d_row2_c1:
        if st.button(f"✉️ ทำถึงขั้นตอน: {step_labels[2]} ({counts[2]} เรื่อง)", key="b3", type="primary" if st.session_state.selected_dashboard_step == 2 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 2 else 2; st.rerun()
    with d_row2_c2:
        if st.button(f"🚔 ทำถึงขั้นตอน: {step_labels[3]} ({counts[3]} เรื่อง)", key="b4", type="primary" if st.session_state.selected_dashboard_step == 3 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 3 else 3; st.rerun()

    d_row3_c1, d_row3_c2 = st.columns(2)
    with d_row3_c1:
        if st.button(f"🖨️ ทำถึงขั้นตอน: {step_labels[4]} ({counts[4]} เรื่อง)", key="b5", type="primary" if st.session_state.selected_dashboard_step == 4 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 4 else 4; st.rerun()
    with d_row3_c2:
        if st.button(f"📤 ทำถึงขั้นตอน: {step_labels[5]} ({counts[5]} เรื่อง)", key="b6", type="primary" if st.session_state.selected_dashboard_step == 5 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 5 else 5; st.rerun()

    d_row4_c1, d_row4_c2 = st.columns(2)
    with d_row4_c1:
        if st.button(f"🟢 เสร็จสิ้น: {step_labels[6]} ({counts[6]} เรื่อง)", key="b7", type="primary" if st.session_state.selected_dashboard_step == 6 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 6 else 6; st.rerun()
    with d_row4_c2:
        if st.button(f"⚪ ยังไม่เริ่มดำเนินการเลย ({counts[7]} เรื่อง)", key="b8", type="primary" if st.session_state.selected_dashboard_step == 7 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 7 else 7; st.rerun()

    st.write("---")
    st.write("**🔍 ค้นหาข้อมูลเพิ่มเติม**")
    search_query = st.text_input("พิมพ์รหัสหนังสือ หรือ ชื่อบุคคลที่ต้องการค้นหา:", placeholder="พิมพ์ค้นหาที่นี่...").strip()
    
    if st.session_state.selected_dashboard_step is not None:
        if st.button("❌ ล้างตัวกรองปุ่มขั้นตอน Dashboard", use_container_width=True):
            st.session_state.selected_dashboard_step = None
            st.rerun()

    st.write("---")
    st.write("**📋 ตารางตรวจสอบสถานะปัจจุบัน**")
    
    if st.session_state.db_dict:
        header_cols = st.columns([1, 1.2, 1, 2, 1.2, 0.7, 0.7])
        with header_cols[0]: st.markdown("**เลขหนังสือ**")
        with header_cols[1]: st.markdown("**ชื่อ-สกุล**")
        with header_cols[2]: st.markdown("**ต้นสังกัด**")
        with header_cols[3]: st.markdown("**สถานะปัจจุบัน**")
        with header_cols[4]: st.markdown("**หมายเหตุ**")
        with header_cols[5]: st.markdown("**แก้ไข**")
        with header_cols[6]: st.markdown("**ลบ**")
        st.write("<div style='border-bottom: 2px solid #800000; margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        for k, v in st.session_state.db_dict.items():
            if "❌ ลบข้อมูลแล้ว" in v["status"]:
                continue
                
            s_idx = 7 if "ยังไม่ได้เริ่ม" in v["status"] else next((i for i, x in enumerate(step_labels) if x in v["status"]), None)
            
            if st.session_state.selected_dashboard_step is not None and s_idx != st.session_state.selected_dashboard_step:
                continue
            if search_query and (search_query not in str(k) and search_query not in str(v["name"]) and search_query not in str(v["dept"])):
                continue
                
            row_cols = st.columns([1, 1.2, 1, 2, 1.2, 0.7, 0.7])
            with row_cols[0]: st.write(k)
            with row_cols[1]: st.write(v["name"])
            with row_cols[2]: st.write(v["dept"])
            with row_cols[3]: st.write(v["status"])
            with row_cols[4]: st.write(v["note"] if v["note"] else "-")
            
            with row_cols[5]:
                if st.button("✏️", key=f"edit_btn_{k}", use_container_width=True):
                    st.session_state.edit_id = k
                    st.session_state.form_key_index += 1  
                    st.rerun()
            with row_cols[6]:
                if st.button("🗑️", key=f"del_btn_{k}", use_container_width=True):
                    confirm_delete_dialog(k, v["name"], v)
                    
            st.write("<div style='border-bottom: 1px solid #eee; margin-top: 4px; margin-bottom: 4px;'></div>", unsafe_allow_html=True)

        st.write("---")
        if st.button("🔄 ดึงข้อมูลเวอร์ชันล่าสุดจาก Google Sheets", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อฐานข้อมูล...")
