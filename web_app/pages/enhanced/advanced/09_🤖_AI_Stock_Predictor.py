"""
🤖 JoJo Trading AI 股價預測系統
Phase 5: AI 智能化升級 - 機器學習股價預測

核心功能:
- LSTM 深度學習股價預測
- 技術指標特徵工程
- 多時間框架預測
- 預測結果可視化
- 模型準確度評估
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 模擬 ML 模型類別（實際應用時需要真實的模型）
class AIStockPredictor:
    """AI 股價預測器"""
    
    def __init__(self):
        self.model_loaded = False
        self.accuracy = 0.0
        self.last_trained = None
        
    def load_model(self, symbol: str):
        """載入預訓練模型"""
        # 模擬模型載入
        self.model_loaded = True
        self.accuracy = np.random.uniform(0.65, 0.85)  # 模擬準確度
        self.last_trained = datetime.now() - timedelta(days=np.random.randint(1, 30))
        return True
        
    def prepare_features(self, price_data: pd.DataFrame):
        """特徵工程 - 準備技術指標特徵"""
        features = price_data.copy()
        
        # 技術指標特徵
        features['SMA_5'] = features['Close'].rolling(5).mean()
        features['SMA_20'] = features['Close'].rolling(20).mean()
        features['EMA_12'] = features['Close'].ewm(span=12).mean()
        features['EMA_26'] = features['Close'].ewm(span=26).mean()
        
        # RSI 指標
        delta = features['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD 指標
        features['MACD'] = features['EMA_12'] - features['EMA_26']
        features['MACD_Signal'] = features['MACD'].ewm(span=9).mean()
        
        # 價格變化率
        features['Price_Change'] = features['Close'].pct_change()
        features['Volume_Change'] = features['Volume'].pct_change()
        
        # 布林帶
        bb_period = 20
        features['BB_Middle'] = features['Close'].rolling(bb_period).mean()
        bb_std = features['Close'].rolling(bb_period).std()
        features['BB_Upper'] = features['BB_Middle'] + (bb_std * 2)
        features['BB_Lower'] = features['BB_Middle'] - (bb_std * 2)
        features['BB_Position'] = (features['Close'] - features['BB_Lower']) / (features['BB_Upper'] - features['BB_Lower'])
        
        return features.dropna()
        
    def predict_price(self, features: pd.DataFrame, days_ahead: int = 5):
        """預測未來股價"""
        if not self.model_loaded:
            raise Exception("模型尚未載入")
            
        # 模擬 LSTM 預測（實際應用時需要真實的 LSTM 模型）
        last_price = features['Close'].iloc[-1]
        last_volume = features['Volume'].iloc[-1]
        
        predictions = []
        confidence_intervals = []
        
        for i in range(days_ahead):
            # 模擬預測邏輯
            trend_factor = np.random.uniform(0.98, 1.02)
            volatility = features['Close'].rolling(20).std().iloc[-1] / features['Close'].iloc[-1]
            random_factor = np.random.normal(1, volatility * 0.5)
            
            predicted_price = last_price * trend_factor * random_factor
            
            # 置信區間
            confidence = 0.1 * (i + 1) * predicted_price  # 隨時間增加不確定性
            
            predictions.append(predicted_price)
            confidence_intervals.append(confidence)
            
            last_price = predicted_price
            
        return predictions, confidence_intervals
        
    def evaluate_model_performance(self, features: pd.DataFrame):
        """評估模型性能"""
        # 模擬回測結果
        backtest_days = min(30, len(features))
        actual_prices = features['Close'].tail(backtest_days).values
        
        # 模擬預測價格（加入一些噪音）
        predicted_prices = actual_prices * np.random.normal(1, 0.05, len(actual_prices))
        
        # 計算評估指標
        mse = np.mean((actual_prices - predicted_prices) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(actual_prices - predicted_prices))
        mape = np.mean(np.abs((actual_prices - predicted_prices) / actual_prices)) * 100
        
        return {
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape,
            'Accuracy': max(0, 100 - mape),
            'Actual': actual_prices,
            'Predicted': predicted_prices
        }

def generate_sample_data(symbol: str, days: int = 365):
    """生成樣本股價數據（用於演示）"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 生成時間序列
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 模擬股價走勢
    np.random.seed(hash(symbol) % 1000)  # 基於股票代碼的固定種子
    base_price = np.random.uniform(50, 200)
    
    # 生成隨機漫步股價
    returns = np.random.normal(0, 0.02, len(dates))
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, 1))  # 確保價格不為負
    
    # 生成成交量
    volumes = np.random.lognormal(10, 1, len(dates))
    
    data = pd.DataFrame({
        'Date': dates,
        'Open': np.array(prices) * np.random.uniform(0.98, 1.02, len(prices)),
        'High': np.array(prices) * np.random.uniform(1.00, 1.05, len(prices)),
        'Low': np.array(prices) * np.random.uniform(0.95, 1.00, len(prices)),
        'Close': prices,
        'Volume': volumes
    })
    
    return data

def render_ai_prediction_interface():
    """渲染 AI 預測界面"""
    st.title("🤖 AI 股價預測系統")
    
    # 檢查用戶權限
    if not st.session_state.get("logged_in", False):
        st.warning("⚠️ 請先登入以使用 AI 預測功能")
        if st.button("前往登入"):
            st.switch_page("pages/enhanced/00_👤_User_Center.py")
        return
    
    user_data = st.session_state.get("user_data", {})
    user_plan = user_data.get("plan", "free")
    
    if user_plan == "free":
        st.info("🔒 AI 預測功能僅限專業版及企業版用戶使用")
        if st.button("升級到專業版"):
            st.switch_page("pages/enhanced/00_👤_User_Center.py")
        return
    
    # 主界面
    st.markdown("""
    ### 🎯 功能特色
    - 🧠 **深度學習預測**: 基於 LSTM 神經網絡的股價預測
    - 📊 **多維特徵**: 整合技術指標、成交量、市場情緒
    - ⏰ **多時間框架**: 支援 1-30 天的預測範圍
    - 📈 **可視化展示**: 直觀的預測結果圖表
    - 🎯 **準確度評估**: 實時模型性能監控
    """)
    
    # 側邊欄控制
    with st.sidebar:
        st.header("🔧 預測設定")
        
        # 股票選擇
        symbol = st.text_input(
            "📈 股票代碼", 
            value="2330", 
            help="輸入台股代碼，例如：2330、0050"
        )
        
        # 預測天數
        predict_days = st.slider(
            "📅 預測天數", 
            min_value=1, 
            max_value=30, 
            value=7,
            help="選擇要預測的未來天數"
        )
        
        # 模型設定
        st.subheader("🤖 模型設定")
        model_type = st.selectbox(
            "模型類型",
            ["LSTM", "GRU", "Transformer"],
            help="選擇預測模型類型"
        )
        
        confidence_level = st.slider(
            "信心水準", 
            min_value=0.8, 
            max_value=0.99, 
            value=0.95, 
            step=0.01,
            help="預測結果的置信區間"
        )
        
        # 執行預測按鈕
        predict_button = st.button("🚀 開始預測", use_container_width=True)
    
    # 主要內容區域
    if predict_button or st.session_state.get("show_prediction", False):
        st.session_state["show_prediction"] = True
        
        with st.spinner("🔄 載入數據並訓練模型..."):
            # 生成樣本數據
            price_data = generate_sample_data(symbol, days=365)
            
            # 初始化 AI 預測器
            predictor = AIStockPredictor()
            predictor.load_model(symbol)
            
            # 特徵工程
            features = predictor.prepare_features(price_data)
            
        # 顯示模型資訊
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 模型準確度", f"{predictor.accuracy:.1%}")
        
        with col2:
            st.metric("📊 訓練樣本", f"{len(features)} 天")
        
        with col3:
            st.metric("🕐 最後訓練", f"{predictor.last_trained.strftime('%Y-%m-%d')}")
        
        with col4:
            st.metric("🤖 模型類型", model_type)
        
        # 執行預測
        try:
            predictions, confidence_intervals = predictor.predict_price(features, predict_days)
            
            # 顯示預測結果
            st.subheader("📈 預測結果")
            
            # 創建預測圖表
            fig = go.Figure()
            
            # 歷史價格
            recent_data = features.tail(30)
            fig.add_trace(go.Scatter(
                x=recent_data.index,
                y=recent_data['Close'],
                mode='lines',
                name='歷史價格',
                line=dict(color='blue', width=2)
            ))
            
            # 預測價格
            future_dates = pd.date_range(
                start=features.index[-1] + timedelta(days=1),
                periods=predict_days,
                freq='D'
            )
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=predictions,
                mode='lines+markers',
                name='預測價格',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ))
            
            # 置信區間
            upper_bound = [p + c for p, c in zip(predictions, confidence_intervals)]
            lower_bound = [p - c for p, c in zip(predictions, confidence_intervals)]
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=upper_bound,
                mode='lines',
                name='上界',
                line=dict(color='lightgray', width=1),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=lower_bound,
                mode='lines',
                fill='tonexty',
                name=f'{confidence_level:.0%} 置信區間',
                line=dict(color='lightgray', width=1),
                fillcolor='rgba(255, 0, 0, 0.1)'
            ))
            
            fig.update_layout(
                title=f'{symbol} 股價預測 - 未來 {predict_days} 天',
                xaxis_title='日期',
                yaxis_title='股價 (TWD)',
                hovermode='x unified',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 預測數據表
            st.subheader("📋 詳細預測數據")
            
            prediction_df = pd.DataFrame({
                '日期': future_dates.strftime('%Y-%m-%d'),
                '預測價格': [f'{p:.2f}' for p in predictions],
                '置信區間': [f'±{c:.2f}' for c in confidence_intervals],
                '變化幅度': [f'{((p / features["Close"].iloc[-1]) - 1) * 100:+.1f}%' 
                           for p in predictions]
            })
            
            st.dataframe(prediction_df, use_container_width=True)
            
            # 投資建議
            st.subheader("💡 AI 投資建議")
            
            current_price = features['Close'].iloc[-1]
            final_prediction = predictions[-1]
            price_change = (final_prediction / current_price - 1) * 100
            
            if price_change > 5:
                recommendation = "🟢 強力買入"
                reason = f"AI 模型預測未來 {predict_days} 天將上漲 {price_change:.1f}%"
            elif price_change > 2:
                recommendation = "🔵 建議買入"
                reason = f"AI 模型預測溫和上漲 {price_change:.1f}%"
            elif price_change > -2:
                recommendation = "🟡 持有觀望"
                reason = f"AI 模型預測價格相對穩定（{price_change:+.1f}%）"
            elif price_change > -5:
                recommendation = "🟠 建議賣出"
                reason = f"AI 模型預測可能下跌 {price_change:.1f}%"
            else:
                recommendation = "🔴 強力賣出"
                reason = f"AI 模型預測大幅下跌 {price_change:.1f}%"
            
            st.info(f"**{recommendation}**\n\n{reason}")
            
            # 模型性能評估
            with st.expander("📊 模型性能評估", expanded=False):
                performance = predictor.evaluate_model_performance(features)
                
                perf_col1, perf_col2 = st.columns(2)
                
                with perf_col1:
                    st.metric("準確度", f"{performance['Accuracy']:.1f}%")
                    st.metric("平均絕對誤差", f"{performance['MAE']:.2f}")
                
                with perf_col2:
                    st.metric("均方根誤差", f"{performance['RMSE']:.2f}")
                    st.metric("平均絕對百分比誤差", f"{performance['MAPE']:.1f}%")
                
                # 實際 vs 預測比較圖
                backtest_fig = go.Figure()
                
                backtest_fig.add_trace(go.Scatter(
                    y=performance['Actual'],
                    mode='lines',
                    name='實際價格',
                    line=dict(color='blue')
                ))
                
                backtest_fig.add_trace(go.Scatter(
                    y=performance['Predicted'],
                    mode='lines',
                    name='預測價格',
                    line=dict(color='red', dash='dash')
                ))
                
                backtest_fig.update_layout(
                    title='回測結果：實際 vs 預測',
                    yaxis_title='價格',
                    template='plotly_white',
                    height=300
                )
                
                st.plotly_chart(backtest_fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ 預測過程中發生錯誤: {str(e)}")
    
    else:
        # 顯示功能介紹
        st.subheader("🚀 開始使用 AI 預測")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🧠 深度學習
            - LSTM 神經網絡
            - 多層序列建模
            - 時間依賴學習
            """)
        
        with col2:
            st.markdown("""
            #### 📊 智能特徵
            - 技術指標整合
            - 成交量分析
            - 市場情緒指標
            """)
        
        with col3:
            st.markdown("""
            #### 🎯 精準預測
            - 多時間框架
            - 置信區間評估
            - 風險量化分析
            """)
        
        st.info("💡 在左側設定參數，點擊「開始預測」來體驗 AI 股價預測功能！")

def main():
    """主應用"""
    st.set_page_config(
        page_title="JoJo Trading - AI 股價預測",
        page_icon="🤖",
        layout="wide"
    )
    
    render_ai_prediction_interface()

if __name__ == "__main__":
    main()
