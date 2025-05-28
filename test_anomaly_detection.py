"""
一次性收益異常檢測功能測試工具
用於驗證和調整異常檢測算法的準確性
"""

import json
import pandas as pd
from data_handler import calculate_historical_fcf_eps, calculate_dcf_valuation
from jojo_state_machine import JoJoStateMachine

def load_test_cases():
    """載入測試案例"""
    test_cases = {
        "normal_stocks": [
            # 正常股票：穩定的歷史FCF_EPS
            {"stock_code": "2330", "name": "台積電", "expected_result": "normal"},
            {"stock_code": "2317", "name": "鴻海", "expected_result": "normal"},
            {"stock_code": "2454", "name": "聯發科", "expected_result": "normal"},
        ],
        "potential_anomaly_stocks": [
            # 可能有異常的股票（需要實際測試驗證）
            {"stock_code": "2409", "name": "友達", "expected_result": "anomaly_or_normal"},
            {"stock_code": "2412", "name": "中華電", "expected_result": "anomaly_or_normal"},
        ],
        "test_settings": [
            {"threshold": 1.5, "description": "保守模式"},
            {"threshold": 2.0, "description": "標準模式"},
            {"threshold": 2.5, "description": "寬鬆模式"},
        ]
    }
    return test_cases

def test_anomaly_detection_accuracy():
    """測試異常檢測的準確性"""
    print("🔍 開始測試一次性收益異常檢測功能...")
    
    # 初始化狀態機
    machine = JoJoStateMachine()
    test_cases = load_test_cases()
    
    results = {
        "test_summary": {},
        "detailed_results": [],
        "recommendations": []
    }
    
    for setting in test_cases["test_settings"]:
        threshold = setting["threshold"]
        description = setting["description"]
        
        print(f"\n📊 測試設定: {description} (閾值: {threshold}x)")
        print("-" * 50)
        
        # 設定測試環境
        machine.context['enable_anomaly_detection'] = True
        machine.context['anomaly_threshold'] = threshold
        machine.context['stock_details'] = {}
        
        setting_results = {
            "threshold": threshold,
            "description": description,
            "normal_detected_correctly": 0,
            "anomaly_detected_correctly": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "test_details": []
        }
        
        # 測試正常股票
        for stock in test_cases["normal_stocks"]:
            stock_code = stock["stock_code"]
            stock_name = stock["name"]
            
            print(f"🔍 測試正常股票: {stock_code} ({stock_name})")
            
            try:
                # 計算歷史FCF_EPS
                historical_result = calculate_historical_fcf_eps(
                    stock_code, {}, machine.context, periods=4
                )
                
                if historical_result.get("error"):
                    print(f"  ❌ 歷史數據獲取失敗: {historical_result.get('error')}")
                    continue
                
                # 模擬當期數據進行檢測
                avg_historical = historical_result.get("avg_fcf_eps", 0)
                max_historical = historical_result.get("max_fcf_eps", 0)
                periods_count = historical_result.get("periods_count", 0)
                cv = historical_result.get("cv", 0)
                quality_score = historical_result.get("quality_score", 0)
                
                # 評估結果
                is_stable = cv < 0.5 if cv != float('inf') else False
                has_sufficient_data = periods_count >= 3
                
                test_detail = {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "avg_historical_fcf_eps": round(avg_historical, 3),
                    "max_historical_fcf_eps": round(max_historical, 3),
                    "periods_count": periods_count,
                    "cv": round(cv, 3) if cv != float('inf') else "無限",
                    "quality_score": round(quality_score, 3),
                    "is_stable": is_stable,
                    "has_sufficient_data": has_sufficient_data,
                    "detection_readiness": is_stable and has_sufficient_data
                }
                
                setting_results["test_details"].append(test_detail)
                
                print(f"  📈 歷史平均FCF_EPS: {avg_historical:.3f}")
                print(f"  📊 數據期數: {periods_count}, 變異係數: {cv:.3f}")
                print(f"  🎯 數據品質評分: {quality_score:.3f}")
                print(f"  ✅ 檢測就緒: {'是' if test_detail['detection_readiness'] else '否'}")
                
                if test_detail['detection_readiness']:
                    setting_results["normal_detected_correctly"] += 1
                
            except Exception as e:
                print(f"  ❌ 測試過程發生錯誤: {e}")
        
        # 測試潛在異常股票
        for stock in test_cases["potential_anomaly_stocks"]:
            stock_code = stock["stock_code"]
            stock_name = stock["name"]
            
            print(f"🔍 測試潛在異常股票: {stock_code} ({stock_name})")
            
            try:
                historical_result = calculate_historical_fcf_eps(
                    stock_code, {}, machine.context, periods=4
                )
                
                if historical_result.get("error"):
                    print(f"  ❌ 歷史數據獲取失敗: {historical_result.get('error')}")
                    continue
                
                avg_historical = historical_result.get("avg_fcf_eps", 0)
                cv = historical_result.get("cv", 0)
                quality_score = historical_result.get("quality_score", 0)
                
                test_detail = {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "avg_historical_fcf_eps": round(avg_historical, 3),
                    "cv": round(cv, 3) if cv != float('inf') else "無限",
                    "quality_score": round(quality_score, 3),
                    "note": "潛在異常股票，需實際檢測驗證"
                }
                
                setting_results["test_details"].append(test_detail)
                
                print(f"  📈 歷史平均FCF_EPS: {avg_historical:.3f}")
                print(f"  📊 變異係數: {cv:.3f}, 品質評分: {quality_score:.3f}")
                
            except Exception as e:
                print(f"  ❌ 測試過程發生錯誤: {e}")
        
        results["detailed_results"].append(setting_results)
    
    # 生成測試報告
    generate_test_report(results)
    return results

def generate_test_report(results):
    """生成測試報告"""
    print("\n" + "="*60)
    print("📋 一次性收益異常檢測功能測試報告")
    print("="*60)
    
    for setting_result in results["detailed_results"]:
        threshold = setting_result["threshold"]
        description = setting_result["description"]
        
        print(f"\n🔧 測試設定: {description} (閾值: {threshold}x)")
        print("-" * 40)
        
        total_tests = len(setting_result["test_details"])
        ready_for_detection = sum(1 for detail in setting_result["test_details"] 
                                if detail.get("detection_readiness", False))
        
        print(f"總測試股票數: {total_tests}")
        print(f"具備檢測條件的股票: {ready_for_detection}")
        print(f"檢測就緒率: {ready_for_detection/total_tests*100:.1f}%" if total_tests > 0 else "N/A")
        
        # 顯示詳細結果
        print("\n詳細測試結果:")
        for detail in setting_result["test_details"]:
            status = "🟢 就緒" if detail.get("detection_readiness", False) else "🟡 待優化"
            print(f"  {detail['stock_code']} ({detail['stock_name']}): {status}")
            print(f"    歷史FCF_EPS: {detail['avg_historical_fcf_eps']}, 期數: {detail['periods_count']}")
            print(f"    變異係數: {detail['cv']}, 品質評分: {detail['quality_score']}")
    
    # 生成建議
    print("\n💡 優化建議:")
    print("1. 對於變異係數過高的股票，可考慮增加歷史期數或改用中位數")
    print("2. 數據期數不足的股票，建議降低檢測敏感度")
    print("3. 可考慮加入行業比較的異常檢測方式")
    print("4. 對於穩定性好的股票，可以使用更嚴格的閾值")

def save_test_results(results, filename="anomaly_detection_test_results.json"):
    """保存測試結果到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 測試結果已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存測試結果失敗: {e}")

if __name__ == "__main__":
    # 執行測試
    test_results = test_anomaly_detection_accuracy()
    
    # 保存結果
    save_test_results(test_results)
    
    print("\n🎉 異常檢測功能測試完成！")
    print("請檢查測試報告以優化檢測參數。")
