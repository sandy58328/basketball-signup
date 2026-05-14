import streamlit as st
import json
import time
import uuid
import re
from datetime import datetime, date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 0. 設定區
# ==========================================
MAX_CAPACITY = 20
APP_URL = "https://sunny-girls-basketball.streamlit.app"
SHEET_NAME = "basketball_db"

def get_admin_password():
    try:
        return st.secrets["admin_password"]
    except Exception:
        return "sunny"  # fallback，建議在 secrets 設定

# ==========================================
# 1. CSS 樣式
# ==========================================
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');

    /* ── 基礎 ── */
    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; color: #334155 !important; }
    html, body, [class*="css"], p, div, label, span, h1, h2, h3, .stMarkdown {
        font-family: 'Noto Sans TC', sans-serif; color: #334155 !important;
    }
    .block-container { padding-top: 4rem !important; padding-bottom: 5rem !important; }
    header { background: transparent !important; }
    [data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stStatusWidget"],
    footer, #MainMenu, .stDeployButton { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }

    /* ── Header ── */
    .header-box {
        background: white; padding: 1.5rem 1rem; border-radius: 20px;
        text-align: center; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #f1f5f9;
    }
    .header-title { font-size: 1.6rem; font-weight: 800; color: #1e293b !important; letter-spacing: 1px; margin-bottom: 5px; }
    .header-sub   { font-size: 0.9rem; color: #64748b !important; font-weight: 500; }
    .info-pill {
        background: #f1f5f9; padding: 4px 14px; border-radius: 30px;
        font-size: 0.8rem; font-weight: 600; color: #475569 !important;
        display: inline-block; margin-top: 10px;
    }

    /* ── 名單列表 ── */
    .player-row {
        background: white; border: 1px solid #f1f5f9; border-radius: 12px;
        padding: 8px 10px; margin-bottom: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        display: flex; align-items: center; width: 100%; min-height: 40px;
    }
    .list-index        { color: #cbd5e1 !important; font-weight: 700; font-size: 0.9rem; margin-right: 12px; min-width: 20px; text-align: right; }
    .list-index-flower { color: #f472b6 !important; font-weight: 700; font-size: 1rem;  margin-right: 12px; min-width: 20px; text-align: right; }
    .list-name         { color: #334155 !important; font-weight: 700; font-size: 1.15rem; flex-grow: 1; line-height: 1.2; }

    /* ── 標籤 ── */
    .badge        { padding: 2px 6px; border-radius: 5px; font-size: 0.7rem; font-weight: 700; margin-left: 4px; display: inline-block; vertical-align: middle; }
    .badge-sunny  { background: #fffbeb; color: #d97706 !important; }
    .badge-ball   { background: #fff7ed; color: #c2410c !important; }
    .badge-court  { background: #eff6ff; color: #1d4ed8 !important; }
    .badge-visit  { background: #fdf2f8; color: #db2777 !important; border: 1px solid #fce7f3; }

    /* ── 進度條 ── */
    .progress-container { width: 100%; background: #e2e8f0; border-radius: 6px; height: 6px; margin-top: 8px; overflow: hidden; }
    .progress-bar       { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
    .progress-info      { display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748b !important; margin-bottom: 2px; font-weight: 600; }

    /* ── 編輯框 ── */
    .edit-box { border: 1px solid #3b82f6; border-radius: 12px; padding: 12px; background: #eff6ff; margin-bottom: 10px; }

    /* ── 規則說明 ── */
    .rules-box    { background-color: white; border-radius: 16px; padding: 20px; border: 1px solid #f1f5f9; box-shadow: 0 4px 15px rgba(0,0,0,0.02); margin-top: 15px; }
    .rules-header { font-size: 1rem; font-weight: 800; color: #334155 !important; margin-bottom: 15px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; }
    .rules-row    { display: flex; align-items: flex-start; margin-bottom: 12px; }
    .rules-icon   { font-size: 1.1rem; margin-right: 12px; line-height: 1.4; }
    .rules-content   { font-size: 0.9rem; color: #64748b !important; line-height: 1.5; }
    .rules-content b { color: #475569 !important; font-weight: 700; }
    .rules-footer    { margin-top: 15px; font-size: 0.85rem; color: #94a3b8 !important; text-align: right; font-weight: 500; }

    /* ── 統計報表列 ── */
    .stat-row {
        background: white; border: 1px solid #f1f5f9; border-radius: 12px;
        padding: 10px 14px; margin-bottom: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .stat-name   { font-weight: 700; font-size: 1rem; color: #1e293b !important; }
    .stat-detail { font-size: 0.78rem; color: #94a3b8 !important; margin-top: 2px; }

    /* ── 按鈕 ── */
    button[data-testid="stBaseButton-secondary"] { width: 100% !important; height: 36px !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料庫
# ==========================================
@st.cache_resource
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        st.error(f"❌ 資料庫連線失敗：{e}")
        return None

def load_data() -> dict:
    sheet = get_sheet()
    if not sheet:
        return {"sessions": {}, "hidden": [], "leaves": {}, "removed_members": []}
    try:
        raw = sheet.acell('A1').value
        if not raw:
            return {"sessions": {}, "hidden": [], "leaves": {}, "removed_members": []}
        data = json.loads(raw)
        data.setdefault("leaves", {})
        data.setdefault("sessions", {})
        data.setdefault("hidden", [])
        data.setdefault("removed_members", [])   # 退群名單（正規化後的 key）
        return data
    except Exception:
        return {"sessions": {}, "hidden": [], "leaves": {}, "removed_members": []}

def save_data(data: dict):
    sheet = get_sheet()
    if not sheet:
        return
    try:
        sheet.update_acell('A1', json.dumps(data, ensure_ascii=False))
    except Exception as e:
        st.error(f"❌ 資料儲存失敗：{e}")

# ==========================================
# 3. 工具函式
# ==========================================
NAME_ALIASES: dict[str, str] = {
    "金閃閃": "kingsley金閃閃",
    "冬青":   "冬青得來速",
    "得來速": "冬青得來速",
    "菜":     "小菜",
    "小菜":   "小菜",
}

def normalize_name(name: str) -> str:
    if not name:
        return ""
    clean = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name).replace(" ", "").lower()
    for key, val in NAME_ALIASES.items():
        if key in clean:
            return val
    return clean

def is_friend(name: str) -> bool:
    return any(k in name for k in ["友", "（", "("])

def update_player(pid, date_key, name, is_member, bring_ball, occupy_court, is_visitor):
    data = load_data()
    player = next((p for p in data["sessions"][date_key] if p['id'] == pid), None)
    if not player:
        return
    old_name = player['name']
    final_is_member = False if is_friend(name) else is_member

    if st.session_state.is_admin and is_member and old_name != name:
        for p in data["sessions"][date_key]:
            if p['name'].startswith(f"{old_name} (") or p['name'].startswith(f"{old_name} （"):
                p['name'] = p['name'].replace(old_name, name, 1)

    player.update({
        'name':        name,
        'isMember':    final_is_member,
        'bringBall':   bring_ball,
        'occupyCourt': occupy_court,
        'count':       0 if is_visitor else 1,
    })
    save_data(data)
    st.session_state.edit_target = None
    st.toast("✅ 資料已更新")
    time.sleep(0.5)
    st.rerun()

def delete_player(pid, date_key):
    data = load_data()
    target = next((p for p in data["sessions"][date_key] if p['id'] == pid), None)
    if not target:
        return
    name = target['name']
    if is_friend(name):
        data["sessions"][date_key] = [p for p in data["sessions"][date_key] if p['id'] != pid]
    else:
        data["sessions"][date_key] = [
            p for p in data["sessions"][date_key]
            if p['id'] != pid
            and not (
                p['name'].startswith(f"{name} (")
                or p['name'].startswith(f"{name} （")
                or p['name'] == f"{name}之友"
            )
        ]
    if st.session_state.edit_target == pid:
        st.session_state.edit_target = None
    save_data(data)
    st.toast("🗑️ 已刪除")
    time.sleep(0.5)
    st.rerun()

# ==========================================
# 4. 名單渲染
# ==========================================
def render_list(players, date_key, is_wait=False, can_edit=True, is_admin_mode=False):
    if not players:
        if not is_wait:
            st.markdown("""
            <div style="text-align:center;padding:40px;color:#cbd5e1;">
                <div style="font-size:36px;">🏀</div><p>尚未有人報名</p>
            </div>""", unsafe_allow_html=True)
        return

    sorted_players = sorted(players, key=lambda x: x.get('timestamp', 0))
    counter = 0

    for p in sorted_players:
        is_playing = p.get('count', 1) > 0
        if is_playing:
            counter += 1
            idx_str, idx_cls = f"{counter}.", "list-index"
        else:
            idx_str, idx_cls = "🌸", "list-index-flower"

        # ── 編輯模式 ──
        if st.session_state.edit_target == p['id']:
            with st.container():
                st.markdown(f"<div class='edit-box'>✏️ 正在編輯：{p['name']}</div>", unsafe_allow_html=True)
                with st.form(key=f"e_{p['id']}"):
                    new_name  = st.text_input("姓名", p['name'], disabled=not is_admin_mode)
                    c1, c2, c3 = st.columns(3)
                    friend      = is_friend(p['name'])
                    new_member  = c1.checkbox("⭐晴女", p.get('isMember'),    disabled=(not is_admin_mode and friend))
                    new_ball    = c2.checkbox("🏀帶球", p.get('bringBall'),   disabled=friend)
                    new_court   = c3.checkbox("🚩佔場", p.get('occupyCourt'), disabled=friend)
                    new_visitor = st.checkbox("📣 不打球 (加油團)", p.get('count') == 0, disabled=friend)
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 儲存", type="primary"):
                        update_player(p['id'], date_key, new_name, new_member, new_ball, new_court, new_visitor)
                    if b2.form_submit_button("取消"):
                        st.session_state.edit_target = None
                        st.rerun()
        else:
            # ── 顯示模式 ──
            badges = ""
            if p.get('count') == 0:
                badges += "<span class='badge badge-visit'>📣加油團</span>"
            if p.get('isMember') and not is_friend(p['name']):
                badges += "<span class='badge badge-sunny'>晴女</span>"
            if p.get('bringBall'):
                badges += "<span class='badge badge-ball'>帶球</span>"
            if p.get('occupyCourt'):
                badges += "<span class='badge badge-court'>佔場</span>"

            cols = st.columns([6, 1, 1, 2], gap="small")
            with cols[0]:
                st.markdown(
                    f"""<div class="player-row">
                        <span class="{idx_cls}">{idx_str}</span>
                        <span class="list-name">{p['name']}</span>{badges}
                    </div>""",
                    unsafe_allow_html=True,
                )
            if can_edit:
                with cols[1]:
                    if st.button("✏️", key=f"be_{p['id']}"):
                        st.session_state.edit_target = p['id']
                        st.rerun()
                with cols[2]:
                    with st.popover("❌"):
                        st.write("確定取消報名？")
                        if st.button("確認刪除", key=f"conf_del_{p['id']}", type="primary"):
                            delete_player(p['id'], date_key)

# ==========================================
# 5. 出席統計（含編輯名稱 / 退群）
# ==========================================
def build_stats(raw_data: dict, visible_dates: list) -> tuple[dict, dict]:
    norm_cache: dict[str, str] = {}

    def get_norm(n: str) -> str:
        if n not in norm_cache:
            norm_cache[n] = normalize_name(n)
        return norm_cache[n]

    # 近期報名（只看可見場次）
    member_signups: dict[str, list] = {}
    for sd in visible_dates:
        label = f"{int(sd.split('-')[1])}/{int(sd.split('-')[2])}"
        for p in raw_data["sessions"].get(sd, []):
            if not is_friend(p['name']):
                member_signups.setdefault(get_norm(p['name']), []).append(label)

    # 歷史出席
    stats: dict[str, dict] = {}
    for sd, players in raw_data["sessions"].items():
        day = datetime.strptime(sd, "%Y-%m-%d").date()
        if day > date.today():
            continue
        for p in players:
            if not is_friend(p['name']):
                key = get_norm(p['name'])
                if key not in stats:
                    stats[key] = {"name": p['name'], "last_date": day, "leaves": set()}
                elif day > stats[key]["last_date"]:
                    stats[key]["last_date"] = day
                    stats[key]["name"] = p['name']

    # 請假
    for raw_name, months in raw_data["leaves"].items():
        key = get_norm(raw_name)
        stats.setdefault(key, {"name": raw_name, "last_date": None, "leaves": set()})
        stats[key]["leaves"].update(months)

    return stats, member_signups


def render_stats(raw_data: dict, visible_dates: list):
    removed     = set(raw_data.get("removed_members", []))
    stats, signups = build_stats(raw_data, visible_dates)
    active_keys = [k for k in sorted(stats.keys()) if k not in removed]
    current_month = date.today().strftime("%Y-%m")

    if not active_keys:
        st.info("目前無統計資料")
    else:
        for key in active_keys:
            item          = stats[key]
            last          = item["last_date"]
            leaves_sorted = sorted(item["leaves"])
            signup_str    = ", ".join(signups.get(key, [])) or "—"

            days_ago = (date.today() - last).days if last else 999
            last_str = str(last) if last else "無紀錄"

            if current_month in leaves_sorted:      status = "🏖️ 請假中"
            elif days_ago > 60:                     status = "🔴 逾期"
            elif days_ago > 45:                     status = "🟡 預警"
            else:                                   status = "🟢 活躍"

            leave_str = "　請假：" + ", ".join(leaves_sorted) if leaves_sorted else ""

            # ── 編輯模式 ──
            if st.session_state.get(f"stat_edit_{key}"):
                st.markdown(f"<div class='edit-box'>✏️ 編輯成員：{item['name']}</div>", unsafe_allow_html=True)
                with st.form(key=f"stat_form_{key}"):
                    new_display = st.text_input("顯示名稱", item['name'])
                    b1, b2, b3  = st.columns(3)
                    if b1.form_submit_button("💾 儲存", type="primary"):
                        cur = load_data()
                        old = item['name']
                        for sd in cur["sessions"]:
                            for p in cur["sessions"][sd]:
                                if normalize_name(p['name']) == key and not is_friend(p['name']):
                                    p['name'] = new_display
                                for fp in cur["sessions"][sd]:
                                    if fp['name'].startswith(f"{old} (") or fp['name'].startswith(f"{old} （"):
                                        fp['name'] = fp['name'].replace(old, new_display, 1)
                        if old in cur["leaves"]:
                            cur["leaves"][new_display] = cur["leaves"].pop(old)
                        save_data(cur)
                        st.session_state[f"stat_edit_{key}"] = False
                        st.toast("✅ 名稱已更新")
                        time.sleep(0.5)
                        st.rerun()
                    if b2.form_submit_button("取消"):
                        st.session_state[f"stat_edit_{key}"] = False
                        st.rerun()
                    if b3.form_submit_button("🚪 退群", type="secondary"):
                        cur = load_data()
                        cur.setdefault("removed_members", [])
                        if key not in cur["removed_members"]:
                            cur["removed_members"].append(key)
                        save_data(cur)
                        st.session_state[f"stat_edit_{key}"] = False
                        st.toast(f"👋 {item['name']} 已從統計移除")
                        time.sleep(0.5)
                        st.rerun()
            else:
                # ── 顯示模式 ──
                cols = st.columns([5.5, 1, 1], gap="small")
                with cols[0]:
                    st.markdown(f"""
                    <div class="stat-row">
                        <div class="stat-name">{status} &nbsp; {item['name']}</div>
                        <div class="stat-detail">近期：{signup_str}　最後出席：{last_str}{leave_str}</div>
                    </div>""", unsafe_allow_html=True)
                with cols[1]:
                    if st.button("✏️", key=f"stat_btn_edit_{key}"):
                        st.session_state[f"stat_edit_{key}"] = True
                        st.rerun()
                with cols[2]:
                    with st.popover("🚪"):
                        st.write(f"將「{item['name']}」從統計移除？")
                        if st.button("確認退群", key=f"stat_rm_{key}", type="primary"):
                            cur = load_data()
                            cur.setdefault("removed_members", [])
                            if key not in cur["removed_members"]:
                                cur["removed_members"].append(key)
                            save_data(cur)
                            st.toast(f"👋 {item['name']} 已移除")
                            time.sleep(0.5)
                            st.rerun()

    # 已退群名單（可恢復）
    if removed:
        st.divider()
        with st.expander(f"👻 已退群名單（{len(removed)} 人）", expanded=False):
            removed_stats = {k: stats[k] for k in removed if k in stats}
            if removed_stats:
                for key, item in sorted(removed_stats.items(), key=lambda x: x[1]['name']):
                    c1, c2 = st.columns([5, 1])
                    c1.markdown(f"**{item['name']}**")
                    with c2:
                        if st.button("↩️ 恢復", key=f"stat_restore_{key}"):
                            cur = load_data()
                            if key in cur.get("removed_members", []):
                                cur["removed_members"].remove(key)
                            save_data(cur)
                            st.toast(f"✅ {item['name']} 已恢復")
                            time.sleep(0.5)
                            st.rerun()
            else:
                st.write("（無歷史紀錄）")

# ==========================================
# 6. 初始化
# ==========================================
if 'is_admin'    not in st.session_state: st.session_state.is_admin    = False
if 'edit_target' not in st.session_state: st.session_state.edit_target = None

st.set_page_config(page_title="晴女籃球報名", page_icon="☀️", layout="centered")
load_css()

# ==========================================
# 7. 主畫面
# ==========================================
st.markdown("""
<div class="header-box">
    <div class="header-title">晴女☀️在場邊等妳🌈</div>
    <div class="header-sub">✨ Keep Playing, Keep Shining ✨</div>
    <div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div>
</div>
""", unsafe_allow_html=True)

st.session_state.data = load_data()

# ── 請假 & 公報 ──
col_leave, col_board = st.columns(2)

with col_leave:
    with st.expander("🏖️ 我要請假 (長假登記)"):
        with st.form("leave_form", clear_on_submit=True):
            leave_name  = st.text_input("姓名")
            leave_month = st.date_input("請假月份")
            if st.form_submit_button("送出假單") and leave_name:
                data = load_data()
                month_str = leave_month.strftime("%Y-%m")
                data["leaves"].setdefault(leave_name, [])
                if month_str not in data["leaves"][leave_name]:
                    data["leaves"][leave_name].append(month_str)
                    save_data(data)
                    st.toast("✅ 已登記")
                    time.sleep(1)
                    st.rerun()

with col_board:
    with st.expander("📜 休假公報", expanded=False):
        leaves = st.session_state.data.get("leaves", {})
        merged:      dict[str, set] = {}
        display_map: dict[str, str] = {}
        for raw_name, months in leaves.items():
            key = normalize_name(raw_name)
            merged.setdefault(key, set()).update(months)
            display_map.setdefault(key, raw_name)

        if any(merged.values()):
            for key in sorted(merged.keys()):
                month_list = sorted(merged[key])
                c1, c2 = st.columns([0.82, 0.18])
                with c1:
                    st.markdown(f"**👤 {display_map[key]}**: {', '.join(month_list)}")
                with c2:
                    with st.popover("🗑️"):
                        for m in month_list:
                            if st.button(f"刪除 {m}", key=f"dl_{key}_{m}"):
                                data = load_data()
                                for k in list(data["leaves"].keys()):
                                    if normalize_name(k) == key and m in data["leaves"][k]:
                                        data["leaves"][k].remove(m)
                                        if not data["leaves"][k]:
                                            del data["leaves"][k]
                                save_data(data)
                                st.toast(f"🗑️ 移除 {m}")
                                time.sleep(0.5)
                                st.rerun()
                        st.divider()
                        if st.button("🚨 強制刪除", key=f"f_dl_{key}", type="secondary"):
                            data = load_data()
                            for k in list(data["leaves"].keys()):
                                if normalize_name(k) == key:
                                    del data["leaves"][k]
                            save_data(data)
                            st.toast("🗑️ 強制移除")
                            time.sleep(0.5)
                            st.rerun()
        else:
            st.info("目前無人請假")

# ── 場次 ──
all_dates     = sorted(st.session_state.data["sessions"].keys())
visible_dates = [d for d in all_dates if d not in st.session_state.data.get("hidden", [])]

if not visible_dates:
    st.info("👋 目前沒有開放報名的場次")
else:
    tabs = st.tabs([f"{int(d.split('-')[1])}/{int(d.split('-')[2])}" for d in visible_dates])

    for i, dk in enumerate(visible_dates):
        with tabs[i]:
            dt_obj      = datetime.strptime(dk, "%Y-%m-%d")
            cutoff      = (dt_obj - timedelta(days=1)).replace(hour=12, minute=0, second=0)
            is_expired  = datetime.now() > cutoff
            can_operate = st.session_state.is_admin or (not is_expired)

            all_players = st.session_state.data["sessions"][dk]
            active      = [p for p in all_players if p.get('count', 1) > 0]
            visitor     = [p for p in all_players if p.get('count', 1) == 0]

            prioritized = sorted(active, key=lambda x: (0 if x.get('isMember') else 1, x.get('timestamp', 0)))
            main_active = prioritized[:MAX_CAPACITY]
            wait_active = prioritized[MAX_CAPACITY:]
            main_list   = sorted(main_active + visitor, key=lambda x: x.get('timestamp', 0))
            wait_list   = sorted(wait_active,           key=lambda x: x.get('timestamp', 0))

            curr_count  = len(main_active)
            ball_count  = sum(1 for p in main_active if p.get('bringBall'))
            court_count = sum(1 for p in main_active if p.get('occupyCourt'))
            pct         = min(100, (curr_count / MAX_CAPACITY) * 100)
            bar_color   = '#4ade80' if pct < 50 else '#fbbf24' if pct < 85 else '#f87171'

            st.markdown(f"""
            <div style="margin-bottom:5px;padding:0 4px;">
                <div class="progress-info">
                    <span>正選 ({curr_count}/{MAX_CAPACITY})</span>
                    <span>候補: {len(wait_list)}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width:{pct}%;background:{bar_color};"></div>
                </div>
            </div>
            <div style="display:flex;justify-content:flex-end;gap:15px;font-size:0.85rem;
                        color:#64748b;margin-bottom:25px;font-weight:500;padding-right:5px;">
                <span>🏀 帶球：<b>{ball_count}</b></span>
                <span>🚩 佔場：<b>{court_count}</b></span>
            </div>
            """, unsafe_allow_html=True)

            # ── 報名表單 ──
            with st.expander("📝 點擊報名 / 規則說明", expanded=not is_expired):
                if is_expired and not st.session_state.is_admin:
                    st.warning("⛔ 本場次已截止報名與修改 (前一日 12:00)")

                with st.form(f"signup_{dk}", clear_on_submit=True):
                    player_name  = st.text_input("球員姓名", disabled=not can_operate)
                    c1, c2, c3   = st.columns(3)
                    is_member    = c1.checkbox("⭐晴女",           key=f"m_{dk}", disabled=not can_operate)
                    bring_ball   = c2.checkbox("🏀帶球",           key=f"b_{dk}", disabled=not can_operate)
                    occupy_court = c3.checkbox("🚩佔場",           key=f"c_{dk}", disabled=not can_operate)
                    is_visitor   = st.checkbox("📣 不打球 (加油團)", key=f"v_{dk}", disabled=not can_operate)
                    total        = st.number_input("報名人數", 1, 3, 1, key=f"t_{dk}", disabled=not can_operate)

                    if st.form_submit_button("送出報名", type="primary", disabled=not can_operate):
                        if "友" in player_name:
                            st.error("❌ 請輸入團員姓名")
                        elif player_name:
                            latest        = load_data()
                            existing      = latest["sessions"].get(dk, [])
                            related_count = len([x for x in existing if player_name in x['name']])

                            if related_count == 0 and not is_member:
                                st.error("❌ 第一次報名需勾選「⭐晴女」")
                            elif related_count > 0 and is_member:
                                st.error("❌ 加報朋友請勿重複勾選晴女")
                            elif related_count + total > 3:
                                st.error("❌ 每人上限 3 位")
                            else:
                                ts = time.time()
                                for k in range(total):
                                    first     = (k == 0 and related_count == 0)
                                    full_name = player_name if first else f"{player_name} (友{related_count + k})"
                                    latest["sessions"][dk].append({
                                        "id":          str(uuid.uuid4()),
                                        "name":        full_name,
                                        "count":       0 if (is_visitor and first) else 1,
                                        "isMember":    is_member if first else False,
                                        "bringBall":   bring_ball if first else False,
                                        "occupyCourt": occupy_court if first else False,
                                        "timestamp":   ts + (k * 0.01),
                                    })
                                save_data(latest)
                                st.balloons()
                                st.toast("🎉 報名成功！")
                                time.sleep(2)
                                st.rerun()

                st.markdown("""
                <div class="rules-box">
                    <div class="rules-header">📌 報名須知</div>
                    <div class="rules-row">
                        <span class="rules-icon">🔴</span>
                        <div class="rules-content"><b>資格與規範</b>：採實名制。僅限 <b>⭐晴女</b> 報名。欲事後補報朋友，請用原名再次填寫即可 (含自己上限3位)。</div>
                    </div>
                    <div class="rules-row">
                        <span class="rules-icon">🟡</span>
                        <div class="rules-content"><b>📣加油團</b>：團員若「不打球但帶朋友」請勾此項。本人不佔名額，但朋友會佔打球名額。</div>
                    </div>
                    <div class="rules-row">
                        <span class="rules-icon">🟢</span>
                        <div class="rules-content"><b>優先機制</b>：正選 20 人。當人數超過時，<b>⭐晴女</b> 享有進入正選名單之優先權。</div>
                    </div>
                    <div class="rules-row">
                        <span class="rules-icon">🔵</span>
                        <div class="rules-content"><b>時間與修改</b>：截止於前一日 12:00。</div>
                    </div>
                    <div class="rules-footer">有任何問題請找最美管理員們 ❤️</div>
                </div>
                """, unsafe_allow_html=True)

            # ── 名單 ──
            st.subheader("🏀 報名名單")
            render_list(main_list, dk, False, can_operate, st.session_state.is_admin)

            if wait_list:
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("⏳ 候補名單")
                render_list(wait_list, dk, True, can_operate, st.session_state.is_admin)

# ==========================================
# 8. 管理員專區
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("<div style='text-align:center;color:#cbd5e1;font-size:0.8rem;'>▼ 管理員專用通道 ▼</div>", unsafe_allow_html=True)

with st.expander("⚙️ 管理員專區 (Admin)", expanded=st.session_state.is_admin):
    if not st.session_state.is_admin:
        pwd = st.text_input("密碼", key="admin_pwd_input", type="password")
        if pwd == get_admin_password():
            st.session_state.is_admin = True
            st.rerun()
    else:
        if st.button("登出"):
            st.session_state.is_admin = False
            st.rerun()

        st.subheader("管理功能")

        new_date = st.date_input("新增日期")
        if st.button("新增場次"):
            data = load_data()
            if str(new_date) not in data["sessions"]:
                data["sessions"][str(new_date)] = []
                save_data(data)
                st.rerun()

        all_sessions = sorted(st.session_state.data["sessions"].keys())

        if all_sessions:
            del_target = st.selectbox("刪除場次", all_sessions)
            if st.button("完全刪除場次"):
                data = load_data()
                del data["sessions"][del_target]
                save_data(data)
                st.rerun()

            hidden = st.multiselect("隱藏場次", all_sessions, default=st.session_state.data.get("hidden", []))
            if st.button("更新隱藏設定"):
                data = load_data()
                data["hidden"] = hidden
                save_data(data)
                st.rerun()

        st.divider()
        with st.expander("🕵️ 編輯隱藏場次資料", expanded=False):
            hidden_dates = st.session_state.data.get("hidden", [])
            if hidden_dates:
                target_hidden = st.selectbox("選擇日期", sorted(hidden_dates))
                if target_hidden:
                    render_list(
                        st.session_state.data["sessions"].get(target_hidden, []),
                        target_hidden,
                        is_admin_mode=True,
                    )
            else:
                st.write("目前無隱藏場次")

        # ── 出席統計 ──
        st.divider()
        st.subheader("📊 出席統計報表")
        st.caption("✏️ 改名　🚪 退群移除（下方可恢復）")
        render_stats(st.session_state.data, visible_dates)

        # ── 清洗標籤 ──
        st.divider()
        if st.button("🧹 一鍵清洗標籤"):
            data = load_data()
            count = 0
            for dk in data["sessions"]:
                for p in data["sessions"][dk]:
                    if is_friend(p['name']) and p.get('isMember'):
                        p['isMember'] = False
                        count += 1
            save_data(data)
            st.success(f"清洗完成！共修正 {count} 筆。")
            time.sleep(2)
            st.rerun()
