import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

# 🎨 🛠️ ปรับแต่งตารางระบบตรวจประวัติใหม่ทั้งหมด ให้ตรงเป๊ะทั้งในคอมและในโทรศัพท์
st.markdown("""
    <style>
    /* พื้นหลังหลักขาวสะอาดตา */
    .stApp {
        background-color: #ffffff;
        color: #2d3748;
    }
    
    /* สไตล์กล่องแดชบอร์ดขั้นตอน */
    .step-card {
        color: white !important;
        border-radius: 10px;
        margin-bottom: 6px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        text-align: center;
    }
    .step-card-inner {
        padding: 15px 8px;
    }
    .step-card-value {
        font-size: 42px; 
        font-weight: 900; 
        margin: 0;
        line-height: 1;
        color: #ffffff !important;
    }
    .step-card-title {
        font-size: 14px; 
        font-weight: 700;
        color: #ffffff !important;
        margin-top: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 44px;
        line-height: 22px;
    }
    
    /* 📋 📊 โครงสร้างตารางโมเดิร์นแบบล็อกหัวข้อให้ตรงกับข้อมูล 100% */
    .modern-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
        background-color: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .modern-table th {
        background: linear-gradient(135deg, #1e3d59, #2b5c8f);
        color: #ffffff !important;
        font-weight: 600;
        padding: 14px 12px;
        text-align: left;
        font-size: 15px;
        border: none;
    }
    
    .modern-table td {
        padding: 14px 12px;
        font-size: 14px;
        color: #2d3748;
        border-bottom: 1px solid #edf2f7;
        vertical-align: middle;
        white-space: normal; /* ยอมให้ข้อความขึ้นบรรทัดใหม่เมื่อยาวเกินไป ช่องจะไม่เบี้ยว */
        word-wrap: break-word;
    }
    
    .modern-table tr:hover {
        background-color: #f7fafc;
    }
    
    /* ซ่อนป้ายข้อความสำหรับมือถือเมื่อเปิดบนคอมพิวเตอร์ */
    .m-title {
        display: none;
    }

    /* 📱 CSS จัดการหน้าจอโทรศัพท์ (Responsive Mobile Layout) */
    @media screen and (max-width: 800px) {
        /* ซ่อนหัวตารางเดิมของคอมพิวเตอร์ */
        .modern-table thead {
            display: none;
        }
        
        /* เปลี่ยนโครงสร้างตารางให้แตกออกมารียงเป็นแผ่นการ์ดรายบุคคล */
        .modern-table, .modern-table tbody, .modern-table tr, .modern-table td {
            display: block;
            width: 100%;
        }
        
        .modern-table tr {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            margin-bottom: 15px;
            padding: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        
        .modern-table td {
            text-align: left;
            padding: 8px 4px;
            border-bottom: 1px dashed #f0f4f8;
        }
        
        .modern-table td:last-child {
            border-bottom: none;
        }
        
        /* เปิดใช้งานและตกแต่งป้ายกำกับหัวข้อในโทรศัพท์ให้สวยงาม */
        .m-title {
            display: inline-block;
            width: 95px;
            font-weight: bold;
            color: #1e3d59;
            background-color: #ebf4ff;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 13px;
            margin-right: 8px;
            vertical-align: top;
        }
        
        /* บังคับข้อความเนื้อหาในมือถือให้อยู่ในบรรทัดขนานกับป้าย */
        .m-content {
            display: inline-block;
            width: calc(100% - 110px);
            vertical-align: top;
            font-size: 14px;
        }
    }
    
    /* สไตล์ปุ่มกดทั่วไป */
    .stButton > button {
        border-radius: 6px !important;
        font-size: 13px !important;
    }
    label, p {
        color: #2d3748 !important;
    }
    </style>
    
    <div style='background: linear-gradient(135deg, #1e3d59, #17b890); padding:20px; border-radius:12px; margin-bottom:25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);'>
        <h2 style='color:#ffffff; text-align:center; margin:0; font-size:25px; font-weight:700;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# 🔑 เชื่อมต่อกับคลาวด์ Supabase ผ่าน Secrets
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("🚨 ไม่สามารถดึงรหัสเชื่อมต่อฐานข้อมูลออนไลน์ได้ กรุณาตรวจสอบในระบบ Secrets")
    st.stop()

# รายชื่อขั้นตอนทั้งหมด
step_labels = [
    "1. รับหนังสือจากต้นสังกัด",
    "2. กรอกประวัติ พิมพ์มือ 2 ชุด",
    "3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง",
    "4. ไปส่ง พฐ. ตรวจที่ ภ.จว.",
    "5. ถ่ายเอกสารผลตรวจไว้ในสำเนา",
    "6. ทำหนังสือส่งผลกลับต้นสังกัด",
    "7. ต้นสังกัดเซ็นรับตัวจริงเรียบร้อย"
]

if "db_dict" not in st.session_state: st.session_state.db_dict = {}
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "form_key_index" not in st.session_state: st.session_state.form_key_index = 0
if "filter_step_id" not in st.session_state: st.session_state.filter_step_id = None  

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
                    "name": row.get("name", ""), "dept": row.get("dept", ""),
                    "status": row.get("status", "⚪ ยังไม่ได้เริ่ม"), "note": row.get("note", ""),
                    "steps": [
                        str(row.get("s1", "False")).strip() == "True", str(row.get("s2", "False")).strip() == "True",
                        str(row.get("s3", "False")).strip() == "True", str(row.get("s4", "False")).strip() == "True",
                        str(row.get("s5", "False")).strip() == "True", str(row.get("s6", "False")).strip() == "True",
                        str(row.get("s7", "False")).strip() == "True"
                    ]
                }
        st.session_state.db_dict = new_db
    except Exception as e:
        st.warning(f"⚠️ ดึงข้อมูลออนไลน์ขัดข้องชั่วคราว: {e}")

st.session_state["prevent_reloading"] = False

# 🗑️ ยืนยันการลบข้อมูล
@st.dialog("⚠️ ยืนยันการลบข้อมูลถาวร")
def confirm_delete_dialog(doc_id, name):
    st.write(f"คุณแน่ใจหรือไม่ว่าต้องการลบข้อมูลของ **{name}** (เลขที่หนังสือ: {doc_id})?")
    st.error("🚨 ระบบจะลบข้อมูลนี้ออกจากฐานข้อมูลออนไลน์ถาวร!")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚨 ยืนยันลบข้อมูล", type="primary", use_container_width=True):
            try:
                supabase.table("cases").delete().eq("doc", doc_id).execute()
                if doc_id in st.session_state.db_dict: del st.session_state.db_dict[doc_id]
                st.session_state["prevent_reloading"] = True; st.rerun()
            except Exception as e: st.error(f"เกิดข้อผิดพลาด: {e}")
    with c2:
        if st.button("❌ ยกเลิก", use_container_width=True): st.rerun()

# เซ็ตค่าเริ่มต้นฟอร์มข้อมูล
default_doc, default_name, default_dept, default_note = "", "", "", ""
loaded_steps = [False] * 7
default_title_index = 0

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    full_name_str = item["name"]
    default_dept = item["dept"]
    raw_note = item["note"]
    default_note = raw_note.split(" [รับเรื่อง:")[0].strip() if " [รับเรื่อง:" in raw_note else raw_note
    loaded_steps = item["steps"]
    
    if full_name_str.startswith("นาย"): default_title_index = 0; default_name = full_name_str.replace("นาย", "", 1)
    elif full_name_str.startswith("นางสาว"): default_title_index = 1; default_name = full_name_str.replace("นางสาว", "", 1)
    elif full_name_str.startswith("นาง"): default_title_index = 2; default_name = full_name_str.replace("นาง", "", 1)
    else: default_name = full_name_str

def on_step_change(index):
    w_key = f"step_idx_{index}_{st.session_state.form_key_index}"
    if st.session_state.get(w_key, False):
        for i in range(index + 1): st.session_state[f"step_idx_{i}_{st.session_state.form_key_index}"] = True
    else:
        for i in range(index, 7): st.session_state[f"step_idx_{i}_{st.session_state.form_key_index}"] = False

# คำนวณเคสตามแต่ละขั้นตอน
step_counts = [0] * 7  
for k, v in st.session_state.db_dict.items():
    v_status = v["status"]
    for idx, label in enumerate(step_labels):
        if label.split(".")[1].strip() in v_status or label in v_status:
            step_counts[idx] += 1; break

# 📊 ด้านบนสุด: แดชบอร์ดสรุปขั้นตอนงานปัจจุบัน
st.write("**📊 แดชบอร์ดสรุปขั้นตอนงานปัจจุบัน (คลิกเพื่อกรองรายชื่อ)**")
dash_cols = st.columns(7)
card_backgrounds = [
    "linear-gradient(135deg, #4a69bd, #1e3d59)", "linear-gradient(135deg, #4a69bd, #1e3d59)",
    "linear-gradient(135deg, #1e3d59, #17b890)", "linear-gradient(135deg, #1e3d59, #17b890)",
    "linear-gradient(135deg, #2ecc71, #27ae60)", "linear-gradient(135deg, #9b59b6, #8e44ad)",
    "linear-gradient(135deg, #e74c3c, #c0392b)" 
]

for idx in range(7):
    with dash_cols[idx]:
        is_active = st.session_state.filter_step_id == idx
        border_style = "border: 3px solid #ffcc00; box-shadow: 0 0 15px rgba(255, 204, 0, 0.5);" if is_active else ""
        st.markdown(f"""
            <div class="step-card" style="background: {card_backgrounds[idx]}; {border_style}">
                <div class="step-card-inner">
                    <div class="step-card-value">{step_counts[idx]}</div>
                    <div class="step-card-title">{step_labels[idx]}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        btn_txt = "📌 ดูกลุ่มนี้" if is_active else "🔎 คลิกกรอง"
        if st.button(btn_txt, key=f"btn_filter_step_{idx}", use_container_width=True, type="secondary" if not is_active else "primary"):
            st.session_state.filter_step_id = idx
            st.session_state["prevent_reloading"] = True; st.rerun()

st.write("---")

col1, col2 = st.columns([1.1, 1.9])

# ==================== ฝั่งซ้าย: ฟอร์มบันทึกข้อมูล ====================
with col1:
    st.markdown("<h4 style='font-weight:700; color:#1e3d59;'>📝 ฟอร์มบันทึกข้อมูล</h4>", unsafe_allow_html=True)
    with st.container(border=True):
        if st.session_state.edit_id: st.warning(f"กำลังแก้ไขเลขที่หนังสือ: {st.session_state.edit_id}")
        
        doc_num = st.text_input("เลขที่หนังสือรับ:", value=default_doc, key=f"doc_inp_{st.session_state.form_key_index}", disabled=(st.session_state.edit_id is not None))
        title_prefix = st.radio("คำนำหน้านาม:", ["นาย", "นางสาว", "นาง"], index=default_title_index, horizontal=True, key=f"title_inp_{st.session_state.form_key_index}")
        name_input = st.text_input("ชื่อ-สกุล ผู้ขอตรวจประวัติ:", value=default_name, key=f"name_inp_{st.session_state.form_key_index}")
        dept = st.text_input("หน่วยงานต้นสังกัด:", value=default_dept, key=f"dept_inp_{st.session_state.form_key_index}")
        note = st.text_area("หมายเหตุเพิ่มเติม:", value=default_note, height=70, key=f"note_inp_{st.session_state.form_key_index}")
        
        st.write("**ขั้นตอนที่ดำเนินการเสร็จสิ้น:**")
        for idx, label in enumerate(step_labels):
            st.checkbox(label, value=loaded_steps[idx], key=f"step_idx_{idx}_{st.session_state.form_key_index}", on_change=on_step_change, args=(idx,))

        checks = [st.session_state.get(f"step_idx_{i}_{st.session_state.form_key_index}", False) for i in range(7)]
        status_text = "⚪ ยังไม่ได้เริ่ม"
        if checks[6]: status_text = f"🟢 {step_labels[6]}"
        else:
            for idx in range(6, -1, -1):
                if checks[idx]: status_text = f"🟡 {step_labels[idx]}"; break

        btn_label = "💾 อัปเดตข้อมูลเดิม" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงคลาวด์"
        
        b_col1, b_col2 = st.columns([2, 1])
        with b_col1:
            if st.button(btn_label, type="primary", use_container_width=True):
                if doc_num and name_input:
                    full_name = f"{title_prefix}{name_input.strip()}"
                    today_str = datetime.today().strftime('%Y-%m-%d')
                    start_date = today_str
                    if st.session_state.edit_id:
                        old_item = st.session_state.db_dict.get(st.session_state.edit_id, {})
                        if "[รับเรื่อง:" in old_item.get("note", ""):
                            start_date = old_item["note"].split("[รับเรื่อง:")[1].split("]")[0].strip()
                    end_date = today_str if checks[6] else "-"
                    
                    final_note = f"{note.strip()} [รับเรื่อง: {start_date}] [สำเร็จ: {end_date}]"
                    case_data = {
                        "doc": str(doc_num).strip(), "name": full_name, "dept": dept, "status": status_text, "note": final_note,
                        "s1": str(checks[0]), "s2": str(checks[1]), "s3": str(checks[2]), "s4": str(checks[3]), 
                        "s5": str(checks[4]), "s6": str(checks[5]), "s7": str(checks[6])
                    }
                    try:
                        if st.session_state.edit_id: supabase.table("cases").update(case_data).eq("doc", st.session_state.edit_id).execute()
                        else: supabase.table("cases").insert(case_data).execute()
                        
                        st.session_state.db_dict[str(doc_num)] = {"name": full_name, "dept": dept, "status": status_text, "note": final_note, "steps": checks}
                        st.session_state.edit_id = None; st.session_state["prevent_reloading"] = False
                        st.session_state.form_key_index += 1; st.rerun()
                    except Exception as e: st.error(f"ขัดข้อง: {e}")
                else: st.error("กรุณากรอกเลขหนังสือและชื่อผู้ขอตรวจ")
        with b_col2:
            if st.session_state.edit_id and st.button("❌ ยกเลิก", use_container_width=True):
                st.session_state.edit_id = None; st.session_state["prevent_reloading"] = True
                st.session_state.form_key_index += 1; st.rerun()

# ==================== ฝั่งขวา: ตารางรายชื่อสถานะ (แกไขแบบ Responsive สมบูรณ์แบบ) ====================
with col2:
    st.markdown("<h4 style='font-weight:700; color:#1e3d59;'>📋 ตารางตรวจสอบสถานะข้อมูล</h4>", unsafe_allow_html=True)
    search_query = st.text_input("🔍 ค้นหาด้วย เลขหนังสือ หรือ ชื่อ-สกุล:", placeholder="พิมพ์คำค้นหาที่นี่...").strip()

    if st.session_state.filter_step_id is not None:
        st.info(f"🎯 กำลังแสดงขั้นตอน: {step_labels[st.session_state.filter_step_id]}")
        if st.button("❌ ล้างตัวกรองทั้งหมด", type="secondary"):
            st.session_state.filter_step_id = None; st.session_state["prevent_reloading"] = True; st.rerun()

    if st.session_state.db_dict:
        # เปิดหัวโครงตารางหลัก
        table_html = """
        <table class="modern-table">
            <thead>
                <tr>
                    <th style="width: 15%;">เลขหนังสือ</th>
                    <th style="width: 20%;">ชื่อ-สกุล</th>
                    <th style="width: 18%;">หน่วยงานต้นสังกัด</th>
                    <th style="width: 22%;">สถานะปัจจุบัน</th>
                    <th style="width: 25%;">หมายเหตุและประวัติติดตาม</th>
                </tr>
            </thead>
            <tbody>
        """
        
        has_rows = False
        # วนลูปสร้างข้อมูลภายในตารางทีละแถว
        for k, v in st.session_state.db_dict.items():
            if st.session_state.filter_step_id is not None:
                sel_lbl = step_labels[st.session_state.filter_step_id]
                if sel_lbl.split(".")[1].strip() not in v["status"] and sel_lbl not in v["status"]: continue

            if search_query and (search_query not in str(k) and search_query not in str(v["name"]) and search_query not in str(v["dept"]) and search_query not in str(v["note"])): 
                continue
            
            has_rows = True
            dept_val = v['dept'] if v['dept'] else "-"
            note_val = v['note'] if v['note'] else "-"
            
            table_html += f"""
                <tr>
                    <td><span class="m-title">เลขหนังสือ</span><span class="m-content"><b>{k}</b></span></td>
                    <td><span class="m-title">ชื่อ-สกุล</span><span class="m-content">{v['name']}</span></td>
                    <td><span class="m-title">หน่วยงาน</span><span class="m-content">{dept_val}</span></td>
                    <td><span class="m-title">สถานะ</span><span class="m-content">{v['status']}</span></td>
                    <td><span class="m-title">หมายเหตุ</span><span class="m-content">{note_val}</span></td>
                </tr>
            """
            
        table_html += "</tbody></table>"
        
        if has_rows:
            # 1. พ่นตารางหลักที่จัดระเบียบโครงสร้างเรียบร้อยแล้วออกหน้าจอ
            st.markdown(table_html, unsafe_allow_html=True)
            
            # 2. พ่นปุ่ม จัดการ (แก้ไข/ลบ) แยกออกมาต่างหากด้านล่าง เพื่อไม่ให้ไปเบียดพื้นที่ในตารางตอมและมือถือ
            st.write("<div style='margin-top: 8px;'><b>🛠️ เมนูจัดการข้อมูลรายบุคคลตามตารางด้านบน:</b></div>", unsafe_allow_html=True)
            
            for k, v in st.session_state.db_dict.items():
                if st.session_state.filter_step_id is not None:
                    sel_lbl = step_labels[st.session_state.filter_step_id]
                    if sel_lbl.split(".")[1].strip() not in v["status"] and sel_lbl not in v["status"]: continue
                if search_query and (search_query not in str(k) and search_query not in str(v["name"]) and search_query not in str(v["dept"]) and search_query not in str(v["note"])): 
                    continue
                
                # แสดงแถบแถวปุ่มแบบกระชับสวยงาม เข้าใจง่าย
                btn_cols = st.columns([3, 1, 1])
                with btn_cols[0]:
                    st.markdown(f"🔹 หนังสือเลขที่: `{k}` | **{v['name']}**")
                with btn_cols[1]:
                    if st.button("✏️ แก้ไขข้อมูล", key=f"edit_btn_{k}", use_container_width=True):
                        st.session_state.edit_id = k
                        st.session_state.form_key_index += 1; st.rerun()
                with btn_cols[2]:
                    if st.button("🗑️ ลบถาวร", key=f"del_btn_{k}", use_container_width=True):
                        confirm_delete_dialog(k, v["name"])
                st.markdown("<div style='border-bottom: 1px dashed #edf2f7; margin-bottom: 6px;'></div>", unsafe_allow_html=True)
        else:
            st.info("ไม่พบข้อมูลที่ตรงกับเงื่อนไขการค้นหา")

        st.write("")
        if st.button("🔄 อัปเดตรีเฟรชฐานข้อมูลล่าสุด", use_container_width=True):
            st.session_state.clear(); st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบฐานข้อมูล")
