#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JoJo Trading 系統性能優化
優化監控系統性能並提供系統健康檢查
"""

import time
import sys
import psutil
import threading
from pathlib import Path
from datetime import datetime, timedelta

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

class PerformanceOptimizer:
    """性能優化器"""
    
    def __init__(self):
        self.optimization_results = {}
        
    def check_system_resources(self):
        """檢查系統資源使用情況"""
        print("🔍 檢查系統資源使用情況...")
        
        # CPU檢查
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 記憶體檢查
        memory = psutil.virtual_memory()
        
        # 磁碟檢查
        disk = psutil.disk_usage('.')
        
        # 進程檢查
        python_processes = [p for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']) 
                          if p.info['name'] and 'python' in p.info['name'].lower()]
        
        print(f"💻 CPU: {cpu_percent:.1f}% (核心數: {cpu_count})")
        print(f"🧠 記憶體: {memory.percent:.1f}% (可用: {memory.available // (1024**3):.1f}GB)")
        print(f"💾 磁碟: {disk.percent:.1f}% (可用: {disk.free // (1024**3):.1f}GB)")
        print(f"🐍 Python進程數: {len(python_processes)}")
        
        # 檢查資源警告
        warnings = []
        if cpu_percent > 80:
            warnings.append("CPU使用率過高")
        if memory.percent > 85:
            warnings.append("記憶體使用率過高")
        if disk.percent > 90:
            warnings.append("磁碟空間不足")
        if len(python_processes) > 20:
            warnings.append("Python進程過多")
        
        if warnings:
            print("⚠️ 發現問題:")
            for warning in warnings:
                print(f"   - {warning}")
        else:
            print("✅ 系統資源狀況良好")
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'python_processes': len(python_processes),
            'warnings': warnings
        }
    
    def optimize_monitoring_settings(self):
        """優化監控設定"""
        print("\n🔧 優化監控設定...")
        
        try:
            from src.jojo_trading.core.system_monitor import get_system_monitor
            
            monitor = get_system_monitor()
            
            # 檢查當前監控狀態
            status = monitor.get_system_status()
            print(f"📊 當前監控狀態: {status.get('status', 'unknown')}")
            print(f"🔄 監控是否活躍: {status.get('monitoring_active', False)}")
            
            # 優化建議
            optimizations = []
            
            # 檢查歷史數據大小
            history_size = len(monitor.metrics_history)
            if history_size > 500:
                optimizations.append("建議減少歷史數據保留數量")
                # 清理舊數據
                monitor.metrics_history = monitor.metrics_history[-200:]
                print(f"✂️ 清理歷史數據: {history_size} -> {len(monitor.metrics_history)}")
            
            # 檢查錯誤計數
            total_errors = sum(monitor.error_counts.values())
            if total_errors > 50:
                optimizations.append("建議重置錯誤計數器")
                # 重置錯誤計數
                for key in monitor.error_counts:
                    monitor.error_counts[key] = 0
                print("🔄 已重置錯誤計數器")
            
            # 建議監控間隔
            if not monitor.monitoring_active:
                optimizations.append("建議啟動背景監控（60秒間隔）")
                monitor.start_monitoring(interval=60)
                print("🚀 已啟動優化的背景監控")
            
            print(f"✅ 完成 {len(optimizations)} 項優化")
            return optimizations
            
        except Exception as e:
            print(f"❌ 監控優化失敗: {e}")
            return []
    
    def cleanup_log_files(self):
        """清理日誌文件"""
        print("\n🧹 清理日誌文件...")
        
        log_dir = Path("logs")
        if not log_dir.exists():
            print("📁 日誌目錄不存在")
            return
        
        # 清理30天前的日誌
        cutoff_date = datetime.now() - timedelta(days=30)
        
        cleaned_files = 0
        total_size_freed = 0
        
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                size = log_file.stat().st_size
                try:
                    log_file.unlink()
                    cleaned_files += 1
                    total_size_freed += size
                    print(f"🗑️ 刪除舊日誌: {log_file.name}")
                except Exception as e:
                    print(f"❌ 刪除失敗: {log_file.name} - {e}")
        
        # 清理舊指標文件
        for metrics_file in log_dir.glob("metrics_*.jsonl"):
            if metrics_file.stat().st_mtime < cutoff_date.timestamp():
                size = metrics_file.stat().st_size
                try:
                    metrics_file.unlink()
                    cleaned_files += 1
                    total_size_freed += size
                    print(f"🗑️ 刪除舊指標: {metrics_file.name}")
                except Exception as e:
                    print(f"❌ 刪除失敗: {metrics_file.name} - {e}")
        
        if cleaned_files > 0:
            print(f"✅ 清理完成: {cleaned_files} 個文件, 釋放 {total_size_freed // 1024:.1f}KB")
        else:
            print("✅ 無需清理日誌文件")
        
        return cleaned_files
    
    def verify_system_health(self):
        """驗證系統整體健康狀況"""
        print("\n🏥 系統健康檢查...")
        
        health_score = 100
        issues = []
        
        try:
            # 檢查核心模組
            print("🔍 檢查核心模組...")
            from src.jojo_trading.core.dcf_calculator import DCFCalculator
            from src.jojo_trading.core.data_processor import DataProcessor
            from src.jojo_trading.core.system_monitor import SystemMonitor
            from src.jojo_trading.core.macro_data_handler import MacroDataHandler
            print("✅ 所有核心模組正常")
            
            # 檢查監控系統
            print("🔍 檢查監控系統...")
            monitor = SystemMonitor()
            status = monitor.get_system_status()
            
            if status.get('status') == 'error':
                health_score -= 20
                issues.append("監控系統狀態異常")
            
            total_errors = status.get('total_errors', 0)
            if total_errors > 20:
                health_score -= 10
                issues.append(f"系統錯誤過多: {total_errors}")
            
            print("✅ 監控系統正常")
            
            # 檢查資源使用
            print("🔍 檢查資源使用...")
            resources = self.check_system_resources()
            
            if resources['cpu_percent'] > 80:
                health_score -= 15
                issues.append("CPU使用率過高")
            
            if resources['memory_percent'] > 85:
                health_score -= 15
                issues.append("記憶體使用率過高")
            
            if len(resources['warnings']) > 0:
                health_score -= 10 * len(resources['warnings'])
                issues.extend(resources['warnings'])
            
            print("✅ 資源檢查完成")
            
        except Exception as e:
            health_score -= 30
            issues.append(f"系統檢查異常: {e}")
        
        # 健康評級
        if health_score >= 90:
            grade = "🟢 優秀"
        elif health_score >= 75:
            grade = "🟡 良好"
        elif health_score >= 50:
            grade = "🟠 一般"
        else:
            grade = "🔴 需要關注"
        
        print(f"\n💯 系統健康分數: {health_score}/100 ({grade})")
        
        if issues:
            print("⚠️ 發現問題:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("🎉 系統運行完美！")
        
        return health_score, issues

def main():
    """主優化函數"""
    print("=" * 60)
    print("⚡ JoJo Trading 系統性能優化")
    print("=" * 60)
    print(f"📅 優化時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    optimizer = PerformanceOptimizer()
    
    # 1. 系統資源檢查
    resources = optimizer.check_system_resources()
    
    # 2. 監控優化
    optimizations = optimizer.optimize_monitoring_settings()
    
    # 3. 日誌清理
    cleaned_files = optimizer.cleanup_log_files()
    
    # 4. 系統健康檢查
    health_score, issues = optimizer.verify_system_health()
    
    # 5. 優化報告
    print("\n" + "=" * 60)
    print("📊 優化報告總結")
    print("=" * 60)
    
    print(f"🏥 系統健康分數: {health_score}/100")
    print(f"⚡ 執行優化數量: {len(optimizations)}")
    print(f"🧹 清理文件數量: {cleaned_files}")
    print(f"💻 CPU使用率: {resources['cpu_percent']:.1f}%")
    print(f"🧠 記憶體使用率: {resources['memory_percent']:.1f}%")
    
    if health_score >= 80:
        print("\n🎉 系統優化完成！運行狀況良好。")
        recommendation = "系統運行正常，建議定期進行健康檢查。"
    elif health_score >= 60:
        print("\n✅ 系統優化完成，但需要持續關注。")
        recommendation = "建議監控系統資源使用情況，考慮升級硬體配置。"
    else:
        print("\n⚠️ 系統需要進一步優化。")
        recommendation = "建議立即檢查系統配置，重啟相關服務，必要時聯絡技術支援。"
    
    print(f"💡 建議: {recommendation}")
    
    return health_score >= 70

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 優化{'成功' if success else '需要進一步處理'}")
