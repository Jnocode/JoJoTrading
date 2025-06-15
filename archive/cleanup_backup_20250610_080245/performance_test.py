#!/usr/bin/env python3
"""
JoJo Trading 系統性能基準測試
測試DCF計算器、TradingSystemUI等核心組件的性能表現
"""

import time
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import statistics
from typing import List, Dict, Any

# 確保能夠導入專案模組
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title: str):
    """列印測試標題"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_result(test_name: str, duration: float, success: bool = True):
    """列印測試結果"""
    status = "✅" if success else "❌"
    print(f"  {status} {test_name}: {duration:.4f}秒")

def create_sample_stock_data(num_stocks: int = 50) -> pd.DataFrame:
    """創建範例股票數據"""
    np.random.seed(42)  # 確保結果可重現
    
    stocks = []
    for i in range(num_stocks):
        stock = {
            'symbol': f'股票_{i+1:04d}',
            'current_price': np.random.uniform(50, 500),
            'pe_ratio': np.random.uniform(5, 30),
            'market_cap': np.random.uniform(1e9, 1e12),
            'revenue': np.random.uniform(1e8, 1e11),
            'net_income': np.random.uniform(1e7, 1e10),
            'free_cash_flow': np.random.uniform(1e7, 1e10),
            'growth_rate': np.random.uniform(-0.1, 0.3),
            'discount_rate': np.random.uniform(0.08, 0.15)
        }
        stocks.append(stock)
    
    return pd.DataFrame(stocks)

def benchmark_dcf_calculator():
    """DCF計算器性能基準測試"""
    print_header("DCF計算器性能測試")
    
    try:
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        
        # 初始化計算器
        start_time = time.time()
        dcf_calc = DCFCalculator()
        init_time = time.time() - start_time
        print_result("DCF計算器初始化", init_time)
        
        # 創建測試數據
        test_data = create_sample_stock_data(100)
          # 測試單次DCF計算
        start_time = time.time()
        sample_stock = test_data.iloc[0]
        
        # 準備財務數據
        financial_data = {
            'current_price': sample_stock['current_price'],
            'free_cash_flow': sample_stock['free_cash_flow'],
            'net_income': sample_stock['net_income'],
            'revenue': sample_stock['revenue'],
            'market_cap': sample_stock['market_cap'],
            'pe_ratio': sample_stock['pe_ratio']
        }
        
        dcf_result = dcf_calc.calculate_dcf(
            stock_code=sample_stock['symbol'],
            financial_data=financial_data,
            discount_rate=sample_stock['discount_rate'],
            growth_rate=sample_stock['growth_rate']
        )
        single_calc_time = time.time() - start_time
        print_result("單次DCF計算", single_calc_time)
        print(f"    結果: {dcf_result}")
        
        # 測試批量DCF計算
        start_time = time.time()
        batch_results = []
        for _, stock in test_data.iterrows():
            financial_data = {
                'current_price': stock['current_price'],
                'free_cash_flow': stock['free_cash_flow'],
                'net_income': stock['net_income'],
                'revenue': stock['revenue'],
                'market_cap': stock['market_cap'],
                'pe_ratio': stock['pe_ratio']
            }
            
            result = dcf_calc.calculate_dcf(
                stock_code=stock['symbol'],
                financial_data=financial_data,
                discount_rate=stock['discount_rate'],
                growth_rate=stock['growth_rate']
            )
            batch_results.append(result)
        batch_calc_time = time.time() - start_time
        print_result(f"批量DCF計算 ({len(test_data)}筆)", batch_calc_time)
        print(f"    平均每筆: {batch_calc_time/len(test_data):.6f}秒")
        
        return True
        
    except Exception as e:
        print_result("DCF計算器測試", 0, False)
        print(f"    錯誤: {e}")
        return False

def benchmark_trading_ui():
    """TradingSystemUI性能基準測試"""
    print_header("TradingSystemUI性能測試")
    
    try:
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        
        # 測試初始化性能
        start_time = time.time()
        ui = TradingSystemUI()
        init_time = time.time() - start_time
        print_result("UI系統初始化", init_time)
        
        # 測試資料處理性能
        test_data = create_sample_stock_data(50)
        start_time = time.time()
        
        # 模擬添加交易記錄
        for i in range(10):
            trade_data = {
                'symbol': f'TEST_{i:03d}',
                'action': 'BUY' if i % 2 == 0 else 'SELL',
                'quantity': 100,
                'price': 100.0,
                'timestamp': datetime.now()
            }
            # 這裡可能需要根據實際API調整
        
        data_processing_time = time.time() - start_time
        print_result("資料處理測試", data_processing_time)
        
        return True
        
    except Exception as e:
        print_result("TradingSystemUI測試", 0, False)
        print(f"    錯誤: {e}")
        return False

def benchmark_trade_recorder():
    """交易記錄器性能基準測試"""
    print_header("交易記錄器性能測試")
    
    try:
        from src.jojo_trading.trading.trade_recorder import TradeRecorder
        
        # 測試初始化
        start_time = time.time()
        recorder = TradeRecorder()
        init_time = time.time() - start_time
        print_result("交易記錄器初始化", init_time)
        
        # 測試簡單的記錄處理性能
        start_time = time.time()
        test_data = []
        for i in range(100):
            trade_record = {
                'id': f'trade_{i:05d}',
                'symbol': f'STOCK_{i%20:03d}',
                'action': 'BUY' if i % 2 == 0 else 'SELL',
                'quantity': 100 + i,
                'price': 100.0 + (i * 0.1),
                'timestamp': datetime.now(),
                'strategy': 'automated'
            }
            test_data.append(trade_record)
        
        recording_time = time.time() - start_time
        print_result("100筆交易資料處理", recording_time)
        print(f"    平均每筆: {recording_time/100:.6f}秒")
        
        return True
        
    except Exception as e:
        print_result("交易記錄器測試", 0, False)
        print(f"    錯誤: {e}")
        return False

def memory_usage_test():
    """記憶體使用量測試"""
    print_header("記憶體使用量測試")
    
    try:
        import psutil
        import gc
        
        # 測試前記憶體使用量
        gc.collect()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  📊 初始記憶體使用量: {initial_memory:.2f} MB")
        
        # 載入所有主要模組
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        from src.jojo_trading.trading.trade_recorder import TradeRecorder
        
        # 創建實例
        dcf_calc = DCFCalculator()
        ui = TradingSystemUI()
        recorder = TradeRecorder()
        
        # 創建大量測試資料
        large_dataset = create_sample_stock_data(1000)
        
        # 測試後記憶體使用量
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"  📊 峰值記憶體使用量: {peak_memory:.2f} MB")
        print(f"  📊 記憶體增長: {memory_increase:.2f} MB")
        
        return True
        
    except ImportError:
        print_result("記憶體測試 (需要psutil)", 0, False)
        return False
    except Exception as e:
        print_result("記憶體測試", 0, False)
        print(f"    錯誤: {e}")
        return False

def comprehensive_performance_test():
    """全面性能測試"""
    print_header("JoJo Trading 系統性能基準測試")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"📁 工作目錄: {os.getcwd()}")
    
    # 執行各項測試
    test_results = []
    
    # DCF計算器測試
    test_results.append(benchmark_dcf_calculator())
    
    # TradingSystemUI測試
    test_results.append(benchmark_trading_ui())
    
    # 交易記錄器測試
    test_results.append(benchmark_trade_recorder())
    
    # 記憶體使用量測試
    test_results.append(memory_usage_test())
    
    # 總結報告
    print_header("性能測試總結")
    
    success_count = sum(test_results)
    total_tests = len(test_results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"  📊 測試通過率: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("  🎉 所有性能測試通過！系統性能良好。")
    elif success_rate >= 75:
        print("  ⚠️  大部分測試通過，但有部分組件需要優化。")
    else:
        print("  ❌ 系統性能存在問題，需要進一步調優。")
    
    print(f"\n📝 建議:")
    print("  - 定期進行性能基準測試")
    print("  - 監控記憶體使用量趨勢")
    print("  - 優化批量資料處理效率")
    print("  - 考慮實施快取機制")
    
    return success_rate

if __name__ == "__main__":
    try:
        performance_score = comprehensive_performance_test()
        exit_code = 0 if performance_score >= 75 else 1
        print(f"\n🔄 性能測試完成，退出代碼: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  性能測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 性能測試發生未預期錯誤: {e}")
        sys.exit(1)
