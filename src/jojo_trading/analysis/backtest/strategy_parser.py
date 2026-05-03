
import pandas as pd
import numpy as np
import re
from typing import Dict, Any
from jojo_trading.analysis.backtest.risk_radar import RiskRadar

class StrategyParser:
    """
    Parses string-based strategies and calculates indicators on the DataFrame.
    """
    
    @staticmethod
    def parse_and_calculate(df: pd.DataFrame, strategy_str: str) -> pd.DataFrame:
        """
        Pre-calculates indicators mentioned in the strategy string and adds them to DF.
        Returns the modified DataFrame.
        """
        # 11. Risk Radar: "Risk_Score", "Risk_Allowed"
        if 'Risk' in strategy_str:
             if 'Risk_Score' not in df.columns:
                 df = RiskRadar.calculate_risk(df)
             if 'Risk_Allowed' not in df.columns:
                 df = RiskRadar.apply_risk_filter(df, max_risk=6.0)

        # 9. SuperTrend: "SuperTrend" or "SuperTrend_Trend"
        if 'SuperTrend' in strategy_str:
            if 'SuperTrend' not in df.columns:
                StrategyParser._calculate_supertrend(df)

        # 10. SMC: "SMC_SwingHigh", "SMC_SwingLow"
        if 'SMC' in strategy_str:
            if 'SMC_SwingHigh' not in df.columns:
                StrategyParser._calculate_smc(df)

        # 1. Moving Averages: Matches "MA(\d+)" or "D(\d+)MA"
        # Example: MA20 or D20MA
        # 1. Moving Averages: Matches "MA(\d+)" or "D(\d+)MA"
        # Example: MA20 or D20MA
        ma_matches = []
        ma_matches.extend(re.findall(r'MA(\d+)', strategy_str, re.IGNORECASE))
        ma_matches.extend(re.findall(r'D(\d+)MA', strategy_str, re.IGNORECASE))
        
        for window in ma_matches:
            col_name = f"MA{window}"
            if col_name not in df.columns:
                 df[col_name] = df['close'].rolling(window=int(window)).mean()
                
        # 2. RSI: Matches "RSI(\d+)"
        rsi_matches = re.findall(r'RSI(\d+)', strategy_str, re.IGNORECASE)
        for window in rsi_matches:
            col_name = f"RSI{window}"
            if col_name not in df.columns:
                df[col_name] = StrategyParser._calculate_rsi(df['close'], int(window))

        # 3. Volume MA: "VMA(\d+)"
        vma_matches = re.findall(r'VMA(\d+)', strategy_str, re.IGNORECASE)
        for window in vma_matches:
            col_name = f"VMA{window}"
            if col_name not in df.columns:
                df[col_name] = df['volume'].rolling(window=int(window)).mean()
        
        return df

    @staticmethod
    def _calculate_bollinger(df: pd.DataFrame, n=20, k=2):
        ma = df['close'].rolling(window=n).mean()
        std = df['close'].rolling(window=n).std()
        df['BB_Mid'] = ma
        df['BB_Upper'] = ma + k * std
        df['BB_Lower'] = ma - k * std

    @staticmethod
    def _calculate_supertrend(df: pd.DataFrame, period=10, multiplier=3):
        # Calculate ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()

        # Basic Upper/Lower Bands
        hl2 = (df['high'] + df['low']) / 2
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)
        
        # Convert to numpy and handle NaN
        close_prices = df['close'].values
        bu = basic_upper.values
        bl = basic_lower.values
        n = len(df)
        
        fu = np.full(n, np.nan)
        fl = np.full(n, np.nan)
        tr = np.full(n, np.nan)
        
        # Find first valid index (after ATR warmup)
        first_valid = period  # ATR needs 'period' bars
        
        # Initialize first valid values
        if first_valid < n:
            fu[first_valid] = bu[first_valid]
            fl[first_valid] = bl[first_valid]
            # Initial trend: Bull if close > hl2, else Bear
            tr[first_valid] = 1 if close_prices[first_valid] > hl2.iloc[first_valid] else -1
        
        # Iterative calculation
        for i in range(first_valid + 1, n):
            # Skip if basic bands are NaN
            if np.isnan(bu[i]) or np.isnan(bl[i]):
                fu[i] = fu[i-1]
                fl[i] = fl[i-1]
                tr[i] = tr[i-1]
                continue
                
            # Final Upper Band
            if bu[i] < fu[i-1] or close_prices[i-1] > fu[i-1]:
                fu[i] = bu[i]
            else:
                fu[i] = fu[i-1]
                
            # Final Lower Band
            if bl[i] > fl[i-1] or close_prices[i-1] < fl[i-1]:
                fl[i] = bl[i]
            else:
                fl[i] = fl[i-1]
                
            # Trend determination
            prev_trend = tr[i-1]
            if prev_trend == -1:  # Was Bear
                if close_prices[i] > fu[i]:
                    tr[i] = 1  # Switch to Bull
                else:
                    tr[i] = -1
            else:  # Was Bull
                if close_prices[i] < fl[i]:
                    tr[i] = -1  # Switch to Bear
                else:
                    tr[i] = 1
                    
        # SuperTrend line: Lower band when Bull, Upper band when Bear
        supertrend = np.where(tr == 1, fl, fu)
        
        df['SuperTrend'] = supertrend
        df['SuperTrend_Trend'] = tr  # 1=Bull, -1=Bear

    @staticmethod
    def _calculate_smc(df: pd.DataFrame, left=10, right=10):
        # Issue 3 Fix: Correct Rolling Window Logic
        # We use a centered rolling window logic shifted to the confirmation time.
        # Pivot at T is the max of [T-L, T+R].
        # Confirmed at T+R.
        # We want to identify if T-R was the max of [T-2R, T].
        # Or simpler:
        # 1. Compute rolling max centered.
        # 2. Shift the boolean result to the confirmation time.
        
        window = left + right + 1
        
        # Using rolling with center=True computes the max over [i-R, i+R] at index i.
        # If df['high'][i] == max([i-R, i+R]), then i is a pivot.
        # But we only know this at i+R.
        # so we shift the boolean signal forward by R.
        # This aligns the confirmation with "now".
        
        # Note: rolling(center=True) requires standard index or handling.
        
        is_pivot_high_raw = (df['high'] == df['high'].rolling(window=window, center=True).max())
        is_pivot_low_raw = (df['low'] == df['low'].rolling(window=window, center=True).min())
        
        is_pivot_high = is_pivot_high_raw.shift(right)
        is_pivot_low = is_pivot_low_raw.shift(right)
        
        # We want the LEVEL of the pivot, available from the moment it is confirmed (current time)
        # Forward fill the last confirmed pivot level
        last_pivot_high = df['high'].shift(right).where(is_pivot_high).ffill()
        last_pivot_low = df['low'].shift(right).where(is_pivot_low).ffill()
        
        df['SMC_SwingHigh'] = last_pivot_high
        df['SMC_SwingLow'] = last_pivot_low

    @staticmethod
    def evaluate_condition(row: pd.Series, condition_str: str) -> bool:
        """
        Evaluates a single boolean condition for a specific row.
        Example: "close > MA20 and RSI14 < 30"
        """
        try:
            # Replace &&, || with and, or for Python eval
            safe_cond = condition_str.replace('&&', ' and ').replace('||', ' or ')
            
            # Additional pre-calc calls inside evaluate not supported, must be pre-calc in parse
            # But we can handle dynamic attributes if we ensure columns exist.
            
            # Map variable names to row values
            # Simply usage: standard python eval with row as locals
            # Note: This requires the variables (MA20, etc.) to be valid identifiers in the row
            return eval(safe_cond, {}, row.to_dict())
        except Exception as e:
            # print(f"Eval Error: {e} | {condition_str}")
            return False

    @staticmethod
    def _calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def check_signal(df: pd.DataFrame, idx: int, buy_condition: str, sell_condition: str) -> str:
        """
        Checks signal for a specific index (day).
        """
        if idx < 0 or idx >= len(df): return 'hold'
        
        row = df.iloc[idx]
        
        # Check Sell first (Stop loss / Take profit usually priority, or Strategy Exit)
        if sell_condition and StrategyParser.evaluate_condition(row, sell_condition):
            return 'sell'
            
        # Check Buy
        if buy_condition and StrategyParser.evaluate_condition(row, buy_condition):
            return 'buy'
            
        return 'hold'
