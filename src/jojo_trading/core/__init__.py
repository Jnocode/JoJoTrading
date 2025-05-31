"""
JoJoTrading 核心業務邏輯模組

包含系統的核心功能實現：
- DCF估值計算器
- 資料處理器
- 狀態機管理
- 增強DCF模型
"""

# 避免循環導入，使用模組級導入
from . import data_handler
from .state_machine import JoJoStateMachine, JoJoState, State

# 條件導入，避免缺失模組錯誤
try:
    from .dcf_calculator import DCFCalculator
except ImportError:
    DCFCalculator = None

try:
    from .enhanced_dcf import EnhancedDCFModel
except ImportError:
    EnhancedDCFModel = None

try:
    from .integrated_dcf_handler import calculate_enhanced_dcf_valuation
except ImportError:
    calculate_enhanced_dcf_valuation = None

__all__ = [
    "data_handler",
    "JoJoStateMachine",
    "JoJoState", 
    "State",
]

# 動態添加可用的模組到 __all__
if DCFCalculator is not None:
    __all__.append("DCFCalculator")
if EnhancedDCFModel is not None:
    __all__.append("EnhancedDCFModel")
if calculate_enhanced_dcf_valuation is not None:
    __all__.append("calculate_enhanced_dcf_valuation")
