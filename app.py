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
    '''<div style="display:flex;justify-content:center;margin-bottom:16px;"><div style="background:white;border-radius:20px;overflow:hidden;display:inline-flex;align-items:stretch;border:1px solid #e8e6e0;box-shadow:0 2px 12px rgba(0,0,0,0.06);"><div style="width:130px;flex-shrink:0;overflow:hidden;position:relative;"><img src="data:image/png;base64,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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwH0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD6AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD6AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/Z" style="width:100%;height:100%;object-fit:cover;object-position:30% center;display:block;" alt=""><div style="position:absolute;top:0;right:0;bottom:0;width:15%;background:linear-gradient(to right,transparent,white);"></div></div><div style="padding:20px 22px;display:flex;flex-direction:column;justify-content:center;gap:4px;"><div style="font-size:20px;font-weight:900;color:#1e293b;">晴女 ☀️ 在場邊等妳 🌈</div><div style="font-size:13px;color:#64748b;font-weight:600;">Keep Playing, Keep Shining</div><div style="margin-top:8px;display:inline-block;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:30px;padding:4px 13px;font-size:12px;font-weight:600;color:#475569;width:fit-content;">📍 朱崙公園 &nbsp;|&nbsp; 🕑 19:00</div></div></div></div>''',
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
        }},600);
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

        # ── 一鍵複製名單 ──
        st.markdown('<div class="admin-section"><div class="admin-section-title">📋 複製名單</div>', unsafe_allow_html=True)
        _copy_sessions = sorted(st.session_state.data['sessions'].keys())
        if _copy_sessions:
            _copy_dk = st.selectbox('選擇場次', _copy_sessions, key='copy_dk_select', label_visibility='collapsed')
            if _copy_dk:
                _players = st.session_state.data['sessions'].get(_copy_dk, [])
                _active  = sorted([p for p in _players if p.get('count',1)>0], key=lambda x:x.get('timestamp',0))
                _wait    = sorted([p for p in _players if p.get('count',1)>0][MAX_CAPACITY:], key=lambda x:x.get('timestamp',0))
                _active  = sorted([p for p in _players if p.get('count',1)>0], key=lambda x:(0 if x.get('isMember') else 1, x.get('timestamp',0)))
                _main    = _active[:MAX_CAPACITY]
                _w       = _active[MAX_CAPACITY:]
                _mo, _dy = int(_copy_dk.split('-')[1]), int(_copy_dk.split('-')[2])
                _lines   = [f"📅 {_mo}/{_dy} 報名名單\n"]
                _lines  += [f"{i+1}. {p['name']}" for i,p in enumerate(_main)]
                if _w:
                    _lines += ["", "⏳ 候補"]
                    _lines += [f"{i+1}. {p['name']}" for i,p in enumerate(_w)]
                _text = "\n".join(_lines)
                st.text_area('名單', _text, height=200, key='copy_text_area')
                components.html(f"""
                <button onclick="navigator.clipboard.writeText({repr(_text)}).then(()=>{{this.textContent='✅ 已複製!';setTimeout(()=>this.textContent='📋 複製到剪貼簿',1500)}})" 
                style="background:#e05a2b;color:white;border:none;padding:8px 18px;border-radius:8px;font-size:14px;cursor:pointer;font-family:sans-serif;">
                📋 複製到剪貼簿</button>
                """, height=50)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── 出席統計 ──
        st.markdown('<div class="admin-section"><div class="admin-section-title">📊 出席統計報表</div>', unsafe_allow_html=True)
        st.caption("✏️ 改名　🚪 退群（移至下方，可恢復或永久刪除）")
        st.markdown('</div>', unsafe_allow_html=True)
        render_stats(st.session_state.data)
