
import sys
import os
import pandas as pd
from jojo_trading.core.finmind_fetcher import FinMindFetcher
from jojo_trading.strategy.smc_strategy import SMCStrategy
from jojo_trading.analysis.backtest.engine import BacktestEngine

def run_backtest(stock_code="2330", days=600):
    print(f"🚀 Starting Backtest for {stock_code} (Last {days} days)...")
    
    # 1. Fetch Data
    fetcher = FinMindFetcher()
    print("📡 Fetching data from FinMind...")
    df = fetcher.get_stock_price(stock_code, days=days)
    
    if df.empty:
        print("❌ Error: No data fetched.")
        return

    print(f"✅ Fetched {len(df)} bars.")
    
    # 2. Run Strategy
    print("🧠 analyzing with SMC Strategy (Pure SMC Mode)...")
    config = {
        'swings_length': 20,
        'confirm_bars': 1,
        'use_structure_confirm': True,
        'use_price_filter': False,
        'price_filter_percent': 50,
        'use_atr_stop': True,
        'atr_mult': 3.0
    }
    
    strategy = SMCStrategy(config)
    df = strategy.analyze(df)
    
    # Debug: Print signals
    signals = df[df['Signal'] != 0]
    print(f"📊 Signals Generated: {len(signals)}")
    if not signals.empty:
        print(signals[['Close', 'Signal', 'Comment']].tail())

    # 3. Simulate Logic
    print("💰 Running Simulation...")
    # Add 'close' column required by engine if not lower case
    if 'Close' in df.columns:
        df['close'] = df['Close']
        
    engine = BacktestEngine(initial_capital=1000_0000)
    
    # Use our new run_dataframe method
    result = engine.run_dataframe(df) # df already has 'Signal' and 'date' index
    
    # 4. Report
    print("-" * 40)
    print(f"🏁 Final Equity: ${result['final_equity']:,.0f}")
    print(f"📈 Return: {result['total_return_pct']:.2f}% (Annurel: {result['ann_return_pct']:.2f}%)")
    print(f"⚡ Volatility: {result['ann_volatility_pct']:.2f}%")
    print(f"⚖️ Sharpe Ratio: {result['sharpe_ratio']:.2f}")
    print(f"📊 Benchmark: {result['benchmark_return']:.2f}%")
    print(f"🔄 Total Trades: {result['total_trades']}")
    print(f"🎯 Win Rate: {result['win_rate']:.2f}%")
    if result['max_drawdown_pct'] != 0:
        print(f"📉 Max Drawdown: {result['max_drawdown_pct']:.2f}%")
    
    # Plotting
    try:
        import matplotlib.pyplot as plt
        
        equity_data = [e['equity'] for e in result['equity_curve']]
        dates = [e['date'] for e in result['equity_curve']]
        
        plt.figure(figsize=(10, 6))
        plt.plot(dates, equity_data, label='Equity')
        plt.title(f'SMC Strategy Backtest - {stock_code}')
        plt.xlabel('Date')
        plt.ylabel('Equity')
        plt.legend()
        plt.grid(True)
        
        output_path = os.path.join(os.path.dirname(__file__), 'backtest_result.png')
        plt.savefig(output_path)
        print(f"🖼️ Saved Equity Curve to: {output_path}")
        
    except Exception as e:
        print(f"⚠️ Plotting failed: {e}")

    if result['total_trades'] == 0:
        print("\n⚠️ No trades executed. Check if logic is too strict.")
    else:
        print("\n📝 Recent Trades:")
        for t in result['trades'][-5:]:
            pnl_str = f", PnL: {t['pnl']:,.0f}" if 'pnl' in t else ""
            print(f"[{t['date'].strftime('%Y-%m-%d')}] {t['type'].upper()} {t['qty']} @ {t['price']}{pnl_str}")

if __name__ == "__main__":
    # Ensure src is in path
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    sys.path.append(src_path)
    
    # Run
    run_backtest("2330", days=500) # TSMC
    print("-" * 40)
    # run_backtest("2603", days=500) # Evergreen (Volatile)
