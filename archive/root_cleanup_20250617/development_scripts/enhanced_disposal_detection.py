#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版處分資產收益檢測與調整模組
Enhanced Asset Disposal Detection and Adjustment Module

針對處分資產導致的一次性業外收入進行專項檢測與調整
解決因處分資產扭曲DCF估值的問題

主要功能：
1. 專項檢測處分資產收益/損失
2. 識別各種類型的一次性項目
3. 智能還原核心營運能力
4. 提供多級調整方案
5. 歷史數據趨勢分析

作者: JoJo Trading Team
版本: 2.0.0
日期: 2025-06-17
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import warnings

class EnhancedDisposalDetector:
    """增強版處分資產檢測器"""
    
    def __init__(self):
        # 處分資產相關關鍵字（更詳細分類）
        self.disposal_keywords = {
            '處分收益': ['處分利益', '處分收益', '出售利益', '出售收益', '售產收益'],
            '處分損失': ['處分損失', '出售損失', '售產損失'],
            '資產減損': ['減損', '資產減損', '商譽減損', '存貨跌價'],
            '投資處分': ['投資處分', '轉投資處分', '金融資產處分'],
            '子公司處分': ['子公司出售', '轉投資出售', '事業處分'],
            '土地處分': ['土地處分', '不動產處分', '廠房出售'],
            '重組費用': ['重組費用', '重組損失', '員工遣散', '關廠費用']
        }
        
        # 業外收入分類閾值
        self.thresholds = {
            'non_operating_ratio': 0.20,     # 業外收入比例閾值 20%
            'disposal_ratio': 0.15,          # 處分收益比例閾值 15%
            'volatility_threshold': 0.30,     # 波動率閾值 30%
            'trend_deviation': 0.50           # 趨勢偏離閾值 50%
        }
    
    def detect_disposal_anomalies(self, financial_data: Dict, 
                                historical_data: Optional[List[Dict]] = None, 
                                verbose: bool = True) -> Dict:
        """檢測處分資產異常"""
        
        analysis_result = {
            'disposal_detected': False,
            'disposal_items': [],
            'severity_level': 'low',
            'estimated_disposal_amount': 0,
            'core_operating_metrics': {},
            'adjustment_recommendations': [],
            'confidence_score': 100,
            'valuation_impact': {}
        }
        
        try:
            # 基本財務數據
            net_income = financial_data.get('net_income_parent', 0)
            operating_income = financial_data.get('operating_income', 0)
            investment_income = financial_data.get('investment_income', 0)
            other_income = financial_data.get('other_income', 0)
            total_revenue = financial_data.get('total_revenue', 0)
            
            if verbose:
                print(f"\n🔍 增強版處分資產檢測分析")
                print(f"=" * 50)
                print(f"📊 基本財務數據:")
                print(f"  營業收入: {total_revenue/1e8:.1f}億元")
                print(f"  營業利益: {operating_income/1e8:.1f}億元")
                print(f"  投資收益: {investment_income/1e8:.1f}億元")
                print(f"  其他收益: {other_income/1e8:.1f}億元")
                print(f"  歸屬淨利: {net_income/1e8:.1f}億元")
            
            # 1. 處分收益檢測
            disposal_analysis = self._detect_disposal_gains(
                net_income, operating_income, investment_income, other_income)
            
            analysis_result.update(disposal_analysis)
            
            # 2. 歷史趨勢分析（如果有歷史數據）
            if historical_data:
                trend_analysis = self._analyze_historical_consistency(
                    financial_data, historical_data)
                analysis_result['historical_analysis'] = trend_analysis
            
            # 3. 計算核心營運指標
            core_metrics = self._calculate_core_metrics(
                financial_data, analysis_result)
            analysis_result['core_operating_metrics'] = core_metrics
            
            # 4. 生成調整建議
            recommendations = self._generate_adjustment_recommendations(
                analysis_result)
            analysis_result['adjustment_recommendations'] = recommendations
            
            # 5. 評估對估值的影響
            valuation_impact = self._assess_valuation_impact(
                financial_data, analysis_result)
            analysis_result['valuation_impact'] = valuation_impact
            
            if verbose:
                self._print_analysis_summary(analysis_result)
        
        except Exception as e:
            analysis_result['error'] = str(e)
            if verbose:
                print(f"❌ 分析過程發生錯誤: {e}")
        
        return analysis_result
    
    def _detect_disposal_gains(self, net_income: float, operating_income: float, 
                              investment_income: float, other_income: float) -> Dict:
        """檢測處分收益"""
        
        result = {
            'disposal_detected': False,
            'disposal_items': [],
            'severity_level': 'low',
            'estimated_disposal_amount': 0,
            'confidence_score': 100
        }
        
        if net_income == 0 or operating_income == 0:
            result['confidence_score'] = 30
            return result
        
        # 業外收入總額
        non_operating_income = net_income - operating_income
        
        # 1. 業外收入比例檢測
        non_operating_ratio = abs(non_operating_income) / abs(net_income)
        
        if non_operating_ratio > self.thresholds['non_operating_ratio']:
            result['disposal_detected'] = True
            result['disposal_items'].append({
                'type': '業外收入異常',
                'amount': non_operating_income,
                'ratio': non_operating_ratio,
                'description': f"業外收入佔淨利 {non_operating_ratio*100:.1f}%"
            })
        
        # 2. 投資收益檢測（可能包含處分收益）
        if investment_income != 0:
            investment_ratio = abs(investment_income) / abs(net_income)
            
            if investment_ratio > self.thresholds['disposal_ratio']:
                result['disposal_detected'] = True
                result['disposal_items'].append({
                    'type': '疑似處分收益',
                    'amount': investment_income,
                    'ratio': investment_ratio,
                    'description': f"投資收益 {investment_income/1e8:.1f}億元 (佔淨利 {investment_ratio*100:.1f}%)"
                })
                
                # 估計處分收益金額
                result['estimated_disposal_amount'] += abs(investment_income)
        
        # 3. 其他收益檢測
        if other_income != 0:
            other_ratio = abs(other_income) / abs(net_income)
            
            if other_ratio > 0.10:  # 其他收益超過10%
                result['disposal_detected'] = True
                result['disposal_items'].append({
                    'type': '其他收益異常',
                    'amount': other_income,
                    'ratio': other_ratio,
                    'description': f"其他收益 {other_income/1e8:.1f}億元 (佔淨利 {other_ratio*100:.1f}%)"
                })
        
        # 4. 評估嚴重程度
        total_disposal_ratio = result['estimated_disposal_amount'] / abs(net_income) if net_income != 0 else 0
        
        if total_disposal_ratio > 0.50:
            result['severity_level'] = 'critical'
            result['confidence_score'] -= 40
        elif total_disposal_ratio > 0.30:
            result['severity_level'] = 'high'
            result['confidence_score'] -= 25
        elif total_disposal_ratio > 0.15:
            result['severity_level'] = 'medium'
            result['confidence_score'] -= 15
        
        return result
    
    def _analyze_historical_consistency(self, current_data: Dict, 
                                       historical_data: List[Dict]) -> Dict:
        """分析歷史一致性"""
        
        result = {
            'is_consistent': True,
            'volatility_metrics': {},
            'anomaly_years': [],
            'trend_analysis': {}
        }
        
        try:
            # 提取歷史數據
            years_data = []
            for data in historical_data:
                years_data.append({
                    'net_income': data.get('net_income_parent', 0),
                    'operating_income': data.get('operating_income', 0),
                    'investment_income': data.get('investment_income', 0)
                })
            
            # 加入當前年度數據
            years_data.append({
                'net_income': current_data.get('net_income_parent', 0),
                'operating_income': current_data.get('operating_income', 0),
                'investment_income': current_data.get('investment_income', 0)
            })
            
            # 計算各項指標的波動率
            net_incomes = [d['net_income'] for d in years_data if d['net_income'] != 0]
            op_incomes = [d['operating_income'] for d in years_data if d['operating_income'] != 0]
            invest_incomes = [d['investment_income'] for d in years_data]
            
            if len(net_incomes) >= 3:
                # 淨利波動率
                net_income_cv = np.std(net_incomes) / np.mean(net_incomes) if np.mean(net_incomes) != 0 else 0
                
                # 營業利益波動率
                op_income_cv = np.std(op_incomes) / np.mean(op_incomes) if np.mean(op_incomes) != 0 else 0
                
                # 投資收益波動率
                invest_cv = np.std(invest_incomes) / (np.mean(np.abs(invest_incomes)) + 1e6)
                
                result['volatility_metrics'] = {
                    'net_income_cv': net_income_cv,
                    'operating_income_cv': op_income_cv,
                    'investment_income_cv': invest_cv
                }
                
                # 檢測異常年度
                if net_income_cv > self.thresholds['volatility_threshold']:
                    result['is_consistent'] = False
                    
                # 檢測投資收益異常年度
                mean_invest = np.mean(invest_incomes)
                std_invest = np.std(invest_incomes)
                
                for i, income in enumerate(invest_incomes):
                    if abs(income - mean_invest) > 2 * std_invest:
                        result['anomaly_years'].append({
                            'year_index': i,
                            'investment_income': income,
                            'deviation': abs(income - mean_invest) / (std_invest + 1e6)
                        })
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _calculate_core_metrics(self, financial_data: Dict, 
                               analysis_result: Dict) -> Dict:
        """計算核心營運指標"""
        
        net_income = financial_data.get('net_income_parent', 0)
        operating_income = financial_data.get('operating_income', 0)
        estimated_disposal = analysis_result.get('estimated_disposal_amount', 0)
        
        # 估計稅率
        total_income_before_tax = financial_data.get('income_before_tax', operating_income * 1.1)
        estimated_tax_rate = max(0.15, min(0.25, 1 - net_income / total_income_before_tax)) if total_income_before_tax != 0 else 0.20
        
        # 調整後核心數據
        core_metrics = {
            'original_net_income': net_income,
            'core_operating_income': operating_income,
            'estimated_disposal_amount': estimated_disposal,
            'estimated_tax_rate': estimated_tax_rate,
            'adjusted_net_income': operating_income * (1 - estimated_tax_rate),
            'adjustment_magnitude': 0
        }
        
        # 計算調整幅度
        if net_income != 0:
            core_metrics['adjustment_magnitude'] = (core_metrics['adjusted_net_income'] - net_income) / net_income
        
        return core_metrics
    
    def _generate_adjustment_recommendations(self, analysis_result: Dict) -> List[str]:
        """生成調整建議"""
        
        recommendations = []
        
        if not analysis_result['disposal_detected']:
            recommendations.append("✅ 未檢測到重大處分收益，可直接使用財務數據")
            return recommendations
        
        severity = analysis_result['severity_level']
        
        if severity == 'critical':
            recommendations.extend([
                "🚨 檢測到重大處分收益，強烈建議使用調整後數據",
                "📊 建議使用營業利益為基礎進行DCF估值",
                "⚠️ 增加風險溢價 2-3%",
                "🔍 建議深入分析處分資產的性質與影響"
            ])
        elif severity == 'high':
            recommendations.extend([
                "⚠️ 檢測到明顯處分收益，建議使用調整後數據",
                "📊 建議混合使用原始與調整後數據",
                "⚠️ 增加風險溢價 1-2%",
                "🔍 關注處分收益的可持續性"
            ])
        elif severity == 'medium':
            recommendations.extend([
                "💡 檢測到輕度處分收益，建議謹慎評估",
                "📊 可同時參考原始與調整後數據",
                "⚠️ 適度增加風險溢價 0.5-1%"
            ])
        
        # 根據檢測項目添加具體建議
        for item in analysis_result['disposal_items']:
            if '處分收益' in item['type']:
                recommendations.append(f"💰 處分收益 {item['amount']/1e8:.1f}億元為一次性收入，不應計入持續經營能力")
            elif '投資收益' in item['type']:
                recommendations.append(f"📈 投資收益波動較大，建議使用保守假設")
        
        return recommendations
    
    def _assess_valuation_impact(self, financial_data: Dict, 
                                analysis_result: Dict) -> Dict:
        """評估對估值的影響"""
        
        impact = {
            'dcf_impact': 'low',
            'pe_impact': 'medium',
            'adjustment_needed': False,
            'impact_metrics': {}
        }
        
        core_metrics = analysis_result.get('core_operating_metrics', {})
        adjustment_magnitude = abs(core_metrics.get('adjustment_magnitude', 0))
        
        if adjustment_magnitude > 0.30:  # 調整幅度超過30%
            impact['dcf_impact'] = 'high'
            impact['pe_impact'] = 'high'
            impact['adjustment_needed'] = True
        elif adjustment_magnitude > 0.15:  # 調整幅度超過15%
            impact['dcf_impact'] = 'medium'
            impact['pe_impact'] = 'high'
            impact['adjustment_needed'] = True
        
        impact['impact_metrics'] = {
            'adjustment_magnitude': adjustment_magnitude,
            'original_net_income': core_metrics.get('original_net_income', 0),
            'adjusted_net_income': core_metrics.get('adjusted_net_income', 0)
        }
        
        return impact
    
    def _print_analysis_summary(self, analysis_result: Dict):
        """打印分析摘要"""
        
        print(f"\n🎯 處分資產檢測結果摘要")
        print(f"-" * 40)
        
        if analysis_result['disposal_detected']:
            print(f"⚠️ 檢測到處分收益影響")
            print(f"  嚴重程度: {analysis_result['severity_level'].upper()}")
            print(f"  信心分數: {analysis_result['confidence_score']}/100")
            print(f"  檢測項目數: {len(analysis_result['disposal_items'])}")
            
            for item in analysis_result['disposal_items']:
                print(f"    • {item['description']}")
        else:
            print(f"✅ 未檢測到重大處分收益")
        
        # 核心指標
        core_metrics = analysis_result.get('core_operating_metrics', {})
        if core_metrics:
            print(f"\n📊 核心營運指標:")
            print(f"  原始淨利: {core_metrics.get('original_net_income', 0)/1e8:.1f}億元")
            print(f"  調整淨利: {core_metrics.get('adjusted_net_income', 0)/1e8:.1f}億元")
            print(f"  調整幅度: {core_metrics.get('adjustment_magnitude', 0)*100:.1f}%")
        
        # 估值影響
        valuation_impact = analysis_result.get('valuation_impact', {})
        if valuation_impact.get('adjustment_needed'):
            print(f"\n💡 估值建議:")
            for rec in analysis_result.get('adjustment_recommendations', []):
                print(f"  {rec}")


def test_enhanced_disposal_detection():
    """測試增強版處分資產檢測"""
    
    print("🧪 增強版處分資產檢測測試")
    print("=" * 60)
    
    detector = EnhancedDisposalDetector()
    
    # 測試案例1: 正常營運（無處分收益）
    print("\n📊 案例1: 正常營運數據")
    normal_data = {
        'net_income_parent': 1000000000,    # 10億
        'operating_income': 950000000,      # 9.5億
        'investment_income': 30000000,      # 0.3億
        'other_income': 20000000,           # 0.2億
        'total_revenue': 8000000000,        # 80億
    }
    
    result1 = detector.detect_disposal_anomalies(normal_data)
    
    print("\n" + "-" * 60)
    
    # 測試案例2: 大額處分收益
    print("\n📊 案例2: 大額處分資產收益")
    disposal_data = {
        'net_income_parent': 3000000000,    # 30億 (含處分收益)
        'operating_income': 800000000,      # 8億
        'investment_income': 2000000000,    # 20億 (處分收益)
        'other_income': 200000000,          # 2億
        'total_revenue': 8000000000,        # 80億
    }
    
    result2 = detector.detect_disposal_anomalies(disposal_data)
    
    print("\n" + "-" * 60)
    
    # 測試案例3: 包含歷史數據的分析
    print("\n📊 案例3: 歷史趨勢分析 (含處分收益)")
    
    historical_data = [
        # 3年前
        {
            'net_income_parent': 800000000,
            'operating_income': 750000000,
            'investment_income': 50000000
        },
        # 2年前
        {
            'net_income_parent': 900000000,
            'operating_income': 850000000,
            'investment_income': 50000000
        },
        # 1年前
        {
            'net_income_parent': 950000000,
            'operating_income': 900000000,
            'investment_income': 50000000
        }
    ]
    
    current_anomaly_data = {
        'net_income_parent': 2500000000,    # 25億 (今年含處分收益)
        'operating_income': 950000000,      # 9.5億
        'investment_income': 1550000000,    # 15.5億 (處分收益)
        'other_income': 0,
        'total_revenue': 8500000000,        # 85億
    }
    
    result3 = detector.detect_disposal_anomalies(
        current_anomaly_data, historical_data)
    
    print("\n" + "=" * 60)
    print("🎯 測試總結")
    print("=" * 60)
    
    test_cases = [
        ("正常營運", result1['disposal_detected'], result1['confidence_score']),
        ("大額處分", result2['disposal_detected'], result2['confidence_score']),
        ("歷史異常", result3['disposal_detected'], result3['confidence_score'])
    ]
    
    print("案例         檢測結果    信心分數")
    print("-" * 35)
    for case, detected, score in test_cases:
        status = "檢測到" if detected else "正常"
        print(f"{case:<10} {status:<8} {score}/100")
    
    print(f"\n✅ 增強版檢測功能驗證完成")
    print(f"💡 主要改進:")
    print(f"  • 更精確的處分收益識別算法")
    print(f"  • 多層次嚴重程度評估")
    print(f"  • 歷史趨勢一致性分析")
    print(f"  • 詳細的估值影響評估")
    print(f"  • 具體的調整建議方案")


if __name__ == "__main__":
    test_enhanced_disposal_detection()
