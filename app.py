import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import uuid
from datetime import datetime, date, timedelta

# ==========================================
# 0. 設定區 (管理員密碼 & 分享網址)
# ==========================================
ADMIN_PASSWORD = "sunny"

# ⚠️ 請將下方網址改成你實際部署後的網址
APP_URL = "https://sunny-girls-basketball.streamlit.app"

# ==========================================
# 1. 資料處理函式
# ==========================================
FILE_PATH = 'basketball_data.json'
MAX_CAPACITY = 20

def load_data():
    default_data = {"sessions": {}, "hidden": []}
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "sessions" not in data:
                    data["sessions"] = {}
                if "hidden" not in data:
                    data["hidden"] = []
                return data
        except:
            return default_data
    return default_data

def save_data(data):
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# 用來記錄目前正在編輯哪一筆 ID
if 'edit_target' not in st.session_state:
    st.session_state.edit_target = None

# ==========================================
# 2. 介面樣式
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #f0f9ff;
        border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0f2fe; border-bottom: 2px solid #0ea5e9; font-weight: bold;
    }
    .header-box {
        background: linear-gradient(to right, #38bdf8, #3b82f6, #6366f1);
        padding: 2rem; border-radius: 1rem; color: white; margin-bottom: 1rem;
        text-align: center;
    }
    .info-tag {
        background: rgba(255, 255, 255, 0.2);
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
        backdrop-filter: blur(5px);
    }
    button[kind="secondary"] {
        padding: 0px 10px;
        border-radius: 5px;
    }
    /* 調整 Expander 樣式 */
    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    div[data-testid="stExpander"] details {
        border: none !important;
    }
    /* 編輯模式的框框 */
    .edit-box {
        border: 2px solid #3b82f6;
        border-radius: 10px;
        padding: 15px;
        background-color: #f0f9ff;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄：場次管理
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    pwd_input = st.text_input("輸入管理密碼解鎖功能", type="password")
    
    is_admin = (pwd_input == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("🔓 已解鎖 (管理員模式)")
        
        # 新增場次
        new_date = st.date_input("新增打球日期", min_value=date.today())
        if st.button("➕ 新增場次"):
            date_str = str(new_date)
            if date_str not in st.session_state.data["sessions"]:
                st.session_state.data["sessions"][date_str] = []
                save_data(st.session_state.data)
                st.success(f"已新增 {date_str}")
                st.rerun()
            else:
                st.warning("日期已存在")
        
        st.markdown("---")
        
        all_session_dates = sorted(st.session_state.data["sessions"].keys())
        
        if all_session_dates:
            st.write("👁️ **設定隱藏場次**")
            current_hidden = st.session_state.data["hidden"]
            current_hidden = [d for d in current_hidden if d in all_session_dates]
            
            # 【這裡改了】設定 placeholder="Choose Date"
            selected_hidden = st.multiselect(
                "Choose Date",   # 上面的標題
                options=all_session_dates,
                default=current_hidden,
                placeholder="Choose Date"  # 框框裡面的灰字
            )
            
            if set(selected_hidden) != set(st.session_state.data["hidden"]):
                st.session_state.data["hidden"] = selected_hidden
                save_data(st.session_state.data)
                st.rerun()

            st.markdown("---")
            
            # 刪除場次
            del_date = st.selectbox("刪除日期", options=all_session_dates)
            if st.button("確認刪除"):
                del st.session_state.data["sessions"][del_date]
                if del_date in st.session_state.data["hidden"]:
                    st.session_state.data["hidden"].remove(del_date)
                save_data(st.session_state.data)
                st.success("已刪除")
                st.rerun()
    else:
        if pwd_input: st.error("密碼錯誤")

# ==========================================
# 4. 主頁面邏輯
# ==========================================

col_header, col_share = st.columns([8, 2])

with col_header:
    st.markdown("""
        <div class="header-box">
            <h1 style="margin:0; font-size: 2.2rem; font-weight: 800; letter-spacing: 1px;">晴女☀️在場邊等妳🌈</h1>
            <p style="margin:5px 0 15px 0; font-size: 0.9rem; opacity: 0.9; letter-spacing: 1px;">✨ 希望永遠是晴天 ✨</p>
            <div class="info-tag">
                📍 地點：朱崙公園 &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 時間：19:00開打
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_share:
    st.write("") 
    st.write("")
    components.html(
        f"""
        <style>
        .copy-btn {{
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            color: #333;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            font-family: "Source Sans Pro", sans-serif;
            font-weight: 600;
            cursor: pointer;
            transition-duration: 0.4s;
            width: 100%;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        .copy-btn:hover {{
            background-color: #f8f9fa;
            border-color: #d0d0d0;
        }}
        .copy-btn:active {{
            background-color: #e9ecef;
            transform: translateY(1px);
        }}
        </style>
        <button class="copy-btn" onclick="copyToClipboard()" id="shareBtn">
            🔗 分享連結
        </button>
        <script>
        function copyToClipboard() {{
            const url = "{APP_URL}";
            navigator.clipboard.writeText(url).then(function() {{
                const btn = document.getElementById("shareBtn");
                btn.innerText = "✅ 已複製！";
                btn.style.borderColor = "#4CAF50";
                btn.style.color = "#4CAF50";
                setTimeout(function() {{
                    btn.innerText = "🔗 分享連結";
                    btn.style.borderColor = "#e0e0e0";
                    btn.style.color = "#333";
                }}, 2000);
            }}, function(err) {{
                console.error('Async: Could not copy text: ', err);
            }});
        }}
        </script>
        """,
        height=50
    )

# -----------------------------------------------------

all_dates_raw = sorted(st.session_state.data["sessions"].keys())
hidden_list = st.session_state.data.get("hidden", [])

if is_admin:
    display_dates = all_dates_raw
else:
    display_dates = [d for d in all_dates_raw if d not in hidden_list]

if not display_dates:
    if is_admin:
        st.info("👋 目前沒有場次，請在左側新增！")
    else:
        st.info("👋 目前沒有開放報名的場次，請稍後再來！")
else:
    tab_titles = []
    for d in display_dates:
        title = f"📅 {d}"
        if is_admin and d in hidden_list:
            title += " (🔒隱藏)"
        tab_titles.append(title)

    tabs = st.tabs(tab_titles)

    for i, date_key in enumerate(display_dates):
        with tabs[i]:
            # ==========================================
            # 判斷是否截止 (開團前一天 18:00)
            # ==========================================
            try:
                y, m, d_int = map(int, date_key.split('-'))
                session_date = datetime(y, m, d_int)
                # 截止時間：前一天 18:00
                deadline_dt = (session_date - timedelta(days=1)).replace(hour=18, minute=0, second=0)
                current_dt = datetime.now()
                is_locked = current_dt > deadline_dt
            except:
                is_locked = False

            # 【重要】是否允許編輯 (含修改與刪除)
            can_edit = is_admin or (not is_locked)
            form_disabled = not can_edit

            current_players = st.session_state.data["sessions"][date_key]
            
            sorted_players = sorted(current_players, key=lambda x: x.get('timestamp', 0))
            main_list = []
            wait_list = []
            current_count = 0

            for p in sorted_players:
                p_count = p.get('count', 1)
                if current_count + p_count <= MAX_CAPACITY:
                    main_list.append(p)
                    current_count += p_count
                else:
                    wait_list.append(p)
            
            total_reg = sum(p.get('count', 1) for p in current_players)
            c1, c2, c3 = st.columns(3)
            c1.metric("總人數", f"{total_reg}")
            c2.metric("正選", f"{len(main_list)} / {MAX_CAPACITY}")
            c3.metric("候補", f"{len(wait_list)}")
            st.markdown("---")

            col_form, col_list = st.columns([1, 2])

            with col_form:
                st.subheader("📝 我要報名")
                
                if is_locked and not is_admin:
                    st.warning(f"⛔ 報名已於前一日 18:00 截止，表單已鎖定。\n\n如需異動請聯繫管理員。")

                with st.form(f"form_{date_key}", clear_on_submit=True):
                    name_input = st.text_input("球員姓名", disabled=form_disabled)
                    is_member = st.checkbox("⭐我是晴女", key=f"mem_{date_key}", disabled=form_disabled)
                    total_count = st.number_input("報名總人數 (含自己, Max 3)", 1, 3, 1, key=f"tot_{date_key}", disabled=form_disabled)
                    
                    c_b, c_c = st.columns(2)
                    bring_ball = c_b.checkbox("🏀帶球", key=f"b_{date_key}", disabled=form_disabled)
                    occupy_court = c_c.checkbox("🚩佔場", key=f"c_{date_key}", disabled=form_disabled)
                    
                    submit_label = "送出" if can_edit else "⛔ 已截止"
                    
                    if st.form_submit_button(submit_label, disabled=form_disabled):
                        if name_input:
                            ts = time.time()
                            new_entries = []
                            # 自己
                            new_entries.append({
                                "id": str(uuid.uuid4()), "name": name_input, "count": 1,
                                "isMember": is_member, "bringBall": bring_ball,
                                "occupyCourt": occupy_court, "timestamp": ts
                            })
                            # 朋友 (拆成獨立資料，方便個別刪除)
                            friends = total_count - 1
                            for f in range(friends):
                                new_entries.append({
                                    "id": str(uuid.uuid4()), "name": f"{name_input} (朋友{f+1})",
                                    "count": 1, "isMember": False, "bringBall": False,
                                    "occupyCourt": False, "timestamp": ts + 0.1 + (f * 0.01)
                                })
                            st.session_state.data["sessions"][date_key].extend(new_entries)
                            save_data(st.session_state.data)
                            st.rerun()
                        else:
                            st.error("需填寫姓名")

                st.info("""
                **📌 規則**
                * **人數修改**：若要「減人」，請直接在名單中按刪除❌；若要「加人」，請重新報名排隊。
                * **資料修改**：點擊名單旁的✏️可修改屬性 (晴女/帶球/佔場)。
                * **遞補規則**：候補⭐晴女可優先遞補正選「非晴女」。
                * **截止時間**：開團前一日 18:00 截止。
                """)

            with col_list:
                # 刪除功能
                def delete_p(pid, d_key):
                    st.session_state.data["sessions"][d_key] = [
                        p for p in st.session_state.data["sessions"][d_key] if p["id"] != pid
                    ]
                    if st.session_state.edit_target == pid:
                        st.session_state.edit_target = None
                    save_data(st.session_state.data)
                    st.rerun()

                # 遞補功能
                def promote_p(wait_pid, d_key, target_main_list):
                    all_p = st.session_state.data["sessions"][d_key]
                    wait_person = next((p for p in all_p if p['id'] == wait_pid), None)
                    
                    target_guest = None
                    for p in reversed(target_main_list):
                        if not p.get('isMember'):
                            target_id = p['id']
                            target_guest = next((op for op in all_p if op['id'] == target_id), None)
                            break
                    
                    if wait_person and target_guest:
                        cutoff_person = target_main_list[-1]
                        cutoff_time = cutoff_person.get('timestamp', 0)
                        
                        wait_person['timestamp'] = target_guest['timestamp'] - 1.0
                        target_guest['timestamp'] = cutoff_time + 1.0
                        
                        save_data(st.session_state.data)
                        st.success(f"遞補成功！晴女 {wait_person['name']} 已晉升正選。")
                        time.sleep(0.5)
                        st.rerun()
                    elif wait_person and not target_guest:
                        st.error("❌ 無法遞補：正選名單全是晴女。")

                # 修改功能
                def update_p(pid, d_key, new_name, new_is_mem, new_ball, new_court):
                    all_p = st.session_state.data["sessions"][d_key]
                    target = next((p for p in all_p if p['id'] == pid), None)
                    if target:
                        target['name'] = new_name
                        target['isMember'] = new_is_mem
                        target['bringBall'] = new_ball
                        target['occupyCourt'] = new_court
                        save_data(st.session_state.data)
                        st.session_state.edit_target = None
                        st.rerun()

                st.subheader("✅ 正選名單")
                if main_list:
                    for idx, p in enumerate(main_list):
                        # 如果是編輯狀態 (且 ID 符合)
                        if st.session_state.edit_target == p['id']:
                            with st.container():
                                st.markdown(f"<div class='edit-box'><b>✏️ 編輯中：{p['name']}</b>", unsafe_allow_html=True)
                                with st.form(key=f"edit_{p['id']}"):
                                    e_name = st.text_input("姓名", value=p['name'])
                                    col_e1, col_e2, col_e3 = st.columns(3)
                                    e_mem = col_e1.checkbox("⭐晴女", value=p.get('isMember', False))
                                    e_ball = col_e2.checkbox("🏀帶球", value=p.get('bringBall', False))
                                    e_court = col_e3.checkbox("🚩佔場", value=p.get('occupyCourt', False))
                                    
                                    b1, b2 = st.columns([1, 1])
                                    if b1.form_submit_button("💾 儲存"):
                                        update_p(p['id'], date_key, e_name, e_mem, e_ball, e_court)
                                    if b2.form_submit_button("取消"):
                                        st.session_state.edit_target = None
                                        st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)

                        else:
                            # 正常顯示模式
                            cols = st.columns([0.5, 3, 1.5, 0.5, 0.5]) 
                            cols[0].write(f"{idx+1}.")
                            cols[1].write(p['name'] + (" ⭐" if p.get('isMember') else ""))
                            
                            tag_s = []
                            if p.get('bringBall'): tag_s.append("🏀")
                            if p.get('occupyCourt'): tag_s.append("🚩")
                            cols[2].write(" ".join(tag_s))
                            
                            if can_edit:
                                # 編輯按鈕
                                if cols[3].button("✏️", key=f"e_{p['id']}"):
                                    st.session_state.edit_target = p['id']
                                    st.rerun()
                                # 刪除按鈕
                                if cols[4].button("❌", key=f"d_{p['id']}"):
                                    delete_p(p['id'], date_key)
                else:
                    st.write("尚無人報名")

                if wait_list:
                    st.divider()
                    st.subheader(f"⏳ 候補名單 ({len(wait_list)})")
                    
                    for idx, p in enumerate(wait_list):
                        if st.session_state.edit_target == p['id']:
                            with st.container():
                                st.markdown(f"<div class='edit-box'><b>✏️ 編輯中：{p['name']}</b>", unsafe_allow_html=True)
                                with st.form(key=f"edit_wait_{p['id']}"):
                                    e_name = st.text_input("姓名", value=p['name'])
                                    col_e1, col_e2, col_e3 = st.columns(3)
                                    e_mem = col_e1.checkbox("⭐晴女", value=p.get('isMember', False))
                                    e_ball = col_e2.checkbox("🏀帶球", value=p.get('bringBall', False))
                                    e_court = col_e3.checkbox("🚩佔場", value=p.get('occupyCourt', False))
                                    
                                    b1, b2 = st.columns([1, 1])
                                    if b1.form_submit_button("💾 儲存"):
                                        update_p(p['id'], date_key, e_name, e_mem, e_ball, e_court)
                                    if b2.form_submit_button("取消"):
                                        st.session_state.edit_target = None
                                        st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            can_promote = p.get('isMember')
                            cols = st.columns([0.5, 3, 1, 1, 0.5, 0.5]) 

                            cols[0].write(f"{idx+1}.")
                            cols[1].write(p['name'] + (" ⭐" if p.get('isMember') else ""))
                            
                            tag_s = []
                            if p.get('bringBall'): tag_s.append("🏀")
                            if p.get('occupyCourt'): tag_s.append("🚩")
                            cols[2].write(" ".join(tag_s
