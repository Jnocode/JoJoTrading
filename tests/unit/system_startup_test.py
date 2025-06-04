#!/usr/bin/env python3
"""
系統啟動測試腳本
測試所有關鍵模組是否能正常載入和運行
"""

import sys
import traceback
from datetime import datetime

def test_imports():
    """測試模組導入"""
    print("=" * 50)
    print("📦 模組導入測試")
    print("=" * 50)
    
    # 基礎模組測試
    test_results = []
    
    # 測試Streamlit
    try:
        import streamlit as st
        test_results.append(("✅", "Streamlit", "成功"))
    except Exception as e:
        test_results.append(("❌", "Streamlit", f"失敗: {e}"))
    
    # 測試DCF分析UI
    try:
        from src.jojo_trading.ui.app import main as dcf_main
        test_results.append(("✅", "DCF分析UI", "成功"))
    except Exception as e:
        test_results.append(("❌", "DCF分析UI", f"失敗: {e}"))
    
    # 測試交易系統UI
    try:
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        test_results.append(("✅", "交易系統UI", "成功"))
    except Exception as e:
        test_results.append(("❌", "交易系統UI", f"失敗: {e}"))
    
    # 測試交易記錄器
    try:
        from src.jojo_trading.trading.trade_recorder import TradeRecorder
        test_results.append(("✅", "交易記錄器", "成功"))
    except Exception as e:
        test_results.append(("❌", "交易記錄器", f"失敗: {e}"))
    
    # 測試AI建議引擎
    try:
        from src.jojo_trading.trading.ai_advisor import AITradingAdvisor
        test_results.append(("✅", "AI建議引擎", "成功"))
    except Exception as e:
        test_results.append(("❌", "AI建議引擎", f"失敗: {e}"))
    
    # 測試信號生成器
    try:
        from src.jojo_trading.trading.signal_generator import SignalGenerator
        test_results.append(("✅", "信號生成器", "成功"))
    except Exception as e:
        test_results.append(("❌", "信號生成器", f"失敗: {e}"))
    
    # 測試DCF處理器
    try:
        from src.jojo_trading.core.integrated_dcf_handler import IntegratedDCFHandler
        test_results.append(("✅", "DCF處理器", "成功"))
    except Exception as e:
        test_results.append(("❌", "DCF處理器", f"失敗: {e}"))
    
    # 輸出結果
    for status, module, result in test_results:
        print(f"{status} {module:<20} {result}")
    
    success_count = sum(1 for status, _, _ in test_results if status == "✅")
    total_count = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {success_count}/{total_count} 模組正常載入")
    print("=" * 50)
    
    return success_count == total_count

def test_dcf_functionality():
    """測試DCF功能"""
    print("\n💰 DCF功能測試")
    print("=" * 30)
    
    try:
        from data_handler import main as data_main
        print("✅ data_handler.py 導入成功")
        
        # 測試基本配置
        from src.jojo_trading.utils.config_loader import ConfigLoader
        config_loader = ConfigLoader()
        print("✅ ConfigLoader 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ DCF功能測試失敗: {e}")
        traceback.print_exc()
        return False

def test_trading_system():
    """測試交易系統功能"""
    print("\n🤖 交易系統功能測試")
    print("=" * 30)
    
    try:
        # 測試交易記錄器初始化
        from src.jojo_trading.trading.trade_recorder import TradeRecorder
        recorder = TradeRecorder()
        print("✅ TradeRecorder 初始化成功")
        
        # 測試AI建議引擎初始化
        from src.jojo_trading.trading.ai_advisor import AITradingAdvisor
        advisor = AITradingAdvisor()
        print("✅ AITradingAdvisor 初始化成功")
        
        # 測試信號生成器初始化
        from src.jojo_trading.trading.signal_generator import SignalGenerator
        signal_gen = SignalGenerator()
        print("✅ SignalGenerator 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 交易系統功能測試失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print(f"🚀 JoJo Trading 系統啟動測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"📂 工作目錄: {sys.path[0]}")
    
    # 執行測試
    import_test = test_imports()
    dcf_test = test_dcf_functionality()
    trading_test = test_trading_system()
    
    # 綜合結果
    print("\n" + "=" * 50)
    print("🎯 綜合測試結果")
    print("=" * 50)
    
    print(f"📦 模組導入測試: {'✅ 通過' if import_test else '❌ 失敗'}")
    print(f"💰 DCF功能測試: {'✅ 通過' if dcf_test else '❌ 失敗'}")
    print(f"🤖 交易系統測試: {'✅ 通過' if trading_test else '❌ 失敗'}")
    
    overall_success = import_test and dcf_test and trading_test
    
    print(f"\n🏆 總體狀態: {'✅ 系統準備就緒' if overall_success else '❌ 系統需要修復'}")
    
    if overall_success:
        print("\n🎉 恭喜！所有系統測試通過，可以啟動應用程式：")
        print("   python -m streamlit run main_app.py")
    else:
        print("\n⚠️  系統存在問題，請檢查錯誤信息並修復後重新測試")
    
    return overall_success

if __name__ == "__main__":
    main()
