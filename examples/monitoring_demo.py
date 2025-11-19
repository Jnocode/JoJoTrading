"""
效能監控功能示範

展示如何使用指標收集功能來監控系統效能
"""

import sys
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import time
from src.jojo_trading.utils.metrics import get_metrics_collector
from src.jojo_trading.utils.helpers import api_request_with_retry

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_api_monitoring():
    """示範 API 請求監控"""
    logger.info("🚀 開始 API 監控示範")
    
    collector = get_metrics_collector()
    collector.reset()
    
    # 模擬多次 API 請求
    test_urls = [
        'https://httpbin.org/status/200',  # 成功
        'https://httpbin.org/delay/2',      # 延遲 2 秒
        'https://httpbin.org/status/500',   # 伺服器錯誤
        'https://httpbin.org/status/200',   # 成功
    ]
    
    for i, url in enumerate(test_urls, 1):
        logger.info(f"📡 請求 {i}/{len(test_urls)}: {url}")
        
        try:
            response = api_request_with_retry(
                url,
                timeout=10,
                max_retries=2,
                enable_metrics=True
            )
            logger.info(f"✅ 成功: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 失敗: {e}")
        
        time.sleep(0.5)  # 避免請求過快
    
    # 顯示統計
    logger.info("\n" + "="*60)
    logger.info("📊 API 請求統計")
    logger.info("="*60)
    
    stats = collector.get_api_statistics()
    
    print(f"\n總請求數: {stats['total_requests']}")
    print(f"成功率: {stats['success_rate']:.1f}%")
    print(f"平均回應時間: {stats['response_time']['avg']:.2f} 秒")
    print(f"最慢請求: {stats['response_time']['max']:.2f} 秒")
    
    if stats['total_retries'] > 0:
        print(f"\n⚠️  觸發重試: {stats['total_retries']} 次")
        print(f"重試率: {stats['retry_triggered_rate']:.1f}%")


def demo_cache_monitoring():
    """示範快取監控"""
    logger.info("\n🚀 開始快取監控示範")
    
    collector = get_metrics_collector()
    
    # 模擬快取操作
    cache_operations = [
        ('hit', 'stock_2330'),
        ('hit', 'stock_2317'),
        ('miss', 'stock_2454'),
        ('write', 'stock_2454'),
        ('hit', 'stock_2330'),
        ('stale', 'stock_2412'),
        ('hit', 'stock_2317'),
    ]
    
    for operation, key in cache_operations:
        collector.record_cache_operation(operation, key)
        logger.info(f"💾 快取 {operation}: {key}")
        time.sleep(0.2)
    
    # 顯示統計
    logger.info("\n" + "="*60)
    logger.info("📊 快取統計")
    logger.info("="*60)
    
    stats = collector.get_cache_statistics()
    
    print(f"\n總操作數: {stats['total_operations']}")
    print(f"命中: {stats['cache_hits']}")
    print(f"未命中: {stats['cache_misses']}")
    print(f"命中率: {stats['hit_rate']:.1f}%")
    print(f"有效命中率: {stats['effective_hit_rate']:.1f}% (含過期)")


def demo_health_monitoring():
    """示範系統健康監控"""
    logger.info("\n🚀 開始健康狀態監控示範")
    
    collector = get_metrics_collector()
    
    # 取得健康狀態
    health = collector.get_overall_health()
    
    logger.info("\n" + "="*60)
    logger.info(f"{health['emoji']} 系統健康報告")
    logger.info("="*60)
    
    print(f"\n狀態: {health['status']}")
    print(f"評分: {health['health_score']}/100")
    print(f"運行時間: {health['uptime']}")
    
    if health['issues']:
        print(f"\n⚠️  發現問題:")
        for issue in health['issues']:
            print(f"  - {issue}")
    else:
        print(f"\n✅ 系統運行正常，無問題發現")


def demo_report_generation():
    """示範報告生成"""
    logger.info("\n🚀 開始報告生成示範")
    
    collector = get_metrics_collector()
    
    # 生成不同格式的報告
    formats = ['text', 'markdown', 'json']
    
    for fmt in formats:
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 {fmt.upper()} 格式報告")
        logger.info(f"{'='*60}\n")
        
        report = collector.generate_report(output_format=fmt)
        
        if fmt == 'json':
            # JSON 格式只顯示前 200 字元
            print(report[:200] + "...\n")
        else:
            print(report)
        
        # 儲存到檔案
        output_file = f"performance_report.{fmt if fmt != 'text' else 'txt'}"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"✅ 報告已儲存至: {output_file}")
        except Exception as e:
            logger.error(f"❌ 儲存失敗: {e}")


def main():
    """主函數"""
    print("\n" + "="*60)
    print("🎯 jojo_trading 效能監控功能示範")
    print("="*60 + "\n")
    
    try:
        # 1. API 監控
        demo_api_monitoring()
        
        # 2. 快取監控
        demo_cache_monitoring()
        
        # 3. 健康監控
        demo_health_monitoring()
        
        # 4. 報告生成
        demo_report_generation()
        
        print("\n" + "="*60)
        print("✅ 示範完成！")
        print("="*60)
        print("\n提示：使用以下命令查看即時監控：")
        print("  python -m src.jojo_trading.cli.monitor --quick")
        print("  python -m src.jojo_trading.cli.monitor --watch")
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 示範已中斷")
    except Exception as e:
        logger.error(f"❌ 執行錯誤: {e}", exc_info=True)


if __name__ == '__main__':
    main()
