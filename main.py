import pandas as pd
import numpy as np
import shioaji as sj
from datetime import datetime, time, timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
import sys # 導入 sys
from PyQt6.QtWidgets import QApplication # 導入 QApplication
from core.engine import MainEngine
from core.event import EventEngine
from gateway.shioaji_gateway import ShioajiGateway
from gateway.api_gateway import ApiGateway  # 導入新的API网关
from gui import TradingWindow # 假設 GUI 在 gui.py 中
# 移除 indicators, pd, np, datetime, os, load_dotenv, QObject, pyqtSignal, QTimer, time, threading, SignalGenerator 的導入，因為舊類別已移除
# import indicators
# import pandas as pd
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
    qapp = QApplication(sys.argv) # 創建 QApplication 實例

    # 創建事件引擎和主引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    # 添加交易接口 (Shioaji)
    main_engine.add_gateway(ShioajiGateway)
    
    # 添加API网关接口
    main_engine.add_gateway(ApiGateway)

    # 添加應用模組 (例如策略引擎、數據記錄等 - 根據需要添加)
    # main_engine.add_app(CtaStrategyApp) 
    # main_engine.add_app(DataRecorderApp)

    # 創建並顯示 GUI 主窗口
    # 將主引擎和事件引擎傳遞給 GUI
    main_window = TradingWindow(main_engine, event_engine) 
    main_window.show()

    # 啟動事件引擎 (在 GUI 顯示後啟動)
    event_engine.start()

    # 連接交易接口 (可以在 GUI 啟動後或通過按鈕觸發)
    # 這裡假設有一個配置字典 setting
    shioaji_setting = {} # 實際應從配置文件或 GUI 讀取
    main_engine.connect(shioaji_setting, "Shioaji")
    
    # 啟動API服務器
    api_setting = {
        "host": "127.0.0.1",
        "port": 8000
    }
    main_engine.connect(api_setting, "API")

    # 啟動 Qt 事件循環
    sys.exit(qapp.exec())

if __name__ == "__main__":
    main()
