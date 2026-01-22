
import shioaji as sj
import os
from dotenv import load_dotenv

load_dotenv()

def probe_index():
    api = sj.Shioaji(simulation=False)
    api.login(
        os.getenv('SHIOAJI_API_KEY', '').strip(),
        os.getenv('SHIOAJI_SECRET_KEY', '').strip()
    )
    
    print("Attempting to fetch TSE001 (TaiEx)...")
    try:
        # Common path for Index
        # Note: Indices might need specific permissions or different contract lookup
        target = api.Contracts.Indices.TSE.TSE001
        print(f"Found: {target.name}")
        
        snap = api.snapshots([target])
        print(f"Snapshot: {snap[0].close}")
    except Exception as e:
        print(f"Failed: {e}")
        # Try generic search
        try:
           print("Listing Indices.TSE...")
           # contracts = [c for c in api.Contracts.Indices.TSE]
           # print(f"First 3: {contracts[:3]}")
           pass
        except:
           pass

if __name__ == "__main__":
    probe_index()
