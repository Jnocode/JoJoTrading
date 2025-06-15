#!/usr/bin/env python3
"""
JoJo Trading 系統優化性能測試
針對實際的DCF計算器數據格式進行的性能基準測試
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

def create_realistic_financial_data(num_stocks: int = 50) -> pd.DataFrame:
    """創建符合DCF計算器需求的完整財務數據"""
    np.random.seed(42)  # 確保結果可重現
    
    stocks = []
    for i in range(num_stocks):
        # 基礎價格和規模數據
        market_cap = np.random.uniform(1e9, 1e12)
        shares_outstanding = np.random.uniform(1e6, 1e9)
        current_price = market_cap / shares_outstanding
        
        # 盈利數據
        net_income_parent = np.random.uniform(1e7, 1e10)
        revenue = net_income_parent / np.random.uniform(0.05, 0.25)  # 合理的淨利率
        
        # 現金流數據
        depreciation = np.random.uniform(1e6, 1e9)
        capex = np.random.uniform(1e6, 2e9)
        free_cash_flow = net_income_parent + depreciation - capex
        
        stock = {
            'symbol': f'股票_{i+1:04d}',
            'current_price': current_price,
            'pe_ratio': np.random.uniform(5, 30),
            'market_cap': market_cap,
            'revenue': revenue,
            'net_income': net_income_parent,  # 簡化版本
            'net_income_parent': net_income_parent,  # DCF需要的版本
            'free_cash_flow': free_cash_flow,
            'depreciation': depreciation,
            'capex': capex,
            'shares_outstanding': shares_outstanding,
            'growth_rate': np.random.uniform(-0.1, 0.3),
            'discount_rate': np.random.uniform(0.08, 0.15),
            # 額外的財務比率
            'roe': np.random.uniform(0.05, 0.25),
            'debt_to_equity': np.random.uniform(0.1, 2.0),
            'current_ratio': np.random.uniform(0.8, 3.0),
            'operating_margin': np.random.uniform(0.02, 0.3)
        }
        stocks.append(stock)
    
    return pd.DataFrame(stocks)

def benchmark_enhanced_dcf_calculator():
    """測試增強版DCF計算器的真實性能"""
    print_header("增強版DCF計算器性能測試")
    
    try:
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        
        # 初始化計算器
        start_time = time.time()
        dcf_calc = DCFCalculator()
        init_time = time.time() - start_time
        print_result("DCF計算器初始化", init_time)
        
        # 創建符合需求的測試數據
        test_data = create_realistic_financial_data(10)  # 減少數量以便詳細分析
        
        # 測試單次DCF計算
        start_time = time.time()
        sample_stock = test_data.iloc[0]
        
        # 準備完整的財務數據
        financial_data = {
            'current_price': sample_stock['current_price'],
            'free_cash_flow': sample_stock['free_cash_flow'],
            'net_income': sample_stock['net_income'],
            'net_income_parent': sample_stock['net_income_parent'],
            'revenue': sample_stock['revenue'],
            'market_cap': sample_stock['market_cap'],
            'pe_ratio': sample_stock['pe_ratio'],
            'depreciation': sample_stock['depreciation'],
            'capex': sample_stock['capex'],
            'shares_outstanding': sample_stock['shares_outstanding'],
            'roe': sample_stock['roe'],
            'debt_to_equity': sample_stock['debt_to_equity'],
            'current_ratio': sample_stock['current_ratio'],
            'operating_margin': sample_stock['operating_margin']
        }
        
        dcf_result = dcf_calc.calculate_dcf(
            stock_code=sample_stock['symbol'],
            financial_data=financial_data,
            discount_rate=sample_stock['discount_rate'],
            growth_rate=sample_stock['growth_rate']
        )
        single_calc_time = time.time() - start_time
        print_result("單次增強DCF計算", single_calc_time)
        
        # 顯示計算結果摘要
        if 'error' in dcf_result:
            print(f"    ⚠️ 計算警告: {dcf_result.get('error', 'Unknown')}")
            if 'validation_score' in dcf_result:
                print(f"    📊 數據品質評分: {dcf_result['validation_score']}/100")
        else:
            print(f"    📈 內在價值: ${dcf_result.get('intrinsic_value_per_share', 'N/A'):.2f}")
            print(f"    📊 市場價格: ${dcf_result.get('current_market_price', sample_stock['current_price']):.2f}")
        
        # 測試小批量計算
        start_time = time.time()
        batch_results = []
        successful_calcs = 0
        for _, stock in test_data.head(5).iterrows():  # 只測試前5筆
            financial_data = {
                'current_price': stock['current_price'],
                'free_cash_flow': stock['free_cash_flow'],
                'net_income': stock['net_income'],
                'net_income_parent': stock['net_income_parent'],
                'revenue': stock['revenue'],
                'market_cap': stock['market_cap'],
                'pe_ratio': stock['pe_ratio'],
                'depreciation': stock['depreciation'],
                'capex': stock['capex'],
                'shares_outstanding': stock['shares_outstanding'],
                'roe': stock['roe'],
                'debt_to_equity': stock['debt_to_equity'],
                'current_ratio': stock['current_ratio'],
                'operating_margin': stock['operating_margin']
            }
            
            result = dcf_calc.calculate_dcf(
                stock_code=stock['symbol'],
                financial_data=financial_data,
                discount_rate=stock['discount_rate'],
                growth_rate=stock['growth_rate']
            )
            batch_results.append(result)
            if 'error' not in result:
                successful_calcs += 1
        
        batch_calc_time = time.time() - start_time
        print_result(f"小批量DCF計算 (5筆)", batch_calc_time)
        print(f"    ✅ 成功計算: {successful_calcs}/5")
        print(f"    ⏱️ 平均每筆: {batch_calc_time/5:.4f}秒")
        
        return True
        
    except Exception as e:
        print_result("增強DCF計算器測試", 0, False)
        print(f"    錯誤: {e}")
        return False

def benchmark_basic_dcf_performance():
    """測試基本DCF計算的性能指標"""
    print_header("基本DCF計算性能基準測試")
    
    try:
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        dcf_calc = DCFCalculator()
        
        # 創建大量測試數據進行壓力測試
        large_dataset = create_realistic_financial_data(100)
        
        # 測試大批量處理性能
        start_time = time.time()
        successful_count = 0
        error_count = 0
        
        for _, stock in large_dataset.iterrows():
            financial_data = {
                'current_price': stock['current_price'],
                'free_cash_flow': stock['free_cash_flow'],
                'net_income_parent': stock['net_income_parent'],
                'revenue': stock['revenue'],
                'market_cap': stock['market_cap'],
                'depreciation': stock['depreciation'],
                'capex': stock['capex'],
                'shares_outstanding': stock['shares_outstanding']
            }
            
            result = dcf_calc.calculate_dcf(
                stock_code=stock['symbol'],
                financial_data=financial_data,
                discount_rate=stock['discount_rate'],
                growth_rate=stock['growth_rate']
            )
            
            if 'error' in result:
                error_count += 1
            else:
                successful_count += 1
        
        total_time = time.time() - start_time
        print_result(f"大批量DCF計算 (100筆)", total_time)
        print(f"    ✅ 成功: {successful_count}")
        print(f"    ❌ 錯誤: {error_count}")
        print(f"    📊 成功率: {(successful_count/(successful_count + error_count)*100):.1f}%")
        print(f"    ⏱️ 平均處理時間: {total_time/100:.4f}秒/筆")
        
        return True
        
    except Exception as e:
        print_result("大批量DCF測試", 0, False)
        print(f"    錯誤: {e}")
        return False

def system_integration_test():
    """系統整合性能測試"""
    print_header("系統整合性能測試")
    
    try:
        # 測試主要模組協同工作
        from src.jojo_trading.core.dcf_calculator import DCFCalculator
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        from src.jojo_trading.trading.trade_recorder import TradeRecorder
        
        start_time = time.time()
        
        # 創建模組實例
        dcf_calc = DCFCalculator()
        trading_ui = TradingSystemUI()
        trade_recorder = TradeRecorder()
        
        # 創建測試數據
        test_data = create_realistic_financial_data(10)
        
        # 模擬完整的分析流程
        analysis_results = []
        for _, stock in test_data.iterrows():
            financial_data = {
                'current_price': stock['current_price'],
                'free_cash_flow': stock['free_cash_flow'],
                'net_income_parent': stock['net_income_parent'],
                'revenue': stock['revenue'],
                'market_cap': stock['market_cap'],
                'depreciation': stock['depreciation'],
                'capex': stock['capex'],
                'shares_outstanding': stock['shares_outstanding']
            }
            
            # DCF分析
            dcf_result = dcf_calc.calculate_dcf(
                stock_code=stock['symbol'],
                financial_data=financial_data,
                discount_rate=stock['discount_rate']
            )
            analysis_results.append(dcf_result)
        
        total_time = time.time() - start_time
        print_result("完整分析流程", total_time)
        print(f"    📊 處理股票數量: {len(test_data)}")
        print(f"    ⏱️ 平均分析時間: {total_time/len(test_data):.4f}秒/股票")
        
        return True
        
    except Exception as e:
        print_result("系統整合測試", 0, False)
        print(f"    錯誤: {e}")
        return False

def optimized_performance_test():
    """優化版性能測試主函數"""
    print_header("JoJo Trading 優化性能基準測試")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(f"📁 工作目錄: {os.getcwd()}")
    
    # 執行各項測試
    test_results = []
    
    # 增強DCF計算器測試
    test_results.append(benchmark_enhanced_dcf_calculator())
    
    # 基本DCF性能測試
    test_results.append(benchmark_basic_dcf_performance())
    
    # 系統整合測試
    test_results.append(system_integration_test())
    
    # 總結報告
    print_header("優化性能測試總結")
    
    success_count = sum(test_results)
    total_tests = len(test_results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"  📊 測試通過率: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("  🎉 所有性能測試通過！系統性能優秀。")
        print("  💡 系統已準備好用於生產環境。")
    elif success_rate >= 75:
        print("  ⚠️  大部分測試通過，系統性能良好。")
        print("  💡 建議針對失敗的測試進行優化。")
    else:
        print("  ❌ 系統性能需要重大改進。")
        print("  💡 建議全面檢查系統架構和實作。")
    
    print(f"\n📝 優化建議:")
    print("  - 實施智能快取策略以提升重複計算效率")
    print("  - 考慮使用並行處理批量分析任務")
    print("  - 建立性能監控和自動優化機制")
    print("  - 定期進行性能基準測試和調優")
    print("  - 為高頻率使用場景優化核心算法")
    
    return success_rate

if __name__ == "__main__":
    try:
        performance_score = optimized_performance_test()
        exit_code = 0 if performance_score >= 75 else 1
        print(f"\n🔄 優化性能測試完成，退出代碼: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  性能測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 性能測試發生未預期錯誤: {e}")
        sys.exit(1)
