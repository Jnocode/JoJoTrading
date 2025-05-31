"""
JoJoTrading 台灣股市專用預設配置
==============================

針對台灣股市特性優化的預設配置系統，包含：
1. 成長股篩選預設配置
2. DCF 估值參數預設配置
3. 產業特定配置
4. 市場環境配置

適用於不同投資策略和市場條件
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class TaiwanMarketConfig:
    """台灣股市配置基類"""
    name: str
    description: str
    version: str
    created_date: str
    recommended_for: str
    market_conditions: List[str]

@dataclass
class TaiwanGrowthStockConfig(TaiwanMarketConfig):
    """台灣成長股篩選配置"""
    revenue_cagr_threshold: float
    eps_cagr_threshold: float
    roe_threshold: float
    logic_operator: str
    min_market_cap: float  # 最小市值（億台幣）
    exclude_industries: List[str]  # 排除產業
    
@dataclass
class TaiwanDCFConfig(TaiwanMarketConfig):
    """台灣DCF估值配置"""
    short_term_growth_rate: float
    terminal_growth_rate: float
    risk_preference: float
    projection_years: int
    screening_threshold: float
    enable_anomaly_detection: bool
    fcf_optimization: Dict[str, Any]

@dataclass
class TaiwanIndustryConfig(TaiwanMarketConfig):
    """台灣產業特定配置"""
    industry_codes: List[str]
    industry_names: List[str]
    custom_dcf_params: Dict[str, Any]
    custom_growth_params: Dict[str, Any]

# ============================================
# 成長股預設配置
# ============================================

# 1. 積極成長型（科技股導向）
TAIWAN_AGGRESSIVE_GROWTH = TaiwanGrowthStockConfig(
    name="台股積極成長",
    description="適合台灣高成長科技股投資",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="風險承受度高的投資者，專注科技成長股",
    market_conditions=["牛市", "科技股熱潮", "創新驅動經濟"],
    revenue_cagr_threshold=0.15,  # 15%
    eps_cagr_threshold=0.18,      # 18%
    roe_threshold=0.15,           # 15%
    logic_operator="OR",          # 滿足任一條件即可
    min_market_cap=100,           # 100億台幣
    exclude_industries=["金融業", "營建業", "傳統製造業"]
)

# 2. 穩健成長型（均衡配置）
TAIWAN_BALANCED_GROWTH = TaiwanGrowthStockConfig(
    name="台股穩健成長",
    description="平衡成長與穩定性的台股投資策略",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="一般投資者，追求穩定成長",
    market_conditions=["多頭市場", "經濟穩定成長", "政策支持"],
    revenue_cagr_threshold=0.08,  # 8%
    eps_cagr_threshold=0.10,      # 10%
    roe_threshold=0.12,           # 12%
    logic_operator="AND",         # 需同時滿足所有條件
    min_market_cap=50,            # 50億台幣
    exclude_industries=["高風險產業"]
)

# 3. 價值成長型（傳統產業包容）
TAIWAN_VALUE_GROWTH = TaiwanGrowthStockConfig(
    name="台股價值成長",
    description="包容傳統產業的價值成長策略",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="偏好價值投資的保守型投資者",
    market_conditions=["熊市復甦", "景氣循環底部", "價值回歸"],
    revenue_cagr_threshold=0.05,  # 5%
    eps_cagr_threshold=0.08,      # 8%
    roe_threshold=0.10,           # 10%
    logic_operator="OR",          # 滿足任一條件即可
    min_market_cap=30,            # 30億台幣
    exclude_industries=[]         # 不排除任何產業
)

# 4. ESG永續成長型
TAIWAN_ESG_GROWTH = TaiwanGrowthStockConfig(
    name="台股ESG永續成長",
    description="重視ESG與永續發展的成長策略",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="關注ESG的長期投資者",
    market_conditions=["ESG趨勢", "永續發展政策", "綠色轉型"],
    revenue_cagr_threshold=0.10,  # 10%
    eps_cagr_threshold=0.12,      # 12%
    roe_threshold=0.12,           # 12%
    logic_operator="AND",         # 需同時滿足所有條件
    min_market_cap=80,            # 80億台幣
    exclude_industries=["傳統污染產業", "高碳排產業"]
)

# 5. 小型潛力成長型
TAIWAN_SMALL_CAP_GROWTH = TaiwanGrowthStockConfig(
    name="台股小型潛力成長",
    description="專注於小型股的高潛力成長策略",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="專業投資者，追求高風險高報酬",
    market_conditions=["創新創業", "小型股機會", "市場不效率"],
    revenue_cagr_threshold=0.25,  # 25%
    eps_cagr_threshold=0.30,      # 30%
    roe_threshold=0.20,           # 20%
    logic_operator="OR",          # 滿足任一條件即可
    min_market_cap=10,            # 10億台幣
    exclude_industries=["金融業", "公用事業"]
)

# 6. 股息成長型
TAIWAN_DIVIDEND_GROWTH = TaiwanGrowthStockConfig(
    name="台股股息成長",
    description="重視穩定股息且具成長潛力的策略",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="收益型投資者，重視現金流",
    market_conditions=["穩定股息", "現金流重視", "長期持有"],
    revenue_cagr_threshold=0.08,  # 8%
    eps_cagr_threshold=0.10,      # 10%
    roe_threshold=0.12,           # 12%
    logic_operator="AND",         # 需同時滿足所有條件
    min_market_cap=50,            # 50億台幣
    exclude_industries=["高科技成長股", "生技新創"]
)

# ============================================
# DCF 估值預設配置
# ============================================

# 1. 科技股優化DCF
TAIWAN_TECH_DCF = TaiwanDCFConfig(
    name="台股科技DCF",
    description="針對台灣科技股特性優化的DCF參數",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="科技股投資者",
    market_conditions=["科技創新", "數位轉型", "半導體週期"],
    short_term_growth_rate=0.12,  # 12%
    terminal_growth_rate=0.04,    # 4%
    risk_preference=0.08,         # 8%
    projection_years=5,
    screening_threshold=0.20,     # 20%
    enable_anomaly_detection=True,
    fcf_optimization={
        'maintenance_capex_ratio': 0.7,
        'working_capital_limit': 0.25,
        'heavy_asset_threshold': 0.20,
        'min_fcf_eps_threshold': -30
    }
)

# 2. 傳統產業DCF
TAIWAN_TRADITIONAL_DCF = TaiwanDCFConfig(
    name="台股傳統產業DCF",
    description="適合台灣傳統製造業的DCF參數",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="傳統產業投資者",
    market_conditions=["景氣循環", "製造業復甦", "出口導向"],
    short_term_growth_rate=0.06,  # 6%
    terminal_growth_rate=0.025,   # 2.5%
    risk_preference=0.06,         # 6%
    projection_years=4,
    screening_threshold=0.15,     # 15%
    enable_anomaly_detection=True,
    fcf_optimization={
        'maintenance_capex_ratio': 0.8,
        'working_capital_limit': 0.35,
        'heavy_asset_threshold': 0.25,
        'min_fcf_eps_threshold': -50
    }
)

# 3. 金融股DCF
TAIWAN_FINANCIAL_DCF = TaiwanDCFConfig(
    name="台股金融DCF",
    description="專為台灣金融業設計的DCF參數",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="金融股投資者",
    market_conditions=["利率環境", "金融監管", "經濟週期"],
    short_term_growth_rate=0.05,  # 5%
    terminal_growth_rate=0.03,    # 3%
    risk_preference=0.05,         # 5%
    projection_years=3,
    screening_threshold=0.12,     # 12%
    enable_anomaly_detection=False,  # 金融業特殊會計處理
    fcf_optimization={
        'maintenance_capex_ratio': 0.3,  # 金融業資本支出較低
        'working_capital_limit': 0.15,
        'heavy_asset_threshold': 0.05,
        'min_fcf_eps_threshold': -20
    }
)

# 4. 均衡型DCF（預設推薦）
TAIWAN_BALANCED_DCF = TaiwanDCFConfig(
    name="台股均衡DCF",
    description="適合大多數台股的均衡DCF配置",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="一般投資者的預設選擇",
    market_conditions=["一般市場環境", "混合投資組合"],
    short_term_growth_rate=0.08,  # 8%
    terminal_growth_rate=0.035,   # 3.5%
    risk_preference=0.07,         # 7%
    projection_years=5,
    screening_threshold=0.15,     # 15%
    enable_anomaly_detection=True,
    fcf_optimization={
        'maintenance_capex_ratio': 0.6,
        'working_capital_limit': 0.3,
        'heavy_asset_threshold': 0.15,
        'min_fcf_eps_threshold': -40
    }
)

# 5. 成長股DCF（高成長）
TAIWAN_HIGH_GROWTH_DCF = TaiwanDCFConfig(
    name="台股高成長DCF",
    description="適合高成長潛力股票的DCF參數",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="成長股投資者",
    market_conditions=["創新週期", "高成長期", "市場擴張"],
    short_term_growth_rate=0.20,  # 20%
    terminal_growth_rate=0.06,    # 6%
    risk_preference=0.12,         # 12%（高風險）
    projection_years=6,
    screening_threshold=0.30,     # 30%
    enable_anomaly_detection=True,
    fcf_optimization={
        'maintenance_capex_ratio': 0.5,
        'working_capital_limit': 0.20,
        'heavy_asset_threshold': 0.10,
        'min_fcf_eps_threshold': -20
    }
)

# 6. 價值股DCF（保守）
TAIWAN_VALUE_DCF = TaiwanDCFConfig(
    name="台股價值DCF",
    description="適合價值投資的保守DCF參數",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="價值投資者",
    market_conditions=["市場低迷", "價值窪地", "長期投資"],
    short_term_growth_rate=0.04,  # 4%
    terminal_growth_rate=0.02,    # 2%
    risk_preference=0.05,         # 5%（低風險）
    projection_years=3,
    screening_threshold=0.10,     # 10%
    enable_anomaly_detection=True,
    fcf_optimization={
        'maintenance_capex_ratio': 0.9,
        'working_capital_limit': 0.40,
        'heavy_asset_threshold': 0.30,
        'min_fcf_eps_threshold': -60
    }
)

# ============================================
# 產業特定配置
# ============================================

# 半導體產業
TAIWAN_SEMICONDUCTOR_CONFIG = TaiwanIndustryConfig(
    name="台股半導體產業",
    description="半導體產業專用配置",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="半導體產業投資者",
    market_conditions=["半導體週期", "科技創新", "全球供應鏈"],
    industry_codes=["24"],
    industry_names=["半導體業"],
    custom_dcf_params={
        'short_term_growth_rate': 0.15,
        'terminal_growth_rate': 0.05,
        'risk_preference': 0.09,
        'screening_threshold': 0.25
    },
    custom_growth_params={
        'revenue_cagr_threshold': 0.20,
        'eps_cagr_threshold': 0.25,
        'roe_threshold': 0.18
    }
)

# 生技醫療產業
TAIWAN_BIOTECH_CONFIG = TaiwanIndustryConfig(
    name="台股生技醫療",
    description="生技醫療產業專用配置",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="生技醫療投資者",
    market_conditions=["醫療創新", "人口老化", "新藥開發"],
    industry_codes=["18"],
    industry_names=["生技醫療業"],
    custom_dcf_params={
        'short_term_growth_rate': 0.18,
        'terminal_growth_rate': 0.06,
        'risk_preference': 0.12,  # 高風險
        'screening_threshold': 0.30
    },
    custom_growth_params={
        'revenue_cagr_threshold': 0.25,
        'eps_cagr_threshold': 0.30,
        'roe_threshold': 0.15
    }
)

# 電子零組件產業
TAIWAN_ELECTRONIC_COMPONENTS_CONFIG = TaiwanIndustryConfig(
    name="台股電子零組件",
    description="電子零組件產業專用配置",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="電子產業投資者",
    market_conditions=["電子產業鏈", "5G發展", "物聯網趨勢"],
    industry_codes=["23"],
    industry_names=["電子零組件業"],
    custom_dcf_params={
        'short_term_growth_rate': 0.10,
        'terminal_growth_rate': 0.04,
        'risk_preference': 0.08,
        'screening_threshold': 0.20
    },
    custom_growth_params={
        'revenue_cagr_threshold': 0.15,
        'eps_cagr_threshold': 0.18,
        'roe_threshold': 0.15
    }
)

# 金融服務業
TAIWAN_FINANCIAL_SERVICES_CONFIG = TaiwanIndustryConfig(
    name="台股金融服務",
    description="金融服務業專用配置",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="金融業投資者",
    market_conditions=["利率環境", "金融創新", "數位金融"],
    industry_codes=["17"],
    industry_names=["金融保險業"],
    custom_dcf_params={
        'short_term_growth_rate': 0.05,
        'terminal_growth_rate': 0.025,
        'risk_preference': 0.06,
        'screening_threshold': 0.12
    },
    custom_growth_params={
        'revenue_cagr_threshold': 0.08,
        'eps_cagr_threshold': 0.10,
        'roe_threshold': 0.12
    }
)

# 傳統製造業
TAIWAN_MANUFACTURING_CONFIG = TaiwanIndustryConfig(
    name="台股傳統製造",
    description="傳統製造業專用配置",
    version="1.0",
    created_date="2025-05-30",
    recommended_for="製造業投資者",
    market_conditions=["製造業轉型", "自動化", "供應鏈重組"],
    industry_codes=["08", "09", "10", "11"],
    industry_names=["塑膠工業", "紡織纖維", "電機機械", "鋼鐵工業"],
    custom_dcf_params={
        'short_term_growth_rate': 0.06,
        'terminal_growth_rate': 0.025,
        'risk_preference': 0.07,
        'screening_threshold': 0.15
    },
    custom_growth_params={
        'revenue_cagr_threshold': 0.10,
        'eps_cagr_threshold': 0.12,
        'roe_threshold': 0.10
    }
)

# ============================================
# 市場環境配置
# ============================================

@dataclass
class TaiwanMarketEnvironmentConfig:
    """台灣市場環境配置"""
    name: str
    description: str
    market_phase: str  # "bull", "bear", "neutral", "recovery"
    recommended_growth_configs: List[str]
    recommended_dcf_configs: List[str]
    risk_adjustments: Dict[str, float]

# 牛市配置
TAIWAN_BULL_MARKET_CONFIG = TaiwanMarketEnvironmentConfig(
    name="台股牛市配置",
    description="適合牛市環境的積極策略",
    market_phase="bull",
    recommended_growth_configs=["aggressive", "small_cap"],
    recommended_dcf_configs=["tech", "high_growth"],
    risk_adjustments={
        'growth_threshold_multiplier': 1.2,
        'dcf_discount_adjustment': 0.01,  # 降低風險偏好
        'screening_threshold_multiplier': 1.3
    }
)

# 熊市配置
TAIWAN_BEAR_MARKET_CONFIG = TaiwanMarketEnvironmentConfig(
    name="台股熊市配置",
    description="適合熊市環境的保守策略",
    market_phase="bear",
    recommended_growth_configs=["value", "dividend"],
    recommended_dcf_configs=["value", "financial"],
    risk_adjustments={
        'growth_threshold_multiplier': 0.7,
        'dcf_discount_adjustment': 0.03,  # 提高風險偏好
        'screening_threshold_multiplier': 0.6
    }
)

# ============================================
# 配置集合
# ============================================

TAIWAN_GROWTH_CONFIGS = {
    "aggressive": TAIWAN_AGGRESSIVE_GROWTH,
    "balanced": TAIWAN_BALANCED_GROWTH,
    "value": TAIWAN_VALUE_GROWTH,
    "esg": TAIWAN_ESG_GROWTH,
    "small_cap": TAIWAN_SMALL_CAP_GROWTH,
    "dividend": TAIWAN_DIVIDEND_GROWTH
}

TAIWAN_DCF_CONFIGS = {
    "tech": TAIWAN_TECH_DCF,
    "traditional": TAIWAN_TRADITIONAL_DCF,
    "financial": TAIWAN_FINANCIAL_DCF,
    "balanced": TAIWAN_BALANCED_DCF,  # 預設推薦
    "high_growth": TAIWAN_HIGH_GROWTH_DCF,
    "value": TAIWAN_VALUE_DCF
}

TAIWAN_INDUSTRY_CONFIGS = {
    "semiconductor": TAIWAN_SEMICONDUCTOR_CONFIG,
    "biotech": TAIWAN_BIOTECH_CONFIG,
    "electronic_components": TAIWAN_ELECTRONIC_COMPONENTS_CONFIG,
    "financial_services": TAIWAN_FINANCIAL_SERVICES_CONFIG,
    "manufacturing": TAIWAN_MANUFACTURING_CONFIG
}

TAIWAN_MARKET_ENVIRONMENT_CONFIGS = {
    "bull": TAIWAN_BULL_MARKET_CONFIG,
    "bear": TAIWAN_BEAR_MARKET_CONFIG
}

# ============================================
# 配置應用函數
# ============================================

def get_taiwan_growth_config(config_name: str = "balanced") -> TaiwanGrowthStockConfig:
    """獲取台股成長配置"""
    return TAIWAN_GROWTH_CONFIGS[config_name]

def get_taiwan_dcf_config(config_name: str = "balanced") -> TaiwanDCFConfig:
    """獲取台股DCF配置"""
    return TAIWAN_DCF_CONFIGS[config_name]

def get_taiwan_industry_config(industry_name: str) -> Optional[TaiwanIndustryConfig]:
    """獲取台股產業配置"""
    return TAIWAN_INDUSTRY_CONFIGS.get(industry_name)

# 新增：獲取所有預設配置的函數
def get_all_taiwan_growth_presets() -> Dict[str, TaiwanGrowthStockConfig]:
    """獲取所有台灣成長股預設配置"""
    return TAIWAN_GROWTH_CONFIGS.copy()

def get_all_taiwan_dcf_presets() -> Dict[str, TaiwanDCFConfig]:
    """獲取所有台灣DCF估值預設配置"""
    return TAIWAN_DCF_CONFIGS.copy()

def get_all_taiwan_industry_presets() -> Dict[str, TaiwanIndustryConfig]:
    """獲取所有台灣產業特定預設配置"""
    return TAIWAN_INDUSTRY_CONFIGS.copy()

# 新增：應用預設配置到Streamlit session state的函數
def apply_taiwan_growth_preset(preset_name: str, session_state: Dict[str, Any]):
    """將台灣成長股預設配置應用到Streamlit session state"""
    if preset_name not in TAIWAN_GROWTH_CONFIGS:
        raise ValueError(f"找不到成長股預設配置: {preset_name}")
    
    config = TAIWAN_GROWTH_CONFIGS[preset_name]
    
    # 應用成長股篩選參數
    session_state['revenue_cagr_threshold'] = config.revenue_cagr_threshold
    session_state['eps_cagr_threshold'] = config.eps_cagr_threshold
    session_state['roe_threshold'] = config.roe_threshold
    session_state['logic_operator'] = config.logic_operator
    session_state['min_market_cap'] = config.min_market_cap
    session_state['exclude_industries'] = config.exclude_industries
    
    return config

def apply_taiwan_dcf_preset(preset_name: str, session_state: Dict[str, Any]):
    """將台灣DCF估值預設配置應用到Streamlit session state"""
    if preset_name not in TAIWAN_DCF_CONFIGS:
        raise ValueError(f"找不到DCF預設配置: {preset_name}")
    
    config = TAIWAN_DCF_CONFIGS[preset_name]
    
    # 應用DCF估值參數
    session_state['dcf_short_term_growth_rate'] = config.short_term_growth_rate
    session_state['dcf_terminal_growth_rate'] = config.terminal_growth_rate
    session_state['dcf_risk_preference'] = config.risk_preference
    session_state['dcf_projection_years'] = config.projection_years
    session_state['dcf_screening_threshold'] = config.screening_threshold
    session_state['dcf_enable_anomaly_detection'] = config.enable_anomaly_detection
    session_state['dcf_fcf_optimization'] = config.fcf_optimization
    
    return config

def apply_taiwan_industry_preset(industry_name: str, session_state: Dict[str, Any]):
    """將台灣產業特定預設配置應用到Streamlit session state"""
    if industry_name not in TAIWAN_INDUSTRY_CONFIGS:
        raise ValueError(f"找不到產業特定配置: {industry_name}")
    
    config = TAIWAN_INDUSTRY_CONFIGS[industry_name]
    
    # 應用產業特定參數（這些參數會根據實際需求調整）
    session_state['industry_preset_applied'] = True
    session_state['industry_preset_name'] = industry_name
    session_state['industry_config'] = config
    
    return config

def apply_taiwan_config_to_context(
    context: Dict[str, Any], 
    growth_config: str = "balanced",
    dcf_config: str = "balanced",
    industry_config: Optional[str] = None
) -> Dict[str, Any]:
    """
    將台股配置應用到上下文
    
    Args:
        context: 現有上下文
        growth_config: 成長股配置名稱
        dcf_config: DCF配置名稱
        industry_config: 產業配置名稱（可選）
        
    Returns:
        更新後的上下文
    """
    # 應用成長股配置
    growth_cfg = get_taiwan_growth_config(growth_config)
    context.update({
        'revenue_cagr_enabled': True,
        'revenue_cagr_threshold': growth_cfg.revenue_cagr_threshold * 100,
        'eps_cagr_enabled': True,
        'eps_cagr_threshold': growth_cfg.eps_cagr_threshold * 100,
        'roe_enabled': True,
        'roe_threshold': growth_cfg.roe_threshold * 100,
        'growth_logic_operator': growth_cfg.logic_operator,
        'min_market_cap_filter': growth_cfg.min_market_cap * 100000000,  # 轉換為台幣
        'exclude_industries': growth_cfg.exclude_industries
    })
    
    # 應用DCF配置
    dcf_cfg = get_taiwan_dcf_config(dcf_config)
    context.update({
        'dcf_short_term_growth_rate': dcf_cfg.short_term_growth_rate,
        'dcf_terminal_growth_rate': dcf_cfg.terminal_growth_rate,
        'risk_preference': dcf_cfg.risk_preference,
        'dcf_projection_years': dcf_cfg.projection_years,
        'screening_threshold': dcf_cfg.screening_threshold,
        'enable_anomaly_detection': dcf_cfg.enable_anomaly_detection,
        'fcf_optimization': dcf_cfg.fcf_optimization
    })
    
    # 應用產業配置（如果指定）
    if industry_config:
        industry_cfg = get_taiwan_industry_config(industry_config)
        if industry_cfg:
            # 產業特定的DCF參數覆蓋一般設定
            context.update(industry_cfg.custom_dcf_params)
            # 產業特定的成長參數覆蓋一般設定
            for key, value in industry_cfg.custom_growth_params.items():
                if key.endswith('_threshold'):
                    context[key] = value * 100  # 轉換為百分比
                else:
                    context[key] = value
    
    # 記錄使用的配置
    context['taiwan_config_applied'] = {
        'growth_config': growth_config,
        'dcf_config': dcf_config,
        'industry_config': industry_config,
        'applied_at': datetime.now().isoformat()
    }
    
    return context

def get_config_recommendations(
    investment_style: str = "balanced",
    risk_tolerance: str = "medium",
    industry_focus: Optional[str] = None
) -> Dict[str, str]:
    """
    根據投資風格推薦配置
    
    Args:
        investment_style: 投資風格 (aggressive, balanced, conservative, value)
        risk_tolerance: 風險承受度 (high, medium, low)
        industry_focus: 產業聚焦 (可選)
        
    Returns:
        推薦的配置組合
    """
    recommendations = {}
    
    # 根據投資風格推薦成長股配置
    if investment_style == "aggressive":
        recommendations['growth_config'] = "aggressive"
        recommendations['dcf_config'] = "tech"
    elif investment_style == "conservative":
        recommendations['growth_config'] = "value"
        recommendations['dcf_config'] = "traditional"
    elif investment_style == "value":
        recommendations['growth_config'] = "value"
        recommendations['dcf_config'] = "traditional"
    else:  # balanced
        recommendations['growth_config'] = "balanced"
        recommendations['dcf_config'] = "balanced"
    
    # 根據風險承受度調整
    if risk_tolerance == "high":
        recommendations['dcf_config'] = "tech"
    elif risk_tolerance == "low":
        recommendations['dcf_config'] = "financial"
      # 產業聚焦
    if industry_focus:
        recommendations['industry_config'] = industry_focus
    
    return recommendations

def get_smart_config_recommendation(
    market_cap_preference: str = "medium",
    sector_preference: str = "balanced",
    investment_horizon: str = "medium",
    current_market_phase: str = "neutral"
) -> Dict[str, str]:
    """
    智能配置推薦系統
    
    Args:
        market_cap_preference: 市值偏好 (small, medium, large)
        sector_preference: 產業偏好 (tech, traditional, financial, balanced)
        investment_horizon: 投資期間 (short, medium, long)
        current_market_phase: 當前市場階段 (bull, bear, neutral, recovery)
        
    Returns:
        智能推薦的配置組合
    """
    recommendations = {}
    
    # 基於市值偏好
    if market_cap_preference == "small":
        recommendations['growth_config'] = "small_cap"
        recommendations['dcf_config'] = "high_growth"
    elif market_cap_preference == "large":
        recommendations['growth_config'] = "balanced"
        recommendations['dcf_config'] = "balanced"
    else:  # medium
        recommendations['growth_config'] = "balanced"
        recommendations['dcf_config'] = "tech"
    
    # 基於產業偏好
    if sector_preference == "tech":
        recommendations['industry_config'] = "semiconductor"
        recommendations['dcf_config'] = "tech"
    elif sector_preference == "traditional":
        recommendations['industry_config'] = "manufacturing"
        recommendations['dcf_config'] = "traditional"
    elif sector_preference == "financial":
        recommendations['industry_config'] = "financial_services"
        recommendations['dcf_config'] = "financial"
    
    # 基於投資期間
    if investment_horizon == "long":
        recommendations['growth_config'] = "esg"
    elif investment_horizon == "short":
        recommendations['growth_config'] = "aggressive"
    
    # 基於市場階段
    if current_market_phase == "bull":
        recommendations['growth_config'] = "aggressive"
        recommendations['dcf_config'] = "high_growth"
    elif current_market_phase == "bear":
        recommendations['growth_config'] = "value"
        recommendations['dcf_config'] = "value"
    elif current_market_phase == "recovery":
        recommendations['growth_config'] = "balanced"
        recommendations['dcf_config'] = "balanced"
    
    return recommendations

def apply_market_environment_adjustments(
    context: Dict[str, Any], 
    market_phase: str
) -> Dict[str, Any]:
    """
    根據市場環境調整配置參數
    
    Args:
        context: 現有上下文
        market_phase: 市場階段 (bull, bear, neutral, recovery)
        
    Returns:
        調整後的上下文
    """
    if market_phase not in TAIWAN_MARKET_ENVIRONMENT_CONFIGS:
        return context
    
    env_config = TAIWAN_MARKET_ENVIRONMENT_CONFIGS[market_phase]
    adjustments = env_config.risk_adjustments
    
    # 應用成長閾值調整
    if 'revenue_cagr_threshold' in context:
        context['revenue_cagr_threshold'] *= adjustments.get('growth_threshold_multiplier', 1.0)
    
    if 'eps_cagr_threshold' in context:
        context['eps_cagr_threshold'] *= adjustments.get('growth_threshold_multiplier', 1.0)
    
    # 應用DCF風險調整
    if 'risk_preference' in context:
        context['risk_preference'] += adjustments.get('dcf_discount_adjustment', 0.0)
    
    # 應用篩選閾值調整
    if 'screening_threshold' in context:
        context['screening_threshold'] *= adjustments.get('screening_threshold_multiplier', 1.0)
    
    # 記錄環境調整
    context['market_environment_adjustment'] = {
        'market_phase': market_phase,
        'adjustments_applied': adjustments,
        'adjusted_at': datetime.now().isoformat()
    }
    
    return context

def get_all_configs_summary() -> str:
    """獲取所有台股配置的摘要"""
    summary = "🇹🇼 JoJoTrading 台灣股市預設配置總覽\n"
    summary += "=" * 50 + "\n\n"
    
    summary += "📈 成長股篩選配置:\n"
    for name, config in TAIWAN_GROWTH_CONFIGS.items():
        summary += f"  • {config.name} ({name})\n"
        summary += f"    {config.description}\n"
        summary += f"    適用: {config.recommended_for}\n\n"
    
    summary += "💰 DCF 估值配置:\n"
    for name, config in TAIWAN_DCF_CONFIGS.items():
        summary += f"  • {config.name} ({name})\n"
        summary += f"    {config.description}\n"
        summary += f"    適用: {config.recommended_for}\n\n"
    
    summary += "🏭 產業特定配置:\n"
    for name, config in TAIWAN_INDUSTRY_CONFIGS.items():
        summary += f"  • {config.name} ({name})\n"
        summary += f"    {config.description}\n"
        summary += f"    適用: {config.recommended_for}\n\n"
    
    return summary

# ============================================
# 使用範例
# ============================================

if __name__ == "__main__":
    # 顯示所有配置摘要
    print(get_all_configs_summary())
    
    # 範例：取得積極成長型配置
    aggressive_config = get_taiwan_growth_config("aggressive")
    print(f"積極成長配置: {aggressive_config.name}")
    print(f"營收CAGR閾值: {aggressive_config.revenue_cagr_threshold*100:.1f}%")
    
    # 範例：應用配置到上下文
    context = {}
    context = apply_taiwan_config_to_context(
        context, 
        growth_config="aggressive",
        dcf_config="tech"
    )
    print(f"\n應用配置後的部分參數:")
    print(f"營收CAGR閾值: {context['revenue_cagr_threshold']:.1f}%")
    print(f"DCF短期成長率: {context['dcf_short_term_growth_rate']*100:.1f}%")
    
    # 範例：取得投資建議
    recommendations = get_config_recommendations(
        investment_style="aggressive",
        risk_tolerance="high",
        industry_focus="semiconductor"
    )
    print(f"\n投資建議配置:")
    for key, value in recommendations.items():
        print(f"  {key}: {value}")
    
    # 範例：智能配置推薦
    smart_recommendations = get_smart_config_recommendation(
        market_cap_preference="small",
        sector_preference="tech",
        investment_horizon="long",
        current_market_phase="bull"
    )
    print(f"\n智能配置建議:")
    for key, value in smart_recommendations.items():
        print(f"  {key}: {value}")
    
    # 範例：應用市場環境調整
    context = apply_market_environment_adjustments(context, "bull")
    print(f"\n應用市場環境調整後的參數:")
    print(f"營收CAGR閾值: {context['revenue_cagr_threshold']:.1f}%")
    print(f"DCF短期成長率: {context['dcf_short_term_growth_rate']*100:.1f}%")
    print(f"風險偏好: {context['risk_preference']:.2f}")
