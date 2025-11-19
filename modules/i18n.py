MESSAGES = {
    "zh": {
        "welcome": "歡迎使用 JoJoTrading",
        "clear_cache": "清理暫存資料",
        "cache_cleared": "暫存資料已清除",
        "api_delay": "API呼叫延遲 (毫秒)",
        "use_simulated_data": "開啟模擬數據測試",
        "debug_section": "除錯 (Debug)",
        "language": "語言",
        "chinese": "中文",
        "english": "英文",
        "run": "執行",
        "cancel": "取消",
        "confirm_clear_cache": "確定要清除所有暫存資料嗎？",
        "yes": "是",
        "no": "否",
        "error": "錯誤",
        "success": "成功",
        "select_language": "選擇語言"
    },
    "en": {
        "welcome": "Welcome to JoJoTrading",
        "clear_cache": "Clear Cache",
        "cache_cleared": "Cache cleared",
        "api_delay": "API Call Delay (ms)",
        "use_simulated_data": "Enable Simulated Data",
        "debug_section": "Debug",
        "language": "Language",
        "chinese": "Chinese",
        "english": "English",
        "run": "Run",
        "cancel": "Cancel",
        "confirm_clear_cache": "Are you sure you want to clear all cache?",
        "yes": "Yes",
        "no": "No",
        "error": "Error",
        "success": "Success",
        "select_language": "Select Language"
    }
}

def t(key, lang="zh"):
    """
    多語言翻譯函數
    :param key: 字串key
    :param lang: "zh" or "en"
    :return: 翻譯後字串
    """
    return MESSAGES.get(lang, {}).get(key, key)
