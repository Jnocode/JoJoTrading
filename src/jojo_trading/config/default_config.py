"""
JoJo Trading 預設配置模組
========================
"""

import json
from pathlib import Path

# 預設配置字典
DEFAULT_CONFIG = {
    "risk_free_rate": 0.01,
    "market_risk_premium": 0.06,
    "terminal_growth_rate": 0.02,
    "discount_periods": 5,
    "currency": "TWD",
    "taiwan_market": {
        "risk_free_rate": 0.01,
        "market_risk_premium": 0.06,
        "terminal_growth_rate": 0.02,
        "currency": "TWD"
    }
}

def get_default_config():
    """獲取預設配置"""
    return DEFAULT_CONFIG.copy()

def load_config_from_file(config_path):
    """從文件載入配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return get_default_config()

def save_config_to_file(config, config_path):
    """保存配置到文件"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

# 向後相容性
TAIWAN_MARKET_CONFIG = DEFAULT_CONFIG["taiwan_market"]

__all__ = [
    'DEFAULT_CONFIG', 
    'TAIWAN_MARKET_CONFIG',
    'get_default_config',
    'load_config_from_file',
    'save_config_to_file'
]


def get_all_taiwan_growth_presets():
    """獲取所有台灣成長股預設配置"""
    return {
        "conservative": {
            "growth_rate": 0.05,
            "risk_premium": 0.03,
            "terminal_growth": 0.02
        },
        "moderate": {
            "growth_rate": 0.10,
            "risk_premium": 0.05,
            "terminal_growth": 0.025
        },
        "aggressive": {
            "growth_rate": 0.15,
            "risk_premium": 0.08,
            "terminal_growth": 0.03
        }
    }

def get_growth_stock_optimization_config():
    """獲取成長股優化配置"""
    return {
        "screening_criteria": {
            "min_revenue_growth": 0.15,
            "min_earnings_growth": 0.20,
            "max_pe_ratio": 30
        },
        "valuation_adjustments": {
            "growth_premium": 1.2,
            "risk_discount": 0.9
        }
    }

def get_all_taiwan_dcf_presets():
    """獲取所有台灣 DCF 預設配置"""
    return {
        "conservative": {
            "discount_rate": 0.08,
            "terminal_growth_rate": 0.02,
            "risk_free_rate": 0.01,
            "market_risk_premium": 0.06
        },
        "moderate": {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "risk_free_rate": 0.01,
            "market_risk_premium": 0.08
        },
        "aggressive": {
            "discount_rate": 0.12,
            "terminal_growth_rate": 0.03,
            "risk_free_rate": 0.01,
            "market_risk_premium": 0.10
        }
    }

def get_all_taiwan_industry_presets():
    """獲取所有台灣行業預設配置"""
    return {
        "technology": {
            "growth_rate": 0.12,
            "risk_premium": 0.08,
            "pe_multiple": 25
        },
        "finance": {
            "growth_rate": 0.06,
            "risk_premium": 0.05,
            "pe_multiple": 15
        },
        "manufacturing": {
            "growth_rate": 0.08,
            "risk_premium": 0.06,
            "pe_multiple": 18
        }
    }

def apply_taiwan_growth_preset(preset_name):
    """應用台灣成長股預設配置"""
    presets = get_all_taiwan_growth_presets()
    return presets.get(preset_name, presets["moderate"])

def apply_taiwan_dcf_preset(preset_name):
    """應用台灣 DCF 預設配置"""
    presets = get_all_taiwan_dcf_presets()
    return presets.get(preset_name, presets["moderate"])

def apply_taiwan_industry_preset(preset_name):
    """應用台灣行業預設配置"""
    presets = get_all_taiwan_industry_presets()
    return presets.get(preset_name, presets["technology"])

# 更新 __all__ 列表
__all__ = [
    'DEFAULT_CONFIG', 
    'TAIWAN_MARKET_CONFIG',
    'get_default_config',
    'load_config_from_file',
    'save_config_to_file',
    'get_all_taiwan_growth_presets',
    'get_growth_stock_optimization_config',
    'get_all_taiwan_dcf_presets',
    'get_all_taiwan_industry_presets',
    'apply_taiwan_growth_preset',
    'apply_taiwan_dcf_preset',
    'apply_taiwan_industry_preset'
]
