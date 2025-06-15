"""
數據驗證模組 - 向後兼容性
"""
# 為了向後兼容，重新導出 utils.data_validator
from jojo_trading.utils.data_validator import FinancialDataValidator

__all__ = ['FinancialDataValidator']
