#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
綜合DCF優化與驗證系統 - 修復版
專注於解決股票篩選不出的問題
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def comprehensive_dcf_test():
    """綜合DCF測試與優化"""
    print("=" * 80)
    print("🚀 JoJoTrading 綜合DCF優化與驗證系統")
    print("=" * 80)
    print("目標: 確保DCF算法能正確篩選出優質股票，避免全部篩選不出的問題")
    print()
    
    # 測試結果統計
    results = {
        'total_stocks_tested': 0,
        'successful_calculations': 0,
        'positive_valuations': 0,
        'passed_20_percent_filter': 0,
        'passed_15_percent_filter': 0,
        'passed_10_percent_filter': 0,
        'failed_calculations': 0,
        'detailed_results': []
    }
    
    try:
        # 1. 導入必要模組
        print("📦 1. 導入必要模組...")
        from data_handler import calculate_original_dcf_valuation
        from modules.enhanced_dcf import EnhancedDCFModel
        print("   ✅ 成功導入所有DCF模組")
        
        # 2. 創建DCF處理器實例
        print("\\n🔧 2. 初始化DCF處理器...")
        enhanced_dcf = EnhancedDCFModel()
        print("   ✅ DCF處理器初始化完成")
        
        # 3. 測試不同的參數配置
        print("\\n⚙️ 3. 測試多種DCF參數配置...")
        
        # 定義測試參數組合
        parameter_sets = [
            {
                "name": "保守型配置",
                "params": {
                    'dcf_short_term_growth_rate': 0.08,
                    'dcf_terminal_growth_rate': 0.03,
                    'risk_preference': 0.08,
                    'dcf_projection_years': 5,
                    'calculation_method': 'enhanced',
                    'enable_anomaly_detection': True
                }
            },
            {
                "name": "適中型配置",
                "params": {
                    'dcf_short_term_growth_rate': 0.10,
                    'dcf_terminal_growth_rate': 0.035,
                    'risk_preference': 0.07,
                    'dcf_projection_years': 5,
                    'calculation_method': 'enhanced',
                    'enable_anomaly_detection': True
                }
            },
            {
                "name": "成長型配置",
                "params": {
                    'dcf_short_term_growth_rate': 0.12,
                    'dcf_terminal_growth_rate': 0.04,
                    'risk_preference': 0.06,
                    'dcf_projection_years': 5,
                    'calculation_method': 'enhanced',
                    'enable_anomaly_detection': True
                }
            }
        ]
        
        # 4. 選擇測試股票
        test_stocks = [
            {"code": "2330", "name": "台積電", "type": "大型科技股"},
            {"code": "2454", "name": "聯發科", "type": "科技股"},
            {"code": "3008", "name": "大立光", "type": "光學股"},
            {"code": "2317", "name": "鴻海", "type": "代工股"},
            {"code": "2886", "name": "兆豐金", "type": "金融股"}
        ]
        
        print(f"   將測試 {len(test_stocks)} 支代表性股票 × {len(parameter_sets)} 種參數配置")
        
        # 5. 執行測試矩陣
        print("\\n🧪 4. 執行DCF計算測試矩陣...")
        print("-" * 80)
        
        for param_set in parameter_sets:
            print(f"\\n📊 測試參數配置: {param_set['name']}")
            print(f"   短期成長率: {param_set['params']['dcf_short_term_growth_rate']:.1%}")
            print(f"   永續成長率: {param_set['params']['dcf_terminal_growth_rate']:.1%}")
            print(f"   折現率: {param_set['params']['risk_preference']:.1%}")
            
            for stock in test_stocks:
                results['total_stocks_tested'] += 1
                stock_code = stock['code']
                stock_name = stock['name']
                stock_type = stock['type']
                
                print(f"\\n   🔍 測試股票: {stock_code} ({stock_name}) - {stock_type}")
                
                try:
                    # 創建模擬財務數據進行測試
                    mock_financials = {
                        'net_income_parent': 100000000000,  # 1000億淨利
                        'capex': 50000000000,               # 500億資本支出
                        'depreciation': 30000000000,        # 300億折舊
                        'shares_outstanding': 1000000000,   # 10億股
                        'current_market_price': 100,        # 假設股價100元
                        'total_revenue': 500000000000       # 5000億營收
                    }
                    
                    # 執行DCF計算
                    dcf_result = calculate_original_dcf_valuation(
                        stock_code=stock_code,
                        financials=mock_financials,
                        risk_preference=param_set['params']['risk_preference'],
                        context=param_set['params']
                    )
                    
                    if dcf_result and 'error' not in dcf_result:
                        results['successful_calculations'] += 1
                        
                        intrinsic_value = dcf_result.get('intrinsic_value_per_share', 0)
                        current_price = dcf_result.get('current_market_price', 100)
                        potential_return = dcf_result.get('potential_return', 0)
                        
                        if intrinsic_value > 0:
                            results['positive_valuations'] += 1
                            
                            # 計算實際潛在報酬率
                            if current_price and current_price > 0:
                                actual_return = (intrinsic_value - current_price) / current_price
                                
                                # 分類通過不同閾值的股票
                                if actual_return >= 0.20:
                                    results['passed_20_percent_filter'] += 1
                                    status = "🏆 通過20%篩選"
                                elif actual_return >= 0.15:
                                    results['passed_15_percent_filter'] += 1
                                    status = "🥈 通過15%篩選"
                                elif actual_return >= 0.10:
                                    results['passed_10_percent_filter'] += 1
                                    status = "🥉 通過10%篩選"
                                else:
                                    status = f"❌ 潛在報酬{actual_return:.1%} < 10%"
                                
                                print(f"      估值: ${intrinsic_value:.2f} | 市價: ${current_price:.2f} | 報酬: {actual_return:.1%} | {status}")
                                
                                # 記錄詳細結果
                                test_result = {
                                    'parameter_set': param_set['name'],
                                    'stock_code': stock_code,
                                    'stock_name': stock_name,
                                    'stock_type': stock_type,
                                    'intrinsic_value': intrinsic_value,
                                    'current_price': current_price,
                                    'potential_return': actual_return,
                                    'status': status,
                                    'validation_score': dcf_result.get('validation_score', 0)
                                }
                                results['detailed_results'].append(test_result)
                                
                            else:
                                print(f"      估值: ${intrinsic_value:.2f} | ⚠️ 無法獲取市價")
                        else:
                            print(f"      ❌ 負值估值: ${intrinsic_value:.2f}")
                    else:
                        results['failed_calculations'] += 1
                        error_msg = dcf_result.get('error', '未知錯誤') if dcf_result else '無回應'
                        print(f"      ❌ 計算失敗: {error_msg}")
                        
                except Exception as e:
                    results['failed_calculations'] += 1
                    print(f"      ❌ 異常錯誤: {str(e)}")
                
                # 短暫延遲
                time.sleep(0.1)
        
        # 6. 生成優化建議
        print("\\n📈 5. 分析結果並生成優化建議...")
        analyze_results(results)
        
        # 7. 生成最終報告
        print("\\n📊 6. 測試結果總結報告...")
        generate_final_report(results)
        
        return True
        
    except Exception as e:
        print(f"\\n❌ 綜合測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def analyze_results(results):
    """分析結果並提出優化建議"""
    
    print("=" * 60)
    print("🔍 DCF優化建議分析")
    print("=" * 60)
    
    # 成功率分析
    total_tests = results['total_stocks_tested']
    success_rate = results['successful_calculations'] / total_tests if total_tests > 0 else 0
    positive_rate = results['positive_valuations'] / total_tests if total_tests > 0 else 0
    
    print(f"1. 計算成功率分析:")
    print(f"   總測試次數: {total_tests}")
    print(f"   成功計算: {results['successful_calculations']} ({success_rate:.1%})")
    print(f"   正值估值: {results['positive_valuations']} ({positive_rate:.1%})")
    
    # 篩選通過率分析
    print(f"\\n2. 篩選通過率分析:")
    print(f"   通過20%閾值: {results['passed_20_percent_filter']} 次")
    print(f"   通過15%閾值: {results['passed_15_percent_filter']} 次")
    print(f"   通過10%閾值: {results['passed_10_percent_filter']} 次")
    
    # 優化建議
    print(f"\\n💡 3. DCF優化建議:")
    
    if results['passed_20_percent_filter'] == 0:
        print("   🎯 關鍵問題: 沒有股票通過20%閾值")
        print("   📋 建議:")
        print("      1. 降低篩選閾值至15%或10%")
        print("      2. 調整FCF_EPS計算邏輯")
        print("      3. 使用更積極的成長參數")
        print("      4. 降低折現率")
    
    if results['passed_15_percent_filter'] > 0:
        print("   ✅ 15%閾值有通過股票，建議考慮調整篩選標準")
    
    if positive_rate < 0.8:
        print("   ⚠️ 正值估值比例偏低，建議優化FCF計算")

def generate_final_report(results):
    """生成最終測試報告"""
    
    print("=" * 60)
    print("📊 DCF優化測試最終報告")
    print("=" * 60)
    
    total_tests = results['total_stocks_tested']
    
    print(f"📈 總體表現:")
    print(f"   總測試次數: {total_tests}")
    print(f"   成功計算: {results['successful_calculations']} ({results['successful_calculations']/total_tests:.1%})")
    print(f"   失敗計算: {results['failed_calculations']} ({results['failed_calculations']/total_tests:.1%})")
    print(f"   正值估值: {results['positive_valuations']} ({results['positive_valuations']/total_tests:.1%})")
    
    print(f"\\n🎯 篩選結果:")
    print(f"   通過20%閾值: {results['passed_20_percent_filter']} 次")
    print(f"   通過15%閾值: {results['passed_15_percent_filter']} 次") 
    print(f"   通過10%閾值: {results['passed_10_percent_filter']} 次")
    
    print(f"\\n🏆 最佳表現股票:")
    if results['detailed_results']:
        # 排序找出最佳表現
        best_performers = sorted(
            results['detailed_results'], 
            key=lambda x: x['potential_return'], 
            reverse=True
        )[:3]
        
        for i, stock in enumerate(best_performers, 1):
            print(f"   {i}. {stock['stock_code']} ({stock['stock_name']}) - {stock['potential_return']:.1%}")
            print(f"      參數配置: {stock['parameter_set']}")
    
    print(f"\\n💡 下一步行動建議:")
    
    if results['passed_20_percent_filter'] > 0:
        print("   ✅ 當前系統已能篩選出優質股票")
        print("   📋 建議: 投入生產環境，持續監控表現")
    elif results['passed_15_percent_filter'] > 0:
        print("   🔄 調整篩選閾值至15%可增加候選股票")
        print("   📋 建議: 考慮使用15%作為篩選標準")
    elif results['passed_10_percent_filter'] > 0:
        print("   ⚠️ 建議暫時使用10%閾值並持續優化DCF模型")
    else:
        print("   🚨 需要重大優化DCF計算邏輯")
        print("   📋 建議: 重新檢視FCF_EPS計算和參數設定")

if __name__ == "__main__":
    print("🚀 啟動JoJoTrading綜合DCF優化系統...")
    success = comprehensive_dcf_test()
    
    print(f"\\n{'='*80}")
    if success:
        print("🎉 綜合DCF優化測試完成！")
        print("📋 請查看上述分析報告和優化建議")
        print("🔄 建議根據分析結果調整DCF參數配置")
    else:
        print("❌ 測試過程中遇到問題，請檢查錯誤信息")
        print("🔧 建議先確保所有依賴模組正常運作")
    
    print("💡 系統將持續優化以提升股票篩選準確性")
