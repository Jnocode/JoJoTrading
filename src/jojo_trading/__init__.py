"""
JoJoTrading - 台股智慧投資分析系統

一個專為台灣股市設計的綜合投資分析平台，整合DCF估值、成長股篩選、
技術分析等多種投資策略，提供專業級的投資決策支援。

主要功能:
- DCF估值計算與優化
- 成長股智能篩選
- 台股市場預設配置
- 用戶自訂配置管理
- 即時資料分析
- 投資組合優化

版本: 1.0.0
作者: JoJoTrading Development Team
"""

__version__ = "1.0.0"
__author__ = "JoJoTrading Development Team"

# 主要模組導入 - 使用條件導入避免錯誤
try:
    from .core import JoJoStateMachine, JoJoState
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

try:
    from .config import TAIWAN_PRESETS
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

try:
    from .analysis.growth_analyzer import evaluate_growth_potential, GrowthCriterion
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False

try:
    from .utils.helpers import setup_logging, get_project_root
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

# 版本資訊
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "pre_release": None
}

def get_version():
    """獲取版本字串"""
    version = f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}"
    if VERSION_INFO['pre_release']:
        version += f"-{VERSION_INFO['pre_release']}"
    return version

# 套件元資訊
__all__ = [
    "__version__",
    "__author__", 
    "get_version",
    "VERSION_INFO"
]

# 動態添加可用的功能
if CORE_AVAILABLE:
    __all__.extend(["JoJoStateMachine", "JoJoState"])

if CONFIG_AVAILABLE:
    __all__.extend(["TAIWAN_PRESETS"])

if ANALYSIS_AVAILABLE:
    __all__.extend(["evaluate_growth_potential", "GrowthCriterion"])

if UTILS_AVAILABLE:
    __all__.extend(["setup_logging", "get_project_root"])
