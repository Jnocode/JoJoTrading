
"""
Hedging Analysis Module
用途：計算期貨避險所需的口數與策略建議
"""
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class HedgeRecommendation:
    contract_code: str
    contract_name: str
    current_price: float
    multiplier: float
    required_contracts: float
    contract_value: float
    coverage_ratio: float # e.g. 100%

class HedgingCalculator:
    """
    提供投資組合避險計算邏輯
    公式: N = (Portfolio Value * Beta) / (Future Price * Multiplier)
    """
    
    # 標準合約規格 (點值)
    SPECS = {
        'TXF': {'name': '台指期 (大台)', 'multiplier': 200},
        'MXF': {'name': '小台指 (小台)', 'multiplier': 50},
        'ZEF': {'name': '微台指 (微台)', 'multiplier': 10} # 假設代號
    }

    @staticmethod
    def calculate_contracts(
        portfolio_value: float,
        future_price: float,
        contract_type: str = 'TXF',
        target_beta: float = 1.0,
        portfolio_beta: float = 1.0
    ) -> HedgeRecommendation:
        """
        計算特定合約所需的避險口數
        """
        spec = HedgingCalculator.SPECS.get(contract_type)
        if not spec:
            raise ValueError(f"Unknown contract type: {contract_type}")
            
        multiplier = spec['multiplier']
        contract_name = spec['name']
        
        # 單口合約價值
        notional_value = future_price * multiplier
        
        # 需避險的總曝險金額 (Adjusted by Beta)
        # 若希望將 Beta 降為 0 (完全避險)，則需避險 Beta * Value
        # contracts = (Value * Beta) / Notional
        
        required_qty = (portfolio_value * portfolio_beta) / notional_value
        
        return HedgeRecommendation(
            contract_code=contract_type,
            contract_name=contract_name,
            current_price=future_price,
            multiplier=multiplier,
            required_contracts=round(required_qty, 2),
            contract_value=notional_value,
            coverage_ratio=1.0
        )

    @staticmethod
    def get_all_recommendations(
        portfolio_value: float,
        future_price: float,
        portfolio_beta: float = 1.0
    ) -> List[HedgeRecommendation]:
        """
        一次產生 大台/小台/微台 的建議
        """
        results = []
        for code in ['TXF', 'MXF', 'ZEF']:
            try:
                rec = HedgingCalculator.calculate_contracts(
                    portfolio_value, future_price, code, portfolio_beta=portfolio_beta
                )
                results.append(rec)
            except:
                pass
        return results
