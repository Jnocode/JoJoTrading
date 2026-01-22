"""
Stage 4 整合功能示範應用

獨立的 Streamlit 應用，展示 WACC、處分偵測、參數推薦的整合功能

執行方式:
    streamlit run streamlit_stage4_demo.py

Author: jojo_trading team
Date: 2025-11-19
"""

import streamlit as st

# ⚠️ set_page_config() 必須是第一個 Streamlit 命令
st.set_page_config(
    page_title="Stage 4 整合示範 - JoJo Trading",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
from pathlib import Path

# 添加 src 到路徑
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from jojo_trading.ui.components.stage4_integration import Stage4IntegrationPanel


def main():
    """主程式"""
    
    # 標題
    st.title("🎯 Stage 4 進階 DCF 分析工具")
    st.markdown("""
    本工具整合了三大進階功能，協助您進行更準確的 DCF 估值：
    
    1. **💰 WACC 計算**: 精確計算加權平均資本成本
    2. **🔍 處分偵測**: 自動識別一次性資產處分收益
    3. **🎯 參數推薦**: 智能推薦最適合的 DCF 參數
    """)
    
    st.markdown("---")
    
    # 側邊欄
    with st.sidebar:
        st.header("📊 關於本工具")
        st.markdown("""
        **Stage 4 整合功能**
        
        版本: 1.0.0  
        日期: 2025-11-19
        
        **功能特色**:
        - ✅ CAPM 模型計算權益成本
        - ✅ 自動偵測異常收益
        - ✅ 產業化參數推薦
        - ✅ 情境分析支援
        - ✅ 視覺化圖表展示
        """)
        
        st.markdown("---")
        
        st.markdown("""
        **使用提示**:
        1. 從 WACC 計算開始
        2. 檢查是否有處分收益
        3. 獲取參數推薦
        4. 查看整合分析報告
        """)
        
        st.markdown("---")
        
        # 快速連結
        st.markdown("**📚 相關文件**")
        st.markdown("""
        - [WACC 說明](https://github.com)
        - [DCF 教學](https://github.com)
        - [API 文件](https://github.com)
        """)
    
    # 渲染主面板
    panel = Stage4IntegrationPanel()
    results = panel.render()
    
    # 頁尾
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        Made with ❤️ by JoJo Trading Team | © 2025 All Rights Reserved
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
