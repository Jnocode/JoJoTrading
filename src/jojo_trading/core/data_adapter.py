
"""
Data Adapter Module
負責將不同來源 (FinMind, Yahoo Finance) 的資料進行標準化與對齊。
確保上層應用程式 (DCF Model, UI) 接收到的資料格式一致。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataAdapter:
    
    # 定義系統標準欄位 (Canonical Fields)
    STANDARD_FIELDS = [
        "stock_code",           # 股票代碼 (e.g., "2330")
        "stock_name",           # 股票名稱
        "current_market_price", # 現價 (元)
        "shares_outstanding",   # 流通股數 (股)
        "market_cap",           # 市值 (元)
        "revenue",              # 營收 (元)
        "net_income_parent",    # 歸屬母公司淨利 (元)
        "eps",                  # 每股盈餘 (元)
        "fcf",                  # 自由現金流 (元)
        "capex",                # 資本支出 (元，通常為負值)
        "depreciation",         # 折舊與攤銷 (元)
        "cash",                 # 現金及約當現金 (元)
        "source",               # 資料來源標記
        "data_date"             # 資料日期/季度
    ]

    @staticmethod
    def normalize_symbol_for_yfinance(stock_code: str) -> str:
        """
        將系統標準代碼轉換為 Yahoo Finance 格式
        策略：優先嘗試 .TW (上市)，未來可擴充 .TWO (上櫃) 檢測邏輯
        """
        stock_code = str(stock_code).strip()
        if stock_code.endswith('.TW') or stock_code.endswith('.TWO'):
            return stock_code
        
        # 預設假設為上市 (.TW)，實務上若失敗可由 Fetcher 層重試 .TWO
        return f"{stock_code}.TW"

    @staticmethod
    def standardize_yfinance_data(stock_code: str, yf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將 Yahoo Finance 的原始資料轉換為系統標準格式
        """
        if not yf_data:
            return {}

        standardized = {field: None for field in DataAdapter.STANDARD_FIELDS}
        
        standardized["stock_code"] = stock_code
        standardized["source"] = "yfinance"
        
        # 1. 基礎資訊對齊
        standardized["shares_outstanding"] = yf_data.get("shares_outstanding")
        standardized["market_cap"] = yf_data.get("market_cap")
        standardized["current_market_price"] = yf_data.get("current_market_price")
        
        # 2. 財務數據對齊
        # Yahoo Finance 的 Net Income 通常對應到我們的 net_income_parent
        standardized["net_income_parent"] = yf_data.get("net_income")
        standardized["revenue"] = yf_data.get("revenue")
        standardized["cash"] = yf_data.get("cash")
        
        # 3. FCF 與 Capex
        # 注意：Yahoo 的 Capex 通常是負數，我們的模型通常預期 Capex 為負數或正數需統一
        # 這裡統一保持原始數值 (通常為負)，由模型層決定如何運算 (通常是 + Capex 或 - abs(Capex))
        standardized["fcf"] = yf_data.get("fcf")
        standardized["capex"] = yf_data.get("capex")
        standardized["depreciation"] = yf_data.get("depreciation")
        
        # 4. 計算衍生欄位 (如果來源沒有提供)
        if standardized["net_income_parent"] and standardized["shares_outstanding"]:
            try:
                standardized["eps"] = standardized["net_income_parent"] / standardized["shares_outstanding"]
            except ZeroDivisionError:
                standardized["eps"] = 0

        return standardized

    @staticmethod
    def merge_data(primary_data: Dict[str, Any], secondary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        資料合併策略：
        以 Primary (通常是 FinMind) 為主，若欄位缺失則用 Secondary (Yahoo Finance) 填補。
        """
        if not primary_data:
            return secondary_data or {}
        
        if not secondary_data:
            return primary_data

        merged = primary_data.copy()
        
        # 檢查關鍵欄位，若 Primary 缺失則補上 Secondary 的值
        keys_to_check = ["current_market_price", "shares_outstanding", "net_income_parent", "revenue", "fcf", "eps", "capex", "depreciation"]
        
        for key in keys_to_check:
            primary_val = merged.get(key)
            secondary_val = secondary_data.get(key)
            
            # 判斷 Primary 值是否無效 (None, 0, 或特定錯誤標記)
            is_primary_invalid = primary_val is None or primary_val == 0 or primary_val == "N/A"
            
            if is_primary_invalid and secondary_val is not None:
                merged[key] = secondary_val
                # 標記該欄位來源已被替換 (可選)
                merged[f"{key}_source"] = "yfinance_fallback"
                logger.info(f"Field '{key}' missing in primary source, filled with secondary source value: {secondary_val}")

        return merged
