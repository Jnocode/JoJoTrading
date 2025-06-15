#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("=== JoJo Trading 系統測試 ===")

# 測試 JSON 配置載入
print("\n1. 測試 industries.json 配置載入:")
try:
    import json
    with open('industries.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("   [OK] 配置載入成功")
    print(f"   [INFO] 產業數量: {len(config['industries'])}")
    print(f"   [INFO] 預設風險溢價: {config['default_risk_premium']}")
    print(f"   [INFO] 風險選項: {list(config['risk_premium_options'].keys())}")
except Exception as e:
    print(f"   [ERROR] 配置載入失敗: {e}")
    exit(1)

# 測試模組導入
print("\n2. 測試模組導入:")
try:
    from src.jojo_trading.core.state_machine import JoJoStateMachine, JoJoState
    print("   [OK] 狀態機模組導入成功")
except Exception as e:
    print(f"   [ERROR] 狀態機模組導入失敗: {e}")
    exit(1)

try:
    from src.jojo_trading.core import data_handler
    print("   [OK] data_handler 模組導入成功")
except Exception as e:
    print(f"   [ERROR] data_handler 模組導入失敗: {e}")

# 測試狀態機實例化
print("\n3. 測試狀態機實例化:")
try:
    machine = JoJoStateMachine()
    print(f"   [OK] 狀態機創建成功")
    print(f"   [INFO] 當前狀態: {machine.current_state}")
    
    if machine.current_state == JoJoState.ERROR:
        error_msg = machine.context.get('error_message', '未知錯誤')
        print(f"   [ERROR] 狀態機錯誤: {error_msg}")
    elif machine.current_state == JoJoState.UI_INIT:
        print("   [OK] 狀態機正常運行，已進入 UI_INIT 狀態")
        
        # 檢查配置是否正確載入到狀態機 context
        if 'industry_data' in machine.context:
            industry_count = len(machine.context['industry_data'].get('industries', []))
            print(f"   [INFO] 狀態機中載入的產業數量: {industry_count}")
        
        if 'industry_names' in machine.context:
            names_count = len(machine.context['industry_names'])
            print(f"   [INFO] 產業名稱列表長度: {names_count}")
            
        print("   [SUCCESS] JoJo Trading 系統配置完全正常！")
    else:
        print(f"   [WARNING] 狀態機處於非預期狀態: {machine.current_state}")
        
except Exception as e:
    print(f"   [ERROR] 狀態機實例化失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 測試完成 ===")
