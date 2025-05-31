"""
JoJotrading 國際化 (i18n) 模組

此模組提供台股篩選系統的多語言支援功能，
目前支援繁體中文與英文兩種語言介面。

主要功能：
1. 多語言字典管理
   - 中文 (zh): 繁體中文介面文字
   - 英文 (en): 英文介面文字
   - 支援新增其他語言的擴展性設計

2. 翻譯函數
   - t(key, lang): 根據語言代碼回傳對應翻譯文字
   - 支援預設語言回退機制
   - 處理缺失翻譯鍵的錯誤情況

3. 涵蓋範圍
   - 使用者介面標籤與按鈕
   - 系統訊息與通知
   - 錯誤提示與狀態訊息
   - 調試與開發工具文字

設計特色：
- 集中式翻譯字典管理
- 簡潔的 API 介面設計
- 支援動態語言切換
- 容錯機制避免顯示錯誤

使用範例：
    from modules.i18n import t
    
    # 顯示中文歡迎訊息
    welcome_msg = t("welcome", "zh")  # "歡迎使用 JoJoTrading"
    
    # 顯示英文歡迎訊息  
    welcome_msg = t("welcome", "en")  # "Welcome to JoJoTrading"
    
    # 在 Streamlit 中使用
    st.title(t("welcome", st.session_state.get("language", "zh")))

擴展指南：
- 新增語言：在 MESSAGES 字典中加入新的語言代碼
- 新增翻譯鍵：在各語言字典中加入對應的翻譯文字
- 維持翻譯一致性：確保所有語言包含相同的翻譯鍵
"""

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
