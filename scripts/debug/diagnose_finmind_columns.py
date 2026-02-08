
import sys
import os
import pandas as pd
from src.jojo_trading.core.auto_data_fetcher import AutoDataFetcher

def diagnose_balance_sheet_columns(stock_code="2330"):
    print(f"🔍 Diagnosing Balance Sheet columns for {stock_code}...")
    
    fetcher = AutoDataFetcher()
    if not fetcher.data_handler:
        print("❌ DataHandler not initialized in fetcher!")
        return

    # Force fetch Balance Sheet using the fetcher's internal handler
    df_bs = fetcher.data_handler.fetch_finmind_financial_statement_data(
        stock_code, "2024-01-01", 'BalanceSheet'
    )
    
    if df_bs.empty:
        print("❌ No Balance Sheet data found!")
        return
        
    # Get latest date
    latest_date = df_bs['date'].max()
    print(f"📅 Latest Date: {latest_date}")
    
    # Filter for latest date
    latest_df = df_bs[df_bs['date'] == latest_date]
    
    print("\n📋 Balance Sheet Structure:")
    print(latest_df.head())
    print(f"Columns: {latest_df.columns.tolist()}")
    
    # Check if format is Long (type, value)
    if 'type' in latest_df.columns and 'value' in latest_df.columns:
        print("\n📋 Available Financial Items (Long Format):")
        unique_types = latest_df['type'].unique()
        for t in sorted(unique_types):
             val = latest_df[latest_df['type'] == t]['value'].iloc[0]
             print(f"  - {t}: {val}")
    else:
        # Wide format
        print("\n📋 All available columns (Wide Format):")
        all_cols = sorted(latest_df.columns.tolist())
        for col in all_cols:
            val = latest_df[col].iloc[0] if not latest_df.empty else "N/A"
            print(f"  - {col}: {val}")

if __name__ == "__main__":
    diagnose_balance_sheet_columns()
