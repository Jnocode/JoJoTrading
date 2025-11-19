"""
資產處分偵測模組

自動偵測財務報表中的一次性收益，特別是資產處分收益，
避免這些非經常性項目影響 DCF 估值的準確性。

偵測項目：
1. 資產處分收益/損失
2. 投資收益異常
3. 業外收入異常
4. 特殊項目收入

Author: jojo_trading team
Date: 2025-11-19
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DisposalDetectionResult:
    """資產處分偵測結果"""
    has_disposal: bool
    disposal_amount: float
    disposal_items: List[Dict[str, Any]]
    adjusted_income: float
    original_income: float
    adjustment_ratio: float
    confidence_level: str
    detection_details: Dict[str, Any]


class AssetDisposalDetector:
    """
    資產處分偵測器
    
    偵測財務報表中的一次性資產處分收益，並提供調整建議。
    """
    
    # 可能的資產處分相關欄位名稱
    DISPOSAL_FIELDS = [
        # 中文
        '處分資產利益', '處分資產損失', '資產處分損益', '出售資產利益',
        '出售資產損失', '非流動資產處分損益', '固定資產處分損益',
        # 英文
        'GainLossOnDisposalOfAssets', 'DisposalGain', 'DisposalLoss',
        'GainOnSaleOfAssets', 'LossOnSaleOfAssets',
        'NonOperatingIncome', 'OtherIncome', 'ExtraordinaryItems',
    ]
    
    # 投資收益相關欄位
    INVESTMENT_FIELDS = [
        '投資收益', '金融資產評價利益', '採用權益法認列之關聯企業及合資損益之份額',
        'InvestmentIncome', 'GainOnFinancialAssets', 'EquityMethodInvestment',
    ]
    
    def __init__(
        self,
        disposal_threshold: float = 0.10,  # 處分收益占稅前淨利 10%
        volatility_threshold: float = 2.0,  # 標準差倍數
        min_data_points: int = 3
    ):
        """
        初始化資產處分偵測器
        
        Args:
            disposal_threshold: 處分收益重要性門檻（占稅前淨利比例）
            volatility_threshold: 波動性異常門檻（標準差倍數）
            min_data_points: 最小數據點數量
        """
        self.disposal_threshold = disposal_threshold
        self.volatility_threshold = volatility_threshold
        self.min_data_points = min_data_points
        
        logger.info(
            f"🔍 資產處分偵測器已初始化 "
            f"(threshold={disposal_threshold:.0%}, "
            f"volatility={volatility_threshold}σ)"
        )
    
    def detect_disposal_in_period(
        self,
        period_data: pd.Series,
        period_label: str = "當期"
    ) -> Dict[str, Any]:
        """
        偵測單一期間的資產處分情況
        
        Args:
            period_data: 單期財務數據
            period_label: 期間標籤
        
        Returns:
            偵測結果字典
        """
        logger.debug(f"🔍 偵測 {period_label} 的資產處分...")
        
        disposal_found = {}
        total_disposal = 0
        
        # 1. 檢查明確的處分收益欄位
        for field in self.DISPOSAL_FIELDS:
            if field in period_data.index:
                value = float(period_data[field])
                if abs(value) > 0:
                    disposal_found[field] = value
                    total_disposal += value
                    logger.info(f"  ✓ 找到 {field}: {value:,.0f}")
        
        # 2. 檢查投資收益異常
        for field in self.INVESTMENT_FIELDS:
            if field in period_data.index:
                value = float(period_data[field])
                if abs(value) > 0:
                    disposal_found[f"{field} (投資)"] = value
                    logger.debug(f"  ℹ️ 投資收益 {field}: {value:,.0f}")
        
        return {
            'disposal_items': disposal_found,
            'total_disposal': total_disposal,
            'has_disposal': len(disposal_found) > 0,
            'period': period_label
        }
    
    def detect_from_financial_data(
        self,
        financial_data: pd.DataFrame,
        income_field: str = 'ProfitBeforeTax'
    ) -> DisposalDetectionResult:
        """
        從完整財務數據偵測資產處分
        
        Args:
            financial_data: 財務報表數據（多期）
            income_field: 稅前淨利欄位名稱
        
        Returns:
            完整偵測結果
        """
        logger.info("🔍 開始資產處分偵測...")
        
        if financial_data.empty:
            logger.warning("⚠️  財務數據為空")
            return self._create_empty_result()
        
        # 確保數據按日期排序（最新在前）
        if 'date' in financial_data.columns:
            financial_data = financial_data.sort_values('date', ascending=False)
        
        # 1. 逐期偵測
        all_disposal_items = []
        total_disposal = 0
        
        for idx, row in financial_data.head(self.min_data_points).iterrows():
            period = row.get('date', f'Period {idx}')
            result = self.detect_disposal_in_period(row, str(period))
            
            if result['has_disposal']:
                all_disposal_items.append(result)
                total_disposal += result['total_disposal']
        
        # 2. 取得最新期間的稅前淨利
        latest_data = financial_data.iloc[0]
        
        # 嘗試不同的淨利欄位名稱
        income_fields = [
            income_field, 'ProfitBeforeTax', 'NetIncome', 'EBT',
            '稅前淨利', '本期淨利', '稅前損益'
        ]
        
        original_income = 0
        found_income_field = None
        for field in income_fields:
            if field in latest_data.index:
                original_income = float(latest_data[field])
                found_income_field = field
                logger.info(f"  使用淨利欄位: {field} = {original_income:,.0f}")
                break
        
        if original_income == 0:
            logger.warning("⚠️  未找到有效的淨利數據")
            return self._create_empty_result()
        
        # 3. 計算調整後淨利
        # 只調整最新期間的處分收益
        latest_disposal = (all_disposal_items[0]['total_disposal'] 
                          if all_disposal_items else 0)
        
        adjusted_income = original_income - latest_disposal
        adjustment_ratio = (latest_disposal / original_income 
                          if original_income != 0 else 0)
        
        # 4. 判斷是否重要
        has_significant_disposal = (
            abs(adjustment_ratio) >= self.disposal_threshold and
            len(all_disposal_items) > 0
        )
        
        # 5. 信心水準評估
        confidence = self._assess_confidence(
            disposal_amount=latest_disposal,
            adjustment_ratio=abs(adjustment_ratio),
            detection_count=len(all_disposal_items)
        )
        
        # 6. 組裝結果
        logger.info(
            f"✅ 偵測完成: "
            f"{'發現' if has_significant_disposal else '未發現'}重要資產處分 "
            f"(調整比例: {adjustment_ratio:.1%})"
        )
        
        return DisposalDetectionResult(
            has_disposal=has_significant_disposal,
            disposal_amount=latest_disposal,
            disposal_items=all_disposal_items,
            adjusted_income=adjusted_income,
            original_income=original_income,
            adjustment_ratio=adjustment_ratio,
            confidence_level=confidence,
            detection_details={
                'income_field_used': found_income_field,
                'periods_analyzed': len(financial_data),
                'disposal_periods': len(all_disposal_items),
                'threshold_used': self.disposal_threshold,
            }
        )
    
    def detect_volatility_anomaly(
        self,
        financial_data: pd.DataFrame,
        field: str
    ) -> Dict[str, Any]:
        """
        偵測欄位值的異常波動
        
        Args:
            financial_data: 財務數據
            field: 要分析的欄位
        
        Returns:
            異常偵測結果
        """
        if field not in financial_data.columns:
            logger.warning(f"⚠️  欄位 '{field}' 不存在")
            return {'has_anomaly': False, 'reason': 'field_not_found'}
        
        values = financial_data[field].dropna()
        
        if len(values) < self.min_data_points:
            logger.warning(f"⚠️  數據點不足 ({len(values)} < {self.min_data_points})")
            return {'has_anomaly': False, 'reason': 'insufficient_data'}
        
        # 計算統計量
        mean_val = values.mean()
        std_val = values.std()
        latest_val = values.iloc[0]
        
        # Z-score
        z_score = (latest_val - mean_val) / std_val if std_val > 0 else 0
        
        # 判斷是否異常
        has_anomaly = abs(z_score) > self.volatility_threshold
        
        logger.info(
            f"  {field}: 最新={latest_val:,.0f}, 平均={mean_val:,.0f}, "
            f"標準差={std_val:,.0f}, Z-score={z_score:.2f}"
        )
        
        return {
            'has_anomaly': has_anomaly,
            'z_score': z_score,
            'latest_value': latest_val,
            'mean_value': mean_val,
            'std_value': std_val,
            'threshold': self.volatility_threshold,
            'field': field
        }
    
    def _assess_confidence(
        self,
        disposal_amount: float,
        adjustment_ratio: float,
        detection_count: int
    ) -> str:
        """
        評估偵測信心水準
        
        Returns:
            'high', 'medium', 'low'
        """
        # 高信心：明確找到處分欄位且金額重要
        if detection_count > 0 and adjustment_ratio >= self.disposal_threshold * 2:
            return 'high'
        
        # 中等信心：找到處分欄位但金額不太大
        if detection_count > 0 and adjustment_ratio >= self.disposal_threshold:
            return 'medium'
        
        # 低信心：金額小或僅透過波動偵測
        return 'low'
    
    def _create_empty_result(self) -> DisposalDetectionResult:
        """建立空結果"""
        return DisposalDetectionResult(
            has_disposal=False,
            disposal_amount=0.0,
            disposal_items=[],
            adjusted_income=0.0,
            original_income=0.0,
            adjustment_ratio=0.0,
            confidence_level='low',
            detection_details={'reason': 'no_data'}
        )
    
    def generate_report(self, result: DisposalDetectionResult) -> str:
        """
        生成偵測報告
        
        Args:
            result: 偵測結果
        
        Returns:
            格式化報告文字
        """
        report = []
        report.append("="*70)
        report.append("📊 資產處分偵測報告")
        report.append("="*70)
        
        if not result.has_disposal:
            report.append("\n✅ 未偵測到重要資產處分收益")
            return "\n".join(report)
        
        report.append(f"\n⚠️  偵測到資產處分收益")
        report.append(f"   信心水準: {result.confidence_level.upper()}")
        report.append("")
        
        report.append("原始數據:")
        report.append(f"  • 稅前淨利: {result.original_income:,.0f}")
        report.append(f"  • 處分收益: {result.disposal_amount:,.0f}")
        report.append(f"  • 調整比例: {result.adjustment_ratio:.1%}")
        report.append("")
        
        report.append("調整後數據:")
        report.append(f"  • 調整後淨利: {result.adjusted_income:,.0f}")
        report.append(f"  • 影響金額: {result.disposal_amount:,.0f}")
        report.append("")
        
        report.append("偵測明細:")
        for item in result.disposal_items:
            report.append(f"  • {item['period']}:")
            for field, amount in item['disposal_items'].items():
                report.append(f"    - {field}: {amount:,.0f}")
        
        report.append("")
        report.append("建議:")
        if result.adjustment_ratio > 0.20:
            report.append("  ⚠️  處分收益占比超過 20%，強烈建議使用調整後淨利進行估值")
        elif result.adjustment_ratio > 0.10:
            report.append("  ℹ️  處分收益占比超過 10%，建議使用調整後淨利進行估值")
        else:
            report.append("  ✓ 處分收益影響較小，可考慮是否調整")
        
        report.append("="*70)
        
        return "\n".join(report)


def detect_asset_disposal(
    financial_data: pd.DataFrame,
    income_field: str = 'ProfitBeforeTax'
) -> DisposalDetectionResult:
    """
    便捷函數：偵測資產處分
    
    Args:
        financial_data: 財務數據
        income_field: 淨利欄位名稱
    
    Returns:
        偵測結果
    """
    detector = AssetDisposalDetector()
    return detector.detect_from_financial_data(financial_data, income_field)


if __name__ == '__main__':
    # 測試範例
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("🔍 資產處分偵測器測試")
    print("="*70)
    
    # 建立測試數據
    test_data = pd.DataFrame({
        'date': pd.date_range('2021-12-31', periods=3, freq='Y'),
        'ProfitBeforeTax': [1_000_000_000, 1_100_000_000, 1_500_000_000],
        '處分資產利益': [0, 0, 300_000_000],
        'Revenue': [10_000_000_000, 11_000_000_000, 12_000_000_000],
    })
    
    # 反轉順序（最新在前）
    test_data = test_data.sort_values('date', ascending=False)
    
    print("\n測試數據:")
    print(test_data)
    
    # 執行偵測
    detector = AssetDisposalDetector()
    result = detector.detect_from_financial_data(test_data)
    
    # 印出報告
    print("\n" + detector.generate_report(result))
