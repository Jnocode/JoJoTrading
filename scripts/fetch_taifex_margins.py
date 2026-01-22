
import pandas as pd
import requests

def fetch_margins():
    url = "https://www.taifex.com.tw/cht/5/indexMarging"
    print(f"Fetching {url}...")
    
    try:
        # Use pandas directly (it uses lxml/bs4 under hood)
        dfs = pd.read_html(url, encoding='utf-8')
        print(f"Found {len(dfs)} tables.")
        
        # Usually the main table is the first or second large one
        for i, df in enumerate(dfs):
            print(f"\n--- Table {i} ---")
            print(df.head())
            
            # Check if columns indicate margin data
            # Typically: "商品名稱", "結算保證金", "維持保證金", "原始保證金"
            if any("原始保證金" in str(c) for c in df.columns):
                print("✅ Found Margin Table!")
                # Clean up and print relevant rows
                # Filter for TX (臺股期貨), MTX (小型臺指), TMF (微型臺指)?
                # Note: Scraped names might be "臺股期貨 (TX)", etc.
                return df
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_margins()
