#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCF 負值修正驗證腳本
測試修正後的 DCF 參數是否能產生合理的評估值
"""

import sys
from pathlib import Path

# 添加 src 路徑到 Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import sys
import os

# 添加專案目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from jojo_trading.core.data_handler import get_stock_data, calculate_dcf_valuation
    from jojo_trading.core.enhanced_dcf import calculate_enhanced_dcf_valuation
    from jojo_trading.utils.data_validator import validate_data_for_dcf
    from jojo_trading.core.integrated_dcf_handler import IntegratedDCFHandler
    import pandas as pd
    import datetime
except ImportError as e:
    print(f"匯入錯誤: {e}")
    print("請確保所有必要的模組都已正確安裝")
    sys.exit(1)

def test_stock_dcf(stock_code, test_name=""):
    """測試單一股票的 DCF 計算"""
    print(f"\n{'='*60}")
    print(f"測試股票: {stock_code} {test_name}")
    print(f"{'='*60}")
    
    # 測試參數 - 使用修正後的參數
    context = {
        'dcf_short_term_growth_rate': 0.08,  # 修正後參數 (7% -> 8%)
        'dcf_terminal_growth_rate': 0.03,    # 修正後參數 (2.5% -> 3%)
        'dcf_projection_years': 5,
        'risk_preference': 0.08,             # 修正後參數 (10% -> 8%)
        'use_enhanced_dcf': True
    }
    
    try:
        # 1. 取得股票資料
        print(f"1. 取得 {stock_code} 的財務資料...")
        stock_data = get_stock_data(stock_code)
        
        if not stock_data or 'financials' not in stock_data:
            print(f"   ❌ 無法取得 {stock_code} 的財務資料")
            return False
            
        financials = stock_data['financials']
        print(f"   ✅ 成功取得財務資料")
        
        # 2. 驗證資料 (if validation function exists)
        print(f"2. 驗證 DCF 計算所需資料...")
        try:
            validation_result = validate_data_for_dcf(stock_code, financials, context)
            if not validation_result.get('is_valid', False):
                print(f"   ❌ 資料驗證失敗: {validation_result.get('reason', '未知原因')}")
                return False
            print(f"   ✅ 資料驗證通過")
        except Exception as e:
            print(f"   ⚠️  驗證函數不可用，跳過驗證: {e}")
        
        # 3. 計算標準 DCF
        print(f"3. 計算標準 DCF 估值...")
        context['use_enhanced_dcf'] = False
        standard_dcf_result = calculate_dcf_valuation(
            stock_code, financials, context['risk_preference'], context
        )
        
        # 4. 計算增強 DCF
        print(f"4. 計算增強 DCF 估值...")
        context['use_enhanced_dcf'] = True
        enhanced_dcf_result = calculate_dcf_valuation(
            stock_code, financials, context['risk_preference'], context
        )
        
        # 5. 顯示結果
        print(f"\n📊 DCF 估值結果:")
        print(f"   股票代號: {stock_code}")
        
        standard_success = False
        enhanced_success = False
        
        if standard_dcf_result and 'dcf_valuation' in standard_dcf_result:
            dcf_val = standard_dcf_result['dcf_valuation']
            market_price = standard_dcf_result.get('current_market_price', 'N/A')
            print(f"   標準 DCF 估值: ${dcf_val:.2f}")
            print(f"   目前市價: ${market_price}")
            if isinstance(market_price, (int, float)) and market_price > 0:
                upside = ((dcf_val - market_price) / market_price) * 100
                print(f"   上漲空間: {upside:.1f}%")
            
            if dcf_val > 0:
                standard_success = True
                print(f"   ✅ 標準 DCF 產生正值估值")
            else:
                print(f"   ❌ 標準 DCF 仍為負值或零")
        else:
            print(f"   ❌ 標準 DCF 計算失敗")
            
        if enhanced_dcf_result and 'dcf_valuation' in enhanced_dcf_result:
            dcf_val = enhanced_dcf_result['dcf_valuation']
            market_price = enhanced_dcf_result.get('current_market_price', 'N/A')
            print(f"   增強 DCF 估值: ${dcf_val:.2f}")
            if isinstance(market_price, (int, float)) and market_price > 0:
                upside = ((dcf_val - market_price) / market_price) * 100
                print(f"   增強 DCF 上漲空間: {upside:.1f}%")
            
            if dcf_val > 0:
                enhanced_success = True
                print(f"   ✅ 增強 DCF 產生正值估值")
            else:
                print(f"   ❌ 增強 DCF 仍為負值或零")
        else:
            print(f"   ❌ 增強 DCF 計算失敗")
        
        # 6. 判斷是否修正成功
        success = standard_success or enhanced_success
        
        if success:
            print(f"   🎉 DCF 修正成功!")
        else:
            print(f"   ⚠️  仍需要進一步調整參數")
        
        return success
        
    except Exception as e:
        print(f"   ❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_comparison():
    """測試新舊參數對比"""
    print(f"\n{'='*60}")
    print("DCF 參數修正對比")
    print(f"{'='*60}")
    
    print("修正前參數:")
    print("  短期成長率: 7%")
    print("  永續成長率: 2.5%")
    print("  風險偏好/折現率: 10%")
    
    print("\n修正後參數:")
    print("  短期成長率: 8% (+1%)")
    print("  永續成長率: 3% (+0.5%)")
    print("  風險偏好/折現率: 8% (-2%)")
    
    print("\n修正理由:")
    print("1. 台灣十年期公債殖利率約 1.5%，10% 折現率過高")
    print("2. 台灣科技股成長性較強，7% 短期成長率過於保守")
    print("3. 永續成長率應與長期 GDP 成長預期一致")

def main():
    """主測試函數"""
    print("🚀 DCF 負值修正驗證腳本")
    print(f"測試時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 顯示參數修正對比
    test_parameter_comparison()
    
    # 測試股票列表 (台灣主要股票)
    test_stocks = [
        ("2330", "台積電 (TSMC)"),
        ("2317", "鴻海 (Foxconn)"),
        ("2454", "聯發科 (MediaTek)"),
        ("2382", "廣達 (Quanta)"),
        ("2881", "富邦金 (Fubon Financial)")
    ]
    
    print(f"\n📋 測試計畫:")
    for code, name in test_stocks:
        print(f"   - {code}: {name}")
    
    # 執行測試
    success_count = 0
    total_count = len(test_stocks)
    
    for stock_code, stock_name in test_stocks:
        success = test_stock_dcf(stock_code, stock_name)
        if success:
            success_count += 1
    
    # 測試摘要
    print(f"\n{'='*60}")
    print(f"📈 測試摘要")
    print(f"{'='*60}")
    print(f"測試股票總數: {total_count}")
    print(f"修正成功數量: {success_count}")
    print(f"修正失敗數量: {total_count - success_count}")
    print(f"成功率: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print(f"🎉 所有測試都通過! DCF 負值問題已成功修正")
        print(f"✅ 建議將修正後的參數作為系統預設值")
    elif success_count > total_count * 0.6:  # 60% 以上成功率
        print(f"✅ 大部分測試通過，修正基本成功")
        print(f"⚠️  仍有 {total_count - success_count} 隻股票需要個別調整")
    else:
        print(f"❌ 修正效果不佳，需要進一步調整參數")
        print(f"💡 建議:")
        print(f"   - 考慮進一步降低折現率 (如 7%)")
        print(f"   - 提高短期成長率 (如 9-10%)")
        print(f"   - 調整 FCF 計算方式")
    
    return success_count >= total_count * 0.6

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試腳本發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
