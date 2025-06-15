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
