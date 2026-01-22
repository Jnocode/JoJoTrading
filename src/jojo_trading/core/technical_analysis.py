import pandas as pd
import numpy as np

class TechnicalAnalysis:
    """
    技術分析核心模組
    提供 RSI, MACD, MA, Bollinger Bands 等計算功能
    盡量只依賴 pandas/numpy，避免安裝困難的 ta-lib
    """

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """
        計算相對強弱指標 (RSI)
        返回最新一期的 RSI 值
        """
        if len(prices) < period + 1:
            return 50.0  # 數據不足返回中性值

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 處理除以零的情況
        rsi = rsi.fillna(100) # 若 loss 為 0，RSI 為 100
        
        return rsi.iloc[-1]

    @staticmethod
    def calculate_ma(prices: pd.Series, window: int) -> float:
        """
        計算簡單移動平均 (SMA)
        """
        if len(prices) < window:
            return prices.iloc[-1] if not prices.empty else 0.0
        
        return prices.rolling(window=window).mean().iloc[-1]

    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """
        計算 MACD 指標
        返回: {'macd': float, 'signal': float, 'hist': float}
        """
        if len(prices) < slow + signal:
            return {'macd': 0.0, 'signal': 0.0, 'hist': 0.0}

        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            'macd': macd_line.iloc[-1],
            'signal': signal_line.iloc[-1],
            'hist': histogram.iloc[-1]
        }

    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: int = 2) -> dict:
        """
        計算布林通道
        """
        if len(prices) < window:
            return {'upper': 0.0, 'middle': 0.0, 'lower': 0.0}

        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)

        return {
            'upper': upper_band.iloc[-1],
            'middle': sma.iloc[-1],
            'lower': lower_band.iloc[-1]
        }
