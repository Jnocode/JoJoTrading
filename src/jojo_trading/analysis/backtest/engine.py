
import pandas as pd
import logging
from typing import Dict, Any, List
from .data_adapter import BacktestDataAdapter
from .strategy_parser import StrategyParser

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0 # Quantity
        self.position_avg_cost = 0.0
        self.trades = [] # List of dicts
        self.equity_curve = []

    def run(self, stock_code: str, buy_strategy: str, sell_strategy: str, start_date: str = "2023-01-01", end_date: str = None, interval: str = "1d", progress_callback=None) -> Dict[str, Any]:
        """
        Run the simulation.
        """
        # 1. Fetch Data
        if progress_callback: progress_callback(10) # 10% for data fetching
        
        # Determine yfinance period based on start_date roughly
        data_map = BacktestDataAdapter.get_kline_data(stock_code, period="max", interval=interval)
        
        if not data_map or 'daily' not in data_map:
            return {'error': 'No data'}
            
        df = data_map['daily']
        if df.empty:
            return {'error': 'Empty data'}

        # 2. Pre-calculate Indicators
        # Combine strategies to ensure all indicators are calculated
        full_strategy_text = f"{buy_strategy} {sell_strategy}"
        df = StrategyParser.parse_and_calculate(df, full_strategy_text)
        
        # 3. Filter by Date
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        mask = (df['date'] >= pd.to_datetime(start_date))
        if end_date:
            mask = mask & (df['date'] <= pd.to_datetime(end_date))
            
        df = df[mask].reset_index(drop=True)

        
        # 4. Main Loop
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        
        total_days = len(df)
        
        for i in range(total_days):
            # Progress update (from 20% to 100%)
            if progress_callback and i % 10 == 0:
                progress = 20 + int((i / total_days) * 80)
                progress_callback(progress)

            row = df.iloc[i]
            current_date = row['date']
            close_price = row['close']
            
            # Record Equity before trade
            market_val = self.position * close_price
            equity = self.capital + market_val
            self.equity_curve.append({'date': current_date, 'equity': equity, 'price': close_price})
            
            # Check Signal
            # Note: In real backtest, we might use 'open' of NEXT day for execution to be realistic,
            # or use 'close' if we assume we trade at close. 
            # astock_single logic: "Point-in-time" usually means we decide at close (or open).
            # Let's assume we execute at CLOSE price of the signal day (Simplest approximation).
            
            signal = StrategyParser.check_signal(df, i, buy_strategy, sell_strategy)
            
            if signal == 'buy':
                if self.position == 0:
                    self._buy(current_date, close_price)
                    
            elif signal == 'sell':
                if self.position > 0:
                    self._sell(current_date, close_price)
                    
        # Force close at end
        if self.position > 0:
            last_price = df.iloc[-1]['close']
            self._sell(df.iloc[-1]['date'], last_price, reason="End of Backtest")
            
        return self._generate_report(df)

    def run_dataframe(self, df: pd.DataFrame, progress_callback=None) -> Dict[str, Any]:
        """
        Run backtest on a DataFrame that already contains 'Signal' column (1, -1, 0).
        Requires columns: 'date', 'close', 'Signal'
        """
        # Ensure date column is datetime
        df = df.copy() # Avoid modifying original
        if 'date' not in df.columns:
            if 'Date' in df.columns: 
                df.rename(columns={'Date': 'date'}, inplace=True)
            elif isinstance(df.index, pd.DatetimeIndex):
                df['date'] = df.index
            else:
                df['date'] = df.index # Fallback
            
        df['date'] = pd.to_datetime(df['date'])
        
        # Ensure column names map to what we expect
        if 'Close' in df.columns and 'close' not in df.columns:
            df['close'] = df['Close']
            
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        
        total_days = len(df)
        
        for i in range(total_days):
            if progress_callback and i % 10 == 0:
                progress = int((i / total_days) * 100)
                progress_callback(progress)

            row = df.iloc[i]
            current_date = row['date']
            close_price = row['close']
            
            # Record Equity
            market_val = self.position * close_price
            equity = self.capital + market_val
            self.equity_curve.append({'date': current_date, 'equity': equity, 'price': close_price})
            
            # Check Signal (1=Buy, -1=Sell)
            signal_val = row.get('Signal', 0)
            
            # Execution Logic (Long Only for now)
            if signal_val == 1:
                if self.position == 0:
                    self._buy(current_date, close_price)
            elif signal_val == -1:
                # -1 closes Long position
                if self.position > 0:
                    self._sell(current_date, close_price)
            
            # TODO: Intra-candle Stop Loss using Low/High
                    
        # Force close at end
        if self.position > 0:
            last_price = df.iloc[-1]['close']
            self._sell(df.iloc[-1]['date'], last_price, reason="End of Backtest")
            
        return self._generate_report(df)

    def _buy(self, date, price):
        # Full position buy (Simple)
        # Fee: 0.1425% (Tai Stock)
        fee_rate = 0.001425
        
        max_qty = int(self.capital / (price * (1 + fee_rate)))
        max_qty = (max_qty // 1000) * 1000 # Round down to 1 lot (1000 shares)
        
        if max_qty > 0:
            cost = max_qty * price
            fee = cost * fee_rate
            self.capital -= (cost + fee)
            self.position = max_qty
            self.position_avg_cost = price
            
            self.trades.append({
                'type': 'buy',
                'date': date,
                'price': price,
                'qty': max_qty,
                'fee': fee
            })


    def _sell(self, date, price, reason="Signal"):
        # Sell all
        fee_rate = 0.001425
        tax_rate = 0.003 # Tai Stock Tax
        
        revenue = self.position * price
        fee = revenue * fee_rate
        tax = revenue * tax_rate
        
        net_revenue = revenue - fee - tax
        self.capital += net_revenue
        
        # Calculate PnL for this round trip
        buy_record = [t for t in self.trades if t['type']=='buy'][-1]
        pnl = net_revenue - (buy_record['price'] * buy_record['qty'] + buy_record['fee']) # Approx
        
        self.trades.append({
            'type': 'sell',
            'date': date,
            'price': price,
            'qty': self.position,
            'fee': fee + tax,
            'pnl': pnl,
            'reason': reason
        })
        
        self.position = 0

    def _generate_report(self, df):
        # 1. Trade Statistics
        completed_trades = [t for t in self.trades if t['type'] == 'sell']
        total_trades = len(completed_trades)
        wins = [t for t in completed_trades if t['pnl'] > 0]
        losses = [t for t in completed_trades if t['pnl'] <= 0]
        
        gross_profit = sum(t['pnl'] for t in wins)
        gross_loss = abs(sum(t['pnl'] for t in losses))
        
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0)
        
        # 2. Equity Statistics
        final_equity = self.capital # Position is 0
        total_return_pct = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # Helper for Annualized Metrics
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        
        if not equity_series.empty:
            # Daily Returns
            daily_returns = equity_series.pct_change().dropna()
            
            # Annualized Return (CAGR approximation or simple annualized)
            # Assuming 252 trading days
            days_held = len(equity_series)
            if days_held > 10: # Avoid crazy numbers for short periods
                ann_return_pct = ((final_equity / self.initial_capital) ** (252 / days_held) - 1) * 100
            else:
                ann_return_pct = 0.0
                
            # Annualized Volatility
            ann_volatility_pct = daily_returns.std() * (252 ** 0.5) * 100
            
            # Sharpe Ratio (Risk Free Rate = 2%)
            rf_daily = 0.02 / 252
            if daily_returns.std() != 0:
                excess_returns = daily_returns - rf_daily
                sharpe_ratio = (excess_returns.mean() / daily_returns.std()) * (252 ** 0.5)
            else:
                sharpe_ratio = 0.0
            
            # Max Drawdown
            running_max = equity_series.cummax()
            drawdown = (equity_series - running_max) / running_max
            max_drawdown_pct = drawdown.min() * 100
        else:
            ann_return_pct = 0.0
            ann_volatility_pct = 0.0
            sharpe_ratio = 0.0
            max_drawdown_pct = 0.0

        # 3. Benchmark (Buy & Hold)
        if not df.empty:
            first_price = df.iloc[0]['close']
            last_price = df.iloc[-1]['close']
            benchmark_return = (last_price - first_price) / first_price * 100
        else:
            benchmark_return = 0.0

        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return_pct': total_return_pct,
            'ann_return_pct': ann_return_pct,
            'ann_volatility_pct': ann_volatility_pct,
            'sharpe_ratio': sharpe_ratio,
            'benchmark_return': benchmark_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_drawdown_pct,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'df': df # Return DataFrame for plotting
        }
