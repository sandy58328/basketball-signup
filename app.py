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
    /* 按鈕樣式 */
    button[kind="secondary"] {
        padding: 0px 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄：場次管理
# ==========================================
with st.sidebar:
    st.header("⚙️ 場次管理員")
    pwd_input = st.text_input("輸入管理密碼解鎖功能", type="password")
    
    # 判斷是否為管理員
    is_admin = (pwd_input == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("🔓 已解鎖 (管理員模式)")
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
            
            # 排序邏輯：依照 timestamp
            sorted_players = sorted(current_players, key=lambda x: x.get('timestamp', 0))
            main_list = []
            wait_list = []
            current_count = 0

            # 分組：正選 vs 候補
            for p in sorted_players:
                p_count = p.get('count', 1)
                if current_count + p_count <= MAX_CAPACITY:
                    main_list.append(p)
                    current_count += p_count
                else:
                    wait_list.append(p)
            
            # 統計數據
            total_reg = sum(p.get('count', 1) for p in current_players)
            c1, c2, c3 = st.columns(3)
            c1.metric("總人數", f"{total_reg}")
            c2.metric("正選", f"{len(main_list)} / {MAX_CAPACITY}")
            c3.metric("候補", f"{len(wait_list)}")
            st.markdown("---")

            col_form, col_list = st.columns([1, 2])

            # [左側] 報名表單
            with col_form:
                st.subheader("📝 我要報名")
                with st.form(f"form_{date_key}", clear_on_submit=True):
                    name_input = st.text_input("球員姓名")
                    
                    # [修改重點] 勾選框加上星星符號
                    is_member = st.checkbox("我是團員 ⭐", key=f"mem_{date_key}")
                    
                    total_count = st.number_input("報名總人數 (含自己, Max 3)", 1, 3, 1, key=f"tot_{date_key}")
                    
                    c_b, c_c = st.columns(2)
                    bring_ball = c_b.checkbox("🏀帶球", key=f"b_{date_key}")
                    occupy_court = c_c.checkbox("🚩佔場", key=f"c_{date_key}")
                    
                    if st.form_submit_button("送出"):
                        if name_input:
                            ts = time.time()
                            new_entries = []
                            # 主報名者
                            new_entries.append({
                                "id": str(uuid.uuid4()), "name": name_input, "count": 1,
                                "isMember": is_member, "bringBall": bring_ball,
                                "occupyCourt": occupy_court, "timestamp": ts
                            })
                            # 朋友
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

                # [修改重點] 規則文字更新
                st.info("""
                **📌 規則**
                * 上限 20 人，單次報名上限 3 人含本人，超過轉候補。
                * 候補團員中⭐團員，可優先依序遞補，而原先正選之非⭐團員，將轉為候補。
                * 雨天當日 17:00 前通知是否開團。
                """)

            # [右側] 名單顯示區
            with col_list:
                # 刪除功能
                def delete_p(pid, d_key):
                    st.session_state.data["sessions"][d_key] = [
                        p for p in st.session_state.data["sessions"][d_key] if p["id"] != pid
                    ]
                    save_data(st.session_state.data)
                    st.rerun()

                # 遞補功能
                def promote_p(wait_pid, d_key, target_main_list):
                    all_p = st.session_state.data["sessions"][d_key]
                    wait_person = next((p for p in all_p if p['id'] == wait_pid), None)
                    
                    # 找正選最後一個非團員
                    target_guest = None
                    for p in reversed(target_main_list):
                        if not p.get('isMember'):
                            target_id = p['id']
                            target_guest = next((op for op in all_p if op['id'] == target_id), None)
                            break
                    
                    if wait_person and target_guest:
                        # 交換時間
                        t_temp = target_guest['timestamp']
                        target_guest['timestamp'] = wait_person['timestamp']
                        wait_person['timestamp'] = t_temp
                        save_data(st.session_state.data)
                        st.success(f"遞補成功！團員 {wait_person['name']} 已晉升正選，{target_guest['name']} 轉為候補。")
                        st.rerun()
                    elif wait_person and not target_guest:
                        st.error("❌ 無法遞補：正選名單全是團員，無路人可替換。")

                # --- 顯示正選名單 ---
                st.subheader("✅ 正選名單")
                if main_list:
                    for idx, p in enumerate(main_list):
                        # [對齊] 0.5 : 3 : 2 : 0.5
                        cols = st.columns([0.5, 3, 2, 0.5]) 
                        cols[0].write(f"{idx+1}.")
                        cols[1].write(p['name'] + (" ⭐" if p.get('isMember') else ""))
                        
                        # 標籤欄位
                        tag_s = []
                        if p.get('bringBall'): tag_s.append("🏀")
                        if p.get('occupyCourt'): tag_s.append("🚩")
                        cols[2].write(" ".join(tag_s))
                        
                        # 刪除按鈕
                        if cols[3].button("❌", key=f"d_{p['id']}"):
                            delete_p(p['id'], date_key)
                else:
                    st.write("尚無人報名")

                # --- 顯示候補名單 ---
                if wait_list:
                    st.divider()
                    st.subheader(f"⏳ 候補名單 ({len(wait_list)})")
                    
                    for idx, p in enumerate(wait_list):
                        can_promote = p.get('isMember')
                        
                        # [對齊] 0.5 : 3 : 1 : 1 : 0.5
                        cols = st.columns([0.5, 3, 1, 1, 0.5]) 

                        # 1. 序號
                        cols[0].write(f"{idx+1}.")
                        
                        # 2. 姓名 (只含星星)
                        cols[1].write(p['name'] + (" ⭐" if p.get('isMember') else ""))
                        
                        # 3. 標籤 (獨立欄位)
                        tag_s = []
                        if p.get('bringBall'): tag_s.append("🏀")
                        if p.get('occupyCourt'): tag_s.append("🚩")
                        cols[2].write(" ".join(tag_s))
                        
                        # 4. 遞補按鈕 (只有管理員看得到)
                        if can_promote and is_admin:
                            btn_key = f"up_{p['id']}"
                            if cols[3].button("⬆️遞補", key=btn_key):
                                promote_p(p['id'], date_key, main_list)
                        
                        # 5. 刪除按鈕
                        del_key = f"dw_{p['id']}"
                        if cols[4].button("❌", key=del_key):
                            delete_p(p['id'], date_key)
