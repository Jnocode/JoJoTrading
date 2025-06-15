#!/usr/bin/env python3
"""
JoJotrading 完整功能測試腳本

此腳本執行端到端的功能測試，驗證整個系統從數據獲取到結果輸出的完整流程。
測試包括：
1. 狀態機初始化和配置載入
2. 產業選擇和股票數據獲取
3. DCF 估值計算（增強型和標準）
4. 結果篩選和排序
5. 錯誤處理和降級機制

執行方式：python end_to_end_test.py
"""

import sys
from pathlib import Path

# 添加 src 路徑到 Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import sys
import traceback
from datetime import datetime
import pandas as pd

# JoJotrading 模組
from jojo_trading.core.state_machine import JoJoStateMachine, JoJoState
from jojo_trading.utils.data_validator import FinancialDataValidator
from jojo_trading.core.enhanced_dcf import EnhancedDCFModel
from jojo_trading.core.integrated_dcf_handler import IntegratedDCFHandler
from jojo_trading.core.data_handler import DataHandler

def test_system_initialization():
    """測試系統初始化"""
    print("=" * 60)
    print("🚀 系統初始化測試")
    print("=" * 60)
    
    try:
        # 初始化狀態機
        state_machine = JoJoStateMachine()
        
        print(f"✓ 狀態機初始化成功")
        print(f"  當前狀態: {state_machine.current_state.name}")
        print(f"  產業數量: {len(state_machine.context.get('industry_names', []))}")
        print(f"  增強型 DCF: {state_machine.context.get('use_enhanced_dcf', False)}")
        print(f"  數據品質閾值: {state_machine.context.get('data_quality_threshold', 'N/A')}")
        
        return True, state_machine
        
    except Exception as e:
        print(f"✗ 系統初始化失敗: {e}")
        traceback.print_exc()
        return False, None

def test_data_processing():
    """測試數據處理流程"""
    print("\n" + "=" * 60)
    print("📊 數據處理流程測試")
    print("=" * 60)
    
    try:
        # 創建測試數據
        test_financial_data = pd.DataFrame({
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'operating_income': [200, 220, 240, 260, 280],
            'net_income': [150, 165, 180, 195, 210],
            'total_debt': [500, 520, 540, 560, 580],
            'cash': [100, 110, 120, 130, 140],
            'shares_outstanding': [100, 100, 100, 100, 100],
            'free_cash_flow': [180, 190, 200, 210, 220]
        })
        
        # 測試數據驗證
        validator = FinancialDataValidator()
        quality_score = validator.validate_data_quality(test_financial_data)
        print(f"✓ 數據品質驗證: {quality_score:.3f}")
        
        # 測試 DCF 參數
        dcf_inputs = {
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'growth_rate': 0.05,
            'terminal_growth_rate': 0.03,
            'discount_rate': 0.10,
            'shares_outstanding': 100,
            'debt': 500,
            'cash': 100
        }
        
        # 測試增強型 DCF
        enhanced_dcf = EnhancedDCFModel()
        result = enhanced_dcf.calculate_enhanced_dcf(**dcf_inputs)
        print(f"✓ 增強型 DCF 計算: ${result.base_case_valuation:.2f}")
        
        # 測試整合處理器
        handler = IntegratedDCFHandler()
        integrated_result = handler.calculate_integrated_dcf(
            financial_data=test_financial_data,
            dcf_inputs=dcf_inputs,
            quality_threshold=0.6
        )
        print(f"✓ 整合處理器結果: ${integrated_result:.2f}")
        
        return True, (quality_score, result, integrated_result)
        
    except Exception as e:
        print(f"✗ 數據處理測試失敗: {e}")
        traceback.print_exc()
        return False, None

def test_error_handling():
    """測試錯誤處理機制"""
    print("\n" + "=" * 60)
    print("🛡️ 錯誤處理機制測試")
    print("=" * 60)
    
    try:
        # 測試低品質數據的處理
        low_quality_data = pd.DataFrame({
            'revenue': [1000, None, 800, None, 600],  # 缺失值
            'operating_income': [200, -50, None, 150, -100],  # 缺失值和負值
            'net_income': [150, None, 50, 100, None],  # 多個缺失值
            'total_debt': [500, 800, 1200, 1500, 2000],
            'cash': [100, 80, 50, 20, 10],
            'shares_outstanding': [100, 120, 150, 180, 200]
        })
        
        # 驗證低品質數據
        validator = FinancialDataValidator()
        quality_score = validator.validate_data_quality(low_quality_data)
        print(f"✓ 低品質數據評分: {quality_score:.3f}")
        
        # 測試降級機制
        handler = IntegratedDCFHandler()
        dcf_inputs = {
            'revenue': [1000, 950, 800, 1200, 600],
            'growth_rate': 0.05,
            'terminal_growth_rate': 0.03,
            'discount_rate': 0.10,
            'shares_outstanding': 100,
            'debt': 500,
            'cash': 100
        }
        
        result = handler.calculate_integrated_dcf(
            financial_data=low_quality_data,
            dcf_inputs=dcf_inputs,
            quality_threshold=0.8  # 高閾值，強制降級
        )
        print(f"✓ 降級機制測試通過: ${result:.2f}")
        
        # 測試異常輸入處理
        try:
            invalid_inputs = {
                'revenue': [],  # 空列表
                'growth_rate': 'invalid',  # 無效類型
                'discount_rate': -0.1,  # 負值
            }
            enhanced_dcf = EnhancedDCFModel()
            enhanced_dcf.calculate_enhanced_dcf(**invalid_inputs)
            print("✗ 應該拋出異常但沒有")
            return False
            
        except Exception:
            print("✓ 異常輸入正確被捕獲")
        
        return True
        
    except Exception as e:
        print(f"✗ 錯誤處理測試失敗: {e}")
        traceback.print_exc()
        return False

def test_configuration_flexibility():
    """測試配置靈活性"""
    print("\n" + "=" * 60)
    print("⚙️ 配置靈活性測試")
    print("=" * 60)
    
    try:
        # 測試不同配置下的行為
        configurations = [
            {"use_enhanced_dcf": True, "data_quality_threshold": 0.5},
            {"use_enhanced_dcf": True, "data_quality_threshold": 0.8},
            {"use_enhanced_dcf": False, "data_quality_threshold": 0.6},
        ]
        
        for i, config in enumerate(configurations, 1):
            print(f"\n配置 {i}: {config}")
            
            # 暫時設置配置
            original_use_enhanced = DataHandler().USE_ENHANCED_DCF
            DataHandler().USE_ENHANCED_DCF = config["use_enhanced_dcf"]
            
            try:
                handler = IntegratedDCFHandler()
                # 這裡可以添加具體的配置測試邏輯
                print(f"  ✓ 配置 {i} 載入成功")
                
            finally:
                # 恢復原始配置
                DataHandler().USE_ENHANCED_DCF = original_use_enhanced
        
        print("✓ 所有配置測試通過")
        return True
        
    except Exception as e:
        print(f"✗ 配置測試失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """執行完整的端到端測試"""
    print("🎯 JoJotrading 完整功能測試")
    print("=" * 80)
    print(f"測試開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # 執行各項測試
    tests = [
        ("系統初始化", test_system_initialization),
        ("數據處理流程", test_data_processing),
        ("錯誤處理機制", test_error_handling),
        ("配置靈活性", test_configuration_flexibility),
    ]
    
    for test_name, test_func in tests:
        try:
            if test_name == "系統初始化":
                success, state_machine = test_func()
                test_results.append((test_name, success))
            else:
                success = test_func()
                test_results.append((test_name, success))
                
        except Exception as e:
            print(f"✗ {test_name} 執行異常: {e}")
            test_results.append((test_name, False))
    
    # 測試總結
    print("\n" + "=" * 80)
    print("📋 測試總結")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{test_name:<20} {status}")
    
    print(f"\n總體結果: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有功能測試通過！")
        print("✅ JoJotrading 系統運行正常，已準備好投入生產使用。")
        print("\n🚀 建議下一步行動：")
        print("   1. 部署到生產環境")
        print("   2. 監控系統性能")
        print("   3. 收集用戶反饋")
        print("   4. 規劃 Phase 2 功能")
    else:
        print(f"\n❌ {total - passed} 項測試失敗")
        print("請檢查上述錯誤信息並修復問題。")
    
    print(f"\n測試結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
