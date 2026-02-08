"""
📈 JoJo Trading - 高級技術分析
Advanced Technical Analysis

提供完整的技術分析工具：
- RSI、MACD、移動平均線等經典指標
- 多重時間框架分析
- 訊號檢測與趨勢分析
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class TechnicalAnalyzer:
    """技術分析器"""
    
    def __init__(self):
        self.indicators = {
            'momentum': ['RSI', 'STOCH', 'ROC'],
            'trend': ['MACD', 'EMA', 'SMA'],
            'volatility': ['BB'],
            'volume': ['OBV']
        }
    
    def get_stock_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """獲取股票數據"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                st.error(f"無法獲取 {symbol} 的數據")
                return pd.DataFrame()
                
            # 確保數據型別正確
            df = df.astype({
                'Open': 'float64',
                'High': 'float64', 
                'Low': 'float64',
                'Close': 'float64',
                'Volume': 'int64'
            })
                
            return df
            
        except Exception as e:
            st.error(f"數據獲取錯誤: {str(e)}")
            return pd.DataFrame()
    
    def calculate_rsi(self, close: pd.Series, window: int = 14) -> pd.Series:
        """計算 RSI（相對強弱指標）"""
        try:
            delta = close.diff()
            
            # 分離上漲和下跌
            gain = delta.clip(lower=0)
            loss = (-delta).clip(lower=0)
            
            # 計算平均增益和損失
            avg_gain = gain.rolling(window=window, min_periods=window).mean()
            avg_loss = loss.rolling(window=window, min_periods=window).mean()
            
            # 計算 RS 和 RSI
            rs = avg_gain / (avg_loss + 1e-10)  # 避免除零
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            st.warning(f"RSI 計算錯誤: {str(e)}")
            return pd.Series([np.nan] * len(close), index=close.index)
    
    def calculate_macd(self, close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算 MACD"""
        try:
            ema_fast = close.ewm(span=fast, min_periods=fast).mean()
            ema_slow = close.ewm(span=slow, min_periods=slow).mean()
            
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal, min_periods=signal).mean()
            histogram = macd - signal_line
            
            return macd, signal_line, histogram
            
        except Exception as e:
            st.warning(f"MACD 計算錯誤: {str(e)}")
            empty_series = pd.Series([np.nan] * len(close), index=close.index)
            return empty_series, empty_series, empty_series
    
    def calculate_bollinger_bands(self, close: pd.Series, window: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算布林通道"""
        try:
            middle = close.rolling(window=window, min_periods=window).mean()
            std = close.rolling(window=window, min_periods=window).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return upper, middle, lower
            
        except Exception as e:
            st.warning(f"布林通道計算錯誤: {str(e)}")
            empty_series = pd.Series([np.nan] * len(close), index=close.index)
            return empty_series, empty_series, empty_series
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> Tuple[pd.Series, pd.Series]:
        """計算隨機指標"""
        try:
            lowest_low = low.rolling(window=window, min_periods=window).min()
            highest_high = high.rolling(window=window, min_periods=window).max()
            
            # 計算 %K
            k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
            
            # 計算 %D（%K 的移動平均）
            d_percent = k_percent.rolling(window=3, min_periods=3).mean()
            
            return k_percent, d_percent
            
        except Exception as e:
            st.warning(f"隨機指標計算錯誤: {str(e)}")
            empty_series = pd.Series([np.nan] * len(close), index=close.index)
            return empty_series, empty_series
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """計算能量潮（On Balance Volume）"""
        try:
            obv = pd.Series(index=close.index, dtype=float)
            obv.iloc[0] = volume.iloc[0]
            
            for i in range(1, len(close)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]
            
            return obv
            
        except Exception as e:
            st.warning(f"OBV 計算錯誤: {str(e)}")
            return pd.Series([np.nan] * len(close), index=close.index)
    
    def get_all_indicators(self, df: pd.DataFrame) -> Dict:
        """計算所有技術指標"""
        indicators = {}
        
        try:
            # 動量指標
            indicators['RSI'] = self.calculate_rsi(df['Close'])
            indicators['STOCH_K'], indicators['STOCH_D'] = self.calculate_stochastic(df['High'], df['Low'], df['Close'])
            indicators['ROC'] = df['Close'].pct_change(periods=10) * 100
            
            # 趨勢指標
            indicators['MACD'], indicators['MACD_SIGNAL'], indicators['MACD_HIST'] = self.calculate_macd(df['Close'])
            indicators['EMA_12'] = df['Close'].ewm(span=12, min_periods=12).mean()
            indicators['EMA_26'] = df['Close'].ewm(span=26, min_periods=26).mean()
            indicators['SMA_20'] = df['Close'].rolling(window=20, min_periods=20).mean()
            indicators['SMA_50'] = df['Close'].rolling(window=50, min_periods=50).mean()
            
            # 波動性指標
            indicators['BB_UPPER'], indicators['BB_MIDDLE'], indicators['BB_LOWER'] = self.calculate_bollinger_bands(df['Close'])
            
            # 成交量指標
            indicators['OBV'] = self.calculate_obv(df['Close'], df['Volume'])
            
        except Exception as e:
            st.error(f"指標計算錯誤: {str(e)}")
        
        return indicators
    
    def create_technical_chart(self, df: pd.DataFrame, indicators: Dict, selected_indicators: List[str]) -> go.Figure:
        """創建技術分析圖表"""
        # 計算子圖數量
        subplot_count = 1  # 主圖
        subplot_titles = ['價格與技術指標']
        
        # 動量指標子圖
        if any(ind in selected_indicators for ind in ['RSI', 'STOCH_K', 'STOCH_D']):
            subplot_count += 1
            subplot_titles.append('動量指標')
            
        # MACD 子圖
        if any(ind in selected_indicators for ind in ['MACD', 'MACD_SIGNAL', 'MACD_HIST']):
            subplot_count += 1
            subplot_titles.append('MACD')
            
        # 成交量指標子圖
        if 'OBV' in selected_indicators:
            subplot_count += 1
            subplot_titles.append('成交量指標')
        
        # 創建子圖
        fig = make_subplots(
            rows=subplot_count, 
            cols=1,
            shared_xaxes=True,
            subplot_titles=subplot_titles,
            vertical_spacing=0.05,
            row_heights=[0.6] + [0.4/(subplot_count-1)]*(subplot_count-1) if subplot_count > 1 else [1.0]
        )
        
        # 主圖：K線圖
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='價格',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # 添加移動平均線到主圖
        if 'SMA_20' in selected_indicators and 'SMA_20' in indicators:
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['SMA_20'], name='SMA 20', 
                          line=dict(color='orange', width=2)),
                row=1, col=1
            )
        
        if 'SMA_50' in selected_indicators and 'SMA_50' in indicators:
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['SMA_50'], name='SMA 50',
                          line=dict(color='blue', width=2)),
                row=1, col=1
            )
        
        if 'EMA_12' in selected_indicators and 'EMA_12' in indicators:
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['EMA_12'], name='EMA 12',
                          line=dict(color='green', width=2)),
                row=1, col=1
            )
        
        # 布林通道
        if all(ind in selected_indicators for ind in ['BB_UPPER', 'BB_MIDDLE', 'BB_LOWER']):
            if all(ind in indicators for ind in ['BB_UPPER', 'BB_MIDDLE', 'BB_LOWER']):
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['BB_UPPER'], name='BB Upper',
                              line=dict(color='red', width=1, dash='dash')),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['BB_MIDDLE'], name='BB Middle',
                              line=dict(color='gray', width=1)),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['BB_LOWER'], name='BB Lower',
                              line=dict(color='green', width=1, dash='dash')),
                    row=1, col=1
                )
        
        current_row = 2
        
        # 動量指標子圖
        if any(ind in selected_indicators for ind in ['RSI', 'STOCH_K', 'STOCH_D']):
            if 'RSI' in selected_indicators and 'RSI' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['RSI'], name='RSI',
                              line=dict(color='purple', width=2)),
                    row=current_row, col=1
                )
                # RSI 參考線
                fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超買 70")
                fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超賣 30")
            
            if 'STOCH_K' in selected_indicators and 'STOCH_K' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['STOCH_K'], name='Stoch %K',
                              line=dict(color='orange', width=2)),
                    row=current_row, col=1
                )
            
            if 'STOCH_D' in selected_indicators and 'STOCH_D' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['STOCH_D'], name='Stoch %D',
                              line=dict(color='red', width=2)),
                    row=current_row, col=1
                )
            
            current_row += 1
        
        # MACD 子圖
        if any(ind in selected_indicators for ind in ['MACD', 'MACD_SIGNAL', 'MACD_HIST']):
            if 'MACD' in selected_indicators and 'MACD' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['MACD'], name='MACD',
                              line=dict(color='blue', width=2)),
                    row=current_row, col=1
                )
            
            if 'MACD_SIGNAL' in selected_indicators and 'MACD_SIGNAL' in indicators:
                fig.add_trace(
                    go.Scatter(x=df.index, y=indicators['MACD_SIGNAL'], name='MACD Signal',
                              line=dict(color='red', width=2)),
                    row=current_row, col=1
                )
            
            if 'MACD_HIST' in selected_indicators and 'MACD_HIST' in indicators:
                fig.add_trace(
                    go.Bar(x=df.index, y=indicators['MACD_HIST'], name='MACD Histogram',
                           marker_color='gray', opacity=0.7),
                    row=current_row, col=1
                )
            
            current_row += 1
        
        # 成交量指標子圖
        if 'OBV' in selected_indicators and 'OBV' in indicators:
            fig.add_trace(
                go.Scatter(x=df.index, y=indicators['OBV'], name='OBV',
                          line=dict(color='green', width=2)),
                row=current_row, col=1
            )
        
        # 更新佈局
        fig.update_layout(
            title=dict(
                text='📈 技術分析圖表',
                font=dict(size=20)
            ),
            height=600 + (subplot_count - 1) * 200,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_title='日期',
            template='plotly_white'
        )
        
        return fig

def main():
    st.set_page_config(
        page_title="JoJo Trading - 高級技術分析", 
        page_icon="📈", 
        layout="wide"
    )
    
    st.title("📈 高級技術分析")
    st.markdown("---")
    
    # 創建分析器
    analyzer = TechnicalAnalyzer()
    
    # 側邊欄配置
    with st.sidebar:
        st.header("📊 分析配置")
        
        # 股票選擇
        symbol = st.text_input(
            "股票代碼", 
            value="2330.TW", 
            help="輸入股票代碼，例如：2330.TW（台積電）、AAPL（蘋果）"
        )
        
        # 時間範圍
        period = st.selectbox(
            "時間範圍",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=3,
            help="選擇分析的時間範圍"
        )
        
        st.markdown("---")
        
        # 指標選擇
        st.subheader("🔧 技術指標選擇")
        
        # 趨勢指標
        trend_indicators = st.multiselect(
            "📈 趨勢指標",
            options=["SMA_20", "SMA_50", "EMA_12", "EMA_26", "MACD", "MACD_SIGNAL", "MACD_HIST"],
            default=["SMA_20", "MACD", "MACD_SIGNAL"],
            help="選擇趨勢分析指標"
        )
        
        # 動量指標
        momentum_indicators = st.multiselect(
            "⚡ 動量指標",
            options=["RSI", "STOCH_K", "STOCH_D", "ROC"],
            default=["RSI"],
            help="選擇動量分析指標"
        )
        
        # 波動性指標
        volatility_indicators = st.multiselect(
            "📊 波動性指標",
            options=["BB_UPPER", "BB_MIDDLE", "BB_LOWER"],
            default=["BB_UPPER", "BB_MIDDLE", "BB_LOWER"],
            help="選擇波動性分析指標"
        )
        
        # 成交量指標
        volume_indicators = st.multiselect(
            "📊 成交量指標",
            options=["OBV"],
            default=[],
            help="選擇成交量分析指標"
        )
        
        # 合併所有選中的指標
        selected_indicators = trend_indicators + momentum_indicators + volatility_indicators + volume_indicators
    
    # 主要內容區域
    if st.button("🚀 開始分析", type="primary", use_container_width=True):
        if not symbol:
            st.error("❌ 請輸入股票代碼")
            return
        
        if not selected_indicators:
            st.error("❌ 請至少選擇一個技術指標")
            return
        
        with st.spinner("📊 正在獲取數據和計算指標..."):
            # 獲取數據
            df = analyzer.get_stock_data(symbol, period)
            
            if df.empty:
                st.error("❌ 無法獲取股票數據，請檢查股票代碼")
                return
            
            # 計算指標
            indicators = analyzer.get_all_indicators(df)
            
            # 顯示基本信息
            st.subheader("📊 股票基本信息")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                current_price = df['Close'].iloc[-1]
                st.metric("💰 當前價格", f"{current_price:.2f}")
            
            with col2:
                daily_change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
                daily_change_pct = (daily_change / df['Close'].iloc[-2]) * 100
                st.metric(
                    "📈 日變化", 
                    f"{daily_change:.2f}", 
                    f"{daily_change_pct:+.2f}%"
                )
            
            with col3:
                volume = df['Volume'].iloc[-1]
                st.metric("📊 成交量", f"{volume:,.0f}")
            
            with col4:
                if 'RSI' in indicators:
                    current_rsi = indicators['RSI'].iloc[-1]
                    if not pd.isna(current_rsi):
                        rsi_status = "🔴 超買" if current_rsi > 70 else "🟢 超賣" if current_rsi < 30 else "🟡 正常"
                        st.metric("⚡ RSI", f"{current_rsi:.1f}", rsi_status)
            
            st.markdown("---")
            
            # 繪製圖表
            st.subheader("📈 技術分析圖表")
            fig = analyzer.create_technical_chart(df, indicators, selected_indicators)
            st.plotly_chart(fig, use_container_width=True)
            
            # 技術分析摘要
            if st.checkbox("📋 顯示技術分析摘要"):
                st.subheader("🔍 技術分析摘要")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📈 趨勢分析")
                    if 'SMA_20' in indicators and 'SMA_50' in indicators:
                        sma20_current = indicators['SMA_20'].iloc[-1]
                        sma50_current = indicators['SMA_50'].iloc[-1]
                        
                        if not pd.isna(sma20_current) and not pd.isna(sma50_current):
                            if sma20_current > sma50_current:
                                st.success("🟢 短期趨勢向上（SMA20 > SMA50）")
                            else:
                                st.warning("🔴 短期趨勢向下（SMA20 < SMA50）")
                    
                    if 'MACD' in indicators and 'MACD_SIGNAL' in indicators:
                        macd_current = indicators['MACD'].iloc[-1]
                        signal_current = indicators['MACD_SIGNAL'].iloc[-1]
                        
                        if not pd.isna(macd_current) and not pd.isna(signal_current):
                            if macd_current > signal_current:
                                st.success("🟢 MACD 買入訊號")
                            else:
                                st.warning("🔴 MACD 賣出訊號")
                
                with col2:
                    st.markdown("### ⚡ 動量分析")
                    if 'RSI' in indicators:
                        rsi_current = indicators['RSI'].iloc[-1]
                        if not pd.isna(rsi_current):
                            if rsi_current > 70:
                                st.warning("🔴 RSI 超買區間（>70）")
                            elif rsi_current < 30:
                                st.success("🟢 RSI 超賣區間（<30）")
                            else:
                                st.info("🟡 RSI 正常區間（30-70）")
                    
                    if 'STOCH_K' in indicators:
                        stoch_k = indicators['STOCH_K'].iloc[-1]
                        if not pd.isna(stoch_k):
                            if stoch_k > 80:
                                st.warning("🔴 隨機指標超買（>80）")
                            elif stoch_k < 20:
                                st.success("🟢 隨機指標超賣（<20）")
                            else:
                                st.info("🟡 隨機指標正常（20-80）")
            
            # 顯示詳細數據
            if st.checkbox("📋 顯示詳細數據表"):
                st.subheader("📊 技術指標數據")
                
                # 創建顯示數據框
                display_df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                
                # 添加選中的指標
                for indicator in selected_indicators:
                    if indicator in indicators:
                        if len(indicators[indicator]) == len(display_df):
                            display_df[indicator] = indicators[indicator].round(2)
                
                # 顯示最近30天的數據
                st.dataframe(
                    display_df.tail(30),
                    use_container_width=True,
                    height=400
                )
    
    else:
        # 顯示說明
        st.info("👆 請在左側選擇股票代碼和技術指標，然後點擊「開始分析」按鈕")
        
        # 顯示指標說明
        with st.expander("📚 技術指標說明"):
            st.markdown("""
            ### 📈 趨勢指標
            - **SMA (Simple Moving Average)**：簡單移動平均線，用於判斷趨勢方向
            - **EMA (Exponential Moving Average)**：指數移動平均線，對近期價格更敏感
            - **MACD**：移動平均收斂發散指標，用於判斷買賣時機
            
            ### ⚡ 動量指標
            - **RSI (Relative Strength Index)**：相對強弱指標，判斷超買超賣
            - **Stochastic**：隨機指標，衡量價格在一定時間內的相對位置
            - **ROC (Rate of Change)**：變化率指標，衡量價格動量
            
            ### 📊 波動性指標
            - **Bollinger Bands**：布林通道，衡量價格波動性和支撐阻力
            
            ### 📊 成交量指標
            - **OBV (On Balance Volume)**：能量潮指標，結合價格和成交量分析
            """)

if __name__ == "__main__":
    main()
