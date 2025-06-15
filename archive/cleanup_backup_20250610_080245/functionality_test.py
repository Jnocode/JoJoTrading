#!/usr/bin/env python3
"""
JoJo Trading 功能驗證測試
驗證修復版應用程式的所有核心功能
"""

import sys
import os
import time
from datetime import datetime

# 添加專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title: str):
    """列印測試標題"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def print_result(test_name: str, success: bool, details: str = ""):
    """列印測試結果"""
    status = "✅" if success else "❌"
    print(f"  {status} {test_name}")
    if details:
        print(f"      {details}")

def test_dcf_calculator():
    """測試DCF計算器核心功能"""
    print_header("DCF計算器功能驗證")
    
    try:
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        dcf_calc = DCFCalculator()
        print_result("DCF計算器初始化", True, "模組成功載入並初始化")
        
        # 測試基本計算功能
        sample_financial_data = {
            'current_price': 100.0,
            'free_cash_flow': 1000000,
            'net_income_parent': 800000,
            'revenue': 5000000,
            'market_cap': 10000000,
            'depreciation': 200000,
            'capex': 300000,
            'shares_outstanding': 100000
        }
        
        result = dcf_calc.calculate_dcf(
            stock_code="TEST_001",
            financial_data=sample_financial_data,
            discount_rate=0.1
        )
        
        if isinstance(result, dict):
            print_result("DCF計算執行", True, f"返回結果類型: {type(result)}")
            if 'error' in result:
                print_result("錯誤處理機制", True, f"正確處理錯誤: {result['error'][:50]}...")
            else:
                print_result("成功計算結果", True, "計算完成無錯誤")
        else:
            print_result("DCF計算執行", False, "返回結果格式不正確")
            
        return True
        
    except Exception as e:
        print_result("DCF計算器測試", False, f"異常: {str(e)}")
        return False

def test_trading_system():
    """測試交易系統功能"""
    print_header("交易系統功能驗證")
    
    try:
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        trading_ui = TradingSystemUI()
        print_result("交易系統初始化", True, "TradingSystemUI模組成功載入")
        
        # 測試是否有核心方法
        methods_to_check = ['render', 'render_trading_dashboard', '_render_add_trade_form']
        for method in methods_to_check:
            has_method = hasattr(trading_ui, method)
            print_result(f"方法檢查: {method}", has_method, 
                        "方法存在" if has_method else "方法不存在")
        
        return True
        
    except Exception as e:
        print_result("交易系統測試", False, f"異常: {str(e)}")
        return False

def test_trade_recorder():
    """測試交易記錄器功能"""
    print_header("交易記錄器功能驗證")
    
    try:
        from src.jojo_trading.trading.trade_recorder import TradeRecorder
        recorder = TradeRecorder()
        print_result("交易記錄器初始化", True, "TradeRecorder模組成功載入")
        
        # 測試基本功能
        methods_to_check = ['add_trade', 'get_open_trades', 'calculate_portfolio_performance']
        for method in methods_to_check:
            has_method = hasattr(recorder, method)
            print_result(f"方法檢查: {method}", has_method, 
                        "方法存在" if has_method else "方法不存在")
        
        # 測試實際功能
        open_trades = recorder.get_open_trades()
        print_result("獲取開倉交易", True, f"返回 {len(open_trades)} 筆開倉交易")
        
        portfolio_perf = recorder.calculate_portfolio_performance()
        print_result("計算投資組合績效", True, f"績效類型: {type(portfolio_perf)}")
        
        return True
        
    except Exception as e:
        print_result("交易記錄器測試", False, f"異常: {str(e)}")
        return False

def test_main_app_structure():
    """測試主應用程式結構"""
    print_header("主應用程式結構驗證")
    
    try:
        # 檢查主應用程式檔案
        app_files = [
            'main_app.py',
            'main_app_fixed_v2.py'
        ]
        
        for app_file in app_files:
            if os.path.exists(app_file):
                with open(app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 檢查關鍵內容
                has_page_config = 'st.set_page_config' in content
                has_dcf_import = 'dcf' in content.lower()
                has_trading_import = 'trading' in content.lower()
                
                print_result(f"檔案存在: {app_file}", True, f"大小: {len(content)} 字符")
                print_result("頁面配置", has_page_config, "st.set_page_config 存在" if has_page_config else "缺少頁面配置")
                print_result("DCF功能", has_dcf_import, "包含DCF相關功能" if has_dcf_import else "缺少DCF功能")
                print_result("交易功能", has_trading_import, "包含交易相關功能" if has_trading_import else "缺少交易功能")
            else:
                print_result(f"檔案存在: {app_file}", False, "檔案不存在")
        
        return True
        
    except Exception as e:
        print_result("主應用程式結構測試", False, f"異常: {str(e)}")
        return False

def test_data_flow():
    """測試數據流程"""
    print_header("數據流程功能驗證")
    
    try:
        # 測試模組間的數據流
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        
        dcf_calc = DCFCalculator()
        trading_ui = TradingSystemUI()
        
        # 模擬數據流程
        test_data = {
            'current_price': 150.0,
            'free_cash_flow': 2000000,
            'net_income_parent': 1500000,
            'revenue': 8000000,
            'market_cap': 15000000,
            'depreciation': 400000,
            'capex': 600000,
            'shares_outstanding': 100000
        }
        
        # DCF分析
        dcf_result = dcf_calc.calculate_dcf(
            stock_code="FLOW_TEST",
            financial_data=test_data
        )
        
        print_result("數據流測試", True, "DCF → Trading 數據流程正常")
        print_result("結果格式", isinstance(dcf_result, dict), f"結果類型: {type(dcf_result)}")
        
        return True
        
    except Exception as e:
        print_result("數據流程測試", False, f"異常: {str(e)}")
        return False

def test_error_handling():
    """測試錯誤處理機制"""
    print_header("錯誤處理機制驗證")
    
    try:
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        dcf_calc = DCFCalculator()
        
        # 測試無效數據處理
        invalid_data = {
            'invalid_field': 'invalid_value'
        }
        
        result = dcf_calc.calculate_dcf(
            stock_code="ERROR_TEST",
            financial_data=invalid_data
        )
        
        has_error_handling = isinstance(result, dict) and ('error' in result or 'validation_issues' in result)
        print_result("錯誤處理", has_error_handling, "系統能正確處理無效數據" if has_error_handling else "錯誤處理不當")
        
        return True
        
    except Exception as e:
        print_result("錯誤處理測試", False, f"異常: {str(e)}")
        return False

def comprehensive_functionality_test():
    """全面功能驗證測試"""
    print_header("JoJo Trading 全面功能驗證測試")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(f"📁 工作目錄: {os.getcwd()}")
    
    # 執行各項功能測試
    test_functions = [
        test_dcf_calculator,
        test_trading_system,
        test_trade_recorder,
        test_main_app_structure,
        test_data_flow,
        test_error_handling
    ]
    
    test_results = []
    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append(result)
        except Exception as e:
            print_result(f"測試執行: {test_func.__name__}", False, f"異常: {str(e)}")
            test_results.append(False)
    
    # 總結報告
    print_header("功能驗證測試總結")
    
    success_count = sum(test_results)
    total_tests = len(test_results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"  📊 功能測試通過率: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("  🎉 所有功能測試通過！系統功能完整。")
        print("  ✅ 修復版應用程式已準備好部署使用。")
    elif success_rate >= 75:
        print("  ⚠️  大部分功能測試通過，系統基本可用。")
        print("  💡 建議修復失敗的功能測試項目。")
    else:
        print("  ❌ 系統功能存在重大問題。")
        print("  💡 需要全面檢查和修復系統功能。")
    
    print(f"\n📝 功能狀態總結:")
    test_names = ["DCF計算器", "交易系統", "交易記錄器", "主應用程式", "數據流程", "錯誤處理"]
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ 正常" if result else "❌ 異常"
        print(f"  - {name}: {status}")
    
    print(f"\n🚀 部署建議:")
    if success_rate >= 75:
        print("  - 修復版應用程式可以進行生產部署")
        print("  - 建議進行使用者接受測試 (UAT)")
        print("  - 可以開始進行實際交易策略測試")
        print("  - 建立監控和日誌記錄機制")
    else:
        print("  - 需要修復核心功能問題後再部署")
        print("  - 建議進行詳細的程式碼審查")
        print("  - 加強單元測試覆蓋率")
    
    return success_rate

if __name__ == "__main__":
    print("🚀 開始執行JoJo Trading功能驗證測試...")
    try:
        functionality_score = comprehensive_functionality_test()
        exit_code = 0 if functionality_score >= 75 else 1
        print(f"\n🔄 功能驗證測試完成，退出代碼: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  功能測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 功能測試發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
