
import yfinance as yf
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class YFinanceFetcher:
    """
    專門負責從 Yahoo Finance 獲取台股數據的元件。
    作為 FinMind 的互補來源，解決 API 限制問題。
    """
    
    @staticmethod
    def _fetch_ticker(stock_code: str) -> Optional[yf.Ticker]:
        """
        嘗試獲取有效的 Ticker 對象 (自動嘗試 .TW 和 .TWO)
        """
        for suffix in ['.TW', '.TWO']:
            try:
                ticker_str = f"{stock_code}{suffix}"
                ticker = yf.Ticker(ticker_str)
                # 簡單驗證有效性: 檢查是否有歷史數據
                # 注意: info 屬性有時會很慢，history 比較快
                hist = ticker.history(period="1d")
                if not hist.empty:
                    # logger.info(f"Found valid ticker: {ticker_str}")
                    return ticker
            except Exception:
                continue
        return None

    @staticmethod
    def get_stock_price(stock_code: str, period: str = "1mo") -> float:
        """
        獲取最新股價
        """
        try:
            stock = YFinanceFetcher._fetch_ticker(stock_code)
            if not stock:
                logger.warning(f"No valid Yahoo Finance ticker found for {stock_code}")
                return None
                
            hist = stock.history(period=period)
            if not hist.empty:
                return hist.iloc[-1]['Close']
            return None
        except Exception as e:
            logger.error(f"YFinance price fetch error for {stock_code}: {e}")
            return None

    @staticmethod
    def get_quote(stock_code: str) -> Optional[dict]:
        """
        獲取完整報價 (Open, High, Low, Close, Volume, PrevClose)
        """
        try:
            stock = YFinanceFetcher._fetch_ticker(stock_code)
            if not stock: return None
            
            # Fetch 5 days to ensure we get prev close even after weekend/holiday
            hist = stock.history(period="5d")
            if hist.empty: return None
            
            current = hist.iloc[-1]
            data = {
                'price': float(current['Close']),
                'high': float(current['High']),
                'low': float(current['Low']),
                'volume': int(current['Volume']),
                'prev_close': None
            }
            
            if len(hist) >= 2:
                data['prev_close'] = float(hist.iloc[-2]['Close'])
                
            return data
        except Exception as e:
            logger.error(f"Quote error {stock_code}: {e}")
            return None

    @staticmethod
    def get_price_history(stock_code: str, period: str = "6mo") -> Optional[pd.Series]:
        """
        獲取歷史股價 (收盤價 Series)
        """
        try:
            stock = YFinanceFetcher._fetch_ticker(stock_code)
            if not stock:
                return None
            
            hist = stock.history(period=period)
            if not hist.empty:
                return hist['Close']
            return None
        except Exception as e:
            logger.error(f"YFinance history fetch error for {stock_code}: {e}")
            return None

    @staticmethod
    def get_history_ohlc(stock_code: str, period: str = "6mo") -> Optional[pd.DataFrame]:
        """
        獲取歷史 OHLCV 數據 (DataFrame)
        """
        try:
            stock = YFinanceFetcher._fetch_ticker(stock_code)
            if not stock: return None
            
            hist = stock.history(period=period)
            if hist.empty: return None
            
            # Ensure index is DatetimeIndex
            # yfinance usually returns DatetimeIndex with timezone
            return hist[['Open', 'High', 'Low', 'Close', 'Volume']]
            
        except Exception as e:
            logger.error(f"YFinance OHLC fetch error {stock_code}: {e}")
            return None

    @staticmethod
    def get_financial_data(stock_code: str):
        """
        獲取財務數據 (EPS, 營收, 淨利, FCF)
        """
        try:
            stock = YFinanceFetcher._fetch_ticker(stock_code)
            if not stock:
                return None
                
            info = stock.info
            
            # 基礎資訊
            shares = info.get('sharesOutstanding')
            market_cap = info.get('marketCap')
            
            # 財務報表
            inc = stock.income_stmt
            bs = stock.balance_sheet
            cf = stock.cashflow
            
            data = {
                "shares_outstanding": shares,
                "market_cap": market_cap,
                "net_income": None,
                "revenue": None,
                "fcf": None,
                "cash": None,
                "capex": None,
                "depreciation": None,
                "source": "yfinance"
            }
            
            if not inc.empty:
                # 嘗試獲取最新年度/季度的淨利
                # yfinance 通常返回 TTM 或最近年度
                if 'Net Income' in inc.index:
                    data['net_income'] = inc.loc['Net Income'].iloc[0]
                if 'Total Revenue' in inc.index:
                    data['revenue'] = inc.loc['Total Revenue'].iloc[0]
                    
            if not bs.empty:
                if 'Cash And Cash Equivalents' in bs.index:
                    data['cash'] = bs.loc['Cash And Cash Equivalents'].iloc[0]
                    
            if not cf.empty:
                if 'Free Cash Flow' in cf.index:
                    data['fcf'] = cf.loc['Free Cash Flow'].iloc[0]
                
                if 'Capital Expenditure' in cf.index:
                    data['capex'] = cf.loc['Capital Expenditure'].iloc[0]
                    
                # 嘗試獲取折舊 (通常在現金流量表的 Operating Activities 中)
                if 'Depreciation And Amortization' in cf.index:
                    data['depreciation'] = cf.loc['Depreciation And Amortization'].iloc[0]
                elif 'Depreciation' in cf.index:
                    data['depreciation'] = cf.loc['Depreciation'].iloc[0]

                # 如果 FCF 沒抓到，嘗試手動計算
                if data['fcf'] is None and 'Operating Cash Flow' in cf.index and data['capex'] is not None:
                    ocf = cf.loc['Operating Cash Flow'].iloc[0]
                    data['fcf'] = ocf + data['capex'] # Capex is usually negative in yfinance
            
            return data
            
        except Exception as e:
            logger.error(f"YFinance financial fetch error for {stock_code}: {e}")
            return None
