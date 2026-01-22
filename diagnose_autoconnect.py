
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.append(src_path)

try:
    from jojo_trading.core.stock_database import StockDatabase
    from jojo_trading.core.auth.broker_manager import BrokerProfileManager
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def diagnose():
    print("=== Auto-Connect Diagnosis ===")
    
    # Check Database
    try:
        db = StockDatabase()
        print("StockDatabase loaded.")
    except Exception as e:
        print(f"Error loading StockDatabase: {e}")
        return

    # Check Active Profile Setting
    active_profile_name = db.get_setting("active_profile")
    print(f"Active Profile Setting: '{active_profile_name}'")

    # Check Profiles
    try:
        profiles = BrokerProfileManager.get_profiles()
        print(f"Total Profiles Found: {len(profiles)}")
        for p in profiles:
            print(f" - Profile: {p.get('profile_name')} | ID: {p.get('person_id')} | Default: {p.get('is_default', 'N/A')}")
    except Exception as e:
        print(f"Error getting profiles: {e}")
        return

    # Simulate Selection Logic
    if not profiles:
        print("❌ No profiles found. Auto-connect will fail.")
        return

    target_profile = profiles[0]
    print(f"Initial Fallback Profile: {target_profile.get('profile_name')}")

    if active_profile_name:
        found = False
        for p in profiles:
            if p['profile_name'] == active_profile_name:
                target_profile = p
                print(f"✅ Found Active Profile match: {active_profile_name}")
                found = True
                break
        if not found:
            print(f"⚠️ Active profile '{active_profile_name}' set but not found in profiles. Using fallback.")
    
    print(f"🎯 Final Target for Auto-Connect: {target_profile.get('profile_name')}")

    # Compare with Env (to see if sync is needed)
    from dotenv import load_dotenv
    load_dotenv()
    
    env_api = os.getenv('SHIOAJI_API_KEY', '').strip()
    # Decrypt profile to compare
    full_prof = BrokerProfileManager.get_decrypted_profile(target_profile['profile_name'])
    
    if full_prof:
        db_api = full_prof.get('api_key', '')
        
        match = env_api == db_api
        print(f"Checking Consistency with .env:")
        print(f" - API Key Match: {match}")
        if not match:
            print(f"   (Env ends with {env_api[-4:] if env_api else 'None'})")
            print(f"   (DB  ends with {db_api[-4:] if db_api else 'None'})")
        else:
            print("   (Credentials are 100% in sync)")
    else:
        print("Could not decrypt profile to compare.")

if __name__ == "__main__":
    diagnose()
