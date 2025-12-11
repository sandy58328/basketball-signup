import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime, date

# ==========================================
# 0. 管理員設定
# ==========================================
ADMIN_PASSWORD = "sunny"

# ==========================================
# 1. 設定與資料處理
# ==========================================
FILE_PATH = 'basketball_data.json'
MAX_CAPACITY = 20

def load_data():
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
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# ==========================================
# 2. 介面樣式
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="wide")

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
    .priority-alert {
        background-color: #fefce8; border-left: 5px solid #eab308;
        padding: 1rem; color: #854d0e; margin-bottom: 1rem;
    }
    /* 特別加強按鈕樣式 */
    button[kind="secondary"] {
        padding: 0px 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄：場次管理
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    pwd_input = st.text_input("輸入管理密碼解鎖功能", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        st.success("🔓 已解鎖")
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
        sessions = st.session_state.data["sessions"]
        if sessions:
            del_date = st.selectbox("刪除日期", options=sorted(sessions.keys()))
            if st.button("確認刪除"):
                del st.session_state.data["sessions"][del_date]
                save_data(st.session_state.data)
                st.success("已刪除")
                st.rerun()
    else:
        if pwd_input: st.error("密碼錯誤")

# ==========================================
# 4. 主頁面邏輯
# ==========================================

st.markdown("""
    <div class="header-box">
        <h1 style="margin:0; font-size: 2.5rem; font-weight: 800; letter-spacing: 1px;">晴女☀️在場邊等妳🌈</h1>
        <p style="margin:5px 0 15px 0; font-size: 0.9rem; opacity: 0.9; letter-spacing: 1px;">✨ 希望永遠是晴天 ✨</p>
        <div class="info-tag">
            📍 地點：朱崙公園 &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 時間：19:00開打
        </div>
    </div>
""", unsafe_allow_html=True)

all_dates = sorted(st.session_state.data["sessions"].keys())

if not all_dates:
    st.info("👋 請版主在左側新增場次！")
else:
    tabs = st.tabs([f"📅 {d}" for d in all_dates])

    for i, date_key in enumerate(all_dates):
        with tabs[i]:
            current_players = st.session_state.data["sessions"][date_key]
            
            # 排序邏輯
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
                    wait_list.
