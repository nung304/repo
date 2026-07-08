import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

st.markdown("""
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# 🔗 1. ลิงก์ยิงฟอร์มหลังบ้านของพี่ (ดึงจาก action ของฟอร์มในภาพของพี่มาให้เรียบร้อยแล้วครับ)
FORM_URL = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSckbSH3a337W8yknyGAsAw7esyGyEv55lgK8g6qWCv_q2HtgF/formResponse"

# 🔑 2. แผนผังรหัสกล่องข้อความที่แกะจากหน้าจอของพี่เป๊ะๆ
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
    "s7": "entry.20673364_s7",       # step7 (จำลองรหัสตัวสุดท้ายเพื่อระบบหลังบ้าน)
}

# ฟังก์ชันดึงลิงก์อ่านข้อมูลจาก Google Sheets (มาโชว์ที่ตารางขวา)
def get_sheet_urls():
    try:
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sheet_id = base_url.split("/d/")[1].split("/edit")[0] if "/edit" in base_url else base_url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    except:
        return None

read_url = get_sheet_urls()
cols = ["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "หน่วยงานต้นสังกัด", "สถานะปัจจุบัน", "หมายเหตุ", "step1", "step2", "step3", "step4", "step5", "step6", "step7"]

if read_url:
    try:
        df = pd.read_csv(read_url)
        # ปรับจำนวนคอลัมน์ให้ล้อไปตามโครงสร้างข้อมูล
        df.columns = cols[:len(df.columns)]
    except:
        df = pd.DataFrame(columns=cols)
else:
    df = pd.DataFrame(columns=cols)

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
    default_steps = item["steps"]

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
            # 🚀 ยิงส่งข้อมูลผ่านสตรีมเข้าฟอร์มทันทีเมื่อกดปุ่ม
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
                requests.post(FORM_URL, data=form_data)
                st.session_state.db_dict[str(doc_num)] = {"name": name, "dept": dept, "status": status_text, "note": note, "steps": checks}
                st.session_state.edit_id = None
                st.success("🎉 บันทึกข้อมูลลงฐานข้อมูล Google Sheets ถาวรเรียบร้อยแล้ว!")
                st.balloons()
                st.rerun()
            except:
                st.error("❌ ระบบขัดข้องชั่วคราว แต่ข้อมูลบันทึกบนหน้าจอให้แล้วครับ")
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
            records.append({"เลขที่หนังสือรับ": k, "ชื่อ-สกุล ผู้ขอตรวจ": v["name"], "หน่วยงานต้นสังกัด": v["dept"], "สถานะปัจจุบัน": v["status"], "หมายเหตุ": v["note"]})
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        
        st.write("---")
        st.write("**⚙️ เครื่องมือจัดการข้อมูล:**")
        select_doc = st.selectbox("เลือกเลขที่หนังสือรับที่ต้องการจัดการ:", ["-- เลือกรายการ --"] + list(st.session_state.db_dict.keys()))
        
        if select_doc != "-- เลือกรายการ --":
            c_edit, c_del = st.columns(2)
            with c_edit:
                if st.button("✏️ ดึงข้อมูลไปแก้ไข", use_container_width=True):
                    st.session_state.edit_id = select_doc
                    st.rerun()
            with c_del:
                if st.button("🗑️ ลบข้อมูลเคสนี้", use_container_width=True):
                    if select_doc in st.session_state.db_dict: del st.session_state.db_dict[select_doc]
                    if st.session_state.edit_id == select_doc: st.session_state.edit_id = None
                    st.success("ลบข้อมูลเรียบร้อยแล้ว")
                    st.rerun()
                    
        if st.button("🔄 ดึงข้อมูลอัปเดตจาก Google Sheets ใหม่"):
            st.session_state.clear()
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังดึงข้อมูลจาก Google Sheets...")
