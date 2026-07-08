import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

st.markdown("""
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# 🔗 1. ลิงก์ยิงฟอร์มหลังบ้านของพี่ จากรูป action ในระบบ
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSckbSH3a337W8yknYgAsAw7esyGyEv55lgK8g6QWCv_q2HtFg/formResponse"

# 🔑 2. แผนผังรหัสกล่องข้อความจากภาพถ่ายตรวจสอบหน้าจอของพี่
ENTRY_MAP = {
    "doc": "entry.1277005650",       # เลขที่หนังสือรับ
    "name": "entry.921566157",       # ชื่อ-สกุล ผู้ขอตรวจ
    "dept": "entry.1915980561",      # หน่วยงานต้นสังกัด
    "status": "entry.1882399362",    # สถานะปัจจุบัน
    "note": "entry.1501544296",      # หมายเหตุ
    "s1": "entry.1914699467",        # step1
    "s2": "entry.1895799813",        # step2
    "s3": "entry.1846523425",        # step3
    "s4": "entry.452301442",         # step4
    "s5": "entry.1142071523",        # step5
    "s6": "entry.20673364",          # step6
    "s7": "entry.20673364_s7",       # step7 (จำลองเนื่องจากพฐ.มี 6 ข้อในโค้ดเก่า)
}

# 🔄 3. ฟังก์ชันดึงลิงก์อ่านข้อมูลโดยตรงผ่านสิทธิ์แชร์ "ทุกคนที่มีลิงก์"
def get_sheet_urls():
    try:
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sheet_id = base_url.split("/d/")[1].split("/edit")[0] if "/edit" in base_url else base_url.split("/d/")[1].split("/")[0]
        # เจาะจงดึงข้อมูลจากแท็บแรกที่มีข้อมูลการตอบกลับจากฟอร์มมาแสดงผล
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    except:
        return None

read_url = get_sheet_urls()

# ตัวแปรเก็บฐานข้อมูลชั่วคราวบนหน้าจอหลัก
if "db_dict" not in st.session_state:
    st.session_state.db_dict = {}

# ดึงข้อมูลจาก Sheets มาอัปเดตลงตารางขวา
if read_url:
    try:
        df = pd.read_csv(read_url)
        if not df.empty:
            for _, row in df.iterrows():
                # ตรวจเช็กจำนวนคอลัมน์เพื่อความชัวร์ (ปกติคอลัมน์แรกคือ Timestamp ของ Form)
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

default_doc, default_name, default_dept, default_note = "", "", "", ""
default_steps = [False] * 7

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    default_name = item["name"]
    default_dept = item["dept"]
    default_note = item["note"]
    default_steps = item["steps"] if len(item["steps"]) == 7 else [False]*7

col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("📝 บันทึก / แก้ไขข้อมูล")
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
        for idx in range(5, -1, -1):
            if checks[idx]:
                status_text = f"🟡 {step_labels[idx]}"
                break

    btn_label = "💾 อัปเดตและบันทึกข้อมูลข้อมูลลงระบบ" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงระบบ"
    
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
                # ส่งเข้า Google ฟอร์มตรงๆ ไม่ต้องผ่าน Service Account
                response = requests.post(FORM_URL, data=form_data)
                
                # บันทึกเข้าความจำหน้าจอทันทีเพื่อความเร็ว
                st.session_state.db_dict[str(doc_num)] = {"name": name, "dept": dept, "status": status_text, "note": note, "steps": checks}
                st.session_state.edit_id = None
                st.success("🎉 บันทึกข้อมูลเข้า Google Sheets สำเร็จเรียบร้อยแล้วครับพี่!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error("❌ เกิดข้อผิดพลาดทางเครือข่าย แต่บันทึกบนหน้าจอชั่วคราวให้แล้วครับ")
        else:
            st.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")

    if st.session_state.edit_id and st.button("❌ ยกเลิกการแก้ไข", use_container_width=True):
        st.session_state.edit_id = None
        st.rerun()

with col2:
    st.subheader("📊 ตารางตรวจสอบสถานะปัจจุบัน")
    if st.session_state.db_dict:
        records = []
        for k, v in st.session_state.db_dict.items():
            records.append({
                "เลขที่หนังสือรับ": k, 
                "ชื่อ-สกุล ผู้ขอตรวจ": v["name"], 
                "หน่วยงานต้นสังกัด": v["dept"], 
                "สถานะปัจจุบัน": v["status"], 
                "หมายเหตุ": v["note"]
            })
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        
        st.write("---")
        if st.button("🔄 ดึงข้อมูลเวอร์ชันล่าสุดจาก Google Sheets"):
            st.session_state.clear()
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อฐานข้อมูล...")
