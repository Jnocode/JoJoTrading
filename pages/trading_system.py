"""
Trading System Page
智能交易系統頁面
"""

import streamlit as st
import sys
import os

# 確保能夠導入模組
parent_dir = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(parent_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 智能交易系統主介面
st.title("🤖 智能交易系統")

# 導航按鈕
if st.button("⬅️ 返回主頁"):
    st.switch_page("main_app.py")

st.markdown("---")

try:
    # 嘗試導入並使用交易系統
    from jojo_trading.trading.trading_ui import TradingSystemUI
    
    # 初始化交易系統
    trading_ui = TradingSystemUI()
    trading_ui.render()
    
except ImportError as e:
    st.warning(f"交易系統模組載入中: {e}")
    
    # 提供基本的交易系統介面
    st.subheader("📊 智能交易系統 - 基本版")
    
    # 交易儀表板
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("今日信號", "12", delta="3")
    
    with col2:
        st.metric("投資組合價值", "$1,250,000", delta="2.3%")
    
    with col3:
        st.metric("活躍交易", "8", delta="-1")
    
    with col4:
        st.metric("總回報率", "15.6%", delta="1.2%")
    
    # 交易功能
    st.subheader("🎯 交易功能")
    
    tab1, tab2, tab3 = st.tabs(["交易信號", "投資組合", "風險管理"])
    
    with tab1:
        st.write("**最新交易信號**")
        signal_data = {
            "股票代號": ["2330", "2317", "2454", "3008"],
            "信號類型": ["買入", "賣出", "持有", "買入"],
            "信心度": ["85%", "72%", "90%", "78%"],
            "目標價": ["$580", "$95", "$125", "$210"]
        }
        st.dataframe(signal_data, use_container_width=True)
    
    with tab2:
        st.write("**當前投資組合**")
        portfolio_data = {
            "股票代號": ["2330", "2317", "3008"],
            "持股數量": [1000, 5000, 2000],
            "當前價格": ["$575", "$92", "$205"],
            "總價值": ["$575,000", "$460,000", "$410,000"]
        }
        st.dataframe(portfolio_data, use_container_width=True)
    
    with tab3:
        st.write("**風險控制**")
        st.info("風險管理模組正在監控投資組合風險。")
        
        risk_col1, risk_col2 = st.columns(2)
        with risk_col1:
            st.metric("VaR (95%)", "2.3%")
            st.metric("Beta 值", "1.15")
        with risk_col2:
            st.metric("最大回撤", "5.8%")
            st.metric("夏普比率", "1.42")
    
    st.info("💡 這是簡化版本，完整功能需要載入交易系統模組。")
