"""
增強型DCF模型
提供更準確的折現現金流估值計算，支援多種數據格式
"""

import logging
from typing import Union, List, Dict, Any, Tuple, Optional

class EnhancedDCFModel:
    """增強型DCF模型 - 支援多種數據格式"""
    
    def __init__(self):
        self.default_growth_rate = 0.05
        self.default_discount_rate = 0.10
        self.terminal_growth_rate = 0.02
        self.logger = logging.getLogger(__name__)
    
    def extract_fcf_data(self, financial_data: Union[Dict, List, Any]) -> List[float]:
        """智能提取自由現金流數據，支援多種格式"""
        try:
            # 情況1：直接是數值列表
            if isinstance(financial_data, list):
                return [float(x) for x in financial_data if x is not None]
            
            # 情況2：字典格式，尋找自由現金流欄位
            if isinstance(financial_data, dict):
                # 嘗試不同的 FCF 欄位名稱
                fcf_fields = ['free_cash_flow', 'fcf', 'operating_cash_flow', 'cash_flow']
                
                for field in fcf_fields:
                    if field in financial_data:
                        fcf_data = financial_data[field]
                        
                        # 如果是列表，直接返回
                        if isinstance(fcf_data, list):
                            return [float(x) for x in fcf_data if x is not None]
                        
                        # 如果是嵌套字典，嘗試提取 annual 數據
                        if isinstance(fcf_data, dict):
                            for key in ['annual', 'yearly', 'values']:
                                if key in fcf_data:
                                    return [float(x) for x in fcf_data[key] if x is not None]
                        
                        # 如果是單個數值
                        if isinstance(fcf_data, (int, float)):
                            return [float(fcf_data)]
                
                # 如果沒找到專門的 FCF 欄位，嘗試從現金流表中提取
                if 'cash_flow' in financial_data:
                    cash_flow = financial_data['cash_flow']
                    if isinstance(cash_flow, dict) and 'free_cash_flow' in cash_flow:
                        return [float(x) for x in cash_flow['free_cash_flow'] if x is not None]
            
            # 情況3：單個數值
            if isinstance(financial_data, (int, float)):
                return [float(financial_data)]
            
            self.logger.warning(f"無法從數據中提取FCF: {type(financial_data)}")
            return []
            
        except Exception as e:
            self.logger.error(f"提取FCF數據時發生錯誤: {e}")
            return []
    
    def calculate_dcf_value(self, financial_data: Union[Dict, List, Any], 
                          discount_rate: Optional[float] = None, 
                          growth_rate: Optional[float] = None) -> float:
        """計算DCF估值 - 自動適應數據格式"""
        if discount_rate is None:
            discount_rate = self.default_discount_rate
        if growth_rate is None:
            growth_rate = self.default_growth_rate
            
        # 智能提取現金流數據
        cash_flows = self.extract_fcf_data(financial_data)
        
        if not cash_flows:
            self.logger.warning("無有效現金流數據，返回0")
            return 0
            
        # 計算折現現金流
        present_value = 0
        for i, cf in enumerate(cash_flows):
            if cf > 0:  # 只考慮正現金流
                present_value += cf / ((1 + discount_rate) ** (i + 1))
            
        # 計算終值 (使用最後一年現金流)
        if cash_flows:
            terminal_value = self.calculate_terminal_value(
                cash_flows[-1], discount_rate, growth_rate
            )
            present_value += terminal_value / ((1 + discount_rate) ** len(cash_flows))
            
        return present_value
    
    def calculate_terminal_value(self, final_cash_flow: float, 
                               discount_rate: Optional[float] = None, 
                               growth_rate: Optional[float] = None) -> float:
        """計算終值"""
        if discount_rate is None:
            discount_rate = self.default_discount_rate
        if growth_rate is None:
            growth_rate = self.terminal_growth_rate
            
        if discount_rate <= growth_rate:
            # 避免分母為負或零
            adjusted_discount_rate = growth_rate + 0.02
            self.logger.warning(f"調整折現率從 {discount_rate} 至 {adjusted_discount_rate}")
            discount_rate = adjusted_discount_rate
            
        return (final_cash_flow * (1 + growth_rate)) / (discount_rate - growth_rate)


class IntegratedDCFHandler:
    """整合式 DCF 處理器 - 向後兼容性"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.dcf_model = EnhancedDCFModel()
        self.logger = logging.getLogger(__name__)
    
    def calculate_dcf_value(self, financial_data: Union[Dict, List, Any], 
                          discount_rate: float = 0.1, 
                          terminal_growth_rate: float = 0.02) -> float:
        """計算 DCF 價值 - 統一接口"""
        try:
            return self.dcf_model.calculate_dcf_value(
                financial_data, discount_rate, terminal_growth_rate
            )
        except Exception as e:
            self.logger.error(f"DCF計算錯誤: {e}")
            return 0
    
    def validate_inputs(self, data: Any) -> Tuple[bool, str]:
        """驗證輸入數據"""
        try:
            if data is None:
                return False, "數據為空"
            
            # 嘗試提取現金流數據
            fcf_data = self.dcf_model.extract_fcf_data(data)
            
            if not fcf_data:
                return False, "無法提取有效的現金流數據"
            
            if len(fcf_data) == 0:
                return False, "現金流數據為空"
            
            return True, "數據有效"
            
        except Exception as e:
            return False, f"數據驗證錯誤: {e}"
