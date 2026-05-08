#!/usr/bin/env python3
"""
JoJo Trading 系統整合驗證
驗證DCF模型改進和交易系統功能
"""

import sys
import os
import time
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_system_status():
    """檢查系統基本狀態"""
    print("🔍 系統基本狀態檢查")
    print("=" * 60)
    
    # 檢查Python環境
    print(f"Python版本: {sys.version}")
    print(f"工作目錄: {os.getcwd()}")
    
    # 檢查關鍵套件
    required_packages = ['streamlit', 'pandas', 'numpy', 'plotly']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 已安裝")
        except ImportError:
            print(f"❌ {package}: 未安裝")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_dcf_threshold_fix():
    """檢查DCF品質門檻修復狀態"""
    print("\n🔧 DCF品質門檻修復驗證")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 4
    
    # 檢查1: data_handler.py中的設定
    try:
        with open('data_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'quality_score >= 45' in content:
                print("✅ data_handler.py: 品質門檻已修改為45分")
                checks_passed += 1
            else:
                print("❌ data_handler.py: 品質門檻修改失敗")
    except Exception as e:
        print(f"❌ 無法檢查data_handler.py: {e}")
    
    # 檢查2: integrated_dcf_handler.py中的設定
    try:
        handler_path = 'src/jojo_trading/core/integrated_dcf_handler.py'
        with open(handler_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'quality_score >= 45' in content:
                print("✅ integrated_dcf_handler.py: 品質門檻已修改為45分")
                checks_passed += 1
            else:
                print("❌ integrated_dcf_handler.py: 品質門檻修改失敗")
    except Exception as e:
        print(f"❌ 無法檢查integrated_dcf_handler.py: {e}")
    
    # 檢查3: UI app.py中的設定
    try:
        ui_path = 'src/jojo_trading/ui/app.py'
        with open(ui_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'value=machine.context.get(\'min_data_quality_score\', 45)' in content:
                print("✅ UI app.py: 預設品質分數已修改為45分")
                checks_passed += 1
            elif 'min_value=30' in content and 'max_value=90' in content:
                print("✅ UI app.py: 品質分數範圍已調整為30-90")
                checks_passed += 1
            else:
                print("❌ UI app.py: 品質分數設定可能有問題")
    except Exception as e:
        print(f"❌ 無法檢查UI app.py: {e}")
    
    # 檢查4: data_validator.py優化
    try:
        validator_path = 'src/jojo_trading/utils/data_validator.py'
        with open(validator_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'error_penalty = 25' in content and 'warning_penalty = 5' in content:
                print("✅ data_validator.py: 懲罰機制已優化")
                checks_passed += 1
            else:
                print("❌ data_validator.py: 懲罰機制優化可能失敗")
    except Exception as e:
        print(f"❌ 無法檢查data_validator.py: {e}")
    
    print(f"\nDCF門檻修復檢查結果: {checks_passed}/{total_checks} 項通過")
    assert checks_passed >= 3

def check_trading_system():
    """檢查交易系統組件"""
    print("\n📈 交易系統組件驗證")
    print("=" * 60)
    
    trading_components = [
        ('src/jojo_trading/trading/trade_recorder.py', 'TradeRecorder', '交易記錄器'),
        ('src/jojo_trading/trading/ai_advisor.py', 'AITradingAdvisor', 'AI交易建議器'),
        ('src/jojo_trading/trading/signal_generator.py', 'SignalGenerator', '信號生成器'),
        ('src/jojo_trading/trading/trading_ui.py', 'TradingSystemUI', '交易系統UI')
    ]
    
    components_ok = 0
    
    for file_path, class_name, description in trading_components:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if f'class {class_name}' in content:
                        print(f"✅ {description}: 檔案和類別完整")
                        components_ok += 1
                    else:
                        print(f"⚠️ {description}: 檔案存在但類別可能有問題")
            except Exception as e:
                print(f"❌ {description}: 讀取檔案錯誤 - {e}")
        else:
            print(f"❌ {description}: 檔案不存在 ({file_path})")
    
    print(f"\n交易系統組件檢查結果: {components_ok}/{len(trading_components)} 項正常")
    assert components_ok >= 3

def check_main_app():
    """檢查主應用程式整合"""
    print("\n🚀 主應用程式整合驗證")
    print("=" * 60)
    
    if not os.path.exists('main_app.py'):
        print("❌ main_app.py: 檔案不存在")
        assert False
    
    try:
        with open('main_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks_passed = 0
        total_checks = 4
        
        # 檢查導入
        if 'from src.jojo_trading.ui.app import main as dcf_main' in content:
            print("✅ DCF主應用模組導入正確")
            checks_passed += 1
        else:
            print("❌ DCF主應用模組導入有問題")
            
        if 'from src.jojo_trading.trading.trading_ui import TradingSystemUI' in content:
            print("✅ 交易系統UI模組導入正確")
            checks_passed += 1
        else:
            print("❌ 交易系統UI模組導入有問題")
        
        # 檢查頁面配置
        if 'st.set_page_config' in content:
            print("✅ Streamlit頁面配置正確")
            checks_passed += 1
        else:
            print("❌ Streamlit頁面配置有問題")
            
        # 檢查導航功能
        if 'navigation' in content.lower() or 'selectbox' in content or 'sidebar' in content:
            print("✅ 頁面導航功能存在")
            checks_passed += 1
        else:
            print("❌ 頁面導航功能可能缺失")
        
        print(f"\n主應用程式檢查結果: {checks_passed}/{total_checks} 項正常")
        assert checks_passed >= 3
        
    except Exception as e:
        print(f"❌ 主應用程式檢查失敗: {e}")
        assert False

def test_module_imports():
    """測試關鍵模組導入"""
    print("\n🔌 模組導入測試")
    print("=" * 60)
    
    import_tests = [
        ('streamlit', 'Streamlit UI框架'),
        ('pandas', 'Pandas數據處理'),
        ('numpy', 'Numpy數值計算'),
    ]
    
    passed_imports = 0
    
    for module_name, description in import_tests:
        try:
            __import__(module_name)
            print(f"✅ {description}: 導入成功")
            passed_imports += 1
        except ImportError as e:
            print(f"❌ {description}: 導入失敗 - {e}")
    
    # 測試項目內部模組（基本檢查，不實際導入）
    internal_modules = [
        ('src.jojo_trading.ui.app', 'DCF主應用'),
        ('src.jojo_trading.trading.trading_ui', '交易系統UI'),
        ('src.jojo_trading.trading.trade_recorder', '交易記錄器'),
        ('src.jojo_trading.trading.ai_advisor', 'AI建議器')
    ]
    
    for module_path, description in internal_modules:
        file_path = module_path.replace('.', '/') + '.py'
        if os.path.exists(file_path):
            print(f"✅ {description}: 模組檔案存在")
            passed_imports += 1
        else:
            print(f"❌ {description}: 模組檔案不存在")
    
    total_tests = len(import_tests) + len(internal_modules)
    print(f"\n模組導入測試結果: {passed_imports}/{total_tests} 項通過")
    return passed_imports >= (total_tests - 2)  # 容許少量失敗

def generate_system_report():
    """生成系統狀態報告"""
    print("\n📊 系統整合狀態報告")
    print("=" * 60)
    
    # 執行所有檢查
    basic_status = check_system_status()
    dcf_fix_status = check_dcf_threshold_fix()
    trading_status = check_trading_system()
    main_app_status = check_main_app()
    import_status = test_module_imports()
    
    # 統計結果
    passed_tests = sum([basic_status, dcf_fix_status, trading_status, main_app_status, import_status])
    total_tests = 5
    
    print(f"\n🎯 整體系統狀態: {passed_tests}/{total_tests} 項檢查通過")
    print(f"完成度: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests >= 4:
        print("\n🎉 系統整合狀態良好，可以進行功能測試！")
        status = "GOOD"
    elif passed_tests >= 3:
        print("\n⚠️ 系統基本功能正常，但有部分問題需要修復")
        status = "FAIR"
    else:
        print("\n❌ 系統存在多項問題，需要進一步修復")
        status = "POOR"
    
    # 生成簡要報告
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'overall_status': status,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'completion_rate': f"{(passed_tests/total_tests)*100:.1f}%",
        'components': {
            'basic_system': '✅' if basic_status else '❌',
            'dcf_threshold_fix': '✅' if dcf_fix_status else '❌',
            'trading_system': '✅' if trading_status else '❌',
            'main_app_integration': '✅' if main_app_status else '❌',
            'module_imports': '✅' if import_status else '❌'
        }
    }
    
    return report, status

def main():
    """主要執行函數"""
    print("🚀 JoJo Trading 系統整合驗證")
    print("=" * 80)
    print(f"驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("版本: v2.0 (包含DCF改進 + 交易系統)")
    print("=" * 80)
    
    try:
        # 執行系統驗證
        report, status = generate_system_report()
        
        # 顯示建議
        print(f"\n💡 系統建議:")
        if status == "GOOD":
            print("- 系統準備就緒，可以啟動主應用程式進行測試")
            print("- 建議使用 'streamlit run main_app.py' 啟動應用")
            print("- 可以開始進行DCF篩選和交易系統功能測試")
        elif status == "FAIR":
            print("- 系統基本功能正常，建議先修復檢查失敗的組件")
            print("- 可以啟動基本功能進行測試，但某些功能可能不穩定")
        else:
            print("- 系統存在多項問題，建議按順序修復:")
            print("  1. 檢查Python環境和套件安裝")
            print("  2. 驗證檔案結構完整性")
            print("  3. 修復模組導入問題")
        
        # 保存報告到檔案
        import json
        with open('system_verification_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 詳細報告已保存到: system_verification_report.json")
        
        return status == "GOOD"
        
    except Exception as e:
        print(f"\n❌ 系統驗證過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        assert False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*80}")
    if success:
        print("🎉 系統驗證完成 - 狀態良好")
        exit(0)
    else:
        print("⚠️ 系統驗證完成 - 發現問題")
        exit(1)
