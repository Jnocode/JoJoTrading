import sys
import os
import json
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
from jojo_trading.core.stock_database import StockDatabase
from jojo_trading.core.simple_dcf import calculate_dcf_with_potential_return, map_sector_code_to_name
from jojo_trading.core.industry_dcf_params import get_industry_params

def update_semiconductors():
    print("🚀 Starting Semiconductor Sector Update...")
    
    # 1. Load all companies
    json_path = os.path.join(os.path.dirname(__file__), '..', 'all_companies_basic_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)
    
    # 2. Filter for Semiconductor (Code 24)
    semiconductors = [c for c in companies if c.get('產業別') == '24']
    print(f"📋 Found {len(semiconductors)} semiconductor companies.")
    
    # 3. Initialize Fetcher and DB
    fetcher = AutoDataFetcher()
    db = StockDatabase()
    
    # 4. Update loop
    success_count = 0
    for i, company in enumerate(semiconductors, 1):
        code = company['公司代號']
        name = company['公司名稱']
        print(f"\n[{i}/{len(semiconductors)}] Processing {code} {name}...")
        
        try:
            # Fetch data (AutoDataFetcher now uses YFinance first)
            dcf_data = fetcher.get_dcf_ready_data(code)
            
            if dcf_data.get('success'):
                # --- DCF Calculation Logic (Copied from update_stock_db.py) ---
                
                # Determine Sector
                raw_sector = dcf_data.get('sector', '')
                mapped_sector = map_sector_code_to_name(raw_sector)
                
                # Get Industry Params
                industry_params = get_industry_params(mapped_sector)
                growth_rate = industry_params['growth_rate']
                terminal_growth = industry_params['terminal_growth']
                discount_rate = industry_params['discount_rate']
                
                # Calculate DCF
                net_income = dcf_data.get('net_income_parent', 0) / 1e8
                depreciation = dcf_data.get('depreciation', 0) / 1e8
                amortization = dcf_data.get('amortization', 0) / 1e8
                capex = dcf_data.get('capex', 0) / 1e8
                
                # Simplified FCF
                fcf = net_income + depreciation + amortization - capex
                
                calc_input = {
                    "company_name": dcf_data.get('company_name'),
                    "free_cash_flow": max(fcf, 1.0), # Ensure positive for calculation
                    "current_price": dcf_data.get('current_market_price'),
                    "shares_outstanding": dcf_data.get('shares_outstanding', 0)/1e8, # Convert to 億
                    "sector": mapped_sector
                }
                
                result, error = calculate_dcf_with_potential_return(
                    calc_input, growth_rate, terminal_growth, discount_rate
                )
                
                if error:
                    print(f"  ❌ DCF Calculation Error: {error}")
                    continue
                    
                # Save to DB
                db_record = {
                    'code': code,
                    'name': name,
                    'sector': mapped_sector,
                    'price': result['current_price'],
                    'intrinsic_value': result['intrinsic_value_per_share'],
                    'potential_return': result['potential_return'],
                    'market_cap': result['current_market_value'],
                    'fcf': result['current_fcf'],
                    'data_quality_score': dcf_data.get('data_quality_score', 0),
                    'data_source': 'auto_fetcher'
                }
                
                db.update_stock(db_record)
                print(f"  ✅ Updated DB: Return {result['potential_return']:.1f}%")
                success_count += 1
            else:
                print(f"  ❌ Failed to fetch data: {dcf_data.get('error')}")
                
        except Exception as e:
            print(f"  💥 Error processing {code}: {e}")
            
        # Small delay to be nice
        time.sleep(0.5)

    print(f"\n✨ Update Complete. Success: {success_count}/{len(semiconductors)}")

if __name__ == "__main__":
    update_semiconductors()
