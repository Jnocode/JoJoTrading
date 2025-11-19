#!/usr/bin/env python3
"""
系統監控 CLI 工具

提供命令列介面查看系統健康狀態和統計資料

使用方式:
    python -m src.jojo_trading.cli.monitor            # 顯示即時統計
    python -m src.jojo_trading.cli.monitor --watch    # 持續監控
    python -m src.jojo_trading.cli.monitor --report   # 生成報告
    python -m src.jojo_trading.cli.monitor --reset    # 重置統計
"""

import sys
import time
import argparse
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.jojo_trading.utils.metrics import get_metrics_collector, print_health_report


def show_stats(format_type='text'):
    """顯示統計資料"""
    collector = get_metrics_collector()
    
    if format_type == 'json':
        print(collector.generate_report(output_format='json'))
    elif format_type == 'markdown':
        print(collector.generate_report(output_format='markdown'))
    else:
        print(collector.generate_report(output_format='text'))


def watch_stats(interval=5, format_type='text'):
    """持續監控統計"""
    try:
        while True:
            # 清除螢幕（跨平台）
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            
            show_stats(format_type)
            print(f"\n⏰ 每 {interval} 秒自動更新... (按 Ctrl+C 退出)")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n👋 監控已停止")


def generate_report(output_file=None, format_type='markdown'):
    """生成並儲存報告"""
    collector = get_metrics_collector()
    report = collector.generate_report(output_format=format_type)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 報告已儲存至: {output_file}")
    else:
        print(report)


def reset_stats():
    """重置統計資料"""
    collector = get_metrics_collector()
    
    # 確認
    response = input("⚠️  確定要重置所有統計資料？ (yes/no): ")
    if response.lower() in ['yes', 'y']:
        collector.reset()
        print("✅ 統計資料已重置")
    else:
        print("❌ 取消重置")


def show_quick_status():
    """顯示快速狀態"""
    collector = get_metrics_collector()
    health = collector.get_overall_health()
    
    print(f"\n{health['emoji']} 系統狀態: {health['status']}")
    print(f"   健康評分: {health['health_score']}/100")
    print(f"   運行時間: {health['uptime']}")
    
    api_stats = health.get('api_stats', {})
    if api_stats.get('total_requests', 0) > 0:
        print(f"\n📡 API 統計:")
        print(f"   總請求: {api_stats['total_requests']}")
        print(f"   成功率: {api_stats['success_rate']:.1f}%")
        print(f"   平均時間: {api_stats['response_time']['avg']:.2f}s")
    
    cache_stats = health.get('cache_stats', {})
    if cache_stats.get('total_operations', 0) > 0:
        print(f"\n💾 快取統計:")
        print(f"   命中率: {cache_stats['hit_rate']:.1f}%")
        print(f"   總操作: {cache_stats['total_operations']}")
    
    if health.get('issues'):
        print(f"\n⚠️  發現 {len(health['issues'])} 個問題:")
        for issue in health['issues'][:3]:  # 只顯示前 3 個
            print(f"   - {issue}")
    
    print()


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='jojo_trading 系統監控工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s                     顯示當前統計
  %(prog)s --quick             快速查看狀態
  %(prog)s --watch             持續監控（每 5 秒更新）
  %(prog)s --watch 10          持續監控（每 10 秒更新）
  %(prog)s --report            生成 Markdown 報告
  %(prog)s --report -o report.md  儲存報告到檔案
  %(prog)s --format json       以 JSON 格式顯示
  %(prog)s --reset             重置統計資料
        """
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='快速查看狀態'
    )
    
    parser.add_argument(
        '--watch', '-w',
        nargs='?',
        const=5,
        type=int,
        metavar='SECONDS',
        help='持續監控模式（預設每 5 秒更新）'
    )
    
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='生成報告'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        metavar='FILE',
        help='報告輸出檔案路徑'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'markdown', 'json'],
        default='text',
        help='輸出格式（預設: text）'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='重置統計資料'
    )
    
    args = parser.parse_args()
    
    # 處理命令
    if args.reset:
        reset_stats()
    elif args.quick:
        show_quick_status()
    elif args.watch is not None:
        watch_stats(interval=args.watch, format_type=args.format)
    elif args.report:
        format_type = 'markdown' if not args.output or args.output.endswith('.md') else args.format
        generate_report(output_file=args.output, format_type=format_type)
    else:
        show_stats(format_type=args.format)


if __name__ == '__main__':
    main()
