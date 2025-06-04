"""
財務數據驗證器
提供數據完整性和準確性檢查
"""

class FinancialDataValidator:
    """財務數據驗證器"""
    
    def __init__(self):
        pass
    
    def validate_financial_data(self, data):
        """驗證財務數據的完整性"""
        if data is None or data.empty:
            return False
        return True
    
    def validate_dcf_inputs(self, inputs):
        """驗證DCF輸入參數"""
        required_fields = ['revenue', 'fcf', 'growth_rate']
        for field in required_fields:
            if field not in inputs or inputs[field] is None:
                return False
        return True
