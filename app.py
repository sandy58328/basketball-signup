import streamlit as st
import json
import time
import uuid
from datetime import datetime, date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 0. 設定區
# ==========================================
ADMIN_PASSWORD = "sunny"
SHEET_NAME = "basketball_db" 
MAX_CAPACITY = 20
APP_URL = "https://sunny-girls-basketball.streamlit.app" 

# ==========================================
# 1. 資料庫連線與資料處理
# ==========================================
@st.cache_resource
def get_db_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1 
        return sheet
    except Exception as e:
        st.error(f"❌ 資料庫連線失敗：{e}")
        return None

def load_data():
    sheet = get_db_connection()
    if not sheet: return {"sessions": {}, "hidden": [], "leaves": {}}
    try:
        data_str = sheet.acell('A1').value
        if not data_str: return {"sessions": {}, "hidden": [], "leaves": {}}
        data = json.loads(data_str)
        # 自動補齊欄位
        if "leaves" not in data: data["leaves"] = {}
        if "sessions" not in data: data["sessions"] = {}
        if "hidden" not in data: data["hidden"] = []
        return data
    except:
        return {"sessions": {}, "hidden": [], "leaves": {}}

def save_data(data):
    sheet = get_db_connection()
    if not sheet: return
    try:
        sheet.update_acell('A1', json.dumps(data, ensure_ascii=False))
    except Exception as e:
        st.error(f"❌ 資料儲存失敗：{e}")

# ==========================================
# 2. 功能工具箱 (先定義好，避免 NameError)
# ==========================================
def update_player(pid, d, n, im, bb, oc, iv):
    current_data = load_data()
    t = next((p for p in current_data["sessions"][d] if p['id']==pid), None)
    if t: 
        new_count = 0 if iv else 1
        t.update({'name':n,'isMember':im,'bringBall':bb,'occupyCourt':oc, 'count': new_count})
        save_data(current_data)
        st.session_state.edit_target = None
        st.toast("✅ 資料已更新")
        time.sleep(0.5)
        st.rerun()

def delete_player(pid, d):
    current_data = load_data()
    target = next((p for p in current_data["sessions"][d] if p['id'] == pid), None)
    if target:
        target_name = target['name']
        if "(友" in target_name:
            current_data["sessions"][d] = [p for p in current_data["sessions"][d] if p['id'] != pid]
        else:
            current_data["sessions"][d] = [
                p for p in current_data["sessions"][d] 
                if p['id'] != pid and not p['name'].startswith(f"{target_name} (友")
            ]
        if st.session_state.edit_target == pid: st.session_state.edit_target = None
        save_data(current_data)
        st.toast("🗑️ 已刪除")
        time.sleep(0.5)
        st.rerun()

def promote_player(wid, d):
    current_data = load_data()
    _players = sorted(current_data["sessions"][d], key=lambda x: x.get('timestamp', 0))
    _main, _ = [], []
    _c = 0
    for _p in _players:
        if _c + _p.get('count', 1) <= MAX_CAPACITY: _main.append(_p); _c += _p.get('count', 1)
    
    w = next((p for p in current_data["sessions"][d] if p['id']==wid), None)
    tg = next((p for p in reversed(_main) if not p.get('isMember') and next((x for x in current_data["sessions"][d] if x['id']==p['id']), None)), None) 
    
    if w and tg:
       tg_ref = next((p for p in current_data["sessions"][d] if p['id']==tg['id']), None)
       cutoff = _main[-1]['timestamp']
       w['timestamp'] = tg_ref['timestamp'] - 1.0
       tg_ref['timestamp'] = cutoff + 1.0
       save_data(current_data)
       st.balloons()
       st.toast("🎉 遞補成功！")
       time.sleep(1)
       st.rerun()
    else: st.error("無可遞補對象")

def render_list(lst, date_key, is_wait=False, can_edit_global=True, is_admin_mode=False):
    if not lst:
        if not is_wait: st.markdown("""<div style="text-align: center; padding: 40px; color: #cbd5e1; opacity:0.8;"><div style="font-size: 36px; margin-bottom: 8px;">🏀</div><p style="font-size: 0.85rem; font-weight:500;">場地空蕩蕩...<br>快來當第一位！</p></div>""", unsafe_allow_html=True)
        return

    display_counter = 0
    for idx, p in enumerate(lst):
        if p.get('count', 1) > 0:
            display_counter += 1
            index_str = f"{display_counter}."
            idx_class = "list-index"
        else:
            index_str = "🌸"
            idx_class = "list-index-flower"

        if st.session_state.edit_target == p['id']:
            with st.container():
                st.markdown(f"<div class='edit-box'>✏️ 正在編輯：{p['name']}</div>", unsafe_allow_html=True)
                with st.form(key=f"e_{p['id']}"):
                    en = st.text_input("姓名 (不可修改)", p['name'], disabled=True)
                    ec1, ec2, ec3 = st.columns(3)
                    is_friend = "(友" in p['name']
                    if is_friend: em = ec1.checkbox("⭐晴女", False, disabled=True)
                    else: em = ec1.checkbox("⭐晴女", p.get('isMember'), disabled=True)
                    eb = ec2.checkbox("🏀帶球", p.get('bringBall'), disabled=is_friend)
                    ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'), disabled=is_friend)
                    ev = st.checkbox("📣 不打球 (最美加油團)", p.get('count') == 0, disabled=is_friend)
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 儲存", type="primary"): update_player(p['id'], date_key, en, em, eb, ec, ev)
                    if b2.form_submit_button("取消"): st.session_state.edit_target = None; st.rerun()
        else:
            badges = ""
            if p.get('count') == 0: badges += "<span class='badge badge-visit'>📣加油團</span>"
            if p.get('isMember'): badges += "<span class='badge badge-sunny'>晴女</span>"
            if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
            if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"

            # 動態調整欄位比例
            c_cfg = [7.8, 0.6, 0.6, 1.0] if not (is_admin_mode and is_wait) else [6.5, 1.2, 0.6, 0.6, 1.1]
            cols = st.columns(c_cfg, gap="small")
            
            with cols[0]:
                st.markdown(f"""<div class="player-row"><span class="{idx_class}">{index_str}</span><span class="list-name">{p['name']}</span>{badges}</div>""", unsafe_allow_html=True)
            
            b_idx = 1
            if is_admin_mode and is_wait and p.get('isMember'):
                with cols[b_idx]:
                    if st.button("⬆️", key=f"up_{p['id']}"): promote_player(p['id'], date_key)
                b_idx += 1

            if can_edit_global:
                if b_idx < len(cols):
                    is_friend = "(友" in p['name']
                    if not is_friend:
                        with cols[b_idx]:
                            if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target = p['id']; st.rerun()
                if b_idx+1 < len(cols):
                    with cols[b_idx+1]:
                        if st.button("❌", key=f"bd_{p['id']}"): delete_player(p['id'], date_key)

# ==========================================
# 3. 初始化 Session State
# ==========================================
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'edit_target' not in st.session_state:
    st.session_state.edit_target = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# ==========================================
# 4. UI 設定 (CSS)
# ==========================================
st.set_page_config(page_title="晴女籃球報名", page_icon="☀️", layout="centered") 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; color: #334155 !important; }
    html, body, [class*="css"], p, div, label, span, h1, h2, h3, .stMarkdown { font-family: 'Noto Sans TC', sans-serif; color: #334155 !important; }
    .block-container { padding-top: 4rem !important; padding-bottom: 5rem !important; }
    header {background: transparent !important;}
    [data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stStatusWidget"], footer, #MainMenu, .stDeployButton {display: none !important;}
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }

    .header-box { background: white; padding: 1.5rem 1rem; border-radius: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; }
    .header-title { font-size: 1.6rem; font-weight: 800; color: #1e293b !important; letter-spacing: 1px; margin-bottom: 5px; }
    .header-sub { font-size: 0.9rem; color: #64748b !important; font-weight: 500; }
    .info-pill { background: #f1f5f9; padding: 4px 14px; border-radius: 30px; font-size: 0.8rem; font-weight: 600; color: #475569 !important; display: inline-block; margin-top: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] { height: 38px; background-color: transparent; border-radius: 20px; padding: 0 16px; font-size: 0.9rem; border: 1px solid transparent; color: #64748b !important; font-weight: 500; }
    .stTabs [aria-selected="true"] { background-color: white; color: #3b82f6 !important; border: none; box-shadow: 0 2px 6px rgba(0,0,0,0.04); font-weight: 700; }
    div[data-baseweb="tab-highlight"] { display: none !important; height: 0 !important; }
    div[data-baseweb="tab-border"] { display: none !important; }
    .player-row { background: white; border: 1px solid #f1f5f9; border-radius: 12px; padding: 8px 10px; margin-bottom: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); display: flex; align-items: center; width: 100%; min-height: 40px; }
    .list-index { color: #cbd5e1 !important; font-weight: 700; font-size: 0.9rem; margin-right: 12px; min-width: 20px; text-align: right;}
    .list-index-flower { color: #f472b6 !important; font-weight: 700; font-size: 1rem; margin-right: 12px; min-width: 20px; text-align: right;}
    .list-name { color: #334155 !important; font-weight: 700; font-size: 1.15rem; flex-grow: 1; line-height: 1.2; }
    .badge { padding: 2px 6px; border-radius: 5px; font-size: 0.7rem; font-weight: 700; margin-left: 4px; display: inline-block; vertical-align: middle; }
    .badge-sunny { background: #fffbeb; color: #d97706 !important; }
    .badge-ball { background: #fff7ed; color: #c2410c !important; }
    .badge-court { background: #eff6ff; color: #1d4ed8 !important; }
    .badge-visit { background: #fdf2f8; color: #db2777 !important; border: 1px solid #fce7f3; }
    .progress-container { width: 100%; background: #e2e8f0; border-radius: 6px; height: 6px; margin-top: 8px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
    .progress-info { display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748b !important; margin-bottom: 2px; font-weight: 600; }
    .edit-box { border: 1px solid #3b82f6; border-radius: 12px; padding: 12px; background: #eff6ff; margin-bottom: 10px; }
    .rules-box { background-color: white; border-radius: 16px; padding: 20px; border: 1px solid #f1f5f9; box-shadow: 0 4px 15px rgba(0,0,0,0.02); margin-top: 15px; }
    .rules-header { font-size: 1rem; font-weight: 800; color: #334155 !important; margin-bottom: 15px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. 主畫面標頭
# ==========================================
st.markdown("""
    <div class="header-box">
        <div class="header-title">晴女☀️在場邊等妳🌈</div>
        <div class="header-sub">✨ Keep Playing, Keep Shining ✨</div>
        <div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div>
    </div>
""", unsafe_allow_html=True)

# 重新載入最新資料
st.session_state.data = load_data()

# ==========================================
# 6. 請假系統 (自助登記與休假公報)
# ==========================================
col_leave1, col_leave2 = st.columns(2)

with col_leave1:
    with st.expander("🏖️ 我要請假 (長假登記)"):
        with st.form("self_leave_form", clear_on_submit=True):
            l_name = st.text_input("姓名 (需與報名名稱一致)")
            l_month = st.date_input("請假月份", min_value=date.today())
            if st.form_submit_button("送出假單"):
                if l_name:
                    leave_str = l_month.strftime("%Y-%m")
                    current_data = load_data()
                    if l_name not in current_data["leaves"]: current_data["leaves"][l_name] = []
                    if leave_str not in current_data["leaves"][l_name]:
                        current_data["leaves"][l_name].append(leave_str)
                        save_data(current_data)
                        st.toast(f"✅ 已幫 {l_name} 登記 {leave_str} 請假")
                        time.sleep(1); st.rerun()
                    else: st.warning("該月已登記過")
                else: st.error("請輸入姓名")

with col_leave2:
    with st.expander("📜 休假公報 (已登記名單)"):
        leaves_data = st.session_state.data.get("leaves", {})
        active_leaves = {n: d for n, d in leaves_data.items() if d}
        if active_leaves:
            for player, months in active_leaves.items():
                st.markdown(f"**👤 {player}**")
                st.caption(f"📅 請假月份: {', '.join(sorted(months))}")
        else:
            st.info("目前尚無團員請長假中")

# ==========================================
# 7. 場次 Tab 系統
# ==========================================
all_dates = sorted(st.session_state.data["sessions"].keys())
hidden = st.session_state.data.get("hidden", [])
dates = [d for d in all_dates if d not in hidden]

if not dates:
    st.info("👋 目前沒有開放報名的場次，請稍後再來！")
else:
    tabs = st.tabs([f"{int(d.split('-')[1])}/{int(d.split('-')[2])}" for d in dates])

    for i, date_key in enumerate(dates):
        with tabs[i]:
            try:
                dt_obj = datetime.strptime(date_key, "%Y-%m-%d")
                deadline = (dt_obj - timedelta(days=1)).replace(hour=12, minute=0, second=0)
                is_locked = datetime.now() > deadline
            except: is_locked = False
            
            # 管理員權限或未截止即可編輯
            can_edit_global = st.session_state.is_admin or (not is_locked)

            players = sorted(st.session_state.data["sessions"][date_key], key=lambda x: x.get('timestamp', 0))
            main, wait = [], []
            curr = 0
            for p in players:
                p_count = p.get('count', 1) 
                if curr + p_count <= MAX_CAPACITY: main.append(p); curr += p_count
                else: wait.append(p)

            # 統計數據
            ball_count = len([p for p in main if p.get('bringBall')])
            court_count = len([p for p in main if p.get('occupyCourt')])
            pct = min(100, (curr / MAX_CAPACITY) * 100)
            bar_color = "#4ade80" if pct < 50 else "#fbbf24" if pct < 85 else "#f87171"
            
            st.markdown(f"""
            <div style="margin-bottom: 5px; padding: 0 4px;">
                <div class="progress-info"><span style="color:#334155;">正選 ({curr}/{MAX_CAPACITY})</span><span style="color:#94a3b8; font-weight:400;">候補: {len(wait)}</span></div>
                <div class="progress-container"><div class="progress-bar" style="width: {pct}%; background: {bar_color};"></div></div>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 15px; font-size: 0.85rem; color: #64748b; margin-bottom: 25px; font-weight: 500; padding-right: 5px;">
                <span>🏀 帶球：<b style="color:#ea580c;">{ball_count}</b></span><span>🚩 佔場：<b style="color:#2563eb;">{court_count}</b></span>
            </div>
            """, unsafe_allow_html=True)

            # 報名規則區
            with st.expander("📝 點擊報名 / 規則說明", expanded=not is_locked):
                if is_locked and not st.session_state.is_admin: st.warning("⛔ 已截止報名")
                with st.form(f"f_{date_key}", clear_on_submit=True):
                    name = st.text_input("球員姓名", disabled=not can_edit_global)
                    c1, c2, c3 = st.columns(3)
                    im = c1.checkbox("⭐晴女", key=f"m_{date_key}", disabled=not can_edit_global)
                    bb = c2.checkbox("🏀帶球", key=f"b_{date_key}", disabled=not can_edit_global)
                    oc = c3.checkbox("🚩佔場", key=f"c_{date_key}", disabled=not can_edit_global)
                    ev = st.checkbox("📣 不打球 (加油團)", key=f"v_{date_key}", disabled=not can_edit_global)
                    tot = st.number_input("報名人數 (含自己)", 1, 3, 1, key=f"t_{date_key}", disabled=not can_edit_global)
                    
                    if st.form_submit_button("送出報名", disabled=not can_edit_global, type="primary"):
                        if name:
                            latest_data = load_data()
                            latest_players = latest_data["sessions"].get(date_key, [])
                            related = [p for p in latest_players if p['name'] == name or p['name'].startswith(f"{name} (友")]
                            
                            if len(related) == 0 and not im: st.error("❌ 第一次報名需勾選「⭐晴女」")
                            elif len(related) > 0 and im: st.error("❌ 已報名過，加報朋友請勿重複勾選晴女")
                            elif len(related) + tot > 3: st.error("❌ 每人上限 3 位")
                            else:
                                ts = time.time()
                                new_list = []
                                for k in range(tot):
                                    is_main = (k == 0) and (len(related) == 0)
                                    final_n = name if is_main else f"{name} (友{len(related)+k+1})"
                                    new_list.append({"id": str(uuid.uuid4()),"name": final_n,"count": (0 if ev and is_main else 1),"isMember": (im if is_main else False),"bringBall": (bb if is_main else False),"occupyCourt": (oc if is_main else False),"timestamp": ts + (k*0.01)})
                                latest_data["sessions"][date_key].extend(new_list)
                                save_data(latest_data)
                                st.balloons(); st.rerun()
                        else: st.toast("❌ 請輸入姓名")

                st.markdown("""<div class="rules-box"><div class="rules-header">📌 報名須知</div><div class="rules-content">1. 採實名制，僅限晴女報名。<br>2. 截止於前一日 12:00。<br>3. 正選 20 人，團員享有優先遞補權。</div></div>""", unsafe_allow_html=True)

            # 渲染名單
            render_list(main, date_key, is_wait=False, can_edit_global=can_edit_global, is_admin_mode=st.session_state.is_admin)
            if wait:
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("⏳ 候補名單")
                render_list(wait, date_key, is_wait=True, can_edit_global=can_edit_global, is_admin_mode=st.session_state.is_admin)

# ==========================================
# 8. 管理員專區 (置底)
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("<div style='text-align: center; color: #cbd5e1; font-size: 0.8rem;'>▼ 管理員專用通道 ▼</div>", unsafe_allow_html=True)

with st.expander("⚙️ 管理員專區 (Admin)", expanded=st.session_state.is_admin):
    if not st.session_state.is_admin:
        adm_pwd = st.text_input("密碼", type="password")
        if adm_pwd == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
    else:
        if st.button("登出管理模式"):
            st.session_state.is_admin = False
            st.rerun()
        
        # 場次新增
        st.subheader("新增場次")
        c1, c2 = st.columns([3, 1])
        nd = c1.date_input("選擇日期")
        if c2.button("新增"):
            cur = load_data()
            if str(nd) not in cur["sessions"]:
                cur["sessions"][str(nd)] = []
                save_data(cur); st.rerun()

        # 出席統計
        st.subheader("出席統計")
        if st.button("📊 產生報表"):
            try:
                ls = {}
                data = st.session_state.data
                for d_s, p_l in data["sessions"].items():
                    d_o = datetime.strptime(d_s, "%Y-%m-%d").date()
                    if d_o <= date.today():
                        for p in p_l:
                            if "(友" not in p['name']:
                                if p['name'] not in ls or d_o > ls[p['name']]: ls[p['name']] = d_o
                rep = []
                for n, d_o in ls.items():
                    diff = (date.today() - d_o).days
                    on_l = any(m in data["leaves"].get(n, []) for m in [date.today().strftime("%Y-%m")])
                    rep.append({"姓名": n, "最後出席": str(d_o), "未出席天數": diff, "狀態": "🏖️ 請假" if on_l else "🔴 警告" if diff > 60 else "🟢 活躍"})
                st.table(rep)
            except: st.error("統計失敗")
