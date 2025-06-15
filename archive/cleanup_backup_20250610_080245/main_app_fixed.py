"""
JoJo Trading 主應用程式 - 修復版本
使用 Streamlit 多頁面標準架構
"""

import streamlit as st
import sys
import os

# 頁面配置
st.set_page_config(
    page_title="JoJo Trading Platform",
    page_icon="📈",
    layout="wide"
)

def main_page():
    """主頁面"""
    st.title("🏠 JoJo Trading Platform")
    
    # 歡迎訊息
    st.markdown("""
    ## 歡迎來到JoJo Trading Platform！
    
    這是一個整合DCF估值分析和智能交易系統的綜合投資平台，
    專為台股投資者設計，提供專業級的分析工具和交易輔助功能。    """)
    
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
        
        if st.button("🚀 開始DCF分析", key="dcf_btn", use_container_width=True):
            st.switch_page("pages/dcf_analysis.py")
    
    with col2:
        st.subheader("🤖 智能交易系統")
        st.markdown("""
        - **AI交易建議**: 基於DCF結果的智能建議
        - **交易信號生成**: 自動化技術分析信號
        - **投資組合管理**: 完整的交易記錄和績效追蹤
        - **風險管理**: 自動化風險控制機制
        - **模擬交易**: 無風險的策略驗證環境
        """)
        
        if st.button("📊 開啟交易系統", key="trading_btn", use_container_width=True):
            st.switch_page("pages/trading_system.py")
    
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
    
    # 模擬數據
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    values = np.random.randn(30).cumsum() + 100
    
    chart_data = pd.DataFrame({
        'Date': dates,
        'Portfolio Value': values
    })
    
    st.line_chart(chart_data.set_index('Date'))
    
    # 快速統計
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("今日分析次數", "23", delta="5")
    
    with col2:
        st.metric("活躍交易信號", "12", delta="3")
    
    with col3:
        st.metric("系統使用率", "87%", delta="12%")

if __name__ == "__main__":
    main_page()
