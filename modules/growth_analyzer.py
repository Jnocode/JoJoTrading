"""
JoJotrading 成長股分析模組

此模組提供成長股判定和篩選功能，支援多種財務指標的評估：
- 營收複合年成長率 (Revenue CAGR)
- 每股盈餘複合年成長率 (EPS CAGR)  
- 股東權益報酬率 (ROE)
- 自訂條件組合邏輯 (AND/OR)

主要功能：
- GrowthCriterion: 定義單一成長指標條件
- GrowthCriteriaSet: 組合多個條件與邏輯運算
- evaluate_growth_potential: 評估股票成長潛力

範例用法：
    from modules.growth_analyzer import evaluate_growth_potential, GrowthCriterion
    
    criteria = [
        GrowthCriterion('revenue_cagr', period_years=3, threshold=0.15),
        GrowthCriterion('roe', threshold=0.12)
    ]
    
    result = evaluate_growth_potential(financial_data, criteria, 'AND')
"""

from dataclasses import dataclass
from typing import List, Optional, Callable, Any, Dict, Union

@dataclass
class GrowthCriterion:
    metric_name: str           # 指標名稱，例如 'revenue_cagr', 'eps_cagr', 'roe'
    period_years: Optional[int] = None  # 計算週期（如CAGR的年數），部分指標可為None
    threshold: float = 0.0     # 閾值，例如 0.15 代表 15%
    operator: str = '>'        # 比較運算符：'>'、'>='、'<'、'<='、'=='
    label: Optional[str] = None  # UI顯示用說明文字

@dataclass
class GrowthCriteriaSet:
    criteria: List[GrowthCriterion]
    logic_operator: str = 'AND'  # 'AND' 或 'OR'

# 範例：預設條件組合
DEFAULT_CRITERIA = [
    GrowthCriterion(
        metric_name='revenue_cagr',
        period_years=3,
        threshold=0.15,
        operator='>',
        label='近3年營收CAGR > 15%'
    ),
    GrowthCriterion(
        metric_name='eps_cagr',
        period_years=3,
        threshold=0.15,
        operator='>',
        label='近3年EPS CAGR > 15%'
    ),
    GrowthCriterion(
        metric_name='roe',
        period_years=None,
        threshold=0.15,
        operator='>',
        label='最新一期ROE > 15%'
    ),
]

DEFAULT_CRITERIA_SET = GrowthCriteriaSet(
    criteria=DEFAULT_CRITERIA,
    logic_operator='AND'
)

def calculate_cagr(values: List[float], years: int) -> Optional[float]:
    """
    計算年複合成長率（CAGR）。
    :param values: 依時間序列由舊到新（如 [2020, 2021, 2022]），至少需兩個數值
    :param years: 期數（如3年）
    :return: CAGR 百分比（如0.15代表15%），若資料不足或數值異常則回傳 None
    """
    if not values or len(values) < 2 or years <= 0:
        return None
    try:
        start = values[0]
        end = values[-1]
        if start is None or end is None or start <= 0:
            return None
        cagr = (end / start) ** (1 / years) - 1
        return cagr
    except Exception:
        return None

def get_revenue_cagr(financial_data: Dict, years: int) -> Optional[float]:
    """
    從財報資料計算近N年營收CAGR。
    :param financial_data: 結構化財報資料，需包含 'revenue' 欄位（list，舊到新）
    :param years: 計算年數
    :return: CAGR 百分比，資料不足回傳 None
    """
    revenue_list = financial_data.get("revenue")
    if not revenue_list or len(revenue_list) < years + 1:
        return None
    values = revenue_list[-(years+1):]
    return calculate_cagr(values, years)

def get_eps_cagr(financial_data: Dict, years: int) -> Optional[float]:
    """
    從財報資料計算近N年EPS CAGR。
    :param financial_data: 結構化財報資料，需包含 'eps' 欄位（list，舊到新）
    :param years: 計算年數
    :return: CAGR 百分比，資料不足回傳 None
    """
    eps_list = financial_data.get("eps")
    if not eps_list or len(eps_list) < years + 1:
        return None
    values = eps_list[-(years+1):]
    return calculate_cagr(values, years)

def get_latest_roe(financial_data: Dict) -> Optional[float]:
    """
    取得最新一期ROE。
    :param financial_data: 結構化財報資料，需包含 'roe' 欄位（list，舊到新）
    :return: 最新一期ROE，資料不足回傳 None
    """
    roe_list = financial_data.get("roe")
    if not roe_list or len(roe_list) == 0:
        return None
    return roe_list[-1]

def get_latest_gross_profit_margin(financial_data: Dict) -> Optional[float]:
    """
    取得最新一期毛利率。
    :param financial_data: 結構化財報資料，需包含 'gross_profit_margin' 欄位（list，舊到新）
    :return: 最新一期毛利率，資料不足回傳 None
    """
    margin_list = financial_data.get("gross_profit_margin")
    if not margin_list or len(margin_list) == 0:
        return None
    return margin_list[-1]

def get_latest_operating_income_margin(financial_data: Dict) -> Optional[float]:
    """
    取得最新一期營業利益率。
    :param financial_data: 結構化財報資料，需包含 'operating_income_margin' 欄位（list，舊到新）
    :return: 最新一期營業利益率，資料不足回傳 None
    """
    margin_list = financial_data.get("operating_income_margin")
    if not margin_list or len(margin_list) == 0:
        return None
    return margin_list[-1]

def get_latest_net_profit_margin(financial_data: Dict) -> Optional[float]:
    """
    取得最新一期稅後淨利率。
    :param financial_data: 結構化財報資料，需包含 'net_profit_margin' 欄位（list，舊到新）
    :return: 最新一期稅後淨利率，資料不足回傳 None
    """
    margin_list = financial_data.get("net_profit_margin")
    if not margin_list or len(margin_list) == 0:
        return None
    return margin_list[-1]

def evaluate_growth_potential(
    financial_data: Dict,
    criteria_config: List[GrowthCriterion],
    logic_operator: str = "AND"
) -> Dict[str, Any]:
    """
    綜合評估單一股票是否為成長股，並回傳詳細條件結果。
    :param financial_data: 單一股票的結構化財報資料
    :param criteria_config: 成長條件列表
    :param logic_operator: 'AND' 或 'OR'
    :return: {
        'is_growth_stock': bool,
        'details': List[Dict]  # 每個條件的檢查結果
    }
    """
    # 指標名稱對應到計算函數
    metric_func_map = {
        "revenue_cagr": get_revenue_cagr,
        "eps_cagr": get_eps_cagr,
        "roe": get_latest_roe,
        "gross_profit_margin": get_latest_gross_profit_margin,
        "operating_income_margin": get_latest_operating_income_margin,
        "net_profit_margin": get_latest_net_profit_margin,
    }

    results = []
    pass_list = []
    for criterion in criteria_config:
        func = metric_func_map.get(criterion.metric_name)
        value = None
        if func:
            if criterion.period_years is not None:
                value = func(financial_data, criterion.period_years)
            else:
                value = func(financial_data)
        status = "數據不足"
        passed = False
        if value is not None:
            try:
                if criterion.operator == ">":
                    passed = value > criterion.threshold
                elif criterion.operator == ">=":
                    passed = value >= criterion.threshold
                elif criterion.operator == "<":
                    passed = value < criterion.threshold
                elif criterion.operator == "<=":
                    passed = value <= criterion.threshold
                elif criterion.operator == "==":
                    passed = value == criterion.threshold
                status = "通過" if passed else "未通過"
            except Exception:
                status = "數據錯誤"
        results.append({
            "criterion": criterion.label or criterion.metric_name,
            "value": value,
            "status": status
        })
        pass_list.append(passed if value is not None else None)

    # AND/OR 組合邏輯
    valid_results = [p for p in pass_list if p is not None]
    if not valid_results:
        is_growth_stock = False
    elif logic_operator.upper() == "AND":
        is_growth_stock = all(valid_results) and len(valid_results) == len(pass_list)
    elif logic_operator.upper() == "OR":
        is_growth_stock = any(valid_results)
    else:
        is_growth_stock = False

    return {
        "is_growth_stock": is_growth_stock,
        "details": results
    }
