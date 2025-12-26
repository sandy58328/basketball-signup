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
# 1. 資料庫連線 (Google Sheets)
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

if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'edit_target' not in st.session_state:
    st.session_state.edit_target = None

# ==========================================
# 2. UI 設定 (CSS)
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
    [data-testid="stSidebarCollapsedControl"] { display: block !important; visibility: visible !important; color: #334155 !important; background-color: white !important; border-radius: 50%; padding: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 999999 !important; }
    .header-box { background: white; padding: 1.5rem 1rem; border-radius: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; }
    .header-title { font-size: 1.6rem; font-weight: 800; color: #1e293b !important; letter-spacing: 1px; margin-bottom: 5px; }
    .header-sub { font-size: 0.9rem; color: #64748b !important; font-weight: 500; }
    .info-pill { background: #f1f5f9; padding: 4px 14px; border-radius: 30px; font-size: 0.8rem; font-weight: 600; color: #475569 !important; display: inline-block; margin-top: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] { height: 38px; background-color: transparent; border-radius: 20px; padding: 0 16px; font-size: 0.9rem; border: 1px solid transparent; color: #64748b !important; font-weight: 500; }
    .stTabs [aria-selected="true"] { background-color: white; color: #3b82f6 !important; border: none; box-shadow: 0 2px 6px rgba(0,0,0,0.04); font-weight: 700; }
    div[data-baseweb="tab-highlight"] { display: none !important; height: 0 !important; }
    div[data-baseweb="tab-border"] { display: none !important; }
    .player-row { background: white; border: 1px solid #f1f5f9; border-radius: 12px; padding: 8px 10px; margin-bottom: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); transition: transform 0.1s; display: flex; align-items: center; width: 100%; min-height: 40px; }
    .player-row:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    .list-index { color: #cbd5e1 !important; font-weight: 700; font-size: 0.9rem; margin-right: 12px; min-width: 20px; text-align: right;}
    .list-index-flower { color: #f472b6 !important; font-weight: 700; font-size: 1rem; margin-right: 12px; min-width: 20px; text-align: right;}
    .list-name { color: #334155 !important; font-weight: 700; font-size: 1.15rem; letter-spacing: 0.5px; flex-grow: 1; line-height: 1.2; }
    .badge { padding: 2px 6px; border-radius: 5px; font-size: 0.7rem; font-weight: 700; margin-left: 4px; display: inline-block; vertical-align: middle; transform: translateY(-1px);}
    .badge-sunny { background: #fffbeb; color: #d97706 !important; }
    .badge-ball { background: #fff7ed; color: #c2410c !important; }
    .badge-court { background: #eff6ff; color: #1d4ed8 !important; }
    .badge-visit { background: #fdf2f8; color: #db2777 !important; border: 1px solid #fce7f3; }
    .list-btn-col button { border: none !important; background: transparent !important; padding: 0px !important; color: #cbd5e1 !important; font-size: 14px !important; line-height: 1 !important; height: 32px !important; width: 32px !important; display: flex; justify-content: center; align-items: center; margin: 0 !important; }
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; border-radius: 6px; }
    .list-btn-d button { color: unset !important; opacity: 0.7; font-size: 12px !important; }
    .list-btn-d button:hover { opacity: 1; background: #fef2f2 !important; border-radius: 6px; }
    .list-btn-up button { padding: 0px 8px !important; height: 26px !important; font-size: 0.75rem !important; border-radius: 6px !important; background: #e0f2fe !important; color: #0284c7 !important; font-weight: 600 !important; width: auto !important; }
    .progress-container { width: 100%; background: #e2e8f0; border-radius: 6px; height: 6px; margin-top: 8px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
    .progress-info { display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748b !important; margin-bottom: 2px; font-weight: 600; }
    .edit-box { border: 1px solid #3b82f6; border-radius: 12px; padding: 12px; background: #eff6ff; margin-bottom: 10px; color: #334155 !important; }
    .rules-box { background-color: white; border-radius: 16px; padding: 20px; border: 1px solid #f1f5f9; box-shadow: 0 4px 15px rgba(0,0,0,0.02); margin-top: 15px; color: #475569 !important; }
    .rules-header { font-size: 1rem; font-weight: 800; color: #334155 !important; margin-bottom: 15px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; letter-spacing: 1px; }
    .rules-row { display: flex; align-items: flex-start; margin-bottom: 12px; }
    .rules-icon { font-size: 1.1rem; margin-right: 12px; line-height: 1.4; }
    .rules-content { font-size: 0.9rem; color: #64748b !important; line-height: 1.5; }
    .rules-content b { color: #475569 !important; font-weight: 700; }
    .rules-footer { margin-top: 15px; font-size: 0.85rem; color: #94a3b8 !important; text-align: right; font-weight: 500; }
    .stCode { font-family: monospace !important; font-size: 0.8rem !important; }
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
        
        # 1. 新增場次
        new_date = st.date_input("新增日期", min_value=date.today())
        if st.button("➕ 新增場次"):
            current_data = load_data() 
            if (d:=str(new_date)) not in current_data["sessions"]:
                current_data["sessions"][d] = []
                save_data(current_data)
                st.session_state.data = current_data
                st.rerun()
        st.markdown("---")
        
        st.session_state.data = load_data()
        dates = sorted(st.session_state.data["sessions"].keys())
        
        if dates:
            hidden = st.multiselect("隱藏場次", dates, default=[d for d in st.session_state.data["hidden"] if d in dates])
            if set(hidden) != set(st.session_state.data["hidden"]):
                st.session_state.data["hidden"] = hidden
                save_data(st.session_state.data)
                st.rerun()
            st.markdown("---")
            if st.button("🗑️ 刪除選定日期"):
               del_d = st.selectbox("選擇日期", dates)
               del st.session_state.data["sessions"][del_d]
               save_data(st.session_state.data)
               st.rerun()
        
        # [V4.5] 管理員也可以幫忙請假/刪除請假
        st.markdown("---")
        with st.expander("🛠️ 請假管理 (管理員)"):
            st.caption("這裡可以查看與刪除大家的假單")
            leaves_data = st.session_state.data.get("leaves", {})
            if leaves_data:
                for lname, ldates in leaves_data.items():
                    if ldates:
                        st.markdown(f"**{lname}**: {', '.join(ldates)}")
                        # 刪除功能
                        del_month = st.selectbox(f"刪除 {lname} 的假", ["請選擇"] + ldates, key=f"adm_del_{lname}")
                        if del_month != "請選擇":
                            if st.button("確認刪除", key=f"btn_del_{lname}"):
                                current_data = load_data()
                                if lname in current_data["leaves"] and del_month in current_data["leaves"][lname]:
                                    current_data["leaves"][lname].remove(del_month)
                                    save_data(current_data)
                                    st.rerun()
            else:
                st.info("目前無人請假")

        # 踢人統計 (含請假過濾)
        st.markdown("---")
        show_stats = st.checkbox("📊 出席統計 (含請假狀態)")
        if show_stats:
            st.info("計算中...")
            try:
                last_seen = {}
                all_sessions = st.session_state.data["sessions"]
                leaves_data = st.session_state.data.get("leaves", {})
                
                for d_str, p_list in all_sessions.items():
                    try:
                        d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
                    except: continue 
                    if d_obj <= date.today():
                        for p in p_list:
                            if "(友" not in p['name']:
                                name = p['name']
                                if name not in last_seen or d_obj > last_seen[name]:
                                    last_seen[name] = d_obj
                report_data = []
                today = date.today()
                
                for name, last_date in last_seen.items():
                    days_diff = (today - last_date).days
                    status = "🟢 活躍"
                    
                    is_on_leave = False
                    player_leaves = leaves_data.get(name, [])
                    check_months = [
                        today.strftime("%Y-%m"), 
                        (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m"),
                        (today.replace(day=1) - timedelta(days=40)).strftime("%Y-%m")
                    ]
                    for m in check_months:
                        if m in player_leaves:
                            is_on_leave = True
                            break
                    
                    if days_diff >= 60:
                        if is_on_leave: status = "🏖️ 請假中 (Pass)"
                        else: status = "🔴 踢出 (>60天)"
                    elif days_diff >= 30:
                        if is_on_leave: status = "🏖️ 請假中 (Pass)"
                        else: status = "🟡 觀察 (>30天)"
                    
                    report_data.append({"姓名": name,"最後出席": str(last_date),"未出席": days_diff,"狀態": status})
                
                report_data.sort(key=lambda x: x["未出席"], reverse=True)
                if report_data: st.dataframe(report_data, hide_index=True)
                else: st.warning("目前沒有足夠的歷史資料")
            except Exception as e:
                st.error(f"統計失敗: {e}")

st.markdown("""
    <div class="header-box">
        <div class="header-title">晴女☀️在場邊等妳🌈</div>
        <div class="header-sub">✨ Keep Playing, Keep Shining ✨</div>
        <div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 4. 主畫面邏輯
# ==========================================
st.session_state.data = load_data() 

# [V4.5] 自助請假區塊 (放在最上面)
with st.expander("🏖️ 我要請假 (長假登記)"):
    st.markdown("""
    <div style="font-size:0.9rem; color:#64748b; margin-bottom:10px;">
    若您預計<b>整個月</b>都無法出席，請在此登記，以免被列入踢人名單。<br>
    (請輸入您的名字，並選擇要請假的月份，選該月任意一天即可)
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("self_leave_form", clear_on_submit=True):
        col_l1, col_l2 = st.columns(2)
        l_name = col_l1.text_input("姓名 (需與報名名稱一致)")
        l_month = col_l2.date_input("請假月份", min_value=date.today())
        
        if st.form_submit_button("送出假單"):
            if l_name:
                leave_str = l_month.strftime("%Y-%m")
                current_data = load_data()
                
                # 初始化
                if "leaves" not in current_data: current_data["leaves"] = {}
                if l_name not in current_data["leaves"]: current_data["leaves"][l_name] = []
                
                # 檢查重複
                if leave_str not in current_data["leaves"][l_name]:
                    current_data["leaves"][l_name].append(leave_str)
                    save_data(current_data)
                    st.toast(f"✅ 已幫 {l_name} 登記 {leave_str} 請假！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning(f"{l_name} 已經登記過 {leave_str} 的假囉！")
            else:
                st.error("請輸入姓名")

# 下方顯示場次
all_dates = sorted(st.session_state.data["sessions"].keys())
hidden = st.session_state.data.get("hidden", [])
dates = all_dates if is_admin else [d for d in all_dates if d not in hidden]

if not dates:
    st.info("👋 目前沒有開放報名的場次，請稍後再來！")
else:
    tabs = st.tabs([f"{int(d.split('-')[1])}/{int(d.split('-')[2])}" + ("🔒" if d in hidden else "") for d in dates])

    for i, date_key in enumerate(dates):
        with tabs[i]:
            try:
                dt_obj = datetime.strptime(date_key, "%Y-%m-%d")
                deadline = (dt_obj - timedelta(days=1)).replace(hour=12, minute=0, second=0)
                is_locked = datetime.now() > deadline
            except: is_locked = False
            can_edit = is_admin or (not is_locked)

            players = sorted(st.session_state.data["sessions"][date_key], key=lambda x: x.get('timestamp', 0))
            main, wait = [], []
            curr = 0
            for p in players:
                p_count = p.get('count', 1) 
                if curr + p_count <= MAX_CAPACITY:
                    main.append(p)
                    curr += p_count
                else:
                    wait.append(p)

            # 統計與進度
            ball_count = len([p for p in main if p.get('bringBall')])
            court_count = len([p for p in main if p.get('occupyCourt')])
            pct = min(100, (curr / MAX_CAPACITY) * 100)
            bar_color = "#4ade80" if pct < 50 else "#fbbf24" if pct < 85 else "#f87171"
            
            st.markdown(f"""
            <div style="margin-bottom: 5px; padding: 0 4px;">
                <div class="progress-info">
                    <span style="color:#334155;">正選 ({curr}/{MAX_CAPACITY})</span>
                    <span style="color:#94a3b8; font-weight:400;">候補: {len(wait)}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {pct}%; background: {bar_color};"></div>
                </div>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 15px; font-size: 0.85rem; color: #64748b; margin-bottom: 25px; font-weight: 500; padding-right: 5px;">
                <span>🏀 帶球：<b style="color:#ea580c;">{ball_count}</b></span>
                <span>🚩 佔場：<b style="color:#2563eb;">{court_count}</b></span>
            </div>
            """, unsafe_allow_html=True)
            
            # Functions
            def update(pid, d, n, im, bb, oc, iv):
                current_data = load_data()
                t = next((p for p in current_data["sessions"][d] if p['id']==pid), None)
                if t: 
                    new_count = 0 if iv else 1
                    t.update({'name':n,'isMember':im,'bringBall':bb,'occupyCourt':oc, 'count': new_count})
                    save_data(current_data)
                    st.session_state.edit_target=None
                    st.toast("✅ 資料已更新")
                    time.sleep(0.5)
                    st.rerun()
            
            def delete(pid, d):
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
            
            def promote(wid, d):
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

            # 報名表單
            with st.expander("📝 點擊報名 / 規則說明", expanded=not is_locked):
                if is_locked and not is_admin: st.warning("⛔ 已截止")
                with st.form(f"f_{date_key}", clear_on_submit=True):
                    name = st.text_input("球員姓名", disabled=not can_edit, placeholder="輸入您的稱呼...")
                    st.caption("⚠️ 名字請務必與群組內一致，不符者將直接刪除")
                    
                    c1, c2, c3 = st.columns(3)
                    im = c1.checkbox("⭐晴女 (團員務必勾選)", key=f"m_{date_key}", disabled=not can_edit)
                    bb = c2.checkbox("🏀帶球", key=f"b_{date_key}", disabled=not can_edit)
                    oc = c3.checkbox("🚩佔場", key=f"c_{date_key}", disabled=not can_edit)
                    ev = st.checkbox("📣 不打球 (最美加油團)", key=f"v_{date_key}", disabled=not can_edit)
                    
                    tot = st.number_input("本次報名人數 (含自己, 上限3人)", 1, 3, 1, key=f"t_{date_key}", disabled=not can_edit)
                    
                    if st.form_submit_button("送出報名", disabled=not can_edit, type="primary"):
                        if name:
                            latest_data = load_data()
                            latest_players = latest_data["sessions"].get(date_key, [])
                            related_entries = [p for p in latest_players if p['name'] == name or p['name'].startswith(f"{name} (友")]
                            current_count = len(related_entries)
                            is_ok = False
                            error_message = None
                            
                            if current_count == 0:
                                if not im: error_message = "❌ 身份驗證失敗！第一次報名必須是「⭐晴女」團員本人。朋友不能單獨報名。"
                                else: is_ok = True
                            elif current_count > 0:
                                if im: error_message = f"❌ {name} 已有報名資料，加報朋友請勿重複勾選「⭐晴女」。"
                                elif ev: error_message = "❌ 朋友無法報名「📣最美加油團」，該選項僅限「⭐晴女」本人適用。"
                                elif current_count + tot > 3: error_message = f"❌ {name} 已有 {current_count} 筆報名，每人上限 3 位。"
                                else: is_ok = True
                            
                            if error_message: st.error(error_message)
                            elif is_ok:
                                ts = time.time()
                                new_entries_list = []
                                for k in range(tot):
                                    is_main = (k == 0) and (current_count == 0)
                                    if is_main:
                                        final_name = name
                                        p_im, p_bb, p_oc = im, bb, oc 
                                        p_count = 0 if ev else 1
                                    else:
                                        db_friend_count = len([p for p in latest_players if p['name'].startswith(f"{name} (友")])
                                        current_loop_friend_count = len([n for n in new_entries_list if n['name'].startswith(f"{name} (友")])
                                        friend_seq = db_friend_count + current_loop_friend_count + 1
                                        final_name = f"{name} (友{friend_seq})"
                                        p_im, p_bb, p_oc = False, False, False 
                                        p_count = 1 
                                    
                                    new_entries_list.append({"id": str(uuid.uuid4()),"name": final_name,"count": p_count,"isMember": p_im,"bringBall": p_bb,"occupyCourt": p_oc,"timestamp": ts + 0.1 + (k * 0.01)})
                                
                                latest_data["sessions"][date_key].extend(new_entries_list)
                                save_data(latest_data)
                                st.balloons()
                                st.toast(f"🎉 歡迎 {name} 加入！", icon="🏀")
                                time.sleep(1.5)
                                st.rerun()
                        else: st.toast("❌ 請輸入姓名")

                st.markdown("""
                <div class="rules-box">
                    <div class="rules-header">📌 報名須知</div>
                    <div class="rules-row"><span class="rules-icon">🔴</span><div class="rules-content"><b>資格與規範</b>：採實名制 (需與群組名一致)。僅限 <b>⭐晴女</b> 報名，朋友不可單獨報名 (需由團員帶入)。<b>欲事後補報朋友，請用原名再次填寫即可</b> (含自己上限3位)。</div></div>
                    <div class="rules-row"><span class="rules-icon">🟡</span><div class="rules-content"><b>📣最美加油團</b>：團員若「不打球但帶朋友」請勾此項。本人不佔名額，但朋友會佔打球名額。</div></div>
                    <div class="rules-row"><span class="rules-icon">🟢</span><div class="rules-content"><b>優先與遞補</b>：正選 20 人。候補名單中之 <b>⭐晴女</b>，享有優先遞補「非晴女」之權利。</div></div>
                    <div class="rules-row"><span class="rules-icon">🔵</span><div class="rules-content"><b>時間與修改</b>：截止於前一日 12:00、雨備於當日 17:00 通知。僅能修改勾選項目。</div></div>
                    <div class="rules-footer">有任何問題請找最美管理員們 ❤️</div>
                </div>
                """, unsafe_allow_html=True)

            # 名單
            st.subheader("🏀 報名名單")
            def render_list(lst, is_wait=False):
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
                                if b1.form_submit_button("💾 儲存", type="primary"): update(p['id'], date_key, en, em, eb, ec, ev)
                                if b2.form_submit_button("取消"): st.session_state.edit_target=None; st.rerun()
                    else:
                        badges = ""
                        if p.get('count') == 0: badges += "<span class='badge badge-visit'>📣加油團</span>"
                        if p.get('isMember'): badges += "<span class='badge badge-sunny'>晴女</span>"
                        if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
                        if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"

                        c_cfg = [7.8, 0.6, 0.6, 1.0] if not (is_admin and is_wait) else [6.5, 1.2, 0.6, 0.6, 1.1]
                        cols = st.columns(c_cfg, gap="small")
                        with cols[0]:
                            st.markdown(f"""<div class="player-row"><span class="{idx_class}">{index_str}</span><span class="list-name">{p['name']}</span>{badges}</div>""", unsafe_allow_html=True)
                        
                        b_idx = 1
                        if is_admin and is_wait and p.get('isMember'):
                            with cols[b_idx]:
                                st.markdown('<div class="list-btn-up">', unsafe_allow_html=True)
                                if st.button("⬆️", key=f"up_{p['id']}"): promote(p['id'], date_key)
                                st.markdown('</div>', unsafe_allow_html=True)
                            b_idx += 1

                        if can_edit:
                            if b_idx < len(cols):
                                # 朋友不顯示編輯按鈕，只顯示刪除
                                is_friend = "(友" in p['name']
                                if not is_friend:
                                    with cols[b_idx]:
                                        st.markdown('<div class="list-btn-col list-btn-e">', unsafe_allow_html=True)
                                        if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target=p['id']; st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)
                            if b_idx+1 < len(cols):
                                with cols[b_idx+1]:
                                    st.markdown('<div class="list-btn-col list-btn-d">', unsafe_allow_html=True)
                                    if st.button("❌", key=f"bd_{p['id']}"): delete(p['id'], date_key)
                                    st.markdown('</div>', unsafe_allow_html=True)

            render_list(main)
            if wait:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                st.subheader(f"⏳ 候補名單")
                render_list(wait, is_wait=True)
