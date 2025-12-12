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
FILE_PATH = 'basketball_data.json'
MAX_CAPACITY = 20
APP_URL = "https://sunny-girls-basketball.streamlit.app" 

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
# 2. UI 極簡禪意風格 (CSS) - V3.37 規則完美補完版
# ==========================================
st.set_page_config(page_title="最美加油團", page_icon="🌸", layout="centered") 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; background-color: #f8fafc; }
    
    /* 頂部留白 */
    .block-container { 
        padding-top: 3.5rem !important; 
        padding-bottom: 5rem !important; 
    }
    
    #MainMenu, footer { visibility: hidden; }

    /* Header */
    .header-box {
        background: white;
        padding: 1.5rem 1rem; border-radius: 20px; 
        text-align: center; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    .header-title { font-size: 1.6rem; font-weight: 800; color: #1e293b; letter-spacing: 1px; margin-bottom: 5px; }
    .header-sub { font-size: 0.9rem; color: #64748b; font-weight: 500; }
    .info-pill {
        background: #f1f5f9; padding: 4px 14px;
        border-radius: 30px; font-size: 0.8rem; font-weight: 600; color: #475569;
        display: inline-block; margin-top: 10px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 38px; background-color: transparent; border-radius: 20px;
        padding: 0 16px; font-size: 0.9rem; border: 1px solid transparent; color: #64748b; font-weight: 500;
    }
    .stTabs [aria-selected="true"] { 
        background-color: white; color: #3b82f6; border: none; 
        box-shadow: 0 2px 6px rgba(0,0,0,0.04); font-weight: 700;
    }
    div[data-baseweb="tab-highlight"] { display: none !important; height: 0 !important; }
    div[data-baseweb="tab-border"] { display: none !important; }

    /* 列表卡片樣式 */
    .player-row {
        background: white;
        border: 1px solid #f1f5f9;
        border-radius: 12px;
        padding: 10px 8px 10px 14px;
        margin-bottom: 8px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        transition: transform 0.1s;
        display: flex; 
        align-items: center;
        width: 100%;
        line-height: 1.5;
    }
    .player-row:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }

    .list-index { color: #cbd5e1; font-weight: 700; font-size: 0.9rem; margin-right: 12px; min-width: 20px; text-align: right;}
    .list-index-flower { color: #f472b6; font-weight: 700; font-size: 1rem; margin-right: 12px; min-width: 20px; text-align: right;}
    
    /* 名字樣式 */
    .list-name { 
        color: #334155; 
        font-weight: 700; 
        font-size: 1.15rem; 
        letter-spacing: 0.5px;
        flex-grow: 1;
        line-height: 1.2;
    }
    
    .badge { padding: 2px 6px; border-radius: 5px; font-size: 0.7rem; font-weight: 700; margin-left: 4px; display: inline-block; vertical-align: middle; transform: translateY(-1px);}
    .badge-sunny { background: #fffbeb; color: #d97706; }
    .badge-ball { background: #fff7ed; color: #c2410c; }
    .badge-court { background: #eff6ff; color: #1d4ed8; }
    .badge-visit { background: #fdf2f8; color: #db2777; border: 1px solid #fce7f3; }

    /* 按鈕樣式 */
    [data-testid="stHorizontalBlock"] { align-items: center !important; gap: 0rem !important; }
    [data-testid="column"] { padding: 0px 2px !important; } 
    
    .list-btn-col button {
        border: none !important; 
        background: transparent !important;
        padding: 0px !important;
        color: #cbd5e1 !important; 
        font-size: 14px !important;
        line-height: 1 !important;
        height: 32px !important;
        width: 32px !important;
        display: flex; justify-content: center; align-items: center;
        margin: 0 !important;
    }
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; border-radius: 6px; }
    .list-btn-d button { color: unset !important; opacity: 0.7; font-size: 12px !important; }
    .list-btn-d button:hover { opacity: 1; background: #fef2f2 !important; border-radius: 6px; }
    .list-btn-up button { 
        padding: 0px 8px !important; height: 26px !important; font-size: 0.75rem !important; 
        border-radius: 6px !important; background: #e0f2fe !important; color: #0284c7 !important;
        font-weight: 600 !important; width: auto !important;
    }

    /* Progress Bar */
    .progress-container { width: 100%; background: #e2e8f0; border-radius: 6px; height: 6px; margin-top: 8px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
    .progress-info { display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748b; margin-bottom: 2px; font-weight: 600; }
    
    .edit-box { border: 1px solid #3b82f6; border-radius: 12px; padding: 12px; background: #eff6ff; margin-bottom: 10px; }
    
    /* [V3.37 Upgrade] 大師級規則區塊 */
    .rules-box {
        background-color: white;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 4px 15px rgba(0,0,0,0.02);
        margin-top: 15px;
    }
    .rules-header {
        font-size: 1rem;
        font-weight: 800;
        color: #334155;
        margin-bottom: 15px;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 8px;
        letter-spacing: 1px;
    }
    .rules-row {
        display: flex;
        align-items: flex-start;
        margin-bottom: 12px;
    }
    .rules-icon {
        font-size: 1.1rem;
        margin-right: 12px;
        line-height: 1.4;
    }
    .rules-content {
        font-size: 0.9rem;
        color: #64748b;
        line-height: 1.5;
    }
    .rules-content b {
        color: #475569;
        font-weight: 700;
    }
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

# ==========================================
# 4. 主畫面邏輯
# ==========================================
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

            # === 進度條 ===
            pct = min(100, (curr / MAX_CAPACITY) * 100)
            bar_color = "#4ade80" if pct < 50 else "#fbbf24" if pct < 85 else "#f87171"
            
            st.markdown(f"""
            <div style="margin-bottom: 25px; padding: 0 4px;">
                <div class="progress-info">
                    <span style="color:#334155;">正選 ({curr}/{MAX_CAPACITY})</span>
                    <span style="color:#94a3b8; font-weight:400;">候補: {len(wait)}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {pct}%; background: {bar_color};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # === Functions ===
            def update(pid, d, n, im, bb, oc, iv):
                t = next((p for p in st.session_state.data["sessions"][d] if p['id']==pid), None)
                if t: 
                    new_count = 0 if iv else 1
                    t.update({'name':n,'isMember':im,'bringBall':bb,'occupyCourt':oc, 'count': new_count})
                    save_data(st.session_state.data)
                    st.session_state.edit_target=None
                    st.toast("✅ 資料已更新")
                    time.sleep(0.5)
                    st.rerun()
            
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
                    st.caption("⚠️ 名字請務必與群組內一致，不符者將直接刪除")
                    
                    c1, c2, c3 = st.columns(3)
                    im = c1.checkbox("⭐晴女 (團員務必勾選)", key=f"m_{date_key}", disabled=not can_edit)
                    bb = c2.checkbox("🏀帶球", key=f"b_{date_key}", disabled=not can_edit)
                    oc = c3.checkbox("🚩佔場", key=f"c_{date_key}", disabled=not can_edit)
                    ev = st.checkbox("📣 不打球 (最美加油團)", key=f"v_{date_key}", disabled=not can_edit)
                    
                    tot = st.number_input("本次報名人數 (含自己, 上限3人)", 1, 3, 1, key=f"t_{date_key}", disabled=not can_edit)
                    
                    if st.form_submit_button("送出報名", disabled=not can_edit, type="primary"):
                        if name:
                            related_entries = [p for p in players if p['name'] == name or p['name'].startswith(f"{name} (友")]
                            current_count = len(related_entries)
                            is_ok = False
                            error_message = None
                            
                            if current_count == 0:
                                if ev and not im: error_message = "❌ 報名「最美加油團」必須是「⭐晴女」團員。"
                                elif not im: error_message = "❌ 報名或帶朋友報名，請務必勾選「⭐晴女」以驗證團員身份。"
                                else: is_ok = True
                            elif current_count > 0:
                                if im: error_message = f"❌ {name} 已有報名資料，加報朋友請勿重複勾選「⭐晴女」。"
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
                                        db_friend_count = len([p for p in players if p['name'].startswith(f"{name} (友")])
                                        current_loop_friend_count = len([n for n in new_entries_list if n['name'].startswith(f"{name} (友")])
                                        friend_seq = db_friend_count + current_loop_friend_count + 1
                                        final_name = f"{name} (友{friend_seq})"
                                        p_im, p_bb, p_oc = False, False, False 
                                        p_count = 1 
                                    
                                    new_entries_list.append({"id": str(uuid.uuid4()),"name": final_name,"count": p_count,"isMember": p_im,"bringBall": p_bb,"occupyCourt": p_oc,"timestamp": ts + 0.1 + (k * 0.01)})
                                st.session_state.data["sessions"][date_key].extend(new_entries_list); save_data(st.session_state.data); st.balloons(); st.toast(f"🎉 歡迎 {name} 加入！", icon="🏀"); time.sleep(1.5); st.rerun()
                        else: st.toast("❌ 請輸入姓名")

                # [V3.37 Upgrade] 大師級規則美化
                st.markdown("""
                <div class="rules-box">
                    <div class="rules-header">📌 報名須知</div>
                    <div class="rules-row">
                        <span class="rules-icon">🔴</span>
                        <div class="rules-content"><b>資格與規範</b>：採實名制 (需與群組名一致)。僅限 <b>⭐晴女</b> 報名，朋友不可單獨報名 (需由團員帶入，含自己上限3位)。</div>
                    </div>
                    <div class="rules-row">
                        <span class="rules-icon">🟡</span>
                        <div class="rules-content"><b>📣最美加油團</b>：團員若「不打球但帶朋友」請勾此項。本人不佔名額，但朋友會佔打球名額。</div>
                    </div>
                    <div class="rules-row">
                        <span class="rules-icon">🟢</span>
                        <div class="rules-content"><b>優先與遞補</b>：正選 20 人。候補名單中之 <b>⭐晴女</b>，享有優先遞補「非晴女」之權利。</div>
                    </div>
                    <div class="rules-row">
                        <span class="rules-icon">🔵</span>
                        <div class="rules-content"><b>行政與時間</b>：截止於前一日 12:00。雨備於當日 17:00 通知。僅能修改屬性，不可改名。</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # === 名單渲染 ===
            st.subheader("🏀 報名名單")
            def render_list(lst, is_wait=False):
                if not lst:
                    if not is_wait:
                        st.markdown("""<div style="text-align: center; padding: 40px; color: #cbd5e1; opacity:0.8;"><div style="font-size: 36px; margin-bottom: 8px;">🏀</div><p style="font-size: 0.85rem; font-weight:500;">場地空蕩蕩...<br>快來當第一位！</p></div>""", unsafe_allow_html=True)
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
                                em = ec1.checkbox("⭐晴女", p.get('isMember'))
                                eb = ec2.checkbox("🏀帶球", p.get('bringBall'))
                                ec = ec3.checkbox("🚩佔場", p.get('occupyCourt'))
                                ev = st.checkbox("📣 不打球 (最美加油團)", p.get('count') == 0)
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
                            st.markdown(f"""
                            <div class="player-row">
                                <span class="{idx_class}">{index_str}</span>
                                <span class="list-name">{p['name']}</span>
                                {badges}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        b_idx = 1
                        if is_admin and is_wait and p.get('isMember'):
                            with cols[b_idx]:
                                st.markdown('<div class="list-btn-up">', unsafe_allow_html=True)
                                if st.button("⬆️", key=f"up_{p['id']}"): promote(p['id'], date_key)
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

            render_list(main)
            
            if wait:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                st.subheader(f"⏳ 候補名單")
                render_list(wait, is_wait=True)
