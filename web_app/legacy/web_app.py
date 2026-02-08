"""
JoJo Analysis (Web UI)
主打功能：股票篩選、估值計算、市場分析
適用場景：雲端部署、輕量級分析、無需券商連線
"""

import streamlit as st
import sys
import os
import time
from pathlib import Path

# -----------------------------------------------------------------------------
# 1. 頁面基礎配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="JoJo Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# -----------------------------------------------------------------------------
# 3. 模組載入 (Lazy Loading)
# -----------------------------------------------------------------------------
def get_dashboard_ui():
    try:
        from jojo_trading.ui.dashboard import DashboardUI
        return DashboardUI()
    except Exception as e:
        return None

def get_dcf_modules():
    try:
        from jojo_trading.ui.app import run_individual_dcf, run_sector_screening
        return run_individual_dcf, run_sector_screening
    except Exception as e:
        return None, None

def get_screener_ui():
    try:
        from jojo_trading.ui.screener_ui import ScreenerUI
        return ScreenerUI()
    except Exception as e:
        return None

def get_news_dashboard_ui():
    try:
        from jojo_trading.ui.news_dashboard import NewsDashboardUI
        return NewsDashboardUI()
    except Exception as e:
        return None

# -----------------------------------------------------------------------------
# 4. 側邊欄導航
# -----------------------------------------------------------------------------
def render_sidebar():
    st.sidebar.title("📊 JoJo Analysis")
    st.sidebar.caption("Web Analytics Edition")
    st.sidebar.markdown("---")
    
    nav_options = {
        "🏠 市場儀表板": "dashboard",
        "🎯 股票篩選器": "screener",
        "💎 價值估算 (DCF)": "valuation",
        "📰 金十快訊 & AI熱度": "news",
    }
    
    selected_label = st.sidebar.radio(
        "功能導航",
        options=list(nav_options.keys()),
        index=0
    )
    
    st.session_state.current_web_page = nav_options[selected_label]
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 此版本僅提供分析功能，如需下單交易請使用 Desktop 版。")

# -----------------------------------------------------------------------------
# 5. 頁面視圖
# -----------------------------------------------------------------------------
def show_dashboard():
    ui = get_dashboard_ui()
    if ui:
        ui.render()
    else:
        st.info("儀表板載入中或模組未就緒...")

def show_screener():
    ui = get_screener_ui()
    if ui:
        ui.render()
    else:
        st.error("篩選器模組載入失敗")

def show_valuation():
    st.title("💎 企業價值估算 (DCF)")
    
    run_individual, run_sector = get_dcf_modules()
    
    tab1, tab2 = st.tabs(["個股詳細估值", "類股批次掃描"])
    
    with tab1:
        if run_individual:
            run_individual()
    with tab2:
        if run_sector:
            run_sector()

def show_news():
    ui = get_news_dashboard_ui()
    if ui:
        ui.render()
    else:
        st.error("新聞儀表板載入失敗")

# -----------------------------------------------------------------------------
# 6. 主程式進入點
# -----------------------------------------------------------------------------
def main():
    render_sidebar()
    
    page = st.session_state.get('current_web_page', 'dashboard')
    
    if page == 'dashboard':
        show_dashboard()
    elif page == 'screener':
        show_screener()
    elif page == 'valuation':
        show_valuation()
    elif page == 'news':
        show_news()

if __name__ == "__main__":
    main()
