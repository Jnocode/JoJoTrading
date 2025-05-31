"""
增強型 DCF 估值模型

此模組提供改進的 DCF 估值功能，包括：
1. 動態折現率計算（CAPM 模型）
2. 敏感性分析
3. 蒙地卡羅模擬
4. 情境分析
5. 詳細估值報告

主要功能：
- calculate_enhanced_dcf(): 增強 DCF 估值
- calculate_dynamic_discount_rate(): 動態折現率計算
- sensitivity_analysis(): 敏感性分析
- monte_carlo_simulatio        params = {
            'fcf_eps': fcf_eps,
            'short_term_growth': context.get('dcf_short_term_growth_rate', 0.10),  # 提高至 10% 適應台灣科技股
            'terminal_growth': terminal_growth,                                     # 動態調整的永續成長率
            'projection_years': context.get('dcf_projection_years', 5),
            'risk_preference': context.get('risk_preference', 0.07),               # 降低至 7% 適應台灣低利率環境
            'shares_outstanding': financial_data.get('shares_outstanding', 1),
            'current_market_price': financial_data.get('current_market_price')
        }模擬
- DCFResult: 詳細估值結果數據類別

技術特色：
- CAPM 模型動態折現率
- 多情境分析
- 風險調整
- 不確定性量化
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


@dataclass
class DCFScenario:
    """DCF 情境設定"""
    name: str
    short_term_growth: float
    terminal_growth: float
    probability: float = 1.0
    description: str = ""


@dataclass
class SensitivityResult:
    """敏感性分析結果"""
    parameter: str
    base_value: float
    test_values: List[float]
    resulting_valuations: List[float]
    elasticity: float  # 彈性係數


@dataclass
class MonteCarloResult:
    """蒙地卡羅模擬結果"""
    mean_valuation: float
    std_valuation: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    confidence_interval_95: Tuple[float, float]
    simulations: List[float]


@dataclass
class DCFResult:
    """增強型 DCF 估值結果"""
    stock_code: str
    base_case_valuation: float
    current_market_price: Optional[float]
    potential_return: Optional[float]
    
    # 估值組成
    pv_growth_stage: float
    pv_terminal_value: float
    terminal_value_percentage: float
    
    # 使用的參數
    fcf_eps: float
    discount_rate: float
    short_term_growth: float
    terminal_growth: float
    projection_years: int
    
    # 動態折現率組成
    risk_free_rate: Optional[float] = None
    beta: Optional[float] = None
    market_premium: Optional[float] = None
    
    # 情境分析
    scenarios: List[Tuple[str, float]] = field(default_factory=list)
    
    # 敏感性分析
    sensitivity_results: List[SensitivityResult] = field(default_factory=list)
    
    # 蒙地卡羅模擬
    monte_carlo_result: Optional[MonteCarloResult] = None
    
    # 品質指標
    valuation_confidence: float = 0.0  # 估值信心度 (0-100)
    data_quality_score: float = 0.0    # 輸入數據品質
    model_reliability: float = 0.0     # 模型可靠性


class EnhancedDCFModel:
    """增強型 DCF 估值模型"""
    
    def __init__(self):
        # 預設市場參數
        self.default_risk_free_rate = 0.015    # 1.5% 十年期公債利率
        self.default_market_premium = 0.06     # 6% 股權風險溢酬
        self.default_beta = 1.0                # 預設 Beta 值
          # 估值參數範圍
        self.parameter_ranges = {
            'short_term_growth': (-0.10, 0.30),   # -10% 到 30%
            'terminal_growth': (-0.02, 0.05),     # -2% 到 5%
            'discount_rate': (0.05, 0.20),        # 5% 到 20%
            'projection_years': (3, 10)           # 3 到 10 年
        }
          # 預設情境設定
        self.default_scenarios = [
            DCFScenario("樂觀", 0.15, 0.03, 0.25, "高成長情境"),
            DCFScenario("基準", 0.08, 0.025, 0.50, "合理成長情境"),
            DCFScenario("保守", 0.03, 0.015, 0.25, "低成長情境")
        ]

    def calculate_enhanced_dcf(
        self,
        stock_code: str = "TEST",
        financial_data: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        enable_dynamic_discount_rate: bool = True,
        enable_sensitivity_analysis: bool = True,
        enable_monte_carlo: bool = True,
        monte_carlo_simulations: int = 1000,
        **kwargs
    ) -> DCFResult:
        """
        增強型 DCF 估值計算
        
        Args:
            stock_code: 股票代碼
            financial_data: 財務數據
            context: 上下文參數
            enable_dynamic_discount_rate: 是否啟用動態折現率
            enable_sensitivity_analysis: 是否進行敏感性分析
            enable_monte_carlo: 是否進行蒙地卡羅模擬
            monte_carlo_simulations: 蒙地卡羅模擬次數
            **kwargs: 額外參數（支援測試格式）
            
        Returns:
            DCFResult: 詳細估值結果
        """
        
        # 處理測試腳本傳入的參數格式
        if financial_data is None and kwargs:
            # 如果傳入的是 kwargs 格式（測試模式）
            financial_data = {}
            context = context or {}
            
            # 從 kwargs 提取參數
            if 'revenue' in kwargs:
                # 使用營收計算基本財務指標
                revenue_list = kwargs['revenue']
                if isinstance(revenue_list, list) and len(revenue_list) > 0:
                    financial_data['net_income_parent'] = revenue_list[-1] * 0.1  # 假設10%淨利率
                    financial_data['shares_outstanding'] = kwargs.get('shares_outstanding', 100)
                    
            # 設定成長率和其他參數
            context.update({
                'dcf_short_term_growth_rate': kwargs.get('growth_rate', 0.05),
                'dcf_terminal_growth_rate': kwargs.get('terminal_growth_rate', 0.03),
                'risk_preference': kwargs.get('discount_rate', 0.10),
                'dcf_projection_years': kwargs.get('projection_years', 5)
            })
            
            # 假設基本現金流數據
            financial_data.update({
                'capex': kwargs.get('debt', 0) * 0.05,  # 假設資本支出
                'depreciation': kwargs.get('debt', 0) * 0.03,  # 假設折舊
                'ar_t0': 0, 'inv_t0': 0, 'ap_t0': 0,
                'ar_t1': 0, 'inv_t1': 0, 'ap_t1': 0
            })
        
        # 1. 準備基本參數
        base_params = self._prepare_base_parameters(financial_data, context)
        
        # 2. 計算動態折現率
        if enable_dynamic_discount_rate:
            discount_rate_info = self._calculate_dynamic_discount_rate(
                stock_code, financial_data, base_params['risk_preference']
            )
            base_params.update(discount_rate_info)
        
        # 3. 計算基準情境估值
        base_valuation, valuation_components = self._calculate_base_dcf(base_params)        # 4. 建立結果對象
        # 準備 DCFResult 所需的參數
        base_params_for_result = base_params.copy()
        current_market_price = base_params_for_result.pop('current_market_price', None)
        
        # 先計算潛在報酬
        potential_return = None
        if current_market_price and current_market_price > 0:
            potential_return = (base_valuation / current_market_price) - 1
        
        # 移除不屬於 DCFResult 的參數
        excluded_params = ['risk_preference', 'shares_outstanding']
        for param in excluded_params:
            base_params_for_result.pop(param, None)
        
        result = DCFResult(
            stock_code=stock_code,
            base_case_valuation=base_valuation,
            current_market_price=current_market_price,
            potential_return=potential_return,
            **valuation_components,
            **base_params_for_result
        )
        # 5. 情境分析
        result.scenarios = self._scenario_analysis(base_params)
        
        # 6. 敏感性分析
        if enable_sensitivity_analysis:
            result.sensitivity_results = self._sensitivity_analysis(base_params)
        
        # 7. 蒙地卡羅模擬
        if enable_monte_carlo:
            result.monte_carlo_result = self._monte_carlo_simulation(
                base_params, monte_carlo_simulations
            )
          # 8. 計算信心度指標
        result.valuation_confidence = self._calculate_valuation_confidence(result)
        result.model_reliability = self._calculate_model_reliability(base_params)
        
        return result

    def _prepare_base_parameters(self, financial_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """準備基本估值參數"""
        # 計算 FCF_EPS（從原始 data_handler 邏輯提取）
        fcf_eps = self._calculate_fcf_eps(financial_data)
        
                # 嘗試獲取即時 GDP 成長率作為永續成長率參考
        terminal_growth_base = context.get('dcf_terminal_growth_rate', 0.03)
        try:
            from .macro_data_handler import macro_data_handler
            gdp_growth = macro_data_handler.get_gdp_growth_rate()
            # 永續成長率通常設為 GDP 成長率的 80-120%
            terminal_growth_adjusted = min(gdp_growth * 1.0, 0.04)  # 最高不超過 4%
            print(f"  (EnhancedDCFModel) 基於GDP成長率調整永續成長率: {gdp_growth:.2%} -> {terminal_growth_adjusted:.2%}")
            terminal_growth = terminal_growth_adjusted
        except Exception as e:
            print(f"  (EnhancedDCFModel) ⚠️ 無法獲取GDP數據，使用預設永續成長率: {e}")
            terminal_growth = terminal_growth_base
        
        params = {
            'fcf_eps': fcf_eps,
            'short_term_growth': context.get('dcf_short_term_growth_rate', 0.10),  # 提高至 10% 適應台灣科技股
            'terminal_growth': terminal_growth,                                     # 動態調整的永續成長率
            'projection_years': context.get('dcf_projection_years', 5),
            'risk_preference': context.get('risk_preference', 0.07),               # 降低至 7% 適應台灣低利率環境
            'shares_outstanding': financial_data.get('shares_outstanding', 1),
            'current_market_price': financial_data.get('current_market_price')
        }
        
        return params

    def _calculate_fcf_eps(self, financial_data: Dict[str, Any]) -> float:
        """計算自由現金流每股盈餘（FCFE_EPS）- 針對台灣科技股優化"""
        
        try:
            # 基本財務數據
            net_income = float(financial_data.get('net_income_parent', 0))
            capex = float(financial_data.get('capex', 0))
            depreciation = float(financial_data.get('depreciation', 0))
            amortization = float(financial_data.get('amortization', 0))
            shares = float(financial_data.get('shares_outstanding', 1))
            
            # 營運資金變化計算
            ar_t0 = float(financial_data.get('ar_t0', 0) or 0)
            inv_t0 = float(financial_data.get('inv_t0', 0) or 0)
            ap_t0 = float(financial_data.get('ap_t0', 0) or 0)
            ar_t1 = float(financial_data.get('ar_t1', 0) or 0)
            inv_t1 = float(financial_data.get('inv_t1', 0) or 0)
            ap_t1 = float(financial_data.get('ap_t1', 0) or 0)
            
            wc_t0 = ar_t0 + inv_t0 - ap_t0
            wc_t1 = ar_t1 + inv_t1 - ap_t1
            delta_wc = wc_t0 - wc_t1
            
            # 調整後的資本支出處理 - 針對台灣科技股特性
            net_capex = capex - depreciation - amortization
            
            # 檢測是否為重資產科技股（資本支出佔營收比例高）
            revenue = float(financial_data.get('total_revenue', 0))
            if revenue > 0:
                capex_ratio = capex / revenue
                if capex_ratio > 0.15:  # 資本支出占營收超過15%視為重資產
                    # 對重資產科技股使用調整係數，只考慮維持性資本支出
                    maintenance_capex_ratio = 0.6  # 假設60%為維持性資本支出
                    net_capex = net_capex * maintenance_capex_ratio
                    print(f"  (FCF_EPS) 檢測到重資產特性，調整淨資本支出係數: {maintenance_capex_ratio}")
            
            # 限制營運資金變化的極端影響
            if abs(delta_wc) > net_income * 0.3:  # 營運資金變化不應超過淨利的30%
                delta_wc = delta_wc * 0.5  # 減半處理極端情況
                print(f"  (FCF_EPS) 營運資金變化過大，調整為: {delta_wc/1e8:.1f}億")
            
            # 假設淨借款為零（保守估計）
            net_borrowing = 0
            
            # FCFE 計算
            fcfe = net_income - net_capex - delta_wc + net_borrowing
            fcf_eps = fcfe / shares if shares > 0 else 0
            
            # 確保 FCF_EPS 不會過度負值（設置合理下限）
            if fcf_eps < -50:  # 每股自由現金流不應低於-50元
                fcf_eps = max(fcf_eps, net_income / shares * 0.3)  # 至少保留30%的淨利作為自由現金流
                print(f"  (FCF_EPS) 調整過度負值，設定為: {fcf_eps:.2f}")
            
            return fcf_eps
            
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0

    def _calculate_dynamic_discount_rate(
        self, 
        stock_code: str, 
        financial_data: Dict[str, Any], 
        fallback_rate: float
    ) -> Dict[str, Any]:
        """
        計算動態折現率（CAPM 模型）
        
        Returns:
            包含折現率組成的字典
        """
        
        try:
            # 嘗試獲取市場數據（這裡使用預設值，實際應用中可以連接市場數據API）
            risk_free_rate = self._get_risk_free_rate()
            market_premium = self._get_market_premium()
            beta = self._get_stock_beta(stock_code, financial_data)
            
            # CAPM: r = rf + β(rm - rf)
            discount_rate = risk_free_rate + beta * market_premium
              # 確保在合理範圍內
            discount_rate = max(0.05, min(0.25, discount_rate))
            
            return {
                'discount_rate': discount_rate,
                'risk_free_rate': risk_free_rate,
                'beta': beta,
                'market_premium': market_premium
            }
            
        except Exception:
            # 如果動態計算失敗，使用回退值
            return {
                'discount_rate': fallback_rate,
                'risk_free_rate': None,
                'beta': None,
                'market_premium': None
            }

    def _get_risk_free_rate(self) -> float:
        """獲取無風險利率（十年期公債利率）"""
        try:
            # 使用宏觀數據模組獲取即時公債殖利率
            from .macro_data_handler import macro_data_handler
            return macro_data_handler.get_risk_free_rate()
        except Exception as e:
            print(f"  (EnhancedDCFModel) ⚠️ 無法獲取即時無風險利率: {e}")
            # 回退到預設值
            return self.default_risk_free_rate

    def _get_market_premium(self) -> float:
        """獲取股權風險溢酬"""
        # 實際應用中應該根據歷史數據計算
        # 台灣股市風險溢酬通常在 5-8% 之間
        return self.default_market_premium

    def _get_stock_beta(self, stock_code: str, financial_data: Dict[str, Any]) -> float:
        """
        獲取或估算股票 Beta 值
        
        實際應用中應該：
        1. 從金融數據庫獲取計算好的 Beta
        2. 使用股價與市場指數的歷史數據計算
        3. 根據產業特性估算
        """
        
        # 根據產業特性提供 Beta 估值
        industry_betas = {
            "半導體": 1.3,
            "電子": 1.2,
            "金融": 0.8,
            "食品": 0.7,
            "化工": 1.1,
            "鋼鐵": 1.4,
            "營建": 1.2,
            "觀光": 1.5,
        }
        
        # 從財務數據中嘗試獲取產業資訊
        industry = financial_data.get('industry', '')
        for ind, beta in industry_betas.items():
            if ind in industry:
                return beta
        
        # 預設 Beta
        return self.default_beta

    def _calculate_base_dcf(self, params: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """計算基準 DCF 估值"""
        
        fcf_eps = params['fcf_eps']
        discount_rate = params['discount_rate']
        short_term_growth = params['short_term_growth']
        terminal_growth = params['terminal_growth']
        projection_years = params['projection_years']
        
        # 計算成長期現值
        pv_growth_stage = 0
        current_fcf = fcf_eps
        
        for year in range(1, projection_years + 1):
            current_fcf *= (1 + short_term_growth)
            pv = current_fcf / ((1 + discount_rate) ** year)
            pv_growth_stage += pv
        
        # 計算終值
        terminal_fcf = current_fcf * (1 + terminal_growth)
        
        # 防止分母為零或負數
        denominator = discount_rate - terminal_growth
        if denominator <= 0:
            terminal_value = current_fcf * 20  # 使用 20 倍作為保守估計
        else:
            terminal_value = terminal_fcf / denominator
        
        pv_terminal_value = terminal_value / ((1 + discount_rate) ** projection_years)
        
        # 總估值
        total_valuation = pv_growth_stage + pv_terminal_value
        
        # 終值佔比
        terminal_percentage = (pv_terminal_value / total_valuation * 100) if total_valuation > 0 else 0
        
        components = {
            'pv_growth_stage': pv_growth_stage,
            'pv_terminal_value': pv_terminal_value,
            'terminal_value_percentage': terminal_percentage,
        }
        
        return total_valuation, components

    def _scenario_analysis(self, base_params: Dict[str, Any]) -> List[Tuple[str, float]]:
        """情境分析"""
        scenarios = []
        
        for scenario in self.default_scenarios:
            params = base_params.copy()
            params['short_term_growth'] = scenario.short_term_growth
            params['terminal_growth'] = scenario.terminal_growth
            
            valuation, _ = self._calculate_base_dcf(params)
            scenarios.append((scenario.name, valuation))
        
        return scenarios

    def scenario_analysis(self, base_inputs: Dict[str, Any], scenarios: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        情景分析（測試腳本兼容方法）
        
        Args:
            base_inputs: 基礎輸入參數
            scenarios: 情景定義
            
        Returns:
            Dict[str, float]: 各情景的估值結果
        """
        results = {}
        
        for scenario_name, scenario_params in scenarios.items():
            # 合併參數
            scenario_inputs = base_inputs.copy()
            scenario_inputs.update(scenario_params)
            
            try:
                # 計算估值
                result = self.calculate_enhanced_dcf(**scenario_inputs)
                results[scenario_name] = result.base_case_valuation
            except Exception as e:
                print(f"  情景分析錯誤 ({scenario_name}): {e}")
                results[scenario_name] = 0.0
                
        return results

    def _sensitivity_analysis(self, base_params: Dict[str, Any]) -> List[SensitivityResult]:
        """敏感性分析"""
        results = []
        
        # 分析參數列表
        sensitivity_params = {
            'short_term_growth': [-0.02, -0.01, 0, 0.01, 0.02],  # ±2% 變化
            'terminal_growth': [-0.005, -0.0025, 0, 0.0025, 0.005],  # ±0.5% 變化
            'discount_rate': [-0.01, -0.005, 0, 0.005, 0.01],  # ±1% 變化
        }
        
        base_valuation, _ = self._calculate_base_dcf(base_params)
        
        for param, changes in sensitivity_params.items():
            base_value = base_params[param]
            test_values = [base_value + change for change in changes]
            valuations = []
            
            for test_value in test_values:
                params = base_params.copy()
                params[param] = test_value
                
                # 確保參數在合理範圍內
                if param in self.parameter_ranges:
                    min_val, max_val = self.parameter_ranges[param]
                    params[param] = max(min_val, min(max_val, test_value))
                
                valuation, _ = self._calculate_base_dcf(params)
                valuations.append(valuation)
            
            # 計算彈性係數
            elasticity = self._calculate_elasticity(
                test_values, valuations, base_value, base_valuation
            )
            
            results.append(SensitivityResult(
                parameter=param,
                base_value=base_value,
                test_values=test_values,
                resulting_valuations=valuations,
                elasticity=elasticity
            ))
        
        return results

    def monte_carlo_simulation(self, base_inputs: Dict[str, Any], n_simulations: int = 1000, volatility: float = 0.15) -> Dict[str, float]:
        """
        蒙地卡羅模擬（測試腳本兼容方法）
        
        Args:
            base_inputs: 基礎輸入參數
            n_simulations: 模擬次數
            volatility: 波動率
            
        Returns:
            Dict[str, float]: 模擬結果統計
        """
        import random
        
        valuations = []
        base_growth = base_inputs.get('growth_rate', 0.05)
        
        for _ in range(n_simulations):
            # 隨機調整成長率
            adjusted_growth = base_growth * (1 + random.gauss(0, volatility))
            
            # 構建模擬參數
            sim_inputs = base_inputs.copy()
            sim_inputs['growth_rate'] = max(0.01, adjusted_growth)  # 確保正值
            
            try:
                result = self.calculate_enhanced_dcf(**sim_inputs)
                valuations.append(result.base_case_valuation)
            except:
                valuations.append(0.0)
        
        # 計算統計指標
        valuations.sort()
        n = len(valuations)
        
        return {
            'mean': sum(valuations) / n,
            'std': (sum((v - sum(valuations)/n)**2 for v in valuations) / n) ** 0.5,
            'var_95': valuations[int(0.05 * n)] if n > 0 else 0.0,
            'percentile_25': valuations[int(0.25 * n)] if n > 0 else 0.0,
            'percentile_75': valuations[int(0.75 * n)] if n > 0 else 0.0
        }

    def _calculate_elasticity(
        self, 
        test_values: List[float], 
        valuations: List[float], 
        base_value: float, 
        base_valuation: float
    ) -> float:
        """計算彈性係數"""
        try:
            # 使用中間點方法計算彈性
            mid_idx = len(test_values) // 2
            if mid_idx > 0 and mid_idx < len(test_values) - 1:
                delta_param = (test_values[mid_idx + 1] - test_values[mid_idx - 1]) / base_value
                delta_valuation = (valuations[mid_idx + 1] - valuations[mid_idx - 1]) / base_valuation
                
                if delta_param != 0:
                    return delta_valuation / delta_param
            
            return 0.0
        except (ZeroDivisionError, IndexError):
            return 0.0

    def _monte_carlo_simulation(
        self, 
        base_params: Dict[str, Any], 
        num_simulations: int
    ) -> MonteCarloResult:
        """蒙地卡羅模擬"""
        
        valuations = []
        
        # 參數分布假設（常態分布）
        param_distributions = {
            'short_term_growth': {
                'mean': base_params['short_term_growth'],
                'std': 0.02  # 2% 標準差
            },
            'terminal_growth': {
                'mean': base_params['terminal_growth'],
                'std': 0.005  # 0.5% 標準差
            },
            'discount_rate': {
                'mean': base_params['discount_rate'],
                'std': 0.01  # 1% 標準差
            }
        }
        
        for _ in range(num_simulations):
            sim_params = base_params.copy()
            
            # 隨機生成參數
            for param, dist in param_distributions.items():
                random_value = np.random.normal(dist['mean'], dist['std'])
                
                # 確保在合理範圍內
                if param in self.parameter_ranges:
                    min_val, max_val = self.parameter_ranges[param]
                    random_value = max(min_val, min(max_val, random_value))
                
                sim_params[param] = random_value
            
            # 計算估值
            valuation, _ = self._calculate_base_dcf(sim_params)
            valuations.append(valuation)
        
        # 統計結果
        valuations = np.array(valuations)
        mean_val = np.mean(valuations)
        std_val = np.std(valuations)
        
        percentiles = np.percentile(valuations, [5, 25, 75, 95])
        confidence_95 = (percentiles[0], percentiles[3])
        
        return MonteCarloResult(
            mean_valuation=mean_val,
            std_valuation=std_val,
            percentile_5=percentiles[0],
            percentile_25=percentiles[1],
            percentile_75=percentiles[2],
            percentile_95=percentiles[3],
            confidence_interval_95=confidence_95,
            simulations=valuations.tolist()
        )

    def _calculate_valuation_confidence(self, result: DCFResult) -> float:
        """計算估值信心度"""
        confidence = 100.0
        
        # 基於敏感性分析的信心度調整
        if result.sensitivity_results:
            high_elasticity_count = sum(
                1 for sens in result.sensitivity_results 
                if abs(sens.elasticity) > 2.0
            )
            confidence -= high_elasticity_count * 15
        
        # 基於終值佔比的信心度調整
        if result.terminal_value_percentage > 80:
            confidence -= 20  # 終值佔比過高降低信心度
        elif result.terminal_value_percentage > 60:
            confidence -= 10
        
        # 基於蒙地卡羅模擬的信心度調整
        if result.monte_carlo_result:
            cv = result.monte_carlo_result.std_valuation / result.monte_carlo_result.mean_valuation
            if cv > 0.5:  # 變異係數過高
                confidence -= 25
            elif cv > 0.3:
                confidence -= 15
        
        return max(0, min(100, confidence))

    def _calculate_model_reliability(self, params: Dict[str, Any]) -> float:
        """計算模型可靠性"""
        reliability = 100.0
        
        # FCF_EPS 可靠性檢查
        if params['fcf_eps'] <= 0:
            reliability -= 30
        elif params['fcf_eps'] < 1:
            reliability -= 15
        
        # 參數合理性檢查
        if params['discount_rate'] > 0.20:
            reliability -= 20
        elif params['discount_rate'] < 0.05:
            reliability -= 15
        
        if abs(params['short_term_growth']) > 0.25:
            reliability -= 15
        
        if abs(params['terminal_growth']) > 0.05:
            reliability -= 10
        
        return max(0, min(100, reliability))

    def generate_detailed_report(self, result: DCFResult) -> Dict[str, Any]:
        """生成詳細估值報告"""
        
        report = {
            'basic_info': {
                'stock_code': result.stock_code,
                'valuation_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                'base_case_valuation': round(result.base_case_valuation, 2),
                'current_market_price': result.current_market_price,
                'potential_return': f"{result.potential_return:.2%}" if result.potential_return else "N/A"
            },
            
            'valuation_breakdown': {
                'growth_stage_pv': round(result.pv_growth_stage, 2),
                'terminal_value_pv': round(result.pv_terminal_value, 2),
                'terminal_value_percentage': f"{result.terminal_value_percentage:.1f}%"
            },
            
            'parameters_used': {
                'fcf_eps': round(result.fcf_eps, 4),
                'discount_rate': f"{result.discount_rate:.2%}",
                'short_term_growth': f"{result.short_term_growth:.2%}",
                'terminal_growth': f"{result.terminal_growth:.2%}",
                'projection_years': result.projection_years
            },
            
            'quality_metrics': {
                'valuation_confidence': f"{result.valuation_confidence:.1f}%",
                'data_quality_score': f"{result.data_quality_score:.1f}%",
                'model_reliability': f"{result.model_reliability:.1f}%"
            }
        }
        
        # 動態折現率資訊
        if result.risk_free_rate is not None:
            report['discount_rate_breakdown'] = {
                'risk_free_rate': f"{result.risk_free_rate:.2%}",
                'beta': round(result.beta, 2) if result.beta else "N/A",
                'market_premium': f"{result.market_premium:.2%}" if result.market_premium else "N/A"
            }
        
        # 情境分析
        if result.scenarios:
            report['scenario_analysis'] = {
                scenario_name: round(valuation, 2)
                for scenario_name, valuation in result.scenarios
            }
        
        # 敏感性分析摘要
        if result.sensitivity_results:
            report['sensitivity_summary'] = {
                sens.parameter: {
                    'elasticity': round(sens.elasticity, 2),
                    'valuation_range': [
                        round(min(sens.resulting_valuations), 2),
                        round(max(sens.resulting_valuations), 2)
                    ]
                }
                for sens in result.sensitivity_results
            }
        
        # 蒙地卡羅模擬摘要
        if result.monte_carlo_result:
            mc = result.monte_carlo_result
            report['monte_carlo_summary'] = {
                'mean_valuation': round(mc.mean_valuation, 2),
                'std_deviation': round(mc.std_valuation, 2),
                'confidence_95_interval': [
                    round(mc.confidence_interval_95[0], 2),
                    round(mc.confidence_interval_95[1], 2)
                ],
                'percentiles': {
                    '5%': round(mc.percentile_5, 2),
                    '25%': round(mc.percentile_25, 2),
                    '75%': round(mc.percentile_75, 2),
                    '95%': round(mc.percentile_95, 2)
                }
            }
        
        return report
