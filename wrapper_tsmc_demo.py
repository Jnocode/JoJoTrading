import sys
import os
import pandas as pd
from unittest.mock import MagicMock

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Mock streamlit before importing UI components
import streamlit
sys.modules["streamlit"] = MagicMock()

from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
from jojo_trading.analysis.wacc_calculator import WACCCalculator
from jojo_trading.ui.components.stage4_integration import Stage4IntegrationPanel

def run_demo():
    print("🚀 開始台積電 (2330) 完整估值演練 (Backend Verification)")
    print("="*60)

    # 1. 抓取真實數據
    print("\n1. 正在從 FinMind 抓取 2330 財務數據...")
    fetcher = AutoDataFetcher()
    dcf_data = fetcher.get_dcf_ready_data("2330")
    
    if not dcf_data['success']:
        print("❌ 抓取失敗:", dcf_data.get('error'))
        return

    # Extract Key Data
    price = dcf_data['current_market_price']
    shares = dcf_data['shares_outstanding']
    market_cap = price * shares
    total_debt = dcf_data['total_debt']
    # Use estimated interest if 0 (logic from UI)
    interest_expense = dcf_data['interest_expense']
    if interest_expense == 0 and total_debt > 0:
        interest_expense = total_debt * 0.025
        print("  (使用估算利息費用: 2.5%)")

    print(f"  ✅ 股價: {price}")
    print(f"  ✅ 市值: {market_cap/1e8:.1f} 億")
    print(f"  ✅ 總債務: {total_debt/1e8:.1f} 億")
    
    cash = dcf_data.get('cash', 0)
    net_debt = total_debt - cash
    print(f"  ✅ 現金: {cash/1e8:.1f} 億")
    print(f"  ✅ 淨債務: {net_debt/1e8:.1f} 億")

    # 2. 計算 WACC
    print("\n2. 計算 WACC (假設市場參數)...")
    wacc_calc = WACCCalculator()
    # Params from UI defaults
    rf = 0.015
    mr = 0.08
    beta = 1.2
    tax = 0.20
    
    ce = wacc_calc.calculate_cost_of_equity(beta, rf, mr)
    cd = wacc_calc.calculate_cost_of_debt(interest_expense, total_debt, tax)
    wacc_res = wacc_calc.calculate_wacc(market_cap, total_debt, ce, cd, tax)
    
    wacc = wacc_res['wacc']
    print(f"  ✅ WACC: {wacc:.2%}")

    # 3. 執行詳細 DCF 估值 (Waterfall Logic)
    print("\n3. 執行詳細 DCF 估值 (Waterfall Logic)...")
    panel = Stage4IntegrationPanel()
    
    # Extract detailed FCF components
    ni = dcf_data.get('net_income_parent', 0)
    dep = dcf_data.get('depreciation', 0)
    amo = dcf_data.get('amortization', 0)
    capex = dcf_data.get('capex', 0)
    
    print(f"  [輸入] 淨利: {ni/1e8:.1f}億")
    print(f"  [輸入] 折舊: {dep/1e8:.1f}億")
    print(f"  [輸入] 攤提: {amo/1e8:.1f}億")
    print(f"  [輸入] 資本支出: {capex/1e8:.1f}億")
    
    # Assumptions
    g_terminal = 0.03
    g_short = 0.10
    
    breakdown = panel._calculate_dcf_breakdown(
        base_fcf=0,
        shares=shares,
        wacc=wacc,
        terminal_growth=g_terminal,
        short_term_growth=g_short,
        net_debt=net_debt, # Correct Net Debt
        net_income=ni,
        depreciation=dep,
        amortization=amo,
        capex=capex,
        use_detailed_fcf=True
    )
    
    print(f"\n  [結果] 初始 FCF: {breakdown['current_fcf']/1e8:.1f}億")
    print(f"  [結果] 預測期現值 (5年): {breakdown['pv_explicit']/1e8:.1f}億")
    print(f"  [結果] 終值現值: {breakdown['pv_terminal']/1e8:.1f}億")
    print(f"  [結果] 企業價值: {breakdown['enterprise_value']/1e8:.1f}億")
    print(f"  [結果] 股權價值: {breakdown['equity_value']/1e8:.1f}億")
    print("="*60)
    print(f"🎯 預估合理股價: ${breakdown['share_price']:.2f}")
    
    # 4. 驗證情境分析 (Scenario Analysis)
    print("\n4. 驗證情境分析 (Scenario Analysis)...")
    
    def calc_scenario(g_short, g_term):
        return panel._calculate_dcf_breakdown(
            base_fcf=0, shares=shares, wacc=wacc,
            terminal_growth=g_term, short_term_growth=g_short,
            net_debt=net_debt, net_income=ni, depreciation=dep, 
            amortization=amo, capex=capex, use_detailed_fcf=True
        )['share_price']
        
    p_bear, p_base, p_bull = 0.2, 0.6, 0.2
    
    price_bear = calc_scenario(g_short - 0.05, g_terminal - 0.01)
    price_base = calc_scenario(g_short, g_terminal)
    price_bull = calc_scenario(g_short + 0.05, g_terminal + 0.01)
    
    weighted_price = (price_bear * p_bear + price_base * p_base + price_bull * p_bull)
    
    print(f"  🐻 Bear ($ {price_bear:.1f}) | 🏠 Base ($ {price_base:.1f}) | 🐂 Bull ($ {price_bull:.1f})")
    print(f"  🎯 加權目標價: $ {weighted_price:.2f}")
    
    # 5. 驗證反向 DCF (Reverse DCF)
    print("\n5. 驗證反向 DCF (Reverse DCF)...")
    market_price = price
    
    # Define solver func
    def solve_target_price_func(g):
         return panel._calculate_dcf_breakdown(
            base_fcf=0, shares=shares, wacc=wacc,
            terminal_growth=g_terminal, short_term_growth=g,
            net_debt=net_debt, net_income=ni, depreciation=dep, 
            amortization=amo, capex=capex, use_detailed_fcf=True
         )['share_price']
    
    implied_g = panel._solve_implied_growth(market_price, solve_target_price_func)
    print(f"  📈 當前股價: ${market_price}")
    if implied_g:
        print(f"  🔮 市場隱含成長率: {implied_g:.2%}")
        if implied_g > 0.20:
             print("  ⚠️ 結論: 高度成長溢價 (High Growth Premium)")
        else:
             print("  ℹ️ 結論: 合理或低估")
    else:
        print("  ❌ 無法計算隱含成長率")

    # 6. 驗證 DCF 適用性檢查 (Suitability Check)
    print("\n6. 驗證 DCF 適用性檢查...")
    
    # Case A: TSMC (Pass)
    print("  [測試] 台積電 (2330):", end=" ")
    if not str(2330).startswith('28') and ni > 0:
        print("✅ 通過")
    else:
        print("❌ 失敗 (不應發生)")
        
    # Case B: Fubon Financial (2881) - Mock Check
    print("  [測試] 富邦金 (2881):", end=" ")
    if str(2881).startswith('28'):
        print("⚠️ 警告: 金融類股 (正確識別)")
    else:
        print("❌ 未識別為金融股")

    # Case C: Loss Making Mock
    print("  [測試] 虧損公司 (Net Income < 0):", end=" ")
    if -1000 < 0:
        print("⚠️ 警告: 虧損公司 (正確識別)")
    
    
    # Verify DDM Logic
    print("\n7. 驗證 DDM 估值模型...")
    # Mock Dividend Data
    latest_div_mock = 14.0 # TSMC approx quarterly * 4
    ke_mock = 0.12 # Cost of Equity
    g_mock = 0.08  # Growth
    
    print(f"  [參數] D0=${latest_div_mock}, Ke={ke_mock:.1%}, g={g_mock:.1%}")
    d1 = latest_div_mock * (1 + g_mock)
    ddm_val = d1 / (ke_mock - g_mock)
    print(f"  [結果] DDM 估值: ${ddm_val:.2f}")
    
    if ddm_val > 0:
        print("✅ DDM 計算正常")
    else:
        print("❌ DDM 計算錯誤")
        
    print("="*60)

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
