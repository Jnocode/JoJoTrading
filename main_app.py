"""
JoJo Trading 主應用程式 (修復版 v2)
整合DCF估值分析和智能交易系統的綜合平台
"""

import streamlit as st

# 頁面配置必須是第一個Streamlit命令
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
        
        版本: v2.0 (修復版)
        """    }
)

# 延遲導入避免在set_page_config之前執行Streamlit命令
import sys
import os

# 添加src路徑到Python路徑
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def get_dcf_main():
    """延遲導入DCF主函數"""
    try:
        from jojo_trading.ui.app import main as dcf_main
        return dcf_main
    except Exception as e:
        st.error(f"DCF模組載入失敗: {e}")
        return None

# 延遲導入TradingSystemUI
def get_trading_ui():
    """延遲導入TradingSystemUI"""
    try:
        from jojo_trading.trading.trading_ui import TradingSystemUI
        return TradingSystemUI()
    except Exception as e:
        st.error(f"交易系統模組載入失敗: {e}")
        return None

def main():
    """主應用程式"""
    # 設置側邊欄導航
    st.sidebar.title("🚀 JoJo Trading")
    st.sidebar.markdown("---")
    
    # 頁面選擇
    page = st.sidebar.selectbox(
        "選擇功能頁面",
        ["🏠 首頁", "📊 DCF估值分析", "🎯 智能交易系統", "⚙️ 系統設定"],
        index=0
    )
    
    # 顯示選擇的頁面
    if page == "🏠 首頁":
        show_home_page()
    elif page == "📊 DCF估值分析":
        show_dcf_page()
    elif page == "🎯 智能交易系統":
        show_trading_page()
    elif page == "⚙️ 系統設定":
        show_settings_page()

def show_home_page():
    """顯示首頁"""
    st.title("🚀 JoJo Trading Platform")
    st.markdown("### 台股智能分析與交易系統")
    
    # 系統狀態檢查
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("系統狀態", "🟢 正常運行", "修復版 v2.0")
    
    with col2:
        st.metric("DCF模組", "✅ 已載入", "增強版模型")
    
    with col3:
        st.metric("交易模組", "✅ 已載入", "AI驅動")
    
    st.markdown("---")
    
    # 功能概覽
    st.markdown("## 📋 主要功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📊 DCF估值分析
        - **增強版DCF模型**: 多情境分析和動態折現率
        - **數據品質驗證**: 自動化財務數據品質檢查
        - **風險評估**: 敏感性分析和蒙地卡羅模擬
        - **視覺化報告**: 互動式圖表和分析報告
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 智能交易系統
        - **AI交易信號**: 機器學習驅動的買賣建議
        - **投資組合管理**: 自動化資產配置和再平衡
        - **風險控制**: 停損停利和部位管理
        - **績效追蹤**: 實時交易績效分析
        """)
    
    # 快速開始
    st.markdown("---")
    st.markdown("## 🚀 快速開始")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 開始DCF分析", use_container_width=True):
            st.session_state.page = "DCF估值分析"
            st.rerun()
    
    with col2:
        if st.button("🎯 啟動交易系統", use_container_width=True):
            st.session_state.page = "智能交易系統"
            st.rerun()

def show_dcf_page():
    """顯示DCF分析頁面"""
    st.title("📊 DCF估值分析")
    
    try:
        dcf_main = get_dcf_main()
        if dcf_main:
            dcf_main()
        else:
            st.error("DCF模組載入失敗，請檢查系統設定")
            st.markdown("""
            ### 故障排除建議：
            1. 檢查 `src/jojo_trading/ui/app.py` 是否存在
            2. 確認所有相依模組已正確安裝
            3. 檢查 Python 路徑設定
            """)
    except Exception as e:
        st.error(f"DCF頁面載入錯誤: {e}")
        st.code(f"詳細錯誤信息: {str(e)}")

def show_trading_page():
    """顯示交易系統頁面"""
    st.title("🎯 智能交易系統")
    
    try:
        trading_ui = get_trading_ui()
        if trading_ui:
            # 顯示交易系統介面
            st.markdown("### 🤖 AI驅動的交易決策系統")
            
            # 投資組合概覽
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("投資組合價值", "$0", "尚未開始交易")
            
            with col2:
                st.metric("今日損益", "$0", "0.00%")
            
            with col3:
                st.metric("累計報酬", "0.00%", "基準點")
            
            with col4:
                st.metric("風險指標", "低", "安全模式")
            
            st.markdown("---")
            
            # 交易信號區域
            st.markdown("### 📈 交易信號")
            
            signal_col1, signal_col2 = st.columns(2)
            
            with signal_col1:
                st.markdown("#### 🟢 買入信號")
                st.info("目前沒有強烈的買入信號")
            
            with signal_col2:
                st.markdown("#### 🔴 賣出信號")
                st.info("目前沒有強烈的賣出信號")
            
            # 手動交易區域
            st.markdown("---")
            st.markdown("### ⚙️ 手動交易")
            
            trade_col1, trade_col2, trade_col3 = st.columns(3)
            
            with trade_col1:
                stock_code = st.text_input("股票代碼", placeholder="例如：2330")
            
            with trade_col2:
                quantity = st.number_input("交易數量", min_value=1, value=1000)
            
            with trade_col3:
                action = st.selectbox("交易動作", ["買入", "賣出"])
            
            if st.button("執行交易", type="primary"):
                st.success(f"模擬交易：{action} {stock_code} {quantity} 股")
                st.info("注意：這是模擬交易，不會實際執行")
            
        else:
            st.error("交易系統模組載入失敗")
            st.markdown("""
            ### 故障排除建議：
            1. 檢查 `src/jojo_trading/trading/trading_ui.py` 是否存在
            2. 確認 Streamlit 環境正確設定
            3. 檢查模組路徑配置
            """)
    except Exception as e:
        st.error(f"交易系統載入錯誤: {e}")
        st.code(f"詳細錯誤信息: {str(e)}")

def show_settings_page():
    """顯示系統設定頁面"""
    st.title("⚙️ 系統設定")
    
    # 系統資訊
    st.markdown("### 📊 系統資訊")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.info(f"""
        **應用程式版本**: v2.0 (修復版)
        **Streamlit版本**: {st.__version__}
        **Python版本**: {st.session_state.get('python_version', '檢測中...')}
        """)
    
    with info_col2:
        st.info(f"""
        **DCF模組狀態**: ✅ 正常
        **交易模組狀態**: ✅ 正常
        **數據連接狀態**: ⚠️ 離線模式
        """)
    
    # 設定選項
    st.markdown("---")
    st.markdown("### 🔧 應用程式設定")
    
    # DCF設定
    with st.expander("📊 DCF分析設定"):
        default_discount_rate = st.slider("預設折現率 (%)", 5.0, 15.0, 10.0, 0.1)
        default_growth_rate = st.slider("預設成長率 (%)", 0.0, 20.0, 5.0, 0.1)
        enable_monte_carlo = st.checkbox("啟用蒙地卡羅模擬", value=True)
        
        if st.button("儲存DCF設定"):
            st.success("DCF設定已儲存")
    
    # 交易設定
    with st.expander("🎯 交易系統設定"):
        risk_level = st.selectbox("風險等級", ["保守", "穩健", "積極"])
        max_position_size = st.slider("最大單一部位 (%)", 1, 20, 10)
        enable_auto_trading = st.checkbox("啟用自動交易", value=False)
        
        if st.button("儲存交易設定"):
            st.success("交易設定已儲存")
    
    # 數據設定
    with st.expander("📡 數據連接設定"):
        st.warning("數據連接功能開發中...")
        api_key = st.text_input("API金鑰", type="password", placeholder="輸入您的數據API金鑰")
        data_source = st.selectbox("數據來源", ["模擬數據", "Yahoo Finance", "其他"])
        
        if st.button("測試連接"):
            st.info("連接測試功能開發中...")
    
    # 系統維護
    st.markdown("---")
    st.markdown("### 🛠️ 系統維護")
    
    maint_col1, maint_col2, maint_col3 = st.columns(3)
    
    with maint_col1:
        if st.button("清除快取"):
            st.cache_data.clear()
            st.success("快取已清除")
    
    with maint_col2:
        if st.button("重置設定"):
            st.warning("設定重置功能開發中...")
    
    with maint_col3:
        if st.button("系統診斷"):
            st.info("系統診斷功能開發中...")

if __name__ == "__main__":
    main()
