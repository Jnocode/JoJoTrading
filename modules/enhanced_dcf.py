"""
增強型DCF模型
提供更準確的折現現金流估值計算
"""

class EnhancedDCFModel:
    """增強型DCF模型"""
    
    def __init__(self):
        self.default_growth_rate = 0.05
        self.default_discount_rate = 0.10
        self.terminal_growth_rate = 0.02
    
    def calculate_dcf_value(self, cash_flows, discount_rate=None):
        """計算DCF估值"""
        if discount_rate is None:
            discount_rate = self.default_discount_rate
            
        if not cash_flows:
            return 0
            
        # 簡化的DCF計算
        present_value = 0
        for i, cf in enumerate(cash_flows):
            present_value += cf / ((1 + discount_rate) ** (i + 1))
            
        return present_value
    
    def calculate_terminal_value(self, final_cash_flow, discount_rate=None):
        """計算終值"""
        if discount_rate is None:
            discount_rate = self.default_discount_rate
            
        return (final_cash_flow * (1 + self.terminal_growth_rate)) / (discount_rate - self.terminal_growth_rate)
