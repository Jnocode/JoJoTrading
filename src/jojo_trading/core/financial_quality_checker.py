#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
財務數據品質檢測與異常處理模組
Financial Data Quality Checker and Anomaly Handler

功能概述：
- 檢測一次性業外收入（處分資產、投資收益等）
- 識別財務異常項目（重組費用、減損等）
- 自動調整核心營運數據
- 提供標準化的財務數據供DCF估值使用

主要特色：
1. 業外收入檢測：自動識別非經常性損益
2. 核心營運分析：分離營運收入與業外收入
3. 趨勢異常檢測：識別財務數據的異常變化
4. 調整建議：提供數據調整方案

作者: JoJo Trading Team
版本: 1.0.0
日期: 2025-06-17
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import warnings

class FinancialDataQualityChecker:
    """財務數據品質檢測器"""
    
    def __init__(self):
        # 一次性項目關鍵字（中英文）
        self.one_time_keywords = [
            # 中文關鍵字
            '處分', '出售', '減損', '重組', '清算', '訴訟', '賠償',
            '資產重估', '存貨跌價', '呆帳', '投資損益', '兌換損益',
            '停業', '裁員', '關廠', '搬遷', '合併', '分拆',
            # 英文關鍵字
            'disposal', 'sale', 'impairment', 'restructuring', 'litigation',
            'settlement', 'revaluation', 'writedown', 'writeoff', 'extraordinary',
            'discontinued', 'merger', 'acquisition', 'divestiture'
        ]
        
        # 核心營運項目
        self.core_operations_items = [
            'operating_revenue', 'cost_of_sales', 'gross_profit',
            'operating_expenses', 'operating_income', 'ebitda'
        ]
        
        # 業外項目
        self.non_operating_items = [
            'investment_income', 'disposal_gain', 'foreign_exchange',
            'interest_income', 'other_income', 'extraordinary_items'
        ]
    
    def detect_one_time_items(self, financial_data: Dict, verbose: bool = True) -> Dict:
        """檢測一次性項目"""
        
        results = {
            'has_anomalies': False,
            'anomaly_items': [],
            'adjusted_net_income': None,
            'core_operating_income': None,
            'non_recurring_items': {},
            'quality_score': 100,
            'warnings': []
        }
        
        try:
            net_income = financial_data.get('net_income_parent', 0)
            operating_income = financial_data.get('operating_income', 0)
            
            if net_income == 0 or operating_income == 0:
                results['warnings'].append("缺少核心財務數據")
                results['quality_score'] -= 30
                return results
            
            # 1. 檢測營運外收入比例異常
            non_operating_ratio = abs(net_income - operating_income) / abs(net_income) if net_income != 0 else 0
            
            if non_operating_ratio > 0.3:  # 業外收入超過30%
                results['has_anomalies'] = True
                results['anomaly_items'].append({
                    'type': '業外收入比例異常',
                    'ratio': non_operating_ratio,
                    'description': f"業外收入佔淨利比例達 {non_operating_ratio*100:.1f}%"
                })
                results['quality_score'] -= 25
            
            # 2. 檢測淨利與營業利益差異
            income_gap = net_income - operating_income
            income_gap_ratio = income_gap / operating_income if operating_income != 0 else 0
            
            if abs(income_gap_ratio) > 0.5:  # 差異超過50%
                results['has_anomalies'] = True
                results['anomaly_items'].append({
                    'type': '淨利營業利益差異過大',
                    'gap': income_gap,
                    'ratio': income_gap_ratio,
                    'description': f"淨利與營業利益差異 {income_gap/1e8:.1f}億元 ({income_gap_ratio*100:.1f}%)"
                })
                results['quality_score'] -= 20
            
            # 3. 檢測投資收益異常
            investment_income = financial_data.get('investment_income', 0)
            if investment_income != 0:
                investment_ratio = investment_income / net_income if net_income != 0 else 0
                
                if abs(investment_ratio) > 0.2:  # 投資收益超過20%
                    results['has_anomalies'] = True
                    results['anomaly_items'].append({
                        'type': '投資收益異常',
                        'amount': investment_income,
                        'ratio': investment_ratio,
                        'description': f"投資收益 {investment_income/1e8:.1f}億元 (佔淨利 {investment_ratio*100:.1f}%)"
                    })
                    results['non_recurring_items']['investment_income'] = investment_income
                    results['quality_score'] -= 15
            
            # 4. 計算調整後核心數據
            results['core_operating_income'] = operating_income
            
            # 調整後淨利 = 營業利益 - 估計稅費
            estimated_tax_rate = 0.2  # 假設20%稅率
            results['adjusted_net_income'] = operating_income * (1 - estimated_tax_rate)
            
            # 5. 資料品質評分
            if results['quality_score'] >= 90:
                quality_level = "優秀"
            elif results['quality_score'] >= 70:
                quality_level = "良好"
            elif results['quality_score'] >= 50:
                quality_level = "普通"
            else:
                quality_level = "需要調整"
            
            if verbose:
                print(f"\n🔍 財務數據品質檢測結果:")
                print(f"  品質評分: {results['quality_score']}/100 ({quality_level})")
                
                if results['has_anomalies']:
                    print(f"  ⚠️ 發現 {len(results['anomaly_items'])} 項異常:")
                    for item in results['anomaly_items']:
                        print(f"    • {item['description']}")
                else:
                    print(f"  ✅ 未發現明顯異常項目")
                
                if results['adjusted_net_income'] != net_income:
                    print(f"  📊 調整建議:")
                    print(f"    原始淨利: {net_income/1e8:.1f}億元")
                    print(f"    調整淨利: {results['adjusted_net_income']/1e8:.1f}億元")
                    print(f"    調整幅度: {(results['adjusted_net_income']-net_income)/net_income*100:.1f}%")
        
        except Exception as e:
            results['warnings'].append(f"檢測過程發生錯誤: {str(e)}")
            results['quality_score'] = 50
        
        return results
    
    def analyze_historical_trends(self, historical_data: List[Dict], verbose: bool = True) -> Dict:
        """分析歷史趨勢異常"""
        
        results = {
            'trend_anomalies': [],
            'volatility_score': 0,
            'growth_consistency': 0,
            'recommendations': []
        }
        
        if len(historical_data) < 3:
            results['recommendations'].append("歷史數據不足，建議收集更多期間數據")
            return results
        
        try:
            # 提取關鍵財務指標
            revenues = [data.get('total_revenue', 0) for data in historical_data]
            net_incomes = [data.get('net_income_parent', 0) for data in historical_data]
            operating_incomes = [data.get('operating_income', 0) for data in historical_data]
            
            # 計算成長率
            revenue_growth_rates = []
            income_growth_rates = []
            
            for i in range(1, len(revenues)):
                if revenues[i-1] != 0:
                    revenue_growth = (revenues[i] - revenues[i-1]) / revenues[i-1]
                    revenue_growth_rates.append(revenue_growth)
                
                if net_incomes[i-1] != 0:
                    income_growth = (net_incomes[i] - net_incomes[i-1]) / net_incomes[i-1]
                    income_growth_rates.append(income_growth)
            
            # 檢測異常波動
            if revenue_growth_rates:
                revenue_volatility = np.std(revenue_growth_rates)
                if revenue_volatility > 0.3:  # 營收波動超過30%
                    results['trend_anomalies'].append({
                        'type': '營收波動過大',
                        'volatility': revenue_volatility,
                        'description': f"營收成長率標準差 {revenue_volatility*100:.1f}%"
                    })
            
            if income_growth_rates:
                income_volatility = np.std(income_growth_rates)
                if income_volatility > 0.5:  # 淨利波動超過50%
                    results['trend_anomalies'].append({
                        'type': '淨利波動過大',
                        'volatility': income_volatility,
                        'description': f"淨利成長率標準差 {income_volatility*100:.1f}%"
                    })
            
            # 檢測營業利益與淨利的一致性
            op_net_ratios = []
            for i in range(len(operating_incomes)):
                if net_incomes[i] != 0:
                    ratio = operating_incomes[i] / net_incomes[i]
                    op_net_ratios.append(ratio)
            
            if op_net_ratios:
                ratio_volatility = np.std(op_net_ratios)
                if ratio_volatility > 0.3:  # 比例波動超過30%
                    results['trend_anomalies'].append({
                        'type': '營業利益淨利比例不穩定',
                        'volatility': ratio_volatility,
                        'description': f"可能存在不規律的業外收入"
                    })
            
            # 生成建議
            if len(results['trend_anomalies']) == 0:
                results['recommendations'].append("財務數據趨勢穩定，適合DCF估值")
            else:
                results['recommendations'].append("建議使用調整後的核心營運數據進行估值")
                results['recommendations'].append("考慮使用多年平均數據平滑異常波動")
        
        except Exception as e:
            results['recommendations'].append(f"趨勢分析失敗: {str(e)}")
        
        if verbose and results['trend_anomalies']:
            print(f"\n📈 歷史趨勢異常檢測:")
            for anomaly in results['trend_anomalies']:
                print(f"  ⚠️ {anomaly['description']}")
            
            print(f"\n💡 建議:")
            for rec in results['recommendations']:
                print(f"  • {rec}")
        
        return results
    
    def adjust_financial_data(self, financial_data: Dict, quality_check: Dict) -> Dict:
        """根據品質檢測結果調整財務數據"""
        
        adjusted_data = financial_data.copy()
        
        # 如果有異常，使用調整後的數據
        if quality_check['has_anomalies'] and quality_check['adjusted_net_income']:
            adjusted_data['net_income_parent_original'] = financial_data.get('net_income_parent', 0)
            adjusted_data['net_income_parent'] = quality_check['adjusted_net_income']
            adjusted_data['data_adjustment_applied'] = True
            adjusted_data['adjustment_reason'] = "移除一次性業外收入影響"
        
        # 添加品質指標
        adjusted_data['data_quality_score'] = quality_check['quality_score']
        adjusted_data['data_quality_warnings'] = quality_check['warnings']
        adjusted_data['anomaly_items'] = quality_check['anomaly_items']
        
        return adjusted_data
    
    def get_valuation_recommendations(self, quality_check: Dict) -> List[str]:
        """根據數據品質提供估值建議"""
        
        recommendations = []
        
        if quality_check['quality_score'] >= 90:
            recommendations.append("數據品質優秀，可直接用於DCF估值")
        elif quality_check['quality_score'] >= 70:
            recommendations.append("數據品質良好，建議使用標準DCF參數")
        elif quality_check['quality_score'] >= 50:
            recommendations.append("數據品質普通，建議增加風險溢價或使用保守參數")
            recommendations.append("考慮使用相對估值法進行交叉驗證")
        else:
            recommendations.append("數據品質較差，不建議單獨使用DCF估值")
            recommendations.append("建議使用多種估值方法綜合判斷")
            recommendations.append("等待更完整的財務數據後再進行估值")
        
        # 針對特定異常的建議
        for anomaly in quality_check.get('anomaly_items', []):
            if '業外收入' in anomaly['type']:
                recommendations.append("重點關注核心營運能力，業外收入不可持續")
            elif '投資收益' in anomaly['type']:
                recommendations.append("投資收益波動較大，建議使用營業利益進行估值")
            elif '差異過大' in anomaly['type']:
                recommendations.append("營業利益與淨利差異大，需深入分析業外項目")
        
        return recommendations
    
    def detect_asset_disposal_specifically(self, financial_data: Dict, verbose: bool = True) -> Dict:
        """專門檢測處分資產收益/損失的增強功能"""
        
        results = {
            'disposal_detected': False,
            'disposal_items': [],
            'disposal_severity': 'low',
            'estimated_disposal_impact': 0,
            'core_earnings_adjustment': {},
            'disposal_warnings': [],
            'quality_impact': 0
        }
        
        try:
            net_income = financial_data.get('net_income_parent', 0)
            operating_income = financial_data.get('operating_income', 0)
            investment_income = financial_data.get('investment_income', 0)
            other_income = financial_data.get('other_income', 0)
            
            if net_income == 0 or operating_income == 0:
                results['disposal_warnings'].append("缺少基本財務數據，無法準確檢測處分收益")
                return results
            
            # 1. 檢測大額投資收益（疑似處分收益）
            if investment_income != 0:
                investment_ratio = abs(investment_income) / abs(net_income)
                
                # 處分收益判斷標準
                if investment_ratio > 0.15:  # 投資收益超過淨利15%
                    results['disposal_detected'] = True
                    disposal_item = {
                        'type': '疑似處分資產收益',
                        'amount': investment_income,
                        'ratio': investment_ratio,
                        'description': f"投資收益 {investment_income/1e8:.1f}億元，佔淨利 {investment_ratio*100:.1f}%",
                        'impact_assessment': self._assess_disposal_impact(investment_ratio)
                    }
                    results['disposal_items'].append(disposal_item)
                    results['estimated_disposal_impact'] += abs(investment_income)
            
            # 2. 檢測其他收益異常（可能包含處分收益）
            if other_income != 0:
                other_ratio = abs(other_income) / abs(net_income)
                
                if other_ratio > 0.10:  # 其他收益超過淨利10%
                    results['disposal_detected'] = True
                    disposal_item = {
                        'type': '其他收益異常',
                        'amount': other_income,
                        'ratio': other_ratio,
                        'description': f"其他收益 {other_income/1e8:.1f}億元，佔淨利 {other_ratio*100:.1f}%",
                        'impact_assessment': self._assess_disposal_impact(other_ratio)
                    }
                    results['disposal_items'].append(disposal_item)
            
            # 3. 檢測營業利益與淨利的異常差距（總體業外收入檢測）
            earnings_gap = net_income - operating_income
            gap_ratio = abs(earnings_gap) / abs(net_income) if net_income != 0 else 0
            
            if gap_ratio > 0.25:  # 業外收入超過25%
                results['disposal_detected'] = True
                disposal_item = {
                    'type': '業外收入比例過高',
                    'amount': earnings_gap,
                    'ratio': gap_ratio,
                    'description': f"業外收入 {earnings_gap/1e8:.1f}億元，佔淨利 {gap_ratio*100:.1f}%",
                    'impact_assessment': self._assess_disposal_impact(gap_ratio)
                }
                results['disposal_items'].append(disposal_item)
            
            # 4. 評估處分收益的嚴重程度
            total_disposal_ratio = results['estimated_disposal_impact'] / abs(net_income) if net_income != 0 else 0
            
            if total_disposal_ratio > 0.50:
                results['disposal_severity'] = 'critical'
                results['quality_impact'] = 50
                results['disposal_warnings'].append("處分收益佔比過高(>50%)，嚴重影響核心營運評估")
            elif total_disposal_ratio > 0.30:
                results['disposal_severity'] = 'high'
                results['quality_impact'] = 30
                results['disposal_warnings'].append("處分收益佔比較高(>30%)，需調整後進行估值")
            elif total_disposal_ratio > 0.15:
                results['disposal_severity'] = 'medium'
                results['quality_impact'] = 15
                results['disposal_warnings'].append("檢測到處分收益，建議審慎評估")
            
            # 5. 計算核心盈利調整
            if results['disposal_detected']:
                results['core_earnings_adjustment'] = self._calculate_core_earnings(
                    financial_data, results['estimated_disposal_impact'])
            
            if verbose and results['disposal_detected']:
                print(f"\n🏢 處分資產專項檢測結果:")
                print(f"  檢測到處分收益影響: {results['disposal_severity'].upper()}")
                print(f"  估計處分金額: {results['estimated_disposal_impact']/1e8:.1f}億元")
                print(f"  品質影響程度: -{results['quality_impact']}分")
                
                for item in results['disposal_items']:
                    print(f"    • {item['description']}")
                    print(f"      影響評估: {item['impact_assessment']}")
                
                if results['core_earnings_adjustment']:
                    adj = results['core_earnings_adjustment']
                    print(f"  📊 核心盈利調整:")
                    print(f"    調整前淨利: {adj['original_net_income']/1e8:.1f}億元")
                    print(f"    調整後淨利: {adj['adjusted_net_income']/1e8:.1f}億元")
                    print(f"    調整幅度: {adj['adjustment_percentage']:.1f}%")
        
        except Exception as e:
            results['disposal_warnings'].append(f"處分資產檢測失敗: {str(e)}")
        
        return results
    
    def _assess_disposal_impact(self, ratio: float) -> str:
        """評估處分收益的影響程度"""
        if ratio > 0.50:
            return "重大影響 - 建議完全排除該項收益"
        elif ratio > 0.30:
            return "顯著影響 - 強烈建議調整估值參數"
        elif ratio > 0.15:
            return "中等影響 - 建議使用保守估值"
        else:
            return "輕微影響 - 可採用標準估值方法"
    
    def _calculate_core_earnings(self, financial_data: Dict, disposal_amount: float) -> Dict:
        """計算排除處分收益後的核心盈利"""
        
        original_net_income = financial_data.get('net_income_parent', 0)
        operating_income = financial_data.get('operating_income', 0)
        
        # 方法1: 直接從淨利中扣除處分收益
        adjusted_net_income_method1 = original_net_income - disposal_amount
        
        # 方法2: 基於營業利益重新計算（考慮稅率）
        estimated_tax_rate = 0.20  # 假設20%稅率
        adjusted_net_income_method2 = operating_income * (1 - estimated_tax_rate)
        
        # 選擇較保守的調整方法
        adjusted_net_income = min(adjusted_net_income_method1, adjusted_net_income_method2)
        
        adjustment_percentage = ((adjusted_net_income - original_net_income) / original_net_income * 100) if original_net_income != 0 else 0
        
        return {
            'original_net_income': original_net_income,
            'disposal_amount_removed': disposal_amount,
            'adjusted_net_income': adjusted_net_income,
            'adjustment_percentage': adjustment_percentage,
            'method_used': 'conservative_approach'
        }
    
    def generate_disposal_recommendations(self, disposal_analysis: Dict) -> List[str]:
        """根據處分資產分析生成具體建議"""
        
        recommendations = []
        
        if not disposal_analysis['disposal_detected']:
            recommendations.append("✅ 未檢測到重大處分資產收益，財務數據相對純淨")
            return recommendations
        
        severity = disposal_analysis['disposal_severity']
        
        # 根據嚴重程度提供建議
        if severity == 'critical':
            recommendations.extend([
                "🚨 重大處分收益警告！建議採取以下措施：",
                "📊 使用營業利益為基礎重新計算DCF估值",
                "⚠️ 風險溢價增加 3-5%",
                "🔍 深入研究處分資產的性質（土地、子公司、投資等）",
                "📈 考慮使用多年平均營業利益進行估值",
                "💡 建議等待下一季度財報確認營運趨勢"
            ])
        elif severity == 'high':
            recommendations.extend([
                "⚠️ 明顯處分收益影響，建議謹慎處理：",
                "📊 同時計算原始和調整後的DCF估值進行比較",
                "⚠️ 風險溢價增加 2-3%",
                "🔍 查閱財報附註了解處分收益來源",
                "💡 重點關注營業利益的成長趨勢"
            ])
        elif severity == 'medium':
            recommendations.extend([
                "💡 輕度處分收益影響，建議審慎評估：",
                "📊 可使用標準DCF方法，但需增加保守性",
                "⚠️ 風險溢價增加 1-2%",
                "🔍 留意未來季度是否有類似一次性收入"
            ])
        
        # 針對特定項目的具體建議
        for item in disposal_analysis['disposal_items']:
            item_type = item['type']
            amount = item['amount'] / 1e8
            
            if '處分資產' in item_type:
                recommendations.append(f"💰 處分收益 {amount:.1f}億元為一次性收入，不應納入持續經營評估")
            elif '投資收益' in item_type:
                if amount > 0:
                    recommendations.append(f"📈 投資收益 {amount:.1f}億元可能包含處分收益，需確認其性質")
                else:
                    recommendations.append(f"📉 投資損失 {abs(amount):.1f}億元可能為一次性損失，應調整回核心營運能力")
            elif '其他收益' in item_type:
                recommendations.append(f"🔍 其他收益 {amount:.1f}億元異常，需查明具體來源")
        
        # 估值方法建議
        if disposal_analysis['estimated_disposal_impact'] > 0:
            impact_amount = disposal_analysis['estimated_disposal_impact'] / 1e8
            recommendations.append(f"📋 建議估值調整：排除 {impact_amount:.1f}億元一次性收益進行DCF計算")
        
        return recommendations


def demo_financial_quality_checker():
    """示範財務數據品質檢測功能"""
    
    print("🔍 財務數據品質檢測與異常處理示範")
    print("=" * 60)
    
    checker = FinancialDataQualityChecker()
    
    # 模擬財務數據 - 包含異常項目
    print("\n📊 案例1: 正常財務數據")
    normal_data = {
        'net_income_parent': 1000000000,    # 10億
        'operating_income': 900000000,      # 9億
        'investment_income': 50000000,      # 0.5億
        'total_revenue': 5000000000,        # 50億
    }
    
    quality_check1 = checker.detect_one_time_items(normal_data)
    adjusted_data1 = checker.adjust_financial_data(normal_data, quality_check1)
    recommendations1 = checker.get_valuation_recommendations(quality_check1)
    
    print("\n💡 估值建議:")
    for rec in recommendations1:
        print(f"  • {rec}")
    
    print("\n" + "-" * 60)
    print("\n📊 案例2: 含大額處分收益的異常數據")
    anomaly_data = {
        'net_income_parent': 2000000000,    # 20億 (含處分收益)
        'operating_income': 800000000,      # 8億
        'investment_income': 1200000000,    # 12億 (處分資產收益)
        'total_revenue': 5000000000,        # 50億
    }
    
    quality_check2 = checker.detect_one_time_items(anomaly_data)
    adjusted_data2 = checker.adjust_financial_data(anomaly_data, quality_check2)
    recommendations2 = checker.get_valuation_recommendations(quality_check2)
    
    print("\n💡 估值建議:")
    for rec in recommendations2:
        print(f"  • {rec}")
    
    print(f"\n📈 調整對比:")
    print(f"  原始淨利: {anomaly_data['net_income_parent']/1e8:.1f}億元")
    print(f"  調整淨利: {adjusted_data2['net_income_parent']/1e8:.1f}億元")
    print(f"  調整幅度: {(adjusted_data2['net_income_parent']-anomaly_data['net_income_parent'])/anomaly_data['net_income_parent']*100:.1f}%")
    
    print("\n" + "-" * 60)
    print("\n📊 案例3: 歷史趨勢分析")
    historical_data = [
        {'total_revenue': 4000000000, 'net_income_parent': 800000000, 'operating_income': 750000000},
        {'total_revenue': 5000000000, 'net_income_parent': 900000000, 'operating_income': 850000000},
        {'total_revenue': 5200000000, 'net_income_parent': 2000000000, 'operating_income': 880000000},  # 異常年度
        {'total_revenue': 5100000000, 'net_income_parent': 920000000, 'operating_income': 900000000},
    ]
    
    trend_analysis = checker.analyze_historical_trends(historical_data)


if __name__ == "__main__":
    demo_financial_quality_checker()
