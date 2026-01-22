
import shioaji as sj
import os
from dotenv import load_dotenv
import pandas as pd

def inspect_futures_margin_data():
    load_dotenv()
    print("Connecting to Shioaji...")
    api = sj.Shioaji(simulation=False)
    api.login(os.getenv('SHIOAJI_API_KEY'), os.getenv('SHIOAJI_SECRET_KEY'))
    
    # Get futures account
    fut_acc = None
    for acc in api.list_accounts():
        if 'Future' in str(acc.account_type):
            fut_acc = acc
            break
            
    if not fut_acc:
        print("No Futures Account found.")
        return

    print(f"Using Futures Account: {fut_acc.account_id}")

    # 1. Check Margin / Equity
    # Note: different versions use different calls. Common is api.margin() or api.get_account_margin()
    try:
        print("\n--- Fetching Margin/Equity Info ---")
        # Trying api.margin first (returns a Pydantic model usually)
        margin_info = api.margin(fut_acc)
        print(margin_info)
        
        # Check specific fields like 'equity', 'available_margin', etc.
        # print(f"Equity: {margin_info.equity}")
    except Exception as e:
        print(f"api.margin() failed: {e}")

    # 2. Check specific contract margin data?
    # Shioaji doesn't always provide "Margin Requirements" per contract dynamically via API easily.
    # Usually we need to hardcode or scrape.
    # But let's check API docs or available methods if any.
    
if __name__ == "__main__":
    inspect_futures_margin_data()
