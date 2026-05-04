import pandas as pd
from FinMind.data import DataLoader
import datetime
from typing import Optional, Dict
from jojo_trading.core.stock_database import StockDatabase

class FinMindFetcher:
    """
    Fetcher for Taiwan Stock Data using FinMind API.
    Focus: Institutional Chips (Three Big Legal Persons)
    """
    def __init__(self):
        self.loader = DataLoader() # FinMind DataLoader
        self._try_login()
        
    def _try_login(self):
        """Attempt to login using settings from DB"""
        try:
            db = StockDatabase()
            token = db.get_setting("FINMIND_API_TOKEN")
            user = db.get_setting("FINMIND_USER_ID")
            pwd = db.get_setting("FINMIND_PASSWORD")
            
            if token:
                # Prefer Token login if available
                # print(f"🔑 Logging into FinMind with Token...")
                self.loader.login_by_token(api_token=token)
            elif user and pwd:
                # print(f"🔑 Logging into FinMind with User/Pass...")
                self.loader.login(user_id=user, password=pwd)
            else:
                print("ℹ️ FinMind: Running in Guest Mode (Rate Limited)")
                
        except Exception as e:
            # print(f"⚠️ FinMind Login Warning: {e}")
            pass

    def get_institutional_data(self, stock_code: str, days: int = 365) -> pd.DataFrame:
        """
        Fetch Institutional Investors' Buy/Sell Data.
        
        :param stock_code: Stock ID (e.g. '2330')
        :param days: Number of days to look back
        :return: DataFrame with columns ['date', 'Foreign_Buy', 'Investment_Trust_Buy', 'Dealer_Buy']
                 Note: Values are Net Buy/Sell (Buy - Sell) in shares (usually).
        """
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            # Dataset: TaiwanStockInstitutionalInvestors
            df = self.loader.taiwan_stock_institutional_investors(
                stock_id=stock_code,
                start_date=start_str,
                end_date=end_str
            )
            
            if df.empty:
                return pd.DataFrame()
                
            # Pivot or aggregate to get simple columns per date
            # FinMind returns: date, stock_id, name (Foreign_Investor, etc.), buy, sell
            # We want Net Buy per category
            
            # Categories in FinMind:
            # 'Foreign_Investor' (外資)
            # 'Investment_Trust' (投信)
            # 'Dealer' (自營商) (Sometimes split into Proprietary/Hedging)
            
            # Calculate Net Buy (buy - sell)
            df['net_buy'] = df['buy'] - df['sell']
            
            # Pivot: Date x Name -> Net Buy
            pivot_df = df.pivot_table(
                index='date', 
                columns='name', 
                values='net_buy', 
                aggfunc='sum'
            ).fillna(0)
            
            # Rename columns to standardized English IDs
            # Typical FinMind names: 'Foreign_Investor', 'Investment_Trust', 'Dealer_Self', 'Dealer_Hedging'
            # We map specific keywords
            
            column_map = {
                'Foreign_Investor': 'Foreign_Buy',
                'Investment_Trust': 'IT_Buy', # Investment Trust
                'Dealer': 'Dealer_Buy',
                'Dealer_Self': 'Dealer_Buy', # Merge for simplicity? Or keep separate?
                'Dealer_Hedging': 'Dealer_Buy'
            }
            
            # Sum up Dealers if multiple columns exist for them?
            # Let's keep it simple first
            
            new_cols = []
            for col in pivot_df.columns:
                mapped = col
                if 'Foreign' in col: mapped = 'Foreign_Buy'
                elif 'Trust' in col: mapped = 'IT_Buy'
                elif 'Dealer' in col: mapped = 'Dealer_Buy'
                new_cols.append(mapped)
                
            # If duplicates (e.g. Dealer Self + Hedging), we might need to group sum on columns?
            # Creating a clean DF manually
            
            final_df = pd.DataFrame(index=pivot_df.index)
            final_df['Foreign_Buy'] = 0
            final_df['IT_Buy'] = 0
            final_df['Dealer_Buy'] = 0
            
            for col in pivot_df.columns:
                if 'Foreign' in col:
                    final_df['Foreign_Buy'] += pivot_df[col]
                elif 'Trust' in col:
                    final_df['IT_Buy'] += pivot_df[col]
                elif 'Dealer' in col:
                    final_df['Dealer_Buy'] += pivot_df[col]
                    
            final_df = final_df.reset_index()
            final_df['date'] = pd.to_datetime(final_df['date'])
            
            return final_df
            
        except Exception as e:
            print(f"❌ FinMind Fetch Error: {e}")
            return pd.DataFrame()

    def get_monthly_revenue(self, stock_code: str, months: int = 24) -> pd.DataFrame:
        """
        Fetch Monthly Revenue Data.
        Returns columns: ['date', 'revenue', 'revenue_month', 'revenue_year', 'revenue_yoy']
        """
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=months*30)
        
        try:
            # Dataset: TaiwanStockMonthRevenue
            df = self.loader.taiwan_stock_month_revenue(
                stock_id=stock_code,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            if df.empty:
                return pd.DataFrame()
                
            # Keep relevant columns
            # FinMind cols: date, stock_id, revenue, revenue_month, revenue_year
            # Note: 'date' is usually the 1st of the month covering the revenue
            # e.g., 2023-01-01 for Jan 2023 revenue.
            
            # Use 'revenue_year' and 'revenue_month' to calculate YoY if not present
            # But simpler to just return data first
            
            # Simple feature engineering: YoY Growth
            # Note: FinMind might not provide percentage directly, often just raw numbers
            
            # We will calculate YoY manually later or here if sufficient history
            # Let's return raw data primarily
            
            # Rename for clarity
            df = df.rename(columns={'revenue': 'Revenue'})
            
            # Select columns
            cols = ['date', 'Revenue']
            return df[cols]
            
        except Exception as e:
            print(f"❌ FinMind Revenue Fetch Error: {e}")
            return pd.DataFrame()
    def get_stock_price(self, stock_code: str, days: int = 365) -> pd.DataFrame:
        """
        Fetch OHLCV Data.
        """
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        
        try:
            # Dataset: TaiwanStockPrice
            df = self.loader.taiwan_stock_daily(
                stock_id=stock_code,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # FinMind columns: date, stock_id, Trading_Volume, Trading_money, open, max, min, close, spread, Trading_turnover
            # Rename mapping
            rename_map = {
                'date': 'Date',
                'open': 'Open',
                'max': 'High',
                'min': 'Low',
                'close': 'Close',
                'Trading_Volume': 'Volume'
            }
            
            df = df.rename(columns=rename_map)
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Ensure proper types
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            # Return only existing columns
            cols = [c for c in cols if c in df.columns]
            
            # Set index to Date
            df = df.set_index('Date')
            
            # Select columns (excluding Date since it's index)
            final_cols = [c for c in cols if c != 'Date' and c in df.columns]
            return df[final_cols]
            
        except Exception as e:
            print(f"❌ FinMind Price Fetch Error: {e}")
            return pd.DataFrame()

    def get_eps_data(self, stock_code: str, quarters: int = 4) -> pd.DataFrame:
        """
        Placeholder for EPS data fetch to prevent AttributeError in data adapter.
        """
        return pd.DataFrame()


if __name__ == "__main__":
    # Test
    f = FinMindFetcher()
    print("Fetching Chips...")
    df = f.get_institutional_data("2330", days=10)
    print(df.tail())
    
    print("Fetching Revenue...")
    rev = f.get_monthly_revenue("2330", months=6)
    print(rev.tail())
    
    print("Fetching EPS...")
    eps = f.get_eps_data("2330", quarters=4)
    print(eps.tail())
