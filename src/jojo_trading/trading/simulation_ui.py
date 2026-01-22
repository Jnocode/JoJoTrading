# -*- coding: utf-8 -*-
"""
模擬交易系統 UI 組件
專門用於展示模擬數據與測試功能，與真實交易邏輯分離
"""

import streamlit as st
import pandas as pd
import uuid
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

class SimulatedTradingUI:
    """模擬交易系統 UI 管理器"""
    
    def __init__(self):
        """初始化模擬交易系統"""
        # 使用獨立的 session state key 避免與真實交易混淆
        if 'sim_trades' not in st.session_state:
            st.session_state.sim_trades = []
            
        self.trades = st.session_state.sim_trades
    
    def render(self):
        """渲染模擬交易介面"""
        st.title("🎮 模擬交易專區")
        st.markdown("### 這裡的所有數據與交易皆為**模擬**，不會連接真實券商")
        
        tab1, tab2 = st.tabs(["📝 模擬下單", "📊 模擬記錄"])
        
        with tab1:
            self._render_order_form()
            
        with tab2:
            self._render_trade_records()
            
    def _render_order_form(self):
        """渲染模擬下單表單"""
        st.subheader("🎲 快速模擬交易")
        
        with st.form("sim_order_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                stock_code = st.text_input("股票代碼", placeholder="例如: 2330", value="2330")
                trade_type = st.selectbox("交易類型", options=["買入", "賣出"])
                price = st.number_input("價格", min_value=0.1, value=500.0, step=0.5)
                
            with col2:
                quantity = st.number_input("數量", min_value=1, value=1000, step=1000)
                signal_type = st.selectbox("模擬信號來源", options=["手動", "隨機信號", "模擬策略A"])
                notes = st.text_input("備註", placeholder="測試單...")
                
            if st.form_submit_button("🚀送出模擬單"):
                self._execute_sim_trade(stock_code, trade_type, price, quantity, signal_type, notes)
                
    def _execute_sim_trade(self, code, type_, price, qty, signal, notes):
        """執行模擬交易"""
        trade = {
            'id': str(uuid.uuid4())[:8],
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'code': code,
            'type': type_,
            'price': price,
            'qty': qty,
            'amt': price * qty,
            'signal': signal,
            'notes': notes,
            'status': '已成交(模擬)'
        }
        st.session_state.sim_trades.insert(0, trade) # 最新在最前
        st.success(f"✅ 模擬單已建立！ {type_} {code} {qty}股 @ {price}")
        
    def _render_trade_records(self):
        """渲染模擬交易記錄"""
        if not st.session_state.sim_trades:
            st.info("尚無模擬交易記錄")
            return
            
        df = pd.DataFrame(st.session_state.sim_trades)
        
        # 簡單統計
        st.metric("總模擬交易次數", len(df))
        
        st.dataframe(
            df, 
            column_config={
                "price": st.column_config.NumberColumn("價格", format="$%.2f"),
                "amt": st.column_config.NumberColumn("總金額", format="$%.2f"),
            },
            use_container_width=True
        )
        
        if st.button("🗑️ 清空模擬記錄"):
            st.session_state.sim_trades = []
            st.rerun()

def main():
    ui = SimulatedTradingUI()
    ui.render()

if __name__ == "__main__":
    main()
