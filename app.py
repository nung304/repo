import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

st.markdown("""
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# เชื่อมต่อ Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0s")
except Exception:
    df = pd.DataFrame(columns=["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "หน่วยงานต้นสังกัด", "สถานะปัจจุบัน", "หมายเหตุ", "step1", "step2", "step3", "step4", "step5", "step6", "step7"])

# ค้นหาเคสที่จะแก้ไข
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

default_doc = ""
default_name = ""
default_dept = ""
default_note = ""
default_steps = [False] * 7

if st.session_state.edit_id is not None and not df.empty:
    target = df[df["เลขที่หนังสือรับ"].astype(str) == str(st.session_state.edit_id)]
    if not target.empty:
        idx = target.index[0]
        default_doc = str(target.at[idx, "เลขที่หนังสือรับ"])
        default_name = str(target.at[idx, "ชื่อ-สกุล ผู้ขอตรวจ"])
        default_dept = str(target.at[idx, "หน่วยงานต้นสังกัด"]) if pd.notna(target.at[idx, "หน่วยงานต้นสังกัด"]) else ""
        default_note = str(target.at[idx, "หมายเหตุ"]) if pd.notna(target.at[idx, "หมายเหตุ"]) else ""
        for i in range(7):
            default_steps[i] = bool(target.at[idx, f"step{i+1}"])

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

    btn_label = "💾 อัปเดตข้อมูลเก่า" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงระบบ"
    
    if st.button(btn_label, type="primary", use_container_width=True):
        if doc_num and name:
            # ลบแถวเก่าถ้าเป็นการอัปเดตหรือเลขซ้ำ
            if not df.empty:
                df = df[df["เลขที่หนังสือรับ"].astype(str) != str(doc_num)]
            
            new_row = pd.DataFrame([{
                "เลขที่หนังสือรับ": doc_num, "ชื่อ-สกุล ผู้ขอตรวจ": name, "หน่วยงานต้นสังกัด": dept,
                "สถานะปัจจุบัน": status_text, "หมายเหตุ": note,
                "step1": step1, "step2": step2, "step3": step3, "step4": step4, "step5": step5, "step6": step6, "step7": step7
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=df)
            st.session_state.edit_id = None
            st.success("บันทึกข้อมูลลงฐานข้อมูล Google Sheets เรียบร้อย!")
            st.rerun()
        else:
            st.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")

    if st.session_state.edit_id is not None:
        if st.button("❌ ยกเลิกการแก้ไข", use_container_width=True):
            st.session_state.edit_id = None
            st.rerun()

with col2:
    st.subheader("📊 ตารางตรวจสอบสถานะปัจจุบัน")
    if not df.empty:
        show_df = df[["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "หน่วยงานต้นสังกัด", "สถานะปัจจุบัน", "หมายเหตุ"]]
        st.dataframe(show_df, use_container_width=True, hide_index=True)
        
        st.write("---")
        st.write("**⚙️ เครื่องมือจัดการข้อมูล:**")
        select_doc = st.selectbox("เลือกเลขที่หนังสือรับที่ต้องการจัดการ:", ["-- เลือกรายการ --"] + list(df["เลขที่หนังสือรับ"].unique()))
        
        if select_doc != "-- เลือกรายการ --":
            c_edit, c_del = st.columns(2)
            with c_edit:
                if st.button("✏️ ดึงข้อมูลไปแก้ไข", use_container_width=True):
                    st.session_state.edit_id = select_doc
                    st.rerun()
            with c_del:
                if st.button("🗑️ ลบข้อมูลเคสนี้", use_container_width=True):
                    df = df[df["เลขที่หนังสือรับ"].astype(str) != str(select_doc)]
                    conn.update(data=df)
                    if st.session_state.edit_id == select_doc:
                        st.session_state.edit_id = None
                    st.success("ลบข้อมูลออกจาก Google Sheets เรียบร้อย!")
                    st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อฐานข้อมูล...")
