import streamlit as st
import json
import time
import uuid
import re
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

# 姓名標準化 (抓出影分身)
def normalize_name(name):
    if not name: return ""
    clean = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name).replace(" ", "").lower()
    if "金閃閃" in clean: return "kingsley金閃閃"
    if "冬青" in clean or "得來速" in clean: return "冬青得來速"
    if clean == "菜" or clean == "小菜": return "小菜"
    return clean

# ==========================================
# 2. 功能工具箱
# ==========================================
def update_player(pid, d, n, im, bb, oc, iv):
    current_data = load_data()
    t = next((p for p in current_data["sessions"][d] if p['id']==pid), None)
    if t: 
        final_im = False if any(k in n for k in ["友", "（", "("]) else im
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
        if any(k in target_name for k in ["友", "（", "("]):
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

def render_list(lst, date_key, is_wait=False, can_edit_global=True, is_admin_mode=False):
    if not lst:
        if not is_wait: st.markdown("""<div style="text-align: center; padding: 40px; color: #cbd5e1; opacity:0.8;"><div style="font-size: 36px; margin-bottom: 8px;">🏀</div><p style="font-size: 0.85rem; font-weight:500;">無人報名</p></div>""", unsafe_allow_html=True)
        return
    display_lst = sorted(lst, key=lambda x: x.get('timestamp', 0))
    p_counter = 0 
    for p in display_lst:
        is_playing = p.get('count', 1) > 0
        if is_playing:
            p_counter += 1
            idx_str, idx_cls = f"{p_counter}.", "list-index"
        else:
            idx_str, idx_cls = "🌸", "list-index-flower"
            
        if st.session_state.edit_target == p['id']:
            with st.container():
                st.markdown(f"<div class='edit-box'>✏️ 正在編輯：{p['name']}</div>", unsafe_allow_html=True)
                with st.form(key=f"e_{p['id']}"):
                    # 管理員特權：此處姓名不再鎖死
                    en = st.text_input("姓名", p['name'], disabled=not is_admin_mode)
                    ec1, ec2, ec3 = st.columns(3)
                    is_friend = any(k in p['name'] for k in ["友", "（", "("])
                    em = ec1.checkbox("⭐晴女", p.get('isMember'), disabled=(not is_admin_mode and is_friend))
                    eb = ec2.checkbox("🏀帶球", p.get('bringBall'), disabled=is_friend)
                    ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'), disabled=is_friend)
                    ev = st.checkbox("📣 不打球 (加油團)", p.get('count') == 0, disabled=is_friend)
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 儲存", type="primary"): update_player(p['id'], date_key, en, em, eb, ec, ev)
                    if b2.form_submit_button("取消"): st.session_state.edit_target = None; st.rerun()
        else:
            badges = ""
            if p.get('count') == 0: badges += "<span class='badge badge-visit'>📣加油團</span>"
            if p.get('isMember') and not any(k in p['name'] for k in ["友", "（", "("]): 
                badges += "<span class='badge badge-sunny'>晴女</span>"
            if p.get('bringBall'): badges += "<span class='badge badge-ball'>帶球</span>"
            if p.get('occupyCourt'): badges += "<span class='badge badge-court'>佔場</span>"
            
            c_cfg = [7.5, 0.6, 0.6, 1.3] 
            cols = st.columns(c_cfg, gap="small")
            with cols[0]:
                st.markdown(f"""<div class="player-row"><span class="{idx_cls}">{idx_str}</span><span class="list-name">{p['name']}</span>{badges}</div>""", unsafe_allow_html=True)
            if can_edit_global:
                with cols[1]:
                    if st.button("✏️", key=f"be_{p['id']}"): st.session_state.edit_target = p['id']; st.rerun()
                with cols[2]:
                    with st.popover("❌"):
                        st.write("確定取消報名？")
                        if st.button("確認刪除", key=f"conf_del_{p['id']}", type="primary"): delete_player(p['id'], date_key)

# ==========================================
# 3. 初始化 & CSS
# ==========================================
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'edit_target' not in st.session_state: st.session_state.edit_target = None

st.set_page_config(page_title="晴女籃球報名", page_icon="☀️", layout="centered") 
st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');[data-testid="stAppViewContainer"]{background-color:#f8fafc!important;color:#334155!important;}html,body,[class*="css"],p,div,label,span,h1,h2,h3,.stMarkdown{font-family:'Noto Sans TC',sans-serif;color:#334155!important;}.block-container{padding-top:4rem!important;padding-bottom:5rem!important;}header{background:transparent!important;}[data-testid="stDecoration"],[data-testid="stToolbar"],[data-testid="stStatusWidget"],footer,#MainMenu,.stDeployButton{display:none!important;}[data-testid="stSidebarCollapsedControl"]{display:none!important;}.header-box{background:white;padding:1.5rem 1rem;border-radius:20px;text-align:center;margin-bottom:20px;box-shadow:0 4px 20px rgba(0,0,0,0.03);border:1px solid #f1f5f9;}.header-title{font-size:1.6rem;font-weight:800;color:#1e293b!important;letter-spacing:1px;margin-bottom:5px;}.header-sub{font-size:0.9rem;color:#64748b!important;font-weight:500;}.info-pill{background:#f1f5f9;padding:4px 14px;border-radius:30px;font-size:0.8rem;font-weight:600;color:#475569!important;display:inline-block;margin-top:10px;}.player-row{background:white;border:1px solid #f1f5f9;border-radius:12px;padding:8px 10px;margin-bottom:8px;box-shadow:0 2px 5px rgba(0,0,0,0.03);display:flex;align-items:center;width:100%;min-height:40px;}.list-index{color:#cbd5e1!important;font-weight:700;font-size:0.9rem;margin-right:12px;min-width:20px;text-align:right;}.list-index-flower{color:#f472b6!important;font-weight:700;font-size:1rem;margin-right:12px;min-width:20px;text-align:right;}.list-name{color:#334155!important;font-weight:700;font-size:1.15rem;flex-grow:1;line-height:1.2;}.badge{padding:2px 6px;border-radius:5px;font-size:0.7rem;font-weight:700;margin-left:4px;display:inline-block;vertical-align:middle;}.badge-sunny{background:#fffbeb;color:#d97706!important;}.badge-ball{background:#fff7ed;color:#c2410c!important;}.badge-court{background:#eff6ff;color:#1d4ed8!important;}.badge-visit{background:#fdf2f8;color:#db2777!important;border:1px solid #fce7f3;}.progress-container{width:100%;background:#e2e8f0;border-radius:6px;height:6px;margin-top:8px;overflow:hidden;}.progress-bar{height:100%;border-radius:6px;transition:width 0.6s ease;}.progress-info{display:flex;justify-content:space-between;font-size:0.8rem;color:#64748b!important;margin-bottom:2px;font-weight:600;}.edit-box{border:1px solid #3b82f6;border-radius:12px;padding:12px;background:#eff6ff;margin-bottom:10px;}button[data-testid="stBaseButton-secondary"]{width:100%!important;height:32px!important;padding:0!important;}</style>""", unsafe_allow_html=True)

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
            comb_l = {}; n_map = {}
            for o_n, mons in l_d.items():
                low_n = normalize_name(o_n)
                if low_n not in comb_l: comb_l[low_n] = set(); n_map[low_n] = o_n
                comb_l[low_n].update(mons)
            for low_n in sorted(comb_l.keys()):
                disp_n, m_list = n_map[low_n], sorted(list(comb_l[low_n]))
                col_i, col_m = st.columns([0.8, 0.2])
                with col_i: st.markdown(f"**👤 {disp_n}**: {', '.join(m_list)}")
                with col_m:
                    with st.popover("🗑️"):
                        for m_i in m_list:
                            if st.button(f"刪除 {m_i}", key=f"dl_{low_n}_{m_i}"):
                                cur = load_data()
                                for ok in list(cur["leaves"].keys()):
                                    if normalize_name(ok) == low_n and m_i in cur["leaves"][ok]:
                                        cur["leaves"][ok].remove(m_i)
                                        if not cur["leaves"][ok]: del cur["leaves"][ok]
                                save_data(cur); st.toast(f"🗑️ 移除 {m_i}"); time.sleep(0.5); st.rerun()
                        st.divider()
                        if st.button("🚨 強制刪除", key=f"f_dl_{low_n}", type="secondary"):
                            cur = load_data()
                            for ok in list(cur["leaves"].keys()):
                                if normalize_name(ok) == low_n: del cur["leaves"][ok]
                            save_data(cur); st.toast("🗑️ 已強制移除"); time.sleep(0.5); st.rerun()
        else: st.info("目前無人請假")

# 場次顯示
all_dates = sorted(st.session_state.data["sessions"].keys())
dates = [d for d in all_dates if d not in st.session_state.data.get("hidden", [])]

if not dates: st.info("👋 目前沒有開放報名的場次")
else:
    tabs = st.tabs([f"{int(d.split('-')[1])}/{int(d.split('-')[2])}" for d in dates])
    for i, dk in enumerate(dates):
        with tabs[i]:
            all_p = st.session_state.data["sessions"][dk]
            act_p = [p for p in all_p if p.get('count', 1) > 0]
            non_p = [p for p in all_p if p.get('count', 1) == 0]
            prio_p = sorted(act_p, key=lambda x: (0 if x.get('isMember') else 1, x.get('timestamp', 0)))
            main_active = prio_p[:MAX_CAPACITY]
            wait_active = prio_p[MAX_CAPACITY:]
            main_list = sorted(main_active + non_p, key=lambda x: x.get('timestamp', 0))
            wait_list = sorted(wait_active, key=lambda x: x.get('timestamp', 0))
            
            curr_c = len(main_active)
            b_c = len([x for x in main_active if x.get('bringBall')])
            c_c = len([x for x in main_active if x.get('occupyCourt')])
            pct = min(100, (curr_c/MAX_CAPACITY)*100)
            
            c_code = '#4ade80' if pct < 50 else '#fbbf24' if pct < 85 else '#f87171'
            p_h = f'<div class="progress-info"><span>正選 ({curr_c}/{MAX_CAPACITY})</span><span>候補: {len(wait_list)}</span></div>'
            b_h = f'<div class="progress-container"><div class="progress-bar" style="width: {pct}%; background: {c_code};"></div></div>'
            s_h = f'<div style="display: flex; justify-content: flex-end; gap: 15px; font-size: 0.85rem; color: #64748b; margin-bottom: 25px; font-weight: 500; padding-right: 5px;"><span>🏀 帶球：<b>{b_c}</b></span><span>🚩 佔場：<b>{c_c}</b></span></div>'
            st.markdown(f'<div style="margin-bottom: 5px; padding: 0 4px;">{p_h}{b_h}</div>{s_h}', unsafe_allow_html=True)

            with st.expander("📝 點擊報名"):
                with st.form(f"f_{dk}", clear_on_submit=True):
                    name = st.text_input("球員姓名")
                    c1, c2, c3 = st.columns(3)
                    im = c1.checkbox("⭐晴女", key=f"m_{dk}")
                    bb = c2.checkbox("🏀帶球", key=f"b_{dk}")
                    oc = c3.checkbox("🚩佔場", key=f"c_{dk}")
                    ev = st.checkbox("📣 不打球 (加油團)", key=f"v_{dk}")
                    tot = st.number_input("報名人數", 1, 3, 1, key=f"t_{dk}")
                    if st.form_submit_button("送出報名", type="primary"):
                        if "友" in name: st.error("❌ 請輸入團員姓名")
                        elif name:
                            lat = load_data(); cur_p = lat["sessions"].get(dk, [])
                            num_rel = len([x for x in cur_p if name in x['name']])
                            if num_rel == 0 and not im: st.error("❌ 第一次報名需勾選「⭐晴女」")
                            elif num_rel > 0 and im: st.error("❌ 加報朋友請勿重複勾選晴女")
                            elif num_rel + tot > 3: st.error("❌ 每人上限 3 位")
                            else:
                                ts = time.time(); new_li = []
                                for k in range(tot):
                                    is_m = (k==0 and num_rel == 0)
                                    fn = name if is_m else f"{name} (友{num_rel+k})"
                                    new_li.append({"id": str(uuid.uuid4()),"name": fn,"count": (0 if ev and is_m else 1),"isMember": (im if is_m else False),"bringBall": (bb if is_m else False),"occupyCourt": (oc if is_m else False),"timestamp": ts + (k*0.01)})
                                lat["sessions"][dk].extend(new_li); save_data(lat); st.balloons(); st.toast("🎉 報名成功！"); time.sleep(2); st.rerun()

            st.subheader("🏀 報名名單")
            render_list(main_list, dk, False, True, st.session_state.is_admin)
            if wait_list:
                st.markdown("<br>", unsafe_allow_html=True); st.subheader("⏳ 候補名單")
                render_list(wait_list, dk, True, True, st.session_state.is_admin)

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
            if st.button("確認完全刪除場次"):
                cur = load_data(); del cur["sessions"][del_s]; save_data(cur); st.rerun()
            h_s = st.multiselect("隱藏場次", all_s, default=st.session_state.data.get("hidden", []))
            if st.button("更新隱藏設定"):
                cur = load_data(); cur["hidden"] = h_s; save_data(cur); st.rerun()

        # --- 管理員特權：編輯隱藏場次 ---
        st.divider()
        st.subheader("🕵️ 編輯隱藏場次資料")
        hidden_dates = st.session_state.data.get("hidden", [])
        if hidden_dates:
            target_h_date = st.selectbox("選擇要修改的隱藏日期", sorted(hidden_dates))
            if target_h_date:
                h_p_list = st.session_state.data["sessions"].get(target_h_date, [])
                st.info(f"正在管理 {target_h_date} 的資料")
                render_list(h_p_list, target_h_date, is_admin_mode=True)
        else: st.write("目前無隱藏場次")

        st.divider()
        st.subheader("📊 出席統計報表")
        if st.button("產生統計"):
            try:
                d_m = st.session_state.data; stats = {} 
                open_s = dates; member_signups = {} 
                for osd in open_s:
                    f_d = f"{int(osd.split('-')[1])}/{int(osd.split('-')[2])}"
                    for p in d_m["sessions"].get(osd, []):
                        if "友" not in p['name']:
                            nm = normalize_name(p['name'])
                            if nm not in member_signups: member_signups[nm] = []
                            member_signups[nm].append(f_d)
                for ds, pl in d_m["sessions"].items():
                    do = datetime.strptime(ds, "%Y-%m-%d").date()
                    if do <= date.today():
                        for p in pl:
                            if "友" not in p['name']:
                                ln = normalize_name(p['name'])
                                if ln not in stats: stats[ln] = {"name": p['name'], "last_date": do, "leaves": set()}
                                elif do > stats[ln]["last_date"]: stats[ln]["last_date"] = do; stats[ln]["name"] = p['name']
                for ln, lms in d_m["leaves"].items():
                    nm = normalize_name(ln)
                    if nm not in stats: stats[nm] = {"name": ln, "last_date": None, "leaves": set(lms)}
                    else: stats[nm]["leaves"].update(lms)
                rep = []; curm = date.today().strftime("%Y-%m")
                for ln in sorted(stats.keys()):
                    it = stats[ln]; ld = it["last_date"]; lms = sorted(list(it["leaves"]))
                    sgn = ", ".join(member_signups.get(ln, [])) if member_signups.get(ln) else "—"
                    if ld: days = (date.today()-ld).days; ldstr = str(ld)
                    else: days = 999; ldstr = "無紀錄"
                    if curm in lms: stt = "🏖️ 請假中"
                    elif days > 60: stt = "🔴 逾期"
                    elif days > 45: stt = "🟡 預警"
                    else: stt = "🟢 活躍"
                    rep.append({"姓名": it["name"],"近期報名": sgn,"最後出席": ldstr,"請假月份": ", ".join(lms) if lms else "無","累計月數": len(lms),"狀態": stt})
                st.table(rep)
            except Exception as e: st.error(f"統計失敗: {e}")

        st.divider()
        if st.button("🧹 一鍵清洗標籤"):
            cur = load_data(); count = 0
            for dk in cur["sessions"]:
                for p in cur["sessions"][dk]:
                    if any(k in p['name'] for k in ["友", "（", "("]) and p.get('isMember'):
                        p['isMember'] = False; count += 1
            save_data(cur); st.success(f"清洗完成！共修正 {count} 筆。"); time.sleep(2); st.rerun()
