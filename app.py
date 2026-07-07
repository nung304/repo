import streamlit as st
import pandas as pd

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

# ส่วนหัวของเว็บ (สีเลือดหมูตำรวจ)
st.markdown("""
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# จำลองฐานข้อมูลใน Session State
if "db_dict" not in st.session_state:
    st.session_state.db_dict = {}

# ดึงข้อมูลเพื่อเตรียมแก้ไข (ถ้ามี)
edit_key = st.session_state.get("edit_key", None)
default_doc = ""
default_name = ""
default_dept = ""
default_note = ""
default_steps = [False] * 7

if edit_key and edit_key in st.session_state.db_dict:
    item = st.session_state.db_dict[edit_key]
    default_doc = edit_key
    default_name = item["name"]
    default_dept = item["dept"]
    default_note = item["note"]
    default_steps = item["steps"]

# แบ่งหน้าจอเป็น 2 ฝั่ง (ฝั่งกรอกข้อมูล - ฝั่งตาราง)
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

    # คำนวณสถานะ
    checks = [step1, step2, step3, step4, step5, step6, step7]
    done_count = sum(checks)
    
    if step7:
        status_text = "🟢 เสร็จสิ้นครบ 7 ขั้นตอน"
    elif done_count > 0:
        status_text = f"🟡 กำลังดำเนินการ (ขั้นตอนที่ {done_count})"
    else:
        status_text = "⚪ ยังไม่ได้เริ่ม"

    btn_label = "💾 อัปเดตข้อมูลเก่า" if edit_key else "💾 บันทึกข้อมูลลงระบบ"
    
    if st.button(btn_label, type="primary", use_container_width=True):
        if doc_num and name:
            # บันทึกข้อมูล (ถ้าใช้เลขหนังสือซ้ำจะถือเป็นการอัปเดตตัวเดิมอัตโนมัติ)
            st.session_state.db_dict[doc_num] = {
                "name": name,
                "dept": dept,
                "note": note,
                "status": status_text,
                "steps": checks
            }
            # ล้างสถานะแก้ไขหลังจากบันทึกเสร็จ
            if "edit_key" in st.session_state:
                del st.session_state.edit_key
            st.success(f"บันทึกข้อมูลเลขที่ {doc_num} สำเร็จ!")
            st.rerun()
        else:
            st.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")
            
    if edit_key:
        if st.button("❌ ยกเลิกการแก้ไข (กลับไปเพิ่มเคสใหม่)", use_container_width=True):
            if "edit_key" in st.session_state:
                del st.session_state.edit_key
            st.rerun()

with col2:
    st.subheader("📊 ตารางตรวจสอบสถานะปัจจุบัน")
    
    if st.session_state.db_dict:
        # แปลงข้อมูลใน dict ออกมาเป็น DataFrame เพื่อแสดงในตาราง
        records = []
        for k, v in st.session_state.db_dict.items():
            records.append({
                "เลขที่หนังสือรับ": k,
                "ชื่อ-สกุล ผู้ขอตรวจ": v["name"],
                "หน่วยงานต้นสังกัด": v["dept"],
                "สถานะปัจจุบัน": v["status"],
                "หมายเหตุ": v["note"]
            })
        df = pd.DataFrame(records)
        
        # แสดงตารางข้อมูล
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.write("---")
        st.write("**⚙️ เครื่องมือจัดการข้อมูล:**")
        
        # ตัวเลือกสำหรับแก้ไขหรือลบข้อมูล
        select_doc = st.selectbox("เลือกเลขที่หนังสือรับที่ต้องการจัดการ:", ["-- เลือกรายการ --"] + list(st.session_state.db_dict.keys()))
        
        if select_doc != "-- เลือกรายการ --":
            c_edit, c_del = st.columns(2)
            with c_edit:
                if st.button("✏️ ดึงข้อมูลไปแก้ไข", use_container_width=True):
                    st.session_state.edit_key = select_doc
                    st.rerun()
            with c_del:
                if st.button("🗑️ ลบข้อมูลเคสนี้", use_container_width=True):
                    del st.session_state.db_dict[select_doc]
                    if st.session_state.get("edit_key") == select_doc:
                        del st.session_state.edit_key
                    st.success(f"ลบข้อมูลเลขที่ {select_doc} เรียบร้อยแล้ว")
                    st.rerun()
                    
        if st.button("⚠️ ล้างข้อมูลทั้งหมดในตาราง", type="secondary"):
            st.session_state.db_dict = {}
            if "edit_key" in st.session_state:
                del st.session_state.edit_key
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ กรุณากรอกข้อมูลในฟอร์มฝั่งซ้ายมือ")
