#!/usr/bin/env python3
"""
JoJo Trading 模組修復狀態檢查
專注於識別和修復模組導入問題
"""

import os
import sys
from pathlib import Path

def check_module_status():
    """檢查模組狀態並識別需要修復的問題"""
    
    print("JoJo Trading 模組修復狀態檢查")
    print("=" * 50)
    
    # 1. 檢查Python路徑設置
    print("\n1. Python 路徑檢查:")
    src_path = os.path.join(os.getcwd(), 'src')
    if src_path in sys.path:
        print(f"[OK] src路徑已在Python路徑中: {src_path}")
    else:
        print(f"[ISSUE] src路徑不在Python路徑中，需要添加: {src_path}")
        sys.path.insert(0, src_path)
    
    # 2. 檢查關鍵模組檔案
    print("\n2. 關鍵模組檔案檢查:")
    key_modules = [
        "src/jojo_trading/__init__.py",
        "src/jojo_trading/config/__init__.py", 
        "src/jojo_trading/ui/__init__.py",
        "src/jojo_trading/ui/app.py",
        "src/jojo_trading/trading/__init__.py",
        "src/jojo_trading/trading/trading_ui.py",
        "src/jojo_trading/utils/__init__.py"
    ]
    
    missing_files = []
    for module_file in key_modules:
        if os.path.exists(module_file):
            size = os.path.getsize(module_file)
            print(f"[OK] {module_file} ({size} bytes)")
        else:
            print(f"[MISSING] {module_file}")
            missing_files.append(module_file)
    
    # 3. 測試模組導入
    print("\n3. 模組導入測試:")
    module_tests = [
        ("jojo_trading", "主套件"),
        ("jojo_trading.config", "配置模組"),
        ("jojo_trading.ui.app", "DCF應用"),
        ("jojo_trading.trading.trading_ui", "交易UI"),
        ("jojo_trading.utils", "工具模組")
    ]
    
    import_issues = []
    for module_name, description in module_tests:
        try:
            __import__(module_name)
            print(f"[OK] {description} ({module_name})")
        except Exception as e:
            print(f"[FAIL] {description} ({module_name}): {str(e)[:60]}...")
            import_issues.append((module_name, str(e)))
    
    # 4. 生成修復建議
    print("\n4. 修復建議:")
    if missing_files:
        print("需要創建缺失的檔案:")
        for file in missing_files:
            print(f"  - {file}")
    
    if import_issues:
        print("需要修復的導入問題:")
        for module, error in import_issues:
            print(f"  - {module}: {error[:80]}...")
    
    if not missing_files and not import_issues:
        print("所有模組檢查通過！")
        return True
    
    return False

if __name__ == "__main__":
    success = check_module_status()
    if success:
        print("\n[SUCCESS] 模組狀態良好，可以進行功能驗證")
    else:
        print("\n[ACTION NEEDED] 發現問題，開始修復流程")
