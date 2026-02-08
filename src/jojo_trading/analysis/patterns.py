import pandas as pd
import numpy as np
from typing import Tuple, Optional

class PatternRecognizer:
    """
    技術分析形態識別器
    """

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        計算基礎技術指標
        """
        if len(df) < 60:
            return df
            
        # MA
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

    @staticmethod
    def check_golden_cross(df: pd.DataFrame, short_window=5, long_window=20) -> bool:
        """
        檢查黃金交叉 (短均線上穿長均線)
        """
        if len(df) < long_window + 2:
            return False
            
        short_ma = df['Close'].rolling(window=short_window).mean()
        long_ma = df['Close'].rolling(window=long_window).mean()
        
        # 昨天短均 < 長均 且 今天短均 > 長均
        return (short_ma.iloc[-2] < long_ma.iloc[-2]) and (short_ma.iloc[-1] > long_ma.iloc[-1])

    @staticmethod
    def check_death_cross(df: pd.DataFrame, short_window=5, long_window=20) -> bool:
        """
        檢查死亡交叉 (短均線下穿長均線)
        """
        if len(df) < long_window + 2:
            return False
            
        short_ma = df['Close'].rolling(window=short_window).mean()
        long_ma = df['Close'].rolling(window=long_window).mean()
        
        return (short_ma.iloc[-2] > long_ma.iloc[-2]) and (short_ma.iloc[-1] < long_ma.iloc[-1])

    @staticmethod
    def check_double_bottom(df: pd.DataFrame, window=60, threshold=0.03) -> bool:
        """
        簡單的 W 底 (雙底) 識別
        概念：尋找區間內的兩個低點，它們的值相近，且中間有反彈
        """
        if len(df) < window:
            return False
            
        recent = df['Close'].tail(window)
        # 尋找兩個明顯的低谷 (這裡用簡單的演算法，實際需更複雜)
        # 1. 找出最低點
        min_idx = recent.idxmin()
        min_val = recent.min()
        
        # 如果最低點就是今天，可能還在跌，不算成形的W底
        if min_idx == recent.index[-1]:
            return False
            
        # 2. 尋找第二低點 (排除了最低點附近的日期)
        # 簡單起見，我們將區間分成兩半，看是否各有一個低點接近
        mid_point = len(recent) // 2
        
        part1 = recent.iloc[:mid_point]
        part2 = recent.iloc[mid_point:]
        
        min1 = part1.min()
        min2 = part2.min()
        
        if abs(min1 - min2) / min1 < threshold:
            # 兩個低點接近，且中間有漲起來 (中間的最大值大於低點一定比例)
            middle_max = recent.iloc[len(part1)//2 : len(recent)-len(part2)//2].max()
            if middle_max > min1 * (1 + threshold * 2):
                return True
                
        return False

    @staticmethod
    def check_rsi_oversold(df: pd.DataFrame, threshold=30) -> bool:
        """
        RSI 超賣 (< 30)
        """
        if 'RSI' not in df.columns:
            df = PatternRecognizer.calculate_indicators(df)
            
        if df['RSI'].empty:
            return False
            
        return df['RSI'].iloc[-1] < threshold

    @staticmethod
    def check_rsi_overbought(df: pd.DataFrame, threshold=70) -> bool:
        """
        RSI 超買 (> 70)
        """
        if 'RSI' not in df.columns:
            df = PatternRecognizer.calculate_indicators(df)
            
        if df['RSI'].empty:
            return False
            
        return df['RSI'].iloc[-1] > threshold

    @staticmethod
    def check_ma_breakthrough_bullish(df: pd.DataFrame) -> bool:
        """
        一陽穿三線 (多頭突破)
        定義：收盤價同時突破 5日, 10日, 20日均線
        俗稱：雖然用戶稱之為三陽開泰，但技術上這通常指「一陽穿三線」或「出水芙蓉」
        """
        if len(df) < 20:
            return False
            
        # 確保指標存在
        if 'MA5' not in df.columns:
            df = PatternRecognizer.calculate_indicators(df)
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 今天的收盤價大於三條均線
        cond_close_above = (latest['Close'] > latest['MA5']) and \
                           (latest['Close'] > latest['MA10']) and \
                           (latest['Close'] > latest['MA20'])
                           
        # 昨天的收盤價或今天的開盤價 至少低於其中幾條 (表示是穿越)
        # 嚴格定義：開盤價在三線之下 (實體穿越)
        cond_open_below = (latest['Open'] < latest['MA5']) and \
                          (latest['Open'] < latest['MA10']) and \
                          (latest['Open'] < latest['MA20'])
        
        return cond_close_above and cond_open_below

    @staticmethod
    def check_ma_breakthrough_bearish(df: pd.DataFrame) -> bool:
        """
        一陰穿三線 (空頭跌破 / 斷頭鍘刀)
        定義：收盤價同時跌破 5日, 10日, 20日均線
        """
        if len(df) < 20:
            return False
            
        if 'MA5' not in df.columns:
            df = PatternRecognizer.calculate_indicators(df)
            
        latest = df.iloc[-1]
        
        # 今天的收盤價小於三條均線
        cond_close_below = (latest['Close'] < latest['MA5']) and \
                           (latest['Close'] < latest['MA10']) and \
                           (latest['Close'] < latest['MA20'])
                           
        # 今天的開盤價大於三條均線 (實體向下穿越)
        cond_open_above = (latest['Open'] > latest['MA5']) and \
                          (latest['Open'] > latest['MA10']) and \
                          (latest['Open'] > latest['MA20'])
        
        return cond_close_below and cond_open_above

    @staticmethod
    def check_bullish_perfect_order(df: pd.DataFrame) -> bool:
        """
        四海游龍 (均線多頭排列)
        定義：5MA > 10MA > 20MA > 60MA
        象徵：股價如游龍般在四海(均線)之上遨遊，趨勢強勢向上
        """
        if len(df) < 60:
            return False
            
        if 'MA60' not in df.columns:
            df = PatternRecognizer.calculate_indicators(df)
            
        # 確保最後一天有值
        if pd.isna(df['MA60'].iloc[-1]):
            return False
            
        latest = df.iloc[-1]
        
        return (latest['MA5'] > latest['MA10']) and \
               (latest['MA10'] > latest['MA20']) and \
               (latest['MA20'] > latest['MA60'])

    @staticmethod
    def check_bearish_perfect_order(df: pd.DataFrame) -> bool:
        """
        四面楚歌 (均線空頭排列)
        定義：5MA < 10MA < 20MA < 60MA
        象徵：股價被四條均線層層壓制，上方壓力重重
        """
        if len(df) < 60:
            return False
            
        if 'MA60' not in df.columns:
            df = PatternRecognizer.calculate_indicators(df)

        if pd.isna(df['MA60'].iloc[-1]):
            return False
            
        latest = df.iloc[-1]
        
        return (latest['MA5'] < latest['MA10']) and \
               (latest['MA10'] < latest['MA20']) and \
               (latest['MA20'] < latest['MA60'])
