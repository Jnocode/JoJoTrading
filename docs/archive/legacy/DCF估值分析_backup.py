"""
DCF估值分析頁面
整合的DCF估值分析系統介面
"""

import streamlit as st
import sys
import os

# 確保能夠導入模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 頁面標題
st.title("📊 DCF估值分析")

# 導航按鈕
if st.button("⬅️ 返回主頁"):
    st.switch_page("main_app_fixed.py")

st.markdown("---")

try:
    from src.jojo_trading.ui.app import main as dcf_main
    
    # 執行DCF分析應用
    dcf_main()
        
except ImportError as e:
    st.error(f"無法載入DCF分析模組: {e}")
    st.write("請確認系統安裝正確。")
    
    # 提供基本的DCF分析介面
    st.subheader("📈 基本DCF估值分析")
    st.write("DCF分析模組暫時無法使用，請聯繫系統管理員。")
