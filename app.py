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

# ==========================================
# 1. 資料庫與連線 (先定義好基本功)
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
    except Exception:
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
    except Exception:
        st.error("❌ 儲存失敗，請重整頁面")

# ==========================================
# 2. 名單渲染函數 (【關鍵】放在最上方防止 NameError)
# ==========================================
def render_list(lst, dk, is_wait=False, can_edit=True, is_adm=False):
    if not lst:
        if not is_wait: st.markdown("""<div style="text-align: center; padding: 40px; color: #cbd5e1; opacity:0.8;"><div style="font-size: 36px; margin-bottom: 8px;">🏀</div><p style="font-size: 0.85rem; font-weight:500;">目前無人報名</p></div>""", unsafe_allow_html=True)
        return
    
    for idx, p in enumerate(lst):
        # 判斷是否為加油團 (加油團 count 為 0)
        is_f = p.get('count', 1) > 0
        idx_str, idx_cls = (f"{idx+1}.", "list-index") if is_f else ("🌸", "list-index-flower")
        
        # 編輯模式
        if st.session_state.get('edit_target') == p['id']:
            with st.form(key=f"e_{p['id']}"):
                en = st.text_input("球員姓名", p['name'], disabled=True)
                is_friend = "(友" in p['name']
                c1, c2, c3 = st.columns(3)
                eb = c2.checkbox("🏀帶球", p.get('bringBall'), disabled=is_friend)
                ec = c3.checkbox("🚩佔場", p.get('occupyCourt'), disabled=is_friend)
                ev = st.checkbox("📣加油團", p.get('count') == 0, disabled=is_friend)
                if st.form_submit_button("💾 儲存"):
                    current_data = load_data()
                    t = next((x for x in current_data["sessions"][dk] if x['id']==p['id']), None)
                    if t:
                        t.update({'bringBall':eb,'occupyCourt':ec, 'count': 0 if ev else 1})
                        save_data(current_data)
                        st.session_state.edit_target = None
                        st.rerun()
                if st.form_submit_button("取消"):
                    st.session_state.edit_target = None
                    st.rerun()
        else:
            # 一般顯示模式
            badges = ""
            if p.get('count') == 0: badges += "<span class='badge badge-visit'>📣加油團</span>"
            if p.get('isMember'): badges += "<span class='badge badge-sunny'>晴女</span>"
            if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
            if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"
            
            # 手機版欄位配置
            cols = st.columns([7.5, 1.0, 1.0, 1.0] if not (is_adm and is_wait) else [6.5, 1.2, 1.0, 1.0, 1.0], gap="small")
            cols[0].markdown(f"""<div class="player-row"><span class="{idx_cls}">{idx_str}</span><span class="list-name">{p['name']}</span>{badges}</div>""", unsafe_allow_html=True)
            
            b_idx = 1
            if is_adm and is_wait and p.get('isMember'):
                if cols[b_idx].button("⬆️", key=f"up_{p['id']}"):
                    current_data = load_data()
                    pl = sorted(current_data["sessions"][dk], key=lambda x: x.get('timestamp', 0))
                    main_p, curr = [], 0
                    for x in pl:
                        if curr + x.get('count', 1) <= MAX_CAPACITY: main_p.append(x); curr += x.get('count', 1)
                    target_move = next((x for x in current_data["sessions"][dk] if x['id']==p['id']), None)
                    target_swap = next((x for x in reversed(main_p) if not x.get('isMember')), None)
                    if target_move and target_swap:
                        ts_ref = next((x for x in current_data["sessions"][dk] if x['id']==target_swap['id']), None)
                        target_move['timestamp'], ts_ref['timestamp'] = ts_ref['timestamp'] - 1.0, main_p[-1]['timestamp'] + 1.0
                        save_data(current_data); st.balloons(); st.rerun()
                b_idx += 1
            
            if can_edit:
                if b_idx < len(cols) and "(友" not in p['name']:
                    if cols[b_idx].button("✏️", key=f"be_{p['id']}"):
                        st.session_state.edit_target = p['id']; st.rerun()
                if b_idx+1 < len(cols):
                    if cols[b_idx+1].button("❌", key=f"bd_{p['id']}"):
                        current_data = load_data()
                        tn = p['name']
                        if "(友" in tn: current_data["sessions"][dk] = [x for x in current_data["sessions"][dk] if x['id'] != p['id']]
                        else: current_data["sessions"][dk] = [x for x in current_data["sessions"][dk] if x['id'] != p['id'] and not x['name'].startswith(f"{tn} (友")]
                        save_data(current_data); st.toast("🗑️ 已刪除"); time.sleep(0.5); st.rerun()

# ==========================================
# 3. 初始化 Session & CSS
# ==========================================
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'edit_target' not in st.session_state: st.session_state.edit_target = None

st.set_page_config(page_title="晴女籃球報名", page_icon="☀️", layout="centered") 
st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');[data-testid="stAppViewContainer"]{background-color:#f8fafc!important;color:#334155!important}html,body,[class*="css"],p,div,label,span,h1,h2,h3,.stMarkdown{font-family:'Noto Sans TC',sans-serif;color:#334155!important}.block-container{padding-top:4rem!important;padding-bottom:5rem!important}header{background:transparent!important}[data-testid="stDecoration"],[data-testid="stToolbar"],[data-testid="stStatusWidget"],footer,#MainMenu,.stDeployButton{display:none!important}[data-testid="stSidebarCollapsedControl"]{display:none!important}.header-box{background:white;padding:1.5rem 1rem;border-radius:20px;text-align:center;margin-bottom:20px;box-shadow:0 4px 20px rgba(0,0,0,.03);border:1px solid #f1f5f9}.header-title{font-size:1.6rem;font-weight:800;color:#1e293b!important;letter-spacing:1px;margin-bottom:5px}.header-sub{font-size:.9rem;color:#64748b!important;font-weight:500}.info-pill{background:#f1f5f9;padding:4px 14px;border-radius:30px;font-size:.8rem;font-weight:600;color:#475569!important;display:inline-block;margin-top:10px}.stTabs [data-baseweb="tab-list"]{gap:8px;margin-bottom:10px}.stTabs [data-baseweb="tab"]{height:38px;background-color:transparent;border-radius:20px;padding:0 16px;font-size:.9rem;border:1px solid transparent;color:#64748b!important;font-weight:500}.stTabs [aria-selected="true"]{background-color:white;color:#3b82f6!important;border:none;box-shadow:0 2px 6px rgba(0,0,0,.04);font-weight:700}div[data-baseweb="tab-highlight"],div[data-baseweb="tab-border"]{display:none!important}.player-row{background:white;border:1px solid #f1f5f9;border-radius:12px;padding:8px 10px;margin-bottom:8px;box-shadow:0 2px 5px rgba(0,0,0,.03);display:flex;align-items:center;width:100%;min-height:40px}.list-index{color:#cbd5e1!important;font-weight:700;font-size:.9rem;margin-right:12px;min-width:20px;text-align:right}.list-index-flower{color:#f472b6!important;font-weight:700;font-size:1rem;margin-right:12px;min-width:20px;text-align:right}.list-name{color:#334155!important;font-weight:700;font-size:1.15rem;flex-grow:1;line-height:1.2}.badge{padding:2px 6px;border-radius:5px;font-size:.7rem;font-weight:700;margin-left:4px;display:inline-block;vertical-align:middle}.badge-sunny{background:#fffbeb;color:#d97706!important}.badge-ball{background:#fff7ed;color:#c2410c!important}.badge-court{background:#eff6ff;color:#1d4ed8!important}.badge-visit{background:#fdf2f8;color:#db2777!important;border:1px solid #fce7f3}.progress-container{width:100%;background:#e2e8f0;border-radius:6px;height:6px;margin-top:8px;overflow:hidden}.progress-bar{height:100%;border-radius:6px;transition:width .6s ease}.progress-info{display:flex;justify-content:space-between;font-size:.8rem;color:#64748b!important;margin-bottom:2px;font-weight:600}.rules-box{background-color:white;border-radius:16px;padding:20px;border:1px solid #f1f5f9;box-shadow:0 4px 15px rgba(0,0,0,.02);margin-top:15px}.rules-header{font-size:1rem;font-weight:800;color:#334155!important;margin-bottom:15px;border-bottom:2px solid #f1f5f9;padding-bottom:8px}.rules-row{display:flex;align-items:flex-start;margin-bottom:12px}.rules-icon{font-size:1.1rem;margin-right:12px;line-height:1.4}.rules-content{font-size:.9rem;color:#64748b!important;line-height:1.5}.rules-content b{color:#475569!important;font-weight:700}.rules-footer{margin-top:15px;font-size:.85rem;color:#94a3b8!important;text-align:right;font-weight:500}</style>""", unsafe_allow_html=True)

# ==========================================
# 4. 主畫面抬頭
# ==========================================
st.markdown("""<div class="header-box"><div class="header-title">晴女☀️在場邊等妳🌈</div><div class="header-sub">✨ Keep Playing, Keep Shining ✨</div><div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div></div>""", unsafe_allow_html=True)
st.session_state.data = load_data()

# 請假與公報
c_l1, c_l2 = st.columns(2)
with c_l1:
    with st.expander("🏖️ 我要請假 (長假登記)"):
        with st.form("h_form", clear_on_submit=True):
            n = st.text_input("球員姓名")
            m = st.date_input("請假月份", min_value=date.today())
            if st.form_submit_button("送出假單") and n:
                cur = load_data(); s = m.strftime("%Y-%m")
                if n not in cur["leaves"]: cur["leaves"][n] = []
                if s not in cur["leaves"][n]: cur["leaves"][n].append(s); save_data(cur); st.toast("✅ 已登記"); time.sleep(1); st.rerun()
with c_l2:
    with st.expander("📜 休假公報"):
        ld = st.session_state.data.get("leaves", {})
        has_any = False
        for k, v in ld.items():
            if v: has_any = True; st.markdown(f"👤 **{k}**: {', '.join(sorted(v))}")
        if not has_any: st.info("目前無人請長假")

# ==========================================
# 5. 場次 Tab 系統
# ==========================================
all_d, h_d = sorted(st.session_state.data["sessions"].keys()), st.session_state.data.get("hidden", [])
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
            can_e = st.session_state.is_admin or (not locked)
            
            pl = sorted(st.session_state.data["sessions"][dk], key=lambda x: x.get('timestamp', 0))
            main_p, wait_p, curr = [], [], 0
            for p in pl:
                if curr + p.get('count', 1) <= MAX_CAPACITY: main_p.append(p); curr += p.get('count', 1)
                else: wait_p.append(p)
            
            b_c, c_c = len([x for x in main_p if x.get('bringBall')]), len([x for x in main_p if x.get('occupyCourt')])
            pct = min(100, (curr/MAX_CAPACITY)*100)
            st.markdown(f"""<div style="margin-bottom: 5px; padding: 0 4px;"><div class="progress-info"><span>正選 ({curr}/{MAX_CAPACITY})</span><span>候補: {len(wait_p)}</span></div><div class="progress-container"><div class="progress-bar" style="width: {pct}%; background: {'#4ade80' if pct < 50 else '#fbbf24' if pct < 85 else '#f87171'};"></div></div></div><div style="display: flex; justify-content: flex-end; gap: 15px; font-size: 0.85rem; color: #64748b; margin-bottom: 25px; font-weight: 500; padding-right: 5px;"><span>🏀 帶球：<b>{b_c}</b></span><span>🚩 佔場：<b>{c_c}</b></span></div>""", unsafe_allow_html=True)
            
            with st.expander("📝 點擊報名 / 規則說明", expanded=not locked):
                if locked and not st.session_state.is_admin: st.warning("⛔ 已截止報名")
                with st.form(f"f_{dk}", clear_on_submit=True):
                    nm = st.text_input("球員姓名", disabled=not can_e)
                    c1, c2, c3 = st.columns(3)
                    im, bb, oc = c1.checkbox("⭐晴女", key=f"m_{dk}", disabled=not can_e), c2.checkbox("🏀帶球", key=f"b_{dk}", disabled=not can_e), c3.checkbox("🚩佔場", key=f"c_{dk}", disabled=not can_e)
                    ev = st.checkbox("📣加油團", key=f"v_{dk}", disabled=not can_e)
                    tot = st.number_input("報名人數", 1, 3, 1, key=f"t_{dk}", disabled=not can_e)
                    if st.form_submit_button("送出報名", disabled=not can_e, type="primary"):
                        if nm:
                            lat = load_data(); cur_ps = lat["sessions"].get(dk, [])
                            rel = [x for x in cur_ps if x['name'] == nm or x['name'].startswith(f"{nm} (友")]
                            if not rel and not im: st.error("❌ 第一次報名需勾選「⭐晴女」")
                            elif rel and im: st.error("❌ 加報朋友請勿重複勾選晴女")
                            elif len(rel) + tot > 3: st.error("❌ 每人上限 3 位")
                            else:
                                ts, new_li = time.time(), []
                                for k in range(tot):
                                    is_m = (k==0 and not rel)
                                    fn = nm if is_m else f"{nm} (友{len(rel)+k+1})"
                                    new_li.append({"id": str(uuid.uuid4()),"name": fn,"count": (0 if ev and is_m else 1),"isMember": (im if is_m else False),"bringBall": (bb if is_m else False),"occupyCourt": (oc if is_m else False),"timestamp": ts + (k*0.01)})
                                lat["sessions"][dk].extend(new_li); save_data(lat); st.balloons(); st.rerun()
                st.markdown("""<div class="rules-box"><div class="rules-header">📌 報名須知</div><div class="rules-row"><span class="rules-icon">🔴</span><div class="rules-content"><b>資格與規範</b>：採實名制 (需與群組名一致)。僅限 <b>⭐晴女</b> 報名，朋友不可單獨報名 (需由團員帶入)。欲事後補報朋友，請用原名再次填寫即可 (含自己上限3位)。</div></div><div class="rules-row"><span class="rules-icon">🟡</span><div class="rules-content"><b>📣最美加油團</b>：團員若「不打球但帶朋友」請勾此項。本人不佔名額，但朋友會佔打球名額。</div></div><div class="rules-row"><span class="rules-icon">🟢</span><div class="rules-content"><b>優先與遞補</b>：正選 20 人。候補名單中之 <b>⭐晴女</b>，享有優先遞補「非晴女」之權利。</div></div><div class="rules-row"><span class="rules-icon">🔵</span><div class="rules-content"><b>時間與修改</b>：截止於前一日 12:00、雨備於當日 17:00 通知。僅能修改勾選項目。</div></div><div class="rules-footer">有任何問題請找最美管理員們 ❤️</div></div>""", unsafe_allow_html=True)
            
            st.subheader("🏀 報名名單")
            render_list(main_p, dk, False, can_e, st.session_state.is_admin)
            if wait_p:
                st.markdown("<br>", unsafe_allow_html=True); st.subheader("⏳ 候補名單"); render_list(wait_p, dk, True, can_e, st.session_state.is_admin)

# ==========================================
# 6. 管理員專區 (置底)
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True); st.divider()
st.markdown("<div style='text-align: center; color: #cbd5e1; font-size: 0.8rem;'>▼ 管理員專用通道 ▼</div>", unsafe_allow_html=True)

with st.expander("⚙️ 管理員登入 (Admin Login)", expanded=st.session_state.is_admin):
    if not st.session_state.is_admin:
        adm_input = st.text_input("管理員密碼", type="password")
        if st.button("確認登入"):
            if adm_input == ADMIN_PASSWORD: st.session_state.is_admin = True; st.rerun()
            else: st.error("密碼不正確")
    else:
        if st.button("👋 登出管理模式"): st.session_state.is_admin = False; st.rerun()
        
        st.subheader("1. 場次日期管理")
        nd = st.date_input("新增場次日期", min_value=date.today())
        if st.button("➕ 新增場次"):
            cur = load_data(); 
            if str(nd) not in cur["sessions"]: cur["sessions"][str(nd)] = []; save_data(cur); st.rerun()
        all_ss = sorted(st.session_state.data["sessions"].keys())
        if all_ss:
            ds = st.selectbox("選擇要刪除的場次", all_ss)
            if st.button("🗑️ 確定刪除此日期"):
                cur = load_data(); del cur["sessions"][ds]; save_data(cur); st.rerun()
            hs = st.multiselect("隱藏場次 (不公開)", all_ss, default=st.session_state.data.get("hidden", []))
            if st.button("💾 更新隱藏設定"):
                cur = load_data(); cur["hidden"] = hs; save_data(cur); st.rerun()

        # 【重點】強迫顯示的請假管理清單
        st.divider()
        st.subheader("2. 請假管理 (管理員專用)")
        l_data = st.session_state.data.get("leaves", {})
        recs = []
        for name, months in l_data.items():
            for m in months: recs.append({"name": name, "month": m})
        
        if recs:
            st.info(f"系統目前共有 {len(recs)} 筆請假資料")
            for r in recs:
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"👤 **{r['name']}**：{r['month']}")
                if c2.button("刪除", key=f"del_{r['name']}_{r['month']}"):
                    cur = load_data()
                    if r['name'] in cur["leaves"]:
                        cur["leaves"][r['name']].remove(r['month'])
                        if not cur["leaves"][r['name']]: del cur["leaves"][r['name']]
                        save_data(cur); st.rerun()
        else:
            st.warning("⚠️ 警告：目前後台抓不到請假資料，請確認上方公報是否有顯示人名。")

        st.divider()
        st.subheader("3. 出席統計")
        if st.button("📊 產生出席報表"):
            try:
                ls, dm = {}, st.session_state.data; today = date.today()
                for ds, pl in dm["sessions"].items():
                    d_obj = datetime.strptime(ds, "%Y-%m-%d").date()
                    if d_obj <= today:
                        for p in pl:
                            if "(友" not in p['name'] and (p['name'] not in ls or d_obj > ls[p['name']]): ls[p['name']] = d_obj
                rep = []
                for n, do in ls.items():
                    df = (today - do).days
                    onl = any(m in dm["leaves"].get(n, []) for m in [today.strftime("%Y-%m")])
                    stt = "🏖️ 請假" if onl else "🔴 警告" if df > 60 else "🟢 活躍"
                    rep.append({"姓名": n, "最後出席": str(do), "未出席": df, "狀態": stt})
                st.dataframe(rep, hide_index=True)
            except: st.error("統計失敗")
