import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime, date

# ==========================================
# 1. 設定與資料處理 (Backend Logic)
# ==========================================

FILE_PATH = 'basketball_data.json'
MAX_CAPACITY = 20  # 每場上限

def load_data():
    """從 JSON 讀取資料，結構改變為支援多場次"""
    default_data = {"sessions": {}}
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "sessions" not in data:
                    return default_data
                return data
        except:
            return default_data
    return default_data

def save_data(data):
    """儲存資料"""
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化 Session State
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# ==========================================
# 2. 介面樣式 (CSS)
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #f0f9ff;
        border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0f2fe; border-bottom: 2px solid #0ea5e9; font-weight: bold;
    }
    .header-box {
        background: linear-gradient(to right, #38bdf8, #3b82f6, #6366f1);
        padding: 1.5rem; border-radius: 1rem; color: white; margin-bottom: 1rem;
    }
    .priority-alert {
        background-color: #fefce8; border-left: 5px solid #eab308;
        padding: 1rem; color: #854d0e; margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄：場次管理 (Admin)
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    st.info("版主專用：新增或刪除打球日期")
    
    # 新增日期
    new_date = st.date_input("新增打球日期", min_value=date.today())
    if st.button("➕ 新增場次"):
        date_str = str(new_date)
        if date_str not in st.session_state.data["sessions"]:
            st.session_state.data["sessions"][date_str] = []
            save_data(st.session_state.data)
            st.success(f"已新增 {date_str}")
            st.rerun()
        else:
            st.warning("這個日期已經存在囉！")

    st.markdown("---")
    
    # 刪除日期
    sessions = st.session_state.data["sessions"]
    if sessions:
        st.write("🗑️ **刪除舊場次**")
        del_date = st.selectbox("選擇要刪除的日期", options=sorted(sessions.keys()))
        if st.button("確認刪除場次"):
            del st.session_state.data["sessions"][del_date]
            save_data(st.session_state.data)
            st.success(f"已刪除 {del_date}")
            st.rerun()
    else:
        st.warning("目前沒有開放的場次，請先新增！")

# ==========================================
# 4. 主頁面邏輯
# ==========================================

# 標題區
st.markdown(f"""
    <div class="header-box">
        <h1 style="margin:0; font-size: 2rem;">🏀 Sunny Girls Basketball</h1>
        <p style="margin:5px 0 0 0; opacity:0.9;">晴女☀️在場邊等妳🌈 | 台北市朱崙公園籃球場 | 19:00 開打</p>
    </div>
""", unsafe_allow_html=True)

# 取得所有場次並排序
all_dates = sorted(st.session_state.data["sessions"].keys())

if not all_dates:
    st.info("👋 目前沒有開放報名的場次，請版主在左側選單新增日期！")
else:
    # 建立分頁 (Tabs)
    tabs = st.tabs([f"📅 {d}" for d in all_dates])

    # 針對每一個日期分頁，渲染獨立的報名表和名單
    for i, date_key in enumerate(all_dates):
        with tabs[i]:
            current_players = st.session_state.data["sessions"][date_key]
            
            # --- 邏輯處理 (排序、候補計算) ---
            sorted_players = sorted(current_players, key=lambda x: x.get('timestamp', 0))
            main_list = []
            wait_list = []
            current_count = 0

            for p in sorted_players:
                p_count = p.get('count', 1)
                if current_count + p_count <= MAX_CAPACITY:
                    main_list.append(p)
                    current_count += p_count
                else:
                    wait_list.append(p)
            
            # --- 統計資訊 ---
            total_reg = sum(p.get('count', 1) for p in current_players)
            c1, c2, c3 = st.columns(3)
            c1.metric("總報名人數", f"{total_reg} 人")
            c2.metric("正選", f"{len(main_list)} / {MAX_CAPACITY}")
            c3.metric("候補", f"{len(wait_list)}")
            
            st.markdown("---")

            # --- 左右佈局 ---
            col_form, col_list = st.columns([1, 2])

            # [左側] 報名表單
            with col_form:
                st.subheader("📝 我要報名")
                with st.form(f"form_{date_key}", clear_on_submit=True):
                    # 修改文字：讓使用者知道這格是填「第一位球員」
                    name_input = st.text_input("第一位球員姓名 (或是幫朋友報名)")
                    is_member = st.checkbox("這位是團員嗎？", key=f"mem_{date_key}")
                    
                    # 邏輯設定：朋友最多 +2 (總共 3 人)
                    friend_count = st.number_input(
                        "額外攜帶朋友 (上限2人)", 
                        min_value=0, max_value=2, value=0, 
                        key=f"friend_{date_key}"
                    )
                    
                    c_ball, c_court = st.columns(2)
                    bring_ball = c_ball.checkbox("🏀 帶球", key=f"ball_{date_key}")
                    occupy_court = c_court.checkbox("🚩 佔場", key=f"court_{date_key}")
                    
                    if st.form_submit_button("送出報名"):
                        if name_input:
                            ts = time.time()
                            new_entries = []
                            # 1. 第一位球員 (主報名者)
                            new_entries.append({
                                "id": str(uuid.uuid4()), 
                                "name": name_input, 
                                "count": 1,
                                "isMember": is_member, 
                                "bringBall": bring_ball,
                                "occupyCourt": occupy_court, 
                                "timestamp": ts
                            })
                            
                            # 2. 額外朋友 (最多 2 位)
                            for f_i in range(friend_count):
                                new_entries.append({
                                    "id": str(uuid.uuid4()), 
                                    "name": f"{name_input} (朋友{f_i+1})", 
                                    "count": 1,
                                    "isMember": False, # 朋友預設非團員
                                    "bringBall": False, 
                                    "occupyCourt": False, 
                                    "timestamp": ts + 0.1 + (f_i * 0.01)
                                })
                            
                            st.session_state.data["sessions"][date_key].extend(new_entries)
                            save_data(st.session_state.data)
                            st.success(f"報名成功！總共新增 {len(new_entries)} 位。")
                            st.rerun()
                        else:
                            st.error("請輸入名字")

                st.info("""
                **📌 報名規則**
                * 總上限 **3 人** (第一位 + 最多 2 位朋友)。
                * 若您是幫朋友代報且自己不來，請在「姓名欄」填朋友的名字。
                """)

            # [右側] 名單顯示
            with col_list:
                # 刪除功能
                def delete_p(pid, d_key):
                    st.session_state.data["sessions"][d_key] = [
                        p for p in st.session_state.data["sessions"][d_key] if p["id"] != pid
                    ]
                    save_data(st.session_state.data)
                    st.rerun()

                # 優先權警告
                has_mem_wait = any(p.get('isMember') for p in wait_list)
                has_guest_main = any(not p.get('isMember') for p in main_list)
                if has_mem_wait and has_guest_main:
                    st.markdown(f"""<div class="priority-alert">
                    ⚠️ <b>優先權提醒 ({date_key})</b><br>
                    候補有團員，但正選有名朋友。建議協調讓團員遞補。
                    </div>""", unsafe_allow_html=True)

                # 正選列表
                st.subheader("✅ 正選名單")
                if main_list:
                    for idx, p in enumerate(main_list):
                        cols = st.columns([0.5, 3, 2, 1])
                        cols[0].write(f"{idx+1}.")
                        name_str = p['name'] + (" ⭐" if p.get('isMember') else "")
                        cols[1].write(name_str)
                        
                        tags = []
                        if p.get('bringBall'): tags.append("🏀")
                        if p.get('occupyCourt'): tags.append("🚩")
                        cols[2].write(" ".join(tags))
                        
                        if cols[3].button("刪", key=f"del_{p['id']}"):
                            delete_p(p['id'], date_key)
                else:
                    st.write("尚無人報名")

                # 候補列表
                if wait_list:
                    st.divider()
                    st.subheader(f"⏳ 候補名單 ({len(wait_list)})")
                    for idx, p in enumerate(wait_list):
                        cols = st.columns([0.5, 5, 1])
                        cols[0].write(f"{idx+1}.")
                        cols[1].write(p['name'] + (" (團員)" if p.get('isMember') else ""))
                        if cols[2].button("取消", key=f"del_w_{p['id']}"):
                            delete_p(p['id'], date_key)
