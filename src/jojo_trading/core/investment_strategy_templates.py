"""
投資策略模板系統
Investment Strategy Templates

提供多種預設投資策略的篩選條件模板
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class InvestmentStyle(Enum):
    """投資風格枚舉"""
    VALUE = "value"              # 價值投資
    GROWTH = "growth"            # 成長投資
    DEFENSIVE = "defensive"      # 防禦型投資
    CONTRARIAN = "contrarian"    # 逆勢投資
    MOMENTUM = "momentum"        # 動能投資
    DIVIDEND = "dividend"        # 股利投資
    QUALITY = "quality"          # 品質投資


@dataclass
class ScreeningCriteria:
    """篩選條件資料類別"""
    name: str
    description: str
    
    # 基本面條件
    min_market_cap: float = 0           # 最小市值（億元）
    max_pe_ratio: float = float('inf')  # 最大本益比
    min_pe_ratio: float = 0             # 最小本益比
    max_pb_ratio: float = float('inf')  # 最大股價淨值比
    min_pb_ratio: float = 0             # 最小股價淨值比
    min_roe: float = 0                  # 最小股東權益報酬率
    max_debt_ratio: float = 1.0         # 最大負債比率
    min_current_ratio: float = 0        # 最小流動比率
    
    # 成長性條件
    min_revenue_growth: float = -1.0    # 最小營收成長率
    min_eps_growth: float = -1.0        # 最小EPS成長率
    min_profit_growth: float = -1.0     # 最小獲利成長率
    
    # 股利條件
    min_dividend_yield: float = 0       # 最小股息率
    min_payout_ratio: float = 0         # 最小配息率
    max_payout_ratio: float = 1.0       # 最大配息率
    
    # 估值條件
    min_dcf_upside: float = 0           # 最小DCF上漲空間
    min_data_quality: float = 0         # 最小數據品質分數
    
    # 技術面條件（可選）
    price_trend: str = "any"            # 價格趨勢：up/down/any
    volume_trend: str = "any"           # 成交量趨勢：up/down/any


class InvestmentStrategyTemplates:
    """投資策略模板管理器"""
    
    def __init__(self):
        """初始化策略模板"""
        self.templates = self._create_default_templates()
    
    def _create_default_templates(self) -> Dict[str, ScreeningCriteria]:
        """創建預設策略模板"""
        
        templates = {}
        
        # 1. 價值投資策略
        templates[InvestmentStyle.VALUE.value] = ScreeningCriteria(
            name="價值投資策略",
            description="尋找被低估的穩健公司：低PE、高股息、穩定獲利",
            min_market_cap=50,          # 市值至少50億
            max_pe_ratio=18,            # PE < 18倍
            min_pe_ratio=5,             # PE > 5倍（避免虧損股）
            max_pb_ratio=2.5,           # PB < 2.5倍
            min_roe=0.08,               # ROE > 8%
            max_debt_ratio=0.6,         # 負債比 < 60%
            min_current_ratio=1.2,      # 流動比率 > 1.2
            min_dividend_yield=0.02,    # 股息率 > 2%
            min_dcf_upside=0.10,        # DCF上漲空間 > 10%
            min_data_quality=40         # 數據品質 > 40分
        )
        
        # 2. 成長投資策略
        templates[InvestmentStyle.GROWTH.value] = ScreeningCriteria(
            name="成長投資策略", 
            description="尋找高成長潛力公司：高成長率、創新產業、擴張中",
            min_market_cap=20,          # 市值至少20億
            max_pe_ratio=35,            # PE < 35倍（允許較高估值）
            min_roe=0.15,               # ROE > 15%
            max_debt_ratio=0.7,         # 負債比 < 70%
            min_revenue_growth=0.10,    # 營收成長 > 10%
            min_eps_growth=0.15,        # EPS成長 > 15%
            min_profit_growth=0.10,     # 獲利成長 > 10%
            min_dcf_upside=0.15,        # DCF上漲空間 > 15%
            min_data_quality=35,        # 數據品質 > 35分
            price_trend="up"            # 價格趨勢向上
        )
        
        # 3. 防禦型投資策略
        templates[InvestmentStyle.DEFENSIVE.value] = ScreeningCriteria(
            name="防禦型投資策略",
            description="尋找穩定抗跌股票：低波動、穩定現金流、民生必需",
            min_market_cap=100,         # 市值至少100億（大型股）
            max_pe_ratio=20,            # PE < 20倍
            min_pe_ratio=8,             # PE > 8倍
            max_pb_ratio=2.0,           # PB < 2.0倍
            min_roe=0.10,               # ROE > 10%
            max_debt_ratio=0.5,         # 負債比 < 50%（保守）
            min_current_ratio=1.5,      # 流動比率 > 1.5（充足現金）
            min_dividend_yield=0.03,    # 股息率 > 3%
            min_payout_ratio=0.3,       # 配息率 > 30%
            max_payout_ratio=0.8,       # 配息率 < 80%（保留盈餘）
            min_data_quality=50         # 數據品質 > 50分（高品質）
        )
        
        # 4. 逆勢投資策略
        templates[InvestmentStyle.CONTRARIAN.value] = ScreeningCriteria(
            name="逆勢投資策略",
            description="尋找被錯殺的品質公司：暫時困難但基本面良好",
            min_market_cap=30,          # 市值至少30億
            max_pe_ratio=15,            # PE < 15倍（被低估）
            min_pe_ratio=3,             # PE > 3倍（避免地雷股）
            max_pb_ratio=1.5,           # PB < 1.5倍（淨值以下）
            min_roe=0.05,               # ROE > 5%（基本獲利能力）
            max_debt_ratio=0.7,         # 負債比 < 70%
            min_current_ratio=1.0,      # 流動比率 > 1.0
            min_revenue_growth=-0.1,    # 營收成長 > -10%（衰退有限）
            min_dcf_upside=0.20,        # DCF上漲空間 > 20%（大幅低估）
            min_data_quality=35,        # 數據品質 > 35分
            price_trend="down"          # 價格趨勢向下（逆勢）
        )
        
        # 5. 動能投資策略
        templates[InvestmentStyle.MOMENTUM.value] = ScreeningCriteria(
            name="動能投資策略",
            description="追逐市場熱點：業績爆發、價格突破、資金追捧",
            min_market_cap=10,          # 市值至少10億（包含中小型股）
            max_pe_ratio=50,            # PE < 50倍（允許高估值）
            min_roe=0.12,               # ROE > 12%
            min_revenue_growth=0.15,    # 營收成長 > 15%
            min_eps_growth=0.25,        # EPS成長 > 25%（業績爆發）
            min_profit_growth=0.20,     # 獲利成長 > 20%
            min_dcf_upside=0.10,        # DCF上漲空間 > 10%
            min_data_quality=30,        # 數據品質 > 30分
            price_trend="up",           # 價格趨勢向上
            volume_trend="up"           # 成交量增加
        )
        
        # 6. 股利投資策略
        templates[InvestmentStyle.DIVIDEND.value] = ScreeningCriteria(
            name="股利投資策略",
            description="追求穩定現金流：高股息、穩定配息、現金充裕",
            min_market_cap=50,          # 市值至少50億
            max_pe_ratio=25,            # PE < 25倍
            min_pe_ratio=6,             # PE > 6倍
            max_pb_ratio=3.0,           # PB < 3.0倍
            min_roe=0.08,               # ROE > 8%
            max_debt_ratio=0.6,         # 負債比 < 60%
            min_current_ratio=1.2,      # 流動比率 > 1.2
            min_dividend_yield=0.04,    # 股息率 > 4%（高股息）
            min_payout_ratio=0.4,       # 配息率 > 40%
            max_payout_ratio=0.9,       # 配息率 < 90%（可持續）
            min_data_quality=45         # 數據品質 > 45分
        )
        
        # 7. 品質投資策略
        templates[InvestmentStyle.QUALITY.value] = ScreeningCriteria(
            name="品質投資策略",
            description="尋找優質企業：高ROE、低負債、穩定成長、護城河",
            min_market_cap=100,         # 市值至少100億（大型優質股）
            max_pe_ratio=30,            # PE < 30倍
            min_pe_ratio=10,            # PE > 10倍
            max_pb_ratio=4.0,           # PB < 4.0倍
            min_roe=0.18,               # ROE > 18%（高獲利能力）
            max_debt_ratio=0.4,         # 負債比 < 40%（低負債）
            min_current_ratio=1.5,      # 流動比率 > 1.5
            min_revenue_growth=0.05,    # 營收成長 > 5%（穩定成長）
            min_eps_growth=0.08,        # EPS成長 > 8%
            min_dividend_yield=0.01,    # 股息率 > 1%
            min_dcf_upside=0.05,        # DCF上漲空間 > 5%
            min_data_quality=60         # 數據品質 > 60分（高品質）
        )
        
        return templates
    
    def get_template(self, strategy: str) -> ScreeningCriteria:
        """獲取策略模板"""
        return self.templates.get(strategy, self.templates[InvestmentStyle.VALUE.value])
    
    def get_all_templates(self) -> Dict[str, ScreeningCriteria]:
        """獲取所有策略模板"""
        return self.templates.copy()
    
    def get_template_names(self) -> List[str]:
        """獲取所有策略名稱"""
        return [template.name for template in self.templates.values()]
    
    def get_template_descriptions(self) -> Dict[str, str]:
        """獲取策略描述"""
        return {
            template.name: template.description 
            for template in self.templates.values()
        }
    
    def create_custom_template(
        self, 
        name: str, 
        description: str, 
        **criteria
    ) -> ScreeningCriteria:
        """創建自訂策略模板"""
        
        template = ScreeningCriteria(
            name=name,
            description=description,
            **criteria
        )
        
        # 添加到模板庫
        self.templates[name.lower().replace(" ", "_")] = template
        
        return template
    
    def apply_template_to_screening(
        self, 
        template: ScreeningCriteria,
        stock_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """應用策略模板進行篩選"""
        
        filtered_stocks = []
        
        for stock in stock_data:
            if self._meets_criteria(stock, template):
                # 計算策略適合度分數
                score = self._calculate_strategy_score(stock, template)
                stock['strategy_score'] = score
                stock['strategy_name'] = template.name
                filtered_stocks.append(stock)
        
        # 按策略分數排序
        filtered_stocks.sort(key=lambda x: x.get('strategy_score', 0), reverse=True)
        
        return filtered_stocks
    
    def _meets_criteria(self, stock: Dict[str, Any], criteria: ScreeningCriteria) -> bool:
        """檢查股票是否符合策略條件"""
        
        try:
            # 市值檢查
            market_cap = stock.get('market_cap', 0) / 1e8  # 轉換為億元
            if market_cap < criteria.min_market_cap:
                return False
            
            # 本益比檢查
            pe_ratio = stock.get('pe_ratio', 0)
            if not (criteria.min_pe_ratio <= pe_ratio <= criteria.max_pe_ratio):
                return False
            
            # 股價淨值比檢查
            pb_ratio = stock.get('pb_ratio', 0)
            if not (criteria.min_pb_ratio <= pb_ratio <= criteria.max_pb_ratio):
                return False
            
            # ROE檢查
            roe = stock.get('roe', 0)
            if roe < criteria.min_roe:
                return False
            
            # 負債比檢查
            debt_ratio = stock.get('debt_ratio', 0)
            if debt_ratio > criteria.max_debt_ratio:
                return False
            
            # 流動比率檢查
            current_ratio = stock.get('current_ratio', 0)
            if current_ratio < criteria.min_current_ratio:
                return False
            
            # 成長率檢查
            revenue_growth = stock.get('revenue_growth', 0)
            if revenue_growth < criteria.min_revenue_growth:
                return False
            
            eps_growth = stock.get('eps_growth', 0)
            if eps_growth < criteria.min_eps_growth:
                return False
            
            # 股息率檢查
            dividend_yield = stock.get('dividend_yield', 0)
            if dividend_yield < criteria.min_dividend_yield:
                return False
            
            # DCF上漲空間檢查
            dcf_upside = stock.get('dcf_upside', 0)
            if dcf_upside < criteria.min_dcf_upside:
                return False
            
            # 數據品質檢查
            data_quality = stock.get('data_quality_score', 0)
            if data_quality < criteria.min_data_quality:
                return False
            
            return True
            
        except Exception as e:
            print(f"篩選條件檢查錯誤: {e}")
            return False
    
    def _calculate_strategy_score(self, stock: Dict[str, Any], criteria: ScreeningCriteria) -> float:
        """計算策略適合度分數（0-100分）"""
        
        try:
            score = 0
            max_score = 0
            
            # 基本面分數（40分）
            max_score += 40
            
            # ROE分數（最高15分）
            roe = stock.get('roe', 0)
            if criteria.name == "品質投資策略":
                score += min(15, roe * 75)  # ROE 20% = 15分
            else:
                score += min(10, roe * 50)  # ROE 20% = 10分
            
            # PE分數（最高10分）
            pe_ratio = stock.get('pe_ratio', 0)
            if pe_ratio > 0:
                # 低PE較好，15倍PE = 10分
                score += max(0, min(10, (25 - pe_ratio) / 2))
            
            # 負債比分數（最高10分）
            debt_ratio = stock.get('debt_ratio', 0)
            score += max(0, (1 - debt_ratio) * 10)  # 負債比越低越好
            
            # 股息分數（最高5分）
            dividend_yield = stock.get('dividend_yield', 0)
            if criteria.min_dividend_yield > 0:
                score += min(5, dividend_yield * 100)  # 5%股息率 = 5分
            
            # 成長性分數（30分）
            max_score += 30
            
            # 營收成長分數（最高10分）
            revenue_growth = stock.get('revenue_growth', 0)
            if criteria.min_revenue_growth > 0:
                score += min(10, max(0, revenue_growth * 50))  # 20%成長 = 10分
            
            # EPS成長分數（最高15分）
            eps_growth = stock.get('eps_growth', 0)
            if criteria.min_eps_growth > 0:
                score += min(15, max(0, eps_growth * 50))  # 30%成長 = 15分
            
            # 獲利成長分數（最高5分）
            profit_growth = stock.get('profit_growth', 0)
            if criteria.min_profit_growth > 0:
                score += min(5, max(0, profit_growth * 25))  # 20%成長 = 5分
            
            # 估值分數（20分）
            max_score += 20
            
            # DCF上漲空間分數（最高15分）
            dcf_upside = stock.get('dcf_upside', 0)
            score += min(15, dcf_upside * 50)  # 30%上漲空間 = 15分
            
            # PB比分數（最高5分）
            pb_ratio = stock.get('pb_ratio', 0)
            if pb_ratio > 0:
                score += max(0, min(5, (3 - pb_ratio) * 2.5))  # PB 1倍 = 5分
            
            # 數據品質分數（10分）
            max_score += 10
            data_quality = stock.get('data_quality_score', 0)
            score += (data_quality / 100) * 10
            
            # 計算百分比分數
            final_score = (score / max_score) * 100 if max_score > 0 else 0
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            print(f"策略分數計算錯誤: {e}")
            return 0


# 創建全域實例
investment_strategy_templates = InvestmentStrategyTemplates()
