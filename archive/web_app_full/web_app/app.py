#!/usr/bin/env python3
"""
JoJo Trading 統一入口點
Unified Entry Point for JoJo Trading Platform

這是 JoJo Trading 系統的統一入口點，整合了所有功能。
支援 Web 應用、CLI 模式、快速驗證等多種使用方式。

使用方式:
    python app.py                   # 啟動 Streamlit Web 應用 (預設)
    python app.py --cli             # 啟動命令列介面
    python app.py --version         # 顯示版本資訊
    python app.py --test            # 執行系統測試
    python app.py --quick-start     # 快速啟動驗證
    python app.py --simple          # 簡化模式
    python app.py --help            # 顯示幫助
"""

import sys
import argparse
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

# 添加 src 目錄到 Python 路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# 版本資訊
VERSION = "2.1.0"
BUILD_DATE = "2025-06-15"

def print_banner():
    """顯示啟動橫幅"""
    print("=" * 70)
    print("🎯             JoJo Trading Platform v{}            🎯".format(VERSION))
    print("💰                 統一入口點 - 整合版                    💰")
    print("=" * 70)
    print(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"版本: {VERSION} (Build: {BUILD_DATE})")
    print()

def check_environment():
    """檢查運行環境"""
    print("🔍 環境檢查...")
    
    # 檢查 Python 版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"⚠️  Python 版本警告: {python_version.major}.{python_version.minor}")
        print("   建議使用 Python 3.8 或更高版本")
    else:
        print(f"✅ Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 檢查關鍵依賴
    dependencies = ['streamlit', 'pandas', 'numpy']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: 已安裝")
        except ImportError:
            print(f"❌ {dep}: 未安裝")
    
    print()

def run_web_app(simple_mode=False):
    """啟動 Streamlit Web 應用程式"""
    print("🚀 啟動 Web 應用...")
    
    try:
        # 選擇應用程式文件
        if simple_mode:
            app_file = current_dir / "simple_app.py"
            if not app_file.exists():
                print("❌ 簡化應用程式檔案不存在，使用主應用程式")
                app_file = current_dir / "main_app.py"
        else:
            app_file = current_dir / "main_app.py"
        
        if not app_file.exists():
            print("❌ 應用程式檔案不存在")
            return False
        
        print(f"📱 使用應用檔案: {app_file.name}")
        
        # 啟動 Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_file)]
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        return False
    
    return True

def run_cli():
    """啟動命令列介面"""
    print("🎯 啟動 CLI 模式...")
    
    try:
        from jojo_trading.core.state_machine import JoJoStateMachine
        
        print("=" * 50)
        print("🎯 JoJo Trading CLI 模式")
        print("=" * 50)
        
        # 初始化狀態機
        machine = JoJoStateMachine()
        print(f"當前狀態: {machine.current_state}")
        
        # CLI 互動邏輯
        while True:
            print("\n📋 可用選項:")
            print("1. 執行 DCF 分析")
            print("2. 查看系統狀態")
            print("3. 執行快速測試")
            print("4. 退出")
            
            choice = input("\n請選擇 (1-4): ").strip()
            
            if choice == "1":
                print("🔄 DCF 分析功能...")
                try:
                    from jojo_trading.core.dcf_calculator import DCFCalculator
                    calculator = DCFCalculator()
                    print("✅ DCF 計算器已初始化")
                except Exception as e:
                    print(f"❌ DCF 分析失敗: {e}")
                    
            elif choice == "2":
                print(f"📊 系統狀態: {machine.current_state}")
                print(f"📅 當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
            elif choice == "3":
                run_test(quick=True)
                
            elif choice == "4":
                print("👋 CLI 模式結束")
                break
            else:
                print("❌ 無效選擇，請重新輸入")
                
    except Exception as e:
        print(f"❌ CLI 模式失敗: {e}")
        return False
    
    return True

def run_test(quick=False):
    """執行系統測試"""
    print("🧪 執行系統測試...")
    
    if quick:
        print("⚡ 快速測試模式")
    
    test_results = []
    
    # 基本模組導入測試
    print("\n📋 模組導入測試:")
    modules_to_test = [
        ('streamlit', 'Streamlit Web框架'),
        ('pandas', 'Pandas 資料處理'),
        ('numpy', 'NumPy 數值計算'),
    ]
    
    if not quick:
        modules_to_test.extend([
            ('jojo_trading.core.state_machine', '狀態機模組'),
            ('jojo_trading.core.dcf_calculator', 'DCF計算器'),
            ('jojo_trading.ui.app', 'UI應用模組'),
        ])
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            test_results.append((description, "✅"))
            print(f"  ✅ {description}")
        except ImportError as e:
            test_results.append((description, "❌"))
            print(f"  ❌ {description}: {e}")
    
    # 文件存在測試
    if not quick:
        print("\n📁 檔案存在測試:")
        files_to_check = [
            ('main_app.py', '主應用程式'),
            ('../src/jojo_trading/', '核心模組目錄'),
            ('../tests/', '測試目錄'),
            ('../data/', '數據目錄'),
        ]
        
        for file_path, description in files_to_check:
            path = current_dir / file_path
            if path.exists():
                test_results.append((description, "✅"))
                print(f"  ✅ {description}")
            else:
                test_results.append((description, "❌"))
                print(f"  ❌ {description}: 不存在")
    
    # 測試總結
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    passed = sum(1 for _, status in test_results if status == "✅")
    total = len(test_results)
    
    for description, status in test_results:
        print(f"  {status} {description}")
    
    print(f"\n🎯 通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試通過！系統狀態良好。")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查相關配置。")
        return False

def run_quick_start():
    """執行快速啟動驗證"""
    print("⚡ 快速啟動驗證...")
    
    # 執行快速測試
    print("\n1️⃣ 系統檢查:")
    if not run_test(quick=True):
        print("❌ 系統檢查失敗")
        return False
    
    print("\n2️⃣ 嘗試啟動核心模組:")
    try:
        from jojo_trading.core.auto_data_fetcher import AutoDataFetcher
        fetcher = AutoDataFetcher()
        print("✅ 資料抓取器初始化成功")
        
        from jojo_trading.core.dcf_calculator import DCFCalculator  
        calculator = DCFCalculator()
        print("✅ DCF計算器初始化成功")
        
    except Exception as e:
        print(f"❌ 核心模組啟動失敗: {e}")
        return False
    
    print("\n3️⃣ 準備啟動 Web 應用:")
    print("🎯 系統驗證完成，可以安全啟動！")
    print("\n" + "=" * 50)
    print("🚀 即將啟動 JoJo Trading Web 應用...")
    print("=" * 50)
    
    # 等待一下再啟動
    time.sleep(2)
    return run_web_app()

def show_help():
    """顯示幫助信息"""
    print("""
🎯 JoJo Trading Platform - 使用指南

📋 可用命令:
  python app.py              啟動 Web 應用 (預設)
  python app.py --cli        啟動命令列介面
  python app.py --test       執行完整系統測試
  python app.py --quick      快速測試
  python app.py --start      快速啟動驗證
  python app.py --simple     簡化模式 Web 應用
  python app.py --version    顯示版本資訊
  python app.py --help       顯示此幫助

🚀 快速開始:
  1. 首次使用: python app.py --start
  2. 日常使用: python app.py
  3. 開發調試: python app.py --cli

📚 更多資訊請參考 README.md
""")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="JoJo Trading Platform 統一入口點",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python app.py                   # 啟動 Web 應用
  python app.py --cli             # CLI 模式
  python app.py --start           # 快速啟動
        """
    )
    
    parser.add_argument('--cli', action='store_true', help='啟動命令列介面')
    parser.add_argument('--test', action='store_true', help='執行完整系統測試')
    parser.add_argument('--quick', action='store_true', help='執行快速測試')
    parser.add_argument('--start', '--quick-start', action='store_true', help='快速啟動驗證')
    parser.add_argument('--simple', action='store_true', help='簡化模式')
    parser.add_argument('--version', action='store_true', help='顯示版本資訊')
    parser.add_argument('--env-check', action='store_true', help='僅檢查環境')
    
    args = parser.parse_args()
    
    # 顯示橫幅
    if not args.version and not args.env_check:
        print_banner()
    
    # 處理參數
    if args.version:
        print(f"JoJo Trading Platform v{VERSION}")
        print(f"Build Date: {BUILD_DATE}")
        print("Copyright (c) 2025 JoJo Trading Team")
        return 0
    
    if args.env_check:
        check_environment()
        return 0
    
    if args.cli:
        return 0 if run_cli() else 1
    
    if args.test:
        return 0 if run_test() else 1
    
    if args.quick:
        return 0 if run_test(quick=True) else 1
    
    if args.start:
        return 0 if run_quick_start() else 1
    
    # 預設行為：啟動 Web 應用
    check_environment()
    return 0 if run_web_app(simple_mode=args.simple) else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 程序已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序執行錯誤: {e}")
        sys.exit(1)
