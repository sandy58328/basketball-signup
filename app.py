import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime, date

# ==========================================
# 0. 管理員設定 (Admin Config)
# ==========================================
ADMIN_PASSWORD = "sunny"  # 管理員密碼

# ==========================================
# 1. 設定與資料處理 (Backend Logic)
# ==========================================

FILE_PATH = 'basketball_data.json'
MAX_CAPACITY = 20  # 每場上限

def load_data():
    """從 JSON 讀取資料"""
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
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄：場次管理 (含密碼鎖)
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    
    # --- 密碼鎖 ---
    pwd_input = st.text_input("輸入管理密碼解鎖功能", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        st.success("🔓 管理員模式已解鎖")
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
            
    else:
        if pwd_input:
            st.error("密碼錯誤 ❌")
        st.caption("一般球友請忽略此區塊 😊")

# ==========================================
# 4. 主頁面邏輯
# ==========================================

# --- 標題區 ---
st.markdown(f"""
    <div class="header-box">
        <h1 style="margin:0; font-size: 2.5rem; font-weight: 800; letter-spacing: 1px;">晴女☀️在場邊等妳🌈</h1>
        <p style="
