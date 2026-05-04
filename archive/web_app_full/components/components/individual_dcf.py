"""
Individual DCF Analysis Component
個股DCF分析組件
"""

import streamlit as st
from typing import Dict, Any


class IndividualDCFComponent:
    """個股DCF分析UI組件"""
    
    def __init__(self):
        """初始化個股DCF組件"""
        self.default_values = {
            'stock_code': '2330',
            'current_price': 500.0,
            'net_income': 100.0,
            'shares_outstanding': 25.9,
            'discount_rate': 8.0,
            'growth_rate': 8.0,
            'terminal_growth': 3.0,
            'projection_years': 5
        }
    
    def render_input_panel(self) -> Dict[str, Any]:
        """渲染輸入面板
        
        Returns:
            Dict[str, Any]: 用戶輸入的參數
        """
        st.subheader("📈 輸入參數")
        
        # 股票基本資訊
        stock_code = st.text_input(
            "股票代碼", 
            value=self.default_values['stock_code'], 
            help="請輸入台股代碼，例如：2330"
        )
        
        # 財務數據輸入
        st.markdown("**財務數據**")
        current_price = st.number_input(
            "目前股價 (元)", 
            value=self.default_values['current_price'], 
            min_value=0.1, 
            step=1.0
        )
        net_income = st.number_input(
            "年度淨利 (億元)", 
            value=self.default_values['net_income'], 
            min_value=0.1, 
            step=1.0
        )
        shares_outstanding = st.number_input(
            "流通股數 (億股)", 
            value=self.default_values['shares_outstanding'], 
            min_value=0.1, 
            step=0.1
        )
        
        # DCF 參數設定
        st.markdown("**DCF 估值參數**")
        discount_rate = st.slider(
            "折現率 (%)", 
            min_value=5.0, 
            max_value=15.0, 
            value=self.default_values['discount_rate'], 
            step=0.1
        ) / 100
        
        growth_rate = st.slider(
            "短期成長率 (%)", 
            min_value=-10.0, 
            max_value=30.0, 
            value=self.default_values['growth_rate'], 
            step=0.1
        ) / 100
        
        terminal_growth = st.slider(
            "永續成長率 (%)", 
            min_value=0.0, 
            max_value=5.0, 
            value=self.default_values['terminal_growth'], 
            step=0.1
        ) / 100
        
        projection_years = st.selectbox(
            "預測年數", 
            options=[3, 5, 7, 10], 
            index=1
        )
        
        return {
            'stock_code': stock_code,
            'current_price': current_price,
            'net_income': net_income,
            'shares_outstanding': shares_outstanding,
            'discount_rate': discount_rate,
            'growth_rate': growth_rate,
            'terminal_growth': terminal_growth,
            'projection_years': projection_years
        }
    
    def render_results_panel(self, params: Dict[str, Any]) -> None:
        """渲染結果面板
        
        Args:
            params: 計算參數
        """
        st.subheader("💰 估值結果")
        
        # 計算按鈕
        if st.button("🧮 執行 DCF 估值計算", type="primary"):
            try:
                # 導入 DCF 計算器
                from src.jojo_trading.core.dcf_calculator import DCFCalculator
                
                # 建立財務數據字典
                financial_data = {
                    'current_market_price': params['current_price'],
                    'net_income_parent': params['net_income'] * 100000000,  # 轉換為元
                    'shares_outstanding': params['shares_outstanding'] * 100000000,  # 轉換為股
                    'current_price': params['current_price']
                }
                
                # 建立 DCF 計算器並執行計算
                with st.spinner("正在執行 DCF 估值計算..."):
                    dcf_calculator = DCFCalculator()
                    
                    result = dcf_calculator.calculate_dcf(
                        stock_code=params['stock_code'],
                        financial_data=financial_data,
                        discount_rate=params['discount_rate'],
                        growth_rate=params['growth_rate'],
                        terminal_growth_rate=params['terminal_growth'],
                        projection_years=params['projection_years']
                    )
                
                self._display_calculation_results(result, params)
                
            except ImportError as e:
                st.error(f"無法載入 DCF 計算器模組: {e}")
                st.write("請確認系統安裝正確。")
            except Exception as e:
                st.error(f"計算過程發生錯誤: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    def _display_calculation_results(self, result: Dict[str, Any], params: Dict[str, Any]) -> None:
        """顯示計算結果
        
        Args:
            result: DCF計算結果
            params: 計算參數
        """
        # 顯示計算結果
        if 'error' in result:
            st.error(f"計算錯誤: {result['error']}")
        else:
            # 成功計算，顯示結果
            intrinsic_value = result.get('intrinsic_value_per_share', 0)
            potential_return = result.get('potential_return', 0)
            current_price = params['current_price']
            
            # 顯示核心指標
            st.success("✅ DCF 估值計算完成")
            
            # 建立指標顯示
            metric_col1, metric_col2 = st.columns(2)
            
            with metric_col1:
                st.metric("內在價值", f"${intrinsic_value:.2f}", 
                         delta=f"${intrinsic_value - current_price:.2f}")
            
            with metric_col2:
                if potential_return is not None:
                    return_pct = potential_return * 100
                    st.metric("潛在報酬", f"{return_pct:.1f}%",
                             delta="看漲" if return_pct > 0 else "看跌")
            
            # 詳細資訊
            st.markdown("**詳細分析**")
            
            # 投資建議
            self._display_investment_advice(intrinsic_value, current_price)
            
            # 計算詳情
            self._display_calculation_details(result, params)
    
    def _display_investment_advice(self, intrinsic_value: float, current_price: float) -> None:
        """顯示投資建議
        
        Args:
            intrinsic_value: 內在價值
            current_price: 當前股價
        """
        if intrinsic_value > current_price * 1.1:
            st.success("🚀 **投資建議**: 低估，考慮買入")
        elif intrinsic_value > current_price * 0.9:
            st.info("⚖️ **投資建議**: 合理價位")
        else:
            st.warning("⚠️ **投資建議**: 高估，謹慎考慮")
    
    def _display_calculation_details(self, result: Dict[str, Any], params: Dict[str, Any]) -> None:
        """顯示計算詳情
        
        Args:
            result: DCF計算結果
            params: 計算參數
        """
        with st.expander("📊 計算詳情"):
            st.write(f"**使用方法**: {result.get('calculation_method', 'basic_dcf')}")
            st.write(f"**使用折現率**: {result.get('used_discount_rate', params['discount_rate']):.1%}")
            st.write(f"**使用成長率**: {result.get('used_growth_rate', params['growth_rate']):.1%}")
            st.write(f"**永續成長率**: {result.get('used_terminal_growth', params['terminal_growth']):.1%}")
            
            # 敏感度分析
            st.markdown("**敏感度分析**")
            sens_col1, sens_col2 = st.columns(2)
            
            intrinsic_value = result.get('intrinsic_value_per_share', 0)
            discount_rate = params['discount_rate']
            
            with sens_col1:
                st.write("折現率 ±1%:")
                high_discount = intrinsic_value * (discount_rate / (discount_rate + 0.01))
                low_discount = intrinsic_value * (discount_rate / (discount_rate - 0.01))
                st.write(f"  • +1%: ${high_discount:.2f}")
                st.write(f"  • -1%: ${low_discount:.2f}")
            
            with sens_col2:
                st.write("成長率 ±1%:")
                st.write(f"  • +1%: ${intrinsic_value * 1.05:.2f}")
                st.write(f"  • -1%: ${intrinsic_value * 0.95:.2f}")
    
    def render_usage_info(self) -> None:
        """渲染使用說明"""
        st.markdown("---")
        st.markdown("**💡 使用說明**")
        st.info("""
        1. 輸入股票代碼和基本財務數據
        2. 調整 DCF 估值參數
        3. 點擊「執行 DCF 估值計算」按鈕
        4. 查看估值結果和投資建議
        
        **注意**: 此為估值參考工具，投資前請做充分研究。
        """)
        
        # 底部免責聲明
        st.markdown("---")
        st.caption("⚠️ 免責聲明：本工具僅供教育和研究用途，不構成投資建議。投資有風險，請謹慎決策。")
    
    def render(self) -> None:
        """渲染完整的個股DCF分析界面"""
        st.subheader("📈 個股DCF估值分析")
        st.markdown("輸入股票代碼，系統將自動獲取財報數據並計算DCF估值")
        
        # 建立兩欄佈局
        col1, col2 = st.columns([1, 1])
        
        with col1:
            params = self.render_input_panel()
        
        with col2:
            self.render_results_panel(params)
        
        self.render_usage_info()
