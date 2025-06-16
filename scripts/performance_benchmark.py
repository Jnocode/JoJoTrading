#!/usr/bin/env python3
"""
JoJo Trading System - 性能基準測試腳本
建立 Phase 4 優化前的性能基線

Created: 2025-06-16
Author: JoJo Trading Development Team
"""

import time
import psutil
import sys
from pathlib import Path
import pandas as pd
import json
import datetime
from typing import Dict, Any

# 添加 src 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def measure_performance(func, *args, **kwargs):
    """測量函數性能指標"""
    # 記憶體使用測量
    process = psutil.Process()
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # 時間測量
    start_time = time.time()
    
    # 執行函數
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    # 結束測量
    end_time = time.time()
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    
    return {
        'execution_time': end_time - start_time,
        'memory_before_mb': memory_before,
        'memory_after_mb': memory_after,
        'memory_used_mb': memory_after - memory_before,
        'success': success,
        'error': error,
        'result': result
    }

def test_dcf_calculation_performance():
    """測試 DCF 計算性能"""
    print("📊 測試 DCF 計算性能...")
    
    try:
        from jojo_trading.core.enhanced_dcf import EnhancedDCFModel
        
        # 準備測試數據
        sample_data = {
            'revenue': [1000000, 1100000, 1200000],
            'operating_income': [200000, 220000, 240000],
            'net_income': [150000, 165000, 180000],
            'free_cash_flow': [130000, 140000, 150000]
        }
        
        dcf_model = EnhancedDCFModel()
        
        # 測試單次計算
        single_calc = measure_performance(
            dcf_model.calculate_dcf_value, 
            sample_data, 
            discount_rate=0.10, 
            terminal_growth_rate=0.03
        )
        
        # 測試批量計算 (10次)
        batch_start = time.time()
        batch_results = []
        for i in range(10):
            result = measure_performance(
                dcf_model.calculate_dcf_value,
                sample_data,
                discount_rate=0.10 + i*0.01,
                terminal_growth_rate=0.03
            )
            batch_results.append(result)
        batch_time = time.time() - batch_start
        
        return {
            'single_calculation': single_calc,
            'batch_calculation': {
                'total_time': batch_time,
                'average_time': batch_time / 10,
                'results': batch_results
            }
        }
        
    except ImportError as e:
        return {'error': f'無法導入 DCF 模組: {e}'}

def test_data_loading_performance():
    """測試數據載入性能"""
    print("📈 測試數據載入性能...")
    try:
        # 使用現有的數據處理模組
        from jojo_trading.core.data_handler import DataHandler
        
        handler = DataHandler()
        
        # 測試基本數據載入
        basic_load = measure_performance(
            handler.get_basic_info, 
            "2330"  # 台積電
        )
        
        return {
            'basic_data_load': basic_load
        }
        
    except ImportError:
        # 如果無法導入，使用模擬測試
        def simulate_data_load(stock_code):
            time.sleep(0.1)  # 模擬數據載入時間
            return {'stock_code': stock_code, 'data': 'simulated'}
        
        basic_load = measure_performance(simulate_data_load, "2330")
        return {
            'basic_data_load': basic_load,
            'note': '使用模擬數據測試'
        }
    except Exception as e:
        return {'error': f'數據載入錯誤: {e}'}

def test_system_import_performance():
    """測試系統模組導入性能"""
    print("🔧 測試系統模組導入性能...")
    
    import_tests = {}
      # 測試關鍵模組導入時間
    modules_to_test = [
        'jojo_trading.core.enhanced_dcf',
        'jojo_trading.core.data_handler',
        'jojo_trading.utils.data_validator',
        'jojo_trading.config.default_config',
    ]
    
    for module in modules_to_test:
        def import_module():
            import importlib
            return importlib.import_module(module)
        
        result = measure_performance(import_module)
        import_tests[module] = result
    
    return import_tests

def test_streamlit_startup_performance():
    """測試 Streamlit 啟動性能"""
    print("🌐 測試 Streamlit 啟動性能...")
    
    try:
        import streamlit as st
        
        # 測試基本 Streamlit 組件載入
        def create_basic_components():
            # 模擬基本組件創建（不實際渲染）
            return {
                'title': 'JoJo Trading System',
                'sidebar': True,
                'dataframe': pd.DataFrame({'test': [1, 2, 3]}),
                'chart': True
            }
        
        st_performance = measure_performance(create_basic_components)
        return {'streamlit_components': st_performance}
        
    except ImportError:
        return {'error': '無法導入 Streamlit'}

def generate_performance_report(results: Dict[str, Any]):
    """生成性能報告"""
    print("\n" + "="*60)
    print("🚀 JoJo Trading 系統性能基準報告")
    print("="*60)
    print(f"測試時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 版本: {sys.version}")
    print(f"系統記憶體: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
    print(f"CPU 核心數: {psutil.cpu_count()}")
    print()
    
    # DCF 計算性能
    if 'dcf_performance' in results:
        dcf_data = results['dcf_performance']
        if 'error' not in dcf_data:
            print("📊 DCF 計算性能:")
            single = dcf_data['single_calculation']
            print(f"  單次計算時間: {single['execution_time']:.4f} 秒")
            print(f"  記憶體使用: {single['memory_used_mb']:.2f} MB")
            
            batch = dcf_data['batch_calculation']
            print(f"  批量計算 (10次): {batch['total_time']:.4f} 秒")
            print(f"  平均每次: {batch['average_time']:.4f} 秒")
            print()
    
    # 數據載入性能
    if 'data_performance' in results:
        data_perf = results['data_performance']
        if 'error' not in data_perf:
            print("📈 數據載入性能:")
            basic = data_perf['basic_data_load']
            print(f"  基本數據載入: {basic['execution_time']:.4f} 秒")
            print(f"  成功狀態: {'✅' if basic['success'] else '❌'}")
            print()
    
    # 模組導入性能
    if 'import_performance' in results:
        print("🔧 模組導入性能:")
        for module, perf in results['import_performance'].items():
            status = "✅" if perf['success'] else "❌"
            print(f"  {module}: {perf['execution_time']:.4f} 秒 {status}")
        print()
    
    # Streamlit 性能
    if 'streamlit_performance' in results:
        st_data = results['streamlit_performance']
        if 'error' not in st_data:
            print("🌐 Streamlit 性能:")
            comp = st_data['streamlit_components']
            print(f"  組件創建時間: {comp['execution_time']:.4f} 秒")
            print()
    
    # 性能評級
    print("📋 性能評級建議:")
    
    # DCF 計算速度評級
    if 'dcf_performance' in results and 'error' not in results['dcf_performance']:
        dcf_time = results['dcf_performance']['single_calculation']['execution_time']
        if dcf_time < 0.01:
            print("  DCF 計算速度: 🟢 優秀 (<0.01s)")
        elif dcf_time < 0.1:
            print("  DCF 計算速度: 🟡 良好 (<0.1s)")
        else:
            print("  DCF 計算速度: 🔴 需要優化 (>0.1s)")
    
    print("\n" + "="*60)
    print("📊 基準測試完成！")
    print("📋 Phase 4 優化目標:")
    print("  - DCF 計算速度: 目標 <0.01秒")
    print("  - 數據載入速度: 目標 <2秒")
    print("  - 記憶體使用: 目標 <512MB")
    print("  - 模組導入: 目標 <0.1秒")
    print("="*60)

def main():
    """主要測試函數"""
    print("🚀 開始 JoJo Trading 性能基準測試...")
    print("這將建立 Phase 4 優化前的性能基線\n")
    
    results = {}
    
    # 1. 測試 DCF 計算性能
    results['dcf_performance'] = test_dcf_calculation_performance()
    
    # 2. 測試數據載入性能
    results['data_performance'] = test_data_loading_performance()
    
    # 3. 測試模組導入性能
    results['import_performance'] = test_system_import_performance()
    
    # 4. 測試 Streamlit 性能
    results['streamlit_performance'] = test_streamlit_startup_performance()
    
    # 5. 生成報告
    generate_performance_report(results)
    
    # 6. 保存結果到檔案
    results_file = f"performance_baseline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 詳細結果已保存至: {results_file}")
    
    return results

if __name__ == "__main__":
    main()
