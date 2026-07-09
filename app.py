# ==================== ฝั่งขวา: ตารางรายชื่อสถานะ (เวอร์ชันล็อกหัวข้อตรงกับข้อมูล) ====================
with col2:
    st.markdown("<h4 style='font-weight:700; color:#1e3d59;'>📋 ตารางตรวจสอบสถานะข้อมูล</h4>", unsafe_allow_html=True)
    search_query = st.text_input("🔍 ค้นหาด้วย เลขหนังสือ หรือ ชื่อ-สกุล:", placeholder="พิมพ์คำค้นหาที่นี่...").strip()

    if st.session_state.filter_step_id is not None:
        st.info(f"🎯 กำลังแสดงขั้นตอน: {step_labels[st.session_state.filter_step_id]}")
        if st.button("❌ ล้างตัวกรองทั้งหมด", type="secondary"):
            st.session_state.filter_step_id = None; st.session_state["prevent_reloading"] = True; st.rerun()

    if st.session_state.db_dict:
        # สร้างตารางเดียวที่ครอบทั้งข้อมูลและปุ่ม เพื่อให้หัวข้อตรงกันเสมอ
        table_html = """
        <table class="modern-table">
            <thead>
                <tr>
                    <th>เลขหนังสือ</th>
                    <th>ชื่อ-สกุล</th>
                    <th>หน่วยงาน</th>
                    <th>สถานะ</th>
                    <th>หมายเหตุ</th>
                    <th>จัดการ</th>
                </tr>
            </thead>
            <tbody>
        """
        
        has_rows = False
        for k, v in st.session_state.db_dict.items():
            if st.session_state.filter_step_id is not None:
                sel_lbl = step_labels[st.session_state.filter_step_id]
                if sel_lbl.split(".")[1].strip() not in v["status"] and sel_lbl not in v["status"]: continue

            if search_query and (search_query not in str(k) and search_query not in str(v["name"]) and search_query not in str(v["dept"]) and search_query not in str(v["note"])): 
                continue
            
            has_rows = True
            
            # ใช้ปุ่มจริงของ Streamlit ลำบากในตาราง HTML ผมจึงใช้ Link แบบปุ่มมาทดแทนเพื่อให้กดง่ายในทุกอุปกรณ์
            table_html += f"""
                <tr>
                    <td><span class="m-title">เลขหนังสือ</span><span class="m-content"><b>{k}</b></span></td>
                    <td><span class="m-title">ชื่อ-สกุล</span><span class="m-content">{v['name']}</span></td>
                    <td><span class="m-title">หน่วยงาน</span><span class="m-content">{v['dept'] if v['dept'] else "-"}</span></td>
                    <td><span class="m-title">สถานะ</span><span class="m-content">{v['status']}</span></td>
                    <td><span class="m-title">หมายเหตุ</span><span class="m-content">{v['note'] if v['note'] else "-"}</span></td>
                    <td>
                        <span class="m-title">เมนู</span>
                        <span class="m-content">
                            <a href="?edit={k}" style="text-decoration:none; padding:4px 8px; background:#edf2f7; border-radius:4px; font-size:12px;">✏️ แก้ไข</a>
                        </span>
                    </td>
                </tr>
            """
        
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
        
        # ตรวจสอบการกดปุ่มจาก URL Parameter (วิธีที่เสถียรที่สุดใน Streamlit HTML)
        query_params = st.query_params
        if "edit" in query_params:
            st.session_state.edit_id = query_params["edit"]
            st.session_state.form_key_index += 1
            st.query_params.clear()
            st.rerun()

        if not has_rows:
            st.info("ไม่พบข้อมูลที่ตรงกับเงื่อนไข")
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")
