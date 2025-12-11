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
MAX_CAPACITY = 20

def load_data():
    """從 JSON 檔案讀取資料，如果沒有則回傳預設值"""
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"gameDate": str(date.today()), "players": []}
    return {"gameDate": str(date.today()), "players": []}

def save_data(data):
    """儲存資料到 JSON 檔案"""
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化 Session State
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# ==========================================
# 2. 介面樣式 (CSS Styling)
# ==========================================
st.set_page_config(page_title="Sunny Girls Basketball", page_icon="☀️", layout="wide")

# 自定義 CSS
st.markdown("""
    <style>
    .main { background-color: #f0f9ff; }
    .stButton>button { width: 100%; border-radius: 8px; }
    .header-box {
        background: linear-gradient(to right, #38bdf8, #3b82f6, #6366f1);
        padding: 2rem; border-radius: 0 0 1rem 1rem; color: white; margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stat-card {
        background: white; padding: 1rem; border-radius: 0.75rem;
        border: 1px solid #e0f2fe; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .priority-alert {
        background-color: #fefce8; border-left: 5px solid #eab308;
        padding: 1rem; border-radius: 0 0.5rem 0.5rem 0; color: #854d0e; margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 頁面主體 (UI Layout)
# ==========================================

data = st.session_state.data
players = data.get("players", [])
game_date = data.get("gameDate", str(date.today()))

# --- Header 區塊 ---
st.markdown(f"""
    <div class="header-box">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; color: #fde047; margin-bottom: 8px;">
                    <span style="font-size: 1.5rem;">☀️</span>
                    <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 99px; font-size: 0.8rem; font-weight: bold;">Sunny Girls Basketball</span>
                </div>
                <h1 style="margin: 0; font-size: 2rem; font-weight: bold;">晴女☀️在場邊等妳🌈</h1>
                <p style="margin-top: 8px; color: #e0f2fe;">✨ 祈禱永遠晴天</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); min-width: 250px;">
                <div style="margin-bottom: 8px;">🕒 <span style="font-weight: bold; margin-left: 5px;">19:00 開打</span></div>
                <div>📍 <span style="font-weight: bold; margin-left: 5px;">台北市朱崙公園籃球場</span></div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 日期選擇 ---
col_date, _ = st.columns([1, 3])
with col_date:
    new_date = st.date_input("📅 設定打球日期", value=datetime.strptime(game_date, "%Y-%m-%d") if game_date else date.today())
    if str(new_date) != game_date:
        data["gameDate"] = str(new_date)
        save_data(data)
        st.rerun()

# --- 數據邏輯處理 ---
# 依照報名時間排序
sorted_players = sorted(players, key=lambda x: x.get('timestamp', 0))

# 分割正選與候補
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

# 計算統計數據
total_registered = sum(p.get('count', 1) for p in players)
total_waitlist = sum(p.get('count', 1) for p in wait_list)
total_ball = len([p for p in players if p.get('bringBall')])
total_court = len([p for p in players if p.get('occupyCourt')])

# --- 統計數據欄 ---
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="stat-card"><div style="font-size:0.75rem;color:#6b7280;">總報名人數</div><div style="font-size:1.5rem;font-weight:bold;color:#1f2937;">{total_registered} 人</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat-card" style="border-color:#fef2f2;"><div style="font-size:0.75rem;color:#ef4444;">目前候補人數</div><div style="font-size:1.5rem;font-weight:bold;color:#dc2626;">{total_waitlist} 人</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat-card"><div style="font-size:0.75rem;color:#6b7280;">🏀 幫忙帶球</div><div style="font-size:1.5rem;font-weight:bold;color:#f97316;">{total_ball}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="stat-card"><div style="font-size:0.75rem;color:#6b7280;">🚩 幫忙佔場</div><div style="font-size:1.5rem;font-weight:bold;color:#16a34a;">{total_court}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 主佈局 ---
left_col, right_col = st.columns([1, 2])

# ================= Left Column: 報名表單 =================
with left_col:
    st.subheader("📝 我要報名")
    
    with st.form("signup_form", clear_on_submit=True):
        name_input = st.text_input("你的名字 / 暱稱")
        is_member = st.checkbox("我是團員 (Member)")
        
        # 修改處：這裡設定 max_value=2
        friend_count = st.number_input("攜帶朋友數量 (不含自己，上限2人)", min_value=0, max_value=2, value=0)
        
        c_ball, c_court = st.columns(2)
        bring_ball = c_ball.checkbox("🏀 幫忙帶球")
        occupy_court = c_court.checkbox("🚩 幫忙佔場")
        
        submitted = st.form_submit_button("確認報名")
        
        if submitted and name_input:
            timestamp = time.time()
            new_entries = []
            
            # 1. 加入主要報名者
            new_entries.append({
                "id": str(uuid.uuid4()),
                "name": name_input,
                "count": 1,
                "isMember": is_member,
                "bringBall": bring_ball,
                "occupyCourt": occupy_court,
                "timestamp": timestamp
            })
            
            # 2. 自動拆分朋友為獨立名單
            if friend_count > 0:
                for i in range(friend_count):
                    friend_name = f"{name_input} (朋友{i+1})"
                    new_entries.append({
                        "id": str(uuid.uuid4()),
                        "name": friend_name,
                        "count": 1,
                        "isMember": False, 
                        "bringBall": False, 
                        "occupyCourt": False,
                        "timestamp": timestamp + 0.1 + (i * 0.01)
                    })
            
            data["players"].extend(new_entries)
            save_data(data)
            st.success(f"報名成功！已新增 {len(new_entries)} 位。")
            st.rerun()

    st.info("""
    **🏆 報名規則說明**
    * 上限 **20 人**，超過系統自動轉候補。
    * 每人可帶朋友 **(上限2位)**，朋友將列為獨立名單。
    * 若遇額滿，**候補團員 (⭐)** 優先取代非團員。
    * 🌧️ 若遇雨天，當日 17:00 前通知是否取消。
    """)

# ================= Right Column: 名單列表 =================
with right_col:
    
    def delete_player(player_id):
        data["players"] = [p for p in data["players"] if p["id"] != player_id]
        save_data(data)
        st.rerun()

    # 優先權偵測
    member_on_waitlist = any(p.get('isMember') for p in wait_list)
    guest_on_mainlist = any(not p.get('isMember') for p in main_list)
    
    if member_on_waitlist and guest_on_mainlist:
        st.markdown("""
        <div class="priority-alert">
            <h4>⚠️ 優先權調整建議</h4>
            <p>偵測到 <strong>候補名單中有團員</strong>，而正選名單中有 <strong>非團員 (朋友)</strong>。</p>
            <p>建議手動協調，讓團員遞補上來。</p>
        </div>
        """, unsafe_allow_html=True)

    # --- 正選名單 ---
    st.subheader(f"✅ 正選名單 ({len(main_list)}/{MAX_CAPACITY})")
    
    if len(main_list) > 0:
        for idx, p in enumerate(main_list):
            with st.container():
                # 修改處：移除了顯示時間的欄位，調整了寬度比例
                c1, c2, c3, c4 = st.columns([0.5, 3.5, 2, 1])
                
                c1.write(f"**{idx+1}.**")
                
                name_display = p['name']
                if p.get('isMember'):
                    name_display += " ⭐"
                c2.write(name_display)
                
                tags = []
                if p.get('bringBall'): tags.append("🏀")
                if p.get('occupyCourt'): tags.append("🚩")
                c3.write(" ".join(tags))
                
                # 修改處：這裡刪除了顯示時間的代碼
                
                if c4.button("刪除", key=f"del_{p['id']}"):
                    delete_player(p['id'])
                st.markdown("---")
    else:
        st.text("目前還沒有人報名，快來搶頭香！")

    # --- 候補名單 ---
    if len(wait_list) > 0:
        st.subheader(f"⏳ 候補名單 ({len(wait_list)})")
        st.markdown("---")
        for idx, p in enumerate(wait_list):
            with st.container():
                c1, c2, c3 = st.columns([0.5, 5, 1])
                c1.write(f"{idx+1}.")
                
                name_display = p['name']
                if p.get('isMember'):
                    name_display += " (團員優先)" 
                c2.write(name_display)
                
                if c3.button("取消", key=f"del_wait_{p['id']}"):
                    delete_player(p['id'])

