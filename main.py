import pandas as pd
import numpy as np
import shioaji as sj
from datetime import datetime, time, timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
import sys
import argparse # 導入 argparse
from PyQt6.QtWidgets import QApplication
from core.engine import MainEngine, TradingMode # 導入 MainEngine 和 TradingMode
from core.event import EventEngine
# 不再需要直接導入 Gateway，由 MainEngine 處理
# from gateway.shioaji_gateway import ShioajiGateway # No longer needed here
# from gateway.api_gateway import ApiGateway # No longer needed here
from gui import TradingWindow
# Import the new App
from modules.left_value_zone_app import LeftValueZoneApp
# 移除舊導入
# import numpy as np
# import shioaji as sj
# from datetime import datetime, time, timedelta
# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from PyQt6.QtCore import QObject, pyqtSignal, QTimer
# import time
# import threading
# from signal_generator import SignalGenerator


# 移除舊的 TaiwanFuturesTrader 類別定義
# class TaiwanFuturesTrader(QObject):
#     ... (所有舊類別的方法都應被移除) ...


def main():
    """主應用程序入口"""
    # --- 解析命令列參數 ---
    parser = argparse.ArgumentParser(description="JoJo 量化交易系統")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["live", "simulation"],
        default="live", # 預設為 LIVE 模式
        help="選擇交易模式: live (實盤) 或 simulation (模擬)"
    )
    args = parser.parse_args()

    # 將字串模式轉換為 TradingMode 枚舉
    mode = TradingMode.LIVE if args.mode == "live" else TradingMode.SIMULATION
    print(f"啟動模式: {mode.name}")
    # ---

    qapp = QApplication(sys.argv) # 創建 QApplication 實例

    # 創建事件引擎和主引擎 (傳入模式)
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine, mode=mode) # 將模式傳遞給 MainEngine

    # 不再需要手動添加 Gateway，MainEngine 會自動處理
    # main_engine.add_gateway(ShioajiGateway)
    # main_engine.add_gateway(ApiGateway) # 如果 ApiGateway 也需要根據模式添加，需修改 MainEngine

    # 添加應用模組 (例如策略引擎、數據記錄等 - 根據需要添加)
    # 例如，可以根據模式選擇性添加 App
    # if mode == TradingMode.LIVE:
    #     main_engine.add_app(LiveTradingApp)
    # else:
    #     main_engine.add_app(SimulationApp)
    # main_engine.add_app(CtaStrategyApp) # Example for future futures app
    # main_engine.add_app(DataRecorderApp) # Example for data recorder app

    # --- Add LeftValueZoneApp ---
    main_engine.add_app(LeftValueZoneApp)
    # ---

    # 創建並顯示 GUI 主窗口
    # 將主引擎和事件引擎傳遞給 GUI
    main_window = TradingWindow(main_engine, event_engine)
    main_window.show()

    # 啟動事件引擎 (在 GUI 顯示後啟動)
    event_engine.start()

    # --- 連接交易接口 ---
    # MainEngine 會根據模式自動添加 Shioaji 或 Simulation Gateway
    # 我們只需要調用 connect，傳遞對應的設定
    # 注意：SimulationGateway 的 connect 可能不需要 setting，或使用空的 setting
    # 注意：ApiGateway 的連接邏輯可能需要獨立處理或整合進 MainEngine
    gateway_setting = {} # 實際應從配置文件或 GUI 讀取 Shioaji 設定
    # 連接預設接口 (Shioaji 或 Simulation)
    main_engine.connect(gateway_setting) # Connect the default gateway (Shioaji or Simulation)

    # --- Start Apps (Example: Start LeftValueZoneApp after connection) ---
    # You might want to start apps based on config or GUI interaction later
    main_engine.start_app("LeftValueZone")
    # ---

    # 處理 ApiGateway (如果需要) - 假設它不是預設接口，需要單獨處理
    # Check if ApiGateway class exists and add it if needed
    try:
        from gateway.api_gateway import ApiGateway # Try importing here
        api_gateway_instance = main_engine.add_gateway(ApiGateway) # Add it explicitly
        if api_gateway_instance:
            # 關鍵：將 main_engine 實例指派給 api_gateway_instance
            api_gateway_instance.main_engine = main_engine
            api_setting = {
                "host": "127.0.0.1",
                "port": 8000
            }
            main_engine.connect(api_setting, "API") # Connect it explicitly
        else:
            print("警告: 未能添加或連接 ApiGateway")
    except ImportError:
        print("資訊: 未找到 ApiGateway 模組，跳過連接。")
    except Exception as e:
        print(f"處理 ApiGateway 時發生錯誤: {e}")


    # 啟動 Qt 事件循環
    sys.exit(qapp.exec())

if __name__ == "__main__":
    main()
# --- Removed duplicated code block below ---
