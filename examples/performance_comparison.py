"""
效能比較測試：記憶體快取 vs 磁碟快取

比較有無記憶體快取層的效能差異。

Author: jojo_trading team
Date: 2025-11-19
"""

import time
import os
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.jojo_trading.utils.memory_cache import get_memory_cache
from src.jojo_trading.utils.metrics import get_metrics_collector


def demo_cache_layers_performance():
    """
    演示記憶體快取與磁碟快取的效能差異
    """
    print("\n" + "="*70)
    print("🚀 快取效能比較測試")
    print("="*70)
    
    # 取得記憶體快取實例
    memory_cache = get_memory_cache(
        max_items=100,
        max_memory_mb=50,
        default_ttl=3600
    )
    
    # 模擬資料
    import pandas as pd
    
    # 建立模擬的財務報表數據
    test_data = pd.DataFrame({
        'date': pd.date_range('2020-01-01', periods=100, freq='D'),
        'revenue': range(1000, 1100),
        'net_income': range(100, 200),
        'assets': range(5000, 5100),
    })
    
    print(f"\n📊 測試數據大小: {test_data.shape}")
    print(f"   記憶體使用: {sys.getsizeof(test_data)} bytes")
    
    # 清空記憶體快取以確保公平測試
    memory_cache.clear()
    
    # 測試 1: 第一次訪問（無快取，需從磁碟或API）
    print("\n" + "-"*70)
    print("📝 測試 1: 第一次訪問（模擬磁碟 I/O）")
    print("-"*70)
    
    start = time.perf_counter()
    # 模擬磁碟讀取延遲（通常 10-50ms）
    time.sleep(0.02)  # 20ms
    result1 = test_data.copy()
    disk_time = (time.perf_counter() - start) * 1000
    
    print(f"⏱️  磁碟讀取時間: {disk_time:.2f} ms")
    
    # 儲存到記憶體快取
    cache_key = "test_2330_financial_20200101"
    memory_cache.set(cache_key, result1.copy())
    
    # 測試 2: 第二次訪問（記憶體快取命中）
    print("\n" + "-"*70)
    print("📝 測試 2: 第二次訪問（記憶體快取命中）")
    print("-"*70)
    
    start = time.perf_counter()
    result2 = memory_cache.get(cache_key)
    memory_time = (time.perf_counter() - start) * 1000
    
    print(f"⏱️  記憶體讀取時間: {memory_time:.4f} ms")
    print(f"✅ 資料正確: {result2 is not None and result2.shape == test_data.shape}")
    
    # 測試 3: 連續訪問測試
    print("\n" + "-"*70)
    print("📝 測試 3: 連續訪問 100 次")
    print("-"*70)
    
    # 模擬磁碟訪問
    start = time.perf_counter()
    for _ in range(100):
        time.sleep(0.001)  # 模擬 1ms 磁碟延遲
        _ = test_data.copy()
    disk_batch_time = (time.perf_counter() - start) * 1000
    
    print(f"💾 磁碟批次讀取: {disk_batch_time:.2f} ms")
    
    # 記憶體訪問
    start = time.perf_counter()
    for _ in range(100):
        _ = memory_cache.get(cache_key)
    memory_batch_time = (time.perf_counter() - start) * 1000
    
    print(f"🚀 記憶體批次讀取: {memory_batch_time:.4f} ms")
    
    # 效能提升計算
    print("\n" + "="*70)
    print("📊 效能分析結果")
    print("="*70)
    
    speedup_single = disk_time / memory_time if memory_time > 0 else float('inf')
    speedup_batch = disk_batch_time / memory_batch_time if memory_batch_time > 0 else float('inf')
    
    print(f"\n單次訪問:")
    print(f"  • 磁碟快取: {disk_time:.2f} ms")
    print(f"  • 記憶體快取: {memory_time:.4f} ms")
    print(f"  • 加速比: {speedup_single:.0f}x")
    
    print(f"\n批次訪問 (100次):")
    print(f"  • 磁碟快取: {disk_batch_time:.2f} ms")
    print(f"  • 記憶體快取: {memory_batch_time:.4f} ms")
    print(f"  • 加速比: {speedup_batch:.0f}x")
    
    # 記憶體快取統計
    print("\n" + "-"*70)
    print("📈 記憶體快取統計")
    print("-"*70)
    
    stats = memory_cache.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  • {key}: {value:.2f}")
        else:
            print(f"  • {key}: {value}")
    
    # 估算實際應用效益
    print("\n" + "="*70)
    print("💰 實際應用效益估算")
    print("="*70)
    
    # 假設每天分析 50 檔股票，每檔 3 種報表
    daily_operations = 50 * 3
    saved_time_per_day = (disk_time - memory_time) * daily_operations / 1000  # 轉換為秒
    
    print(f"\n假設場景: 每天分析 50 檔股票 × 3 種報表 = {daily_operations} 次操作")
    print(f"  • 使用磁碟快取: {disk_time * daily_operations / 1000:.2f} 秒")
    print(f"  • 使用記憶體快取: {memory_time * daily_operations / 1000:.4f} 秒")
    print(f"  • 每天節省時間: {saved_time_per_day:.2f} 秒")
    print(f"  • 每月節省時間: {saved_time_per_day * 30 / 60:.2f} 分鐘")
    print(f"  • 每年節省時間: {saved_time_per_day * 365 / 3600:.2f} 小時")


def demo_with_metrics():
    """
    演示整合指標收集的效能測試
    """
    print("\n" + "="*70)
    print("📊 整合指標收集測試")
    print("="*70)
    
    collector = get_metrics_collector()
    memory_cache = get_memory_cache()
    
    # 重設統計
    collector.reset()
    memory_cache.clear()
    
    # 模擬快取操作
    print("\n正在模擬快取操作...")
    
    import pandas as pd
    test_data = pd.DataFrame({'value': range(100)})
    
    # 10 次 miss + write
    for i in range(10):
        collector.record_cache_operation('miss', f'stock_{i}')
        memory_cache.set(f'stock_{i}', test_data.copy())
        collector.record_cache_operation('write', f'stock_{i}')
    
    # 20 次 hit
    for i in range(10):
        _ = memory_cache.get(f'stock_{i}')
        collector.record_cache_operation('hit', f'stock_{i}')
        _ = memory_cache.get(f'stock_{i}')
        collector.record_cache_operation('hit', f'stock_{i}')
    
    # 顯示快取統計
    print("\n" + "-"*70)
    print("📈 快取操作統計")
    print("-"*70)
    
    cache_stats = collector.get_cache_statistics()
    print(f"\n  • 總操作數: {cache_stats['total_operations']}")
    print(f"  • 命中數: {cache_stats['cache_hits']}")
    print(f"  • 未命中數: {cache_stats['cache_misses']}")
    print(f"  • 命中率: {cache_stats['hit_rate']:.2f}%")
    print(f"  • 寫入數: {cache_stats['cache_writes']}")
    
    # 顯示記憶體快取狀態
    print("\n" + "-"*70)
    print("💾 記憶體快取狀態")
    print("-"*70)
    
    mem_stats = memory_cache.get_stats()
    print(f"\n  • 快取項目數: {mem_stats['total_items']}")
    print(f"  • 記憶體使用: {mem_stats['total_size_mb']:.2f} MB")
    print(f"  • 使用率: {mem_stats['utilization']:.1f}%")
    print(f"  • 內部命中率: {mem_stats['hit_rate']:.2f}%")
    
    # 健康分數
    print("\n" + "-"*70)
    print("🏥 系統健康評分")
    print("-"*70)
    
    health = collector.get_overall_health()
    print(f"\n  總分: {health['health_score']:.1f}/100")
    print(f"  狀態: {health['status']} {health['emoji']}")
    print(f"  運行時間: {health['uptime']}")


def main():
    """主程式"""
    print("\n" + "="*70)
    print("🎯 JoJo Trading 快取效能測試套件")
    print("="*70)
    
    try:
        # 測試 1: 快取層效能比較
        demo_cache_layers_performance()
        
        # 測試 2: 整合指標收集
        demo_with_metrics()
        
        print("\n" + "="*70)
        print("✅ 所有測試完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
