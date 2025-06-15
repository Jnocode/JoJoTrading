"""
JoJoTrading 成長股判定優化配置
==================================

針對台灣股市特性優化的成長股篩選參數設定
提供多種預設情境，適應不同投資策略需求
"""

from dataclasses import dataclass
from typing import Dict, List
from src.jojo_trading.analysis.growth_analyzer import GrowthCriterion, GrowthCriteriaSet

@dataclass
class OptimizedGrowthConfig:
    """優化的成長股配置"""
    name: str
    description: str
    criteria_set: GrowthCriteriaSet
    recommended_for: str

# ============================================
# 優化配置方案
# ============================================

# 方案1：推薦配置（平衡型）
RECOMMENDED_CONFIG = OptimizedGrowthConfig(
    name="推薦配置",
    description="適合台灣市場的平衡型成長股篩選",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion(
                metric_name='revenue_cagr',
                period_years=3,
                threshold=0.10,  # 10%
                operator='>',
                label='近3年營收CAGR > 10%'
            ),
            GrowthCriterion(
                metric_name='eps_cagr',
                period_years=3,
                threshold=0.12,  # 12%
                operator='>',
                label='近3年EPS CAGR > 12%'
            ),
            GrowthCriterion(
                metric_name='roe',
                period_years=None,
                threshold=0.10,  # 10%
                operator='>',
                label='最新ROE > 10%'
            ),
        ],
        logic_operator='OR'  # 任一條件達成即可
    ),
    recommended_for="大多數台灣投資者，平衡成長潛力與投資機會"
)

# 方案2：積極成長型
AGGRESSIVE_CONFIG = OptimizedGrowthConfig(
    name="積極成長",
    description="尋找高成長潛力股票",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion(
                metric_name='revenue_cagr',
                period_years=3,
                threshold=0.15,  # 15%
                operator='>',
                label='近3年營收CAGR > 15%'
            ),
            GrowthCriterion(
                metric_name='eps_cagr',
                period_years=3,
                threshold=0.18,  # 18%
                operator='>',
                label='近3年EPS CAGR > 18%'
            ),
            GrowthCriterion(
                metric_name='roe',
                period_years=None,
                threshold=0.15,  # 15%
                operator='>',
                label='最新ROE > 15%'
            ),
        ],
        logic_operator='OR'
    ),
    recommended_for="風險承受度高的投資者，追求高成長股票"
)

# 方案3：穩健型
CONSERVATIVE_CONFIG = OptimizedGrowthConfig(
    name="穩健型",
    description="重視穩定成長的保守策略",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion(
                metric_name='revenue_cagr',
                period_years=3,
                threshold=0.06,  # 6%
                operator='>',
                label='近3年營收CAGR > 6%'
            ),
            GrowthCriterion(
                metric_name='eps_cagr',
                period_years=3,
                threshold=0.08,  # 8%
                operator='>',
                label='近3年EPS CAGR > 8%'
            ),
            GrowthCriterion(
                metric_name='roe',
                period_years=None,
                threshold=0.08,  # 8%
                operator='>',
                label='最新ROE > 8%'
            ),
        ],
        logic_operator='AND'  # 所有條件都要達成
    ),
    recommended_for="風險厭惡的投資者，重視穩健性"
)

# 方案4：科技股專用
TECH_FOCUSED_CONFIG = OptimizedGrowthConfig(
    name="科技股專用",
    description="針對科技業特性調整的篩選標準",
    criteria_set=GrowthCriteriaSet(
        criteria=[
            GrowthCriterion(
                metric_name='revenue_cagr',
                period_years=3,
                threshold=0.20,  # 20%
                operator='>',
                label='近3年營收CAGR > 20%'
            ),
            GrowthCriterion(
                metric_name='eps_cagr',
                period_years=3,
                threshold=0.15,  # 15%
                operator='>',
                label='近3年EPS CAGR > 15%'
            ),
            GrowthCriterion(
                metric_name='roe',
                period_years=None,
                threshold=0.12,  # 12%
                operator='>',
                label='最新ROE > 12%'
            ),
        ],
        logic_operator='OR'
    ),
    recommended_for="專注科技股投資，追求創新成長企業"
)

# ============================================
# 配置字典
# ============================================

OPTIMIZED_CONFIGS = {
    "recommended": RECOMMENDED_CONFIG,
    "aggressive": AGGRESSIVE_CONFIG, 
    "conservative": CONSERVATIVE_CONFIG,
    "tech_focused": TECH_FOCUSED_CONFIG
}

# ============================================
# 快速應用函數
# ============================================

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
    
    # 根據配置啟用相應條件
    for criterion in criteria_set.criteria:
        if criterion.metric_name == 'revenue_cagr':
            context['revenue_cagr_enabled'] = True
            context['revenue_cagr_threshold'] = criterion.threshold * 100  # 轉換為百分比
        elif criterion.metric_name == 'eps_cagr':
            context['eps_cagr_enabled'] = True
            context['eps_cagr_threshold'] = criterion.threshold * 100
        elif criterion.metric_name == 'roe':
            context['roe_enabled'] = True
            context['roe_threshold'] = criterion.threshold * 100
    
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
            threshold_pct = criterion.threshold * 100
            summary += f"     • {criterion.label.replace(f'> {threshold_pct:.0f}%', f'> {threshold_pct:.1f}%')}\n"
        summary += "\n"
    
    return summary

# ============================================
# 使用範例
# ============================================

if __name__ == "__main__":
    # 顯示所有配置摘要
    print(get_config_summary())
    
    # 範例：應用推薦配置
    sample_context = {}
    updated_context = apply_config_to_context(sample_context, "recommended")
    print("應用推薦配置後的context:")
    for key, value in updated_context.items():
        print(f"  {key}: {value}")
