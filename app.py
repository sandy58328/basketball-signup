import streamlit as st
import json
import time
import uuid
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
# 1. 資料庫連線 (Google Sheets)
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
        # [V4.4] 自動補齊 leaves 欄位 (舊資料相容)
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

if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'edit_target' not in st.session_state:
    st.session_state.edit_target = None

# ==========================================
# 2. UI 設定 (CSS)
# ==========================================
st.set_page_config(page_title="晴女籃球報名", page_icon="☀️", layout="centered") 

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; color: #334155 !important; }
    html, body, [class*="css"], p, div, label, span, h1, h2, h3, .stMarkdown { font-family: 'Noto Sans TC', sans-serif; color: #334155 !important; }
    .block-container { padding-top: 4rem !important; padding-bottom: 5rem !important; }
    header {background: transparent !important;}
    [data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stStatusWidget"], footer, #MainMenu, .stDeployButton {display: none !important;}
    [data-testid="stSidebarCollapsedControl"] { display: block !important; visibility: visible !important; color: #334155 !important; background-color: white !important; border-radius: 50%; padding: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 999999 !important; }
    .header-box { background: white; padding: 1.5rem 1rem; border-radius: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; }
    .header-title { font-size: 1.6rem; font-weight: 800; color: #1e293b !important; letter-spacing: 1px; margin-bottom: 5px; }
    .header-sub { font-size: 0.9rem; color: #64748b !important; font-weight: 500; }
    .info-pill { background: #f1f5f9; padding: 4px 14px; border-radius: 30px; font-size: 0.8rem; font-weight: 600; color: #475569 !important; display: inline-block; margin-top: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab"] { height: 38px; background-color: transparent; border-radius: 20px; padding: 0 16px; font-size: 0.9rem; border: 1px solid transparent; color: #64748b !important; font-weight: 500; }
    .stTabs [aria-selected="true"] { background-color: white; color: #3b82f6 !important; border: none; box-shadow: 0 2px 6px rgba(0,0,0,0.04); font-weight: 700; }
    div[data-baseweb="tab-highlight"] { display: none !important; height: 0 !important; }
    div[data-baseweb="tab-border"] { display: none !important; }
    .player-row { background: white; border: 1px solid #f1f5f9; border-radius: 12px; padding: 8px 10px; margin-bottom: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); transition: transform 0.1s; display: flex; align-items: center; width: 100%; min-height: 40px; }
    .player-row:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    .list-index { color: #cbd5e1 !important; font-weight: 700; font-size: 0.9rem; margin-right: 12px; min-width: 20px; text-align: right;}
    .list-index-flower { color: #f472b6 !important; font-weight: 700; font-size: 1rem; margin-right: 12px; min-width: 20px; text-align: right;}
    .list-name { color: #334155 !important; font-weight: 700; font-size: 1.15rem; letter-spacing: 0.5px; flex-grow: 1; line-height: 1.2; }
    .badge { padding: 2px 6px; border-radius: 5px; font-size: 0.7rem; font-weight: 700; margin-left: 4px; display: inline-block; vertical-align: middle; transform: translateY(-1px);}
    .badge-sunny { background: #fffbeb; color: #d97706 !important; }
    .badge-ball { background: #fff7ed; color: #c2410c !important; }
    .badge-court { background: #eff6ff; color: #1d4ed8 !important; }
    .badge-visit { background: #fdf2f8; color: #db2777 !important; border: 1px solid #fce7f3; }
    .list-btn-col button { border: none !important; background: transparent !important; padding: 0px !important; color: #cbd5e1 !important; font-size: 14px !important; line-height: 1 !important; height: 32px !important; width: 32px !important; display: flex; justify-content: center; align-items: center; margin: 0 !important; }
    .list-btn-e button:hover { color: #3b82f6 !important; background: #eff6ff !important; border-radius: 6px; }
    .list-btn-d button { color: unset !important; opacity: 0.7; font-size: 12px !important; }
    .list-btn-d button:hover { opacity: 1; background: #fef2f2 !important; border-radius: 6px; }
    .list-btn-up button { padding: 0px 8px !important; height: 26px !important; font-size: 0.75rem !important; border-radius: 6px !important; background: #e0f2fe !important; color: #0284c7 !important; font-weight: 600 !important; width: auto !important; }
    .progress-container { width: 100%; background: #e2e8f0; border-radius: 6px; height: 6px; margin-top: 8px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
    .progress-info { display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748b !important; margin-bottom: 2px; font-weight: 600; }
    .edit-box { border: 1px solid #3b82f6; border-radius: 12px; padding: 12px; background: #eff6ff; margin-bottom: 10px; color: #334155 !important; }
    .rules-box { background-color: white; border-radius: 16px; padding: 20px; border: 1px solid #f1f5f9; box-shadow: 0 4px 15px rgba(0,0,0,0.02); margin-top: 15px; color: #475569 !important; }
    .rules-header { font-size: 1rem; font-weight: 800; color: #334155 !important; margin-bottom: 15px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; letter-spacing: 1px; }
    .rules-row { display: flex; align-items: flex-start; margin-bottom: 12px; }
    .rules-icon { font-size: 1.1rem; margin-right: 12px; line-height: 1.4; }
    .rules-content { font-size: 0.9rem; color: #64748b !important; line-height: 1.5; }
    .rules-content b { color: #475569 !important; font-weight: 700; }
    .rules-footer { margin-top: 15px; font-size: 0.85rem; color: #94a3b8 !important; text-align: right; font-weight: 500; }
    .stCode { font-family: monospace !important; font-size: 0.8rem !important; }
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
        
        # 1. 新增場次
        new_date = st.date_input("新增日期", min_value=date.today())
        if st.button("➕ 新增場次"):
            current_data = load_data() 
            if (d:=str(new_date)) not in current_data["sessions"]:
                current_data["sessions"][d] = []
                save_data(current_data)
                st.session_state.data = current_data
                st.rerun()
        st.markdown("---")
        
        st.session_state.data = load_data()
        dates = sorted(st.session_state.data["sessions"].keys())
        
        if dates:
            hidden = st.multiselect("隱藏場次", dates, default=[d for d in st.session_state.data["hidden"] if d in dates])
            if set(hidden) != set(st.session_state.data["hidden"]):
                st.session_state.data["hidden"] = hidden
                save_data(st.session_state.data)
                st.rerun()
            st.markdown("---")
            if st.button("🗑️ 刪除選定日期"):
               del_d = st.selectbox("選擇日期", dates)
               del st.session_state.data["sessions"][del_d]
               save_data(st.session_state.data)
               st.rerun()
        
        # [V4.4] 請假管理系統
        st.markdown("---")
        with st.expander("🏖️ 請假管理 (新增/刪除)"):
            # 整理所有歷史名單 (當作選項)
            all_players = set()
            for s_list in st.session_state.data["sessions"].values():
                for p in s_list:
                    if "(友" not in p['name']: all_players.add(p['name'])
            
            if all_players:
                leave_name = st.selectbox("選擇團員", sorted(list(all_players)))
                leave_month = st.date_input("選擇請假月份 (選該月任意一天即可)", min_value=date.today().replace(day=1))
                leave_str = leave_month.strftime("%Y-%m
