import streamlit as st
import pandas as pd

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

st.markdown("""
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# 🛠️ ฟังก์ชันสำหรับแปลงลิงก์ Google Sheets ให้เป็นลิงก์ดึง CSV/ส่งข้อมูล
def get_sheet_urls():
    # ดึงลิงก์จาก Secrets ที่พี่ตั้งไว้
    try:
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # ตัดแต่งลิงก์ให้อยู่ในรูปสำหรับการอ่านและเขียนแบบ Web Form
        if "/edit" in base_url:
            sheet_id = base_url.split("/d/")[1].split("/edit")[0]
        else:
            sheet_id = base_url.split("/d/")[1].split("/")[0]
        
        read_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        return read_url, sheet_id
    except Exception:
        st.error("❌ ไม่พบลิงก์ Google Sheets ในระบบ Secrets กรุณาตรวจสอบการตั้งค่า")
        return None, None

read_url, sheet_id = get_sheet_urls()

# ดึงข้อมูลจาก Google Sheets มาแสดง
if read_url:
    try:
        df = pd.read_csv(read_url)
        # ตรวจสอบและบังคับให้หัวคอลัมน์ถูกต้อง
        cols = ["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "หน่วยงานต้นสังกัด", "สถานะปัจจุบัน", "หมายเหตุ", "step1", "step2", "step3", "step4", "step5", "step6", "step7"]
        if df.empty or list(df.columns)[:5] != cols[:5]:
            df = pd.DataFrame(columns=cols)
    except Exception:
        df = pd.DataFrame(columns=["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "หน่วยงานต้นสังกัด", "สถานะปัจจุบัน", "หมายเหตุ", "step1", "step2", "step3", "step4", "step5", "step6", "step7"])
else:
    df = pd.DataFrame(columns=["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "หน่วยงานต้นสังกัด", "สถานะปัจจุบัน", "หมายเหตุ", "step1", "step2", "step3", "step4", "step5", "step6", "step7"])

# จัดการจำลองระบบคลังเก็บข้อมูลชั่วคราวก่อนกดเซฟซิงค์ลง Google Sheets ถาวร
if "db_dict" not in st.session_state:
    st.session_state.db_dict = {}
    if not df.empty:
        for _, row in df.iterrows():
            k = str(row["เลขที่หนังสือรับ"])
            st.session_state.db_dict[k] = {
                "name": str(row["ชื่อ-สกุล ผู้ขอตรวจ"]),
                "dept": str(row["หน่วยงานต้นสังกัด"]) if pd.notna(row["หน่วยงานต้นสังกัด"]) else "",
                "status": str(row["สถานะปัจจุบัน"]),
                "note": str(row["หมายเหตุ"]) if pd.notna(row["หมายเหตุ"]) else "",
                "steps": [bool(row.get(f"step{i+1}", False)) for i in range(7)]
            }

# ระบบแก้ไขข้อมูล
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

default_doc = ""
default_name = ""
default_dept = ""
default_note = ""
default_steps = [False] * 7

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    default_name = item["name"]
    default_dept = item["dept"]
    default_note = item["note"]
    default_steps = item["steps"]

# หน้าจอฝั่งซ้าย (ฟอร์มกรอก) กับ ฝั่งขวา (ตาราง)
col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("📝 บันทึก / แก้ไขข้อมูล")
    doc_num = st.text_input("เลขที่หนังสือรับ:", value=default_doc)
    name = st.text_input("ชื่อ-สกุล ผู้ขอตรวจสอบประวัติ:", value=default_name)
    dept = st.text_input("หน่วยงานต้นสังกัด (ที่ส่งมา):", value=default_dept)
    note = st.text_area("หมายเหตุ:", value=default_note, height=70)
    
    st.write("**ติ๊กเลือกขั้นตอนที่ทำเสร็จแล้ว:**")
    step1 = st.checkbox("1. รับหนังสือจากต้นสังกัด", value=default_steps[0])
    step2 = st.checkbox("2. กรอกประวัติ พิมพ์ลายนิ้วมือกลิ้งหมึก 2 ชุด", value=default_steps[1])
    step3 = st.checkbox("3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง", value=default_steps[2])
    step4 = st.checkbox("4. ไปส่ง พฐ. ตรวจที่ ภ.จว. แล้วนำกลับมา", value=default_steps[3])
    step5 = st.checkbox("5. ถ่ายเอกสารผลตรวจ 1 ชุด ไว้ในสำเนาคู่ฉบับ", value=default_steps[4])
    step6 = st.checkbox("6. ทำหนังสือส่ง รายงานผลกลับต้นสังกัด (2 ชุด)", value=default_steps[5])
    step7 = st.checkbox("7. ต้นสังกัดเซ็นรับทั้งตัวจริงและคู่สำเนา นำคู่สำเนากลับมา", value=default_steps[6])

    checks = [step1, step2, step3, step4, step5, step6, step7]
    done_count = sum(checks)
    
    if step7:
        status_text = "🟢 เสร็จสิ้นครบ 7 ขั้นตอน"
    elif done_count > 0:
        status_text = f"🟡 กำลังดำเนินการ (ขั้นตอนที่ {done_count})"
    else:
        status_text = "⚪ ยังไม่ได้เริ่ม"

    btn_label = "💾 อัปเดตและบันทึกข้อมูลข้อมูลลงระบบ" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงระบบ"
    
    if st.button(btn_label, type="primary", use_container_width=True):
        if doc_num and name:
            # เพิ่มหรืออัปเดตลงในหน่วยความจำเว็บ
            st.session_state.db_dict[str(doc_num)] = {
                "name
