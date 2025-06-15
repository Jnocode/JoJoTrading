"""
Utility Functions Module
工具函數模組 - 提供通用工具函數
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import streamlit as st


class PathUtils:
    """路徑工具類"""
    
    @staticmethod
    def get_project_root() -> str:
        """獲取項目根目錄"""
        current_file = os.path.abspath(__file__)
        # 向上查找直到找到 pyproject.toml 或 setup.py
        current_dir = os.path.dirname(current_file)
        
        while current_dir != os.path.dirname(current_dir):  # 不是根目錄
            if any(os.path.exists(os.path.join(current_dir, f)) 
                   for f in ['pyproject.toml', 'setup.py', '.git']):
                return current_dir
            current_dir = os.path.dirname(current_dir)
        
        return current_dir
    
    @staticmethod
    def ensure_path_in_sys(path: str) -> None:
        """確保路徑在 sys.path 中"""
        if path not in sys.path:
            sys.path.append(path)
    
    @staticmethod
    def get_data_dir() -> str:
        """獲取數據目錄"""
        project_root = PathUtils.get_project_root()
        data_dir = os.path.join(project_root, 'data')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    
    @staticmethod
    def get_cache_dir() -> str:
        """獲取快取目錄"""
        project_root = PathUtils.get_project_root()
        cache_dir = os.path.join(project_root, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    
    @staticmethod
    def get_logs_dir() -> str:
        """獲取日誌目錄"""
        project_root = PathUtils.get_project_root()
        logs_dir = os.path.join(project_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir


class DataUtils:
    """數據處理工具類"""
    
    @staticmethod
    def safe_float_convert(value: Any, default: float = 0.0) -> float:
        """安全轉換為浮點數
        
        Args:
            value: 要轉換的值
            default: 轉換失敗時的默認值
            
        Returns:
            float: 轉換後的浮點數
        """
        try:
            if value is None or value == '':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int_convert(value: Any, default: int = 0) -> int:
        """安全轉換為整數
        
        Args:
            value: 要轉換的值
            default: 轉換失敗時的默認值
            
        Returns:
            int: 轉換後的整數
        """
        try:
            if value is None or value == '':
                return default
            return int(float(value))  # 先轉float再轉int，處理小數字符串
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """格式化為百分比字符串
        
        Args:
            value: 要格式化的值（0.15 表示 15%）
            decimal_places: 小數位數
            
        Returns:
            str: 格式化後的百分比字符串
        """
        try:
            return f"{value * 100:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_currency(value: float, currency_symbol: str = "$") -> str:
        """格式化為貨幣字符串
        
        Args:
            value: 要格式化的值
            currency_symbol: 貨幣符號
            
        Returns:
            str: 格式化後的貨幣字符串
        """
        try:
            return f"{currency_symbol}{value:,.2f}"
        except (ValueError, TypeError):
            return f"{currency_symbol}N/A"
    
    @staticmethod
    def clean_numeric_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """清理數字數據，移除無效值
        
        Args:
            data: 要清理的數據字典
            
        Returns:
            Dict[str, Any]: 清理後的數據字典
        """
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)) and not (
                value != value or  # NaN check
                value == float('inf') or 
                value == float('-inf')
            ):
                cleaned_data[key] = value
            elif isinstance(value, str) and value.strip():
                # 嘗試轉換字符串數字
                numeric_value = DataUtils.safe_float_convert(value, None)
                if numeric_value is not None:
                    cleaned_data[key] = numeric_value
                else:
                    cleaned_data[key] = value
            elif value is not None:
                cleaned_data[key] = value
        
        return cleaned_data


class FileUtils:
    """文件處理工具類"""
    
    @staticmethod
    def load_json_file(file_path: str, default: Any = None) -> Any:
        """載入 JSON 文件
        
        Args:
            file_path: 文件路徑
            default: 載入失敗時的默認值
            
        Returns:
            Any: JSON 數據
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"載入 JSON 文件失敗 {file_path}: {e}")
        
        return default or {}
    
    @staticmethod
    def save_json_file(data: Any, file_path: str) -> bool:
        """保存 JSON 文件
        
        Args:
            data: 要保存的數據
            file_path: 文件路徑
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"保存 JSON 文件失敗 {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """獲取文件大小（MB）
        
        Args:
            file_path: 文件路徑
            
        Returns:
            float: 文件大小（MB）
        """
        try:
            if os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                return size_bytes / (1024 * 1024)
        except Exception:
            pass
        return 0.0


class LogUtils:
    """日誌工具類"""
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_file: Optional[str] = None
    ) -> logging.Logger:
        """設置日誌
        
        Args:
            log_level: 日誌級別
            log_file: 日誌文件路徑（可選）
            
        Returns:
            logging.Logger: 配置好的日誌器
        """
        logger = logging.getLogger("jojo_trading")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # 清除現有 handlers
        logger.handlers.clear()
        
        # 控制台 handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 文件 handler（如果指定）
        if log_file:
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"無法創建日誌文件 {log_file}: {e}")
        
        return logger


class StreamlitUtils:
    """Streamlit 工具類"""
    
    @staticmethod
    def show_loading_message(message: str, duration: float = 2.0) -> None:
        """顯示載入訊息
        
        Args:
            message: 載入訊息
            duration: 持續時間（秒）
        """
        with st.spinner(message):
            import time
            time.sleep(duration)
    
    @staticmethod
    def display_metrics_grid(
        metrics: List[Dict[str, Union[str, float]]], 
        columns: int = 3
    ) -> None:
        """顯示指標網格
        
        Args:
            metrics: 指標列表
            columns: 列數
        """
        if not metrics:
            return
        
        # 分組顯示指標
        for i in range(0, len(metrics), columns):
            cols = st.columns(columns)
            for j, metric in enumerate(metrics[i:i+columns]):
                if j < len(cols):
                    with cols[j]:
                        st.metric(
                            label=metric.get('label', ''),
                            value=metric.get('value', ''),
                            delta=metric.get('delta', None)
                        )
    
    @staticmethod
    def create_download_button(
        data: str, 
        filename: str, 
        button_text: str = "下載文件",
        mime_type: str = "text/plain"
    ) -> None:
        """創建下載按鈕
        
        Args:
            data: 要下載的數據
            filename: 文件名
            button_text: 按鈕文字
            mime_type: MIME 類型
        """
        st.download_button(
            label=button_text,
            data=data,
            file_name=filename,
            mime=mime_type
        )
    
    @staticmethod
    def show_success_with_balloons(message: str) -> None:
        """顯示成功訊息並播放氣球動畫
        
        Args:
            message: 成功訊息
        """
        st.success(message)
        st.balloons()
    
    @staticmethod
    def create_info_expander(title: str, content: str) -> None:
        """創建信息展開器
        
        Args:
            title: 標題
            content: 內容
        """
        with st.expander(title):
            st.info(content)


class ValidationUtils:
    """驗證工具類"""
    
    @staticmethod
    def validate_stock_code(stock_code: str) -> bool:
        """驗證股票代碼格式
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            bool: 是否有效
        """
        if not stock_code or not isinstance(stock_code, str):
            return False
        
        # 移除空格並轉為字符串
        code = str(stock_code).strip()
        
        # 台股代碼通常為4位數字，或者6位數字（含副號）
        if len(code) == 4 and code.isdigit():
            return True
        elif len(code) == 6 and code.isdigit():
            return True
        
        return False
    
    @staticmethod
    def validate_financial_data(data: Dict[str, Any]) -> List[str]:
        """驗證財務數據
        
        Args:
            data: 財務數據字典
            
        Returns:
            List[str]: 驗證錯誤列表
        """
        errors = []
        
        # 檢查必要字段
        required_fields = ['current_market_price', 'net_income_parent', 'shares_outstanding']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"缺少必要字段: {field}")
            elif not isinstance(data[field], (int, float)) or data[field] <= 0:
                errors.append(f"字段 {field} 必須為正數")
        
        return errors
    
    @staticmethod
    def validate_dcf_parameters(params: Dict[str, Any]) -> List[str]:
        """驗證DCF參數
        
        Args:
            params: DCF參數字典
            
        Returns:
            List[str]: 驗證錯誤列表
        """
        errors = []
        
        # 檢查折現率
        discount_rate = params.get('discount_rate', 0)
        if not isinstance(discount_rate, (int, float)) or discount_rate <= 0 or discount_rate >= 1:
            errors.append("折現率必須在 0 到 1 之間")
        
        # 檢查成長率
        growth_rate = params.get('growth_rate', 0)
        if not isinstance(growth_rate, (int, float)) or growth_rate < -0.5 or growth_rate > 1:
            errors.append("成長率必須在 -50% 到 100% 之間")
        
        # 檢查永續成長率
        terminal_growth = params.get('terminal_growth', 0)
        if not isinstance(terminal_growth, (int, float)) or terminal_growth < 0 or terminal_growth >= discount_rate:
            errors.append("永續成長率必須小於折現率且大於等於0")
        
        return errors


# 快速導入常用工具
__all__ = [
    'PathUtils',
    'DataUtils', 
    'FileUtils',
    'LogUtils',
    'StreamlitUtils',
    'ValidationUtils'
]
