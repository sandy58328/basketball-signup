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
# 2. UI 極簡禪意風格 (CSS) - V3.28 最終身份核實版
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
    .badge-visit { background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }

    /* 按鈕樣式 */
    [data-testid="stHorizontalBlock"] { align-items: center !important; gap: 0rem !important; }
    [data-testid="column"] { padding: 0px 2px !important; } 
    
    .list-btn-col button {
        border: none !important; 
        background: transparent !important;
        padding: 0px !important;
        color: #cbd5e1 !important
