"""
WACC (加權平均資本成本) 自動計算模組

計算企業的加權平均資本成本，用於 DCF 估值的折現率。

公式：
WACC = (E/V) × Re + (D/V) × Rd × (1 - Tc)

其中：
- E = 權益市值 (Market Value of Equity)
- D = 債務市值 (Market Value of Debt)
- V = E + D (企業總價值)
- Re = 權益成本 (Cost of Equity) - 使用 CAPM
- Rd = 債務成本 (Cost of Debt)
- Tc = 企業稅率 (Corporate Tax Rate)

CAPM (資本資產定價模型):
Re = Rf + β × (Rm - Rf)

其中：
- Rf = 無風險利率 (10年期公債殖利率)
- β = 貝他係數 (股票相對市場波動)
- Rm = 市場報酬率

Author: jojo_trading team
Date: 2025-11-19
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class WACCCalculator:
    """
    WACC 計算器
    
    自動計算企業的加權平均資本成本，用於 DCF 估值。
    """
    
    # 台灣市場預設參數
    DEFAULT_RISK_FREE_RATE = 0.015  # 10年期公債殖利率 1.5%
    DEFAULT_MARKET_RETURN = 0.08    # 台股長期平均報酬 8%
    DEFAULT_CORPORATE_TAX_RATE = 0.20  # 企業所得稅率 20%
    DEFAULT_BETA = 1.0  # 預設貝他值
    
    def __init__(
        self,
        risk_free_rate: Optional[float] = None,
        market_return: Optional[float] = None,
        corporate_tax_rate: Optional[float] = None
    ):
        """
        初始化 WACC 計算器
        
        Args:
            risk_free_rate: 無風險利率（如 10 年期公債殖利率）
            market_return: 市場報酬率
            corporate_tax_rate: 企業所得稅率
        """
        self.risk_free_rate = risk_free_rate or self.DEFAULT_RISK_FREE_RATE
        self.market_return = market_return or self.DEFAULT_MARKET_RETURN
        self.corporate_tax_rate = corporate_tax_rate or self.DEFAULT_CORPORATE_TAX_RATE
        
        logger.info(
            f"🎯 WACC 計算器已初始化 "
            f"(Rf={self.risk_free_rate:.2%}, Rm={self.market_return:.2%}, "
            f"Tax={self.corporate_tax_rate:.2%})"
        )
    
    def calculate_cost_of_equity(
        self,
        beta: Optional[float] = None,
        risk_free_rate: Optional[float] = None,
        market_return: Optional[float] = None
    ) -> float:
        """
        計算權益成本 (Cost of Equity) 使用 CAPM
        
        Re = Rf + β × (Rm - Rf)
        
        Args:
            beta: 貝他係數
            risk_free_rate: 無風險利率
            market_return: 市場報酬率
        
        Returns:
            權益成本
        """
        rf = risk_free_rate or self.risk_free_rate
        rm = market_return or self.market_return
        b = beta or self.DEFAULT_BETA
        
        # CAPM 公式
        cost_of_equity = rf + b * (rm - rf)
        
        logger.debug(
            f"💰 權益成本 = {rf:.2%} + {b:.2f} × ({rm:.2%} - {rf:.2%}) "
            f"= {cost_of_equity:.2%}"
        )
        
        return cost_of_equity
    
    def calculate_cost_of_debt(
        self,
        interest_expense: float,
        total_debt: float,
        min_rate: float = 0.01,
        max_rate: float = 0.15
    ) -> float:
        """
        計算債務成本 (Cost of Debt)
        
        Rd = 利息費用 / 總債務
        
        Args:
            interest_expense: 年度利息費用
            total_debt: 總債務
            min_rate: 最小合理債務成本
            max_rate: 最大合理債務成本
        
        Returns:
            債務成本
        """
        if total_debt <= 0:
            logger.warning("⚠️  總債務 <= 0，債務成本設為 0")
            return 0.0
        
        if interest_expense < 0:
            logger.warning(f"⚠️  利息費用為負數 ({interest_expense})，使用絕對值")
            interest_expense = abs(interest_expense)
        
        # 計算債務成本
        cost_of_debt = interest_expense / total_debt
        
        # 合理性檢查
        if cost_of_debt < min_rate:
            logger.warning(
                f"⚠️  計算的債務成本過低 ({cost_of_debt:.2%})，"
                f"調整為最小值 {min_rate:.2%}"
            )
            cost_of_debt = min_rate
        elif cost_of_debt > max_rate:
            logger.warning(
                f"⚠️  計算的債務成本過高 ({cost_of_debt:.2%})，"
                f"調整為最大值 {max_rate:.2%}"
            )
            cost_of_debt = max_rate
        
        logger.debug(f"💰 債務成本 = {interest_expense:,.0f} / {total_debt:,.0f} = {cost_of_debt:.2%}")
        
        return cost_of_debt
    
    def calculate_wacc(
        self,
        market_cap: float,
        total_debt: float,
        cost_of_equity: float,
        cost_of_debt: float,
        tax_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        計算 WACC (加權平均資本成本)
        
        WACC = (E/V) × Re + (D/V) × Rd × (1 - Tc)
        
        Args:
            market_cap: 權益市值
            total_debt: 總債務
            cost_of_equity: 權益成本
            cost_of_debt: 債務成本
            tax_rate: 企業稅率
        
        Returns:
            包含 WACC 及計算細節的字典
        """
        tax = tax_rate or self.corporate_tax_rate
        
        # 檢查輸入有效性
        if market_cap <= 0:
            logger.error("❌ 市值必須大於 0")
            raise ValueError("市值必須大於 0")
        
        # 計算企業總價值
        total_value = market_cap + total_debt
        
        # 計算權重
        equity_weight = market_cap / total_value
        debt_weight = total_debt / total_value
        
        # 計算 WACC
        wacc = (equity_weight * cost_of_equity) + \
               (debt_weight * cost_of_debt * (1 - tax))
        
        # 組裝結果
        result = {
            'wacc': wacc,
            'equity_weight': equity_weight,
            'debt_weight': debt_weight,
            'cost_of_equity': cost_of_equity,
            'cost_of_debt': cost_of_debt,
            'after_tax_cost_of_debt': cost_of_debt * (1 - tax),
            'tax_rate': tax,
            'market_cap': market_cap,
            'total_debt': total_debt,
            'total_value': total_value,
        }
        
        logger.info(
            f"📊 WACC = {equity_weight:.1%} × {cost_of_equity:.2%} + "
            f"{debt_weight:.1%} × {cost_of_debt:.2%} × (1 - {tax:.0%}) "
            f"= {wacc:.2%}"
        )
        
        return result
    
    def calculate_from_financial_data(
        self,
        financial_data: pd.DataFrame,
        stock_price: float,
        shares_outstanding: float,
        beta: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        從財務報表數據自動計算 WACC
        
        Args:
            financial_data: 財務報表數據（需包含資產負債表和損益表）
            stock_price: 當前股價
            shares_outstanding: 流通股數
            beta: 貝他係數（可選）
        
        Returns:
            包含 WACC 及所有計算細節的字典
        """
        logger.info("🚀 開始從財務數據計算 WACC...")
        
        # 1. 計算市值
        market_cap = stock_price * shares_outstanding
        logger.info(f"  市值 = {stock_price:.2f} × {shares_outstanding:,.0f} = {market_cap:,.0f}")
        
        # 2. 提取最新財務數據
        if financial_data.empty:
            logger.error("❌ 財務數據為空")
            raise ValueError("財務數據為空")
        
        latest_data = financial_data.iloc[0]  # 假設已按日期降序排列
        
        # 3. 提取債務和利息費用
        # 嘗試不同的欄位名稱
        debt_fields = [
            'TotalLiabilities', 'total_liabilities', '負債總額',
            'TotalDebt', 'total_debt', '總債務'
        ]
        
        interest_fields = [
            'InterestExpense', 'interest_expense', '利息費用',
            'FinanceCosts', 'finance_costs', '財務成本'
        ]
        
        total_debt = 0
        for field in debt_fields:
            if field in latest_data.index:
                total_debt = float(latest_data[field])
                logger.info(f"  找到債務欄位: {field} = {total_debt:,.0f}")
                break
        
        if total_debt == 0:
            logger.warning("⚠️  未找到債務數據，假設為 0")
        
        interest_expense = 0
        for field in interest_fields:
            if field in latest_data.index:
                interest_expense = float(latest_data[field])
                logger.info(f"  找到利息費用欄位: {field} = {interest_expense:,.0f}")
                break
        
        if interest_expense == 0 and total_debt > 0:
            # 估算利息費用（使用市場平均利率 3%）
            interest_expense = total_debt * 0.03
            logger.warning(
                f"⚠️  未找到利息費用，估算為 {interest_expense:,.0f} "
                f"(債務 × 3%)"
            )
        
        # 4. 計算權益成本
        cost_of_equity = self.calculate_cost_of_equity(beta=beta)
        
        # 5. 計算債務成本
        cost_of_debt = self.calculate_cost_of_debt(
            interest_expense=interest_expense,
            total_debt=total_debt
        )
        
        # 6. 計算 WACC
        wacc_result = self.calculate_wacc(
            market_cap=market_cap,
            total_debt=total_debt,
            cost_of_equity=cost_of_equity,
            cost_of_debt=cost_of_debt
        )
        
        # 7. 添加額外信息
        wacc_result.update({
            'stock_price': stock_price,
            'shares_outstanding': shares_outstanding,
            'interest_expense': interest_expense,
            'beta': beta or self.DEFAULT_BETA,
            'calculation_method': 'from_financial_data',
        })
        
        logger.info(f"✅ WACC 計算完成: {wacc_result['wacc']:.2%}")
        
        return wacc_result
    
    def get_industry_beta(self, industry: str) -> float:
        """
        取得產業平均 Beta 值
        
        Args:
            industry: 產業名稱
        
        Returns:
            產業平均 Beta
        """
        # 台灣主要產業 Beta 參考值（可根據實際數據更新）
        industry_betas = {
            '半導體': 1.2,
            '電子零組件': 1.1,
            '光電': 1.15,
            '通信網路': 1.0,
            '電腦週邊': 1.05,
            '金融保險': 0.8,
            '鋼鐵': 1.1,
            '塑化': 0.9,
            '食品': 0.7,
            '紡織': 0.8,
            '電機機械': 0.95,
            '汽車': 1.0,
            '生技醫療': 1.3,
            '觀光': 1.2,
            '其他': 1.0,
        }
        
        # 查找產業 Beta
        for key, beta in industry_betas.items():
            if key in industry:
                logger.info(f"📈 產業 '{industry}' 的平均 Beta = {beta}")
                return beta
        
        # 未找到則使用預設值
        logger.warning(f"⚠️  未找到產業 '{industry}' 的 Beta，使用預設值 {self.DEFAULT_BETA}")
        return self.DEFAULT_BETA


def calculate_wacc_simple(
    market_cap: float,
    total_debt: float,
    interest_expense: float,
    beta: float = 1.0,
    risk_free_rate: float = 0.015,
    market_return: float = 0.08,
    tax_rate: float = 0.20
) -> float:
    """
    簡化版 WACC 計算函數
    
    Args:
        market_cap: 市值
        total_debt: 總債務
        interest_expense: 利息費用
        beta: 貝他係數
        risk_free_rate: 無風險利率
        market_return: 市場報酬率
        tax_rate: 稅率
    
    Returns:
        WACC 值
    """
    calculator = WACCCalculator(risk_free_rate, market_return, tax_rate)
    
    # 計算權益成本
    cost_of_equity = calculator.calculate_cost_of_equity(beta)
    
    # 計算債務成本
    cost_of_debt = calculator.calculate_cost_of_debt(interest_expense, total_debt)
    
    # 計算 WACC
    result = calculator.calculate_wacc(
        market_cap=market_cap,
        total_debt=total_debt,
        cost_of_equity=cost_of_equity,
        cost_of_debt=cost_of_debt
    )
    
    return result['wacc']


if __name__ == '__main__':
    # 測試範例
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("🎯 WACC 計算器測試")
    print("="*70)
    
    # 範例：台積電 (假設數據)
    print("\n範例：台積電 WACC 計算")
    print("-"*70)
    
    calculator = WACCCalculator()
    
    # 假設數據
    market_cap = 15_000_000_000_000  # 15兆市值
    total_debt = 500_000_000_000     # 5000億債務
    interest_expense = 15_000_000_000  # 150億利息
    beta = 1.1
    
    # 計算權益成本
    cost_of_equity = calculator.calculate_cost_of_equity(beta=beta)
    print(f"\n權益成本 (Re): {cost_of_equity:.2%}")
    
    # 計算債務成本
    cost_of_debt = calculator.calculate_cost_of_debt(
        interest_expense=interest_expense,
        total_debt=total_debt
    )
    print(f"債務成本 (Rd): {cost_of_debt:.2%}")
    
    # 計算 WACC
    result = calculator.calculate_wacc(
        market_cap=market_cap,
        total_debt=total_debt,
        cost_of_equity=cost_of_equity,
        cost_of_debt=cost_of_debt
    )
    
    print(f"\n" + "="*70)
    print(f"📊 WACC 計算結果")
    print("="*70)
    print(f"權益權重: {result['equity_weight']:.1%}")
    print(f"債務權重: {result['debt_weight']:.1%}")
    print(f"稅後債務成本: {result['after_tax_cost_of_debt']:.2%}")
    print(f"\n✨ WACC = {result['wacc']:.2%}")
