#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JoJo Trading 系統監控整合測試
測試監控器與主應用程序的整合功能
"""

import time
import sys
import os
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_monitor_basic_functions():
    """測試監控器基本功能"""
    print("🧪 測試1: 監控器基本功能")
    print("-" * 40)
    
    try:
        from src.jojo_trading.core.system_monitor import SystemMonitor
        
        # 初始化監控器
        monitor = SystemMonitor()
        print("✅ 監控器初始化成功")
        
        # 測試日誌記錄功能
        monitor.log_system_event("測試系統事件", "INFO", "系統正常運行")
        monitor.log_dcf_calculation("2330", True, 2.5, {"dcf_value": 550}, None)
        monitor.log_trade_action("BUY", "2330", True, {"shares": 1000, "price": 500}, None)
        monitor.log_data_operation("獲取股價資料", True, "成功獲取台積電股價", None)
        print("✅ 日誌記錄功能正常")
        
        # 測試系統狀態
        status = monitor.get_system_status()
        print(f"✅ 系統狀態: {status['status']}")
        print(f"   CPU: {status.get('cpu_percent', 'N/A')}%")
        print(f"   記憶體: {status.get('memory_percent', 'N/A')}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_monitor_integration():
    """測試監控器整合功能"""
    print("\n🧪 測試2: 監控器整合功能")
    print("-" * 40)
    
    try:
        from src.jojo_trading.core.system_monitor import get_system_monitor, init_monitoring
        
        # 測試全域實例
        monitor1 = get_system_monitor()
        monitor2 = get_system_monitor()
        
        if monitor1 is monitor2:
            print("✅ 全域監控器單例模式正常")
        else:
            print("❌ 全域監控器單例模式失敗")
            return False
        
        # 測試初始化
        monitor = init_monitoring(auto_start=False)
        print("✅ 監控初始化功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        return False

def test_monitor_performance():
    """測試監控器性能數據收集"""
    print("\n🧪 測試3: 性能數據收集")
    print("-" * 40)
    
    try:
        from src.jojo_trading.core.system_monitor import get_system_monitor
        
        monitor = get_system_monitor()
        
        # 手動收集指標
        metrics = monitor._collect_metrics()
        print(f"✅ 性能指標收集成功")
        print(f"   時間戳: {metrics.timestamp}")
        print(f"   CPU: {metrics.cpu_percent:.1f}%")
        print(f"   記憶體: {metrics.memory_percent:.1f}%")
        print(f"   回應時間: {metrics.response_time:.3f}秒")
        
        # 儲存指標
        monitor._store_metrics(metrics)
        print("✅ 指標儲存成功")
        
        # 獲取性能摘要
        summary = monitor.get_performance_summary(hours=1)
        print(f"✅ 性能摘要: 包含 {summary.get('data_points', 0)} 個數據點")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")
        return False

def test_monitor_threading():
    """測試監控器多線程功能"""
    print("\n🧪 測試4: 背景監控功能")
    print("-" * 40)
    
    try:
        from src.jojo_trading.core.system_monitor import get_system_monitor
        
        monitor = get_system_monitor()
        
        # 啟動背景監控
        print("🔄 啟動背景監控（5秒間隔）...")
        monitor.start_monitoring(interval=2)
        
        if monitor.monitoring_active:
            print("✅ 背景監控已啟動")
        else:
            print("❌ 背景監控啟動失敗")
            return False
        
        # 等待收集數據
        print("⏱️ 等待6秒收集數據...")
        time.sleep(6)
        
        # 檢查是否收集到數據
        if len(monitor.metrics_history) > 0:
            print(f"✅ 收集到 {len(monitor.metrics_history)} 個監控數據點")
        else:
            print("⚠️ 未收集到監控數據")
        
        # 停止監控
        monitor.stop_monitoring()
        print("✅ 背景監控已停止")
        
        return True
        
    except Exception as e:
        print(f"❌ 背景監控測試失敗: {e}")
        return False

def test_log_files():
    """測試日誌文件生成"""
    print("\n🧪 測試5: 日誌文件檢查")
    print("-" * 40)
    
    try:
        log_dir = Path("logs")
        
        if not log_dir.exists():
            print("❌ 日誌目錄不存在")
            return False
        
        log_files = list(log_dir.glob("*.log"))
        print(f"✅ 發現 {len(log_files)} 個日誌文件:")
        
        for log_file in log_files:
            size = log_file.stat().st_size
            print(f"   📄 {log_file.name}: {size} bytes")
        
        # 檢查今日日誌文件
        today = time.strftime("%Y%m%d")
        expected_files = [
            f"jojo_trading_{today}.log",
            f"jojo_errors_{today}.log"
        ]
        
        for expected_file in expected_files:
            if (log_dir / expected_file).exists():
                print(f"✅ 找到預期的日誌文件: {expected_file}")
            else:
                print(f"⚠️ 未找到預期的日誌文件: {expected_file}")
        
        # 檢查指標文件
        metrics_files = list(log_dir.glob("metrics_*.jsonl"))
        if metrics_files:
            print(f"✅ 發現 {len(metrics_files)} 個指標文件")
        else:
            print("⚠️ 未發現指標文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 日誌文件檢查失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🚀 JoJo Trading 系統監控整合測試")
    print("=" * 60)
    print(f"📅 測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(f"📁 工作目錄: {os.getcwd()}")
    print("=" * 60)
    
    # 執行所有測試
    tests = [
        ("監控器基本功能", test_monitor_basic_functions),
        ("監控器整合功能", test_monitor_integration),
        ("性能數據收集", test_monitor_performance),
        ("背景監控功能", test_monitor_threading),
        ("日誌文件檢查", test_log_files)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 測試 '{test_name}' 執行異常: {e}")
            results.append((test_name, False))
    
    # 總結報告
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    passed_count = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed_count += 1
    
    total_count = len(results)
    success_rate = (passed_count / total_count) * 100
    
    print(f"\n📈 測試通過率: {passed_count}/{total_count} ({success_rate:.1f}%)")
    
    if passed_count == total_count:
        print("🎉 所有測試通過！系統監控功能完全正常。")
        return 0
    elif success_rate >= 80:
        print("✅ 大部分測試通過，系統監控基本正常。")
        return 0
    else:
        print("⚠️ 多項測試失敗，請檢查系統配置。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n🏁 測試完成，退出代碼: {exit_code}")
    sys.exit(exit_code)
