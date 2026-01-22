"""
Sector Screening Component  
類股篩選DCF分析組件（增強版：支援投資策略模板）
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

# 嘗試導入投資策略模板
try:
    from jojo_trading.core.investment_strategy_templates import (
        investment_strategy_templates,
        InvestmentStyle,
        ScreeningCriteria
    )
    STRATEGY_TEMPLATES_AVAILABLE = True
except ImportError as e:
    print(f"投資策略模板導入失敗: {e}")
    STRATEGY_TEMPLATES_AVAILABLE = False

class SectorScreeningComponent:
    """類股篩選DCF分析UI組件（增強版）"""
    
    def __init__(self):
        """初始化類股篩選組件"""
        self.default_values = {
            'risk_preference': 8.0,
            'potential_return_threshold': 15.0,
            'growth_rate': 8.0,
            'terminal_growth': 3.0,
            'revenue_cagr_threshold': 10.0,
            'eps_cagr_threshold': 15.0,
            'roe_threshold': 15.0
        }
        
        # 初始化策略模板功能
        if STRATEGY_TEMPLATES_AVAILABLE:
            self.strategy_templates = investment_strategy_templates
            self.strategy_mode_available = True
        else:
            self.strategy_templates = None
            self.strategy_mode_available = False
    
    def render_parameter_panel(self, machine) -> Dict[str, Any]:
        """渲染參數設定面板
        
        Args:
            machine: 狀態機實例
            
        Returns:
            Dict[str, Any]: 篩選參數
        """
        st.subheader("⚙️ 篩選參數設定")
        
        # 產業選擇
        industry_params = self._render_industry_selection(machine)
        
        # DCF參數設定
        dcf_params = self._render_dcf_parameters()
        
        # 成長股篩選設定
        growth_params = self._render_growth_filter_settings()
        
        return {**industry_params, **dcf_params, **growth_params}
    
    def _render_industry_selection(self, machine) -> Dict[str, Any]:
        """渲染產業選擇"""
        st.markdown("**產業類別**")
        industry_names = machine.context.get('industry_names', ['正在載入產業清單...'])
        
        if industry_names and '正在載入' not in industry_names[0]:
            selected_industry = st.selectbox(
                "選擇產業",
                options=industry_names,
                help="選擇要分析的產業類別"
            )
        else:
            selected_industry = st.selectbox(
                "選擇產業", 
                options=['正在載入產業清單...'],
                disabled=True
            )
        
        return {'selected_industry': selected_industry}
    
    
    def _render_dcf_parameters(self) -> Dict[str, Any]:
        """渲染DCF參數設定 (自動化模式)"""
        # 自動化模式：不再顯示複雜參數，直接使用專業預設值
        # Professional Defaults (Hardcoded)
        defaults = {
            'screening_mode': 'screening', # 只顯示低估股票
            'max_stocks': 0, # 不限制
            'risk_preference': 0.08, # 8% Risk Premium + RFR -> ~10-12% Discount Rate (Conservative)
            'potential_return_threshold': 0.15, # 至少 15% 潛在回報才顯示
            'growth_rate': 0.05, # 5% 短期成長 (保守)
            'terminal_growth': 0.02 # 2% 永續成長 (通膨水準)
        }
        
        st.info("ℹ️ 系統已自動套用法人級估值參數 (折現率約 10%, 永續成長 2%)")
        
        return defaults

    def _render_growth_filter_settings(self) -> Dict[str, Any]:
        """渲染成長股篩選設定 (自動化模式)"""
        # 自動化模式：隱藏成長股篩選細節，使用預設過濾
        return {
            'enable_growth_filter': True, # 強制開啟基本面過濾
            'revenue_cagr_enabled': True,
            'revenue_cagr_threshold': 0.0, # 只要正成長
            'eps_cagr_enabled': True, 
            'eps_cagr_threshold': 0.0, # 只要正成長
            'roe_enabled': True,
            'roe_threshold': 10.0, # ROE > 10% (基本門檻)
            'growth_logic': 'AND'
        }
    
    def render_results_panel(self, machine, params: Dict[str, Any]) -> None:
        """渲染結果面板
        
        Args:
            machine: 狀態機實例
            params: 篩選參數
        """
        st.subheader("📊 篩選結果")
        
        # 開始篩選按鈕
        if st.button("🚀 開始類股DCF篩選", type="primary"):
            self._start_screening(machine, params)
        
        # 顯示狀態機執行狀態
        self._display_state_machine_status(machine, params)
    
    def _start_screening(self, machine, params: Dict[str, Any]) -> None:
        """開始篩選流程
        
        Args:
            machine: 狀態機實例  
            params: 篩選參數
        """
        # 更新狀態機參數
        machine.context.update({
            'selected_industry_name': params['selected_industry'],
            'risk_preference': params['risk_preference'],
            'potential_return_threshold': params['potential_return_threshold'],
            'dcf_short_term_growth_rate': params['growth_rate'],
            'dcf_terminal_growth_rate': params['terminal_growth'],
            'enable_growth_filter': params['enable_growth_filter'],
            'screening_mode': params.get('screening_mode', 'screening'),
            'max_stocks': params.get('max_stocks', 30)
        })
        
        if params['enable_growth_filter']:
            machine.context.update({
                'revenue_cagr_enabled': params.get('revenue_cagr_enabled', True),
                'revenue_cagr_threshold': params.get('revenue_cagr_threshold', 10.0),
                'eps_cagr_enabled': params.get('eps_cagr_enabled', True),
                'eps_cagr_threshold': params.get('eps_cagr_threshold', 15.0),
                'roe_enabled': params.get('roe_enabled', True),
                'roe_threshold': params.get('roe_threshold', 15.0),
                'growth_logic_operator': 'AND' if 'AND' in params.get('growth_logic', '') else 'OR'
            })
        
        # 設置為產業處理狀態開始執行
        try:
            from src.jojo_trading.core.state_machine import JoJoState
            machine.current_state = JoJoState.INDUSTRY_PROCESS
        except ImportError:
            # 如果無法導入狀態機，則跳過狀態設置
            pass
        
        # 重新渲染以開始狀態機執行
        st.rerun()
    
    def _display_state_machine_status(self, machine, params: Dict[str, Any]) -> None:
        """顯示狀態機執行狀態
        
        Args:
            machine: 狀態機實例
            params: 篩選參數
        """
        if hasattr(machine, 'current_state'):
            current_state_name = machine.current_state.name if hasattr(machine.current_state, 'name') else str(machine.current_state)
            
            if current_state_name == "CONFIG_LOAD":
                st.info("📋 系統已就緒，等待開始篩選")
                
            elif current_state_name == "UI_INIT":
                st.info("🔧 正在初始化參數...")
                # Only execute once to avoid infinite loop
                if not hasattr(st.session_state, 'ui_init_executed'):
                    machine.execute_state()
                    st.session_state.ui_init_executed = True
                    st.rerun()
                
            elif current_state_name == "IDLE":
                st.success("📋 系統已就緒，等待開始篩選")
                
            elif current_state_name == "INDUSTRY_PROCESS":
                st.info(f"🏭 正在處理產業: {machine.context.get('selected_industry_name')}")
                machine.execute_state()
                st.rerun()
                
            elif current_state_name == "DATA_FETCH":
                self._display_data_fetch_progress(machine)
                
            elif current_state_name == "VALUATION":
                st.warning("🧮 正在計算DCF估值...")
                with st.spinner("正在執行DCF估值計算，請稍候..."):
                    machine.execute_state()
                st.rerun()
                
            elif current_state_name == "FILTERING":
                st.warning("🔍 正在篩選結果...")
                with st.spinner("正在根據設定條件篩選股票..."):
                    machine.execute_state()
                st.rerun()
                
            elif current_state_name == "RESULTS_DISPLAY":
                self._display_screening_results(machine, params)
                
            elif current_state_name == "ERROR":
                self._display_error_status(machine)
                
            else:
                st.info(f"狀態: {current_state_name}")
    
    def _display_data_fetch_progress(self, machine) -> None:
        """顯示數據獲取進度"""
        st.warning("📡 正在獲取財務數據...")
        
        # 建立進度條元件
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 定義回調函數
        def update_progress(current, total, stock_code, stock_name):
            percent = min(int((current / total) * 100), 100)
            progress_bar.progress(percent)
            status_text.text(f"正在處理 ({current}/{total}): {stock_code} {stock_name}")
            
        # 將回調函數注入到 context 中
        machine.context['progress_callback'] = update_progress
        
        with st.spinner("正在從 FinMind 抓取財務數據，請稍候..."):
            # 執行實際的數據獲取
            machine.execute_state()
            
        progress_bar.progress(100)
        status_text.text("✅ 數據獲取完成")
            
        st.rerun()
    
    def _display_screening_results(self, machine, params: Dict[str, Any]) -> None:
        """顯示篩選結果
        
        Args:
            machine: 狀態機實例
            params: 篩選參數
        """
        st.success("✅ 篩選完成！")
        
        # 顯示篩選結果
        filtered_results = machine.context.get('filtered_results', [])
        
        if filtered_results:
            st.markdown(f"**找到 {len(filtered_results)} 支符合條件的股票**")
            
            # 建立結果表格
            df_results = self._create_results_dataframe(filtered_results)
            st.dataframe(df_results, use_container_width=True)
            
            # 匯出功能
            if st.button("💾 匯出Excel報告"):
                st.success("📊 報告匯出功能準備中...")
            
            # 顯示統計資訊
            self._display_screening_statistics(filtered_results, machine, params)
            
        else:
            self._display_no_results_message()
        
        # 重置按鈕
        if st.button("🔄 重新篩選"):
            try:
                from src.jojo_trading.core.state_machine import JoJoState
                machine.current_state = JoJoState.CONFIG_LOAD
                # 清理 session state
                if 'ui_init_executed' in st.session_state:
                    del st.session_state.ui_init_executed
                st.rerun()
            except ImportError:
                # 如果無法導入狀態機，則重新初始化
                if 'sector_jojo_machine' in st.session_state:
                    del st.session_state.sector_jojo_machine
                st.rerun()
    
    def _create_results_dataframe(self, filtered_results: List[Dict]) -> pd.DataFrame:
        """創建結果數據框
        
        Args:
            filtered_results: 篩選結果列表
            
        Returns:
            pd.DataFrame: 結果數據框
        """
        results_data = []
        for result in filtered_results:
            results_data.append({
                '股票代碼': result.get('stock_code', ''),
                '公司名稱': result.get('name', ''),
                '目前股價': f"${result.get('current_market_price', 0):.2f}",
                '內在價值': f"${result.get('intrinsic_value_per_share', 0):.2f}",
                '潛在回報': f"{result.get('potential_return', 0)*100:.1f}%",
                '安全邊際': f"{(result.get('intrinsic_value_per_share', 0) / result.get('current_market_price', 1) - 1)*100:.1f}%",
                'EPS': f"{result.get('source_eps', 0):.2f}",
                '計算方法': result.get('calculation_method', 'basic_dcf')
            })
        
        df_results = pd.DataFrame(results_data)
        
        # 依潛在回報排序
        df_results['潛在回報數值'] = [float(x.rstrip('%')) for x in df_results['潛在回報']]
        df_results = df_results.sort_values('潛在回報數值', ascending=False)
        df_results = df_results.drop('潛在回報數值', axis=1)
        
        return df_results
    
    def _display_screening_statistics(self, filtered_results: List[Dict], machine, params: Dict[str, Any]) -> None:
        """顯示篩選統計
        
        Args:
            filtered_results: 篩選結果
            machine: 狀態機實例
            params: 篩選參數
        """
        with st.expander("📈 篩選統計與排除原因", expanded=True):
            avg_return = sum(r.get('potential_return', 0) for r in filtered_results) / len(filtered_results) * 100 if filtered_results else 0
            avg_intrinsic = sum(r.get('intrinsic_value_per_share', 0) for r in filtered_results) / len(filtered_results) if filtered_results else 0
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("平均潛在回報", f"{avg_return:.1f}%")
            with col_stat2:
                st.metric("平均內在價值", f"${avg_intrinsic:.2f}")
            with col_stat3:
                st.metric("篩選通過率", f"{len(filtered_results)}/{len(machine.context.get('valuation_results', []))}")
            
            # 成長股篩選統計（如果啟用）
            if params.get('enable_growth_filter'):
                growth_passed = sum(1 for r in filtered_results if r.get('growth_analysis', {}).get('is_growth_stock', False))
                st.metric("成長股比例", f"{growth_passed}/{len(filtered_results)}")
            
            # 顯示排除原因統計
            exclusion_summary = machine.context.get('exclusion_summary', {})
            if exclusion_summary and exclusion_summary.get('total_excluded', 0) > 0:
                st.markdown("---")
                st.markdown("#### 🚫 排除原因分析")
                
                # 準備數據
                reasons_map = {
                    'potential_return_low': '潛在回報不足',
                    'intrinsic_value_zero_or_negative': '內在價值異常 (<=0)',
                    'eps_negative_or_low': 'EPS 過低或虧損',
                    'growth_filter_failed': '未通過成長股條件',
                    'missing_data': '數據缺失',
                    'valuation_error': '估值計算錯誤'
                }
                
                exclusion_data = []
                for key, label in reasons_map.items():
                    count = exclusion_summary.get(key, 0)
                    if count > 0:
                        exclusion_data.append({"原因": label, "數量": f"{count} 檔"})
                
                if exclusion_data:
                    st.table(pd.DataFrame(exclusion_data))
                else:
                    st.info("沒有股票被排除")

            # 顯示詳細排除清單
            excluded_results = machine.context.get('excluded_results', [])
            if excluded_results:
                st.markdown("---")
                st.markdown("#### 📋 未納入列表詳細清單")
                df_excluded = pd.DataFrame(excluded_results)
                # Rename columns for better display
                df_excluded = df_excluded.rename(columns={
                    'stock_code': '股票代碼',
                    'name': '名稱',
                    'reason': '排除原因',
                    'category': '類別'
                })
                st.dataframe(
                    df_excluded[['股票代碼', '名稱', '排除原因']], 
                    use_container_width=True,
                    hide_index=True
                )
    
    def _display_no_results_message(self) -> None:
        """顯示無結果訊息"""
        st.warning("😔 未找到符合條件的股票")
        st.markdown("**建議調整篩選條件：**")
        st.markdown("- 降低潛在回報閾值")
        st.markdown("- 調整風險補償參數")
        st.markdown("- 關閉成長股篩選")
    
    def _display_error_status(self, machine) -> None:
        """顯示錯誤狀態
        
        Args:
            machine: 狀態機實例
        """
        st.error("❌ 發生錯誤")
        error_msg = machine.context.get('error_message', '未知錯誤')
        st.error(f"錯誤訊息: {error_msg}")
        
        if st.button("🔄 重試"):
            try:
                from src.jojo_trading.core.state_machine import JoJoState
                machine.current_state = JoJoState.CONFIG_LOAD
                # 清理錯誤狀態
                if 'error_message' in machine.context:
                    del machine.context['error_message']
                st.rerun()
            except ImportError:
                # 如果無法導入狀態機，則重新初始化
                if 'sector_jojo_machine' in st.session_state:
                    del st.session_state.sector_jojo_machine
                st.rerun()
    
    def render_system_status(self, machine) -> None:
        """渲染系統狀態顯示
        
        Args:
            machine: 狀態機實例
        """
        with st.expander("🔧 系統狀態"):
            st.json({
                "當前狀態": str(machine.current_state),
                "已選產業": machine.context.get('selected_industry_name'),
                "風險補償": f"{machine.context.get('risk_preference', 0)*100:.1f}%",
                "篩選閾值": f"{machine.context.get('potential_return_threshold', 0)*100:.1f}%",
                "成長股篩選": machine.context.get('enable_growth_filter', False)
            })
    
    def render(self) -> None:
        """渲染完整的類股篩選DCF分析界面"""
        st.subheader("🎯 類股篩選DCF估值分析")
        st.markdown("選擇產業類別，系統將自動獲取該類股的財報數據並進行DCF批量估值篩選")
        
        # 初始化狀態機（如果未存在）
        if 'sector_jojo_machine' not in st.session_state:
            try:
                from src.jojo_trading.core.state_machine import JoJoStateMachine, JoJoState
                st.session_state.sector_jojo_machine = JoJoStateMachine()
            except ImportError as e:
                st.error(f"無法載入狀態機模組: {e}")
                # 創建一個簡單的替代物件
                class SimpleMachine:
                    def __init__(self):
                        self.context = {}
                        self.current_state = "IDLE"
                    def execute_state(self):
                        pass
                st.session_state.sector_jojo_machine = SimpleMachine()
        
        machine = st.session_state.sector_jojo_machine
        
        # 建立兩欄佈局
        col1, col2 = st.columns([1, 1])
        
        with col1:
            params = self.render_parameter_panel(machine)
        
        with col2:
            self.render_results_panel(machine, params)
        
        self.render_system_status(machine)
