import pandas as pd
import numpy as np
import dataclasses
from typing import Optional, Dict, Literal

@dataclasses.dataclass
class PivotState:
    current_level: float = np.nan
    last_level: float = np.nan
    crossed: bool = False
    bar_index: int = 0
    bar_time: any = None

@dataclasses.dataclass
class TrailingExtremes:
    top: float = np.nan
    bottom: float = np.nan

class SMCStrategy:
    """
    Port of 'SuperTrend AI + SMC Fusion [LuxAlgo]' (Pure SMC Mode)
    Focuses on Market Structure (BOS), Swings, and Filters.
    """
    
    def __init__(self, config: Dict):
        # Configuration
        self.swings_length = config.get('swings_length', 60)
        self.use_structure_confirm = config.get('use_structure_confirm', True)
        self.confirm_bars = config.get('confirm_bars', 9)
        self.use_price_filter = config.get('use_price_filter', False)
        self.price_filter_percent = config.get('price_filter_percent', 30.0)
        
        # Risk Config
        self.use_atr_stop = config.get('use_atr_stop', True)
        self.atr_length = config.get('atr_length', 14)
        self.atr_mult = config.get('atr_mult', 3.0)
        
        # State Variables
        self.swing_high = PivotState()
        self.swing_low = PivotState()
        self.trailing = TrailingExtremes()
        self.swing_bias = 0 # 1=Bullish, -1=Bearish
        
        # Internal leg tracking
        self.last_leg_state = 0 # 0=Bearish Leg, 1=Bullish Leg

    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        high = df['High']
        low = df['Low']
        close = df['Close']
        prev_close = close.shift()
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        # Wilder's Smoothing (alpha = 1/n) matches Pine Script rma/atr
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        return atr

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze the dataframe and append strategy columns.
        Returns the dataframe with signals.
        """
        # Ensure sufficient data
        if len(df) < self.swings_length + 10:
            return df

        # 1. Pre-calculate TA Indicators
        # ATR
        df['ATR'] = self._calculate_atr(df, self.atr_length)
        
        # High/Low Rolling Windows for detecting new legs (Vectorized prep)
        # We need to know if high[size] > max(high of last size bars)
        # Shifted comparison: df['High'].shift(size) > df['High'].rolling(size).max()
        # Note: rolling(size).max() includes current bar. 
        # Pine: high[size] > ta.highest(high, size)
        # Python: df['High'].shift(self.swings_length) > df['High'].rolling(self.swings_length).max()
        
        size = self.swings_length
        # Max of the *recent* 'size' bars (excluding the one at 'size' ago if we shift properly)
        # In Pine at bar T: ta.highest(high, size) looks at T, T-1, ..., T-(size-1)
        # We compare it with T-size.
        
        df['Recent_Max'] = df['High'].rolling(window=size).max()
        df['Recent_Min'] = df['Low'].rolling(window=size).max() # Typo in plan? Pine uses ta.lowest(low, size)
        df['Recent_Min'] = df['Low'].rolling(window=size).min()

        df['Is_New_Leg_High'] = df['High'].shift(size) > df['Recent_Max']
        df['Is_New_Leg_Low']  = df['Low'].shift(size) < df['Recent_Min']
        
        # Initialize Output Columns
        df['Signal'] = 0 # 1=Buy, -1=Sell
        df['Stop_Loss'] = np.nan
        df['Comment'] = ""
        df['Swing_High_Level'] = np.nan
        df['Swing_Low_Level'] = np.nan
        df['Trend_Bias'] = 0

        # Iteration for Stateful Logic (Structure)
        # Access numpy arrays for speed
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values
        times = df.index # Assuming datetime index
        new_leg_highs = df['Is_New_Leg_High'].values
        new_leg_lows = df['Is_New_Leg_Low'].values
        atrs = df['ATR'].values
        
        n_rows = len(df)
        
        # Reset State
        self.swing_high = PivotState()
        self.swing_low = PivotState()
        self.trailing = TrailingExtremes(top=np.nan, bottom=np.nan)
        self.swing_bias = 0
        leg_state = 0 # 0=Bearish, 1=Bullish
        
        # We start iterating from 'size' index since we need lookback
        start_idx = size + 1
        
        for i in range(start_idx, n_rows):
            current_bar_time = times[i]
            
            # --- 1. Identify Legs (Structure Points) ---
            # Replicating Pine: leg(size) logic
            # var leg = 0
            # if newLegHigh -> leg := BEARISH_LEG (0)
            # else if newLegLow -> leg := BULLISH_LEG (1)
            
            is_new_high = new_leg_highs[i]
            is_new_low = new_leg_lows[i]
            
            current_leg = leg_state
            if is_new_high:
                current_leg = 0 # Bearish Leg
            elif is_new_low:
                current_leg = 1 # Bullish Leg
                
            # Check for Change
            start_of_bearish = (current_leg == 0 and leg_state != 0)
            start_of_bullish = (current_leg == 1 and leg_state != 1)
            
            leg_state = current_leg # Update state
            
            # --- 2. Update Pivots ---
            # If start of Bullish Leg -> We just finished a Bearish move, so a Low Pivot was confirmed?
            # Wait, Pine logic:
            # if startOfBullishLeg (leg changed to 1) -> implies we found a Low that broke the range?
            # Let's re-read Pine carefully:
            # newLegLow = low[size] < ta.lowest(low, size) -> detected a "Low" at size bars ago.
            # if newLegLow -> leg := BULLISH_LEG
            # if startOfNewLeg...
            # if pivotLow (startOfBullishLeg) -> Update swingLow
            
            # So: When we detect a New Leg Low, we update the Swing Low.
            # The Swing Low value is the Low at [i - size].
            
            if start_of_bullish:
                # Update Swing Low
                self.swing_low.last_level = self.swing_low.current_level
                self.swing_low.current_level = lows[i - size]
                self.swing_low.crossed = False
                self.swing_low.bar_index = i - size
                self.swing_low.bar_time = times[i - size]
                
                # Update Trailing
                self.trailing.bottom = self.swing_low.current_level
                
            elif start_of_bearish:
                # Update Swing High
                self.swing_high.last_level = self.swing_high.current_level
                self.swing_high.current_level = highs[i - size]
                self.swing_high.crossed = False
                self.swing_high.bar_index = i - size
                self.swing_high.bar_time = times[i - size]
                
                # Update Trailing
                self.trailing.top = self.swing_high.current_level

            # --- 3. Update Trailing Extremes ---
            # math.max(high, trailing.top)
            if not np.isnan(self.trailing.top):
                self.trailing.top = max(highs[i], self.trailing.top)
            if not np.isnan(self.trailing.bottom):
                self.trailing.bottom = min(lows[i], self.trailing.bottom)
                
            # --- 4. Detect Structure (BOS) ---
            bos_bullish = False
            bos_bearish = False
            
            if not np.isnan(self.swing_high.current_level) and not self.swing_high.crossed:
                if closes[i] > self.swing_high.current_level: # Crossover
                    self.swing_high.crossed = True
                    self.swing_bias = 1 # Bullish
                    bos_bullish = True
                    
            if not np.isnan(self.swing_low.current_level) and not self.swing_low.crossed:
                if closes[i] < self.swing_low.current_level: # Crossunder
                    self.swing_low.crossed = True
                    self.swing_bias = -1 # Bearish
                    bos_bearish = True

            # --- 5. Confirmation Logic ---
            entry_long = False
            entry_short = False
            
            if bos_bullish:
                # Check Confirmations
                # Time Confirm
                bars_since_swing = i - self.swing_high.bar_index
                time_ok = (not self.use_structure_confirm) or (bars_since_swing >= self.confirm_bars)
                
                # Price Filter (Discount Check)
                price_ok = True
                if self.use_price_filter and not np.isnan(self.trailing.top) and not np.isnan(self.trailing.bottom):
                    rnge = self.trailing.top - self.trailing.bottom
                    if rnge > 0:
                        pos = (closes[i] - self.trailing.bottom) / rnge * 100
                        if pos > self.price_filter_percent:
                            price_ok = False
                            
                if time_ok and price_ok:
                    entry_long = True
                    
            if bos_bearish:
                # Check Confirmations (Short usually doesn't need price filter in this strat default, but we follow config)
                bars_since_swing = i - self.swing_low.bar_index
                time_ok = (not self.use_structure_confirm) or (bars_since_swing >= self.confirm_bars)
                
                if time_ok:
                    entry_short = True

            # --- 6. Set Signals & State to DF ---
            if entry_long:
                df.at[times[i], 'Signal'] = 1
                df.at[times[i], 'Comment'] = "SMC Buy"
                # ATR Stop
                if self.use_atr_stop and not np.isnan(atrs[i]):
                     df.at[times[i], 'Stop_Loss'] = closes[i] - (atrs[i] * self.atr_mult)

            elif entry_short:
                df.at[times[i], 'Signal'] = -1
                df.at[times[i], 'Comment'] = "SMC Sell"
                # ATR Stop
                if self.use_atr_stop and not np.isnan(atrs[i]):
                     df.at[times[i], 'Stop_Loss'] = closes[i] + (atrs[i] * self.atr_mult)

            # Debug Columns
            df.at[times[i], 'Swing_High_Level'] = self.swing_high.current_level
            df.at[times[i], 'Swing_Low_Level'] = self.swing_low.current_level
            df.at[times[i], 'Trend_Bias'] = self.swing_bias
            
        return df

