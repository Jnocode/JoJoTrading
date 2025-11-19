"""
快取效能監控示範

展示快取監控功能的實際運作
"""

import sys
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from src.jojo_trading.utils.metrics import get_metrics_collector

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_cache_monitoring_with_real_data():
    """使用實際資料處理器測試快取監控"""
    logger.info("🚀 開始快取監控示範（使用實際資料）")
    
    try:
        from src.jojo_trading.core.data_handler import fetch_finmind_financial_statement_data
        import pandas as pd
        from datetime import datetime, timedelta
        
        collector = get_metrics_collector()
        collector.reset()
        
        # 測試股票代碼
        test_stocks = ['2330', '2317']
        statement_types = ['FinancialStatements', 'BalanceSheet']
        
        # 計算一年前的日期
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        logger.info(f"\n📊 測試快取效能")
        logger.info(f"  測試股票: {', '.join(test_stocks)}")
        logger.info(f"  報表類型: {', '.join(statement_types)}")
        logger.info(f"  起始日期: {one_year_ago}")
        
        # 第一輪：首次請求（預期 MISS）
        logger.info("\n🔄 第一輪請求（預期快取未命中）")
        for stock_id in test_stocks:
            for stmt_type in statement_types:
                logger.info(f"  請求: {stock_id} - {stmt_type}")
                try:
                    df = fetch_finmind_financial_statement_data(
                        stock_id=stock_id,
                        start_date=one_year_ago,
                        statement_type=stmt_type
                    )
                    if df is not None and not df.empty:
                        logger.info(f"    ✅ 取得 {len(df)} 筆資料")
                    else:
                        logger.warning(f"    ⚠️  無資料")
                except Exception as e:
                    logger.error(f"    ❌ 錯誤: {e}")
        
        # 檢視第一輪統計
        stats1 = collector.get_cache_statistics()
        logger.info(f"\n📈 第一輪統計:")
        logger.info(f"  總操作數: {stats1.get('total_operations', 0)}")
        logger.info(f"  命中: {stats1.get('cache_hits', 0)}")
        logger.info(f"  未命中: {stats1.get('cache_misses', 0)}")
        logger.info(f"  寫入: {stats1.get('cache_writes', 0)}")
        
        # 第二輪：重複請求（預期 HIT）
        logger.info("\n🔄 第二輪請求（預期快取命中）")
        for stock_id in test_stocks:
            for stmt_type in statement_types:
                logger.info(f"  請求: {stock_id} - {stmt_type}")
                try:
                    df = fetch_finmind_financial_statement_data(
                        stock_id=stock_id,
                        start_date=one_year_ago,
                        statement_type=stmt_type
                    )
                    if df is not None and not df.empty:
                        logger.info(f"    ✅ 取得 {len(df)} 筆資料（應來自快取）")
                except Exception as e:
                    logger.error(f"    ❌ 錯誤: {e}")
        
        # 最終統計
        stats2 = collector.get_cache_statistics()
        logger.info(f"\n📈 最終統計:")
        logger.info(f"  總操作數: {stats2.get('total_operations', 0)}")
        logger.info(f"  命中: {stats2.get('cache_hits', 0)}")
        logger.info(f"  未命中: {stats2.get('cache_misses', 0)}")
        logger.info(f"  寫入: {stats2.get('cache_writes', 0)}")
        logger.info(f"  命中率: {stats2.get('hit_rate', 0):.1f}%")
        
        # 計算快取效益
        if stats2.get('cache_hits', 0) > 0:
            cache_benefit = (stats2['cache_hits'] / stats2['total_operations']) * 100
            logger.info(f"\n✨ 快取效益:")
            logger.info(f"  避免了 {stats2['cache_hits']} 次 API 請求")
            logger.info(f"  快取效益: {cache_benefit:.1f}%")
        
    except ImportError as e:
        logger.error(f"❌ 無法載入資料處理器: {e}")
        logger.info("  提示: 請確認 FinMind 憑證已設定")
    except Exception as e:
        logger.error(f"❌ 執行錯誤: {e}", exc_info=True)


def demo_cache_statistics_detail():
    """顯示詳細的快取統計"""
    logger.info("\n🚀 詳細快取統計示範")
    
    collector = get_metrics_collector()
    
    # 顯示整體健康狀態
    health = collector.get_overall_health()
    
    logger.info(f"\n{health['emoji']} 系統健康狀態")
    logger.info(f"  評分: {health['health_score']}/100")
    logger.info(f"  狀態: {health['status']}")
    
    # 快取詳細統計
    cache_stats = health.get('cache_stats', {})
    if cache_stats.get('total_operations', 0) > 0:
        logger.info(f"\n💾 快取詳細統計:")
        logger.info(f"  總操作數: {cache_stats['total_operations']}")
        logger.info(f"  命中: {cache_stats['cache_hits']}")
        logger.info(f"  未命中: {cache_stats['cache_misses']}")
        logger.info(f"  寫入: {cache_stats['cache_writes']}")
        logger.info(f"  過期: {cache_stats.get('stale_cache', 0)}")
        logger.info(f"  命中率: {cache_stats['hit_rate']:.1f}%")
        logger.info(f"  有效命中率: {cache_stats.get('effective_hit_rate', 0):.1f}%")
    else:
        logger.info("\n💾 尚無快取操作記錄")
    
    # API 統計
    api_stats = health.get('api_stats', {})
    if api_stats.get('total_requests', 0) > 0:
        logger.info(f"\n📡 API 請求統計:")
        logger.info(f"  總請求數: {api_stats['total_requests']}")
        logger.info(f"  成功率: {api_stats['success_rate']:.1f}%")
        logger.info(f"  平均回應時間: {api_stats['response_time']['avg']:.2f}s")


def analyze_cache_efficiency():
    """分析快取效率並提供建議"""
    logger.info("\n🔍 快取效率分析")
    
    collector = get_metrics_collector()
    cache_stats = collector.get_cache_statistics()
    
    if cache_stats.get('total_operations', 0) == 0:
        logger.warning("  ⚠️  無足夠資料進行分析")
        return
    
    hit_rate = cache_stats.get('hit_rate', 0)
    total_ops = cache_stats['total_operations']
    
    logger.info(f"\n📊 效率評估:")
    logger.info(f"  總操作數: {total_ops}")
    logger.info(f"  命中率: {hit_rate:.1f}%")
    
    # 評分
    if hit_rate >= 70:
        rating = "優秀 🟢"
        advice = "快取效果良好，繼續保持！"
    elif hit_rate >= 50:
        rating = "良好 🟡"
        advice = "快取有效，可考慮增加快取時間"
    elif hit_rate >= 30:
        rating = "普通 🟠"
        advice = "建議檢查快取策略，考慮增加 TTL"
    else:
        rating = "需改善 🔴"
        advice = "快取效果不佳，建議實作 LRU 記憶體快取"
    
    logger.info(f"  評分: {rating}")
    logger.info(f"  建議: {advice}")
    
    # 計算潛在節省的時間
    if cache_stats.get('cache_hits', 0) > 0:
        # 假設每次 API 請求平均需要 2 秒
        time_saved = cache_stats['cache_hits'] * 2
        logger.info(f"\n⏱️  時間節省估算:")
        logger.info(f"  約節省 {time_saved:.1f} 秒 API 請求時間")


def main():
    """主函數"""
    print("\n" + "="*60)
    print("💾 jojo_trading 快取監控功能示範")
    print("="*60 + "\n")
    
    try:
        # 1. 實際資料快取測試
        demo_cache_monitoring_with_real_data()
        
        # 2. 詳細統計
        demo_cache_statistics_detail()
        
        # 3. 效率分析
        analyze_cache_efficiency()
        
        print("\n" + "="*60)
        print("✅ 示範完成！")
        print("="*60)
        print("\n提示：")
        print("  - 快取位於 src/jojo_trading/core/cache/ 目錄")
        print("  - 使用 monitor 工具查看即時統計")
        print("  - 快取預設 TTL: 24 小時")
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 示範已中斷")
    except Exception as e:
        logger.error(f"❌ 執行錯誤: {e}", exc_info=True)


if __name__ == '__main__':
    main()
