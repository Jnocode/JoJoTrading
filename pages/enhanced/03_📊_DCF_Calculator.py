"""
📊 JoJo Trading - 專業級 DCF 估值計算器
Professional DCF Valuation Calculator with Advanced Features
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
import json

# 添加項目路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# 設置頁面配置
st.set_page_config(
    page_title="DCF 估值計算器 - JoJo Trading",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 載入自定義CSS
def load_dcf_css():
    """載入DCF專用CSS樣式"""
    st.markdown("""
    <style>
    .dcf-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    
    .input-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .result-card {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .scenario-card {
        background: white;
        border: 2px solid #e3f2fd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .scenario-card:hover {
        border-color: #2196f3;
        box-shadow: 0 4px 8px rgba(33, 150, 243, 0.2);
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .calculation-step {
        background: white;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

def render_dcf_header():
    """渲染DCF頁面標題"""
    st.markdown("""
    <div class="dcf-header">
        <h1>📊 專業級 DCF 估值計算器</h1>
        <p style="font-size: 1.1em;">Discounted Cash Flow Valuation Calculator</p>
        <p style="font-size: 0.9em; opacity: 0.9;">
            基於現金流折現模型的企業內在價值評估工具
        </p>
    </div>
    """, unsafe_allow_html=True)

class DCFCalculatorAdvanced:
    """進階DCF計算器"""
    
    def __init__(self):
        self.years_forecast = 5
        self.terminal_growth_rate = 0.025
        self.discount_rate = 0.10
        
    def calculate_dcf_value(self, financial_data, assumptions):
        """計算DCF價值"""
        try:
            # 提取參數
            initial_fcf = assumptions['initial_fcf']
            growth_rates = assumptions['growth_rates']
            discount_rate = assumptions['discount_rate']
            terminal_growth = assumptions['terminal_growth']
            shares_outstanding = assumptions['shares_outstanding']
            
            # 計算預測現金流
            fcf_projections = []
            current_fcf = initial_fcf
            
            for i, growth_rate in enumerate(growth_rates):
                current_fcf *= (1 + growth_rate)
                fcf_projections.append(current_fcf)
            
            # 計算現值
            pv_fcf = []
            for i, fcf in enumerate(fcf_projections):
                pv = fcf / ((1 + discount_rate) ** (i + 1))
                pv_fcf.append(pv)
            
            # 計算終值
            terminal_fcf = fcf_projections[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            pv_terminal = terminal_value / ((1 + discount_rate) ** len(growth_rates))
            
            # 企業價值
            enterprise_value = sum(pv_fcf) + pv_terminal
            
            # 每股價值
            value_per_share = enterprise_value / shares_outstanding
            
            return {
                'fcf_projections': fcf_projections,
                'pv_fcf': pv_fcf,
                'terminal_value': terminal_value,
                'pv_terminal': pv_terminal,
                'enterprise_value': enterprise_value,
                'value_per_share': value_per_share,
                'total_pv_fcf': sum(pv_fcf)
            }
            
        except Exception as e:
            st.error(f"DCF計算錯誤: {e}")
            return None

def get_taiwan_stocks():
    """獲取台股清單"""
    return {
        "2330": "台積電",
        "2317": "鴻海",
        "2454": "聯發科",
        "2382": "廣達",
        "2308": "台達電",
        "6505": "台塑化",
        "2891": "中信金",
        "2882": "國泰金",
        "2303": "聯電",
        "3008": "大立光"
    }

def load_sample_data(stock_code):
    """載入樣本數據"""
    sample_data = {
        "2330": {
            "company_name": "台積電",
            "current_fcf": 750000,  # 百萬元
            "shares_outstanding": 25908,  # 百萬股
            "industry": "半導體",
            "market_cap": 15000000,
            "revenue_growth": [0.12, 0.10, 0.08, 0.06, 0.05],
            "margin_trend": "穩定",
            "capex_ratio": 0.25
        },
        "2317": {
            "company_name": "鴻海",
            "current_fcf": 280000,
            "shares_outstanding": 13920,
            "industry": "電子製造",
            "market_cap": 1800000,
            "revenue_growth": [0.08, 0.06, 0.05, 0.04, 0.03],
            "margin_trend": "改善中",
            "capex_ratio": 0.15
        }
    }
    
    return sample_data.get(stock_code, sample_data["2330"])

def render_input_section():
    """渲染輸入區域"""
    st.markdown("### 📝 基本資料輸入")
    
    # 股票選擇
    col1, col2 = st.columns([1, 2])
    
    with col1:
        stocks = get_taiwan_stocks()
        selected_stock = st.selectbox(
            "選擇股票",
            options=list(stocks.keys()),
            format_func=lambda x: f"{x} {stocks[x]}"
        )
    
    with col2:
        # 載入選中股票的數據
        stock_data = load_sample_data(selected_stock)
        st.info(f"已選擇: **{stock_data['company_name']}** ({selected_stock})")
    
    # 分成兩欄顯示輸入
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("""
        <div class="input-section">
            <h4>💰 財務數據</h4>
        </div>
        """, unsafe_allow_html=True)
        
        initial_fcf = st.number_input(
            "當前自由現金流 (百萬元)",
            value=float(stock_data['current_fcf']),
            min_value=0.0,
            step=1000.0,
            help="公司最近一年的自由現金流"
        )
        
        shares_outstanding = st.number_input(
            "流通股數 (百萬股)",
            value=float(stock_data['shares_outstanding']),
            min_value=0.1,
            step=100.0,
            help="公司總流通股數"
        )
        
        # 現金和債務
        cash = st.number_input(
            "現金及約當現金 (百萬元)",
            value=500000.0,
            min_value=0.0,
            step=10000.0
        )
        
        debt = st.number_input(
            "總債務 (百萬元)",
            value=200000.0,
            min_value=0.0,
            step=10000.0
        )
    
    with col_right:
        st.markdown("""
        <div class="input-section">
            <h4>📈 預測假設</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # 成長率設定
        st.markdown("**📊 年度成長率預測**")
        
        growth_rates = []
        default_rates = stock_data['revenue_growth']
        
        for i in range(5):
            rate = st.slider(
                f"第 {i+1} 年成長率",
                min_value=-0.20,
                max_value=0.50,
                value=default_rates[i],
                step=0.01,
                format="%.1%%",
                key=f"growth_{i}"
            )
            growth_rates.append(rate)
        
        # 折現率和終值成長率
        discount_rate = st.slider(
            "加權平均資本成本 (WACC)",
            min_value=0.05,
            max_value=0.20,
            value=0.10,
            step=0.005,
            format="%.1%%",
            help="公司的資本成本，用於折現未來現金流"
        )
        
        terminal_growth = st.slider(
            "永續成長率",
            min_value=0.00,
            max_value=0.05,
            value=0.025,
            step=0.005,
            format="%.1%%",
            help="公司長期永續成長率，通常接近GDP成長率"
        )
    
    return {
        'stock_code': selected_stock,
        'stock_data': stock_data,
        'initial_fcf': initial_fcf,
        'shares_outstanding': shares_outstanding,
        'cash': cash,
        'debt': debt,
        'growth_rates': growth_rates,
        'discount_rate': discount_rate,
        'terminal_growth': terminal_growth
    }

def render_dcf_calculation(inputs):
    """渲染DCF計算結果"""
    st.markdown("### 📊 DCF 估值結果")
    
    # 準備計算參數
    assumptions = {
        'initial_fcf': inputs['initial_fcf'],
        'growth_rates': inputs['growth_rates'],
        'discount_rate': inputs['discount_rate'],
        'terminal_growth': inputs['terminal_growth'],
        'shares_outstanding': inputs['shares_outstanding']
    }
    
    # 計算DCF
    calculator = DCFCalculatorAdvanced()
    result = calculator.calculate_dcf_value({}, assumptions)
    
    if result:
        # 計算淨現值 (考慮現金和債務)
        net_value = result['enterprise_value'] + inputs['cash'] - inputs['debt']
        value_per_share_net = net_value / inputs['shares_outstanding']
        
        # 主要結果展示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="result-card">
                <h3>📈 每股內在價值</h3>
                <h2>NT$ {value_per_share_net:,.2f}</h2>
                <p>基於DCF模型計算</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric(
                "企業價值",
                f"NT$ {result['enterprise_value']:,.0f} M",
                help="未來現金流的現值總和"
            )
        
        with col3:
            st.metric(
                "淨現值",
                f"NT$ {net_value:,.0f} M",
                help="企業價值減去淨債務"
            )
        
        with col4:
            safety_margin = -0.15  # 假設安全邊際
            st.metric(
                "安全邊際價格",
                f"NT$ {value_per_share_net * (1 + safety_margin):,.2f}",
                delta=f"{safety_margin:.1%}",
                help="考慮安全邊際的建議買入價格"
            )
        
        # 詳細計算步驟
        st.markdown("### 🔍 詳細計算過程")
        
        # 現金流預測表
        years = list(range(1, 6))
        fcf_df = pd.DataFrame({
            '年度': [f'第{i}年' for i in years],
            '自由現金流 (M)': [f'{fcf:,.0f}' for fcf in result['fcf_projections']],
            '成長率': [f'{rate:.1%}' for rate in inputs['growth_rates']],
            '現值 (M)': [f'{pv:,.0f}' for pv in result['pv_fcf']],
            '折現因子': [f'{1/((1+inputs["discount_rate"])**(i)):.3f}' for i in years]
        })
        
        st.markdown("#### 📊 現金流預測與現值計算")
        st.dataframe(fcf_df, use_container_width=True, hide_index=True)
        
        # 終值計算
        st.markdown("#### 🎯 終值計算")
        col_tv1, col_tv2 = st.columns(2)
        
        with col_tv1:
            st.markdown(f"""
            <div class="calculation-step">
                <strong>終值現金流:</strong> NT$ {result['fcf_projections'][-1] * (1 + inputs['terminal_growth']):,.0f} M<br>
                <strong>終值:</strong> NT$ {result['terminal_value']:,.0f} M<br>
                <strong>終值現值:</strong> NT$ {result['pv_terminal']:,.0f} M
            </div>
            """, unsafe_allow_html=True)
        
        with col_tv2:
            # 價值構成圓餅圖
            labels = ['現金流現值', '終值現值']
            values = [result['total_pv_fcf'], result['pv_terminal']]
            
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
            fig_pie.update_layout(
                title="企業價值構成",
                height=300,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    return result

def render_sensitivity_analysis(inputs, base_result):
    """渲染敏感性分析"""
    st.markdown("### 🎯 敏感性分析")
    
    if base_result is None:
        st.warning("請先完成基本DCF計算")
        return
    
    # 創建敏感性分析參數範圍
    wacc_range = np.arange(inputs['discount_rate'] - 0.02, inputs['discount_rate'] + 0.03, 0.005)
    growth_range = np.arange(inputs['terminal_growth'] - 0.01, inputs['terminal_growth'] + 0.02, 0.0025)
    
    # 計算敏感性矩陣
    sensitivity_matrix = []
    wacc_labels = []
    growth_labels = []
    
    calculator = DCFCalculatorAdvanced()
    
    for wacc in wacc_range:
        row = []
        if len(wacc_labels) == 0:
            wacc_labels = [f"{w:.1%}" for w in wacc_range]
        
        for growth in growth_range:
            if len(growth_labels) == 0:
                growth_labels = [f"{g:.1%}" for g in growth_range]
            
            # 修改參數並重新計算
            temp_assumptions = {
                'initial_fcf': inputs['initial_fcf'],
                'growth_rates': inputs['growth_rates'],
                'discount_rate': wacc,
                'terminal_growth': growth,
                'shares_outstanding': inputs['shares_outstanding']
            }
            
            temp_result = calculator.calculate_dcf_value({}, temp_assumptions)
            if temp_result:
                net_value = temp_result['enterprise_value'] + inputs['cash'] - inputs['debt']
                value_per_share = net_value / inputs['shares_outstanding']
                row.append(value_per_share)
            else:
                row.append(0)
        
        sensitivity_matrix.append(row)
    
    # 創建熱力圖
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=sensitivity_matrix,
        x=growth_labels,
        y=wacc_labels,
        colorscale='RdYlGn',
        hoverongaps=False,
        hovertemplate='永續成長率: %{x}<br>WACC: %{y}<br>每股價值: NT$%{z:.2f}<extra></extra>'
    ))
    
    fig_heatmap.update_layout(
        title='敏感性分析 - 每股內在價值',
        xaxis_title='永續成長率',
        yaxis_title='加權平均資本成本 (WACC)',
        height=500
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 情境分析
    st.markdown("#### 📋 情境分析")
    
    col_scen1, col_scen2, col_scen3 = st.columns(3)
    
    scenarios = {
        '樂觀': {'wacc_adj': -0.01, 'growth_adj': +0.005, 'fcf_multiplier': 1.2},
        '基準': {'wacc_adj': 0.00, 'growth_adj': 0.000, 'fcf_multiplier': 1.0},
        '悲觀': {'wacc_adj': +0.01, 'growth_adj': -0.005, 'fcf_multiplier': 0.8}
    }
    
    for i, (scenario_name, adjustments) in enumerate(scenarios.items()):
        with [col_scen1, col_scen2, col_scen3][i]:
            # 調整參數
            adj_assumptions = {
                'initial_fcf': inputs['initial_fcf'] * adjustments['fcf_multiplier'],
                'growth_rates': inputs['growth_rates'],
                'discount_rate': inputs['discount_rate'] + adjustments['wacc_adj'],
                'terminal_growth': inputs['terminal_growth'] + adjustments['growth_adj'],
                'shares_outstanding': inputs['shares_outstanding']
            }
            
            scenario_result = calculator.calculate_dcf_value({}, adj_assumptions)
            if scenario_result:
                net_value = scenario_result['enterprise_value'] + inputs['cash'] - inputs['debt']
                scenario_price = net_value / inputs['shares_outstanding']
                
                color = "normal" if scenario_name == "基準" else ("inverse" if scenario_name == "樂觀" else "off")
                
                st.markdown(f"""
                <div class="scenario-card">
                    <h4>{scenario_name}情境</h4>
                    <h3>NT$ {scenario_price:.2f}</h3>
                    <p style="font-size: 0.9em;">
                        WACC: {adj_assumptions['discount_rate']:.1%}<br>
                        永續成長: {adj_assumptions['terminal_growth']:.1%}
                    </p>
                </div>
                """, unsafe_allow_html=True)

def render_comparison_tools():
    """渲染比較工具"""
    st.markdown("### 📊 估值比較工具")
    
    # 相對估值倍數
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 相對估值倍數")
        
        # 樣本數據
        pe_ratio = st.number_input("P/E 本益比", value=15.5, min_value=0.0, step=0.1)
        pb_ratio = st.number_input("P/B 股價淨值比", value=2.1, min_value=0.0, step=0.1)
        eps = st.number_input("每股盈餘 (EPS)", value=12.5, min_value=0.0, step=0.1)
        book_value = st.number_input("每股淨值", value=85.0, min_value=0.0, step=0.1)
        
        # 計算相對估值
        pe_price = pe_ratio * eps
        pb_price = pb_ratio * book_value
        
        st.markdown(f"""
        **相對估值結果:**
        - P/E 估值: NT$ {pe_price:.2f}
        - P/B 估值: NT$ {pb_price:.2f}
        """)
    
    with col2:
        st.markdown("#### 🎯 估值方法比較")
        
        # 假設DCF價值
        dcf_value = 150.0  # 這應該從實際計算結果獲取
        
        comparison_data = pd.DataFrame({
            '估值方法': ['DCF估值', 'P/E估值', 'P/B估值'],
            '價格': [dcf_value, pe_price, pb_price],
            '權重': [0.5, 0.3, 0.2]
        })
        
        # 加權平均價格
        weighted_price = (comparison_data['價格'] * comparison_data['權重']).sum()
        
        st.dataframe(comparison_data, use_container_width=True, hide_index=True)
        st.success(f"加權平均目標價: NT$ {weighted_price:.2f}")

def main():
    """主函數"""
    # 載入CSS樣式
    load_dcf_css()
    
    # 渲染頁面標題
    render_dcf_header()
    
    # 輸入區域
    inputs = render_input_section()
    
    # 計算按鈕
    if st.button("🚀 執行 DCF 估值分析", type="primary", use_container_width=True):
        with st.spinner("正在計算DCF估值..."):
            result = render_dcf_calculation(inputs)
            
            if result:
                # 分頁顯示結果
                tab1, tab2, tab3 = st.tabs(["📊 基本結果", "🎯 敏感性分析", "📋 比較分析"])
                
                with tab2:
                    render_sensitivity_analysis(inputs, result)
                
                with tab3:
                    render_comparison_tools()
    
    # 側邊欄工具
    with st.sidebar:
        st.markdown("### 🛠️ 分析工具")
        
        # 匯出功能
        if st.button("📄 匯出報告", help="匯出DCF分析報告為PDF"):
            st.success("報告匯出功能開發中...")
        
        # 儲存模板
        if st.button("💾 儲存為模板", help="儲存當前參數為模板"):
            st.success("模板儲存功能開發中...")
        
        # 載入模板
        if st.button("📂 載入模板", help="載入之前儲存的參數模板"):
            st.success("模板載入功能開發中...")
        
        st.markdown("---")
        
        # 幫助資訊
        st.markdown("### ❓ 使用說明")
        with st.expander("DCF 模型說明"):
            st.markdown("""
            **DCF (現金流折現) 模型**
            
            DCF是評估企業內在價值的重要方法：
            
            1. **預測自由現金流**: 估算未來5年的現金流
            2. **計算現值**: 使用WACC折現
            3. **計算終值**: 永續成長模型
            4. **求得企業價值**: 現值總和
            5. **計算每股價值**: 除以流通股數
            """)
        
        with st.expander("參數設定指引"):
            st.markdown("""
            **重要參數說明:**
            
            - **WACC**: 加權平均資本成本，通常8%-12%
            - **永續成長率**: 長期成長率，通常2%-4%
            - **成長率**: 基於行業趨勢和公司基本面
            - **安全邊際**: 建議15%-25%的安全邊際
            """)

if __name__ == "__main__":
    main()
