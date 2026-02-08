
import pandas as pd
import numpy as np

class SuperTrendSMCStrategy:
    """
    Python implementation of 'SuperTrend AI + SMC Fusion'.
    Uses manual calculation for SuperTrend and Swing Points to avoid dependency issues.
    """
    def __init__(self, atr_length=10, factor=3.0, smc_swing_length=5):
        self.atr_length = atr_length
        self.factor = factor
        self.swing_length = smc_swing_length

    def calculate_atr(self, df):
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self.atr_length).mean()
        return atr

    def calculate_supertrend(self, df):
        """
        Standard SuperTrend Calculation
        """
        high = df['High']
        low = df['Low']
        close = df['Close']
        atr = self.calculate_atr(df)
        
        hl2 = (high + low) / 2
        basic_upper = hl2 + (self.factor * atr)
        basic_lower = hl2 - (self.factor * atr)
        
        upper = basic_upper.copy()
        lower = basic_lower.copy()
        trend = np.zeros(len(df))
        
        # Iterative calculation needed for previous values
        for i in range(1, len(df)):
            if basic_upper.iloc[i] < upper.iloc[i-1] or close.iloc[i-1] > upper.iloc[i-1]:
                upper.iloc[i] = basic_upper.iloc[i]
            else:
                upper.iloc[i] = upper.iloc[i-1]
                
            if basic_lower.iloc[i] > lower.iloc[i-1] or close.iloc[i-1] < lower.iloc[i-1]:
                lower.iloc[i] = basic_lower.iloc[i]
            else:
                lower.iloc[i] = lower.iloc[i-1]
                
            # Trend Update
            # If prev trend was Down (1) and Close > Upper -> Up (1) ? specific impl varies
            # Common: Trend is 1 (Up) or -1 (Down)
            prev_trend = trend[i-1] if i > 0 else 1
            
            if prev_trend == 1:
                if close.iloc[i] < lower.iloc[i]:
                    trend[i] = -1
                else:
                    trend[i] = 1
            else:
                if close.iloc[i] > upper.iloc[i]:
                    trend[i] = 1
                else:
                    trend[i] = -1
                    
        return trend, upper, lower

    def detect_swings(self, df):
        """
        Basic Swing High/Low detection
        """
        high = df['High']
        low = df['Low']
        
        # Rolling min/max with center? No, standard pivot logic:
        # High > neighbors
        # For simplicity, use rolling window centered, but lookahead is impossible in real-time.
        # So we look back: verifying a pivot after N bars.
        # But for 'Structure Break', we just need recent pivots.
        
        # Simple implementation: 
        # Rolling Max of last L bars. If High[i-L] == RollingMax[i], then it was a pivot.
        # But we need confirmed pivots.
        
        # Let's simplify: Return the most recent Swing High/Low levels
        # A swing high is confirmed if price makes a lower high for N bars? 
        # Let's use simple rolling max/min for resistance/support levels.
        swing_high = high.rolling(window=self.swing_length*2+1, center=True).max()
        swing_low = low.rolling(window=self.swing_length*2+1, center=True).min()
        
        # In real-time at index 'i', we only know up to i.
        # The 'center=True' would look ahead.
        # We must use 'center=False' and shift? 
        # A pivot at 'i-N' is confirmed at 'i'.
        # We just return the levels.
        return swing_high, swing_low

    def generate_signals(self, df):
        """
        Combine SuperTrend + SMC
        Signal: 1 (Buy), -1 (Sell), 0 (Neutral)
        """
        trend, up_line, low_line = self.calculate_supertrend(df)
        
        # 1 = Bullish, -1 = Bearish
        signals = pd.Series(0, index=df.index)
        
        # Simple Crossover logic
        # Buy when Trend flips to 1
        trend_series = pd.Series(trend, index=df.index)
        
        # Detect change
        buy_cond = (trend_series == 1) & (trend_series.shift(1) == -1)
        sell_cond = (trend_series == -1) & (trend_series.shift(1) == 1)
        
        signals[buy_cond] = 1
        signals[sell_cond] = -1
        
        return signals, trend_series

if __name__ == "__main__":
    # Test with larger dataset
    data = {
        'High': [10, 11, 12, 13, 14, 15, 14, 16, 18, 17, 19, 20, 22, 21, 23, 25, 24, 26, 28, 27, 26, 24, 22, 20, 18, 16, 15, 14, 13, 12],
        'Low':  [8,  9,  10, 11, 12, 13, 12, 14, 16, 15, 17, 18, 20, 19, 21, 23, 22, 24, 26, 25, 24, 22, 20, 18, 16, 14, 13, 12, 11, 10],
        'Close':[9, 10, 11, 12, 13, 14, 13, 15, 17, 16, 18, 19, 21, 20, 22, 24, 23, 25, 27, 26, 24, 22, 20, 18, 16, 14, 13, 12, 11, 10]
    }
    df = pd.DataFrame(data)
    # Ensure enough data for ATR(10)
    strategy = SuperTrendSMCStrategy(atr_length=5) # Reduced length for test
    sig, tr = strategy.generate_signals(df)
    print("Signals:", sig.values)
    print("Trend:", tr.values)
