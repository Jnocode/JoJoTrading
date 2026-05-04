"""
JoJo Trading DCF 功能測試
測試 DCF 估值頁面的核心功能
"""

import streamlit as st
import sys
from pathlib import Path

# 添加項目路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

st.set_page_config(
    page_title="DCF 功能測試",
    page_icon="🧪",
    layout="wide"
)

def test_dcf_calculator():
    """測試 DCF 計算器"""
    st.header("🧪 DCF 計算器測試")
    
    try:
        # 嘗試導入 DCF 計算器
        from jojo_trading.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator()
        st.success("✅ DCF 計算器導入成功")
        
        # 顯示狀態
        status = calculator.get_status()
        st.write("**計算器狀態:**")
        for key, value in status.items():
            st.write(f"- {key}: {value}")
        
        # 執行測試計算
        if st.button("執行測試計算"):
            with st.spinner("執行測試中..."):
                test_result = calculator.test_calculation()
                if test_result:
                    st.success("✅ 測試計算成功")
                else:
                    st.error("❌ 測試計算失敗")
        
        return True
        
    except ImportError as e:
        st.error(f"❌ DCF 計算器導入失敗: {e}")
        return False
    except Exception as e:
        st.error(f"❌ 測試過程發生錯誤: {e}")
        return False

def test_basic_dcf():
    """測試基本 DCF 計算"""
    st.header("📊 基本 DCF 計算測試")
    
    # 輸入測試數據
    st.subheader("輸入測試數據")
    
    stock_code = st.text_input("股票代碼", value="2330")
    net_income = st.number_input("淨利 (百萬元)", value=100000.0, step=1000.0)
    shares_outstanding = st.number_input("流通股數 (百萬股)", value=25900.0, step=100.0)
    current_price = st.number_input("目前股價", value=500.0, step=1.0)
    discount_rate = st.slider("折現率", 0.05, 0.15, 0.08, 0.01)
    growth_rate = st.slider("成長率", 0.0, 0.20, 0.08, 0.01)
    
    if st.button("執行基本計算"):
        try:
            # 準備測試數據
            financial_data = {
                'net_income_parent': net_income * 1000000,  # 轉換為元
                'shares_outstanding': shares_outstanding * 1000000,  # 轉換為股
                'current_market_price': current_price
            }
            
            # 嘗試計算
            from jojo_trading.core.dcf_calculator import DCFCalculator
            calculator = DCFCalculator()
            
            result = calculator.calculate_dcf(
                stock_code=stock_code,
                financial_data=financial_data,
                discount_rate=discount_rate,
                growth_rate=growth_rate
            )
            
            # 顯示結果
            st.success("✅ 計算完成")
            st.json(result)
            
        except Exception as e:
            st.error(f"❌ 計算失敗: {e}")
            import traceback
            st.code(traceback.format_exc())

def test_page_components():
    """測試頁面組件"""
    st.header("🔧 頁面組件測試")
    
    # 測試 CSS 載入
    st.subheader("CSS 樣式測試")
    st.markdown("""
    <style>
    .test-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="test-card">
        <h4>測試卡片樣式</h4>
        <p>這是一個測試樣式卡片，確認 CSS 正常載入。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 測試列布局
    st.subheader("列布局測試")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("測試指標 1", "100", "10%")
    
    with col2:
        st.metric("測試指標 2", "200", "-5%")
    
    with col3:
        st.metric("測試指標 3", "300", "15%")
    
    # 測試圖表
    st.subheader("圖表測試")
    try:
        import plotly.graph_objects as go
        import numpy as np
        
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='sin(x)'))
        fig.update_layout(title="測試圖表", height=300)
        
        st.plotly_chart(fig, use_container_width=True)
        st.success("✅ Plotly 圖表正常")
        
    except Exception as e:
        st.error(f"❌ 圖表測試失敗: {e}")

def main():
    st.title("🧪 JoJo Trading DCF 功能測試")
    st.markdown("---")
    
    # 建立分頁
    tab1, tab2, tab3 = st.tabs(["DCF 計算器", "基本計算", "頁面組件"])
    
    with tab1:
        test_dcf_calculator()
    
    with tab2:
        test_basic_dcf()
    
    with tab3:
        test_page_components()
    
    # 整體狀態
    st.markdown("---")
    st.subheader("🔍 系統狀態檢查")
    
    # 檢查關鍵模組
    modules_to_check = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            st.success(f"✅ {module} 已安裝")
        except ImportError:
            st.error(f"❌ {module} 未安裝")

if __name__ == "__main__":
    main()
