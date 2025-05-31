#!/usr/bin/env python3
"""
JoJo Trading 主應用程式入口點

這是 JoJo Trading 台股 DCF 估值系統的主要入口點。
提供命令列介面和 Streamlit Web 應用程式的啟動功能。

使用方式:
    python -m jojo_trading.main            # 啟動 Streamlit Web 應用
    python -m jojo_trading.main --cli       # 使用命令列介面
    python -m jojo_trading.main --help      # 顯示說明

功能特色:
- 台股 DCF 估值計算
- 成長股篩選和分析
- 17種台股預設配置
- 用戶自訂配置管理
- 多語言支援 (中文/英文)
"""

import sys
import argparse
from pathlib import Path

# 將專案根目錄加入 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.jojo_trading.ui.app import main as streamlit_main
from src.jojo_trading.core.state_machine import JoJoStateMachine


def run_cli():
    """命令列介面模式"""
    print("🎯 JoJo Trading CLI 模式")
    print("=" * 50)
    
    # 初始化狀態機
    machine = JoJoStateMachine()
    
    print("📊 系統初始化完成")
    print("💡 提示: Web 介面模式請執行: python -m jojo_trading.main")
    
    # TODO: 實現完整的 CLI 介面
    print("⚠️  CLI 模式開發中，請使用 Web 介面")


def run_web():
    """Streamlit Web 應用程式模式"""
    print("🚀 啟動 JoJo Trading Web 應用程式...")
    streamlit_main()


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="JoJo Trading 台股 DCF 估值系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s                    # 啟動 Web 應用程式
  %(prog)s --cli              # 命令列模式
  %(prog)s --version          # 顯示版本資訊
        """
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="使用命令列介面模式"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="JoJo Trading v1.0.0"
    )
    
    args = parser.parse_args()
    
    try:
        if args.cli:
            run_cli()
        else:
            run_web()
    except KeyboardInterrupt:
        print("\n👋 程式已中止")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
