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
# 2. 手機版 UI 優化樣式 (CSS)
# ==========================================
st.set_page_config(page_title="Sunny Girls", page_icon="☀️", layout="centered") 
# 注意：layout 改成 centered 在手機上反而比較集中好看

st.markdown("""
    <style>
    /* 1. 減少手機版過大的邊距 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* 2. 優化 Tabs 樣式 */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px; 
        white-space: pre-wrap; 
        background-color: #f1f5f9;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6; 
        color: white;
    }

    /* 3. 標題區塊優化 */
    .header-box {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        padding: 1.5rem; 
        border-radius: 12px; 
        color: white; 
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .header-title {
        font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: 1px;
    }
    .header-sub {
        font-size: 0.9rem; opacity: 0.9; margin-top: 5px; margin-bottom: 10px;
    }
    .info-pill {
        background: rgba(255, 255, 255, 0.25);
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85rem;
        display: inline-block;
        backdrop-filter: blur(4px);
    }

    /* 4. 列表卡片樣式 (重要！) */
    .player-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .player-text {
        font-size: 1rem;
        font-weight: 500;
        color: #334155;
    }
    .player-tags {
        font-size: 0.8rem;
        color: #64748b;
        margin-left: 5px;
    }
    
    /* 編輯模式框框 */
    .edit-box {
        border: 2px solid #3b82f6;
        border-radius: 10px;
        padding: 10px;
        background-color: #eff6ff;
        margin-bottom: 10px;
    }
    
    /* 按鈕微調 */
    button[kind="secondary"] {
        padding: 2px 8px;
        font-size: 0.8rem;
        height: auto;
        line-height: 1.5;
    }
    
    /* 隱藏 Streamlit 預設選單以節省空間 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄 (管理區)
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
            st.write("隱藏設定")
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

# ==========================================
# 4. 主畫面
# ==========================================

# 標題區 (HTML 優化版)
st.markdown("""
    <div class="header-box">
        <div class="header-title">☀️ Sunny Girls</div>
        <div class="header-sub">Keep playing, keep shining.</div>
        <div class="info-pill">🏀 朱崙公園 19:00</div>
    </div>
""", unsafe_allow_html=True)

# 分享按鈕 (精簡版)
components.html(
    f"""
    <style>
    body {{ margin: 0; padding: 0; display: flex; justify-content: center; }}
    .btn {{
        background: white; border: 1px solid #ddd; border-radius: 20px;
        padding: 6px 15px; font-size: 14px; cursor: pointer; color: #555;
        font-family: sans-serif; display: flex; align-items: center; gap: 5px;
    }}
    </style>
    <button class="btn" onclick="navigator.clipboard.writeText('{APP_URL}').then(()=>{{document.getElementById('t').innerText='已複製!'}})">
        🔗 <span id="t">分享連結</span>
    </button>
    """, height=40
)

# -----------------------------------------------------

all_dates_raw = sorted(st.session_state.data["sessions"].keys())
hidden_list = st.session_state.data.get("hidden", [])
display_dates = all_dates_raw if is_admin else [d for d in all_dates_raw if d not in hidden_list]

if not display_dates:
    st.info("👋 暫無開放場次")
else:
    # 簡化 Tab 標題，避免手機版太長
    tab_titles = []
    for d in display_dates:
        # 取月/日 (例如 12/25) 比較短
        dt_obj = datetime.strptime(d, "%Y-%m-%d")
        title = f"{dt_obj.month}/{dt_obj.day}"
        if is_admin and d in hidden_list: title += "🔒"
        tab_titles.append(title)

    tabs = st.tabs(tab_titles)

    for i, date_key in enumerate(display_dates):
        with tabs[i]:
            # 計算截止
            try:
                y, m, d_int = map(int, date_key.split('-'))
                sess_dt = datetime(y, m, d_int)
                deadline = (sess_dt - timedelta(days=1)).replace(hour=18, minute=0, second=0)
                is_locked = datetime.now() > deadline
            except:
                is_locked = False

            can_edit = is_admin or (not is_locked)
            
            # 取得資料
            players = st.session_state.data["sessions"][date_key]
            players = sorted(players, key=lambda x: x.get('timestamp', 0))
            
            main, wait = [], []
            curr_count = 0
            for p in players:
                if curr_count + p.get('count', 1) <= MAX_CAPACITY:
                    main.append(p)
                    curr_count += p.get('count', 1)
                else:
                    wait.append(p)

            # 統計資訊 (使用較小的字體)
            c1, c2, c3 = st.columns(3)
            c1.caption(f"總人數: {len(players)}")
            c2.caption(f"正選: {len(main)}/{MAX_CAPACITY}")
            c3.caption(f"候補: {len(wait)}")
            st.markdown("---")

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
                # 找最後一個非晴女
                target_g = None
                for p in reversed(main): # 這裡直接用 main list
                    if not p.get('isMember'):
                        target_g = next((op for op in all_p if op['id'] == p['id']), None)
                        break
                
                if w_p and target_g:
                    cutoff = main[-1]['timestamp']
                    w_p['timestamp'] = target_g['timestamp'] - 1.0
                    target_g['timestamp'] = cutoff + 1.0
                    save_data(st.session_state.data)
                    st.success("遞補成功")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("無法遞補")

            # === 報名與名單顯示 (針對手機優化佈局) ===
            
            # 使用 Expander 收折報名表單，節省空間
            with st.expander("📝 我要報名 / 查看規則", expanded=not is_locked):
                if is_locked and not is_admin:
                    st.warning("⛔ 已截止")
                
                with st.form(f"f_{date_key}", clear_on_submit=True):
                    f_name = st.text_input("姓名", disabled=not can_edit)
                    f_mem = st.checkbox("⭐晴女", key=f"m_{date_key}", disabled=not can_edit)
                    f_tot = st.number_input("人數 (含自己)", 1, 3, 1, key=f"t_{date_key}", disabled=not can_edit)
                    
                    fc1, fc2 = st.columns(2)
                    f_ball = fc1.checkbox("🏀帶球", key=f"b_{date_key}", disabled=not can_edit)
                    f_crt = fc2.checkbox("🚩佔場", key=f"c_{date_key}", disabled=not can_edit)
                    
                    if st.form_submit_button("送出報名", disabled=not can_edit):
                        if f_name:
                            ts = time.time()
                            new_ps = [{
                                "id": str(uuid.uuid4()), "name": f_name, "count": 1,
                                "isMember": f_mem, "bringBall": f_ball, "occupyCourt": f_crt, "timestamp": ts
                            }]
                            for f in range(f_tot - 1):
                                new_ps.append({
                                    "id": str(uuid.uuid4()), "name": f"{f_name} (友{f+1})",
                                    "count": 1, "isMember": False, "bringBall": False, "occupyCourt": False, "timestamp": ts + 0.1 + (f*0.01)
                                })
                            st.session_state.data["sessions"][date_key].extend(new_ps)
                            save_data(st.session_state.data)
                            st.rerun()
                        else:
                            st.error("請輸入姓名")
                st.caption("規則：加人請重填，減人請刪除。晴女優先遞補。")

            # === 名單顯示 (Mobile Friendly) ===
            st.subheader("✅ 正選名單")
            if main:
                for idx, p in enumerate(main):
                    # 編輯模式
                    if st.session_state.edit_target == p['id']:
                        with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ {p['name']}</div>", unsafe_allow_html=True)
                            with st.form(key=f"e_{p['id']}"):
                                en = st.text_input("名", p['name'])
                                ec1, ec2, ec3 = st.columns(3)
                                em = ec1.checkbox("⭐", p.get('isMember'))
                                eb = ec2.checkbox("🏀", p.get('bringBall'))
                                ec = ec3.checkbox("🚩", p.get('occupyCourt'))
                                if st.form_submit_button("💾"):
                                    update_p(p['id'], date_key, en, em, eb, ec)
                                if st.form_submit_button("取消"):
                                    st.session_state.edit_target = None
                                    st.rerun()
                    else:
                        # === 手機版核心改動：合併欄位 ===
                        # 1. 準備顯示文字
                        tags = []
                        if p.get('isMember'): tags.append("⭐")
                        if p.get('bringBall'): tags.append("🏀")
                        if p.get('occupyCourt'): tags.append("🚩")
                        tag_str = " ".join(tags)
                        
                        # 2. 顯示卡片列 (Text | Edit | Del)
                        # 使用 columns 來控制比例，文字區給最大 (6), 按鈕給小 (1)
                        r1, r2, r3 = st.columns([6, 1, 1])
                        
                        # 文字區
                        r1.markdown(f"**{idx+1}. {p['name']}** <span style='color:#666; font-size:0.85em'>{tag_str}</span>", unsafe_allow_html=True)
                        
                        # 按鈕區 (只有在可編輯時出現)
                        if can_edit:
                            if r2.button("✏️", key=f"btn_e_{p['id']}"):
                                st.session_state.edit_target = p['id']
                                st.rerun()
                            if r3.button("❌", key=f"btn_d_{p['id']}"):
                                delete_p(p['id'], date_key)
            else:
                st.write("尚無人報名")

            if wait:
                st.write("") # Spacer
                st.subheader(f"⏳ 候補 ({len(wait)})")
                for idx, p in enumerate(wait):
                    # 候補編輯邏輯同上，略微簡化
                    if st.session_state.edit_target == p['id']:
                         with st.container():
                            st.markdown(f"<div class='edit-box'>✏️ {p['name']}</div>", unsafe_allow_html=True)
                            with st.form(key=f"ew_{p['id']}"):
                                en = st.text_input("名", p['name'])
                                ec1, ec2, ec3 = st.columns(3)
                                em = ec1.checkbox("⭐", p.get('isMember'))
                                eb = ec2.checkbox("🏀", p.get('bringBall'))
                                ec = ec3.checkbox("🚩", p.get('occupyCourt'))
                                if st.form_submit_button("💾"):
                                    update_p(p['id'], date_key, en, em, eb, ec)
                                if st.form_submit_button("取消"):
                                    st.session_state.edit_target = None
                                    st.rerun()
                    else:
                        tags = []
                        if p.get('isMember'): tags.append("⭐")
                        if p.get('bringBall'): tags.append("🏀")
                        if p.get('occupyCourt'): tags.append("🚩")
                        tag_str = " ".join(tags)
                        
                        # 候補列布局：文字 | 遞補 | 編輯 | 刪除
                        cols_cfg = [4, 1.5, 1, 1] if is_admin else [5, 1, 1]
                        cols = st.columns(cols_cfg)
                        
                        cols[0].markdown(f"{idx+1}. {p['name']} <span style='color:#666; font-size:0.8em'>{tag_str}</span>", unsafe_allow_html=True)
                        
                        btn_idx = 1
                        if is_admin and p.get('isMember'):
                            if cols[btn_idx].button("⬆️", key=f"up_{p['id']}"):
                                promote_p(p['id'], date_key)
                            btn_idx += 1
                        
                        if can_edit:
                            # 確保索引不會超出 (針對非管理員看不到遞補鈕的情況)
                            if btn_idx < len(cols):
                                if cols[btn_idx].button("✏️", key=f"bew_{p['id']}"):
                                    st.session_state.edit_target = p['id']
                                    st.rerun()
                            if btn_idx + 1 < len(cols):
                                if cols[btn_idx+1].button("❌", key=f"bdw_{p['id']}"):
                                    delete_p(p['id'], date_key)
