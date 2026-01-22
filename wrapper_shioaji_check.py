
try:
    import shioaji
    print(f"✅ Shioaji installed: {shioaji.__version__}")
except ImportError:
    print("❌ Shioaji not installed")
    exit(1)
