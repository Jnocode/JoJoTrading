
import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import set_key, load_dotenv
from jojo_trading.data_sources.jin10_mcp import Jin10MCPClient
from jojo_trading.data_sources.stock_price import StockPriceFetcher
from jojo_trading.strategies.supertrend_smc import SuperTrendSMCStrategy
from jojo_trading.analysis.news_ai import NewsAnalyzer
import yfinance as yf
import plotly.graph_objects as go

class NewsDashboardUI:
    def __init__(self):
        self.client = Jin10MCPClient()
        self.analyzer = NewsAnalyzer()
        self.price_fetcher = StockPriceFetcher()

    def render(self):
        st.header("📰 金十快訊 & AI 市場熱度分析 (Powered by Gemini 2.0)")
        
        # Controls
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔄 立即刷新快訊"):
                st.rerun()
        with col2:
            auto_refresh = st.checkbox("自動刷新 (30s)", value=False)

        # Main Layout
        heat_col, news_col = st.columns([1, 2])

        # --- Sidebar Filters ---
        st.sidebar.header("🔍 進階篩選")
        
        # 1. Market Filter
        market_options = ["TW", "US", "Crypto", "Forex", "Other"]
        selected_markets = st.sidebar.multiselect("市場 (Market)", market_options, default=["TW", "US"])
        
        # 2. Sentiment Filter
        sentiment_options = ["Bullish", "Bearish", "Neutral"]
        selected_sentiments = st.sidebar.multiselect("情緒 (Sentiment)", sentiment_options, default=sentiment_options)
        
        # 3. Sector Filter (Dynamic from known sectors or simple text input?)
        # Let's use a text input for flexibility or predefined common ones
        sector_filter = st.sidebar.text_input("板塊關鍵字 (例如: 半導體)", "")

        # Fetch Data
        with st.spinner("獲取最新快訊中 (Groq Llama-3 極速分析中)..."):
            news_items = self.client.fetch_latest_news(limit=10)
            
            # Run AI Analysis (Batch)
            analyzed_news_raw = self.analyzer.analyze_impact_batch(news_items)
            
            # --- Apply Filters ---
            analyzed_news = []
            for item in analyzed_news_raw:
                analysis = item.get('analysis', {})
                
                # Filter 1: Sentiment
                sent = analysis.get('sentiment', 'Neutral')
                if sent not in selected_sentiments:
                    continue
                    
                # Filter 2: Market (Check affected stocks or sectors)
                # If "TW" selected, keep if ANY stock is TW or if content implies TW?
                # Using 'affected_stocks' market field is best.
                stocks = analysis.get('affected_stocks', [])
                valid_market = False
                
                # If no stocks found, we might keep it if "Other" is selected or rely on content?
                # Let's be strict: if TW selected, need TW stock OR generic news if "Other" selected.
                # Actually, simpler logic: 
                # Gather markets mentioned in this news
                news_markets = set()
                if stocks:
                    for s in stocks:
                        news_markets.add(s.get('market', 'Other'))
                else:
                    news_markets.add('Other')
                
                # Intersection check
                if not set(selected_markets).intersection(news_markets):
                    # Special case: If user selected "US" and news has no stocks but is generic, maybe 'Other'?
                    # Let's trust AI.
                    continue

                # Filter 3: Sector (Keyword search in 'sectors' list)
                if sector_filter:
                    sectors = analysis.get('sectors', [])
                    # Check if any sector matches keyword (substring)
                    if not any(sector_filter.lower() in s.lower() for s in sectors):
                         continue

                analyzed_news.append(item)
            
            # --- 🎯 Top Aggregated Stocks (Optimized Display) ---
            st.divider()
            st.subheader("🎯 重點關注個股 (Top Focus)")
            
            # Bucket stocks: [TW_Bull, TW_Bear, US_Bull, US_Bear]
            buckets = {'TW': {'Bullish': {}, 'Bearish': {}}, 
                       'US': {'Bullish': {}, 'Bearish': {}}}
            
            for item in analyzed_news:
                stocks = item['analysis'].get('affected_stocks', [])
                for stock in stocks:
                    ticker = stock.get('ticker')
                    market = stock.get('market', 'Other')
                    if not ticker: continue
                    
                    # Normalize Market
                    if market not in ['TW', 'US']: market = 'US' # Default/Other to US bucket for now
                    
                    sent = stock.get('sentiment', 'Neutral')
                    
                    target_dict = None
                    if sent == 'Bullish': target_dict = buckets[market]['Bullish']
                    elif sent == 'Bearish': target_dict = buckets[market]['Bearish']
                    
                    if target_dict is not None:
                        if ticker not in target_dict: target_dict[ticker] = stock

            # Render TW Row
            st.markdown("### 🇹🇼 台股焦點 (Taiwan Market)")
            tw_c1, tw_c2 = st.columns(2)
            with tw_c1:
                if buckets['TW']['Bullish']:
                    st.markdown("#### 🚀 利多 (Bullish)")
                    self._render_stock_grid(list(buckets['TW']['Bullish'].values()), is_adr=False)
                else:
                    st.info("尚無台股利多")
            with tw_c2:
                if buckets['TW']['Bearish']:
                    st.markdown("#### 🩸 利空 (Bearish)")
                    self._render_stock_grid(list(buckets['TW']['Bearish'].values()), is_adr=False)
                else:
                    st.info("尚無台股利空")

            # Render US Row
            st.markdown("### 🇺🇸 美股焦點 (US Market)")
            us_c1, us_c2 = st.columns(2)
            with us_c1:
                if buckets['US']['Bullish']:
                    st.markdown("#### 🚀 利多 (Bullish)")
                    self._render_stock_grid(list(buckets['US']['Bullish'].values()), is_adr=True)
                else:
                    st.info("尚無美股利多")
            with us_c2:
                if buckets['US']['Bearish']:
                    st.markdown("#### 🩸 利空 (Bearish)")
                    self._render_stock_grid(list(buckets['US']['Bearish'].values()), is_adr=True)
                else:
                    st.info("尚無美股利空")
            
            st.divider()

        # --- Left Column: Market Heat ---
        with heat_col:
            st.subheader("🔥 投資熱度概況")
            
            # Split items by session
            # TW Session: 09:00 <= T < 21:30
            # US Session: 21:30 <= T or T < 09:00
            tw_news = []
            us_news = []
            
            for item in analyzed_news:
                time_str = item.get('time', '')
                try:
                    # Jin10 usually returns "YYYY-MM-DD HH:MM:SS"
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    t = dt.time()
                    
                    # Define split times
                    tw_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
                    us_open = datetime.strptime("21:30:00", "%H:%M:%S").time()
                    
                    if tw_open <= t < us_open:
                        tw_news.append(item)
                    else:
                        us_news.append(item)
                except:
                    # Fallback to TW if parse fails (assuming daytime)
                    tw_news.append(item)
            
            # Create Tabs
            tab1, tab2 = st.tabs(["🌞 台股盤中 (上半場)", "🌛 美股盤中 (下半場)"])
            
            with tab1:
                self._render_heat_metrics("台股時段", tw_news)
                
            with tab2:
                self._render_heat_metrics("美股時段", us_news)


        with news_col:
            st.subheader("📡 即時快訊串流")
            
            for item in analyzed_news:
                analysis = item['analysis']
                if "error" in analysis:
                    st.error(f"分析失敗: {analysis['error']}")
                    st.markdown(item['content'], unsafe_allow_html=True)
                    continue

                sentiment = analysis.get('sentiment', 'Neutral')
                color = "gray"
                if sentiment == 'Bullish': color = "green"
                elif sentiment == 'Bearish': color = "red"
                
                # Title Summary
                summary = analysis.get('summary', '無摘要')
                timestamp = item.get('time', '')
                
                with st.expander(f"[{timestamp}] {summary}", expanded=True):
                    # Original Content
                    st.markdown(item['content'], unsafe_allow_html=True)
                    st.divider()
                    
                    # AI Insights
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"**情緒:** :{color}[{sentiment}]")
                        st.markdown(f"**熱度:** {analysis.get('heat_score', 0)}/100")
                    with c2:
                        sectors = analysis.get('sectors', [])
                        companies = analysis.get('companies', [])
                        
                        st.markdown(f"**影響板塊:** {', '.join(sectors) if sectors else '無'}")
                        
                        # Enhanced Stock Display
                        if 'affected_stocks' in analysis:
                            st.markdown("**相關個股與供應鏈:**")
                            for stock in analysis['affected_stocks']:
                                name = stock.get('name', '')
                                ticker = stock.get('ticker', '')
                                market = stock.get('market', 'Other')
                                role = stock.get('role', 'Direct')
                                corr = stock.get('correlation_percentage', 0)
                                sentiment = stock.get('sentiment', 'Neutral')
                                
                                # Styling based on market
                                badge_color = "#e6f3ff" if market == "TW" else "#fff0f0"
                                text_color = "#0052cc" if market == "TW" else "#cc0000"
                                border = "2px solid #0052cc" if market == "TW" else "1px solid #ccc"
                                
                                # Sentiment Icon
                                sent_icon = "⚪"
                                if sentiment == "Bullish": sent_icon = "🟢" # or 📈
                                elif sentiment == "Bearish": sent_icon = "🔴" # or 📉
                                
                                # Role badge
                                role_badge = f"<span style='font-size:0.8em; color:#666'>[{role}]</span>"

                                # Get Price & Strategy Signal
                                price_info = {'price': '...', 'change_pct': 0}
                                strategy_sig = 0
                                try:
                                    # Price
                                    p_data = self.price_fetcher.get_prices([ticker])
                                    if ticker in p_data:
                                        price_info = p_data[ticker]
                                    
                                    # Strategy (Quick Calculation for demo)
                                    # Ideally this should be async or cached
                                    if ticker.endswith('.TW') or ticker.isalpha():
                                        # Minimal history for strategy (e.g. 50 bars)
                                        df_ws = yf.download(ticker, period="5d", interval="1h", progress=False)
                                        if not df_ws.empty and len(df_ws) > 20:
                                           strat = SuperTrendSMCStrategy(atr_length=10)
                                           sigs, _ = strat.generate_signals(df_ws)
                                           strategy_sig = sigs.iloc[-1]
                                except:
                                    pass

                                # Format Price
                                p_val = price_info.get('price', '...')
                                p_change = price_info.get('change_pct', 0)
                                p_color = "red" if p_change < 0 else "green"
                                p_sign = "+" if p_change > 0 else ""
                                price_html = f"<span style='color:{p_color}; font-size:0.9em; margin-left:5px'>${p_val} ({p_sign}{p_change}%)</span>"

                                # Format Strategy Signal
                                strat_html = ""
                                if strategy_sig == 1:
                                    strat_html = "<span style='background:green; color:white; padding:1px 4px; border-radius:4px; font-size:0.8em; margin-left:5px'>BUY</span>"
                                elif strategy_sig == -1:
                                    strat_html = "<span style='background:red; color:white; padding:1px 4px; border-radius:4px; font-size:0.8em; margin-left:5px'>SELL</span>"

                                html = f"""
                                <div style="display:inline-block; margin:2px; padding:2px 8px; background:{badge_color}; border:{border}; border-radius:12px; color:{text_color}">
                                    {sent_icon} <b>{name}</b> ({ticker}) {role_badge} 
                                    {price_html} {strat_html}
                                    <span style="font-size:0.8em; color:#888">🔗{corr}%</span>
                                </div>
                                """
                                st.markdown(html, unsafe_allow_html=True)

                        # Legacy Fallback
                        elif 'companies' in analysis and analysis['companies']:
                            st.markdown(f"**相關個股:** {', '.join(companies)}")

        if auto_refresh:
            time.sleep(30)
            st.rerun()

    def _render_heat_metrics(self, label, news_list):
        if not news_list:
            st.info(f"{label} 尚無快訊數據")
            return

        # Calculate aggregate stats
        bullish_count = sum(1 for item in news_list if item['analysis'].get('sentiment', 'Neutral') == 'Bullish')
        bearish_count = sum(1 for item in news_list if item['analysis'].get('sentiment', 'Neutral') == 'Bearish')
        
        # Safe calculation for average heat
        heat_scores = [item['analysis'].get('heat_score', 0) for item in news_list if isinstance(item['analysis'].get('heat_score'), (int, float))]
        avg_heat = sum(heat_scores) / len(heat_scores) if heat_scores else 0

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("多頭", f"{bullish_count}", delta="筆")
        m2.metric("空頭", f"{bearish_count}", delta_color="inverse", delta="筆")
        m3.metric("熱度", f"{int(avg_heat)}")

        # Sentiment Gauge
        fig = self.render_gauge(int(avg_heat))
        st.plotly_chart(fig, use_container_width=True)

        # Sector Cloud (Simple)
        st.markdown("#### 🌊 熱點板塊")
        all_sectors = []
        for item in news_list:
            sectors = item['analysis'].get('sectors', [])
            if isinstance(sectors, list):
                all_sectors.extend(sectors)
        
        if all_sectors:
            # Count frequency
            from collections import Counter
            sector_counts = Counter(all_sectors)
            
            # Display simply as tags for now
            tags_html = ""
            for sector, count in sector_counts.most_common(8):
                size = 1 + (count * 0.1)
                tags_html += f"<span style='display:inline-block; font-size:{size}em; margin:5px; padding:3px 8px; background-color:#262730; border: 1px solid #444; border-radius:5px;'>{sector} ({count})</span>"
            st.markdown(tags_html, unsafe_allow_html=True)
        else:
            st.info("尚無板塊數據")

    def render_gauge(self, score):
        """
        Render a Gauge Chart for Market Sentiment.
        0-40: Bearish (Red)
        40-60: Neutral (Yellow)
        60-100: Bullish (Green)
        """
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "🔥 市場熱度恐貪指數"},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "white"},
                'bgcolor': "black",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 40], 'color': "rgba(255, 99, 71, 0.9)"}, # Red
                    {'range': [40, 60], 'color': "rgba(255, 215, 0, 0.9)"}, # Yellow
                    {'range': [60, 100], 'color': "rgba(50, 205, 50, 0.9)"} # Green
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            font={'color': "white", 'family': "Arial"},
            margin=dict(l=20, r=20, t=50, b=20),
            height=250
        )
        return fig
        return fig

    def _render_stock_grid(self, stocks, is_adr=False):
        """Helper to render a grid of stock badges"""
        # Batch fetch prices
        tickers = [s.get('ticker') for s in stocks if s.get('ticker')]
        price_map = {}
        try:
             price_map = self.price_fetcher.get_prices(tickers)
        except:
             pass
             
        # Known ADR List (Simple check)
        adr_list = ['TSM', 'UMC', 'ASX', 'IMOS', 'CHT', '2330', '2303'] # 2330 in US context?
             
        cols = st.columns(3) 
        for idx, stock in enumerate(stocks):
            with cols[idx % 3]:
                name = stock.get('name', '')
                ticker = stock.get('ticker', '')
                sent = stock.get('sentiment', 'Neutral')
                
                # ADR Tag logic
                adr_tag = ""
                if is_adr:
                     # Heuristic: If it's a known ADR ticker or name contains ADR/Taiwan
                     if ticker in adr_list or "ADR" in name.upper() or "TAIWAN" in name.upper():
                         adr_tag = "<span style='background:#666; color:white; padding:1px 3px; border-radius:3px; font-size:0.7em; margin-left:4px'>ADR</span>"
                
                # Price & Name
                p_info = price_map.get(ticker, {'price': '...', 'change_pct': 0})
                p_val = p_info.get('price', '...')
                p_change = p_info.get('change_pct', 0)
                
                # Override AI name if official name available
                official_name = p_info.get('name')
                if official_name and official_name != ticker:
                     name = official_name
                
                # Style
                bg_color = "rgba(40, 167, 69, 0.1)" if sent == 'Bullish' else "rgba(220, 53, 69, 0.1)"
                border_color = "#28a745" if sent == 'Bullish' else "#dc3545"
                text_color = "#28a745" if sent == 'Bullish' else "#dc3545"
                
                st.markdown(f"""
                <div style="
                    border: 1px solid {border_color};
                    border-left: 5px solid {border_color};
                    border-radius: 5px;
                    padding: 8px;
                    margin-bottom: 5px;
                    background-color: {bg_color};
                ">
                    <div style="font-weight:bold; color:{text_color}">{name} ({ticker}) {adr_tag}</div>
                    <div style="font-size:0.9em; display:flex; justify-content:space-between;">
                        <span>${p_val}</span>
                        <span style="color:{'green' if p_change > 0 else 'red'}">{p_change}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
