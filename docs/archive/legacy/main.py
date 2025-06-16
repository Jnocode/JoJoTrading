#!/usr/bin/env python3
"""
JoJo Trading 主應用程式入口點

這是 JoJo Trading 系統的主要入口點，提供命令列介面和 Web UI 啟動選項。

使用方式:
    python main.py                  # 啟動 Streamlit Web UI
    python main.py --cli            # 啟動命令列介面
    python main.py --test           # 執行系統測試
    python main.py --version        # 顯示版本資訊
"""

import argparse
import sys
import os
from pathlib import Path

# 添加 src 目錄到 Python 路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.jojo_trading import __version__
from src.jojo_trading.ui.app import drive_state_machine
from src.jojo_trading.core.state_machine import JoJoStateMachine


def run_web_ui():
    """啟動 Streamlit Web UI"""
    import subprocess
    import sys
    from pathlib import Path
    
    # 獲取 app.py 的路徑
    app_path = Path(__file__).parent / "src" / "jojo_trading" / "ui" / "app.py"
    
    # 啟動 Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost"
    ])


def run_cli():
    """執行命令列介面"""
    print("JoJo Trading CLI 模式")
    print(f"版本: {__version__}")
    
    # 初始化狀態機
    state_machine = JoJoStateMachine()
    
    # CLI 操作邏輯
    print("初始化狀態機...")
    
    # 在 CLI 模式下，我們可以模擬基本的工作流程
    # 狀態機已經在初始化時執行了 CONFIG_LOAD -> UI_INIT
    print(f"當前狀態: {state_machine.current_state}")
    
    # 簡單的 CLI 演示：顯示可用的產業
    if state_machine.context.get('industry_names'):
        print(f"載入了 {len(state_machine.context['industry_names'])} 個產業")
        print("前 5 個產業:", state_machine.context['industry_names'][:5])
    
    print("CLI 模式執行完成")


def run_tests():
    """執行系統測試"""
    print("執行 JoJo Trading 系統測試...")
    import subprocess
    
    # 執行 pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", "-v", "--tb=short"
    ], cwd=Path(__file__).parent)
    
    return result.returncode


def show_version():
    """顯示版本資訊"""
    print(f"JoJo Trading 系統版本: {__version__}")
    print("基於 DCF 估值的台股篩選系統")
    print("支援成長股分析、台股預設配置、客製化設定")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="JoJo Trading - 基於 DCF 估值的台股篩選系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python main.py                    啟動 Web UI
  python main.py --cli              命令列模式
  python main.py --test             執行測試
  python main.py --version          顯示版本
        """
    )
    
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="以命令列模式執行"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="執行系統測試"
    )
    
    parser.add_argument(
        "--version", 
        action="store_true", 
        help="顯示版本資訊"
    )
    
    args = parser.parse_args()
    
    try:
        if args.version:
            show_version()
        elif args.test:
            exit_code = run_tests()
            sys.exit(exit_code)
        elif args.cli:
            run_cli()
        else:
            # 預設啟動 Web UI
            print("啟動 JoJo Trading Web 介面...")
            print(f"版本: {__version__}")
            run_web_ui()
            
    except KeyboardInterrupt:
        print("\n系統已停止")
        sys.exit(0)
    except Exception as e:
        print(f"執行錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
