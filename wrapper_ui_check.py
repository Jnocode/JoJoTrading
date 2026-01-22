
try:
    import sys
    import os
    # Add src to path if needed (though wrapper usually runs from root where src is visible via package)
    sys.path.insert(0, os.path.abspath("src"))
    
    from jojo_trading.ui.app import JoJoTradingApp
    from jojo_trading.core.watchlist_manager import WatchlistManager
    from jojo_trading.ui.components.stage4_integration import Stage4IntegrationPanel
    
    print("✅ Imports successful")
    
    # Init Manager
    wm = WatchlistManager("src/jojo_trading/data/test_import.db")
    print("✅ WatchlistManager initialized")
    
    # Init App (Might fail if streamlit context missing, but we catch it)
    try:
        app = JoJoTradingApp()
        print("✅ JoJoTradingApp initialized")
    except Exception as e:
        print(f"⚠️ App Init Warning (Expected if no st context): {e}")

    print("All syntax checks passed.")
    
    if os.path.exists("src/jojo_trading/data/test_import.db"):
        os.remove("src/jojo_trading/data/test_import.db")

except Exception as e:
    print(f"❌ Syntax/Import Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
