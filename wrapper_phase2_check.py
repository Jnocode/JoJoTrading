
import sys
import os
try:
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    from jojo_trading.core.watchlist_manager import WatchlistManager
    from jojo_trading.core.shioaji_connector import ShioajiConnector
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    exit(1)
import os

def test_phase2():
    print("🚀 Testing Phase 2 Integration...")
    
    # 1. Test WatchlistManager Migration
    print("\n1. WatchlistManager Schema Check")
    wm = WatchlistManager("test_phase2.db")
    try:
        # Should auto-migrate on init
        # Verify columns
        import sqlite3
        conn = sqlite3.connect("test_phase2.db")
        c = conn.cursor()
        c.execute("PRAGMA table_info(watchlist)")
        cols = [info[1] for info in c.fetchall()]
        print(f"  Columns: {cols}")
        
        if 'shares_held' in cols and 'average_cost' in cols:
            print("  ✅ Schema Migration Successful")
        else:
            print("  ❌ Schema Migration Failed")
            
        # Test update_holding
        if hasattr(wm, 'update_holding'):
             wm.update_holding("2330", 1000, 500.0)
             df = wm.get_all_entries()
             print(f"  Entry: {df.iloc[0].to_dict()}")
             print("  ✅ update_holding method works")
        else:
             print("  ❌ update_holding method MISSING")
        
    except Exception as e:
        print(f"  ❌ WatchlistManager Test Failed: {e}")
    finally:
        try:
            conn.close()
        except: 
            pass
        try:
            os.remove("test_phase2.db")
        except:
            pass

    # 2. Test ShioajiConnector.get_positions syntax
    print("\n2. ShioajiConnector Syntax Check")
    try:
        connector = ShioajiConnector()
        # Don't actually call get_positions to avoid connecting to real account in test
        # Just check if method exists
        if hasattr(connector, 'get_positions'):
            print("  ✅ get_positions method exists")
            
            # Optional: Call it if user has keys (which they do)
            # CAUTION: This might print real account info or fail if session invalid
            # Let's just print documentation or signature?
            pass
        else:
            print("  ❌ get_positions method MISSING")
            
    except Exception as e:
        print(f"  ❌ ShioajiConnector Init Failed: {e}")

if __name__ == "__main__":
    test_phase2()
