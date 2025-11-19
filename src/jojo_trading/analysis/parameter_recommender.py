"""
DCF 參數推薦引擎

根據公司的財務狀況、產業特性、市場環境，智能推薦最適合的 DCF 估值參數。

推薦參數包括：
1. 折現率 (WACC) - 自動計算或產業平均
2. 永續成長率 - 基於歷史成長率和產業特性
3. 預測期間 - 根據公司穩定性
4. 現金流類型 - FCF vs ECF 建議
5. 安全邊際 - 根據風險評估

Author: jojo_trading team
Date: 2025-11-19
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IndustryType(Enum):
    """產業類型"""
    MATURE = "mature"          # 成熟產業（低成長、穩定）
    GROWTH = "growth"          # 成長產業（中高成長）
    CYCLICAL = "cyclical"      # 景氣循環產業
    TECH = "tech"              # 科技產業（高成長、高風險）
    FINANCIAL = "financial"    # 金融產業


@dataclass
class DCFParameters:
    """DCF 參數推薦結果"""
    discount_rate: float
    terminal_growth_rate: float
    forecast_periods: int
    safety_margin: float
    cash_flow_type: str
    confidence_level: str
    reasoning: Dict[str, str]
    alternative_scenarios: Dict[str, Dict[str, float]]


class DCFParameterRecommender:
    """
    DCF 參數推薦引擎
    
    基於多維度分析，提供智能化的 DCF 參數建議。
    """
    
    # 產業預設參數
    INDUSTRY_DEFAULTS = {
        IndustryType.MATURE: {
            'terminal_growth': 0.02,
            'forecast_periods': 5,
            'safety_margin': 0.20,
        },
        IndustryType.GROWTH: {
            'terminal_growth': 0.03,
            'forecast_periods': 7,
            'safety_margin': 0.25,
        },
        IndustryType.CYCLICAL: {
            'terminal_growth': 0.02,
            'forecast_periods': 10,  # 需要完整週期
            'safety_margin': 0.30,
        },
        IndustryType.TECH: {
            'terminal_growth': 0.04,
            'forecast_periods': 5,
            'safety_margin': 0.35,
        },
        IndustryType.FINANCIAL: {
            'terminal_growth': 0.025,
            'forecast_periods': 5,
            'safety_margin': 0.25,
        },
    }
    
    def __init__(self):
        """初始化參數推薦引擎"""
        logger.info("🎯 DCF 參數推薦引擎已初始化")
    
    def recommend_parameters(
        self,
        financial_data: pd.DataFrame,
        wacc: Optional[float] = None,
        industry_type: Optional[IndustryType] = None,
        company_name: Optional[str] = None,
        has_disposal: bool = False,
        disposal_ratio: float = 0.0
    ) -> DCFParameters:
        """
        推薦 DCF 參數
        
        Args:
            financial_data: 財務數據（多期）
            wacc: WACC 值（如已計算）
            industry_type: 產業類型
            company_name: 公司名稱
            has_disposal: 是否有資產處分
            disposal_ratio: 處分收益占比
        
        Returns:
            完整參數推薦
        """
        logger.info(f"🚀 開始為 {company_name or '公司'} 推薦 DCF 參數...")
        
        reasoning = {}
        
        # 1. 推薦折現率
        if wacc is not None:
            discount_rate = wacc
            reasoning['discount_rate'] = f"使用計算的 WACC: {wacc:.2%}"
        else:
            discount_rate, dr_reason = self._recommend_discount_rate(
                financial_data, industry_type
            )
            reasoning['discount_rate'] = dr_reason
        
        # 2. 分析歷史成長率
        growth_analysis = self._analyze_growth_rates(financial_data)
        
        # 3. 推薦永續成長率
        terminal_growth, tg_reason = self._recommend_terminal_growth(
            growth_analysis, industry_type
        )
        reasoning['terminal_growth'] = tg_reason
        
        # 4. 推薦預測期間
        forecast_periods, fp_reason = self._recommend_forecast_periods(
            financial_data, industry_type, growth_analysis
        )
        reasoning['forecast_periods'] = fp_reason
        
        # 5. 評估風險並推薦安全邊際
        risk_level = self._assess_risk_level(
            financial_data, growth_analysis, has_disposal, disposal_ratio
        )
        safety_margin, sm_reason = self._recommend_safety_margin(
            risk_level, industry_type
        )
        reasoning['safety_margin'] = sm_reason
        
        # 6. 推薦現金流類型
        cash_flow_type, cf_reason = self._recommend_cash_flow_type(
            financial_data, has_disposal
        )
        reasoning['cash_flow_type'] = cf_reason
        
        # 7. 評估信心水準
        confidence = self._assess_confidence(
            financial_data, growth_analysis, risk_level
        )
        
        # 8. 生成替代情境
        scenarios = self._generate_scenarios(
            discount_rate, terminal_growth, safety_margin
        )
        
        logger.info(f"✅ 參數推薦完成 (信心水準: {confidence})")
        
        return DCFParameters(
            discount_rate=discount_rate,
            terminal_growth_rate=terminal_growth,
            forecast_periods=forecast_periods,
            safety_margin=safety_margin,
            cash_flow_type=cash_flow_type,
            confidence_level=confidence,
            reasoning=reasoning,
            alternative_scenarios=scenarios
        )
    
    def _recommend_discount_rate(
        self,
        financial_data: pd.DataFrame,
        industry_type: Optional[IndustryType]
    ) -> Tuple[float, str]:
        """
        推薦折現率（當 WACC 未提供時）
        
        Returns:
            (折現率, 推薦理由)
        """
        # 基礎折現率（市場平均）
        base_rate = 0.10  # 10%
        
        # 根據產業調整
        if industry_type == IndustryType.TECH:
            rate = 0.12
            reason = "科技產業風險較高，建議折現率 12%"
        elif industry_type == IndustryType.FINANCIAL:
            rate = 0.08
            reason = "金融產業槓桿高但穩定，建議折現率 8%"
        elif industry_type == IndustryType.MATURE:
            rate = 0.09
            reason = "成熟產業風險較低，建議折現率 9%"
        else:
            rate = base_rate
            reason = f"使用市場平均折現率 {base_rate:.0%}"
        
        logger.info(f"  折現率: {rate:.2%} - {reason}")
        return rate, reason
    
    def _analyze_growth_rates(
        self,
        financial_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        分析歷史成長率
        
        Returns:
            成長率分析結果
        """
        logger.debug("  分析歷史成長率...")
        
        # 嘗試找到營收或淨利欄位
        revenue_fields = ['Revenue', 'revenue', '營收', '營業收入']
        income_fields = ['NetIncome', 'net_income', 'ProfitBeforeTax', '稅前淨利', '本期淨利']
        
        revenue_series = None
        income_series = None
        
        for field in revenue_fields:
            if field in financial_data.columns:
                revenue_series = financial_data[field].dropna()
                break
        
        for field in income_fields:
            if field in financial_data.columns:
                income_series = financial_data[field].dropna()
                break
        
        analysis = {
            'has_revenue': revenue_series is not None,
            'has_income': income_series is not None,
            'revenue_growth_rates': [],
            'income_growth_rates': [],
            'avg_revenue_growth': 0.0,
            'avg_income_growth': 0.0,
            'volatility': 'unknown',
        }
        
        # 計算營收成長率
        if revenue_series is not None and len(revenue_series) >= 2:
            growth_rates = []
            for i in range(1, len(revenue_series)):
                if revenue_series.iloc[i] > 0:
                    growth = (revenue_series.iloc[i-1] - revenue_series.iloc[i]) / revenue_series.iloc[i]
                    growth_rates.append(growth)
            
            if growth_rates:
                analysis['revenue_growth_rates'] = growth_rates
                analysis['avg_revenue_growth'] = np.mean(growth_rates)
                
                # 評估波動性
                std = np.std(growth_rates)
                if std < 0.1:
                    analysis['volatility'] = 'low'
                elif std < 0.2:
                    analysis['volatility'] = 'medium'
                else:
                    analysis['volatility'] = 'high'
                
                logger.info(
                    f"    營收年均成長: {analysis['avg_revenue_growth']:.1%}, "
                    f"波動性: {analysis['volatility']}"
                )
        
        # 計算淨利成長率
        if income_series is not None and len(income_series) >= 2:
            growth_rates = []
            for i in range(1, len(income_series)):
                if income_series.iloc[i] > 0:
                    growth = (income_series.iloc[i-1] - income_series.iloc[i]) / income_series.iloc[i]
                    growth_rates.append(growth)
            
            if growth_rates:
                analysis['income_growth_rates'] = growth_rates
                analysis['avg_income_growth'] = np.mean(growth_rates)
        
        return analysis
    
    def _recommend_terminal_growth(
        self,
        growth_analysis: Dict[str, Any],
        industry_type: Optional[IndustryType]
    ) -> Tuple[float, str]:
        """
        推薦永續成長率
        
        Returns:
            (永續成長率, 推薦理由)
        """
        # 基礎值（GDP 成長率）
        gdp_growth = 0.025  # 2.5%
        
        # 從產業預設值開始
        if industry_type and industry_type in self.INDUSTRY_DEFAULTS:
            base_growth = self.INDUSTRY_DEFAULTS[industry_type]['terminal_growth']
        else:
            base_growth = 0.025
        
        # 根據歷史成長率調整
        if growth_analysis['has_revenue'] and growth_analysis['avg_revenue_growth'] > 0:
            historical_growth = growth_analysis['avg_revenue_growth']
            
            # 永續成長率不應超過 GDP 成長率太多
            if historical_growth > 0.10:
                # 高成長公司逐漸收斂
                adjusted_growth = min(0.04, base_growth * 1.2)
                reason = f"歷史高成長({historical_growth:.1%})，預期逐漸收斂至 {adjusted_growth:.1%}"
            elif historical_growth > 0.05:
                adjusted_growth = min(0.035, base_growth * 1.1)
                reason = f"歷史中等成長({historical_growth:.1%})，採用 {adjusted_growth:.1%}"
            else:
                adjusted_growth = max(0.02, base_growth)
                reason = f"歷史低成長({historical_growth:.1%})，採用保守 {adjusted_growth:.1%}"
        else:
            adjusted_growth = base_growth
            reason = f"採用產業預設永續成長率 {base_growth:.1%}"
        
        # 確保在合理範圍
        final_growth = max(0.01, min(0.05, adjusted_growth))
        
        logger.info(f"  永續成長率: {final_growth:.2%} - {reason}")
        return final_growth, reason
    
    def _recommend_forecast_periods(
        self,
        financial_data: pd.DataFrame,
        industry_type: Optional[IndustryType],
        growth_analysis: Dict[str, Any]
    ) -> Tuple[int, str]:
        """
        推薦預測期間
        
        Returns:
            (預測年數, 推薦理由)
        """
        # 預設值
        if industry_type and industry_type in self.INDUSTRY_DEFAULTS:
            base_periods = self.INDUSTRY_DEFAULTS[industry_type]['forecast_periods']
        else:
            base_periods = 5
        
        # 根據波動性調整
        volatility = growth_analysis.get('volatility', 'unknown')
        
        if volatility == 'high':
            periods = max(3, base_periods - 2)
            reason = f"高波動性，縮短預測期間至 {periods} 年"
        elif volatility == 'low' and industry_type == IndustryType.MATURE:
            periods = min(10, base_periods + 2)
            reason = f"低波動成熟產業，延長預測期間至 {periods} 年"
        else:
            periods = base_periods
            reason = f"採用標準預測期間 {periods} 年"
        
        logger.info(f"  預測期間: {periods} 年 - {reason}")
        return periods, reason
    
    def _assess_risk_level(
        self,
        financial_data: pd.DataFrame,
        growth_analysis: Dict[str, Any],
        has_disposal: bool,
        disposal_ratio: float
    ) -> RiskLevel:
        """評估風險等級"""
        risk_score = 0
        
        # 波動性風險
        volatility = growth_analysis.get('volatility', 'unknown')
        if volatility == 'high':
            risk_score += 2
        elif volatility == 'medium':
            risk_score += 1
        
        # 資產處分風險
        if has_disposal and disposal_ratio > 0.20:
            risk_score += 2
        elif has_disposal and disposal_ratio > 0.10:
            risk_score += 1
        
        # 數據完整性風險
        if len(financial_data) < 3:
            risk_score += 1
        
        # 評估等級
        if risk_score >= 4:
            level = RiskLevel.HIGH
        elif risk_score >= 2:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        logger.info(f"  風險評估: {level.value.upper()} (score={risk_score})")
        return level
    
    def _recommend_safety_margin(
        self,
        risk_level: RiskLevel,
        industry_type: Optional[IndustryType]
    ) -> Tuple[float, str]:
        """
        推薦安全邊際
        
        Returns:
            (安全邊際比例, 推薦理由)
        """
        # 基礎安全邊際
        if industry_type and industry_type in self.INDUSTRY_DEFAULTS:
            base_margin = self.INDUSTRY_DEFAULTS[industry_type]['safety_margin']
        else:
            base_margin = 0.25  # 25%
        
        # 根據風險調整
        if risk_level == RiskLevel.HIGH:
            margin = min(0.40, base_margin + 0.10)
            reason = f"高風險，建議安全邊際 {margin:.0%}"
        elif risk_level == RiskLevel.MEDIUM:
            margin = base_margin
            reason = f"中等風險，建議安全邊際 {margin:.0%}"
        else:
            margin = max(0.15, base_margin - 0.05)
            reason = f"低風險，建議安全邊際 {margin:.0%}"
        
        logger.info(f"  安全邊際: {margin:.0%} - {reason}")
        return margin, reason
    
    def _recommend_cash_flow_type(
        self,
        financial_data: pd.DataFrame,
        has_disposal: bool
    ) -> Tuple[str, str]:
        """
        推薦現金流類型
        
        Returns:
            (現金流類型, 推薦理由)
        """
        # 檢查是否有現金流數據
        fcf_fields = ['FreeCashFlow', 'free_cash_flow', '自由現金流']
        has_fcf = any(field in financial_data.columns for field in fcf_fields)
        
        if has_disposal:
            cash_flow_type = "FCF"
            reason = "有資產處分，建議使用自由現金流 (FCF) 以排除非經常性項目"
        elif has_fcf:
            cash_flow_type = "FCF"
            reason = "數據完整，建議使用自由現金流 (FCF)"
        else:
            cash_flow_type = "ECF"
            reason = "數據有限，可考慮使用盈餘現金流 (ECF)"
        
        logger.info(f"  現金流類型: {cash_flow_type} - {reason}")
        return cash_flow_type, reason
    
    def _assess_confidence(
        self,
        financial_data: pd.DataFrame,
        growth_analysis: Dict[str, Any],
        risk_level: RiskLevel
    ) -> str:
        """評估推薦信心水準"""
        score = 0
        
        # 數據完整性
        if len(financial_data) >= 5:
            score += 2
        elif len(financial_data) >= 3:
            score += 1
        
        # 成長穩定性
        if growth_analysis.get('volatility') == 'low':
            score += 2
        elif growth_analysis.get('volatility') == 'medium':
            score += 1
        
        # 風險等級
        if risk_level == RiskLevel.LOW:
            score += 1
        
        if score >= 4:
            return 'high'
        elif score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_scenarios(
        self,
        discount_rate: float,
        terminal_growth: float,
        safety_margin: float
    ) -> Dict[str, Dict[str, float]]:
        """生成替代情境（樂觀/悲觀）"""
        scenarios = {
            'optimistic': {
                'discount_rate': max(0.06, discount_rate - 0.01),
                'terminal_growth': min(0.05, terminal_growth + 0.01),
                'safety_margin': max(0.10, safety_margin - 0.05),
            },
            'pessimistic': {
                'discount_rate': min(0.20, discount_rate + 0.02),
                'terminal_growth': max(0.01, terminal_growth - 0.01),
                'safety_margin': min(0.50, safety_margin + 0.10),
            },
        }
        
        return scenarios
    
    def generate_report(self, params: DCFParameters) -> str:
        """
        生成參數推薦報告
        
        Args:
            params: 推薦參數
        
        Returns:
            格式化報告
        """
        report = []
        report.append("="*70)
        report.append("📊 DCF 參數推薦報告")
        report.append("="*70)
        
        report.append(f"\n信心水準: {params.confidence_level.upper()}")
        report.append("")
        
        report.append("推薦參數:")
        report.append(f"  • 折現率 (WACC): {params.discount_rate:.2%}")
        report.append(f"  • 永續成長率: {params.terminal_growth_rate:.2%}")
        report.append(f"  • 預測期間: {params.forecast_periods} 年")
        report.append(f"  • 安全邊際: {params.safety_margin:.0%}")
        report.append(f"  • 現金流類型: {params.cash_flow_type}")
        report.append("")
        
        report.append("推薦理由:")
        for key, reason in params.reasoning.items():
            report.append(f"  • {reason}")
        report.append("")
        
        report.append("替代情境:")
        report.append("\n  樂觀情境:")
        for key, value in params.alternative_scenarios['optimistic'].items():
            if 'rate' in key or 'growth' in key:
                report.append(f"    - {key}: {value:.2%}")
            else:
                report.append(f"    - {key}: {value:.0%}")
        
        report.append("\n  悲觀情境:")
        for key, value in params.alternative_scenarios['pessimistic'].items():
            if 'rate' in key or 'growth' in key:
                report.append(f"    - {key}: {value:.2%}")
            else:
                report.append(f"    - {key}: {value:.0%}")
        
        report.append("")
        report.append("="*70)
        
        return "\n".join(report)


def recommend_dcf_parameters(
    financial_data: pd.DataFrame,
    wacc: Optional[float] = None,
    industry: Optional[str] = None,
    company_name: Optional[str] = None
) -> DCFParameters:
    """
    便捷函數：推薦 DCF 參數
    
    Args:
        financial_data: 財務數據
        wacc: WACC（可選）
        industry: 產業名稱
        company_name: 公司名稱
    
    Returns:
        參數推薦結果
    """
    # 映射產業類型
    industry_map = {
        '半導體': IndustryType.TECH,
        '電子': IndustryType.TECH,
        '科技': IndustryType.TECH,
        '金融': IndustryType.FINANCIAL,
        '銀行': IndustryType.FINANCIAL,
        '食品': IndustryType.MATURE,
        '紡織': IndustryType.MATURE,
        '鋼鐵': IndustryType.CYCLICAL,
        '營建': IndustryType.CYCLICAL,
    }
    
    industry_type = None
    if industry:
        for key, value in industry_map.items():
            if key in industry:
                industry_type = value
                break
    
    recommender = DCFParameterRecommender()
    return recommender.recommend_parameters(
        financial_data=financial_data,
        wacc=wacc,
        industry_type=industry_type,
        company_name=company_name
    )


if __name__ == '__main__':
    # 測試範例
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("🎯 DCF 參數推薦引擎測試")
    print("="*70)
    
    # 建立測試數據
    test_data = pd.DataFrame({
        'date': pd.date_range('2019-12-31', periods=5, freq='YE'),
        'Revenue': [100_000_000_000, 110_000_000_000, 121_000_000_000, 
                   133_000_000_000, 146_000_000_000],
        'NetIncome': [10_000_000_000, 11_000_000_000, 12_100_000_000,
                     13_310_000_000, 14_641_000_000],
    })
    
    # 反轉順序（最新在前）
    test_data = test_data.sort_values('date', ascending=False)
    
    print("\n測試數據:")
    print(test_data[['date', 'Revenue', 'NetIncome']])
    
    # 推薦參數
    recommender = DCFParameterRecommender()
    params = recommender.recommend_parameters(
        financial_data=test_data,
        wacc=0.095,
        industry_type=IndustryType.GROWTH,
        company_name="測試公司"
    )
    
    # 印出報告
    print("\n" + recommender.generate_report(params))
