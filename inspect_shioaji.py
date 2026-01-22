
import shioaji as sj
try:
    print(f"Shioaji Version: {sj.__version__}")
    print(f"dir(sj): {dir(sj)}")
    
    try:
        from shioaji import TickSTTv1
        print("✅ TickSTTv1 found in top level")
    except ImportError:
        print("❌ TickSTTv1 NOT in top level")
        
    try:
        from shioaji import Exchange
        print("✅ Exchange found in top level")
    except ImportError:
        print("❌ Exchange NOT in top level")
        
except Exception as e:
    print(f"Error inspecting: {e}")
