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
# ⚠️ 請記得將下方網址改成你實際部署後的網址，讓分享按鈕生效
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
# 2. UI 美化樣式 (CSS) - 3D 卡片 + 彩色標籤 + 手機優化
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="centered") 

st.markdown("""
    <style>
    /* 1. 字體與基礎設定 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 2. Header 樣式 */
    .header-box {
        background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
        padding: 1.5rem; 
        border-radius: 16px; 
        color: #4a5568; 
        text-align: center; 
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(161, 196, 253, 0.4);
    }
    .header-title { 
        font-size: 1.6rem; font-weight: 800; margin: 0; color: #2d3748; letter-spacing: 1px;
    }
    .header-sub { 
        font-size: 0.9rem; color: #4a5568; margin-top: 4px; font-weight: 500;
    }
    .info-pill {
        background: rgba(255, 255, 255, 0.6); 
        padding: 4px 14px;
        border-radius: 20px; 
        font-size: 0.85rem; 
        font-weight: 600;
        color: #2b6cb0;
        display: inline-block; 
        margin-top: 12px;
        backdrop-filter: blur(5px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* 3. Tabs 樣式 */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; margin-bottom: 15px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px; background-color: #f7fafc; border-radius: 20px;
        padding: 4px 12px; font-size: 0.9rem; border: 1px solid #edf2f7;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #3b82f6; color: white; border: none; box-shadow: 0 2px 5px rgba(59, 130, 246, 0.3);
    }

    /* 4. 名單卡片 (Card) */
    .player-row {
        background: white;
        border: 1px solid #f1f5f9;
        border-radius: 12px;
        padding: 8px 4px 8px 12px; 
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
    }
    .player-row:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #e2e8f0;
    }

    /* 5. 膠囊標籤 (Badges) */
    .badge {
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        margin-left: 4px;
        display: inline-block;
        vertical-align: middle;
    }
    .badge-sunny { background-color: #fef3c7; color: #d97706; border: 1px solid #fcd34d; } /* 金黃 */
    .badge-ball { background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; } /* 橘 */
    .badge-court { background-color: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; } /* 藍 */

    /* 6. 按鈕與排版 */
    [data-testid="stHorizontalBlock"] { align-items: center !important; }
    .list-text { font-size: 1rem; font-weight: 600; color: #334155; }
    
    /* 幽靈按鈕 (Ghost Buttons) */
    .list-btn-col button {
        border: none !important; background: transparent !important;
        padding: 6px !important; margin: 0 !important;
        color: #cbd5e1 !important; line-height: 1 !important;
    }
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; border-radius: 50%; }
    .list-btn-d button:hover { color: #ef4444 !important; background: #fef2f2 !important; border-radius: 50%; }
    
    .list-btn-up button {
        padding: 4px 8px !important; min-height: 28px !important; font-size: 0.8rem !important;
    }
    
    /* 進度條 */
    .progress-container {
        width: 100%; background-color: #f1f5f9; border-radius: 10px; height: 8px; margin-top: 5px; overflow: hidden;
    }
    .progress-bar {
        height: 100%; border-radius: 10px; 
        background: linear-gradient(90deg, #60a5fa, #3b82f6);
        transition: width 0.5s ease;
    }
    .progress-text { font-size: 0.8rem; color: #64748b; margin-bottom: 2px; display: flex; justify-content: space-between;}

    /* 編輯框 */
    .edit-box {
        border: 2px solid #3b82f6; border-radius: 12px;
        padding: 15px; background-color: #fff; margin-bottom: 15px;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
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

# --- Header ---
st.markdown("""
    <div class="header-box">
        <div class="header-title">晴女☀️在場邊等妳🌈</div>
        <div class="header-sub">✨ Keep Playing, Keep Shining ✨</div>
        <div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div>
    </div>
""", unsafe_allow_html=True)

components.html(
    f"""<body style="margin:0;display:flex;justify-content:center;"><button style="background:white;border:1px solid #e2e8f0;border-radius:20px;padding:8px 20px;font-size:13px;cursor:pointer;color:#64748b;font-weight:600;display:flex;align-items:center;gap:6px;box-shadow:0 1px 2px rgba(0,0,0,0.05);transition:all 0.2s;" onclick="navigator.clipboard.writeText('{APP_URL}').then(()=>{{document.getElementById('t').innerText='已複製!'}});this.style.transform='scale(0.95)'">🔗 <span id="t">分享報名連結</span></button></body>""", height=45
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

            # === 進度條與統計 ===
            total_reg = sum(p.get('count', 1) for p in players)
            pct = min(100, (len(main) / MAX_CAPACITY) * 100)
            
            st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <div class="progress-text">
                    <span><b>正選名單</b> ({len(main)}/{MAX_CAPACITY})</span>
                    <span>候補: <b>{len(wait)}</b> 人</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
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

            # === 報名表單 & 規則 ===
            with st.expander("📝 點擊報名 / 查看規則", expanded=not is_locked):
                if is_locked and not is_admin: st.warning("⛔ 報名已於前一日 18:00 截止")
                
                with st.form(f"f_{date_key}", clear_on_submit=True):
                    f_name = st.text_input("球員姓名", disabled=not can_edit, placeholder="請輸入姓名")
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
                
                # --- [修復完成] 規則文案 ---
                st.info("""
                **📌 報名須知**
                * **人數限制**：上限 20 人，每人最多報 3 位。額滿將自動排入候補。
                * **優先遞補**：候補名單中之「⭐晴女」，享有優先遞補「非晴女」之權益。
                * **修改/減人**：需減少人數或修改資料，請直接點擊名單右側的 ✏️ 或 ❌。
                * **增加人數**：為維護排隊公平，**加人請重新填寫報名表**。
                * **截止/雨備**：前一日 18:00 截止報名 (逾時請洽管理員)；雨天於當日 17:00 公告。
                """)

            # === 名單顯示 (卡片 + 膠囊) ===
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
                        badge_html = ""
                        if p.get('isMember'): badge_html += "<span class='badge badge-sunny'>晴女</span>"
                        if p.get('bringBall'): badge_html += "<span class='badge badge-ball'>帶球</span>"
                        if p.get('occupyCourt'): badge_html += "<span class='badge badge-court'>佔場</span>"

                        st.markdown(f'<div class="player-row">', unsafe_allow_html=True)
                        
                        r1, r2, r3 = st.columns([6.5, 1, 1])
                        r1.markdown(f"<span class='list-text'>{idx+1}. {p['name']}</span> {badge_html}", unsafe_allow_html=True)
                        
                        if can_edit:
                            with r2:
                                st.markdown('<div class="list-btn-col list-btn-e">', unsafe_allow_html=True)
                                if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target = p['id']; st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            with r3:
                                st.markdown('<div class="list-btn-col list-btn-d">', unsafe_allow_html=True)
                                if st.button("❌", key=f"bd_{p['id']}"): delete_p(p['id'], date_key)
                                st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.caption("😴 目前尚無人報名，快來搶頭香！")

            if wait:
                st.divider()
                st.subheader(f"⏳ 候補名單")
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
                        badge_html = ""
                        if p.get('isMember'): badge_html += "<span class='badge badge-sunny'>晴女</span>"
                        if p.get('bringBall'): badge_html += "<span class='badge badge-ball'>帶球</span>"
                        if p.get('occupyCourt'): badge_html += "<span class='badge badge-court'>佔場</span>"

                        st.markdown(f'<div class="player-row" style="background-color:#f8fafc;">', unsafe_allow_html=True)
                        
                        cols_cfg = [5, 1.5, 1, 1] if is_admin else [6.5, 1, 1]
                        cols = st.columns(cols_cfg)
                        cols[0].markdown(f"<span class='list-text' style='color:#64748b;'>{idx+1}. {p['name']}</span> {badge_html}", unsafe_allow_html=True)
                        
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
                        st.markdown('</div>', unsafe_allow_html=True)
