
import shioaji as sj
import os
from dotenv import load_dotenv
import pprint

def inspect_contract_specs():
    load_dotenv()
    print("Connecting to Shioaji...")
    api = sj.Shioaji(simulation=False)
    api.login(os.getenv('SHIOAJI_API_KEY'), os.getenv('SHIOAJI_SECRET_KEY'))
    
    print("\n--- Inspecting TXF Contract Specs ---")
    txf_cat = api.Contracts.Futures.TXF
    if txf_cat:
        # Iterate to find first
        txf1 = None
        for c in txf_cat:
            txf1 = c
            break
            
        if txf1:
            print(f"Contract: {txf1}")
            print("Attributes:")
            pprint.pprint(txf1.__dict__)
            
            # Check standard fields
            print(f"\nMultiplier: {getattr(txf1, 'multiplier', 'N/A')}")
            print(f"Margin? {getattr(txf1, 'margin', 'N/A')}")
            print(f"Initial Margin? {getattr(txf1, 'initial_margin', 'N/A')}")
        else:
            print("TXF Category is empty.")
    
    print("\n--- Inspecting Option/Other ---")
    # Sometimes specs are hidden in sub-objects
    
if __name__ == "__main__":
    inspect_contract_specs()
