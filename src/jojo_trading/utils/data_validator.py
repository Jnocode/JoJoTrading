"""
財務數據驗證器
提供數據完整性和準確性檢查
"""
from dataclasses import dataclass
from typing import List
from enum import Enum

class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    field: str
    message: str
    level: ValidationLevel

@dataclass
class ValidationResult:
    quality_score: float
    issues: List[ValidationIssue]
    is_valid: bool

class FinancialDataValidator:
    """財務數據驗證器"""
    
    def __init__(self):
        pass
    
    def validate_financial_data(self, stock_code, data):
        """驗證財務數據的完整性"""
        issues = []
        quality_score = 100.0
        
        # 基本數據存在性檢查
        if data is None or (hasattr(data, 'empty') and data.empty):
            issues.append(ValidationIssue(
                field="data",
                message="財務數據為空",
                level=ValidationLevel.ERROR
            ))
            return ValidationResult(quality_score=0.0, issues=issues, is_valid=False)
            
        if isinstance(data, dict) and len(data) == 0:
            issues.append(ValidationIssue(
                field="data", 
                message="財務數據字典為空",
                level=ValidationLevel.ERROR
            ))
            return ValidationResult(quality_score=0.0, issues=issues, is_valid=False)
        
        # 檢查必要欄位
        required_fields = ['revenue', 'net_income', 'total_equity', 'total_assets']
        missing_fields = []
        
        if isinstance(data, dict):
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
                    quality_score -= 20
                elif isinstance(data[field], list) and len(data[field]) < 3:
                    issues.append(ValidationIssue(
                        field=field,
                        message=f"{field} 數據點不足（少於3個年度）",
                        level=ValidationLevel.WARNING
                    ))
                    quality_score -= 10
        
        if missing_fields:
            issues.append(ValidationIssue(
                field="missing_fields",
                message=f"缺少必要欄位: {', '.join(missing_fields)}",
                level=ValidationLevel.ERROR
            ))
        
        # 確保質量分數不為負
        quality_score = max(0.0, quality_score)
        is_valid = quality_score >= 40.0 and len([i for i in issues if i.level == ValidationLevel.ERROR]) == 0
        
        return ValidationResult(
            quality_score=quality_score,
            issues=issues,
            is_valid=is_valid
        )
    
    def validate_dcf_inputs(self, stock_code, inputs):
        """驗證DCF輸入參數"""
        if inputs is None:
            return False
        required_fields = ['fcf_eps', 'discount_rate']
        if isinstance(inputs, dict):
            for field in required_fields:
                if field not in inputs or inputs[field] is None:
                    return False
        return True
