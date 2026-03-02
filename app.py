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
# 2. 功能工具箱
# ==========================================
def update_player(pid, d, n, im, bb, oc, iv):
    current_data = load_data()
    t = next((p for p in current_data["sessions"][d] if p['id']==pid), None)
    if t: 
        final_im = False if "友" in n else im
        new_count = 0 if iv else 1
        t.update({'name':n,'isMember':final_im,'bringBall':bb,'occupyCourt':oc, 'count': new_count})
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
        if "友" in target_name:
            current_data["sessions"][d] = [p for p in current_data["sessions"][d] if p['id'] != pid]
        else:
            current_data["sessions"][d] = [
                p for p in current_data["sessions"][d] 
                if p['id'] != pid and not (p['name'].startswith(f"{target_name} (友") or p['name'].startswith(f"{target_name} （友") or p['name'] == f"{target_name}之友")
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
    tg = next((p for p in reversed(_main) if "友" in p['name'] and next((x for x in current_data["sessions"][d] if x['id']==p['id']), None)), None) 
    if w and tg:
       tg_ref = next((p for p in current_data["sessions"][d] if p['id']==tg['id']), None)
       cutoff = _main[-1]['timestamp']
       w['timestamp'] = tg_ref['timestamp'] - 1.0
       tg_ref['timestamp'] = cutoff + 1.0
       save_data(current_data)
       st.balloons(); st.toast("🎉 遞補成功！"); time.sleep(2); st.rerun()
    else: st.error("無可遞補對象")

def render_list(lst, date_key, is_wait=False, can_edit_global=True, is_admin_mode=False):
    if not lst:
        if not is_wait: st.markdown("""<div style="text-align: center; padding: 40px; color: #cbd5e1; opacity:0.8;"><div style="font-size: 36px; margin-bottom: 8px;">🏀</div><p style="font-size: 0.85rem; font-weight:500;">場地空蕩蕩...<br>快來當第一位！</p></div>""", unsafe_allow_html=True)
        return
    for idx, p in enumerate(lst):
        is_f = p.get('count', 1) > 0
        idx_str = f"{idx+1}." if is_f else "🌸"
        idx_cls = "list-index" if is_f else "list-index-flower"
        if st.session_state.edit_target == p['id']:
            with st.container():
                st.markdown(f"<div class='edit-box'>✏️ 正在編輯：{p['name']}</div>", unsafe_allow_html=True)
                with st.form(key=f"e_{p['id']}"):
                    en = st.text_input("姓名 (不可修改)", p['name'], disabled=True)
                    ec1, ec2, ec3 = st.columns(3)
                    is_friend = "友" in p['name']
                    em = ec1.checkbox("⭐晴女", p.get('isMember'), disabled=True)
                    eb = ec2.checkbox("🏀帶球", p.get('bringBall'), disabled=is_friend)
                    ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'), disabled=is_friend)
                    ev = st.checkbox("📣 不打球 (加油團)", p.get('count') == 0, disabled=is_friend)
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 儲存", type="primary"): update_player(p['id'], date_key, en, em, eb, ec, ev)
                    if b2.form_submit_button("取消"): st.session_state.edit_target = None; st.rerun()
        else:
            badges = ""
            if p.get('count') == 0: badges += "<span class='badge badge-visit'>📣加油團</span>"
            if p.get('isMember') and "友" not in p['name']: 
                badges += "<span class='badge badge-sunny'>晴女</span>"
            if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
            if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"
            
            c_cfg = [7.5, 0.6, 0.6, 1.3] if not (is_admin_mode and is_wait) else [6.0, 1.2, 0.6, 0.6, 1.6]
            cols = st.columns(c_cfg, gap="small")
            with cols[0]:
                st.markdown(f"""<div class="player-row"><span class="{idx_cls}">{idx_str}</span><span class="list-name">{p['name']}</span>{badges}</div>""", unsafe_allow_html=True)
            b_idx = 1
            if is_admin_mode and is_wait and p.get('isMember'):
                with cols[b_idx]:
                    if st.button("⬆️", key=f"up_{p['id']}"): promote_player(wid=p['id'], d=date_key)
                b_idx += 1
            if can_edit_global:
                if b_idx < len(cols):
                    if "友" not in p['name']:
                        with cols[b_idx]:
                            if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target = p['id']; st.rerun()
                if b_idx+1 < len(cols):
                    with cols[b_idx+1]:
                        with st.popover("❌"):
                            st.write("確定取消報名嗎？")
                            if st.button("確認刪除", key=f"conf_del_{p['id']}", type="primary"):
                                delete_player(pid=p['id'], d=date_key)

# ==========================================
# 3. 初始化 & CSS
# ==========================================
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'edit_target' not in st.session_state: st.session_state.edit_target = None

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
    .rules-row { display: flex; align-items: flex-start; margin-bottom: 12px; }
    .rules-icon { font-size: 1.1rem; margin-right: 12px; line-height: 1.4; }
    .rules-content { font-size: 0.9rem; color: #64748b !important; line-height: 1.5; }
    .rules-content b { color: #475569 !important; font-weight: 700; }
    .rules-footer { margin-top: 15px; font-size: 0.85rem; color: #94a3b8 !important; text-align: right; font-weight: 500; }
    
    button[data-testid="stBaseButton-secondary"] { width: 100% !important; height: 32px !important; padding: 0 !important;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 主畫面內容
# ==========================================
st.markdown("""<div class="header-box"><div class="header-title">晴女☀️在場邊等妳🌈</div><div class="header-sub">✨ Keep Playing, Keep Shining ✨</div><div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div></div>""", unsafe_allow_html=True)
st.session_state.data = load_data()

# 請假與公報
c_l1, c_l2 = st.columns(2)
with c_l1:
    with st.expander("🏖️ 我要請假 (長假登記)"):
        with st.form("l_form", clear_on_submit=True):
            n = st.text_input("姓名")
            m = st.date_input("請假月份")
            if st.form_submit_button("送出假單") and n:
                cur = load_data(); s = m.strftime("%Y-%m")
                if n not in cur["leaves"]: cur["leaves"][n] = []
                if s not in cur["leaves"][n]: cur["leaves"][n].append(s); save_data(cur); st.toast("✅ 已登記"); time.sleep(1); st.rerun()

with c_l2:
    with st.expander("📜 休假公報", expanded=False):
        l_d = st.session_state.data.get("leaves", {})
        if any(l_d.values()):
            # --- 智能化大小寫合併邏輯 ---
            comb_l = {}
            n_map = {}
            for o_n, mons in l_d.items():
                low_n = o_n.lower()
                if low_n not in comb_l:
                    comb_l[low_n] = set()
                    n_map[low_n] = o_n
                comb_l[low_n].update(mons)
            
            for low_n in sorted(comb_l.keys()):
                disp_n = n_map[low_n]
                m_list = sorted(list(comb_l[low_n]))
                col_i, col_m = st.columns([0.8, 0.2])
                with col_i:
                    st.markdown(f"**👤 {disp_n}**: {', '.join(m_list)}")
                with col_m:
                    with st.popover("🗑️"):
                        st.write(f"管理 {disp_n} 的假單：")
                        # 處理正常有月份的刪除
                        for m_i in m_list:
                            if st.button(f"刪除 {m_i}", key=f"dl_{low_n}_{m_i}"):
                                cur = load_data()
                                for ok in list(cur["leaves"].keys()):
                                    if ok.lower() == low_n and m_i in cur["leaves"][ok]:
                                        cur["leaves"][ok].remove(m_i)
                                        if not cur["leaves"][ok]: del cur["leaves"][ok]
                                save_data(cur); st.toast(f"🗑️ 已移除 {m_i}"); time.sleep(0.5); st.rerun()
                        # --- 🚨 新增：針對「R:」這種無月份異常紀錄的保險按鈕 ---
                        st.divider()
                        if st.button("🚨 強制刪除此人", key=f"f_dl_{low_n}", type="secondary"):
                            cur = load_data()
                            for ok in list(cur["leaves"].keys()):
                                if ok.lower() == low_n: del cur["leaves"][ok]
                            save_data(cur); st.toast("🗑️ 已強制移除"); time.sleep(0.5); st.rerun()
        else: st.info("目前無人請假")

# 場次顯示
all_d = sorted(st.session_state.data["sessions"].keys())
h_d = st.session_state.data.get("hidden", [])
dates = [d for d in all_d if d not in h_d]

if not dates: st.info("👋 目前沒有開放報名的場次")
else:
    tabs = st.tabs([f"{int(d.split('-')[1])}/{int(d.split('-')[2])}" for d in dates])
    for i, dk in enumerate(dates):
        with tabs[i]:
            try:
                dt = datetime.strptime(dk, "%Y-%m-%d")
                locked = datetime.now() > (dt - timedelta(days=1)).replace(hour=12, minute=0)
            except: locked = False
            can_edit = st.session_state.is_admin or (not locked)
            p_l = sorted(st.session_state.data["sessions"][dk], key=lambda x: x.get('timestamp', 0))
            main, wait, curr = [], [], 0
            for p in p_l:
                if curr + p.get('count', 1) <= MAX_CAPACITY: main.append(p); curr += p.get('count', 1)
                else: wait.append(p)
            
            b_c = len([x for x in main if x.get('bringBall')])
            c_c = len([x for x in main if x.get('occupyCourt')])
            pct = min(100, (curr/MAX_CAPACITY)*100)
            
            # --- 精確修復 275 行語法錯誤 ---
            c_code = '#4ade80' if pct < 50 else '#fbbf24' if pct < 85 else '#f87171'
            p_html = f'<div class="progress-info"><span>正選 ({curr}/{MAX_CAPACITY})</span><span>候補: {len(wait)}</span></div>'
            b_html = f'<div class="progress-container"><div class="progress-bar" style="width: {pct}%; background: {c_code};"></div></div>'
            s_html = f'<div style="display: flex; justify-content: flex-end; gap: 15px; font-size: 0.85rem; color: #64748b; margin-bottom: 25px; font-weight: 500; padding-right: 5px;"><span>🏀 帶球：<b>{b_c}</b></span><span>🚩 佔場：<b>{c_c}</b></span></div>'
            st.markdown(f'<div style="margin-bottom: 5px; padding: 0 4px;">{p_html}{b_html}</div>{s_html}', unsafe_allow_html=True)

            with st.expander("📝 點擊報名 / 規則說明", expanded=not locked):
                if locked and not st.session_state.is_admin: st.warning("⛔ 已截止報名")
                with st.form(f"f_{dk}", clear_on_submit=True):
                    name = st.text_input("球員姓名", disabled=not can_edit)
                    c1, c2, c3 = st.columns(3)
                    im = c1.checkbox("⭐晴女", key=f"m_{dk}", disabled=not can_edit)
                    bb = c2.checkbox("🏀帶球", key=f"b_{dk}", disabled=not can_edit)
                    oc = c3.checkbox("🚩佔場", key=f"c_{dk}", disabled=not can_edit)
                    ev = st.checkbox("📣 不打球 (加油團)", key=f"v_{dk}", disabled=not can_edit)
                    tot = st.number_input("報名人數", 1, 3, 1, key=f"t_{dk}", disabled=not can_edit)
                    if st.form_submit_button("送出報名", disabled=not can_edit, type="primary"):
                        if "友" in name:
                            st.error("❌ 請輸入『團員姓名』並使用下方『報名人數』來幫朋友報名。")
                        elif name:
                            lat = load_data(); cur_p = lat["sessions"].get(dk, [])
                            rel = [x for x in cur_p if x['name'] == name or x['name'].startswith(f"{name} (友") or x['name'].startswith(f"{name} （友") or x['name'] == f"{name}之友"]
                            if not rel and not im: st.error("❌ 第一次報名需勾選「⭐晴女」")
                            elif rel and im: st.error("❌ 加報朋友請勿重複勾選晴女")
                            elif len(rel) + tot > 3: st.error("❌ 每人上限 3 位")
                            else:
                                ts = time.time(); new_li = []
                                for k in range(tot):
                                    is_m = (k==0 and not [x for x in cur_p if x['name']==name])
                                    fn = name if is_m else f"{name} (友{len(rel)+k})"
                                    new_li.append({"id": str(uuid.uuid4()),"name": fn,"count": (0 if ev and is_m else 1),"isMember": (im if is_m else False),"bringBall": (bb if is_m else False),"occupyCourt": (oc if is_m else False),"timestamp": ts + (k*0.01)})
                                lat["sessions"][dk].extend(new_li); save_data(lat); st.balloons(); st.toast("🎉 報名成功！"); time.sleep(2); st.rerun()

                st.markdown("""
                <div class="rules-box">
                    <div class="rules-header">📌 報名須知</div>
                    <div class="rules-row"><span class="rules-icon">🔴</span><div class="rules-content"><b>資格與規範</b>：採實名制。僅限 <b>⭐晴女</b> 報名。欲事後補報朋友，請用原名再次填寫即可 (含自己上限3位)。</div></div>
                    <div class="rules-row"><span class="rules-icon">🟡</span><div class="rules-content"><b>📣加油團</b>：團員若「不打球但帶朋友」請勾此項。本人不佔名額，但朋友會佔打球名額。</div></div>
                    <div class="rules-row"><span class="rules-icon">🟢</span><div class="rules-content"><b>遞補機制</b>：正選 20 人。候補名單中之 <b>⭐晴女</b>，享有優先遞補「非晴女」之權利。</div></div>
                    <div class="rules-footer">有任何問題請找最美管理員們 ❤️</div>
                </div>
                """, unsafe_allow_html=True)

            st.subheader("🏀 報名名單")
            render_list(main, dk, False, can_edit, st.session_state.is_admin)
            if wait:
                st.markdown("<br>", unsafe_allow_html=True); st.subheader("⏳ 候補名單")
                render_list(wait, dk, True, can_edit, st.session_state.is_admin)

# ==========================================
# 5. 管理員專區
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True); st.divider()
st.markdown("<div style='text-align: center; color: #cbd5e1; font-size: 0.8rem;'>▼ 管理員專用通道 ▼</div>", unsafe_allow_html=True)
with st.expander("⚙️ 管理員專區 (Admin)", expanded=st.session_state.is_admin):
    if not st.session_state.is_admin:
        if st.text_input("密碼", key="admin_pwd_input", type="password") == ADMIN_PASSWORD: st.session_state.is_admin = True; st.rerun()
    else:
        if st.button("登出"): st.session_state.is_admin = False; st.rerun()
        st.subheader("管理功能")
        nd = st.date_input("新增日期")
        if st.button("新增場次"):
            cur = load_data()
            if str(nd) not in cur["sessions"]: cur["sessions"][str(nd)] = []; save_data(cur); st.rerun()
        all_s = sorted(st.session_state.data["sessions"].keys())
        if all_s:
            del_s = st.selectbox("刪除場次", all_s)
            if st.button("確認刪除"):
                cur = load_data(); del cur["sessions"][del_s]; save_data(cur); st.rerun()
            h_s = st.multiselect("隱藏場次", all_s, default=st.session_state.data.get("hidden", []))
            if st.button("更新隱藏"):
                cur = load_data(); cur["hidden"] = h_s; save_data(cur); st.rerun()
        st.subheader("出席統計")
        if st.button("📊 產生報表"):
            try:
                ls = {}; d_m = st.session_state.data
                for ds, pl in d_m["sessions"].items():
                    do = datetime.strptime(ds, "%Y-%m-%d").date()
                    if do <= date.today():
                        for p in pl:
                            if "友" not in p['name']:
                                if p['name'] not in ls or do > ls[p['name']]: ls[p['name']] = do
                rep = []
                for n, do in ls.items():
                    df = (date.today() - do).days
                    onl = any(m in d_m["leaves"].get(n, []) for m in [date.today().strftime("%Y-%m")])
                    rep.append({"姓名": n, "最後出席": str(do), "未出席天數": df, "狀態": "🏖️ 請假" if onl else "🔴 警告" if df > 60 else "🟢 活躍"})
                st.table(rep)
            except: st.error("統計失敗")

        st.divider()
        if st.button("🧹 一鍵清洗現有錯誤標籤"):
            cur = load_data()
            count = 0
            for dk in cur["sessions"]:
                for p in cur["sessions"][dk]:
                    if "友" in p['name'] and p.get('isMember'):
                        p['isMember'] = False
                        count += 1
            save_data(cur); st.success(f"清洗完成！共修正 {count} 筆。"); time.sleep(2); st.rerun()
