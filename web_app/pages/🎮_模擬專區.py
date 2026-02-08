
import streamlit as st
import sys
import os

# 確保能夠導入模組
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from jojo_trading.trading.simulation_ui import SimulatedTradingUI
except ImportError:
    st.error("無法導入模擬交易模組，請檢查安裝。")
    SimulatedTradingUI = None

def main():
    st.set_page_config(
        page_title="模擬交易專區",
        page_icon="🎮",
        layout="wide"
    )
    
    if SimulatedTradingUI:
        ui = SimulatedTradingUI()
        ui.render()
    else:
        st.warning("必需的模組遺失")

if __name__ == "__main__":
    main()
