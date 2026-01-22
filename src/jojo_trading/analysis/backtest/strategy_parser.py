
import pandas as pd
import numpy as np
import re
from typing import Dict, Any

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
    def evaluate_condition(row: pd.Series, condition_str: str) -> bool:
        """
        Evaluates a single boolean condition for a specific row.
        Example: "close > MA20 and RSI14 < 30"
        """
        try:
            # Replace &&, || with and, or for Python eval
            safe_cond = condition_str.replace('&&', ' and ').replace('||', ' or ')
            
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
