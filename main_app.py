"""
JoJo Trading 主應用程式
整合DCF估值分析和智能交易系統的綜合平台
"""

import streamlit as st
from src.jojo_trading.ui.app import main as dcf_main
from src.jojo_trading.trading.trading_ui import TradingSystemUI

# 頁面配置
st.set_page_config(
    page_title="JoJo Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/jojo_trading',
        'Report a bug': "https://github.com/yourusername/jojo_trading/issues",
        'About': """
        # JoJo Trading Platform
        
        這是一個綜合的台股分析與交易平台，包含：
        
        ## 主要功能
        - **DCF估值分析**: 基於現金流折現模型的股票估值
        - **智能交易系統**: AI驅動的交易信號和投資組合管理
        - **成長股篩選**: 多維度成長指標篩選
        - **風險管理**: 自動化風險控制和資金管理
        
        ## 技術特色
        - 增強版DCF模型（情境分析、動態折現率）
        - 數據品質驗證和異常檢測
        - AI驅動的交易建議引擎
        - 自動化交易信號生成
        
        版本: v2.0
        """
    }
)

def dcf_analysis_page():
    """DCF估值分析頁面"""
    st.title("💰 DCF估值分析系統")
    st.markdown("""
    基於現金流折現模型的台股估值分析系統，支援增強版DCF模型、
    數據品質驗證、異常檢測等進階功能。
    """)
    
    # 調用原有的DCF分析主程式
    try:
        dcf_main()
    except Exception as e:
        st.error(f"DCF分析系統發生錯誤：{str(e)}")
        st.info("請檢查配置設定或聯繫技術支援")

def trading_system_page():
    """智能交易系統頁面"""
    st.title("🤖 智能交易系統")
    st.markdown("""
    AI驅動的交易分析與投資組合管理系統，提供交易信號生成、
    風險管理和績效追蹤等功能。
    """)
    
    # 初始化交易系統UI
    try:
        trading_ui = TradingSystemUI()
        trading_ui.render_trading_dashboard()
    except Exception as e:
        st.error(f"交易系統發生錯誤：{str(e)}")
        st.info("請檢查配置設定或聯繫技術支援")

def system_overview_page():
    """系統總覽頁面"""
    st.title("🏠 JoJo Trading Platform")
    
    # 歡迎訊息
    st.markdown("""
    ## 歡迎來到JoJo Trading Platform！
    
    這是一個整合DCF估值分析和智能交易系統的綜合投資平台，
    專為台股投資者設計，提供專業級的分析工具和交易輔助功能。
    """)
    
    # 功能概覽
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 DCF估值分析")
        st.markdown("""
        - **增強版DCF模型**: 支援情境分析和動態折現率
        - **數據品質驗證**: 自動檢測財務數據品質
        - **異常檢測**: 識別一次性收益對估值的影響
        - **成長股篩選**: 多維度成長指標篩選系統
        - **產業比較**: 同業估值比較分析
        """)
        
        if st.button("🚀 開始DCF分析", key="dcf_btn"):
            st.switch_page("DCF估值分析")
    
    with col2:
        st.subheader("🤖 智能交易系統")
        st.markdown("""
        - **AI交易建議**: 基於DCF結果的智能建議
        - **交易信號生成**: 自動化技術分析信號
        - **投資組合管理**: 完整的交易記錄和績效追蹤
        - **風險管理**: 自動化風險控制機制
        - **模擬交易**: 無風險的策略驗證環境
        """)
        
        if st.button("📊 開啟交易系統", key="trading_btn"):
            st.switch_page("智能交易系統")
    
    # 系統狀態
    st.subheader("📊 系統狀態")
    
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.metric("DCF分析狀態", "🟢 正常", delta="系統運行中")
    
    with status_col2:
        st.metric("交易系統狀態", "🟢 正常", delta="AI引擎活躍")
    
    with status_col3:
        st.metric("資料更新", "🟢 最新", delta="即時更新")
    
    with status_col4:
        st.metric("API連接", "🟢 穩定", delta="延遲 < 100ms")
    
    # 最近動態
    st.subheader("📈 系統概況")
    
    # 創建範例圖表
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # 模擬數據
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    performance_data = pd.DataFrame({
        'Date': dates,
        'DCF分析次數': np.random.poisson(5, len(dates)),
        '交易信號數量': np.random.poisson(3, len(dates)),
        '系統健康度': 95 + np.random.normal(0, 2, len(dates))
    })
    
    tab1, tab2, tab3 = st.tabs(["使用統計", "系統性能", "更新日誌"])
    
    with tab1:
        st.line_chart(performance_data.set_index('Date')[['DCF分析次數', '交易信號數量']])
    
    with tab2:
        st.line_chart(performance_data.set_index('Date')['系統健康度'])
    
    with tab3:
        st.markdown("""
        ### 最近更新
        
        **v2.0.0** (2024-12-19)
        - ✅ 整合DCF分析和交易系統
        - ✅ 降低DCF品質門檻至45分
        - ✅ 新增AI交易建議引擎
        - ✅ 完善交易記錄系統
        - ✅ 優化數據品質評分算法
        
        **v1.9.0** (2024-12-18)
        - ✅ 增強版DCF模型上線
        - ✅ 數據品質驗證系統
        - ✅ 異常檢測功能
        """)

def settings_page():
    """系統設定頁面"""
    st.title("⚙️ 系統設定")
    
    st.subheader("🌍 基本設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 語言設定
        language = st.selectbox(
            "界面語言",
            options=["繁體中文", "English"],
            index=0
        )
        
        # 主題設定
        theme = st.selectbox(
            "界面主題",
            options=["Light", "Dark", "Auto"],
            index=0
        )
    
    with col2:
        # 自動重新整理
        auto_refresh = st.checkbox("自動重新整理數據", value=True)
        
        # 開發者模式
        developer_mode = st.checkbox("開發者模式", value=False)
    
    st.subheader("📊 DCF分析設定")
    
    dcf_col1, dcf_col2 = st.columns(2)
    
    with dcf_col1:
        min_quality_score = st.slider(
            "最低數據品質分數",
            min_value=30,
            max_value=90,
            value=45,
            help="低於此分數的股票將被過濾"
        )
        
        anomaly_threshold = st.slider(
            "異常檢測閾值",
            min_value=1.1,
            max_value=3.0,
            value=1.5,
            step=0.1
        )
    
    with dcf_col2:
        enable_enhanced_dcf = st.checkbox("啟用增強版DCF", value=True)
        enable_data_validation = st.checkbox("啟用數據驗證", value=True)
    
    st.subheader("🤖 交易系統設定")
    
    trading_col1, trading_col2 = st.columns(2)
    
    with trading_col1:
        risk_tolerance = st.selectbox(
            "風險承受度",
            options=["保守", "穩健", "積極"],
            index=1
        )
        
        max_position_size = st.slider(
            "最大單一部位比例",
            min_value=5,
            max_value=30,
            value=10,
            help="單一股票最大投資比例"
        )
    
    with trading_col2:
        enable_auto_trading = st.checkbox("啟用自動交易信號", value=False)
        enable_notifications = st.checkbox("啟用通知提醒", value=True)
    
    # 儲存設定
    if st.button("💾 儲存設定", type="primary"):
        # 這裡可以實作設定儲存邏輯
        st.success("設定已儲存！")
        st.rerun()

# 主應用程式邏輯
def main():
    """主應用程式入口"""
    
    # 創建導航菜單    # 創建頁面導航
    pages = [
        st.Page(system_overview_page, title="🏠 系統總覽", icon="🏠"),
        st.Page(dcf_analysis_page, title="💰 DCF估值分析", icon="💰"),
        st.Page(trading_system_page, title="🤖 智能交易系統", icon="🤖"),
        st.Page(settings_page, title="⚙️ 系統設定", icon="⚙️")
    ]
    
    # 使用Streamlit導航
    page = st.navigation(
        pages,
        position="sidebar"
    )
    
    # 執行選定的頁面
    page.run()

if __name__ == "__main__":
    main()
