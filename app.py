import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

st.markdown("""
    <style>
    .stTable, [data-testid="stTable"] {
        display: block !important;
        width: 100% !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        -webkit-overflow-scrolling: touch !important;
    }
    .stButton > button {
        padding: 4px 10px !important;
        font-size: 14px !important;
    }
    </style>
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;font-size:24px;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.) [ระบบฐานข้อมูลออนไลน์]</h2>
    </div>
""", unsafe_allow_html=True)

# 🔑 เชื่อมต่อกับคลาวด์ Supabase ผ่าน Secrets
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("🚨 ไม่สามารถดึงรหัสเชื่อมต่อฐานข้อมูลออนไลน์ได้ กรุณาตรวจสอบการตั้งค่าหลังบ้านในระบบ Secrets")
    st.stop()

# รายชื่อขั้นตอนทั้งหมด (แบบเต็ม)
step_labels = [
    "1. รับหนังสือจากต้นสังกัด",
    "2. กรอกประวัติ พิมพ์ลายนิ้วมือกลิ้งหมึก 2 ชุด",
    "3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง",
    "4. ไปส่ง พฐ. ตรวจที่ ภ.จว. แล้วนำกลับมา",
    "5. ถ่ายเอกสารผลตรวจ 1 ชุด ไว้ในสำเนาคู่ฉับ",
    "6. ทำหนังสือส่ง รายงานผลกลับต้นสังกัด (2 ชุด)",
    "7. ต้นสังกัดเซ็นรับตัวจริงและคู่สำเนา เรียบร้อย"
]

if "db_dict" not in st.session_state:
    st.session_state.db_dict = {}
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "selected_dashboard_step" not in st.session_state:
    st.session_state.selected_dashboard_step = None
if "form_key_index" not in st.session_state:
    st.session_state.form_key_index = 0

# 🔄 ดึงข้อมูลจากคลาวด์ออนไลน์ล่าสุด
if not st.session_state.get("prevent_reloading", False):
    try:
        response = supabase.table("cases").select("*").execute()
        rows = response.data
        
        new_db = {}
        for row in rows:
            k = str(row.get("doc")).strip()
            if k:
                new_db[k] = {
                    "name": row.get("name", ""),
                    "dept": row.get("dept", ""),
                    "status": row.get("status", "⚪ ยังไม่ได้เริ่ม"),
                    "note": row.get("note", ""),
                    "steps": [
                        str(row.get("s1", "False")).strip() == "True",
                        str(row.get("s2", "False")).strip() == "True",
                        str(row.get("s3", "False")).strip() == "True",
                        str(row.get("s4", "False")).strip() == "True",
                        str(row.get("s5", "False")).strip() == "True",
                        str(row.get("s6", "False")).strip() == "True",
                        str(row.get("s7", "False")).strip() == "True"
                    ]
                }
        st.session_state.db_dict = new_db
    except Exception as e:
        st.warning(f"⚠️ ดึงข้อมูลออนไลน์ขัดข้องชั่วคราว: {e}")

st.session_state["prevent_reloading"] = False

# 🗑️ บล็อกยืนยันการลบข้อมูลออกจากคลาวด์
@st.dialog("⚠️ ยืนยันการลบข้อมูลถาวร")
def confirm_delete_dialog(doc_id, name):
    st.write(f"คุณแน่ใจหรือไม่ว่าต้องการลบข้อมูลของ **{name}** (เลขที่หนังสือ: {doc_id})?")
    st.error("🚨 ระบบจะลบแถวข้อมูลรายนี้ออกจากฐานข้อมูลออนไลน์ถาวรทันที!")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚨 ยืนยันลบข้อมูล", type="primary", use_container_width=True):
            try:
                supabase.table("cases").delete().eq("doc", doc_id).execute()
                if doc_id in st.session_state.db_dict:
                    del st.session_state.db_dict[doc_id]
                st.session_state["prevent_reloading"] = True
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
    with c2:
        if st.button("❌ ยกเลิก", use_container_width=True):
            st.rerun()

# เซ็ตค่าเริ่มต้นฟอร์ม
default_doc, default_name, default_dept, default_note = "", "", "", ""
loaded_steps = [False] * 7
default_title_index = 0

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    full_name_str = item["name"]
    default_dept = item["dept"]
    
    # ดึงเฉพาะข้อความหมายเหตุจริง ๆ ออกมาจาก String แท็กวันที่
    raw_note = item["note"]
    if " [รับเรื่อง:" in raw_note:
        default_note = raw_note.split(" [รับเรื่อง:")[0].strip()
    else:
        default_note = raw_note
        
    loaded_steps = item["steps"]
    
    if full_name_str.startswith("นาย"):
        default_title_index = 0
        default_name = full_name_str.replace("นาย", "", 1)
    elif full_name_str.startswith("นางสาว"):
        default_title_index = 1
        default_name = full_name_str.replace("นางสาว", "", 1)
    elif full_name_str.startswith("นาง"):
        default_title_index = 2
        default_name = full_name_str.replace("นาง", "", 1)
    else:
        default_name = full_name_str

def on_step_change(index):
    w_key = f"step_idx_{index}_{st.session_state.form_key_index}"
    if st.session_state.get(w_key, False):
        for i in range(index + 1):
            st.session_state[f"step_idx_{i}_{st.session_state.form_key_index}"] = True
    else:
        for i in range(index, 7):
            st.session_state[f"step_idx_{i}_{st.session_state.form_key_index}"] = False

col1, col2 = st.columns([1, 1.8])

# ==================== ฝั่งซ้าย: แดชบอร์ดปุ่มกด + ฟอร์มบันทึกข้อมูล ====================
with col1:
    # 📊 1. แดชบอร์ดปุ่มสรุปจำนวนเรื่อง
    st.subheader("📊 ระบบติดตามสถานะภาพรวม")
    
    counts = [0] * 8  
    for k, v in st.session_state.db_dict.items():
        v_status = v["status"]
        if "ยังไม่ได้เริ่ม" in v_status: counts[7] += 1
        else:
            for idx, label in enumerate(step_labels):
                if label in v_status: counts[idx] += 1; break

    st.write("**📌 กระดานสรุปสถานะปัจจุบัน (คลิกเพื่อกรองดูรายชื่อ):**")
    
    d_row1_c1, d_row1_c2 = st.columns(2)
    with d_row1_c1:
        if st.button(f"📁 ดำเนินการถึง {step_labels[0]} ({counts[0]} เรื่อง)", key="b1", type="primary" if st.session_state.selected_dashboard_step == 0 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 0 else 0; st.rerun()
    with d_row1_c2:
        if st.button(f"📝 ดำเนินการถึง {step_labels[1]} ({counts[1]} เรื่อง)", key="b2", type="primary" if st.session_state.selected_dashboard_step == 1 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 1 else 1; st.rerun()

    d_row2_c1, d_row2_c2 = st.columns(2)
    with d_row2_c1:
        if st.button(f"✉️ ดำเนินการถึง {step_labels[2]} ({counts[2]} เรื่อง)", key="b3", type="primary" if st.session_state.selected_dashboard_step == 2 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 2 else 2; st.rerun()
    with d_row2_c2:
        if st.button(f"🚔 ดำเนินการถึง {step_labels[3]} ({counts[3]} เรื่อง)", key="b4", type="primary" if st.session_state.selected_dashboard_step == 3 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 3 else 3; st.rerun()

    d_row3_c1, d_row3_c2 = st.columns(2)
    with d_row3_c1:
        if st.button(f"🖨️ ดำเนินการถึง {step_labels[4]} ({counts[4]} เรื่อง)", key="b5", type="primary" if st.session_state.selected_dashboard_step == 4 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 4 else 4; st.rerun()
    with d_row3_c2:
        if st.button(f"📤 ดำเนินการถึง {step_labels[5]} ({counts[5]} เรื่อง)", key="b6", type="primary" if st.session_state.selected_dashboard_step == 5 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 5 else 5; st.rerun()

    d_row4_c1, d_row4_c2 = st.columns(2)
    with d_row4_c1:
        if st.button(f"🟢 เสร็จสิ้น{step_labels[6]} ({counts[6]} เรื่อง)", key="b7", type="primary" if st.session_state.selected_dashboard_step == 6 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 6 else 6; st.rerun()
    with d_row4_c2:
        if st.button(f"⚪ ยังไม่เริ่มดำเนินการ ({counts[7]} เรื่อง)", key="b8", type="primary" if st.session_state.selected_dashboard_step == 7 else "secondary", use_container_width=True):
            st.session_state.selected_dashboard_step = None if st.session_state.selected_dashboard_step == 7 else 7; st.rerun()

    st.write("---")

    # 📝 2. ฟอร์มบันทึก / แก้ไขข้อมูล
    st.subheader("📝 บันทึก / แก้ไขข้อมูล")
    if st.session_state.edit_id:
        st.warning(f"⚠️ กำลังแก้ไขเลขที่หนังสือ: {st.session_state.edit_id}")
    else:
        st.info("➕ กำลังเพิ่มข้อมูลรายใหม่ (ระบบจะบันทึกวันที่รับเรื่องวันนี้อัตโนมัติ)")

    doc_num = st.text_input("เลขที่หนังสือรับ:", value=default_doc, key=f"doc_inp_{st.session_state.form_key_index}", disabled=(st.session_state.edit_id is not None))
    title_prefix = st.radio("คำนำหน้านาม:", ["นาย", "นางสาว", "นาง"], index=default_title_index, horizontal=True, key=f"title_inp_{st.session_state.form_key_index}")
    name_input = st.text_input("ชื่อ-สกุล ผู้ขอตรวจสอบประวัติ (ไม่ต้องพิมพ์คำนำหน้าซ้ำ):", value=default_name, key=f"name_inp_{st.session_state.form_key_index}")
    dept = st.text_input("หน่วยงานต้นสังกัด (ที่ส่งมา):", value=default_dept, key=f"dept_inp_{st.session_state.form_key_index}")
    note = st.text_area("หมายเหตุเพิ่มเติม:", value=default_note, height=70, key=f"note_inp_{st.session_state.form_key_index}")
    
    st.write("**ติ๊กเลือกขั้นตอนที่ทำเสร็จแล้ว:**")
    for idx, label in enumerate(step_labels):
        st.checkbox(label, value=loaded_steps[idx], key=f"step_idx_{idx}_{st.session_state.form_key_index}", on_change=on_step_change, args=(idx,))

    checks = [st.session_state.get(f"step_idx_{i}_{st.session_state.form_key_index}", False) for i in range(7)]
    status_text = "⚪ ยังไม่ได้เริ่ม"
    if checks[6]:
        status_text = f"🟢 {step_labels[6]}"
    else:
        for idx in range(6, -1, -1):
            if checks[idx]:
                status_text = f"🟡 {step_labels[idx]}"
                break

    btn_label = "💾 อัปเดตทับข้อมูลแถวเดิม" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงคลาวด์"
    msg_slot = st.empty()
    
    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        if st.button(btn_label, type="primary", use_container_width=True):
            if doc_num and name_input:
                full_name = f"{title_prefix}{name_input.strip()}"
                today_str = datetime.today().strftime('%Y-%m-%d')
                
                # 🛠️ จัดการระบบแสตมป์วันที่อัตโนมัติ
                if st.session_state.edit_id:
                    # ถ้าเป็นงานเดิมที่เคยบันทึกไว้ ให้ดึงวันที่รับเรื่องเดิมมาใช้
                    old_item = st.session_state.db_dict.get(st.session_state.edit_id, {})
                    old_note_str = old_item.get("note", "")
                    
                    # ค้นหาวันที่รับเรื่องเดิม
                    if "[รับเรื่อง:" in old_note_str:
                        start_date = old_note_str.split("[รับเรื่อง:")[1].split("]")[0].strip()
                    else:
                        start_date = today_str
                        
                    # ตรวจสอบสถานะว่าสำเร็จ (ขั้นตอนที่ 7) หรือยัง
                    if checks[6]:
                        # ค้นหาวันที่สำเร็จเดิม หรือสลอตวันนี้ถ้าเพิ่งสำเร็จ
                        if "[สำเร็จ:" in old_note_str:
                            end_date = old_note_str.split("[สำเร็จ:")[1].split("]")[0].strip()
                            if end_date == "-":
                                end_date = today_str
                        else:
                            end_date = today_str
                    else:
                        end_date = "-"
                else:
                    # ถ้าเป็นเรื่องที่เพิ่มใหม่สดๆ ร้อนๆ
                    start_date = today_str
                    end_date = today_str if checks[6] else "-"
                
                # ประกอบข้อมูลวันที่รวมเข้ากับฟิลด์หมายเหตุ
                final_note = f"{note.strip()} [รับเรื่อง: {start_date}] [สำเร็จ: {end_date}]"
                
                case_data = {
                    "doc": str(doc_num).strip(), "name": full_name, "dept": dept, "status": status_text, "note": final_note,
                    "s1": str(checks[0]), "s2": str(checks[1]), "s3": str(checks[2]), "s4": str(checks[3]), 
                    "s5": str(checks[4]), "s6": str(checks[5]), "s7": str(checks[6])
                }
                try:
                    if st.session_state.edit_id:
                        supabase.table("cases").update(case_data).eq("doc", st.session_state.edit_id).execute()
                    else:
                        supabase.table("cases").insert(case_data).execute()
                    
                    st.session_state.db_dict[str(doc_num)] = {"name": full_name, "dept": dept, "status": status_text, "note": final_note, "steps": checks}
                    st.session_state.edit_id = None
                    st.session_state["prevent_reloading"] = False
                    st.session_state.form_key_index += 1
                    st.rerun()
                except Exception as e:
                    msg_slot.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
            else:
                msg_slot.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")
                
    with btn_col2:
        if st.session_state.edit_id:
            if st.button("❌ ยกเลิก", use_container_width=True):
                st.session_state.edit_id = None
                st.session_state["prevent_reloading"] = True
                st.session_state.form_key_index += 1
                st.rerun()

# ==================== 📋 ฝั่งขวา: กล่องค้นหาและตารางรายชื่อตรวจสอบข้อมูลภาพรวม ====================
with col2:
    search_query = st.text_input("พิมพ์รหัสหนังสือ หรือ ชื่อบุคคลที่ต้องการค้นหา:", placeholder="พิมพ์ค้นหาที่นี่...").strip()
    
    if st.session_state.selected_dashboard_step is not None:
        if st.button("❌ ล้างตัวกรองปุ่มขั้นตอน Dashboard", use_container_width=True):
            st.session_state.selected_dashboard_step = None; st.rerun()

    st.write("---")
    st.write("**📋 ตารางตรวจสอบสถานะปัจจุบัน**")
    
    if st.session_state.db_dict:
        header_cols = st.columns([1, 1.2, 1, 1.8, 1.4, 0.7, 0.7])
        with header_cols[0]: st.markdown("**เลขหนังสือ**")
        with header_cols[1]: st.markdown("**ชื่อ-สกุล**")
        with header_cols[2]: st.markdown("**ต้นสังกัด**")
        with header_cols[3]: st.markdown("**สถานะปัจจุบัน**")
        with header_cols[4]: st.markdown("**หมายเหตุและประวัติติดตาม**")
        with header_cols[5]: st.markdown("**แก้ไข**")
        with header_cols[6]: st.markdown("**ลบ**")
        st.write("<div style='border-bottom: 2px solid #800000; margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        for k, v in st.session_state.db_dict.items():
            s_idx = 7 if "ยังไม่ได้เริ่ม" in v["status"] else next((i for i, x in enumerate(step_labels) if x in v["status"]), None)
            if st.session_state.selected_dashboard_step is not None and s_idx != st.session_state.selected_dashboard_step: continue
            if search_query and (search_query not in str(k) and search_query not in str(v["name"]) and search_query not in str(v["dept"]) and search_query not in str(v["note"])): continue
                
            row_cols = st.columns([1, 1.2, 1, 1.8, 1.4, 0.7, 0.7])
            with row_cols[0]: st.write(k)
            with row_cols[1]: st.write(v["name"])
            with row_cols[2]: st.write(v["dept"])
            with row_cols[3]: st.write(v["status"])
            with row_cols[4]: st.write(v["note"] if v["note"] else "-")
            
            with row_cols[5]:
                if st.button("✏️", key=f"edit_btn_{k}", use_container_width=True):
                    st.session_state.edit_id = k
                    st.session_state.form_key_index += 1; st.rerun()
            with row_cols[6]:
                if st.button("🗑️", key=f"del_btn_{k}", use_container_width=True):
                    confirm_delete_dialog(k, v["name"])
                    
            st.write("<div style='border-bottom: 1px solid #eee; margin-top: 4px; margin-bottom: 4px;'></div>", unsafe_allow_html=True)

        st.write("---")
        if st.button("🔄 ดึงข้อมูลเวอร์ชันล่าสุดจากฐานข้อมูลออนไลน์", use_container_width=True):
            st.session_state.clear(); st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อฐานข้อมูล...")
