import sys
import os
from pathlib import Path
import json
import time
import random

# Add src to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
from jojo_trading.core.stock_database import StockDatabase
from jojo_trading.core.simple_dcf import calculate_dcf_with_potential_return, map_sector_code_to_name
from jojo_trading.core.industry_dcf_params import get_industry_params

def update_database(limit=50, progress_callback=None):
    print("🚀 Starting Stock Database Update...")
    
    # Initialize
    db = StockDatabase()
    fetcher = AutoDataFetcher()
    
    # Get all companies from fetcher
    all_companies = fetcher.company_data
    if not all_companies:
        print("❌ No company data found in AutoDataFetcher.")
        return

    print(f"📋 Found {len(all_companies)} companies in total.")
    
    # Get existing stocks in DB to prioritize new ones
    existing_stocks_df = db.get_all_stocks()
    existing_codes = set(existing_stocks_df['code'].tolist()) if not existing_stocks_df.empty else set()
    
    # Prioritize: 
    # 1. Stocks not in DB
    # 2. Stocks in DB but old (not implemented yet, just doing new ones first for now)
    
    target_stocks = []
    
    # List of all codes
    all_codes = list(all_companies.keys())
    
    # Filter for new stocks
    new_stocks = [code for code in all_codes if code not in existing_codes]
    
    # If we have new stocks, prioritize them
    if new_stocks:
        print(f"🆕 Found {len(new_stocks)} new stocks to add.")
        target_stocks = new_stocks[:limit]
    else:
        print("🔄 All stocks exist in DB. Updating existing stocks (oldest first)...")
        # Sort by last_updated if possible, for now just random or sequential
        # In a real scenario, we would query DB for oldest 'last_updated'
        target_stocks = all_codes[:limit] # Just take first N for now
        
    print(f"🎯 Target stocks for this run: {len(target_stocks)}")
    
    success_count = 0
    total_targets = len(target_stocks)
    
    for i, code in enumerate(target_stocks):
        company_name = all_companies[code].get('公司名稱', '')
        msg = f"[{i+1}/{total_targets}] Processing {code} {company_name}..."
        print(f"\n{msg}")
        
        if progress_callback:
            progress_callback(i, total_targets, f"正在更新 {code} {company_name}...")
        
        try:
            # Fetch Data
            dcf_data = fetcher.get_dcf_ready_data(code)
            
            if not dcf_data.get('success'):
                error_msg = dcf_data.get('error', '')
                print(f"  ❌ Failed to fetch data: {error_msg}")
                
                # Check for API Limit
                if "402" in str(error_msg) or "Requests reach the upper limit" in str(error_msg):
                    print("\n⛔ CRITICAL: FinMind API Limit Reached (Status 402).")
                    print("   Aborting update process to prevent further errors.")
                    print("   Please wait for the API limit to reset (usually 1 hour or next day).")
                    if progress_callback:
                        progress_callback(i, total_targets, "⛔ API 限制已達上限，停止更新")
                    return False # Return False to indicate failure/abort
                
                continue
                
            # Determine Sector
            raw_sector = dcf_data.get('sector', '')
            mapped_sector = map_sector_code_to_name(raw_sector)
            
            # Get Industry Params
            industry_params = get_industry_params(mapped_sector)
            growth_rate = industry_params['growth_rate']
            terminal_growth = industry_params['terminal_growth']
            discount_rate = industry_params['discount_rate']
            
            # Calculate DCF
            # Prepare stock_data dict for calculation
            
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
                'name': company_name,
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
            
            # Sleep to avoid rate limits
            time.sleep(1)
            
        except Exception as e:
            print(f"  💥 Exception: {e}")
            
    print(f"\n✨ Update Complete. Success: {success_count}/{len(target_stocks)}")
    if progress_callback:
        progress_callback(total_targets, total_targets, "更新完成！")
    return True

if __name__ == "__main__":
    # Default to updating all stocks (limit=2000)
    # Can be overridden by command line arg in future
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=2000, help="Number of stocks to update")
    args = parser.parse_args()
    
    update_database(limit=args.limit)
