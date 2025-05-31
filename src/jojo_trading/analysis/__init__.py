"""
JoJoTrading 分析模組

提供各種金融分析功能：
- 財務分析
- 產業分析
- 成長股分析
"""

# 條件導入，避免缺失模組錯誤
try:
    from .financial_analysis import *
    FINANCIAL_ANALYSIS_AVAILABLE = True
except ImportError:
    FINANCIAL_ANALYSIS_AVAILABLE = False

try:
    from .industry_analysis import *
    INDUSTRY_ANALYSIS_AVAILABLE = True
except ImportError:
    INDUSTRY_ANALYSIS_AVAILABLE = False

try:
    from .growth_analyzer import evaluate_growth_potential, GrowthCriterion, DEFAULT_CRITERIA
    GROWTH_ANALYSIS_AVAILABLE = True
except ImportError:
    GROWTH_ANALYSIS_AVAILABLE = False

__all__ = []

# 動態添加可用的模組
if FINANCIAL_ANALYSIS_AVAILABLE:
    __all__.extend(["financial_analysis"])

if INDUSTRY_ANALYSIS_AVAILABLE:
    __all__.extend(["industry_analysis"])

if GROWTH_ANALYSIS_AVAILABLE:
    __all__.extend(["evaluate_growth_potential", "GrowthCriterion", "DEFAULT_CRITERIA"])
