"""
📡 JoJo Trading - 實時市場監控中心
Real-time Market Monitoring Center

提供全天候市場監控功能：
- 即時股價監控
- 市場熱點追蹤
- 異常價量監控
- 技術指標告警
- 新聞事件監控
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
import requests
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class MarketMonitor:
    """市場監控引擎"""
    
    def __init__(self):
        self.watchlist = []
        self.alert_thresholds = {
            'price_change': 5.0,  # 價格變動超過5%
            'volume_spike': 2.0,  # 成交量暴增2倍
            'gap_threshold': 3.0  # 跳空超過3%
        }
        
    def add_to_watchlist(self, symbol: str, name: str = "") -> None:
        """添加股票到監控清單"""
        if symbol not in [item['symbol'] for item in self.watchlist]:
            self.watchlist.append({
                'symbol': symbol,
                'name': name or symbol,
                'added_time': datetime.now()
            })
    
    def remove_from_watchlist(self, symbol: str) -> None:
        """從監控清單移除股票"""
        self.watchlist = [item for item in self.watchlist if item['symbol'] != symbol]
    
    def get_real_time_data(self, symbols: List[str]) -> Dict:
        """獲取即時市場數據"""
        real_time_data = {}
        
        for symbol in symbols:
            try:
                # 台股代碼格式處理
                if symbol.isdigit() and len(symbol) == 4:
                    ticker_symbol = f"{symbol}.TW"
                else:
                    ticker_symbol = symbol
                
                ticker = yf.Ticker(ticker_symbol)
                
                # 獲取即時數據
                info = ticker.info
                hist = ticker.history(period="2d", interval="1m")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = info.get('previousClose', hist['Close'].iloc[0])
                    
                    price_change = current_price - prev_close
                    price_change_pct = (price_change / prev_close) * 100 if prev_close != 0 else 0
                    
                    volume = hist['Volume'].iloc[-1]
                    avg_volume = hist['Volume'].mean()
                    volume_ratio = volume / avg_volume if avg_volume != 0 else 1
                    
                    real_time_data[symbol] = {
                        'current_price': current_price,
                        'prev_close': prev_close,
                        'price_change': price_change,
                        'price_change_pct': price_change_pct,
                        'volume': volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': volume_ratio,
                        'high': hist['High'].max(),
                        'low': hist['Low'].min(),
                        'last_update': datetime.now(),
                        'market_cap': info.get('marketCap', 'N/A'),
                        'pe_ratio': info.get('trailingPE', 'N/A')
                    }
                
            except Exception as e:
                st.warning(f"無法獲取 {symbol} 的即時數據: {str(e)}")
                
        return real_time_data
    
    def detect_alerts(self, market_data: Dict) -> List[Dict]:
        """檢測市場異常和告警"""
        alerts = []
        
        for symbol, data in market_data.items():
            # 價格變動異常
            if abs(data['price_change_pct']) > self.alert_thresholds['price_change']:
                alerts.append({
                    'symbol': symbol,
                    'type': 'PRICE_MOVEMENT',
                    'severity': 'HIGH' if abs(data['price_change_pct']) > 10 else 'MEDIUM',
                    'message': f"{symbol} 價格變動 {data['price_change_pct']:+.2f}%",
                    'value': data['price_change_pct'],
                    'timestamp': datetime.now()
                })
            
            # 成交量異常
            if data['volume_ratio'] > self.alert_thresholds['volume_spike']:
                alerts.append({
                    'symbol': symbol,
                    'type': 'VOLUME_SPIKE',
                    'severity': 'MEDIUM',
                    'message': f"{symbol} 成交量暴增 {data['volume_ratio']:.1f}倍",
                    'value': data['volume_ratio'],
                    'timestamp': datetime.now()
                })
        
        return alerts
    
    def get_market_heatmap_data(self) -> pd.DataFrame:
        """獲取市場熱圖數據"""
        
        # 台股主要類股代表股票
        sectors = {
            '半導體': ['2330', '2454', '3034', '2382'],
            '金融': ['2881', '2882', '2891', '2892'],
            '傳產': ['1101', '1102', '1216', '1301'],
            '電子': ['2317', '2412', '6505', '3008'],
            '生技': ['4131', '6505', '1789', '4198']
        }
        
        heatmap_data = []
        
        for sector, symbols in sectors.items():
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(f"{symbol}.TW")
                    hist = ticker.history(period="1d")
                    
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        prev_close = hist['Open'].iloc[0]
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                        
                        heatmap_data.append({
                            'symbol': symbol,
                            'sector': sector,
                            'change_pct': change_pct,
                            'volume': hist['Volume'].iloc[-1]
                        })
                        
                except Exception:
                    continue
        
        return pd.DataFrame(heatmap_data)
    
    def get_news_sentiment(self, symbol: str) -> Dict:
        """獲取新聞情緒分析（模擬）"""
        # 這裡可以接入真實的新聞API
        # 目前返回模擬數據
        
        import random
        
        sentiments = ['positive', 'neutral', 'negative']
        sentiment = random.choice(sentiments)
        
        news_items = [
            f"{symbol} 財報超預期",
            f"{symbol} 獲得大單",
            f"{symbol} 技術突破",
            f"{symbol} 市場展望佳",
            f"{symbol} 法人看好"
        ]
        
        return {
            'sentiment': sentiment,
            'score': random.uniform(-1, 1),
            'news_count': random.randint(5, 20),
            'latest_news': random.sample(news_items, 3)
        }

def create_real_time_dashboard(monitor: MarketMonitor, symbols: List[str]) -> None:
    """創建即時監控儀表板"""
    
    # 即時數據刷新
    placeholder = st.empty()
    
    with placeholder.container():
        # 獲取即時數據
        market_data = monitor.get_real_time_data(symbols)
        
        if not market_data:
            st.warning("無法獲取市場數據")
            return
        
        # 市場概覽
        st.subheader("📊 市場即時概覽")
        
        # 創建指標卡片
        cols = st.columns(min(len(market_data), 4))
        
        for i, (symbol, data) in enumerate(market_data.items()):
            with cols[i % 4]:
                change_color = "red" if data['price_change_pct'] > 0 else "green"
                
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin: 5px 0;">
                    <h4>{symbol}</h4>
                    <p style="font-size: 24px; margin: 0; color: {change_color};">
                        ${data['current_price']:.2f}
                    </p>
                    <p style="margin: 0; color: {change_color};">
                        {data['price_change']:+.2f} ({data['price_change_pct']:+.2f}%)
                    </p>
                    <p style="margin: 0; font-size: 12px;">
                        成交量: {data['volume']:,.0f}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # 告警系統
        alerts = monitor.detect_alerts(market_data)
        
        if alerts:
            st.subheader("🚨 市場告警")
            
            for alert in alerts[-5:]:  # 顯示最近5個告警
                severity_color = {
                    'HIGH': 'red',
                    'MEDIUM': 'orange',
                    'LOW': 'yellow'
                }.get(alert['severity'], 'gray')
                
                st.markdown(f"""
                <div style="padding: 10px; border-left: 5px solid {severity_color}; 
                           background-color: rgba(255,255,255,0.05); margin: 5px 0;">
                    <strong>{alert['message']}</strong><br>
                    <small>類型: {alert['type']} | 時間: {alert['timestamp'].strftime('%H:%M:%S')}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # 即時圖表
        st.subheader("📈 即時價格走勢")
        
        if symbols:
            selected_symbol = st.selectbox("選擇股票", symbols, key="chart_symbol")
            
            if selected_symbol in market_data:
                # 獲取分鐘數據
                ticker = yf.Ticker(f"{selected_symbol}.TW" if selected_symbol.isdigit() else selected_symbol)
                minute_data = ticker.history(period="1d", interval="1m")
                
                if not minute_data.empty:
                    fig = go.Figure()
                    
                    # 添加價格線
                    fig.add_trace(go.Scatter(
                        x=minute_data.index,
                        y=minute_data['Close'],
                        mode='lines',
                        name='價格',
                        line=dict(color='blue', width=2)
                    ))
                    
                    # 添加成交量
                    fig.add_trace(go.Bar(
                        x=minute_data.index,
                        y=minute_data['Volume'],
                        name='成交量',
                        yaxis='y2',
                        opacity=0.3
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_symbol} 今日即時走勢",
                        xaxis_title="時間",
                        yaxis_title="價格",
                        yaxis2=dict(
                            title="成交量",
                            overlaying='y',
                            side='right'
                        ),
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # 市場熱圖
        st.subheader("🔥 市場熱點圖")
        
        heatmap_data = monitor.get_market_heatmap_data()
        
        if not heatmap_data.empty:
            fig_heatmap = px.treemap(
                heatmap_data,
                path=['sector', 'symbol'],
                values='volume',
                color='change_pct',
                color_continuous_scale='RdYlGn',
                title="市場熱點圖（按類股和漲跌幅）"
            )
            
            fig_heatmap.update_layout(height=500)
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # 最後更新時間
        st.caption(f"最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def create_watchlist_manager(monitor: MarketMonitor) -> None:
    """創建監控清單管理器"""
    
    st.subheader("📋 監控清單管理")
    
    # 添加新股票
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        new_symbol = st.text_input("股票代碼", placeholder="如: 2330")
    
    with col2:
        new_name = st.text_input("股票名稱", placeholder="如: 台積電")
    
    with col3:
        if st.button("➕ 添加"):
            if new_symbol:
                monitor.add_to_watchlist(new_symbol, new_name)
                st.success(f"已添加 {new_symbol} 到監控清單")
                st.rerun()
    
    # 顯示當前監控清單
    if monitor.watchlist:
        st.write("**當前監控清單:**")
        
        for i, item in enumerate(monitor.watchlist):
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
            
            with col1:
                st.write(f"{i+1}.")
            
            with col2:
                st.write(item['symbol'])
            
            with col3:
                st.write(item['name'])
            
            with col4:
                if st.button("🗑️", key=f"remove_{i}"):
                    monitor.remove_from_watchlist(item['symbol'])
                    st.rerun()
    
    else:
        st.info("監控清單為空，請添加股票開始監控")

def main():
    st.set_page_config(
        page_title="實時市場監控中心",
        page_icon="📡",
        layout="wide"
    )
    
    st.title("📡 實時市場監控中心")
    st.markdown("---")
    
    # 初始化監控器
    if 'market_monitor' not in st.session_state:
        st.session_state.market_monitor = MarketMonitor()
        # 添加一些預設股票
        for symbol in ['2330', '0050', '2454']:
            st.session_state.market_monitor.add_to_watchlist(symbol)
    
    monitor = st.session_state.market_monitor
    
    # 側邊欄設置
    with st.sidebar:
        st.header("⚙️ 監控設置")
        
        # 監控清單管理
        create_watchlist_manager(monitor)
        
        st.markdown("---")
        
        # 告警設置
        st.subheader("🚨 告警設置")
        
        price_threshold = st.slider(
            "價格變動告警 (%)", 
            1.0, 20.0, 
            monitor.alert_thresholds['price_change']
        )
        
        volume_threshold = st.slider(
            "成交量倍數告警", 
            1.5, 5.0, 
            monitor.alert_thresholds['volume_spike']
        )
        
        # 更新告警閾值
        monitor.alert_thresholds['price_change'] = price_threshold
        monitor.alert_thresholds['volume_spike'] = volume_threshold
        
        st.markdown("---")
        
        # 自動刷新設置
        auto_refresh = st.checkbox("啟用自動刷新", value=False)
        
        if auto_refresh:
            refresh_interval = st.slider("刷新間隔 (秒)", 5, 60, 30)
        
        # 手動刷新按鈕
        if st.button("🔄 立即刷新", type="primary"):
            st.rerun()
    
    # 主要內容
    if monitor.watchlist:
        symbols = [item['symbol'] for item in monitor.watchlist]
        
        # 標籤頁
        tab1, tab2, tab3 = st.tabs(["📊 即時監控", "📈 技術分析", "📰 新聞情緒"])
        
        with tab1:
            create_real_time_dashboard(monitor, symbols)
        
        with tab2:
            st.subheader("📈 技術分析總覽")
            
            selected_symbol = st.selectbox("選擇分析股票", symbols)
            
            if selected_symbol:
                try:
                    ticker = yf.Ticker(f"{selected_symbol}.TW" if selected_symbol.isdigit() else selected_symbol)
                    hist = ticker.history(period="1mo")
                    
                    if not hist.empty:
                        # 簡單技術指標
                        hist['MA5'] = hist['Close'].rolling(5).mean()
                        hist['MA20'] = hist['Close'].rolling(20).mean()
                        
                        fig = make_subplots(
                            rows=2, cols=1,
                            shared_xaxes=True,
                            subplot_titles=[f'{selected_symbol} 技術分析', '成交量'],
                            vertical_spacing=0.1,
                            row_heights=[0.7, 0.3]
                        )
                        
                        # K線圖
                        fig.add_trace(go.Candlestick(
                            x=hist.index,
                            open=hist['Open'],
                            high=hist['High'],
                            low=hist['Low'],
                            close=hist['Close'],
                            name='價格'
                        ), row=1, col=1)
                        
                        # 移動平均線
                        fig.add_trace(go.Scatter(
                            x=hist.index,
                            y=hist['MA5'],
                            name='MA5',
                            line=dict(color='orange', width=1)
                        ), row=1, col=1)
                        
                        fig.add_trace(go.Scatter(
                            x=hist.index,
                            y=hist['MA20'],
                            name='MA20',
                            line=dict(color='blue', width=1)
                        ), row=1, col=1)
                        
                        # 成交量
                        fig.add_trace(go.Bar(
                            x=hist.index,
                            y=hist['Volume'],
                            name='成交量',
                            marker_color='gray',
                            opacity=0.6
                        ), row=2, col=1)
                        
                        fig.update_layout(
                            height=600,
                            showlegend=True,
                            xaxis_rangeslider_visible=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"無法獲取 {selected_symbol} 的技術分析數據: {str(e)}")
        
        with tab3:
            st.subheader("📰 新聞情緒分析")
            
            selected_symbol = st.selectbox("選擇股票", symbols, key="news_symbol")
            
            if selected_symbol:
                news_data = monitor.get_news_sentiment(selected_symbol)
                
                # 情緒指標
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sentiment_color = {
                        'positive': 'green',
                        'neutral': 'gray',
                        'negative': 'red'
                    }.get(news_data['sentiment'], 'gray')
                    
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px;">
                        <h3 style="color: {sentiment_color};">
                            {news_data['sentiment'].upper()}
                        </h3>
                        <p>總體情緒</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.metric("情緒分數", f"{news_data['score']:.2f}", "(-1到1)")
                
                with col3:
                    st.metric("新聞數量", news_data['news_count'])
                
                # 最新新聞
                st.subheader("📰 最新相關新聞")
                
                for i, news in enumerate(news_data['latest_news'], 1):
                    st.write(f"{i}. {news}")
        
        # 自動刷新
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()
    
    else:
        st.info("請在左側添加股票到監控清單開始監控")
        
        # 顯示功能說明
        st.markdown("""
        ## 📋 實時監控功能說明
        
        ### 📊 即時監控
        - **市場概覽**: 顯示監控股票的即時價格、漲跌幅和成交量
        - **告警系統**: 自動檢測價格異常波動和成交量暴增
        - **即時圖表**: 分鐘級價格走勢和成交量圖表
        - **市場熱圖**: 按類股和漲跌幅顯示市場熱點
        
        ### 📈 技術分析
        - **K線圖**: 顯示開高低收四個價位
        - **移動平均線**: MA5 和 MA20 趨勢線
        - **成交量分析**: 價量配合分析
        
        ### 📰 新聞情緒
        - **情緒分析**: 基於新聞內容的情緒評分
        - **新聞追蹤**: 相關新聞數量統計
        - **最新消息**: 顯示最新相關新聞
        
        ### ⚙️ 自定義設置
        - **監控清單**: 自由添加/移除監控股票
        - **告警閾值**: 自定義價格和成交量告警條件
        - **自動刷新**: 設定自動更新間隔
        
        **開始使用**: 在左側「監控清單管理」中添加要監控的股票代碼。
        """)

if __name__ == "__main__":
    main()
