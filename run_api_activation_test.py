
"""
Sinopac Shioaji API Test Script
用途：協助使用者通過永豐金 API 啟用所需的測試流程
包含：
1. 登入 (Login)
2. 查詢帳戶 (List Accounts)
3. 查詢即時報價 (Snapshots) - 2330
"""
import shioaji as sj
import os
from dotenv import load_dotenv
import time

load_dotenv()

def run_test():
    print("=== API Activation Test Script ===")
    api = sj.Shioaji(simulation=False) # Production
    
    # 1. Login
    print("1. Logging in...")
    try:
        api.login(
            os.getenv('SHIOAJI_API_KEY', '').strip(),
            os.getenv('SHIOAJI_SECRET_KEY', '').strip()
        )
        print("✅ Login Success")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    # 2. Activate CA
    print("\n2. Activating CA...")
    try:
        api.activate_ca(
            ca_path=os.getenv('SHIOAJI_CERT_PATH'),
            ca_passwd=os.getenv('SHIOAJI_CERT_PASS'),
            person_id=os.getenv('SHIOAJI_PERSON_ID')
        )
        print("✅ CA Success")
    except Exception as e:
        print(f"⚠️ CA Message: {e}")

    # 3. List Accounts (The step usually required to be logged)
    print("\n3. Listing Accounts...")
    accounts = api.list_accounts()
    for acc in accounts:
        print(f"  - {acc}")

    # 4. Snapshot Test (Query 2330)
    print("\n4. Testing Time Snapshot (2330)...")
    try:
        contract = api.Contracts.Stocks['2330']
        snap = api.snapshots([contract])
        print(f"  - 2330 Price: {snap[0].close}")
        print("✅ Snapshot Success")
    except Exception as e:
        print(f"⚠️ Snapshot Message: {e}")
        
    print("\n=== Test Complete ===")
    print("請截圖此畫面或確認 API 後台是否有跳轉測試成功狀態")

if __name__ == "__main__":
    run_test()
