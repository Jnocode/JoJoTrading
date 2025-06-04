#!/usr/bin/env python3
"""
直接測試模組導入的腳本
"""

import sys
import os

# 添加專案路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("🚀 JoJo Trading 模組導入測試")
print("=" * 50)

# 測試 1: data_handler
print("\n1. 測試 data_handler 模組:")
try:
    from src.jojo_trading.core import data_handler
    print("   ✅ data_handler 導入成功")
    
    # 檢查模組屬性
    attributes = [attr for attr in dir(data_handler) if not attr.startswith('_')]
    print(f"   📝 模組包含 {len(attributes)} 個公開屬性/函數")
    
    # 檢查重要函數
    important_funcs = ['calculate_dcf_valuation', 'get_financial_data_cached', 'filter_industry_stocks']
    for func in important_funcs:
        if hasattr(data_handler, func):
            print(f"   ✅ {func} 函數存在")
        else:
            print(f"   ⚠️ {func} 函數不存在")
            
except Exception as e:
    print(f"   ❌ data_handler 導入失敗: {e}")

# 測試 2: state_machine
print("\n2. 測試 state_machine 模組:")
try:
    from src.jojo_trading.core.state_machine import JoJoStateMachine, JoJoState
    print("   ✅ state_machine 導入成功")
    
    # 測試實例化
    machine = JoJoStateMachine()
    print(f"   ✅ JoJoStateMachine 實例化成功")
    print(f"   📝 當前狀態: {machine.current_state}")
    
except Exception as e:
    print(f"   ❌ state_machine 導入失敗: {e}")

# 測試 3: taiwan_presets
print("\n3. 測試 taiwan_presets 模組:")
try:
    from src.jojo_trading.config.taiwan_presets import get_all_taiwan_growth_presets
    print("   ✅ taiwan_presets 導入成功")
    
    # 測試函數
    presets = get_all_taiwan_growth_presets()
    print(f"   ✅ get_all_taiwan_growth_presets 函數執行成功")
    print(f"   📝 預設配置數量: {len(presets)}")
    
except Exception as e:
    print(f"   ❌ taiwan_presets 導入失敗: {e}")

# 測試 4: user_config
print("\n4. 測試 user_config 模組:")
try:
    from src.jojo_trading.config.user_config import UserConfigManager
    print("   ✅ user_config 導入成功")
    
    # 測試實例化
    config_manager = UserConfigManager()
    print("   ✅ UserConfigManager 實例化成功")
    
except Exception as e:
    print(f"   ❌ user_config 導入失敗: {e}")

# 測試 5: 舊版模組
print("\n5. 測試舊版模組:")
legacy_modules = [
    ('modules.i18n', 't'),
    ('modules.growth_analyzer', 'DEFAULT_CRITERIA'),
    ('dcf_optimized_config', 'DCF_OPTIMIZED_CONFIG')
]

for module_name, item_name in legacy_modules:
    try:
        module = __import__(module_name, fromlist=[item_name])
        item = getattr(module, item_name)
        print(f"   ✅ {module_name}.{item_name} 導入成功")
    except Exception as e:
        print(f"   ⚠️ {module_name}.{item_name} 導入失敗: {e}")

print("\n" + "=" * 50)
print("📊 測試結果總結:")

# 檢查核心模組狀態
core_ok = True
try:
    from src.jojo_trading.core import data_handler
    from src.jojo_trading.core.state_machine import JoJoStateMachine
    from src.jojo_trading.config.taiwan_presets import get_all_taiwan_growth_presets
    from src.jojo_trading.config.user_config import UserConfigManager
    print("🎉 核心模組狀態: 全部正常")
except Exception as e:
    core_ok = False
    print(f"⚠️ 核心模組狀態: 有問題 - {e}")

if core_ok:
    print("💡 建議: 系統準備就緒，可以啟動Streamlit應用")
    print("🚀 啟動命令: python -m streamlit run main_app.py")
else:
    print("💡 建議: 需要修正模組導入問題後再測試")
