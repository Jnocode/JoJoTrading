"""
DCF 篩選診斷工具
分析為什麼找不到符合條件的股票
"""

import sys
from pathlib import Path

# 添加項目路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
    
    print("="*80)
    print("DCF 篩選診斷報告")
    print("="*80)
    
    # 初始化資料抓取器
    print("\n[1] 初始化 AutoDataFetcher...")
    fetcher = AutoDataFetcher()
    print("✅ AutoDataFetcher 初始化成功")
    
    # 測試股票清單
    test_stocks = [
        "2330", "2317", "2454", "2412", "2882", "2881", "2886", 
        "2303", "2308", "1301", "2002", "2207", "2379", "3711",
        "2357", "2345", "6505", "2382", "2395", "2409"
    ]
    
    print(f"\n[2] 測試 {len(test_stocks)} 檔股票的數據抓取...")
    print("-"*80)
    
    success_count = 0
    fail_count = 0
    missing_fields_count = {}
    
    for stock_code in test_stocks:
        try:
            print(f"\n📊 測試 {stock_code}...")
            data = fetcher.get_dcf_ready_data(stock_code)
            
            if data.get('success'):
                success_count += 1
                print(f"  ✅ 抓取成功")
                
                # 檢查關鍵欄位
                required_fields = {
                    'company_name': '公司名稱',
                    'current_market_price': '當前股價',
                    'shares_outstanding': '流通股數',
                    'net_income_parent': '歸屬母公司淨利',
                    'capex': '資本支出',
                    'depreciation': '折舊費用'
                }
                
                missing = []
                for field, label in required_fields.items():
                    value = data.get(field, 0)
                    if value == 0 or value is None:
                        missing.append(label)
                        missing_fields_count[label] = missing_fields_count.get(label, 0) + 1
                
                if missing:
                    print(f"  ⚠️  缺少欄位: {', '.join(missing)}")
                else:
                    print(f"  ✨ 所有關鍵欄位完整")
                
                # 計算基本指標
                shares = data.get('shares_outstanding', 0)
                price = data.get('current_market_price', 0)
                if shares > 0 and price > 0:
                    market_cap = shares * price / 1e8
                    print(f"  📈 市值: {market_cap:.1f} 億元")
                    
                    net_income = data.get('net_income_parent', 0) / 1e8
                    capex = data.get('capex', 0) / 1e8
                    depreciation = data.get('depreciation', 0) / 1e8
                    
                    # 簡化 FCF 計算
                    fcf = net_income + depreciation - capex
                    print(f"  💰 簡化 FCF: {fcf:.1f} 億元")
                    
                    # 模擬 DCF 計算 (5% 成長, 2% 永續, 8% 折現)
                    if fcf > 0:
                        # 5年預測
                        future_fcf = []
                        for year in range(1, 6):
                            future_fcf.append(fcf * (1.05 ** year))
                        
                        # 終值
                        terminal_value = (future_fcf[-1] * 1.02) / (0.08 - 0.02)
                        
                        # 折現
                        pv_fcf = sum([cf / (1.08 ** (i+1)) for i, cf in enumerate(future_fcf)])
                        pv_terminal = terminal_value / (1.08 ** 5)
                        
                        enterprise_value = pv_fcf + pv_terminal
                        intrinsic_value_per_share = (enterprise_value * 1e8) / shares
                        
                        potential_return = ((intrinsic_value_per_share - price) / price) * 100
                        
                        print(f"  🎯 內在價值: ${intrinsic_value_per_share:.1f}")
                        print(f"  📊 當前股價: ${price:.1f}")
                        print(f"  💡 潛在報酬: {potential_return:+.1f}%")
                        
                        if potential_return >= 0:
                            print(f"  ✨ 符合標準模式 (≥0%)")
                        else:
                            print(f"  ❌ 不符合標準模式 (<0%)")
                    else:
                        print(f"  ⚠️  FCF ≤ 0, 無法進行 DCF 估值")
                else:
                    print(f"  ❌ 市值數據不完整")
            else:
                fail_count += 1
                error = data.get('error', '未知錯誤')
                print(f"  ❌ 抓取失敗: {error}")
                
        except Exception as e:
            fail_count += 1
            print(f"  ❌ 發生異常: {e}")
    
    # 總結報告
    print("\n" + "="*80)
    print("診斷總結")
    print("="*80)
    print(f"✅ 成功抓取: {success_count}/{len(test_stocks)} ({success_count/len(test_stocks)*100:.1f}%)")
    print(f"❌ 失敗: {fail_count}/{len(test_stocks)} ({fail_count/len(test_stocks)*100:.1f}%)")
    
    if missing_fields_count:
        print(f"\n⚠️  常見缺失欄位統計:")
        for field, count in sorted(missing_fields_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {field}: {count} 檔股票缺失")
    
    print("\n" + "="*80)
    print("可能的問題原因")
    print("="*80)
    print("""
1. **數據品質問題**:
   - FinMind API 部分股票數據不完整
   - 某些欄位名稱不匹配
   - 數據時間延遲

2. **DCF 計算問題**:
   - 自由現金流為負值 (成長期公司常見)
   - 折現率設定過高
   - 成長率假設不適合該產業

3. **篩選條件過嚴**:
   - 潛在報酬率門檻 ≥0% 可能在高估市場中難以找到
   - 市值門檻 ≥100億 排除許多中小型股
   - 未考慮不同產業的估值特性

4. **建議解決方案**:
   - 使用「極度寬鬆」或「寬鬆」模式 (允許 -10% ~ -20% 報酬)
   - 降低市值門檻到 50 億或 20 億
   - 針對不同產業使用不同的 DCF 參數
   - 檢查並補充缺失的財務數據
    """)
    
    print("\n" + "="*80)
    print("建議測試")
    print("="*80)
    print("""
請在 Streamlit 應用中嘗試:

1. **調整篩選模式**:
   - 從「標準 📗」改為「寬鬆 📘」或「極度寬鬆 🌊」
   - 觀察結果數量變化

2. **調整 DCF 參數**:
   - 降低折現率: 從 8% → 7% 或 6%
   - 提高成長率: 從 5% → 7% 或 10%
   - 調整永續成長率: 從 2% → 2.5% 或 3%

3. **檢查個股數據**:
   - 使用「個股 DCF 分析」分頁
   - 逐一檢查 2330, 2317, 2454 等股票
   - 確認數據完整性和計算結果

4. **產業篩選**:
   - 選擇特定產業 (如「半導體」)
   - 使用產業特定的 DCF 參數
    """)

except ImportError as e:
    print(f"❌ 模組導入失敗: {e}")
    print("\n請確認:")
    print("1. src/jojo_trading/core/auto_data_fetcher.py 存在")
    print("2. Python 路徑設定正確")
    print("3. 在 jojo_trading 專案根目錄執行此腳本")

except Exception as e:
    print(f"❌ 執行過程發生錯誤: {e}")
    import traceback
    traceback.print_exc()
