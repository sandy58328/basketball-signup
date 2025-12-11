import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime, date

# ==========================================
# 0. 設定區 (管理員密碼 & 分享網址)
# ==========================================
ADMIN_PASSWORD = "sunny"

# ⚠️ 請將下方網址改成你實際部署後的網址
APP_URL = "https://sunny-girls-basketball.streamlit.app"

# ==========================================
# 1. 資料處理函式
# ==========================================
FILE_PATH = 'basketball_data.json'
MAX_CAPACITY = 20

def load_data():
    default_data = {"sessions": {}, "hidden": []}
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "sessions" not in data:
                    data["sessions"] = {}
                if "hidden" not in data:
                    data["hidden"] = []
                return data
        except:
            return default_data
    return default_data

def save_data(data):
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# ==========================================
# 2. 介面樣式 (CSS 美化區)
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="wide")

st.markdown("""
    <style>
    /* Tabs 樣式 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #f0f9ff;
        border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0f2fe; border-bottom: 2px solid #0ea5e9; font-weight: bold;
    }
    
    /* 標題區塊 */
    .header-box {
        background: linear-gradient(to right, #38bdf8, #3b82f6, #6366f1);
        padding: 2rem; border-radius: 1rem; color: white; margin-bottom: 1rem;
        text-align: center;
    }
    .info-tag {
        background: rgba(255, 255, 255, 0.2);
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
        backdrop-filter: blur(5px);
    }
    
    /* 按鈕微調 */
    button[kind="secondary"] {
        padding: 0px 10px;
        border-radius: 5px;
    }
    
    /* === 核心修改：把醜醜的網址框變漂亮 === */
    /* 1. 隱藏 Expander 的邊框和背景，讓它看起來像個乾淨的按鈕 */
    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    div[data-testid="stExpander"] details {
        border: none !important;
    }
    
    /* 2. 把 st.code 的灰色背景和邊框拿掉，變成透明 */
    code {
        background-color: transparent !important;
        color: #3b82f6 !important; /* 讓網址變漂亮的藍色 */
        font-weight: bold;
        border: none !important;
    }
    div[data-testid="stCodeBlock"] {
        background-color: #f0f9ff !important; /* 很淡的藍底，比較有質感 */
        border-radius: 10px;
        padding: 5px;
        border: 1px dashed #3b82f6; /* 虛線邊框，看起來像優惠券 */
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄：場次管理
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    pwd_input = st.text_input("輸入管理密碼解鎖功能", type="password")
    
    is_admin = (pwd_input == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("🔓 已解鎖 (管理員模式)")
        
        # 新增場次
        new_date = st.date_input("新增打球日期", min_value=date.today())
        if st.button("➕ 新增場次"):
            date_str = str(new_date)
            if date_str not in st.session_state.data["sessions"]:
                st.session_state.data["sessions"][date_str] = []
                save_data(st.session_state.data)
                st.success(f"已新增 {date_str}")
                st.rerun()
            else:
                st.warning("日期已存在")
        
        st.markdown("---")
        
        all_session_dates = sorted(st.session_state.data["sessions"].keys())
        
        if all_session_dates:
            # 隱藏場次設定
            st.write("👁️ **設定隱藏場次**")
            current_hidden = st.session_state.data["hidden"]
            current_hidden = [d for d in current_hidden if d in all_session_dates]
            
            selected_hidden = st.multiselect(
                "選擇要隱藏的日期：",
                options=all_session_dates,
                default=current_hidden
            )
            
            if set(selected_hidden) != set(st.session_state.data["hidden"]):
                st.session_state.data["hidden"] = selected_hidden
                save_data(st.session_state.data)
                st.rerun()

            st.markdown("---")
            
            # 刪除場次
            del_date = st.selectbox("刪除日期", options=all_session_dates)
            if st.button("確認刪除"):
                del st.session_state.data["sessions"][del_date]
                if del_date in st.session_state.data["hidden"]:
                    st.session_state.data["hidden"].remove(del_date)
                save_data(st.session_state.data)
                st.success("已刪除")
                st.rerun()
    else:
        if pwd_input: st.error("密碼錯誤")

# ==========================================
# 4. 主頁面邏輯
# ==========================================

# 排版：左邊標題 (7)，右邊分享按鈕 (2)
col_header, col_share = st.columns([7, 2])

with col_header:
    st.markdown("""
        <div class="header-box">
            <h1 style="margin:0; font-size: 2.2rem; font-weight: 800; letter-spacing: 1px;">晴女☀️在場邊等妳🌈</h1>
            <p style="margin:5px 0 15px 0; font-size: 0.9rem; opacity: 0.9; letter-spacing: 1px;">✨ 希望永遠是晴天 ✨</p>
            <div class="info-tag">
                📍 地點：朱崙公園 &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 時間：19:00開打
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_share:
    st.write("") 
    st.write("") 
    # 這裡的 Expander 會被上面的 CSS 美化
    with st.expander("🔗 分享連結", expanded=False):
        # 這裡的 code block 也被 CSS 美化成淡藍色虛線框
        st.code(APP_URL, language="text")

# -----------------------------------------------------

all_dates_raw = sorted(st.session_state.data["sessions"].keys())
hidden_list = st.session_state.data.get("hidden", [])

if is_admin:
    display_dates = all_dates_raw
else:
    display_dates = [d for d in all_dates_raw if d not in hidden_list]

if not display_dates:
    if is_admin:
        st.info("👋 目前沒有場次，請在左側新增！")
    else:
        st.info("👋 目前沒有開放報名的場次，請稍後再來！")
else:
    tab_titles = []
    for d in display_dates:
        title = f"📅 {d}"
        if is_admin and d in hidden_list:
            title += " (🔒隱藏)"
        tab_titles.append(title)

    tabs = st.tabs(tab_titles)

    for i, date_key in enumerate(display_dates):
        with tabs[i]:
            current_players = st.session_state.data["sessions"][date_key]
            
            # 依照時間排序
            sorted_players = sorted(current_players, key=lambda x: x.get('timestamp', 0))
            main_list = []
            wait_list = []
            current_count = 0

            # 分組
            for p in sorted_players:
                p_count = p.get('count', 1)
                if current_count + p_count <= MAX_CAPACITY:
                    main_list.append(p)
                    current_count += p_count
                else:
                    wait_list.append(p)
            
            # 統計
            total_reg = sum(p.get('count', 1) for p in current_players)
            c1, c2, c3 = st.columns(3)
            c1.metric("總人數", f"{total_reg}")
            c2.metric("正選", f"{len(main_list)} / {MAX_CAPACITY}")
            c3.metric("候補", f"{len(wait_list)}")
            st.markdown("---")

            col_form, col_list = st.columns([1, 2])

            with col_form:
                st.subheader("📝 我要報名")
                with st.form(f"form_{date_key}", clear_on_submit=True):
                    name_input = st.text_input("球員姓名")
                    
                    is_member = st.checkbox("⭐我是晴女", key=f"mem_{date_key}")
                    
                    total_count = st.number_input("報名總人數 (含自己, Max 3)", 1, 3, 1, key=f"tot_{date_key}")
                    
                    c_b, c_c = st.columns(2)
                    bring_ball = c_b.checkbox("🏀帶球", key=f"b_{date_key}")
                    occupy_court = c_c.checkbox("🚩佔場", key=f"c_{date_key}")
                    
                    if st.form_submit_button("送出"):
                        if name_input:
                            ts = time.time()
                            new_entries = []
                            new_entries.append({
                                "id": str(uuid.uuid4()), "name": name_input, "count": 1,
                                "isMember": is_member, "bringBall": bring_ball,
                                "occupyCourt": occupy_court, "timestamp": ts
                            })
                            friends = total_count - 1
                            for f in range(friends):
                                new_entries.append({
                                    "id": str(uuid.uuid4()), "name": f"{name_input} (朋友{f+1})",
                                    "count": 1, "isMember": False, "bringBall": False,
                                    "occupyCourt": False, "timestamp": ts + 0.1 + (f * 0.01)
                                })
                            st.session_state.data["sessions"][date_key].extend(new_entries)
                            save_data(st.session_state.data)
                            st.rerun()
                        else:
                            st.error("需填寫姓名")

                st.info("""
                **📌 規則**
                * **人數上限**：上限 20 人，超過轉候補，每人報名上限 3 人含本人。
                * **排序原則**：正選與候補皆依「填單時間」先後排列。
                * **優先遞補**：候補名單中之⭐晴女，可優先遞補正選名單中之「非晴女」。
                * **雨備**：雨天當日 17:00 前通知是否開團。
                """)

            with col_list:
                def delete_p(pid, d_key):
                    st.session_state.data["sessions"][d_key] = [
                        p for p in st.session_state.data["sessions"][d_key] if p["id"] != pid
                    ]
                    save_data(st.session_state.data)
                    st.rerun()

                # 遞補邏輯：插隊 (Cut in) 強力版
                def promote_p(wait_pid, d_key, target_main_list):
                    all_p = st.session_state.data["sessions"][d_key]
                    wait_person = next((p for p in all_p if p['id'] == wait_pid), None)
                    
                    # 找正選名單中「最後一個」非晴女
                    target_guest = None
                    for p in reversed(target_main_list):
                        if not p.get('isMember'):
                            target_id = p['id']
                            target_guest = next((op for op in all_p if op['id'] == target_id), None)
                            break
                    
                    if wait_person and target_guest:
                        cutoff_person = target_main_list[-1]
                        cutoff_time = cutoff_person.get('timestamp', 0)
                        
                        # 1. 晴女時間 = 對方時間 - 1秒
                        wait_person['timestamp'] = target_guest['timestamp'] - 1.0
                        
                        # 2. 非晴女時間 = 第20名時間 + 1秒
                        target_guest['timestamp'] = cutoff_time + 1.0
                        
                        save_data(st.session_state.data)
                        st.success(f"遞補成功！晴女 {wait_person['name']} 已晉升正選，{target_guest['name']} 轉為候補首位。")
                        
                        time.sleep(0.5)
                        st.rerun()

                    elif wait_person and not target_guest:
                        st.error("❌ 無法遞補：正選名單全是晴女，無非晴女可替換。")

                st.subheader("✅ 正選名單")
                if main_list:
                    for idx, p in enumerate(main_list):
                        cols = st.columns([0.5, 3, 2, 0.5]) 
                        cols[0].write(f"{idx+1}.")
                        cols[1].write(p['name'] + (" ⭐" if p.get('isMember') else ""))
                        
                        tag_s = []
                        if p.get('bringBall'): tag_s.append("🏀")
                        if p.get('occupyCourt'): tag_s.append("🚩")
                        cols[2].write(" ".join(tag_s))
                        
                        if cols[3].button("❌", key=f"d_{p['id']}"):
                            delete_p(p['id'], date_key)
                else:
                    st.write("尚無人報名")

                if wait_list:
                    st.divider()
                    st.subheader(f"⏳ 候補名單 ({len(wait_list)})")
                    
                    for idx, p in enumerate(wait_list):
                        can_promote = p.get('isMember')
                        
                        cols = st.columns([0.5, 3, 1, 1, 0.5]) 

                        cols[0].write(f"{idx+1}.")
                        cols[1].write(p['name'] + (" ⭐" if p.get('isMember') else ""))
                        
                        tag_s = []
                        if p.get('bringBall'): tag_s.append("🏀")
                        if p.get('occupyCourt'): tag_s.append("🚩")
                        cols[2].write(" ".join(tag_s))
                        
                        if can_promote and is_admin:
                            btn_key = f"up_{p['id']}"
                            if cols[3].button("⬆️遞補", key=btn_key):
                                promote_p(p['id'], date_key, main_list)
                        
                        del_key = f"dw_{p['id']}"
                        if cols[4].button("❌", key=del_key):
                            delete_p(p['id'], date_key)
