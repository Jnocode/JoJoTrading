"""
數據結構統一處理工具
處理不同格式的財務數據，確保測試和生產環境的一致性
"""

import logging
import pandas as pd
from typing import Union, List, Dict, Any, Optional, Tuple
from pathlib import Path

class DataStructureUnifier:
    """數據結構統一器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def normalize_financial_data(self, data: Any) -> Dict[str, Any]:
        """標準化財務數據格式"""
        try:
            if isinstance(data, dict):
                return self._normalize_dict_data(data)
            elif isinstance(data, list):
                return self._normalize_list_data(data)
            elif isinstance(data, pd.DataFrame):
                return self._normalize_dataframe_data(data)
            else:
                return self._normalize_scalar_data(data)
        except Exception as e:
            self.logger.error(f"數據標準化錯誤: {e}")
            return {}
    
    def _normalize_dict_data(self, data: Dict) -> Dict[str, Any]:
        """標準化字典格式數據"""
        normalized = {}
        
        # 處理自由現金流
        fcf = self._extract_free_cash_flow(data)
        if fcf:
            normalized['free_cash_flow'] = fcf
            
        # 處理其他財務指標
        for key, value in data.items():
            if key not in ['free_cash_flow', 'fcf']:
                normalized[key] = value
                
        return normalized
    
    def _extract_free_cash_flow(self, data: Dict) -> Optional[List[float]]:
        """從字典中提取自由現金流數據"""
        # 可能的 FCF 欄位名稱
        fcf_fields = [
            'free_cash_flow', 'fcf', 'operating_cash_flow',
            'cash_flow', 'free_cash_flows'
        ]
        
        for field in fcf_fields:
            if field in data:
                fcf_data = data[field]
                
                # 如果是列表，直接返回
                if isinstance(fcf_data, list):
                    return [float(x) for x in fcf_data if x is not None]
                
                # 如果是字典，嘗試提取年度數據
                if isinstance(fcf_data, dict):
                    for key in ['annual', 'yearly', 'values', 'data']:
                        if key in fcf_data:
                            values = fcf_data[key]
                            if isinstance(values, list):
                                return [float(x) for x in values if x is not None]
                
                # 如果是單個數值
                if isinstance(fcf_data, (int, float)):
                    return [float(fcf_data)]
        
        # 嘗試從現金流表中提取
        if 'cash_flow' in data:
            cash_flow = data['cash_flow']
            if isinstance(cash_flow, dict):
                for field in fcf_fields:
                    if field in cash_flow:
                        fcf_data = cash_flow[field]
                        if isinstance(fcf_data, list):
                            return [float(x) for x in fcf_data if x is not None]
        
        return None
    
    def _normalize_list_data(self, data: List) -> Dict[str, Any]:
        """標準化列表格式數據"""
        return {
            'free_cash_flow': [float(x) for x in data if x is not None],
            'data_type': 'list',
            'source_format': 'list'
        }
    
    def _normalize_dataframe_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """標準化 DataFrame 格式數據"""
        normalized = {}
        
        # 查找自由現金流列
        fcf_columns = [col for col in data.columns 
                      if 'free_cash_flow' in col.lower() or 'fcf' in col.lower()]
        
        if fcf_columns:
            fcf_values = data[fcf_columns[0]].dropna().tolist()
            normalized['free_cash_flow'] = [float(x) for x in fcf_values]
        
        # 添加其他數據
        normalized['data_type'] = 'dataframe'
        normalized['columns'] = list(data.columns)
        normalized['shape'] = data.shape
        
        return normalized
    
    def _normalize_scalar_data(self, data: Any) -> Dict[str, Any]:
        """標準化標量數據"""
        return {
            'free_cash_flow': [float(data)] if isinstance(data, (int, float)) else [],
            'data_type': 'scalar',
            'original_type': type(data).__name__
        }


class DataSourceManager:
    """數據來源管理器"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path("cache")
        self.logger = logging.getLogger(__name__)
        self.unifier = DataStructureUnifier()
    
    def get_financial_data(self, company_id: str, source: str = "cache") -> Dict[str, Any]:
        """獲取財務數據"""
        try:
            if source == "cache":
                return self._get_cached_data(company_id)
            elif source == "api":
                return self._get_api_data(company_id)
            elif source == "mock":
                return self._get_mock_data(company_id)
            else:
                raise ValueError(f"不支援的數據來源: {source}")
        except Exception as e:
            self.logger.error(f"獲取財務數據失敗 ({company_id}, {source}): {e}")
            return {}
    
    def _get_cached_data(self, company_id: str) -> Dict[str, Any]:
        """從緩存獲取數據"""
        cache_file = self.cache_dir / f"{company_id}_financial.json"
        
        if cache_file.exists():
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.unifier.normalize_financial_data(data)
        
        return {}
    
    def _get_api_data(self, company_id: str) -> Dict[str, Any]:
        """從 API 獲取數據"""
        # 模擬 API 調用
        api_data = {
            'free_cash_flow': [100000, 110000, 120000],
            'revenue': [500000, 550000, 600000],
            'source': 'api'
        }
        return self.unifier.normalize_financial_data(api_data)
    
    def _get_mock_data(self, company_id: str) -> Dict[str, Any]:
        """獲取模擬數據"""
        mock_data = {
            '2330': {
                'free_cash_flow': [50000000, 55000000, 60000000],
                'revenue': [1500000000, 1600000000, 1700000000],
                'company_name': '台積電'
            },
            '2454': {
                'free_cash_flow': [8000000, 8500000, 9000000],
                'revenue': [400000000, 420000000, 450000000],
                'company_name': '聯發科'
            }
        }
        
        if company_id in mock_data:
            return self.unifier.normalize_financial_data(mock_data[company_id])
        
        # 默認數據
        default_data = {
            'free_cash_flow': [100000, 110000, 120000],
            'revenue': [500000, 550000, 600000],
            'company_name': f'公司_{company_id}'
        }
        return self.unifier.normalize_financial_data(default_data)
    
    def validate_data_quality(self, data: Dict) -> Tuple[bool, List[str]]:
        """驗證數據品質"""
        issues = []
        
        # 檢查必要欄位
        if 'free_cash_flow' not in data:
            issues.append("缺少自由現金流數據")
        
        # 檢查數據完整性
        if 'free_cash_flow' in data:
            fcf = data['free_cash_flow']
            if not fcf or len(fcf) == 0:
                issues.append("自由現金流數據為空")
            elif any(x < 0 for x in fcf if x is not None):
                issues.append("自由現金流包含負值")
        
        return len(issues) == 0, issues


class TestDataGenerator:
    """測試數據生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_test_cases(self) -> Dict[str, Dict]:
        """生成標準測試案例"""
        return {
            'format_list': {
                'data': [100000, 110000, 120000],
                'expected_fcf': [100000, 110000, 120000],
                'description': '列表格式測試'
            },
            'format_dict_simple': {
                'data': {
                    'free_cash_flow': [200000, 220000, 240000]
                },
                'expected_fcf': [200000, 220000, 240000],
                'description': '簡單字典格式測試'
            },
            'format_dict_nested': {
                'data': {
                    'cash_flow': {
                        'free_cash_flow': [300000, 330000, 360000]
                    }
                },
                'expected_fcf': [300000, 330000, 360000],
                'description': '嵌套字典格式測試'
            },
            'format_dict_annual': {
                'data': {
                    'free_cash_flow': {
                        'annual': [400000, 440000, 480000]
                    }
                },
                'expected_fcf': [400000, 440000, 480000],
                'description': '年度數據格式測試'
            },
            'format_scalar': {
                'data': 150000,
                'expected_fcf': [150000],
                'description': '標量格式測試'
            }
        }
