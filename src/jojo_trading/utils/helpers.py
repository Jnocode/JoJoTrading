"""
工具輔助函數模組

提供通用的輔助函數和工具類，支援其他模組的功能實現。
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd


def setup_logging(
    name: str = "jojo_trading",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """設置日誌記錄器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重複添加 handler
    if not logger.handlers:
        # 控制台輸出
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 檔案輸出（如果指定）
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
    
    return logger


def safe_json_load(file_path: Union[str, Path]) -> Dict[str, Any]:
    """安全載入 JSON 檔案"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"載入 JSON 檔案失敗 {file_path}: {e}")
        return {}


def safe_json_save(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """安全儲存 JSON 檔案"""
    try:
        # 確保目錄存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"儲存 JSON 檔案失敗 {file_path}: {e}")
        return False


def get_project_root() -> Path:
    """取得專案根目錄"""
    current_file = Path(__file__)
    # 從 src/jojo_trading/utils/helpers.py 往上找到專案根目錄
    return current_file.parent.parent.parent.parent


def get_data_dir() -> Path:
    """取得資料目錄"""
    return get_project_root() / "data"


def get_config_dir() -> Path:
    """取得配置目錄"""
    return get_project_root() / "config"


def get_user_config_dir() -> Path:
    """取得用戶配置目錄"""
    return get_project_root() / "user_configs"


def ensure_dir_exists(path: Union[str, Path]) -> Path:
    """確保目錄存在，如果不存在則創建"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_number(value: Optional[float], decimal_places: int = 2) -> str:
    """格式化數字顯示"""
    if value is None:
        return "N/A"
    
    if abs(value) >= 1e9:
        return f"{value/1e9:.{decimal_places}f}B"
    elif abs(value) >= 1e6:
        return f"{value/1e6:.{decimal_places}f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.{decimal_places}f}K"
    else:
        return f"{value:.{decimal_places}f}"


def format_percentage(value: Optional[float], decimal_places: int = 2) -> str:
    """格式化百分比顯示"""
    if value is None:
        return "N/A"
    return f"{value*100:.{decimal_places}f}%"


def validate_stock_code(code: str) -> bool:
    """驗證台股代碼格式"""
    if not code or not isinstance(code, str):
        return False
    
    # 移除空白字符
    code = code.strip()
    
    # 台股代碼通常是 4-6 位數字
    return code.isdigit() and 4 <= len(code) <= 6


def calculate_date_range(days_back: int = 365) -> tuple[str, str]:
    """計算日期範圍"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    return (
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )


def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
    """清理財務資料"""
    if df.empty:
        return df
    
    # 移除重複記錄
    df = df.drop_duplicates()
    
    # 處理日期欄位
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df = df.sort_values('date', ascending=False)
    
    # 處理數值欄位
    numeric_columns = df.select_dtypes(include=['number']).columns
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def merge_dataframes(*dfs: pd.DataFrame, on: str = 'stock_id') -> pd.DataFrame:
    """合併多個 DataFrame"""
    if not dfs:
        return pd.DataFrame()
    
    result = dfs[0].copy()
    
    for df in dfs[1:]:
        if not df.empty:
            result = pd.merge(result, df, on=on, how='outer')
    
    return result


class ConfigValidator:
    """配置驗證器"""
    
    @staticmethod
    def validate_dcf_config(config: Dict[str, Any]) -> tuple[bool, str]:
        """驗證 DCF 配置"""
        required_fields = [
            'risk_free_rate', 'market_risk_premium', 
            'growth_rate', 'terminal_growth_rate'
        ]
        
        for field in required_fields:
            if field not in config:
                return False, f"缺少必要欄位: {field}"
            
            value = config[field]
            if not isinstance(value, (int, float)):
                return False, f"欄位 {field} 必須是數字"
            
            if value < 0 or value > 1:
                return False, f"欄位 {field} 值必須在 0-1 之間"
        
        return True, "配置驗證通過"
    
    @staticmethod
    def validate_growth_config(config: Dict[str, Any]) -> tuple[bool, str]:
        """驗證成長股配置"""
        required_fields = [
            'revenue_growth_threshold', 'profit_growth_threshold',
            'roe_threshold', 'pe_ratio_max'
        ]
        
        for field in required_fields:
            if field not in config:
                return False, f"缺少必要欄位: {field}"
            
            value = config[field]
            if not isinstance(value, (int, float)):
                return False, f"欄位 {field} 必須是數字"
        
        return True, "配置驗證通過"


# 常用常數
DEFAULT_CACHE_TTL = 3600  # 1小時
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# 導出的函數列表
__all__ = [
    'setup_logging',
    'safe_json_load',
    'safe_json_save', 
    'get_project_root',
    'get_data_dir',
    'get_config_dir',
    'get_user_config_dir',
    'ensure_dir_exists',
    'format_number',
    'format_percentage',
    'validate_stock_code',
    'calculate_date_range',
    'clean_financial_data',
    'merge_dataframes',
    'ConfigValidator'
]
