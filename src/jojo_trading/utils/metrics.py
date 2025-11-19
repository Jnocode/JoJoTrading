"""
效能與統計追蹤模組

提供系統級別的效能指標追蹤功能，包括：
- API 請求統計
- 快取命中率
- 回應時間分析
- 錯誤率追蹤

Author: jojo_trading team
Date: 2025-11-19
Version: 1.0.0
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
import statistics

logger = logging.getLogger(__name__)


@dataclass
class APIRequestMetric:
    """單次 API 請求的指標資料"""
    url: str
    method: str
    status_code: Optional[int]
    duration: float  # 秒
    retry_count: int
    success: bool
    error_type: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CacheMetric:
    """快取操作的指標資料"""
    operation: str  # 'hit', 'miss', 'write', 'stale'
    cache_key: str
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """
    集中式指標收集器
    
    特性：
    - 執行緒安全
    - 記憶體效率（循環緩衝區）
    - 即時統計計算
    - 可匯出報告
    """
    
    def __init__(self, max_records: int = 10000):
        """
        初始化指標收集器
        
        Args:
            max_records: 最大保存記錄數（防止記憶體溢出）
        """
        self._lock = Lock()
        self.max_records = max_records
        
        # API 請求指標
        self.api_requests: List[APIRequestMetric] = []
        
        # 快取指標
        self.cache_metrics: List[CacheMetric] = []
        
        # 快速計數器（避免頻繁遍歷）
        self.counters = defaultdict(int)
        
        # 統計資料
        self.stats = {
            'start_time': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_retries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_writes': 0,
        }
        
        logger.info("🎯 指標收集器已初始化")
    
    def record_api_request(
        self,
        url: str,
        method: str,
        status_code: Optional[int],
        duration: float,
        retry_count: int,
        success: bool,
        error_type: Optional[str] = None
    ):
        """
        記錄 API 請求指標
        
        Args:
            url: 請求 URL
            method: HTTP 方法
            status_code: HTTP 狀態碼
            duration: 請求耗時（秒）
            retry_count: 重試次數
            success: 是否成功
            error_type: 錯誤類型（如果失敗）
        """
        with self._lock:
            metric = APIRequestMetric(
                url=url,
                method=method,
                status_code=status_code,
                duration=duration,
                retry_count=retry_count,
                success=success,
                error_type=error_type
            )
            
            self.api_requests.append(metric)
            
            # 更新統計
            self.stats['total_requests'] += 1
            if success:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
            self.stats['total_retries'] += retry_count
            
            # 循環緩衝區：超過限制時移除舊記錄
            if len(self.api_requests) > self.max_records:
                self.api_requests.pop(0)
            
            logger.debug(
                f"📊 記錄 API 請求: {method} {url[:50]}... "
                f"({'成功' if success else '失敗'}, {duration:.2f}s, "
                f"{retry_count} 次重試)"
            )
    
    def record_cache_operation(self, operation: str, cache_key: str):
        """
        記錄快取操作
        
        Args:
            operation: 操作類型 ('hit', 'miss', 'write', 'stale')
            cache_key: 快取鍵值
        """
        with self._lock:
            metric = CacheMetric(
                operation=operation,
                cache_key=cache_key
            )
            
            self.cache_metrics.append(metric)
            
            # 更新統計
            if operation == 'hit':
                self.stats['cache_hits'] += 1
            elif operation == 'miss':
                self.stats['cache_misses'] += 1
            elif operation == 'write':
                self.stats['cache_writes'] += 1
            
            # 循環緩衝區
            if len(self.cache_metrics) > self.max_records:
                self.cache_metrics.pop(0)
            
            logger.debug(f"💾 記錄快取操作: {operation} - {cache_key[:50]}...")
    
    def get_api_statistics(self, last_n_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        取得 API 請求統計資料
        
        Args:
            last_n_minutes: 只統計最近 N 分鐘的資料（None = 全部）
        
        Returns:
            統計資料字典
        """
        with self._lock:
            requests = self.api_requests
            
            # 時間過濾
            if last_n_minutes:
                cutoff = datetime.now() - timedelta(minutes=last_n_minutes)
                requests = [r for r in requests if r.timestamp >= cutoff]
            
            if not requests:
                return {
                    'total_requests': 0,
                    'message': '無資料'
                }
            
            # 計算統計
            total = len(requests)
            successful = sum(1 for r in requests if r.success)
            failed = total - successful
            
            durations = [r.duration for r in requests]
            retries = [r.retry_count for r in requests]
            
            # 按狀態碼分組
            status_codes = defaultdict(int)
            for r in requests:
                if r.status_code:
                    status_codes[r.status_code] += 1
            
            # 錯誤類型分布
            error_types = defaultdict(int)
            for r in requests:
                if not r.success and r.error_type:
                    error_types[r.error_type] += 1
            
            return {
                'total_requests': total,
                'successful_requests': successful,
                'failed_requests': failed,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'total_retries': sum(retries),
                'avg_retries_per_request': statistics.mean(retries) if retries else 0,
                'retry_triggered_rate': (sum(1 for r in retries if r > 0) / total * 100) if total > 0 else 0,
                'response_time': {
                    'min': min(durations),
                    'max': max(durations),
                    'avg': statistics.mean(durations),
                    'median': statistics.median(durations),
                    'p95': statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
                },
                'status_codes': dict(status_codes),
                'error_types': dict(error_types),
                'time_range': {
                    'start': min(r.timestamp for r in requests),
                    'end': max(r.timestamp for r in requests),
                }
            }
    
    def get_cache_statistics(self, last_n_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        取得快取統計資料
        
        Args:
            last_n_minutes: 只統計最近 N 分鐘的資料（None = 全部）
        
        Returns:
            快取統計字典
        """
        with self._lock:
            metrics = self.cache_metrics
            
            # 時間過濾
            if last_n_minutes:
                cutoff = datetime.now() - timedelta(minutes=last_n_minutes)
                metrics = [m for m in metrics if m.timestamp >= cutoff]
            
            if not metrics:
                return {
                    'total_operations': 0,
                    'message': '無資料'
                }
            
            # 計算統計
            hits = sum(1 for m in metrics if m.operation == 'hit')
            misses = sum(1 for m in metrics if m.operation == 'miss')
            writes = sum(1 for m in metrics if m.operation == 'write')
            stale = sum(1 for m in metrics if m.operation == 'stale')
            
            total_reads = hits + misses + stale
            
            return {
                'total_operations': len(metrics),
                'cache_hits': hits,
                'cache_misses': misses,
                'cache_writes': writes,
                'stale_cache': stale,
                'hit_rate': (hits / total_reads * 100) if total_reads > 0 else 0,
                'miss_rate': (misses / total_reads * 100) if total_reads > 0 else 0,
                'effective_hit_rate': ((hits + stale) / total_reads * 100) if total_reads > 0 else 0,
            }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        取得系統整體健康狀態
        
        Returns:
            健康狀態評估
        """
        api_stats = self.get_api_statistics(last_n_minutes=60)  # 最近 1 小時
        cache_stats = self.get_cache_statistics(last_n_minutes=60)
        
        # 健康評分（0-100）
        health_score = 100
        issues = []
        
        # API 成功率檢查
        if api_stats.get('total_requests', 0) > 0:
            success_rate = api_stats['success_rate']
            if success_rate < 95:
                health_score -= 20
                issues.append(f"API 成功率過低: {success_rate:.1f}%")
            elif success_rate < 98:
                health_score -= 10
                issues.append(f"API 成功率偏低: {success_rate:.1f}%")
        
        # 重試率檢查
        retry_rate = api_stats.get('retry_triggered_rate', 0)
        if retry_rate > 10:
            health_score -= 15
            issues.append(f"重試率過高: {retry_rate:.1f}%")
        elif retry_rate > 5:
            health_score -= 5
            issues.append(f"重試率偏高: {retry_rate:.1f}%")
        
        # 快取命中率檢查
        if cache_stats.get('total_operations', 0) > 10:
            hit_rate = cache_stats.get('hit_rate', 0)
            if hit_rate < 50:
                health_score -= 10
                issues.append(f"快取命中率過低: {hit_rate:.1f}%")
        
        # 回應時間檢查
        if api_stats.get('total_requests', 0) > 0:
            avg_time = api_stats['response_time']['avg']
            p95_time = api_stats['response_time']['p95']
            
            if avg_time > 10:
                health_score -= 15
                issues.append(f"平均回應時間過長: {avg_time:.2f}s")
            elif avg_time > 5:
                health_score -= 5
                issues.append(f"平均回應時間偏長: {avg_time:.2f}s")
            
            if p95_time > 30:
                health_score -= 10
                issues.append(f"P95 回應時間過長: {p95_time:.2f}s")
        
        # 健康等級
        if health_score >= 90:
            status = '優秀'
            emoji = '🟢'
        elif health_score >= 75:
            status = '良好'
            emoji = '🟡'
        elif health_score >= 60:
            status = '警告'
            emoji = '🟠'
        else:
            status = '嚴重'
            emoji = '🔴'
        
        return {
            'health_score': max(0, health_score),
            'status': status,
            'emoji': emoji,
            'issues': issues,
            'uptime': str(datetime.now() - self.stats['start_time']).split('.')[0],
            'api_stats': api_stats,
            'cache_stats': cache_stats,
        }
    
    def generate_report(self, output_format: str = 'text') -> str:
        """
        生成統計報告
        
        Args:
            output_format: 輸出格式 ('text', 'markdown', 'json')
        
        Returns:
            格式化的報告字串
        """
        health = self.get_overall_health()
        
        if output_format == 'json':
            import json
            return json.dumps(health, indent=2, default=str, ensure_ascii=False)
        
        elif output_format == 'markdown':
            return self._generate_markdown_report(health)
        
        else:  # text
            return self._generate_text_report(health)
    
    def _generate_text_report(self, health: Dict[str, Any]) -> str:
        """生成純文字報告"""
        api = health['api_stats']
        cache = health['cache_stats']
        
        lines = [
            "=" * 60,
            f"{health['emoji']} 系統健康報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            f"\n【整體健康】",
            f"  狀態: {health['status']}",
            f"  評分: {health['health_score']}/100",
            f"  運行時間: {health['uptime']}",
        ]
        
        if health['issues']:
            lines.append(f"\n  ⚠️  問題清單:")
            for issue in health['issues']:
                lines.append(f"    - {issue}")
        
        if api.get('total_requests', 0) > 0:
            lines.extend([
                f"\n【API 請求統計】",
                f"  總請求數: {api['total_requests']}",
                f"  成功: {api['successful_requests']} ({api['success_rate']:.1f}%)",
                f"  失敗: {api['failed_requests']}",
                f"  總重試次數: {api['total_retries']}",
                f"  平均重試: {api['avg_retries_per_request']:.2f} 次/請求",
                f"  重試觸發率: {api['retry_triggered_rate']:.1f}%",
                f"\n  回應時間:",
                f"    最小: {api['response_time']['min']:.2f}s",
                f"    平均: {api['response_time']['avg']:.2f}s",
                f"    中位數: {api['response_time']['median']:.2f}s",
                f"    P95: {api['response_time']['p95']:.2f}s",
                f"    最大: {api['response_time']['max']:.2f}s",
            ])
            
            if api.get('error_types'):
                lines.append(f"\n  錯誤類型分布:")
                for error, count in sorted(api['error_types'].items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"    - {error}: {count}")
        
        if cache.get('total_operations', 0) > 0:
            lines.extend([
                f"\n【快取統計】",
                f"  總操作數: {cache['total_operations']}",
                f"  命中: {cache['cache_hits']}",
                f"  未命中: {cache['cache_misses']}",
                f"  寫入: {cache['cache_writes']}",
                f"  過期: {cache['stale_cache']}",
                f"  命中率: {cache['hit_rate']:.1f}%",
                f"  有效命中率: {cache['effective_hit_rate']:.1f}% (含過期)",
            ])
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_markdown_report(self, health: Dict[str, Any]) -> str:
        """生成 Markdown 報告"""
        api = health['api_stats']
        cache = health['cache_stats']
        
        lines = [
            f"# {health['emoji']} 系統健康報告",
            f"\n**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**運行時間**: {health['uptime']}  ",
            f"\n## 整體健康狀態",
            f"\n- **狀態**: {health['status']}",
            f"- **評分**: {health['health_score']}/100",
        ]
        
        if health['issues']:
            lines.append(f"\n### ⚠️ 問題清單")
            for issue in health['issues']:
                lines.append(f"- {issue}")
        
        if api.get('total_requests', 0) > 0:
            lines.extend([
                f"\n## API 請求統計",
                f"\n| 指標 | 數值 |",
                f"|------|------|",
                f"| 總請求數 | {api['total_requests']} |",
                f"| 成功率 | {api['success_rate']:.1f}% |",
                f"| 失敗數 | {api['failed_requests']} |",
                f"| 總重試次數 | {api['total_retries']} |",
                f"| 重試觸發率 | {api['retry_triggered_rate']:.1f}% |",
                f"\n### 回應時間",
                f"\n| 統計量 | 時間 (秒) |",
                f"|--------|----------|",
                f"| 最小 | {api['response_time']['min']:.2f} |",
                f"| 平均 | {api['response_time']['avg']:.2f} |",
                f"| 中位數 | {api['response_time']['median']:.2f} |",
                f"| P95 | {api['response_time']['p95']:.2f} |",
                f"| 最大 | {api['response_time']['max']:.2f} |",
            ])
        
        if cache.get('total_operations', 0) > 0:
            lines.extend([
                f"\n## 快取統計",
                f"\n| 指標 | 數值 |",
                f"|------|------|",
                f"| 總操作數 | {cache['total_operations']} |",
                f"| 命中率 | {cache['hit_rate']:.1f}% |",
                f"| 未命中數 | {cache['cache_misses']} |",
                f"| 寫入數 | {cache['cache_writes']} |",
            ])
        
        return "\n".join(lines)
    
    def reset(self):
        """重置所有統計資料"""
        with self._lock:
            self.api_requests.clear()
            self.cache_metrics.clear()
            self.counters.clear()
            self.stats = {
                'start_time': datetime.now(),
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_retries': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'cache_writes': 0,
            }
            logger.info("🔄 指標資料已重置")


# 全域單例
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """取得全域指標收集器（單例模式）"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def print_health_report():
    """便捷函數：直接印出健康報告"""
    collector = get_metrics_collector()
    print(collector.generate_report(output_format='text'))


if __name__ == '__main__':
    # 測試範例
    logging.basicConfig(level=logging.INFO)
    
    collector = get_metrics_collector()
    
    # 模擬一些指標
    collector.record_api_request(
        url='https://api.example.com/data',
        method='GET',
        status_code=200,
        duration=1.23,
        retry_count=0,
        success=True
    )
    
    collector.record_api_request(
        url='https://api.example.com/data2',
        method='GET',
        status_code=None,
        duration=5.67,
        retry_count=2,
        success=False,
        error_type='Timeout'
    )
    
    collector.record_cache_operation('hit', 'stock_2330_data')
    collector.record_cache_operation('miss', 'stock_2454_data')
    
    # 顯示報告
    print("\n" + collector.generate_report(output_format='text'))
