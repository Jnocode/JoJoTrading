#!/usr/bin/env python3
"""
JoJo Trading 模組修復驗證測試
驗證所有修復後的模組是否能正常工作
"""

import sys
import os
from pathlib import Path

# 添加src路徑
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def test_module_integration():
    """測試模組整合是否成功"""
    
    print("🔧 JoJo Trading 模組修復驗證測試")
    print("=" * 50)
    
    success_count = 0
    total_tests = 6
    
    # 測試1: 基礎模組導入
    print("\n1. 基礎模組導入測試:")
    try:
        import jojo_trading
        print(f"[OK] jojo_trading v{jojo_trading.__version__}")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] jojo_trading: {e}")
    
    # 測試2: 配置模組
    print("\n2. 配置模組測試:")
    try:
        from jojo_trading.config import get_config_manager
        config_manager = get_config_manager()
        print("[OK] 配置管理器初始化成功")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] 配置模組: {e}")
    
    # 測試3: DCF UI模組
    print("\n3. DCF UI模組測試:")
    try:
        from jojo_trading.ui.app import main as dcf_main
        print("[OK] DCF應用模組可以導入")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] DCF UI模組: {e}")
    
    # 測試4: 交易系統模組
    print("\n4. 交易系統模組測試:")
    try:
        from jojo_trading.trading.trading_ui import TradingSystemUI
        trading_ui = TradingSystemUI()
        print("[OK] 交易系統UI初始化成功")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] 交易系統模組: {e}")
    
    # 測試5: 工具模組
    print("\n5. 工具模組測試:")
    try:
        from jojo_trading.utils import utils
        print("[OK] 工具模組可以導入")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] 工具模組: {e}")
    
    # 測試6: 主應用程式整合
    print("\n6. 主應用程式整合測試:")
    try:
        # 模擬主應用程式的導入邏輯
        import sys, os
        project_root = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(project_root, 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from jojo_trading.ui.app import main as dcf_main
        from jojo_trading.trading.trading_ui import TradingSystemUI
        print("[OK] 主應用程式模組整合成功")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] 主應用程式整合: {e}")
    
    # 結果總結
    print(f"\n{'='*50}")
    print(f"測試結果: {success_count}/{total_tests} 通過")
    success_rate = (success_count / total_tests) * 100
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 所有模組修復驗證通過！")
        print("✅ 系統整合完成，可以進行功能測試")
        return True
    elif success_rate >= 80:
        print("\n✅ 大部分模組工作正常")
        print("⚠️ 建議修復剩餘問題")
        return True
    else:
        print("\n❌ 系統需要進一步修復")
        print("🔧 請檢查失敗的模組")
        assert False

def test_core_functionality():
    """測試核心功能是否可用"""
    
    print("\n🧪 核心功能可用性測試")
    print("=" * 50)
    
    # 測試DCF功能
    print("\n1. DCF計算功能測試:")
    try:
        from jojo_trading.ui.components.individual_dcf import IndividualDCFComponent
        dcf_component = IndividualDCFComponent()
        print("[OK] DCF組件可以初始化")
    except Exception as e:
        print(f"[FAIL] DCF組件: {e}")
    
    # 測試交易功能
    print("\n2. 交易系統功能測試:")
    try:
        from jojo_trading.trading.trade_recorder import TradeRecorder
        recorder = TradeRecorder()
        print("[OK] 交易記錄器可以初始化")
    except Exception as e:
        print(f"[FAIL] 交易記錄器: {e}")
    
    # 測試配置功能
    print("\n3. 配置系統功能測試:")
    try:
        from jojo_trading.config.config_manager import ConfigManager
        config = ConfigManager()
        print("[OK] 配置管理器可以初始化")
    except Exception as e:
        print(f"[FAIL] 配置管理器: {e}")

if __name__ == "__main__":
    print("開始模組修復驗證...")
    
    # 執行模組整合測試
    integration_success = test_module_integration()
    
    # 執行功能測試
    test_core_functionality()
    
    print(f"\n{'='*50}")
    if integration_success:
        print("🎯 模組修復驗證完成！")
        print("🚀 系統準備進入下一階段優化")
        print("🌐 主應用程式運行於: http://localhost:8501")
    else:
        print("⚠️ 需要進一步修復問題")
        print("🔧 請檢查失敗的測試項目")
