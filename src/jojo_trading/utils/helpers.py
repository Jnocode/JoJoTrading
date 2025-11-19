"""
工具輔助函數模組

提供通用的輔助函數和工具類，支援其他模組的功能實現。
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import pandas as pd
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


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


# 常用常數（需要在函數定義之前）
DEFAULT_CACHE_TTL = 3600  # 1小時
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30
RETRY_BACKOFF_FACTOR = 2  # 指數退避因子
RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504]  # 需要重試的 HTTP 狀態碼


def api_request_with_retry(
    url: str,
    method: str = 'GET',
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRY_ATTEMPTS,
    backoff_factor: float = RETRY_BACKOFF_FACTOR,
    verify: bool = False,
    enable_metrics: bool = True,
    **kwargs
) -> requests.Response:
    """
    帶有智能重試機制的 API 請求函數
    
    Args:
        url: 請求的 URL
        method: HTTP 方法 (GET, POST, PUT, DELETE 等)
        timeout: 請求超時時間（秒）
        max_retries: 最大重試次數
        backoff_factor: 指數退避因子（每次重試等待時間倍增）
        verify: 是否驗證 SSL 證書
        enable_metrics: 是否啟用指標收集（預設 True）
        **kwargs: 傳遞給 requests 的其他參數
    
    Returns:
        requests.Response: API 響應物件
    
    Raises:
        RequestException: 當所有重試都失敗時
    
    範例:
        >>> response = api_request_with_retry('https://api.example.com/data')
        >>> data = response.json()
    """
    logger = logging.getLogger(__name__)
    
    # 取得指標收集器（如果啟用）
    metrics_collector = None
    if enable_metrics:
        try:
            from .metrics import get_metrics_collector
            metrics_collector = get_metrics_collector()
        except ImportError:
            logger.debug("指標模組未安裝，跳過指標收集")
    
    # 記錄開始時間
    start_time = time.time()
    retry_count = 0
    last_error = None
    last_status_code = None
    
    for attempt in range(max_retries):
        try:
            # 計算重試等待時間（指數退避）
            if attempt > 0:
                wait_time = backoff_factor ** attempt
                logger.info(f"第 {attempt + 1} 次重試，等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
            
            # 發送請求
            logger.debug(f"發送 {method} 請求到: {url} (嘗試 {attempt + 1}/{max_retries})")
            response = requests.request(
                method=method,
                url=url,
                timeout=timeout,
                verify=verify,
                **kwargs
            )
            
            # 檢查狀態碼
            if response.status_code in RETRY_STATUS_CODES:
                logger.warning(
                    f"收到可重試的狀態碼 {response.status_code}，"
                    f"剩餘重試次數: {max_retries - attempt - 1}"
                )
                if attempt < max_retries - 1:
                    continue
            
            # 請求成功，拋出異常如果狀態碼不是 2xx
            response.raise_for_status()
            logger.debug(f"請求成功: {url}")
            
            # 記錄成功的指標
            if metrics_collector:
                duration = time.time() - start_time
                metrics_collector.record_api_request(
                    url=url,
                    method=method,
                    status_code=response.status_code,
                    duration=duration,
                    retry_count=retry_count,
                    success=True
                )
            
            return response
            
        except Timeout as e:
            retry_count += 1
            last_error = 'Timeout'
            logger.warning(f"請求超時 (嘗試 {attempt + 1}/{max_retries}): {e}")
            if attempt >= max_retries - 1:
                logger.error(f"達到最大重試次數，放棄請求: {url}")
                
                # 記錄失敗的指標
                if metrics_collector:
                    duration = time.time() - start_time
                    metrics_collector.record_api_request(
                        url=url,
                        method=method,
                        status_code=None,
                        duration=duration,
                        retry_count=retry_count - 1,
                        success=False,
                        error_type='Timeout'
                    )
                
                raise RequestException(f"API 請求超時，已重試 {max_retries} 次: {url}") from e
                
        except ConnectionError as e:
            retry_count += 1
            last_error = 'ConnectionError'
            logger.warning(f"連線錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            if attempt >= max_retries - 1:
                logger.error(f"達到最大重試次數，放棄請求: {url}")
                
                # 記錄失敗的指標
                if metrics_collector:
                    duration = time.time() - start_time
                    metrics_collector.record_api_request(
                        url=url,
                        method=method,
                        status_code=None,
                        duration=duration,
                        retry_count=retry_count - 1,
                        success=False,
                        error_type='ConnectionError'
                    )
                
                raise RequestException(f"無法連線到 API，已重試 {max_retries} 次: {url}") from e
                
        except RequestException as e:
            retry_count += 1
            last_error = type(e).__name__
            last_status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            logger.warning(f"請求錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            if attempt >= max_retries - 1:
                logger.error(f"達到最大重試次數，放棄請求: {url}")
                
                # 記錄失敗的指標
                if metrics_collector:
                    duration = time.time() - start_time
                    metrics_collector.record_api_request(
                        url=url,
                        method=method,
                        status_code=last_status_code,
                        duration=duration,
                        retry_count=retry_count - 1,
                        success=False,
                        error_type=last_error
                    )
                
                raise
    
    # 理論上不應該到達這裡，但如果到達，記錄失敗指標
    if metrics_collector:
        duration = time.time() - start_time
        metrics_collector.record_api_request(
            url=url,
            method=method,
            status_code=last_status_code,
            duration=duration,
            retry_count=retry_count,
            success=False,
            error_type=last_error or 'Unknown'
        )
    
    raise RequestException(f"API 請求失敗: {url}")


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
    'api_request_with_retry',
    'ConfigValidator'
]
