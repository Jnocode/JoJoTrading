#!/usr/bin/env python3
"""
JoJo Trading Streamlit Web UI
優化版本，減少 ScriptRunContext 警告
"""

import sys
import os
from pathlib import Path

# 添加 src 目錄到 Python 路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import streamlit as st

# 頁面配置（必須在其他streamlit調用之前）
st.set_page_config(
    page_title="📈 JoJo Trading 系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 延遲導入以避免在頁面配置前觸發 Streamlit
from src.jojo_trading.core.state_machine import JoJoStateMachine
from src.jojo_trading.ui.app import drive_state_machine

def main():
    """主要的 Streamlit 應用邏輯"""
    
    # 標題
    st.title("📈 JoJo Trading 系統")
    st.markdown("---")
    
    # 初始化狀態機（只在第一次運行時）
    if 'jojo_machine' not in st.session_state:
        with st.spinner("🔄 初始化系統..."):
            st.session_state.jojo_machine = JoJoStateMachine()
            # 執行初始狀態配置
            st.session_state.jojo_machine.execute_state()
        st.success("✅ 系統初始化完成")
    
    # 獲取狀態機實例
    machine = st.session_state.jojo_machine
    
    # 顯示系統狀態
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.metric("當前狀態", str(machine.current_state).split('.')[-1])
    
    with col2:
        if hasattr(machine, 'context') and 'industry_count' in machine.context:
            industry_count = machine.context.get('industry_count', 0)
            st.metric("已載入產業", f"{industry_count} 個")
    
    # 狀態機控制
    st.markdown("### 🎛️ 系統控制")
    
    if st.button("🔄 重新載入配置"):
        machine.transition_to('CONFIG_LOAD')
        machine.execute_state()
        st.rerun()
    
    # 驅動狀態機執行主要邏輯
    try:
        drive_state_machine(machine)
    except Exception as e:
        st.error(f"❌ 系統執行錯誤: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
