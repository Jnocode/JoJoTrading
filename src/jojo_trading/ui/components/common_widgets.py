"""
Common Widgets Module
通用 UI 組件模組
"""

import streamlit as st
from typing import Dict, Any, List, Optional


class CommonWidgets:
    """通用UI組件類"""
    
    @staticmethod
    def render_page_header(title: str, description: str) -> None:
        """渲染頁面標題
        
        Args:
            title: 頁面標題
            description: 頁面描述
        """
        st.header(title)
        st.markdown(description)
    
    @staticmethod
    def render_metric_cards(metrics: List[Dict[str, Any]]) -> None:
        """渲染指標卡片
        
        Args:
            metrics: 指標列表，每個指標包含 label, value, delta 等字段
        """
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                st.metric(
                    label=metric.get('label', ''),
                    value=metric.get('value', ''),
                    delta=metric.get('delta', None)
                )
    
    @staticmethod
    def render_progress_indicator(current_step: int, total_steps: int, step_names: List[str]) -> None:
        """渲染進度指示器
        
        Args:
            current_step: 當前步驟
            total_steps: 總步驟數
            step_names: 步驟名稱列表
        """
        progress = current_step / total_steps
        st.progress(progress)
        
        # 顯示步驟名稱
        cols = st.columns(total_steps)
        for i, step_name in enumerate(step_names):
            with cols[i]:
                if i < current_step:
                    st.success(f"✅ {step_name}")
                elif i == current_step:
                    st.info(f"🔄 {step_name}")
                else:
                    st.write(f"⏳ {step_name}")
    
    @staticmethod
    def render_info_panel(title: str, content: str, panel_type: str = "info") -> None:
        """渲染資訊面板
        
        Args:
            title: 面板標題
            content: 面板內容
            panel_type: 面板類型 (info, success, warning, error)
        """
        with st.expander(title):
            if panel_type == "info":
                st.info(content)
            elif panel_type == "success":
                st.success(content)
            elif panel_type == "warning":
                st.warning(content)
            elif panel_type == "error":
                st.error(content)
            else:
                st.write(content)
    
    @staticmethod
    def render_parameter_slider(
        label: str, 
        min_value: float, 
        max_value: float, 
        default_value: float,
        step: float = 0.1,
        format_str: str = "%.1f",
        help_text: Optional[str] = None
    ) -> float:
        """渲染參數滑桿
        
        Args:
            label: 滑桿標籤
            min_value: 最小值
            max_value: 最大值
            default_value: 預設值
            step: 步進值
            format_str: 格式化字串
            help_text: 說明文字
            
        Returns:
            float: 選擇的值
        """
        return st.slider(
            label=label,
            min_value=min_value,
            max_value=max_value,
            value=default_value,
            step=step,
            format=format_str,
            help=help_text
        )
    
    @staticmethod
    def render_financial_input_group(defaults: Dict[str, float]) -> Dict[str, float]:
        """渲染財務數據輸入組
        
        Args:
            defaults: 預設值字典
            
        Returns:
            Dict[str, float]: 輸入的財務數據
        """
        st.markdown("**財務數據**")
        
        current_price = st.number_input(
            "目前股價 (元)", 
            value=defaults.get('current_price', 500.0), 
            min_value=0.1, 
            step=1.0
        )
        
        net_income = st.number_input(
            "年度淨利 (億元)", 
            value=defaults.get('net_income', 100.0), 
            min_value=0.1, 
            step=1.0
        )
        
        shares_outstanding = st.number_input(
            "流通股數 (億股)", 
            value=defaults.get('shares_outstanding', 25.9), 
            min_value=0.1, 
            step=0.1
        )
        
        return {
            'current_price': current_price,
            'net_income': net_income,
            'shares_outstanding': shares_outstanding
        }
    
    @staticmethod
    def render_dcf_parameter_group(defaults: Dict[str, float]) -> Dict[str, float]:
        """渲染DCF參數輸入組
        
        Args:
            defaults: 預設值字典
            
        Returns:
            Dict[str, float]: DCF參數
        """
        st.markdown("**DCF 估值參數**")
        
        discount_rate = st.slider(
            "折現率 (%)", 
            min_value=5.0, 
            max_value=15.0, 
            value=defaults.get('discount_rate', 8.0), 
            step=0.1
        ) / 100
        
        growth_rate = st.slider(
            "短期成長率 (%)", 
            min_value=-10.0, 
            max_value=30.0, 
            value=defaults.get('growth_rate', 8.0), 
            step=0.1
        ) / 100
        
        terminal_growth = st.slider(
            "永續成長率 (%)", 
            min_value=0.0, 
            max_value=5.0, 
            value=defaults.get('terminal_growth', 3.0), 
            step=0.1
        ) / 100
        
        projection_years = st.selectbox(
            "預測年數", 
            options=[3, 5, 7, 10], 
            index=1
        )
        
        return {
            'discount_rate': discount_rate,
            'growth_rate': growth_rate,
            'terminal_growth': terminal_growth,
            'projection_years': projection_years
        }
    
    @staticmethod
    def render_loading_message(message: str) -> None:
        """渲染載入訊息
        
        Args:
            message: 載入訊息
        """
        with st.spinner(message):
            st.empty()
    
    @staticmethod
    def render_error_message(error: str, show_details: bool = False) -> None:
        """渲染錯誤訊息
        
        Args:
            error: 錯誤訊息
            show_details: 是否顯示詳細信息
        """
        st.error(f"❌ 錯誤: {error}")
        
        if show_details:
            with st.expander("🔍 詳細錯誤信息"):
                import traceback
                st.code(traceback.format_exc())
    
    @staticmethod
    def render_success_message(message: str) -> None:
        """渲染成功訊息
        
        Args:
            message: 成功訊息
        """
        st.success(f"✅ {message}")
    
    @staticmethod
    def render_disclaimer() -> None:
        """渲染免責聲明"""
        st.markdown("---")
        st.caption("⚠️ 免責聲明：本工具僅供教育和研究用途，不構成投資建議。投資有風險，請謹慎決策。")
    
    @staticmethod
    def render_action_buttons(buttons: List[Dict[str, Any]]) -> Dict[str, bool]:
        """渲染操作按鈕組
        
        Args:
            buttons: 按鈕配置列表
            
        Returns:
            Dict[str, bool]: 按鈕點擊狀態
        """
        button_states = {}
        
        if len(buttons) == 1:
            button = buttons[0]
            button_states[button['key']] = st.button(
                label=button['label'],
                type=button.get('type', 'secondary'),
                help=button.get('help', None),
                disabled=button.get('disabled', False)
            )
        else:
            cols = st.columns(len(buttons))
            for i, button in enumerate(buttons):
                with cols[i]:
                    button_states[button['key']] = st.button(
                        label=button['label'],
                        type=button.get('type', 'secondary'),
                        help=button.get('help', None),
                        disabled=button.get('disabled', False)
                    )
        
        return button_states
