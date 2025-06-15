# -*- coding: utf-8 -*-
"""
DCF計算器 - 統一介面

提供標準的DCF計算器類別，整合現有的增強型DCF功能
"""

from typing import Dict, Any, Optional
import sys
import os

# 添加專案路徑以便導入模組
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class DCFCalculator:
    """DCF計算器主類別"""
    
    def __init__(self):
        """初始化DCF計算器"""
        self._enhanced_dcf = None
        self._integrated_handler = None
        self._initialize_components()
    
    def _initialize_components(self):
        """安全地初始化DCF組件"""
        try:
            # 嘗試導入增強型DCF模型
            from .enhanced_dcf import EnhancedDCFModel
            self._enhanced_dcf = EnhancedDCFModel()
            print("✅ EnhancedDCFModel 初始化成功")
        except ImportError as e:
            print(f"⚠️ EnhancedDCFModel 導入失敗: {e}")
            
        try:
            # 嘗試導入整合處理器
            from .integrated_dcf_handler import IntegratedDCFHandler
            self._integrated_handler = IntegratedDCFHandler()
            print("✅ IntegratedDCFHandler 初始化成功")
        except ImportError as e:
            print(f"⚠️ IntegratedDCFHandler 導入失敗: {e}")
    
    def calculate_dcf(
        self, 
        stock_code: str, 
        financial_data: Dict[str, Any], 
        discount_rate: float = 0.08,
        **kwargs
    ) -> Dict[str, Any]:
        """
        計算DCF估值
        
        Args:
            stock_code: 股票代碼
            financial_data: 財務數據
            discount_rate: 折現率
            **kwargs: 其他參數
            
        Returns:
            Dict[str, Any]: DCF計算結果
        """
        try:
            # 準備基本參數
            context = {
                'dcf_short_term_growth_rate': kwargs.get('growth_rate', 0.08),
                'dcf_terminal_growth_rate': kwargs.get('terminal_growth_rate', 0.03),
                'risk_preference': discount_rate,
                'dcf_projection_years': kwargs.get('projection_years', 5)
            }
            
            # 優先使用整合處理器
            if self._integrated_handler:
                return self._integrated_handler.calculate_dcf_valuation(
                    stock_code, financial_data, discount_rate, context
                )
            
            # 次選使用增強型DCF
            elif self._enhanced_dcf:
                result = self._enhanced_dcf.calculate_enhanced_dcf(
                    stock_code=stock_code,
                    financial_data=financial_data,
                    context=context,
                    **kwargs
                )
                return {
                    'stock_code': stock_code,
                    'intrinsic_value_per_share': result.base_case_valuation,
                    'current_market_price': result.current_market_price,
                    'potential_return': result.potential_return,
                    'calculation_method': 'enhanced_dcf'
                }
            
            # 最後備案：基本DCF計算
            else:
                return self._basic_dcf_calculation(stock_code, financial_data, context)
                
        except Exception as e:
            return {
                'stock_code': stock_code,
                'error': f'DCF計算錯誤: {str(e)}',
                'intrinsic_value_per_share': 0,
                'calculation_method': 'error'
            }
    
    def _basic_dcf_calculation(
        self, 
        stock_code: str, 
        financial_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基本DCF計算（備用方法）
        
        Args:
            stock_code: 股票代碼
            financial_data: 財務數據
            context: 計算上下文
            
        Returns:
            Dict[str, Any]: 基本DCF結果
        """
        try:
            # 提取基本財務數據
            net_income = financial_data.get('net_income_parent', 0)
            shares_outstanding = financial_data.get('shares_outstanding', 1)
            current_price = financial_data.get('current_market_price', 100)
            
            # 基本參數
            growth_rate = context.get('dcf_short_term_growth_rate', 0.08)
            terminal_growth = context.get('dcf_terminal_growth_rate', 0.03)
            discount_rate = context.get('risk_preference', 0.08)
            projection_years = context.get('dcf_projection_years', 5)
            
            # 計算每股盈餘
            eps = net_income / shares_outstanding if shares_outstanding > 0 else 0
            
            # 簡化的DCF計算（假設盈餘等於自由現金流）
            total_pv = 0
            current_eps = eps
            
            # 計算成長期現值
            for year in range(1, projection_years + 1):
                current_eps *= (1 + growth_rate)
                pv = current_eps / ((1 + discount_rate) ** year)
                total_pv += pv
            
            # 計算終值
            terminal_eps = current_eps * (1 + terminal_growth)
            if discount_rate > terminal_growth:
                terminal_value = terminal_eps / (discount_rate - terminal_growth)
                pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)
                total_pv += pv_terminal
            
            # 計算潛在報酬
            potential_return = None
            if current_price and current_price > 0:
                potential_return = (total_pv / current_price) - 1
            
            return {
                'stock_code': stock_code,
                'intrinsic_value_per_share': round(total_pv, 2),
                'current_market_price': current_price,
                'potential_return': round(potential_return, 4) if potential_return else None,
                'calculation_method': 'basic_dcf',
                'used_discount_rate': discount_rate,
                'used_growth_rate': growth_rate,
                'used_terminal_growth': terminal_growth
            }
            
        except Exception as e:
            return {
                'stock_code': stock_code,
                'error': f'基本DCF計算錯誤: {str(e)}',
                'intrinsic_value_per_share': 0,
                'calculation_method': 'basic_dcf_error'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        獲取DCF計算器狀態
        
        Returns:
            Dict[str, Any]: 狀態資訊
        """
        return {
            'enhanced_dcf_available': self._enhanced_dcf is not None,
            'integrated_handler_available': self._integrated_handler is not None,
            'basic_dcf_available': True,
            'preferred_method': (
                'integrated_handler' if self._integrated_handler else
                'enhanced_dcf' if self._enhanced_dcf else
                'basic_dcf'
            )
        }
    
    def test_calculation(self) -> bool:
        """
        測試DCF計算功能
        
        Returns:
            bool: 測試是否成功
        """
        try:
            # 創建測試數據
            test_data = {
                'net_income_parent': 100000000,  # 1億淨利
                'shares_outstanding': 1000000,   # 100萬股
                'current_market_price': 50       # 股價50元
            }
            
            result = self.calculate_dcf('TEST', test_data)
            
            return (
                'error' not in result and 
                result.get('intrinsic_value_per_share', 0) > 0
            )
        
        except Exception:
            return False


# 為了向後兼容，提供測試函數
def comprehensive_dcf_test():
    """綜合DCF測試函數（向後兼容）"""
    calculator = DCFCalculator()
    
    print("=" * 60)
    print("DCF計算器綜合測試")
    print("=" * 60)
    
    # 顯示狀態
    status = calculator.get_status()
    print("狀態檢查:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    # 執行測試
    test_result = calculator.test_calculation()
    print(f"功能測試: {'✅ 通過' if test_result else '❌ 失敗'}")
    
    return test_result


if __name__ == "__main__":
    comprehensive_dcf_test()