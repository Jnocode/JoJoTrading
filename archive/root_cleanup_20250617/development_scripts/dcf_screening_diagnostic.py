"""
DCF篩選診斷工具
幫助診斷為什麼篩選條件找不到符合的股票
"""

import sys
from pathlib import Path

# 添加src路徑
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

def diagnose_screening_issue():
    """診斷篩選問題"""
    print("🔍 DCF篩選診斷工具")
    print("=" * 50)
    
    try:
        # 導入必要模組
        from jojo_trading.core.industry_dcf_params import get_industry_params, get_adjusted_screening_params
        from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
        
        # 初始化資料抓取器
        print("📡 初始化資料抓取器...")
        auto_fetcher = AutoDataFetcher()
        
        # 測試股票清單
        test_stocks = ["2330", "2317", "2454", "2412", "2882"]
        
        print("\n📊 測試股票DCF計算結果:")
        print("-" * 40)
        
        for stock_code in test_stocks:
            print(f"\n🔍 分析股票: {stock_code}")
            
            try:
                # 獲取股票數據
                dcf_data = auto_fetcher.get_dcf_ready_data(stock_code)
                
                if not dcf_data.get('success', False):
                    print(f"  ❌ 資料抓取失敗: {dcf_data.get('error', '未知錯誤')}")
                    continue
                
                # 計算自由現金流
                net_income = dcf_data.get('net_income_parent', 0) / 1e8
                depreciation = dcf_data.get('depreciation', 0) / 1e8
                capex = dcf_data.get('capex', 0) / 1e8
                free_cash_flow = max(net_income + depreciation - capex, 1.0)
                
                current_price = dcf_data.get('current_market_price', 100)
                shares_outstanding = dcf_data.get('shares_outstanding', 100000000) / 1e8
                company_name = dcf_data.get('company_name', f'股票{stock_code}')
                
                print(f"  ✅ 公司: {company_name}")
                print(f"  📈 當前股價: ${current_price:.0f}")
                print(f"  💰 自由現金流: {free_cash_flow:.1f}億")
                print(f"  📊 流通股數: {shares_outstanding:.1f}億股")
                
                # 使用不同參數進行DCF計算
                scenarios = [
                    {"name": "保守", "growth": 3.0, "terminal": 1.5, "discount": 9.0},
                    {"name": "中性", "growth": 5.0, "terminal": 2.0, "discount": 8.0},
                    {"name": "樂觀", "growth": 8.0, "terminal": 2.5, "discount": 7.0}
                ]
                
                for scenario in scenarios:
                    growth_rate = scenario["growth"]
                    terminal_growth = scenario["terminal"]
                    discount_rate = scenario["discount"]
                    
                    # DCF計算
                    if discount_rate <= terminal_growth:
                        continue
                    
                    # 計算未來現金流現值
                    present_values = []
                    for year in range(1, 6):
                        future_fcf = free_cash_flow * (1 + growth_rate/100)**year
                        present_value = future_fcf / (1 + discount_rate/100)**year
                        present_values.append(present_value)
                    
                    # 計算終值
                    terminal_fcf = free_cash_flow * (1 + growth_rate/100)**5
                    terminal_value = terminal_fcf * (1 + terminal_growth/100) / ((discount_rate/100) - (terminal_growth/100))
                    terminal_pv = terminal_value / (1 + discount_rate/100)**5
                      # 企業總價值和每股內在價值
                    total_pv = sum(present_values)
                    enterprise_value = total_pv + terminal_pv
                    intrinsic_value_per_share = enterprise_value / shares_outstanding  # 修正：移除 * 100
                    
                    # 計算潛在報酬率
                    potential_return = ((intrinsic_value_per_share - current_price) / current_price) * 100
                    
                    print(f"    {scenario['name']}情境 (成長{growth_rate}%, 折現{discount_rate}%):")
                    print(f"      內在價值: ${intrinsic_value_per_share:.0f}")
                    print(f"      潛在報酬: {potential_return:+.1f}%")
                
                # 計算市值
                market_cap = current_price * shares_outstanding / 100
                print(f"  💼 市值: {market_cap:.1f}億元")
                
            except Exception as e:
                print(f"  ❌ 計算錯誤: {e}")
        
        print("\n🎯 篩選條件建議:")
        print("-" * 30)
        print("根據診斷結果，建議調整篩選條件:")
        print("1. 🔄 啟用寬鬆篩選模式")
        print("2. 📉 降低最低潛在報酬要求至 3-5%")
        print("3. 💰 降低最小市值要求至 30-50億")
        print("4. 📊 使用較樂觀的成長率參數")
        print("5. 🏭 嘗試特定行業篩選而非全部")
        
        print("\n💡 可能的問題原因:")
        print("- 當前市場可能整體估值偏高")
        print("- 篩選條件可能過於嚴格")
        print("- 部分股票資料可能不完整")
        print("- DCF模型對參數敏感，小幅調整參數可能有較大影響")
        
    except Exception as e:
        print(f"❌ 診斷過程發生錯誤: {e}")
        print("\n🔧 故障排除建議:")
        print("1. 檢查 AutoDataFetcher 是否正常運作")
        print("2. 確認 FinMind API 連接狀態")
        print("3. 檢查行業參數模組是否正確載入")

def suggest_optimal_parameters():
    """建議最佳篩選參數"""
    print("\n🎯 最佳篩選參數建議")
    print("=" * 30)
    
    try:
        from jojo_trading.core.industry_dcf_params import INDUSTRY_DCF_PARAMS
        
        print("根據不同投資策略的建議參數:")
        print()
        
        strategies = {
            "保守型投資者": {
                "min_return": 3.0,
                "min_market_cap": 100,
                "description": "注重穩定性，較低風險偏好"
            },
            "穩健型投資者": {
                "min_return": 5.0,
                "min_market_cap": 50,
                "description": "平衡風險與報酬"
            },
            "積極型投資者": {
                "min_return": 8.0,
                "min_market_cap": 30,
                "description": "追求高報酬，願意承擔較高風險"
            }
        }
        
        for strategy, params in strategies.items():
            print(f"📊 {strategy}:")
            print(f"  最低潛在報酬: {params['min_return']}%")
            print(f"  最小市值: {params['min_market_cap']}億")
            print(f"  說明: {params['description']}")
            print(f"  建議: 啟用寬鬆模式，實際篩選標準會降低30%")
            print()
        
    except Exception as e:
        print(f"參數建議生成失敗: {e}")

if __name__ == "__main__":
    diagnose_screening_issue()
    suggest_optimal_parameters()
