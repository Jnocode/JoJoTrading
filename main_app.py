"""
JoJo Trading 主應用程式 (Human-Centered UX v3.0)
修正了強迫登入的問題，優化導航結構，提供更流暢的使用者體驗。
"""

import streamlit as st
import sys
import os
import time

# -----------------------------------------------------------------------------
# 1. 頁面基礎配置 (必須是第一行 Streamlit 指令)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="JoJo Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/jojo_trading',
        'About': "# JoJo Trading Platform v3.0"
    }
)

# [CSS HACK] Hide Default Sidebar Navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 環境與路徑設置
# -----------------------------------------------------------------------------
# 添加 src 和 scripts 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
scripts_path = os.path.join(current_dir, 'scripts')

if src_path not in sys.path:
    sys.path.insert(0, src_path)
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

# 嘗試導入核心模組
try:
    from update_stock_db import update_database
except ImportError:
    update_database = None

from jojo_trading.core.shioaji_connector import ShioajiConnector
from jojo_trading.core.auth.broker_manager import BrokerProfileManager
try:
    from jojo_trading.core.watchlist_manager import WatchlistManager
    from jojo_trading.ui.dashboard import DashboardUI
except ImportError:
    WatchlistManager = None
    DashboardUI = None
try:
    from jojo_trading.core.network_manager import NetworkManager
except ImportError:
    NetworkManager = None

# -----------------------------------------------------------------------------
# 3. 延遲導入 UI 組件 (避免循環依賴)
# -----------------------------------------------------------------------------
def get_dcf_modules():
    try:
        from jojo_trading.ui.app import run_individual_dcf, run_sector_screening
        return run_individual_dcf, run_sector_screening
    except Exception as e:
        return None, None

def get_trading_ui():
    try:
        from jojo_trading.trading.trading_ui import TradingSystemUI
        return TradingSystemUI()
    except Exception as e:
        return None

def get_simulation_ui():
    try:
        from jojo_trading.trading.simulation_ui import SimulatedTradingUI
        return SimulatedTradingUI()
    except Exception as e:
        return None

# -----------------------------------------------------------------------------
# 4. 側邊欄：全域功能 (連線與導航)
# -----------------------------------------------------------------------------
def render_sidebar():
    """渲染側邊欄：包含連線狀態、導航選單"""
    st.sidebar.title("🚀 JoJo Trading")
    
    # --- A. 連線管理區塊 (不再擋在主畫面) ---
    sj_conn = ShioajiConnector()
    
    # 連線狀態指示燈
    if sj_conn.is_connected:
        st.sidebar.success(f"🟢 已連線: {st.session_state.get('current_broker_profile', 'Unknown')}")
        if st.sidebar.button("斷開連線 (Disconnect)", key="disconnect_btn", use_container_width=True):
            sj_conn.is_connected = False
            sj_conn.api = None
            st.session_state.current_broker_profile = None
            st.rerun()
    else:
        with st.sidebar.expander("🔐 券商連線 (Broker Connect)", expanded=False):
            render_login_form(sj_conn)

    st.sidebar.markdown("---")
    
    # --- B. 主要導航 (使用 Radio Button 減少點擊成本) ---
    
    # 定義導航選項與對應圖示
    nav_options = {
        "🏠 儀表板 (Dashboard)": "dashboard",
        "📊 市場分析": "market_analysis", 
        "🎮 模擬專區": "simulation",
        "💰 交易系統": "real_trading",
        "⚙️ 系統設定": "settings"
    }
    
    selected_label = st.sidebar.radio(
        "主要功能",
        options=list(nav_options.keys()),
        index=0,
        label_visibility="collapsed"
    )
    
    st.session_state.current_page_key = nav_options[selected_label]
    
    # 網路狀態
    if NetworkManager:
        st.sidebar.markdown("---")
        nm = NetworkManager()
        nm.render_sidebar(st)

def render_login_form(sj_conn):
    """渲染登入表單 (精簡版)"""
    profiles = BrokerProfileManager.get_profiles()
    profile_names = [p['profile_name'] for p in profiles]
    
    if not profile_names:
        st.warning("尚無帳號設定")
        st.info("請至「系統設定」新增")
        return

    selected_profile = st.selectbox("選擇帳號", profile_names, key="sidebar_prof_sel")
    
    # 檢查是否需要密碼
    stored_pass_exists = False
    if selected_profile:
        prof_data = next((p for p in profiles if p['profile_name'] == selected_profile), None)
        if prof_data and prof_data.get('cert_pass'):
            stored_pass_exists = True
            
    ca_password = st.text_input("憑證密碼", type="password", 
                              placeholder="已儲存 (留白即可)" if stored_pass_exists else "請輸入",
                              key="sidebar_pass_input")
    
    if st.button("🚀 連線", type="primary", use_container_width=True, key="sidebar_connect_btn"):
        with st.spinner("連線中..."):
            try:
                full_prof = BrokerProfileManager.get_decrypted_profile(selected_profile)
                if full_prof:
                    final_pass = ca_password if ca_password else full_prof.get('cert_pass')
                    sj_conn.connect(
                        api_key=full_prof['api_key'],
                        secret_key=full_prof['secret_key'],
                        cert_path=full_prof['cert_path'],
                        cert_pass=final_pass,
                        person_id=full_prof['person_id'],
                        is_simulation=full_prof['is_simulation']
                    )
                    st.session_state['current_broker_profile'] = selected_profile
                    st.rerun()
            except Exception as e:
                st.error(f"連線失敗: {e}")

# -----------------------------------------------------------------------------
# 5. 主要內容路由
# -----------------------------------------------------------------------------
def main():
    # 初始化 session state
    if "db_updated" not in st.session_state:
        st.session_state.db_updated = False
        
    # 自動更新資料庫 (靜默執行或是顯示輕量進度)
    if not st.session_state.db_updated and update_database:
        with st.spinner("系統初始化中 (更新資料庫)..."):
            try:
                # 快速更新，不阻塞太久
                update_database(limit=5, progress_callback=None)
            except:
                pass 
        st.session_state.db_updated = True

    # 渲染側邊欄
    render_sidebar()
    
    # 根據選擇渲染主頁面
    page_key = st.session_state.get('current_page_key', 'dashboard')
    
    if page_key == 'dashboard':
        show_home_page()
    elif page_key == 'market_analysis':
        show_market_analysis_page()
    elif page_key == 'simulation':
        show_simulation_page()
    elif page_key == 'real_trading':
        show_trading_page()
    elif page_key == 'settings':
        show_settings_page()

# -----------------------------------------------------------------------------
# 6. 各頁面視圖函數
# -----------------------------------------------------------------------------
def show_home_page():
    if DashboardUI:
        dashboard = DashboardUI()
        dashboard.render()
    else:
        st.error("DashboardUI 模組未載入")

def show_market_analysis_page():
    """整合後的市場分析頁面"""
    st.title("📊 市場分析中心")
    
    tab1, tab2 = st.tabs(["📈 個股 DCF 估值", "🎯 類股篩選掃描"])
    
    # Lazy load modules
    run_individual, run_sector = get_dcf_modules()
    
    with tab1:
        if run_individual:
            run_individual()
        else:
            st.error("模組載入失敗")
            
    with tab2:
        if run_sector:
            run_sector()
        else:
            st.error("模組載入失敗")

# Removed individual pages as they are now merged
# def show_individual_dcf_page(): ...
# def show_sector_screening_page(): ...

def show_simulation_page():
    ui = get_simulation_ui()
    if ui:
        ui.render()
    else:
        st.error("模擬模組載入失敗")

def show_trading_page():
    sj_conn = ShioajiConnector()
    if not sj_conn.is_connected:
        st.error("⛔ [存取拒絕] 真實交易功能需要連接券商")
        st.info("請在左側側邊欄「🔐 券商連線」輸入帳號密碼進行連線。")
        st.markdown("---")
        st.markdown("### 為什麼我看到這個？")
        st.markdown("為了保護您的資產安全，真實下單與帳務查詢功能已被嚴格隔離。")
        st.markdown("**如果您只是想測試策略，請前往「🎮 模擬專區」。**")
        return

    ui = get_trading_ui()
    if ui:
        ui.render()
    else:
        st.error("交易模組載入失敗")

def show_settings_page():
    # 這裡可以保留原有的設定頁面邏輯，或者直接導入
    # 為了保持簡潔，這裡重寫一個包含帳號管理的設定頁面
    st.title("⚙️ 系統設定")
    
    tab1, tab2 = st.tabs(["👤 帳號管理", "🔧 系統參數"])
    
    with tab1:
        st.subheader("券商帳號設定")
        from jojo_trading.core.auth.broker_manager import BrokerProfileManager
        
        with st.form("settings_add_profile"):
            st.markdown("##### 新增帳號")
            c1, c2 = st.columns(2)
            name = c1.text_input("設定檔名稱 (Profile Name)")
            pid = c2.text_input("身分證號 (Person ID)")
            api = c1.text_input("API Key", type="password")
            secret = c2.text_input("Secret Key", type="password")
            cert_path = st.text_input("憑證路徑", value="D:/certificate/sinopac.pfx")
            cert_pass = st.text_input("憑證密碼 (選填，若填寫將加密儲存)", type="password")
            
            if st.form_submit_button("儲存"):
                BrokerProfileManager.save_profile(name, api, secret, pid, cert_path, cert_pass, False, bool(cert_pass))
                st.success("已儲存")
                time.sleep(1)
                st.rerun()
                
        # 刪除邏輯... (略，保持簡單)
        
    with tab2:
        st.subheader("外部資料源設定 (External Data Sources)")
        
        # FinMind Settings
        st.markdown("#### FinMind (台股歷史資料)")
        st.info("FinMind 提供台股歷史股價、財報、籌碼等重要數據。請至 [FinMind 官網](https://finmind.github.io/) 註冊會員並申請 API Token。")
        
        from jojo_trading.core.stock_database import StockDatabase
        db = StockDatabase()
        
        # Load current values
        fm_user = db.get_setting("FINMIND_USER_ID", "")
        fm_pass = db.get_setting("FINMIND_PASSWORD", "")
        fm_token = db.get_setting("FINMIND_API_TOKEN", "")
        
        with st.form("finmind_settings"):
            c1, c2 = st.columns(2)
            new_user = c1.text_input("FinMind User ID", value=fm_user)
            new_pass = c2.text_input("FinMind Password", value=fm_pass, type="password")
            new_token = st.text_input("FinMind API Token (JWT)", value=fm_token, type="password", help="登入 FinMind 獲取的長字串 Token，若填寫則優先使用")
            
            if st.form_submit_button("儲存 FinMind 設定"):
                db.set_setting("FINMIND_USER_ID", new_user)
                db.set_setting("FINMIND_PASSWORD", new_pass)
                db.set_setting("FINMIND_API_TOKEN", new_token)
                st.success("FinMind 設定已更新！")
                time.sleep(1)
                st.rerun()

        st.markdown("---")
        st.info("其他系統參數功能開發中...")

if __name__ == "__main__":
    main()
 
