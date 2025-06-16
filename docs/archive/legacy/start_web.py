#!/usr/bin/env python3
"""
JoJo Trading Web UI 直接啟動腳本
這個腳本專門用於啟動 Streamlit Web 應用程式
"""

import sys
from pathlib import Path

# 添加 src 目錄到 Python 路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 導入狀態機和應用邏輯
from src.jojo_trading.core.state_machine import JoJoStateMachine
from src.jojo_trading.ui.app import drive_state_machine
import streamlit as st

def main():
    """主要的 Streamlit 應用入口點"""
    # 設定頁面配置
    st.set_page_config(
        page_title="JoJo Trading 系統",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化狀態機
    if 'jojo_machine' not in st.session_state:
        st.session_state.jojo_machine = JoJoStateMachine()
        # 執行初始狀態
        st.session_state.jojo_machine.execute_state()
    
    # 驅動狀態機
    machine = st.session_state.jojo_machine
    drive_state_machine(machine)

if __name__ == "__main__":
    main()
