#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JoJo Trading 系統監控模組 (修復版)
提供性能監控、錯誤追蹤和系統狀態管理功能
"""

import logging
import time
import psutil
import threading
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class SystemMetrics:
    """系統性能指標"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    response_time: float
    active_sessions: int
    error_count: int

class SystemMonitor:
    """系統監控器"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        初始化系統監控器
        
        Args:
            log_dir: 日誌目錄，預設為專案根目錄下的logs
        """
        if log_dir is None:
            self.log_dir = Path(__file__).parent.parent.parent.parent / "logs"
        else:
            self.log_dir = log_dir
            
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 設定日誌記錄器
        self._setup_logging()
        
        # 系統指標儲存
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        
        # 錯誤計數器
        self.error_counts = {
            'dcf_errors': 0,
            'trading_errors': 0,
            'data_errors': 0,
            'system_errors': 0
        }
        
        # 監控開關
        self.monitoring_active = False
        self.monitor_thread = None
        
        self.logger.info("系統監控器初始化完成")
    
    def _setup_logging(self):
        """設定日誌系統"""
        # 創建主日誌記錄器
        self.logger = logging.getLogger('jojo_trading_monitor')
        self.logger.setLevel(logging.INFO)
        
        # 清除現有處理器
        self.logger.handlers.clear()
        
        # 文件處理器
        log_file = self.log_dir / f"jojo_trading_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 錯誤日誌處理器
        error_log_file = self.log_dir / f"jojo_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        # 添加處理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        
        # 防止重複日誌
        self.logger.propagate = False
    
    def start_monitoring(self, interval: int = 30):
        """
        開始系統監控
        
        Args:
            interval: 監控間隔（秒）
        """
        if self.monitoring_active:
            self.logger.warning("系統監控已在運行中")
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"系統監控已啟動，間隔：{interval}秒")
    
    def stop_monitoring(self):
        """停止系統監控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("系統監控已停止")
    
    def _monitoring_loop(self, interval: int):
        """監控主循環"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {e}")
                time.sleep(interval)
    
    def _collect_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        start_time = time.time()
        
        # 系統資源使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 回應時間（模擬）
        response_time = time.time() - start_time
        
        # 活躍會話數（簡化版）
        active_sessions = 1  # 簡化為固定值
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage=disk.percent,
            response_time=response_time,
            active_sessions=active_sessions,
            error_count=sum(self.error_counts.values())
        )
    
    def _store_metrics(self, metrics: SystemMetrics):
        """儲存系統指標"""
        self.metrics_history.append(metrics)
        
        # 保持歷史記錄大小限制
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
        
        # 儲存到文件
        metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(metrics), ensure_ascii=False) + '\n')
    
    def log_dcf_calculation(self, symbol: str, success: bool, duration: float, result: Any = None, error: Optional[str] = None):
        """記錄DCF計算事件"""
        if success:
            self.logger.info(f"DCF計算成功 - 股票: {symbol}, 耗時: {duration:.2f}秒")
        else:
            self.error_counts['dcf_errors'] += 1
            self.logger.error(f"DCF計算失敗 - 股票: {symbol}, 錯誤: {error}")
    
    def log_trade_action(self, action: str, symbol: str, success: bool, details: Optional[Dict] = None, error: Optional[str] = None):
        """記錄交易動作"""
        if success:
            self.logger.info(f"交易動作成功 - 動作: {action}, 股票: {symbol}, 詳情: {details}")
        else:
            self.error_counts['trading_errors'] += 1
            self.logger.error(f"交易動作失敗 - 動作: {action}, 股票: {symbol}, 錯誤: {error}")
    
    def log_data_operation(self, operation: str, success: bool, details: Optional[str] = None, error: Optional[str] = None):
        """記錄資料操作"""
        if success:
            self.logger.info(f"資料操作成功 - 操作: {operation}, 詳情: {details}")
        else:
            self.error_counts['data_errors'] += 1
            self.logger.error(f"資料操作失敗 - 操作: {operation}, 錯誤: {error}")
    
    def log_system_event(self, event: str, level: str = "INFO", details: Optional[str] = None):
        """記錄系統事件"""
        message = f"系統事件 - {event}"
        if details:
            message += f", 詳情: {details}"
            
        if level.upper() == "ERROR":
            self.error_counts['system_errors'] += 1
            self.logger.error(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態摘要"""
        if not self.metrics_history:
            return {
                'status': 'unknown',
                'message': '暫無監控數據'
            }
        
        latest_metrics = self.metrics_history[-1]
        
        # 判斷系統狀態
        status = 'healthy'
        warnings = []
        
        if latest_metrics.cpu_percent > 80:
            status = 'warning'
            warnings.append('CPU使用率過高')
        
        if latest_metrics.memory_percent > 85:
            status = 'warning'
            warnings.append('記憶體使用率過高')
        
        if latest_metrics.response_time > 5.0:
            status = 'warning'
            warnings.append('回應時間過長')
        
        if sum(self.error_counts.values()) > 10:
            status = 'error'
            warnings.append('錯誤數量過多')
        
        return {
            'status': status,
            'timestamp': latest_metrics.timestamp,
            'cpu_percent': latest_metrics.cpu_percent,
            'memory_percent': latest_metrics.memory_percent,
            'disk_usage': latest_metrics.disk_usage,
            'response_time': latest_metrics.response_time,
            'error_counts': self.error_counts.copy(),
            'total_errors': sum(self.error_counts.values()),
            'warnings': warnings,
            'monitoring_active': self.monitoring_active
        }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """獲取性能摘要報告"""
        if not self.metrics_history:
            return {'message': '暫無性能數據'}
        
        # 篩選指定時間範圍內的數據
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        if not recent_metrics:
            return {'message': f'過去{hours}小時內暫無數據'}
        
        # 計算統計數據
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        response_times = [m.response_time for m in recent_metrics]
        
        return {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu_usage': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_usage': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'response_time': {
                'avg': sum(response_times) / len(response_times),
                'max': max(response_times),
                'min': min(response_times)
            },
            'error_summary': self.error_counts.copy()
        }
    
    def cleanup_old_logs(self, days: int = 30):
        """清理舊日誌文件"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    log_file.unlink()
                    self.logger.info(f"已刪除舊日誌文件: {log_file.name}")
                except Exception as e:
                    self.logger.error(f"刪除舊日誌文件失敗: {log_file.name}, 錯誤: {e}")
        
        for metrics_file in self.log_dir.glob("metrics_*.jsonl"):
            if metrics_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    metrics_file.unlink()
                    self.logger.info(f"已刪除舊指標文件: {metrics_file.name}")
                except Exception as e:
                    self.logger.error(f"刪除舊指標文件失敗: {metrics_file.name}, 錯誤: {e}")

# 全域監控器實例
_monitor_instance = None

def get_system_monitor() -> SystemMonitor:
    """獲取全域系統監控器實例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor()
    return _monitor_instance

def init_monitoring(auto_start: bool = True):
    """初始化系統監控"""
    monitor = get_system_monitor()
    if auto_start:
        monitor.start_monitoring()
    return monitor
