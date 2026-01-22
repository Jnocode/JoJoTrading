
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from jojo_trading.core.stock_database import StockDatabase

class MarginManager:
    """
    Handles fetching and updating Futures Margin Requirements from TAIFEX.
    """
    
    URL = "https://www.taifex.com.tw/cht/5/indexMarging"
    
    @staticmethod
    def fetch_current_margins() -> List[Dict[str, Any]]:
        """
        Scrape TAIFEX website for latest margins.
        Returns list of dict: [{'symbol': 'TXF', 'initial': 100, ...}, ...]
        """
        results = []
        try:
            print(f"Fetching margins from {MarginManager.URL}...")
            dfs = pd.read_html(MarginManager.URL, encoding='utf-8')
            
            if not dfs:
                return []
                
            df = dfs[0] # Usually the first table
            
            # Map TAIFEX names to Symbols
            # 臺股期貨 -> TXF
            # 小型臺指 -> MXF
            # 微型臺指期貨 -> ZEF
            
            name_map = {
                '臺股期貨': 'TXF',
                '小型臺指': 'MXF',
                '微型臺指期貨': 'ZEF'
            }
            
            # Helper to clean currency string "356,000" -> 356000.0
            def clean_num(val):
                if isinstance(val, (int, float)): return float(val)
                return float(str(val).replace(',', '').strip())
            
            for index, row in df.iterrows():
                product_name = str(row.get('商品別', '')).strip()
                
                # Check mapping
                symbol = name_map.get(product_name)
                if not symbol:
                    # Fuzzy match? e.g. "臺股期貨(TX)"
                    for k, v in name_map.items():
                        if k in product_name:
                            symbol = v
                            break
                            
                if symbol:
                    # Found target
                    entry = {
                        'symbol': symbol,
                        'name': product_name,
                        'initial_margin': clean_num(row.get('原始保證金', 0)),
                        'maintenance_margin': clean_num(row.get('維持保證金', 0)),
                        'last_updated': datetime.now().isoformat()
                    }
                    results.append(entry)
                    
            print(f"Parsed {len(results)} margin entries.")
            return results
            
        except Exception as e:
            print(f"Error fetching margins: {e}")
            return []

    @staticmethod
    def sync_to_db():
        """Fetch from Web and Update Database"""
        data = MarginManager.fetch_current_margins()
        if not data:
            return False, "No data fetched"
            
        db = StockDatabase()
        count = 0
        for item in data:
            db.update_margin(
                symbol=item['symbol'],
                initial_margin=item['initial_margin'],
                maintenance_margin=item['maintenance_margin']
            )
            count += 1
            
        return True, f"Updated {count} records (TXF, MXF, ZEF)"
