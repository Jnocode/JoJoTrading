"""
📈 JoJo Trading - 技術分析工具
Advanced Technical Analysis Tools for Professional Trading
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加項目路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# ⚠️ 注意：在多頁面應用中，頁面檔案不應該調用 st.set_page_config()

# 載入自定義CSS
def load_technical_css():
    """載入技術分析專用CSS樣式"""
    st.markdown("""
    <style>
    .tech-header {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    
    .indicator-card {
        background: white;
        border: 2px solid #e74c3c;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .signal-bullish {
        background: linear-gradient(135deg, #00b894, #00cec9);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .signal-bearish {
        background: linear-gradient(135deg, #e17055, #d63031);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .signal-neutral {
        background: linear-gradient(135deg, #fdcb6e, #e17055);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .pattern-box {
        background: #f8f9fa;
        border-left: 4px solid #e74c3c;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

class TechnicalAnalyzer:
    """技術分析計算器"""
    
    @staticmethod
    def calculate_sma(data, window):
        """計算簡單移動平均線"""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def calculate_ema(data, window):
        """計算指數移動平均線"""
        return data.ewm(span=window).mean()
    
    @staticmethod
    def calculate_rsi(data, window=14):
        """計算相對強弱指標"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data, fast=12, slow=26, signal=9):
        """計算MACD指標"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(data, window=20, std_dev=2):
        """計算布林通道"""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_stochastic(high, low, close, k_window=14, d_window=3):
        """計算隨機指標"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        return k_percent, d_percent

def generate_sample_data(stock_code="2330", days=252):
    """生成樣本股價數據"""
    # 生成基礎價格走勢
    dates = pd.date_range(start=datetime.now()-timedelta(days=days), end=datetime.now(), freq='D')
    dates = dates[dates.dayofweek < 5]  # 只保留工作日
    
    # 基於真實台積電價格模擬
    base_prices = {
        "2330": 600,
        "2317": 110,
        "2454": 900,
        "2308": 350
    }
    
    base_price = base_prices.get(stock_code, 600)
    
    # 生成價格序列
    np.random.seed(42)  # 確保可重複性
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = [base_price]
    
    for i in range(1, len(dates)):
        price = prices[-1] * (1 + returns[i])
        prices.append(max(price, base_price * 0.5))  # 設置最低價格
    
    # 生成高低價
    highs = [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices]
    lows = [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices]
    
    # 生成成交量
    volumes = np.random.randint(50000, 200000, len(dates))
    
    df = pd.DataFrame({
        'date': dates[:len(prices)],
        'open': prices,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes
    })
    
    return df

def render_technical_header():
    """渲染技術分析頁面標題"""
    st.markdown("""
    <div class="tech-header">
        <h1>📈 專業技術分析工具</h1>
        <p style="font-size: 1.1em;">Advanced Technical Analysis & Chart Patterns</p>
        <p style="font-size: 0.9em; opacity: 0.9;">
            多重技術指標分析 | 圖表型態識別 | 交易訊號生成
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_stock_selector():
    """渲染股票選擇器"""
    stocks = {
        "2330": "台積電",
        "2317": "鴻海", 
        "2454": "聯發科",
        "2308": "台達電",
        "2382": "廣達",
        "6505": "台塑化",
        "2891": "中信金",
        "2882": "國泰金"
    }
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_stock = st.selectbox(
            "選擇分析股票",
            options=list(stocks.keys()),
            format_func=lambda x: f"{x} {stocks[x]}"
        )
    
    with col2:
        timeframe = st.selectbox(
            "時間週期",
            ["日線", "週線", "月線"],
            index=0
        )
    
    with col3:
        analysis_period = st.selectbox(
            "分析期間",
            ["3個月", "6個月", "1年", "2年"],
            index=2
        )
    
    return selected_stock, stocks[selected_stock], timeframe, analysis_period

def render_price_chart(df, stock_name):
    """渲染價格走勢圖"""
    st.markdown("### 📊 價格走勢與技術指標")
    
    # 計算技術指標
    analyzer = TechnicalAnalyzer()
    
    df['SMA_20'] = analyzer.calculate_sma(df['close'], 20)
    df['SMA_50'] = analyzer.calculate_sma(df['close'], 50)
    df['EMA_12'] = analyzer.calculate_ema(df['close'], 12)
    df['RSI'] = analyzer.calculate_rsi(df['close'])
    
    # 計算MACD
    macd, signal, histogram = analyzer.calculate_macd(df['close'])
    df['MACD'] = macd
    df['MACD_Signal'] = signal
    df['MACD_Histogram'] = histogram
    
    # 計算布林通道
    bb_upper, bb_middle, bb_lower = analyzer.calculate_bollinger_bands(df['close'])
    df['BB_Upper'] = bb_upper
    df['BB_Middle'] = bb_middle
    df['BB_Lower'] = bb_lower
    
    # 創建子圖
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            f'{stock_name} 股價走勢',
            '成交量',
            'RSI 相對強弱指標',
            'MACD 指標'
        ),
        row_width=[0.3, 0.1, 0.15, 0.15]
    )
    
    # 主圖 - K線圖
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K線',
            increasing_line_color='red',
            decreasing_line_color='green'
        ),
        row=1, col=1
    )
    
    # 移動平均線
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['SMA_20'], name='SMA 20', line=dict(color='blue', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['SMA_50'], name='SMA 50', line=dict(color='orange', width=1)),
        row=1, col=1
    )
    
    # 布林通道
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['BB_Upper'], name='布林上軌', 
                  line=dict(color='rgba(128,128,128,0.5)', dash='dash')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['BB_Lower'], name='布林下軌', 
                  line=dict(color='rgba(128,128,128,0.5)', dash='dash'),
                  fill='tonexty', fillcolor='rgba(128,128,128,0.1)'),
        row=1, col=1
    )
    
    # 成交量
    fig.add_trace(
        go.Bar(x=df['date'], y=df['volume'], name='成交量', marker_color='lightblue'),
        row=2, col=1
    )
    
    # RSI
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['RSI'], name='RSI', line=dict(color='purple')),
        row=3, col=1
    )    # RSI 超買超賣線 - 使用 Scatter 替代 add_hline
    rsi_dates = df['date']
    fig.add_trace(
        go.Scatter(x=[rsi_dates.iloc[0], rsi_dates.iloc[-1]], y=[70, 70], 
                  mode='lines', line=dict(color='red', dash='dash'), 
                  name='超買線', showlegend=False),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=[rsi_dates.iloc[0], rsi_dates.iloc[-1]], y=[30, 30], 
                  mode='lines', line=dict(color='green', dash='dash'), 
                  name='超賣線', showlegend=False),
        row=3, col=1
    )
    
    # MACD
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['MACD'], name='MACD', line=dict(color='blue')),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['MACD_Signal'], name='信號線', line=dict(color='red')),
        row=4, col=1
    )
    fig.add_trace(
        go.Bar(x=df['date'], y=df['MACD_Histogram'], name='柱狀圖', marker_color='gray'),
        row=4, col=1
    )
    
    # 更新布局
    fig.update_layout(
        height=800,
        title_text=f"{stock_name} 技術分析圖表",
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    return df

def analyze_signals(df):
    """分析交易訊號"""
    signals = []
    
    # RSI 訊號
    latest_rsi = df['RSI'].iloc[-1]
    if latest_rsi > 70:
        signals.append(("RSI", "超買", "bearish", f"RSI: {latest_rsi:.1f}"))
    elif latest_rsi < 30:
        signals.append(("RSI", "超賣", "bullish", f"RSI: {latest_rsi:.1f}"))
    else:
        signals.append(("RSI", "中性", "neutral", f"RSI: {latest_rsi:.1f}"))
    
    # MACD 訊號
    macd_current = df['MACD'].iloc[-1]
    signal_current = df['MACD_Signal'].iloc[-1]
    if macd_current > signal_current:
        signals.append(("MACD", "多頭", "bullish", "MACD > 信號線"))
    else:
        signals.append(("MACD", "空頭", "bearish", "MACD < 信號線"))
    
    # 移動平均線訊號
    price_current = df['close'].iloc[-1]
    sma20_current = df['SMA_20'].iloc[-1]
    sma50_current = df['SMA_50'].iloc[-1]
    
    if price_current > sma20_current > sma50_current:
        signals.append(("均線", "多頭排列", "bullish", "價格 > SMA20 > SMA50"))
    elif price_current < sma20_current < sma50_current:
        signals.append(("均線", "空頭排列", "bearish", "價格 < SMA20 < SMA50"))
    else:
        signals.append(("均線", "糾結", "neutral", "均線交錯"))
    
    # 布林通道訊號
    bb_upper_current = df['BB_Upper'].iloc[-1]
    bb_lower_current = df['BB_Lower'].iloc[-1]
    
    if price_current > bb_upper_current:
        signals.append(("布林通道", "突破上軌", "bearish", "可能回調"))
    elif price_current < bb_lower_current:
        signals.append(("布林通道", "跌破下軌", "bullish", "可能反彈"))
    else:
        signals.append(("布林通道", "通道內", "neutral", "整理中"))
    
    return signals

def render_signal_analysis(signals):
    """渲染訊號分析"""
    st.markdown("### 🎯 交易訊號分析")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        for indicator, signal, sentiment, detail in signals:
            css_class = f"signal-{sentiment}"
            
            st.markdown(f"""
            <div class="{css_class}">
                <h4>{indicator}: {signal}</h4>
                <p>{detail}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # 綜合評分
        bullish_count = sum(1 for _, _, sentiment, _ in signals if sentiment == "bullish")
        bearish_count = sum(1 for _, _, sentiment, _ in signals if sentiment == "bearish")
        neutral_count = sum(1 for _, _, sentiment, _ in signals if sentiment == "neutral")
        
        total_signals = len(signals)
        
        st.markdown("#### 📊 訊號統計")
        st.metric("看多訊號", bullish_count, f"{bullish_count/total_signals:.1%}")
        st.metric("看空訊號", bearish_count, f"{bearish_count/total_signals:.1%}")
        st.metric("中性訊號", neutral_count, f"{neutral_count/total_signals:.1%}")
        
        # 綜合建議
        if bullish_count > bearish_count:
            overall = "偏多"
            color = "green"
        elif bearish_count > bullish_count:
            overall = "偏空"
            color = "red"
        else:
            overall = "中性"
            color = "orange"
        
        st.markdown(f"""
        <div style="background: {color}; color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h3>綜合判斷: {overall}</h3>
        </div>
        """, unsafe_allow_html=True)

def render_pattern_recognition(df):
    """渲染圖表型態識別"""
    st.markdown("### 🔍 圖表型態識別")
    
    patterns = []
    
    # 簡單型態識別邏輯
    recent_prices = df['close'].tail(20)
    
    # 檢查趨勢
    if recent_prices.iloc[-1] > recent_prices.iloc[0]:
        trend = "上升趨勢"
        patterns.append(("趨勢分析", trend, "最近20天呈現上升走勢"))
    else:
        trend = "下降趨勢"
        patterns.append(("趨勢分析", trend, "最近20天呈現下降走勢"))
    
    # 檢查支撐阻力
    recent_high = recent_prices.max()
    recent_low = recent_prices.min()
    current_price = recent_prices.iloc[-1]
    
    if current_price > recent_high * 0.95:
        patterns.append(("價位分析", "接近阻力", f"當前價格接近近期高點 {recent_high:.2f}"))
    elif current_price < recent_low * 1.05:
        patterns.append(("價位分析", "接近支撐", f"當前價格接近近期低點 {recent_low:.2f}"))
    
    # 波動性分析
    volatility = recent_prices.pct_change().std() * 100
    if volatility > 3:
        patterns.append(("波動分析", "高波動", f"近期波動率 {volatility:.1f}%"))
    elif volatility < 1:
        patterns.append(("波動分析", "低波動", f"近期波動率 {volatility:.1f}%"))
    
    # 顯示型態
    for category, pattern, description in patterns:
        st.markdown(f"""
        <div class="pattern-box">
            <strong>{category}</strong>: {pattern}<br>
            <small>{description}</small>
        </div>
        """, unsafe_allow_html=True)

def render_technical_indicators_table(df):
    """渲染技術指標數值表"""
    st.markdown("### 📋 技術指標數值")
    
    # 準備數據
    latest_data = {
        '指標': ['收盤價', 'SMA 20', 'SMA 50', 'RSI', 'MACD', '布林上軌', '布林下軌'],
        '數值': [
            f"{df['close'].iloc[-1]:.2f}",
            f"{df['SMA_20'].iloc[-1]:.2f}",
            f"{df['SMA_50'].iloc[-1]:.2f}",
            f"{df['RSI'].iloc[-1]:.1f}",
            f"{df['MACD'].iloc[-1]:.3f}",
            f"{df['BB_Upper'].iloc[-1]:.2f}",
            f"{df['BB_Lower'].iloc[-1]:.2f}"
        ],
        '5日變化': [
            f"{((df['close'].iloc[-1] / df['close'].iloc[-6]) - 1) * 100:.1f}%",
            f"{((df['SMA_20'].iloc[-1] / df['SMA_20'].iloc[-6]) - 1) * 100:.1f}%",
            f"{((df['SMA_50'].iloc[-1] / df['SMA_50'].iloc[-6]) - 1) * 100:.1f}%",
            f"{df['RSI'].iloc[-1] - df['RSI'].iloc[-6]:.1f}",
            f"{df['MACD'].iloc[-1] - df['MACD'].iloc[-6]:.3f}",
            f"{((df['BB_Upper'].iloc[-1] / df['BB_Upper'].iloc[-6]) - 1) * 100:.1f}%",
            f"{((df['BB_Lower'].iloc[-1] / df['BB_Lower'].iloc[-6]) - 1) * 100:.1f}%"
        ]
    }
    
    indicators_df = pd.DataFrame(latest_data)
    st.dataframe(indicators_df, use_container_width=True, hide_index=True)

def main():
    """主函數"""
    # 載入CSS樣式
    load_technical_css()
    
    # 渲染頁面標題
    render_technical_header()
    
    # 股票選擇器
    selected_stock, stock_name, timeframe, period = render_stock_selector()
    
    # 生成樣本數據
    df = generate_sample_data(selected_stock)
    
    # 主要分析區域
    tab1, tab2, tab3 = st.tabs(["📊 技術圖表", "🎯 訊號分析", "📋 指標數值"])
    
    with tab1:
        df_with_indicators = render_price_chart(df, stock_name)
        render_pattern_recognition(df_with_indicators)
    
    with tab2:
        if 'df_with_indicators' in locals():
            signals = analyze_signals(df_with_indicators)
            render_signal_analysis(signals)
        else:
            st.warning("請先查看技術圖表以載入指標數據")
    
    with tab3:
        if 'df_with_indicators' in locals():
            render_technical_indicators_table(df_with_indicators)
        else:
            st.warning("請先查看技術圖表以載入指標數據")
    
    # 側邊欄工具
    with st.sidebar:
        st.markdown("### ⚙️ 指標設定")
        
        with st.expander("移動平均線"):
            sma_short = st.slider("短期SMA", 5, 30, 20)
            sma_long = st.slider("長期SMA", 30, 100, 50)
        
        with st.expander("RSI 設定"):
            rsi_period = st.slider("RSI週期", 10, 25, 14)
            rsi_overbought = st.slider("超買線", 65, 85, 70)
            rsi_oversold = st.slider("超賣線", 15, 35, 30)
        
        with st.expander("MACD 設定"):
            macd_fast = st.slider("快線", 8, 15, 12)
            macd_slow = st.slider("慢線", 20, 30, 26)
            macd_signal = st.slider("信號線", 7, 12, 9)
        
        st.markdown("---")
        
        st.markdown("### 📊 市場總覽")
        
        # 模擬市場數據
        market_data = {
            "加權指數": {"value": "18,234", "change": "+1.2%", "color": "green"},
            "櫃買指數": {"value": "234.56", "change": "-0.5%", "color": "red"},
            "美股期貨": {"value": "5,234", "change": "+0.8%", "color": "green"}
        }
        
        for name, data in market_data.items():
            st.metric(name, data["value"], data["change"])
        
        st.markdown("### 🔔 技術分析提醒")
        st.info("💡 RSI 進入超買區間，建議關注回調風險")
        st.warning("⚠️ MACD 出現背離訊號，留意趨勢變化")

if __name__ == "__main__":
    main()
