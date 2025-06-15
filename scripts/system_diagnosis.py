#!/usr/bin/env python3
"""
JoJo Trading 系統診斷工具
用於檢查系統狀態、依賴項和常見問題
"""

import os
import sys
import importlib
import subprocess
import ssl
import requests
from datetime import datetime

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def print_header(title):
    """列印標題"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_python_environment():
    """檢查 Python 環境"""
    print_header("Python 環境檢查")
    print(f"Python 版本: {sys.version}")
    print(f"Python 執行路徑: {sys.executable}")
    print(f"當前工作目錄: {os.getcwd()}")

def check_required_packages():
    """檢查必要的套件"""
    print_header("套件依賴檢查")
    
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'requests',
        'beautifulsoup4',
        'lxml',
        'urllib3',
        'certifi'
    ]
    
    optional_packages = [
        'tej_xbrl_parser'
    ]
    
    print("必要套件:")
    for package in required_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"  ✓ {package} ({version})")
        except ImportError:
            print(f"  ✗ {package} - 未安裝")
    
    print("\n可選套件:")
    for package in optional_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"  ✓ {package} ({version})")
        except ImportError:
            print(f"  ⚠ {package} - 未安裝 (可選)")

def check_ssl_configuration():
    """檢查 SSL 配置"""
    print_header("SSL 配置檢查")
    
    # 檢查 SSL 版本
    print(f"SSL 版本: {ssl.OPENSSL_VERSION}")
    
    # 檢查證書路徑
    import certifi
    print(f"證書包路徑: {certifi.where()}")
    
    # 測試 HTTPS 連接
    test_urls = [
        "https://httpbin.org/get",
        "https://mops.twse.com.tw"
    ]
    
    print("\nHTTPS 連接測試:")
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"  ✓ {url} - 狀態碼: {response.status_code}")
        except requests.exceptions.SSLError as e:
            print(f"  ✗ {url} - SSL 錯誤: {str(e)[:100]}...")
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ {url} - 網路錯誤: {str(e)[:100]}...")

def check_directories():
    """檢查目錄結構"""
    print_header("目錄結構檢查")
    
    required_dirs = [
        'logs',
        'cache',
        'cache/xbrl_zip',
        'cache/xbrl_unzip',
        'modules',
        'modules/xbrl_etl'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - 不存在")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"    → 已創建目錄: {dir_path}")
            except Exception as e:
                print(f"    → 創建失敗: {e}")

def check_log_files():
    """檢查日誌文件"""
    print_header("日誌文件檢查")
    
    log_files = [
        'logs/jojo_trading_app.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            modified_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            print(f"  ✓ {log_file}")
            print(f"    大小: {file_size:,} bytes")
            print(f"    最後修改: {modified_time}")
            
            # 顯示最後幾行
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print("    最後3行:")
                        for line in lines[-3:]:
                            print(f"      {line.strip()}")
            except:
                print("    無法讀取日誌內容")
        else:
            print(f"  ✗ {log_file} - 不存在")

def check_xbrl_functionality():
    """檢查 XBRL 功能"""
    print_header("XBRL 功能檢查")
    
    try:
        # 嘗試導入修復後的模組
        from modules.xbrl_etl.core_parser_fixed import check_tej_parser_availability
        tej_available = check_tej_parser_availability()
        print(f"TEJ XBRL Parser: {'可用' if tej_available else '不可用'}")
        
        # 檢查基本網路連接功能
        from modules.xbrl_etl.core_parser_fixed import get_latest_xbrl_zip_url
        print("測試 MOPS 網站連接...")
        url = get_latest_xbrl_zip_url(2024, 1)  # 測試用參數
        if url:
            print(f"  ✓ 成功取得測試連結: {url}")
        else:
            print("  ⚠ 無法取得下載連結（可能是正常情況）")
            
    except Exception as e:
        print(f"  ✗ XBRL 功能測試失敗: {e}")

def generate_fix_suggestions():
    """產生修復建議"""
    print_header("修復建議")
    
    print("1. SSL 證書問題修復:")
    print("   - 確保網路連接正常")
    print("   - 更新 certifi 套件: pip install --upgrade certifi")
    print("   - 如果仍有問題，暫時使用 verify=False（僅開發環境）")
    
    print("\n2. 依賴套件安裝:")
    print("   pip install -r requirements.txt")
    print("   pip install beautifulsoup4 lxml urllib3 certifi")
    
    print("\n3. TEJ XBRL Parser（可選）:")
    print("   pip install tej_xbrl_parser")
    print("   如果無法安裝，系統會使用基本解析功能")
    
    print("\n4. 日誌檢查:")
    print("   - 檢查 logs/jojo_trading_app.log 的最新錯誤")
    print("   - 注意 SSL 和網路相關錯誤")
    
    print("\n5. 應用程式重啟:")
    print("   - 重新啟動 Streamlit 應用程式")
    print("   - 清除瀏覽器快取")

def main():
    """主要診斷流程"""
    print("JoJo Trading 系統診斷工具")
    print(f"執行時間: {datetime.now()}")
    
    try:
        check_python_environment()
        check_required_packages()
        check_ssl_configuration()
        check_directories()
        check_log_files()
        check_xbrl_functionality()
        generate_fix_suggestions()
        
        print_header("診斷完成")
        print("請根據上述檢查結果和建議進行必要的修復。")
        
    except Exception as e:
        print(f"\n診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
