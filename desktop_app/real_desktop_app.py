import sys
import os

# 添加專案 src 目錄到 path (確保可以正確 import jojo_trading.ui 與 jojo_trading)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
src_dir = os.path.join(root_dir, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 匯入並執行已經經過 UI/UX 翻修的主程式
from jojo_trading.ui.main_desktop import main

if __name__ == "__main__":
    main()
