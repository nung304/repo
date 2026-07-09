import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

# 🎨 🛠️ อัปเดตพื้นหลังเป็นภาพห้องทำงานโลก Cyber แท้ ๆ สไตล์สืบสวนดิจิทัล
st.markdown("""
    <style>
    /* 🌆 เปลี่ยนเป็นภาพห้องทำงาน Workstation ในโลก Cyber ล้ำ ๆ โทนเข้ม */
    .stApp {
        background-image: linear-gradient(rgba(10, 20, 30, 0.88), rgba(10, 20, 30, 0.93)), 
                          url("https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=2000");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* 🖥️ กล่องเนื้อหาหลักโปร่งแสง มิติมืดลึก ช่วยดันตัวหนังสือให้ลอยเด่น */
    [data-testid="stVerticalBlock"] > div {
        background-color: rgba(6, 15, 25, 0.5);
        padding: 10px;
        border-radius: 14px;
        border: 1px solid rgba(0, 188, 212, 0.08);
    }
    
    /* ตั้งค่าตารางให้รองรับมือถือลื่นไหล */
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
    
    /* 🌌 สไตล์กล่องแดชบอร์ดขั้นตอน - ใหญ่ หนา และมีมิติเงาตัดกับพื้นหลังห้องทำงาน */
    .step-card {
        color: white !important;
        border-radius: 10px;
        margin-bottom: 6px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        text-align: center;
        border: 1px solid rgba(255,255,255,0.18);
    }
    .step-card-inner {
        padding: 15px 8px;
    }
    .step-card-value {
        font-size: 42px; /* ขนาดใหญ่พิเศษสะใจ */
        font-weight: 900; /* หนาเข้มระดับสูงสุด */
        margin: 0;
        line-height: 1;
        color: #ffffff !important;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.8); /* ตีเงาเข้มหนาเพื่อสู้กับภาพพื้นหลัง */
    }
    .step-card-title {
        font-size: 16px; /* อักษรอธิบายขั้นตอนคมชัดเต็มตา */
        font-weight: 700;
        color: #ffffff !important;
        margin-top: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 44px;
        line-height: 22px;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.7);
    }
    
    /* ล็อกสีฟอนต์คำอธิบายทุกจุดบนหน้าเว็บให้เป็นสีขาวสว่าง ชัดเจน */
    label, p, .stMarkdown {
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.6);
    }
    
    /* ตัวป้ายกำกับสำหรับแถวข้อมูลบนหน้าจอมือถือ */
    .mobile-label {
        display: none;
        font-weight: bold;
        color: #00bcd4;
        min-width: 90px;
    }
    
    @media (max-width: 768px) {
        .desktop-header {
            display: none !important;
        }
        .mobile-label {
            display: inline-block !important;
            margin-right: 5px;
        }
        .row-divider {
            border-bottom: 2px solid #1e3d59 !important;
            margin-top: 12px !important;
            margin-bottom: 12px !important;
        }
    }
    </style>
    
    <div style='background: linear-gradient(135deg, #051329, #0a1f3d); padding:20px; border-radius:12px; margin-bottom:25px; box-shadow: 0 6px 25px rgba(0,0,0,0.5); border: 1px solid rgba(0, 188, 212, 0.4);'>
        <h2 style='color:#00bcd4; text-align:center; margin:0; font-size:26px; font-weight:700; text-shadow: 0 0 12px rgba(0,188,212,0.6); letter-spacing: 1px;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
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
    "2. กรอกประวัติ พิมพ์มือ 2 ชุด",
    "3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง",
    "4. ไปส่ง พฐ. ตรวจที่ ภ.จว.",
    "5. ถ่ายเอกสารผลตรวจไว้ในสำเนา",
    "6. ทำหนังสือส่งผลกลับต้นสังกัด",
    "7. ต้นสังกัดเซ็นรับตัวจริงเรียบร้อย"
]

if "db_dict" not in st.session_state:
    st.session_state.db_dict = {}
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "form_key_index" not in st.session_state:
    st.session_state.form_key_index = 0
if "filter_step_id" not in st.session_state:
    st.session_state.filter_step_id = None  

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

# คำนวณจำนวนเคสที่อยู่ตามขั้นตอนต่างๆ (1-7)
step_counts = [0] * 7  
for k, v in st.session_state.db_dict.items():
    v_status = v["status"]
    for idx, label in enumerate(step_labels):
        if label.split(".")[1].strip() in v_status or label in v_status:
            step_counts[idx] += 1
            break

# 📊 ด้านบนสุด: แดชบอร์ดสรุปแบบไซเบอร์โมเดิร์น
st.write("**📊 แดชบอร์ดสรุปขั้นตอนงานปัจจุบัน (คลิกเลือกขั้นตอนที่ต้องการตรวจสอบรายชื่อด้านล่าง)**")
dash_cols = st.columns(7)
card_backgrounds = [
    "linear-gradient(135deg, #0b141a, #1f3c4d)", 
    "linear-gradient(135deg, #0b141a, #1f3c4d)",
    "linear-gradient(135deg, #0f2b46, #1d4e79)",
    "linear-gradient(135deg, #0f2b46, #1d4e79)",
    "linear-gradient(135deg, #103419, #256133)",
    "linear-gradient(135deg, #441151, #7b2cbf)",
    "linear-gradient(135deg, #0056b3, #0088ff)" 
]

for idx in range(7):
    with dash_cols[idx]:
        is_active = st.session_state.filter_step_id == idx
        # กล่องที่โดนเลือกกรองข้อมูลอยู่ จะเปิดไฟนีออนสีทองสว่างวาบทันทีล้อมรอบกล่อง
        border_style = "border: 2.5px solid #FFD700; box-shadow: 0 0 22px rgba(255, 215, 0, 0.75);" if is_active else ""
        
        st.markdown(f"""
            <div class="step-card" style="background: {card_backgrounds[idx]}; {border_style}">
                <div class="step-card-inner">
                    <div class="step-card-value">{step_counts[idx]}</div>
                    <div class="step-card-title">{step_labels[idx]}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 🔍 ปุ่มเปิดกลุ่มดูข้อมูลในตาราง
        btn_txt = "📌 ดูกลุ่มนี้อยู่" if is_active else "🔎 คลิกดูข้อมูล"
        if st.button(btn_txt, key=f"btn_filter_step_{idx}", use_container_width=True, type="secondary" if not is_active else "primary"):
            st.session_state.filter_step_id = idx
            st.session_state["prevent_reloading"] = True
            st.rerun()

st.write("---")

col1, col2 = st.columns([1.25, 1.75])

# ==================== ฝั่งซ้าย: ฟอร์มบันทึกข้อมูล ====================
with col1:
    st.markdown("<h3 style='color:#00bcd4; text-shadow: 0 0 8px rgba(0,188,212,0.4);'>📝 บันทึก / แก้ไขข้อมูล</h3>", unsafe_allow_html=True)
    if st.session_state.edit_id:
        st.warning(f"⚠️ กำลังแก้ไขเลขที่หนังสือ: {st.session_state.edit_id}")
    else:
        st.info("➕ เพิ่มข้อมูลรายใหม่ (ระบบลงบันทึกรับเรื่องวันนี้อัตโนมัติ)")

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
                
                if st.session_state.edit_id:
                    old_item = st.session_state.db_dict.get(st.session_state.edit_id, {})
                    old_note_str = old_item.get("note", "")
                    
                    if "[รับเรื่อง:" in old_note_str:
                        start_date = old_note_str.split("[รับเรื่อง:")[1].split("]")[0].strip()
                    else:
                        start_date = today_str
                        
                    if checks[6]:
                        if "[สำเร็จ:" in old_note_str:
                            end_date = old_note_str.split("[สำเร็จ:")[1].split("]")[0].strip()
                            if end_date == "-":
                                end_date = today_str
                        else:
                            end_date = today_str
                    else:
                        end_date = "-"
                else:
                    start_date = today_str
                    end_date = today_str if checks[6] else "-"
                
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

# ==================== 📋 ฝั่งขวา: กล่องค้นหาและตารางรายชื่อข้อมูลภาพรวม ====================
with col2:
    search_query = st.text_input("พิมพ์เลขหนังสือ หรือ ชื่อบุคคลที่ต้องการค้นหาในระบบ:", placeholder="คีย์คำค้นหาที่นี่...").strip()

    # แจ้งเตือนสว่างชัดเมื่อมีการคลิกเลือกฟิลเตอร์ขั้นตอนแดชบอร์ด
    if st.session_state.filter_step_id is not None:
        active_label = step_labels[st.session_state.filter_step_id]
        st.warning(f"🎯 กำลังกรองแสดงเฉพาะรายชื่อในขั้นตอน: **{active_label}**")
        if st.button("❌ ล้างตัวกรอง (คลิกเพื่อแสดงข้อมูลทั้งหมดล่าสุด)", use_container_width=True, type="primary"):
            st.session_state.filter_step_id = None
            st.session_state["prevent_reloading"] = True
            st.rerun()

    st.markdown("<h4 style='color:#00bcd4; text-shadow: 0 0 8px rgba(0,188,212,0.4);'>📋 ตารางตรวจสอบสถานะข้อมูล</h4>", unsafe_allow_html=True)
    
    if st.session_state.db_dict:
        st.markdown('<div class="desktop-header">', unsafe_allow_html=True)
        header_cols = st.columns([1, 1.2, 1, 1.8, 1.4, 0.7, 0.7])
        with header_cols[0]: st.markdown("**เลขหนังสือ**")
        with header_cols[1]: st.markdown("**ชื่อ-สกุล**")
        with header_cols[2]: st.markdown("**ต้นสังกัด**")
        with header_cols[3]: st.markdown("**สถานะปัจจุบัน**")
        with header_cols[4]: st.markdown("**หมายเหตุและประวัติติดตาม**")
        with header_cols[5]: st.markdown("**แก้ไข**")
        with header_cols[6]: st.markdown("**ลบ**")
        st.write("<div style='border-bottom: 2px solid #00bcd4; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        for k, v in st.session_state.db_dict.items():
            # 🔍 ตัวกรองตามขั้นตอนที่คลิกเลือกจากแดชบอร์ดไซเบอร์
            if st.session_state.filter_step_id is not None:
                selected_label = step_labels[st.session_state.filter_step_id]
                if selected_label.split(".")[1].strip() not in v["status"] and selected_label not in v["status"]:
                    continue

            # ตรวจสอบตัวค้นหาพิมพ์ข้อความทั่วไป
            if search_query and (search_query not in str(k) and search_query not in str(v["name"]) and search_query not in str(v["dept"]) and search_query not in str(v["note"])): 
                continue
                
            row_cols = st.columns([1, 1.2, 1, 1.8, 1.4, 0.7, 0.7])
            
            with row_cols[0]: st.markdown(f"<span class='mobile-label'>เลขหนังสือ:</span>{k}", unsafe_allow_html=True)
            with row_cols[1]: st.markdown(f"<span class='mobile-label'>ชื่อ-สกุล:</span>{v['name']}", unsafe_allow_html=True)
            with row_cols[2]: st.markdown(f"<span class='mobile-label'>ต้นสังกัด:</span>{v['dept']}", unsafe_allow_html=True)
            with row_cols[3]: st.markdown(f"<span class='mobile-label'>สถานะปัจจุบัน:</span>{v['status']}", unsafe_allow_html=True)
            with row_cols[4]: st.markdown(f"<span class='mobile-label'>หมายเหตุ:</span>{v['note'] if v['note'] else '-'}", unsafe_allow_html=True)
            
            with row_cols[5]:
                if st.button("✏️ แก้ไข", key=f"edit_btn_{k}", use_container_width=True):
                    st.session_state.edit_id = k
                    st.session_state.form_key_index += 1; st.rerun()
            with row_cols[6]:
                if st.button("🗑️ ลบข้อมูล", key=f"del_btn_{k}", use_container_width=True):
                    confirm_delete_dialog(k, v["name"])
                    
            st.markdown("<div class='row-divider' style='border-bottom: 1px solid rgba(255,255,255,0.12); margin-top: 4px; margin-bottom: 4px;'></div>", unsafe_allow_html=True)

        st.write("---")
        if st.button("🔄 ดึงข้อมูลเวอร์ชันล่าสุดจากฐานข้อมูลออนไลน์", use_container_width=True):
            st.session_state.clear(); st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังเชื่อมต่อฐานข้อมูล...")
