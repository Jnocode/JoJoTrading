import pandas as pd
import numpy as np

class RiskRadar:
    """
    Risk Radar System for calculating market risk scores based on Volatility,
    Volume, and other metrics. Based on OpenClaw's Pine Script logic.
    """
    
    @staticmethod
    def calculate_risk(df: pd.DataFrame, 
                       vix_length=14, 
                       vix_ma_length=50, 
                       volume_ma_length=20) -> pd.DataFrame:
        """
        Calculates Risk Score (0-10) and adds it to the DataFrame.
        """
        # --- 1. Volatility Risk (VIX equivalent) ---
        # Calculate ATR as VIX proxy
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        current_atr = true_range.rolling(vix_length).mean()
        atr_ma = current_atr.rolling(vix_ma_length).mean()
        
        # Volatility Ratio
        volatility_ratio = current_atr / atr_ma
        
        # --- 2. Volume Risk ---
        volume_ma = df['volume'].rolling(volume_ma_length).mean()
        volume_ratio = df['volume'] / volume_ma
        
        # --- Risk Scoring (0-10) ---
        risk_score = pd.Series(0.0, index=df.index)
        
        # Volatility Panic (+2 to +3)
        risk_score += np.where(volatility_ratio > 3.0, 3.0, 
                               np.where(volatility_ratio > 2.0, 2.0, 
                                        np.where(volatility_ratio > 1.5, 1.0, 0.0)))
                                        
        # Volume Spike (+1)
        risk_score += np.where(volume_ratio > 3.0, 1.0, 0.0)
        
        # Tail Risk / Crash Setup (Simplified Skew proxy using Returns)
        # Low returns relative to volatility
        returns = np.log(df['close'] / df['close'].shift())
        mean_return = returns.rolling(20).mean()
        std_return = returns.rolling(20).std()
        
        # If returns are significantly negative (Crash Setup)
        z_score = (returns - mean_return) / std_return
        risk_score += np.where(z_score < -2.0, 2.0, 0.0)

        df['Risk_Score'] = risk_score.clip(upper=10.0).fillna(0)
        
        return df

    @staticmethod
    def apply_risk_filter(df: pd.DataFrame, max_risk=6.0) -> pd.DataFrame:
        """
        Filters out signals where Risk Score exceeds the maximum allowed.
        Adds 'Risk_Allowed' boolean column.
        """
        if 'Risk_Score' not in df.columns:
            df = RiskRadar.calculate_risk(df)
            
        df['Risk_Allowed'] = df['Risk_Score'] < max_risk
        return df
