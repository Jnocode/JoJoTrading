"""
💼 JoJo Trading - 智能投資組合管理
Intelligent Portfolio Management & Risk Analysis
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
def load_portfolio_css():
    """載入投資組合專用CSS樣式"""
    st.markdown("""
    <style>
    .portfolio-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    
    .performance-card {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .risk-card {
        background: linear-gradient(135deg, #fd7e14, #e74c3c);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .holding-card {
        background: white;
        border: 2px solid #e3f2fd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .holding-card:hover {
        border-color: #2196f3;
        transform: translateY(-2px);
    }
    
    .allocation-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .rebalance-alert {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

class PortfolioAnalyzer:
    """投資組合分析器"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 無風險利率2%
        
    def calculate_portfolio_metrics(self, returns, weights):
        """計算投資組合指標"""
        portfolio_return = np.sum(returns.mean() * weights) * 252
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std
        
        return {
            'annual_return': portfolio_return,
            'annual_volatility': portfolio_std,
            'sharpe_ratio': sharpe_ratio
        }
    
    def calculate_var(self, returns, confidence=0.05):
        """計算風險價值 (VaR)"""
        return np.percentile(returns, confidence * 100)
    
    def calculate_max_drawdown(self, prices):
        """計算最大回撤"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

def generate_portfolio_data():
    """生成示範投資組合數據"""
    holdings = {
        '2330': {'name': '台積電', 'shares': 1000, 'avg_cost': 580, 'current_price': 620, 'sector': '半導體'},
        '2317': {'name': '鴻海', 'shares': 2000, 'avg_cost': 105, 'current_price': 112, 'sector': '電子製造'},
        '2454': {'name': '聯發科', 'shares': 500, 'avg_cost': 850, 'current_price': 900, 'sector': '半導體'},
        '0050': {'name': '元大台灣50', 'shares': 1000, 'avg_cost': 135, 'current_price': 142, 'sector': 'ETF'},
        '2891': {'name': '中信金', 'shares': 1500, 'avg_cost': 22, 'current_price': 24, 'sector': '金融'},
        '2308': {'name': '台達電', 'shares': 800, 'avg_cost': 320, 'current_price': 350, 'sector': '電子零組件'}
    }
    
    # 計算持股價值
    for code, holding in holdings.items():
        holding['market_value'] = holding['shares'] * holding['current_price']
        holding['cost_value'] = holding['shares'] * holding['avg_cost']
        holding['unrealized_pnl'] = holding['market_value'] - holding['cost_value']
        holding['unrealized_pnl_pct'] = (holding['unrealized_pnl'] / holding['cost_value']) * 100
    
    return holdings

def render_portfolio_header():
    """渲染投資組合頁面標題"""
    st.markdown("""
    <div class="portfolio-header">
        <h1>💼 智能投資組合管理</h1>
        <p style="font-size: 1.1em;">Portfolio Management & Risk Analysis</p>
        <p style="font-size: 0.9em; opacity: 0.9;">
            專業資產配置 | 風險控制 | 績效分析 | 再平衡建議
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_portfolio_overview(holdings):
    """渲染投資組合總覽"""
    st.markdown("### 📊 投資組合總覽")
    
    # 計算總值
    total_market_value = sum(h['market_value'] for h in holdings.values())
    total_cost_value = sum(h['cost_value'] for h in holdings.values())
    total_unrealized_pnl = total_market_value - total_cost_value
    total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost_value) * 100
    
    # 績效指標卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="performance-card">
            <h3>📈 投資組合總值</h3>
            <h2>NT$ {total_market_value:,.0f}</h2>
            <p>當前市值</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color = "green" if total_unrealized_pnl > 0 else "red"
        st.markdown(f"""
        <div class="performance-card" style="background: linear-gradient(135deg, #{'28a745' if total_unrealized_pnl > 0 else 'e74c3c'}, #{'20c997' if total_unrealized_pnl > 0 else 'd63031'});">
            <h3>💰 未實現損益</h3>
            <h2>NT$ {total_unrealized_pnl:+,.0f}</h2>
            <p>{total_unrealized_pnl_pct:+.2f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.metric(
            "持股檔數",
            len(holdings),
            help="投資組合中的股票數量"
        )
    
    with col4:
        # 計算日變化 (模擬)
        daily_change = np.random.normal(0.001, 0.02)
        daily_change_value = total_market_value * daily_change
        
        st.metric(
            "今日變化",
            f"NT$ {daily_change_value:+,.0f}",
            f"{daily_change:+.2%}",
            delta_color="normal"
        )
    
    return total_market_value, total_cost_value

def render_holdings_table(holdings, total_market_value):
    """渲染持股明細表"""
    st.markdown("### 📋 持股明細")
    
    # 準備表格數據
    holdings_data = []
    for code, holding in holdings.items():
        weight = (holding['market_value'] / total_market_value) * 100
        holdings_data.append({
            '股票代碼': code,
            '股票名稱': holding['name'],
            '產業': holding['sector'],
            '持股數量': f"{holding['shares']:,}",
            '平均成本': f"NT$ {holding['avg_cost']:.2f}",
            '當前價格': f"NT$ {holding['current_price']:.2f}",
            '市值': f"NT$ {holding['market_value']:,.0f}",
            '權重': f"{weight:.1f}%",
            '未實現損益': f"NT$ {holding['unrealized_pnl']:+,.0f}",
            '報酬率': f"{holding['unrealized_pnl_pct']:+.1f}%"
        })
    
    holdings_df = pd.DataFrame(holdings_data)
    
    # 使用 Streamlit 的互動式表格
    st.dataframe(
        holdings_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "權重": st.column_config.ProgressColumn(
                "權重",
                help="在投資組合中的權重",
                min_value=0,
                max_value=50,
            ),
        }
    )

def render_allocation_analysis(holdings, total_market_value):
    """渲染資產配置分析"""
    st.markdown("### 🥧 資產配置分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 按股票的配置
        stock_allocation = []
        colors = px.colors.qualitative.Set3
        
        for i, (code, holding) in enumerate(holdings.items()):
            weight = (holding['market_value'] / total_market_value) * 100
            stock_allocation.append({
                'stock': f"{code} {holding['name']}",
                'weight': weight,
                'value': holding['market_value']
            })
        
        fig_stocks = go.Figure(data=[go.Pie(
            labels=[item['stock'] for item in stock_allocation],
            values=[item['weight'] for item in stock_allocation],
            hole=.3,
            hovertemplate='%{label}<br>權重: %{value:.1f}%<br>市值: NT$ %{customdata:,.0f}<extra></extra>',
            customdata=[item['value'] for item in stock_allocation]
        )])
        
        fig_stocks.update_layout(
            title="股票配置",
            height=400,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5)
        )
        
        st.plotly_chart(fig_stocks, use_container_width=True)
    
    with col2:
        # 按產業的配置
        sector_allocation = {}
        for holding in holdings.values():
            sector = holding['sector']
            if sector not in sector_allocation:
                sector_allocation[sector] = 0
            sector_allocation[sector] += holding['market_value']
        
        sector_weights = [(sector, (value/total_market_value)*100) 
                         for sector, value in sector_allocation.items()]
        
        fig_sectors = go.Figure(data=[go.Pie(
            labels=[item[0] for item in sector_weights],
            values=[item[1] for item in sector_weights],
            hole=.3,
            hovertemplate='%{label}<br>權重: %{value:.1f}%<extra></extra>'
        )])
        
        fig_sectors.update_layout(
            title="產業配置",
            height=400,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5)
        )
        
        st.plotly_chart(fig_sectors, use_container_width=True)

def render_risk_analysis(holdings):
    """渲染風險分析"""
    st.markdown("### ⚠️ 風險分析")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 集中度風險
        total_value = sum(h['market_value'] for h in holdings.values())
        max_holding = max(h['market_value'] for h in holdings.values())
        concentration_risk = (max_holding / total_value) * 100
        
        if concentration_risk > 30:
            risk_level = "高"
            risk_color = "#e74c3c"
        elif concentration_risk > 20:
            risk_level = "中"
            risk_color = "#f39c12"
        else:
            risk_level = "低"
            risk_color = "#27ae60"
        
        st.markdown(f"""
        <div class="risk-card" style="background: {risk_color};">
            <h4>集中度風險</h4>
            <h3>{concentration_risk:.1f}%</h3>
            <p>風險等級: {risk_level}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # 產業集中度
        sector_values = {}
        for holding in holdings.values():
            sector = holding['sector']
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += holding['market_value']
        
        max_sector_weight = max(sector_values.values()) / total_value * 100
        
        if max_sector_weight > 40:
            sector_risk = "高"
            sector_color = "#e74c3c"
        elif max_sector_weight > 25:
            sector_risk = "中"
            sector_color = "#f39c12"
        else:
            sector_risk = "低"
            sector_color = "#27ae60"
        
        st.markdown(f"""
        <div class="risk-card" style="background: {sector_color};">
            <h4>產業集中度</h4>
            <h3>{max_sector_weight:.1f}%</h3>
            <p>風險等級: {sector_risk}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # 波動性風險 (模擬)
        portfolio_volatility = np.random.uniform(15, 25)
        
        if portfolio_volatility > 22:
            vol_risk = "高"
            vol_color = "#e74c3c"
        elif portfolio_volatility > 18:
            vol_risk = "中"
            vol_color = "#f39c12"
        else:
            vol_risk = "低"
            vol_color = "#27ae60"
        
        st.markdown(f"""
        <div class="risk-card" style="background: {vol_color};">
            <h4>年化波動率</h4>
            <h3>{portfolio_volatility:.1f}%</h3>
            <p>風險等級: {vol_risk}</p>
        </div>
        """, unsafe_allow_html=True)

def render_performance_chart():
    """渲染績效走勢圖"""
    st.markdown("### 📈 績效走勢")
    
    # 生成模擬績效數據
    days = 252  # 一年交易日
    dates = pd.date_range(start=datetime.now()-timedelta(days=days), end=datetime.now(), freq='D')
    dates = dates[dates.dayofweek < 5]  # 只保留交易日
    
    # 模擬投資組合和基準指數的績效
    np.random.seed(42)
    portfolio_returns = np.random.normal(0.0008, 0.015, len(dates))
    benchmark_returns = np.random.normal(0.0005, 0.012, len(dates))
    
    # 計算累積報酬
    portfolio_cumulative = (1 + pd.Series(portfolio_returns)).cumprod()
    benchmark_cumulative = (1 + pd.Series(benchmark_returns)).cumprod()
    
    fig = go.Figure()
    
    # 投資組合線
    fig.add_trace(go.Scatter(
        x=dates[:len(portfolio_cumulative)],
        y=(portfolio_cumulative - 1) * 100,
        mode='lines',
        name='投資組合',
        line=dict(color='#2E86C1', width=2)
    ))
    
    # 基準線 (台股加權指數)
    fig.add_trace(go.Scatter(
        x=dates[:len(benchmark_cumulative)],
        y=(benchmark_cumulative - 1) * 100,
        mode='lines',
        name='台股加權指數',
        line=dict(color='#E74C3C', width=2)
    ))
    
    fig.update_layout(
        title='投資組合 vs 基準指數累積報酬',
        xaxis_title='日期',
        yaxis_title='累積報酬率 (%)',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 績效統計
    portfolio_final_return = (portfolio_cumulative.iloc[-1] - 1) * 100
    benchmark_final_return = (benchmark_cumulative.iloc[-1] - 1) * 100
    excess_return = portfolio_final_return - benchmark_final_return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("投資組合年化報酬", f"{portfolio_final_return:.2f}%")
    with col2:
        st.metric("基準指數年化報酬", f"{benchmark_final_return:.2f}%")
    with col3:
        st.metric("超額報酬", f"{excess_return:+.2f}%", delta=f"{excess_return:+.2f}%")

def render_rebalancing_suggestions(holdings, total_market_value):
    """渲染再平衡建議"""
    st.markdown("### ⚖️ 再平衡建議")
    
    # 設定目標權重 (範例)
    target_allocations = {
        '半導體': 40,
        '金融': 20,
        '電子製造': 15,
        'ETF': 15,
        '電子零組件': 10
    }
    
    # 計算當前權重
    current_allocations = {}
    for holding in holdings.values():
        sector = holding['sector']
        if sector not in current_allocations:
            current_allocations[sector] = 0
        current_allocations[sector] += holding['market_value']
    
    # 轉換為百分比
    for sector in current_allocations:
        current_allocations[sector] = (current_allocations[sector] / total_market_value) * 100
    
    # 檢查是否需要再平衡
    rebalance_needed = False
    rebalance_suggestions = []
    
    for sector, target_weight in target_allocations.items():
        current_weight = current_allocations.get(sector, 0)
        difference = current_weight - target_weight
        
        if abs(difference) > 5:  # 超過5%差異需要調整
            rebalance_needed = True
            if difference > 0:
                action = "減碼"
                color = "#e74c3c"
            else:
                action = "加碼"
                color = "#27ae60"
            
            rebalance_suggestions.append({
                'sector': sector,
                'current': current_weight,
                'target': target_weight,
                'difference': difference,
                'action': action,
                'color': color
            })
    
    if rebalance_needed:
        st.markdown("""
        <div class="rebalance-alert">
            <h4>⚠️ 建議進行投資組合再平衡</h4>
            <p>部分產業配置偏離目標權重超過5%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 再平衡建議表
        for suggestion in rebalance_suggestions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div class="holding-card">
                    <strong>{suggestion['sector']}</strong><br>
                    當前權重: {suggestion['current']:.1f}% | 目標權重: {suggestion['target']:.1f}%<br>
                    差異: {suggestion['difference']:+.1f}%
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: {suggestion['color']}; color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                    <strong>{suggestion['action']}</strong>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("✅ 投資組合配置良好，暫時不需要再平衡")

def main():
    """主函數"""
    # 載入CSS樣式
    load_portfolio_css()
    
    # 渲染頁面標題
    render_portfolio_header()
    
    # 生成示範數據
    holdings = generate_portfolio_data()
    
    # 主要內容區域
    tab1, tab2, tab3, tab4 = st.tabs(["📊 總覽", "📋 持股明細", "📈 績效分析", "⚖️ 再平衡"])
    
    with tab1:
        total_market_value, total_cost_value = render_portfolio_overview(holdings)
        render_allocation_analysis(holdings, total_market_value)
        render_risk_analysis(holdings)
    
    with tab2:
        render_holdings_table(holdings, total_market_value)
    
    with tab3:
        render_performance_chart()
    
    with tab4:
        render_rebalancing_suggestions(holdings, total_market_value)
    
    # 側邊欄工具
    with st.sidebar:
        st.markdown("### 🛠️ 投資組合工具")
        
        # 新增持股
        with st.expander("➕ 新增持股"):
            new_stock_code = st.text_input("股票代碼")
            new_shares = st.number_input("股數", min_value=1)
            new_price = st.number_input("買入價格", min_value=0.01)
            
            if st.button("新增"):
                st.success("新增持股功能開發中...")
        
        # 賣出持股
        with st.expander("➖ 賣出持股"):
            sell_stock = st.selectbox("選擇股票", list(holdings.keys()))
            sell_shares = st.number_input("賣出股數", min_value=1)
            
            if st.button("賣出"):
                st.success("賣出功能開發中...")
        
        st.markdown("---")
        
        # 快速統計
        st.markdown("### 📊 快速統計")
        
        total_value = sum(h['market_value'] for h in holdings.values())
        total_pnl = sum(h['unrealized_pnl'] for h in holdings.values())
        
        st.metric("總市值", f"NT$ {total_value:,.0f}")
        st.metric("總損益", f"NT$ {total_pnl:+,.0f}")
        st.metric("持股數", f"{len(holdings)} 檔")
        
        # 風險指標
        st.markdown("### ⚠️ 風險提醒")
        st.warning("💡 半導體類股權重偏高，建議分散投資")
        st.info("📈 建議定期檢視投資組合配置")

if __name__ == "__main__":
    main()
