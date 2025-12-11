import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import uuid
import random
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
# 2. UI 旗艦級美學 (CSS)
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="centered") 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; background-color: #f8fafc; } /* 背景極淡灰，襯托白色卡片 */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 5rem !important; }
    #MainMenu, footer { visibility: hidden; }

    /* Header: 懸浮玻璃質感 */
    .header-box {
        background: white;
        padding: 1.5rem 1rem; border-radius: 24px; color: #1e293b; 
        text-align: center; margin-bottom: 20px;
        box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08); /* 高級柔光陰影 */
    }
    .header-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; letter-spacing: 0.5px; margin-bottom: 4px; }
    .header-sub { font-size: 0.85rem; color: #64748b; font-weight: 500; }
    .info-pill {
        background: #eff6ff; padding: 4px 12px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600; color: #3b82f6;
        display: inline-block; margin-top: 10px;
    }

    /* Tabs: 極簡線條風 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 10px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 36px; background-color: transparent; border-radius: 18px;
        padding: 0 14px; font-size: 0.85rem; border: 1px solid transparent; color: #64748b; font-weight: 600;
    }
    .stTabs [aria-selected="true"] { 
        background-color: white; color: #3b82f6; border: none; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); /* 微微浮起 */
    }

    /* =========================================
       ✨ 核心美學：無框線列表 (Modern List)
       ========================================= */
    .player-row {
        background: white;
        border: none; /* ❌ 去掉框線 */
        border-radius: 16px;
        padding: 10px 10px 10px 16px; 
        margin-bottom: 6px; /* 每個人的間距 */
        display: flex; align-items: center; /* 垂直置中 */
        box-shadow: 0 2px 10px rgba(148, 163, 184, 0.08); /* ☁️ 像雲一樣的陰影 */
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .player-row:hover {
        transform: scale(1.005);
        box-shadow: 0 5px 15px rgba(148, 163, 184, 0.15);
    }

    /* 頭像 (Avatar) */
    .avatar {
        width: 32px; height: 32px; border-radius: 50%;
        background: linear-gradient(135deg, #60a5fa, #a78bfa);
        color: white; font-size: 14px; font-weight: bold;
        display: flex; align-items: center; justify-content: center;
        margin-right: 12px; box-shadow: 0 2px 5px rgba(96, 165, 250, 0.3);
        flex-shrink: 0;
    }
    
    /* 名字與序號 */
    .list-index { font-size: 0.8rem; color: #94a3b8; font-weight: 600; margin-right: 8px; width: 15px; text-align:right;}
    .list-name { font-size: 0.95rem; font-weight: 600; color: #334155; flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* Badges (更精緻的膠囊) */
    .badge { padding: 2px 8px; border-radius: 10px; font-size: 0.65rem; font-weight: 700; margin-left: 4px; display: inline-block; vertical-align: middle; }
    .badge-sunny { background: #fffbeb; color: #d97706; }
    .badge-ball { background: #fff7ed; color: #c2410c; }
    .badge-court { background: #eff6ff; color: #1d4ed8; }

    /* 按鈕區 */
    [data-testid="stHorizontalBlock"] { align-items: center !important; }
    .list-btn-col button {
        border: none !important; background: transparent !important;
        padding: 6px !important; color: #cbd5e1 !important;
    }
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; border-radius: 50%; }
    .list-btn-d button:hover { color: #ef4444 !important; background: #fef2f2 !important; border-radius: 50%; }
    .list-btn-up button { padding: 2px 8px !important; min-height: 24px !important; font-size: 0.7rem !important; border-radius: 12px !important;}

    /* Progress Bar */
    .progress-wrapper { background: white; padding: 10px 15px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
    .progress-container { width: 100%; background: #f1f5f9; border-radius: 6px; height: 6px; margin-top: 6px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 6px; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
    .progress-text { font-size: 0.8rem; color: #64748b; display: flex; justify-content: space-between; font-weight: 600; }

    /* Edit Box */
    .edit-box { border: 2px solid #3b82f6; border-radius: 16px; padding: 12px; background: #fff; margin-bottom: 12px; box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15); }
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
        <div class="header-title">☀️ Sunny Girls</div>
        <div class="header-sub">Keep Playing, Keep Shining.</div>
        <div class="info-pill">🏀 朱崙公園 19:00</div>
    </div>
""", unsafe_allow_html=True)

components.html(
    f"""<body style="margin:0;display:flex;justify-content:center;"><button style="background:white;border:none;border-radius:20px;padding:8px 20px;font-size:12px;cursor:pointer;color:#64748b;font-weight:600;display:flex;align-items:center;gap:6px;box-shadow:0 2px 10px rgba(0,0,0,0.05);transition:all 0.2s;" onclick="navigator.clipboard.writeText('{APP_URL}').then(()=>{{document.getElementById('t').innerText='已複製!'}});this.style.transform='scale(0.95)'">🔗 <span id="t">分享報名連結</span></button></body>""", height=40
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
    # 建立 Tabs (極簡風)
    tabs = st.tabs([f"{int(d.split('-')[1])}/{int(d.split('-')[2])}" + ("🔒" if d in hidden else "") for d in dates])

    for i, date_key in enumerate(dates):
        with tabs[i]:
            try:
                dt_obj = datetime.strptime(date_key, "%Y-%m-%d")
                deadline = (dt_obj - timedelta(days=1)).replace(hour=18, minute=0, second=0)
                is_locked = datetime.now() > deadline
            except: is_locked = False
            can_edit = is_admin or (not is_locked)

            players = sorted(st.session_state.data["sessions"][date_key], key=lambda x: x.get('timestamp', 0))
            main, wait = [], []
            curr = 0
            for p in players:
                if curr + p.get('count', 1) <= MAX_CAPACITY: main.append(p); curr += p.get('count', 1)
                else: wait.append(p)

            # === 進度條 (包在白色卡片裡) ===
            pct = min(100, (len(main) / MAX_CAPACITY) * 100)
            bar_color = "#4ade80" if pct < 50 else "#fbbf24" if pct < 85 else "#f87171"
            
            st.markdown(f"""
            <div class="progress-wrapper">
                <div class="progress-text">
                    <span style="color:#334155;">正選名單</span>
                    <span style="color:#3b82f6;">{len(main)} / {MAX_CAPACITY}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {pct}%; background: {bar_color};"></div>
                </div>
                <div style="text-align:right; font-size:0.7rem; color:#94a3b8; margin-top:6px; font-weight:500;">
                    候補人數: {len(wait)}
                </div>
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
                        st.markdown("""<div style="text-align: center; padding: 40px; color: #94a3b8; opacity:0.6;"><div style="font-size: 40px; margin-bottom: 10px;">🏀</div><p style="font-size: 0.9rem; font-weight:500;">場地空蕩蕩...<br>快來當第一位！</p></div>""", unsafe_allow_html=True)
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
                        # 產生頭像字元
                        avatar_char = p['name'][0] if p['name'] else "?"
                        
                        badges = ""
                        if p.get('isMember'): badges += "<span class='badge badge-sunny'>晴女</span>"
                        if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
                        if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"
                        
                        # 容器與樣式 (無邊框！)
                        opacity = "0.7" if is_wait else "1"
                        st.markdown(f"""
                        <div class="player-row" style="opacity:{opacity};">
                            <span class="list-index">{idx+1}.</span>
                            <div class="avatar">{avatar_char}</div>
                            <div style="flex-grow:1; min-width:0;">
                                <div style="display:flex; align-items:center;">
                                    <span class="list-name">{p['name']}</span>
                                    {badges}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 按鈕邏輯 (透過 columns 來對齊按鈕)
                        # 注意：這裡我用了一個小技巧，在 markdown 下面接 columns
                        # 為了讓按鈕跟上面的 div 在同一行，其實 Streamlit 很難做到完美的同一行
                        # 但因為上面的 div 已經結束了，我們這裡用 columns 只是為了放按鈕
                        # 在視覺上，我建議把按鈕放在獨立的 column，透過 st.columns 來切分整行
                        
                        # 重寫結構：用 columns 包住所有內容
                        
                # 重新設計渲染邏輯以確保對齊
                for idx, p in enumerate(lst):
                     if st.session_state.edit_target == p['id']:
                         # (編輯模式代碼略...同上)
                         with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ 編輯中：{p['name']}</div>", unsafe_allow_html=True)
                            with st.form(key=f"e2_{p['id']}"):
                                en = st.text_input("名", p['name'])
                                ec1, ec2, ec3 = st.columns(3)
                                em = ec1.checkbox("⭐晴女", p.get('isMember'))
                                eb = ec2.checkbox("🏀帶球", p.get('bringBall'))
                                ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'))
                                b1, b2 = st.columns(2)
                                if b1.form_submit_button("💾 儲存", type="primary"): update(p['id'], date_key, en, em, eb, ec)
                                if b2.form_submit_button("取消"): st.session_state.edit_target=None; st.rerun()
                     else:
                        avatar_char = p['name'][0] if p['name'] else "?"
                        badges = ""
                        if p.get('isMember'): badges += "<span class='badge badge-sunny'>晴女</span>"
                        if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
                        if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"

                        # 使用 Flex Container 概念的 HTML 結構 (上層)
                        # 因為 Streamlit 的 Button 不能放進 HTML，所以我們還是得用 Columns
                        # 這裡調整 Columns 比例來達到無框線列表的感覺
                        
                        # 行容器樣式
                        bg = "background:white;" if not is_wait else "background:#f8fafc;"
                        st.markdown(f'<div class="player-row" style="{bg}">', unsafe_allow_html=True)
                        
                        # 佈局：[序號+頭像+名字+標籤]  [按鈕]
                        c_cfg = [7.5, 1, 1] if not (is_admin and is_wait) else [6, 1.5, 1, 1]
                        c = st.columns(c_cfg)
                        
                        # 左側資訊區
                        with c[0]:
                            st.markdown(f"""
                            <div style="display:flex; align-items:center;">
                                <span class="list-index">{idx+1}</span>
                                <div class="avatar">{avatar_char}</div>
                                <div style="display:flex; flex-direction:column; justify-content:center;">
                                    <div style="display:flex; align-items:center;">
                                        <span class="list-name">{p['name']}</span>
                                        {badges}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # 右側按鈕區
                        b_idx = 1
                        if is_admin and is_wait and p.get('isMember'):
                            with c[b_idx]:
                                st.markdown('<div class="list-btn-up">', unsafe_allow_html=True)
                                if st.button("⬆️", key=f"up_{p['id']}"): promote(p['id'], date_key)
                                st.markdown('</div>', unsafe_allow_html=True)
                            b_idx += 1
                        
                        if can_edit:
                            if b_idx < len(c):
                                with c[b_idx]:
                                    st.markdown('<div class="list-btn-col list-btn-e">', unsafe_allow_html=True)
                                    if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target=p['id']; st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)
                            if b_idx+1 < len(c):
                                with c[b_idx+1]:
                                    st.markdown('<div class="list-btn-col list-btn-d">', unsafe_allow_html=True)
                                    if st.button("✕", key=f"bd_{p['id']}"): delete(p['id'], date_key)
                                    st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True) # End player-row

            render_list(main)
            
            if wait:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                st.subheader(f"⏳ 候補名單")
                render_list(wait, is_wait=True)
