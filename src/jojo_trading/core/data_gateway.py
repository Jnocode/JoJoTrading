"""
數據閘道器 - 暫時的模擬實現
"""

class DataGateway:
    """數據閘道器類別"""
    
    def __init__(self):
        """初始化數據閘道器"""
        pass
    
    def get_stock_data(self, stock_code: str):
        """獲取股票數據"""
        return {
            'stock_code': stock_code,
            'current_price': 100.0,
            'volume': 1000
        }
