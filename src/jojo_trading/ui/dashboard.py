import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Try to import internal modules, handle missing gracefully
try:
    from ..core.yfinance_fetcher import YFinanceFetcher
    from ..core.technical_analysis import TechnicalAnalysis
    from ..trading.trade_recorder import TradeRecorder
except ImportError:
    YFinanceFetcher = None
    TechnicalAnalysis = None
    TradeRecorder = None

class DashboardUI:
    """
    儀表板 3.0 (War Room Edition)
    Premium 'Glassmorphism' style dashboard with interactive visualization.
    """
    
    def __init__(self):
        # Default indices to watch
        self.indices = {
            "🇹🇼 0050": "0050.TW",
            "🇺🇸 SPY": "SPY",
            "📉 VIX": "^VIX"
        }
        
    def render(self):
        # --- Header Section ---
        self._render_header()
        
        # --- Market Pulse (Top Row) ---
        st.markdown("### 📡 市場脈動 (Market Pulse)")
        self._render_market_row()
        
        st.markdown("---")
        
        # --- Main Workspace (Grid) ---
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # P&L Chart & Account Stats
            self._render_account_analytics()
            
        with col_right:
            # Quick Actions & Status
            self._render_quick_panel()
            self._render_recent_activity()

    def _render_header(self):
        """Render a welcome header with dynamic time"""
        now = datetime.now()
        greeting = "早安" if 5 <= now.hour < 12 else "午安" if 12 <= now.hour < 18 else "晚安"
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.title(f"{greeting}，Trader Jun")
            st.caption(f"🚀 JoJo Trading 戰情中心 | {now.strftime('%Y-%m-%d %H:%M')}")
        with c2:
            # Placeholder for Connection Status Badge if needed
            st.markdown(
                """
                <div style="text-align: right; padding: 10px;">
                    <span style="background: rgba(0, 201, 255, 0.1); color: #00C9FF; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; border: 1px solid rgba(0,201,255,0.3);">
                        ● System Online
                    </span>
                </div>
                """, unsafe_allow_html=True
            )

    def _render_market_row(self):
        """Render key market indices with mini-charts"""
        if not YFinanceFetcher:
            st.error("Missing Data Module (YFinanceFetcher)")
            return

        cols = st.columns(len(self.indices))
        
        for idx, (name, ticker) in enumerate(self.indices.items()):
            with cols[idx]:
                self._render_index_card(name, ticker)

    def _render_index_card(self, name, ticker):
        """Individual Index Card logic"""
        # Fetch Data (Mock-able or Real)
        try:
            hist = YFinanceFetcher.get_price_history(ticker, period="1mo")
            if hist is None or hist.empty:
                st.warning(f"No Data: {name}")
                return
                
            current = hist.iloc[-1]
            prev = hist.iloc[-2]
            change = current - prev
            pct = (change / prev) * 100
            
            # Color logic
            color = "#00C9FF" # Default blue
            if pct > 0: color = "#92FE9D" # Green
            if pct < 0: color = "#FF4B4B" # Red
            
            # Simple Metric
            st.metric(name, f"{current:.2f}", f"{change:.2f} ({pct:.2f}%)")
            
            # Sparkline Plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist.values,
                mode='lines',
                line=dict(color=color, width=2),
                fill='tozeroy', # Area chart effect
                fillcolor=f"rgba{self._hex_to_rgb(color, 0.1)}"
            ))
            fig.update_layout(
                height=50,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        except Exception as e:
            st.error(f"Err: {name}")

    def _render_account_analytics(self):
        """Account visualization"""
        st.subheader("💰 帳戶透視 (Account Analytics)")
        
        # 1. High-level Stats (Cards)
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("總權益 (Equity)", "$1,240,500", "+$12,400 (1.0%)")
        with s2:
            st.metric("本月已實現", "$45,200", "Win Rate: 68%")
        with s3:
            st.metric("未平倉損益", "-$3,200", "Risk: Low")
            
        st.markdown("#### ⚖️ 損益曲線 (Cumulative P&L)")
        
        # Mock P&L Data for visualization
        dates = pd.date_range(start="2025-01-01", periods=30)
        pnl = np.cumsum(np.random.randn(30) * 1000 + 200) # Upward trend
        df_pnl = pd.DataFrame({"Date": dates, "PnL": pnl})
        
        fig = px.area(df_pnl, x="Date", y="PnL", title=None)
        fig.update_traces(line_color="#00C9FF", fillcolor="rgba(0, 201, 255, 0.2)")
        fig.update_layout(
            height=300,
            paper_bgcolor='rgba(255,255,255,0.02)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888'),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_quick_panel(self):
        """Right side quick actions"""
        st.subheader("⚡ 捷徑")
        
        with st.container(): # Grouping for styling
            if st.button("🔍 智能選股 (AI Scanner)", use_container_width=True, type="primary"):
                st.session_state.current_page_key = 'market_analysis'
                st.rerun()
                
            st.write("") # Spacer
            
            if st.button("📝 記錄交易 (Journal)", use_container_width=True, type="secondary"):
                st.session_state.current_page_key = 'real_trading'
                st.rerun()
                
            st.write("")
            
            if st.button("⚙️ 系統設定 (Settings)", use_container_width=True, type="secondary"):
                st.session_state.current_page_key = 'settings'
                st.rerun()

    def _render_recent_activity(self):
        st.subheader("🔔 最近活動")
        # Mock Activity Feed
        activities = [
            {"time": "14:30", "msg": "System Auto-Hedging Triggered", "type": "warn"},
            {"time": "13:45", "msg": "Bought 2330.TW @ 580", "type": "info"},
            {"time": "09:05", "msg": "Login Successful (API)", "type": "success"},
        ]
        
        for act in activities:
            icon = "🟢" if act['type'] == 'success' else "🟡" if act['type'] == 'warn' else "🔵"
            st.markdown(
                f"""
                <div style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <small style="color: #666;">{act['time']}</small><br>
                    {icon} {act['msg']}
                </div>
                """, unsafe_allow_html=True
            )

    def _hex_to_rgb(self, hex_color, alpha):
        """Helper for RGBA strings"""
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        rgb = tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return f"({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
