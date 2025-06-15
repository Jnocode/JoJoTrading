"""
DCF Valuation Analysis Page
整合的DCF估值分析系統介面
"""

import streamlit as st
import sys
import os

# 確保能夠導入模組
parent_dir = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(parent_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 頁面標題
st.title("📊 DCF估值分析")

# 導航按鈕
if st.button("⬅️ 返回主頁"):
    st.switch_page("main_app.py")

st.markdown("---")

try:
    from jojo_trading.ui.app import main as dcf_main
    
    # 執行DCF分析應用
    dcf_main()
        
except ImportError as e:
    st.error(f"無法載入DCF分析模組: {e}")
    st.write("請確認系統安裝正確。")
    
    # 提供基本的DCF分析介面
    st.subheader("📈 基本DCF估值分析")
    st.write("DCF分析模組暫時無法使用，這是一個簡化的介面。")
    
    # 簡單的DCF計算器
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("輸入參數")
        free_cash_flow = st.number_input("自由現金流 (億元)", value=10.0, step=0.1)
        growth_rate = st.number_input("成長率 (%)", value=5.0, step=0.1) / 100
        discount_rate = st.number_input("折現率 (%)", value=8.0, step=0.1) / 100
        
    with col2:
        st.subheader("計算結果")
        if st.button("計算DCF價值"):
            # 簡單的DCF計算
            terminal_value = free_cash_flow * (1 + growth_rate) / (discount_rate - growth_rate)
            st.metric("估計價值", f"{terminal_value:.2f} 億元")
            st.success("計算完成！")
    
    st.info("💡 這是簡化版本，完整功能請聯繫技術支援。")
