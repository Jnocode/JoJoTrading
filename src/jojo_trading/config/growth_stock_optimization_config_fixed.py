"""
JoJoTrading 成長股判定優化配置
==================================

針對台灣股市特性優化的成長股篩選參數設定
提供多種預設情境，適應不同投資策略需求
"""

from dataclasses import dataclass
from typing import Dict, List
from ..core.growth_analyzer import GrowthCriterion, GrowthCriteriaSet

@dataclass
class OptimizedGrowthConfig:
    """優化的成長股配置"""
    name: str
    description: str
    criteria_set: GrowthCriteriaSet
    recommended_for: str

# 推薦配置 - 平衡成長與品質
RECOMMENDED_CONFIG = OptimizedGrowthConfig(
    name="平衡成長配置",
    description="在成長潛力與財務品質間取得平衡",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion("revenue_cagr", "營收CAGR", 0.08, True, "營收年複合成長率 > 8%"),
            GrowthCriterion("eps_cagr", "EPS CAGR", 0.10, True, "每股盈餘年複合成長率 > 10%"),
            GrowthCriterion("roe", "ROE", 0.12, True, "股東權益報酬率 > 12%"),
        ],
        logic_operator="AND"
    ),
    recommended_for="追求穩健成長的價值投資者"
)

# 積極成長配置
AGGRESSIVE_CONFIG = OptimizedGrowthConfig(
    name="積極成長配置",
    description="追求高成長潛力，容忍較高風險",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion("revenue_cagr", "營收CAGR", 0.15, True, "營收年複合成長率 > 15%"),
            GrowthCriterion("eps_cagr", "EPS CAGR", 0.20, True, "每股盈餘年複合成長率 > 20%"),
        ],
        logic_operator="OR"
    ),
    recommended_for="風險承受度高的成長投資者"
)

# 保守配置
CONSERVATIVE_CONFIG = OptimizedGrowthConfig(
    name="保守成長配置",
    description="注重財務穩健性，適度成長",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion("revenue_cagr", "營收CAGR", 0.05, True, "營收年複合成長率 > 5%"),
            GrowthCriterion("roe", "ROE", 0.10, True, "股東權益報酬率 > 10%"),
            GrowthCriterion("debt_ratio", "負債比率", 0.50, False, "負債比率 < 50%"),
        ],
        logic_operator="AND"
    ),
    recommended_for="追求穩定的保守投資者"
)

# 科技股專用配置
TECH_FOCUSED_CONFIG = OptimizedGrowthConfig(
    name="科技股專用配置",
    description="針對科技產業特性優化",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion("revenue_cagr", "營收CAGR", 0.12, True, "營收年複合成長率 > 12%"),
            GrowthCriterion("eps_cagr", "EPS CAGR", 0.15, True, "每股盈餘年複合成長率 > 15%"),
            GrowthCriterion("rnd_ratio", "研發費用率", 0.03, True, "研發費用率 > 3%"),
        ],
        logic_operator="AND"
    ),
    recommended_for="專注科技產業的投資者"
)

# 所有配置字典
OPTIMIZED_CONFIGS = {
    "recommended": RECOMMENDED_CONFIG,
    "aggressive": AGGRESSIVE_CONFIG,
    "conservative": CONSERVATIVE_CONFIG,
    "tech_focused": TECH_FOCUSED_CONFIG
}

def get_optimized_config(config_name: str = "recommended") -> OptimizedGrowthConfig:
    """
    取得優化配置
    
    Args:
        config_name: 配置名稱 ("recommended", "aggressive", "conservative", "tech_focused")
    
    Returns:
        OptimizedGrowthConfig: 配置物件
    """
    return OPTIMIZED_CONFIGS.get(config_name, RECOMMENDED_CONFIG)

def apply_config_to_context(context: Dict, config_name: str = "recommended") -> Dict:
    """
    將優化配置應用到state machine context
    
    Args:
        context: 現有的context字典
        config_name: 要應用的配置名稱
    
    Returns:
        Dict: 更新後的context
    """
    config = get_optimized_config(config_name)
    criteria_set = config.criteria_set
    
    # 重置所有條件為False
    context['revenue_cagr_enabled'] = False
    context['eps_cagr_enabled'] = False
    context['roe_enabled'] = False
    context['debt_ratio_enabled'] = False
    context['rnd_ratio_enabled'] = False
    
    # 根據配置啟用條件
    for criterion in criteria_set.criteria:
        if criterion.field == "revenue_cagr":
            context['revenue_cagr_enabled'] = True
            context['revenue_cagr_threshold'] = criterion.threshold
        elif criterion.field == "eps_cagr":
            context['eps_cagr_enabled'] = True
            context['eps_cagr_threshold'] = criterion.threshold
        elif criterion.field == "roe":
            context['roe_enabled'] = True
            context['roe_threshold'] = criterion.threshold
        elif criterion.field == "debt_ratio":
            context['debt_ratio_enabled'] = True
            context['debt_ratio_threshold'] = criterion.threshold
        elif criterion.field == "rnd_ratio":
            context['rnd_ratio_enabled'] = True
            context['rnd_ratio_threshold'] = criterion.threshold
    
    # 設定邏輯運算符
    context['growth_logic_operator'] = criteria_set.logic_operator
    
    return context

def get_config_summary() -> str:
    """取得所有配置的摘要說明"""
    summary = "JoJoTrading 成長股篩選優化配置\n"
    summary += "=" * 40 + "\n\n"
    
    for name, config in OPTIMIZED_CONFIGS.items():
        summary += f"📊 {config.name}\n"
        summary += f"   描述：{config.description}\n"
        summary += f"   適用：{config.recommended_for}\n"
        summary += f"   邏輯：{config.criteria_set.logic_operator}\n"
        summary += "   條件：\n"
        for criterion in config.criteria_set.criteria:
            threshold_pct = criterion.threshold * 100 if criterion.threshold < 1 else criterion.threshold
            label_text = criterion.label if criterion.label else f"{criterion.field} > {threshold_pct:.1f}%"
            summary += f"     • {label_text}\n"
        summary += "\n"
    
    return summary

# 使用範例
if __name__ == "__main__":
    # 顯示所有配置摘要
    print(get_config_summary())
    
    # 範例：應用推薦配置
    sample_context = {}
    updated_context = apply_config_to_context(sample_context, "recommended")
    print("應用推薦配置後的context:")
    for key, value in updated_context.items():
        print(f"  {key}: {value}")
