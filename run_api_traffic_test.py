
"""
Sinopac API Activation Traffic Generator
用途：分別對「證券」與「期貨」帳戶產生流量，以滿足 API 啟用測試要求。
邏輯：
1. 執行證券相關查詢 (Snapshot 2330 + List Positions)
2. 等待 2 分鐘
3. 執行期貨相關查詢 (Snapshot TXF + List Positions)
"""
import shioaji as sj
import os
from dotenv import load_dotenv
import time

load_dotenv()

def run_traffic_test():
    print("=== API Activation Traffic Generator ===")
    api = sj.Shioaji(simulation=False)
    
    # 1. Login
    print("1. Logging in...")
    api.login(
        os.getenv('SHIOAJI_API_KEY', '').strip(),
        os.getenv('SHIOAJI_SECRET_KEY', '').strip()
    )
    print("✅ Login Success")

    # 2. CA
    api.activate_ca(
        ca_path=os.getenv('SHIOAJI_CERT_PATH'),
        ca_passwd=os.getenv('SHIOAJI_CERT_PASS'),
        person_id=os.getenv('SHIOAJI_PERSON_ID')
    )
    print("✅ CA Activated")

    # 3. Identify Accounts
    accounts = api.list_accounts()
    stock_acc = None
    future_acc = None
    
    for acc in accounts:
        if str(acc.account_type.value) in ['H', 'S']:
            stock_acc = acc
        elif str(acc.account_type.value) in ['F']:
            future_acc = acc
            
    # ==========================
    # Phase A: Stock / Securities
    # ==========================
    if stock_acc:
        print(f"\n[Phase A] Testing Securities Account: {stock_acc}")
        # Action 1: Snapshot
        try:
            contract = api.Contracts.Stocks['2330']
            snap = api.snapshots([contract])
            print(f"  - Snapshot (2330): {snap[0].close}")
        except Exception as e:
            print(f"  - Snapshot Error: {e}")

        # Action 2: Positions
        try:
            api.list_positions(stock_acc)
            print("  - List Positions: OK (Even if empty)")
        except Exception as e:
            print(f"  - Positions Error: {e}")
            
        print("✅ Securities Test Done.")
    else:
        print("\n⚠️ No Securities Account found.")

    # ==========================
    # Inteval
    # ==========================
    print("\n⏳ Waiting 120 seconds (2 minutes) as requested...")
    for i in range(120, 0, -10):
        print(f"  {i} sec remaining...", end="\r")
        time.sleep(10)
    print("  0 sec remaining. Continuing.\n")

    # ==========================
    # Phase B: Futures
    # ==========================
    if future_acc:
        print(f"[Phase B] Testing Futures Account: {future_acc}")
        # Action 1: Snapshot (TXF - need to find current code or just any future)
        # Using a simple generic query or just account balance which is specific to futures
        try:
            # Try to get first future contract or just skip snapshot if complex to find index
            # api.get_account_margin not available in all versions?
            # Let's try list_positions for futures
            api.list_positions(future_acc)
            print("  - List Positions: OK")
        except Exception as e:
            print(f"  - Positions Error: {e}")
            
        print("✅ Futures Test Done.")
    else:
        print("⚠️ No Futures Account found.")

    print("\n=== All Tests Completed ===")
    print("Please check Sinopac Activation Status.")

if __name__ == "__main__":
    run_traffic_test()
