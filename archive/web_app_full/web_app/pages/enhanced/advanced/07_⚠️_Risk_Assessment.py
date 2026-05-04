"""
⚠️ JoJo Trading - 投資風險評估中心
Investment Risk Assessment Center

提供全方位風險評估工具：
- VaR (Value at Risk) 計算
- 投資組合風險分析
- 相關性風險評估
- 壓力測試
- 風險調整報酬分析
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
from scipy import stats
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class RiskAssessmentEngine:
    """投資風險評估引擎"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 無風險利率 2%
        
    def get_stock_data(self, symbols: List[str], period: str = '2y') -> Dict[str, pd.DataFrame]:
        """獲取多個股票的數據"""
        data = {}
        
        for symbol in symbols:
            try:
                # 台股代碼格式處理
                if symbol.isdigit() and len(symbol) == 4:
                    ticker_symbol = f"{symbol}.TW"
                else:
                    ticker_symbol = symbol
                
                ticker = yf.Ticker(ticker_symbol)
                df = ticker.history(period=period)
                
                if not df.empty:
                    data[symbol] = df
                else:
                    st.warning(f"無法獲取 {symbol} 的數據")
                    
            except Exception as e:
                st.error(f"獲取 {symbol} 數據時發生錯誤: {str(e)}")
        
        return data
    
    def calculate_returns(self, df: pd.DataFrame) -> pd.Series:
        """計算日報酬率"""
        return df['Close'].pct_change().dropna()
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.05) -> Dict:
        """計算風險值 (Value at Risk)"""
        
        # 歷史模擬法
        historical_var = np.percentile(returns, confidence_level * 100)
        
        # 參數法（假設常態分佈）
        mean_return = returns.mean()
        std_return = returns.std()
        parametric_var = stats.norm.ppf(confidence_level, mean_return, std_return)
        
        # 條件風險值 (CVaR/Expected Shortfall)
        cvar = returns[returns <= historical_var].mean()
        
        return {
            'historical_var': historical_var,
            'parametric_var': parametric_var,
            'cvar': cvar,
            'var_95': np.percentile(returns, 5),
            'var_99': np.percentile(returns, 1)
        }
    
    def calculate_portfolio_risk(self, returns_data: Dict[str, pd.Series], 
                               weights: Dict[str, float]) -> Dict:
        """計算投資組合風險"""
        
        # 建立報酬率矩陣
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()
        
        # 權重向量
        weight_vector = np.array([weights.get(symbol, 0) for symbol in returns_df.columns])
        weight_vector = weight_vector / weight_vector.sum()  # 標準化權重
        
        # 計算投資組合報酬率
        portfolio_returns = (returns_df * weight_vector).sum(axis=1)
        
        # 計算風險指標
        portfolio_std = portfolio_returns.std()
        portfolio_mean = portfolio_returns.mean()
        
        # 計算相關矩陣
        correlation_matrix = returns_df.corr()
        
        # 計算協方差矩陣
        cov_matrix = returns_df.cov()
        
        # 投資組合變異數
        portfolio_variance = np.dot(weight_vector.T, np.dot(cov_matrix, weight_vector))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # 計算 Beta 值（相對於市場）
        if '0050' in returns_data:  # 使用 0050 作為市場代理
            market_returns = returns_data['0050']
            covariance = np.cov(portfolio_returns, market_returns)[0][1]
            market_variance = market_returns.var()
            beta = covariance / market_variance if market_variance != 0 else 1
        else:
            beta = 1
        
        # Sharpe Ratio
        excess_return = portfolio_mean - (self.risk_free_rate / 252)  # 日化無風險利率
        sharpe_ratio = excess_return / portfolio_std if portfolio_std != 0 else 0
        
        # Treynor Ratio
        treynor_ratio = excess_return / beta if beta != 0 else 0
        
        # Information Ratio
        tracking_error = portfolio_std
        information_ratio = excess_return / tracking_error if tracking_error != 0 else 0
        
        return {
            'portfolio_returns': portfolio_returns,
            'portfolio_std': portfolio_std,
            'portfolio_mean': portfolio_mean,
            'portfolio_volatility': portfolio_volatility,
            'correlation_matrix': correlation_matrix,
            'weights': dict(zip(returns_df.columns, weight_vector)),
            'beta': beta,
            'sharpe_ratio': sharpe_ratio,
            'treynor_ratio': treynor_ratio,
            'information_ratio': information_ratio
        }
    
    def monte_carlo_simulation(self, returns: pd.Series, num_simulations: int = 1000,
                             time_horizon: int = 252) -> np.ndarray:
        """蒙地卡羅模擬"""
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # 生成隨機數
        random_returns = np.random.normal(mean_return, std_return, 
                                        (num_simulations, time_horizon))
        
        # 計算累積報酬
        cumulative_returns = np.cumprod(1 + random_returns, axis=1)
        
        return cumulative_returns
    
    def stress_test(self, returns: pd.Series, scenarios: List[Dict]) -> Dict:
        """壓力測試"""
        
        stress_results = {}
        
        for scenario in scenarios:
            name = scenario['name']
            shock = scenario['shock']  # 衝擊幅度
            
            # 應用衝擊
            stressed_returns = returns + shock
            
            # 計算風險指標
            var_result = self.calculate_var(stressed_returns)
            
            stress_results[name] = {
                'stressed_var_95': var_result['var_95'],
                'stressed_var_99': var_result['var_99'],
                'stressed_mean': stressed_returns.mean(),
                'stressed_std': stressed_returns.std()
            }
        
        return stress_results
    
    def calculate_drawdown(self, prices: pd.Series) -> Dict:
        """計算最大回撤"""
        
        # 計算累積報酬
        cumulative = (1 + prices.pct_change()).cumprod()
        
        # 計算滾動最大值
        rolling_max = cumulative.expanding().max()
        
        # 計算回撤
        drawdown = (cumulative - rolling_max) / rolling_max
        
        # 最大回撤
        max_drawdown = drawdown.min()
        
        # 最大回撤期間
        max_drawdown_date = drawdown.idxmin()
        
        # 計算回撤持續時間
        drawdown_duration = self._calculate_drawdown_duration(drawdown)
        
        return {
            'drawdown_series': drawdown,
            'max_drawdown': max_drawdown,
            'max_drawdown_date': max_drawdown_date,
            'max_duration': drawdown_duration['max_duration'],
            'current_drawdown': drawdown.iloc[-1]
        }
    
    def _calculate_drawdown_duration(self, drawdown: pd.Series) -> Dict:
        """計算回撤持續時間"""
        
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0
        
        for is_down in in_drawdown:
            if is_down:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        return {
            'max_duration': max(drawdown_periods) if drawdown_periods else 0,
            'avg_duration': np.mean(drawdown_periods) if drawdown_periods else 0,
            'current_duration': current_period
        }

def create_risk_dashboard(risk_engine: RiskAssessmentEngine, symbols: List[str], 
                         weights: Dict[str, float], period: str) -> None:
    """創建風險評估儀表板"""
    
    # 獲取數據
    with st.spinner("正在獲取數據並計算風險指標..."):
        stock_data = risk_engine.get_stock_data(symbols, period)
        
        if not stock_data:
            st.error("無法獲取任何股票數據")
            return
        
        # 計算報酬率
        returns_data = {}
        for symbol, df in stock_data.items():
            returns_data[symbol] = risk_engine.calculate_returns(df)
        
        # 計算投資組合風險
        portfolio_risk = risk_engine.calculate_portfolio_risk(returns_data, weights)
    
    # 顯示關鍵風險指標
    st.subheader("🎯 關鍵風險指標")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        daily_vol = portfolio_risk['portfolio_std'] * 100
        annual_vol = daily_vol * np.sqrt(252)
        st.metric("投資組合波動率", f"{annual_vol:.2f}%", f"日波動率: {daily_vol:.2f}%")
    
    with col2:
        sharpe = portfolio_risk['sharpe_ratio']
        st.metric("Sharpe比率", f"{sharpe:.3f}")
    
    with col3:
        beta = portfolio_risk['beta']
        st.metric("Beta係數", f"{beta:.3f}")
    
    with col4:
        # 計算投資組合 VaR
        portfolio_var = risk_engine.calculate_var(portfolio_risk['portfolio_returns'])
        var_95 = portfolio_var['var_95'] * 100
        st.metric("VaR (95%)", f"{var_95:.2f}%")
    
    # VaR 分析
    st.subheader("⚠️ 風險值 (VaR) 分析")
    
    var_col1, var_col2 = st.columns(2)
    
    with var_col1:
        # VaR 比較表
        var_data = []
        for symbol in symbols:
            if symbol in returns_data:
                var_result = risk_engine.calculate_var(returns_data[symbol])
                var_data.append({
                    '股票': symbol,
                    'VaR 95%': f"{var_result['var_95']*100:.2f}%",
                    'VaR 99%': f"{var_result['var_99']*100:.2f}%",
                    'CVaR': f"{var_result['cvar']*100:.2f}%"
                })
        
        # 添加投資組合 VaR
        var_data.append({
            '股票': '投資組合',
            'VaR 95%': f"{portfolio_var['var_95']*100:.2f}%",
            'VaR 99%': f"{portfolio_var['var_99']*100:.2f}%",
            'CVaR': f"{portfolio_var['cvar']*100:.2f}%"
        })
        
        var_df = pd.DataFrame(var_data)
        st.dataframe(var_df, use_container_width=True)
    
    with var_col2:
        # VaR 視覺化
        fig_var = go.Figure()
        
        portfolio_returns = portfolio_risk['portfolio_returns']
        
        # 直方圖
        fig_var.add_trace(go.Histogram(
            x=portfolio_returns * 100,
            nbinsx=50,
            name='報酬率分佈',
            opacity=0.7
        ))
        
        # VaR 線
        fig_var.add_vline(x=portfolio_var['var_95']*100, line_dash="dash", 
                         line_color="red", annotation_text="VaR 95%")
        fig_var.add_vline(x=portfolio_var['var_99']*100, line_dash="dash", 
                         line_color="darkred", annotation_text="VaR 99%")
        
        fig_var.update_layout(
            title="投資組合報酬率分佈與VaR",
            xaxis_title="日報酬率 (%)",
            yaxis_title="頻率",
            height=400
        )
        
        st.plotly_chart(fig_var, use_container_width=True)
    
    # 相關性分析
    st.subheader("🔗 相關性風險分析")
    
    correlation_matrix = portfolio_risk['correlation_matrix']
    
    # 相關性熱圖
    fig_corr = px.imshow(
        correlation_matrix,
        title="股票相關性矩陣",
        color_continuous_scale="RdBu",
        aspect="auto"
    )
    
    fig_corr.update_layout(height=500)
    st.plotly_chart(fig_corr, use_container_width=True)
    
    # 相關性統計
    corr_stats = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均相關性", f"{corr_stats.mean():.3f}")
    with col2:
        st.metric("最大相關性", f"{corr_stats.max():.3f}")
    with col3:
        st.metric("最小相關性", f"{corr_stats.min():.3f}")
    
    # 壓力測試
    st.subheader("🧪 壓力測試")
    
    stress_scenarios = [
        {'name': '市場崩盤', 'shock': -0.20},
        {'name': '中度修正', 'shock': -0.10},
        {'name': '輕微下跌', 'shock': -0.05},
        {'name': '通膨衝擊', 'shock': -0.15}
    ]
    
    stress_results = risk_engine.stress_test(
        portfolio_risk['portfolio_returns'], stress_scenarios
    )
    
    stress_data = []
    for scenario, results in stress_results.items():
        stress_data.append({
            '情境': scenario,
            '壓力VaR 95%': f"{results['stressed_var_95']*100:.2f}%",
            '壓力VaR 99%': f"{results['stressed_var_99']*100:.2f}%",
            '預期報酬': f"{results['stressed_mean']*100:.2f}%",
            '波動率': f"{results['stressed_std']*100:.2f}%"
        })
    
    stress_df = pd.DataFrame(stress_data)
    st.dataframe(stress_df, use_container_width=True)
    
    # 回撤分析
    st.subheader("📉 回撤分析")
    
    # 選擇一個主要標的進行回撤分析
    main_symbol = symbols[0] if symbols else None
    if main_symbol and main_symbol in stock_data:
        drawdown_result = risk_engine.calculate_drawdown(stock_data[main_symbol]['Close'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("最大回撤", f"{drawdown_result['max_drawdown']*100:.2f}%")
        with col2:
            st.metric("最大回撤持續期", f"{drawdown_result['max_duration']} 天")
        with col3:
            st.metric("當前回撤", f"{drawdown_result['current_drawdown']*100:.2f}%")
        
        # 回撤圖表
        fig_dd = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=[f'{main_symbol} 價格走勢', '回撤百分比'],
            vertical_spacing=0.1
        )
        
        # 價格走勢
        fig_dd.add_trace(go.Scatter(
            x=stock_data[main_symbol].index,
            y=stock_data[main_symbol]['Close'],
            name='收盤價',
            line=dict(color='blue')
        ), row=1, col=1)
        
        # 回撤
        fig_dd.add_trace(go.Scatter(
            x=drawdown_result['drawdown_series'].index,
            y=drawdown_result['drawdown_series'] * 100,
            name='回撤 %',
            fill='tonexty',
            line=dict(color='red')
        ), row=2, col=1)
        
        fig_dd.update_layout(
            title=f"{main_symbol} 回撤分析",
            height=600,
            showlegend=True
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)

def main():
    st.set_page_config(
        page_title="投資風險評估中心",
        page_icon="⚠️",
        layout="wide"
    )
    
    st.title("⚠️ 投資風險評估中心")
    st.markdown("---")
    
    # 初始化風險評估引擎
    risk_engine = RiskAssessmentEngine()
    
    # 側邊欄配置
    with st.sidebar:
        st.header("🔧 風險評估設定")
        
        # 股票選擇
        st.subheader("📈 投資組合設定")
        
        num_stocks = st.number_input("股票數量", min_value=1, max_value=10, value=3)
        
        symbols = []
        weights = {}
        
        for i in range(num_stocks):
            col1, col2 = st.columns([2, 1])
            with col1:
                symbol = st.text_input(f"股票 {i+1}", 
                                     value=["2330", "0050", "2454"][i] if i < 3 else "",
                                     key=f"symbol_{i}")
            with col2:
                weight = st.number_input(f"權重 {i+1}", 
                                       min_value=0.0, max_value=1.0, 
                                       value=1.0/num_stocks, step=0.01,
                                       key=f"weight_{i}")
            
            if symbol:
                symbols.append(symbol)
                weights[symbol] = weight
        
        # 標準化權重
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        # 時間範圍
        period = st.selectbox(
            "分析期間",
            ["6mo", "1y", "2y", "3y", "5y"],
            index=2
        )
        
        # 風險參數
        st.subheader("⚙️ 風險參數")
        confidence_level = st.slider("VaR 信心水準", 0.90, 0.99, 0.95, 0.01)
        risk_free_rate = st.number_input("無風險利率 (%)", value=2.0, min_value=0.0, max_value=10.0)
        
        # 更新風險引擎參數
        risk_engine.risk_free_rate = risk_free_rate / 100
        
        # 分析按鈕
        analyze_btn = st.button("🔍 開始風險評估", type="primary")
    
    # 主要內容
    if analyze_btn:
        if not symbols:
            st.error("請至少輸入一個股票代碼")
            return
        
        st.info(f"正在分析投資組合: {', '.join(symbols)}")
        st.info(f"權重分配: {', '.join([f'{k}: {v:.1%}' for k, v in weights.items()])}")
        
        # 創建風險評估儀表板
        create_risk_dashboard(risk_engine, symbols, weights, period)
    
    else:
        # 顯示說明
        st.markdown("""
        ## 📋 風險評估功能說明
        
        本工具提供以下風險評估功能：
        
        ### 🎯 關鍵風險指標
        - **投資組合波動率**: 衡量投資組合價格變動的程度
        - **Sharpe比率**: 風險調整後報酬率指標
        - **Beta係數**: 相對於市場的系統性風險
        - **VaR**: 在特定信心水準下的最大可能損失
        
        ### ⚠️ 風險值 (VaR) 分析
        - 95% 和 99% 信心水準的 VaR 計算
        - 條件風險值 (CVaR) 分析
        - 投資組合與個股 VaR 比較
        
        ### 🔗 相關性風險分析
        - 股票間相關性矩陣
        - 分散化效果評估
        - 集中度風險識別
        
        ### 🧪 壓力測試
        - 市場崩盤情境模擬
        - 各種不利情境下的投資組合表現
        - 極端風險評估
        
        ### 📉 回撤分析
        - 最大回撤計算
        - 回撤持續時間分析
        - 當前回撤狀況
        
        **使用方法**: 在左側設定投資組合股票與權重，點擊「開始風險評估」即可獲得完整的風險分析報告。
        """)

if __name__ == "__main__":
    main()
