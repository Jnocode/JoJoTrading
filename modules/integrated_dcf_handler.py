"""
整合DCF處理器
統一處理所有DCF相關計算
"""

from .enhanced_dcf import EnhancedDCFModel
from .data_validator import FinancialDataValidator

def calculate_enhanced_dcf_valuation(stock_code, financial_data, **kwargs):
    """
    計算增強型DCF估值
    
    Args:
        stock_code: 股票代碼
        financial_data: 財務數據
        **kwargs: 其他參數
        
    Returns:
        dict: DCF估值結果
    """
    validator = FinancialDataValidator()
    dcf_model = EnhancedDCFModel()
    
    # 驗證數據
    if not validator.validate_financial_data(financial_data):
        return {
            'stock_code': stock_code,
            'dcf_value': 0,
            'error': 'Invalid financial data'
        }
    
    # 簡化的DCF計算
    try:
        # 假設的現金流（實際應從財務數據計算）
        cash_flows = [1000000, 1100000, 1200000, 1300000, 1400000]  # 示例數據
        dcf_value = dcf_model.calculate_dcf_value(cash_flows)
        
        return {
            'stock_code': stock_code,
            'dcf_value': dcf_value,
            'cash_flows': cash_flows,
            'error': None
        }
    except Exception as e:
        return {
            'stock_code': stock_code,
            'dcf_value': 0,
            'error': str(e)
        }

def integrated_dcf_handler(context):
    """整合DCF處理器的主要函數"""
    return calculate_enhanced_dcf_valuation(
        context.get('stock_code', ''),
        context.get('financial_data', None),
        **context
    )
