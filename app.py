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
# ⚠️ 上線後請換成真實網址
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
# 2. UI 極簡禪意風格 (CSS) - V3.29 結構修復版
# ==========================================
st.set_page_config(page_title="晴女籃球報名", page_icon="🌸", layout="centered") 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; background-color: #f8fafc; }
    
    /* 修正頂部被切的問題 */
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

    /* Tabs (無紅線) */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 38px; background-color: transparent; border-radius: 20px;
        padding: 0 16px; font-size: 0.9rem; border: 1px solid transparent; color: #64748b; font-weight: 500;
    }
    .stTabs
