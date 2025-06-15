"""
整合DCF處理器
統一處理所有DCF相關計算
"""

from .enhanced_dcf import EnhancedDCFModel
from ..utils.data_validator import FinancialDataValidator

class IntegratedDCFHandler:
    """整合DCF處理器類別"""
    
    def __init__(self):
        """初始化處理器"""
        try:
            self.validator = FinancialDataValidator()
            self.dcf_model = EnhancedDCFModel()
        except Exception as e:
            print(f"⚠️ IntegratedDCFHandler 初始化警告: {e}")
            self.validator = None
            self.dcf_model = None
    
    def calculate_dcf_valuation(self, stock_code, financials, risk_preference, context):
        """
        計算DCF估值
        
        Args:
            stock_code: 股票代碼
            financials: 財務數據
            risk_preference: 風險偏好
            context: 計算上下文
            
        Returns:
            dict: DCF估值結果
        """
        if not self.validator or not self.dcf_model:
            return {
                'stock_code': stock_code,
                'intrinsic_value_per_share': 0,
                'error': 'Handler not properly initialized'
            }
        
        try:
            # 簡化的DCF計算
            net_income = financials.get('net_income_parent', 0)
            shares_outstanding = financials.get('shares_outstanding', 1)
            current_price = financials.get('current_market_price', 0)
              # 基本DCF估值
            growth_rate = context.get('dcf_short_term_growth_rate', 0.08)
            terminal_growth = context.get('dcf_terminal_growth_rate', 0.03)
            
            # 根據風險偏好設定折現率
            risk_rates = {
                'conservative': 0.12,  # 保守：12%
                'moderate': 0.10,      # 中等：10%
                'aggressive': 0.08     # 積極：8%
            }
            discount_rate = risk_rates.get(risk_preference, 0.10)  # 預設為中等風險
            
            # 計算每股盈餘
            eps = net_income / shares_outstanding if shares_outstanding > 0 else 0
            
            # 簡化的DCF計算
            total_pv = 0
            current_eps = eps
            
            # 5年預測
            for year in range(1, 6):
                future_eps = current_eps * ((1 + growth_rate) ** year)
                pv = future_eps / ((1 + discount_rate) ** year)
                total_pv += pv
            
            # 終值計算
            terminal_eps = current_eps * ((1 + growth_rate) ** 5) * (1 + terminal_growth)
            terminal_value = terminal_eps / (discount_rate - terminal_growth)
            terminal_pv = terminal_value / ((1 + discount_rate) ** 5)
            
            total_pv += terminal_pv
            
            # 計算潛在回報
            potential_return = None
            if current_price and current_price > 0:
                potential_return = (total_pv / current_price) - 1
            
            return {
                'stock_code': stock_code,
                'intrinsic_value_per_share': round(total_pv, 2),
                'current_market_price': current_price,
                'potential_return': round(potential_return, 4) if potential_return else None,
                'calculation_method': 'integrated_dcf',
                'used_discount_rate': discount_rate,
                'used_growth_rate': growth_rate,
                'used_terminal_growth': terminal_growth
            }
            
        except Exception as e:
            return {
                'stock_code': stock_code,
                'intrinsic_value_per_share': 0,
                'error': f'Integrated DCF calculation error: {str(e)}'
            }

def calculate_enhanced_dcf_valuation(stock_code, financial_data, **kwargs):
    """
    計算增強型DCF估值（向後相容）
    
    Args:
        stock_code: 股票代碼
        financial_data: 財務數據
        **kwargs: 其他參數
        
    Returns:
        dict: DCF估值結果
    """
    handler = IntegratedDCFHandler()
    return handler.calculate_dcf_valuation(
        stock_code, financial_data, 
        kwargs.get('risk_preference', 0.08),
        kwargs
    )

# 建立全域實例以供向後相容
integrated_dcf_handler = IntegratedDCFHandler()
