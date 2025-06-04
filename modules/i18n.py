"""
國際化(i18n)支援模組
提供多語言文本支援
"""

# 簡化的翻譯字典
TRANSLATIONS = {
    'zh': {
        'title': 'JoJo Trading 系統',
        'loading': '載入中...',
        'success': '成功',
        'error': '錯誤',
        'industry': '產業',
        'stock_code': '股票代碼',
        'valuation': '估值',
        'growth_rate': '成長率',
    },
    'en': {
        'title': 'JoJo Trading System',
        'loading': 'Loading...',
        'success': 'Success',
        'error': 'Error',
        'industry': 'Industry',
        'stock_code': 'Stock Code',
        'valuation': 'Valuation',
        'growth_rate': 'Growth Rate',
    }
}

# 預設語言
DEFAULT_LANGUAGE = 'zh'

def t(key, lang=None):
    """
    翻譯函數
    
    Args:
        key: 翻譯鍵值
        lang: 語言代碼，預設為中文
        
    Returns:
        str: 翻譯後的文本
    """
    if lang is None:
        lang = DEFAULT_LANGUAGE
    
    return TRANSLATIONS.get(lang, {}).get(key, key)
