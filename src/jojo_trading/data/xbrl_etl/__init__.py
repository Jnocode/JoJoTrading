"""
JoJotrading XBRL ETL 模組

此模組提供 XBRL (eXtensible Business Reporting Language) 財務報表
數據的提取、轉換和載入 (ETL) 功能，用於處理台灣上市櫃公司的
標準化財務報告數據。

主要功能：

1. XBRL 數據獲取
   - get_latest_xbrl_zip_url(): 獲取最新 XBRL 壓縮檔 URL
   - download_xbrl_zip(): 下載 XBRL 數據壓縮檔
   - unzip_xbrl_files(): 解壓縮 XBRL 檔案

2. XBRL 解析處理
   - parse_xbrl_folder(): 解析整個 XBRL 資料夾
   - 支援多格式財務報表標準
   - 自動化數據結構標準化

3. 數據存取管理
   - save_parsed_xbrl_data(): 儲存解析後的財務數據
   - load_parsed_xbrl_data(): 載入已解析的財務數據
   - 支援增量更新與版本控制

4. 自動化更新
   - update_xbrl_data_for_period(): 特定期間數據更新
   - ensure_latest_xbrl_data(): 確保使用最新財務數據
   - 排程化數據同步機制

5. 財務項目對應
   - FINANCIAL_ITEMS_MAPPING: 財務科目標準化對應表
   - 統一不同公司間的財務項目命名
   - 支援自訂財務指標計算

技術特色：
- 符合台灣 XBRL 分類標準
- 高效能批次處理能力
- 錯誤處理與資料驗證
- 支援多期間財務數據比較

數據來源：
- 台灣證券交易所 XBRL 資料庫
- 櫃買中心財務報告資料
- 符合金管會申報格式標準

使用範例：
    from modules.xbrl_etl import ensure_latest_xbrl_data, load_parsed_xbrl_data
    
    # 確保最新數據
    ensure_latest_xbrl_data("2024Q3")
    
    # 載入財務數據
    financial_data = load_parsed_xbrl_data("2024Q3")

應用場景：
- DCF 估值模型數據來源
- 財務比率分析
- 產業比較研究
- 投資決策支援系統
"""

from .main import (
    get_latest_xbrl_zip_url,
    download_xbrl_zip,
    unzip_xbrl_files,
    parse_xbrl_folder,
    save_parsed_xbrl_data,
    load_parsed_xbrl_data,
    update_xbrl_data_for_period,
    ensure_latest_xbrl_data
)
from .financial_items_mapping import FINANCIAL_ITEMS_MAPPING

__all__ = [
    "get_latest_xbrl_zip_url",
    "download_xbrl_zip",
    "unzip_xbrl_files",
    "parse_xbrl_folder",
    "save_parsed_xbrl_data",
    "load_parsed_xbrl_data",
    "update_xbrl_data_for_period",
    "ensure_latest_xbrl_data",
    "FINANCIAL_ITEMS_MAPPING"
]
