import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ..core.yfinance_fetcher import YFinanceFetcher
from ..core.technical_analysis import TechnicalAnalysis
from ..trading.trade_recorder import TradeRecorder

class DashboardUI:
    """
    儀表板 2.0 (Cockpit)
    提供市場概況、大盤趨勢、帳戶摘要的一站式視圖
    """
    
    def __init__(self):
        self.market_proxy = "0050.TW" # 使用 0050 作為台股大盤指標
        
    def render(self):
        st.title("🚀 戰情中心 (Dashboard)")
        
        # 1. 市場溫度計 (大盤多空)
        self._render_market_overview()
        
        st.markdown("---")
        
        # 2. 帳戶與交易概況
        self._render_account_summary()
        
        # 3. 快速捷徑
        self._render_quick_actions()

    def _render_market_overview(self):
        """渲染大盤與市場溫度"""
        st.subheader("📊 市場天候 (Market Climate)")
        
        if not YFinanceFetcher:
            st.error("無法載入數據模組")
            return

        # 獲取大盤(0050)數據
        hist = YFinanceFetcher.get_price_history(self.market_proxy, period="6mo")
        
        if hist is None or hist.empty:
            st.warning(f"無法獲取市場數據 ({self.market_proxy})")
            return
            
        # 計算技術指標
        current_price = hist.iloc[-1]
        ta = TechnicalAnalysis()
        ma20 = ta.calculate_ma(hist, 20)
        ma60 = ta.calculate_ma(hist, 60)
        rsi = ta.calculate_rsi(hist)
        
        # 判斷多空
        trend = "牛市 (Bull)" if ma20 > ma60 else "熊市 (Bear)"
        trend_color = "green" if ma20 > ma60 else "red"
        
        # 判斷溫度
        temp_emoji = "🌡️ 正常"
        if rsi > 75: temp_emoji = "🔥 過熱 (Overheated)"
        elif rsi < 25: temp_emoji = "🧊 過冷 (Oversold)"
        
        # 顯示關鍵指標卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("市場指標 (0050)", f"{current_price:.2f}", 
                     f"{current_price - hist.iloc[-2]:.2f} ({((current_price/hist.iloc[-2])-1)*100:.1f}%)")
        with col2:
            st.markdown(f"**趨勢訊號**")
            st.markdown(f":{trend_color}[**{trend}**]")
            st.caption(f"MA20: {ma20:.1f} / MA60: {ma60:.1f}")
        with col3:
            st.metric("RSI 動能", f"{rsi:.1f}", temp_emoji)
        with col4:
            # 簡單成交量 (假設 hist 有 Volume，但 YFinanceFetcher.get_price_history 只回傳 Close)
            # 這裡暫時顯示簡單的變動
            week_change = (current_price - hist.iloc[-5]) / hist.iloc[-5] * 100
            st.metric("近一周漲跌", f"{week_change:.1f}%")

        # 繪製迷你走勢圖
        self._plot_mini_chart(hist, ma20, ma60)

    def _plot_mini_chart(self, hist, ma20, ma60):
        """繪製簡單的趨勢圖"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Price", line=dict(color='white', width=2)))
        # 簡單計算 MA 線 (為了圖表顯示，需重新計算完整序列，或是 Dashboard 簡單只畫價格)
        # 為了效能，這裡暫時只畫價格，若要畫 MA 需要完整 Series
        fig.update_layout(
            height=250, 
            margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_account_summary(self):
        """渲染帳戶摘要"""
        try:
            recorder = TradeRecorder()
            stats = recorder.calculate_portfolio_performance()
            
            st.subheader("💰 帳戶概況 (Account Overview)")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("總損益", f"${stats.get('total_pnl', 0):,.0f}")
            with c2:
                st.metric("勝率", f"{stats.get('win_rate', 0):.1f}%")
            with c3:
                # 這裡需要連接券商才能拿到真實庫存，暫時顯示記錄器中的未平倉
                open_trades = len(recorder.get_open_trades())
                st.metric("持倉部位", f"{open_trades} 檔")
            with c4:
                st.metric("總交易次數", f"{stats.get('total_trades', 0)}")
                
        except Exception as e:
            st.error(f"無法載入帳戶資訊: {e}")

    def _render_quick_actions(self):
        """渲染快速捷徑"""
        st.subheader("⚡ 快速行動 (Quick Actions)")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔍 掃描半導體類股", use_container_width=True):
                st.session_state.current_page_key = 'market_analysis'
                # 預設觸發掃描 (需配合 Market Analysis 頁面實作)
                st.session_state.auto_scan_industry = "半導體業"
                st.rerun()
        with c2:
            if st.button("📝 查看交易日誌", use_container_width=True):
                st.session_state.current_page_key = 'real_trading'
                st.rerun()
        with c3:
            if st.button("⚙️ 調整策略參數", use_container_width=True):
                st.session_state.current_page_key = 'settings'
                st.rerun()
