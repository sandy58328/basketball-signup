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
# ⚠️ 上線後請換成真實網址
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
# 2. UI 極致美化 (CSS) - 緊湊版
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="centered") 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    .block-container { padding-top: 1rem !important; padding-bottom: 4rem !important; }
    #MainMenu, footer { visibility: hidden; }

    /* Header */
    .header-box {
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
        padding: 1.5rem 1rem; border-radius: 16px; color: #4a5568; 
        text-align: center; margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(161, 196, 253, 0.3);
    }
    .header-title { font-size: 1.5rem; font-weight: 800; color: #2d3748; letter-spacing: 1px; margin-bottom: 4px; }
    .header-sub { font-size: 0.85rem; color: #5a6b84; font-weight: 500; opacity: 0.9; }
    .info-pill {
        background: rgba(255, 255, 255, 0.65); padding: 4px 12px;
        border-radius: 30px; font-size: 0.8rem; font-weight: 600; color: #2b6cb0;
        display: inline-block; margin-top: 10px; backdrop-filter: blur(8px);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 38px; background-color: #f8fafc; border-radius: 20px;
        padding: 0 12px; font-size: 0.85rem; border: 1px solid #edf2f7; color: #64748b;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #3b82f6; color: white; border: none; 
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }

    /* Player Card (緊湊化調整) */
    .player-row {
        background: white; border: 1px solid #f1f5f9; border-radius: 12px;
        padding: 6px 4px 6px 12px; /* 上下縮減為 6px */
        margin-bottom: 5px; /* 卡片間距縮減為 5px */
        box-shadow: 0 1px 3px rgba(0,0,0,0.02); transition: transform 0.2s, box-shadow 0.2s;
    }
    .player-row:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0,0,0,0.05); }

    /* Badges */
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; margin-left: 6px; display: inline-block; vertical-align: middle; }
    .badge-sunny { background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; }
    .badge-ball { background: #fff7ed; color: #c2410c; border: 1px solid #fdba74; }
    .badge-court { background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; }

    /* Buttons & Layout */
    [data-testid="stHorizontalBlock"] { align-items: center !important; }
    .list-text { font-size: 0.95rem; font-weight: 600; color: #334155; }
    .list-btn-col button {
        border: none !important; background: transparent !important;
        padding: 6px !important; color: #cbd5e1 !important; line-height: 1 !important;
    }
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; border-radius: 50%; }
    .list-btn-d button:hover { color: #ef4444 !important; background: #fef2f2 !important; border-radius: 50%; }
    .list-btn-up button { padding: 2px 8px !important; min-height: 26px !important; font-size: 0.75rem !important; }

    /* Progress Bar */
    .progress-container { width: 100%; background: #f1f5f9; border-radius: 8px; height: 8px; margin-top: 6px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 8px; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
    .progress-text { font-size: 0.8rem; color: #64748b; margin-bottom: 4px; display: flex; justify-content: space-between; font-weight: 500; }

    /* Edit Box */
    .edit-box { border: 2px solid #3b82f6; border-radius: 12px; padding: 12px; background: #fff; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.15); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄 & Header
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    pwd = st.text_input("密碼", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("🔓 已解鎖")
        new_date = st.date_input("新增日期", min_value=date.today())
        if st.button("➕ 新增場次"):
            if (d:=str(new_date)) not in st.session_state.data["sessions"]:
                st.session_state.data["sessions"][d] = []
                save_data(st.session_state.data); st.rerun()
        st.markdown("---")
        dates = sorted(st.session_state.data["sessions"].keys())
        if dates:
            hidden = st.multiselect("隱藏場次", dates, default=[d for d in st.session_state.data["hidden"] if d in dates])
            if set(hidden) != set(st.session_state.data["hidden"]):
                st.session_state.data["hidden"] = hidden; save_data(st.session_state.data); st.rerun()
            st.markdown("---")
            if st.button("🗑️ 刪除選定日期"):
               del_d = st.selectbox("選擇日期", dates)
               del st.session_state.data["sessions"][del_d]
               save_data(st.session_state.data); st.rerun()

st.markdown("""
    <div class="header-box">
        <div class="header-title">晴女☀️在場邊等妳🌈</div>
        <div class="header-sub">✨ Keep Playing, Keep Shining ✨</div>
        <div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div>
    </div>
""", unsafe_allow_html=True)

components.html(
    f"""<body style="margin:0;display:flex;justify-content:center;"><button style="background:white;border:1px solid #e2e8f0;border-radius:20px;padding:6px 16px;font-size:12px;cursor:pointer;color:#64748b;font-weight:600;display:flex;align-items:center;gap:6px;box-shadow:0 1px 2px rgba(0,0,0,0.05);transition:all 0.2s;" onclick="navigator.clipboard.writeText('{APP_URL}').then(()=>{{document.getElementById('t').innerText='已複製!'}});this.style.transform='scale(0.95)'">🔗 <span id="t">分享報名連結</span></button></body>""", height=40
)

# ==========================================
# 4. 主畫面邏輯
# ==========================================
all_dates = sorted(st.session_state.data["sessions"].keys())
hidden = st.session_state.data.get("hidden", [])
dates = all_dates if is_admin else [d for d in all_dates if d not in hidden]

if not dates:
    st.info("👋 目前沒有開放報名的場次，請稍後再來！")
else:
    # 建立 Tabs
    tabs = st.tabs([f"{int(d.split('-')[1])}/{int(d.split('-')[2])}" + ("🔒" if d in hidden else "") for d in dates])

    for i, date_key in enumerate(dates):
        with tabs[i]:
            # 鎖定邏輯
            try:
                dt_obj = datetime.strptime(date_key, "%Y-%m-%d")
                deadline = (dt_obj - timedelta(days=1)).replace(hour=18, minute=0, second=0)
                is_locked = datetime.now() > deadline
            except: is_locked = False
            can_edit = is_admin or (not is_locked)

            # 資料分組
            players = sorted(st.session_state.data["sessions"][date_key], key=lambda x: x.get('timestamp', 0))
            main, wait = [], []
            curr = 0
            for p in players:
                if curr + p.get('count', 1) <= MAX_CAPACITY: main.append(p); curr += p.get('count', 1)
                else: wait.append(p)

            # === 智慧變色進度條 ===
            pct = min(100, (len(main) / MAX_CAPACITY) * 100)
            bar_color = "#4ade80" if pct < 50 else "#fbbf24" if pct < 85 else "#f87171"
            
            st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <div class="progress-text">
                    <span style="color:#334155;"><b>正選名單</b></span>
                    <span>{len(main)} / {MAX_CAPACITY}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {pct}%; background: {bar_color};"></div>
                </div>
                <div style="text-align:right; font-size:0.75rem; color:#94a3b8; margin-top:4px;">候補等待: {len(wait)} 人</div>
            </div>
            """, unsafe_allow_html=True)
            
            # === Action Functions ===
            def update(pid, d, n, im, bb, oc):
                t = next((p for p in st.session_state.data["sessions"][d] if p['id']==pid), None)
                if t: t.update({'name':n,'isMember':im,'bringBall':bb,'occupyCourt':oc}); save_data(st.session_state.data); st.session_state.edit_target=None; st.toast("✅ 資料已更新"); time.sleep(0.5); st.rerun()
            
            def delete(pid, d):
                st.session_state.data["sessions"][d] = [p for p in st.session_state.data["sessions"][d] if p['id']!=pid]
                if st.session_state.edit_target == pid: st.session_state.edit_target = None
                save_data(st.session_state.data); st.toast("🗑️ 已刪除"); time.sleep(0.5); st.rerun()
            
            def promote(wid, d):
                all_p = st.session_state.data["sessions"][d]
                w = next((p for p in all_p if p['id']==wid), None)
                tg = next((p for p in reversed(main) if not p.get('isMember') and next((x for x in all_p if x['id']==p['id']), None)), None) 
                tg_ref = next((p for p in all_p if p['id']==tg['id']), None) if tg else None

                if w and tg_ref:
                   cutoff = main[-1]['timestamp']
                   w['timestamp'] = tg_ref['timestamp'] - 1.0
                   tg_ref['timestamp'] = cutoff + 1.0
                   save_data(st.session_state.data); st.balloons(); st.toast("🎉 遞補成功！"); time.sleep(1); st.rerun()
                else: st.error("無可遞補對象")

            # === 報名表單 ===
            with st.expander("📝 點擊報名 / 規則說明", expanded=not is_locked):
                if is_locked and not is_admin: st.warning("⛔ 已截止")
                with st.form(f"f_{date_key}", clear_on_submit=True):
                    name = st.text_input("球員姓名", disabled=not can_edit, placeholder="輸入您的稱呼...")
                    c1, c2, c3 = st.columns(3)
                    im = c1.checkbox("⭐晴女", key=f"m_{date_key}", disabled=not can_edit)
                    bb = c2.checkbox("🏀帶球", key=f"b_{date_key}", disabled=not can_edit)
                    oc = c3.checkbox("🚩佔場", key=f"c_{date_key}", disabled=not can_edit)
                    tot = st.number_input("總人數 (含自己)", 1, 3, 1, key=f"t_{date_key}", disabled=not can_edit)
                    
                    if st.form_submit_button("送出報名", disabled=not can_edit, type="primary"):
                        if name:
                            ts = time.time()
                            new = [{"id":str(uuid.uuid4()),"name":name,"count":1,"isMember":im,"bringBall":bb,"occupyCourt":oc,"timestamp":ts}]
                            for k in range(tot-1): new.append({"id":str(uuid.uuid4()),"name":f"{name} (友{k+1})","count":1,"isMember":False,"bringBall":False,"occupyCourt":False,"timestamp":ts+0.1+(k*0.01)})
                            st.session_state.data["sessions"][date_key].extend(new)
                            save_data(st.session_state.data)
                            st.balloons() 
                            st.toast(f"🎉 歡迎 {name} 加入！", icon="🏀")
                            time.sleep(1.5)
                            st.rerun()
                        else: st.toast("❌ 請輸入姓名")

                st.info("""
                **📌 報名規則**
                * **人數上限**：每場20人，含自己最多報名3位，超過的進入候補名單。
                * **遞補規則**：候補名單中之 ⭐晴女，可優先遞補正選名單中之「非晴女」。
                * **修改/刪除**：若需「減少人數」或「修改屬性」，請直接點擊名單上的 ✏️ 或 ❌。
                * **增加人數**：若需「增加人數」，請重新填寫報名表，以維護公平性。
                * **截止時間**：開團前一日 18:00 截止報名，後續修改請通知管理員協助。
                * **雨備通知**：雨天當日 17:00 前通知是否開團。
                """)

            # === 名單顯示 ===
            def render_list(lst, is_wait=False):
                if not lst:
                    if not is_wait:
                        st.markdown("""<div style="text-align: center; padding: 30px; color: #cbd5e1;"><div style="font-size: 40px; margin-bottom: 10px;">🏀</div><p style="font-size: 0.9rem;">場地空蕩蕩...<br>快來當第一位！</p></div>""", unsafe_allow_html=True)
                    return

                for idx, p in enumerate(lst):
                    if st.session_state.edit_target == p['id']:
                        with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ 編輯中：{p['name']}</div>", unsafe_allow_html=True)
                            with st.form(key=f"e_{p['id']}"):
                                en = st.text_input("名", p['name'])
                                ec1, ec2, ec3 = st.columns(3)
                                em = ec1.checkbox("⭐晴女", p.get('isMember'))
                                eb = ec2.checkbox("🏀帶球", p.get('bringBall'))
                                ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'))
                                b1, b2 = st.columns(2)
                                if b1.form_submit_button("💾 儲存", type="primary"): update(p['id'], date_key, en, em, eb, ec)
                                if b2.form_submit_button("取消"): st.session_state.edit_target=None; st.rerun()
                    else:
                        badges = ""
                        if p.get('isMember'): badges += "<span class='badge badge-sunny'>晴女</span>"
                        if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
                        if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"
                        
                        bg_style = "background-color:#f8fafc;" if is_wait else ""
                        st.markdown(f'<div class="player-row" style="{bg_style}">', unsafe_allow_html=True)
                        
                        c_cfg = [6.5, 1, 1] if not (is_admin and is_wait) else [5, 1.5, 1, 1]
                        cols = st.columns(c_cfg)
                        
                        num_color = "#64748b" if is_wait else "#334155"
                        cols[0].markdown(f"<span class='list-text' style='color:{num_color}'>{idx+1}. {p['name']}</span> {badges}", unsafe_allow_html=True)
                        
                        b_idx = 1
                        if is_admin and is_wait and p.get('isMember'):
                            with cols[b_idx]:
                                st.markdown('<div class="list-btn-up">', unsafe_allow_html=True)
                                if st.button("⬆️遞補", key=f"up_{p['id']}"): promote(p['id'], date_key)
                                st.markdown('</div>', unsafe_allow_html=True)
                            b_idx += 1

                        if can_edit:
                            if b_idx < len(cols):
                                with cols[b_idx]:
                                    st.markdown('<div class="list-btn-col list-btn-e">', unsafe_allow_html=True)
                                    if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target=p['id']; st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)
                            if b_idx+1 < len(cols):
                                with cols[b_idx+1]:
                                    st.markdown('<div class="list-btn-col list-btn-d">', unsafe_allow_html=True)
                                    if st.button("❌", key=f"bd_{p['id']}"): delete(p['id'], date_key)
                                    st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

            render_list(main)
            
            if wait:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                st.subheader(f"⏳ 候補名單")
                render_list(wait, is_wait=True)
                
