"""
JoJoTrading 配置管理模組

管理系統的各種配置：
- 台股市場預設配置
- 用戶自訂配置
- 優化參數配置
"""

# 條件導入，避免缺失模組錯誤
try:
    from .taiwan_presets import *
    TAIWAN_PRESETS_AVAILABLE = True
except ImportError:
    TAIWAN_PRESETS_AVAILABLE = False

try:
    from .user_config import *
    USER_CONFIG_AVAILABLE = True
except ImportError:
    USER_CONFIG_AVAILABLE = False

try:
    from .optimization_config import *
    OPTIMIZATION_CONFIG_AVAILABLE = True
except ImportError:
    OPTIMIZATION_CONFIG_AVAILABLE = False

__all__ = []

# 動態添加可用的模組
if TAIWAN_PRESETS_AVAILABLE:
    __all__.extend([
        "get_all_taiwan_growth_presets",
        "get_all_taiwan_dcf_presets", 
        "get_all_taiwan_industry_presets",
        "apply_taiwan_growth_preset",
        "apply_taiwan_dcf_preset",
        "apply_taiwan_industry_preset"
    ])

if USER_CONFIG_AVAILABLE:
    __all__.extend([
        "UserConfigManager",
        "UserGrowthConfig",
    "UserDCFConfig",
        "UserIntegratedConfig",
        "UserConfigMetadata"
    ])

if OPTIMIZATION_CONFIG_AVAILABLE:
    __all__.extend([
        "DCF_OPTIMIZED_CONFIG"
    ])
