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
# 2. 手機版 UI 優化樣式 (CSS) - 終極優化版
# ==========================================
st.set_page_config(page_title="Sunny Girls", page_icon="☀️", layout="centered") 

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
    .header-title { font-size: 1.6rem; font-weight: 800; margin: 0; }
    .info-pill {
        background: rgba(255, 255, 255, 0.2); padding: 3px 10px;
        border-radius: 12px; font-size: 0.8rem; display: inline-block; margin-top: 8px;
    }

    /* 3. Tabs 優化 */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 36px; background-color: #f1f5f9; border-radius: 5px;
        padding: 4px 8px; font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] { background-color: #3b82f6; color: white; }

    /* =================================================================
       4. 【關鍵修改】列表與按鈕的強力排版修正
    ================================================================= */
    
    /* 強制讓 st.columns 在水平方向上垂直置中對齊 */
    [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }

    /* 列表文字樣式 */
    .list-text {
        font-size: 0.95rem; font-weight: 500; line-height: 1.4;
    }
    .list-tags {
        font-size: 0.8rem; color: #666; margin-left: 4px;
    }

    /* 將列表中的按鈕極簡化 (Ghost Buttons)，去除邊框和背景，看起來更像圖示 */
    .list-btn-col button {
        border: none !important;
        background: transparent !important;
        padding: 4px 8px !important;
        margin: 0 !important;
        color: #94a3b8 !important; /* 預設淺灰色 */
        min-height: 0px !important;
        height: auto !important;
        line-height: 1 !important;
        box-shadow: none !important;
    }
    /* 編輯按鈕滑鼠移過去變藍色 */
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; }
    /* 刪除按鈕滑鼠移過去變紅色 */
    .list-btn-d button:hover { color: #ef4444 !important; background: #fef2f2 !important; }
    
    /* 遞補按鈕特殊樣式 (維持明顯) */
    .list-btn-up button {
        padding: 4px 8px !important; min-height: 28px !important;
        font-size: 0.8rem !important;
    }
    
    /* 編輯模式的框框 */
    .edit-box {
        border: 2px solid #3b82f6; border-radius: 8px;
        padding: 10px; background-color: #eff6ff; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄 & Header (維持精簡)
# ==========================================
with st.sidebar:
    st.header("⚙️ 管理員")
    pwd_input = st.text_input("密碼", type="password")
    is_admin = (pwd_input == ADMIN_PASSWORD)
    if is_admin:
        st.success("已登入")
        new_date = st.date_input("新增日期", min_value=date.today())
        if st.button("➕ 新增"):
            d_str = str(new_date)
            if d_str not in st.session_state.data["sessions"]:
                st.session_state.data["sessions"][d_str] = []
                save_data(st.session_state.data)
                st.rerun()
        st.markdown("---")
        all_dates = sorted(st.session_state.data["sessions"].keys())
        if all_dates:
            cur_hidden = [d for d in st.session_state.data["hidden"] if d in all_dates]
            sel_hidden = st.multiselect("隱藏場次", all_dates, default=cur_hidden, placeholder="選擇日期...")
            if set(sel_hidden) != set(st.session_state.data["hidden"]):
                st.session_state.data["hidden"] = sel_hidden
                save_data(st.session_state.data)
                st.rerun()
            st.markdown("---")
            del_d = st.selectbox("刪除場次", all_dates)
            if st.button("確認刪除"):
                del st.session_state.data["sessions"][del_d]
                if del_d in st.session_state.data["hidden"]: st.session_state.data["hidden"].remove(del_d)
                save_data(st.session_state.data)
                st.rerun()

st.markdown("""
    <div class="header-box">
        <div class="header-title">☀️ Sunny Girls</div>
        <div style="font-size: 0.85rem; opacity: 0.9;">Keep playing, keep shining.</div>
        <div class="info-pill">🏀 朱崙公園 19:00</div>
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
    st.info("👋 暫無開放場次")
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

            c1, c2, c3 = st.columns(3)
            c1.caption(f"總人數: {len(players)}")
            c2.caption(f"正選: {len(main)}/{MAX_CAPACITY}")
            c3.caption(f"候補: {len(wait)}")
            
            # === 功能函式 (維持不變) ===
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

            # === 報名表單 (Expander) ===
            with st.expander("📝 報名 / 規則", expanded=not is_locked):
                if is_locked and not is_admin: st.warning("⛔ 已截止")
                with st.form(f"f_{date_key}", clear_on_submit=True):
                    f_name = st.text_input("姓名", disabled=not can_edit)
                    col_f1, col_f2, col_f3 = st.columns(3)
                    f_mem = col_f1.checkbox("⭐晴女", key=f"m_{date_key}", disabled=not can_edit)
                    f_ball = col_f2.checkbox("🏀帶球", key=f"b_{date_key}", disabled=not can_edit)
                    f_crt = col_f3.checkbox("🚩佔場", key=f"c_{date_key}", disabled=not can_edit)
                    f_tot = st.number_input("總人數 (含自己)", 1, 3, 1, key=f"t_{date_key}", disabled=not can_edit)
                    if st.form_submit_button("送出報名", disabled=not can_edit, type="primary"):
                        if f_name:
                            ts = time.time()
                            new_ps = [{"id": str(uuid.uuid4()), "name": f_name, "count": 1, "isMember": f_mem, "bringBall": f_ball, "occupyCourt": f_crt, "timestamp": ts}]
                            for f in range(f_tot - 1):
                                new_ps.append({"id": str(uuid.uuid4()), "name": f"{f_name} (友{f+1})", "count": 1, "isMember": False, "bringBall": False, "occupyCourt": False, "timestamp": ts + 0.1 + (f*0.01)})
                            st.session_state.data["sessions"][date_key].extend(new_ps)
                            save_data(st.session_state.data)
                            st.rerun()
                        else: st.error("請輸入姓名")
                st.caption("規則：加人請重填，減人請刪除。晴女優先遞補。")

            # ============================================================
            #  【關鍵修改】名單顯示區 - 使用 CSS Class 進行強力排版
            # ============================================================
            st.subheader("✅ 正選")
            if main:
                for idx, p in enumerate(main):
                    if st.session_state.edit_target == p['id']:
                        # --- 編輯模式 (保持原樣) ---
                        with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ 編輯：{p['name']}</div>", unsafe_allow_html=True)
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
                        # --- 顯示模式 (極簡化按鈕) ---
                        tags = []
                        if p.get('isMember'): tags.append("⭐")
                        if p.get('bringBall'): tags.append("🏀")
                        if p.get('occupyCourt'): tags.append("🚩")
                        tag_str = " ".join(tags)

                        # 使用較緊湊的比例 [6.5, 1, 1]
                        r1, r2, r3 = st.columns([6.5, 1, 1])
                        
                        # 文字欄
                        r1.markdown(f"<span class='list-text'>{idx+1}. {p['name']}</span> <span class='list-tags'>{tag_str}</span>", unsafe_allow_html=True)
                        
                        # 按鈕欄 (套用特殊 CSS Class)
                        if can_edit:
                            with r2:
                                st.markdown('<div class="list-btn-col list-btn-e">', unsafe_allow_html=True)
                                if st.button("✏️", key=f"be_{p['id']}"):
                                    st.session_state.edit_target = p['id']; st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                            with r3:
                                st.markdown('<div class="list-btn-col list-btn-d">', unsafe_allow_html=True)
                                if st.button("❌", key=f"bd_{p['id']}"):
                                    delete_p(p['id'], date_key)
                                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.caption("尚無人報名")

            if wait:
                st.divider()
                st.subheader(f"⏳ 候補 ({len(wait)})")
                for idx, p in enumerate(wait):
                    if st.session_state.edit_target == p['id']:
                         # --- 候補編輯模式 ---
                         with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ 編輯：{p['name']}</div>", unsafe_allow_html=True)
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
                        # --- 候補顯示模式 ---
                        tags = []; 
                        if p.get('isMember'): tags.append("⭐")
                        if p.get('bringBall'): tags.append("🏀")
                        if p.get('occupyCourt'): tags.append("🚩")
                        tag_str = " ".join(tags)
                        
                        # 根據是否為管理員調整欄位
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
