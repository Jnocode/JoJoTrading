
import yfinance as yf
import pandas as pd
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BacktestDataAdapter:
    """
    Adapter to fetch and format data for the Backtest Engine.
    Standardizes output to: date, open, high, low, close, volume
    """
    
    @staticmethod
    def get_kline_data(stock_code: str, period: str = "2y", interval: str = "1d") -> Dict[str, pd.DataFrame]:
        import datetime
        logger.info(f"Fetching Backtest Data: {stock_code}, Period={period}, Interval={interval}")
        
        # 1. Check if we should use Shioaji (for Intraday TW Stocks)
        # Conditions: Interval is minute-based ('m' in interval) and 'mo' not in interval
        use_shioaji = 'm' in interval.lower() and 'mo' not in interval.lower()
        
        if use_shioaji:
            try:
                from jojo_trading.core.shioaji_connector import ShioajiConnector
                connector = ShioajiConnector()
                if connector.is_connected:
                    logger.info(f"Using Shioaji for unrestricted minute data: {stock_code}")
                    
                    end_date_obj = datetime.datetime.now()
                    start_date_obj = end_date_obj - datetime.timedelta(days=60) # Default
                    
                    if period == '2y' or period == 'max':
                        start_date_obj = end_date_obj - datetime.timedelta(days=365)
                        
                    sj_code = stock_code.replace('.TW', '').replace('.TWO', '')
                    
                    df = connector.get_kbars(
                        sj_code, 
                        start_date=start_date_obj.strftime("%Y-%m-%d"), 
                        end_date=end_date_obj.strftime("%Y-%m-%d")
                    )
                    
                    if not df.empty:
                        df.set_index('date', inplace=True)
                        pandas_freq = interval.replace('m', 'T').replace('h', 'H')
                        
                        if pandas_freq != '1T':
                            agg_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
                            try:
                                df = df.resample(pandas_freq).agg(agg_dict).dropna()
                            except:
                                pass # formatting might be tricky
                        
                        df = df.reset_index()
                        return {'daily': df}
            except Exception as e:
                logger.error(f"Shioaji fetch failed, falling back: {e}")

        # 2. Fallback to YFinance
        try:
            ticker_str = stock_code
            if not (stock_code.endswith('.TW') or stock_code.endswith('.TWO')):
                ticker_str = f"{stock_code}.TW"
            
            ticker = yf.Ticker(ticker_str)
            # Adjust period for intraday if needed
            yf_period = "max"
            if interval in ['1m', '5m', '15m', '30m', '60m', '1h']:
                yf_period = "60d" 
            
            df = ticker.history(period=yf_period, interval=interval)
            
            if df.empty:
                # Try .TWO
                ticker_str = f"{stock_code}.TWO"
                ticker = yf.Ticker(ticker_str)
                df = ticker.history(period=yf_period, interval=interval)
            
            if df.empty:
                logger.error(f"No data found for {stock_code}")
                return {}

            # Reset index to get Date as column
            df = df.reset_index()
            
            # Standardize columns
            # YFinance columns: Date, Open, High, Low, Close, Volume, Dividends, Stock Splits
            # Intraday might be Datetime
            df.columns = [c.lower() for c in df.columns]
            
            if 'datetime' in df.columns:
                df.rename(columns={'datetime': 'date'}, inplace=True)
            
            # Ensure 'date' is datetime (remove timezone if present for easier comparison)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            
            # Select required columns
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(c in df.columns for c in required_cols):
                logger.error(f"Missing columns in YFinance data: {df.columns}")
                return {}
            
            final_df = df[required_cols].copy()
            
            # Sort by date
            final_df = final_df.sort_values('date').reset_index(drop=True)

            # --- Merge FinMind Institutional Data ---
            try:
                # Optimized: Only fetch if Daily interval (Chips are daily)
                if 'd' in interval.lower():
                    from jojo_trading.core.finmind_fetcher import FinMindFetcher
                    fm = FinMindFetcher()
                    
                    # Clean code for FinMind (remove .TW)
                    fm_code = stock_code.replace('.TW', '').replace('.TWO', '')
                    
                    # Fetch enough history to cover likely backtest range (e.g. 2 years)
                    # Ideally we match the period parameter
                    lookback_days = 730 # approx 2y
                    if period == 'max': lookback_days = 3650
                    elif period == '5y': lookback_days = 1825
                    elif period == '1y': lookback_days = 365
                    
                    chips_df = fm.get_institutional_data(fm_code, days=lookback_days)
                    
                    if not chips_df.empty:
                        # Merge on date
                        # Ensure date types match
                        chips_df['date'] = pd.to_datetime(chips_df['date']).dt.tz_localize(None)
                        final_df = pd.merge(final_df, chips_df, on='date', how='left')
                        
                        # Fill NaN with 0 (no data = neutral/0 net buy)
                        final_df['Foreign_Buy'] = final_df['Foreign_Buy'].fillna(0)
                        final_df['IT_Buy'] = final_df['IT_Buy'].fillna(0)
                        final_df['Dealer_Buy'] = final_df['Dealer_Buy'].fillna(0)
                        
                        logger.info(f"Merged FinMind Chips Data for {stock_code}")
                        
                    # --- Revenue & EPS (Fundamental) ---
                    # 1. Revenue
                    rev_df = fm.get_monthly_revenue(fm_code, months=lookback_days//30 + 12) # +12 for YoY
                    if not rev_df.empty:
                        rev_df['date'] = pd.to_datetime(rev_df['date'])
                        # Calculate YoY
                        rev_df = rev_df.sort_values('date')
                        rev_df['Revenue_YOY'] = rev_df['Revenue'].pct_change(periods=12) * 100
                        
                        # Shift dates to simulate reporting lag (Avoid Look-Ahead Bias)
                        # Revenue released ~10th of next month. Current date is 1st.
                        # Shift: +1 Month + 10 Days
                        rev_df['date'] = rev_df['date'] + pd.DateOffset(months=1, days=10)
                        
                        # Merge using asof merge or left join + ffill
                        # Since final_df is daily, we can use merge_asof if sorted
                        final_df = final_df.sort_values('date')
                        rev_df = rev_df.sort_values('date')
                        
                        final_df = pd.merge_asof(final_df, rev_df[['date', 'Revenue', 'Revenue_YOY']], on='date', direction='backward')
                        
                    # 2. EPS
                    eps_df = fm.get_eps_data(fm_code, quarters=lookback_days//90 + 5)
                    if not eps_df.empty:
                        eps_df['date'] = pd.to_datetime(eps_df['date'])
                        # Shift: Q1 (Mar 31) -> May 15 (approx +45 days)
                        eps_df['date'] = eps_df['date'] + pd.DateOffset(days=45)
                        
                        eps_df = eps_df.sort_values('date')
                        final_df = pd.merge_asof(final_df, eps_df[['date', 'EPS']], on='date', direction='backward')
                        
            except Exception as fe:
                logger.warning(f"Failed to merge FinMind data: {fe}")
            # ---------------------------------------

            return {
                'daily': final_df
                # 'weekly': ... (resample if needed)
            }
            
        except Exception as e:
            logger.error(f"Data Adapter Error: {e}")
            return {}
