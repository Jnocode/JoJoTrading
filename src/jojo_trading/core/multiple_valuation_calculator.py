"""
多重估值計算器
Enhanced Multi-Valuation Calculator

提供DCF、PE、PB、EV/EBITDA等多種估值方法的整合計算
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np


class MultipleValuationCalculator:
    """多重估值計算器"""
    
    def __init__(self):
        """初始化多重估值計算器"""
        self.valuation_methods = {
            'dcf': self._calculate_dcf_valuation,
            'pe': self._calculate_pe_valuation,
            'pb': self._calculate_pb_valuation,
            'ev_ebitda': self._calculate_ev_ebitda_valuation,
            'dividend_yield': self._calculate_dividend_valuation
        }
    
    def calculate_all_valuations(
        self, 
        stock_data: Dict[str, Any],
        market_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        計算所有估值方法的結果
        
        Args:
            stock_data: 個股財務數據
            market_data: 市場/同業數據
            
        Returns:
            Dict: 包含所有估值結果的字典
        """
        results = {}
        current_price = stock_data.get('current_market_price', 0)
        
        for method, calculator in self.valuation_methods.items():
            try:
                valuation = calculator(stock_data, market_data)
                results[method] = {
                    'value': valuation,
                    'upside': (valuation / current_price - 1) if current_price > 0 else 0,
                    'method_weight': self._get_method_weight(method, stock_data)
                }
            except Exception as e:
                results[method] = {
                    'value': 0,
                    'upside': 0,
                    'error': str(e),
                    'method_weight': 0
                }
        
        # 計算加權平均估值
        results['consensus'] = self._calculate_consensus_valuation(results, current_price)
        
        return results
    
    def _calculate_dcf_valuation(
        self, 
        stock_data: Dict[str, Any], 
        market_data: Dict[str, Any] = None
    ) -> float:
        """計算DCF估值"""
        try:
            # 基本參數
            net_income = stock_data.get('net_income_parent', 0)
            shares_outstanding = stock_data.get('shares_outstanding', 1)
            growth_rate = 0.08  # 預設8%成長率
            terminal_growth = 0.03  # 預設3%永續成長率
            discount_rate = 0.10  # 預設10%折現率
            
            # 計算每股自由現金流（簡化版：假設為淨利的80%）
            fcf_per_share = (net_income * 0.8) / shares_outstanding if shares_outstanding > 0 else 0
            
            # 5年預測期現值
            total_pv = 0
            for year in range(1, 6):
                future_fcf = fcf_per_share * ((1 + growth_rate) ** year)
                pv = future_fcf / ((1 + discount_rate) ** year)
                total_pv += pv
            
            # 終值計算
            terminal_fcf = fcf_per_share * ((1 + growth_rate) ** 5) * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            terminal_pv = terminal_value / ((1 + discount_rate) ** 5)
            
            return total_pv + terminal_pv
            
        except Exception as e:
            print(f"DCF計算錯誤: {e}")
            return 0
    
    def _calculate_pe_valuation(
        self, 
        stock_data: Dict[str, Any], 
        market_data: Dict[str, Any] = None
    ) -> float:
        """計算PE估值"""
        try:
            # 計算每股盈餘
            net_income = stock_data.get('net_income_parent', 0)
            shares_outstanding = stock_data.get('shares_outstanding', 1)
            eps = net_income / shares_outstanding if shares_outstanding > 0 else 0
            
            if eps <= 0:
                return 0
            
            # 使用行業平均PE（簡化版：假設為15倍）
            # 實際應用中應該從市場數據獲取同業PE
            industry_pe = market_data.get('industry_pe', 15) if market_data else 15
            
            # 根據公司品質調整PE
            # ROE > 15%: +20%, ROE < 10%: -20%
            roe = stock_data.get('roe', 0.12)
            if roe > 0.15:
                adjusted_pe = industry_pe * 1.2
            elif roe < 0.10:
                adjusted_pe = industry_pe * 0.8
            else:
                adjusted_pe = industry_pe
            
            return eps * adjusted_pe
            
        except Exception as e:
            print(f"PE估值計算錯誤: {e}")
            return 0
    
    def _calculate_pb_valuation(
        self, 
        stock_data: Dict[str, Any], 
        market_data: Dict[str, Any] = None
    ) -> float:
        """計算PB估值"""
        try:
            # 計算每股淨值
            total_equity = stock_data.get('total_equity', 0)
            shares_outstanding = stock_data.get('shares_outstanding', 1)
            book_value_per_share = total_equity / shares_outstanding if shares_outstanding > 0 else 0
            
            if book_value_per_share <= 0:
                return 0
            
            # 使用行業平均PB（簡化版）
            industry_pb = market_data.get('industry_pb', 1.5) if market_data else 1.5
            
            # 根據ROE調整PB倍數
            roe = stock_data.get('roe', 0.12)
            # 高ROE公司應該有更高的PB倍數
            if roe > 0.15:
                adjusted_pb = industry_pb * 1.3
            elif roe < 0.08:
                adjusted_pb = industry_pb * 0.7
            else:
                adjusted_pb = industry_pb
            
            return book_value_per_share * adjusted_pb
            
        except Exception as e:
            print(f"PB估值計算錯誤: {e}")
            return 0
    
    def _calculate_ev_ebitda_valuation(
        self, 
        stock_data: Dict[str, Any], 
        market_data: Dict[str, Any] = None
    ) -> float:
        """計算EV/EBITDA估值"""
        try:
            # 計算EBITDA（簡化版：營業利益 + 折舊）
            operating_income = stock_data.get('operating_income', 0)
            depreciation = stock_data.get('depreciation', 0)
            ebitda = operating_income + depreciation
            
            if ebitda <= 0:
                return 0
            
            # 行業平均EV/EBITDA倍數
            industry_ev_ebitda = market_data.get('industry_ev_ebitda', 10) if market_data else 10
            
            # 計算企業價值
            enterprise_value = ebitda * industry_ev_ebitda
            
            # 減去淨負債得到股權價值
            net_debt = stock_data.get('total_debt', 0) - stock_data.get('cash', 0)
            equity_value = enterprise_value - net_debt
            
            # 計算每股價值
            shares_outstanding = stock_data.get('shares_outstanding', 1)
            return equity_value / shares_outstanding if shares_outstanding > 0 else 0
            
        except Exception as e:
            print(f"EV/EBITDA估值計算錯誤: {e}")
            return 0
    
    def _calculate_dividend_valuation(
        self, 
        stock_data: Dict[str, Any], 
        market_data: Dict[str, Any] = None
    ) -> float:
        """計算股利折現估值（適用於高股息股票）"""
        try:
            dividend_per_share = stock_data.get('dividend_per_share', 0)
            
            if dividend_per_share <= 0:
                return 0
            
            # 假設股利成長率2%，要求報酬率8%
            dividend_growth = 0.02
            required_return = 0.08
            
            # Gordon Growth Model
            if required_return > dividend_growth:
                return dividend_per_share * (1 + dividend_growth) / (required_return - dividend_growth)
            else:
                return 0
                
        except Exception as e:
            print(f"股利估值計算錯誤: {e}")
            return 0
    
    def _get_method_weight(self, method: str, stock_data: Dict[str, Any]) -> float:
        """根據公司特性決定估值方法權重"""
        
        # 基本權重
        weights = {
            'dcf': 0.4,      # DCF最重要
            'pe': 0.3,       # PE次之
            'pb': 0.15,      # PB較少
            'ev_ebitda': 0.1, # EV/EBITDA輔助
            'dividend_yield': 0.05  # 股利估值最少
        }
        
        # 根據公司特性調整權重
        dividend_yield = stock_data.get('dividend_yield', 0)
        roe = stock_data.get('roe', 0.12)
        
        # 高股息股票增加股利估值權重
        if dividend_yield > 0.05:  # 股息率 > 5%
            weights['dividend_yield'] = 0.15
            weights['dcf'] = 0.35
            weights['pe'] = 0.25
        
        # 高成長公司增加DCF權重
        if roe > 0.18:  # ROE > 18%
            weights['dcf'] = 0.5
            weights['pe'] = 0.25
            weights['pb'] = 0.15
            weights['ev_ebitda'] = 0.1
        
        return weights.get(method, 0.2)
    
    def _calculate_consensus_valuation(
        self, 
        results: Dict[str, Any], 
        current_price: float
    ) -> Dict[str, Any]:
        """計算加權平均共識估值"""
        
        total_weight = 0
        weighted_sum = 0
        valid_methods = []
        
        for method, result in results.items():
            if method == 'consensus':
                continue
                
            value = result.get('value', 0)
            weight = result.get('method_weight', 0)
            
            if value > 0 and 'error' not in result:
                weighted_sum += value * weight
                total_weight += weight
                valid_methods.append(method)
        
        if total_weight > 0:
            consensus_value = weighted_sum / total_weight
            consensus_upside = (consensus_value / current_price - 1) if current_price > 0 else 0
            
            # 計算估值範圍（基於有效方法的標準差）
            valid_values = [results[method]['value'] for method in valid_methods 
                          if results[method]['value'] > 0]
            
            if len(valid_values) > 1:
                std_dev = np.std(valid_values)
                value_range = (consensus_value - std_dev, consensus_value + std_dev)
            else:
                value_range = (consensus_value * 0.9, consensus_value * 1.1)
            
            return {
                'value': consensus_value,
                'upside': consensus_upside,
                'range': value_range,
                'confidence': min(len(valid_methods) / 4, 1.0),  # 最高信心度為100%
                'valid_methods': valid_methods
            }
        else:
            return {
                'value': 0,
                'upside': 0,
                'range': (0, 0),
                'confidence': 0,
                'valid_methods': []
            }


class InvestmentAdviser:
    """投資建議生成器"""
    
    def __init__(self):
        self.recommendation_rules = {
            'strong_buy': {'upside': 0.25, 'confidence': 0.8},
            'buy': {'upside': 0.15, 'confidence': 0.6},
            'hold': {'upside': 0.05, 'confidence': 0.4},
            'sell': {'upside': -0.05, 'confidence': 0.4},
            'strong_sell': {'upside': -0.15, 'confidence': 0.6}
        }
    
    def generate_recommendation(
        self, 
        valuation_results: Dict[str, Any],
        risk_assessment: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        生成投資建議
        
        Args:
            valuation_results: 估值結果
            risk_assessment: 風險評估結果
            
        Returns:
            Dict: 投資建議
        """
        consensus = valuation_results.get('consensus', {})
        upside = consensus.get('upside', 0)
        confidence = consensus.get('confidence', 0)
        current_value = consensus.get('value', 0)
        
        # 基於上漲空間和信心度決定建議
        if upside >= 0.25 and confidence >= 0.8:
            recommendation = 'strong_buy'
            action = '強烈買入'
            reason = f'估值低估{upside:.1%}，建議積極布局'
        elif upside >= 0.15 and confidence >= 0.6:
            recommendation = 'buy'
            action = '買入'
            reason = f'具備{upside:.1%}上漲空間，建議進場'
        elif upside >= 0.05:
            recommendation = 'hold'
            action = '持有'
            reason = f'估值合理，建議持有等待'
        elif upside >= -0.05:
            recommendation = 'hold'
            action = '持有'
            reason = '估值中性，可繼續持有'
        elif upside >= -0.15:
            recommendation = 'sell'
            action = '賣出'
            reason = f'估值偏高{abs(upside):.1%}，建議減碼'
        else:
            recommendation = 'strong_sell'
            action = '強烈賣出'
            reason = f'估值嚴重偏高{abs(upside):.1%}，建議停損'
        
        # 計算目標價和停損價
        target_price = current_value * 1.1  # 目標價為估值+10%
        stop_loss = current_value * 0.85   # 停損價為估值-15%
        
        return {
            'recommendation': recommendation,
            'action': action,
            'reason': reason,
            'confidence_level': confidence,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'upside_potential': upside,
            'risk_level': self._assess_risk_level(risk_assessment) if risk_assessment else 'medium'
        }
    
    def _assess_risk_level(self, risk_assessment: Dict[str, Any]) -> str:
        """評估風險等級"""
        # 簡化的風險評估邏輯
        financial_risk = risk_assessment.get('financial_risk', 'medium')
        market_risk = risk_assessment.get('market_risk', 'medium')
        industry_risk = risk_assessment.get('industry_risk', 'medium')
        
        risk_scores = {
            'low': 1,
            'medium': 2,
            'high': 3
        }
        
        avg_risk = (
            risk_scores.get(financial_risk, 2) +
            risk_scores.get(market_risk, 2) +
            risk_scores.get(industry_risk, 2)
        ) / 3
        
        if avg_risk <= 1.5:
            return 'low'
        elif avg_risk <= 2.5:
            return 'medium'
        else:
            return 'high'
