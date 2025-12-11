import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import uuid
from datetime import datetime, date, timedelta

# ==========================================
# 0. 設定區
# ==========================================
ADMIN_PASSWORD = "sunny"
APP_URL = "https://sunny-girls-basketball.streamlit.app"
FILE_PATH = 'basketball_data.json'
MAX_CAPACITY = 20

# ==========================================
# 1. 資料處理
# ==========================================
def load_data():
    default_data = {"sessions": {}, "hidden": []}
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "sessions" not in data: data["sessions"] = {}
                if "hidden" not in data: data["hidden"] = []
                return data
        except:
            return default_data
    return default_data

def save_data(data):
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'edit_target' not in st.session_state:
    st.session_state.edit_target = None

# ==========================================
# 2. 手機版 UI 優化樣式 (CSS)
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="centered") 

st.markdown("""
    <style>
    /* 1. 基礎設定 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 2. Header 優化 */
    .header-box {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        padding: 1.5rem; border-radius: 12px; color: white; 
        text-align: center; margin-bottom: 15px;
    }
    /* 標題字體調整，讓中文標題在手機上不會換行 */
    .header-title { font-size: 1.5rem; font-weight: 800; margin: 0; letter-spacing: 1px; }
    .header-sub { font-size: 0.9rem; opacity: 0.95; margin-top: 5px; }
    
    .info-pill {
        background: rgba(255, 255, 255, 0.2); padding: 3px 12px;
        border-radius: 12px; font-size: 0.85rem; display: inline-block; margin-top: 10px;
    }

    /* 3. Tabs 優化 */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 38px; background-color: #f1f5f9; border-radius: 5px;
        padding: 4px 8px; font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] { background-color: #3b82f6; color: white; }

    /* 4. 列表與按鈕排版修正 (這是讓畫面變整齊的關鍵) */
    [data-testid="stHorizontalBlock"] { align-items: center !important; }

    .list-text { font-size: 1rem; font-weight: 500; line-height: 1.4; color: #334155; }
    .list-tags { font-size: 0.8rem; color: #666; margin-left: 4px; }

    /* 按鈕樣式極簡化 */
    .list-btn-col button {
        border: none !important; background: transparent !important;
        padding: 4px 8px !important; margin: 0 !important;
        color: #94a3b8 !important; min-height: 0px !important;
        height: auto !important; line-height: 1 !important; box-shadow: none !important;
    }
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; }
    .list-btn-d button:hover { color: #ef4444 !important; background: #fef2f2 !important; }
    
    .list-btn-up button {
        padding: 4px 8px !important; min-height: 28px !important; font-size: 0.8rem !important;
    }
    
    .edit-box {
        border: 2px solid #3b82f6; border-radius: 8px;
        padding: 10px; background-color: #eff6ff; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄 & Header
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    pwd_input = st.text_input("輸入管理密碼", type="password")
    is_admin = (pwd_input == ADMIN_PASSWORD)
    if is_admin:
        st.success("🔓 已解鎖")
        new_date = st.date_input("新增打球日期", min_value=date.today())
        if st.button("➕ 新增場次"):
            d_str = str(new_date)
            if d_str not in st.session_state.data["sessions"]:
                st.session_state.data["sessions"][d_str] = []
                save_data(st.session_state.data)
                st.rerun()
        st.markdown("---")
        all_dates = sorted(st.session_state.data["sessions"].keys())
        if all_dates:
            st.write("設定隱藏場次")
            cur_hidden = [d for d in st.session_state.data["hidden"] if d in all_dates]
            sel_hidden = st.multiselect("Choose Date", all_dates, default=cur_hidden, placeholder="Choose Date")
            if set(sel_hidden) != set(st.session_state.data["hidden"]):
                st.session_state.data["hidden"] = sel_hidden
                save_data(st.session_state.data)
                st.rerun()
            st.markdown("---")
            del_d = st.selectbox("刪除日期", all_dates)
            if st.button("確認刪除"):
                del st.session_state.data["sessions"][del_d]
                if del_d in st.session_state.data["hidden"]: st.session_state.data["hidden"].remove(del_d)
                save_data(st.session_state.data)
                st.rerun()

# --- 恢復中文標題 ---
st.markdown("""
    <div class="header-box">
        <div class="header-title">晴女☀️在場邊等妳🌈</div>
        <div class="header-sub">✨ 希望永遠是晴天 ✨</div>
        <div class="info-pill">📍 地點：朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div>
    </div>
""", unsafe_allow_html=True)

components.html(
    f"""<body style="margin:0;display:flex;justify-content:center;"><button style="background:white;border:1px solid #ddd;border-radius:20px;padding:6px 15px;font-size:13px;cursor:pointer;color:#555;display:flex;align-items:center;gap:5px;" onclick="navigator.clipboard.writeText('{APP_URL}').then(()=>{{document.getElementById('t').innerText='已複製!'}})">🔗 <span id="t">分享連結</span></button></body>""", height=35
)

# ==========================================
# 4. 主畫面邏輯
# ==========================================
all_dates_raw = sorted(st.session_state.data["sessions"].keys())
hidden_list = st.session_state.data.get("hidden", [])
display_dates = all_dates_raw if is_admin else [d for d in all_dates_raw if d not in hidden_list]

if not display_dates:
    st.info("👋 目前沒有開放報名的場次，請稍後再來！")
else:
    tab_titles = []
    for d in display_dates:
        # 手機版顯示日期簡短一點比較好看 (月/日)
        dt_obj = datetime.strptime(d, "%Y-%m-%d")
        title = f"{dt_obj.month}/{dt_obj.day}"
        if is_admin and d in hidden_list: title += "🔒"
        tab_titles.append(title)

    tabs = st.tabs(tab_titles)

    for i, date_key in enumerate(display_dates):
        with tabs[i]:
            try:
                y, m, d_int = map(int, date_key.split('-'))
                sess_dt = datetime(y, m, d_int)
                deadline = (sess_dt - timedelta(days=1)).replace(hour=18, minute=0, second=0)
                is_locked = datetime.now() > deadline
            except: is_locked = False

            can_edit = is_admin or (not is_locked)
            players = st.session_state.data["sessions"][date_key]
            players = sorted(players, key=lambda x: x.get('timestamp', 0))
            main, wait = [], []
            curr_count = 0
            for p in players:
                if curr_count + p.get('count', 1) <= MAX_CAPACITY:
                    main.append(p)
                    curr_count += p.get('count', 1)
                else: wait.append(p)

            c1, c2, c3 = st.columns(3)
            c1.caption(f"總人數: {len(players)}")
            c2.caption(f"正選: {len(main)}/{MAX_CAPACITY}")
            c3.caption(f"候補: {len(wait)}")
            
            # === 功能函式 ===
            def update_p(pid, d_key, name, is_m, ball, court):
                target = next((p for p in st.session_state.data["sessions"][d_key] if p['id'] == pid), None)
                if target:
                    target['name'], target['isMember'] = name, is_m
                    target['bringBall'], target['occupyCourt'] = ball, court
                    save_data(st.session_state.data)
                    st.session_state.edit_target = None
                    st.rerun()
            def delete_p(pid, d_key):
                st.session_state.data["sessions"][d_key] = [p for p in st.session_state.data["sessions"][d_key] if p["id"] != pid]
                if st.session_state.edit_target == pid: st.session_state.edit_target = None
                save_data(st.session_state.data)
                st.rerun()
            def promote_p(wait_pid, d_key):
                all_p = st.session_state.data["sessions"][d_key]
                w_p = next((p for p in all_p if p['id'] == wait_pid), None)
                target_g = None
                for p in reversed(main):
                    if not p.get('isMember'):
                        target_g = next((op for op in all_p if op['id'] == p['id']), None)
                        break
                if w_p and target_g:
                    cutoff = main[-1]['timestamp']
                    w_p['timestamp'] = target_g['timestamp'] - 1.0
                    target_g['timestamp'] = cutoff + 1.0
                    save_data(st.session_state.data)
                    st.success("遞補成功"); time.sleep(0.5); st.rerun()
                else: st.error("無法遞補")

            # === 報名表單 (恢復原本的文字內容) ===
            with st.expander("📝 我要報名 / 查看規則", expanded=not is_locked):
                if is_locked and not is_admin: st.warning("⛔ 報名已於前一日 18:00 截止，表單已鎖定。")
                with st.form(f"f_{date_key}", clear_on_submit=True):
                    f_name = st.text_input("球員姓名", disabled=not can_edit)
                    col_f1, col_f2, col_f3 = st.columns(3)
                    f_mem = col_f1.checkbox("⭐晴女", key=f"m_{date_key}", disabled=not can_edit)
                    f_ball = col_f2.checkbox("🏀帶球", key=f"b_{date_key}", disabled=not can_edit)
                    f_crt = col_f3.checkbox("🚩佔場", key=f"c_{date_key}", disabled=not can_edit)
                    f_tot = st.number_input("報名總人數 (含自己, Max 3)", 1, 3, 1, key=f"t_{date_key}", disabled=not can_edit)
                    
                    if st.form_submit_button("送出報名", disabled=not can_edit, type="primary"):
                        if f_name:
                            ts = time.time()
                            new_ps = [{"id": str(uuid.uuid4()), "name": f_name, "count": 1, "isMember": f_mem, "bringBall": f_ball, "occupyCourt": f_crt, "timestamp": ts}]
                            for f in range(f_tot - 1):
                                new_ps.append({"id": str(uuid.uuid4()), "name": f"{f_name} (朋友{f+1})", "count": 1, "isMember": False, "bringBall": False, "occupyCourt": False, "timestamp": ts + 0.1 + (f*0.01)})
                            st.session_state.data["sessions"][date_key].extend(new_ps)
                            save_data(st.session_state.data)
                            st.rerun()
                        else: st.error("需填寫姓名")
                
                # --- 恢復完整的規則說明 ---
                st.info("""
                **📌 規則**
                * **人數修改**：若要「減人」，請直接在名單中按刪除❌；若要「加人」，請重新報名排隊。
                * **資料修改**：點擊名單旁的✏️可修改屬性 (晴女/帶球/佔場)。
                * **遞補規則**：候補⭐晴女可優先遞補正選「非晴女」。
                * **截止時間**：開團前一日 18:00 截止。
                """)

            # === 名單顯示 ===
            st.subheader("✅ 正選名單")
            if main:
                for idx, p in enumerate(main):
                    if st.session_state.edit_target == p['id']:
                        with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ 編輯中：{p['name']}</div>", unsafe_allow_html=True)
                            with st.form(key=f"e_{p['id']}"):
                                en = st.text_input("姓名", p['name'])
                                ec1, ec2, ec3 = st.columns(3)
                                em = ec1.checkbox("⭐晴女", p.get('isMember'))
                                eb = ec2.checkbox("🏀帶球", p.get('bringBall'))
                                ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'))
                                b1, b2 = st.columns(2)
                                if b1.form_submit_button("💾 儲存", type="primary"): update_p(p['id'], date_key, en, em, eb, ec)
                                if b2.form_submit_button("取消"): st.session_state.edit_target = None; st.rerun()
                    else:
                        tags = []
                        if p.get('isMember'): tags.append("⭐")
                        if p.get('bringBall'): tags.append("🏀")
                        if p.get('occupyCourt'): tags.append("🚩")
                        tag_str = " ".join(tags)

                        r1, r2, r3 = st.columns([6.5, 1, 1])
                        r1.markdown(f"<span class='list-text'>{idx+1}. {p['name']}</span> <span class='list-tags'>{tag_str}</span>", unsafe_allow_html=True)
                        
                        if can_edit:
                            with r2:
                                st.markdown('<div class="list-btn-col list-btn-e">', unsafe_allow_html=True)
                                if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target = p['id']; st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            with r3:
                                st.markdown('<div class="list-btn-col list-btn-d">', unsafe_allow_html=True)
                                if st.button("❌", key=f"bd_{p['id']}"): delete_p(p['id'], date_key)
                                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.caption("尚無人報名")

            if wait:
                st.divider()
                st.subheader(f"⏳ 候補名單 ({len(wait)})")
                for idx, p in enumerate(wait):
                    if st.session_state.edit_target == p['id']:
                         with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ 編輯中：{p['name']}</div>", unsafe_allow_html=True)
                            with st.form(key=f"ew_{p['id']}"):
                                en = st.text_input("姓名", p['name'])
                                ec1, ec2, ec3 = st.columns(3)
                                em = ec1.checkbox("⭐晴女", p.get('isMember'))
                                eb = ec2.checkbox("🏀帶球", p.get('bringBall'))
                                ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'))
                                b1, b2 = st.columns(2)
                                if b1.form_submit_button("💾 儲存", type="primary"): update_p(p['id'], date_key, en, em, eb, ec)
                                if b2.form_submit_button("取消"): st.session_state.edit_target = None; st.rerun()
                    else:
                        tags = []; 
                        if p.get('isMember'): tags.append("⭐")
                        if p.get('bringBall'): tags.append("🏀")
                        if p.get('occupyCourt'): tags.append("🚩")
                        tag_str = " ".join(tags)
                        
                        cols_cfg = [5, 1.5, 1, 1] if is_admin else [6.5, 1, 1]
                        cols = st.columns(cols_cfg)
                        cols[0].markdown(f"<span class='list-text'>{idx+1}. {p['name']}</span> <span class='list-tags'>{tag_str}</span>", unsafe_allow_html=True)
                        
                        btn_idx = 1
                        if is_admin and p.get('isMember'):
                            with cols[btn_idx]:
                                st.markdown('<div class="list-btn-up">', unsafe_allow_html=True)
                                if st.button("⬆️遞補", key=f"up_{p['id']}"): promote_p(p['id'], date_key)
                                st.markdown('</div>', unsafe_allow_html=True)
                            btn_idx += 1
                        
                        if can_edit:
                             if btn_idx < len(cols):
                                with cols[btn_idx]:
                                    st.markdown('<div class="list-btn-col list-btn-e">', unsafe_allow_html=True)
                                    if st.button("✏️", key=f"bew_{p['id']}"): st.session_state.edit_target = p['id']; st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)
                             if btn_idx + 1 < len(cols):
                                with cols[btn_idx+1]:
                                    st.markdown('<div class="list-btn-col list-btn-d">', unsafe_allow_html=True)
                                    if st.button("❌", key=f"bdw_{p['id']}"): delete_p(p['id'], date_key)
                                    st.markdown('</div>', unsafe_allow_html=True)
