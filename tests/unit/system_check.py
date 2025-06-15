#!/usr/bin/env python3
"""
JoJo Trading 系統狀態檢測腳本
確保所有核心功能模組可正常運作
"""

import sys
from pathlib import Path

# 添加 src 路徑到 Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import sys
import os
import importlib
from pathlib import Path

def check_system_status():
    """檢查系統整體狀態"""
    print("🔍 JoJo Trading 系統狀態檢測")
    print("=" * 50)
    
    all_checks_passed = True
    
    # 1. 檢查Python版本
    print(f"\n📋 Python版本檢查")
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} - 版本符合需求")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} - 需要Python 3.8+")
        all_checks_passed = False
    
    # 2. 檢查主要執行檔
    print(f"\n📋 主要執行檔檢查")
    main_app_path = Path("main_app.py")
    if main_app_path.exists():
        print("✅ main_app.py - 主執行檔存在")
    else:
        print("❌ main_app.py - 主執行檔不存在")
        all_checks_passed = False
    
    # 3. 檢查核心相依套件
    print(f"\n📋 核心套件檢查")
    required_packages = [
        ("streamlit", "Streamlit Web框架"),
        ("pandas", "數據處理"),
        ("numpy", "數值計算"),
        ("yfinance", "股票數據獲取"),
        ("plotly", "圖表繪製")
    ]
    
    for package_name, description in required_packages:
        try:
            importlib.import_module(package_name)
            print(f"✅ {package_name} - {description}")
        except ImportError:
            print(f"❌ {package_name} - {description} (未安裝)")
            all_checks_passed = False
    
    # 4. 檢查核心模組
    print(f"\n📋 核心模組檢查")
    
    # 檢查DCF模組
    try:
        sys.path.append('.')
        from src.jojo_trading.ui.app import main as dcf_main
        print("✅ DCF分析模組 - 可正常導入")
    except Exception as e:
        print(f"❌ DCF分析模組 - 導入失敗: {str(e)}")
        all_checks_passed = False
    
    # 檢查交易系統模組
    try:
        from src.jojo_trading.trading.trading_ui import TradingSystemUI
        print("✅ 交易系統模組 - 可正常導入")
    except Exception as e:
        print(f"❌ 交易系統模組 - 導入失敗: {str(e)}")
        all_checks_passed = False
    
    # 5. 檢查必要目錄結構
    print(f"\n📋 目錄結構檢查")
    required_dirs = [
        "src/jojo_trading",
        "src/jojo_trading/core",
        "src/jojo_trading/ui", 
        "src/jojo_trading/trading",
        "src/jojo_trading/utils",
        "config",
        "data"
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/ - 目錄存在")
        else:
            print(f"❌ {dir_path}/ - 目錄不存在")
            all_checks_passed = False
    
    # 6. 檢查配置檔案
    print(f"\n📋 配置檔案檢查")
    config_files = [
        ("requirements.txt", "套件需求清單"),
        (".env", "環境變數配置"),
        ("README.md", "專案說明文件")
    ]
    
    for file_path, description in config_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - {description}")
        else:
            print(f"⚠️ {file_path} - {description} (可選)")
    
    # 結果總結
    print(f"\n{'='*50}")
    if all_checks_passed:
        print("🎉 系統檢查完成！所有核心功能正常")
        print("\n🚀 啟動指令：")
        print("   streamlit run main_app.py")
        print("\n🌐 瀏覽器網址：")
        print("   http://localhost:8501")
    else:
        print("⚠️ 系統檢查發現問題，請先解決上述錯誤")
        print("\n🔧 建議解決步驟：")
        print("1. 確保Python版本 >= 3.8")
        print("2. 安裝必要套件：pip install -r requirements.txt")
        print("3. 確認檔案結構完整")
    
    return all_checks_passed

if __name__ == "__main__":
    try:
        check_system_status()
    except KeyboardInterrupt:
        print("\n\n👋 檢查中斷")
    except Exception as e:
        print(f"\n❌ 檢查過程發生錯誤：{str(e)}")
        sys.exit(1)
