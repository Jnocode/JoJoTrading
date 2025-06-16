"""
Enhanced Individual DCF Analysis Component - Fixed Version
修復列布局嵌套問題的個股DCF分析組件
"""

import streamlit as st
from typing import Dict, Any, Optional
import sys
import os
import pandas as pd

# 添加專案路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

try:
    from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
    from jojo_trading.core.dcf_calculator import DCFCalculator
except ImportError as e:
    print(f"模組導入警告: {e}")


class FixedEnhancedIndividualDCFComponent:
    """修復版增強個股DCF分析組件"""
    
    def __init__(self):
        """初始化組件"""
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
        
        # 初始化自動資料抓取器
        try:
            self.auto_fetcher = AutoDataFetcher()
            self.auto_fetch_available = True
        except Exception as e:
            print(f"自動資料抓取功能初始化失敗: {e}")
            self.auto_fetcher = None
            self.auto_fetch_available = False
        
        # 會話狀態初始化
        if 'fetched_data' not in st.session_state:
            st.session_state.fetched_data = {}
        if 'last_fetched_stock' not in st.session_state:
            st.session_state.last_fetched_stock = ''
    
    def render(self) -> None:
        """渲染主要界面"""
        st.markdown("### 📈 增強版個股DCF估值分析")
        st.markdown("整合即時數據抓取的智能DCF估值系統")
        
        # 渲染參數輸入
        params = self._render_dcf_parameters()
        
        # 渲染結果面板
        if params:
            self.render_results_panel(params)
    
    def _render_dcf_parameters(self) -> Optional[Dict[str, Any]]:
        """渲染DCF參數設定"""
        st.markdown("### 📊 輸入參數")
        
        # 股票代碼輸入
        stock_code = st.text_input(
            "股票代碼",
            value=self.default_values['stock_code'],
            placeholder="請輸入股票代碼 (如: 2330)",
            help="請輸入台股代碼，系統將自動獲取財務數據"
        )
        
        # 自動資料抓取選項（使用簡單布局）
        if self.auto_fetch_available:
            auto_fetch = st.checkbox(
                "🚀 自動抓取即時數據", 
                value=True,
                help="啟用後將自動從 FinMind API 獲取最新財務數據"
            )
            
            if stock_code and auto_fetch:
                if st.button("🔄 立即抓取", help="點擊獲取最新數據"):
                    self._fetch_and_update_data(stock_code)
        else:
            auto_fetch = False
            st.warning("⚠️ 自動資料抓取功能不可用，請手動輸入數據")
        
        # 根據是否啟用自動抓取顯示不同界面
        if auto_fetch and stock_code and self.auto_fetch_available:
            return self._render_auto_data_panel(stock_code)
        else:
            safe_stock_code = stock_code if stock_code else self.default_values['stock_code']
            return self._render_manual_input_panel(safe_stock_code)
    
    def _fetch_and_update_data(self, stock_code: str) -> None:
        """抓取並更新股票數據"""
        if not self.auto_fetcher:
            st.error("自動資料抓取器未初始化")
            return
        
        with st.spinner(f"正在抓取 {stock_code} 的最新財務數據..."):
            try:
                dcf_data = self.auto_fetcher.get_dcf_ready_data(stock_code)
                
                if dcf_data['success']:
                    st.session_state.fetched_data = dcf_data
                    st.session_state.last_fetched_stock = stock_code
                    st.success(f"✅ 成功抓取 {dcf_data['company_name']} 的數據！")
                    
                    # 顯示數據摘要（避免嵌套列）
                    st.markdown("**數據摘要:**")
                    st.write(f"📈 股價: ${dcf_data['current_market_price']:.2f}")
                    st.write(f"💰 淨利: {dcf_data['net_income_parent']/1e8:.1f}億")
                    st.write(f"⭐ 品質: {dcf_data['data_quality_score']:.0f}%")
                else:
                    st.error(f"❌ 數據抓取失敗: {dcf_data.get('error', '未知錯誤')}")
                    
            except Exception as e:
                st.error(f"數據抓取過程發生錯誤: {str(e)}")
    
    def _render_auto_data_panel(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """渲染自動數據面板"""
        # 檢查是否有已抓取的數據
        if (stock_code == st.session_state.last_fetched_stock and 
            st.session_state.fetched_data):
            
            data = st.session_state.fetched_data
            
            # 顯示已抓取的數據
            st.success(f"🎯 已載入 {data['company_name']} 的最新數據")
            
            # 顯示數據詳情
            with st.expander("📊 數據詳情"):
                st.write("**數據來源:**")
                for field, source in data['data_sources'].items():
                    if field in ['current_market_price', 'net_income_parent', 'shares_outstanding']:
                        st.write(f"• {field}: {source}")
                
                st.write("**數據品質:**")
                st.write(f"• 品質評分: {data['data_quality_score']:.0f}%")
                st.write(f"• 更新時間: {data['last_updated'][:19]}")
            
            # 財務數據輸入
            st.markdown("**財務數據 (可調整)**")
            
            current_price = st.number_input(
                "目前股價 (元)", 
                value=float(data['current_market_price']), 
                min_value=0.1, 
                step=1.0,
                help="來源: FinMind API"
            )
            
            net_income_billion = data['net_income_parent'] / 1e8
            net_income = st.number_input(
                "年度淨利 (億元)", 
                value=float(net_income_billion), 
                step=0.1,
                help="來源: FinMind 財務報表"
            )
            
            shares_outstanding_billion = data['shares_outstanding'] / 1e8
            shares_outstanding = st.number_input(
                "流通股數 (億股)", 
                value=float(shares_outstanding_billion), 
                min_value=0.1, 
                step=0.1,
                help="來源: FinMind 基本資料"
            )
            
            # DCF估值參數
            st.markdown("**DCF 估值參數**")
            
            discount_rate = st.slider(
                "折現率 (%)", 
                min_value=5.0, 
                max_value=15.0, 
                value=8.0, 
                step=0.5,
                help="反映投資風險的折現率"
            )
            
            growth_rate = st.slider(
                "短期成長率 (%)", 
                min_value=-10.0, 
                max_value=30.0, 
                value=8.0, 
                step=1.0,
                help="未來5年平均成長率"
            )
            
            terminal_growth = st.slider(
                "永續成長率 (%)", 
                min_value=0.0, 
                max_value=5.0, 
                value=2.5, 
                step=0.5,
                help="長期永續成長率"
            )
            
            projection_years = st.selectbox(
                "預測年數", 
                options=[3, 5, 7, 10], 
                index=1,
                help="DCF預測的年數"
            )
            
            return {
                'stock_code': stock_code,
                'current_price': current_price,
                'net_income': net_income * 1e8,  # 轉換回元
                'shares_outstanding': shares_outstanding * 1e8,  # 轉換回股
                'discount_rate': discount_rate / 100,
                'growth_rate': growth_rate / 100,
                'terminal_growth': terminal_growth / 100,
                'projection_years': projection_years,
                'is_auto_data': True
            }
        else:
            st.info(f"請點擊「🔄 立即抓取」來獲取 {stock_code} 的最新數據")
            return None
    
    def _render_manual_input_panel(self, stock_code: str) -> Dict[str, Any]:
        """渲染手動輸入面板"""
        st.markdown("**手動輸入模式**")
        
        current_price = st.number_input(
            "目前股價 (元)", 
            value=self.default_values['current_price'], 
            min_value=0.1, 
            step=1.0
        )
        
        net_income = st.number_input(
            "年度淨利 (億元)", 
            value=self.default_values['net_income'], 
            step=0.1
        )
        
        shares_outstanding = st.number_input(
            "流通股數 (億股)", 
            value=self.default_values['shares_outstanding'], 
            min_value=0.1, 
            step=0.1
        )
        
        discount_rate = st.slider(
            "折現率 (%)", 
            min_value=5.0, 
            max_value=15.0, 
            value=self.default_values['discount_rate'], 
            step=0.5
        )
        
        growth_rate = st.slider(
            "短期成長率 (%)", 
            min_value=-10.0, 
            max_value=30.0, 
            value=self.default_values['growth_rate'], 
            step=1.0
        )
        
        terminal_growth = st.slider(
            "永續成長率 (%)", 
            min_value=0.0, 
            max_value=5.0, 
            value=self.default_values['terminal_growth'], 
            step=0.5
        )
        
        projection_years = st.selectbox(
            "預測年數", 
            options=[3, 5, 7, 10], 
            index=1
        )
        
        return {
            'stock_code': stock_code,
            'current_price': current_price,
            'net_income': net_income * 1e8,
            'shares_outstanding': shares_outstanding * 1e8,
            'discount_rate': discount_rate / 100,
            'growth_rate': growth_rate / 100,
            'terminal_growth': terminal_growth / 100,
            'projection_years': projection_years,
            'is_auto_data': False
        }
    
    def render_results_panel(self, params: Dict[str, Any]) -> None:
        """渲染結果面板"""
        if not params:
            return
        
        st.markdown("### 💰 DCF 估值結果")
        
        if st.button("🚀 執行 DCF 計算", type="primary"):
            self._execute_dcf_calculation(params)
    
    def _execute_dcf_calculation(self, params: Dict[str, Any]) -> None:
        """執行DCF計算"""
        try:
            financial_data = {
                'net_income_parent': params['net_income'],
                'shares_outstanding': params['shares_outstanding'],
                'current_market_price': params['current_price']
            }
            
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
            
            # 顯示結果
            if 'error' not in result:
                st.success("✅ DCF 估值計算完成！")
                
                intrinsic_value = result.get('intrinsic_value_per_share', 0)
                current_price = params['current_price']
                
                # 顯示主要結果
                st.markdown(f"### 📊 估值結果")
                st.markdown(f"**內在價值:** NT$ {intrinsic_value:,.2f}")
                st.markdown(f"**目前價格:** NT$ {current_price:,.2f}")
                
                if intrinsic_value > 0:
                    upside_pct = (intrinsic_value / current_price - 1) * 100
                    st.markdown(f"**潛在報酬:** {upside_pct:+.1f}%")
                    
                    if upside_pct > 15:
                        st.success("🟢 股票被低估，具有投資潛力")
                    elif upside_pct > -15:
                        st.info("🟡 股票估值合理")
                    else:
                        st.warning("🔴 股票可能被高估")
                
                # 顯示計算詳情
                with st.expander("📋 計算詳情"):
                    st.json(result)
            else:
                st.error(f"計算錯誤: {result['error']}")
                
        except Exception as e:
            st.error(f"計算過程發生錯誤: {str(e)}")
            with st.expander("錯誤詳情"):
                import traceback
                st.code(traceback.format_exc())
