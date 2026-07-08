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

# 🔑 2. แผนผังรหัสกล่องข้อความ Google Form ของพี่
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

# ดึงข้อมูลจาก Sheets มาอัปเดตลงตาราง
if read_url:
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

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ตั้งค่าเริ่มต้นของฟอร์มกรอกข้อมูล
default_doc, default_name, default_dept, default_note = "", "", "", ""
default_steps = [False] * 7

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    default_name = item["name"]
    default_dept = item["dept"]
    default_note = item["note"]
    default_steps = item["steps"] if len(item["steps"]) == 7 else [False]*7

# แบ่งคอลัมน์ซ้าย (ฟอร์ม) - ขวา (ตารางระบบค้นหา)
col1, col2 = st.columns([1, 1.4])

# ==================== ฝั่งซ้าย: ฟอร์มกรอกและแก้ไขข้อมูล ====================
with col1:
    st.subheader("📝 บันทึก / แก้ไขข้อมูล")
    
    if st.session_state.edit_id:
        st.warning(f"⚠️ กำลังแก้ไขเลขที่หนังสือ: {st.session_state.edit_id}")
    else:
        st.info("➕ กำลังเพิ่มข้อมูลรายใหม่")

    doc_num = st.text_input("เลขที่หนังสือรับ:", value=default_doc)
    name = st.text_input("ชื่อ-สกุล ผู้ขอตรวจสอบประวัติ:", value=default_name)
    dept = st.text_input("หน่วยงานต้นสังกัด (ที่ส่งมา):", value=default_dept)
    note = st.text_area("หมายเหตุ:", value=default_note, height=70)
    
    st.write("**ติ๊กเลือกขั้นตอนที่ทำเสร็จแล้ว:**")
    step_labels = [
        "1. รับหนังสือจากต้นสังกัด",
        "2. กรอกประวัติ พิมพ์ลายนิ้วมือกลิ้งหมึก 2 ชุด",
        "3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง",
        "4. ไปส่ง พฐ. ตรวจที่ ภ.จว. แล้วนำกลับมา",
        "5. ถ่ายเอกสารผลตรวจ 1 ชุด ไว้ในสำเนาคู่ฉบับ",
        "6. ทำหนังสือส่ง รายงานผลกลับต้นสังกัด (2 ชุด)",
        "7. ต้นสังกัดเซ็นรับตัวจริงและคู่สำเนา เรียบร้อย"
    ]
    
    s1 = st.checkbox(step_labels[0], value=default_steps[0])
    s2 = st.checkbox(step_labels[1], value=default_steps[1])
    s3 = st.checkbox(step_labels[2], value=default_steps[2])
    s4 = st.checkbox(step_labels[3], value=default_steps[3])
    s5 = st.checkbox(step_labels[4], value=default_steps[4])
    s6 = st.checkbox(step_labels[5], value=default_steps[5])
    s7 = st.checkbox(step_labels[6], value=default_steps[6])

    checks = [s1, s2, s3, s4, s5, s6, s7]
    
    status_text = "⚪ ยังไม่ได้เริ่ม"
    if s7:
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
                    ENTRY_MAP["s1"]: str(s1), ENTRY_MAP["s2"]: str(s2), ENTRY_MAP["s3"]: str(s3),
                    ENTRY_MAP["s4"]: str(s4), ENTRY_MAP["s5"]: str(s5), ENTRY_MAP["s6"]: str(s6), ENTRY_MAP["s7"]: str(s7)
                }
                try:
                    response = requests.post(FORM_URL, data=form_data)
                    st.session_state.db_dict[str(doc_num)] = {"name": name, "dept": dept, "status": status_text, "note": note, "steps": checks}
                    st.session_state.edit_id = None
                    st.success("🎉 บันทึกข้อมูลสำเร็จแล้วครับพี่!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error("❌ เกิดข้อผิดพลาดทางเครือข่าย แต่บันทึกบนหน้าจอชั่วคราวให้แล้วครับ")
            else:
                st.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")
                
    with btn_col2:
        if st.session_state.edit_id:
            if st.button("❌ ยกเลิกแก้ไข", use_container_width=True):
                st.session_state.edit_id = None
                st.rerun()

# ==================== ฝั่งขวา: ตารางและการค้นหาขั้นสูง ====================
with col2:
    st.subheader("📊 ตารางตรวจสอบสถานะปัจจุบัน")
    
    # 🔍 โซนค้นหาแบบระบุคอลัมน์ (Advanced Search)
    st.write("**🔍 ค้นหาข้อมูลขั้นสูง**")
    search_query = st.text_input("พิมพ์คำที่ต้องการค้นหา (เลขหนังสือ, ชื่อ, หรือสังกัด):", placeholder="พิมพ์ค้นหาที่นี่...").strip()
    
    st.write("ติ๊กเลือกคอลัมน์ที่ต้องการค้นหา:")
    c_search1, c_search2, c_search3 = st.columns(3)
    with c_search1:
        search_doc = st.checkbox("เลขที่หนังสือรับ", value=True)
    with c_search2:
        search_name = st.checkbox("ชื่อ-สกุล ผู้ขอตรวจ", value=True)
    with c_search3:
        search_dept = st.checkbox("หน่วยงานต้นสังกัด", value=False)

    st.write("---")
    
    if st.session_state.db_dict:
        # 1. แปลงข้อมูลดิบเป็น List ของดิคชันนารีเพื่อเอามากรองข้อมูล
        all_records = []
        for k, v in st.session_state.db_dict.items():
            all_records.append({
                "เลขที่หนังสือรับ": str(k),
                "ชื่อ-สกุล ผู้ขอตรวจ": str(v["name"]),
                "หน่วยงานต้นสังกัด": str(v["dept"]),
                "สถานะปัจจุบัน": str(v["status"]),
                "หมายเหตุ": str(v["note"])
            })
            
        # 2. กระบวนการกรองข้อมูลตามคำค้นหาและคอลัมน์ที่เลือกติ๊กไว้
        filtered_records = []
        if search_query:
            for r in all_records:
                match = False
                if search_doc and search_query in r["เลขที่หนังสือรับ"]:
                    match = True
                if search_name and search_query in r["ชื่อ-สกุล ผู้ขอตรวจ"]:
                    match = True
                if search_dept and search_query in r["หน่วยงานต้นสังกัด"]:
                    match = True
                if match:
                    filtered_records.append(r)
        else:
            filtered_records = all_records

        # 3. แสดงผลตารางพร้อมปุ่มแก้ไขแบบรายบรรทัด (Row-by-Row)
        if filtered_records:
            # ส่วนหัวตารางจำลองเพื่อความสวยงามและอ่านง่าย
            t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([1.2, 1.5, 1.2, 1.8, 1])
            with t_col1: st.caption("**เลขหนังสือรับ**")
            with t_col2: st.caption("**ชื่อ-สกุล**")
            with t_col3: st.caption("**ต้นสังกัด**")
            with t_col4: st.caption("**สถานะปัจจุบัน**")
            with t_col5: st.caption("**จัดการ**")
            st.write("<div style='margin-top:-10px; margin-bottom:10px; border-bottom:1px solid #ddd;'></div>", unsafe_allow_html=True)
            
            # วนลูปสร้างแถวข้อมูลทีละแถว และฝังปุ่มแก้ไขไว้ท้ายแถว
            for row in filtered_records:
                r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([1.2, 1.5, 1.2, 1.8, 1])
                with r_col1: st.write(row["เลขที่หนังสือรับ"])
                with r_col2: st.write(row["ชื่อ-สกุล ผู้ขอตรวจ"])
                with r_col3: st.write(row["หน่วยงานต้นสังกัด"])
                with r_col4: st.write(row["สถานะปัจจุบัน"])
                with r_col5:
                    # ใช้เลขที่หนังสือรับเป็น Key ของปุ่ม เพื่อไม่ให้ซ้ำกันซะเอง
                    if st.button("✏️ แก้ไข", key=f"edit_btn_{row['เลขที่หนังสือรับ']}", use_container_width=True):
                        st.session_state.edit_id = row["เลขที่หนังสือรับ"]
                        st.rerun()
                # แสดงหมายเหตุในบรรทัดย่อยหากแถวนั้นมีหมายเหตุพิมพ์ไว้
                if row["หมายเหตุ"]:
                    st.markdown(f"<p style='color:gray; font-size:13px; margin-left:10px; margin-top:-5px; margin-bottom:12px;'>📌 หมายเหตุ: {row['หมายเหตุ']}</p>", unsafe_allow_html=True)
                else:
                    st.write("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
        else:
            st.warning("🔍 ไม่พบข้อมูลที่ตรงกับเงื่อนไขการค้นหาของพี่ครับ")

        st.write("---")
        if st.button("🔄 ดึงข้อมูลเวอร์ชันล่าสุดจาก Google Sheets"):
            st.session_state.clear()
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อฐานข้อมูล...")
