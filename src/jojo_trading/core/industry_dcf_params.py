"""
行業特定的DCF估值參數配置
Industry-Specific DCF Valuation Parameters Configuration

根據不同行業的特性，設定適當的DCF估值參數
"""

from typing import Dict, Any

# 行業特定的DCF估值參數
INDUSTRY_DCF_PARAMS = {"半導體": {
        "growth_rate": 12.0,     # 台積電等龍頭具備強勁成長潛力
        "terminal_growth": 3.0,   # 科技業長期成長略高於GDP
        "discount_rate": 8.5,     # 調降風險溢價，反映龍頭地位
        "volatility": "中高",
        "description": "全球半導體龍頭，具備技術護城河和強勁成長潛力"
    },
    "電子": {
        "growth_rate": 6.0,
        "terminal_growth": 2.0,
        "discount_rate": 8.5,
        "volatility": "中高",
        "description": "製造業龍頭，穩定成長但受景氣循環影響"
    },
    "金融": {
        "growth_rate": 4.0,      # 金融業成長較穩定
        "terminal_growth": 2.0,
        "discount_rate": 7.0,     # 相對低風險
        "volatility": "中",
        "description": "穩定收益行業，成長率較保守但風險相對較低"
    },
    "電信": {
        "growth_rate": 3.0,      # 成熟產業，成長有限
        "terminal_growth": 1.5,
        "discount_rate": 6.5,     # 公用事業性質，風險較低
        "volatility": "低",
        "description": "公用事業性質，穩定現金流但成長有限"
    },
    "傳統製造": {
        "growth_rate": 3.5,
        "terminal_growth": 1.8,
        "discount_rate": 7.5,
        "volatility": "中",
        "description": "傳統製造業，受景氣循環影響"
    },
    "塑膠": {
        "growth_rate": 3.5,
        "terminal_growth": 1.8,
        "discount_rate": 7.5,
        "volatility": "中",
        "description": "傳統化工業，受原料價格波動影響"
    },
    "鋼鐵": {
        "growth_rate": 2.5,
        "terminal_growth": 1.5,
        "discount_rate": 8.0,
        "volatility": "高",
        "description": "週期性行業，受景氣循環影響較大"
    },
    "汽車": {
        "growth_rate": 4.5,
        "terminal_growth": 2.0,
        "discount_rate": 8.0,
        "volatility": "中高",
        "description": "消費製造業，受景氣與消費力影響"
    },
    "生技醫療": {
        "growth_rate": 10.0,     # 高成長行業
        "terminal_growth": 3.0,
        "discount_rate": 12.0,    # 高風險高報酬
        "volatility": "極高",
        "description": "高成長高風險行業，具備爆發性潛力"
    },
    "其他": {
        "growth_rate": 5.0,      # 預設值
        "terminal_growth": 2.0,
        "discount_rate": 8.0,
        "volatility": "中",
        "description": "一般行業預設參數"
    }
}

def get_industry_params(sector):
    """
    根據行業獲取適當的DCF參數
    
    Args:
        sector (str): 行業名稱
        
    Returns:
        dict: 包含growth_rate, terminal_growth, discount_rate的字典
    """
    # 正規化行業名稱
    sector_mapping = {
        "半導體": "半導體",
        "電子": "電子", 
        "金融": "金融",
        "銀行": "金融",
        "保險": "金融",
        "證券": "金融",
        "電信": "電信",
        "通訊": "電信",
        "塑膠": "塑膠",
        "化工": "塑膠",
        "鋼鐵": "鋼鐵",
        "汽車": "汽車",
        "運輸": "汽車",
        "生技": "生技醫療",
        "醫療": "生技醫療",
        "製藥": "生技醫療"
    }
    
    normalized_sector = sector_mapping.get(sector, "其他")
    return INDUSTRY_DCF_PARAMS.get(normalized_sector, INDUSTRY_DCF_PARAMS["其他"])

def get_adjusted_screening_params(sector, base_min_return=5.0):
    """
    根據行業調整篩選參數
    
    Args:
        sector (str): 行業名稱
        base_min_return (float): 基礎最低報酬率
        
    Returns:
        dict: 調整後的篩選參數
    """
    industry_params = get_industry_params(sector)
    
    # 根據行業風險調整最低報酬要求
    risk_adjustment = {
        "低": 0.7,      # 電信等低風險行業，降低報酬要求
        "中": 1.0,      # 一般行業
        "中高": 1.2,    # 製造業等
        "高": 1.5,      # 半導體、鋼鐵等高風險行業
        "極高": 2.0     # 生技等極高風險行業
    }
    
    volatility = industry_params.get("volatility", "中")
    adjustment_factor = risk_adjustment.get(volatility, 1.0)
    
    adjusted_min_return = base_min_return * adjustment_factor
    
    return {
        "min_potential_return": adjusted_min_return,
        "industry_params": industry_params,
        "risk_level": volatility
    }

# 行業分類映射
SECTOR_CATEGORIES = {
    "科技成長": ["半導體", "電子", "生技醫療"],
    "穩定收益": ["金融", "電信"],
    "週期性": ["鋼鐵", "塑膠", "汽車"],
    "其他": ["其他"]
}

def get_sector_category(sector):
    """獲取行業類別"""
    for category, sectors in SECTOR_CATEGORIES.items():
        if sector in sectors:
            return category
    return "其他"

# 個股特定的DCF參數調整
STOCK_SPECIFIC_ADJUSTMENTS = {    "2330": {  # 台積電
        "growth_rate": 20.0,     # AI晶片時代的超級成長（3-5年）
        "terminal_growth": 4.0,   # 長期仍能維持較高成長
        "discount_rate": 7.5,     # 降低風險溢價，反映龍頭地位
        "adjustment_reason": "全球晶圓代工龍頭，AI時代獨占優勢，技術護城河無可匹敵"
    },
    "2454": {  # 聯發科
        "growth_rate": 10.0,     # 5G和AIoT晶片成長潛力
        "terminal_growth": 3.0,
        "discount_rate": 9.0,
        "adjustment_reason": "5G和AIoT晶片領導者，成長潛力佳"
    },
    "2317": {  # 鴻海
        "growth_rate": 8.0,      # 電動車和雲端代工轉型
        "terminal_growth": 2.5,
        "discount_rate": 8.5,
        "adjustment_reason": "全球代工龍頭，積極轉型電動車和雲端業務"
    }
}

def get_stock_specific_params(stock_code: str, sector: str) -> Dict[str, Any]:
    """
    獲取個股特定的DCF參數
    優先使用個股調整，否則使用行業參數
    """
    if stock_code in STOCK_SPECIFIC_ADJUSTMENTS:
        stock_params = STOCK_SPECIFIC_ADJUSTMENTS[stock_code].copy()
        stock_params['source'] = 'stock_specific'
        return stock_params
    else:
        # 使用行業參數
        industry_params = get_industry_params(sector)
        industry_params['source'] = 'industry'
        industry_params['adjustment_reason'] = f"使用{sector}行業標準參數"
        return industry_params

def add_market_scenario_analysis():
    """為頂級股票添加市場情境分析"""
    
    # 市場情境參數
    MARKET_SCENARIOS = {
        "2330": {  # 台積電
            "AI樂觀": {
                "growth_rate": 25.0,
                "terminal_growth": 5.0,
                "discount_rate": 7.0,
                "description": "AI晶片需求爆發，台積電獨占高階市場"
            },
            "AI基準": {
                "growth_rate": 20.0,
                "terminal_growth": 4.0,
                "discount_rate": 7.5,
                "description": "AI需求穩定成長，保持技術領先"
            },
            "AI保守": {
                "growth_rate": 15.0,
                "terminal_growth": 3.0,
                "discount_rate": 8.5,
                "description": "AI成長趨緩，面臨更多競爭"
            }
        }
    }
    
    return MARKET_SCENARIOS

def calculate_scenario_dcf(fcf, shares_yi, scenario_params):
    """計算特定情境下的DCF估值"""
    growth = scenario_params['growth_rate']
    terminal = scenario_params['terminal_growth']
    discount = scenario_params['discount_rate']
    
    # 5年DCF計算
    total_pv = sum([fcf * (1 + growth/100)**year / (1 + discount/100)**year for year in range(1, 6)])
    
    # 終值
    terminal_fcf = fcf * (1 + growth/100)**5
    terminal_value = terminal_fcf * (1 + terminal/100) / ((discount/100) - (terminal/100))
    terminal_pv = terminal_value / (1 + discount/100)**5
    
    enterprise_value = total_pv + terminal_pv
    intrinsic_value = enterprise_value / shares_yi
    
    return {
        'enterprise_value': enterprise_value,
        'intrinsic_value': intrinsic_value,
        'total_pv': total_pv,
        'terminal_pv': terminal_pv
    }
