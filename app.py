import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

# ปรับแต่ง CSS ให้ตารางอ่านง่ายและสวยงามยิ่งขึ้นบนมือถือ
st.markdown("""
    <style>
    [data-testid="stDataFrame"] {
        width: 100%;
    }
    .reportview-container .main .block-container{
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
    <div style='background-color:#800000;padding:15px;border-radius:10px;margin-bottom:20px'>
        <h2 style='color:white;text-align:center;margin:0;font-size:22px;'>ระบบฐานข้อมูลและติดตามขั้นตอนการตรวจประวัติ (สภ. ส่ง พฐ.)</h2>
    </div>
""", unsafe_allow_html=True)

# 🔗 1. ลิงก์ยิงฟอร์มหลังบ้าน
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSckbSH3a337W8yknYgAsAw7esyGyEv55lgK8g6QWCv_q2HtFg/formResponse"

# 🔑 2. แผนผังรหัสกล่องข้อความ Google Form
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

# รายชื่อขั้นตอนทั้งหมด (ชื่อเต็ม)
step_labels = [
    "1. รับหนังสือจากต้นสังกัด",
    "2. กรอกประวัติ พิมพ์ลายนิ้วมือกลิ้งหมึก 2 ชุด",
    "3. ทำหนังสือส่งตรวจ พฐ. ลงลายเซ็นรอง",
    "4. ไปส่ง พฐ. ตรวจที่ ภ.จว. แล้วนำกลับมา",
    "5. ถ่ายเอกสารผลตรวจ 1 ชุด ไว้ในสำเนาคู่ฉับ",
    "6. ทำหนังสือส่ง รายงานผลกลับต้นสังกัด (2 ชุด)",
    "7. ต้นสังกัดเซ็นรับตัวจริงและคู่สำเนา เรียบร้อย"
]

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

if "prevent_reloading" not in st.session_state:
    st.session_state.prevent_reloading = False

# ดึงข้อมูลจาก Sheets มาอัปเดตลงตาราง
if read_url and not st.session_state.prevent_reloading:
    try:
        df = pd.read_csv(read_url)
        if not df.empty:
            # ล้างข้อมูลเก่าก่อนโหลดใหม่เพื่อป้องกันการซ้อนทับที่ทำให้เกิด Error
            st.session_state.db_dict = {}
            for _, row in df.iterrows():
                if len(row) >= 6:
                    k = str(row.iloc[1]).strip()
                    current_status = str(row.iloc[4]) if pd.notna(row.iloc[4]) else "⚪ ยังไม่ได้เริ่ม"
                    
                    if "❌ ลบข้อมูลแล้ว" in current_status:
                        continue
                        
                    if k and k != "nan" and k != "":
                        st.session_state.db_dict[k] = {
                            "name": str(row.iloc[2]) if pd.notna(row.iloc[2]) else "",
                            "dept": str(row.iloc[3]) if pd.notna(row.iloc[3]) else "",
                            "status": current_status,
                            "note": str(row.iloc[5]) if pd.notna(row.iloc[5]) else "",
                            "steps": [bool(row.iloc[i]) if i < len(row) and pd.notna(row.iloc[i]) else False for i in range(6, 13)]
                        }
    except:
        pass

st.session_state.prevent_reloading = False

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "selected_dashboard_step" not in st.session_state:
    st.session_state.selected_dashboard_step = None

# ตั้งค่าเริ่มต้นของฟอร์มกรอกข้อมูล
default_doc, default_name, default_dept, default_note = "", "", "", ""
loaded_steps = [False] * 7

if st.session_state.edit_id and st.session_state.edit_id in st.session_state.db_dict:
    item = st.session_state.db_dict[st.session_state.edit_id]
    default_doc = st.session_state.edit_id
    default_name = item["name"]
    default_dept = item["dept"]
    default_note = item["note"]
    loaded_steps = item["steps"] if len(item["steps"]) == 7 else [False]*7

# กลไกเช็คบ็อกซ์เดินหน้าอัตโนมัติแบบเสถียร
def on_step_change(index):
    # ดึงค่าปัจจุบันของการติ๊กเช็คบ็อกซ์ในปัจจุบัน
    current_val = st.session_state[f"step_widget_{index}"]
    if current_val:
        for i in range(index + 1):
            st.session_state[f"step_widget_{i}"] = True
    else:
        for i in range(index, 7):
            st.session_state[f"step_widget_{i}"] = False

# จัดโครงสร้างแบบยืดหยุ่น (Responsive) บนมือถือจะเรียงลงมาอย่างสวยงาม
col1, col2 = st.columns([1, 1.5])

# ==================== ฝั่งที่ 1: ฟอร์มกรอกและแก้ไขข้อมูล ====================
with col1:
    st.subheader("📝 บันทึก / แก้ไขข้อมูล")
    
    if st.session_state.edit_id:
        st.warning(f"⚠️ กำลังแก้ไขเลขที่หนังสือ: {st.session_state.edit_id}")
    else:
        st.info("➕ กำลังเพิ่มข้อมูลรายใหม่")

    doc_num = st.text_input("เลขที่หนังสือรับ:", value=default_doc, key="doc_num_input")
    name = st.text_input("ชื่อ-สกุล ผู้ขอตรวจสอบประวัติ:", value=default_name, key="name_input")
    dept = st.text_input("หน่วยงานต้นสังกัด (ที่ส่งมา):", value=default_dept, key="dept_input")
    note = st.text_area("หมายเหตุ:", value=default_note, height=70, key="note_input")
    
    st.write("**เลือกขั้นตอนที่ทำเสร็จแล้ว:**")
    
    for idx, label in enumerate(step_labels):
        st.checkbox(
            label,
            value=loaded_steps[idx],
            key=f"step_widget_{idx}",
            on_change=on_step_change,
            args=(idx,)
        )

    checks = [st.session_state[f"step_widget_{i}"] for i in range(7)]
    
    status_text = "⚪ ยังไม่ได้เริ่ม"
    if checks[6]:
        status_text = f"🟢 {step_labels[6]}"
    else:
        for idx in range(6, -1, -1):
            if checks[idx]:
                status_text = f"🟡 {step_labels[idx]}"
                break

    btn_label = "💾 อัปเดตและบันทึกข้อมูล" if st.session_state.edit_id else "💾 บันทึกข้อมูลลงระบบ"
    
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
                    ENTRY_MAP["s1"]: str(checks[0]), ENTRY_MAP["s2"]: str(checks[1]), ENTRY_MAP["s3"]: str(checks[2]),
                    ENTRY_MAP["s4"]: str(checks[3]), ENTRY_MAP["s5"]: str(checks[4]), ENTRY_MAP["s6"]: str(checks[5]), ENTRY_MAP["s7"]: str(checks[6])
                }
                try:
                    response = requests.post(FORM_URL, data=form_data)
                    st.session_state.db_dict[str(doc_num)] = {"name": name, "dept": dept, "status": status_text, "note": note, "steps": checks}
                    st.session_state.edit_id = None
                    st.session_state.prevent_reloading = True
                    st.success("🎉 บันทึกข้อมูลสำเร็จแล้วครับพี่!")
                    st.balloons()
                    st.rerun()
                except:
                    st.error("❌ เกิดข้อผิดพลาดทางเครือข่าย")
            else:
                st.error("กรุณากรอกข้อมูลเลขที่หนังสือและชื่อผู้ขอตรวจให้ครบถ้วน")
                
    with btn_col2:
        if st.session_state.edit_id:
            if st.button("❌ ยกเลิก", use_container_width=True):
                st.session_state.edit_id = None
                st.session_state.prevent_reloading = True
                st.rerun()

# ==================== ฝั่งที่ 2: Dashboard และ ตารางตรวจสอบสถานะ ====================
with col2:
    st.subheader("📊 ระบบติดตามสถานะภาพรวม")
    
    counts = [0] * 8  
    for k, v in st.session_state.db_dict.items():
        v_status = v["status"]
        if "❌ ลบข้อมูลแล้ว" in v_status:
            continue
        if "ยังไม่ได้เริ่ม" in v_status:
            counts[7] += 1
        else:
            for idx, label in enumerate(step_labels):
                if label in v_status:
                    counts[idx] += 1
                    break

    st.write("**📌 กดปุ่มเพื่อกรองข้อมูลตามขั้นตอน:**")
    
    # แบ่งปุ่มกดกระดานแบบกะทัดรัด (รองรับหน้าจอมือถือไม่ให้เบียดกัน)
    d_c1, d_c2 = st.columns(2)
    with d_c1:
        if st.button(f"📁 ขั้นตอนที่ 1 ({counts[0]})", key="d1", use_container_width=True): st.session_state.selected_dashboard_step = 0; st.rerun()
        if st.button(f"📝 ขั้นตอนที่ 2 ({counts[1]})", key="d2", use_container_width=True): st.session_state.selected_dashboard_step = 1; st.rerun()
        if st.button(f"✉️ ขั้นตอนที่ 3 ({counts[2]})", key="d3", use_container_width=True): st.session_state.selected_dashboard_step = 2; st.rerun()
        if st.button(f"🚔 ขั้นตอนที่ 4 ({counts[3]})", key="d4", use_container_width=True): st.session_state.selected_dashboard_step = 3; st.rerun()
    with d_c2:
        if st.button(f"🖨️ ขั้นตอนที่ 5 ({counts[4]})", key="d5", use_container_width=True): st.session_state.selected_dashboard_step = 4; st.rerun()
        if st.button(f"📤 ขั้นตอนที่ 6 ({counts[5]})", key="d6", use_container_width=True): st.session_state.selected_dashboard_step = 5; st.rerun()
        if st.button(f"🟢 เสร็จสิ้น ({counts[6]})", key="d7", use_container_width=True): st.session_state.selected_dashboard_step = 6; st.rerun()
        if st.button(f"⚪ ยังไม่เริ่ม ({counts[7]})", key="d8", use_container_width=True): st.session_state.selected_dashboard_step = 7; st.rerun()

    if st.session_state.selected_dashboard_step is not None:
        if st.button("❌ ล้างตัวกรองปุ่มสถานะ", use_container_width=True):
            st.session_state.selected_dashboard_step = None
            st.rerun()

    st.write("---")

    # 🛠️ ระบบจัดการข้อมูลสำหรับหน้าจอมือถือ (เลือกรายชื่อเพื่อ แก้ไข หรือ ลบ)
    if st.session_state.db_dict:
        st.write("**🛠️ จัดการข้อมูล (แก้ไข / ลบรายชื่อ)**")
        options_list = ["-- เลือกเลขที่หนังสือที่ต้องการจัดการ --"] + [f"{k} - {v['name']}" for k, v in st.session_state.db_dict.items()]
        selected_option = st.selectbox("เลือกรายการรายชื่อบุคคล:", options=options_list, index=0)
        
        if selected_option != "-- เลือกเลขที่หนังสือที่ต้องการจัดการ --":
            target_id = selected_option.split(" - ")[0]
            target_name = st.session_state.db_dict[target_id]["name"]
            
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                if st.button(f"✏️ ดึงข้อมูล {target_id} ไปแก้ไข", type="primary", use_container_width=True):
                    st.session_state.edit_id = target_id
                    st.rerun()
            with m_col2:
                if st.button(f"🗑️ ลบข้อมูล {target_id} ออกจากระบบ", use_container_width=True):
                    form_data = {
                        ENTRY_MAP["doc"]: target_id,
                        ENTRY_MAP["name"]: target_name,
                        ENTRY_MAP["dept"]: st.session_state.db_dict[target_id]["dept"],
                        ENTRY_MAP["status"]: "❌ ลบข้อมูลแล้ว",
                        ENTRY_MAP["note"]: st.session_state.db_dict[target_id]["note"],
                        ENTRY_MAP["s1"]: "False", ENTRY_MAP["s2"]: "False", ENTRY_MAP["s3"]: "False",
                        ENTRY_MAP["s4"]: "False", ENTRY_MAP["s5"]: "False", ENTRY_MAP["s6"]: "False", ENTRY_MAP["s7"]: "False"
                    }
                    try:
                        requests.post(FORM_URL, data=form_data, timeout=8)
                    except:
                        pass
                    if target_id in st.session_state.db_dict:
                        del st.session_state.db_dict[target_id]
                    st.session_state.prevent_reloading = True
                    st.toast(f"ลบเลขที่หนังสือ {target_id} เรียบร้อยแล้วครับ!")
                    st.rerun()

    st.write("---")
    
    # 🔍 ช่องค้นหาอัจฉริยะ
    search_query = st.text_input("🔍 พิมพ์ค้นหา (เลขหนังสือ หรือ ชื่อ):", placeholder="พิมพ์เพื่อค้นหาที่นี่...").strip()

    # 📱 ส่วนประมวลผลและแสดงผลตารางแท้ (Dataframe)
    if st.session_state.db_dict:
        all_records = []
        for k, v in st.session_state.db_dict.items():
            s_idx = 7 if "ยังไม่ได้เริ่ม" in v["status"] else next((i for i, x in enumerate(step_labels) if x in v["status"]), None)
            
            # ตัวกรองปุ่มสถานะ
            if st.session_state.selected_dashboard_step is not None and s_idx != st.session_state.selected_dashboard_step:
                continue
            # ตัวกรองช่องค้นหา
            if search_query and (search_query not in str(k) and search_query not in str(v["name"])):
                continue
                
            all_records.append({
                "เลขที่หนังสือรับ": k,
                "ชื่อ-สกุล ผู้ขอตรวจ": v["name"],
                "หน่วยงานต้นสังกัด": v["dept"],
                "สถานะปัจจุบัน": v["status"],
                "หมายเหตุ": v["note"]
            })
            
        if all_records:
            display_df = pd.DataFrame(all_records)
            st.write("**📋 ตารางตรวจสอบสถานะปัจจุบัน (ปัดหน้าจอ ซ้าย-ขวา เพื่อดูให้ครบได้ครับ):**")
            # คำสั่งสร้างตารางแท้ ล็อกมิติความสวยงาม ไม่กระจัดกระจายบนมือถือ
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "เลขที่หนังสือรับ": st.column_config.TextColumn("เลขหนังสือ", width="small"),
                    "ชื่อ-สกุล ผู้ขอตรวจ": st.column_config.TextColumn("ชื่อ-สกุล", width="medium"),
                    "หน่วยงานต้นสังกัด": st.column_config.TextColumn("ต้นสังกัด", width="small"),
                    "สถานะปัจจุบัน": st.column_config.TextColumn("สถานะปัจจุบัน", width="medium"),
                    "หมายเหตุ": st.column_config.TextColumn("หมายเหตุ", width="medium"),
                }
            )
        else:
            st.warning("🔍 ไม่พบข้อมูลที่ตรงกับเงื่อนไขครับ")

        st.write("---")
        if st.button("🔄 ดึงข้อมูลเวอร์ชันล่าสุดจาก Google Sheets", use_container_width=True):
            st.session_state.clear()
            st.rerun()
