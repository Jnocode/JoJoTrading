"""
國際化翻譯系統
支援多語言界面
"""

import json
from pathlib import Path
from typing import Dict, Any

class Translator:
    """多語言翻譯器"""
    
    def __init__(self, default_language: str = "zh_TW"):
        self.default_language = default_language
        self.current_language = default_language
        self.translations = {}
        self.load_translations()
        
    def load_translations(self):
        """載入翻譯文件"""
        locales_dir = Path(__file__).parent.parent.parent.parent / "locales"
        
        for lang_dir in locales_dir.iterdir():
            if lang_dir.is_dir():
                lang_code = lang_dir.name
                translation_file = lang_dir / "messages.json"
                
                if translation_file.exists():
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                        
    def set_language(self, language_code: str):
        """設定當前語言"""
        if language_code in self.translations:
            self.current_language = language_code
            
    def translate(self, key: str, **kwargs) -> str:
        """翻譯文本"""
        try:
            translation = self.translations[self.current_language].get(key, key)
            return translation.format(**kwargs)
        except (KeyError, AttributeError):
            # 回退到預設語言
            try:
                translation = self.translations[self.default_language].get(key, key)
                return translation.format(**kwargs)
            except (KeyError, AttributeError):
                return key

# 全域翻譯器實例
translator = Translator()

def t(key: str, **kwargs) -> str:
    """翻譯快捷函數"""
    return translator.translate(key, **kwargs)
