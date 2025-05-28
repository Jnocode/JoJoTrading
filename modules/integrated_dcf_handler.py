"""
Enhanced DCF Handler with integrated data validation and advanced features
This module provides the upgraded DCF calculation capabilities for JoJotrading Phase 1 optimization.
"""

from .data_validator import FinancialDataValidator
from .enhanced_dcf import EnhancedDCFModel

class IntegratedDCFHandler:
    """
    Integrated DCF handler that combines data validation with enhanced DCF calculations
    """
    
    def __init__(self):
        self.financial_validator = FinancialDataValidator()
        self.enhanced_dcf_model = EnhancedDCFModel()
        print("IntegratedDCFHandler initialized with validation and enhanced DCF capabilities")
    
    def calculate_dcf_valuation(self, stock_code, financials, risk_preference, context):
        """
        Main DCF calculation method with integrated validation and enhancement features
        
        Args:
            stock_code (str): Stock symbol
            financials (dict): Financial data from data_handler
            risk_preference (float): Risk preference/discount rate
            context (dict): Calculation context and parameters
            
        Returns:
            dict: DCF valuation results with validation metrics
        """
        print(f"  (IntegratedDCFHandler) 開始為股票 {stock_code} 進行增強版 DCF 估值...")
        
        # Phase 1: Data Validation
        print(f"  (IntegratedDCFHandler) 🔍 Phase 1: 執行財務數據品質驗證...")
        validation_result = self.financial_validator.validate_dcf_inputs(financials, stock_code)
        
        # Log validation results
        print(f"    (IntegratedDCFHandler) 驗證品質分數: {validation_result.overall_quality_score:.1f}/100")
        print(f"    (IntegratedDCFHandler) 錯誤數量: {validation_result.error_count}, 警告數量: {validation_result.warning_count}")
        
        # Check for critical errors that would prevent DCF calculation
        critical_errors = [issue for issue in validation_result.issues if issue.level == 'ERROR']
        if critical_errors:
            error_messages = [f"{issue.field}: {issue.message}" for issue in critical_errors]
            print(f"    (IntegratedDCFHandler) ❌ 嚴重錯誤阻止 DCF 計算: {'; '.join(error_messages)}")
            return {
                "stock_code": stock_code,
                "error": f"數據驗證失敗: {'; '.join(error_messages)}",
                "validation_score": validation_result.overall_quality_score,
                "data_quality": "POOR",
                "validation_issues": len(critical_errors)
            }
        
        # Continue with enhanced DCF if validation passes
        if validation_result.overall_quality_score >= 60:  # Minimum quality threshold
            print(f"  (IntegratedDCFHandler) 🚀 Phase 2: 執行增強版 DCF 估值計算...")
            
            # Prepare enhanced DCF inputs
            enhanced_inputs = self._prepare_enhanced_dcf_inputs(stock_code, financials, context)
            
            # Execute enhanced DCF with scenario analysis
            dcf_result = self.enhanced_dcf_model.calculate_dcf_with_scenarios(enhanced_inputs)
            
            # Add validation metrics to result
            dcf_result.update({
                'validation_score': validation_result.overall_quality_score,
                'data_quality': self._get_quality_rating(validation_result.overall_quality_score),
                'validation_warnings': [issue.message for issue in validation_result.issues if issue.level == 'WARNING'],
                'validation_info': [issue.message for issue in validation_result.issues if issue.level == 'INFO'],
                'enhanced_dcf_used': True
            })
            
            print(f"    (IntegratedDCFHandler) ✅ 增強版 DCF 完成，內在價值: {dcf_result.get('intrinsic_value_per_share', 'N/A')}")
            return dcf_result
        
        else:
            # Fall back to standard DCF if quality is moderate
            print(f"  (IntegratedDCFHandler) ⚠️ 數據品質中等({validation_result.overall_quality_score:.1f})，使用標準 DCF...")
            return self._calculate_standard_dcf_with_validation(stock_code, financials, risk_preference, context, validation_result)
    
    def _prepare_enhanced_dcf_inputs(self, stock_code, financials, context):
        """Prepare inputs for enhanced DCF calculation"""
        return {
            'stock_code': stock_code,
            'net_income': financials.get("net_income_parent"),
            'shares_outstanding': financials.get("shares_outstanding"),
            'capex': financials.get("capex"),
            'depreciation': (financials.get("depreciation", 0) or 0) + (financials.get("amortization", 0) or 0),
            'working_capital_change': self._calculate_working_capital_change(financials),
            'current_market_price': financials.get("current_market_price"),
            'risk_free_rate': context.get('risk_free_rate', 0.01),
            'market_premium': context.get('market_premium', 0.06),
            'beta': financials.get('beta', context.get('beta', 1.0)),
            'growth_rate_short': context.get('dcf_short_term_growth_rate', 0.07),
            'growth_rate_terminal': context.get('dcf_terminal_growth_rate', 0.025),
            'projection_years': context.get('dcf_projection_years', 5)
        }
    
    def _calculate_working_capital_change(self, financials):
        """Calculate working capital change for DCF"""
        ar_t0 = financials.get('ar_t0', 0) or 0
        inv_t0 = financials.get('inv_t0', 0) or 0
        ap_t0 = financials.get('ap_t0', 0) or 0
        ar_t1 = financials.get('ar_t1', 0) or 0
        inv_t1 = financials.get('inv_t1', 0) or 0
        ap_t1 = financials.get('ap_t1', 0) or 0
        
        wc_t0 = ar_t0 + inv_t0 - ap_t0
        wc_t1 = ar_t1 + inv_t1 - ap_t1
        
        return wc_t0 - wc_t1
    
    def _get_quality_rating(self, score):
        """Convert quality score to rating"""
        if score >= 85:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 55:
            return "FAIR"
        else:
            return "POOR"
    
    def _calculate_standard_dcf_with_validation(self, stock_code, financials, risk_preference, context, validation_result):
        """
        Standard DCF calculation with validation integration for lower quality data
        """
        print(f"    (IntegratedDCFHandler) 執行標準 DCF 計算 (含驗證整合)...")
        
        # Basic error checking
        if financials.get("error"):
            return {
                "stock_code": stock_code,
                "error": f"財務數據錯誤: {financials['error']}",
                "validation_score": validation_result.overall_quality_score,
                "data_quality": self._get_quality_rating(validation_result.overall_quality_score),
                "enhanced_dcf_used": False
            }
        
        # Extract core financial data
        net_income = financials.get("net_income_parent")
        shares_outstanding = financials.get("shares_outstanding")
        current_market_price = financials.get("current_market_price")
        
        # Basic validation
        if not net_income or not shares_outstanding or shares_outstanding <= 0:
            return {
                "stock_code": stock_code,
                "error": "核心財務數據不足",
                "validation_score": validation_result.overall_quality_score,
                "data_quality": self._get_quality_rating(validation_result.overall_quality_score),
                "enhanced_dcf_used": False
            }
        
        # Simple DCF calculation
        try:
            # Basic FCFE calculation
            capex = financials.get("capex", 0) or 0
            if capex < 0:
                capex = -capex  # Convert to positive
            
            depreciation = (financials.get("depreciation", 0) or 0) + (financials.get("amortization", 0) or 0)
            working_capital_change = self._calculate_working_capital_change(financials)
            
            fcfe = net_income - capex + depreciation - working_capital_change
            fcf_eps = fcfe / shares_outstanding
            
            # Simple DCF calculation
            growth_rate = context.get('dcf_short_term_growth_rate', 0.07)
            terminal_growth = context.get('dcf_terminal_growth_rate', 0.025)
            discount_rate = max(risk_preference, 0.05)  # Minimum 5% discount rate
            projection_years = context.get('dcf_projection_years', 5)
            
            # Ensure discount rate > terminal growth
            if discount_rate <= terminal_growth:
                terminal_growth = discount_rate * 0.8
            
            # Calculate present value of projected cash flows
            pv_fcf = 0
            current_fcf = fcf_eps
            for year in range(1, projection_years + 1):
                current_fcf *= (1 + growth_rate)
                pv_fcf += current_fcf / ((1 + discount_rate) ** year)
            
            # Terminal value
            terminal_fcf = current_fcf * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)
            
            intrinsic_value = pv_fcf + pv_terminal
            
            # Calculate potential return
            potential_return = None
            if current_market_price and current_market_price > 0:
                potential_return = (intrinsic_value / current_market_price) - 1
            
            return {
                "stock_code": stock_code,
                "intrinsic_value_per_share": round(intrinsic_value, 2),
                "current_market_price": current_market_price,
                "potential_return": round(potential_return, 4) if potential_return is not None else None,
                "calculated_fcf_eps": round(fcf_eps, 2),
                "used_discount_rate": discount_rate,
                "used_short_term_growth": growth_rate,
                "used_terminal_growth": terminal_growth,
                "validation_score": validation_result.overall_quality_score,
                "data_quality": self._get_quality_rating(validation_result.overall_quality_score),
                "validation_warnings": [issue.message for issue in validation_result.issues if issue.level == 'WARNING'],
                "enhanced_dcf_used": False
            }
            
        except Exception as e:
            print(f"    (IntegratedDCFHandler) 標準 DCF 計算錯誤: {str(e)}")
            return {
                "stock_code": stock_code,
                "error": f"DCF 計算錯誤: {str(e)}",
                "validation_score": validation_result.overall_quality_score,
                "data_quality": self._get_quality_rating(validation_result.overall_quality_score),
                "enhanced_dcf_used": False
            }

# Global instance for backward compatibility
integrated_dcf_handler = IntegratedDCFHandler()

def calculate_enhanced_dcf_valuation(stock_code, financials, risk_preference, context):
    """
    Wrapper function for backward compatibility with existing data_handler.py
    """
    return integrated_dcf_handler.calculate_dcf_valuation(stock_code, financials, risk_preference, context)
