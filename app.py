import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

st.markdown("""
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
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
    "5. ถ่ายเอกสารผลตรวจ 1 ชุด ไว้ในสำเนาคู่ฉบับ",
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

# ตัวแปรเก็บฐานข้อมูลในความจำหน้าจอ
if "db_dict" not in st.session_state:
    st.session_state.db_dict = {}

# 🛠️ ใช้ระบบเวอร์ชันคีย์ เพื่อบังคับรีเซ็ตวิดเจ็ตแบบปลอดภัย 100%
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# ดึงข้อมูลจาก Sheets มาอัปเดตลงตาราง
if read_url and not st.session_state.get("prevent_reloading", False):
    try:
        df = pd.read_csv(read_url)
        if not df.empty:
            for _, row in df.iterrows():
                if len(row) >= 6:
                    k = str(row.iloc[1]).strip()
                    if k and k != "nan" and k != "":
                        st.session_state.db_dict[k] = {
                            "name": str(row.iloc[2]) if pd.notna(row.iloc[2]) else "",
                            "dept": str(row.iloc[3]) if pd.notna(row.iloc[3]) else "",
                            "status": str(row.iloc[4]) if pd.notna(row.iloc[4]) else "⚪ ยังไม่ได้เริ่ม",
                            "note": str(row.iloc[5]) if pd.notna(row.iloc[5]) else "",
                            "steps": [bool(row.iloc[i]) if i < len(row) and pd.notna(row.iloc[i]) else False for i in range(6, 13)]
                        }
    except:
        pass

st.session_state["prevent_reloading"] = False

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ตัวแปรควบคุมการคลิกเลือกกรองจาก Dashboard
if "selected_dashboard_step" not in st.session_state:
    st.session_state.selected_dashboard_step = None

# ตั้งค่าเริ่มต้นของฟอร์มกรอกข้อมูล
default_doc, default_name, default_dept, default_note = "", "", "", ""
loaded_steps = [False] * 7

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    default_name = item["name"]
    default_dept = item["dept"]
    default_note = item["note"]
    loaded_steps = item["steps"] if len(item["steps"]) == 7 else [False]*7

# สร้าง/อัปเดตคีย์เช็คบ็อกซ์ตามเวอร์ชันปัจจุบัน (ป้องกันหน้าจอแดง)
for i in range(7):
    widget_key = f"step_widget_{i}_v_{st.session_state.form_version}"
    if widget_key not in st.session_state or (st.session_state.edit_id and st.session_state.get("last_loaded_edit_id") != st.session_state.edit_id):
        st.session_state[widget_key] = loaded_steps[i]

if st.session_state.edit_id:
    st.session_state["last_loaded_edit_id"] = st.session_state.edit_id
else:
    if "last_loaded_edit_id" in st.session_state:
        st.session_state["last_loaded_edit_id"] = None

# ฟังก์ชันกลไก Auto-Check เดินหน้าแบบปลอดภัย
def on_step_change(index, version):
    widget_key = f"step_widget_{index}_v_{version}"
    if st.session_state[widget_key]:
        for i in range(index + 1):
            st.session_state[f"step_widget_{i}_v_{version}"] = True
    else:
        for i in range(index, 7):
            st.session_state[f"step_widget_{i}_v_{version}"] = False

# แบ่งคอลัมน์ซ้าย (ฟอร์ม) - ขวา (Dashboard & ตาราง)
col1, col2 = st.columns([1, 1.8])

# ==================== ฝั่งซ้าย: ฟอร์มกรอกและแก้ไขข้อมูล ====================
with col1:
    st.subheader("📝 บันทึก / แก้ไขข้อมูล")
    
    if st.session_state.edit_id:
        st.warning(f"⚠️ กำลังแก้ไขเลขที่หนังสือ: {st.session_state.edit_id}")
    else:
        st.info("➕ กำลังเพิ่มข้อมูลรายใหม่")

    doc_num = st.text_input("เลขที่หนังสือรับ:", value=default_doc, key=f"doc_num_input_{st.session_state.form_version}")
    name = st.text_input("ชื่อ-สกุล ผู้ขอตรวจสอบประวัติ:", value=default_name, key=f"name_input_{st.session_state.form_version}")
    dept = st.text_input("หน่วยงานต้นสังกัด (ที่ส่งมา):", value=default_dept, key=f"dept_input_{st.session_state.form_version}")
    note = st.text_area("หมายเหตุ:", value=default_note, height=70, key=f"note_input_{st.session_state.form_version}")
    
    st.write("**ติ๊กเลือกขั้นตอนที่ทำเสร็จแล้ว:**")
    
    for idx, label in enumerate(step_labels):
        st.checkbox(
            label,
            key=f"step_widget_{idx}_v_{st.session_state.form_version}",
            on_change=on_step_change,
            args=(idx, st.session_state.form_version)
        )

    checks = [st.session_state[f"step_widget_{i}_v_{st.session_state.form_version}"] for i in range(7)]
    
    status_text = "⚪ ยังไม่ได้เริ่ม"
    if checks[6]:
        status_text = f"🟢 {step_labels[6]}"
    else:
        for idx in range(6, -1, -1):
            if checks[idx]:
                status_text = f"🟡 {step_labels[idx]}"
                break

    btn_label = "💾 อัปเดตข้อมูลและบันทึกลงระบบ" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงระบบ"
    
    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        if st.button(btn_label, type="primary", use_container_width=True):
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
                    response = requests.post(FORM_URL, data=form_data)
                    st.session_state.db_dict[str(doc_num)] = {"name": name, "dept": dept, "status": status_text, "note": note, "steps": checks}
                    st.session_state.edit_id = None
                    st.session_state["prevent_reloading"] = True
                    # อัปเดตเวอร์ชันฟอร์มเพื่อเคลียร์วิดเจ็ตแบบปลอดภัยไร้กังวล
                    st.session_state.form_version += 1
                    st.success("🎉 บันทึกข้อมูลสำเร็จแล้วครับพี่!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error("❌ เกิดข้อผิดพลาดทางเครือข่าย")
            else:
                st.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")
                
    with btn_col2:
        if st.session_state.edit_id:
            if st.button("❌ ยกเลิกแก้ไข", use_container_width=True):
                st.session_state.edit_id = None
                st.session_state["prevent_reloading"] = True
                # เปลี่ยนเวอร์ชันฟอร์มเพื่อรีเซ็ตหน้าจอโดยไม่ติดขัดระบบหลังบ้าน
                st.session_state.form_version += 1
                st.rerun()

# ==================== ฝั่งขวา: Dashboard และ ตารางตรวจสอบสถานะ ====================
with col2:
    st.subheader("📊 ระบบติดตามสถานะภาพรวม")
    
    # 🧮 1. คำนวณสถิติเรื่องในแต่ละข้อ
    counts = [0] * 8  
    for k, v in st.session_state.db_dict.items():
        v_status = v["status"]
        if "ยังไม่ได้เริ่ม" in v_status:
            counts[7] += 1
        else:
            for idx, label in enumerate(step_labels):
                if label in v_status:
                    counts[idx] += 1
                    break

    # 🖥️ 2. แดชบอร์ดแบบชื่อเต็ม แถวละ 2 กล่อง
    st.write("**📌 กระดานสรุปสถานะปัจจุบัน (คลิกขั้นตอนเพื่อกรองดูรายชื่อ):**")
    
    # แถวที่ 1: ข้อ 1 และ 2
    d_row1_c1, d_row1_c2 = st.columns(2)
    with d_row1_c1:
        b1_label = f"📁 ทำถึงขั้นตอน: {step_labels[0]} \n\n ({counts[0]} เรื่อง)"
        if st.button(b1_label, key="dash_b1", type="primary" if st.session_state.selected_dashboard_step == 0 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 0 else 0
            st.rerun()
    with d_row1_c2:
        b2_label = f"📝 ทำถึงขั้นตอน: {step_labels[1]} \n\n ({counts[1]} เรื่อง)"
        if st.button(b2_label, key="dash_b2", type="primary" if st.session_state.selected_dashboard_step == 1 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 1 else 1
            st.rerun()

    # แถวที่ 2: ข้อ 3 และ 4
    d_row2_c1, d_row2_c2 = st.columns(2)
    with d_row2_c1:
        b3_label = f"✉️ ทำถึงขั้นตอน: {step_labels[2]} \n\n ({counts[2]} เรื่อง)"
        if st.button(b3_label, key="dash_b3", type="primary" if st.session_state.selected_dashboard_step == 2 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 2 else 2
            st.rerun()
    with d_row2_c2:
        b4_label = f"🚔 ทำถึงขั้นตอน: {step_labels[3]} \n\n ({counts[3]} เรื่อง)"
        if st.button(b4_label, key="dash_b4", type="primary" if st.session_state.selected_dashboard_step == 3 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 3 else 3
            st.rerun()

    # แถวที่ 3: ข้อ 5 และ 6
    d_row3_c1, d_row3_c2 = st.columns(2)
    with d_row3_c1:
        b5_label = f"🖨️ ทำถึงขั้นตอน: {step_labels[4]} \n\n ({counts[4]} เรื่อง)"
        if st.button(b5_label, key="dash_b5", type="primary" if st.session_state.selected_dashboard_step == 4 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 4 else 4
            st.rerun()
    with d_row3_c2:
        b6_label = f"📤 ทำถึงขั้นตอน: {step_labels[5]} \n\n ({counts[5]} เรื่อง)"
        if st.button(b6_label, key="dash_b6", type="primary" if st.session_state.selected_dashboard_step == 5 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 5 else 5
            st.rerun()

    # แถวที่ 4: ข้อ 7 และ ยังไม่เริ่ม
    d_row4_c1, d_row4_c2 = st.columns(2)
    with d_row4_c1:
        b7_label = f"🟢 เสร็จสิ้น: {step_labels[6]} \n\n ({counts[6]} เรื่อง)"
        if st.button(b7_label, key="dash_b7", type="primary" if st.session_state.selected_dashboard_step == 6 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 6 else 6
            st.rerun()
    with d_row4_c2:
        b8_label = f"⚪ ยังไม่เริ่มดำเนินการเลย \n\n ({counts[7]} เรื่อง)"
        if st.button(b8_label, key="dash_b8", type="primary" if st.session_state.selected_dashboard_step == 7 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 7 else 7
            st.rerun()

    st.write("---")

    # 🔍 3. ช่องค้นหาข้อมูลเพิ่มเติม
    st.write("**🔍 ค้นหาข้อมูลเพิ่มเติม**")
    search_query = st.text_input("พิมพ์คำค้นหาเพิ่มเติม (เลขหนังสือ, ชื่อ, หรือสังกัด):", placeholder="พิมพ์ค้นหาที่นี่...", key="search_query_input").strip()
    
    c_search1, c_search2, c_search3, c_clear = st.columns([1, 1, 1, 1.2])
    with c_search1:
        search_doc = st.checkbox("เลขที่หนังสือรับ", value=True, key="search_doc_check")
    with c_search2:
        search_name = st.checkbox("ชื่อ-สกุล ผู้ขอตรวจ", value=True, key="search_name_check")
    with c_search3:
        search_dept = st.checkbox("หน่วยงานต้นสังกัด", value=False, key="search_dept_check")
    with c_clear:
        if st.session_state.selected_dashboard_step is not None:
            if st.button("❌ ล้างตัวกรอง Dashboard", use_container_width=True):
                st.session_state.selected_dashboard_step = None
                st.rerun()

    if st.session_state.selected_dashboard_step is not None:
        if st.session_state.selected_dashboard_step == 7:
            st.warning("🎯 กำลังแสดงเฉพาะเรื่องที่: [⚪ ยังไม่ได้เริ่ม]")
        elif st.session_state.selected_dashboard_step == 6:
            st.success("🎯 กำลังแสดงเฉพาะเรื่องที่: [🟢 ขั้นตอนที่ 7 เสร็จสิ้นเรียบร้อย]")
        else:
            st.warning(f"🎯 กำลังแสดงเฉพาะเรื่องที่อยู่สถานะ: [{step_labels[st.session_state.selected_dashboard_step]}]")

    st.write("---")
    
    if st.session_state.db_dict:
        all_records = []
        for k, v in st.session_state.db_dict.items():
            all_records.append({
                "เลขที่หนังสือรับ": str(k),
                "ชื่อ-สกุล ผู้ขอตรวจ": str(v["name"]),
                "หน่วยงานต้นสังกัด": str(v["dept"]),
                "สถานะปัจจุบัน": str(v["status"]),
                "หมายเหตุ": str(v["note"]),
                "step_index": 7 if "ยังไม่ได้เริ่ม" in v["status"] else next((i for i, x in enumerate(step_labels) if x in v["status"]), None)
            })
            
        filtered_records = []
        for r in all_records:
            if st.session_state.selected_dashboard_step is not None:
                if r["step_index"] != st.session_state.selected_dashboard_step:
                    continue
            
            if search_query:
                match = False
                if search_doc and search_query in r["เลขที่หนังสือรับ"]:
                    match = True
                if search_name and search_query in r["ชื่อ-สกุล ผู้ขอตรวจ"]:
                    match = True
                if search_dept and search_query in r["หน่วยงานต้นสังกัด"]:
                    match = True
                if not match:
                    continue
                    
            filtered_records.append(r)

        # 5. แสดงผลตารางรายชื่อข้อมูล
        if filtered_records:
            t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([1.2, 1.5, 1.2, 2.0, 0.8])
            with t_col1: st.caption("**เลขหนังสือรับ**")
            with t_col2: st.caption("**ชื่อ-สกุล**")
            with t_col3: st.caption("**ต้นสังกัด**")
            with t_col4: st.caption("**สถานะปัจจุบัน**")
            with t_col5: st.caption("**จัดการ**")
            st.write("<div style='margin-top:-10px; margin-bottom:10px; border-bottom:1px solid #ddd;'></div>", unsafe_allow_html=True)
            
            for row in filtered_records:
                r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([1.2, 1.5, 1.2, 2.0, 0.8])
                with r_col1: st.write(row["เลขที่หนังสือรับ"])
                with r_col2: st.write(row["ชื่อ-สกุล ผู้ขอตรวจ"])
                with r_col3: st.write(row["หน่วยงานต้นสังกัด"])
                with r_col4: st.write(row["สถานะปัจจุบัน"])
                with r_col5:
                    if st.button("✏️ แก้ไข", key=f"edit_btn_{row['เลขที่หนังสือรับ']}", use_container_width=True):
                        st.session_state.edit_id = row["เลขที่หนังสือรับ"]
                        st.rerun()
                if row["หมายเหตุ"]:
                    st.markdown(f"<p style='color:gray; font-size:13px; margin-left:10px; margin-top:-5px; margin-bottom:12px;'>📌 หมายเหตุ: {row['หมายเหตุ']}</p>", unsafe_allow_html=True)
                else:
                    st.write("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
        else:
            st.warning("🔍 ไม่พบข้อมูลที่ตรงกับเงื่อนไขการเลือก/คำค้นหาในขณะนี้ครับ")

        st.write("---")
        if st.button("🔄 ดึงข้อมูลเวอร์ชันล่าสุดจาก Google Sheets"):
            st.session_state.clear()
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อฐานข้อมูล...")
