"""
整合DCF處理器
統一處理所有DCF相關計算
"""

from .enhanced_dcf import EnhancedDCFModel
from ..utils.data_validator import FinancialDataValidator

class IntegratedDCFHandler:
    """整合DCF處理器類別"""
    
    def __init__(self):
        """初始化處理器"""
        try:
            self.validator = FinancialDataValidator()
            self.dcf_model = EnhancedDCFModel()
        except Exception as e:
            print(f"⚠️ IntegratedDCFHandler 初始化警告: {e}")
            self.validator = None
            self.dcf_model = None
    
    def calculate_fcf(self, financials):
        """
        嘗試計算自由現金流 (Simplified FCFE)
        FCF = Net Income + D&A - Capex
        """
        try:
            net_income = financials.get('net_income_parent', 0)
            depreciation = financials.get('depreciation', 0)
            amortization = financials.get('amortization', 0)
            capex = financials.get('capex', 0)
            
            # 檢查必要數據是否存在且合理
            # 注意: Capex 通常為正值 (在 AutoDataFetcher 中已轉為絕對值)
            if capex == 0 and depreciation == 0:
                return None
                
            # 簡易 FCF 計算
            fcf = net_income + depreciation + amortization - capex
            return fcf
        except Exception:
            return None

    def calculate_dcf_valuation(self, stock_code, financials, risk_preference, context):
        """
        計算DCF估值
        
        Args:
            stock_code: 股票代碼
            financials: 財務數據
            risk_preference: 風險偏好
            context: 計算上下文
            
        Returns:
            dict: DCF估值結果
        """
        if not self.validator or not self.dcf_model:
            return {
                'stock_code': stock_code,
                'intrinsic_value_per_share': 0,
                'error': 'Handler not properly initialized'
            }
        
        try:
            # 1. 提取基礎數據
            net_income = financials.get('net_income_parent', 0)
            shares_outstanding = financials.get('shares_outstanding', 1)
            current_price = financials.get('current_market_price', 0)
            
            # 2. 嘗試計算自由現金流 (FCF)
            fcf = self.calculate_fcf(financials)
            
            # 3. 決定估值基礎 (FCF vs EPS)
            valuation_basis = 'EPS'
            base_value_per_share = 0
            quality_note = ""
            
            eps = net_income / shares_outstanding if shares_outstanding > 0 else 0
            
            if fcf is not None and fcf > 0:
                # 如果有正的 FCF，優先使用 FCF
                fcf_per_share = fcf / shares_outstanding if shares_outstanding > 0 else 0
                base_value_per_share = fcf_per_share
                valuation_basis = 'FCF'
                quality_note = "使用自由現金流(FCF)進行估值，較為嚴謹。"
            else:
                # 否則退回使用 EPS (Earnings Model)
                base_value_per_share = eps
                valuation_basis = 'EPS'
                if fcf is not None and fcf < 0:
                    quality_note = "注意：公司自由現金流為負，改用 EPS 估值，風險較高。"
                else:
                    quality_note = "缺乏現金流數據，使用 EPS 估值 (Discounted Earnings)。"

            # 4. 設定參數
            growth_rate = context.get('dcf_short_term_growth_rate', 0.08)
            terminal_growth = context.get('dcf_terminal_growth_rate', 0.03)
            
            # 根據風險偏好設定折現率
            risk_rates = {
                'conservative': 0.12,  # 保守：12%
                'moderate': 0.10,      # 中等：10%
                'aggressive': 0.08     # 積極：8%
            }
            discount_rate = risk_rates.get(risk_preference, 0.10)
            
            # 如果是用 EPS 估值，建議提高折現率以反映風險 (Earnings != Cash)
            if valuation_basis == 'EPS':
                discount_rate += 0.01  # 加 1% 風險溢價
                quality_note += " (已增加 1% 折現率作為安全邊際)"

            # 5. 執行折現計算 (Base Case)
            base_result = self._compute_pv_model(
                base_value_per_share, growth_rate, terminal_growth, discount_rate
            )
            total_pv = base_result['total_pv']
            
            # 計算潛在回報
            potential_return = None
            if current_price and current_price > 0:
                potential_return = (total_pv / current_price) - 1

            # 6. 情境分析 (Scenario Analysis)
            scenarios = self._calculate_scenarios(
                base_value_per_share, growth_rate, terminal_growth, discount_rate, current_price
            )
            
            return {
                'stock_code': stock_code,
                'intrinsic_value_per_share': round(total_pv, 2),
                'current_market_price': current_price,
                'potential_return': round(potential_return, 4) if potential_return else None,
                'calculation_method': f'integrated_dcf_{valuation_basis.lower()}',
                'valuation_basis': valuation_basis,
                'quality_note': quality_note,
                'used_discount_rate': round(discount_rate, 3),
                'used_growth_rate': growth_rate,
                'used_terminal_growth': terminal_growth,
                'scenarios': scenarios  # 新增情境分析結果
            }
            
        except Exception as e:
            return {
                'stock_code': stock_code,
                'intrinsic_value_per_share': 0,
                'error': f'Integrated DCF calculation error: {str(e)}'
            }

    def _compute_pv_model(self, current_value, growth_rate, terminal_growth, discount_rate, projection_years=5):
        """計算單一 DCF 模型的現值"""
        total_pv = 0
        
        # 5年預測
        for year in range(1, projection_years + 1):
            future_value = current_value * ((1 + growth_rate) ** year)
            pv = future_value / ((1 + discount_rate) ** year)
            total_pv += pv
        
        # 終值計算
        terminal_value_future = current_value * ((1 + growth_rate) ** projection_years) * (1 + terminal_growth)
        # 防止分母為負或過小
        denominator = max(discount_rate - terminal_growth, 0.01)
        terminal_value = terminal_value_future / denominator
        terminal_pv = terminal_value / ((1 + discount_rate) ** projection_years)
        
        total_pv += terminal_pv
        return {'total_pv': total_pv}

    def _calculate_scenarios(self, base_value, base_growth, terminal_growth, base_discount, current_price):
        """計算 悲觀/基本/樂觀 三種情境"""
        
        # 定義情境參數
        cases = {
            'bear': {'growth': base_growth - 0.02, 'discount': base_discount + 0.01, 'label': '悲觀情境'},
            'base': {'growth': base_growth,       'discount': base_discount,       'label': '基本情境'},
            'bull': {'growth': base_growth + 0.02, 'discount': base_discount - 0.01, 'label': '樂觀情境'}
        }
        
        results = {}
        for key, params in cases.items():
            # 確保參數合理
            g = params['growth']
            d = params['discount']
            
            pv = self._compute_pv_model(base_value, g, terminal_growth, d)['total_pv']
            upside = (pv / current_price - 1) if current_price > 0 else 0
            
            results[key] = {
                'label': params['label'],
                'value': round(pv, 2),
                'upside': round(upside, 4),
                'growth_used': round(g, 3),
                'discount_used': round(d, 3)
            }
            
        return results

def calculate_enhanced_dcf_valuation(stock_code, financial_data, **kwargs):
    """
    計算增強型DCF估值（向後相容）
    
    Args:
        stock_code: 股票代碼
        financial_data: 財務數據
        **kwargs: 其他參數
        
    Returns:
        dict: DCF估值結果
    """
    handler = IntegratedDCFHandler()
    return handler.calculate_dcf_valuation(
        stock_code, financial_data, 
        kwargs.get('risk_preference', 0.08),
        kwargs
    )

# 建立全域實例以供向後相容
integrated_dcf_handler = IntegratedDCFHandler()
