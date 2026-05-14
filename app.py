import streamlit as st
import streamlit.components.v1 as components
import json
import time
import uuid
import re
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 0. 設定區
# ==========================================
MAX_CAPACITY         = 20
APP_URL              = "https://sunny-girls-basketball.streamlit.app"
SHEET_NAME           = "basketball_db"
ABSENCE_LIMIT_MONTHS = 2
MAX_LEAVE_EXEMPT     = 2

def get_admin_password() -> str:
    try:
        return st.secrets["admin_password"]
    except Exception:
        return "sunny"

def get_name_aliases() -> dict[str, str]:
    try:
        return dict(st.secrets["name_aliases"])
    except Exception:
        return {
            "金閃閃": "kingsley金閃閃",
            "冬青":   "冬青得來速",
            "得來速": "冬青得來速",
            "菜":     "小菜",
            "小菜":   "小菜",
        }

# ==========================================
# 1. CSS
# ==========================================
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');

    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; color: #334155 !important; }
    html, body, [class*="css"], p, div, label, span, h1, h2, h3, .stMarkdown {
        font-family: 'Noto Sans TC', sans-serif; color: #334155 !important;
    }
    .block-container { padding-top: 3rem !important; padding-bottom: 5rem !important; }
    header { background: transparent !important; }
    [data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stStatusWidget"],
    footer, #MainMenu, .stDeployButton { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }

    /* ── Header ── */
    .header-box {
        position: relative; overflow: hidden;
        border-radius: 20px; text-align: center; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #f1f5f9;
        padding: 2rem 1rem 1.5rem 1rem;
    }
    .header-bg {
        position: absolute; inset: 0;
        background-size: cover; background-position: center;
        filter: brightness(0.35) saturate(0.8);
        z-index: 0;
    }
    .header-content { position: relative; z-index: 1; }
    .header-title { font-size: 1.6rem; font-weight: 900; color: white !important; letter-spacing: 1px; margin-bottom: 5px; text-shadow: 0 2px 8px rgba(0,0,0,0.3); }
    .header-sub   { font-size: 0.9rem; color: rgba(255,255,255,0.85) !important; font-weight: 500; }
    .info-pill {
        background: rgba(255,255,255,0.18); backdrop-filter: blur(4px);
        padding: 4px 14px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.3);
        font-size: 0.8rem; font-weight: 600; color: white !important;
        display: inline-block; margin-top: 10px;
    }

    /* ── 管理員 badge ── */
    .admin-badge {
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        color: white !important; font-size: 0.75rem; font-weight: 700;
        padding: 3px 10px; border-radius: 20px; display: inline-block;
        margin-bottom: 14px; letter-spacing: 0.5px;
    }

    /* ── DB 狀態 ── */
    .db-status-err { background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:6px 12px;
                     font-size:0.78rem; color:#b91c1c !important; font-weight:600; margin-bottom:12px; }

    /* ── 名單列表 ── */
    .player-row {
        background: white; border: 1px solid #f1f5f9; border-radius: 12px;
        padding: 10px 12px; margin-bottom: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        display: flex; align-items: center; width: 100%; min-height: 48px;
    }
    .wait-row { background: #fffbf0 !important; border-color: #fde68a !important; border-left: 3px solid #fbbf24 !important; }
    .list-index        { color: #cbd5e1 !important; font-weight: 700; font-size: 0.9rem; margin-right: 12px; min-width: 22px; text-align: right; flex-shrink: 0; }
    .list-index-flower { color: #f472b6 !important; font-weight: 700; font-size: 1rem;  margin-right: 12px; min-width: 22px; text-align: right; flex-shrink: 0; }
    .list-name         { color: #334155 !important; font-weight: 700; font-size: 1.1rem; flex-grow: 1; line-height: 1.3; }
    .list-time         { color: #cbd5e1 !important; font-size: 0.7rem; font-weight: 500; white-space: nowrap; margin-left: 4px; }

    /* ── 標籤 ── */
    .badge        { padding: 3px 7px; border-radius: 6px; font-size: 0.68rem; font-weight: 700; margin-left: 4px; display: inline-block; vertical-align: middle; }
    .badge-sunny  { background: #fffbeb; color: #d97706 !important; }
    .badge-ball   { background: #fff7ed; color: #c2410c !important; }
    .badge-court  { background: #eff6ff; color: #1d4ed8 !important; }
    .badge-visit  { background: #fdf2f8; color: #db2777 !important; border: 1px solid #fce7f3; }
    .badge-rain   { background: #f0f9ff; color: #0369a1 !important; border: 1px solid #bae6fd; }

    /* ── 進度條 ── */
    .progress-container { width: 100%; background: #e2e8f0; border-radius: 6px; height: 8px; margin-top: 8px; overflow: hidden; }
    .progress-bar       { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
    .progress-info      { display: flex; justify-content: space-between; font-size: 0.82rem; color: #64748b !important; margin-bottom: 4px; font-weight: 600; }

    /* ── 報名表單 ── */
    .form-box {
        background: white; border: 1px solid #f1f5f9; border-radius: 16px;
        padding: 18px 16px; margin-bottom: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }
    .form-title { font-size: 1rem; font-weight: 800; color: #334155 !important; margin-bottom: 14px; }

    /* 人數選擇大按鈕 */
    .total-btn-wrap { display: flex; gap: 8px; margin: 8px 0 4px; }
    .total-btn {
        flex: 1; padding: 10px 4px; border-radius: 10px; border: 2px solid #e2e8f0;
        background: white; font-size: 0.9rem; font-weight: 700; color: #64748b !important;
        text-align: center; cursor: pointer; transition: all 0.15s;
    }
    .total-btn-active {
        border-color: #6366f1 !important; background: #eef2ff !important;
        color: #4338ca !important;
    }

    /* ── 規則說明（折疊）── */
    .rules-box    { background-color: #f8fafc; border-radius: 14px; padding: 16px; border: 1px solid #f1f5f9; margin-top: 8px; }
    .rules-header { font-size: 0.9rem; font-weight: 800; color: #334155 !important; margin-bottom: 12px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; }
    .rules-row    { display: flex; align-items: flex-start; margin-bottom: 10px; }
    .rules-icon   { font-size: 1rem; margin-right: 10px; line-height: 1.5; flex-shrink: 0; }
    .rules-content   { font-size: 0.85rem; color: #64748b !important; line-height: 1.5; }
    .rules-content b { color: #475569 !important; font-weight: 700; }
    .rules-footer    { margin-top: 12px; font-size: 0.8rem; color: #94a3b8 !important; text-align: right; font-weight: 500; }

    /* ── 候補區塊 ── */
    .wait-header { font-size: 0.85rem; font-weight: 800; color: #92400e !important;
                   margin: 20px 0 10px 4px; }
    div[data-testid='stVerticalBlockBorderWrapper']:has(.wait-player) {
        border: 1.5px dashed #fcd34d !important; border-radius: 14px !important;
        background: #fffbf0 !important; padding: 8px !important; margin-top: 4px !important;
    }
    .wait-player .player-row { background: #fff8e7 !important; border-color: #fde68a !important; }

    /* ── 編輯框 ── */
    .edit-box { border: 1px solid #3b82f6; border-radius: 12px; padding: 12px; background: #eff6ff; margin-bottom: 10px; }

    /* ── 統計報表 ── */
    .stat-row         { background: white; border: 1px solid #f1f5f9; border-radius: 12px; padding: 10px 14px; margin-bottom: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
    .stat-row-red     { border-left: 3px solid #fca5a5 !important; background: #fff9f9 !important; }
    .stat-row-yellow  { border-left: 3px solid #fcd34d !important; background: #fffef5 !important; }
    .stat-row-green   { border-left: 3px solid #86efac !important; }
    .stat-row-leave   { border-left: 3px solid #93c5fd !important; background: #f8fbff !important; }
    .stat-name        { font-weight: 700; font-size: 1rem; color: #1e293b !important; }
    .stat-detail      { font-size: 0.78rem; color: #94a3b8 !important; margin-top: 2px; }

    /* ── 統計總覽卡片 ── */
    .stat-group-header { font-size: 0.8rem; font-weight: 800; color: #94a3b8 !important;
                         letter-spacing: 1px; margin: 16px 0 8px 4px; }
    div[data-testid="stButton"] button[kind="secondary"] {
        background: white !important; border: 1px solid #f1f5f9 !important;
        border-radius: 12px !important; padding: 10px 8px !important;
        height: auto !important; min-height: 64px !important;
        white-space: pre-line !important; font-family: 'Noto Sans TC', sans-serif !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
        transition: transform 0.15s, box-shadow 0.15s !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08) !important;
    }

    /* ── 管理員區塊 ── */
    .admin-section { background: white; border: 1px solid #f1f5f9; border-radius: 14px;
                     padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
    .admin-section-title { font-size: 0.85rem; font-weight: 800; color: #475569 !important;
                           margin-bottom: 10px; letter-spacing: 0.3px; }

    /* ── 場次卡片選擇器 ── */
    .session-cards { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
    .session-card {
        flex: 1; min-width: 80px; max-width: 160px;
        background: white; border: 1.5px solid #e2e8f0; border-radius: 14px;
        padding: 12px 10px; text-align: center; cursor: pointer;
        transition: all 0.15s; box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .session-card:hover { border-color: #94a3b8; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .session-card-active {
        border-color: #6366f1 !important; background: #eef2ff !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }
    .session-card-date { font-size: 1.1rem; font-weight: 800; color: #1e293b !important; }
    .session-card-count { font-size: 0.75rem; color: #64748b !important; margin-top: 3px; font-weight: 600; }
    .session-card-active .session-card-date { color: #4f46e5 !important; }
    .session-card-active .session-card-count { color: #6366f1 !important; }
    .session-card-rain .session-card-date { color: #0369a1 !important; }

    /* ── 天氣取消 ── */
    .rain-banner { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px;
                   padding: 8px 14px; margin-bottom: 12px;
                   font-size: 0.88rem; color: #0369a1 !important; font-weight: 600; }

    /* ── 手機優化：加大可點擊區域 ── */
    @media (max-width: 768px) {
        .block-container { padding-left: 12px !important; padding-right: 12px !important; }
        .list-name { font-size: 1.05rem !important; }
        button[data-testid="stBaseButton-secondary"] { min-height: 44px !important; }
    }

    button[data-testid="stBaseButton-secondary"] { width: 100% !important; min-height: 40px !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料庫
# ==========================================
@st.cache_resource
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        creds  = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        st.error(f"❌ 資料庫連線失敗：{e}")
        return None

def _read_cell(sheet, cell: str, default):
    try:
        raw = sheet.acell(cell).value
        return json.loads(raw) if raw else default
    except Exception:
        return default

def load_data() -> dict:
    sheet = get_sheet()
    if not sheet:
        return _empty_data()
    try:
        a1_raw = _read_cell(sheet, 'A1', {})
        if isinstance(a1_raw, dict) and "sessions" in a1_raw:
            old      = a1_raw
            sessions = old.get("sessions", {})
            leaves   = old.get("leaves", {})
            meta     = {"hidden": old.get("hidden", []), "rained_out": old.get("rained_out", []), "removed_members": old.get("removed_members", [])}
            try:
                sheet.update_acell('A1', json.dumps(sessions, ensure_ascii=False))
                sheet.update_acell('B1', json.dumps(meta,     ensure_ascii=False))
                sheet.update_acell('C1', json.dumps(leaves,   ensure_ascii=False))
            except Exception:
                pass
        else:
            sessions = a1_raw
            meta     = _read_cell(sheet, 'B1', {})
            leaves   = _read_cell(sheet, 'C1', {})
        return {
            "sessions":        sessions,
            "leaves":          leaves,
            "hidden":          meta.get("hidden", []),
            "rained_out":      meta.get("rained_out", []),
            "removed_members": meta.get("removed_members", []),
        }
    except Exception:
        return _empty_data()

def save_data(data: dict):
    sheet = get_sheet()
    if not sheet:
        return
    try:
        meta = {"hidden": data.get("hidden", []), "rained_out": data.get("rained_out", []), "removed_members": data.get("removed_members", [])}
        sheet.update_acell('A1', json.dumps(data.get("sessions", {}), ensure_ascii=False))
        sheet.update_acell('B1', json.dumps(meta,                     ensure_ascii=False))
        sheet.update_acell('C1', json.dumps(data.get("leaves", {}),   ensure_ascii=False))
    except Exception as e:
        st.error(f"❌ 資料儲存失敗：{e}")

def _empty_data() -> dict:
    return {"sessions": {}, "hidden": [], "leaves": {}, "removed_members": [], "rained_out": []}

def check_db_connection() -> bool:
    return get_sheet() is not None

# ==========================================
# 3. 工具函式
# ==========================================
def normalize_name(name: str) -> str:
    if not name:
        return ""
    aliases = get_name_aliases()
    clean   = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name).replace(" ", "").lower()
    for k, v in aliases.items():
        if k in clean:
            return v
    return clean

def is_friend(name: str) -> bool:
    return any(k in name for k in ["友", "（", "("])

def format_timestamp(ts: float) -> str:
    if not ts:
        return ""
    dt    = datetime.fromtimestamp(ts)
    today = date.today()
    d     = dt.date()
    if d == today:
        return f"今天 {dt.strftime('%H:%M')}"
    elif d == today - timedelta(days=1):
        return f"昨天 {dt.strftime('%H:%M')}"
    else:
        return dt.strftime("%-m/%-d %H:%M")

def compute_status(last_date: date | None, leave_months: set[str]) -> str:
    today             = date.today()
    current_month_str = today.strftime("%Y-%m")
    if last_date is None:
        return "🔴 逾期"
    exempt_used          = 0
    effective_months_gap = 0
    cursor = date(last_date.year, last_date.month, 1) + relativedelta(months=1)
    end    = date(today.year, today.month, 1)
    while cursor <= end:
        m_str = cursor.strftime("%Y-%m")
        if m_str in leave_months:
            if exempt_used < MAX_LEAVE_EXEMPT:
                exempt_used += 1
            else:
                effective_months_gap += 1
        else:
            effective_months_gap += 1
        cursor += relativedelta(months=1)
    if current_month_str in leave_months:
        return "🔴 逾期（請假中）" if effective_months_gap > ABSENCE_LIMIT_MONTHS else "🏖️ 請假中"
    elif effective_months_gap > ABSENCE_LIMIT_MONTHS:
        return "🔴 逾期"
    elif effective_months_gap >= ABSENCE_LIMIT_MONTHS:
        return "🟡 預警"
    else:
        return "🟢 活躍"

def status_to_row_class(status: str) -> str:
    if "🔴" in status: return "stat-row stat-row-red"
    if "🟡" in status: return "stat-row stat-row-yellow"
    if "🏖️" in status: return "stat-row stat-row-leave"
    return "stat-row stat-row-green"

# ==========================================
# 4. 報名 CRUD
# ==========================================
def update_player(pid, date_key, name, is_member, bring_ball, occupy_court, is_visitor):
    data   = load_data()
    player = next((p for p in data["sessions"][date_key] if p['id'] == pid), None)
    if not player:
        return
    old_name = player['name']
    if st.session_state.is_admin and is_member and old_name != name:
        for p in data["sessions"][date_key]:
            if p['name'].startswith(f"{old_name} (") or p['name'].startswith(f"{old_name} （"):
                p['name'] = p['name'].replace(old_name, name, 1)
    player.update({'name': name, 'isMember': False if is_friend(name) else is_member,
                   'bringBall': bring_ball, 'occupyCourt': occupy_court, 'count': 0 if is_visitor else 1})
    save_data(data)
    _set_tab_for_date(date_key, data)
    st.session_state.edit_target = None
    st.toast("✅ 資料已更新")
    time.sleep(0.5)
    st.rerun()

def _set_tab_for_date(date_key: str, data: dict | None = None):
    """rerun 前呼叫，確保畫面停在 date_key 對應的 tab。"""
    try:
        d = data if data is not None else st.session_state.data
        all_d   = sorted(d["sessions"].keys())
        hidden  = d.get("hidden", [])
        visible = [x for x in all_d if x not in hidden]
        if date_key in visible:
            st.session_state['_tab_jump'] = visible.index(date_key)
    except Exception:
        pass

def delete_player(pid, date_key):
    data   = load_data()
    target = next((p for p in data["sessions"][date_key] if p['id'] == pid), None)
    if not target:
        return
    name = target['name']
    if is_friend(name):
        data["sessions"][date_key] = [p for p in data["sessions"][date_key] if p['id'] != pid]
    else:
        data["sessions"][date_key] = [
            p for p in data["sessions"][date_key]
            if p['id'] != pid and not (
                p['name'].startswith(f"{name} (") or p['name'].startswith(f"{name} （") or p['name'] == f"{name}之友"
            )
        ]
    if st.session_state.edit_target == pid:
        st.session_state.edit_target = None
    save_data(data)
    _set_tab_for_date(date_key, data)
    st.toast("🗑️ 已刪除")
    time.sleep(0.5)
    st.rerun()

# ==========================================
# 5. 名單渲染
# ==========================================
def render_list(players, date_key, is_wait=False, can_edit=True, is_admin_mode=False):
    if not players:
        if not is_wait:
            st.markdown("""<div style="text-align:center;padding:40px;color:#cbd5e1;">
                <div style="font-size:36px;">🏀</div><p>尚未有人報名</p></div>""", unsafe_allow_html=True)
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

        if st.session_state.edit_target == p['id']:
            with st.container():
                st.markdown(f"<div class='edit-box'>✏️ 正在編輯：{p['name']}</div>", unsafe_allow_html=True)
                with st.form(key=f"e_{p['id']}"):
                    new_name    = st.text_input("姓名", p['name'], disabled=not is_admin_mode)
                    c1, c2, c3  = st.columns(3)
                    friend      = is_friend(p['name'])
                    new_member  = c1.checkbox("⭐晴女", p.get('isMember'),    disabled=(not is_admin_mode and friend))
                    new_ball    = c2.checkbox("🏀帶球", p.get('bringBall'),   disabled=friend)
                    new_court   = c3.checkbox("🚩佔場", p.get('occupyCourt'), disabled=friend)
                    new_visitor = st.checkbox("📣 不打球 (加油團)", p.get('count') == 0, disabled=friend)
                    b1, b2      = st.columns(2)
                    if b1.form_submit_button("💾 儲存", type="primary"):
                        update_player(p['id'], date_key, new_name, new_member, new_ball, new_court, new_visitor)
                    if b2.form_submit_button("取消"):
                        st.session_state.edit_target = None
                        st.rerun()
        else:
            badges = ""
            if p.get('count') == 0:   badges += "<span class='badge badge-visit'>📣加油團</span>"
            if p.get('isMember') and not is_friend(p['name']): badges += "<span class='badge badge-sunny'>晴女</span>"
            if p.get('bringBall'):    badges += "<span class='badge badge-ball'>帶球</span>"
            if p.get('occupyCourt'):  badges += "<span class='badge badge-court'>佔場</span>"

            time_html = ""
            if is_admin_mode and p.get('timestamp'):
                time_html = f"<span class='list-time'>{format_timestamp(p['timestamp'])}</span>"

            row_extra = " wait-row" if is_wait else ""
            cols = st.columns([6, 1, 1], gap="small")
            with cols[0]:
                st.markdown(f"""
<div class="header-box">
    <div class="header-bg" style="background-image:url('data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCASxBLYDASIAAhEBAxEB/8QAHAABAQADAQEBAQAAAAAAAAAAAAECBgcFBAMI/8QAQRAAAgIBAwMCBAQDBgUEAgIDAAECEQMEITEFBkESURMiYXEHFTKRFDOBFiNCUqGxJENTwdElNGJyNeHwJkSC8f/EABoBAQEAAwEBAAAAAAAAAAAAAAABAgQFAwb/xAAqEQEBAAIBAwQCAwADAQEBAAAAAQIRAwQSIRMUMVEyQQUiMxUjYYFxQv/aAAwDAQACEQMRAD8A6AkHd7Esq2PPbLarfYlJMKVsnkbNq0gtiWUoNgj5HJNjJIjS5FewadUUVUiNkSdUVASkKKLJ4BAie5SBVIlMrZU9jIRp0FtyWyWTQMIFRRPuGkHuSgDKiNPgLYCiyclSAV5AoGItEAAJlsxZUXYMllLRBFyHyFszIDFuiJ2Vu+QqAJoOn5DoUXYn9SgcFD/QBEZNi7CguCN7jYoAZABAi7Cy2RhjYtjkxKmmhsP6mSSaMXyUhsUaIwuSmQUKXlgcE8h6aFURFTseRGty0AyBQoLgAKXuAAAQCAeAH7AA2FbD3CsAitEZE6AyongtkLKLRGgyUxsVRsOkK2D3GwsWAxBLKEBQocDclkCyqK8ksqfuAbSQTTW4uJHRdjLYjocLYleWNjKg0Y2VDyALsQU2AqRBs2lCi7+SNjZtVyVkToyGzbGhwWiUQGFfkLcNbl0GwYqgVVb2JexVtyHwYogvYiKZLsTBiZE2gARWQWhQSYMjZuNwNwARNyoCsgt+wTQC62YfpI+SAZFsxooCy0QNsxCh6iWyqixVsjLs0FSIieAyt77BKzISi0QIG1ohadkd2BaMWVmJiIAC7UABAAAXTKiloLcMWKKg1RAKwGE9i7EoqHkDYNUPuGyLkeBlRPIb3BAKqMbCAvkE2LwAYS2LsH7ANg+DFr2KgARXRGAYAf0AEYTopf8A0LBEilBPcMMLgxABj7l2I+Sk8lIA4LsSzI0J7mSMGVcmINiw2S03uBQh5FgAEK3GzQR2XjkXaLs0LgIPYlqybGTogI0mBaA8E3QFbI26KmrLf0AxSsRjQ2L6gHkX7kvcOwLwL8mL25Fl0aZGJfAQ0aZL2FEd2Wm0QQB8kfJf/wAFTQCr2DpsgE82ijcEAuR4CAy5MWVBgY3uUi5KAVPktESfkPYC0Ri2uQ22BLLbsL2FgG9gAABBZYKCWORRQEhZAA38EoCpIbeCNMLZgVjlE5KBiZLgABYIwgMrIGAF+CNexaJQFXNlsx4exkgKHutibksCpBt3Qtkv3AWPPJWrRC7FSbLXgjdEk6IHkBNNBgRlI/cICgi5FgUE/qQDIE8BAW62AL4Aif0G3sPIZkDSD4C4IzEUNsidmS4AlgCgDJRC2ZCrkeQmHbZiK3ZOAgwAI+SgWyX4I9mF7gHyGg+bKwMHyAwFAAAAAGYQBYg9wkxwy2NDFq2WqQYIIhuUASvYLkoZYI9mOSsgor2CVhfUMgNEoJuy+QCtsye5i6AFkqIGybsC3uCcMvIAMBl+BEikToqIABfBfkR1RA7KiAA2AIluUiKBXsyNWrFkbZkbOAguRRiFDYqaDW1gYriwZCgC2C25IrTLdsCt77hLcxfItgZujGhbYQEoWjJqiVYEsqDW5aTQEAojLoGvYhkCCeSoNKggJIijfJnSFbgY0xbRlQouzaEbMvASoUY2PNla2IiCkaovnkMsNIrL4KlsKIMWVFaXgUwC5DC2YfIEZOChbgE9gKSAEYWxQqvcuiCI1Zkkg6GjTG6dMPcpUh8Gk8ERk6CVEErwRFfJaQEAYRkAKqGxNCAUmXYolewQa3KuDEQFdWRpF0IkUqSFDQiBWvYm3kgiZQqsy+WgMTL7mPL2MgDSI0BsDQkR8lsqVssIi4DK6S3IkmSiW7pj7lqnuKRYI9gWkK3GhAq8lpIUQQjoySFICIxM1RXFcoD8yoypXuRpXsAZLK/oAJYsuxdmBLIqMqRHsAAQaAVuKKqRGkBKIZ7BoDFFAad2Wh4HAKt2Q0xfIRWOAAXIAB8mJkR8AYgnkItVQAQAABmFyAy6RWR/QN1syc8EFsBAugDJuXwNAgRqwl9RBfA9Q8EaRRVuHsPFon3MQRQgA2DHkjArIuCrgUAYQAAWTcbAEiF3Kk+QJuLK0PTsBGVLYPciVGQMhkycmK6QyRKIubBpk+SMteSPm/Yu0FyW99yfYU0QGhZeQWLqJYsLkPkiVOSrgf0DAMqpETD5AtrwKIjJMuhHYVltEtN2QAg2LAMEashZDTJ8FjSVGNeQkIaXzYQoNlLFDewb3Im6oEAVvZow9W+7owucl8s5hatjcNxrlWFKPlmHqS/teystxW1Ecl7oKcaptD1cfs7KUrDWxi8kV5I8irZj1sfteysla8l3fkxU4tW5E+JH/Mi+rj9p6dZNNLZhNmLyx90PXHlND1cfs9Osk7ZWr8mHrp71+5XKPKf+pPVx+z06y2Gxg5Rb5oOaS2ew9XE9Ov1asxMVkg1VhTVbND1cftOyskR7EU1fI+LBvketjP2s48mSQbZg8iX+JE+JB/4kPXx+17KzZko35PyeSC4kirJGr9aHr4fZ2VmzEjywr9SIssL/AFInrY/aenWaof1MXlglyh8SF8j1sT06y2DfsY/FhzaHxcf+ZF9bFfTrJOg6Zh8WH+ZFWSNfqQ9bE9OskZUfmskPdD4sOPUh62P2np1k2VcGHrh/mHrx+49bE9O/TOw6owU4XyiPJD3Q9bE9O/T9AzB5Yf5kT4kb/Uh62K+nkzb+ov3MPiwveSDyY2tmh6s+09Ov08cB3Rh8SC8ofEhza/cerj9np1mnsDFZY+6CyRvlD1cftPTyZB7Mxco/5g8kb5Q9XE9OskLa4MVON8ofEjXKHrY/Z6eTK75G5iskV5QWSF1aJ6uP2vp1bZU2YKcLe6KssE92h62J2VlY8mPxYVs0RZI3dos58fteys2VcH5/Fj/mQWWL8r9yethP2enWTuuQrrkweSPug8sK/Uh6+H2enX6eSp7H4/Ej5a/cyWWFcoevj9np1+l7WY+r6EeSCX6kR5oeWhObD7Oysk6LZ+aywq/UX4sH5RfWw+09Os7+gRh8SF16l+5fiRv9SHr4fZ6dfoTY/P4i5tEWSL5kh62P2vZX6WrErMHkgvKHxo+6JebH7Oysv6kCyR/zIqlFf4kX1Z9p6dOGVGMpw90FOPuheXGfsmFr9ORfgxUk1tIySRnM5fhjcbGLHBkq8mPL2M55Nag3sROyz2CToljEHAaJRA87CXADsDBeQigKAAAAAMtxRfSEt+QlGt7JaK0RIBZRVMm1l3VUlsbjkbobjcbhDdBClfIYG6aV8ckT8FrYJIqaRoIv2Bia0l+4W+5WrIl7l3V2fRCi1sVLYibRKiPkpGXQvgjQSbFMaFjQCsqtj9AiN70XyTe9iGl8kZG6CtmRosrexKLuYmkshk+AwqJtocFSfKYftyBiVMUGn7AUjsboWwmhCypIenlsCWwy0LAxKi7B/QulEycCgxUHVBUEUglp7BIFT2AWT+hQXYJqw9uAWxCJ9w2HQVIfSlbewVJ7jZmOV1F/YZ3UrPGb8PJ6r1Vaebxwe548usZ5SdXR+HVU562TvY+dRai9zgdT1GUy1K6XDwyybfW+ralN/MVdW1X+Y+FJvwRppM1sefk29rxYSvQj1jUy4ZhPq2pu7Z8UXSdJlinJU0x6uZ6eD631PU1+oxXVNU/8TPllGXsyKMv8rHq8izDjfV+aaq/1sfmWpb/Uz5al/lZlKMvT+kvrci9vG+v8x1Nr5g+p6qMk/Uz4VHJd+lmXz3+lj1uQ7MH2ZeqaqTRkupauK5PhnOTX6Wixcmnsx6vIeng+t9U1Tf6mZPqeoS2k2fCvVTXpZIKV006Hq5p6eD7F1LVPf1FfVNSltJnxtuLpRY3/AMrJ6uazDB9b6rq63bMZ9U1VX6j5ab/wselvamT1czswfRLqWqa/W/3Itfqq/Wz5d7/Sy7/5WS8vIvp4Pph1DVXXrZ+ktdq0r9bPj9L59JnUqpxE5OROzB+35jqZK/WJdR1Ka+dn4JVxExeOTd+hl78zswfZk6hqWlU2Ra7U/wDUZ86i6/Q9jCnJ/pZfUzOzB9b6lqV/jZj+Yal/42fg4tf4Q4yq/Qx6nIvZg+hdR1FfqZf4/U1+pnyuMq/QyVN8RYmfIlwwfUtfqq/Ux/Harn1s+dRzf5HRm4ya/Sx38hMcH7LqOpr9Yj1LVereZ8vw5Xaiy+jJ4gX1ORezB9b6jqU/1MPqOpa5Z8nwsrf6WZrFlS2gyd/IdnGzn1HVJ7Nn6Y+o6irc2v6n5LFkreDMZYJ/5B38idvG/V6/VN36/wDUfmGqTty/1PwUJLZQY9GR8wHqcq9uD6F1HUt/qf7lfUtRHmVf1PlUcilvDYyeOTf6C+pyJ28b6X1DU1amyrqeoS/Wz53CVUoMxWGT29DHqchceN9T6rqK/WyLqeplv6j5XhlX6TD0TX+Enq8hMMH2Pqepb/UZw6lqnfzf6nwRU73ifpUvESXk5C4cb959S1N16v8AUq6lqW03L/U+T4Um7aK8ck0kmPU5E7MH1vqWpT2l/qSHU9Vvcv8AU+Vxlf6WEml+ll9TM7MH0vqWqV1IxXVNWl+p/ufjGMv8jK4NqvQ/2J35r28b9J9Q1TW02RdQ1i/xs/J45r/CzCayX+lj1M2Xbxvpj1HVXvNleu1LdrIz5VGbXDMlimvDHfmnZg/ddQ1N7zZfzDVJ28jPn+Hku/SzKUX6d4svqZnZg/f8x1Te2QPqOq4c2fPGNRpRdn5uGS9kTvzOzB9n5jqUtpMyXU9U1vJnyRc1/hYbnf6R6nInZg+ldR1V/qZlLqWq/wA58klJK2jBRk3wO/M7MH2Pqepv9TMo9U1Ke8mfI4y8phwfsX1ORfT431vqepf+JmD6nqn/AImfhGLSugoPn0tj1OSnp8b6odS1K5mzN9T1DVepnwOMr/SZRjJuqZJycienhX2PqmoSpSYXUtVz6mfLkxtLdGMYuuaMcubki48XH+nq6LqmZTSm9mbLoc6zY00zRW3ao2TtzM3H0s2+l6i26ta3UcMk8PeYdJBjejvcd3HLona3CDTvgltGVY1XyPuS7ZeCB5Df0CYYGALTIFAAAAAGe3uH9zHxsip2ZyWl8K15IqvkW2qDS9uRpNxbS8i0T0jb3Lo2oG3hkb9xolZ8mNWHfgOVIaFeyIlasXS9yW/YllGdbck48mDbHq3oaqshW9EtNhOy6GVbgR3TthNXuXSbNrD4FqwnSe5O21U4AfjcNeR202J7EdhWZXtQ7KbjHdFuuCWroNq+B2UW/cq5MGv3KuSXGi7MBtEaV7E7KjKPIfBL3WwtqzLsyDyLDb4REmuSdlFS+peOTF2W217l7aqpWw07MW3dVQTlY7am14Yfj6kTbe4a92O2i0xuwm65Ci+V5JcaH6RY55I5Wthohe+w2vkqVInncx1pVS2J53KR2xtFDdGJkQGEGHwAsGJki2AGth4DZFYlFMrtF3vSy+UW3JM++OX2MvBhmbWOVexjyfjVw/JpGv8A/eSt+TCK3Svk/TqCf8XNfU/LF+uL+p83zTfL/wDXZ4r/AEbD07pmPJhTkt2j6F0fBdM+jpTvTxf0PtpbM6fF02OUlrn8vLlLXmrpWGK/SjJdLwN/oR6NWt6JVM9/aYfTz9e18L6Xg/yoj6Xp6/Sj0E2w1a5L7TBPXyeculYGv0on5VgezSPRBfaYHrV8H5ZgSr0on5Zp/EUehVoLkntcF9a/bz30vTvb0oflenraNHoqkL9h7XBfWv2819KwJ36Uw+mae/0Kz0XXuNuSe0wT16859K0/mKZV0rT1+g9B0Fuh7TA9evh/KtPW0B+V6dL9CPuaYftYnSYfR61+3nflWnf+FE/KdNe8UelwH9R7TD6X1r9vN/KtPf6UZPpembr0o9BLcOhOkwPWyfBHpemXMUX8t0/+Q+7lWTgy9pgetXxflmnr9Biul6ZO/Sj0HuOTG9JiXmv28/8ALNO1tBGX5bp6pwR9+xj5HtcU9a/b4/y3T+n9CJHpunX+BH3JMK15Mva4nr2ft8q0OCqeNGP5bp7/AEI+wqa8idNinrXXy+F9O065girp+C9opH2PdlaL7bBZzZPk/L8H+VBaPAucZ9QZfbYfSXmyfM9Hg/yE/gMDX6EfUFsPb4/Setk+NdOw3/LRZaDBX6EfY3fgm9k9tj9HrZfb4/4DA9vQh+XYF/gR9lWw4t72PbYL6uT5H0/TpfoTKtDp/wDppH0rbkrdi9NivrX7fHLp+nv9CIum6d/4D7aHymN6XE9bJ8S6Zp/8iK+m6Zv9CPtVskh7XH6PWv2+F9M09/pQfS9Pz6T7d3yXwX2uH0etft8H5Zp3/hRH0vT/AOVHoNr2I1fBPa4U9XJ8Uem6dcxRX0/T8KB9vkJoe1wT1b9vj/LcLX6DB9M07/wH3tthRY9rj9LOW/bz10vTL/Cj9IdP06X6UfZ5Gy3Y9rj9HrX7fGun6dPeKLLpumkq9CPrYSrcvtcD1q899K06VegxXS8F/pPSbaJbJ7XH6X1cvt5/5Xgv9KH5Xgb/AEo9HlildD2uP0nr15sul6Z+EVdK06jwehRa2HtMPo9evNfS8F/pH5Tgbv0nptIibsXpMPo9evPfStPW0SfleJLaKPRu2VOie1wn6PXrzF0rE3+lGS6VhTtxR6Ck74Mm1XA9pjo9fKV5mXpeBx43Na6thWDO4x4N2fDRp/cN/wAWzQ6vgmEbPT8ltm3mqlTPb7bleRnhtKj2+2qWQ5/T+M43eo84bbQmiswjwjJUmfT8Xw4uc8jTvknncye7Gz5PSsGK5K7fgcBX7kQ9PkNOh81h8AYtEK7IWrAAEAAAeRre5el6bI4PLb//AJ9T5Jd49Linc9zkGp1j1E25Sds+TK3LKmpP0nb4+k2596i12X+23TKfzf6Bd8dLjC5SON+mSd+p0WMFNtuWyPWdFEvUV2D+3PTG9mZrvXpT3s424+l0vJl6HFXJ3YvRxj7iuxvvPprr0vkzfeXSvSlKe/2OM4m/Ds/Rrhye7J7OLOorsM+8umxjalsYPvXpvpck7o4/mg/RtI/PBCbTqW49nF9xXXn3109uvJlj746e7cm7+xx+GGWOXqfzNn6uDT9TfJb0cPcV12Pe3TW92Sfe3Toq0cjmvSk0z883qaVPYns4evXYId8dPk92ZrvTQevbycYSlacZH0fEmorfcezh69dfyd6aCLrazF97aF+Dj0nlck3Js/RZZQScjKdHinuK63Dvjp3HlFn3v0z0OuTkDkppuKrcxptOrJ7PFfXrr8e++m1T/wC5ku+um1Xj7HG5Qaauz9W1KCiX2cY+vXXv7d9M9aijOXe+gr2OQOMYUMrbgmmT2cX166/j726dPYzh3n02Savc43CMob2SUpx3T5Hs4s6iuwy706cnV7lXevTKtvdHGZvImm2fpBU25N7oeylPcV2KXe/TFBtsxh3x09xu9jkKSlGSvZI/FN+j0psvssT3Fdnj3v02uSR746c27ZxlycIJNttsz062lKTaHs8U9xk7I+9+m8/+TCXfHTmtl/ucfmnJfK2IZKTi7MfZQ9xk7DHvfpzifmu+NEm1Ff7nG/XJ5XFWfviyOM97L7KHuK69/bfp6k3J8fRlh3107e1S96Zx3M5Kbkm6FycPTezHsovr12KffXT0rjG1f1MF33oXb9HP3OSQl6IKw5qUvlY9lE9xk61DvnRer5o7f1Mpd99O48/1OStyjBuSPycXKDmizosU9xXYZ989P9CaV39zLF3t05zUJqr8nHW5OHyvdGDeX1K5PYxvR4/plOor+h9DrsOrxRniyKSZ9K255OU/h51nJi1MdPkk2nsrOqwl64xd8o5nUcXZW3xZ9zKyKyxSp2SLpmpXqMIrVhEKjLwKJ5AFTG1BAWyAIaBPcr3C2dB0mFx+RGOor0P7GT42Pzzt/Df2MeT4ZYfLSOof+8n9z8sEX8SP3P06hKtbL7n5aaTeaK+p85y79T/67HH+DdOlf+2j9j7HSVnydMT/AIaN+x9fiju9Nf6xy+W+ajq6su9E8lUqZtV4yHgKkHvwFuSJYbeAgxwqG00WxTfI9RORtloaCvwGkVPwh/8Ai6pQd+C/pRFK3ZJWOhrbciG9ltou9KJvyHzYT3DkXYFpkryLdjYKwvYBE2L6WtwuCOwhsXYitvYUV+yGxGGF9RaTGyCVumGnexHbT8EjJXUZX7jujLt2yDW2wfAT8Et2x8Si93yE3RVwQFoh5KkhRdJtLFk29gkNrtSpkCobNgHJGmU2bWWtiUUlqbHfsN/ITDafgSnk38C2RfQOxtWV+w+5EGxU0rJZFyPNsisk9iFT2MUXabVSZkRV4DobNjoNqtyNtvYjvyNqy8E8ituQo/Um10Mq4I78BcGUp5gt3sEt9ytbbEXBdobIqaMVuWWy2Jtdsq23JwSvqEybY3Fb34JbsNu9iWKs8K3vYUtgyIu/Bvyrapmo9wtPVNm2u6ZqncEf+JbOZ10/rW3035R5CTvc9vt5/wB6eM+D2O3l/enH4P8ASOnz/g2iNUmjLmjBbIqex9PxfDi5/LJhkvYto9HlEvYfYMq4JaURH9Q2/BGyDF8gMFpAAEUAAH82wjL5dz6sGj1OqyKOCDdbujDHKFquTfPwwxY8+efrgml7n1GfLMMXHmG61OHR+o04/An+xF0TqLdLDJL7HdFodNV/Cj+yC0Wm5+FH9kaV6/TanTbjhWXonUWqWGd/YyxdB6o/14pNfY7o9Bp7v4Uf2RVpcFV8KP7Ix/5A9s4Suh9RU21hlX2K+j9UT3wyf9Duj0emr+TH9kHotO6/uo/sh789s4Z+S9Tmv5El/Qyh0Lqai0sLv7Hcv4PT8LFH9kX+EwL/AJcf2Q/5Cr7ZxHH0bqcIXLTyf9D8cvRuqtN/AlT+h3R6XTtU8cb+xi9Jh/6Ua+yH/IX6T2zhy6L1OUK+BK/qjJdC6nKFPC/2O3fweD/px/Yv8Jgr+XH9h/yF+l9q4jDt/qUWv7h7/Q/SfbvUU1WJ7/Q7Y9Jhpf3cf2QWjw/5F+wv8ge2cV/s71OK9XwW/wChjl6B1KWL+Q1/Q7Z8DDuvQv2RHpcNV8NfsjH/AJCntnDsXb/VKcVge79j6tL2x1Km54nb+h2iGlwr/lr9kZrBi/yL/Ql/kKe2cPydsdV9f8ptfYS7Z6okv7qX7Hb1p8X/AE1+wWmxtbwX7Ie/p7ZxOPbPVJtf3Uq+wydrdV9SisTr7HbFp8VfoX7B4MX/AE0P+Qp7ZxOfbHVYR2wt39Cf2Z6skm8L/Y7e8GOt8aHwIVXw1sP+Qq+2cOn2v1XIq+E1/QS7X6r6Unjey9juDw4lxjh+xI4cUm7gv2H/ACFPbOI4u1upu08Ulf0M5dpdUjBJY3f2O1x02JPaC/YrwY7/AEoe/qe1cOfanVJNf3b2+hi+2OquLrE6X0O5fBx3+iP7D+HxJOoR/Yf8hT2rh+DtvqkFTwu/sYPtvq3rb+C/2O4vTYW/5a/YPT4b/lr9jKdfT2rhy7d6p69tO/2P2fa/VdpLC/2O1vTYPGKP7Izjp8Vfy1+xL19PauJQ7V6nm2eJp/YyfZ/U20vQ1X0O2R0+NPaCDwwW/pV/YxvX09q4rLtDqcVTg3/Q/J9pdUi7+G/2O3fDg/8AAv2L8PG1vBfsPf1fauMz7V6nLEv7t7/QwfaPVFD9Dr2o7UsUFH+Wv2K8UK/Qv2QnXVPa6cNzds9TxQ9bxtRW/B5WbBKM3GdxkuTvfVMGP+Cn8qtL2OI9xprqmRRVKzb6fqO/5ePLxdr6+zVfVsf3O2YU1CHlOJxTsy49WxpvydswuseP/wCpqdbHv024/RpX7EaXBZfNwR0mjmWeW3T+pkjF7sOyfBVZKKuAQKJTKABbJwSy7F8iStojLV0VZ8j42MMu+Nr6GZjm3xy+x58nxWWHy0fqMf8Ai5/c/HTNLMr9z99e61c79z58H8+P3PneX/T/AOu1xf5t36Ztgh9j65Lg+Ppu2mhXsfWtzudN+Mcrl+U/qOWGirg2rXj8F0hFbXYDSSJEs38KiO2/ofnqM0cUHKdKKPB1fc+jw5XjUk2jDLkkemPFbPDYK33MvFHmdM6vp9cqjJWeinS9yzKWbLhcbI/HVarBpo3lml9z5cfWNA3tkV/c0rvvX5oav4UZNRZq8s+W16csrNfPqO3w6HF0Nzx27Vgz4s8bhNSX0P1fG2xonYGvy5cssU5OX3N6TPXj5O6NPqOG8eWldtCmzHezOj1+XhZpEgHaZE3VFukqlTVETI9nZNJ4VvcV5C3Kn4FulYNvgsSto/OeaGJ/O1FDc0ymNr9XJeTFNM+aGt08pOMZpv7n0xlGlRJlKdtl+GSRhkaim34MlNHl9e6jj0elm3JW1sMspjNsuPjuWWnj9y9xrR3ixP5ma5oe6tVHUtzdxs8bquqep1Mpt3vsfBdydujncnUWZO7wfx8uPl2LovVcPUMUXGS9VbnqJ2ce6D1XLoNTGXqfp9jp3ReqYtdgjOLXqa3Njg55lNVz+q6O8d3p6lt8DxwE9tieTanny59n6LKttxe9mW1DSa0x3fgJfQJPyE0mIUtPkbewa9iXWxUjK/CJb4CdbpHz6zVYtNH15ZJGNumcx/Ufu7KmzwZ9yaL4qh8RPwevpdVj1OL145JjuxrO8dk+H7NMNpKwpOk/B4ndPVHoNM5R/Uy3KSJjj3XT1nnxRdOaTM4St7O0clydwazLnWT1ujZ+2O4nmyLDllua+PPLdVtZdHlJtuyFIwxS9UFK7TRluzYl3NtLLGy6VOmE/oRqmVcCF+B/QxMmStypJtknaMZzjBXOVINbmod69Ylpn8HG2meeWXbN16cfHc7ptD1umin/AH0T831TRcPLGzksup6pt3kf7mEtVqX83xXv9Wat6rTqYfx1s261Pq+hj/zk/wCphLrWiS/mo5O9Rlcf5rb+7MYZ8zTubv7mHu6z/wCMututS63oYRv4y3+pg+uaFLbKt/qckyarM2k5ul9TOWTKoprI3/UnvKy/42usfnmhX/NX7lfXdAl/MX7nJo5Mkl/Nf7mDz5lKviN/1Hu6v/G7dYyde0Edvip/1Eev9Pq/ir9zk6y5W6c2/wCpVLIt3N/uWdZUn8bp1mPXdBJ/zVZ9em12m1FfDyJtnGHlyptxnL9z0ejdX1GlzRcptqzPDq91hy/x1k3HYFt/Up8PR9WtZpI5PofcbkymU25PJh2XyuzMN1dFeyKt0XTCfLFt07NU7hl/xLNrnw0al3En/Es53W/jW1035R5nqbSo9rtxP4rZ4ySpI9vt1r1tHI4P9I6XP+DZEtjKttjGLpmdpI+l4/iOLn8sWQyaVBqmejziR5KmRbMvJLCqYsofAgwb2JT8FBFkCy5IWXJYIACD+c8cVzB0joX4StOeVvff/sc8gk/NfQ6J+Ecd83t6uf6H0XV/g5vF4rpaoqoi5K7SODl8ujjdwXI+UWl4Jy9ibZaLZURIr2JU0qceA2r4MakxTJs0qe9giTLTQlNJWxVsPAXBd/8Aq6XdEb3LZj5CaGndlvyW9g6C6S17C15QHqfsTZpLXIe79hYsppVJoer6GO/lFrYappU1W4snngqdrgGlTtBr+hE3dGVWhqmmLonDDVIJE1UPAVIr4MfqJDS73ZVzwThlspofIkk+EErZSrqsV5RUE1RPJE1TdcGSRBdkh5Vut7Ja9+Q7JX0MoPl6l6Vosn/1ZxLuVOXUcrjymztnVk1osirf0s4d12U11TMn5bOn0UanUPp7MbfWMdv/ABI7hgp44Jf5ThnZsZR65De/mO5Yk1ihXsXrfg6e+X6t7US1yKtWVpUcm3y2qiV8FJZUyAGWkRoDEq5IVcgg+Qg+SrgA1W6AdBmSz5ThmObbFJ/QzPzztPFL7HnyfFZ4fLSuoNLWT+5+WBL4kfuZ6+v4uf3Z+eBL40fuj53l/wBP/rscX4N06Yr00b9j60qo+bpy/wCGj9j6LbO50/4xyuX8hMsdyUVbGza8L5VKkSt1Yu7RJWkm3shldR6YTfhp/fnUs2nx/Bxv037HPZvJN+uTcpN2bT37qFk1foi7o1dSkqbOVz8t2+h6Lpp27se52rqsmLVxim+Tp2HKpYVLy0cr6HqcGnzfEyPjc2OXdmGMPTDelRnxc+o8+q6a5Wajxu+E59StcGvKO7fk9Lq+ulrNQ8t7Hmu45LfDNflylu3R6biswkbh2BS1NurZv7cE79SOQdK6rPRTfwz7p9y61u/U6Pfi5pJpzur6TLPPbqLyY/M1+5Y5E/0uzlEu4Ne5bTdfc9PondGb+IjjzN7s2MeolrTz6DKTenRnw7KntR+OlzLPgjkXDVn7KjZxts25uWNl0Lmw9wHuZvP9nqSMX7osou7MXsnb+VE3Izxx38Pz1WaOHDLLN0kc67m7hy59TLFinSTrY9jvbrcccHpsMrb22NCy7zeSX6maXNz68Ot0vSXPzX36Lqmrw5lJ5G1fFnSO2dc9dpFJ/qSOY6DBLVZYwgm9zfumZ9P0fp395JKVcHnxct+Xr1PBJ4ke7r9Zi0mCU8klaRzHujq2TXamShJqKfg/TuHrmXWZZRxSfpTZ4Kty9UvJObn7vEZ9L0mp3VIr1v0rk9bRdEy59M8rg+D9+3ukS1udScKgnydG0PT8WDTLEkqo8+Ph7vNe3N1U4vErkObE8c3jkqa9z7+hdXy9Ozx+ZyhZ73ePQ5QnLUYYv0+aNOlFRb9T39jHLC8d3HpjzY8+Or8uu9C6vi1uCMvUlKuD1VJNXexxfQdR1GkaeNtJG49G7sxzhHHnl6ZfU2uPqPGq53P0Nm7G9R4tBtM+HQ6/DqYJ48idn3Js28OTbl8nHcL5FVDkMxRnt5s0yPceSNpc8Df7SI36U99kc/786s55np8cqp+Da+4+oR0OglP1VJrY5TrdY9Xnlklve5qdRyyR1Oj6a52Wvxg505uT9XNm99ha3PP+7k3KKNESknGPLZ0XsXQvDp/izVNmvwZXKxvdbx4YYabYrV+Ea73rov4jQSlFP1JGxpuj8tTjWfFLHKNpo6GU3HE48u3Lbh7jLHkkmqadH66bPPBnjki6aZ7ndvSpaLVSlGPyt8mvyi4tP3OZyY3DLb6PhznLhp1jtfqcNZoopv5kj3E90kcp7Z6o9FqYwT+Vs6docy1GKOSO9qzc6fl3NOR1nT3C2vpfIu+EE3W5UlRtuZZUa8k/oZXsQLvRatI5p3/G9fydLSOZd9ya6k/JrdRfDf6GbzjWoYpTl9z78HSdXlVwhaZ82lTeWK43On9u6fGtDGTim2jQ4+Lvvl2ep6i8eOo0GPQNe1tjaM125rpP9NHR+o5sWi00sriqSNS1Pd+OGWSjDZbHrnwyRq8fU8nJPDxZ9taqEHPI/lW7PMy4FDJ6PVsnR7ut7q/idPPFGLVo1fLKU5Sk5O2zWsxjf4cs74r3dJ0KWrw+vDPf+h+sO1dY099z5Oh9byaCPpdyVnsR7yXqS+HIzx7XnyzllfLDtXVrnk/LP2xrfFm09E7hxa7MsdU37mzLGpR9VXaNjHixy+I0c+ozwy1a49r+n59GksiaPkhJuUY0br+IGOMWmlRpmN/MnRr58UwydDi5PUwdR7Kb/Lo72tjYHRrXZEn+XRRsiTq7Onw/i+f6rxnVJ5LW4R7S/LVnyklUWan3Gv8AiTbZ8Gp9x/8AuUc3rr/Stvpp5jyeUe120v7xnhttOj3O2f5jON09/wCyOhz/AINlS9zMxbM00kfT8f4xxs/lGPNC1Qozjz/YjIwRWKUZJFMZCCAAii5KyLkrAgAMh/OkMcPXbZ0f8LGksno3V/8AY5xixcOTOjfhX8s5qL2v/sd/qrbg5vFN5OjRtsyIlbK1Rwcvl0p4g9wkAQ2tEotkYKqaFmL5CMUUllFJgRPcpK3Ky6F8EAdEFTJe4GwBgPcjL4IUOBZdym0tWUUAWj+hFwPJlaSJs2j2FtDknnchtbTDD+g5LsHdbAAhsb2oxL9SA2q9ipWYmS4BsezDaoi3DSBs+5fsSi8Bdlqtw3sRLcPbhmUiV8nVU46LI3v8rOF9xOUeqZpvi2d06u29BkX/AMWcK7jk31HJGv8AEzqdDPDV6h9vZD9XWMcvqdwwSTxR28HF+xsMH1XG/Nrydoxv5IxrwOuTgfp9HwJV4BGctt34RFQSLWxKJbKg+CIgrIGx/QCFQXJQVGqCVlZVS4LFiH56lpYpfY/Vvc/LU18GX2MM/is8Plout31cvuzDHfxY17metr+Ln9z88C/vor6nzvN/r/8AXZ4/wbv0u/4aF+x9lnx9OVaaH2Psq0ju9P8AjHJ5vyqNqx4FUw6o2NPHXlG6Ts83r+uho9G5eqm1sei2oxd+xoHfvUfXljghwnuePPnqVt9NxeplGsdU1EtVrZZJStWfNSt2+CTkpq47HpdG6Xl18nGDOPlbnX1GFx4cPLzm1XO5+dNJrybf/Y/USSfqo/T+x2ZK3kPWcOWvDwvV8d/bT0nJKMXv5LlVtR8rk9DqeiWg1MsblvwefOFNSbts8csbK2ePkmWO4kYxTqWzoO/Ts7Nm6H2/HqOmjlcqrY9HF2Yqac6PTDgyy8tbk6zHC6rR/iyX6j6Onwlm1MVBb3yjdI9l4auWS/6M9Ppvbem0uSLpOj34+nyl3Wty9fjcdR6fQscsfT8cZc0uT0UYwhGCUV4M/Gx08ZZHA5Mu61Kb4E048bhNoOXlFk15rz1qo7TVvweN3H1bHodJJN1Kj0tbqIYNPLLkdUrOZd1dT/MNRJJv0p+Dw5uSSN/peC514+t1ktTrJZpO03sfmo+vIkt7MItKcm+Ej2OhaJaiOWcVbStHLtuVfQ4ycXG/bRajD0vF8yUsjR8Ot6jl1WVucn6X4R8+pU3nn8Z1TJjwSzTjDDFtmXneow/pfNflabe/k+rR48XxF8R/KevoO2s7xPNkTTq6PG6hiyYdTLG4yil5McuOy7X1sLO2N26P1jpmjxLEqT99j1I9y6CqUl/octgl6t5NfuHaf6nX9T1nPcJrTW5Oixzu7XTc/cXS80JQyuMk9qdGp9b0/TM03l00lFvwa8/TJU5tCNSfpjKTa+5Mubvnwz4+kx4v7bZZ8cobR3R+ailV7M2/tjov8XhbzQ5WzZh1btLUqbnp/mXhImPFl8rl1eHxXkdD6pqNJrIY/W/S35Oq9PzPNpoTW9o5/wBE7W1ctTGeohSTs6Fo8C0+GONLhUb3BjZ8uT1nJhn8P3d3wEVEunwbVnlzdLbfyvhn4avNDBjlKbpJH6ZHGMG5OvJpPd3cOOKlpoP1S42PHm5ZjGz0/BeSx4vdvVZa3WywxneNXwa+1FNUi5W5ZJS4bM9JhlqMkMONOTZys8rndR9JxcePDh5eh2907JreoQfpuKaOqaDTrT4IY0qpHkdrdKWjwRlNL1VubA00tkdDp+LUjidZz991GXijFbugnZXHe/BtRzt6eR3F06Os0klSlJLY5Z1XR5dNqZQyRainsdpdXXJrXdvRces08skIpSW+xr8/HubdHo+ouNk25kpOEoyjyjd+yuvpNabNKnwrNO1OKeDI8UlTT8kw5Xjmp43UovlHP487x5eXa5uLHnw27XCXxIqUWqZnw6ZpnZ/cPxqwaiVNbJm4wyJxuPzWdTDOZSeXznPw5cd+GS5KmRW0Xg99NbW4jZzLvl/+ouzpypvY5h35t1ORq9TP6t7oLe+PC0kl/EQ+51jt+noMdeyOS6JKWrx3xa/3Os9EyQxdOg5Okomr0/j5b/X7utMe6NNPUdOyRx7v08I5Xm0OsWWUfgPZvejqWfr/AE6DcJ5E/B866j0Wfzf3ds9uTGZftrdPnnx/rbmGfSZ8XplPG4x8uj816ZJ148m9906rpmbp0o4fT6voaI4NJ71GzQ5OOY/t2ul5Ll8xjH9dRXqs+mOj1L3jhe/0MdGoQyRm90nZvGh650bFpYLLCKklvsXixlXqM8sb4jxu1NBqoa5TlBxR0vAvTCKfsasu5ulYncEl9aPv0ncugzuMVkSbN7jskcLnnJyZb08f8Q4XFM0SM1FpM37vzLiyaNZYO1Rz5TjPd+54c1lrodFLMbK6l2JKE+mRr2Nj5NV7C26ftwjaYbJfY3env9XI6uazqp7hrcitvgre57aac+SXDNU7jf8AxJtUnatGqdyN/wASc3rvwbnS/lHk0m7Z7Xbm2Q8VJ7Ht9tqps4/Tz/sjo8/4tlq0ZLijGD5+xkt+T6fi+I4ufylF8AeD0YIuS2Er5FIlShjIzMZEGIAChWQAAAGT+dsSdVydB/C6DWebT2//AEc908k0nKVM6N+FFTjml7P/ALH0PU/g5nF+ToseSsi2QODl8uhFCFFIJbC3ZaDaomxGqCaG75KQLVDwKtiqAV5I+QwgDFFVCwI22Etgi3SLoEJEsbvggqRHZeAXQibFlXBGNByy0RFcqIIg+R9SrjYDEqK0R8gVcAiL5AcE2K+AqoCMqJ5LwrZdCN7ETMrXsHXhCAg/YllvyKI07FMO29iLgs8H6fJ1ZuOhyN/5X/scK7ilF9Ryurfqf+53TrNvQZL/AMrOFdbcY9Sy3v8AMzqdC1eo+Hq9gQ9fVYu63O14l6ccaXg4j2LP09Xx1snJHbcbfojvtSHW/J079HzfuYt7mS3e5HSZy21RF5JsUxEdkKyA2q5KRci/YC2uRZLCVl+AbV8lMa3Mq2EWD42Px1P8iW3g/d8H5alpYJV7Hnl8Vnj+TQ9an/Fz+406fxY/dH6a1r+Jl9zDT280a9z57m/1drD8G6aC/wCHh9j67ex8vTv5EfsfXtSO70/4xyeX8kknZE65K2FXk2d6eMur5fnltqXjY5h3xhzY9bKW9M6jXqb4SRr3cOLpuVv+KlFNfY1efHbd6S2ZbjmWnwTm1GMW22dG7M6Z/DaZTmvmZ5+mXRcE/VH0uvsepi7i6dhSjHZI1MccZXQ6nPPPHUbF6VGPBGvlbs1rUd36RbQVnwajvJW/RA2ry4yNHHpuS2V43e3y9Svw2eFO20vB9vXupPqGdZHHc+CTdKjncmcuW4+g6Xj7MNV0LsZJ6RK9rRtjSTdbbHJulddz9Ogow3R6E+89Z69o7f1Nnh55PFcrqem5M8/Do6aafzblVRptrc5su7tXJ+F/Uwzd1a67T2PfLqI1/Y8jp0Wru7M09l9Tn/Re6s0s8Y590zeNJnefEsi4e568fNMmrzdPlx3y/dp2YZcsMKbm6SMm3Vmmd69WzYYSxRbSexny5am4x4uO55SPl7y64srlp8E7XmjS1JtP3sqy5JuWSdyk2ftotNn1LbhDY5fLbl8Poun48OLHy+dU23Ve5tPZGSCzPE1+rZmrzVOS/wASk00ex2hkeLqUPV5Z58Xzp7dRZeO2Nw6j2xpNTkc1FRb3Po6X2/pdE1Nxja8s9tSjDH6peEaX3P3FPFkliwSprY6FwmPlw8c+TkvbG5RWBL0/LR52u6P0/Uyc5RhbOew7g6jTfxf9Q+4uotV6v9TznLjfl749Lyb+W5T7d6cnxFH5f2d6ddP0u/qjUZdd6jJbzf8ARn5LrGtjO5ZpX9zyuWFr3nFzfG25T7X0En6ko0fRpO3OnQa+WNo0vH3Br0/5jr7iHcHUVNr17fdlmWELxc1mtuo6XT4NPBQxVFJH7qS9O9NHLYd0a9OnL/VnpdL7t1D1Mceamn9T3x5sb4jT5el5MZuugqN7pUVJH5aLPHUYI5I8NWfv552NrGz5jnZXz5Irck5JLfhC23seX3DrVo9LKV06LllqbMMe7KR43d3Xv4fFLBie7VbHPp5J6jK8mR/M/c/fqGulqtVOT+tHzQg5P6vg5fNlcrp9F03FjxY7qLHOeVQh8zexvfaPQ/hRjmyQpv3Pk7S6FLJOObPCkt02b5gxRx41H07JbUZ8HD53Wv1nVzWoyxJY01Jqj8pa7Twn6Hlh+6PE716pPQ6NLFL0to51qOoavK/iLPL1XdWbV5Zh4aPHwXl812eE4SS9DUk/Yy9TNC7L63qM0o4MrlKvc3uDbSfuZ8efdWtz8XZV+qMMmNSg090+T9NkqYdVfueuU3NPHuuNmmid5dv+ty1GGFedjR3CeHI8Uo1L6nb82OOWDhKNxZpHd3bblJ6nTx+Zb7HP6jg35js9J1mtStL02XJjzKUJelxdm/8AavcCywjhyy+bg0GWnz4ZSeSDjR6na2myZOpRmk/SmefD3Y1t9VcM8NusQkpx9S42K0037H5YPUsUVwqR+yts6WNtj57LxbpFaVI5l39B/wAffG505Lc5n+ILrW7M8Ool7W30P5tf0MV/FY63dr/c6Fq3l/JUsa39JzvptR1uO3zJf7nWum44ZNBGMlacTV4Ja6PV2TW3ItZlyrNL1qXqT+pis03BV6kdC7h6V0zBB5skUmahn1Ogxt+nEpJcbGPLuXUr16XKWfDy5PJJOLcmv6mCi1BxcX+zPTfUNLGq0y/Yxlr9M1tp1+xrXVnlu4Y9t28+FxVJMqjKT3tI+xavBF74VX2P1XUdHS/uV+wx+PDPK9zz3GU9qbr6H2dO0mplni8cZV/U9noefp+p1KxvElf0N50XS9HFRlCCW18Gxw4Wzy53U88wutNU6/Ca6RFZOVHyaY241XudF76xxjo0o7I57kjFJO/Jly46Xo8u+V0f8P2nonTNqitv6Gofh5to3Rt0Hsb3T/i5HWfndKrWw2b4D4CpHu0Z8pNquDUu4k3qrNulTRqfcKb1Oxzeu/BudL+UeRvR7nbifxKPGiklue12/wDztjkdPP7ujz/i2SHkyRIKkZI+l4viOLl81ORwBuejA5BKFslSqluYyKubJIggACgAAAAD+c4Qi5XXB0/8K/THT5Eo8v8A7HMnGnGmdI/CtuEckW7t/wDY+h6j8K53D+TofuFsEXwcC/LoRbFmIMRfsR2ZWGwIi7USxYFT3Dsie+5R8LIlFr6jyGWU8ojLYxom9jSarLcMWR8jRRUW14JSLaoaVLZS+CUNGjgOvA4L9aKa2hHHe2ytN8FSvkmjtrFFQcdwk/caNCTvcvp2sj5Em6oaNCe1BK2FwS3YmqaVJvkOkLpFjG3bLZIuqxWyL4DVPYjbJpLF2Fr2H1KluRGLC3LKiJ3sA4ZkqohHyZQr4+sv/wBOy1/lZwnrmOUuo5n/APJndurq9DlX/wAWcN6+3DqWRLj1M6vQtXqH2djpS6vjVVUkdwxKscV9EcQ7Mmn1fG0q3R23Fbxwf0ROv+U4H6vkjoNOyNUcrbbvwGXknARCq1sTyVvYxAyVUNvApsNMAASy0VLclbhcl8kP0rPy1K/uJN+xnHk/PU18GX2MeSf1emHzGj62nq5fdl0zXxYr6mGsdayf3Gm3zx+583yf6f8A12cfwbvoGnp4/Y+i/B82g/8Abw+x9KVqzvdN+Mcnm/Ko1uGPcqNmvL5j4urZ3pNJOcaujlfWtfn1Opm3J7M6r1jAtRo5wivmo5d1HpWt0+qm/huUW/Y1ObddLobhjfLyseSd/qZJufq3bpn2Lp2rb+XG7f0P1XSNdNb42mjn5Y5bdv1OGvOV3yZ/4d/J9eo6XqNNH1ZNj43Sf2MbLry9uPsz+Em2qVbmLUpSSP0Uk3dcGE38+3B435e3bpavZ+BJRUedzKM1Hjez0um9Hl1BXCVM9Mcd3ww5MpjN2PMx40t2yzlFbNmyYuztVJ/rZ+2Ls3M5/O7Nj0Mq0L1vHGt6av4nGob7nVu3nL+Agn7HhdK7Tx4Zqc92ja8GGGHEscfCo2+HiuLl9X1OOc8P0k03saX3n0nUaqXrxJs3V8EnGM0rSl9za5MNzTS4+Xtvhynp3b+tyZlDLBxjZumi6Ni0Wik1Fepx5NgWLHGVqCT+x8/UnWin6efSa04JJW17vLKyOO6+KXU80Y+Jv/c9Dtxy/NMa9medrU/zHM3y5P8A3Pu7bjNdVxteWaeu3N2Pnh3XUtZP09Pk/wD4/wDY5N1eXr6hk34kdY1e/TpJ/wCU5L1WH/H5Fx8zPfnysxaXRTeVfgoSk3Sv7FliyRjbi0j7u3cPxNfGE/mi2bV3bptPpumRePGlJrk1sOPc3W/yc3ZnI0WMpvhH6LT5su8cbZdNvmja5Z0jpGh035YpvEnJx52GPHvZydR26czywePn5ZIyxRnNv0RbdH39ywjHXyUEkkel2Pp8Woz/AN7G0jGYbunplza4+7TXZ4XilUotN+5ca9GRS5aZs/feDBp5x+HFRVmrQVzVO7Ze3tyeWHL6mF26r2hm+L06Kb8HtrY8Hs2Cj02P2PfV1bOrwzWO6+e6mTuumKT+x4fduklqdJJQV7HvGM4wknGSszs3Hjhn23biuXR58Wd45YnzybJ2t0DLmzRy5ofL9Tep9L0k5+qWKFr6H04cWLEqhFRr2NecHnbey63KzUTT6eGHFGEUkkj9JyUItvhciTs8Hu3qkdFopRi/mex7WTHHbVwmXJl5an39roanXLFCVpGrySjC1szPPlyajLLLNt2z9NJg/ickYq92czLPuzfRcHHOLj8tn/D3SzyZfiNbI6LDyvY8Ltbpy0Oiiq3aPazZFixSlHlI6HD4m3D6vLv5PCzyQi92kWOSE9oyTOadw9f1a1kscJOMUz8Ol9xarFqYrJNuLZjl1GrplOjtx7nU7adWTJGE4+lq0z4+l63HqsEcidyaPtXF+57Y2ZxrZY5YZPH1vQtJqW3KCR+vTOi6bRq4RVo9NW3RG96Q9OSrefKzVqRTSozumY8GRnJp43z5Gcx79k31FpnTnvwcw7/26jZ4dRdYt/oPzeBocf8AxeOT4tHXOir/AIHH7ek5LpG3lhW26Oq9Gm49Kg3vUTU4K3uum7GtfiD8al6U/S3TNM0+ky5/0xbo9/vDqeaeplikqimeHptbmwbY1sefPvbY6PD+sfrk6XqX6flpMj6Rq0k/Q6MsnVdS0tzJ9X1KhHfk8Lq/Lbyxz2wl0zU1Xps/DPoc2JpShVn7/mGqk7Uj88uuy5X87toXxPCzGy+Xo9vaPJ/GxdbJnUdDFx08U62icj03U82DLFwdUzpHbOulrNIpS3lRtdPltzP5DD9x8XfjS0Tv2Ob0pPf3Oi9/zcdFVco5zBtp7eS893WXQfFdF/D5JaTY21KzUvw+T/grNtXFm5wTWDl9V/oqS4DJ52I0z2rRnyv0NU7jlWr2NqaaNV7kV6k5/XfjW7035R5fqTZ7Xbi+ds8JRaas9vty/Wzj9P8Am6PP+DZUZrZEitrKj6Tj+HGy+asuQt0GwerzQjKESoLcjstUw2iDAABQAAAAB/Oe8mqW9nSPwsxyXxPV7/8AY5qpSxz3d+x038LXKpSe9/8Ag+i6n/OudxX+zoXikVJ1ZE9rMrfB8/fl0IjRaAZiIyMoX1AJWVIxvcy429y0Si71wCZJLHFyb+VEt15WS3wq2/qHutjX+p9y6fSzcVTaPNfeONNtRPO8sjZ4+myvluSH9TTYd44m90fp/bLAv8I9eVnely+m27p1ZGrexqa7ywN16TKPd+mXI9WHts/ptXkqVM1V93aVrY/OXeWBLaNj1Z9pOlz+m4eNzG96NSx95YJbOJlLu/TRV+kerD22f02tt3yPU+TUl3jgcto7B954HKvSPVi+1y+m3OW2w9To1F944E6UQ+8sPiI9WHtc/ptybSK5OjTl3ni9Veks+8sKl+nYerE9rl9Nv+pFbdNGof2zxc+gf2ywpfpHqxfaZfTcA1W5qP8AbHTtXW5+mDu7SyfzPYvq4sb0uc/Tao78klaex8PTuqabWx/upKz7k15MpZl5eOWFl8quCFtUFRm897E7DJuQxTS7sPbgIuwEXJWEPuZQ/T4+r1/AZK/ys4T3A76nl28v/c7t1b/2WT/6s4V3Hf5nlr/M/wDc6vQ/DV6h9fZX/wCWxt+6O5aeT+BCvZHCuzXNdVx//ZHc9O3/AA2Pbwh13ynT/L9eWHwER8HKvy2wyIy8oxE8lI+Sp7AL3K1sQACeCtbEq0AWxaCVFXNj9n6Rrc/HVfyJfY/Zs/HWL+4lXsY8v416YfMaPrP/AHcvuyYNs8a90NSl/Fyvm2TBFvPH2tHzef8Ao7OM/o3bpzf8NH7H1pbHyaBVggl7H1t7I+g6af1jk835VLpiK3ZPJU9z308WLat0fPl0mHL+qKZ9X6fASVkykvyzmWvh8kdBpkt4Lb6Hz9Rek0eGWSUYrY+jXavFp8UsmSaVI5x3R17Lrc8sUG1jWxrcmWOLc4MOTksfP1/qj1OeUcf6E6PHdKvqSMm7teT7ukdPyazUJU/Sjncn9r4fQcePozy+JpxX3MLdNno9c0602dYz4McG19zyyxsraw5JlNov0v3Z6XQup5NDnTfFnx59NmhBZFF+k/JcW+TLD+t28+WTkmnXOi9Rw63BGUGvVW56iSa22ZyDofV9RoM6qT9Ce50bo3XtNrMcfmSlR0eDll8V8/1HBcbt7SSbvyV7smLJBq07Mls7NyWX4czKefJ4oKlyUjj9TKeUvga2Z8fVHWhyX/lZ9lOqPh623Hp+ZvxBmGXxdPTh85RyLV763N/9n/ufZ2u3+aQT9z4dS1/E5Je83/ueh2vG+rY2vLOV/wD2+ks1wuo6hXopf/U5P13H6epZGv8AMzrGpVaN/wD1/wCxyfrkvV1LLv8A4me/U+ZGn0XnOp0jVrTauORq0mex3B1zHrtMsUeUjWsUX6vf6DLaeyo1Mc7I6fJxS5Ta4pyjmjJqkmbnoO5MWLQRwye6RplNyV8FWPJK/RF7DDKxjycONfR1XOtRrZZFw2et2r1PDovU5uma84+n1KX6kMa9auKdr2J3ay2yvFLhp7/dfUMfUJx9Duv/ACeJjaWSKXhn5pcp7P6meDbIr5sz7u7JMeKYYXTqfaX/AONi/oe6tmzwuz3/AOnx+x7lbs6vDf6vmupmsqr9y1tYWyI9zONTf6Lr7Dxa5HiiOSim3si3wykvxH5arLHBhlkbqKTZynufqktdrpY0/lTNj736+4Rlo8Uvo2jRVJtvI92zQ6jm8ajtdF09msrH6qKik15Nr7L6P8XLHUTjtya50XSZNdr4rmKe51bo+ljpdLGMUlSPPg492VsddzTHHUfdCCglFLZGGaCnjlF+UZtv2I91vydKSSacDdt3XLu8emzwaqWRLZs16bcUq8HV+5emrWaaTr5kjmGtwT0ueWOcWlZzOedt27/Q5zPHtbJ2X1eWPLHDlls+DouKcZwUlumjiulm8GWMoy3TOk9odWWpwLHOXzLY9ODla3XdPreUbIgm7IlasrdNHQl3HGss+RvcrdDa9yWrG0HZzLv9N9QpnTk9zmXf/wA3UdjX6i/1b/Qec2vaPbPHfyv9zqvb79fToJ8UjlGBOOSPvZ1Tta306F+yNbp9ft0etmpHzdd7ewalvK0rW/Bz/q8MOk1EseNXTpnS+4uq4tDppOTTbVUcv6pqMepzynFV6nd/1Mep1s6C5Wx8ypvbgjSr5tiKM2ouG6RcibjaZoWW13Nys8KTaT4PX0fTMGb5pZEl/Q8eKahstwsudL5JuvY9JNTy8OTG5b092fSdGppLKv8AQ3TtjHp8OnjDHNORy7156tTlZtPY8tVLUpylL02bXDJXL6rjvb5ex+IMnHTf0OeY3TbfFm/fiC3LTrfejQlukvI5fFZdFNY10nsLbQJ+5tSXy2a12ND09OjfsbKt1sb3Bf6OP1V/7KbeCS5LW4a3R7tT9sZXRqncbX8Sza5bWal3Gm9Uc7rvxbvTflHmW/Y9zty/WeHHk9ztx3M4/TfnHQ5vwbIm6Rk07MUmluZH0nF8RxsvmjRH7FZHyerzEZJ0YooSsmYgjMRiAAoAAAAA/nB7qNrazpf4WZLU14v/ALHM4ObxqDW50f8ACa4xmmt3/wCD6Hqv83N4fl0u7WwW3JIMyfJwb8ul+ksPcNewRgipeRy6I9mPIB8h8DyWwEuEjye5cs8HTpSi96Z6z4PD7ut9MmvozDkuo9+CS5yOX6vUzz5pOcvJ+aTvkkoP1S2t2fV0zTz1OoWNLZs5eeVtfTcWGOOG6+dyXCRJSrwbZHtTNJKUXV/Q/Rdo5q3kv2PScWVnh4XqeOeGowkmuNw/0vbc3Bdn5V8yn/ofku0s8pu57fYelmxvVccail6Vb8lVVujcX2dll/jMMnZ+dKlL/Qelke742oqSa+WLDnFcpmzvtTUxfyv/AEIu09RNk9HL7X3XHWtRkvDpE2T9zYsvaWri7TbMI9sa97OP+hfRyX3XG8ObVWYtNb2bFj7U1f8Aif8AofpLtTVNVZPRy+19zxtajFNepsSafBsse0tUuWJdp6n7Mvo5MfdcbWYLd2YOm36eDaH2nqopp72ZY+z9TGDl6v6F9HL7X3XG1aD+V3dkg23TdGwaztzPpsUss9ktzX54/nf0PHkmWNe/Flhyx73aGry4uoqDn8rOoYX64xfujk3a0H+Zwv3Or6baEUvY3emtscjrsJjfD9WnwVUgnuDbcqwasijbK9gmE2xd2WPJatWRoChhBllJ/wCvk6u/+Cy//VnCe44tdUyNurk/9zuvVU1ocn/1ZwvuSKy9Szc2m/8Ac6vQfDU6m+H09nwcesYqd7nccFvBC9nSOGdltR6riW9+pHc9NJfAx/8A1Reu+U6bzX60yMy3sUcn9tysTJccEoyXHIpUfPALJexjwNCgJ2GQVkb9hfuThgVboXtQsiLJ5WfC7UfjrX/w8q9j9Um1uflrP5EvsYcv41nh8tF1drUyf1ZdPK8sa90XVb6mW3lkwL+9jS8nznJ/o7WP+cbp07fBC/Y+xcUz4+n2sEL9j6zvdN+Mcjm/KhFzZQ9kbNkeX/hNql4PO6l1TT6THL1TXqR83dHUVodL6k6k0cz6n1HUazK5yyNRbNXn5e1v9L0l5NV6XcPXs2rySjifyng5JKdW6b5MlTXyuz6dB0/LrssYRg6vk59tzru48ePBj5OkaLJqs6gouSb5OidG6RHR6a5Q+ajLtroeHR4IykrnXk9zP8mKV8UbXHweNuV1HWXPPU+HKu7Yt66TSrc8eCXqir3s9vumV9QkvFs8FJfHjXFmty6mWnX4L/1OgdI6Zj1vSKnG2+Ga31voebR5JNRbib32lH/0zH54PU12iw6nFKOSCdmxjwd+LlZ9ZePk8uLJ/NJVVH76fUZsEvVjm1Rsncfa08Tlk06bjzsavlx5MT9E4NNe5r5ceWF3HQ4+fj5pO5tHRe7cuKMcWdN15Zt/SOu6fWJJSXqZyb5FW9P2Ps6VqMun1cZQm6b4PXi5st6rX6no8LNx2SM00q8mXk8/pGWWbSQnLlo++zo4Xc24XJjJdKmeZ3G2ul5mv8rPT8bnmdx79LzL/wCDJnPFOG/2jkTanlyf/d/7nsdoU+pwvwzxYbZcnn53/ue12g76rHxucq+c30l/wdK18q0M68R/7HJep3LqGR//ACZ1jqO2hm//AI/9jk3VZOWuyJKt2bPUSdsaXRfnX7dEwxy9Qjjl8ybR6/dvTsOkwRnCNN0eX2wq6jH3tGwd9uX8NjfikeHFjLG31HJZnJtqmjjGWWKl7m+6Ho+mfT1k9HzOJoegiv4uDb8o6hpprH0jZXUDPj455eXUcmW5quZdVUMWvywS2TPY7Q6dh1kZepWeJ1ZqXUczfv8A9zaOwpRgm1wzymE72xnnfS+Xj916HHodUowVWeThipZo/c2Pv+Slr1JcGtYZSeWLXFjKSZnDlbhXVu09tBHbwe5F77nidptfl0G/Y9p78HU4POL5/qbvOq2CJ2G6PSfLWknyrfyv3PB7p6pHSaWSjL5mtj2c81jxSm3VLycs7q12TVa+UfVaTZr8/JqVu9HwepnHi6/PPU6iU8l23e5NNjeacYrdN1/QznFy3/oZ6bLLFbVJrjY5GWe7t9RjxduGm79uaPS6GEZylG3uzY11TSRjSmkcq/i8+S3LLJVwk2fn8fP66WWVP6s2ePm7I5vN0dzvl1WfXdHHnNF19T5s/cuixpv1r9zmDnmk95y/dmM3NreT/c9PdVhP43F0HU936WN1Uk0an3BrtNr38THGpfQ8lQqO+4T9P+HY8OTlubb4elx4vMr81b2s9PoXUZ6LVxfqai3uec4Nv1LgNcJPY8sMrK2s+LHkxsdl6TrI6rTRnCSaaPvXhs552T1b4eWOnyv5eDoMJerHFre9zrcPJLHy3WcHZlqMmrbIkXyLNj5jR3TlnMe/7j1E6cjmXfr9XUjW6nxG/wBB4za7hd5Y3zZ0HR9Sh0/o0Zy5cTnyThOMlymbbLBk1nRYxhvJI0eK2Oz1GEurWvdW6rk1+ql6p/I2fJiwPPlWOCvfwfZDoOtlP0/DaVm49s9vY9LCOTMrlzuenb3V53mx4sP6/LyodC/huj5M04/NWxqDbjl9Mls3/wBzsPWsccnSsuNQXG1HJdTgzLVyh6HsxlwzTHp+pyy293S9G/ienfFw7yo8DU4cmmzOOROL+p0bszG8fTlHLFb+5+PdHQcWsxSy40vWt9jD0fHhnOqzmer8ND0k8ccq9e6OgdrS0koxeKvV7Gg5+narTylGWNuuDZOxsWpjnucWo35HFj21l1GUzx2+v8QNkknSZpE/1xUfc2/8QZtzjT4NQck0vcvLZconSzWFrqPZn/4yD+hsUKpmvdlbdJg/dHvK6bOhwz+scTqrvkrJp3Yvciexbp8Hs1d+R7p7Gp9wprVM2y9map3DN/xTRz+un9a2+lvl497s9/tpfM2a/KW7dGwdtT3Zx+n/ANI6PP8Ag2Qr42MUVJvyfScc8Rxs/kRH9DJqjFcHowouSkZV9TFKBrYtKwwPzYD5Ii1VABAAAH84xclarc6R+FMZJTclz/4ObLIpNOLZ0z8K5+vHJyb2/wDB9F1X+bm8X5OiLZGSaoxW7sy4OBfl0Z8J5K0YmXgx0aRi0FwOGQVb8DhMREqAjbZ43du3Tp/Znsnjd2v/ANNnfszDlv8AVsdN+ccqm5/ElttbNg7Lgp622r3PEyxty+57fZaa1qTfk5mF/u+h5ctcTpONUkktjP0tEgtk07M7t7o6mEmnzued3UV1uGkuEXbyhs/BnqPPuok62EdluW6Dab2RO2HdWNb7JUT0R9kZ1twRN+xe2Lu39p6E/ah6YtbRMvPATS4QuMLbP2xUFXAlBUZqqI17Dth3X7YqEVyPRG+A9yxHbEuV+0aT/Sg0uK3Mtq2RPVtVE7Ysyrxe6/8A8Zkr2ZyyTrJK/dnVu6Ir8rybeGcnyyrNK7/UzndTj5dv+Nt09jth/wDqUfudTwL+6i/ocp7Wb/Mo/c6rppP4cV9D16XxHj/IXy/ZJtkppltojZu2OPVfASVBcFvaiIiaYvwAwBVwYAyK+bq1vRZElfys4R3BKWLq+Ze7fP3O/TjGUZRe6ezOfd1dj/xurep07pvdo3um5ZjPl4c2FyjTuzsbl1fE1u/UuDt+BNYsa+iNP7R7Rj0/KsuWnJG7JKKSXCL1fJM5PKcGFi+CUVbsto0GyxSsrsrdk5AeAyWVukSxLNMQFuV/cghUQvkuiKiNGT+pPJYsJtqkfjrL/hpP6H7SeyPw18mtNL7Hly/FZ4/lGkah/wDFS+7M9NKPxop+6Pz1D/4iV+7GnV5o+9nzvJ/p/wDXax/zbto1/cQ+x9PlHy9P208L9j6nwjv9NP6xx+b8qU7Di6vkOVCNpbHvY8/hq3fegy6nTL0W65o51PBmxz+G4O1twdsnCM16ZxUk+bPPy9F0Msnr+BG/sa3LxdzodN1fpxzrovQdRqsql6Wkb/0fouPRwj8i9R6ODTYsEEsUFFI/ZtvZMcfBInP1uXJdbRxUWqVH56i/hS28H6vZb7mOVKcGvc98prHw08LO7zXKO66/MJfc8Zqpxl7M2XvPp+bHq3kjByT9jw8OHNmyxh8J8nK5cLct6fRdNyz09bdH7IyerpsU+NjY6352PG7U0zwdPjGSp7HsfqlVHR4JqeXD6uy8jDJCM7jJKSfueL1Tt3S6tNxgoyZ73D2Rb3qSM8uKX5eWHLljfDnHUuz86yN4eDPpHa+ohli8q4OhtX5MVDfk8vbyXbZvW5a1t+GiwrBghjS4R9FCMd7K3X1PeTU1Gnnnbdo+T4OuxcumZa59L/2Pv3Py1eJZcEsfNoZzcrLjsmUrimb+71c4cfM/9z2+0Kl1OMlu7Pt632tl/ipZMSq2z0+z+hT0mX4uWKs584r3bd3Lqsbw9ra9TD4mklFLmJyjr+CWn6jkck0m/Y7Ak6+ZI8bqvQNLr5uWSCs9uTjuU053D1Ewy20HtTTZcuvjNL5Uzc+5OlS1nT4+jeSR6HSujabQ0oQVnp/Di1T4Lx8OovP1UyyljmHTu3dYtVGUotJSR0LDpJR0CwPn0n2LFFN+lGVPyzPHj1Xln1Fys8ua9a7d1X8ZOUFabPmU8/RMTUtpM6lPHjbVxs1fvTor1kfi4Vujzy4dXbZ4eql/rl8Of6/X5NdP15Ls/LBbzQS9/Y/bNo9Tgm8bxu0/Y9Tt/o+fPqoynBqNmnMbc3Uy5cMePxW/dsRUemRTXhHrq2vsfPoMCwaeONLhH0rg6nDNR87z5d2VolsEvLCYb2M7HhPD5tfCWTBKMeWqOT9f0ubTa2TnF05N/wCp2DdfY8jrXRcOvhcor1GvzcXdPDe6TqPSscnUklabD33ps6BHtLTNelxTPs03a+ixpJ4Iyr3RpTpbt18v5Ca+XNYuo7Y3f2P2xaXPkSccUn/RnUMfQOnwf/tsf7H2Q6bosaXpwRX9DOdNd/Dxy/kZ+nK49J12Rr04mfVHtzXZYqsZ0+Omwx4xxo/RQiuEkes6aNbL+Sv6c2w9qaxpKSo/ddnamTXH7nRWvdIlRs9J00kefv8AOtA1Pa2TT6KTdNpGo5ccsOWeOapp7HackI5IShJWmaV3D2tPNqXnwuk3wjX5uD9yNvp+tsvmtS6VkS1kPRfqs650xylpYOT39K/2NR6D2q8Gojlzcpm64oRjBQiuNj06bC43y1uu55yXwzXPJGn7lpLwPJvTW3Mn/pCL3o5r37F49e36TpSbv6Gp97dLlqYfExxt/Q8OfHcbXSZzHNzmWRy/w3R63T+u5tLgWNRtI87PpsuHK4yjkX9DBY5p7qVfY5dtxvw+j3hySeXu/wBqsqe2Lcyx93a1vaNL/wDn0PAeJvdRa/oX4U4r/EZerZ+mF4eP917+XuvWyTi47P6nn5urSnP1vCvUzzpxyNX6ZfsE8rW0ZC8mV/Rhw4Y3w9jB17WY4P0KooyXcevlb8fc8eEM0m6iy+jInTxv9iTLKLlx4W/L1M3W8smnPGpM/bB3Flwen4eL037HjTxy2uLJ6Mnp2UjCXKXa3iws1t6PWuoz1yi8qPPUY3HbZiMclVJSkz0uj9NzarUw+V+lMzmNysYZ3HiwsldA7QxuPScXjY9tJ1R8/TcEdPpYY1tSPqVcnW45rGPm+a7zrFJlbrYy2atMxSTM97eWke3Bq3cLX8S/c2iVbmpdxqtU6NDrr/Wtrpfl5W/qZ73bj3Z4CUmz3e3Hc6ON09/7I6XP/m2hPgsSRWwkqR9Lx3xHFz+WTquTB8iib+TOsKFXIQfI+EVMkmVGMiCPciKC6UABAAAH85LHFKMXszo34V3Gc4Va9/6HOpOLV38x0b8KbcZt8r/wfRdT/m5nF+To63RldLcxx8bmTqjgZfLpSsW9yojW5SKLbkWVfUnkxRY7klyWPId2CCVuzwe9G49OlXse7bTPB7036dLfwYcn4trpvzjmblblfue72Y4vWr7mvzVW/dnv9mL/AI2LRzeP/R3+Wf8AU6ZiXyL7GZ+eJ/IkZo6mHw+b5Pmj2ZV7hC1RXlRq0EtgivkG0Sd0EmVkouzaNP3KlfJaVkGzZ5HgF2obNpW5a2J5srarYqpVrYNUl5CDdobWPJ7ob/LMi/8AizkubfLL6NnWu53/AOl5P/qzk06+PL7s53Uu5/G/D1O1pJdSj9zqul/lx+xyjtrbqkV9Tq+lX91F/Qz6Z5fyH5P2dEtIMJK9zeci1abWxOCt1sh4JPLGfLEvpJvZl6nVDS2bYrYFW73C5F2Tx4K2DXy1sVS29jGbV23QmdjLtuXxFajW7ojpu7Pmza3BiVyyLY+DL3BooS9LkmYZc0/b1x6bKz4ezfsFua5qO59ND9LTPn/tbg9jzvPPh6To862x/clpcs1rD3TpZNJ0elg61pcqTU0ZTlxS9Lnj+nqJIOqPxxamGVXCSdn6Nrw7PSZy/tr5cdl8wd3sN3ygrRU7LpNSI0NvJWK9hNoq9g9iLbyHuy/tIN7H5auKemk37H6pJn5ay/4aW/g8uX4r0wn9mjaxf30mvdl0ibyRv3MtWv76T+rGi+bPFfU+c5P9Xax/BuWgX/Dx+x9a4Pm0SfwYr6H0ukqPoOn/ABjj835Vi0pMbJlVUNmbOmAE23TFewJcU2UvBEV7BUTt0eB80GnQfOwY0r5NZocOoi1lhbPiw9G0uOd/DR7D/wBQrvcwvHLdvSc+WM1K/PDjUYqMVSR+jVPYNu9iWzOSSaeWVuV3Vt3uFdhNVuKdF0TcLixsTYvjYJf/AEJxyUDa70Ea8JlqmEvJLkX/AMYZMXqe6RYQjBbUjK/dmLonj6Xuy18slKgpK2iJ2t+CpIt0SjvwIvbct/Qx2sb8JWTWxOSO/HBUmT97JNCV8eDGcVJNNWmZK02/Au/BbNpNyvPzdJ0mSfqljTZ+2DR4cS+SCVH087eCpUYTCS7097yZSfLFWWyi7RnPDx3u+RBexUyFNDewfGwX1BKiRi92En7lSKkuWIyuV1raVXJKRXTYRdpNiSYaS3DaCY1UsKfAST55HAuh8Hn9I1UqQklTtC2x6t90TxflZbESSaa8GfqT4RNmtiRVDtjK20oKytqwqLpjacGOXHGcfTJJp+5mvTRjRLN+KS2XbytV0TRZ25Sxq2fK+3NG+IKjYKj6d0Gr4PO8ON/TYnVZyeK1+Pbmjtr4a/Y/RdvaOL3xpnuKIcfoYzhx+l93yfbxF0HQv/lL9gu39Cnti/0R7TjEq9NGXo4/R7vk+3iw6Fo03WFFfQtE1Xwkj2HS4JGNu7MbxT6Pc8l/bxJ9uaOW/oIu3dGuMZ7rX1CVj0oe65J+3iR7d0f/AE0fdo+nabTKoRSkfcuRSfgynFImXPnnPNT01G0Iq+S+BR6Waa9vkcXz4CFvgqSGtG2LV2zVO4o/8SzbG+TU+45f8Sc7rvxbPS3y8ptJJI9ntv8AmWeKnbVnudtpfEOR0+pyR0+f/NssXSL9zFcUZ1adH0vHrUcXP5YtO9ip+A9kFF8szrzo15HKIxZAoAcAYvbgiKC1YAAgAAD+b8eNudt0dH/CptZMkfN/9jn/AMNZLcXT+h0L8LF88/8AMv8AwfRdT+DmcX5Ojx4opI8GSOBl8ulC65FlCRjBBVIpGQVNk8lW/I8giNKzwe9E/wAulS8Huu7Vnh96tLp0vsYcv4tnp/zjl+Wqf3Pe7Nf/ABsUa/kalOS+p73ZjS6hHfyczC/3fRck/wCp03Fbir9j9EY4toxr2Ml5Oph8PmeX5GGHwQyeS2XejEtOi+FVBEW3JURGRi+RwGACFmIGT2MbLyRrcLFT2LYjsR/QsWPK7oi5dMyK6+VnKJY/Rlnve7/3Osdy1LpeW/8AKzlU9ssvuzQ6mO3/ABv7el2xGL6lF/U6pp1/dRp+Dlfa9PqMfudU01LFH7GXTeHj/IXyzolFthm45HyIWQpYaFQ3ewil55K34Lv9spdInXC5E5xim20l5Pl1usw6TFKc5o0jr/c2WTlDBKo8bHlycsxlbXDwXls1Gz9X6/pdJCS9Scl7GodR7qz5nJYW1Hwa7nz5NTP1ZZttmK9MVRzuTqbfh2uDoZJ5j6M/U9Zmm7yydnz3lm23N2Ryp0kXHHJ67p0auXPa3JwYz9JKUqp22Rc+TKfrU/mWxJzVUjH1K9Zx4/SPJJK0mftj1OeKTjkaZhFOaqKsjxTjK3HYvq2JeLHXw9bSde1mmr5m0jZui91QzOMM3ys0NtN8UW3FeqOzPbj57P21OTo8c58Ox6TVY9TH1Y5KSZ9V0tzknRuu6rRTTcnJL3N+6D13FroJTkkzf4uol8ON1HR5YX48PcavgRVIJpq09vAvazcl/bQ1J4ErdlT34K9qoi4ZN7u2PxUT3s/DXutNJr2P3as+bqW2kl9jz5vxr04/yaXqX6ssq92ft06NZ42fNklWeXtZ+unyqOaL9mfN8l1yeXZwm8W7aW1ijXsfs3xseHg6vjhCMW+D9X1rC/J1eLqcZjJtzuThyuXw9hEPJXW8D5K+s4L5Nr3eH28/Qy+nrUybo8v84wVdhdZ0/uPd4fZ6GX09WieTy11jA3s0V9Yw+6HusPtPQyekluHyeYutae+TJ9X09XY91h9noZPTVMNo8pdY0/8AmKusaZ7Jj3eH2ehk9RcGLWx5y6tp092jGfWMF8j3WH2voZfT0ynlvrGD08kXWMHhox91j9noZ/T1fTZKPMfWcCY/ONPV2J1eP2ehn9PVQdHlfnOn4tD85wJ7se7w+09DJ6zqtiM8l9awVyF1jA1yX3WH2Tp8vp6voVFUY8WeS+tYE+TH84wt8l93h9r6Gd/T2KXASS4PJ/OcHlkXWsHhj3eB7fJ6xb24PI/OcJfzrB7idVh9nt8vp6tsvg8l9awe5fzjB4ZPdYX9p7fL6eo2/I2rY8tdXwVdhdZwLyW9Vh9noZPUV2JNHlPrOD3QXWcHlonusPtLwZV6m1E9R5kus4F5Qj1fBzaHusPtl6GX09NO3uHszzPzfBfKD6vgXDQ91h9no5X9PU45LbR5L61hvajN9YwV4HusJ+09HL6endg8yPV8DV2g+saf3Rfd4fZeny+npt0RteTzX1fB/mRH1bT3yPd4fazgy+npJ7mSZ5b6tp1/iKuq4K/UPd4fa+jl9PTtsJVyeX+b4P8AMPzjBf6ie7wn7T0Mvp6jaSGzPLXV8HuqH5vp/EkT3eH2ehl9PUS9L5LdM8pdXwXu0V9X07/xIvusPs9DL6em3uSzy31bAt/UYvrOG+Se7w+z2+X09e6XAizyH1rCvIXWMHKZZ1eH2ehl9PXtBteDyX1nBW7Rj+dYPcXq8PsnBl9PYt0HK0eQ+s4gus4fJPd4T9r6GX09dIj5PJfWcF8lXWcL8oy93h9no5PXbtCttjyfzjBXKJ+dYfcl6rD7T0K9VL3LJpI8pdZwkfWNPzY91h9l6evWT2La8nmR6xp6W4fVtPV2T3OH2l4MnpN77A8x9X09cmL6zgrke6w+ycGX09Ryt7FT9zyfzjD7hdaw+6J7rDXyvoZfT1ZVuap3D/7o9R9aw/Q8bqmqhqclrk0+q58c5rbY6fiuNedtZ7nbi/vDxWe324l6tjn9Pq8k03Of8GyR4KYq0zLk+l4/iONfkvcyUlREvcPZGf7edR8gi5G7GjSkkVWSZBiAC1ZAAEAAAfzl88W/SdI/ChqPrvdv/wAHO/ixds6H+E7TeS/P/g+i6n8K5nD+To8WZGKSsyfBwMvFdKIrYZfqGYDEq5CReAC5El5C5EgRjw0eD3t/+Pd+x7z/AFI8Hvbfp0vsY8v41s9P/pHL0l8SX3PY7UTj1ONe543payyr3Pd7Ui/zKL+pyuP/AEfR8n+Lp+D9EfsfquGflhb9MfsfquDrYfD5jk+aLgjVFvwCvJiZJ7CiVvQF5MTOtjHyNKWCrcbl0glfAQVloSDFGUlaDJduhoR7EMg0VXk9ytrpeV//ABZyWU29RO/f/udc7j26blv/ACs5NlgnqJte7/3Of1Ndz+Nvh6/ayX5hH7nUNM7xR+xy7teT/MYqvJ1DBfwY17GXTXw8v5H5fuuCPkJ0Tk3HI0iZUxSQRksjKLv7nwdV6hi0WnlknJepeD9dfqselwPLJ1SOa9ydYya3PKKl8iZrc3J2zw3en6a8tYdb65l1mWSUn6fY8Rz9S+cSavYuNeqSs5fJzW+H0XB0+PFIzxv1uoxPohop5JJ0fb07SQS9TR6MYxiqSRp551nlyWfD4MGgglc1ufRDDji9on0v6Ilb/U8LyV43kteX1PAljcoxPIStGzarH68bXJrerThllFI9ceS17ceVr9NBL0ZUn7nvrT4skFt4Nag/S4z8o2Hp2f4uJK9y5Wss9yPw1PT4u3BHnZ9PlxbVsbFF71RMuGGRVSswnJY8ceSy+WsRiqdqmfRodbm0uVSxypI+vW6GrcEeZOEoypqqNji5rLGeWM5JrTpPbHXIazFHHll6ZI2W01tvZxrRavLpssZY5NUzovbPWIazBGMp/MlR1+Ln3NOH1fR9t22FvfcWYp+p/cya22NzG7jlZTVS3ex8+vi5aeafsfQvLomSPqi4+GjHkm5pZdXbRdXjUMsrPnTTdI2XqnSvXKTgt2eX+VZo8RODz9NbluOtw88kedvdNlTa2s9FdLzv/Cx+U56/SzxnDm9fV47Xn8+Rs3uz049JzpcEn0nOnaQnFyJ6vG8+bio1ZjH08M9B9Kzt24h9Jzv/AAj0uRPVweepeEyXJvk9OPR8y3oflea6ol4eQ9XB5qVPkrdLk+99I1Ce6D6Tna4Hpci+rxvPT+ovfk+99J1FbIQ6Tnb4L6PIerxviadcmMrvk9N9J1Le6dGMukZ26SY9HkPV43nXJLcxbknsz049I1DW6D6RnT2RZw8h6vG8xSk3vZZTa2R6n5Vm49JJdKzN/pYvDyHq8by0n7mfjZnovpGav0kj0rPX6WT0eQ9XjedG7qw/1VZ6S6TqL/SPyjPd+lj0eRPVweby92Yy2lSZ6v5PmW9E/KMzd0PQ5F9XjeWvVy2Xf3PRfSdRfBPyjUXwx6PInq4Pgj6vcbnoLpWo9mVdI1HNMejyL6mDzvsHNpVZ6a6RmrgwfRs8numT0eQ9XjefCUmtjFykpcnqLpGeO1EfRs13RfR5D1eN5ybq2E/Nnqx6Nm9NNMwfRsy8Mno8kPV43lptu/BZOSezaPVj0jMl+lh9JzezL6PIvq8byX6krssLa3Z6f5TnumtiflOe+Nh6PIetxvMlKUX7lc7WzZ6Uuk534D6RmS2Q9HkPV43mxckt2SUmnds9FdI1F8My/Kc7XBfS5E9XjeXL1XyzP1OuT0H0nUXwZPpWd/4R6XIvq8by3J+5knOuT7/ynPfA/LNRF16WT0uRPV43nXN8ther3PUfSs7X6WF0nP8A5S+lyHq8by1OXuEn4kep+U5v8pH0jP4Q9LkPV43m+m1+oqTr9R6S6Tn9irpGfmtielyHq4PLS35CdTpnqPpGf2IujZmraHo8ierxvOnvuiJtHpx6RnvdOiz6TmXCHo8i+rxvKm37khZ6kekZ2+DJdIzXVC8OZ6vG8xvbYwTlZ6k+lZ09osx/KdR5iyejyHq8bzUnJ8imtrPTj0nP/lEukZ3/AIS+jyHq8bzkn7kl6k+T0V0jUJW0yflOe+GPS5VnJg85epB+t+T0/wApztVTIuj6i7pj0uRfUwee3KK5J6m1R6n5RmrhhdIzew9LkYXkweY7rkx3b5PVfSc3+VmL6TnS/SyelyE5eN5ybI21wen+VZ0v0mD6Vnv9LL6PIy9XB5+7MlHyfd+U5+fSzKHSs9/pZL0+d+T1uOPPcWld2e728pXxR8+LpOWUla2Pf6fpI6fGklubHS9NZlNvDn55ljqPthZbZCo7+PiRy8r5Rsj33D5LaovywqKirYBFUvcxkZebMZEqaQAEUAAAAAfzhGMmm2qR0v8ACZpRm6//AJRzhP5Kkzo34UV89Pj/AMH0PVfhXM4p/Z0d8ECuyvc4OXy6UELIDA0yFeAmWwaKpkkLD3GyMWm2jw+84uXTJV7Hunh94NLpsvsefJ5xbPT/AJxytqXrlv5Pd7OT/MI2/J4knUpV7s9vtCV6+L+pzMPHI+i5P8nUMK2Vex+ibPz07uC+x+vg62Hw+Z5PmsUXgB0uSvL5E7K0rIvSw6LIoych/VBD4XSp0WyWvYtquCom9ltkLaoJpLK+CXfAQNG9hJ0E237F3C7eT3Nb6Zl/+rOTZU1ll93/ALnWu40307Le/wArOS6h1nnS4bOf1Udv+N+Hpdruceoxve2jquB1ij9Uco7alOXUYXtudW0n8uG/gdLWP8hPL6Iqw0kGx9TecXaNXsuDGTUVbdUZN+mzyO5eoQ0OglO/mapGPJdSvXjxuVkaz3v1n+9enxy24Zpsnf8A3P11uaWozvNN3e5hij8RqCXJyOfktfTdJxenjthKO31MXKknHk9hdPXwr80efmwywyfqjsafdK3ZlK+rp2s+ZQkz2o+maUo7mqwqM7XJ6Wh1rhNQlweeU2888bfh7Ke4T33MYSUkpJ3Zk0vL3Rr2WNXLc8MXe6PH6vgcZ+utj2bV2fnqsSzYmmr2Mscrtnx5arWqTW/k+jQZvg5VT2Px1ON4puLRhDk2JdxtS7jaMeWM4KUTPmnZ4vTtU4P4cnsexBqaTi9jwyxu2tnhZVa90ed1PTqKc4qj0m3deTHLBTg4yV2XC6MMrK1b1U3fk+7ouvyaPVwkpNRvdH5a/TvBlv07WfPGLlK/00bnDyWV7cmE5MfLsHStdHV6eOSL3pWffexoXY3U1CUtPklvxub3ikpQTOz0+fdHzXV8XZl4ZJ2q4K3S2J6b4Mo1wbEaF+WDdrgiS9jOaQXBjePG/LOZWMfSk+EKi3wi7+RXkx9HH9MrnVcVfBHFexa3sluxOLGfpO+o1G+CuMa4RQW8WP0vfUSiv8NhKKd+koHo4/R31i0n/hQSj5iZIOyejj9J31i4xa4EYxXCRkrDMvSxO+lLyiKCu9itDgTin0vdU9MbDxq7oqjW5kPTn0lyv2wcV4W4cPoZPmy3Rj6UO+vzSS8F9K9iteSbovpY/R337FFf5RSa4Mq+hK3HpRO6/aehew9MfYrD4ovpQ78k9Ma4HpjJcCmWKS5HpT6XvrH0Rfgej6Iya9iWPRn0nfkno34MlBVwiWwh6M+l76qim+ERxV8ItJPYtUPSn0d1YtbiUVyZUg0h6U+k7qx9KvgOG3BWmTck4p9HdT0xrgNbfpMlugmh6WP0d1YtJrZIih9jKk3sV7bD0sfpe6sPSkuCJK+DNJckrex6WP0d1+09KvhGXpinui0uRIejj9HfWLjH/KT0x9kZBpNF9KfR337IxVcINL2QSpCnZPSx+jvv2JK+CelXwZUxTJ6U+jvv2xarwT0fQzZEnfJZxT6LlftIxXsHFXsjJckHpY/R31HFEcVfBk+S0h6WP0d9YqMfCK4Jb0ZJJbhj0sfo779vzcVd0X0J+Cq0hTselid9T0xS4Ior2MmN7HpY/R31j6fFD4a9kZBInpRe+sPQuaRVBeUjOiGU4p9HqVi4eyKor2KgkS8WP0lzrFpeyL6FW6RUUno4/R31h8NeUg4xT/SjJprZhRbHpY/R31El/lRJQVbJGXpDTZfSm/guVRKKXBaVBbFfAmElY3K1KHkP6BJnprwg0vI+UNWx6aHwmxUkLDFKhs2jYe6IVvbcbViCIooAAgAAD+dZ436vV4Oi/hNjaWSSezf/AGOc6fJPJFr29zo34TZZtZYOFU+V9j6Lqp/RzeHzk6P5oMlWyJJM4GXy6M+FBSGBs8lIHuC1UGyAEVcHg95tflcvsz3X7Hg950unS38GHLP6tnp/9I5a04+q/LPe7Opa+N+54VuTleyTPX7WnGPUVKTpWczHUz8vo85bxeHVsO2NccH6L9J5S6ro8eNKWVJ17n4Ze5enYU/VmVnSx5MdPn+Tp87fh7fkNL3NU1PeGjjBvC/VI8vL3tlt1hf32F5ZDHpM7+m/pKK4GyRzbN3lqpcRaPny926+lVnleoj1nQ5V1H1E9aRyyPdfUa8n5z7r6jTqye4j0n8flXV/VbLtyclxd1dSvds/Vd29RukmX3ML/HZR1X1bhvY5VLurqVLcPunqdbMe6jH/AI/N1Vt1aG97nLsPd2uhtOz78feWT5XKN/sJ1MTLoMo6Grd3wiNy8cGkYO9F6164/K+T1cHdXT8iinkSbPSc+NeGXSZz9PX6pheo0WTGlzE5X1bp2fBnyP0SavwdS03UdLqqWLNF34LqdBpdSmpRjdc0YcmOOb34OTLg8ac37U0eaerjKUGkmdP0y9GKK8pHy6Lp2n0zuCSf2Pvikvqi8fFMfhh1HNeRkkiPYBmxfhpa8MZPeznvf2teTP8Aw8XsjfdZP0aecl4RyXuHUvL1Kdu92a3UZaxrodHx92cfBFpWudj0Ok6f1ZPWzzoV6tt7ZsPTsajgUuDhc2Vr6HL+uOn00lt4Pm1Wmjlg3W9H10mqRPS0rNWZV4TO43bWc+nlhm0z8vi715Nj1Onhng9vmPD1Wllgm7PbHKVs4ckynl9fT9ZKNRk9j2MU4ygq3s1aEva7R9mh6g8c1jn+lkyxlTk45fMe63vwWW6tH548kZJSg7sz3Tt+TwssrWyllfDr9Ip3NLc8icPTNpqmjZ5pSifBrtCpwcsa3PXDJ7ceenjbJXfzH29O1koyUZM8/PhnidSMYqVpp8HrdWPeyWNphOElae5+itbms49Tmxtel3R9eLq2RV6/B5XDy8MuPz4fd1PD8TDJ18y3PDakoP3R6/5jiyY5Xy1R5GV25el7M9sJpnxy/FfV0rN8DqGLIpUm0dZ6Zkjl00WndpHHIN+qMls07Ol9nar4+jSe7VHV6TLzpy/5Li1Ntj3SBE09ynS34fP0Q8FsjtP3FB37DfgMMRRXRUzFJjgqaUJmPkA0yDRi2WK82TZpVZk3tuRbBuxtUutw2HV2G1wNgt+RSI0VLYdy7GFdlaCXku02LgjKR0TafK0K+hjbMk7GzYnZHbZSjZti9iU/cr+osu12iT8stAVvZLU2qSqiNKwg+C7UpjfyiJqw2rG02tpLYie5XQ44G12MJ2XlEXJNmywmuA1YVJjZtW6Jdh7lG02xV3wV7ldeCDZs8FT2IrbA2u125LVrkxYG02encrXsRj1DZpVYXBLtBNsWnlkY27L4FDapbfATbKkycMbFfNhqybsbjZsKifcqew2bSV1sE65K3ZENm1bVC0VLwSqG02csNPwQbjZtaYX1IpeC37FUbIOQ3QTaocEuyrgmzaglixs2NMqI2qJY2qsUYpWyvmhsWxTMaMtyIjHgJO+S8l2ILLRHdkAlFprcL3AlBmSJJ0BgA9wFAAAAAH854Y1KT4Z0z8J1H4GTa3e/7HMvhSjy9zo34TSklkT/AP5sfRdV+Fczh8ZOkKqKyfRFUTgZTy6X6ER7GXAZNKx5L9ypIP6AtgR7MyaVBrYx2sYz8JHgd4yi9BKLkuD0uq66Gh00smR7pbHNOvddy63NKMZfJZr8/LJNOh0fBcs5XlZHu1F0rPzjOePJcHX2Yjlp+lozr1uoQbf2OVbbl4fR6mOOqy+Pkm/myS/c/Ka9Tb9TbPS0nRtZqUvTjaTPT03aerf6lVmxjjnWlycvFjdVrr9Kx15MMTdt1Zt8OzMkmvVNr9j0NL2bigl65X+xn6OVed6vjjQpzTv5GWCctlBnSsXamhj+qN/0R9GLtrQwd+hfsZzp6wvX4Ry5wyLZY3+xY4ZpXLG9zqi6Bob/AJa/Ysug6GVP4a2+gvT1h/yE+nKJ4cnjGw8c0r+E7/qdZj0LQV/KX7EfQdC3/KX7EnT2n/IxyiUJuP8ALf7GMVOLpxf7HWH0HQ1Xw0v6H5y7c6e/8Cv7F9syn8hi5TkUmt4v9iS29PJ1HN2vop+Ev6Hzz7R0cr2/0Jenv6ZTrsa5vDypPbwfpOb9Cje30Nx1fZtz+SXpPg1PaWrxxfpl6jC8WUZzquOte0mrzaefqxZZKvqz29B3XrcFLJJyR5+o6FrtPFv4Tdex5+TBmxy+eDj99jG5ZY/LK4cfL8OldI7mwamoZHUn7mxYMmOcVODUk/qcXxTlifrjKpG2dp9cyLLHDmla45Pbi6jfitPqui1Nx0Jbit9zDFNTgmuHufo/ob29zw41lnh5vcGT4fTsjTq0ci1fqlrJy5VnVO75OPSZ/Y5S7eST92aXU3w7P8bj5j9MEf7+KfDZsOOlijFHg6Vp6qMWbDGMVGJxOW7dfmXhGSVmDoqfnwa3nbX3tZr5tuD8dVp4Z4NNbn6yfqfyiO/HJZbGUy18Ne1mmlp5txWx8qe7UlybPnwRyQaa3PC1ujljyNpfKe+OW/D3wz34rPpur+DNRk7i/J7+LJHJFUzVdoo+vRaqWNr1PYtxlZZYyxsV06Jwm358H5afNDLBOzO1Z45SxrZSx8+q0mPLFyo8bV6PJCXy8Gwzk3t4MXjjJUy45sseTTVUpRk07Dp7s2LL0/DNN+T4s3SW94yPSZSvfHkjzXTx2lVH5RTu2+T0ZdMyq97Pm1Omy4Gm0ekyZTKb8Pzg9q9jevw/zL0OF8mi/pjv5Nn7DytalwRvdLdVqddjLi6PCqM3wfnieyRm2daXxHy2Wu6p5L4LtyGZ1jUReURJ2GJSAsiZGNjLkiRVwVcFBNUYstKy8AjFp0EtrZWvYE0DFUrJ52FMU2qfkm4sPfgmkVC9iJMUBUK8mJU/cuzah7IB8bEBbh7MJMMyILcjVlWz3K9lZPCotmLt0E0w0LRa9xSr3MbZVb2KaEvIfIHmgGwba43HmgYoJhFsx3fBkrKvNkbJe+5WECkAXQw2mOR6QnhU14Hki2YfIPAxRQwoyFpUEwmxEXJbIybC3ZXYQ8EE9TQBePJkKYslluzFVVVuKMCoDKimCsqMhfIsjAFIyrncrW1gYpKx/UVuGnQTQKsekA8A4KtkS/A3DZaCoEfIGTaoion2ITwMk9tg9yIrbKLskTYFV+SShRGqDfkOSYsBSLb8E28j1VwTQr43It1YuyPZUgL5MZFQe6AxAAUAAAAAfztkbateDffwoyXmnF+5oCccaa5N3/DHVafDllPNNRr3PpOpxuWHhysLrLy6q9th4uzzJde6XdfHV/ci6901P+cv3OJlw57+HRnJLHrLgi3dnmQ6702Tf/ER/cS690yCd5439x6GX0vqYvTsr2Wx42XuXpkIus0W/ufhj7t6ZOXpc0q82JwZfSXkxe+/uWT+X6o8aHcvS5NtZVS+p9Oj6z0/Vv0Qyxt/Uxy4bP0uPJI1v8SMmRaWKTdNbnP4R9MLrc691/pcOo6SUdntszm3V+kanQ5ZJxbivNHJ6njr6DoOfHU28z0pq2qPY7fz6fDlTzpNfU8iW6p7UR1FbN2vqaE3jfLs54zOeHU+n9S6d6FXpielDX6SVemaOOwzalK4TaSP3h1LWQa/vHZucfNI5fN0Nt27FDLjlxJM/RyVe5yfT9c1+Oa/vHR6EO69VFKLdntOokaeXQZx0hMrlZzuHd+eDqSs/ePeU0rcT0nUY153oc2+ep+wTs0Rd5Tv9Ox+q7xSXzL/AGL6+LH2ec/TdlXuVvbZmlf20xNfp/2MJ96Y6r0/7F9xiw9rnb8N3TT5K2vY0R96R9LqO5+f9tJy/wAJL1EZeyzrfk4r2JKUWuUqOcaju7USv0bHxS7m1026k1Zj7iR6Y9BnXT8ufFFfPNI+LVdX0eBVKaZzPUdZ12TnK1fg+LPq9RkX95kbs8c+pl+Gzh/H2/tv+v7k0NOMVFs1HrfUsepn8sEl9DyIxnJ3KTMpNfejV5Oa3xp0uDpZh5R/O6TPt6JHJ/HwST5R8+l0ufUTSxRuzde1egTxzWXMvm5MuLC3yw6rmmMsbj0+46TH6uaR+6aaryY4opQ9K8FVJ/U62E/r5fM5ZS14neKb6TNXyctm3GW3lnV+6oerpU/LSbOTZZXOS9maPVzcdj+Ok3H6YJqGpjN+D2odQxNJeUa9GaTafkzUqez3ORljt2s+PcbMtTimtmj9ccsco1aNXhmkuGftDV5YeTzvG8bw+GxuKTqI4do8vS9QbSUz0MObHkWzVnlcNPHLCxm6/qfnnxLLFx52P19CvZ8k9Mosxls8sZbGvazSTxSbrY+Zb88m0Z8UMmN3yeF1DRyhbgtj2wy22MM9sNNqZYpKnse5pdRjzY00/m9jWcVq1LlH7abPPDk2exllJYzywljZmvmDW5+Gj1UMsEv8R9O/k1ssbGtlhYxXIpJGSVvYk9iS1hNwtVseT1tOl7nrQ5Vnk9cr4iSZ74ea9OO215cmm4p+DZexI3rW0axP+YkzcPw+w3llNnT6aJ1l1g3/ABrYycdyY2vSvcNts68niPlc75qr6Bi6RLMmJbKTll9JYaRoVfIY5IbVILZtEVhF2q7WOSMi2KMg9yItk2FDkNsMiFGLbsu7FNsyUshaIYoq5KEABG2isxAyTVEVsLgJ0WfQob8GLlGP6ppNlW+8XaMphZNm4LnYO06CW5WY1UsqMTJJPchR2CN77BstT9HJURFZAaBEALyRclXBPOwNnI3CsoBLcr5CVC1e4EexE9zJtMx8lhFFUgn7BsUKBbKQYhGREFQF8k8iIBME3QFoIJiwDf0IuStoAE00FyBuuDJWQtUY+oqYFBGRybAt7iyIUPB8nkjjuE3ZlZNJpjuKKTyQKYovHgie/AFXAoKxYCth4ALAH9SNuykD7igAHIS9gPAD6gEYBbh7BB7gYgAKAAAAAP5zcqdem7P1x5smLbG3G+aPs1/RtfpJpTxNpH5vTaj0p/Be/wBGfSzllmq5WXHZ5fPDU53l3yS/cynqtTGe05tfcylpNROSUMMk/sfotJqotReCTf2ZbcCdz8cWs1Ct+uRgtVqJ5XeSVH0y0mrk6jp5fsxDRaxfK9PK/syd3GbyfO8uZP8AmNr7keedWpP9z6odN1ybk8Mmn9GYPp2sb2wS/Zl7+NP7Pw/iM6arI0m/c9Dp2tzYNRilDK1ur3PwXTNWpb4ZbfQ+vpnSdbn1sIrE1FP2PPlvHY9MO6uy9t6h6vpeObdv0rk/TqWgxauDhOC4Pz7f0ktJ03Hjlykj0pL29jhdRhjbdOnwZ3DWnMe7OjQ0K+LBbM1e23Z0vv7F69AnXBzZKv3ONz4SXw+l6PnuWPl+2P4jj8sW0JYcjVuDNh7RwYdTNQyRTNxl0DRTh+hGOHFtn1HV3C6cr9VbU0zFtO2dKzdqaGabSSf2Pkz9oaZR+UyvBXjj1+Nuq0B0knyyev1Omj7ut6FaHVyxRVpOj5NNGOTVwhWzPK42XTdw5Mcps4jvsYeq1TZtMe2MueCnB/K0Y/2P1HKbMpxZV43quOXVavBW6bM5Qj4Zs67R1B9GPtDI4JN0y+lkw91xT4abKC4QUdvY2Tqnb70GBzm90a1OVt+yZ5ZSy6bPFyYZzemUE3x4K1v8qbZ7na3Toa7J6Wribbp+1tHGfqlFM9ePiucePP1WHHfDnHw8kkmoM/fHodRmSaxv9jp2Pt7RQX6E6+h9UOm6TDCliW30PWdNWpf5D6ci1OLNgkoSi0z85J0jYu9nCOtUYRS+xr6bm4xrc188dZadLi5bnx7bz2NooSxeuUbZucMcYrbY1/svG46JWuUbIttjf4MfD53q+S3KkUkudyV5Ycb4CT/qbetRo/M2+Pq+L4mgnHm0zkXUcSxazJBqqbOzZYeqDT4ZzHvTRrT6+WRKkzU6jHcdPoOTWUa/H0ya2M44JzbcVsYU1VeT1OmTVelrdnG5PFfSTK2befLBOK/Sz802nujaJYcU1XpPlz9OxzVx2PKZ/p5zk8vE9aqzPTZ8mPImnsfrqNHLG2q2PmScZbl3Ku5k2DRayOVJN00fYt1Zq0cksc04uj2umaxZY+mXKPLLF458b7Yrd37ky4ozTVWZqnF353sxfFx3R5S2V4y2V4mu0bjNyitj4GnextE4qcark8nX6J4rnBX9D3xy34bGHJb4fDp808M04s9zSalZoq38x4KW9y2fsfpizyxSTXBlcZYzuMsbNF0rJOSbVnw6PWRypRb3PrcvS/c17jZWvljZWU3HejX+ozlPVUvB7WpyejG5M1/LP1ZXL6nrxzyy4sd3dflJt5dvBvvYGJxxOVco0XFD1ZIr3Z1PtbSx0+ihtu0dbpcWr/I8kk09mC23MiKSoJnWk1I+cvm2q9iKqD5J4oWIySF+xjdcBO/BZBlfvyDHzuiye11aL2Wpv7VOmCX49Ib3pi4VNwvex5+hVV7kaV2TVi7gih1QvayaNAAJo2jKiPkpbLAY28giRCKmrDJW5UDQR8laFARbn5azPDTYZZZuopWfsttjVfxE1c9L0fI4SabTPbhx7qxzuo0rr3dusl1XJHDNqEXt+5uX4fdXzdRwS+LK2jkGKXxpyc/1M6n+FujeHSSyPhnR5OKTDbWx5La3l0kR8hNi+fc5et3Tbl8bCxaR+c80YQcpv0pHyQ6nosmT4ayr1fcynHb5S5R97Ssj2Eakm7tDyY2WeFl2qJIINWYCKisiRaZYLt5CCWwabILYIkC0VyRKd2PSZE2aSiMyMVdgRFLRFyXQCy2SxaLYQv3CIL4MWnyZEZdCPYi3KJKiB9SebFNrcqWwAlFVpgvyCCDA+Bd3yRlfGxL33IHJaI3YLQsWEGQAFVbguhHzZkmqI06FEEYV+S0HwAW5GioASmNy2G2/AEfItjcq4AiK3sCNUAsq4MS+AKRc7lJ52AMhlRiBHyCsgWAAAAAD5NT0vS6jfLji39j8JdD0HHwY19j1KbVlW/J7TnyYXCV5cOhaCL9SwR/ZFfRtDKV/Bh+x6fgLgyvPkk459PNj0fRRe2CP7B9K0V38CH7HpJX5DXgl5sl7Mfp8C6Xo0t8Mf2Iul6GN/wBxF39D0ElRKHq5fZ6eP0+B9K0Vt/BhuZ4OnaXFL1QxRTPsfASfptcEvLb+yccitqqfA2T23siqraI1dVseVtr0k08juzCsvTJN8pHKMqrI17M7F1zG8nTskX7HH+oL4ernH6s0Oojs/wAfl+nvdkZPTr4q+WjpmL5oWch7d1fwNfD1OlaOq9P1Ec+CMsck9i9LlPMqfyOFl3H2KKStGE4e/BnG9n5DdXfNG5LjHLw+XPO/dJ8LUrKo/K+TUYZPh5ozXKexu/fmtxTi8KacktzRm0k5PlHN5dd23e6Pdw06t2tnWbp0N7pHtKk6NA7G6pDDFYJy38Wb9CUJwUovk2+CzKOb1XHljaz2tpoxdX9j9F8qV7nydQ1GPTaeWWWx63WManHbldNR7+1NYvhp8miL0/CS8tnt909RWt1LUdkmeLBxik3vRy+bKXJ9J0mHbx+XQewdJGGm+LW/JuCUUt0aX2X1TF8FYeHVG5wkpR332N3prNOP1uOXffplJep7cGGoaWKVcpMyUpXSPO6zrMWl003klTaNnOyRqceFt1HNe6cnxOrybeybPg01y1MY1tZ+nV9RDU6+WSC2bM+mVPVwVcs5GV3m+k45cOL/AOOm9tQcNHFJeD2Kbf2Ph6RD0aSKXsfdF2zpcM8PnOpu8qm/AWztlfIfFHvvw19+GMre5qnfPT/jaR5Ura3NsbSdI/DXYIZ9NKEo3aow5cd4vfgz7bHF79Eqfg/TTZ/Rnifb3LoJ6LXyVVBt0eY401fPg4nPx6r6jpeSZ4abRp5qcE00fq2q5PG6bq1FqE3sezCUJJPlGhlNJyY2Pzy44yjclyeVr9G4/PCJ7ckmk/B+eRKUaasky0xxys+WqzUvXuq9z9Mc5YpqUHR6PU9Iqc4Lg8zd7XVHvLLG1jZlHv6TUrLiUb3SPrW0K9zXdBl+Hnir2ZsDmnCMonjnjGvyYfuM9ktz851NU1aM/V6krVB7PY8pdPHdjx9do3bnHY82aabVG0yhGXJ5ev0e0pRR64Zbe/HybeZgm8TtPc9fR6uM0lN7niuDjOpFcpQdxZ63HcbHbMno9V1K/lx8nnJNQbfLJGbnNue/sfpji82RYkt29jPi47tjdYY16Xa+ilqtYpSjcYtHUtJjWPDBRVJI8Ds7pi02m+JOPzNGycRr3Oz0/HqPm+t57ndMmr4K0qItluST2vwb3bbrTn26W6fuiNpnwdT6vo9BjbyZFa8Gndd75ilKGkjv77Gxx9PcnhlySN61OrwaeHqnkUUubPG1XdPT8Vr4qbX1OU9Q6/1DWOSlncU/G558JZJS+bM23ydDj6KftrZdR9Oq6jvnQY36VJP+p8U/xB08Zut0cyyxak23+5cOHG8TnJ39j3nSYPK89ro67/g5+p/pZ+mP8QNM571+5zF+lXjUXRljjDFGpQb9mX2mH2Tlyda0/fGiybOS/c+zD3d02bSeRfucbSvaFxszi/St3K15s88uhxqzmsdz0fWdFqV/d5ou/qehiyQkl6ZJtnAMGs1WL5sOaUa92z19F3X1TTJN5HNI8cuhkle2PUO2L2K6T3ObdK/EFXGGohv5extfTu5+naxKsijJ+7NLPpMpfEe05ZXuP3KuD8cWow5q+HljJn7XJezPC4ZTxXrMpSnREVq1sYvenZhYy2vgK1uV3WyIm2uCaBuyoxW25k3sNJoap2aB+KuritE8SdybqjfZNelnJvxJzufUlF7xUt0bvSY7rx57qNS0kY/Fgq3fKO19nYlh6PjjFU2jjfSIvUdXxwhH/EjufRsXwdBixtU/Sjc6rLWOmvwzd2+4jyKMHJ7V7h0/lXk1Tvrra6dpJYoS+dqjncPHcsm3llJHid99yZMU5afTzqW62NM0HVNY9THI8ju99z4NVnz6vVSy5Zbt2rPv6Hos2u18MWNed9jq+hMcd1oXltunYu1tVk1PTISm96R68r5Pg6BolodJDFd0tz73uzlc1nddN7il1upvs7KRrYUeD02J7FsnAMSsr2FihYBbIIIUBXa2Fh+5PI0bLBUGAtEKuBRfgQxK7DIIZRD4EVaAXvYZRaAXsSrAQDyE6AAWSwuS0Wh4ALVrYUQBtkfAhFQQXATKVG3wgGQxFVFsJBrwAT2Dsl+5bABsEboCslhBrYCGS4IuC1sBHyVEaoICigXhUBjQ4ZeSVuBSPYKjJoCWYvgyoj5AxAAIAAKAAD9N+BshfuGXQjYX1CYadFBv2IxRVQGJkuCqh4G6bTkj9VbFI3sSifM1uVXYVvYqVO7Ibr5uoJz02Rf/ABZyLreOtfkT92dhzxUsUq8pnJe6cLx9RyPi2zV6ieHT/j8tZPJi5Rd8PwbX2p1yWDJHDlntdbmq+hyj6kISnBr0v5kzn8fJccnd5uGcuLteHUY8mNZYyTVHgdy9fx6aEscJfP8AQ1HpncOo0+meJzb2o8nWajLqs8pzbk29jcvUSxyZ0Nxytvwzz5sus1UpzblKT4P11vSs+HCtRKL9L8Hu9ndCnPL/ABWaNxu0mbnqem6fU6WWJ40lRheK8k29fdY8NmMcgwZsuHLHJF1TOg9pddhnxxw5ZVJe5q/cnQs+g1Ep423F+DydNny4MzyRfpkvYwxuXFdPfPHHqMdx2bJqsePH8SUkkkc/7u65PUZZYMEvl+h8Oo7g1Wo0kcKdUqbPDSzTz/KvVJnryc/f4a3F0cwu6zxQnlyJJOUnyerk6FqMej+O4unubB2l2/SWpzrdq6NwnpMOTB8OWNemqoxx4NzemefWTC9scg0eoyaTOnCTi0+Dofa3XMeswKGSVTW25rXd3Q3psvx8MflfhGv6LVZdLlUsbcWpbkluFXLHHnx3+3X9drcWkwSzTkoxo5t3L1ietyyWOfyN+5+fVOvZ9ZgWHK36XseK8atJPYnLz2zW16fophd1nhVNv9R7HbuD4vUYOuGjx4xrdM2bsrG8msUq4Z48P9rutzqbMOPw6NpIKOGK9kj9nHfYwxbY0voZXvsdfCaj5Xku7V+4f0JbKzP9PLwnklPhlaoJvkvzNVlLrzHgd09Lx6rBLJ6fmS2Oa6jFLHnljmvS09js+SMcicXujTO7e33l9Wo08akt9jR5+GWb063Q9TqyVoqfplu6Z6Gj1zjSyPY+HLhyQm4ZY+mSMPRUre6RyeTi1dad3umcbTp8kMsfUpfK/B+iSvZbGtabVyxSpul7Hq6fXxyJJv0mrePVeOXG+rUY/VCS52Nd1ONQyy8GyRyY5RpSuzyur6dJfFgjLCWM+PLV08yMqcWuUzYNBkWTAo+UjwKcaflnodIySWRxfkuU3HrlNx7EGm1ZnNJ8H5w/VZXL3Z4WeWncfLJWluSaTXzcH5z1OKCabs8/V9StOMC4zVZYzz4fl1WOBN+l0zzJWluZZMsskm5oi9TXy2bfHja2pe2bpGnVfqNq7V6Q9RljmnDZO9z5O2+hz1meGTJD5VudG0GlxaaEYY4pJLc6HBw+d6cvrOr1LJX0YMaxwUYrhH6VXncSikvlkfnPJHHB5JuklvZ1uLj/AFHz/Jnu7M+SOLG5TdRXk0vuvu7FpYSw6aXqkvY+HvvuudvS6WWytNo5/wDFyZ5Slkfqb3tnV6fptzdjT5ef6fZ1Pqer17csk3ufC24wp7t+5jCWXLk9EY+p/Q2rt7tLVa9xyZ04wfg3f+vjjV3c61fHpsmV/InJ+yR6ek6Dr9QoqGGSv6HVOkdrdO0UIr4ClJeWj28Gnw4UlGCjRr8nXSeI9Men25ZpuyNdkx/PH9z6cXYWoapuvpwdOb3uuPYO587L6Gretyj2nTRzR9iZpRaSSZJ9h53jp7tHSkn48mSTWzRj73L7X28clz9j9QxpuKteDx9X0Dqmnk08Eml5O5OL/wARhPDjntPFFnrj11nyxvBK4DPQ6mL+fHKKXOx+Mrxy9NHd9T0bp2o/Xp40eD1Tsbpuol68WNQf0RsY9ZjbHllwa+HJI4sql66tM/bFmz4N4Tafjc3bq/ZOrx4W9Lle3jY1LW9J6ppXWXC5Jedz3nLhk87hlPh9vTOvdTw1NTbS+puPR+9sSjFal/N5OZTyZsM/Sk4rymJtTVN035Rjlw4ck8LOXKO76Drei1cU454xbXFno45xkqg/Uvc/nrBqc2llGeLPktcG0dE7x6jpmo5cjlFeGzSz6LV8NjHndflf3DbStbmr9D7w0Wvax5ZKEvr/APs2XBqMGVXjmpJ8bmpnxXH9PfHklZrfdldVRje4/wC54WWM9+Nvx1uVYNNPJLZKL/2OJ92616vquVx/Qm0dX711S0vR5uXLi1/ucWlOE8k5Pdts6nRce/LU58pZpsHYOGObrMZei6SOyQgkk/Cj/wBjnP4X9ObnPVzjSql+50X9EHKb2Meq85aTgmpt8nU9XHR6KeaTqlscb7p6pPqOuk2/Uk9l/U2j8QeuvJllo8E/lWzo0NR+dV80mevS8UnmseXk3fC6XE9Rljjit3sdY7I6Hi0ekjnnC8jV7mt9idvvNlWqzQ2W6Om4IRhBQS9KSJ1fN41s4uPd3pnB1S4Mm0uDFNcFrc5N3but2fQ2qCBDHa6hQpChQ8C8oV4AsbBWmV2RsWSAyLZlbJuwLZLKgwImWyeoJpgXd+CblvfYb+QH3CewapWSwLIiD+pUAAFbAG0QrFAS97KRhcgZJryGvZkSQ4YB3ySypuiNu+C/AeNwi+NyJ7DYoF+AQVBkJ5ApG0HYoCgDkB9iNPwZUHwBjbRfBGGkXQLdF8CwiAAAIuSsJgCUXf3G4AeSNOiiTAwAAIAAKAADMvJB5LtNp5K26CDIbOQmwRcl2bVhAMhsZjtZWTgLGSI92RtiJYDUakmc178xKOtbS9zpk0jQvxBxJv1Hhzzcb3R3WUaZCSSSZ9GowwhiWSNWfHGtnZ+jnLIvh7s5Fx8vp8cpMI/NelO35Z6nb+HHl10VOvTZ8b6flWD1yi/TyNPllhfqg6kmZTHXy8sspnLI650/FDHgisSpJH3KkuK2NN7U68syjhzSVrY25ZIuF/4a5OnxZTtj57qeGzJ8fVdJg1WnksiVVyzlfXNPDTdQlHG7jb4N07t658CEsOB7vbY0DPly5MjyydybNXqMpbqOn0OGUkt+H5L1N2rRs3Z2iwZs6lkqUlwma68WZJTmmkz6+nazJoMkcsZP7Hhx+Lut3nsuOsXX9LGGLGlGNUj9rclutjw+3Oqw1+njbXqPV1eohp8Tm5JRSOpx8k7dPnOTiy7nydahpnp5PNSVeTlfWY4P42XwHSTPe7r69LVzeHBKop70au4Tm3OLts0efKZZeHX6LiuGO6bRVzi2j7JYsX8NFx2bR+E8OXFBSzRfpZjOSaUE3X3NTLHV8unjlMvCLhrk3LsHEpRc/N/9zTIppNI6D2Hha0ql5e579PPLT6/KTBt8UvSi0RXVFa+Wjr4zUfMWzdA7JZGy/p5slZGEy8iLNMVVkyQjNNNFS3MrSe4s3NMplq7jUu5e2/4pSyYI1JGhdQ0Oo0WVxywf3O0tKmzzOodK02thJZccd/Jq8nBLHQ6frLjZuuPwtu3v9DNtp7G5dX7QlBylpt0a1rOk6vTzblB0jQ5Omsdbi63HL5fhDUZMfD4P2y6ycsXplvZ8bc0/TKNFSXL4NbLi025lL5gk5S9bZ++mzejJ6vCPycOGuBuou/JOzf6e3dNPQXUmr9KPwnrcs26Z8fzXSMmnHbyY+nJ+nlZJ5Z5ZzlvJn4OTUq5ZZLJJqKi2z0un9F1Wq9LUHue2HDu/Dzy58MI8+OHJOaUE5WbP2525mzOOTJFqJsHQ+3cWnjGeaNy+pseLHDFBRgqS9jf4un1+nI6nrrfEr8NBo8OkxKEFTo+tKlXuVJOr5RWrTb/ob+HHI5Wedz81i6/Y0v8AEDuBaXBLS4nUntaNp6vqYaLp2TNOVOKbOKdc6lLX6zJN77ujodJxd9afLyajz8kpznL1tycndn66fDPO1gxQcpP2PmXq9cccU3KTOmdhdurHjjq88bk1aTOlyck4ppp443Ov07O7Ux4cUc2ox3J77o3jBhx4oKGKKjXsZQjGMEkqSMlSb+pyOXn7r8t3j4pBe92zGvqZLjcitI1ra9fgS23IqsrLs+RvbJHV/YN2WlZHujFNLfuRhb7sviiyqlOhRU1QM5deUslGlKNNHyanp+mzRl8TFFpn1L9X0LLd7mU5bP2lwlad1ns7S6uMpYYKEjTOsdm63R28cXkivbc7Em4vjYxnjjODUkmn7mzx9VZXllwSv59y6WeKTjl+SS8MjcYuN+fKO09V7a6froNywqMn5RoXXey9Tp5Slpk5RXF7m9x9VLPLXy4dNQ+NlhnTxJx+qPf6P3LrOnzj68znFeLPI1Gg1ejk/iwa9z5vXGDv03b8nv2YZzbytuNdd7e7t0utgo5JqMvqzaMOaGWCljkpfY/n9Z5wyRlin6H9DYuh906vQ5IrJkcomvydJP09cefxqtk/FDXN4o6aM934/qc5xx8en5vc9ju/q/5tqYZce1J8fc+PoWnnq9fhhdr1Kz14+O8eLyyy3XWuydJHTdExOXMlf+x+PfHWY9O6dNY5fO1VeT08ubB0zpMXkpKGNUvrRyDu7qsuodQlNSbg3xexrY4XPPde9ymOHh5efU5M+eUp25Sd2z2+1ejZeoa2KSbimrZ42i08tVrIYYJtya/odk7S6PDp2gjKS+dq7Pfn5JhNRhx4d929Tpujx6PTRxQS2Ss+xJv9KJV8IjnGCcpzUUjkZ92dbs1jGTS5exK9tzyNf3F03SX68yk19TWOsd+4oprSL+uzPTHpcq87yyfLfo3TXpYafL2bORw726g9Sp+v5W+De+0+4fzWDjOnJIufSXCJjzS1sQJasN7mnZpsX42riRIt0RuxtDyXlERaIIqMvBANib8FQZG2BatAJvglgUMiKBHbC53I2wmBWVb8kYQFvwVGO1lVsDLbyYyi/BU/BW2BgvqUE4AqCCCe4BcE3LJqrIpfQuxWnZKot7k9TvYaBclfBi+TJEERWGSvcC2RiipbgEZGLCAyI7KAMQlaG/kcF2I1QRbTZaRBAw9uABEWvqABHvsVIn2Km6AVuSfCK3uSW4GPgAAgAAoAAMwXwQIeQ2i+CJK9y7AV5FVuhRCjZVZGPABkl7h2iMER7mUV7ESVmV1sZfLL5PLs0r8Q8beO0jdLNZ75x+rROXsjx5vONbPTXWccwaappeT2+1enLV6tevfc8ebdbe5tPYr/AONirOZhjvJ9By5WcXht2o6LgyaB4YwSkonN+t6DJodVKHpfp5s7Eq4rekeD3D0nHrNPN+lerwzdz4JcduVwdVZnquZ6PNLFkWSD9NM2eXc0odM9Hq+eqNY1umnpNS8TdJM/Kai0neyZo91w8bdicWPLJX66jPkzzllyScrex93ROmZuoZ4/K/Sn7H59I0MtbqIwW8bOl9G6fj0eCKjBKVbs9OPC53bW6nm9GajzNb29iloFjUfnUeaNA6jpMuh1MsWVNxvZnZnTW6V0a93T0fFrNNKailJLk2OThkjR6fq7cvLQejdTlodTGUZv0o9Pr/ceTVQjjxOk1ua9qdPLT55Y5eGYu3Gl4Zp3O4+HWx4Mc9ZVXvbu2zY+1OlT1OSM8sfl53R83bfSv4zPFyVxTOldO0eLS44whBKlyevDx993Wt1vNOKduLxutdCw5tBKEIpNLZnNdXhlpNVPFJXT5Oz635dNNrwjk/XZLJ1PKmvJl1GEn6YdDzXK+XxxaaivLOmdnY/R0+LS8HN9JBS1GOPvI6r2/jWPRxitvlRj0s8r/J5eNPSVoytsj+hU1W504+f/AGxBXQstYiK+BZGxBVa3FjwSvYbU2oOKaQirYezJJ5WU9O1UfJqdDps6anBbn2fUjpLekvcenMv0szuN+Wua3tbR5U3BUzxdV2fNpvE+Gb368UtlNWKUVaexhl0ktbOPW54/tzp9qapM/LJ2zrHL01sbx1DrWg0KayZF6j8NJ3B07UqlkimyXov/AB6f8jnL8tQx9p6pO+T7NL2hlnO8j2N4wOGSHrxyUov2P1SSVmN6WY/pb/IZ2fLXtF21pMVeuKk0exptJg06ShBV9j61XFCVexnjxyfprXnzy+aiSa2RUtgqQvwekmnjbbUreivlJeBwrXJhOSgpTfhWZTzZpjcvFaF+K/VZYNNDSY5U5umc3xY7Vrd8s2D8QtatZ1mk7UGeBCMlNRjzI7fSY9s253Ld3T3uyumLqHU/VOPqUWdj0mCGDBHHBVS4NV/DzpcdN09aiUfnkrNubbftZo9XyW2+WxwYam2XgjaWxW9yOvUaGo2vgvbYqWxFxZXsthtNjT8kcWkFJ2ZWmirWKT8lrYBmKJww92V2RA//AAAUnYk2zIiO7MuERCXuJPKrSSMWrexl4JTQ/ayiiv6mMofEVSimjK96Yb3ottnwx1HkdU6FotdjaljSkzQe4+ys2FyyaaPqit6OqNq6MckYyVNWjY4uouP7eOfFK4BqNJPSzccsGpL6H5Upqmdm6323o9fCX92lJ+aOc9w9q6nQylPCnKJ1OHqZlrdaufFY1lNxk4RZ6/bOshotfDLlfypnl/AcVKM0/Wgn6cTTXzG9/XPHUa88Xy3TvTub8wxQw6V/L6Un+xp0MM8uRelW2y4HFxcG/mZ6XQJYcWaWXO1Udzx9Lsnwy7t+G49g9uxx/wDGamCt7qzc9X1PRaKH95kiklwc21XeeT4LwaX5Yra0a7reqavWyl8XK6Zq5dPeS+XvjyTGOi9U740kFKGmfql9DUeod263USlFZHFM1iclC0v1PyY4sWWUr3lZ6YdNMZuscuW1+2v1OXO3N5HKT+p8qfqh6ZWmelpei6/UZoyhjfpZsWi7I1WocZZFS8np6uGDDtyrVNPjyT+XGnLbbY6b+GnTc+HFLUZYuKkeh0jtDSaWEXOKlJGzabBj0+JYsUVGKNLqOqmXiNji4rLt+i3k2XwTcLc5Nvluy6mhArJ5MUqoJkAGaVkYL4AxYvYPkl7jYqd8lryFSVj1WAAAFdE5AAUT7Bl8bAKfKFu6C2DTLTSpMbonBbtbkEuwVr2IBNrDD5FgX7BNexE2XegDoiaL9wAAAEZSJOxQBu2HshQasCoJ+CUkgBmLSRFwHwAe72I7I3QsBRUnZii2BfSHsSwA5ZSIoAWGRWgLVoxMiMDDyUMAgAAoAAMvJRWxEIlUEsvgshovYckSK0NKWLIVJMaTQ2hZaQklRBjaHLMklRKtllWfKOqPF7txqfTZ/Y9lp1ued1+Cn06a+hhnN41scF/vHIZpRnKL8M9ntLLPH1KPp4tHla2v4qca4Z9vb2R4uow+6OZLrN9BlO7idbjJSinfKR5HX+q4dFgkvUnKtj8+s9Wx6PQL5qk47HOOq9Ry63UScpOr2Nrk59TTm8HTXLK2sOoZ5a3UyzPbez5WpxdNOrPW6F0vNrssaXy2bF1ft5R6f6oR+ZI1bx93l08ebHh8NZ6Dr5aTUxf+GzqPSNbj1WnjKO7rc5BkjPDkljkqaZ7nbXW8mjzLHOdxZlxcnp3Tx6ji9ad0dRckuf3NY7u6zj0uGWLHK5P2Mup9fxY9BeOS9TRz/qOqlq5yyTbbs2M+bcaXT9Le7dfjmzSzTlkbttn5L1JbqrZ6fQelZNbnXNeTZuq9sRWiUscfmS3NW8Xddup7jHj/AKvD7Z6r/B6lRk6i2dM0WqhnwxnjakmjjWqwZdNnantTNg7Y69k0mRYs07i9kenHn6fhq9TwzmndG/8AWcvwdDlknzE5Bq8ssmtnlvmR0zrGqhqOjzlGV3E5e005Pn5i8+e4dDxavl93TU567Ckv8SOs9MjWkh70jl/bEFl6niTXDR1bTxUcaS9jLpY8v5LLVfqiqgltuFub8ji73U2XJUkWlW5BpjoIy7klwNGhhexPIGlW6fuVq9ycLcsX7+xZ5qafJ1HXYdHgllzS9KSOddwd758mWWHSbRXlH0fiX1SXxXpoNpHPUpSncd2dPpunmXmtTm5dXUbBj7p6ljmpSyN/Sz29N3tlejlDJtJrk0bLCcmuU0fhJZYzfLRvTpMLXheXLT6+p9Q1Ot1Mp5MsvS3tufPhy6nHUsOWTV+5+ulwrUKo/qMMkHhyywJ06PScGEjznJlf26P+H3cOTJJaXUS+ibOgRltfhnA+j6nNpdbicJO/Urf9TuPSM61HT8WS7bijl9VxSVu8Gdr7FJpUW20VKnuXyc6+K2rUoi2KKJaSo/3s+HruR4enZJJ70fbW54femZYekZG3TpntxTeUY5+JXGeqznl6hkzN3cn/ALn6dOTn1HDF8Wl/qfFllN5W27Tm/wDc/fS5/g6iE/Kkn/qd7ix1g5uV/s7x0bGsPTsONLZQR9ittHi9oa/+N6XBveSSPcVVXk4nUz+1dDhvgZHEq3D9jW29LTgEsCoUkXlGLsDZV4QTojA0MmyIcsjW5V0OgZJbBkl8pUXI+xfsYy2RfJvwOait3X3JDJGbbhJSNK7/AOvT0CWLDKpS9j4fw/67qNTrHhzzcnfk2ceDeO3neTzp0XxZbMU2/sZM8MsdV6SsWXaiAxsZzzFUfofjqdLhzwcMsE0/c/Z34QUne62Msc7jfDC4y/LQe6e0YtyzaaO+7pGga7QZtNKUcsGmd7moztNbHg9e7ewa/FJwglNo6PB1Vny1uThn6cUWKSl8S2q4M5QyLG229+T2er9Ly9MzSxZ4/Km6Z4ssjUmpbp8HUw5pnPLSyw1WOJKLj6Vdn7w0eq1OT04cbZhpqhki2trOo9kPpmbTRXw4/E88GHLn2zwYzdan0fszWatqWeLjF+5uPR+zNLpUnmXrr3NthihFL0qkfouN+Dl8vWZN3Dhj4tJ07SYEljxJJfQ+xQjGvSqKnapcF+hp5cuWX7bGOEgvajFqnaMl9CM8t39rrQuQuQi+SrpGYozoxMUCpWKKBHyXwRkLsXkUI8lII0EG7CAboqFAA/oAAD4JuJcgC1vuL+gF0jJVt+RZi3ZQi2Tllf1HDMRBS5sPkUAsInkoBoIXewYAFQQBEfJXwYt2XYrJYZCDJP3HqXsS6QSsDJsjHAdgNg+CcMvKAxBQgCLRBTAqWw5C4IBWLMTJALdkZSPiwMQACAACgAAzI+TJ8GLCKuAmHwRcliqhsKDTRdpsFbEocMbXav6FXBCWBQxYBB7o+TqOP16Scfoz6/G5+OquWKSXlGFnivTjt7o491TG4dTyx9mz8tJmlg1Cm1wz0+7NJkw6+WRJq2ePBuvm3bOVzY2ZbfT9NZcPNfX1PqOXXSXqb9K8GfSOk5tdnilF+m+T6eidIya3Kvlai3ydE6L0rFosKSirR68fFc/Na/VdRjxy9r8+hdLhocUUknKuT1smOM8fokk0zOCS4LNKtjenFqacTPmtrn3eXQXCcs+CP12NOnHJCVPaSZ2rWaeOpwuEkqaOd909Ey6XPLJjjcW72NPm4L8up0fVSf1ya7LLnlFQlJtH6aLSZtVnjjinVjDp8+XIo+l3fg3ztTpCw445MkblV7o8OPjy35bXU8+OGP8AV9/bXTFo8EW181HtzxuUfm3TJFJUuKP0VtHUwwknlweTkmV207vDoMcyllwQ352NBz4MuHLKE/laO2ZYRyJqSuzT+6u3vjRlnwR3W+xrdRx/uNzo+q1dZfDVdL1XLHRSwN2qo8yM020/LP1yaaeGUozXpaPyWP1Spcs0bjlZ5dzjvHfMbF2ZgU9epremdNxKoLwzSOxNDKDWWSaN4VSWx0enx1i4PXckyz8KnsWlVkaJHg2teHNnwrGwKkgJVuytEumV+42J6fIaXA8hEqFOSMJJ+iX2ZnJtLYS3hT5Zlh8r+nF+/wCT/N5qT3tngwyLDDdep8m4/ib0yWLVvVJWmaPHdNybO50dmnM5pq7b70npej1vQZaj0r4ii/uaVmccetyYlG0rW57PanWJ6TK9Nk3xy2Pq6n0HU59Y9Tpcfqx5N3R7XPsytY/lNR5vaWn+N1NLw3wY9zaXHp+s5Ke/pRvHaHbj0OKWqzxqSW1+DRu6c3xOvZ738f6mGPLMstQvHccdvlSUXjnFbtnZ+z1L8lwt/wCU4rpsierhHlJo7j2zFro2BrZelGv1u9Pbp5p6d34H2DaqmguDjWVvX4HuSgnZlwLPsjGPJqH4mtx6RL0+U/8AY293dmnfiW76Y0vZ/wCxscP5Rhy/i5FBtbz5TdB+ptVtZlki/UnWyZlkcZJJbM+i45vBy87qt4/DjqmTBn/hsmSot7HUYSi91w/JwPpOb+G1ePOptOL3OydsdShrtFF3cktzl9XxWXbb4M3srgq4Ja8F8HKs1W5KxKhRfBLfChHyOPAZE0VaDjXkeKD3WxdmiFcmT3ZgXwQZOr2ZDFt0VXexktn7Fa44MMk4xXqnJJfU/PW6iGkxSyZJJRSvc5X3z3xNSlp9HPi02mbXB09zu3lnySR+f4l5cM+qRnDKm14v6nzdhajFDq6ySyqO6u2aBr+oanV5nkyZG5fUx0+o1GGSyY8rUvodnHpp2tDLPy/pPqPW9JotMsksikmvDNWffkf4z0en5W9mctxdc12shHBlySkltRsPb3QtbrtTCcYP0Npt0a/J0+OM29cOTbsvStZDXaRZo+UfWl7nxdE0a0WihhXhbn2qvByOTUt03Mb4FyOEFyR8mEj08Kl5DbSpclS2vkkvGw3qmpXkdwdF0vU8EllglOtmco7n6Dn6Znk5RcoXs0dtfzcqqPg6v03T9QwSxZIKTfDo2eDn1Wvy8W/hwhySx3R9PR+qZ9BqY5cU36U+D1u6e38/Ts83HG5Yr8GvwjGnGqZ2sM8eTFo5S412btPuDB1LSxjOVZUtzYYWovfZnBeidVzdO1cZRuMUzrva3XcHU9NG5pyXg5/U9NqbjZ4ub9PetJ0he9kSTla4De9UczzK297+GSojCGxLF+DkqDaBNftNKkiUExY1VEGEOREiSsistIhdU8rRXwSyGJ5Ety17EW5fJfk2MW0qD9ij/wDRG2WPG4JaIrJqxSIG2gkS96DH1L9GXYqaollXBGiit7EYBiCdFbIAIyp/1AAeSvghVwBLKmgyNbA+B8hjwFwBHyQyaIkAoqTFhPcDJxaMWWUmTflgR/UqI2icAZERCoCgloq4AqSogbJ5AtBkdmX2Ax8hui07IzIYPcpXSZDEgBQYUAAGdi1QQ+oRKKuQALZGybimBUTzsGtqCQFJYT3oPZgLRXJJcEfIqwsuj1WiuKrj7hJBuuPJaedvK6t0bTdQT9UakeJi7Owxz+pu4m4J+B6duTzvFMq2Meozxmtvi0HT8GjgoYoLbzR9GXLjwQlkyP0pH6NOvY1b8Q8ufF0qSxz9LfsenHxSXUePJy2zdftq+7+m4Mixye91Z63SupYOoYXPE/VscF1OeUoR+JJykpG+/hfq8i1LxOTcWlSOhl02sNtTDl/t5dKim27VH5anTYs8HGeOMvufpvdsq4dGhlJfFbUzs8x5eLo2lx5PVGEbPRxY4wSSpJeDJLxtuVx8GExkZ5cty8Wq0gvYqvikTzZlvbys/wDRq9nwYuMZRlFq4vwZc+R44JZL4WWzy1/qvbem1zc4pRZ52m7PjizKUnaRuN77USjyvFK2sOozk1t82i0mPS4lGC45PpUVzHyHsqYTUaXg9cZqaa+eVyu6tPyCuSb2IzJhEq+R9g9wuTEVNWV+6I/3J9QD5svqMSoCtth1X2IyVaL8K8ruTpuPqOgyY5xuVOjjPU9FLp+qyY80ZRVujvbXlqzUu+O24dS0ssuKHzpXsdDpebtuq1ufi3NuSYbp5Mbdp2jfOwO5IwktJrKaeys0XLgzaPPPBlTg02qZjinkwZ45Ytqt7OrljOXHw0sb2V3/AFDWXQzUF8sltRxDuPDJdZzJtX6n/ubt2Z3R/E4lpNTKtqTZpfd+RLr+aFX5TXtZr8PFZm9cs5lNPgw/DWtxqFuVo7h27nhj6JheWSilE4Tim4ZY5KqSdmw6nujVy0UNNjuMUqtHr1PDc4w489V1bUdf6fgdTzxf9S6fr/Tc0vRHNC39ThWbU6nLJtzlK/qZYNTnxSuOSUZL6mpeiutvf139CY8kZx9WOakmZNvho5J2h3XqcOpjgz5HKLdWzq2l1MNTgjmg000aXN09xrY485X7I1D8TcXr6TKqWzNvb2+prnfuCWbpEqd7M8+HxlF5Z4cZ+aMGnuhpYKdprd+S5cUlkcZS2TZ9vQ8C1Gtenuk9kz6Ljy1jtzMpuvlcW/7uG0vLNm7O61LperhhzZPlb9zx+tdK1XT9VKMl8re0jz5X6l6m3JcGHJJnDC3Gv6A0epxarDGeJppq7R9F777o5P2R3Tk0WSOn1Mv7tuk2dO0Wqx6rCsmKSlF7nI5+nstrocfLLp9Lt+SJuwmhfu6NOTXitjxWXAVGK9X9DJLayaqaG0DG9+DJ0TSaRrYi4MqtErYaVHuip0twtjHL6nCSS8GeE3lDK+K5r+LPX5afA9Jhk/U7To5C5TcpSlcpS5Nw/FKeRdZanvuadHMl6lKO/iz6DpOOac7lt2mVRVWrvkwTfrTjGl9TOcX6k+bJ6vXNenauTfk0179vp08/RP4sLU148HYPw/7j0uHpkFqvTGSXJxZZfS5RSpe57HSsuf4ajFy9L9jV6jCWM8Lp3DJ3h02L9MZtt/U9DpXW9Lr2ownUjiOTFlqMo+p1vSNo7Cw9Qy9QjNKUYJ+Tk8vDjI28MrfDrd77FRjBNY4p8pFp+DRymq2sfMWWyMU3wytN+SLk8/gkXZoLmq/qW3ewdpboTxVvl8fU9Dg12nliywUrXJyfu7t3L07O54YNwbvZHY3X+FbHxdU6fi12CWHJFW1s2b3B1Hb4rW5eLbgeXHcl6m/sen0Dqc+ma2Msc2ot7pn2d09Fy9O18rj8jfJ4Uljhbe6OtOTHlx00+24V3ToHVcOv00ZQmnKj06vd7HEe1euZen62Kcm8V/0OvdO6vpNZo1mWWKpb2c3qensvht8fLNR6DbukNn9Twuodz9O0jp5oyZ4up780WJv4bTf9DXx6bLKPW80jd2n7McP7HOc/4hbfJD/Y+LL33qZqXoTRnOkz+mHrz7dUdPYU1zscg/tz1FukmmiZO/Oow5Tf/wDPuZzo7T159uwbtcE+W99jlvT/AMRMyS+Njf8Aoevg/EHSSaWRKLf2ML0mUJzS/tvkfuHSdGs6Lu7puopfFjFv6nuaXqOj1EU4Zou/qeWXT5T9M5yS/t9LastEVN2Xl0keVws+WeOcpSocBp0Y+ow0u2S2ZHJ+BexCqyjug0hGw99zFP2LbkNoJ+CtbBUMW9ypBhEt0ZLcEXOwFY80KI+C/wDgqXkfQJjkgBfUjVBK3QFZU0Rx92WmFG0Tkq9iPYIEXJa2I0/AGTIRtp0EBQopEsvqArI7YdeB9WBEhww2VLyBiOTIMCMIIqSAUFsHdkYF55Lfgxq1aLv5AMxKyGQUG2HwQlIWACKAADK2VFoqQRiA+QwHkMeCMArZSIMCsfciL5Aj5IWmFSLs+VjsHuGRMbE38GSbe5FyV7Ib0uzhmo/iTt0qV7WbanezNR/E1Sl0eVPhf+T34Pyjz5Phx+T33+bezfPwthfUXJeKNEhUIr1Ldo378KpX1GSh7Ln7nZ5f82jj+TqLqlfkxXIJwtjhZ/NdDGeFdFT23MaMlwYSM9eFbsl7gNLkmmOigRNocsQ0NUFzZW1VBU2WrvR9ieS7+CN+CE8iKyIpkXwjHkMhNDJojVFRHY0hRUkS3Q38EEboq9mKJRdC+ncjSap/1Lv4PP65roaDRZM0mrUdj24pbl4TkskaX+IXSdC5y1HqjGa32OczkpTcLqKPV7h6vm6jmlKM/lt7WeK1atvfyfQdNLjPLlcl8+H7YM2TBk9eKTjXk/TU5Jat/Fk/VNbX5PwWJtUnsyfEeKVLejZ7Z8vO2soSrZx3ZnKcaqvmMPjYZL1S2d8H1dNwR1OeKStJnny5duNenFj3ZPz0Olz5s/8AdxdMy1uj1Gnyf3sKXubz0zQ48OOMlFKS8nzd44Y5tEkopSS5OfOrlva6F6PU20rCkn606a3Oqfh71ZZtJHBKXqa2OWRxvEnFuzbfwzm4dR9Pq2fg9Oom8NtXG3DPTrTklslszzu4cby9Myx5+VnoNWr8H5a2HxNNOPNo4+PjJv67sfLg2tjGGtnBy39T/wB2ft0PULTdThKruSPy7j0+TT9fzKWyu1+7Pl0zlDPHJ7M7fFd8bmZzWTrvWOi4et9Gjkx7TcL2OXdR6Tqen6qUM0W4p7M632Nq/wCK6NB38yikfR1voem6hilGcEpv/EaXr3DLTY9KZTw4tmnKMIxi79mke1253TrOl5I48jcsf1Zev9u6vpuaTjjcoeGjX3jUZP1v5vrybmNx5ZqvG43B2Xo3dWj1ySnJRkz3ceXDkV4sikcAwZp4MtY5yT8UeppO5Oo6OfpU3JfU8OXopfh6Yc1nh271OvZmXq3V8nIP7cdRTjGTuudzcu0u6PzPJHDNfNRqZ9NcI9sefdbam290Ux9W/GxkmmaGUsrZllmwxdtMybt7E55Ikg90R8P6gqZlLq7Wzw5V+L/QpSw/xmOLclu6OR+mbavxsz+puq9Ow6/TSw54qUWq3OM949j6nTamU9Fj9UW26R1+k6iSeWly8dvw0nA4t09z8skU8ja4R92fpHUtMmsmmkmvo/8AwfR0bt7qPUcnphhlGN03TOneox1vbX9K7fBpMD1Uo4cULlKVbI7N2V2do4dOhk1eL1Sas/HsrsTFoZx1GrinJbqzoUMahBQSqK2Ryup6rz4bHHw6eTh7d6XBprAtvfc9HS6HTaZVhxxivokfQqW6ItuDn5c1rbnHIqXsVNp0E/fkq53PG21lLpH9iblbsDym0T3Kycso2bE9qZFdtMPcbou9LuWPK7h6Tg6jpZY8kE5VszkPcPQ8nT88oyi3jvk7nFXfqezPF7j6Ni6jpJx9K9VbM2+n5+2vHl45Y4W0ozu36UfXh6pqsONwx5JQg/Fn1db6XPQZ5YpppLg8rJalFNVFHb48pyTzHPylxr6Z5VmpzyScvq2fhqlL1qnsfTgwxyyXzJHq4ujucE3Tvg8ebkx4JvSY5XLw8G/Skkrpo+mFtNNcnsLoi9XzbH04uk4ow3k2zn3+Vw0z7K1jKpqba2R+XwU2pOVpm2vpOGm2nX2Pwl0TDVqTMJ/K4SpeKtb+BFNSb28H6OEU17nt5eieqvS6SPwz9FzJfK7o98f5Piy/ZMMo8r4koS+W19mfZo+o6vA1KGeUWvds/Geh1OKW8HR+c1JOnBpr6Gzhy8XJPlN5RufRO+dZpUo6l+qK2bN56P3Foup44uOVRk/BwhZHHK038rPr0uo1ODJGenyONb80XPpsc54ZY8tlf0OpJxTTtPgJe/Jz3szu95lHSa2dSv0qTN/xZI5MUZwmpRf1OVzdPePbd4+SXwz2steSJrx4FpmrY9vKordksWT/AMBWHaQTVBu9kBFyHyWhQAR2ARaH1JS8l+wJAocBcloAxZGHQB3di37BN1wVP6ASxyGEwL43JwHZKZYLVhc0I7CyBYobMm4BFIr8FoCUVDfyNwAJbLYCiblI+QKHxZNy2AQYbQYEohbIAfBCsgUAAAAAZ37j1IjZAisq4IuBugDA2fJUASBWqIwDMbaZf6jyATYZeES97LAYQ8gh8qluR2Tgq5ssm1kOEan+Jba6RL2o21t2af8AifOX5M6Pfg/KMeWeHJo428Pqkbt+FSrqEml7f7mkPJF4IRT38m8/hbKS13pS9jscv+bnYfk6hKLTpl8Dl/UP2OHl810sfhiWyPYqaow0yqoMlewv3Kh5oULRbSJUPSXgjlY5IBPJfAEIJeQAZF8owuSjbwYiUwzJMjAlD6FAEoteAyNvwBHaVHP/AMTtfLHCOD1bS2/0OgPfl7nK/wAVW3rMcfr/ANje6OTu8vDm+GlRxpN19z6OmdPzazP+l+lM/HBB+tO/O6N/6PiwYumqcIpza3Oxy8kwx8NTi4+/PVeFrujY3pk8P6kaxnwzw6hwnFrxudDVerjzufP1fo2LWY3lxpetLwaHH11ueq6efRTs3I0CeFQlbXJ73acfVmbUbo/HU9K1cpvHHE215o9ntnQajSRl8WNNnv1PPLh8tfpeCzP4e/FuSW1Ued3ZkjHQqL2bR6GPLWRRkqSNb7x1cck1CMlS5RyeDG5cm3V6rKY4aay5tN7epG1fhonPqidVuaoptNtK0b7+FWlllzSzeikmdrqLMeNwMbbm6g1VLamRppU9ytW/sPr7bnDt8ujPEcj/ABT0UsHUYZ4RpTfP9DU1L5EvKR1b8TenPUdLWaCuUN7OSt0/Tw1szs9JnLhqufzY6u3Qvwp19qeBy4lsjpUqkr8HC+0NbPp/V4/N8s2dt0GZajSxn4aNTq+PXl7cGW9RNZgxarH6J41JPbc03r/ZODO5ZtPH0y5pG8y2pLgu63qzT4+fLBsZ8crifU+2eo6VtqDkl9DzJ6XUwg45Mck15O9ZcGLIqljUr9zz9Z0LQaiLXwlFv6L/AMG9h1ts8tXLp7+nEHh9MXUXKTNt/DjRan80WZ42oL3Nxj2loYNNRTa33Pb6dodPocfoxY0n7pDk6uZTRhw2V9S2bsRW4XLsrexzM7utyTUX6h7kW+43MfCpvZkqoxbRUVLS21TMJYoZFTin9zNb7lRZlZ8HivP1PSdFmbc8Md/oOndM0ulbWLEo/wBD0Kt7ikk1wZetlr5TsxY0klsX6VsVLYUYXK1ZNHp9mEBZNm6DcPgjGz5UWBQ3s0nkoJZA3vYt+DHgyStF2qf0DT3+pbaEXtvuWXV8JZtqvefQo67STyY4/OldnHddp8+DUy0+WLVOrP6JmlKLTXys0Hv3t+E4S1Wmx2+XR0+m5rNTbU5sPnTmkX6ZxUZVTNn6Nr45cXw5y3XBrGXFU2pfLJM/TSTeGSlbNzq+L1uPw08fF8t3b9VbfL7hNKXufF0/VfHwRSe9H2KvR7s+J6riywtjcxssZ+q1RhP1WkjKHzVXkj22XJo/2Z+B+xVd8cmP3YbaVrgylynwalVqD5SZ8mp0WDNa9CT9z6lFN/Vmahvse/H1HLhZ5Y3GVq/UOiU/XBbcnkarFlxpRaaSZvvp9T9LVr2PL6106ObBJwVNHb6P+UssmVa+XH+41TBlyRzQljfpcXex1LsLuD1wjpdRL5vFnL3hcZOK2lF7n0dO1mp0urhljKqe538pjzYd08phbjY/oVNSqXgLmzyO2OoR6h0zFO/mSVnr2cXlx7a6WGUsViguLJfueVixWtiIWQhVbovgcmJfgZLiwnvQQ2IG9FSJ4LvQNIwGFyAoWuAwAoJ/QIFoWH9CiyURIcMN0TyBXsR8FfBPFALY3DCYCn4FFZLAu5LKGtgJuPuUWBEtwysmwBFAAAEQBkMmYgGQrIWqAAgAADLkJBPYthACxYEY3LS9w+ACDiS97L6gJXuH7i0VgROw0x5KBPqGUPgEYUZIhkixlIr4/oah+JVPpEr9v/Jtzq6NS/Epxj0ad+P/ANmxwflHny/Dj+LGkoyfBvf4Z51+ZemH0NHTvBGXGxuf4UqP5i5Pydjln/W5+F/s6ure4vcvnYlU7OHn+VdLH4R7kL5Hk8lpZCsgRaF/QpPO4D1fQyTtcE2KuC0P6Cl7CyWQBYCQUAeyHgJpa2J4LewXAEC5LtYAj5HCD5I3QEato0P8TenfEwfxEI2477G+0nW58XV9FDW6OeOSu0za6fLty8sOSbjgePJJZN/sbP2x1L0zeDK/ladHmdx9OydO18ouDUbdOjz8OScJxyQfzJnbms8NNGZXjy237PD5U4Lnez88eoyY23wlsfH0Tq2PPFYsrSlR62XR/EwfFg00cTqODLHLcjv9N1OOeMlfjhy03JxVssZuUzD4eS1Fx/Y+zTYvRFOUbs1LyZXxW7jjxybfF1HVR0+GTl7M0fU5oajNklN8t0bJ3c5Y424tRZpyknk2VJs6/Q8U1twuv593Ufvo9PPNqo4ccbt7naezOmfl/ToL01KSs5z2JHSz6lH4zSlex2LA4rHFKvSlsenW5WTTU4JLWdLb3K9kyfqaYkm0ci+W9HxdX061fT82KSu47HDusaT+F6hkxSW6bo77V2m+Uct/EnpXwNU9VGOzfg3+k5NXTV58dxpeKUoSjPhwex13sLqkdX02OGTXqSo468knaqrNr/DvqEtNr44skvlb2Oj1HH3Yba3Fl212JcbhOuUYQmpQi07TSZk90cDkxsro43cg22Vq0GqYtmEtZ+GK+X6mSq7IuQ+S7RZL2Ma2KlRU9tybSokyl8GL2ZC0aIVsUWAisJqh5FAju9jJB8EGKLGxFe5UCo+QHyAArcGQGILRGAoLgvgxa3APkq4JRbpA0SVGK2Mm0yKhtYmz53Pz1OGGbDLHKNpqj9aSRH9T2489JcZflx3vroGTR6uWoxJqLdmr2pYbX6ju/X+nYupaOcHFeqtjjPV+nT6d1HLhyxqN7HV6bn7/AOtaHLx6u4vR9Q8UouT2RsuPJin6ZKSVo0qWT4L+jZ+7106qM68Hn1f8dOXzHjjyWXTb5ZsMHtNMxnq8MVbkjUIZtTO28jJL+Im2nk/1OdP4f7enqX5bVPqWmj+qR+S6vpXaTNTlGSbjKVkxUp7mU/icZfKXkraZ9ZxRexcHVVOdJbM13KoySSe59GhUrUUmzy5+i48IyxytvltWDOsi+5+r9Mvlfk+PRY5RinLY+v0/NdnCy1jl4r31uNY7g08NNnc8apNHkeu3xs/JtXcmJZdKpVwarlaS+x9T/F8lzx01eTxXTPwx6hi+B/D+rdHQEnexxv8ADbMo9QSXlnZMTbgn7l6zj7a2+DLcVXYZVfkjTqzQs02U8AyWwSREEBt4DasugRaIi3vRApiw9iMAguQyLZgVgjCAtAqe1BlogAIKuCMIrdgYuwuCmIFYXuLCWwFDCAEsMqI3uBAVigLyicBWigAglsRbMCmJkKAIUPIYGL4IV8ECgAAAADJlXAbC4CFEopHfgC00Rcl8E3QFSXkWTkUAsr3WxiX2AcC9huxywFi9i+SbeQCK2TYedgu14NQ/Eip9IyX7f+Tbndmo/iQn+UTX0/8AJscH5R58vmOQp3ijFeEbj+FeRR6qoNmlO4qP2Nv/AA3j/wCrwkvLO1yf5tDD8nYVs9it7GKlcV9jK7VM4Wc810sfhinuXyGimC0e5EUlOzFFryHuBdbARJIyXBjyNwKEqCH3L4FaQRCpogPdEWyoq4I9wK0qItkFuVbcgRBPYLgXSAPgxaMgwIlsE/DRaDSaMpdeYaa33b0LF1HBKUYL11zRyXq/Ts/Ts7xyi6O+ON7eDX+6O3sHU8EqilkS2aN/p+psunhycMvlxvDmcE5R2ke70rr2ow+jHkk5RXJ8XWej6vpmSUcmJyV7Ojzo5PSpJq5NbHU1hy4/+tWZ5cVdO0WqxavEpYknJo9TQaKeVr4kaRyzoHXM/TtXFyfyN+TsXb/UsHUNJDLj9Ntb0cnqOkuF3HQ4+ruc1Xld29ChrOmSjGC9UY2qORavTS0mWWOa9LTrc/oWUfVGXqWz2pnPPxB7c51eGF3u6M+k5phdV4c+Hd5c+6dnemyxzRdSTOs9l9w49dpo48k16kq3ZyHLBQk4bquT6eldQnoM0cmGb2e6Ohy8U5cdxpYZ9mT+gYPZU7Qbbe5rHZ3ceLX6eMJup15NoTt2uGcbk4rhXS48pZtKXpbPC7x0C13TJL0/Mke9JP0WtzDJGM4OEls15MOLPtyXLHcfz3rcbxamWJxpwdF0eeen1OPLF00zbvxC6C9PqZanFH5XvsaZCDqUm+D6HhzmeGq5vJO3J2rs7qcNdoYJzuSVGw3tRxfsTq09B1BYpyfok/c7Hps0c2GOSDtNHL6riuNtbfByP1TbFlSS4BzpWz8+UsPkrI1ZNxlVTpBboNNIeCIURlVlpBGKKR7PYq9y/oTdEMnsREFTaHJWlRAaVEXI4HkaIeQwxdoaANgAEVPciCB8rLglhth7tF0WfpjTsrPzz58eJP1TUSYtRhyL5JpsndHpOO2P08ljyNvctpLctm4x1YjSG1blS5IuBj4LYxStOlWxp34g9Ejq9NLUYofMua+hubuKPyz4VmwzxyVpo9+LPsu3lljLH8+6nG4SlCfKdHywbjKSkvJtvfXR8mh18skcb9DdqjVp+qabca3O9wc3di5vLhrJ+mn/AIjL/Lx7H6/wWsb9SjR6Pbuox36PSr+psajBxb9KOP1vXZcNZYY7adDpGsyu3aPpxdF1CfzG0wjFLbY/OTd0cjL+Wzv7e04nj6bolO5M9LBoMWFLbdn7VJKrMt2jT5etz5PG1nHpnH0+j01wT1b0IxlYcUm2uTS153a9NafJ1mP/AAEn43NKzK5+lPazeOq/P0+UVzRo84+nO7eyZ9R/DXzGryx7/YUlj6rGF+Ttmnb+FF/Q4d2Ykutx32s7hpXemh9jo/yEt8vXp/l+q5MmtiLgqe1HJy8t5ABdEiCe+4Je5fAFSVBcBEtMAC2RsARlW5a+oGLIZSVGIGSDCewAFohU9gDRELJ6twD5DD4sq3AngINBX4AMIPkq4Aj5HLHIfIFC4DJvQFIyFQF8GK5oybRE0AfARRQAjKmkRtgR8EKQKAAAAAKVclaZEEUPgADG37GS4BHsAYsqDSVATllJwxe4F4HjYMN7ATkUVIMCNBJoU2PoWEVs1P8AEdqPR5t+3/k2tpt2aj+Jqvo0vqv/ACbHB+TDk+HIFBzUX4Nq/DlNddxrhWjVdPOsaTfCNq/DjL8Tr+KKVUztck/62hh+TscUqQaocJWL3o4PJ810sfhb2IuSsiVHnVqr2RWTgXexEAGSmBSJ7l3WwAeCWUmwEf0KgwlYFLaMWmVAFsG9h5IwKv0kRfATAj52I21sXyHyWC26IvqER7MaVaC5tojsygvJZbL4S/Dz+r9L03UcMoZIK35o5P3V27PpesllSfwn5OzK7Z5fcvTMfVOmzxTirSdM3un57LJtr8nFvy4T6IK3Pjwbh+HvXI6TUrTZHUXxZrfWNO9FrJaeUPlT5Pmx5VCcJ4m4yTuzq3GZ4tOW4V/QeDLHPjjOLtPguoxQz4ZQnFST2ZpfYXcGPUYI6bPk9MlsbtaaXp3T8nH5OO4ZbjewzmUct757alp8r1Gnx/I95UaYscYt7fMvc/oDXYMWpxPDkgmmqZzXvHtaWCU9RpY1HnY3en6nxqvDl4f203p/Uc2gz+vHJwafB1Ds/urFrcMcWfIlLjc5LlhNZXHJGpL3P10csmDKp48rhJPajY5eKck3HjjyXG6f0NCScE1K4viiy5qrs5v2p3fPE46bWyuPCbOhaXV4NTjjLBkUk1exyubguF+G7x8ss1Xn9z9PWu6bPHS9STaOK9T089NqZ4XGpJtH9ATimnGW6aOa/iN0Vwb1WCFeXSNnp+W7krx5+PfmNBw5XiyRnH9SOq/h911avAsGWXzJHJdk2236k9z1ega/L07W48uOfyuStG9zYTPF4cduN1XeIuuSp+58PSNbDXaKGdNNuO6TPtW6XizhcvHcK6OF3FvcqaoxT34MlVWeMj0qt7EaTREUaRWYsqDSIjEysJRDW+wEYXJaJ5AoSbYIuQL5K0iFoDFk5MqFF2MS17Foj52IbEHfgqDe4JNpwg3UZP2RW7HKa90W/DLHxl5c37q6pqZa+UIycUnR5+i6zqtJli3NuPk27uHt+OolLLiVSe5pWv0c9LleOcXs+TV5LZXY6fHjyx1XQuhdZw6yEVKVSr3Pbu/qjkeh1k9HmjKDaOidA6nDV6aPql81cF4uTd1Xl1PS68z4e0vIaoKpK0wr8s2d+XNs1WPlGVqxLkjW5ZdJrw8DvTpS6h0ybUblFWv9zi+rwS0+eWOdpxdUf0NNRlGnvaqjlH4h9FWl6hLU+moSd7HS6fk1pp82G2o6WTx54zi633Nw0GSOXDFp3tuae8bypwx7P3PW6FqPgP4E5XIw/k+nmfH3SNbjy1fLYXGn8u5i6aKpWqQVVVnxuePbdVty7RbcmV217E4V8lX6fYw1tRyd0FbMf1N09yq4qm9zPsqbj8dbtp53x6TTNRKMssotU7N4mlLG4PdtGm9ZxrBqpemPJ3/4fKzOStflm4/btqfo6riadL1c/wBUd06fJS0eOS4a5P5/0+T+Hy48kH/iV/udt7M1sNX0qCtNpLk73WYWzcODLVe2nsZLcnCtrZeCp7nFy8eHQ+QjKhdmO1AxTFF2iWQyZErIH9SqqI+SoC8oekJlv6gY1QLZjYF8DhBcCW6Av3FETfAe4NmxKVhkQFe+yKtuSJ0VARuwh7hAHyVcE5ZQJQXJWTwBQguBQEYQou4B7BtItsxbsCK2yvbYJOioBEMADHwQLlgtUABAAAH6S5IFzuHzsENyWUlAOQikYFSI3uqKR8gUfYlFWwEfuXwGR8gXeg1sW9h4AiWwcQr8FYJEe6s0/wDE1yXRpVvRt7Vo1P8AEbFfSpb7OP8A5Nnp/wAox5J4ca9SUIyRtP4Ztz6/iS2do1eGKKy+i7S3Np/Dtp9wYvT8tNcf1O1yf5ufh+bs/wAzSUvBa3Cv0xf0DODyfNdLH4NroWR8hJ+x51aFVUKohEX+g9QJvwBURug+SAZAiK3sAZOCoPgC7kXASdF4L8DHyVoL9QfJNiUQrsUBAABkicPYq4pkZdkG2VOluK2sliL8nN1sRq4tPf6FXBapxtGcy15ibaP3525DPp5arBH5t20crlCXxpYpr0+ln9EzxQywljn80Wqo5p372q4ZJazSRpctI6XS9RvxWpzcW/ho+i1mXRauOTFJqnZ1zs3uTF1HTRwzmlNHG2pY87WWO65Pr0HUMuh1Mcmnbj7pG9ycU5MfDWwyuF0/oG74apn5anDizRePJFST23NX7S7nx63DHDqGoz43Ntx1KKcKkn5ONyceXHW9hlMppzru/s5yctTpIvfeqNCz6LPp8rxyi/Unyz+gpxShJSXqT8M1ruHtnTdQxTniioZGv8OxscPVXHUrDPil+HH52qUrUl5PZ7d7l1fTcihJyljXk/HrvQdf06a9UJSinyeZHKoSpx2OlMuPmnlqXeFde6N3fodWo43JKb23PX6ngw9S0csbakpR2rc4Qsrx5lPFal9DYOm93a7RemLk5V7nhydLd7xr1x5tzy+Dubo+TpfUJuaahJtqzy9PGSad2vBtfcncGHrGjXxYJZUvY1OM2/liqivJtcWNxmr5eWV87jd+w+vvT6habPJqL2R1LBOOWEZp3FrY/nzFOWHNGUJ007Or9hddjrNNHS5Z/MlSs0us4P3Hvwcum3vd7INUE7WzCT8vg49mm7LtEqdmSexEFZjSrVbUBbI3uIfKpr2BLDZBWxwN1uFYUCW5FxZVe7RbdJobp7F2fJHdEslNMqH9SXaAhoUfNsNpBb+Q02i6UQa8kXBVuieU+E5ZXwCMsW1HFtcHh9w9Hx6jDLJCPzUe8m+DGcU4te5hlJY9uLluNjjusxz02oeOa4Z6fQNZk0+rinJ+lnod6dP9Gf4qXJr+D1RcXdJGnlLjXdxznLx6dZ0eVZcUZxezR+7PE7VzfF0EU3bR7S8Pk3OO7kcTnw1lYqDsqdBuzPWmvfDG6dJXXueL3f06Ov6Xki43JJtUe07uiTSlFxfk9ePPVYZ47jgGqxz0WeWCXyyto/PSZvRqFPl3uzcvxG6N8DM9VCNJu+DRk1B+53MLObj05nJjcK3jQyjmwRmt0fs/Re3J4HQNdBY/h5ZelI+3UdWwYX8jUj5nrf463LxHrx5/b0JRrl0Y59RgxYm5TSZ4Ot6xlyR/u/J5GfNmyTueRyT8WXg/icrJauXL9Nhz9YwxxuOLdnxrq+XJOovg8iHop29yYlLHl23TZ0/+O4sMf7POZ21uOgy/FgnJ7nl9w6aKlHL6b+x9fSfU4RteD7dThjmg1JJnKnJjwc018PWy2NGytQlcU6fg2fsnrmTp+pjjy5GsbZ4nVtLPBndr5Wz5PlUo1JqvJ9Lw8uPPg1vONf0Lo9Tj1WCOTFK4tWfQrZyTszunJossdNnn6sd0rOpaLWYtZijlwyUk1bRzuo6e43bf4uXfh9SG1kTfnZF439zRsbP/AKOXhEsrXsRISeNoWUjVBEBiygAAhwwAoMlgZPgiew2KqAiAYAj5FBoqssEaoq4I+SkCw9wk6C5AidFTEt3sTjwA8hi/ccsAi8guwGPDL6g0EgCa8ktFAFTsj+gAAMEYEfBCsgUAAAAAZIq4MS0EUBACN7mS+pi+SbgZNoWTlh0AsrdoPfgeAC4oj24CaMnVATwN6QQbbALgnkorYVYipvc1T8SU/wAmn6fb/wAm1rlmp/iTk9HSZPxX/k2uD8ox5PhxyWOUYpp/M1ubL+HV/n+G/dGtublNS8UbF2BOuu4f/sdrk/BzsPzdtTqEWntRLMcXzY19jN8HB5J5ro4fCLdmVIkEVnlWVETkciyIkuQuSkfIFHBE2WmwJ5KiNUFwBQ0+SbsqMgrbkIDclotE4BFuyKtixRKCFkLwtyJNMCsVsPJdvBdBexEXYj4sgWW21XsTwWJksSV+OT8tThhqMLx5VcWj99kRtOO5ZlZZYlm3Le9O2J6eU9Tpobc7GjOE/W1Nelrwf0HqsEM+N45RTi0c87x7Sacs+kju93R1un6rU1Wny8X7jSNJq8mlmpwk01ujeu1e8ZRccWqfyulbOf5cGTBmlHNFprbcRbjBtOn4o2s+PHlm48McrjX9AaTV4NVBSxTUrXhn7VW1VI4j0PuXW9Myxk5ylFeDpXQO6tJ1GEfiSUcrVbnM5emsrcw5Zp7Ou0Gm1uNxzY1KzSO4eylJSlpeHukdAhOE1cZKW12VW040qMePky41ywxzcG6h0jWdNytZcUpVwfCpSeVXCvud81vTNLq0/iY1J/U1rqvZejzXLFH0y+hvcfV/bXy4LPhyjJkue8d2SUn6aiuDbeqdmarG28e6PHn0PqGnclLG2janUY14XjryPlat7M+7o/U8/TtZjy4m6TVn46rRZsMaywcb9z53CMEm3SPW3HkmmMlxrufbHVY9T0UZqS9S2Z7S4bbOM9kdWydO1kVKf922de0mohqdNHLjacWkzidRwXH4b/DyS+K/dfoKuDHaqKaNmmzLv4W2mS9yFXJjfAqe1B8E5YQ+EsV2YuzJt0Rvai7WUbqLCdpWSTUYty2SVs1XrPeGl0GpeNNOnR648dzY55yNs2RE63qzyOgdd03VMacX8x7C442Jnh2/K45So2pMUikTt0ef6XYqKtlSJwHsikWO63C2MXYJUrIxLWxN/YaIyXIk9qSsl0gtlZbGUumud54lLTOTW9Ggyb9XpXFnRO8Y3om/oc6u/V9GanPNV2uhu8W79lZV8D03ZtW7WxpXZDdtG7LhHpxfDS6ySZp5sLkLZ2W1Z7baVHzZHu7RXyQfDG+Xjd2dOXUOlZIpeppNnENbing1s8M1XpbP6IlBTvH4a3OR/iJ0ZaXXSzQVKW51Oh5dXVavUce5uNP+Ioy2dWVzVJt2zKWGLh8y3fBlpNH/ABL9K2p0dTknHfNaEtnhgs6aSrcuSGfJkSwwbR7uk6DjSUpHq4dJhwJemKbOP1X8jhxXUeuPHa1nSdF1ObJGeRuK9j39J0nDignNW0egpJpUqLNepWmcXqf5LPk8StjHjkflCMVtFUkZJKS+pl6VXJKqWxyLy5W7tesk+HydQ0i1WNprdeTVddpZYpOLjwbtJx9Vo+TqOkx5oOlbOr0P8heOyWvDk49tKxKWN7Xa8m29nd0ZtBqo4s824N1ueBrMLwTlGUaPj+G/Une9n1U5MefDbwxtxr+hNDqseq08csJXFq9j6l78o5z+HfXPQlo88/l4Vs6JF3FSi/lfBy+fi7a6HFnuaZ3uLVEv3XBLZrXw9dK9yIWFyYisWRkAyCQV2V7AR/UbBvcUAFkRQBAyAVbclvYxL4LCL5AXAGiqiAECgy7CgISvYvAAPgheByXQMfcjC5IK3sQoQBbBtWFwTyBbMTKvBGBGQrIFAAAAAGS5KKAQJe4ZAKuQ/oQAXyHuE0VMAAwAaS3JzvRQAT8Ankyf6UBjZVbIZLgVYxUW2an+JUU+jyvwv/Jtt7mo/ibX5POvb/ybPT/lGHLfDjkEm1XBsXYUH+fYn9V/3Ndh6lGPpRtPYXqfW8Vryjt8n4Odj+bsuHaEfsZz3ZjBVCP2L5OFyfNdLH4PJfBHyGeTKqgERpmKDZAALZU2RhcgUiorMWBkSwt+SgTl7mS4Iyq6bFIknsIh7EXJZBWCJ7laII6KgzEDJoeCJ2Uy1s0nkyoj4CbolBr2CAGjY7G5bMXdj5WVPdXwTLCOSPpmk0y+SpLkylsLJY07untXFrVLJgioy5ObdX6TqunZGpwdLhneXT3SPM6v0bTdRxNZIK/c3eHqbj4rX5OKVwi7ivVz7GeDV5NNk9eNuLXFG79f7MnhlKeCNxXsjTdXoc+mzuM4NJcnT4+bDOarTy47L4bL0TvPU4IRjmcpLjc37o3cmi1uOPqyqMmuGzi1pN7L0o/XBnyxl6sGRxa9iZ9Phl8Ljy2fLv8Ahy48kfVGaafsfpfscU6Z3V1HSJJyk4r3ZsPTu/m2o5lsaWXS2Xw98eeV0iUItVJWfjk0emyfqxp/0Nf0veXT8ySckr+p6WLr/T8i/mr9zxvDySs/Uwrz+6e3tPq9JJ4oKM0r2RyLrGjy6TUyw5E0k6O4z6zoGvS8sWn9TSe+tJoNVilnwzj6vobvT3OfLw5JL5jQMGVxh8nKN+7A7kazx0eol8r2TbNBSUV6Irf3Liy5cGWM8Wzju3/qbnNxzPF4YZWV/Q0ZRmlKO8X5L6tmvc0zsLuSOu00cOaXzL3Ny5V3sjhc/Dca6HFybjLYLgj2aSLRrWedPa1jLYjM1G1ZikuCfDKKnZXVWyO29tkj5ep6qGm00sknVKzPDDvykeeWWnjd69ah07QyUZJSaqjjmvzPUZZaibv1Ss9fu/q+TqnUZQT/ALtNnj6fD8bLHDj3bZ2eHgmGO60c+Tdbt+F8M2TVepJqCOpXtsjW+xumR0PTIy9NTkjY18qSOd1VlvhtcUutrtV3uY35DRa9zUkte5YZE1e5U29zO4WEylLIC+xhS+S9hYfIfBEHuG/AXIXJd+Fn/rXe9Mvo0jj9Dn8Pnb+5u/e8rwNeDRsbqVrizV5vNdroprHw3bsrC4wtm3P9KRrnZ1PSKS2bRsLukenF8NHrLbmtbh8k4Mlwe1+WpRhEW7Le+w15QWzvyzWO/Oly12glOCuUUbM0nRhqsSzYJ4n5R68WVxyY547j+ftTHJhnKE+U6P16RmeLMr8nqd9dNeg6nLZ+mT2PBxr01O6o7fjk43L5Me3JvOmfrxJqRZJ229zzuh6j4mD0+q2j0E/DXJ8b/IceWGdbPHZYJ7FV3dkgubMrryczdr1V/Kicq/cjlsYKVtIatGcopVYr2MnxuYTe3sjLXafL4eraKOowykl8yNR1MMmPK4N00zfItelp+djW+5dHGL+NBfU7v8Z1dmUxta/Lj4ebo9Vl02rxZYyapq2dt7Q6lHqPS4XJSlFKzh1KSi1wb5+GHUPh6t6Zy2a2PoepwmeHdE4eTV06gmwtuQ6ir9ycuzj5x0JfG1oOqJ52KkeYVsEEW64AcEYAEb2C4EuBuwATYaIAKuSFXIFoLbwRclLAbIg1YSopV8hNcDZbh0Y6Fog38gAwEADCHncy2S3AxYS3D5KnQEkqYEyWwKRc0VbkfIFIxRADIVkCgAAAADNgi5KwiPgIJUtygSgkW/BfAEVFojKuAI+SN7mXgxa8gV8GJVyXbyBPO5W9gnYf6QIuCp1wTwEWLF+Xg1D8S7/Jp0vH/k21rc1X8SV/6NN/T/ybPB+UefL8ONY1kcE6Nq/D31/nWJyXLRrUHKOKL8Gxdh5vT1qDe+6r/U7XJ+DQ4/ydojvFfQy+xhhknji15RlW5weX5ro4/A+Sr3DB5sqXWwI+SrgxSo3YSCKBKIZUWvLAx+wLsS96YBsL3LQf0AO6sJstUiIsCXBF7mSaMWQXYfYiKBHfkheWGBDLYxK0ZGywihk2JZWRFIFkZDNboyIw8FsWkEFGgtluGkWlWw3f0mmE4RmvmSaPG6n27o9Y5NxUWz222lsNmtz0wzuN+Uywlcu632NqMfryaX5o8moZtBqtDklGeGW3mjv7TkmvHk+DV9I0OpT9eJW/NG7xdXZ4rXz4NuEeqbVODj9yQ9CXzbHX9b2boM0JOEUpfajWNd2Hm9T+E7Rv49XhZ5auXDk0eeRRV4puxHV51G1la/qzYtT2Xr8KclFv7Hm5O3tfBtPFL9j0nJx1j2ZR8uHXalrbM/3Z+OXVajK3B5nL6Wz7PyrV4Y0sM239GXT9J1vq9TwS3+j/APBe7jn7NZPhg5Qm/Ox+jyP4UlKNSeyPSw9F6jkyNRwtXwY9V6F1HR445skG4+aMpz4WsPTr4ekazUdO1UcsH8qdtHZe0ut4ep6GNzXrqqOL5oL4UXLlH19D61n6ZqoSxyfptJxPDqOOck3Htx5XG+Xe00nYk3Z5XbnVcPU9FDJFr11uj1WrXJw8+O410MMpWSdEfKox3sTnHHD1Sql5ZhMbayt15YZ8kceJ5JSqK3dnMe/u6XlzS0enl8q2dHp9990QxY5abTS+Z7Ojl8pyz53lk22+bOp0/BPFafLyb8R+qyp26uT5Nv8Aw/6C9Rq46nJF+m7PA7e6Rm13UYRhFuLe/wBDtPQ+m4+m6OOKCXqSPfqeWYY6eXHx23b7sUVjxKMFSSozt1uVJ1RLW5xcst10McfA26+54Xd3WV0nQOS3k0e5OcYq5cI5d+I/UoZ9TLTxlfg9eDjueTHkz7Y+DTd665a31zv0N0dR6Frf4/QRzLykcG0OKU9VHE+XI7j2hg/h+kwi/Y2+o45ji1+LO5V7LpuychX/AKFXBzL4bcPIAJsKrkqpMnLoj2YitW75j/cv2o0NL0zSXDZ0TvLF8TROXsjnUk4OUn7mtyx2+iylw06D2dK9Mor2NkT2Vmjdl9QhF/Dk6s3eMk1F8poz4bNRp9Zhe7bJLcyaXgiafBXye9m2jZ9sUvIryVkbrYynjyi0FxfkqI7Zjv6Gl/iL0uWp0jz44XKO5yfL645HDIqrY/oTXYFqNJPFJXaf+xxHunp09N1XJCvTFt0dXo+TxqtHnx2nQtRHHmUYu02bMn69zStHeHURa9zbdNmUsUbaujnfynTXLzI8+OyPqjsq8hL1Xfg/OefBGLlKSTX1PjfUsPok4y3SPn/a8l+I97nH3NW/oRqEXbkkeBl65Jtxj4PhydQz5JtqTNzi/jOTP5Y3lbVk1WNOvUtjKGbHk2UjU4Z8k07e59+gzTWSKsy5v4+8c3UnJt77Vqj4usYY5NLL3R9cLpSvkw1lLBK/Y1+klw5Yyy8xpsY/Cu/c9PtfUvTdc07g6TaTr7nk6v1zzSV7Jn39uQ9Wuw+rlTVfufbY2Xh8tSeMneNPKU8MJN7NJn6pUvc+fRy/4LCl/lR9LXH1RxeWarp4XcSyp+5PSWmeNZowB4IUQFgA1uA90SmBbJywlsEBaJRSpAT7hN0UjANi/cWLAn9QuS0KAqFEFgAVUHxYVC0vJG9h4CLdeB/QgvYAyN7FJwwKgNkRLcBbD5LW5GBGQrIwoAAAAAyezCZAEVsL3FEAyToE5LVICWVMLgAGxVj7FSYEpUSitEYFSoPgi5KwJ4JF8gRLFio1H8TpNdEn9v8AybamjUvxLkvyWaft/wCTZ4Pyjz5fhyGKl8CFexsHYra6zhSim21f+pr3pl8CPpZs/wCHkV+c4U95Wjtcn4NDj/J2TDSxxpVsjPezGFelbVsZHB5fmujj8I3ToWHyVrY8qv7YlT2IWvJSqCIUSii/BCtEEbSK6q0RclfAEQ3KuAuS6By2CMtvcbJciDDdEMrtkZBSNkAF87i0yF2LD5Emx5sqD+ooX5I3uSn4Kl7kELZa2I2kXRoRXwYmS+pBiVB8kMjQZIi4KqoxtNi4ox82ZMxe5ZFlE2mwuORVmS2W5b/4u0pXYpXwiWmty1aJMrGOokoxkuL+5+U9Lgf/AC4u+T9XF2UznJlP2nbHyPQaW7+DF/0M3otLW2GH7H7+aMk1VUX1Mk7cb+n4Q0unStYYppeD8dZoNPq9NPDlgm2tj7W96oxr5tkXHls/aXDHTivd/Rc/TdbJpN4nuvoa5BKU/Ve6Z3jr/ScPUtHPHOC9TTp/U491vo+XpeplGcXXq2Ot0vNuarT5ePXmPQ7U61m6XqY73jb3SOtdK1uDXaaOfHK7XBwOMsq3ibL2t3Hm6W/Tmk5RfuZ83TzLzGPHy3H5dfz5oYcbyZZemKVmgd5921CWn0cm5e6PG7k7vz6tejE/TB7Gszy+uMpzl6r3PDi6TV3l8PTPmtj8suoyanK55lcubZ+/TNDl1upjDHDdvwYaDBm1moWHDH1Nutjq3ZnbcdDp45tTFOb3Njl5ceKaxeWGFyr6+zuh4+n6aM5xXxHubDv6nXgrcbVbJFTpuvJx+XkvJd7b/HhJBNkq2OZJCUvSn9DyktrPevLze5eoYtB03Jlm/S2mkcU6rq/4rWSzN3ctjbfxO6y8+b+Ewu0uf3NDxv1tKt0djpuKSbrQ5uTu8PZ7Y0WXVdYxOMbimrO26HF8HSwitqijSfw06W1gepyQprg32NtelI1+r5d+Hp0+GvKJ2tyonpoyObbtuUA38DfyRBPcN7htVsG3YlJdPi6vp/j6OcKt0ct6rgyYNXLHONRvY69KNxp+TV+6+jfHxvJhh8y3PHkxtb/Sc3bdVo2m1E9Lk9cHTRunb3cWPJjjDPKpJeTR9RgnhyvHldNGDcoNPHJpr2NaZXC6djPDDmjsOn1GLND1QknZ+ylf1OYdH6zqNG16pNxRufSOu6fU40nJRk/DNnHncrqOis8x7tPyF7cGGLJGatPfwZx95bntMpZ4aNlx8UQpIc7INOizx4SeYt2rZzf8SdC1l/iVHbydFbdUuTxO7dGtX0ua9NtJmz0+dxyeHLjuOKZJxb9S+Vr2Li1+eLcVKSRNdgyYcuTGlVNny404z+Z7s7nZjy4brm5Syv3eTPl9TeZ17WXFkafo/dn76bp+fMvki/Sz0sHQsnpTk6T5ObycvDxX4Mccq8VehKb5l9C6eWRUlibv6Gy4Oi6bFJer5m/c+6Ol0sElHGv2NPP+Twx+HpOO35a3ptPlnL1fDo9bp+hcJeuaPThCEVtBIzb9LOZ1P8jeWWR6Y8cg1SXg+XqE1/DyUnWx9m8lvweN1/NBYnC9zX6LG58srLksk8NazS9Oee/LPY7Oh/EdXxQa+VSR5LxwyNybtG8fhf0lZdS873it7Psr/Tia+E3k6bgioYIJL9KVGabvcv6arhE9SbOLnba6eE1iyW4MY22ZI8lEHSQXAXIBJMtEfJUCpvYsNk8gCon2KARkR8WY2Bnt5MWLJbAoVPkxKtkBkyBblXAEAa3KuAJ/QPdbFsbcBWLKn4YZEtyxFbYcfJVwQgJbDzRWtiJbgEggGtgJYYRZP2AxfBCvggUAAAAAZ0ODHgyCCDDIgHDDew5YSVAFyUUKAiW5kkyLYfTkBQ58gNtgQMhQCbTC9iDa9ixT001Zp/4nq+kTS8L/AMm5NeWah+JcW+kZP/57mzwflHnyfDkGKMnp04vjk2f8OP8A81ia5vc1jRSfplF+GbP+H23W4L3kdnk/zaGH5OzWqXnYr2MYJ+iO/gNnC5J5rpY/C37C2ELR5VRlIwnREVBkscgVcCx4IuQDTspLHLAR4C5FFUaQClyHwSwA87iirfkbN0gMQZJAuhFyVX7AIqwdEv2DbFJolSiFspGQE7DpsFaMliVRUSircxQdNhIVQS3LsH9wWiMioyJIvkFgr+hFutxZkpbcbDdXTGt+A9mRv07n45tViwJ/EkkvuLZGU47fh9DbvkPjc8ifXtHF+n1kfX9FFb5KJ34s5wZfT11u7Dvl8Hl6Xreh1E/Sssb+56KnBwuMlJP2HdKl47P0zut7Cu/oISVMOScfmail9SzHd8PO+PmJJJq7PF7l6Pg1+inKcYxkk6kz9+pdb0OjjJzyxbS4s0HuXvTPq3LBo7jDhtG903FnuVr8uWOq1XqeOGk1c8Sfqp7HwSnJcvkz1CnlyvJkl6pNn5VJ5PTTe53ePUn9nMy3b4ZqVpKrR6vR9DqNbljixYrXFn1dvdvanqM4/I4w96Oodv8AQdP03DFehOVcmn1PUYyajY4+O3T4O1O2cegSzZIxc3vujaklSr5UiKK99hb3S8HG5eS51v8AHhMYrSaCuyRbRXLfc8fM8M/34Jc+r28Hjd0dSx9P0E5eqpOOyPS1uox6XSTzZJJJJnIu9+uPXZ5Y8eRuKdG903Dcrt4c3JqNf6hqsvUNbkyt8tn19u9Oy6nXwxqPqXq3POhCbmlBXZ0v8Ouj5McFqcsN+VZ1c8px4aaOEuWTcukaSOk0WPHGKjsrPu2vbYippIPk4PLl3WujhNRXtuCN2LPNnpeAvruS9gjEVUuCsw4Mm9hoDGcfWmpboysF8VlLZ5a71vt3T6tSnCPpn7mm6/oeq0s5fI5JeTqckkrR+GXT48sX8SKdnjyccvmN3g6q4a8uO54ZI3GnFmWmy5sMoyWT5l7HQOr9uYc8ZSxL0y8Gm9U6Zl0ORrJFpL2NXLjuLq8XU48vitg7f7jlCUcWo38WbnptRHNjjKDu1Zx9yklH0unexuPaXV2lHT5ZW/FnpxZWVr9X0ss7sW7Rd8kd2SEvVBNeTJG5LtxrNXSfW9z8s+NZMMsct7R+r5rwGZ4XVeeXlxfvjRPR9TlJKoyexrEXc/sda/EfpizaR6iMfU0rZybLC8l/pp0d3peTux05/PNVtvQs0ZYVj2tI9C/rWxqvRs7waqEZPZm1QlGaT+h89/K8eWN2cOSupV9CtLZmMduCt70z5253ba0S22uyemS48lcVzZjOah80nskMcLWO9Pz1ef4GFp7GpdRzvJmcm9j0Or615ZuEXsjydVj9UFf6j6n+K6SzWVjX5LvxH76XB8TLHHj3cmdh7F6c9D0qKqvVTb/oaL+HvRZavURzSVxTvc6xixxxYo447JbUdHq+TzqPXgwZRfp+XlMsYq7KtmyW2qOVvdrcn0u3gi5C4QZjSqvuTyVEfI+RlQaVE+w39xBdmQIEAr4MGyp+4GVkDpoifgBQXJVwGBiVKyFQAyTVEdGIGbbZE9iV7lAP6DgnktWwDdsJF8Cy0HZEvcX7lTIDC97I+aLSLsRtWG9g0Yi0X6DcqDIMSMyfJi9woAAAAAy8hKy+QERhLYMoEsq4IVAFuGGqDAV7EaRCoBW9FJRfAEZCvkeACDQvYLkKpqP4lyS6RJVz/wDs241P8SZRj0eVq/8A+M2uD8o8+T4cewKpvybP2FJPrmNR8NGs4N7muGbR2Akus45LltHZ5P8ANoY/k7FB3CP2EluRWor7FTvk4XJ8ulh8KuC+CIr4PKqLgUS0Vbk0lRblbAYC7YXNBc7EfIFa3J9yoANxdk3IBaQa3CsWDSsi5L4sLcATh7lRX9UBAK9hwWETzuQy8CilS/cth8ESMRQKDMliWX1EXIaVk0jJEvewK8kAb+QFyA8ERZcEXIhsT8BpuGxWqPx1OR4scp+ErL8eXpjj3WPL7h6vj0OJxi/no0XqHVNZqvV87UWfp3HrJ6rX5N7jGR5sZScWoo1eTkv6dvpumkm6x+LJOm3uZSTnDdt2fbp+l59RD5YP9j9MnR9Zjhag3R4/2rYufHj408nFeLJ6oNxkj1dL1zX4HSzSpfU+V6XNCT+LjaMfgqUtk0Zy2Mcpx5thxd1ahYnauVcs17qvd3Usnqx45uLb8MylhdqLdJ8njdZgsU18KLcvob3T57ykrm9XwYzG2Ph1ep1eoblmyNt82z5sXq9Mle/0PU0XTdZrJL0YJb/Q2TovZOWeeOTUJxj5TO/jyYceMfN5YZXLTTtBodZq8yhDHJ/U3ftjsybyrNqla9mbr0roWi0XpUcacl9D1oQjF1FUjT5ert+HrhwyPm0GiwaLAseHGlS8H1JuqMv0v7mMluc7LPLK+W1jjIR53ZWttiKlwi3a3JrTKqrj9T88uSOOEpzajFbkz5seLG5TkoxSttnPu9O7Iv1aTSzutm0z24eC55PPPkmMfJ373Msrno9NOorZtGh44vJO5u297GSbzSnPJu35/qer0PpuTqGojDFFuNqzs8cnFi0csrnXq9n9Hev18ZThcI+TrWi00NNgjjxxSSVbHn9tdIxdN0kY+leprc9mOzpnO6nn7rrbZ4ePXli1fgJGb9zE5+91tSIVbFZKHwlRiwVIbEKn4DSKuCKjpFG3kUmDYk3uStzJJ1uRpPdFnhPIkt3I8rrXTMeuwS9cfm8M9X7kXDRhljK9ePK43e3Jep6KWi1Esc1tezJoJ/B1UMqe9o2zvfRx9Cy1vZpr2lF8Uatx7a7fDyXPDy6n0bUPLo4yfNI+5mvdnZ3k0qTZsMuf6G1h5jkc8mOdXwPoRcBcmc8Nazy+Pq2l/itDlxPdNNHEuuaF6TqOXFKNK3R3mVVSObfiN0trI9TCP3o6fR8urI1uow20HFOpxXMovk2vpeWOTTR33SNRcJRmvfye10DM/W4t0ken8jwephuNPG9tbDGqqjFV6tzJtWqMcrhFeqTo+My4bOTt03PUnaZJQxw9UnVHg9Y6lKacMeyQ611Df4cGePlcn8ydt+Dt9B/G22XL4a+fJ+mM8ie/+I+/onTdR1HVwhCNxtWfN07RT1eojjjB+ps672b0KHTtNHNkivU15O9yZ48GOsUwwtu3o9udMh07RQhGKUktz1Xu7oR+ZtcJFST/AKHH5eW55fLoceOojqiJUqMnsDym4ztRclRiFY2itFW3JPIRBWSw7CVgLFlI/oAS3DVDgvIGJVwGtwwLZGyoMCLfkpKHIBqiAA2yXA8giAMIMq4AqFE3LYBrYi2MluRlgOmY+S3sRDQr4JRWRDQpWR8iyDFshX+lECgAAAADNvcN0RLYnIRWXwRFfAEtimE0W/YA+AgiMCoBAAR8lZHyBCviiAC+CBfUvLLSFs1L8S7/ACaXnY21pGo/ia3HpDr2/wDJs8H5Rjy/DkuL5cS9S2o2L8PpP85gnxaNY9c5wj4Rs3YlLrGFLm0dnk/zc7D8nZsdelX7GTqtj88TuCvlJGTOFyXzXSx+GSqxJmKbM62PKMmBkicFTYiUZHyG2QWFZLZ7B7mJkQSip+5USrYBtPgUSipMBt4LSIKGhXwRAIugVht+Aivgglkb3KyLkyFF+Atx6TERvffcqa8ity0i/Axst+A0KGzaJbityoMbFfCFohUkNiOgUbENo3ZErLsmSX0CjdqlyfP1BOWjmlzTPoSSX1JOClCSfDQy+GfH4srk+u9S1eVe8jHRJfGXq4s9nuHpuTBrZZFD5XueQ4O9tjTzl2+h4eSZYabv0bUaT4UYr0pnqqWnk6+V2c0wT1GJ7TaPqfUdVjS/vHaMscpJp4Z9Plfhv89Bpc6p407+h8mboOmk9lTPD6B3DN5Viyu3wbnhyLJjU0uVZ7TVaPL6nE1qfbUHN09mfri7V0qkpZIqVe5sbVK6I7fJ64yY+Y1sufLKar5NJ03S6eKWPFFNcbI+qEUnukjJ14JT9z0vJlfl4TGMklYXuuCRvgPik9jDutWSaV7sN1zuRccmE8ijblJJLmyyWpvUfp4v3Pl6hrcGhwueWaVKzx+t9y6PQQlGORSmlwjmfcPcur6jllD1OMb2o3eDpbnfLW5OfXh7PeHdWXUuWDTZPTH6Gl5svxYNzdyfLPzinK3Ke9eT99BijmzRjJr0vZs6uHBOONS8ndX19H6Zl1so4MUW1J7yo6t2l27h6Xgi3G5pW2zDs/o2l0ukhmx1OTVmzqVL0pUaHU8uvDZ4eOUVOtiqrt+DFJp8i2tzmZefLb+Gabb3I9mE73Je9mEhtZEschltKhkjEyRBGFfgo4Bti7sOzLzYBtLCvyH7lXAWUoNbBPYxbdlk0y+Wvd6x9Whf0NAW+NWbz3zlcNIl7miQdNJmtyatdjo7rFu/YzbxNPwba90a52ZiUdI5e5sUeD14/hz+qsudRbFW73DCs9bGtUrdHk90aFazQZI+m36dj16MJw9WOUX5PXjyuFjzzm5XANfglh1eTDPZxkz9enaj4M072Pf/ABE6ZLT9T+LjjUZptmqQxyUbO5hfVwkc3knbW4/HxLTRy3wrPE6j1T1zUcfC5Pinqs/wFivxT+x81+lNS3kzU/4/Dv7rEme/DHW5XOd+T9+lYM+rzRxwi22z9dB03Nr80Y4oN7nU+0e18OixRz5Ypz5o2Obkw4cdYsseO2p2f21i0mKOfNBOfKs2yKpVwkIqKj8uyXgq9zkcvL31v8fHJFtVQTaCWxGa3zXp8LdoBbchATzuPUWW5iBeWUi5KAb8BLYIvAEJ53KNgIwik2sBvdj6FTDAb+xLKY8gVIu6RI7Fe/AGIMgATtkezKtg9wJzwUJ0Rt1ZYMkyNqwmLTZATKiOgmWA/oRB2yDYyfBEmEVMgFsiLQGE2YrgykYrgKoAAAADNp+AvqROiphEe7G6KHb3QEplQ38i/cABYABsWK8gTnkPkpGBConIAq5G10VEaVgiK7NS/E9S/KJe1G2pSb29zUvxPlXSJJvejZ4PyY8vw5B6Pki0/Bsn4fQn+f43Li0a/it4ltwbN+HzS6zD1+6O1yf5udh+TsONVCL+hm6a22MIK4xb4oz8HB5Pl0sPxY1Wxmk9rMVd7mTex5/pkjqxVBLeysiJdojMqpkqxsRclFbgbNAQA2aXYNqiL7lr6l2ItwHwFuiQSxYsoEvfcoZLAMqoxKgMtg9+CFTGgof1Fjb3APgbBpe5HSQCvBapUQJPkCoj24CDZdAKJYTILS8kYTDBFZN1wWqW5OHuLGU8Pl1+khqsbUop7Go9T6LLHOUoqoo3mnTb2NV7x6otPieOG8meecmm50vJlbpqOqrE2lK2j5HJ5Hdn5vLPJkcpJu2fpixZJzShF2zU1uu/hl247r6NBF/xUfSvmTOm9JT/AIKLltsaf0Do2aWWOWcaRvOCKx4oxXCRs8WNcbrOWZXwzv0ytj1RV35Pyz51hxSyT2SVmi9V7k1MNXL4NuKZ7ZZyNTDgufw3/Zewk4tXfBy7Wd3a3FBuNo+Fd6dRlBv11ZtdPxXkjw6iXi8V1uefFFNyyJV9T5M3VtFjT9eaL/qce1XcfUc6knlkr+p5uXW6yf6tRK/a2beHR39xqXqJp1vqnd2i00GoSTaNM673hq9TFxwycYv2NQnky5F87lJmeKfojVU37m1h0+OPy18uW34q59Tm1EnPLJykz8IpuVp39D6+n6HV6vPWHC5W/CN17d7JyZcqzav5Vz6We3q8fH8POYZZfLRFhS3kuVwIKcd8fy0bv3f2hlwR+Lo16klwjTJfG06ljyx9MlsZTnxz8Jlx2Np7Q7rzaOccGZtwT8nT+mdQxa/BHJja3P5+jlcZNJ/NLg2btbuXP03PHDktwNXqOn7puPbi5dOzK/IW255/SOp6fqOBTxZFJ1vuegjk58dlb2OcsZKhSvYxMjx3rwz0j5K+AyIiURfBGUtgElyUhAQbCQ8lgNughfgLkgX7EezRa3sPcumU8NS7/T+BF1smv9zSE/VK/qb/AN74vXoXKuDn6dNU6TNXmvl2Ok/F0Xs6SloUrNg4a8o0/srVpweFPg2/G9l9T14ruNHq8NZbV/YvBH9BfuezVnkugn6ivcm3gu6lljWu+enLU9OlmUblBM5K/klKDXGx3jX4VqNNOD4cXt/Q4r3XopaPqOSMdlbOp0fLZqNLnw3NvNy+ptNM9PonRNT1HPFeh+l+Tx8eZxpSVpHWfw9y6XNoI+hL1Lk3eoz7cdtfixlr7u2+3sPTcMW4py9zYFGns6LW3BEqfN2cLkzuVu66WGEkH9C+Ar8hcs1/2znwsNkVbbkWxW9qKlYvdlYoAHwSt6K/oYgZJBugmOWKAAAMJpBjwABA7QDjgvqIyAZIIn3LQBkTZXsE2AA5FAWtiDkO7AAlBcl0aWwRoLggNBbMXuGBW1wRh8hsugRQhRBkSXIXAfAGEjFcGTIFAAAAAGaQXIXBAisEstgORSaIygT01vZfBHaLyBPqLMkg0BhbsrLTG/kDEqQe4QE8hbFsisLGUU2ab+J+J/lTdb//APTcU2maf+KHr/J3KEt1/wDs2eD8mHL8OSaSSjCVmwdgyU+uY6TXzeTwMMFLAm5/M1Z73YdfnuFLZ+o7XJ/m52H5O1x2hFL2Duxj/Sl9EZySrY4PJ8ulj8MUrMkYxL9jyZVkY0/cq3RLVlqKnaJwV7Ij4TIC4Kh4HgCAFsuhOQGLaIAA8FhWL+pkn7kYRBeQ2lsR2uCqvIBJsUVt+CNMAVEAF5I00tgXxuXQi4DRUGQSvqVGL5LHYCshWRgYlovpJwwHgbcimy8IuyD2ofUBL1oWKwzyrHKS3SRzPunLLLr5RlwmdL1K/uZR+hzPuDC11CTfFnjyS6dHopN+Xl4sfqyxgvLN17b6RjhCOWUVJs07C3jyKVXTs2jp/cUcOGMXj3R4cfi+XT6m246xbhCEYJKMVFIuXUY8cHKclFI1bP3Wq9Kx/MeJ1Hrmp1bajL0R9j2y5J+nOw6TPO7r7e6euyzSlhwydcbGrTnJbveT5P2n89W/mt7n66XS5NVkWLHFuTa3PPdyro4cePDjuvJ6hjco+uMG19Dzc2GT9PpxSXudh6R29pceljj1OJSl9T7f7P8AS09tNE6nScvpxweu1y26cPjpc8/04pH1aLo+t1Dv4Ev2O1w6L0yLX/DRPox6DSYt8WGKSN69b9OZ7fTkmDszXZEnUkmbJ0TsTHCKnqfmrwzflGNUopBpe9Gtn1dvh6Y9PHm9O6Po9G18PEk19D04x9L+VIJRSrmyxjW6NbPkt/b2nHI/PLCOSPpnG0zTO7u1MWq9WTBFKXOyN2t3fIdSTtLcz4uayplxyx/PHVdBn0eZ45RcZJ7WfiviRSfl/udo7p7a0vUsUskIqOVK1scn6507V6DVSjkg/TF7bHX4OomU1WhycfbfD6u2utajpepUpTbi/F7HVu3uvabqeOLjNeut0cPhJ5G7lu/B93SOoarpmoWTTttJ202Xm6eZzcTj5bL5d/i1V8FV+TVe0u6NP1HDHHmmo5ltT2NohJVbdp+xyOXguFb2HJtlaoL6hbr5Q0zXvl7aR+5kjBp+QjFNM2YvkoLo0jFFFfUglMJF3BYQpeDGm3ZbZXstxFteZ3Dpf4vQZIpf4W/9DlmXFLFklCS3To7JOKeKSfDVGgd19HngyyzYY2nb2PDkx3HR6Pl1ZK8joOulotWnJ1E6N0zqODU4ouORWzk83NTUWqZ9Gl1ur0krhkdLwa+PJ2V0eXppyzeLsMWt5XsVU1dmh9K7rcVHHqZV/qbXoOo6bVQTx5Lvw9jZw5JXJ5Oky433t06RbSEKauxtz4PaVqWX9pJ7/RnO/wAS+mJJ6qMf2OjSir3PJ7k0UNZ0zLBq5el0bHDyduUeWeO44VBRlGam92qNs/DjqX8Jr1ppN03Rq+qxS0+rzY5RfyzdH66TVrBlhmgqkpI7Vnq8bnydmb+gYu4Ra4asrd1aPE7U6lDqHS8eS/mUVZ7PhU7OJy4dlro4XcZol09iFSvc12UiIr+hFyX6gon4ZbI6q0RboCtX5IuA00HaRdAihAaGRPsSy3sQYsIXvQaLSwpWPJUt9w+SCMhkg0BiZIlFAm9BEfJlSW7L8AtyyJaTK3fAobrkxbMr24J5IC3DHBEy7NibKRc2UglFoJMMCMIoSssBbsDhlfBBFyVmKK9grFrYj2LbIZAADEAAZDJpijJuycGKJwErfBeQA28k2srFr2AAWNvBkAtIbjbyDSN7lV1uGr4G9E0qPkjD3AiQAf0HC3Iy/Q27NV/EXH6+kZL4rn9za7NR/E2Tj0WTTq1VGzwfMeefw5FpqilTutjaexYY5dbwvz6kavgivhxpbtGyfh4v/wCwY/Vtujs5/wCbnY/m7Kl8safgydNbkVKC2okk75o4fJ8ulj8MogKweVZUvwKrci5YVkQ52Ra23JwH6mwLT5CsjvgK6oCgBbgLQTSDaY2AeQAWCMRVsoRAfBEVutiUmBkiO1wAtuQCb8l5DoiAMbmRi2/6F2CDJZfBBiWymIFsq3MSrmgLbI6Yf1HgCjf2IhuwCT4MlsiRbXIe/BdL40kqdp+TUO7ekTyN5cSt/Q3D0prfwY5YRnFxaTTJljt6cXJcLuOTTw5sb9M16WWGPe27o6J1DoWm1CcvSlI8uXbOP/C6PG8e3W4usmptp+RKUrr+ph8H4v6N2blDtiF/M20ffougaXBv6LZjOJ6Z9dP007pvRs2qyxUk/Sbn0Xo+HSQi3GpHpabS4sSXogon7OPFeD1x45HO5urufgiqReTLwS9z0nhp72L2HBPJS7S3ZYsNh78GP72RCq3wEBbtKnpsOL55LbYTfsZSMpfti916a5PH690XTdSwShkgvVWzPZbl+xGk9n+5lhyXCsMsJY4d3N0HU9K1UpRxP4d8pHlOE5xTVbneuqdN0+v00sOWEG62bRyvujtnU9OzzyYE3j5Ox0/VyzVaHNwa8xrmDUZtNljPHJqafKOh9od3etR02re/Fs5xH9Un5XNmXxpJp4/la8o2eXjx5J4eWOVwr+gcGVZcKyYZpxfsftBylXsco7Q7tyaKccGql6ovZWdL0GvwazDHJikm2uEcfm6e4XxG9x8u4+ubbeyHHJWlSkiPg1da+WxLuKh5CXkGCbP6lXG4sjAV7AEsGl82GrInbMm9qQW1INU0z8NRp8efDKM42mfRSrcxunXKFm2WN15aN3B241J5NND67Gs59FqMNrLB7HX/AEqTppUfFrOmabUJqeNb/Q8M+Lbo8HWen4ci+HJySS4Pt0XUc+lnFQbSRt3Ve18bjKWnuMkafr9Nl02R480HFp1ZrXC410cefHlmq6B271iGsxRjKVSXJ78fTW3ByLp2pno9THJCTUb3OmdD1sddpoyT3o2uPPc053V8HZdx6L2RjKNw9Mt7M+XXsYyTq2bGHiuXZtyn8Rulx0mt+Nih8k95NGlZIq9ro7f3j02Gu6RP5bklycV1sMmDNLFJVTa3O50mcs00Oox1dtx/Dbq88Of+GlKovhM6tBqUU0/B/PnR8z0uvxZVNr5l/udx7f1UdX0/HP1W6R4dXw68s+n5N+K9F7Oi06otep0yv2OTZrw3rfDFFK/0kJpim5kuCeC2BHsBKqJvRZSKLtkRkkKUS2KT1URkBryAAG/gU6ATdgOC2RigKRgr4Ai2K3ZGgk7oyCrFVsEGYguCoxRlbAMxpFb2C4AjQT3KwqAIthBqgIK9gwWAL2DdeCEFsjLsRgR8GK4MnwYrgEUABQAGQze5PNFDJURFfArcMgJeSOi0hQGJkuB5BfgN7JZkuSMbNgIypWiFTyXgj5IWEXxZN3uzJcERGX6Odmab+KTro0qRuTNS/EuKl0aT8GzwfMeefw5LiT+BH3o9z8P/AIkuu4k9qlz+54MItqKi/Bsf4fyX55jinupL/udnP8HPx/N2WP6I37Ir4CXyxr2DOHyfLpY/Cq6I07ELK2jysWogisnDGkUMjY+o0KiUKKQTfgbl3FtgRplRLKqAV4DLZHyWCWEV8ESGhfAYRUQY07KGyfUClbohGBWwSixAPglMrADxZEvJk+ABOQ9g+R9wAAYE5e5bIy0Bdg6IGXQEcaL9iK73GmUs0jtsUZCiG79oKRRZkTY9tiF8ES3JUulTIvIS3FOyaFoB7E3G0Voi+pSqgqX4oB8j7hNjKiOq4FobNbVmLRXvwL9y+CQ8Hy6/SYdXhljyxUrPqVJWSKpWtzPDPRljK5d3T2lPTuefTR+V70jSM+KeP1Y2mpJ0f0LmwRzQlGaUovmzR+7O0IZ1LPpI+mT32OnwdXJ4rT5OH9xy7Faa9bqS4Ni7a7i1HTc0fiZLh7HjdU0Oo6fn9OXG2/DPxSjNJvnydC9nJi8POFdy6D1zS9SwKUZpS9rPWvdNM4P0bqOfp+rWTHkfpXg6R213bg1Sjh1Ekpe7Obz9HZ5kbHHzb+W5XvwNq3MMWSGWKnjmpRf1M682c3LGy+Y2pZYU/ALuGYKhGZEfuD4YpNbmVeQ7CZdmtnI+4ctick0a0t+4Zi9ix4EJv9MckXJtpUjXO6elY8+CWSMfmSs2aUnVI+TqMfiaaX/1JySWfDZ4OSyxyLPBxm4f5Wbd2RrJLIsV7cGtdUg8euyL3bZ9na2d4+oRa4bNPHxk7fLj38W3UI8te5nwqPzxP1QjJexnVqzel8Pns5qsZxjKEscv0tUcg/EXpv8ABax5YQ+Vs7C+V9DXe+OmQ13Tp/Im0tjd6Xk7co1ebHccUhOMVGfnwdH/AA36vbjp8kvtZzvU4ZafPLFONeln29G1+Tp+sx5o7K1Z1+STPDw05ezJ3xP1K1yZKW3ueV251GGv0UMsZXKlZ6tRv7nC5cO210OPLuhfgN7BNcC/B4aZ6FuVqiJofch+lSsj+g4Ah8JTLew28AtABb8l2IIh52KkvIe3AE4A5ADllsgAtggAthGPkoCwpILcte4Evfcrexi+RvQNDFlXALBEQq53K15ICpIroi4AIjsisu7LTSAjsLkuzIwIAAD4IV8EBAABQAGQzAZdibRAV8EIABaTRkqFsxZSVDfyK3HgqIbNh4D3I9gI+ScmRKBCiLgb0E65Cr4NT/Epr8lklyzbVumjUfxJv8qftX/k2en/ACjDP4cfUnFJ/Q2P8P031qEkvK/7mvQSbX0Nq/DucPzyMa8r/udrP/Nzsfzdfg/7uP2RSqmo0U4XJ8unj8C4JwxfsLPK7UsnJXyKHkEWtqJRfA0iIvBEVkALgjLWwGJkYmS4AB8GILBkuAyJhvYgqYbMQXR4ZXtYsiFexFVBfULYMsQbRi5bmRGkxATMk0YpFYgr4C4HjkjdECnYDdoxV+4GRHyV8EfAEKiGSqgAZOWPJdmxFb2Iwhs2q3LSfBGiK0TaqGFuGi7TZexPJaI+SBe5U9iIr4AEYpF4VAYmS+pN3yUuwACfI2a0AAlDwK2ACq0mRWkX7h7j4SItjGfplyjLyYtJllsLNvB7j7d03UcMpfDSm06dHMOu9C1HS5yXoco3ydtUndco+PqXT9NrcUoZMcZX5o3uDns/bw5OLbgM5Nv0cMzxZcmDIpQk1JG6dzdmZMOWWo06+V70jTcmnzafPLFli17NnV4+bHOarTywuNbb2v3fn0844tTL1R43Ok9L6nptdhjPDNW+UcH+DKPzKVUep0zrup0E4vDN0uVZ5dR00z8yMuPm14rusZplRqHbHdmm10I480lHIvc2rFOORKUZJxZyuXhuP6bvHyTJ+i5YX6glfAvwt2a18vW+fhWY1uZNbGLFSLyEl5IhbS3IrJmPnYyTICWwSatn5Z16sUkfo3TSMciTi7F+GeHy5f3TiePqMq8nzdGax66D8tnq954pQ1vqfFnhaXI4ayMuEmjSy8Zbd7ity4tOu6J+rTY37o/dumed0XN8TQY2nukfet1TNzju44vNNZaorb2MM+P4mOUWrTR+mydEdt0z0xy7bt4ZTbkPf3SJaPXyzKNQkzV9p4vZo7Z3X0yHUdBKLjckrRxnqenlo9VLFNVT2O10nL3TTnc/Hqtu/DvrD02ZaXJLZulZ1CDWSMZxezR/PnT9XPDqo5YvdM7L2X1Va7Rxi5fMlvZ59Xwbm4y6fPVbDa5GyVkoqSOTlNVvy7grL4CKY2JtGFuR8hcEiqOS0QIcBPcLkebCjslmTMWEUEXJQAAAMNNgtgQr4IxfguwRbIBoH9i2NhaIJ5AtNhlgF8GLdsb0QUrVES8h3QBJ1YZY8GLLBDIKvIsgjIZ0R2Bi+CFfBAoAAAAMhmS2LDZimlTtBkTspZDQEOF7hblUBGvYNEqVXIJ7kCIVfJGK3opYIiNlphrwxpYgq2VPwV/Qgi2s1H8TZV0eSRt/Fmnfian+USNnp/mMM/hyHDxbe5tf4dyi+uQ97X/c1PBFSj5s2j8OYKPXoNve1t+52s/wc/D83Z7dR28FTIv0q14MklRwuX8nSx+GITdi14InueVVb9xyLA2L4FbERb8DaCAXAZAY8EaYulyBWQpOWAoLdl8CwJQov2I+OS7CkKIuC+Bs0cMJi/BBKaZIyMEVEoP6Ev3KPJkFhEobrgmtmlqmHwEV1wxZo0xXJaCr3DogP6kp0PuUDFKtyq/BXwRJl2Ce5eSUBoFuUidsNpPcaF8cgnBVuiGwqe4RPIFIy0RIAElY55CQVdkTl7hqhyEFyHVBkewIJl9VkteAn7g2t3uDEqWwFHLJwypgR80WyXvZbFhDkj2LYfBfP6IiI/JkkNvI3f0zfnkhHLBwyRUk15NY7i7TwayEp4oqMt+Da20nZi+fp7Hvxc1wvl458cyjhXXOja7QZ5QnF+nwzya9LSez+p33qnTNNr8TWSC9Xh0c17r7SzYcry4YeqPsjrcHWY2arT5OHVapDLkwNZMEmpfQ2vtrvXJppRwavePFs1DNhnp8rhOLj9zFRjKd1aNi44ckeMuWFd46T1fS9QxRlhyptrg9KqV2cF6R1XU9P1Klhm/SvB0Xtnu/DqmsOaVS43OZz9LZfEbnHzyybbrfkNXuj8sWaGZKcJJpn6J0tzQy47PmNiZS/DKticlvagltuYf+Mt1GOVyGthToaLSr3ZGWwnfAs2yxuvLVe+dF8XS/FjHdGhSuLt7SOvdR08dTgliau0c56/0vJptRKUY7eDU5sb8ux0PPNatep2j1p4pRw53SfBvGKcZxU4u4s47GU8e/ElwbJ0TuPJp8Sx5nf9S8fJqaq9V0szvdHQWk+OSpP07vg8Tp3XNNqmkp02ezCalTi7TNnGyuTy8Vwvwk6dxa2exzb8Q+iOMpavFC48ujptKvqfB1bSY9XpZ4pxTtOja6fl7K1uTHujg1wx43WP5j3uzet5NDq4xk/TFs/HufpWTp+tkvTUW9tjx/X8NJqVPwdmZTlx05+rhk79oNTDVaaOaDtNLg+i7V+5zr8PeuRUY6bNlu9lZ0THJSVp7Pg5HU8Vxu9N7jzljJO1uA68EW5q36e0m1CZKZUTSaZAxW5dl5IaHwTwVsgE2stk3ofctFsIlqwnZDSgIrAgApUABJclRZBG3YZSO2XSiVFCDXkaTwjJbsv0G3INK1sVJUY2LJSxQ9uAuAthYI26CTorIuCCFsUxsBkmRsiDAjIVkCgAAAAyGTCSLe10Hu/YkB0RrYu6+oVF2Mbr6mXqrwRtLgg3Bk3sF83ISbBNgK8i6DZdg0rDG9EbRLQ25D4CK0khslYpWZJUFVB88j5WUapGnfiY76S9tjcXsqNP8AxLUpdIdeDY6f8o8+T4rkuKSUdlRs34e+h9exf5m1/wBzVotennc2bsDJCHXsKSvf/wAna5JPTc/Gf2dlt+lbGTbqqJG/TH6ld+5weTxXQwvhI2/AaSZb25Ju3dmG4zVrchU/DHp80TZpKCRWHwTcppHyET/UyVtbIJpf6GLv2RaFWi+F0iKK8WR87DZoYj9ipeS2t6G4aYrZh834LY5VWNmiiJe5U/BG6KaowiciwulRlwRPYfUlY6H830I1RfHJLJs0LkysiqtyPnYu1kVyaIrb3Cu+A7LuBKyeC72K34L4Ci8IlBqiGlQ9TuqJauiqSugaRsJCldplf6SbTSJUSm2ZJ77l4RNmhrYiVEbt8lXsXwaOAnuKtiqIulb3FmL3exWq5Lo0raRHIJryVJN3Q0aSwZbeTFu2Jo0BX5GxLZfBod+w3rYyoj2JaI1tyFwR7+Q2vciUKuCLfyWi7NgRavlh7ciU2lrwLQpN2Vr6F3SJ5FW7It9h5JVrJ1e42fBiZLgbT4RrYwy4seVVOPqXlNH6PZe4UtttjKZWJZK0zuntDT62Dy6eCjLmjm3VOkarQZHDLhainzud68NM8/qvStNr8Thlxptrk3OHqbK8c+GWeHB3GounT9yLM8DjLFOSmmbz3L2bLCpZNOm480jRtTp54csoThJNPydTj5sc55+Wnlhca2bt3u7WaOajlm5x/c6Z0Truj6hgjKGRKTW6ZwqCfMefY+vTdS1OicZY5uMrJydPM/gw5rH9A3cLjv8AUqfy+7OZ9sd81kjg1stuLZ0HQa/T6zEp4JqVnL5enuN+G7hzSvrp2V3RjFv+o81yallj31L8Kl7imL9wjC3Xg8w8fU+HqXT8WrxNSScmj738y2MUt6aGWMs8vTDK43crm/WeharT53NQ9UXxR4mfHPHOpQr7nYcuLHlTjKKZ4+v7f0udyaglI18uP6dDj6yyarn3TJZMWeLW1vwdO6M5S0cJSu2vJ4uk7Zji1ClLdJmyYMSxQUFskqPTjxsry6jmmb9Ldhpt+osFT3I3TPXdl20L8ta716PHXaSWWMfmSvY4/wBR0uXFq3hlFxSZ/Qco+uElJXFnPe/u336ZanTx352Ol0vPqyNXm49zcc+02TNpNRDLilXpe9HYuy+t4+o9PjGc0s0VVeTjOaOTF6oP9R6XbHUc3TdbHJ62o3uvBvc3HOSNfHO43Tu0btX55MntweX0LqmLqOkjkxyuXk9NLZvn2OLy8VwrocecsE9iqmRpCKpHhIyW/oKtDfyqH0GtIi2ZlaZGiVsIWraJaKkvJfBaJV7ig3QtPkgl27KEXhF0qcANoIaTY0nuicFT3EnvuJarHyVst7EVNl7qbVOtx6tgGq3RNw2i53D3YVvkVuXwFCn4Lavcl7l2LuRX5FinyPlNDCSrkrS8jZGOlS03Vitw6XAb2Ii0HVERXwBiyFZAoAAAAMhHmxJfzEFmwt7ZUc7nrtQ/+YxHWai/5jNGdZJ8x59zoqzYK3zRJ8fCn/Nic7es1Dv+8ZhHV6lSt5X+5L1sO50d5cF/zYiWfCuMsTnf8bne7ySH8XqG7+Kx72Hc6Is+Kv5iItRgunkRz3+O1NV62YrV6lu/iMe8lO+OirNgfGRD4uFf8xHPFrtTH/GyrqGpb3mye7h3x0P4mCX/ADEFkwr/AJiOeLX51L9bL/H6lvbIyzrIdzoTy4qtZIE+PgfORfuc/et1FfzH+5+cdXnv9cv3L7yfR3R0T42nXGVD42CtssTnj1efxNket1CVKb/cTrIdzoizYv8AqxNd78xLP0qccUlJ/Q15arUNfNkZ+c9VqJerHKblF+56YddJdpldxouXGsClGcH6vobX+G2lhPqCy5KjVVYz6DBkn6skVZ++iS0crwP0v6G3n/LSzTWmOq6cp4lS+KivJi/6qOdrXapu3kf7ha7VN/zX+5o3rpb8NmXUdDWTF/1UFmxJ18WJz+Gv1PnIw+oam7+I6Mfexn3x0L1YvOWJHnxL/mo59+Yal/8AMZHrdQ+cj/ce8n0nc6F8bF/1YkefC9vjQOePW6j/AKj/AHMXrM1/zH+5PeT6TudEWbB/1omSzYk9s0TnK1WoT/mP9zNazU1/Mf7j3sXudDWXC/8AnxDyQrbLFnPlq87X8x39yfx+oSpTf7mXvJ9J3Oh/Eh/1Ih5Md/zInO1r9Tf81/uJ6/Ut7ZX+497idzojyw/6sSPLi5+LE54tfqa/mMj12ppp5H+5Pexe90RZMT/50CfEx3/Oic6jrdSv+Y/3M3rdQ1/Mf7j3sO90RTxc/GiHkxP/AJ0TnS12pbr4j/cS12p4+I/3J72J3uirJir+dEvxMfjLE5w9ZqP+q/3LDXahv+Y/3HvYdzo3rx/9WI+Lju3lic7lrtSnXxG/6l/j9RW2Rj3kO50KWXH/ANWJFkxP/nROefx+qvebKtfqV/zGPez6O90JzxN/zohZMKdPKjnr6hqb2yMxev1Lf8xj3s+judGeTE+MqDyYUqeVHOv43VJbZX+5P47Vf9R/uX3sJnHRlkwVXxYmMsmL/qo53/Hamt8jJ/G6m7+I/wByzrIdzovxcP8A1UX4mFr+ajna12p/zssddqlzka/qW9ZPo7nQvXi/6qHrx+MiOeS1+p4WR/uVa7UqNPIye9h3uhfFxLjIi/FxVvkRzxa/UpW8jD1+ocf1sx97DudD9eKv5iCyYn/zUc8hr9QlvkZP4/Ver+Y6HvYdzoqnhW3xYj14f+rE54uoair+I/3MH1DVX/MY95DudF+JiT3yoPJia2yo55/H6pq/iMfmGoSv4jL72He6GsmP/Oiyy4vORHPF1LUem1NkfUNS1vNmXvIdzoXxsMnSyIqyQ8ZUc8Wt1Hp9Xrf7lXUNVV+t/uT3kO50Fzgv+ai/Eh5zQOfR6jqJf43+5i9dqm7+I6L7yfR3Oh/Ex/8AViT42Jc5Uc/fUM6Vet/uYPXah/8AMa/qT3sO50X4uGtsiHxcX/Vic5/MNQl/MZHr9TV/EdF95DudGeTG91kiPiY/+rE55j12pa/mTMY6/Uetr1z/AHJ72fR3Oi+vEuMkSPJjf/Nic9n1DUL/AJj/AHC6hqEt8kv3HvJ9Hc6D8TF5yxMlkxPnKjnT1uaTtZH+5XrdRW2R/uPeT6XbonxMN7ZEX4mPxNNnN1r9UnvkZ9GDqmeE95suPVy3RMnQDLlHm9C1n8Vpk27Z6Vm1jlMptlPLGr8imvJWkQorC25LyR/UspEaXITXuWkPIlsrLwxyQeVOE4xcX9DWu4O09Hrsc5Y4enI/JtC3DiqPfDmuDyyxlcN6323rumZXL4bnFPlHlaj5l6XGmubO/avR4NTCs2NST9zUO4ezMOpUsmnjT9uDo8HW/qtXk4N/DlmJYkvmTc/DTo9fo3Xtf0xr4eS4p/pZ+PVOkazpuofrxP0rzR5qk5ZXa58G9Lx8s217MsHWu3u8tJq8cceql8Ob2ts2zBnx5caeOcZxflHAHlhBKMX6ZeGe30DubWdPnGOTK5R+pp8/Sb/F7cfPY7TXkKuTWuh916TW+nHlyKMmbFDNimrxyUk/ZnN5ODLCtzHlmTN+qwntxuE1T3CdL3PG42M5VV0RtNblTdPYlKjHxDz+yPO6K2k7MVuN7Ltdq/crp8GIXNjxSyK062Px1enjqMEsWRWnsfs+Qvrui4W41LjLHJO9O31otTLPCEnFu9jVc7UYL0Ljk7v1nQYtdpJY5RTbRxru3ouo6bq5UmoNnY6bnl8Vz+bjsu31dodxZemauPxJP4LpNHXOmdRw6/Sxz4cilGXjycAxzjaTWx7/AG51/U9InFepvFd0e3UdPOSbjHj5e2u2XfOxb92aBi7/AMMq9S4Pox9+aWa3XBy8uksvhuY8003h0lsDTv7c6NQvyXF3109upbM870ucZTljcHt5JuazDvHp05KPqps9DTdw9Py0vjRX3ZL0+cWckr103wx6uT5cfUNJka9OaO/1R+sc2CUvlyJ/1Mbw5Re6M1vygLi+NyqvL3MLhYsyglXJXurRWS62rYx1drLKLgP7hEadF1plJBXYdMsar6n5536cUp+xLlqMaycscNpTSMXmwL/mo0nq/VtQ9RKEJOkzzn1DUt162amXVSVhcnR1mwLnKi/GwP8A5qOc/wAdqK3myLXalf8AMZ5+9h3OjvNp/GVE+Lh/6qOdfx2o8ZGHr9Tx8RmU6yL3OivNh5+LAizYHxlic6Wu1DTTyMQ1uoTr4r/cx95DudGWXF/1Uz9E9tpWc4jr9Sp0sjNl7a6jPNL4eSVs9uPqO+6WZbbC3bFbblk2YpGzLtfkqJfuR7DZkFTIgqvYr4L8CMgfIsVQAEAAGQ5usOT/AKbI8OW2lB/sdCfT9Mo/oQXTtNf6Ec32rz7XO3p83+RkenzL/lv9jov5fpv8iI+naVv9CJ7Q7XPHgzNV6H+xY4MqVel/sdC/L9Nz6UPy7TN36EPaHa56sGa7+G/2LHDmbv4bOgvQaaq9Ef2LHQab/JEe0O1z948vnGyfBml+hnQH0/T3tBfsYvpun8wRfanY0BYcl36DL4WS69DN9/LdMuIoq6fplzBD2p2tBePLw8b/AGMXjyVtjOgvp+lf+BBdO0q5gh7U7WgQwZq3gzF6fM3tB/sdCWh0y4gi/wAFp6/loe0O1ztafUf4oMjw5k1WN/sdEeg07/5aH5fpmv5aHtdHa569Lmav0Nk/h81JPGzoi0GmS2gifwOmv9CJ7U7XO3gyceh/sIafIn+h/sdD/L9Ld/DQ/LtMnfoQnSLpz74U3a9D/Yqw5FHeD/Y359N01/y0V9O0z29C/YXpWPa598PKuMb/AGHws3/TZ0JdO0v+RF/LtM+Ma/Ye0Xtc8WHL/wBNklp8v/Tf7HQn03TXfoRfy/TcehD2h2ue/Byf9N/sR4sv/Tf7HQfy7S3+hFfTtL/lQ9qdrn0MWVf8tmTxzr+Wzf10/S/9NFfTtN/00Pana548U/V/LZXhm3tjZ0H8t0v+RBdN0q/wIe1O1z34ORPaDEsORv8AQzoT6bpb/Qg+naXn0IntDtc+eHJW2Nljgy1vBnQF07TL/AjJ6DTf5EPaHa56sORb+h2YPDmbv4bOhrp2lb/Qh+W6X/Kie1p2ueLDlW3of7GSwZE7eJ/6nQfy3T3+hFfT9M1TxovtadrnjhkT2w3+5kseblY2joC6bpK/Qv2I+m6ZcQQ9odrn8MOZv9DK8WVP+WzoC6fpkqUEPy7TNfy1+xfaHa56sWVv9DMv4fLX6Gb8+m6b/KjJdO01fpQ9odrnvwsqe8GZfCyviD/Y399N0z/wr9iLp2m/yIe0h2tDWny1vBmLwzv9L/Y6Cun6bhwRH03S+YIvtTtc/WPIuIP9jNYsklvB/sb4um6Vf4EVdP01bQQ9qdrQZabInag/2MZ4s3Hw3+x0F6HT1+hEeg03/TQ9qunP/hZa/lsLDla/QdAXTtLW8EF07Sr/AAontE7XPXhypbwYjhyp/oZ0JdO0t/oQfTtJf6UPaHa5/wDCycehkeDK3axs6D+W6W79CD6fpk/0Ie0O1z9YptU8bH8PkS2xtnQPy/T/AORGX5fpq/Qh7Q7XPnimo18J/sYThmapY3+x0SXT9L/kRiunaW/0IvtV0558LMo18NmUIZHCvhv9joT6dpePQgunaa/0Ie1NOevFlX/Lf7F+Dka/lv8AY6E+naVr9CIun6ZKlBD2qdrnrwZXv8J/sV4MrW2N/sdCeg01fy0T+A0y/wACJ7Q7XPHgy3/LZXiy1Xw3+x0L8v0v+RD8v0138NF9qunPPg6hP5Ytf0K9Pnq/S2zoX8Dpl/y0VaHTf9ND2ppz1abPW8GyrTZb3xs6H/Bab/IiPRaZ/wCBD2qdrn38JlXEGHps6W2N/sdAeh01/oRktFp/8i/YntDtc8jpszW+J/sZYdDnnkSWN0zoS0mBLaC/YsNNhi7jBJmePTTGnbp8Pb+knptP8ypnqbvcQpKlwG9qNzHHU1GcHvuYle/BaPQ0i3FbiPJW/cmljHyWmPIdCptUnZNwn7lGtkpeyvcklF78fQr5MXd2izcLI+PXdN0utxuObEpJryjQu5Oy/SpZdFD0rmkdJV3yWUFJU1aNnj6i4vPPilfz31HpWs0k2skJbPmj5p+tJKSs7x1Xo2j10HGUI2aP1/svLjUsmmj6lzsdHh6uXxWrnwWfDQ8GSeKanCbjJGxdC7p1uiyx+JlcoLw2eD1HQavR5XHNjkvqfhH0tVF/c2LjhyPGTLCuy9D7r0WuShlkoTZsWDPiyq8WSLR/PeDLlw5PVHJ6X4pnvdI7n1ukmk8kpRX1Nbk6SX4e2PUWeHa1ut2WlVGhdE74w5ZrHqF6X7m26Tq2i1CXozK39TQ5Ols/TZx5pfl99BtkUoyScX6l9DJ1XBr3js+Xp3SsSkV1wLvcxkkrOyWK+RdIeCqJbqpJpj528nl9wdHwdS0koTxr1Vsz1k9w1ttyZ8edxrHPCWODdd6Jqel6yUJY3LG26dHw5UoYkmr+53Xq3StNr8DjkhH1PzRqPUOxoSm3jfys6nF1Uk8tPLg+nNUoNXGKtExRfxpUtmb6+wssb9Hk+eXZGsi/lR7zqML8vP0so1FSg6i1VDLDHNqSlVG0ZeyeoN2kz5p9l9Sjuk3+4nPxxfTya8pKEv1MuXJNR9ePLKz18vavU4uvhyf9D5dT0LX6eO+LJ+w9XjqdmcfPpdfr8a9b1MtvFn3YO4OqRncM8kl9Tysuj1mONPFL9j84ZPhv0Si0/qXtwqbyjdND33rNKowyy9fvbNl6X3vpNS0ssVGT8nJX6Jyl6ufBlijKCtOmYZdNMvgx5bHfdN1PR6iKePMm39j61J1tJM4Nour6vT7xyNNfU2fonfGXHKOPUbx9zw5OksbGPPL8upRbZX7njdH6/odfFfDyJS9rPYUm0mt7Ofnw3G+XvjnKq5tGGePrwygvJmtmVpXZ4ZYzTO6aD1bpmbHqpShH1Js+L+Ezc+h2dGyYMWTmKZ+S0OBP9CZo8nT7vhjrbnr02dcwZisGW/0P9jon8Dpmt4In5dpfEEeftE7XPlgyp/y2Hgyp/wAp/sdB/LdNd+hGX5fpq3gv2HtV054sWS/5T/YZME+fhtf0Ohfl+lX+BB9O0z/wIe1NOeQwz2fodmw9saLKs/xZJpGwflunT2gj6cOLHijUUkevHwdt2SMnF+44ZWTc3JNMjlCiO0VcGQJJCihk+RiRlZGKsAAQAAZDN+1i6QIyeBbRi+SrkboeDS+nYle5Spe7KI4oJKivgJUBE97oMyI0TwicD7hon9Bo2Ol5DHI2GlFaMt14MVyVIaByZVdEqwNQ8AElW4W6GoaRt3sXeiqOwabGjTGyt7gIahoafuFsuSsxQ0KNqFXuyPYeBaViO73Csm1jUFWwvfcXvQQ8A+AA/oNQNwyAmoKrBL8IeLY1IJv7l/qPsVIsv/gcE5MmieB/+gk/AW75JuTceBk+Rboxfqb2Lch4Cmyp0qJuGNQ0K15Kkw1sROhqGloNojdkHgZBP6mKKhJIVW9wC0PAioMNBsaCvcmxf6ihpNF+WLEn4IhpdLYd1yPBG3Y0aVpPySknyLF72PAqpbhsJ2KGoIvqPJUKtjUNDexGWkibDwF3wR2ZEfJJE2q+4vfkEaL4VRYSDSQshtGn4H3KhRPBssfYLktF8JtPOwa3BLG5+j5I8lfAWyEiqJbWAg+TFNsQwAoVPcWUuwQlbY+gsiIlRbD2Ww58F2bRU3dEnFSTuqMmqJT5LMrPgs28rqXRNHr4SWXDFt+UqNJ612N6VKel2fsdMbdmMoxfKs9+PqMo8suKVwXX9E1ejyVlxtpHxZcbS3i4te53rW9O02pi45MSd+aNZ6v2dgyqU8Kp+yOhxdXP218uD9xybT/Ell/VTR6WLX6zTtenK00z1Nf2vr9PllKGN0vY8TV4M+OTjkxzUk/Zm7OXjza+WOUrZek9567SOKzv1R+puHSe9dFqUllai2chnKXo9L5GGc4b7xo88unxy+GWPJcXftN1XSZ1cMqp+LPqjkhJVGVpnBMHVtZpkpQyt/Q9vp/d2vxKMsjbj9zU5Oi3fD2x6i/t2JLaxZpPRO98Gb0487Ub8m36PV4NVjU8GRSv2NLk6fLDy2ceSV+7tbmSqtiN7BNpGtq16Ferki22MkJc2ZS3SyMX9GErdsvHgnjYnfkmorr2I4pvgJ7UW7dUXuq2Ri8ON8xV/Y/PLptPk/XijL+iP2kfnqM8NPic5tKK9zPDLK1jlJry+LUdG0GW38CKTXsv/B4fUOy9BqG5wioyPp1fdugw5XD1ptc0SHd/TJNRllSs28byPHeN+Wr67sOcPVLBuazre3upabJJuDcV9DrOPuPpeSSj8eNM+iGfpmrTqWOSf2PbDl5MXlcca4VlxZMc5LJBpo/BP1J0uDtHU+2um623jeOMmvdGkdd7Oz6SUpYWpR52Nzi6jfixr54WfDV9BrNTpcqyYZyVezOh9od3Smo4dZKuFbOdZcWTTTljlH5kfjjz5YZF6LjJHpycGOc2xw5LjX9EafNDUY1PHJNNWfsm6prc55+H3XpThHS6iTb4VnQYyTS9quzidTw9ldDiz7orpsPkrSQa8mp4e6WLZeERXQ8J4N73ZU/qRWNxqVdxUrY2TI20RbjQyb35BLCoSaXUGL2F+5BalUFQoiI7QsrJQEfBCsgUAAAAGQzBPO5SVKBvYNologWVbhNIequDLajF70Sxe9k2MzFsW2GRD1JgVSI02A/qWyKi2DRt4LZLDLrZovyZVaswZUNKNJiMq8BKibMRNsrJYA2bLApcksbLVAvYljZsZC3tQIbQAqLs2MIvJOCLsoULZUDYwrDFmSCaC5G3KQf0MRaFk+oadWi7IqtkexE3ZlTaGzaJ+5W/YiVclfBAJQrceaCsktjF7FctiWE2J7EdFdJERdEVF2IRjRpkG2ier6Ectx8GlW4uiJoNkNDsUVcEYNo7KuCAG1S2LRHsLMjai9iLcypNGJtj9C0Nh4BsbJsykXINqAwty6NJRKp2ZMlEsVWE9yUGixNMm0Tkxa3KiGmSSojJbG7MjSojCQdmK6Ulsq3DGgRHRWtiUgm1Wy3D3BHyXZsr2Fi0PBAZOC2PINCKmrIhQNFshkqI9uC6BFIXgmzQL+oGxdqSMfGxkvqRjabE0+WE9wuNy0Jb9nh+c8WOSfqgpJnl67oPT9W5Slhim/oew2kqJtTs9cOTLH9pcJXPOsdhxc3PTefBrHVe1eoYItQg2l7I7Sl5MMmOE0/VBSv3NvDrLHhnwS/DgGfQajBBRyY3a+hK+T0ytM7drehaHVJt4opv6God1dpYsGklnwbV7G7xdXL8tfLgs+HOsj+Ck1/ob3+GnU8kdQsM8nqi/DNDzRk8zi3ai6dns9sal6XqeOUXs3uevLjM8NscLccncW01sLvZn4aDJHLpYSvlI+h8nD5Jq10sLvES3orVslstbHjKfCchfKi8EZbVRN3ZfNktf1F3u0xNruKt2ap+Imqyafpsljk1a8G1L0/azw+7ekT6noJQx/qo9+G6vl5cnmeHEfiyblOcvVJ+5+MW3P1Sk6R7HVe0OtaacpRxSlG+EjzJ9N6rgxVPR5G/sdni5OOxz8scts16pv1QlKkfvpeoa/Ty9GPNJI+N/mGHEl/A5d//AIn5fH1EZp5MMo/dGf8A12pO+PcXcXVcUl6dTJtfU+qPePUppwyNy2ptmt5dTBzX+FtFag4XCVtk7MN7lW5Za8x9us109Vlc3Hd8s+OTbntyz9MTSxUuSzWyqkzb45NPDK16XQNRPS6/FL1eUdu6Tleo6fDI+HFf7HCNAnLV4kt3aO5dubdIxJ/5V/scvr5I3entfd9zLhbksbcHFreUMli7RE0qfsWzFC9zI0ron1DVlYNiX1DVKgGTZtKFFXBiQtW3VE38l+xQC+oDJQEZCshaoACAADIZMhkiNbEqCpBuyLcpBC1aIVMsUoNOihsiAJZkgG5DIjAxd7kVtmVBcASg7QbDBKpbMU2ZVsKJ9yNMyRGIIkVEXJV7l2DsnDK0mTyJRWRl5A2bYpFaopKZBCrkqS8gug4Iyu2wQYlQZQBHQshdmmVL3CpMir3oOl5IL4sJuiMqpIAVMjl9CWBk+dhTIVMsEDe4ZGQ2VYYsLkyNr9x5Cqg1ZNmx8GJk+CVsUEmVx9xvZW9jEY0EhYtgHs9gg+AgKyLkpGBbIwKAKkZLkiXgcAHyRlKkqAidbMhWt7IwHJYkRVYBgNF2YVj/AFLf1LsRpCIWLAoy0aC2QX4Bo9VsMV7AlqquQ1uLZGyC0QrboWEQjsysxZdiFVshUxsKDKmRtkNiKTYUi2rtUiPd0ivj6hbKxN0nmol5KlW5LK9yrSkyUGE9yVBcl8hsWRNqmRqwvoN/AEoXSaLv5HPgu9G2KT8stJcoNEZdsp5LSuz5eq4Y59DkxtXcWfU6MXbi1V2jPDKy/LHLHccF69pHpeoZsdVcmfjoJS0+eE3bpnvfiLpMun6pLK4v0tmsx1LpKjucGXfx6c3klmTu3aeeOo6Rjny6PVramzRPwx1s8mm+FKVpI3pyjVJHK6nDVrd4LuMn8vG4XzKyJqtwr8Gm9qPmg3T9y8vYxd3XsZzz4S3w/HV6jFgh8TLNQS9zwdX3f07Bl9DyKVfU8L8T+oZsUFhxzcb22OZT+Lln/Mk2+TpdP00ym2ry8uq7tou4um6lL+9ir+p6WLV4Myfw8iaP55hk1mB3DI1X1Z6mj671PTKLjqH9j3y6GfqvKdRa7s4Rk/TKMXaPxnodLPaWGLf2RybS99dQxJPIvVX1PTxfiFnSUp4jyvSZ4s5zS10KXTtBNU9Njf8A/qv/AAfPm6B0rLKpaTHf2X/g0/B3+ppt4fT9T959/wCmS+SDlIxnFntneXHT2dX2d0jNJ/8ADxjflJL/ALHk6/sfpWKEpKfp/r/+jy9V+IOolfowV/U8Hqvc/UtemnJwj9Ge3Hw5y+XjlySx8/XulaXp+VrFm9VP3Z4ssrnL0Rjx7n6yyZM+RvLNyf1M8EHPOscIOUn7I6E/pPl4b3fh6Ha2nyajqmKKg5U1Z2/p+L4Olx438tRW39DTuwOhPTQjqs8KlKmrRvHpbW644ON1nL31u8GGvJW5k0q2JTTMlwc6tq+E5Q8By2JdkRCsthAL8Cq4BbFEAYAIjRaZLRdAl9C0hfsEQCy5C5EuQMJ+TFcGU+DFcBVAAAAGQzAVgxQSI+Ni+QBERrwVCm2WwEFbLQGjQ0guA0/JVtuQRvcMru/BHYEsWKvyKLBDJEa8l8bDRpK3MlwYvkql7kF4RLVhtMlqyw0tKyvgl0xaY0KuDF8l9SDtsQECLZ0yogUDLbwShsSl7jZcFaJtYC2wW0QugfIbQsjGjSAtMNOxo0nI28mVEoaNCD42FMUNGhciXIorRTSKyrkBIlAjexlTJvexBjT5BXaHJdCpbWA2EU0jFj7kJo0yvayMhRo0haC5LLZDRpiC15INGlsnkqQoaNG9FRi9ipOho0qDCXsW/qQSgyq/cjAEZUHuXYiMrIkWiCb+QBZdBt5DrwKBBH7lW4fAospD7h8CguaFpSK33K0vBGCKuy5I6sWg92ACe4SRVwBGHwAwjEyXBEqKA4DKg1ZaMaT3K/Fchkm1GLt7JGUm/BbrytNLfwR3tRrXW+7dJ09vGmpSXgnQe8ND1KXw9oy4PfHgumHqSVs9B1ZipKSUlw/Yu1+6PHPCys5lKje5UrElTJv4MPg+V2QQSC3IWKhRHa5Km3sAa82FyV8DlAQje5eAuSxYnC+o35exVS5D4MllaN+JujWXSfEULaXNHJsuzbSqnR/QHcOmjqunZIuN1FnDusYFg108bVVJ7HU6LPzpo9RP29/8POqPR62OOT2k/wD9HYsbjkgpLzufz90zM9NrMWXhJr/c7j25rI6vpOLKndRSZOt49TZwZa8PRYXBF7jzctjlXxG740yfKom11YbSlbumRxTdoyxlnlL5jnX4pad7ZYqzm8XNStvjwdr750P8T0zJJK2otnGZ4/TlnGTppv8A3O30Wc1pz+owYylLJtGPqDhJN2nGj6OmThHUx9auLludO0Xa3TupaDHnSSco7m5y80wa2GG3KorHLduzCfyq2/V9Dper/DzT1KWHIeVqfw/1XquGTY8Pe417Xgs+Gm4JOcd36U0ZRg1BtO6Nq0/YutcpeqTVGUOxte5Sj636WL1HHPJOHJqfrUofUeuUqj6b+xvmk7BlS+JP7nvdP7K6fgqU4JyJl1mMnhljwWub9J6Pq9dNRhgcYvzudB7X7Pw6OUc2dKUudzadH07S6OCjhxRSR9ar2SNDl6y34e+HBpjHHDHFRgqivBm1sNwtuDn5ZXK7bOM1B8kYspjfK72nAQfJCC0X7BSrkje9gUAMtAqogRBW35IXcnktoiMkTgWTQyJLkiLLkDCS8mK4M5cGC4CqAAAAMhlbMkzFlSsmk0LkbXRV9SOHsxfHlTYO/A2XlBO/Jhc4mxXY4CavwXZ8GXfDaNvmh6n5Q2rcn9Sd0+zcX1B2/Bjt7mSd+UO6G4JB7DYbPkndDwj38C9uC/LX/wCybe474bip2uCtOuDFJe5U/djul/Z4N6qiel+xXvww26HfIeD7Im5bpBc8j1IqUUrarkie+5e+CVuW/Abj9Amq5Q74L4BE/qT5b5J3QE2Wm+RdseeR3QKJyypq+Q6Q703EaFF28sfL7jvNwVht+xVSXP8AqRte47obgERte/8AqLj7juk/ZuLuET1R8v8A1Fprn/UerDZ9Qm6Kmqq0YtpLdoepDa2y+rbgiquUV/cd+P2bhdLcXvwHxu0E01yO/E3B2RPbcype6JVjvn2bY20ypsra+himnw0PU0bg5Mqqi0vdGLa4HqQ3AqZVQfpHqRdo3RYv1LciUfdGVx8NF74bYrloUPVH3HrjxY7jYky0L+wTHcm4JbF/oRS38BySL3Q2WOApJ8h+kxucNrZHwS4raw5K+UTvn2eGVktURv6hSinu0O+fZsstj1R90S4ray95uLuRqh6lezKpJ+R3m4RFWzFyinyiv0ve0LlPsli0PBG4y2sv0TLjlF3AJIJJB0X58ptdhX1IuA20y6CgkvuE/cP6DRs2CQYT2IAFiwAlsEGBLZeTF7BFhpW9mfH1dzj0/K8f6lFn1+dxmisuNwa2apmeHi7TKeHAOuZM2TqGVTbv1Pk+fS6jLpHCWGXpae9fc27v3t/Np9TLVYINxe7o0b1TUpLe+Gdzp+3Oac/l3jduw9k9z4tZgjp9RkSyVSs3GC2W5/O2g1eXQauOWMmq3Or9n91Q1uOOLPNKSpKzw6jptbsj04OXfy3Pl/Qq+hjCayQ9UWmmE35OTljq/Ddxu2Sf0CW4teA+LMdFux2L9yLdhrcaXSoq23MUZWmRKj3DrkOgDZaaJ5+hUkR8Ui2+FTIvVCUeU0cd/Ebpz02v+LFbNnY01e25pX4m9OlqOnSy443JI2+lz1lGvzY7jlcHKUUlwjp34X9SWXTS0spbpf8AY5Ulkg2r3XKNh7H6hLRdXxL1VGT3Ovz8fqcbTwy1k7dG6pPdH56vPjwYpTyNKMVdsunyLJijkW6aNZ/ErVZNP0b+7bTldtHFnHO7trf7vC6jvPQ4svwm01dXse90zXYNdgjlwyUov2P56nOeRuWSTtvZ2bv+HHWZ6fPHS5cjcW6Vm7emnZuR4zm86rqOvwLPpp427TVHDu5dE9L1fLFxai2/9zuylGeKMlxVnLvxP0zxaj4sY1Zh0mVxz0vLqxo9qEk1ymdj/DrVRz9HhD1XUUji0Mnqk01udG/CnW05aeTr2/Y3+rlyx21eLxXS6q14DjZa2Cdqjh5WyunJLE9KjGl5GOEeQVy8GPdftNDjF8BbKiJMP1JkttWTStVuEtw9ypGCjIk/BlsiUmXaWothRbphkPhiAAKluHyQq2AoI/cLjcCor4ImOXuAI3bK+CUAZC+BQBFIuS+AMZrYxXBm+DELKAAAADIZsiBkjEJcHhdX6ytLJwie5ktwlt4ND7jhklq5WtrPLlysjG1+2TuLK38tmMe4NQlR4tenky2S3OZeXNhbXsy6/nq7JDuDU+7PFat7GVNJUjC8uabr2H1/V+rdma69qa5PEbld0VN1wJy5m69iXXtSnyF1/UPyeNTk6K4elcF9TM3Xsf2h1Ce7L/aDUe54bi2+A4u6RPVzN17T6/qX7j+0OoXueOrWzCTb2L6uZuvZXX9R9Srr+oryeKk7orTTHq5m69n+0GoXuH3FqK8nhu2yqLYvLmbr2n3DqX5Yh3DqfqeN6GIRaY9XM3Xtf2i1H2J/aLUPhnjyox9NK0i+rmbr2v7QamStsi6/qLps8ZW9qMWmpcMnqZm6919fz+5Jdf1D4Z4jvyi02uGPUzN5PdXX863I+4dRd7nh06Mm21wT1MzeT2o9wZ2ZS7gz1yeAnRabMvVzhuvZfXtS1+p/uYrrupb/AFHk+nbkRi75J6uZuvZXX9SuWH3BqL5PHarkxf2Hq5m69mXXtRXP+oXXs68nizTa2Qqlwy+pmbr2X1zUN7P/AFD67qPc8dR+gcX4THqZm69lddz1+ok+uah8S/1PIcaXDMEt/I9TM3Xrx65rFLeTozXX9Te8n+540fUm9mVXf6Sd+a+XtPr2pa5MX1/U1yzx7k2WpPeh35puvWj17VeZMy/PdT7s8dqX+VhetLZMvfmbr2Jde1NbNmMevalO2zx2pJcBNt1Q9TOG6938/wA9ckXcGou2eK4tIiVoermbr3f7R52qujFde1F36jw2lfBl6VXBLy5m69p9e1D3UjH8/wBR7njNUjFRaHq5ruvdfcGoa8mP55qOfUzxk7VUVRktyetmbr2H1/Urywuv6lvds8hVV1ZG1zQ9bNN17L67qfLD65qa5/1PGlurIm35MvVzN17a67qPLE+v6lKrPHaaW5infgnq5m69bL1zU7bmH53qbuzzP1L7GKk+K4Hq5LuvYfW9S1+p/uYrrOpv9R5SdqnYUWne49XJLXrz61qV/iJHrep49R5St8mMou9kPVzN17L63qXtf+pH1rVLf1M8hS9OzQlNvhD1czdeq+s6lv8AUZLrmoUdpPY8VN+UZRX7C8uZuvXj1zU2t2e70XrC1Mljm6kaXbb2R6nbeKc9YnXDPXizytMbbW/Qa5D+pjj+WKv2MnZ1cPx8vWIhfsGVLYuj5GShQsaNJwVOgyEAFogFTRSLkMCNWZLYxKuSxYvI8MIF2l8+Hy6/S4dVp5YssfVarg5T3d2tl0GaefDByg96R15N3Xk/HV6bFqMUseWKkmvKNng57x158nHMo/nqMPU5LIqaT2Z+ui1GXTNTxS9LTtM3bvHtCeJz1GkjabtpGkZMc8U3jywcWtnZ2uLnx5ZNudnx3C7joHaPeSUo4NVLna2dA0urw6pRlimpJrwfz36nFr0bfVGx9sdyajpuWMcs3KH1Zr9R0ky8x7cPNZ8u02rryXg8LovcOj1uKLU16n9T2ozjJepNSs5PJw2N3HklZ+Q9yKx5PLVjLeyjNLYxQ9VMxCQQ8hA0DyOUR82WLEf6j5eraeOp0GTHJXcWfYzGa234ZnhbMmFm5pwPr+k/hOp5sdelOXJ8OD1Yc8M0XspJm9fib0v05/4nHHZvevuaTKDjiUfc+g6bPuw05vLj25bdl7K6nHWdMilK5Jbo/L8RcDz9An6I+qUU2aL+HvV5aHXrBll8knR1XVYoavQZMcl6o5IWjQ5eK48m3vx5bmn8+R3Ti+Uz9+n6mWl12PMtl6kfv3DpXoOtZMLVRbbR5+olJ0/C4Ojx2Zcenjn4yd77b1kNX0zFkT9XyqzX/wATNLHLoHlS4R5/4TdQnkxS0+Sd1skbN3pheXpE0lwmc3LG4cm21LLi4bD5Mrdbrk2fsPUuHWYJP0ps17PjePUzT8M9Ptmbx9WxSW1yX+50b/fi21J4yd3xtvFGXujJKj8dHP1aTE//AIo/Y4HJ4yrpYXwMemyvgibPK7Z1XxQJe5WIiLkoD4IDew+wZi9uC7NMgSxZNmkBlQoDEqIX+hdCPZmVhoi2KomXbwTYIlSrLlB8BkXJATdDyUICLkyfBPIb2AjMStmL4BFAAUABkMmyxbRKYaoxTbJS9zztf07FqW3Jbs9BFtWTKbmh4D7d08nyP7OYPLR732HB4Xp59Jp4f9ncC9h/Z/B7nubAe3n0dseL+QaeuTFdvYPc9ykTdse3n0drxF27gvkr7ewN8ntuwt+S+2hp4v8AZ/ThdvadO7PZTot+5Pb4/R2vDl2/p72a/wBSf2fwe6PdTVhvce3n0drw12/g9/8AcLt/BfKPcS25InvyPbz6O14n9n9PfP8AuF2/p65/3Pcb9mG/qPbw7Xh/2fwLksegac9v1fULgvt4unhy7e07XIXb2nSps9yyUPb4/Rp4i7e06fKM329p6u0ew1Qprhj2+P0mnifkGD3X+pV29g90e1uHfuPbQ08R9v4DJdv6euEeyk7LvY9tDTxX2/gb2SI+38FeD26fuKZPbz6O14b7fwXtQ/s/g+h7dJIX7D28+l7XiPoGBrYq7fwVye16q2oqY9vPpO14r6Bp65K+gaZb7HsuqI90PQn0dryH0LS14Eeg6az1jJIvoY/R2vHfQtM3uh+Q6W+Eew0gmlsPQx+jTxn0HTfQq6Dpq4TPYaRU0lVD0J9Gni/kOm9kWPQcF+D2aXsR1RfQn0drx30HA/CC6Fp096PYsOmPQn0dryH0LTPwjFdB0t8I9m/Ap2Y+hj9Ha8l9B0tb0Y/kOlrwew1sOFux6GP0aeN+QaZ+EX8h0yXB7CYv3L6GP0aeN+Qabyi/kOleyPXb+pU1Q9DH6NPH/INJ7Ir6BpK4PWQXJPQn0aeRHoOlqjGXb+lex7Qch7eHa8R9vaZqnX/8/oRdu6ZPwe23Y/qPb4na8X+z2An9nsC//n/6Pb83Ya35Ht8TteI+39OI9vaaz2273KmvA9vPo7Xhy7e0/uP7PYPc9yTsXsPbz6O14n9n8HuiLt/Be9HtpsN7j28O2PEfb2n+g/s9p65PcTYd+49vDtjxJdu6ZrkxXbuC6tHur7krfdj28NPFXb2nq9j7tB07DpN4xVn2vbZCr2ZceGS70SI3sFwWttyedjYniaXcX7gPglMgy2Y2Mdwy7Fa+oVeSK2HZBSMpGBCkKi/+m9C+o2K0C/LKUSVGLmopNtUMs1CEpeEjlvePduqw9RnptNKopntxcPc8s8+11CE4yb9LTRkrark4/wBF7t1uLUxWon8jZ1Lo3UMOv0kcmPIm2t0e3J02WM288eWZV9WTHGacJRUk+UzUu6u0sWshLNp4KM3vsbkrb9S8C1Pd8+x54c1w8M88JY/n/q/StR0zK45otJM+PaST4o7l13oOl6pB/FglKjnXcPZ+p0kpTwxcorg6fB1cs8tTk4vqNcxdQyaRxWHI7RuPb/eWTAow1UvUmaLmwzwZPRlg1X0Pzladq2j3vHhyR5S3F3rpXWtHrsacMqTa4s9SLuPqTs4B07qOq084yxZJRp/U2jpneurwOMMz9UVszR5Ojs22MOeTxXWE72fJdq3NV6X3fotRGLySUZNGwaXXabPi9cMqlfg0sunyx/T3nJL+31Nexi7umZRqULsnD92eNlny9prSK0VbloiMZ8irbkkntYa3G3LLLqprdeN3P06Ot0MvltpHF+rYcmn1mTHL5Um0kf0BOHri0uGjlP4mdGy4dStVhjcW96On0nLq6a3Uce40rBOePLDJF1JO2dn7H6vDqPSowck5wVP/AGOMJOMW5cHu9mdYl07qKXqaxzaTOhzYTLHcafHe26e9+K3S445rXRj96OdrKsmON+Tt/XsGLrfQMko1K4epfszhrwPTarLp8i3hKjHpfiysuSb8tq7C18dB1XHGT2m0jqvcU/X0SU1w4WcO02X+Gy4s65i0zrL6hHV9pRyepNuFP9kefUcVtXiy1HKtWvXq5pPaz7OgKup4l4Ul/ufFqE1qpuDu3yff298/V8cY8epX/oes/rxaT5ydv6Y09Bhr/Kj6mfPoIKGixL/4o/dOzg80/tXRw+FdEobijy34Z2idMtpkryQiMnRLZeUEgMXuZJMj5KrSClUioPgjLIgRlIyAvcrMUm9y0iwZWS15JQZTaXTLY29ieCbFsqSZFTKQA20RkAyTDC4IwI6IVkCgAAAAyGYKzFmKMkRbsiewRloi7IKmLC28Eu1HtwHuVkY8m0VlTYV3uVjVTbFt2WnQSSVl9T9hq/tdpXuVE5DjsNC7chESpCvqNABYZBW9iLngi22KqLo0NfQJstMnprll1/6BEXYj5GhkyX7ofNdi2NJobDdrZEbseBqqKytNksqY1QSaW5FbMm2RXVk8gARtDym1rbZB8BNFpDZs8FS2JaJf1Kp9y2vCJyGmkAoE3G9WBlWxLImi8mIjk75F2K+hVt4Mhi34YtGTkvYKq4Js2x39ypsu3sFQ1sHuHwVsx3Hg2Iq3MeCppsbibXbwFQaVBJDZtIumVyLe9GNKyqqdkbsy2FIDBfUyasjMl9QMaY9P1MmtiImgsie5VsXZjQxbfgiexa3K0kNUShuEW1VUPAlF3HkNOh4De6sGO9mW9F0bFtyW2tzFptlt8EsTTLZsxfOxUqI+SQHwRsPkJJGRpN/IT3MmNvBiMShoUwKRlQYGLMoikSgv6ZWiXbCpDYs8Esflq4SyaeUY7WnucP720WXB1qcpRfpbe53Srts1rvDoGPqekk4RXxEvBudPyzGxr8uG5dOLZGppenlGz9n9xz6bOGOU36G6Z4PVNFn6fnnhyRcUvLPkjth9X7Hdsx5ONz7bhX9DdM12HW6aOXDNSi1bo+t0laX9TivaXdGfpmWMMkv7p8o6v0fq2n6hgjkwZFL1Lg43N0urtvcPL3fL0vSpW+D8suOOVOGSKlFn6JUt3ZXK9qs07vG+GzJK1jrvZ+j10JTxRjGT4Oe9Y7U13T3KUYOUV7HaOP07GGXHDNFwyRUk15Pfi6rKV458Mr+epueNSg8bjJe6o/NSmobrc7T1ftbp2shL04oxm/KNL6t2RqcFyw3KPNHT4url+WrlwX9NK+NkjjtScWmj0unde12lnH0Zm4rxZ+er6PrsPqjkxtR+x8X8NmhOlja/obF5OPKPHWWNdZ7O7pXUFHDmfzLY3SLTimco/DrpuV6yOacGkqZ1WOySS8HH6nt3dN/its8siUUM0nvIlF38hvcjqiVR3do83uDp0eodOyYnFOTWx6d2qI1tV87GfHncMtpZuOA9X0E9Frp6fMvSlJ0zzV6ou4u2mdc797cj1DBLPhjWWCvY5Q8c9PqMmPNBxcdju8HPM8dVzeTjsrc+x+5XH/gtU/lapX9qPH746d/CdXlqcVOGZuUWjxYT2jKPyyT5R9ev6jqNXihizyv4apNnvOPVljyuX28/JBzxyvake10/rc8XQ5aP1NtWl+54WeckqTuxg4d7Ns2MsZZ5eUysrOOeXqfu/c2TsDSSz9VjJq0nexr0MHxJqKVtnVvw36R/DaRZpxXqaNHqs5jjqNniltbpjiljjFcJUZpNcE2DbOFyXd26WM1Cyp+5EVLc8pVoEr4CMnxQEZjxuV35Fl2I+bRkt1yRcBWQPIHgtbAYtUVLfcO7CTW4Dgl72GPBkIUgMRaDSL6gwIisWAJTDWxbVh8AQhaIAZCsgUAAAAGQzkjEyRGYypoXFFWxFyV7GcqpL2CC5DJam1CQVstUybEZLMmYvdjZsVlv3IN6oU2rVgn0FOiaNqwSggbUiVb2UA2xabMlFpE3TMnfuDaW7rwZWq3IuLF3yZKbeCN0Bv4AJt8h7l3I0wmk4G/IGzJs2qW4G4Ls2rMXZXySibNo23tQVloleBs2FIL3IuwqQSKXZaeAANoeojKGhaMUtzJGJkuBsV0QWTchtaTe4JuNy7NrfuRF/qR8imx8hPayGRDaX7loEthdjSFPwxRUtgbRK2Gr3Rk9rIgm0FmTS8E9INo027F0i+S0vINsU7GyKwtwbABQChyC8A2lVyKK6INGxqy+CBvYaNjqy0QSui7D6FWysiVclQ2I78EppmVoje+w0L8tbilwYrnkr5IFJDbwH7EoC34MXbexkHsBLHkclTYDd8jyG7C5sVZ8HjgVsG9gEFHzZElbvgO6oK/S0ZyrfLUu8+2IdV08p4YpTXsjlPU+n6rpzliz42knSP6Cqo0+PJ4vcXb+l6lhknBeqtmb/T9X2+Gry8Xc4NJeicZbuLPa6L1jVdJyxngyOUW/0n29xdt6np8n6IOUfGxrc24P0zi4tM6M5MeSeWpMcsK7P2v3dpepQjizSUJ+b9zaYyhNXBqUX5R/Oul1WfT5FPE3a3tG39vd5arTemOeXqivc1OXpL8xscfNZ4rriq2T56vwa90ruzQavEm5KMnzue5p9Tp8yU8eRST8WaGfBlh+mzOSV+yil865E16lurT9x5+jL49J4d2UrPW3z5+n6TPGsmDG39j4J9vdMl//AIyv7L/wetVMbXwZzks/bG4R82k0Om0kUsOP0n0tqkGrd+xGmmS52spJGTCMfUWzFR82VJUR2R2BklTMXH1fQy8UNlt5MU2xlFNNNepM03vLtLFr8cs+kiseRbte5uislVe1nvxctwrHPHuj+fNf0/VaLK8WfE41w1sj5YVKUvXJJeDu3V+haTXpvJjTk/ZGqdT7Dxzi/gr0+x1+HrpJ5aOfT2Vy93LI/ZGSUZZFGD+Zm9w7Bzpterc9fovYmHTzWTPH1Ne56ZddKwnT+Wv9kdtZ9Vq458yrGnZ1rTYMWnxqGNJJKtjDRaTFpMax4sail7H7rZOzldRz99bnHxdq+PqElZik0tix9mafy2PhXSew5HpCRESioBbchWTexg+SsWERFjyAi/IrX+pKryVPwR0NBvfIIKIK+DErFqgIAAKkULgj5AMq4Ii3sAlVcGKK7ZaAeLMTIjAjIVkL+lAAQAAZD9EGRAx0iblttALYuzYtgivgnggsWVmKpmQGJKMqFAYpWZLYULRkIwi7MjMQI0VDwBEGHyEAXJboBF2K+CAJblNj5LZGkFVA2Oy+CPkNk8mx8k4Yt+ScjYyvyGFwWiCAAARe5a8Bl0I2x5KPBDYE3wHwF7hTyAuSsu0Y00LLJkSsgNUTezLYARclZHyUAxYYr3AlloGPksIoL4CpkKljkrAigvcEYTwre+wInuBs0qe+5bMeRQ2aWyNsqDAiLdEVooC7DbS2Igi6NK9laD4FbURjSqgRFQ2isbKO5i2GQ0vBbMDLyAbC3BWkKaRrYx/oZN2ybLwBAZWvYVZdEiIoqh4GjQGtiULd0NGhFMSrchVC34AFItEfIsPgbBkvehZVvyXWgT8PgfLewe/BGmizxdl+H46vR6fUwccuNST9zR+5+ysGZSz6WPzexv29UR7t2tj3x57jXnlh3P5/1/TNVodQ4ZsTjG/Y+PO0pJVR3jq3RtJr4P144+r3aNM652PJXk0+/mkdLh6ua1WrnwWOcxy5cNLFOUb9jYe1+va7T62GN5JSjaW7Pw1/b+v07t4W6+h9HbnSNZl10fXgcYp80enLy4ZxjhhlK7H0zO9TpYZJctH1NbHy9Lwfw+khDykfU3a2ONy634b2Hx5HG0R0kW6JyjzsZVd/BG7Lb9g9zE0iQZVsAbG9guAluXxyAS2JW4fBEBXZK9zKiJJAn2nLI3sXyFyZy2LrfynjgKPuZPYfYd1rHtFtb8DxY8EMbdqK/BVZiuTJFWwT33C9w1tsFwYoXuGxRGBVQa32C4FWgImy2AWC0KICBdFtEe4sB4snLLZFyAYRSIC+AuB/QX9AJQVobl3oAt9w1TC2D5Aq4MWZLgkgMWQsuCFsUABAABkMwWiMm0AAQEGnQvfYDRsV3ZSET3GlZNBCyBNslVGL5CotBRUHyE0KCIPBkSgMCoUVJgCWUlFgrSollVhkEW48hFAib8iyGSAWAwAYAAAAACWUsEv3FlZiKaVkMohomzQgFsOCwAHtsFwQSisAAgAAJZUGvYGgj5C9i0U0lFXBaZOCqqVhqiN0L2MU0eSMo5BpFyGV2P6F8KidF9Vlr6E/oXwnhFyXYCrY3FGSisUNw8C4FADcBolFW6FP3JdCUWvqKDIhdbhsiDVDarwPuShZknhXuEBwTUVHyQq3ZSguAuQwlRNiydkRGtxRdjJNUY7WXwRX4GyDCDrwNvcm4Ktw9iX7MOyeBbFhk2E0lQq2AXBdEiGVNIxdhOxdxdMm9iWTlGXCIWaEl5J5qgyt2jLeieX459Nhyr58UZf0McWl0+JXDFGP2R9C4I0i99jG4+VXAX+pEy+TC21lrUZKKfJOAmR7mSFlRikioxBi6YABclogssFdeSWvACSGxbRBwxRRGVKyOipmJsaJRbJZabFyUJ7DYhtHyVPyR2w7Rd6WVWwuCUKIDYQoIIoTARdCsgsPgkEtkKisAOQAFE4ZlZGtrAAlh2wKS2LY8AVBhcElyWhexVuAthQZGZ8mLqyKxZCyIX5AAEAAGQ/RblIUxRJGLTMmSyw0xMlwHQKo9yUVNVuLRNCJe5U0ti2uCV5KK15F06Md7L9TFBqwky+NxwXRspiXAbYY0IirjchGQW9xdongpYCRGi8BkDgMjDVgEUbGSAlEaMiNgQMeAwIwmwUACMqsuw8jgPkMpURXa3K+AmqMdG0pcl5DpkLAfuSmW/cEEov0BHuwFhchIr4L8hygrXLInuj8Nbq4aTE5ZNvYwyy1C19FeWyto1ufckE3S2Pz/tNC/wBLPD3MibbPvyVuzWF3LCtkP7TRv9I91DubMLNWn3Mo/wCEi7oj/lJ7rE22oXTNV/tOr3QfcyfCHucU22psJ/U1NdzRcqaZnLuWK4THucV22lNcF/qao+5opXQXdEWroe5xNtp8lbVmrLuZXwSXc6uqHucTbaWVbGq/2mVcF/tNH2HucTbaXu7I39DWY9zRe/pI+543XpLOqidzaLrgJ/U1Z9zW9kzJdyxS4ZPdQ7mzsjTZrH9po1wYruiKdVRPdYm42lR+o4NWXcsb8mT7nh7Ms6qG42h3XJE6NaXc0GH3LBcIvucfs22VshrUu5YtcGC7oinTQ91iu20Lbgyt8GsruWD4iY/2lXsPdw7mzv3Km6NY/tLD2D7mhWyYvVQ22dvfYOvc1X+0sfqVdyw9mPdQ22jZeSqvBq67kx+zI+5op7Jj3UJk2h0RJWa1/aWHsyvuXGnwx7qHc2XYceTWn3JjvyY/2mx+zJ7nE7mzvkf0NYfc0KtxLDubG1fpE6mfZ3NncW0Sma0+58dbRPzfc8br0j3Un7TubUqoVE1/SdwY8s1FqrPcw5FlgpR3s9ePmma7fp5BOOS2e662WCbBP2BrXwIX7hclZPlWJVVWKFDekpYYRCCpOioiMkBA+CvgxYIIPdALncAivZBrbYKwHjclle6IBGCojChkuCJ7UwuaLUVcmTSaIqD4GxL3oNsInJBlaqyJ2K2IotcFhFZFyUFKLYPkqS5ZHyYgW0CNOwD2ZGUeQCew8AJ7UAACLsG6e4UrDTIk7IK6AY8AER7l5I+SwKfJUBTvYgyRjK7sNUV8AYOq3IiyqjFBVAAAAGQzKuCJbF/qYoNfQlFbJ52AC1dAj5Arfigmlyg2GWLFdPwTgqJ53LUonewt8ItKrI3XgxBt1uPAQAN7C9gK2AK7JIpG9wKBZEwDe5UR7jcCoMjbMktgMUrLQRdwIuQV87GMW22AuyikKAIDgPgCMt+SWPABuwvcrTCTRaVatWKJZUQQIt+GT7AGt7Iyt3wFXkyE3IZURmIIPkpFwBX5aNV7ylnpK2om0pq9z5ep6DFrsfplyYcmO4WOcppJJsSW5suftmfruD2D7bzemrOdnw5WvOxrS3DSZsH9m898h9uZ/Bh6GR21rz2VMzgoNHu/2b1DdNmcO2syX6h6GRqtclBXaKoI2N9t5ktnuYR7c1HuT0MjVa+/SyNI2Zds5Ursxl23mfDHo5mq1ppVVBxSWyNj/sxqG+SvtnNW8h6GZqtajXlGW13RsS7WzXfqMv7L5/MiehmarWpfQicXybNLtjNW0jFdsZ1vY9vmarXU0lVGNWzZf7M5mrtE/s1nS5RfQzTTXYp3uZOMWuT332zn/wAxlHtrPXJfRzXTW0mvqi3HitzZf7M5ktpGK7ZzJ+49DI1Wt2r/AE0Scd/Y2WfbWWy/2Zy1+ont8yytZWzMp0kqNi/sxmT5Mv7MZXH9RPb5mq1uL23RHD5jZ4drz49RX2vk/wAxZwZmq1hKuA1b3Zsc+2MviRF2xnr9Q9DM7a130pEe3Bske2s6e7LPtjN4kWcGZ21rbjFq7IqSNj/s1mr9RlHtnM1ux6GR21rKXq8l9FeTZF2zm8Mv9mM3+eh6GZ21rbTq7oNLZt2bIu2MrX8wyfbGRL+Z/oPQyO2tZUE5bJhRe6SNlh21mTdy2Ku3Mrb+Ye3zp21rcor0/pMXGvFGyvtvM/8AEWXbWR1ch7fOHbWsVT3MX+rg2l9sS59Zh/ZbJ4mS9Pmdta7pvWp2nVG99sZG9GlJ2ebpu2nGVykbBoNNDR4vhpWbXBxXH5ZSV9EqEVZGEb+2ZTKRNlIlL+g3JbKk/AEsPgtJsyaVAYqqC4JwVMCJbmXgn1LYEbJRbABfUAGRF8DwQEocB7gEAcoPgiLQfJUAQVcCib+C7+UBF5KmqI0FsAaFFVsoGLHI8jhgWxa8ooAbeCNtcCyPkuhLLYBAjuJAeAJbCZeRYCy78BB7b2XYO3uQyv6kGw8bk2LSIkr5IHmx5ALoOTIxvctkGMjBGbMQoAAIwUF0umYf0F7lZWKf0C4JTKuCaBEfJQ9nbIBfBEN+DJYUA0+RV7sJafRCmvIS3LKuLJoPBAmHRAAFAEgluK+pPIFa32CQbpBNVsBWvYgdslsCgeAA4F2tglb3KlQBKnbCVPYNuiJ7DRskvJEVuuRd8ALD4DQAi5KglT3K68F2IxYD3FBhOiJl5IIt2HyZUyPYBQolCjJTzuVk5ZfSYongiMq8ErcBTsr22oEavcuyK9vAvYxsyTtCyKJqw91dmJa8jUFe+1k4ZVxuGNQmkfJUl4Ye4Q1A+bhrYBKwLIaE3dEZVd7BtjUTRVbke5G2+AO2GlWy3bLs1yw/sLaWyHbDRXhIlfQtol+41DQvcyXBEl7DgmjQ1JBNrkMxHj6JGUuOSXtRDJNeSyQsFxuyNr3CYbHhVX0ZLt8i0VNVY1Aarhk3otle5NQYpt+DL1bcC6VEQ1DRYbaDoJF1AthttbkoqW41AWyCl4JJIRoaieV3r6Evbgre5jTTGoqpu6ZW0ShQuMFk2t1uE7e7CarcOmNRNI9t07Lbkt9gl7skkNQi8jYiFCihEsyXBBjXuUN1sEA3sFsXsBHwRFe49O/IEvcMr2IrYEG3kq5KBEyoxM0X4ELWxPO5k1XBBKDQp0KfgCPYi5K0yUBW99gFwOQKnQbC5MtgMLDK6MXyBbKiJFfAEKyFYCxYS2IwDCRCvgtUr2Fk4FkRQSx5AtBpURvwFbQBNjkvAoAL2FEa2AJjkLdBbgEVN2KHiiwGibpclD4IMWQMBQAAAAZDNIydUYscBEZUrKki7eCbEdrwT7lIxsFsPVuANmxyYVALkgrSrYlF9QtATwKRbRG0BEVOieSqvIAB7DyAIuSvknkCkRUw2uAG1bAET8AZKw2xbIwKm6oj2KnSoiu9wDYXIIwK2Swy0BiVBhAUChQDZ8gFXA0JZG2ytEYETMr2MQBkPU6omxdvIEthWy0qIwq7eS/KSgi1FaRHGjLaiN7kEqlYDYLoW9iEZV9SBwCvgi5LKFgrSJRTYvqV1RADZYoJ7blsm1GSgwNpsolFD4GzaJsyXBCrgbNjJRWyENpTFF4DdgtGqDQtMPcCVaKo1uW9iN+C7XaMqdDbyKSID3JW5Qk1wXabGgW0+SP6FAFoV7k2bR78j0h0VOhs2goNqwNmwMWi7DZtEr5JXsVgbNjVoi4D9yooAMGItDdBFLRi92RMr+gQ+RGy3tZGVcEAfYnP2MktyygzGzNoxa3HgTnkoBBEi8B7bAAxZNrH2AtyKm6ZIlb3oCWS3ZWTyBRQsAG2FYRkBEvcUGTguhk9hyY8l3RAonBbDewDccinRAK6DIuQ+TIEGioMxEACoByOAg+bALncqI9ggHkJ7E8j6gZJbEW3A8EQFYAAB8APgDB8gsuCFqgAIAAMh+rqtjEF2MUTcMcAAvqGVUyMGxkoyojGhOBZWYgVK+SuiIoBLYbGLe+xQKwqoitlv3ArRAADMTJkrcB4FEewTdAW2K2I7LYBFIluUDEtlJQFHJK2CAr2JZWSgCKEGAsWCLkChWAgDaFkfIrawKRhpjgBsKCLQEQbFoOn4ARdothIx88gVlJRQI3Q5LLYLgCUV0kA+C0PBLCIQWxZa2FARchIoYB80F7ETvcpkC9hfsRkJ4FsWWvcj2ZBQSgwLYQpUPSBJcBLYrQQBWC3sRgGY8lYXG5YRVvyV8GL5KltuQtOCWVpijILK+CUGTYjsJvyVgURiyFRA5ZdqIxyBVQshAMlwHwQhdioIIvkgeANvcWAX0D2Im7K+QIisiDL/wCCkW5UKFgcC3W48h8EBthGJbApAuQ37AVPyLIAKRKxbKmA4EkA2AAQAjFmSSqyMAgLDdgWyN7jgMfKouTLci2MrQ0iURp2V7cEfJdCrgjTsyIxoRGRiZEEboglyFwBGXkj5CAIoa8kYFq2CWEBa8gi5Mk9gIvqTyZbEYGJU6CW5aLIBGNw+SCMhWQKAAAADIZbsqAJpAAFAIj2dmWyJ5CyMidlHkALC3IAS3D4Jb8AWvI2FhqwLsR0EhICXuLK+CLgBfkWVFaAwavcyQAAllsMACWWwAJZUAZFyWrYQEfJWLACw2E62DAhDJ8AAg9txdC7AWSy0GtgFi9iUGBaTHpSIi+AG3knDKyboDLwY7ltj+gE3uyk3CAeTJJBcFAcmLWxkC7GK25DSD52F/QgAeQ3sALRjuVMA1vYW4JYFa3MeDJNkdgX7ERdhYBOhae1EplABckfJVsAYVmSaojAxor4oqaYlwXQxoLgthcFAUAmYgCN2VAS2ZU2QPYAKCb8C2AoJbWRtlvYA+AuAnaoWA5RGWyN7AEguSADJVyAgBfSnvZGtti3uLtUBFvuEthZbdARblogaYDgJqxwOQA4F0OQFkfBUkGl4AxLRUL8AF7BkZQJ5LVIf1DAMCxdoBQDACwSyougACTRAotBB8Fgj2ZLfgtB8D5ADyCBYAAAl+xVwBGE6K3uHwAr3BVdEafIB7EvyKfkUBCvii0RAFyXki5L4AMxLY8gUMB8ATkhkuAwMWQrIFAAAABkMwAEARMr4MRGVERAMkGEGAQ8bFsj9gCpLcliioBuFYfAQBivIYANWANwJ5FlX1D55YBjcefI4ACXA38BgTwFyEi0AsCgA82PNAjW4FCIyAW/craIKYBhWgisAENyUBWAR8gLF2qZXVEpeAC2K+Al7jyBGvJUA+KAE3KthbQBL6kZXbYQGJUyotASy34JVCwAI7qyoAwR0EBQgKV7AGtwW9jF2BWTdlAE2La8InLFAVEfIrct+AJReB5Dd7F0HjYjb8h8BckFWxG7D5IXZtUUnAIKKALoRoLkJ7iXJBQESwLRHfgWEBU/BGVhbgRcUR7GXkeQMQWvYPkCAFXABFfBj5Mr2AJhEoeQMpOxaomxXwBG97LZGgAfJfBGS2BaslVwLfgWBePJFdhlXAEYKw/cAE/qAgK3tyR7hsICUOCtu7I+AKgE9gwI9irgF8UwILYaRW1QETYk9jEtFhRKyiLoNkEfJSMr4AjFEKmBVsXZ8ESVlLRiysN0BA9QTI+AiCuwAA38it7DuwrAtEK15IwJyKCW5QIi2Rl+oChZEGgIyFZAoAAAAMhmADFESst1sgRcgP6BclfBFsBWiU/JXYQBWAwtuQAXIvwGAb2J5IZPgAguSUVoAwB5AIN77BtJEQFbFBkoChMlEAydkRb8E+4FFWwRAVgWRsAxRVvyPIAAMASmVJhcgHdBJ1uV8ckVgRchl8h1QEX3LVGPHBU2BeR6Q03wN/ICh5MSoAuS3SHkjaAqD5AAlCwwuQG5QzECsIhkuADX0FKgg+QIyqq3DJwwKwxZGA+rDCVlqkBEtyhhJsByHQbrYnkB5FlXG5H9ADCKuCcMC0AuCMCvgiQRS6AiDKq8EAj5KRgFZWiIrewCqQryTeygGRbMqarcjAvkBACPkIMVvQFolGVDgCGLW5k2YgCrmgiNO9gLSKyJWVpgRpIq4IigTyGqCuxv5ABchBgUjBAMk/BNyrgtbAYf0KmX0r2FATzsZPgg8gG9ibrkyXBGBHYRQlQChdoABRKKAJ5KPBHyBSN7lQAj4oeC+AwIkGg2UAlsB9ETyA5KlsThlT2ArTRA/qPSBGtiGTJYF3QVj1L2FgHwRXfJVuVrYCNMBMATcvgBbAAwR8gRkKyBQAAAAZDNIydUYoOzFAeSXsEWivgIjCIKPAQoATkN7hAWlRHyGQCoMMgFRWzEqAWUMeQIwUUAXBLdlYQEZDJ1QAlD6lFgRBlXAsCPgUXlEYE38GSIuSgEgLACwGmQC+R4CACWxiVb8h8AG9ggivgAGyWVbgQV/Qq8gCIMNBb8gFbHHJWR8gVEYRQBEG2QCsWCoAuCPkoAiscsyfBiuQLQor4MWwG43ZU/Ab80BGVWPUPUBN2Ut+xjuBWK8ERQJwytbEvey3sAI+S3sRgVDciMlwBBQYAEKP6AShRU2RtgVPYgXJQIx4KAIPsV8GIFCdMBcgVN0RstqhsAStWyNblSDVIA+dhboi2ViwCth2LIBVZVugYgZAKwAIyhgKMTIlIBuiojKtgCDK0TwADBHyBeUPA4F0BFdlYTRG7AqI+QgwKgYlsuxWEYtl8bkF2BiXcCr6hu9xuRbANi2R8kAyXBFsygCbMNUVxFKtwH2G/uSvYtNgI7l4MVyV7AV0Sk97JYXIFe3AW6sB7ACPgqIwKuAYpFApGVEYGL5BWQKAAAADIZoOxfuLMURFX0IigStwyhgSkUJMACPgq2KwMCrkUOGBQ1ZEytoCUEGy8gOAmgkiUBW0QUGBCoq4AAJIjVlQBq+CPkWQADJcBoCIebK+CUXYUPoLoWNgwqDdlRA9RG7FINbAQyJ9RewFWzIxYALbdhhFoAtxwRKnyUBQ4BGAbIVcWGnQBhNBEAraoIqjSsV5AWFwSiAZEdoWFyApsO0UcgLA4DAi3D5CI7sC2X1GIsDKyNlXASAlew4RR9AI5EMthQGJRW5QI+dxWw8lAKqDLTFAR8BcAiArJZSNgLHkIvAE5KuATyBRZGwgHIopGBCqqIWwBCkAtltsxMlwBHfkhkRgEVkSYYBWGEW/YBYsJEYBvYq4IirZARlFk55AcspGUCpryR8gAUjoyMWtwJZVdAt7UBgVFS2AAjDIAMkRboq4Aj5IVFYAll8EQFQJQdoCvgir2H3MktgMXyWw1uR8AX1bkbsfYPkCrgWRBAVJk34KtycsBW9lfAJYBDfkIoBE8lYWwBNNDgBgL9iPiionkCMhWQKAAAADIZt7k5KKMURclexOAwKgieS+ACDCAE5exVfkidFv2APYKmE0HtwgLZi7KuABK2L4qgK2sCUUMgC0FsgisAqJ5CC5Ar4JyUJrgEieCFYTRdLpDJcEaRVwNJYm6KArew0F+4ZGErGg2fAVFolJEFHmhZPICtyoiKwBNhZXwBEVgjANeSgATghkzEDJcB/QiKBLLQoPgA2wF7AARKyhATyWieS+AJZUKI+aAt7gOkAFeSIpEgLZjyVogFtIt7GJkuAWCJsWqFqrLoNr2FgEBB7AjAq4C52I9+CxLsGwmw9xRDSvbYceCO7oUZGi1Y5FbEaJ+wf0KtwgyCW/AoqqiWBSKhyVewDwGCOwIVEKgKiPktUiPkB5KR2y8LcA0T7l3CAm9DcoAcgBAYmSDRNwKGK9wBEGUMBdqgYv6FTMjShitiImzSkb3KGQLC4slItUuS6NHgMPixaaGgfFmJW9gmiCsngqIwKuCMq+gAL2AryGAA5InYFfATIwgD5FloUAACAlgoAhQACZKKkGBELaKgA5HgrIBHsykZfAB8GJb3sMCMhWQKAAAADIZpIPkuy8k2Zii19SOgqKkgJRLMqJtYAMPYATzwWkFV8P8AcroCV9RQ2GwAFoj5AAAAKD5Kq8gY7ItlqL4JsgCWxP6GVobAYy4JuZWKLCVFvsytLwPTYUSrtCrYi+xXb4QNwb8BhX5LUfJibiNuwvqPlsP0pl0g15IUWNDFJh2Zb+4ZGW4xSaZfJPTJMyVpmRbCl5FKtitWrJ6duTFiB0K92GkAA4FpAAwxQERVwFVC14CjA2syVUEYgPkqryBAmhaMk0gMSsr5slgRchpMth15AgYYAjKiMA0v3HBGmH6mZLuIVMUUxTY2T+hlaJ9jICrggJoGR8lQfJQsjLRK9jEircboUxv5Ltdor8mX2J/QKxstHdDhFYoVED3LQsgxotMtoNgTgDlgAk/BGZpojaAi3JTMrQsCEbaMk1YfpYEsloy2I0gCYQSS5LUWBCWWkKQEYRQZCPkq4KgBPsHtuPsVGIx8l8lfJGmX9CN0VrYOMrDUkiKelj0sx39ypMyP/wBUi5K0yKL5MTcOBbFMrUkWG4juh/hDUmhUiruIi78Dei0yaS1EXYb+QRFXBGzJNUR0BGYmdEewABhUAoItEYAbEtiy6NK6CIhwyGloAWvJdLpLHJZNEtFNFiyWWiaNLF2AtgnuU0O7HgAmk0hfBCohWIMqsjVARkKyBQAAAABTIAyQAAAAARhAAUAAAAAAAAAAAAFRFABEXJXwAEnwxKuQAn7EVgBReSoACklyABERgAUAAAAAAAAAACMACAACsIACFXIAFAAAjAAiMlwABPIfIAB8hgAQAAZPkAAWXIQAEAASBEAFUAAAAFCIAJVAAGQAC1i+QuQCfoDEAVIAAirHkPkAEPBACxKyAAgAACMgAWKyoAftP0j5IARQyACUIwC0iFjyARTyZoAyFfggBin6YrkyALRGFwAUUjAMSHgewBap4HkAgwABkiooBP2BJcgEIhVyAZEUjAJSJLkyQBVVcFAAwXJAAyHwRcgAFyUAAAAAADE8gADIPgAIxZAAUAAVGAAP/9k=');"></div>
    <div class="header-content">
        <div class="header-title">晴女☀️在場邊等妳🌈</div>
        <div class="header-sub">✨ Keep Playing, Keep Shining ✨</div>
        <div class="info-pill">📍 朱崙公園 &nbsp;|&nbsp; 🕒 19:00</div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.is_admin:
    st.markdown('<div style="text-align:center"><span class="admin-badge">⚙️ 管理員模式</span></div>', unsafe_allow_html=True)

if not check_db_connection():
    st.markdown('<div class="db-status-err">❌ 資料庫連線異常，請重新整理或聯絡管理員</div>', unsafe_allow_html=True)
    st.stop()

st.session_state.data = load_data()

# ── 請假 & 公報 ──
col_leave, col_board = st.columns(2)
with col_leave:
    with st.expander("🏖️ 我要請假 (長假登記)"):
        with st.form("leave_form", clear_on_submit=True):
            leave_name  = st.text_input("姓名")
            leave_month = st.date_input("請假月份")
            if st.form_submit_button("送出假單") and leave_name:
                data      = load_data()
                month_str = leave_month.strftime("%Y-%m")
                data["leaves"].setdefault(leave_name, [])
                if month_str not in data["leaves"][leave_name]:
                    data["leaves"][leave_name].append(month_str)
                    save_data(data); build_stats.clear()
                    st.toast("✅ 已登記"); time.sleep(1); st.rerun()

with col_board:
    with st.expander("📜 休假公報", expanded=False):
        leaves = st.session_state.data.get("leaves", {})
        merged: dict[str, set] = {}; display_map: dict[str, str] = {}
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
                                        if not data["leaves"][k]: del data["leaves"][k]
                                save_data(data); build_stats.clear()
                                st.toast(f"🗑️ 移除 {m}"); time.sleep(0.5); st.rerun()
                        st.divider()
                        if st.button("🚨 強制刪除", key=f"f_dl_{key}", type="secondary"):
                            data = load_data()
                            for k in list(data["leaves"].keys()):
                                if normalize_name(k) == key: del data["leaves"][k]
                            save_data(data); build_stats.clear()
                            st.toast("🗑️ 強制移除"); time.sleep(0.5); st.rerun()
        else:
            st.info("目前無人請假")

# ── 場次 ──
all_dates     = sorted(st.session_state.data["sessions"].keys())
visible_dates = [d for d in all_dates if d not in st.session_state.data.get("hidden", [])]
rained_out    = set(st.session_state.data.get("rained_out", []))

BASKETBALL_ANIM = """
<!DOCTYPE html>
<html>
<head>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:transparent;overflow:hidden;font-family:'Noto Sans TC',sans-serif;}
#scene{position:relative;width:100%;height:280px;overflow:hidden;}
canvas{position:absolute;top:0;left:0;width:100%;height:100%;}
#msg{position:absolute;bottom:20px;left:50%;transform:translateX(-50%) scale(0);
  font-size:22px;font-weight:700;color:#1e293b;white-space:nowrap;
  transition:transform 0.4s cubic-bezier(0.34,1.56,0.64,1), opacity 0.4s;
  opacity:0;}
#msg.show{transform:translateX(-50%) scale(1);opacity:1;}
</style>
</head>
<body>
<div id="scene">
  <canvas id="c"></canvas>
  <div id="msg">🎉 報名成功！</div>
</div>
<script>
var canvas = document.getElementById('c');
var ctx    = canvas.getContext('2d');
var msg    = document.getElementById('msg');
var W, H;

function resize() {
  W = canvas.width  = canvas.offsetWidth;
  H = canvas.height = canvas.offsetHeight;
}
resize();

// ─ hoop geometry ─
var hoopX, hoopY, hoopR = 28;
function setHoop() {
  hoopX = W * 0.72;
  hoopY = H * 0.30;
}
setHoop();

// ─ confetti pool ─
var confetti = [];
var COLORS = ['#f97316','#3b82f6','#22c55e','#ec4899','#eab308','#8b5cf6','#ef4444'];
function spawnConfetti() {
  for (var i = 0; i < 60; i++) {
    confetti.push({
      x: hoopX, y: hoopY,
      vx: (Math.random() - 0.5) * 14,
      vy: (Math.random() - 2.5) * 8,
      w: 5 + Math.random() * 6,
      h: 3 + Math.random() * 4,
      rot: Math.random() * Math.PI * 2,
      rspd: (Math.random() - 0.5) * 0.3,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      life: 1.0,
      decay: 0.012 + Math.random() * 0.01
    });
  }
}

// ─ easing ─
function easeInOut(t) { return t < 0.5 ? 2*t*t : -1+(4-2*t)*t; }
function easeOutBounce(t) {
  if (t < 1/2.75) return 7.5625*t*t;
  if (t < 2/2.75) { t -= 1.5/2.75; return 7.5625*t*t+0.75; }
  if (t < 2.5/2.75) { t -= 2.25/2.75; return 7.5625*t*t+0.9375; }
  t -= 2.625/2.75; return 7.5625*t*t+0.984375;
}

// ─ ball path: bezier curve ─
var DURATION = 1100; // ms
var startTime = null;
var phase = 'fly'; // fly → bounce → done
var bounceStart = null;
var ballX, ballY, ballAngle = 0;

// start from bottom-left, arc to hoop
var p0x, p0y, p1x, p1y, p2x, p2y, p3x, p3y;
function initPath() {
  p0x = W * 0.08; p0y = H * 0.88;
  p1x = W * 0.10; p1y = H * 0.05;
  p2x = W * 0.50; p2y = H * 0.02;
  p3x = hoopX;    p3y = hoopY;
}
initPath();

function bezier(t, p0, p1, p2, p3) {
  var u = 1 - t;
  return u*u*u*p0 + 3*u*u*t*p1 + 3*u*t*t*p2 + t*t*t*p3;
}

// ─ draw backboard + hoop + net ─
function drawHoop() {
  // backboard
  ctx.save();
  ctx.fillStyle = 'rgba(150,150,150,0.25)';
  ctx.fillRect(hoopX + hoopR + 6, hoopY - 30, 8, 55);
  ctx.restore();

  // back rim (behind ball)
  ctx.beginPath();
  ctx.arc(hoopX + hoopR, hoopY, 5, 0, Math.PI * 2);
  ctx.fillStyle = '#e04b1a';
  ctx.fill();

  // net
  ctx.save();
  ctx.strokeStyle = 'rgba(160,160,160,0.55)';
  ctx.lineWidth = 1;
  var nx = hoopX - hoopR, nw = hoopR * 2, nd = 30;
  for (var xi = 0; xi <= 4; xi++) {
    var nx0 = nx + (nw / 4) * xi;
    var nx1 = nx + 4 + (nw * 0.85 / 4) * xi;
    ctx.beginPath();
    ctx.moveTo(nx0, hoopY + 2);
    ctx.lineTo(nx1, hoopY + nd);
    ctx.stroke();
  }
  for (var yi = 1; yi <= 3; yi++) {
    var frac = yi / 4;
    ctx.beginPath();
    ctx.moveTo(nx + (4 * frac), hoopY + nd * frac);
    ctx.lineTo(nx + nw - (4 * frac), hoopY + nd * frac);
    ctx.stroke();
  }
  ctx.restore();
}

// ─ draw front rim (in front of ball) ─
function drawRim() {
  ctx.beginPath();
  ctx.arc(hoopX - hoopR, hoopY, 5, 0, Math.PI * 2);
  ctx.fillStyle = '#e04b1a';
  ctx.fill();

  // rim bar
  ctx.beginPath();
  ctx.moveTo(hoopX - hoopR, hoopY);
  ctx.lineTo(hoopX + hoopR, hoopY);
  ctx.strokeStyle = '#e04b1a';
  ctx.lineWidth = 4;
  ctx.stroke();
}

// ─ draw ball ─
function drawBall(x, y, angle) {
  var r = 22;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);

  // shadow
  ctx.beginPath();
  ctx.ellipse(0, r + 6, r * 0.7, 5, 0, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(0,0,0,0.08)';
  ctx.fill();

  // ball body
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.fillStyle = '#e07b2a';
  ctx.fill();
  ctx.strokeStyle = '#b85e1a';
  ctx.lineWidth = 1;
  ctx.stroke();

  // seam lines
  ctx.strokeStyle = 'rgba(0,0,0,0.25)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(-r, 0); ctx.lineTo(r, 0);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(0, -r); ctx.lineTo(0, r);
  ctx.stroke();
  // curved seams
  ctx.beginPath();
  ctx.arc(-r*0.4, 0, r*0.65, -0.6, 0.6);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(r*0.4, 0, r*0.65, Math.PI-0.6, Math.PI+0.6);
  ctx.stroke();

  ctx.restore();
}

// ─ draw confetti ─
function drawConfetti() {
  confetti.forEach(function(c) {
    ctx.save();
    ctx.globalAlpha = c.life;
    ctx.translate(c.x, c.y);
    ctx.rotate(c.rot);
    ctx.fillStyle = c.color;
    ctx.fillRect(-c.w/2, -c.h/2, c.w, c.h);
    ctx.restore();
  });
}

function updateConfetti() {
  confetti.forEach(function(c) {
    c.x += c.vx;
    c.y += c.vy;
    c.vy += 0.35; // gravity
    c.vx *= 0.98;
    c.rot += c.rspd;
    c.life -= c.decay;
  });
  confetti = confetti.filter(function(c) { return c.life > 0; });
}

// ─ main loop ─
function loop(ts) {
  ctx.clearRect(0, 0, W, H);
  drawHoop();

  if (phase === 'fly') {
    if (!startTime) startTime = ts;
    var elapsed = ts - startTime;
    var t = Math.min(elapsed / DURATION, 1);
    var et = easeInOut(t);

    ballX = bezier(et, p0x, p1x, p2x, p3x);
    ballY = bezier(et, p0y, p1y, p2y, p3y);
    ballAngle += 0.06 + t * 0.04;

    drawBall(ballX, ballY, ballAngle);
    drawRim();

    if (t >= 1) {
      phase = 'swish';
      bounceStart = ts;
      spawnConfetti();
      setTimeout(function() {
        msg.classList.add('show');
      }, 200);
    }
  } else if (phase === 'swish') {
    // ball drops through net
    var el2 = ts - bounceStart;
    var t2  = Math.min(el2 / 400, 1);
    ballX = hoopX + (Math.sin(t2 * Math.PI * 2) * 6 * (1 - t2));
    ballY = hoopY + t2 * 50;
    var alpha = 1 - t2;
    ctx.globalAlpha = alpha;
    drawBall(ballX, ballY, ballAngle + t2 * 2);
    ctx.globalAlpha = 1;
    drawRim();
    updateConfetti();
    drawConfetti();
    if (t2 >= 1) phase = 'done';
  } else {
    updateConfetti();
    drawConfetti();
    drawRim();
  }

  if (phase !== 'done' || confetti.length > 0) {
    requestAnimationFrame(loop);
  }
}

requestAnimationFrame(loop);
</script>
</body>
</html>
"""

# 報名成功動畫
if st.session_state.get('show_basket_anim'):
    components.html(BASKETBALL_ANIM, height=280)
    st.toast("🎉 報名成功！")
    st.session_state['show_basket_anim'] = False

if not visible_dates:
    st.info("👋 目前沒有開放報名的場次")
else:
    # ── 決定目前選中的場次 index ──
    def _get_active_idx():
        # 操作後跳指定場次
        if st.session_state.get('_tab_jump') is not None:
            idx = st.session_state.pop('_tab_jump')
            if 0 <= idx < len(visible_dates):
                st.session_state['_active_session'] = idx
                return idx
        # 保持上次選的
        saved = st.session_state.get('_active_session')
        if saved is not None and 0 <= saved < len(visible_dates):
            return saved
        # 預設：最近的未來或今天場次
        _today = date.today()
        for j, d in enumerate(visible_dates):
            if datetime.strptime(d, "%Y-%m-%d").date() >= _today:
                st.session_state['_active_session'] = j
                return j
        st.session_state['_active_session'] = len(visible_dates) - 1
        return len(visible_dates) - 1

    active_idx = _get_active_idx()

    # ── 場次卡片選擇器 ──
    card_cols = st.columns(len(visible_dates))
    for ci, d in enumerate(visible_dates):
        players    = st.session_state.data["sessions"].get(d, [])
        active_cnt = len([p for p in players if p.get('count', 1) > 0])
        wait_cnt   = max(0, active_cnt - MAX_CAPACITY)
        play_cnt   = min(active_cnt, MAX_CAPACITY)
        month      = int(d.split('-')[1])
        day        = int(d.split('-')[2])
        is_rain    = d in rained_out
        is_sel     = (ci == active_idx)
        rain_icon  = "☔ " if is_rain else ""
        count_txt  = f"{play_cnt}/{MAX_CAPACITY}" + (f" +{wait_cnt}" if wait_cnt > 0 else "")
        # 整張卡片就是按鈕，用 label 排版
        btn_label  = f"{rain_icon}{month}/{day}\n{count_txt} 人"
        with card_cols[ci]:
            if st.button(
                btn_label,
                key=f"card_btn_{d}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state['_active_session'] = ci
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 只渲染選中的場次 ──
    i  = active_idx
    dk = visible_dates[i]
    if True:  # 保持縮排一致
            is_rained_out = dk in rained_out
            dt_obj        = datetime.strptime(dk, "%Y-%m-%d")
            cutoff        = (dt_obj - timedelta(days=1)).replace(hour=12, minute=0, second=0)
            is_expired    = datetime.now() > cutoff
            can_operate   = st.session_state.is_admin or (not is_expired)

            if is_rained_out:
                st.markdown("""<div class="rain-banner">
                    ☔ 本場次因天氣因素取消，有報名的人仍算出席
                </div>""", unsafe_allow_html=True)

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

            remaining   = max(0, MAX_CAPACITY - curr_count)
            remain_txt  = f"還剩 <b>{remaining}</b> 個名額" if remaining > 0 else "<b>名額已滿</b>"
            remain_col  = "#22c55e" if remaining > 5 else "#f59e0b" if remaining > 0 else "#ef4444"

            st.markdown(f"""
            <div style="margin-bottom:5px;padding:0 4px;">
                <div class="progress-info">
                    <span>正選 ({curr_count}/{MAX_CAPACITY})</span>
                    <span>候補: {len(wait_list)}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width:{pct}%;background:{bar_color};"></div>
                </div>
                <div style="font-size:0.78rem;color:{remain_col};font-weight:700;margin-top:5px;text-align:right;">
                    {remain_txt}
                </div>
            </div>
            <div style="display:flex;justify-content:flex-end;gap:15px;font-size:0.85rem;
                        color:#64748b;margin-bottom:16px;font-weight:500;padding-right:5px;">
                <span>🏀 帶球：<b>{ball_count}</b></span>
                <span>🚩 佔場：<b>{court_count}</b></span>
            </div>
            """, unsafe_allow_html=True)

            # ── 報名表單（截止後自動隱藏，不顯示廢 UI）──
            submit_disabled = not can_operate or (is_rained_out and not st.session_state.is_admin)

            if not is_expired or st.session_state.is_admin:
                with st.expander("📝 我要報名", expanded=not is_expired):
                    if is_rained_out and not st.session_state.is_admin:
                        st.warning("⛔ 本場次已因天氣取消，無法報名")
                    else:
                        with st.form(f"signup_{dk}", clear_on_submit=True):
                            player_name  = st.text_input("✏️ 球員姓名", placeholder="請輸入你的名字", disabled=submit_disabled)

                            # checkbox 兩列排版，手機不擠
                            r1c1, r1c2 = st.columns(2)
                            r2c1, r2c2 = st.columns(2)
                            is_member    = r1c1.checkbox("⭐ 晴女成員", key=f"m_{dk}", disabled=submit_disabled)
                            bring_ball   = r1c2.checkbox("🏀 我帶球",   key=f"b_{dk}", disabled=submit_disabled)
                            occupy_court = r2c1.checkbox("🚩 我佔場",   key=f"c_{dk}", disabled=submit_disabled)
                            is_visitor   = r2c2.checkbox("📣 加油團（不打球）", key=f"v_{dk}", disabled=submit_disabled)

                            # 人數選擇：radio 橫排，不會誤觸 submit
                            total = st.radio(
                                "**報名人數**（含自己）",
                                options=[1, 2, 3],
                                format_func=lambda x: f"{x} 人",
                                horizontal=True,
                                key=f"total_{dk}",
                                disabled=submit_disabled,
                            )

                            submitted = st.form_submit_button("🏀 送出報名", type="primary", disabled=submit_disabled, use_container_width=True)
                            if submitted:
                                if "友" in player_name:
                                    st.error("❌ 請輸入團員姓名")
                                elif player_name:
                                    latest        = load_data()
                                    existing      = latest["sessions"].get(dk, [])
                                    related_count = len([
                                        x for x in existing
                                        if x['name'] == player_name
                                        or x['name'].startswith(f"{player_name} (")
                                        or x['name'].startswith(f"{player_name} （")
                                    ])
                                    if related_count == 0 and not is_member:
                                        st.error("❌ 第一次報名需勾選「⭐ 晴女成員」")
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
                                                "id": str(uuid.uuid4()), "name": full_name,
                                                "count": 0 if (is_visitor and first) else 1,
                                                "isMember": is_member if first else False,
                                                "bringBall": bring_ball if first else False,
                                                "occupyCourt": occupy_court if first else False,
                                                "timestamp": ts + (k * 0.01),
                                            })
                                        save_data(latest); build_stats.clear()
                                        st.session_state['_tab_jump'] = i
                                        st.session_state['show_basket_anim'] = True
                                        st.rerun()

                # 規則說明獨立折疊，不跟表單混在一起
                with st.expander("📌 報名規則說明", expanded=False):
                    st.markdown("""<div class="rules-box">
                        <div class="rules-header">📌 報名須知</div>
                        <div class="rules-row"><span class="rules-icon">🔴</span>
                            <div class="rules-content"><b>資格與規範</b>：採實名制。僅限 <b>⭐晴女</b> 報名。欲事後補報朋友，請用原名再次填寫即可 (含自己上限3位)。</div></div>
                        <div class="rules-row"><span class="rules-icon">🟡</span>
                            <div class="rules-content"><b>📣加油團</b>：團員若「不打球但帶朋友」請勾此項。本人不佔名額，但朋友會佔打球名額。</div></div>
                        <div class="rules-row"><span class="rules-icon">🟢</span>
                            <div class="rules-content"><b>優先機制</b>：正選 20 人。當人數超過時，<b>⭐晴女</b> 享有進入正選名單之優先權。</div></div>
                        <div class="rules-row"><span class="rules-icon">🔵</span>
                            <div class="rules-content"><b>時間與修改</b>：截止於前一日 12:00。</div></div>
                        <div class="rules-footer">有任何問題請找最美管理員們 ❤️</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("⛔ 報名已截止（前一日 12:00）")

            # ── 正選名單 ──
            st.subheader("🏀 報名名單")
            render_list(main_list, dk, False, can_operate, st.session_state.is_admin)

            # ── 候補名單（獨立區塊，黃色背景）──
            if wait_list:
                st.markdown('<div class="wait-header">⏳ 候補名單</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    render_list(wait_list, dk, True, can_operate, st.session_state.is_admin)

# ==========================================
# 9. 管理員專區
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("<div style='text-align:center;color:#cbd5e1;font-size:0.8rem;'>▼ 管理員專用通道 ▼</div>", unsafe_allow_html=True)

with st.expander("⚙️ 管理員專區 (Admin)", expanded=st.session_state.is_admin):
    if not st.session_state.is_admin:
        pwd = st.text_input("密碼", key="admin_pwd_input", type="password")
        if pwd == get_admin_password():
            st.session_state.is_admin = True; st.rerun()
    else:
        col_logout, _ = st.columns([1, 4])
        with col_logout:
            if st.button("🚪 登出"):
                st.session_state.is_admin = False; st.rerun()

        all_sessions = sorted(st.session_state.data["sessions"].keys())

        # ── 場次管理 ──
        st.markdown('<div class="admin-section"><div class="admin-section-title">📅 場次管理</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            new_date = st.date_input("新增日期", label_visibility="collapsed")
        with c2:
            if st.button("➕ 新增", use_container_width=True):
                data = load_data()
                if str(new_date) not in data["sessions"]:
                    data["sessions"][str(new_date)] = []; save_data(data); st.rerun()
        if all_sessions:
            c1, c2 = st.columns([3, 1])
            with c1:
                del_target = st.selectbox("刪除場次", all_sessions, label_visibility="collapsed")
            with c2:
                if st.button("🗑️ 刪除", use_container_width=True):
                    data = load_data(); del data["sessions"][del_target]
                    save_data(data); build_stats.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── 場次設定 ──
        if all_sessions:
            st.markdown('<div class="admin-section"><div class="admin-section-title">⚙️ 場次設定</div>', unsafe_allow_html=True)
            hidden = st.multiselect("👁️ 隱藏場次", all_sessions, default=st.session_state.data.get("hidden", []))
            if st.button("更新隱藏設定", use_container_width=True):
                data = load_data(); data["hidden"] = hidden; save_data(data); st.rerun()
            st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
            new_rained = st.multiselect("☔ 天氣取消場次", all_sessions, default=st.session_state.data.get("rained_out", []), key="rained_multiselect")
            if st.button("更新天氣取消設定", use_container_width=True):
                data = load_data(); data["rained_out"] = new_rained
                save_data(data); build_stats.clear()
                st.toast("✅ 已更新"); time.sleep(0.5); st.rerun()
            st.markdown('</div></div>', unsafe_allow_html=True)

        # ── 編輯隱藏場次 ──
        with st.expander("🕵️ 編輯隱藏場次資料", expanded=False):
            hidden_dates = st.session_state.data.get("hidden", [])
            if hidden_dates:
                target_hidden = st.selectbox("選擇日期", sorted(hidden_dates))
                if target_hidden:
                    render_list(st.session_state.data["sessions"].get(target_hidden, []), target_hidden, is_admin_mode=True)
            else:
                st.write("目前無隱藏場次")

        # ── 出席統計 ──
        st.markdown('<div class="admin-section"><div class="admin-section-title">📊 出席統計報表</div>', unsafe_allow_html=True)
        st.caption("✏️ 改名　🚪 退群（移至下方，可恢復或永久刪除）")
        st.markdown('</div>', unsafe_allow_html=True)
        render_stats(st.session_state.data)
