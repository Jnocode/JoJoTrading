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
