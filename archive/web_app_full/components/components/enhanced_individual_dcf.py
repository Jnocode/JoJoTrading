"""
Enhanced Individual DCF Analysis Component
增強版個股DCF分析組件

整合自動資料抓取功能，提供真實即時的財務數據DCF估值分析
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
    from jojo_trading.core.multiple_valuation_calculator import MultipleValuationCalculator, InvestmentAdviser
except ImportError as e:
    print(f"模組導入警告: {e}")


class EnhancedIndividualDCFComponent:
    """增強版個股DCF分析UI組件"""
    
    def __init__(self):
        """初始化增強版個股DCF組件"""
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
        
        # 初始化多重估值計算器
        try:
            self.multiple_valuator = MultipleValuationCalculator()
            self.investment_adviser = InvestmentAdviser()
            self.multiple_valuation_available = True
        except Exception as e:
            st.warning(f"多重估值功能初始化失敗: {e}")
            self.multiple_valuator = None
            self.investment_adviser = None
            self.multiple_valuation_available = False
        
        # 會話狀態初始化
        if 'fetched_data' not in st.session_state:
            st.session_state.fetched_data = {}
        if 'last_fetched_stock' not in st.session_state:
            st.session_state.last_fetched_stock = ''
    
    def render_input_panel(self) -> Dict[str, Any]:
        """渲染輸入面板並返回參數"""
        
        # 股票代碼輸入
        stock_code = st.text_input(
            "股票代碼", 
            value=self.default_values['stock_code'],
            placeholder="請輸入股票代碼 (如: 2330)",
            help="請輸入台股代碼，系統將自動獲取財務數據"
        )
        
        # 自動資料抓取選項
        if self.auto_fetch_available:
            col1, col2 = st.columns([2, 1])
            with col1:
                auto_fetch = st.checkbox(
                    "🚀 自動抓取即時數據", 
                    value=True,
                    help="啟用後將自動從 FinMind API 獲取最新財務數據"
                )
            with col2:
                if stock_code and auto_fetch:
                    if st.button("🔄 立即抓取", help="點擊獲取最新數據"):
                        self._fetch_and_update_data(stock_code)
        else:
            auto_fetch = False
            st.warning("⚠️ 自動資料抓取功能不可用，請手動輸入數據")
          # 根據是否啟用自動抓取顯示不同界面
        if auto_fetch and stock_code and self.auto_fetch_available:
            return self._render_auto_data_panel(stock_code)
        else:            # 確保 stock_code 不為 None，如果為 None 則使用預設值
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
                    
                    # 顯示數據摘要（不使用嵌套列）
                    st.markdown("**數據摘要:**")
                    metric_cols = st.columns(3)
                    with metric_cols[0]:
                        st.metric("股價", f"${dcf_data['current_market_price']:.2f}")
                    with metric_cols[1]:
                        st.metric("淨利", f"{dcf_data['net_income_parent']/1e8:.1f}億")
                    with metric_cols[2]:
                        st.metric("品質", f"{dcf_data['data_quality_score']:.0f}%")
                else:
                    st.error(f"❌ 數據抓取失敗: {dcf_data.get('error', '未知錯誤')}")
                    
            except Exception as e:
                st.error(f"數據抓取過程發生錯誤: {str(e)}")
    
    def auto_fetch_data(self, stock_code: str) -> Dict[str, Any]:
        """
        提供給外部調用的自動抓取數據方法
        主要用於測試和API調用
        """
        if not self.auto_fetcher:
            return {
                'success': False,
                'error': '自動資料抓取器未初始化'
            }
        
        try:
            return self.auto_fetcher.get_dcf_ready_data(stock_code)
        except Exception as e:
            return {
                'success': False,
                'error': f'數據抓取錯誤: {str(e)}'
            }
    
    def _render_auto_data_panel(self, stock_code: str) -> Dict[str, Any]:
        """渲染自動數據面板"""
        
        # 檢查是否有已抓取的數據
        if (st.session_state.last_fetched_stock == stock_code and 
            st.session_state.fetched_data and 
            st.session_state.fetched_data.get('success')):
            
            data = st.session_state.fetched_data
            
            # 顯示已抓取的數據
            st.success(f"🎯 已載入 {data['company_name']} 的最新數據")
            
            # 顯示數據來源和時間
            with st.expander("📊 數據詳情"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**數據來源:**")
                    for field, source in data['data_sources'].items():
                        if field in ['current_market_price', 'net_income_parent', 'shares_outstanding']:
                            st.write(f"• {field}: {source}")
                
                with col2:
                    st.write("**數據品質:**")
                    st.write(f"• 品質評分: {data['data_quality_score']:.0f}%")
                    st.write(f"• 更新時間: {data['last_updated'][:19]}")
            
            # 關鍵財務數據（可調整）
            st.markdown("**財務數據 (可調整)**")
            
            col1, col2 = st.columns(2)
            with col1:
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
            
            with col2:
                shares_outstanding_billion = data['shares_outstanding'] / 1e8
                shares_outstanding = st.number_input(
                    "流通股數 (億股)", 
                    value=float(shares_outstanding_billion), 
                    min_value=0.1, 
                    step=0.1,
                    help="來源: 公司基本資料"
                )
            
            # DCF 參數設定
            dcf_params = self._render_dcf_parameters()
            
            return {
                'stock_code': stock_code,
                'current_price': current_price,
                'net_income': net_income,
                'shares_outstanding': shares_outstanding,
                'is_auto_data': True,
                'fetched_data': data,
                **dcf_params
            }
        
        else:
            # 尚未抓取數據
            st.info(f"💡 請點擊「立即抓取」按鈕獲取 {stock_code} 的最新財務數據")
            
            # 提供預設值讓用戶可以繼續
            st.markdown("**或使用預設值繼續**")
            return self._render_manual_input_panel(stock_code)
    
    def _render_manual_input_panel(self, stock_code: str) -> Dict[str, Any]:
        """渲染手動輸入面板"""
        
        # 財務數據手動輸入
        st.markdown("**財務數據 (手動輸入)**")
        
        col1, col2 = st.columns(2)
        with col1:
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
        
        with col2:
            shares_outstanding = st.number_input(
                "流通股數 (億股)", 
                value=self.default_values['shares_outstanding'], 
                min_value=0.1, 
                step=0.1
            )
        
        # DCF 參數設定
        dcf_params = self._render_dcf_parameters()
        
        return {
            'stock_code': stock_code,
            'current_price': current_price,
            'net_income': net_income,
            'shares_outstanding': shares_outstanding,
            'is_auto_data': False,
            **dcf_params
        }
    
    def _render_dcf_parameters(self) -> Dict[str, Any]:
        """渲染DCF參數設定"""
        
        st.markdown("**DCF 估值參數**")
        
        col1, col2 = st.columns(2)
        with col1:
            discount_rate = st.slider(
                "折現率 (%)", 
                min_value=5.0, 
                max_value=15.0, 
                value=self.default_values['discount_rate'], 
                step=0.1,
                help="台股建議 7-9%"
            ) / 100
            
            growth_rate = st.slider(
                "短期成長率 (%)", 
                min_value=-10.0, 
                max_value=30.0, 
                value=self.default_values['growth_rate'], 
                step=0.1,
                help="台股科技股建議 8-12%"
            ) / 100
        
        with col2:
            terminal_growth = st.slider(
                "永續成長率 (%)", 
                min_value=0.0, 
                max_value=5.0, 
                value=self.default_values['terminal_growth'], 
                step=0.1,
                help="通常設定為 2-4%"
            ) / 100
            
            projection_years = st.selectbox(
                "預測年數", 
                options=[3, 5, 7, 10], 
                index=1,
                help="建議使用 5 年"
            )
        
        return {
            'discount_rate': discount_rate,
            'growth_rate': growth_rate,
            'terminal_growth': terminal_growth,
            'projection_years': projection_years
        }
    
    def render_results_panel(self, params: Dict[str, Any]) -> None:
        """渲染結果面板"""
        st.subheader("💰 DCF 估值結果")
        
        # 計算按鈕
        if st.button("🧮 執行 DCF 估值計算", type="primary"):
            self._execute_dcf_calculation(params)
    
    def _execute_dcf_calculation(self, params: Dict[str, Any]) -> None:
        """執行DCF計算"""
        try:
            # 準備財務數據
            financial_data = self._prepare_financial_data(params)
            
            # 執行計算
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
            self._display_calculation_results(result, params)
            
        except ImportError as e:
            st.error(f"無法載入 DCF 計算器模組: {e}")
            st.write("請確認系統安裝正確。")
        except Exception as e:
            st.error(f"計算過程發生錯誤: {str(e)}")
            with st.expander("錯誤詳情"):
                import traceback
                st.code(traceback.format_exc())
    
    def _prepare_financial_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """準備財務數據"""
        financial_data = {
            'current_market_price': params['current_price'],
            'net_income_parent': params['net_income'] * 1e8,  # 轉換為元
            'shares_outstanding': params['shares_outstanding'] * 1e8,  # 轉換為股
            'current_price': params['current_price']
        }
        
        # 如果是自動抓取的數據，添加額外的財務項目
        if params.get('is_auto_data') and params.get('fetched_data'):
            data = params['fetched_data']
            
            # 添加DCF計算所需的額外欄位
            additional_fields = ['capex', 'depreciation', 'amortization', 'total_revenue']
            for field in additional_fields:
                if field in data:
                    financial_data[field] = data[field]
            
            # 添加營運資金項目
            working_capital_fields = ['ar_t0', 'inv_t0', 'ap_t0', 'ar_t1', 'inv_t1', 'ap_t1']
            for field in working_capital_fields:
                if field in data:
                    financial_data[field] = data[field]
        
        return financial_data
    
    def _display_calculation_results(self, result: Dict[str, Any], params: Dict[str, Any]) -> None:
        """顯示計算結果（增強版：包含多重估值）"""
        
        if 'error' in result:
            st.error(f"計算錯誤: {result['error']}")
            return
          # 準備多重估值計算
        if (self.multiple_valuation_available and 
            self.multiple_valuator is not None and 
            self.investment_adviser is not None and
            params.get('is_auto_data')):
            financial_data = self._prepare_financial_data(params)
            multiple_valuations = self.multiple_valuator.calculate_all_valuations(financial_data)
            investment_advice = self.investment_adviser.generate_recommendation(multiple_valuations)
        else:
            multiple_valuations = None
            investment_advice = None
        
        # 顯示主要估值結果
        st.success("✅ DCF 估值計算完成")
        
        # 如果有多重估值，優先顯示共識估值
        if (multiple_valuations and 
            multiple_valuations.get('consensus', {}).get('value', 0) > 0 and
            investment_advice is not None):
            self._display_multiple_valuation_results(multiple_valuations, params, investment_advice)
        else:
            self._display_single_dcf_results(result, params)
    
    def _display_multiple_valuation_results(
        self, 
        valuations: Dict[str, Any], 
        params: Dict[str, Any],
        advice: Dict[str, Any]
    ) -> None:
        """顯示多重估值結果"""
        
        consensus = valuations['consensus']
        current_price = params['current_price']
        consensus_value = consensus['value']
        upside = consensus['upside']
        confidence = consensus['confidence']
        
        # 核心指標顯示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "共識估值", 
                f"${consensus_value:.2f}", 
                delta=f"${consensus_value - current_price:.2f}"
            )
        
        with col2:
            return_pct = upside * 100
            delta_color = "normal" if upside > 0 else "inverse"
            st.metric(
                "潛在報酬", 
                f"{return_pct:.1f}%",
                delta="看漲" if upside > 0 else "看跌",
                delta_color=delta_color
            )
        
        with col3:
            confidence_pct = confidence * 100
            st.metric(
                "信心度",
                f"{confidence_pct:.0f}%",
                delta="高信心" if confidence > 0.7 else "低信心"
            )
        
        with col4:
            if advice:
                recommendation_map = {
                    'strong_buy': ('強烈買入', '🚀'),
                    'buy': ('買入', '📈'),
                    'hold': ('持有', '⏸️'),
                    'sell': ('賣出', '📉'),
                    'strong_sell': ('強烈賣出', '⚠️')
                }
                action, emoji = recommendation_map.get(advice['recommendation'], ('持有', '⏸️'))
                st.metric(
                    "投資建議",
                    f"{emoji} {action}",
                    delta=advice.get('reason', '')[:20] + '...' if len(advice.get('reason', '')) > 20 else advice.get('reason', '')
                )
        
        # 投資建議詳情
        if advice:
            self._display_detailed_investment_advice(advice, consensus_value, current_price)
        
        # 多重估值明細
        with st.expander("📊 多重估值明細"):
            self._display_valuation_breakdown(valuations, current_price)
    
    def _display_detailed_investment_advice(
        self, 
        advice: Dict[str, Any], 
        consensus_value: float, 
        current_price: float
    ) -> None:
        """顯示詳細投資建議"""
        
        recommendation = advice.get('recommendation', 'hold')
        action = advice.get('action', '持有')
        reason = advice.get('reason', '')
        
        # 建議框格
        if recommendation in ['strong_buy', 'buy']:
            st.success(f"💡 **投資建議**: {action}")
        elif recommendation == 'hold':
            st.info(f"💡 **投資建議**: {action}")
        else:
            st.warning(f"💡 **投資建議**: {action}")
        
        st.write(f"**建議理由**: {reason}")
        
        # 價位建議
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_price = advice.get('target_price', 0)
            if target_price > 0:
                st.info(f"🎯 **目標價**: ${target_price:.2f}")
        
        with col2:
            if recommendation in ['strong_buy', 'buy']:
                entry_price = consensus_value * 0.95  # 建議在估值95%以下進場
                st.success(f"📈 **建議買進**: ${entry_price:.2f}以下")
        
        with col3:
            stop_loss = advice.get('stop_loss', 0)
            if stop_loss > 0:
                st.error(f"🛑 **停損價**: ${stop_loss:.2f}")
    
    def _display_valuation_breakdown(self, valuations: Dict[str, Any], current_price: float) -> None:
        """顯示估值方法明細"""
        
        method_names = {
            'dcf': 'DCF估值',
            'pe': 'PE估值',
            'pb': 'PB估值',
            'ev_ebitda': 'EV/EBITDA',
            'dividend_yield': '股利估值'
        }
        
        # 創建估值比較表格
        data = []
        for method, result in valuations.items():
            if method == 'consensus':
                continue
                
            if 'error' not in result and result.get('value', 0) > 0:
                data.append({
                    '估值方法': method_names.get(method, method),
                    '估值': f"${result['value']:.2f}",
                    '潛在報酬': f"{result['upside']*100:.1f}%",
                    '權重': f"{result['method_weight']*100:.0f}%"
                })
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # 估值散佈圖（簡單版）
            values = [float(row['估值'].replace('$', '')) for row in data]
            methods = [row['估值方法'] for row in data]
            
            fig_data = {
                '估值方法': methods,
                '估值': values,
                '當前價格': [current_price] * len(methods)
            }
            
            st.bar_chart(pd.DataFrame({'估值': values, '當前價格': [current_price] * len(values)}, index=methods))
    
    def _display_single_dcf_results(self, result: Dict[str, Any], params: Dict[str, Any]) -> None:
        """顯示單一DCF結果（原有功能保持不變）"""
        
        if 'error' in result:
            st.error(f"計算錯誤: {result['error']}")
            return
        
        intrinsic_value = result.get('intrinsic_value_per_share', 0)
        potential_return = result.get('potential_return', 0)
        current_price = params['current_price']
        
        # 核心指標顯示
        st.success("✅ DCF 估值計算完成")
        
        # 建立指標顯示
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "內在價值", 
                f"${intrinsic_value:.2f}", 
                delta=f"${intrinsic_value - current_price:.2f}"
            )
        
        with col2:
            if potential_return is not None:
                return_pct = potential_return * 100
                delta_color = "normal" if return_pct > 0 else "inverse"
                st.metric(
                    "潛在報酬", 
                    f"{return_pct:.1f}%",
                    delta="看漲" if return_pct > 0 else "看跌",
                    delta_color=delta_color
                )
        
        with col3:
            safety_margin = (intrinsic_value / current_price - 1) * 100 if current_price > 0 else 0
            st.metric(
                "安全邊際",
                f"{safety_margin:.1f}%",
                delta="充足" if safety_margin > 10 else "不足"
            )
        
        # 投資建議
        self._display_investment_advice(intrinsic_value, current_price)
        
        # 顯示估值基礎與品質註記
        if 'valuation_basis' in result:
            note_type = "success" if result['valuation_basis'] == 'FCF' else "warning"
            if note_type == "success":
                st.success(f"ℹ️ **估值基礎**: {result['valuation_basis']} - {result.get('quality_note', '')}")
            else:
                st.warning(f"ℹ️ **估值基礎**: {result['valuation_basis']} - {result.get('quality_note', '')}")

        # 情境分析
        if 'scenarios' in result:
            self._display_scenario_analysis(result['scenarios'])

        # 詳細分析
        with st.expander("📊 詳細分析"):
            self._display_detailed_analysis(result, params)
        
        # 如果使用自動數據，顯示數據品質評估
        if params.get('is_auto_data') and params.get('fetched_data'):
            self._display_data_quality_assessment(params['fetched_data'])
    
    def _display_scenario_analysis(self, scenarios: Dict[str, Any]) -> None:
        """顯示情境分析結果"""
        st.markdown("### 🎯 情境分析 (Scenario Analysis)")
        st.markdown("透過調整成長率與折現率，模擬不同市場情境下的估值範圍。")
        
        cols = st.columns(3)
        
        # Bear Case
        with cols[0]:
            bear = scenarios.get('bear', {})
            st.error(f"🐻 {bear.get('label', '悲觀')}")
            st.metric("估值", f"${bear.get('value', 0):.2f}", delta=f"{bear.get('upside', 0)*100:.1f}%")
            st.caption(f"成長: {bear.get('growth_used', 0):.1%} | 折現: {bear.get('discount_used', 0):.1%}")

        # Base Case
        with cols[1]:
            base = scenarios.get('base', {})
            st.info(f"⚖️ {base.get('label', '基本')}")
            st.metric("估值", f"${base.get('value', 0):.2f}", delta=f"{base.get('upside', 0)*100:.1f}%")
            st.caption(f"成長: {base.get('growth_used', 0):.1%} | 折現: {base.get('discount_used', 0):.1%}")

        # Bull Case
        with cols[2]:
            bull = scenarios.get('bull', {})
            st.success(f"🐂 {bull.get('label', '樂觀')}")
            st.metric("估值", f"${bull.get('value', 0):.2f}", delta=f"{bull.get('upside', 0)*100:.1f}%")
            st.caption(f"成長: {bull.get('growth_used', 0):.1%} | 折現: {bull.get('discount_used', 0):.1%}")
        
        st.divider()

    def _display_investment_advice(self, intrinsic_value: float, current_price: float) -> None:
        """顯示投資建議"""
        
        if intrinsic_value <= 0:
            st.warning("⚠️ **投資建議**: 估值為負，建議檢查財務數據")
            return
        
        upside_ratio = intrinsic_value / current_price
        
        if upside_ratio >= 1.2:
            st.success("🚀 **投資建議**: 顯著低估，強烈考慮買入")
        elif upside_ratio >= 1.1:
            st.success("📈 **投資建議**: 輕微低估，可考慮買入")
        elif upside_ratio >= 0.9:
            st.info("⚖️ **投資建議**: 合理價位，持平觀望")
        elif upside_ratio >= 0.8:
            st.warning("📉 **投資建議**: 輕微高估，謹慎考慮")
        else:
            st.error("⛔ **投資建議**: 嚴重高估，不建議買入")
    
    def _display_detailed_analysis(self, result: Dict[str, Any], params: Dict[str, Any]) -> None:
        """顯示詳細分析"""
        
        # 計算方法和參數
        st.markdown("**計算參數**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"• 計算方法: {result.get('calculation_method', 'basic_dcf')}")
            st.write(f"• 使用折現率: {result.get('used_discount_rate', params['discount_rate']):.1%}")
        
        with col2:
            st.write(f"• 短期成長率: {result.get('used_growth_rate', params['growth_rate']):.1%}")
            st.write(f"• 永續成長率: {result.get('used_terminal_growth', params['terminal_growth']):.1%}")
        
        # 敏感度分析
        st.markdown("**敏感度分析**")
        self._display_sensitivity_analysis(result, params)
    
    def _display_sensitivity_analysis(self, result: Dict[str, Any], params: Dict[str, Any]) -> None:
        """顯示敏感度分析"""
        
        intrinsic_value = result.get('intrinsic_value_per_share', 0)
        discount_rate = params['discount_rate']
        growth_rate = params['growth_rate']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**折現率影響:**")
            high_discount = intrinsic_value * (discount_rate / max(discount_rate + 0.01, 0.01))
            low_discount = intrinsic_value * (discount_rate / max(discount_rate - 0.01, 0.01))
            st.write(f"• +1%: ${high_discount:.2f}")
            st.write(f"• -1%: ${low_discount:.2f}")
        
        with col2:
            st.write("**成長率影響:**")
            # 簡化的成長率敏感度分析
            high_growth = intrinsic_value * 1.1  # 假設+1%成長率影響約10%估值
            low_growth = intrinsic_value * 0.9   # 假設-1%成長率影響約-10%估值
            st.write(f"• +1%: ${high_growth:.2f}")
            st.write(f"• -1%: ${low_growth:.2f}")
    
    def _display_data_quality_assessment(self, data: Dict[str, Any]) -> None:
        """顯示數據品質評估"""
        
        with st.expander("🔍 數據品質評估"):
            quality_score = data.get('data_quality_score', 0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("品質評分", f"{quality_score:.0f}%")
                
                if quality_score >= 80:
                    st.success("數據品質優秀")
                elif quality_score >= 60:
                    st.info("數據品質良好")
                else:
                    st.warning("數據品質需要改善")
            
            with col2:
                st.write("**數據來源:**")
                sources = data.get('data_sources', {})
                for field, source in sources.items():
                    if field in ['current_market_price', 'net_income_parent', 'capex']:
                        st.write(f"• {field}: {source}")
    
    def render_usage_info(self) -> None:
        """渲染使用說明"""
        
        with st.expander("💡 使用說明"):
            st.markdown("""
            **🚀 自動模式 (推薦):**
            1. 輸入股票代碼
            2. 勾選「自動抓取即時數據」
            3. 點擊「立即抓取」獲取最新財務數據
            4. 調整 DCF 估值參數
            5. 執行估值計算
            
            **✋ 手動模式:**
            1. 輸入股票代碼和財務數據
            2. 調整 DCF 估值參數
            3. 執行估值計算
            
            **📊 數據來源:**
            - 股價: FinMind API (即時)
            - 財務報表: FinMind API (最新季報)
            - 公司基本資料: 證交所開放資料
            """)
        
        st.caption("⚠️ 免責聲明：本工具僅供教育和研究用途，不構成投資建議。投資有風險，請謹慎決策。")
    
    def render(self) -> None:
        """渲染完整的增強版個股DCF分析界面"""
        
        st.title("📈 增強版個股DCF估值分析")
        st.markdown("整合即時數據抓取的智能DCF估值系統")
        
        # 建立兩欄佈局
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📊 輸入參數")
            params = self.render_input_panel()
        
        with col2:
            self.render_results_panel(params)
        
        # 使用說明
        self.render_usage_info()


def main():
    """主函數 - 用於獨立運行此組件"""
    st.set_page_config(
        page_title="增強版個股DCF分析",
        page_icon="📈",
        layout="wide"
    )
    
    component = EnhancedIndividualDCFComponent()
    component.render()


if __name__ == "__main__":
    main()
