
from FinMind.data import DataLoader
import inspect
import os

print("Checking DataLoader methods...")
dl = DataLoader()
print(f"Has login method? {hasattr(dl, 'login')}")

# Check if we can login with arbitrary creds to verify method signature
print("Signature of login:")
try:
    print(inspect.signature(dl.login))
except:
    print("Cannot get signature")
    
# Check .env current state
print(f"Env USER: {os.getenv('FINMIND_USER_ID')}")
