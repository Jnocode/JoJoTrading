"""
JoJo Trading System - Test Configuration
測試配置文件，定義全局測試夾具和設定

Created: 2025-06-13
Author: JoJo Trading Development Team
"""

import pytest
import sys
import os
from pathlib import Path

# 添加 src 目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

# 測試配置
@pytest.fixture(scope="session")
def test_config():
    """測試配置夾具"""
    return {
        "test_data_dir": PROJECT_ROOT / "tests" / "data",
        "temp_dir": PROJECT_ROOT / "tests" / "temp",
        "log_level": "DEBUG"
    }

@pytest.fixture(scope="session")
def app_config():
    """應用程式配置夾具"""
    return {
        "database_url": "sqlite:///:memory:",
        "cache_dir": PROJECT_ROOT / "cache",
        "data_dir": PROJECT_ROOT / "data",
        "debug": True
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """自動設置測試環境"""
    # 設置測試環境變數
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    yield
    
    # 清理測試環境
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

@pytest.fixture
def sample_stock_data():
    """樣本股票數據夾具"""
    return {
        "2330": {
            "name": "台積電",
            "sector": "半導體",
            "market_cap": 15000000,
            "shares_outstanding": 25930380038,
            "eps": [20.92, 23.45, 26.55],
            "revenue": [1851843000, 1759490000, 1629487000],
            "book_value": 65.23
        },
        "2454": {
            "name": "聯發科",
            "sector": "半導體",
            "market_cap": 1200000,
            "shares_outstanding": 1593166852,
            "eps": [78.46, 82.11, 71.33],
            "revenue": [480817000, 448526000, 434020000],
            "book_value": 145.67
        }
    }

@pytest.fixture
def sample_financial_data():
    """樣本財務數據夾具"""
    return {
        "income_statement": {
            "revenue": [1000000, 1100000, 1200000],
            "operating_income": [200000, 220000, 240000],
            "net_income": [150000, 165000, 180000],
            "eps": [3.5, 3.8, 4.1]
        },
        "balance_sheet": {
            "total_assets": [800000, 850000, 900000],
            "total_liabilities": [300000, 320000, 340000],
            "shareholders_equity": [500000, 530000, 560000],
            "book_value_per_share": [11.5, 12.2, 12.9]
        },
        "cash_flow": {
            "operating_cash_flow": [180000, 195000, 210000],
            "investing_cash_flow": [-50000, -55000, -60000],
            "financing_cash_flow": [-30000, -25000, -20000],
            "free_cash_flow": [130000, 140000, 150000]
        }
    }

@pytest.fixture
def dcf_parameters():
    """DCF 估值參數夾具"""
    return {
        "discount_rate": 0.10,
        "terminal_growth_rate": 0.03,
        "projection_years": 5,
        "risk_free_rate": 0.02,
        "market_risk_premium": 0.08,
        "beta": 1.2
    }

@pytest.fixture
def enhanced_financial_data():
    """增強的財務數據夾具 - 支援多種格式"""
    # 基礎數據結構
    base_data = {
        "income_statement": {
            "revenue": [1000000, 1100000, 1200000],
            "operating_income": [200000, 220000, 240000],
            "net_income": [150000, 165000, 180000],
            "eps": [3.5, 3.8, 4.1]
        },
        "balance_sheet": {
            "total_assets": [800000, 850000, 900000],
            "total_liabilities": [300000, 320000, 340000],
            "shareholders_equity": [500000, 530000, 560000],
            "book_value_per_share": [11.5, 12.2, 12.9]
        },
        "cash_flow": {
            "operating_cash_flow": [180000, 195000, 210000],
            "investing_cash_flow": [-50000, -55000, -60000],
            "financing_cash_flow": [-30000, -25000, -20000],
            "free_cash_flow": [130000, 140000, 150000]  # 根級別
        },
        # 支援嵌套結構的自由現金流
        "free_cash_flow": {
            "annual": [130000, 140000, 150000],
            "quarterly": [32500, 35000, 37500, 40000],
            "projected": [160000, 170000, 180000, 190000, 200000]
        }
    }
    
    return base_data

@pytest.fixture
def multi_format_financial_data():
    """多格式財務數據夾具 - 測試不同數據結構兼容性"""
    return {
        # 格式 1: 列表格式（適用於歷史數據）
        "format_list": {
            "free_cash_flow": [130000, 140000, 150000],
            "revenue": [1000000, 1100000, 1200000],
            "net_income": [150000, 165000, 180000]
        },
        
        # 格式 2: 字典格式（適用於詳細分析）
        "format_dict": {
            "free_cash_flow": {
                "annual": [130000, 140000, 150000],
                "quarterly": [32500, 35000, 37500, 40000]
            },
            "revenue": {
                "annual": [1000000, 1100000, 1200000],
                "quarterly": [250000, 275000, 300000, 325000]
            }
        },
        
        # 格式 3: 混合格式（實際應用情況）
        "format_mixed": {
            "free_cash_flow": [130000, 140000, 150000],  # 列表
            "revenue": {"annual": [1000000, 1100000, 1200000]},  # 嵌套
            "net_income": 150000  # 單值
        }
    }

@pytest.fixture
def dcf_test_data():
    """DCF 測試專用數據夾具"""
    return {
        "company_id": "2330",
        "company_name": "台積電",
        "financial_data": {
            "free_cash_flow": [50000000, 55000000, 60000000],  # 三年歷史FCF
            "revenue": [1500000000, 1600000000, 1700000000],
            "net_income": [500000000, 550000000, 600000000],
            "shares_outstanding": 25930380038,
            "capex": [15000000, 16000000, 17000000],
            "depreciation": [12000000, 13000000, 14000000]
        },
        "dcf_parameters": {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.03,
            "projection_years": 5,
            "short_term_growth": 0.12,
            "long_term_growth": 0.05
        },
        "expected_results": {
            "intrinsic_value_range": (400, 600),  # 預期估值範圍
            "fcf_growth_rate": 0.10,
            "terminal_value_ratio": 0.65
        }
    }

# 數據驗證工具
@pytest.fixture
def data_validator():
    """數據驗證工具夾具"""
    def validate_structure(data, expected_fields):
        """驗證數據結構"""
        missing_fields = []
        for field in expected_fields:
            if field not in data:
                missing_fields.append(field)
        return len(missing_fields) == 0, missing_fields
    
    def validate_fcf_format(fcf_data):
        """驗證自由現金流數據格式"""
        if isinstance(fcf_data, list):
            return "list", len(fcf_data)
        elif isinstance(fcf_data, dict):
            return "dict", list(fcf_data.keys())
        else:
            return "single", type(fcf_data).__name__
    
    return {
        "validate_structure": validate_structure,
        "validate_fcf_format": validate_fcf_format
    }

# 標記定義
def pytest_configure(config):
    """配置自定義標記"""
    config.addinivalue_line(
        "markers", "unit: 標記為單元測試"
    )
    config.addinivalue_line(
        "markers", "integration: 標記為整合測試"
    )
    config.addinivalue_line(
        "markers", "system: 標記為系統測試"
    )
    config.addinivalue_line(
        "markers", "slow: 標記為慢速測試"
    )
    config.addinivalue_line(
        "markers", "api: 標記為 API 測試"
    )
    config.addinivalue_line(
        "markers", "database: 標記為資料庫測試"
    )

# 錯誤處理
@pytest.fixture
def suppress_logs():
    """抑制測試期間的日誌輸出"""
    import logging
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
