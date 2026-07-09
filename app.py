import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="ระบบตรวจประวัติ สภ.", layout="wide")

# --- CSS จัดระเบียบหน้าจอ ---
st.markdown("""
    <style>
    .step-card { color: white; border-radius: 10px; padding: 15px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-bottom: 10px; }
    .modern-table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .modern-table th { background: #1e3d59; color: white; padding: 12px; text-align: left; }
    .modern-table td { padding: 12px; border-bottom: 1px solid #edf2f7; }
    .m-title { display: none; }
    @media screen and (max-width: 800px) {
        .modern-table thead { display: none; }
        .modern-table, .modern-table tr, .modern-table td { display: block; width: 100%; }
        .modern-table tr { margin-bottom: 10px; border: 1px solid #eee; border-radius: 8px; padding: 10px; }
        .m-title { display: inline-block; font-weight: bold; width: 100px; color: #1e3d59; }
    }
    </style>
""", unsafe_allow_html=True)

# --- เชื่อมต่อฐานข้อมูล ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception as e:
    st.error("เชื่อมต่อฐานข้อมูลไม่ได้")
    st.stop()

# --- ดึงข้อมูล (ย่อให้กระชับ) ---
if "db_dict" not in st.session_state:
    try:
        response = supabase.table("cases").select("*").execute()
        st.session_state.db_dict = {str(r['doc']): r for r in response.data}
    except:
        st.session_state.db_dict = {}

# --- หน้าจอหลัก ---
st.title("ระบบตรวจประวัติ สภ.")

# 1. แดชบอร์ด
dash_cols = st.columns(7)
# (ใส่โค้ดแดชบอร์ดสรุปสถิติเดิมของคุณตรงนี้)

# 2. แบ่งคอลัมน์ ฟอร์มซ้าย | ตารางขวา
left_col, right_col = st.columns([1, 2])

with left_col:
    st.subheader("📝 ฟอร์มข้อมูล")
    # (ใส่โค้ดฟอร์มรับค่าเดิมของคุณตรงนี้)

with right_col:
    st.subheader("📋 ตารางรายการ")
    search = st.text_input("🔍 ค้นหา...")
    
    # แสดงตารางแบบใหม่
    table_html = "<table class='modern-table'><thead><tr><th>เลขที่</th><th>ชื่อ</th><th>สถานะ</th><th>จัดการ</th></tr></thead><tbody>"
    for doc, val in st.session_state.db_dict.items():
        if search.lower() in str(val['name']).lower() or search.lower() in str(doc):
            table_html += f"""<tr>
                <td><span class='m-title'>เลขที่</span>{doc}</td>
                <td><span class='m-title'>ชื่อ</span>{val['name']}</td>
                <td><span class='m-title'>สถานะ</span>{val['status']}</td>
                <td><a href='?edit={doc}'>✏️ แก้ไข</a></td>
            </tr>"""
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    # รองรับการกดแก้ไข
    if "edit" in st.query_params:
        st.session_state.edit_id = st.query_params["edit"]
        st.rerun()
