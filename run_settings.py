
import sys
import os

print("Launcher starting...")
# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from jojo_trader.settings_app import main

if __name__ == "__main__":
    main()
