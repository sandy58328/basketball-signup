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
                st.markdown(f"""<div class="player-row{row_extra}">
                    <span class="{idx_cls}">{idx_str}</span>
                    <span class="list-name">{p['name']}</span>{badges}{time_html}
                </div>""", unsafe_allow_html=True)
            if can_edit:
                with cols[1]:
                    if st.button("✏️", key=f"be_{p['id']}"):
                        st.session_state.edit_target = p['id']
                        st.rerun()
                with cols[2]:
                    with st.popover("❌"):
                        st.write(f"確定取消「{p['name']}」的報名？")
                        if st.button("確認刪除", key=f"conf_del_{p['id']}", type="primary"):
                            delete_player(p['id'], date_key)

# ==========================================
# 6. 出席統計
# ==========================================
@st.cache_data(ttl=60, show_spinner=False)
def build_stats(sessions_json: str, leaves_json: str, rained_out_tuple: tuple, all_dates_tuple: tuple) -> tuple[dict, dict, dict]:
    sessions   = json.loads(sessions_json)
    leaves     = json.loads(leaves_json)
    rained_out = set(rained_out_tuple)
    all_dates  = list(all_dates_tuple)
    norm_cache: dict[str, str] = {}

    def get_norm(n: str) -> str:
        if n not in norm_cache:
            norm_cache[n] = normalize_name(n)
        return norm_cache[n]

    member_signups: dict[str, list] = {}
    future_signups: dict[str, list] = {}

    for sd in all_dates:
        day   = datetime.strptime(sd, "%Y-%m-%d").date()
        label = f"{int(sd.split('-')[1])}/{int(sd.split('-')[2])}"
        if day > date.today():
            for p in sessions.get(sd, []):
                if not is_friend(p['name']):
                    future_signups.setdefault(get_norm(p['name']), []).append(label)
            continue
        if sd in rained_out:
            label = f"☔{label}"
        for p in sessions.get(sd, []):
            if not is_friend(p['name']):
                member_signups.setdefault(get_norm(p['name']), []).append(label)

    stats: dict[str, dict] = {}
    for sd, players in sessions.items():
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

    for raw_name, months in leaves.items():
        key = get_norm(raw_name)
        stats.setdefault(key, {"name": raw_name, "last_date": None, "leaves": set()})
        stats[key]["leaves"].update(months)

    return stats, member_signups, future_signups


def _render_stat_row(key, item, signups, future_signups):
    last          = item["last_date"]
    leaves_sorted = sorted(item["leaves"])
    recent_two    = signups.get(key, [])[-2:]
    signup_str    = ", ".join(recent_two) or "—"
    future_list   = future_signups.get(key, [])
    future_str    = "　📅 " + ", ".join(future_list) if future_list else ""
    last_str      = str(last) if last else "無紀錄"
    leave_str     = "　請假：" + ", ".join(leaves_sorted) if leaves_sorted else ""
    status        = compute_status(last, set(leaves_sorted))
    row_cls       = status_to_row_class(status)

    if st.session_state.get(f"stat_edit_{key}"):
        st.markdown(f"<div class='edit-box'>✏️ 編輯成員：{item['name']}</div>", unsafe_allow_html=True)
        with st.form(key=f"stat_form_{key}"):
            new_display = st.text_input("顯示名稱", item['name'])
            b1, b2, b3  = st.columns(3)
            if b1.form_submit_button("💾 儲存", type="primary"):
                cur = load_data(); old = item['name']
                for sd in cur["sessions"]:
                    for p in cur["sessions"][sd]:
                        if normalize_name(p['name']) == key and not is_friend(p['name']):
                            p['name'] = new_display
                        for fp in cur["sessions"][sd]:
                            if fp['name'].startswith(f"{old} (") or fp['name'].startswith(f"{old} （"):
                                fp['name'] = fp['name'].replace(old, new_display, 1)
                if old in cur["leaves"]:
                    cur["leaves"][new_display] = cur["leaves"].pop(old)
                save_data(cur); build_stats.clear()
                st.session_state[f"stat_edit_{key}"] = False
                st.toast("✅ 名稱已更新"); time.sleep(0.5); st.rerun()
            if b2.form_submit_button("取消"):
                st.session_state[f"stat_edit_{key}"] = False; st.rerun()
            if b3.form_submit_button("🚪 退群", type="secondary"):
                cur = load_data(); cur.setdefault("removed_members", [])
                if key not in cur["removed_members"]: cur["removed_members"].append(key)
                save_data(cur); build_stats.clear()
                st.session_state[f"stat_edit_{key}"] = False
                st.toast(f"👋 {item['name']} 已從統計移除"); time.sleep(0.5); st.rerun()
    else:
        cols = st.columns([5.5, 1, 1], gap="small")
        with cols[0]:
            st.markdown(f"""<div class="{row_cls}">
                <div class="stat-name">{status} &nbsp; {item['name']}</div>
                <div class="stat-detail">近期：{signup_str}　最後出席：{last_str}{leave_str}{future_str}</div>
            </div>""", unsafe_allow_html=True)
        with cols[1]:
            if st.button("✏️", key=f"stat_btn_edit_{key}"):
                st.session_state[f"stat_edit_{key}"] = True; st.rerun()
        with cols[2]:
            with st.popover("🚪"):
                st.write(f"將「{item['name']}」移至已退群？")
                if st.button("確認退群", key=f"stat_rm_{key}", type="primary"):
                    cur = load_data(); cur.setdefault("removed_members", [])
                    if key not in cur["removed_members"]: cur["removed_members"].append(key)
                    save_data(cur); build_stats.clear()
                    st.toast(f"👋 {item['name']} 已移除"); time.sleep(0.5); st.rerun()


def render_stats(raw_data: dict):
    all_dates_tuple  = tuple(sorted(raw_data["sessions"].keys()))
    rained_out_tuple = tuple(raw_data.get("rained_out", []))

    stats, signups, future_signups = build_stats(
        sessions_json    = json.dumps(raw_data["sessions"], ensure_ascii=False),
        leaves_json      = json.dumps(raw_data["leaves"],   ensure_ascii=False),
        rained_out_tuple = rained_out_tuple,
        all_dates_tuple  = all_dates_tuple,
    )

    removed     = set(raw_data.get("removed_members", []))
    active_keys = [k for k in sorted(stats.keys()) if k not in removed]

    STATUS_ORDER = ["🟢", "🟡", "🔴", "🏖️"]
    STATUS_LABEL = {"🟢": "🟢 活躍", "🟡": "🟡 預警", "🔴": "🔴 逾期", "🏖️": "🏖️ 請假中"}

    groups: dict[str, list] = {"🟢": [], "🟡": [], "🔴": [], "🏖️": []}
    for key in active_keys:
        item   = stats[key]
        status = compute_status(item["last_date"], set(item["leaves"]))
        if   "🔴" in status: groups["🔴"].append(key)
        elif "🟡" in status: groups["🟡"].append(key)
        elif "🏖️" in status: groups["🏖️"].append(key)
        else:                 groups["🟢"].append(key)

    cnt = {k: len(v) for k, v in groups.items()}

    if "stat_filter" not in st.session_state:
        st.session_state.stat_filter = None

    cols = st.columns(4, gap="small")
    card_colors = {"🟢": "stat-card-green", "🟡": "stat-card-yellow", "🔴": "stat-card-red", "🏖️": "stat-card-blue"}
    for ci, sg in enumerate(STATUS_ORDER):
        is_selected  = st.session_state.stat_filter == sg
        border_style = "outline:2px solid #6366f1;box-shadow:0 0 0 4px rgba(99,102,241,0.12);" if is_selected else ""
        with cols[ci]:
            st.markdown(f"""<div class="{card_colors[sg]} stat-card" style="{border_style}">
                <div class="stat-card-num">{cnt[sg]}</div>
                <div class="stat-card-lbl">{STATUS_LABEL[sg]}</div>
            </div>""", unsafe_allow_html=True)
            btn_label = "✕ 取消" if is_selected else STATUS_LABEL[sg].split(" ")[1]
            if st.button(btn_label, key=f"filter_btn_{sg}", use_container_width=True):
                st.session_state.stat_filter = None if is_selected else sg
                st.rerun()

    if not active_keys:
        st.info("目前無統計資料")
        return

    show_groups = [st.session_state.stat_filter] if st.session_state.stat_filter else STATUS_ORDER
    for sg in show_groups:
        keys_in_group = groups[sg]
        if not keys_in_group:
            continue
        st.markdown(f"<div class='stat-group-header'>{STATUS_LABEL[sg]} · {len(keys_in_group)} 人</div>", unsafe_allow_html=True)
        for key in keys_in_group:
            _render_stat_row(key, stats[key], signups, future_signups)

    # 已退群名單
    if removed:
        st.divider()
        with st.expander(f"👻 已退群名單（{len(removed)} 人）", expanded=False):
            removed_stats = {k: stats[k] for k in removed if k in stats}
            if removed_stats:
                for key, item in sorted(removed_stats.items(), key=lambda x: x[1]['name']):
                    c1, c2, c3 = st.columns([4, 1, 1])
                    c1.markdown(f"**{item['name']}**")
                    with c2:
                        if st.button("↩️ 恢復", key=f"stat_restore_{key}"):
                            cur = load_data()
                            if key in cur.get("removed_members", []): cur["removed_members"].remove(key)
                            save_data(cur); build_stats.clear()
                            st.toast(f"✅ {item['name']} 已恢復"); time.sleep(0.5); st.rerun()
                    with c3:
                        with st.popover("🗑️"):
                            st.warning(f"永久刪除「{item['name']}」所有紀錄？此操作無法復原！", icon="⚠️")
                            if st.button("確定永久刪除", key=f"stat_purge_{key}", type="primary"):
                                cur = load_data()
                                if key in cur.get("removed_members", []): cur["removed_members"].remove(key)
                                for sd in cur["sessions"]:
                                    cur["sessions"][sd] = [p for p in cur["sessions"][sd] if normalize_name(p['name']) != key]
                                for rn in list(cur["leaves"].keys()):
                                    if normalize_name(rn) == key: del cur["leaves"][rn]
                                save_data(cur); build_stats.clear()
                                st.toast(f"🗑️ {item['name']} 所有資料已永久刪除"); time.sleep(0.5); st.rerun()
            else:
                st.write("（無歷史紀錄）")

# ==========================================
# 7. 初始化
# ==========================================
if 'is_admin'    not in st.session_state: st.session_state.is_admin    = False
if 'edit_target' not in st.session_state: st.session_state.edit_target = None
if 'active_tab'  not in st.session_state: st.session_state.active_tab  = 0
if 'total_sel'   not in st.session_state: st.session_state.total_sel   = {}  # {date_key: int}

st.set_page_config(page_title="晴女籃球報名", page_icon="☀️", layout="centered")
load_css()

# ==========================================
# 8. 主畫面
# ==========================================
components.html(
    '''<div style="display:flex;justify-content:center;margin-bottom:16px;"><div style="background:white;border-radius:20px;overflow:hidden;display:inline-flex;align-items:stretch;border:1px solid #e8e6e0;box-shadow:0 2px 12px rgba(0,0,0,0.06);"><div style="width:130px;flex-shrink:0;overflow:hidden;position:relative;"><img src="data:image/jpeg;base64,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" style="width:100%;height:100%;object-fit:cover;object-position:30% center;display:block;" alt=""><div style="position:absolute;top:0;right:0;bottom:0;width:15%;background:linear-gradient(to right,transparent,white);"></div></div><div style="padding:20px 22px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:4px;"><div style="font-size:17px;font-weight:900;color:#1e293b;line-height:1.3;">晴女 ☀️ 在場邊等妳 🌈</div><div style="font-size:13px;color:#64748b;font-weight:600;">Keep Playing, Keep Shining</div><div style="margin-top:8px;display:table;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:30px;padding:4px 13px;font-size:12px;font-weight:600;color:#475569;white-space:nowrap;">📍 朱崙公園 &nbsp;|&nbsp; 🕑 19:00</div></div></div></div>''',
    height=140
)

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
    time.sleep(2.5)
    st.rerun()

# 捲動到剛報名的名字
if st.session_state.get('scroll_to'):
    _sname = st.session_state.pop('scroll_to')
    components.html(f"""
    <script>
    (function(){{
        setTimeout(function(){{
            var els = window.parent.document.querySelectorAll('.list-name');
            for(var i=0;i<els.length;i++){{
                if(els[i].textContent.trim()==='{_sname}'){{
                    els[i].scrollIntoView({{behavior:'smooth',block:'center'}});
                    break;
                }}
            }}
        }},2800);
    }})();
    </script>
    """, height=0)

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
        _today_d   = date.today()
        _dobj      = datetime.strptime(d, "%Y-%m-%d").date()
        _delta     = (_dobj - _today_d).days
        if _delta < 0:    _day_hint = "已結束"
        elif _delta == 0: _day_hint = "今天 🔥"
        elif _delta == 1: _day_hint = "明天"
        else:             _day_hint = f"{_delta} 天後"
        btn_label  = f"{rain_icon}{month}/{day}\n{_day_hint} · {count_txt} 人"
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
                # 截止倒數
                if not is_expired:
                    _remaining = cutoff - datetime.now()
                    _hrs = int(_remaining.total_seconds() // 3600)
                    _mins = int((_remaining.total_seconds() % 3600) // 60)
                    if _hrs >= 24:
                        _cd = f"⏰ 截止時間：{int(_hrs//24)} 天 {_hrs%24} 小時後"
                    elif _hrs > 0:
                        _cd = f"⏰ 截止時間：{_hrs} 小時 {_mins} 分後"
                    else:
                        _cd = f"⏰ 截止時間：{_mins} 分鐘後"
                    st.caption(_cd)
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
                                        st.session_state['scroll_to'] = full_name
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
                        <div class="rules-row"><span class="rules-icon">🟡</span>
                            <div class="rules-content"><b>出席要求</b>：每兩個月至少出席一次，請假不得連續超過兩個月。</div></div>
                        <div class="rules-footer">有任何問題請找最美管理員們 ❤️</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("⛔ 報名已截止（前一日 12:00）")

            # ── 出席 & 請假狀態公開版 ──
            with st.expander("📊 出席 & 請假狀況", expanded=False):
                _stats, _, _ = build_stats(
                    json.dumps(st.session_state.data["sessions"]),
                    json.dumps(st.session_state.data.get("leaves", {})),
                    tuple(st.session_state.data.get("rained_out", [])),
                    tuple(sorted(st.session_state.data["sessions"].keys()))
                )
                _groups = {"🟢": [], "🟡": [], "🔴": []}
                for _item in _stats.values():
                    _s = compute_status(_item["last_date"], set(_item["leaves"]))
                    if "🟢" in _s: _groups["🟢"].append(_item["name"])
                    elif "🟡" in _s: _groups["🟡"].append(_item["name"])
                    elif "🔴" in _s: _groups["🔴"].append(_item["name"])
                _labels = {"🟢": "正常", "🟡": "當月需出席", "🔴": "已逾期"}
                for _icon, _label in _labels.items():
                    _names = _groups[_icon]
                    st.markdown(f"**{_icon} {_label}**")
                    st.caption("　" + "・".join(_names) if _names else "　（無）")
                # 請假區塊
                _leaves = st.session_state.data.get("leaves", {})
                _leave_merged: dict = {}
                _leave_display: dict = {}
                for _rn, _ms in _leaves.items():
                    _k = normalize_name(_rn)
                    _leave_merged.setdefault(_k, set()).update(_ms)
                    _leave_display.setdefault(_k, _rn)
                _leave_list = [((_leave_display[k], sorted(_leave_merged[k]))) for k in sorted(_leave_merged) if _leave_merged[k]]
                st.markdown("**🏖️ 請假中**")
                if _leave_list:
                    for _ln, _lm in _leave_list:
                        st.caption(f"　{_ln}（{"、".join(_lm)}）")
                else:
                    st.caption("　（無）")

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
