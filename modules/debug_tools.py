"""
JoJotrading 除錯工具模組

此模組提供開發和除錯過程中的實用工具函數，
包含模擬數據測試、API 延遲控制和快取管理功能。

主要功能：

1. 模擬數據控制
   - use_simulated_data(): 檢查是否啟用模擬數據模式
   - 用於開發環境測試，避免頻繁呼叫真實 API

2. API 延遲管理
   - api_delay(): 取得設定的 API 呼叫延遲時間
   - apply_api_delay(): 自動套用延遲以符合 API 限制
   - 防止因過於頻繁的 API 呼叫而被限制

3. 快取清理功能
   - clear_cache(): 清除所有暫存資料夾
   - 支援清理 FinMind 數據、價格快取、股本變動等快取
   - 適用於除錯或重新整理數據時使用

設計用途：
- 開發環境的除錯支援
- 效能測試與 API 限制遵循
- 數據一致性維護
- 問題排查與系統重置

支援的快取目錄：
- cache/finmind_data: FinMind API 財務數據快取
- cache/finmind_price_cache: 股價數據快取  
- cache/twse_capital_change: 台證所股本變動快取

使用範例：
    from modules.debug_tools import use_simulated_data, apply_api_delay, clear_cache
    
    # 檢查是否使用模擬數據
    if use_simulated_data(context):
        return mock_financial_data
    
    # 套用 API 延遲
    apply_api_delay(context)
    response = api_call()
    
    # 清理快取
    clear_cache()

除錯配置：
在應用程式的 context["debug"] 中設定：
- use_simulated_data: 布林值，是否啟用模擬數據
- api_delay_ms: 整數，API 呼叫間隔毫秒數
"""

import os
import shutil
import time

def use_simulated_data(context):
    """
    回傳是否啟用模擬數據測試
    """
    return bool(context.get("debug", {}).get("use_simulated_data", False))

def api_delay(context):
    """
    回傳API呼叫延遲（毫秒），預設0
    """
    return int(context.get("debug", {}).get("api_delay_ms", 0))

def apply_api_delay(context):
    """
    根據設定自動sleep指定毫秒數
    """
    delay_ms = api_delay(context)
    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)

def clear_cache():
    """
    清理所有暫存資料夾（finmind_data, finmind_price_cache, twse_capital_change）
    """
    cache_dirs = [
        os.path.join("cache", "finmind_data"),
        os.path.join("cache", "finmind_price_cache"),
        os.path.join("cache", "twse_capital_change"),
    ]
    for d in cache_dirs:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"[debug_tools] 已清除暫存資料夾: {d}")
            except Exception as e:
                print(f"[debug_tools] 清除暫存資料夾失敗: {d}，錯誤: {e}")
        else:
            print(f"[debug_tools] 暫存資料夾不存在: {d}")
