"""
LRU (Least Recently Used) 記憶體快取層

提供記憶體快取功能，減少磁碟 I/O 操作，提升效能。

特性：
- 執行緒安全
- 自動過期機制
- LRU 驅逐策略
- 記憶體使用限制
- 統計追蹤整合

Author: jojo_trading team
Date: 2025-11-19
Version: 1.0.0
"""

import time
import logging
from typing import Any, Optional, Dict, Tuple
from threading import Lock
from collections import OrderedDict
from dataclasses import dataclass
import sys

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """快取項目"""
    value: Any
    timestamp: float
    access_count: int = 0
    size_bytes: int = 0


class LRUMemoryCache:
    """
    LRU 記憶體快取
    
    使用 OrderedDict 實作 LRU 策略，當快取滿時自動移除最少使用的項目。
    
    特性：
    - 自動過期（TTL）
    - 最大項目數限制
    - 最大記憶體限制
    - 執行緒安全
    - 統計資訊
    """
    
    def __init__(
        self,
        max_items: int = 1000,
        max_memory_mb: int = 100,
        default_ttl: int = 3600
    ):
        """
        初始化 LRU 快取
        
        Args:
            max_items: 最大快取項目數
            max_memory_mb: 最大記憶體使用（MB）
            default_ttl: 預設過期時間（秒）
        """
        self._lock = Lock()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        self.max_items = max_items
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        
        # 統計資料
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0,
            'total_size_bytes': 0,
        }
        
        logger.info(
            f"🎯 LRU 快取已初始化 "
            f"(max_items={max_items}, max_memory={max_memory_mb}MB, ttl={default_ttl}s)"
        )
    
    def get(self, key: str) -> Optional[Any]:
        """
        取得快取值
        
        Args:
            key: 快取鍵值
        
        Returns:
            快取值，如果不存在或已過期則返回 None
        """
        with self._lock:
            if key not in self._cache:
                self.stats['misses'] += 1
                logger.debug(f"💾 CACHE MISS: {key}")
                return None
            
            entry = self._cache[key]
            
            # 檢查是否過期
            if time.time() - entry.timestamp > self.default_ttl:
                logger.debug(f"💾 CACHE EXPIRED: {key}")
                self.stats['expired'] += 1
                self._remove(key)
                return None
            
            # 更新訪問記錄（LRU）
            entry.access_count += 1
            self._cache.move_to_end(key)  # 移到最後（最近使用）
            
            self.stats['hits'] += 1
            logger.debug(f"💾 CACHE HIT: {key} (access_count={entry.access_count})")
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        設定快取值
        
        Args:
            key: 快取鍵值
            value: 快取值
            ttl: 過期時間（秒），None 使用預設值
        
        Returns:
            是否成功設定
        """
        with self._lock:
            # 計算值的大小（粗略估算）
            try:
                size_bytes = sys.getsizeof(value)
            except TypeError:
                size_bytes = 1024  # 預設 1KB
            
            # 檢查是否需要驅逐舊項目
            max_evict_attempts = self.max_items  # 避免無限循環
            evict_count = 0
            
            while (len(self._cache) >= self.max_items or \
                   self.stats['total_size_bytes'] + size_bytes > self.max_memory_bytes) and \
                   evict_count < max_evict_attempts:
                if not self._evict_lru():
                    logger.warning(f"⚠️  無法驅逐項目，快取已滿")
                    return False
                evict_count += 1
            
            # 更新或新增項目
            if key in self._cache:
                old_entry = self._cache[key]
                self.stats['total_size_bytes'] -= old_entry.size_bytes
            
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                access_count=0,
                size_bytes=size_bytes
            )
            
            self._cache[key] = entry
            self._cache.move_to_end(key)  # 移到最後
            self.stats['total_size_bytes'] += size_bytes
            
            logger.debug(
                f"💾 CACHE SET: {key} "
                f"(size={size_bytes}B, total_items={len(self._cache)})"
            )
            
            return True
    
    def delete(self, key: str) -> bool:
        """
        刪除快取項目
        
        Args:
            key: 快取鍵值
        
        Returns:
            是否成功刪除
        """
        with self._lock:
            if key in self._cache:
                self._remove(key)
                logger.debug(f"💾 CACHE DELETE: {key}")
                return True
            return False
    
    def clear(self):
        """清空所有快取"""
        with self._lock:
            self._cache.clear()
            self.stats['total_size_bytes'] = 0
            logger.info("💾 快取已清空")
    
    def _remove(self, key: str):
        """內部方法：移除項目（不加鎖）"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self.stats['total_size_bytes'] -= entry.size_bytes
    
    def _evict_lru(self) -> bool:
        """內部方法：驅逐最少使用的項目"""
        if not self._cache:
            return False
        
        # OrderedDict 的第一個項目是最久未使用的
        key = next(iter(self._cache))
        self._remove(key)
        self.stats['evictions'] += 1
        logger.debug(f"💾 CACHE EVICT (LRU): {key}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """取得快取統計資料"""
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_items': len(self._cache),
                'max_items': self.max_items,
                'total_size_bytes': self.stats['total_size_bytes'],
                'total_size_mb': self.stats['total_size_bytes'] / 1024 / 1024,
                'max_size_mb': self.max_memory_bytes / 1024 / 1024,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self.stats['evictions'],
                'expired': self.stats['expired'],
                'utilization': (len(self._cache) / self.max_items * 100) if self.max_items > 0 else 0,
            }
    
    def cleanup_expired(self) -> int:
        """清理過期的快取項目"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time - entry.timestamp > self.default_ttl
            ]
            
            for key in expired_keys:
                self._remove(key)
                self.stats['expired'] += 1
            
            if expired_keys:
                logger.info(f"💾 清理了 {len(expired_keys)} 個過期項目")
            
            return len(expired_keys)
    
    def get_top_accessed(self, n: int = 10) -> list[Tuple[str, int]]:
        """取得最常訪問的項目"""
        with self._lock:
            items = [(k, v.access_count) for k, v in self._cache.items()]
            items.sort(key=lambda x: x[1], reverse=True)
            return items[:n]


# 全域快取實例
_global_memory_cache: Optional[LRUMemoryCache] = None


def get_memory_cache(
    max_items: int = 1000,
    max_memory_mb: int = 100,
    default_ttl: int = 3600
) -> LRUMemoryCache:
    """
    取得全域記憶體快取實例（單例模式）
    
    Args:
        max_items: 最大快取項目數
        max_memory_mb: 最大記憶體使用（MB）
        default_ttl: 預設過期時間（秒）
    
    Returns:
        LRU 記憶體快取實例
    """
    global _global_memory_cache
    if _global_memory_cache is None:
        _global_memory_cache = LRUMemoryCache(
            max_items=max_items,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl
        )
    return _global_memory_cache


if __name__ == '__main__':
    # 測試範例
    logging.basicConfig(level=logging.DEBUG)
    
    cache = get_memory_cache(max_items=5, max_memory_mb=1, default_ttl=10)
    
    # 測試設定和取得
    print("\n測試基本操作:")
    cache.set('key1', 'value1')
    cache.set('key2', {'data': [1, 2, 3]})
    cache.set('key3', 'value3')
    
    print(f"key1: {cache.get('key1')}")
    print(f"key2: {cache.get('key2')}")
    print(f"key_not_exist: {cache.get('key_not_exist')}")
    
    # 測試 LRU 驅逐
    print("\n測試 LRU 驅逐:")
    for i in range(10):
        cache.set(f'key_{i}', f'value_{i}')
    
    # 測試統計
    print("\n快取統計:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 測試最常訪問
    print("\n最常訪問的項目:")
    for key, count in cache.get_top_accessed(5):
        print(f"  {key}: {count} 次")
