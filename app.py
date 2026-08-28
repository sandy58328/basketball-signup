import streamlit as st
import streamlit.components.v1 as components
import json
import time
import uuid
import re
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

def taipei_today() -> date:
    """統一用台北時區判斷「今天」，避免伺服器 UTC 時間在月初/日期交界時分類錯誤。"""
    return datetime.now(TZ_TAIPEI).date()
from dateutil.relativedelta import relativedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 0. 設定區
# ==========================================
MAX_CAPACITY         = 20
APP_URL              = "https://sunny-girls-basketball.streamlit.app"
SHEET_NAME           = "basketball_db"
SHEET_KEY            = "1ZUI1YlL2BZZFFa5Cvg5CIGex_wq0l5o_PgoSLB-ua_c"
ARCHIVE_SHEET_TITLE  = "sessions_archive"
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
@st.cache_resource(show_spinner=False)
def _get_gspread_book():
    """驗證帳號＋開啟試算表只做一次並快取，之後重複使用同一條連線，避免每次操作都重新驗證造成的延遲與 API 限流。"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds  = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_KEY)  # 用 ID 直接開，比用名稱搜尋快，也避免同名試算表誤開

def get_sheet():
    try:
        return _get_gspread_book().sheet1
    except Exception as e:
        st.error(f"❌ 資料庫連線失敗：{e}")
        _get_gspread_book.clear()  # 連線可能已失效，清掉快取讓下次重新驗證
        return None

@st.cache_resource(show_spinner=False)
def _get_archive_worksheet_handle():
    book = _get_gspread_book()
    try:
        return book.worksheet(ARCHIVE_SHEET_TITLE)
    except gspread.exceptions.WorksheetNotFound:
        return book.add_worksheet(title=ARCHIVE_SHEET_TITLE, rows=10, cols=4)

def get_archive_sheet():
    """已隱藏的舊場次資料改放這個分頁，避免 A1 撞到 Google Sheets 單一儲存格 50000 字元上限。"""
    try:
        return _get_archive_worksheet_handle()
    except Exception as e:
        st.error(f"❌ 封存分頁連線失敗：{e}")
        _get_archive_worksheet_handle.clear()
        return None

@st.cache_data(ttl=60, show_spinner=False)
def load_archive() -> dict:
    """讀取已封存（已隱藏）場次的歷史報名資料，供統計使用。"""
    sheet = get_archive_sheet()
    if not sheet:
        return {}
    try:
        raw = sheet.acell('A1').value
        return json.loads(raw) if raw else {}
    except Exception:
        return {}

def archive_hidden_sessions(newly_hidden_keys: list[str], data: dict) -> None:
    """把新被隱藏的場次資料搬進封存分頁，並從 data['sessions'] 移除，讓 A1 不會無限長大。"""
    if not newly_hidden_keys:
        return
    sheet = get_archive_sheet()
    if not sheet:
        return
    try:
        raw = sheet.acell('A1').value
        archive = json.loads(raw) if raw else {}
    except Exception:
        archive = {}
    for k in newly_hidden_keys:
        if k in data["sessions"]:
            archive[k] = data["sessions"].pop(k)
    sheet.update_acell('A1', json.dumps(archive, ensure_ascii=False))
    load_archive.clear()

def auto_archive_old_sessions():
    """只保留「這個月＋下個月」的場次顯示，其餘自動隱藏並搬進封存分頁。
    每次開啟 app 都會檢查，視窗會隨月份自動往後推移，不用手動維護。
    資料不會不見：只是搬去 sessions_archive 分頁，統計會自動合併回來計算。"""
    data = st.session_state.data
    _keep_months = {
        taipei_today().strftime("%Y-%m"),
        (taipei_today() + relativedelta(months=1)).strftime("%Y-%m"),
    }
    _hidden_now = set(data.get("hidden", []))
    _to_hide = [
        d for d in data["sessions"].keys()
        if d[:7] not in _keep_months and d not in _hidden_now
    ]
    if not _to_hide:
        return  # 沒有新的要處理，不用多打 API
    load_data.clear()
    fresh = load_data()
    _hidden_now = set(fresh.get("hidden", []))
    _to_hide = [
        d for d in fresh["sessions"].keys()
        if d[:7] not in _keep_months and d not in _hidden_now
    ]
    if not _to_hide:
        return
    fresh["hidden"] = sorted(_hidden_now | set(_to_hide))
    archive_hidden_sessions(_to_hide, fresh)
    if save_data(fresh):
        st.session_state.data = fresh

def _parse(raw, default):
    try:
        return json.loads(raw) if raw else default
    except Exception:
        return default

@st.cache_data(ttl=20, show_spinner=False)
def load_data() -> dict:
    sheet = get_sheet()
    if not sheet:
        return _empty_data()
    try:
        # 一次 batch_get 取 A1:D1，只打 1 個 API 請求
        rows = sheet.batch_get(["A1", "B1", "C1", "D1"])
        a1_raw = rows[0][0][0] if rows[0] else ""
        b1_raw = rows[1][0][0] if rows[1] else ""
        c1_raw = rows[2][0][0] if rows[2] else ""
        d1_raw = rows[3][0][0] if rows[3] else ""

        a1 = _parse(a1_raw, {})

        # 舊格式自動遷移（第一次讀到就在 save_data 時一起寫回，不在這裡寫）
        if isinstance(a1, dict) and "sessions" in a1:
            sessions = a1.get("sessions", {})
            leaves   = a1.get("leaves", {})
            meta     = {
                "hidden":           a1.get("hidden", []),
                "rained_out":       a1.get("rained_out", []),
                "removed_members":  a1.get("removed_members", []),
            }
        else:
            sessions = a1
            meta     = _parse(b1_raw, {})
            leaves   = _parse(c1_raw, {})

        members = _parse(d1_raw, {})

        return {
            "sessions":        sessions,
            "leaves":          leaves,
            "hidden":          meta.get("hidden", []),
            "rained_out":      meta.get("rained_out", []),
            "removed_members": meta.get("removed_members", []),
            "members":         members,
        }
    except Exception:
        return _empty_data()

def save_data(data: dict) -> bool:
    sheet = get_sheet()
    if not sheet:
        st.error("❌ 資料庫連線失敗，未儲存。請稍後再試或聯絡管理員。")
        return False
    try:
        meta = {
            "hidden":           data.get("hidden", []),
            "rained_out":       data.get("rained_out", []),
            "removed_members":  data.get("removed_members", []),
        }
        # 一次 batch update，只打 1 個 API 請求
        sheet.batch_update([
            {"range": "A1", "values": [[json.dumps(data.get("sessions", {}), ensure_ascii=False)]]},
            {"range": "B1", "values": [[json.dumps(meta,                     ensure_ascii=False)]]},
            {"range": "C1", "values": [[json.dumps(data.get("leaves", {}),   ensure_ascii=False)]]},
            {"range": "D1", "values": [[json.dumps(data.get("members", {}),  ensure_ascii=False)]]},
        ])
        load_data.clear()  # 寫完立刻讓 cache 失效，下次讀到最新資料
        return True
    except Exception as e:
        st.error(f"❌ 資料儲存失敗，未儲存：{e}")
        return False

def _empty_data() -> dict:
    return {"sessions": {}, "hidden": [], "leaves": {}, "removed_members": [], "rained_out": [], "members": {}}

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
    today = taipei_today()
    d     = dt.date()
    if d == today:
        return f"今天 {dt.strftime('%H:%M')}"
    elif d == today - timedelta(days=1):
        return f"昨天 {dt.strftime('%H:%M')}"
    else:
        return dt.strftime("%-m/%-d %H:%M")

def compute_status(last_date: date | None, leave_months: set[str], joined_month: str | None = None) -> str:
    today             = taipei_today()
    current_month_str = today.strftime("%Y-%m")
    if last_date is None:
        # 如果有加入月份，計算是否在寬限期內（加入月+2個月）
        if joined_month:
            try:
                jy, jm = int(joined_month[:4]), int(joined_month[5:7])
                grace_end = date(jy, jm, 1) + relativedelta(months=2)
                if date(today.year, today.month, 1) <= grace_end:
                    return "🟢 活躍"
            except Exception:
                pass
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
    load_data.clear()  # 強制重讀最新資料，避免跟同時間的其他操作互相覆蓋
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
    if save_data(data):
        st.session_state.data = data
        st.session_state['_skip_data_reload'] = True
        _set_tab_for_date(date_key, data)
        st.session_state.edit_target = None
        st.toast("✅ 資料已更新")
        time.sleep(0.5)
        st.rerun()
    else:
        st.error("❌ 更新未成功儲存，請再試一次。")

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
    load_data.clear()  # 強制重讀最新資料，避免跟同時間的其他操作互相覆蓋
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
    if save_data(data):
        st.session_state.data = data
        st.session_state['_skip_data_reload'] = True
        _set_tab_for_date(date_key, data)
        st.toast("🗑️ 已刪除")
        time.sleep(0.5)
        st.rerun()
    else:
        st.error("❌ 刪除未成功儲存，請再試一次。")

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
        if day > taipei_today():
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
        if day > taipei_today():
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
    _joined_m     = st.session_state.data.get("members", {}).get(item["name"], {}).get("joined")
    if last:
        last_str = str(last)
    elif _joined_m:
        last_str = f"{_joined_m[:4]}年{_joined_m[5:]}月加入"
    else:
        last_str = "無紀錄"
    leave_str     = "　請假：" + ", ".join(leaves_sorted) if leaves_sorted else ""
    status        = compute_status(last, set(leaves_sorted), _joined_m)
    row_cls       = status_to_row_class(status)

    if st.session_state.get(f"stat_edit_{key}"):
        st.markdown(f"<div class='edit-box'>✏️ 編輯成員：{item['name']}</div>", unsafe_allow_html=True)
        with st.form(key=f"stat_form_{key}"):
            new_display = st.text_input("顯示名稱", item['name'])
            b1, b2, b3  = st.columns(3)
            if b1.form_submit_button("💾 儲存", type="primary"):
                load_data.clear()
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
                if save_data(cur):
                    st.session_state.data = cur
                    st.session_state['_skip_data_reload'] = True
                    build_stats.clear()
                    st.session_state[f"stat_edit_{key}"] = False
                    st.toast("✅ 名稱已更新"); time.sleep(0.5); st.rerun()
                else:
                    st.error("❌ 更新未成功儲存，請再試一次。")
            if b2.form_submit_button("取消"):
                st.session_state[f"stat_edit_{key}"] = False; st.rerun()
            if b3.form_submit_button("🚪 退群", type="secondary"):
                load_data.clear()
                cur = load_data(); cur.setdefault("removed_members", [])
                if key not in cur["removed_members"]: cur["removed_members"].append(key)
                if save_data(cur):
                    st.session_state.data = cur
                    st.session_state['_skip_data_reload'] = True
                    build_stats.clear()
                    st.session_state[f"stat_edit_{key}"] = False
                    st.toast(f"👋 {item['name']} 已從統計移除"); time.sleep(0.5); st.rerun()
                else:
                    st.error("❌ 更新未成功儲存，請再試一次。")
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
                    load_data.clear()
                    cur = load_data(); cur.setdefault("removed_members", [])
                    if key not in cur["removed_members"]: cur["removed_members"].append(key)
                    if save_data(cur):
                        st.session_state.data = cur
                        st.session_state['_skip_data_reload'] = True
                        build_stats.clear()
                        st.toast(f"👋 {item['name']} 已移除"); time.sleep(0.5); st.rerun()
                    else:
                        st.error("❌ 更新未成功儲存，請再試一次。")


def render_stats(raw_data: dict):
    # 已隱藏的舊場次搬到封存分頁了，這裡合併回來，統計數字（出席率/警示狀態）才會跟以前一樣準確
    combined_sessions = {**load_archive(), **raw_data["sessions"]}
    all_dates_tuple  = tuple(sorted(combined_sessions.keys()))
    rained_out_tuple = tuple(raw_data.get("rained_out", []))

    stats, signups, future_signups = build_stats(
        sessions_json    = json.dumps(combined_sessions, ensure_ascii=False),
        leaves_json      = json.dumps(raw_data["leaves"],   ensure_ascii=False),
        rained_out_tuple = rained_out_tuple,
        all_dates_tuple  = all_dates_tuple,
    )

    removed     = set(raw_data.get("removed_members", []))
    # 手動加入的成員也納入統計
    for _mname, _minfo in raw_data.get("members", {}).items():
        _mk = normalize_name(_mname)
        if _mk not in stats and _mk not in removed:
            stats[_mk] = {"name": _mname, "attend": 0, "last_date": None, "leaves": set()}
    active_keys = [k for k in sorted(stats.keys()) if k not in removed]

    STATUS_ORDER = ["🟢", "🟡", "🔴", "🏖️"]
    STATUS_LABEL = {"🟢": "🟢 活躍", "🟡": "🟡 預警", "🔴": "🔴 逾期", "🏖️": "🏖️ 請假中"}

    groups: dict[str, list] = {"🟢": [], "🟡": [], "🔴": [], "🏖️": []}
    for key in active_keys:
        item   = stats[key]
        _jm2   = st.session_state.data.get("members", {}).get(item["name"], {}).get("joined")
        status = compute_status(item["last_date"], set(item["leaves"]), _jm2)
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
            # 有紀錄的
            for key, item in sorted(removed_stats.items(), key=lambda x: x[1]['name']):
                c1, c2, c3 = st.columns([4, 1, 1])
                c1.markdown(f"**{item['name']}**")
                with c2:
                    if st.button("↩️ 恢復", key=f"stat_restore_{key}"):
                        load_data.clear()
                        cur = load_data()
                        if key in cur.get("removed_members", []): cur["removed_members"].remove(key)
                        if save_data(cur):
                            st.session_state.data = cur
                            st.session_state['_skip_data_reload'] = True
                            build_stats.clear()
                            st.toast(f"✅ {item['name']} 已恢復"); time.sleep(0.5); st.rerun()
                        else:
                            st.error("❌ 更新未成功儲存，請再試一次。")
                with c3:
                    with st.popover("🗑️"):
                        st.warning(f"永久刪除「{item['name']}」所有紀錄？此操作無法復原！", icon="⚠️")
                        if st.button("確定永久刪除", key=f"stat_purge_{key}", type="primary"):
                            load_data.clear()
                            cur = load_data()
                            if key in cur.get("removed_members", []): cur["removed_members"].remove(key)
                            for sd in cur["sessions"]:
                                cur["sessions"][sd] = [p for p in cur["sessions"][sd] if normalize_name(p['name']) != key]
                            for rn in list(cur["leaves"].keys()):
                                if normalize_name(rn) == key: del cur["leaves"][rn]
                            if save_data(cur):
                                st.session_state.data = cur
                                st.session_state['_skip_data_reload'] = True
                                build_stats.clear()
                                st.toast(f"🗑️ {item['name']} 所有資料已永久刪除"); time.sleep(0.5); st.rerun()
                            else:
                                st.error("❌ 刪除未成功儲存，請再試一次。")
            # 沒有歷史紀錄的
            no_record = [k for k in removed if k not in stats]
            for key in sorted(no_record):
                c1, c2, c3 = st.columns([4, 1, 1])
                c1.markdown(f"**{key}**（無歷史紀錄）")
                with c2:
                    if st.button("↩️ 恢復", key=f"stat_restore_{key}"):
                        load_data.clear()
                        cur = load_data()
                        if key in cur.get("removed_members", []): cur["removed_members"].remove(key)
                        if save_data(cur):
                            st.session_state.data = cur
                            st.session_state['_skip_data_reload'] = True
                            build_stats.clear()
                            st.toast(f"✅ 已恢復"); time.sleep(0.5); st.rerun()
                        else:
                            st.error("❌ 更新未成功儲存，請再試一次。")
                with c3:
                    with st.popover("🗑️"):
                        st.warning(f"永久刪除「{key}」？此操作無法復原！", icon="⚠️")
                        if st.button("確定永久刪除", key=f"stat_purge_{key}", type="primary"):
                            load_data.clear()
                            cur = load_data()
                            if key in cur.get("removed_members", []): cur["removed_members"].remove(key)
                            if save_data(cur):
                                st.session_state.data = cur
                                st.session_state['_skip_data_reload'] = True
                                build_stats.clear()
                                st.toast(f"🗑️ 已永久刪除"); time.sleep(0.5); st.rerun()
                            else:
                                st.error("❌ 刪除未成功儲存，請再試一次。")

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
st.markdown(
    '''<div style="display:flex;justify-content:center;margin-bottom:16px;"><div style="background:white;border-radius:20px;overflow:hidden;display:inline-flex;align-items:stretch;border:1px solid #e8e6e0;box-shadow:0 2px 12px rgba(0,0,0,0.06);"><div style="width:130px;flex-shrink:0;overflow:hidden;position:relative;"><img src="https://raw.githubusercontent.com/sandy58328/basketball-signup/main/assets/header.jpg" style="width:100%;height:100%;object-fit:cover;object-position:30% center;display:block;" alt=""><div style="position:absolute;top:0;right:0;bottom:0;width:15%;background:linear-gradient(to right,transparent,white);"></div></div><div style="padding:20px 22px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:4px;"><div style="font-size:17px;font-weight:900;color:#1e293b;line-height:1.3;">晴女 ☀️ 在場邊等妳 🌈</div><div style="font-size:13px;color:#64748b;font-weight:600;">Keep Playing, Keep Shining</div><div style="margin-top:8px;display:table;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:30px;padding:4px 13px;font-size:12px;font-weight:600;color:#475569;white-space:nowrap;">📍 朱崙公園 &nbsp;|&nbsp; 🕑 19:00</div></div></div></div>''',
    unsafe_allow_html=True
)

if st.session_state.is_admin:
    st.markdown('<div style="text-align:center"><span class="admin-badge">⚙️ 管理員模式</span></div>', unsafe_allow_html=True)

if not check_db_connection():
    st.markdown('<div class="db-status-err">❌ 資料庫連線異常，請重新整理或聯絡管理員</div>', unsafe_allow_html=True)
    st.stop()

if st.session_state.pop('_skip_data_reload', False):
    pass  # 上一個動作剛存檔完，已經知道最新資料，不用馬上再問一次 Google，省一次網路來回
else:
    st.session_state.data = load_data()
auto_archive_old_sessions()  # 自動只留近兩個月場次，其餘搬去封存（資料不會不見，統計照算）


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
        _today = taipei_today()
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
        count_txt  = f"{play_cnt}/{MAX_CAPACITY}" + (f" +{wait_cnt}" if wait_cnt > 0 else "")
        # 整張卡片就是按鈕，用 label 排版
        _today_d   = taipei_today()
        _dobj      = datetime.strptime(d, "%Y-%m-%d").date()
        _delta     = (_dobj - _today_d).days
        if _delta < 0:    _day_hint = "已結束"
        elif _delta == 0: _day_hint = "今天 🔥"
        elif _delta == 1: _day_hint = "明天"
        else:             _day_hint = f"{_delta} 天後"
        # 報名狀態圖示：一眼看出可不可以報名，不用點進去
        _cutoff       = (datetime.strptime(d, "%Y-%m-%d") - timedelta(days=1)).replace(hour=12, minute=0, second=0)
        _now          = datetime.now(TZ_TAIPEI).replace(tzinfo=None)
        _card_expired = _now > _cutoff
        _hours_left   = (_cutoff - _now).total_seconds() / 3600
        if is_rain:            status_icon = "☔"
        elif _card_expired:    status_icon = "⛔"
        elif _hours_left <= 6: status_icon = "⏰"
        else:                  status_icon = "✅"
        btn_label  = f"{status_icon} {month}/{day}\n{_day_hint} · {count_txt} 人"
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
            is_expired    = datetime.now(TZ_TAIPEI).replace(tzinfo=None) > cutoff
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
                # 報名規則
                with st.expander("📌 報名規則說明", expanded=False):
                    st.markdown("""<div class="rules-box">
                        <div class="rules-header">📌 報名須知</div>
                        <div class="rules-row"><span class="rules-icon">🔴</span>
                            <div class="rules-content"><b>資格與規範</b>：採實名制。僅限 <b>⭐晴女</b> 報名。欲事後補報朋友，請用原名再次填寫即可 (含自己上限3位)。</div></div>
                        <div class="rules-row"><span class="rules-icon">🟠</span>
                            <div class="rules-content"><b>📣加油團</b>：團員若「不打球但帶朋友」請勾此項。本人不佔名額，但朋友會佔打球名額。</div></div>
                        <div class="rules-row"><span class="rules-icon">🟡</span>
                            <div class="rules-content"><b>優先機制</b>：正選 20 人。當人數超過時，<b>⭐晴女</b> 享有進入正選名單之優先權。</div></div>
                        <div class="rules-row"><span class="rules-icon">🟢</span>
                            <div class="rules-content"><b>時間與修改</b>：截止於前一日 12:00。</div></div>
                        <div class="rules-row"><span class="rules-icon">🔵</span>
                            <div class="rules-content"><b>出席要求</b>：每兩個月至少出席一次，請假不得連續超過兩個月。</div></div>
                        <div class="rules-footer">有任何問題請找最美管理員們 ❤️</div>
                    </div>""", unsafe_allow_html=True)
                # 截止倒數
                if not is_expired:
                    _remaining = cutoff - datetime.now(TZ_TAIPEI).replace(tzinfo=None)
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
                        st.caption("⚠️ 請輸入與 Line 群組**相同**的名字")
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
                                    load_data.clear()  # 強制重讀最新資料，避免跟同時間報名的人互相覆蓋
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
                                        # 自動刪除當月請假
                                        _signup_month = dk[:7]  # YYYY-MM
                                        _pname_norm = normalize_name(player_name)
                                        for _ln in list(latest.get("leaves", {}).keys()):
                                            if normalize_name(_ln) == _pname_norm:
                                                if _signup_month in latest["leaves"][_ln]:
                                                    latest["leaves"][_ln].remove(_signup_month)
                                                    if not latest["leaves"][_ln]:
                                                        del latest["leaves"][_ln]
                                                    break
                                        if save_data(latest):
                                            st.session_state.data = latest
                                            st.session_state['_skip_data_reload'] = True
                                            build_stats.clear()
                                            st.session_state['_tab_jump'] = i
                                            st.session_state['show_basket_anim'] = True
                                            st.session_state['scroll_to'] = full_name
                                            st.rerun()
                                        else:
                                            st.error("❌ 報名未成功儲存，請重新送出一次。")

            else:
                st.caption("⛔ 報名已截止（前一日 12:00）")

            # ── 我要請假 ──
            with st.expander("🏖️ 我要請假（長假登記）", expanded=False):
                with st.form(f"leave_form_{dk}", clear_on_submit=True):
                    leave_name  = st.text_input("姓名", key=f"ln_{dk}")
                    _today = taipei_today()
                    _months = [((_today + relativedelta(months=i)).strftime("%Y-%m"), (_today + relativedelta(months=i)).strftime("%Y 年 %m 月")) for i in range(0, 4)]
                    leave_month = st.selectbox("請假月份", options=[m[0] for m in _months], format_func=lambda x: dict(_months)[x], key=f"lm_{dk}")
                    if st.form_submit_button("送出假單") and leave_name:
                        load_data.clear()
                        _ld = load_data()
                        _ms = leave_month
                        _ld["leaves"].setdefault(leave_name, [])
                        if _ms not in _ld["leaves"][leave_name]:
                            _ld["leaves"][leave_name].append(_ms)
                            if save_data(_ld):
                                st.session_state.data = _ld
                                st.session_state['_skip_data_reload'] = True
                                build_stats.clear()
                                st.toast("✅ 已登記"); time.sleep(1); st.rerun()
                            else:
                                st.error("❌ 請假未成功儲存，請重新送出一次。")
                        else:
                            st.warning("已登記過這個月了")

            # ── 出席 & 請假狀態公開版 ──
            with st.expander("📊 出席 & 請假狀況", expanded=False):
                _stats, _, _ = build_stats(
                    json.dumps(st.session_state.data["sessions"]),
                    json.dumps(st.session_state.data.get("leaves", {})),
                    tuple(st.session_state.data.get("rained_out", [])),
                    tuple(sorted(st.session_state.data["sessions"].keys()))
                )
                # 手動加入的成員也納入
                _removed = set(st.session_state.data.get("removed_members", []))
                for _mn, _mi in st.session_state.data.get("members", {}).items():
                    _mk = normalize_name(_mn)
                    if _mk not in _stats and _mk not in _removed:
                        _stats[_mk] = {"name": _mn, "attend": 0, "last_date": None, "leaves": set()}
                _groups = {"🟢": [], "🟡": [], "🔴": []}
                _members_info = st.session_state.data.get("members", {})
                for _item in _stats.values():
                    _jm = _members_info.get(_item["name"], {}).get("joined")
                    _s = compute_status(_item["last_date"], set(_item["leaves"]), _jm)
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
                _now = taipei_today()
                _recent = set((_now - __import__("dateutil.relativedelta", fromlist=["relativedelta"]).relativedelta(months=i)).strftime("%Y-%m") for i in range(2))
                _leave_list = [((_leave_display[k], [m for m in sorted(_leave_merged[k]) if m >= (_now - __import__("dateutil.relativedelta", fromlist=["relativedelta"]).relativedelta(months=1)).strftime("%Y-%m")])) for k in sorted(_leave_merged) if _leave_merged[k]]
                _leave_list = [x for x in _leave_list if x[1]]
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

        tab_members, tab_sessions, tab_stats = st.tabs(["👥 成員", "📅 場次", "📊 統計"])

        with tab_members:
            # ── 成員管理 ──
            st.markdown('<div class="admin-section"><div class="admin-section-title">👥 成員管理</div>', unsafe_allow_html=True)
            _members = st.session_state.data.get("members", {})

            # 新增成員
            with st.form("add_member_form", clear_on_submit=True):
                _mc1, _mc2, _mc3 = st.columns([2, 2, 1])
                _new_name  = _mc1.text_input("姓名", placeholder="輸入成員姓名")
                _new_month = _mc2.selectbox("加入月份",
                    options=[(taipei_today() - relativedelta(months=i)).strftime("%Y-%m") for i in range(24)],
                    format_func=lambda x: x[:4] + " 年 " + x[5:] + " 月"
                )
                if _mc3.form_submit_button("➕ 新增", use_container_width=True) and _new_name:
                    load_data.clear()
                    _d = load_data()
                    _d.setdefault("members", {})
                    _d["members"][_new_name] = {"joined": _new_month}
                    if save_data(_d):
                        st.session_state.data = _d
                        st.session_state['_skip_data_reload'] = True
                        build_stats.clear()
                        st.toast(f"✅ 已新增 {_new_name}"); time.sleep(0.5); st.rerun()
                    else:
                        st.error("❌ 新增未成功儲存，請再試一次。")

            # 成員清單
            if _members:
                for _mname, _minfo in sorted(_members.items()):
                    _joined = _minfo.get("joined", "未知")
                    _mc1, _mc2, _mc3, _mc4 = st.columns([2, 2, 1, 1])
                    _mc1.markdown(f"**{_mname}**")
                    _mc2.caption(f"加入：{_joined[:4]}年{_joined[5:]}月" if len(_joined) >= 7 else _joined)
                    if _mc3.button("✏️", key=f"edit_m_{_mname}", help="修改"):
                        st.session_state[f"editing_member"] = _mname
                    if _mc4.button("🗑️", key=f"del_m_{_mname}", help="刪除"):
                        load_data.clear()
                        _d = load_data()
                        _d.setdefault("members", {})
                        if _mname in _d["members"]: del _d["members"][_mname]
                        if save_data(_d):
                            st.session_state.data = _d
                            st.session_state['_skip_data_reload'] = True
                            build_stats.clear()
                            st.toast(f"🗑️ 已刪除 {_mname}"); time.sleep(0.5); st.rerun()
                        else:
                            st.error("❌ 刪除未成功儲存，請再試一次。")
            # 編輯成員
            if st.session_state.get("editing_member"):
                _em = st.session_state["editing_member"]
                _em_info = _members.get(_em, {})
                with st.form(f"edit_member_{_em}", clear_on_submit=True):
                    st.caption(f"修改：{_em}")
                    _em_c1, _em_c2 = st.columns(2)
                    _em_newname  = _em_c1.text_input("新名字", value=_em)
                    _em_newmonth = _em_c2.selectbox("加入月份",
                        options=[(taipei_today() - relativedelta(months=i)).strftime("%Y-%m") for i in range(24)],
                        format_func=lambda x: x[:4] + " 年 " + x[5:] + " 月",
                        index=[(taipei_today() - relativedelta(months=i)).strftime("%Y-%m") for i in range(24)].index(_em_info.get("joined", taipei_today().strftime("%Y-%m"))) if _em_info.get("joined") in [(taipei_today() - relativedelta(months=i)).strftime("%Y-%m") for i in range(24)] else 0
                    )
                    _save, _cancel = st.columns(2)
                    if _save.form_submit_button("💾 儲存", use_container_width=True):
                        load_data.clear()
                        _d = load_data()
                        _d.setdefault("members", {})
                        if _em in _d["members"]: del _d["members"][_em]
                        _d["members"][_em_newname] = {"joined": _em_newmonth}
                        if save_data(_d):
                            st.session_state.data = _d
                            st.session_state['_skip_data_reload'] = True
                            build_stats.clear()
                            del st.session_state["editing_member"]
                            st.toast(f"✅ 已更新"); time.sleep(0.5); st.rerun()
                        else:
                            st.error("❌ 更新未成功儲存，請再試一次。")
                    if _cancel.form_submit_button("取消", use_container_width=True):
                        del st.session_state["editing_member"]
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_sessions:
            # ── 場次管理 ──
            st.markdown('<div class="admin-section"><div class="admin-section-title">📅 場次管理</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            with c1:
                new_date = st.date_input("新增日期", label_visibility="collapsed")
            with c2:
                if st.button("➕ 新增", use_container_width=True):
                    load_data.clear()
                    data = load_data()
                    if str(new_date) not in data["sessions"]:
                        data["sessions"][str(new_date)] = []
                        if save_data(data):
                            st.session_state.data = data
                            st.session_state['_skip_data_reload'] = True
                            st.rerun()
                        else:
                            st.error("❌ 新增未成功儲存，請再試一次。")
            if all_sessions:
                c1, c2 = st.columns([3, 1])
                with c1:
                    del_target = st.selectbox("刪除場次", all_sessions, label_visibility="collapsed")
                with c2:
                    if st.button("🗑️ 刪除", use_container_width=True):
                        load_data.clear()
                        data = load_data(); del data["sessions"][del_target]
                        if save_data(data):
                            st.session_state.data = data
                            st.session_state['_skip_data_reload'] = True
                            build_stats.clear(); st.rerun()
                        else:
                            st.error("❌ 刪除未成功儲存，請再試一次。")
            st.markdown('</div>', unsafe_allow_html=True)

            # ── 場次設定 ──
            if all_sessions:
                st.markdown('<div class="admin-section"><div class="admin-section-title">⚙️ 場次設定</div>', unsafe_allow_html=True)
                _hidden_all     = st.session_state.data.get("hidden", [])
                _hidden_default = [d for d in _hidden_all if d in all_sessions]        # 已封存的舊場次不在選項裡，預設值要濾掉，不然選單會報錯
                _hidden_archived = [d for d in _hidden_all if d not in all_sessions]   # 已封存的維持隱藏狀態，存檔時要補回去，不然會被誤判成「取消隱藏」
                hidden = st.multiselect("👁️ 隱藏場次", all_sessions, default=_hidden_default)
                if st.button("更新隱藏設定", use_container_width=True):
                    load_data.clear()
                    data = load_data()
                    newly_hidden = [k for k in hidden if k not in _hidden_all]
                    data["hidden"] = sorted(set(hidden) | set(_hidden_archived))
                    archive_hidden_sessions(newly_hidden, data)  # 搬去封存分頁，避免 A1 塞爆
                    if save_data(data):
                        st.session_state.data = data
                        st.session_state['_skip_data_reload'] = True
                        st.rerun()
                    else:
                        st.error("❌ 更新未成功儲存，請再試一次。")
                st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
                _rained_default = [d for d in st.session_state.data.get("rained_out", []) if d in all_sessions]
                new_rained = st.multiselect("☔ 天氣取消場次", all_sessions, default=_rained_default, key="rained_multiselect")
                if st.button("更新天氣取消設定", use_container_width=True):
                    load_data.clear()
                    data = load_data(); data["rained_out"] = new_rained
                    if save_data(data):
                        st.session_state.data = data
                        st.session_state['_skip_data_reload'] = True
                        build_stats.clear()
                        st.toast("✅ 已更新"); time.sleep(0.5); st.rerun()
                    else:
                        st.error("❌ 更新未成功儲存，請再試一次。")
                st.markdown('</div></div>', unsafe_allow_html=True)

            # ── 編輯隱藏場次 ──
            with st.expander("🕵️ 編輯隱藏場次資料", expanded=False):
                hidden_dates = st.session_state.data.get("hidden", [])
                if hidden_dates:
                    target_hidden = st.selectbox("選擇日期", sorted(hidden_dates))
                    if target_hidden:
                        _archive = load_archive()
                        _hidden_players = st.session_state.data["sessions"].get(target_hidden) or _archive.get(target_hidden, [])
                        render_list(_hidden_players, target_hidden, can_edit=False, is_admin_mode=True)
                else:
                    st.write("目前無隱藏場次")

        with tab_stats:
            # ── 出席統計 ──
            st.markdown('<div class="admin-section"><div class="admin-section-title">📊 出席統計報表</div>', unsafe_allow_html=True)
            st.caption("✏️ 改名　🚪 退群（移至下方，可恢復或永久刪除）")
            st.markdown('</div>', unsafe_allow_html=True)
            render_stats(st.session_state.data)
