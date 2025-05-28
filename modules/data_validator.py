"""
數據品質驗證模組

此模組提供全面的財務數據品質驗證功能，包括：
1. 基本數據存在性驗證
2. 數據合理性驗證
3. 數據一致性驗證
4. 異常值檢測
5. 詳細驗證報告

主要功能：
- validate_financial_data(): 主要驗證入口點
- ValidationResult: 驗證結果數據類別
- DataQualityMetrics: 數據品質指標類別
- generate_quality_report(): 生成品質報告

技術特色：
- 多層次驗證策略
- 自動異常檢測
- 詳細錯誤診斷
- 可配置驗證規則
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class ValidationLevel(Enum):
    """驗證級別"""
    ERROR = "error"      # 嚴重錯誤，會阻止後續處理
    WARNING = "warning"  # 警告，可能影響準確性
    INFO = "info"        # 資訊，僅供參考


@dataclass
class ValidationIssue:
    """驗證問題記錄"""
    level: ValidationLevel
    field: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """驗證結果"""
    stock_code: str
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    quality_score: float = 0.0  # 0-100 的品質分數
    completeness: float = 0.0   # 數據完整性
    consistency: float = 0.0    # 數據一致性
    reliability: float = 0.0    # 數據可靠性


@dataclass
class DataQualityMetrics:
    """數據品質指標"""
    required_fields_present: int
    total_required_fields: int
    numerical_outliers: int
    logical_inconsistencies: int
    date_anomalies: int
    zero_or_negative_issues: int


class FinancialDataValidator:
    """財務數據驗證器"""
    
    def __init__(self):
        # 必需欄位定義
        self.required_basic_fields = [
            'net_income_parent', 'capex', 'depreciation', 'shares_outstanding'
        ]
        
        self.required_calculation_fields = [
            'ar_t0', 'inv_t0', 'ap_t0',  # 營運資金計算需要
            'ar_t1', 'inv_t1', 'ap_t1'
        ]
        
        # 合理範圍定義
        self.reasonable_ranges = {
            'eps_finmind': (-1000, 1000),      # EPS 範圍
            'roe': (-1, 5),                    # ROE 範圍 (-100% 到 500%)
            'gross_profit_margin': (-1, 1),   # 毛利率範圍
            'operating_income_margin': (-1, 1), # 營業利益率範圍
            'net_profit_margin': (-1, 1),     # 淨利率範圍
            'depreciation': (0, float('inf')), # 折舊不應為負
            'capex': (0, float('inf')),       # 資本支出通常為正
        }
        
        # 異常檢測閾值
        self.outlier_thresholds = {
            'z_score': 3.0,     # Z-score 閾值
            'iqr_factor': 1.5,  # IQR 因子
        }

    def validate_financial_data(self, stock_code: str, financial_data: Dict[str, Any]) -> ValidationResult:
        """
        驗證財務數據品質
        
        Args:
            stock_code: 股票代碼
            financial_data: 財務數據字典
            
        Returns:
            ValidationResult: 驗證結果
        """
        result = ValidationResult(stock_code=stock_code, is_valid=True)
        
        # 1. 基本存在性驗證
        self._validate_basic_presence(financial_data, result)
        
        # 2. 數據類型驗證
        self._validate_data_types(financial_data, result)
        
        # 3. 數值合理性驗證
        self._validate_numerical_reasonableness(financial_data, result)
        
        # 4. 邏輯一致性驗證
        self._validate_logical_consistency(financial_data, result)
        
        # 5. 時間序列驗證
        self._validate_time_series(financial_data, result)
        
        # 6. 計算品質指標
        self._calculate_quality_metrics(financial_data, result)
        
        # 7. 決定最終驗證狀態
        self._determine_validation_status(result)
        
        return result

    def _validate_basic_presence(self, data: Dict[str, Any], result: ValidationResult):
        """驗證基本欄位存在性"""
        all_required = self.required_basic_fields + self.required_calculation_fields
        
        for field in all_required:
            if field not in data or data[field] is None:
                level = ValidationLevel.ERROR if field in self.required_basic_fields else ValidationLevel.WARNING
                result.issues.append(ValidationIssue(
                    level=level,
                    field=field,
                    message=f"欄位 '{field}' 缺失或為空值"
                ))

    def _validate_data_types(self, data: Dict[str, Any], result: ValidationResult):
        """驗證數據類型"""
        numerical_fields = [
            'net_income_parent', 'capex', 'depreciation', 'shares_outstanding',
            'ar_t0', 'inv_t0', 'ap_t0', 'ar_t1', 'inv_t1', 'ap_t1',
            'eps_finmind', 'current_market_price'
        ]
        
        for field in numerical_fields:
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    result.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        field=field,
                        message=f"欄位 '{field}' 應為數值類型，實際值: {data[field]}",
                        details={'actual_type': type(data[field]).__name__}
                    ))

    def _validate_numerical_reasonableness(self, data: Dict[str, Any], result: ValidationResult):
        """驗證數值合理性"""
        for field, (min_val, max_val) in self.reasonable_ranges.items():
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    if not (min_val <= value <= max_val):
                        result.issues.append(ValidationIssue(
                            level=ValidationLevel.WARNING,
                            field=field,
                            message=f"欄位 '{field}' 值超出合理範圍 [{min_val}, {max_val}]，實際值: {value}",
                            details={'value': value, 'range': [min_val, max_val]}
                        ))
                except (ValueError, TypeError):
                    pass  # 類型錯誤已在前面檢查

        # 檢查負值情況
        positive_fields = ['shares_outstanding', 'current_market_price']
        for field in positive_fields:
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    if value <= 0:
                        result.issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            field=field,
                            message=f"欄位 '{field}' 應為正值，實際值: {value}",
                            details={'value': value}
                        ))
                except (ValueError, TypeError):
                    pass

    def _validate_logical_consistency(self, data: Dict[str, Any], result: ValidationResult):
        """驗證邏輯一致性"""
        # 檢查營運資金相關欄位的一致性
        wc_fields_t0 = ['ar_t0', 'inv_t0', 'ap_t0']
        wc_fields_t1 = ['ar_t1', 'inv_t1', 'ap_t1']
        
        # 檢查 t0 和 t1 資料的一致性
        t0_available = sum(1 for field in wc_fields_t0 if field in data and data[field] is not None)
        t1_available = sum(1 for field in wc_fields_t1 if field in data and data[field] is not None)
        
        if t0_available > 0 and t1_available > 0 and t0_available != t1_available:
            result.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                field="working_capital",
                message=f"營運資金 T0 期與 T-1 期欄位完整性不一致 (T0: {t0_available}/3, T-1: {t1_available}/3)",
                details={'t0_count': t0_available, 't1_count': t1_available}
            ))

        # 檢查 EPS 與淨利的一致性（如果都存在）
        if all(field in data and data[field] is not None for field in ['eps_finmind', 'net_income_parent', 'shares_outstanding']):
            try:
                eps = float(data['eps_finmind'])
                net_income = float(data['net_income_parent'])
                shares = float(data['shares_outstanding'])
                
                calculated_eps = net_income / shares
                eps_diff_ratio = abs(eps - calculated_eps) / abs(calculated_eps) if calculated_eps != 0 else float('inf')
                
                if eps_diff_ratio > 0.1:  # 10% 差異閾值
                    result.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        field="eps_consistency",
                        message=f"EPS 與淨利/股本計算不一致，報表 EPS: {eps:.4f}, 計算 EPS: {calculated_eps:.4f}",
                        details={
                            'reported_eps': eps,
                            'calculated_eps': calculated_eps,
                            'difference_ratio': eps_diff_ratio
                        }
                    ))
            except (ValueError, TypeError, ZeroDivisionError):
                pass

    def _validate_time_series(self, data: Dict[str, Any], result: ValidationResult):
        """驗證時間序列數據"""
        date_fields = ['bs_report_date_t0', 'bs_report_date_t1', 'cf_report_date', 'is_report_date']
        available_dates = {}
        
        for field in date_fields:
            if field in data and data[field] is not None:
                try:
                    available_dates[field] = pd.to_datetime(data[field])
                except (ValueError, TypeError):
                    result.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        field=field,
                        message=f"日期欄位 '{field}' 格式無效: {data[field]}",
                        details={'value': data[field]}
                    ))

        # 檢查日期邏輯性
        if 'bs_report_date_t0' in available_dates and 'bs_report_date_t1' in available_dates:
            if available_dates['bs_report_date_t0'] <= available_dates['bs_report_date_t1']:
                result.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field="date_logic",
                    message="資產負債表 T0 期日期應晚於 T-1 期日期",
                    details={
                        't0_date': available_dates['bs_report_date_t0'].strftime('%Y-%m-%d'),
                        't1_date': available_dates['bs_report_date_t1'].strftime('%Y-%m-%d')
                    }
                ))

    def _calculate_quality_metrics(self, data: Dict[str, Any], result: ValidationResult):
        """計算品質指標"""
        # 計算完整性
        all_required = self.required_basic_fields + self.required_calculation_fields
        present_fields = sum(1 for field in all_required if field in data and data[field] is not None)
        result.completeness = (present_fields / len(all_required)) * 100

        # 計算一致性（基於邏輯錯誤數量）
        consistency_issues = len([issue for issue in result.issues if 
                                 issue.level == ValidationLevel.WARNING and 
                                 'consistency' in issue.message.lower()])
        result.consistency = max(0, 100 - consistency_issues * 20)

        # 計算可靠性（基於嚴重錯誤數量）
        error_issues = len([issue for issue in result.issues if issue.level == ValidationLevel.ERROR])
        result.reliability = max(0, 100 - error_issues * 30)

        # 整體品質分數
        result.quality_score = (result.completeness * 0.4 + 
                               result.consistency * 0.3 + 
                               result.reliability * 0.3)

    def _determine_validation_status(self, result: ValidationResult):
        """決定驗證狀態"""
        error_count = len([issue for issue in result.issues if issue.level == ValidationLevel.ERROR])
        critical_fields_missing = any(
            issue.field in self.required_basic_fields and issue.level == ValidationLevel.ERROR
            for issue in result.issues
        )
        
        # 如果有嚴重錯誤或關鍵欄位缺失，則驗證失敗
        result.is_valid = error_count == 0 and not critical_fields_missing

    def generate_quality_report(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """
        生成數據品質報告
        
        Args:
            validation_results: 驗證結果列表
            
        Returns:
            品質報告字典
        """
        total_stocks = len(validation_results)
        valid_stocks = sum(1 for result in validation_results if result.is_valid)
        
        # 統計問題類型
        issue_stats = {}
        for result in validation_results:
            for issue in result.issues:
                key = f"{issue.level.value}_{issue.field}"
                issue_stats[key] = issue_stats.get(key, 0) + 1

        # 計算平均品質指標
        avg_quality = np.mean([result.quality_score for result in validation_results])
        avg_completeness = np.mean([result.completeness for result in validation_results])
        avg_consistency = np.mean([result.consistency for result in validation_results])
        avg_reliability = np.mean([result.reliability for result in validation_results])

        return {
            'summary': {
                'total_stocks': total_stocks,
                'valid_stocks': valid_stocks,
                'validation_rate': (valid_stocks / total_stocks * 100) if total_stocks > 0 else 0,
                'avg_quality_score': avg_quality,
                'avg_completeness': avg_completeness,
                'avg_consistency': avg_consistency,
                'avg_reliability': avg_reliability
            },
            'issue_statistics': issue_stats,
            'top_issues': sorted(issue_stats.items(), key=lambda x: x[1], reverse=True)[:10],
            'quality_distribution': {
                'excellent': sum(1 for r in validation_results if r.quality_score >= 90),
                'good': sum(1 for r in validation_results if 70 <= r.quality_score < 90),
                'fair': sum(1 for r in validation_results if 50 <= r.quality_score < 70),
                'poor': sum(1 for r in validation_results if r.quality_score < 50)
            }
        }

    def validate_dcf_inputs(self, stock_code: str, dcf_inputs: Dict[str, Any]) -> ValidationResult:
        """
        專門驗證 DCF 估值輸入參數的品質
        
        Args:
            stock_code: 股票代碼
            dcf_inputs: DCF 輸入參數
            
        Returns:
            ValidationResult: 驗證結果
        """
        result = ValidationResult(stock_code=stock_code, is_valid=True)
        
        # DCF 必需參數
        required_dcf_fields = [
            'fcf_eps', 'discount_rate', 'short_term_growth_rate', 
            'terminal_growth_rate', 'projection_years'
        ]
        
        for field in required_dcf_fields:
            if field not in dcf_inputs or dcf_inputs[field] is None:
                result.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=field,
                    message=f"DCF 參數 '{field}' 缺失"
                ))

        # 驗證 DCF 參數合理性
        if 'discount_rate' in dcf_inputs and dcf_inputs['discount_rate'] is not None:
            discount_rate = dcf_inputs['discount_rate']
            if not 0.01 <= discount_rate <= 0.30:  # 1% 到 30% 的合理範圍
                result.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field='discount_rate',
                    message=f"折現率 {discount_rate:.2%} 超出合理範圍 [1%, 30%]"
                ))

        if 'terminal_growth_rate' in dcf_inputs and dcf_inputs['terminal_growth_rate'] is not None:
            terminal_growth = dcf_inputs['terminal_growth_rate']
            if not -0.05 <= terminal_growth <= 0.10:  # -5% 到 10% 的合理範圍
                result.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field='terminal_growth_rate',
                    message=f"永續成長率 {terminal_growth:.2%} 超出合理範圍 [-5%, 10%]"
                ))

        # 驗證折現率與永續成長率的關係
        if (dcf_inputs.get('discount_rate') is not None and 
            dcf_inputs.get('terminal_growth_rate') is not None):
            discount_rate = dcf_inputs['discount_rate']
            terminal_growth = dcf_inputs['terminal_growth_rate']
            
            if discount_rate <= terminal_growth:
                result.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field='dcf_rates_relationship',
                    message=f"折現率 ({discount_rate:.2%}) 必須大於永續成長率 ({terminal_growth:.2%})"
                ))

        # 計算 DCF 品質分數
        error_count = len([issue for issue in result.issues if issue.level == ValidationLevel.ERROR])
        warning_count = len([issue for issue in result.issues if issue.level == ValidationLevel.WARNING])
        
        result.quality_score = max(0, 100 - error_count * 40 - warning_count * 10)
        result.is_valid = error_count == 0
        
        return result
