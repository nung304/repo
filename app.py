import streamlit as st
import pandas as pd

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

st.markdown("""
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

if "db" not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "สถานะปัจจุบัน"])

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 บันทึกและอัปเดตข้อมูล")
    doc_num = st.text_input("เลขที่หนังสือรับ:")
    name = st.text_input("ชื่อ-สกุล ผู้ขอตรวจสอบประวัติ:")
    
    st.write("**ติ๊กเลือกขั้นตอนที่ทำเสร็จแล้ว:**")
    step1 = st.checkbox("1. รับหนังสือจากต้นสังกัด")
    step2 = st.checkbox("2. กรอกประวัติ พิมพ์ลายนิ้วมือกลิ้งหมึก 2 ชุด")
    step3 = st.checkbox("3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง")
    step4 = st.checkbox("4. ไปส่ง พฐ. ตรวจที่ ภ.จว. แล้วนำกลับมา")
    step5 = st.checkbox("5. ถ่ายเอกสารผลตรวจ 1 ชุด ไว้ในสำเนาคู่ฉบับ")
    step6 = st.checkbox("6. ทำหนังสือส่ง รายงานผลกลับต้นสังกัด (2 ชุด)")
    step7 = st.checkbox("7. ต้นสังกัดเซ็นรับทั้งตัวจริงและคู่สำเนา นำคู่สำเนากลับมา")

    checks = [step1, step2, step3, step4, step5, step6, step7]
    done_count = sum(checks)
    
    if step7:
        status_text = "🟢 เสร็จสิ้นครบ 7 ขั้นตอน"
    elif done_count > 0:
        status_text = f"🟡 กำลังดำเนินการ (ขั้นตอนที่ {done_count})"
    else:
        status_text = "⚪ ยังไม่ได้เริ่ม"

    if st.button("💾 บันทึก / อัปเดตข้อมูลลงระบบ", type="primary"):
        if doc_num and name:
            st.session_state.db = st.session_state.db[st.session_state.db["เลขที่หนังสือรับ"] != doc_num]
            new_data = pd.DataFrame([[doc_num, name, status_text]], columns=["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "สถานะปัจจุบัน"])
            st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
            st.success(f"บันทึกข้อมูลเลขที่ {doc_num} สำเร็จ!")
            st.rerun()
        else:
            st.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")

with col2:
    st.subheader("📊 ตารางตรวจสอบสถานะปัจจุบัน")
    if not st.session_state.db.empty:
        st.dataframe(st.session_state.db, use_container_width=True, hide_index=True)
        if st.button("⚠️ ล้างข้อมูลทั้งหมดในตาราง"):
            st.session_state.db = pd.DataFrame(columns=["เลขที่หนังสือรับ", "ชื่อ-สกุล ผู้ขอตรวจ", "สถานะปัจจุบัน"])
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ กรุณากรอกข้อมูลในฟอร์มฝั่งซ้ายมือ")
