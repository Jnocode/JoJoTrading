import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
                             QGroupBox, QFormLayout, QDateEdit, QSpinBox, QDoubleSpinBox,
                             QTabWidget, QHeaderView, QMenuBar, QMenu, QMessageBox,
                             QDialog, QLineEdit, QDialogButtonBox, QCheckBox, QApplication,
                             QStatusBar, QStyleFactory, QTimeEdit)
from PyQt6.QtCore import Qt, QTimer, QDate, QDateTime, QTime, pyqtSlot, QObject, QCoreApplication
from PyQt6.QtGui import QColor, QIcon, QAction, QFont, QPixmap, QPainter, QCursor, QImage
from PyQt6.QtCore import pyqtSignal # 導入 pyqtSignal
# import indicators # 指標計算移到策略或 App 中
# from main import TaiwanFuturesTrader # 移除舊導入
from core.engine import MainEngine # 導入新的主引擎
from core.event import EventEngine, Event, EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_POSITION, EVENT_ACCOUNT, EVENT_CONTRACT, EVENT_KBAR, EVENT_LOG, EVENT_CONNECTION_STATUS # 導入事件引擎和事件類型
from login import LoginDialog
from gateway.shioaji_gateway import ShioajiGateway
from gateway.api_gateway import ApiGateway # 確保導入
import os
from dotenv import load_dotenv
from modules.valuation_engine import calculate_value # 導入估值函數
from modules.left_value_zone_gui import LeftValueZoneGUI # 導入左側價值區 GUI
import pandas as pd
from datetime import datetime, time, timedelta
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import mplfinance as mpf
import io
from  typing import Dict, Optional, Any # Import typing for hints

# 檢查 PIL 是否安裝
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL (Pillow) 庫未安裝，權益曲線圖將無法顯示。請使用 'pip install Pillow' 安裝。")


# 合併重複 TradingWindow class，保留所有功能與初始化方法
class TradingWindow(QMainWindow):
    # 定義 Qt 信號，用於跨執行緒更新 GUI
    signal_update_futures = pyqtSignal(dict)
    signal_update_kbars = pyqtSignal(str, pd.DataFrame)
    signal_update_stock_table = pyqtSignal(dict) # 用於更新單個股票行或添加新行
    signal_update_log = pyqtSignal(str)
    signal_update_connection_status = pyqtSignal(dict)
    signal_update_trading_records = pyqtSignal(list) # 假設有一個更新交易記錄的信號

    # 修改 __init__ 以接收 main_engine 和 event_engine
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine

        # 新增自動交易管理器
        try:
            from auto_trader_manager import AutoTraderManager
            self.auto_trader_manager = AutoTraderManager()
            # 設定自動交易訊息回呼
            if self.auto_trader_manager and hasattr(self.auto_trader_manager, "trader"):
                self.auto_trader_manager.trader.set_log_callback(self.append_log)
        except Exception as e:
            print(f"載入 AutoTraderManager 失敗: {e}")
            self.auto_trader_manager = None
        self.current_kbars: Dict[str, pd.DataFrame] = { # 用於存儲 GUI 當前顯示的 K 線數據
            '15m': pd.DataFrame(),
            '30m': pd.DataFrame(),
            '1h': pd.DataFrame(),
            '日K': pd.DataFrame()
        }
        self.yesterday_close: Optional[float] = None # 昨收價
        self.stock_data_cache: Dict[str, Dict] = {} # 緩存股票數據以更新表格
        self._init_status_bar_timer() # 初始化狀態欄計時器

        # 設定窗口
        self.setWindowTitle('JoJo 量化交易系統 (重構版)')
        self.setGeometry(100, 100, 1600, 900)

        # 建立中央部件和主佈局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)

        # 初始化狀態欄
        self.status_bar = self.statusBar()
        self.status_bar.showMessage('歡迎使用 JoJo 量化交易系統')

        # 顯示連接狀態 (添加到狀態欄右側)
        self.connection_status = QLabel('API狀態: 未知') # 初始狀態
        self.connection_status.setStyleSheet('color: gray;')
        self.status_bar.addPermanentWidget(self.connection_status)

        # 初始化面板
        self._init_market_data_panel()
        self._init_stock_list()
        self._init_indicator_panel()
        self._init_charts()
        self._init_auto_trading_panel()
        self._init_backtest_panel()
        self._init_valuation_panel() # 初始化新的估值面板

        # 整合左側價值區 GUI
        self._init_left_value_zone_panel()

        # 創建工具欄
        self.create_toolbar()

        # 設置時間更新定時器 (僅更新時間顯示)
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time_display)
        self.time_timer.start(1000)

        # 註冊事件處理函數
        self._register_event_handlers()
        # 連接信號到槽函數
        self._connect_signals()

        # 初始化一次UI狀態
        self.update_time_display()
        # self.update_stock_list() # 列表更新由事件觸發

    def _register_event_handlers(self):
        """註冊 GUI 需要處理的事件"""
        # 訂閱特定事件
        self.event_engine.register(EVENT_TICK + "TXF0", self._handle_futures_update) # 假設台指期代碼為 TXF0
        self.event_engine.register(EVENT_KBAR, self._handle_kbars_update)
        self.event_engine.register(EVENT_ORDER, self._handle_order_update)
        self.event_engine.register(EVENT_TRADE, self._handle_trade_update)
        self.event_engine.register(EVENT_POSITION, self._handle_position_update)
        self.event_engine.register(EVENT_ACCOUNT, self._handle_account_update)
        self.event_engine.register(EVENT_LOG, self._handle_log_update)
        self.event_engine.register(EVENT_CONNECTION_STATUS, self._handle_connection_status_change)
        # 訂閱所有 Tick 事件來更新股票列表 (如果需要實時更新所有股票)
        self.event_engine.register(EVENT_TICK, self._handle_stock_tick_update) # Use general tick handler

    def _connect_signals(self):
        """連接 Qt 信號到對應的槽函數"""
        self.signal_update_futures.connect(self._update_futures_ui)
        self.signal_update_kbars.connect(self._update_kbars_ui)
        self.signal_update_stock_table.connect(self._update_stock_table_ui)
        self.signal_update_log.connect(self._update_log_ui)
        self.signal_update_connection_status.connect(self._update_connection_status_ui)
        self.signal_update_trading_records.connect(self._update_trading_records_ui) # 連接交易記錄信號

    def append_log(self, message: str):
        """將自動交易訊息加入日誌區"""
        try:
            self.auto_trading_log_text.append(message)
        except Exception as e:
            print(f"寫入自動交易日誌失敗: {e}")

    # --- 新增的 UI 更新槽函數 ---
    @pyqtSlot(dict)
    def _update_futures_ui(self, data):
        """在主執行緒中更新期貨 UI"""
        price = data.get('last_price')
        volume = data.get('volume')

        if price is not None:
            self.futures_price_label.setText(f"{price:.2f}")
        if volume is not None:
            self.futures_volume_label.setText(f"{volume:,}")

        if price is not None and self.yesterday_close:
            change = price - self.yesterday_close
            change_percent = (change / self.yesterday_close) * 100 if self.yesterday_close else 0
            color = 'green' if change >= 0 else 'red'
            self.futures_change_label.setText(f"{change:+.2f} ({change_percent:+.2f}%)")
            self.futures_change_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        elif price is not None:
             self.futures_change_label.setText("--")
             self.futures_change_label.setStyleSheet("")

    @pyqtSlot(str, pd.DataFrame)
    def _update_kbars_ui(self, timeframe, df):
        """在主執行緒中更新 K 線數據和圖表"""
        self.current_kbars[timeframe] = df
        if self.period_combo.currentText() == timeframe:
            self.update_charts()

    @pyqtSlot(dict)
    def _update_stock_table_ui(self, data):
         """在主執行緒中更新股票表格行"""
         stock_id = data.get("symbol")
         if not stock_id: return

         # 更新緩存
         self.stock_data_cache[stock_id] = data

         # 查找或添加行並更新
         for row in range(self.stock_table.rowCount()):
             if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == stock_id:
                 self._update_stock_table_row(row, data)
                 break
         else: # 如果循環未被 break，表示股票不在表格中
             self._add_stock_to_table(stock_id, data)

    @pyqtSlot(str)
    def _update_log_ui(self, log_message):
        """在主執行緒中更新狀態欄日誌"""
        self.status_bar.showMessage(log_message, 5000)

    @pyqtSlot(dict)
    def _update_connection_status_ui(self, data):
         """在主執行緒中更新連接狀態顯示"""
         connected = data.get("connected", False)
         message = data.get("message", "未知狀態")
         gateway_name = data.get("gateway_name", "未知接口")

         status_text = f"{gateway_name} 狀態: {message}"
         if connected:
             color = "green"
             conn_label_text = "已連接"
         elif "模擬數據" in message or "API密鑰未設置" in message or "登入憑證錯誤" in message:
             color = "orange"
             conn_label_text = message
         else:
             color = "red"
             conn_label_text = "連接失敗"

         if hasattr(self, 'connection_status'):
              self.connection_status.setText(status_text)
              self.connection_status.setStyleSheet(f"color: {color};")
         if hasattr(self, 'connection_status_label'):
              self.connection_status_label.setText(conn_label_text)
              self.connection_status_label.setStyleSheet(f"color: {color};")

    @pyqtSlot(list)
    def _update_trading_records_ui(self, records):
         """在主執行緒中更新交易記錄表格"""
         # TODO: Implement actual table update logic
         print(f"GUI Slot: Updating trading records UI with {len(records)} records")
         # self._update_trading_records_table(records) # Call helper

    def _init_status_bar_timer(self):
        """初始化用於清除狀態欄的計時器"""
        self.status_clear_timer = QTimer(self)
        self.status_clear_timer.setSingleShot(True)
        self.status_clear_timer.timeout.connect(self._clear_status_bar)

    @pyqtSlot()
    def _clear_status_bar(self):
        """清除狀態欄訊息"""
        self.status_bar.clearMessage()

    # --- 原始事件處理函數 (修改為發射信號) ---
    @pyqtSlot(Event)
    def _handle_futures_update(self, event: Event):
        """處理期貨數據更新事件 (發射信號)"""
        # 不直接更新 UI，而是發射信號
        self.signal_update_futures.emit(event.data)

    @pyqtSlot(Event)
    def _handle_kbars_update(self, event: Event):
        """處理K線數據更新事件 (發射信號)"""
        data = event.data
        timeframe = data.get("timeframe")
        df = data.get("dataframe")
        if timeframe and df is not None:
            # 傳遞 DataFrame 的副本以避免潛在的跨線程問題
            self.signal_update_kbars.emit(timeframe, df.copy())

    @pyqtSlot(Event)
    def _handle_stock_tick_update(self, event: Event):
        """處理通用 Tick 事件 (發射信號更新股票列表)"""
        data = event.data
        stock_id = data.get("symbol")
        if stock_id and stock_id != "TXF0": # 確保是股票代碼
            self.signal_update_stock_table.emit(data)

    @pyqtSlot(Event)
    def _handle_order_update(self, event: Event):
        """處理委託更新事件 (發射信號)"""
        # TODO: Decide how to update trading records (e.g., emit single order or fetch full list)
        # For now, just print in the handler is okay, but ideally emit a signal
        # self.signal_update_trading_records.emit([event.data]) # Example: emit single order
        print(f"GUI Event Handler: Order Update - {event.data}") # Keep print for now

    @pyqtSlot(Event)
    def _handle_account_update(self, event: Event):
        """處理賬戶資金更新事件 (發射信號)"""
        # TODO: Implement signal emission for account update
        # self.signal_update_account.emit(event.data) # Example
        # print(f"GUI Event Handler: Account Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_position_update(self, event: Event):
        """處理持倉更新事件 (發射信號)"""
        # TODO: Implement signal emission for position update
        # self.signal_update_position.emit(event.data) # Example
        # print(f"GUI Event Handler: Position Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_account_update(self, event: Event):
        """處理賬戶資金更新事件 (發射信號)"""
        # TODO: Implement signal emission for account update
        # self.signal_update_account.emit(event.data) # Example
        # print(f"GUI Event Handler: Account Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_log_update(self, event: Event):
        """處理日誌事件 (發射信號)"""
        self.signal_update_log.emit(str(event.data))

    @pyqtSlot(Event)
    def _handle_connection_status_change(self, event: Event):
        """處理連接狀態變更事件 (發射信號)"""
        self.signal_update_connection_status.emit(event.data)

    # --- 其他方法 ---
    def initUI(self):
        # 這個方法似乎與 __init__ 重複，可以考慮移除或合併
        pass

    # _connect_api 方法不再需要

    def update_time_display(self):
        """僅更新時間相關的顯示"""
        now = datetime.now()
        current_date = now.date()
        is_trading_day = now.weekday() < 5

        if is_trading_day:
            trading_day_text = f"{current_date.strftime('%Y/%m/%d')}"
        else:
            trading_day_text = f"{current_date.strftime('%Y/%m/%d')} (非交易日)"
        if hasattr(self, 'trading_day_label'):
            self.trading_day_label.setText(trading_day_text)
        if hasattr(self, 'last_update_label'):
            self.last_update_label.setText(f"{now.strftime('%H:%M:%S')}")
        self.update_market_status_display()

    def update_market_status_display(self):
         """僅更新市場狀態顯示（時間除外）"""
         now = datetime.now()
         current_time = now.time()
         is_weekday = now.weekday() < 5
         is_day_session = time(8, 45) <= current_time <= time(13, 45)
         is_night_session = (time(15, 0) <= current_time <= time(23, 59)) or (time(0, 0) <= current_time < time(5, 0))
         is_market_open = is_weekday and (is_day_session or is_night_session)

         if is_market_open:
             status_text = "日盤交易中" if is_day_session else "夜盤交易中"
             color = "#33ff33" if is_day_session else "#3399ff"
         else:
             status_text = "已收盤"
             color = "#ff3333"
         if hasattr(self, 'market_status_label'):
             self.market_status_label.setText(status_text)
             self.market_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _init_market_data_panel(self):
        """初始化市場數據面板"""
        self.market_data_panel = QGroupBox("市場與期貨狀態")
        market_layout = QVBoxLayout(self.market_data_panel)

        market_status_group = QWidget()
        market_status_layout = QGridLayout(market_status_group)
        market_status_layout.setContentsMargins(0, 5, 0, 5)

        market_status_layout.addWidget(QLabel("交易日:"), 0, 0)
        self.trading_day_label = QLabel("--")
        self.trading_day_label.setToolTip("當前或下一個交易日期")
        market_status_layout.addWidget(self.trading_day_label, 0, 1)

        market_status_layout.addWidget(QLabel("市場狀態:"), 0, 2)
        self.market_status_label = QLabel("未知")
        self.market_status_label.setStyleSheet("color: gray;")
        self.market_status_label.setToolTip("顯示當前市場開/收盤狀態")
        market_status_layout.addWidget(self.market_status_label, 0, 3)

        market_status_layout.addWidget(QLabel("連線狀態:"), 1, 0)
        self.connection_status_label = QLabel("未知") # GUI 內部狀態標籤
        self.connection_status_label.setStyleSheet("color: gray;")
        self.connection_status_label.setToolTip("顯示與交易 API 的連接狀態")
        market_status_layout.addWidget(self.connection_status_label, 1, 1)

        market_status_layout.addWidget(QLabel("最後更新:"), 1, 2)
        self.last_update_label = QLabel("--")
        self.last_update_label.setToolTip("介面時間更新")
        market_status_layout.addWidget(self.last_update_label, 1, 3)

        market_layout.addWidget(market_status_group)

        futures_data_group = QWidget()
        futures_data_layout = QGridLayout(futures_data_group)
        futures_data_layout.setContentsMargins(0, 5, 0, 5)

        futures_data_layout.addWidget(QLabel("台指期價格:"), 0, 0)
        self.futures_price_label = QLabel("--")
        self.futures_price_label.setToolTip("最近的台指期貨成交價格")
        futures_data_layout.addWidget(self.futures_price_label, 0, 1)

        futures_data_layout.addWidget(QLabel("成交量:"), 0, 2)
        self.futures_volume_label = QLabel("--")
        self.futures_volume_label.setToolTip("最近一筆台指期貨成交量")
        futures_data_layout.addWidget(self.futures_volume_label, 0, 3)

        futures_data_layout.addWidget(QLabel("漲跌:"), 1, 0)
        self.futures_change_label = QLabel("--")
        self.futures_change_label.setToolTip("台指期貨相較於昨日收盤價的漲跌幅")
        futures_data_layout.addWidget(self.futures_change_label, 1, 1, 1, 3)

        market_layout.addWidget(futures_data_group)
        market_layout.addStretch()

        self.main_layout.addWidget(self.market_data_panel, 0, 0)

    def create_icon_from_text(self, text, color=QColor(255, 255, 255)):
        """從文字創建圖標"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setPen(color)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)

    def _init_indicator_panel(self):
        """初始化指標選擇面板"""
        indicator_group = QGroupBox('技術分析工具')
        indicator_layout = QVBoxLayout(indicator_group)

        period_widget = QWidget()
        period_layout = QHBoxLayout(period_widget)
        period_layout.addWidget(QLabel('K線週期:'))
        self.period_combo = QComboBox()
        self.period_combo.addItems(['15m', '30m', '1h', '日K'])
        self.period_combo.currentTextChanged.connect(self.update_charts)
        self.period_combo.setToolTip("選擇圖表顯示的K線時間週期")
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        indicator_layout.addWidget(period_widget)

        ma_widget = QWidget()
        ma_layout = QHBoxLayout(ma_widget)
        self.ma_combos = []
        for i in range(3):
            ma_combo = QComboBox()
            ma_combo.addItems(['無', 'MA5', 'MA10', 'MA20', 'MA60', 'MA120', 'EMA12', 'EMA26'])
            ma_combo.currentIndexChanged.connect(self.update_charts)
            ma_combo.setToolTip(f"選擇第 {i+1} 條移動平均線")
            self.ma_combos.append(ma_combo)
            ma_layout.addWidget(QLabel(f'MA{i+1}:'))
            ma_layout.addWidget(ma_combo)
        ma_layout.addStretch()
        indicator_layout.addWidget(ma_widget)

        macd_widget = QWidget()
        macd_layout = QHBoxLayout(macd_widget)
        self.macd_enabled = QCheckBox("MACD")
        self.macd_enabled.toggled.connect(self.update_charts)
        self.macd_enabled.setToolTip("啟用/禁用 MACD 指標顯示")
        macd_layout.addWidget(self.macd_enabled)
        macd_layout.addStretch()
        indicator_layout.addWidget(macd_widget)

        rsi_widget = QWidget()
        rsi_layout = QHBoxLayout(rsi_widget)
        self.rsi_enabled = QCheckBox("RSI")
        self.rsi_enabled.toggled.connect(self.update_charts)
        self.rsi_enabled.setToolTip("啟用/禁用 RSI 指標顯示")
        rsi_layout.addWidget(self.rsi_enabled)
        rsi_layout.addStretch()
        indicator_layout.addWidget(rsi_widget)

        sr_widget = QWidget()
        sr_layout = QHBoxLayout(sr_widget)
        self.sr_enabled = QCheckBox("支撐/阻力")
        self.sr_enabled.toggled.connect(self.update_charts)
        self.sr_enabled.setToolTip("啟用/禁用自動計算的支撐與阻力位顯示")
        sr_layout.addWidget(self.sr_enabled)
        sr_layout.addStretch()
        indicator_layout.addWidget(sr_widget)

        indicator_layout.addStretch()
        self.main_layout.addWidget(indicator_group, 0, 1)

    def _init_charts(self):
        """初始化圖表區域"""
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        self.figure = Figure(figsize=(10, 6), facecolor='#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        self.main_layout.addWidget(chart_widget, 1, 1, 1, 2)
        self.update_charts() # Draw initial empty chart

    def update_charts(self):
        """更新K線圖表"""
        self.figure.clear()
        ax1 = self.figure.add_subplot(111)
        ax1.set_facecolor('#1e1e1e')
        ax1.tick_params(axis='x', colors='white')
        ax1.tick_params(axis='y', colors='white')
        ax1.xaxis.label.set_color('white')
        ax1.yaxis.label.set_color('white')

        period_map = {'15m': '15分鐘', '30m': '30分鐘', '1h': '1小時', '日K': '日K'}
        selected_period_key = self.period_combo.currentText()
        selected_period_display = period_map.get(selected_period_key, selected_period_key)

        df = self.current_kbars.get(selected_period_key, pd.DataFrame())

        if df is None or df.empty:
            ax1.text(0.5, 0.5, '無可用數據', horizontalalignment='center',
                     verticalalignment='center', transform=ax1.transAxes, color='white')
            self.canvas.draw_idle()
            return

        if not isinstance(df.index, pd.DatetimeIndex):
             try:
                 df.index = pd.to_datetime(df.index)
             except Exception as e:
                 print(f"轉換索引為 DatetimeIndex 失敗: {e}")
                 ax1.text(0.5, 0.5, '索引格式錯誤', horizontalalignment='center',
                          verticalalignment='center', transform=ax1.transAxes, color='white')
                 self.canvas.draw_idle()
                 return
        try:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        except Exception as e:
            print(f"轉換數據類型失敗: {e}")
            ax1.text(0.5, 0.5, '數據類型錯誤', horizontalalignment='center',
                     verticalalignment='center', transform=ax1.transAxes, color='white')
            self.canvas.draw_idle()
            return

        mc = mpf.make_marketcolors(up='#00b060', down='#fe3032', edge='inherit', wick='inherit', volume='inherit')
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridcolor='#444444',
                               facecolor='#1e1e1e', figcolor='#1e1e1e', y_on_right=False)

        addplots = []
        for ma_combo in self.ma_combos:
            ma_type = ma_combo.currentText()
            if ma_type != '無':
                try:
                    period = int(ma_type[2:]) if ma_type.startswith('MA') else int(ma_type[3:])
                    if ma_type.startswith('MA'):
                        ma_data = df['Close'].rolling(window=period).mean()
                    else: # EMA
                        ma_data = df['Close'].ewm(span=period, adjust=False).mean()
                    addplots.append(mpf.make_addplot(ma_data, ax=ax1))
                except Exception as e:
                    print(f"計算 {ma_type} 失敗: {e}")

        try:
             mpf.plot(df, type='candle', style=s, ax=ax1, volume=False,
                      addplot=addplots, title=f'台指期 {selected_period_display} K線圖')
        except Exception as e:
             print(f"繪製圖表時發生錯誤: {e}")
             ax1.text(0.5, 0.5, f'繪製圖表錯誤: {e}', horizontalalignment='center',
                      verticalalignment='center', transform=ax1.transAxes, color='white')
             if not ax1.lines:
                 try:
                     mpf.plot(df, type='candle', style=s, ax=ax1, volume=False,
                              title=f'台指期 {selected_period_display} K線圖 (無指標)')
                 except Exception as basic_e:
                      print(f"繪製基礎K線圖也失敗: {basic_e}")

        try:
            self.canvas.draw_idle()
        except Exception as e:
            print(f"更新圖表畫布時出錯: {e}")

    # --- 原始事件處理函數 (修改為發射信號) ---
    @pyqtSlot(Event)
    def _handle_futures_update(self, event: Event):
        """處理期貨數據更新事件 (發射信號)"""
        # 不直接更新 UI，而是發射信號
        self.signal_update_futures.emit(event.data)

    @pyqtSlot(Event)
    def _handle_kbars_update(self, event: Event):
        """處理K線數據更新事件 (發射信號)"""
        data = event.data
        timeframe = data.get("timeframe")
        df = data.get("dataframe")
        if timeframe and df is not None:
            # 傳遞 DataFrame 的副本以避免潛在的跨線程問題
            self.signal_update_kbars.emit(timeframe, df.copy())

    @pyqtSlot(Event)
    def _handle_stock_tick_update(self, event: Event):
        """處理通用 Tick 事件 (發射信號更新股票列表)"""
        data = event.data
        stock_id = data.get("symbol")
        if stock_id and stock_id != "TXF0": # 確保是股票代碼
            self.signal_update_stock_table.emit(data)

    @pyqtSlot(Event)
    def _handle_order_update(self, event: Event):
        """處理委託更新事件 (發射信號)"""
        # TODO: Implement signal emission for trading records update
        # self.signal_update_trading_records.emit([event.data]) # Example
        # print(f"GUI Event Handler: Order Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_trade_update(self, event: Event):
        """處理成交更新事件 (發射信號)"""
        # TODO: Implement signal emission for trading records update
        # self.signal_update_trading_records.emit([event.data]) # Example
        # print(f"GUI Event Handler: Trade Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_position_update(self, event: Event):
        """處理持倉更新事件 (發射信號)"""
        # TODO: Implement signal emission for position update
        # self.signal_update_position.emit(event.data) # Example
        # print(f"GUI Event Handler: Position Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_account_update(self, event: Event):
        """處理賬戶資金更新事件 (發射信號)"""
        # TODO: Implement signal emission for account update
        # self.signal_update_account.emit(event.data) # Example
        # print(f"GUI Event Handler: Account Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_log_update(self, event: Event):
        """處理日誌事件"""
        log_message = event.data
        self.status_bar.showMessage(str(log_message), 5000)

    @pyqtSlot(Event) # Changed to accept Event object
    def _handle_connection_status_change(self, event: Event):
        """處理連接狀態變更信號"""
        data = event.data
        connected = data.get("connected", False)
        message = data.get("message", "未知狀態")
        gateway_name = data.get("gateway_name", "未知接口")

        status_text = f"{gateway_name} 狀態: {message}"
        if connected:
            color = "green"
            conn_label_text = "已連接"
        elif "模擬數據" in message or "API密鑰未設置" in message or "登入憑證錯誤" in message:
            color = "orange"
            conn_label_text = message
        else:
            color = "red"
            conn_label_text = "連接失敗"

        if hasattr(self, 'connection_status'):
             self.connection_status.setText(status_text)
             self.connection_status.setStyleSheet(f"color: {color};")
        if hasattr(self, 'connection_status_label'):
             self.connection_status_label.setText(conn_label_text)
             self.connection_status_label.setStyleSheet(f"color: {color};")

    @pyqtSlot(str, int)
    def _handle_status_bar_message(self, message, timeout):
        """處理狀態欄消息信號"""
        self.status_bar.showMessage(message, timeout)

    # --- 輔助更新方法 ---
    def _update_market_data_display(self, data):
        """僅更新市場數據面板的顯示 (由信號觸發)"""
        # Needs refactoring based on how market analysis data is structured and sent
        if not data: return
        trend = data.get('trend', '--')
        # ... (rest of the method remains similar) ...

    def _add_stock_to_table(self, stock_id, data):
         """向股票表格添加新行"""
         row_count = self.stock_table.rowCount()
         self.stock_table.insertRow(row_count)
         self._update_stock_table_row(row_count, data)

    def _update_stock_table_row(self, row, data):
         """更新股票表格的指定行"""
         try:
             stock_id = data.get('symbol', data.get('code', '--'))
             self.stock_table.setItem(row, 0, QTableWidgetItem(stock_id))

             price = data.get('last_price', data.get('price'))
             price_text = f"{price:.2f}" if price is not None else "--"
             self.stock_table.setItem(row, 1, QTableWidgetItem(price_text))

             # Calculate change percentage if pre_close is available
             change_ratio = None
             pre_close = data.get('pre_close')
             if price is not None and pre_close is not None and pre_close != 0 and not np.isnan(pre_close):
                 change_ratio = ((price - pre_close) / pre_close) * 100

             change_text = f"{change_ratio:.2f}%" if change_ratio is not None else "--"
             change_item = QTableWidgetItem(change_text)
             if change_ratio is not None:
                 color = QColor(0, 200, 0) if change_ratio > 0 else QColor(200, 0, 0) if change_ratio < 0 else QColor(0,0,0)
                 change_item.setForeground(color)
             self.stock_table.setItem(row, 2, change_item)

             volume = data.get('volume', data.get('total_volume'))
             volume_text = "--"
             if volume is not None:
                 if volume >= 1000000: volume_text = f"{volume/1000000:.2f}M"
                 elif volume >= 1000: volume_text = f"{volume/1000:.1f}K"
                 else: volume_text = str(int(volume))
             self.stock_table.setItem(row, 3, QTableWidgetItem(volume_text))

             # Trend and Signal should come from a strategy app event
             trend = data.get('trend', '--') # Placeholder
             trend_item = QTableWidgetItem(trend)
             # ... (set color based on trend) ...
             self.stock_table.setItem(row, 4, trend_item)

             signal_type = data.get('signal_type', '--') # Placeholder
             signal_item = QTableWidgetItem(signal_type)
             # ... (set color based on signal) ...
             self.stock_table.setItem(row, 5, signal_item)

             update_time = data.get('datetime', data.get('last_update'))
             time_text = update_time.strftime('%H:%M:%S') if isinstance(update_time, datetime) else "--"
             self.stock_table.setItem(row, 6, QTableWidgetItem(time_text))

         except Exception as e:
             print(f"更新股票表格行 {row} (ID: {data.get('symbol', 'N/A')}) 失敗: {e}")
             for col in range(self.stock_table.columnCount()):
                 if self.stock_table.item(row, col) is None:
                     self.stock_table.setItem(row, col, QTableWidgetItem("錯誤"))

    def get_stock_name(self, stock_id):
        # This might need to fetch from main_engine or a dedicated contract management part
        stock_names = {
            '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2412': '中華電',
            '2308': '台達電', '2303': '聯電', '2882': '國泰金', '1301': '台塑',
            '2881': '富邦金', '2002': '中鋼', '2886': '兆豐金', '2891': '中信金',
            '3034': '聯詠', '2327': '國巨', '2884': '玉山金', '2885': '元大金'
        }
        return stock_names.get(stock_id, f'股票{stock_id}')

    def is_market_open(self):
        # This logic might be better placed in the engine or a utility module
        now = datetime.now()
        current_time = now.time()
        is_weekday = now.weekday() < 5
        is_trading_hours = time(9, 0) <= current_time <= time(13, 30) # Simplified, needs refinement for futures
        return is_weekday and is_trading_hours

    def show_stock_table_menu(self, position):
        menu = QMenu()
        selected_row = self.stock_table.currentRow()
        if selected_row >= 0:
            stock_id_item = self.stock_table.item(selected_row, 0)
            if stock_id_item:
                stock_id = stock_id_item.text()
                remove_stock = menu.addAction("取消訂閱") # Corrected indentation
                remove_stock.triggered.connect(lambda: self._unsubscribe_stock(stock_id)) # Corrected indentation
                menu.exec(self.stock_table.viewport().mapToGlobal(position)) # Corrected indentation

    def _unsubscribe_stock(self, stock_id):
        """取消訂閱股票行情"""
        print(f"GUI: Requesting unsubscribe for {stock_id}")
        contract = self.main_engine.get_contract(stock_id, "Shioaji")
        if contract:
            req = {"contract": contract}
            self.main_engine.unsubscribe(req, "Shioaji") # 調用 MainEngine 的 unsubscribe
            self.status_bar.showMessage(f"已發送取消訂閱請求: {stock_id}", 3000)
            # Remove row immediately for now, ideally wait for confirmation event
            for row in range(self.stock_table.rowCount()):
                 if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == stock_id:
                     self.stock_table.removeRow(row)
                     break
        else:
            self.status_bar.showMessage(f"取消訂閱失敗，找不到合約: {stock_id}", 3000)

    def _show_technical_indicators(self, stock_id):
        QMessageBox.information(self, "信息", f"技術指標現在集成在主圖表中。請使用右側面板控制。")

    def _show_signal_history(self, stock_id):
         QMessageBox.information(self, "信息", f"信號歷史功能待整合到策略應用模組中。")

    def _show_advanced_indicators(self):
        QMessageBox.information(self, "信息", f"進階指標功能待整合。")

    def _add_index(self):
        """訂閱大盤指數"""
        print("GUI: Requesting subscribe for 大盤指數 (e.g., TXF)")
        # Need to get the actual contract object for the index futures
        # contract = self.main_engine.get_contract("TXF0") # Example, replace with actual logic
        # if contract:
        #     req = {"contract": contract, "quote_type": sj.constant.QuoteType.Tick}
        #     self.main_engine.subscribe(req, "Shioaji")
        #     self.status_bar.showMessage(f"已發送訂閱大盤指數請求", 3000)
        # else:
        #     self.status_bar.showMessage(f"找不到大盤指數合約", 3000)
        self.status_bar.showMessage(f"訂閱大盤指數功能待實現", 3000) # Placeholder

    def _init_stock_list(self):
        """初始化股票列表"""
        stocks_group = QGroupBox("股票監視清單")
        stocks_layout = QVBoxLayout(stocks_group)

        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        add_button = QPushButton("添加/訂閱股票")
        add_button.clicked.connect(self.add_stock)
        add_button.setToolTip("添加新的股票代碼到監視列表並訂閱行情")
        buttons_layout.addWidget(add_button)
        # refresh_button = QPushButton("刷新列表") # Removed
        self.add_index_button = QPushButton("訂閱大盤")
        self.add_index_button.clicked.connect(self._add_index)
        self.add_index_button.setToolTip("訂閱大盤指數行情")
        buttons_layout.addWidget(self.add_index_button)
        buttons_layout.addStretch()
        stocks_layout.addWidget(buttons_widget)

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(7)
        self.stock_table.setHorizontalHeaderLabels(["代碼", "價格", "漲跌%", "總量", "趨勢", "信號", "更新"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.stock_table.horizontalHeader().setStretchLastSection(True)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stock_table.customContextMenuRequested.connect(self.show_stock_table_menu)
        stocks_layout.addWidget(self.stock_table)

        self.main_layout.addWidget(stocks_group, 1, 0, 2, 1)

        # self.update_stock_list() # Initial load removed

    def _init_strategy_list(self):
        """初始化交易策略列表"""
        # Needs refactoring based on strategy app
        try:
            # Placeholder
            # strategy_names = self.main_engine.get_app("StrategyApp").get_strategy_names()
            strategy_names = ["策略A", "策略B"]
            # Check if self.strategy_combo exists before using it
            if hasattr(self, 'strategy_combo'):
                current_strategy = self.strategy_combo.currentText()
                self.strategy_combo.clear()
                if strategy_names:
                    self.strategy_combo.addItems(strategy_names)
                    index = self.strategy_combo.findText(current_strategy)
                    if index >= 0:
                        self.strategy_combo.setCurrentIndex(index)
                else:
                    self.strategy_combo.addItem("無可用策略")
            else:
                 print("警告: strategy_combo 未在 _init_strategy_list 調用前初始化")
        except Exception as e:
            print(f"初始化策略列表失敗: {str(e)}")
            if hasattr(self, 'strategy_combo'):
                self.strategy_combo.clear()
                self.strategy_combo.addItem("無可用策略")

    def _change_strategy(self, strategy_name):
        """更改當前使用的交易策略"""
        if not strategy_name or strategy_name == "無可用策略": return
        print(f"GUI: Requesting change strategy to {strategy_name}")
        # Example: self.main_engine.get_app("StrategyApp").set_active_strategy(strategy_name)
        self.status_bar.showMessage(f"已請求切換到策略: {strategy_name}", 3000)

    def _create_custom_strategy(self):
        """打開自定義策略對話框"""
        QMessageBox.information(self, "提示", "自定義策略功能正在重構中。")

    def _show_strategy_params_dialog(self):
        try:
            from strategy_params_dialog import StrategyParamsDialog
            # 假設有 self.auto_trader_manager.trader.signal_gen
            signal_gen = None
            if self.auto_trader_manager and hasattr(self.auto_trader_manager, "trader"):
                signal_gen = getattr(self.auto_trader_manager.trader, "signal_gen", None)
            if not signal_gen:
                QMessageBox.warning(self, "錯誤", "找不到策略模組")
                return
            # 假設策略參數存於 signal_gen.strategy_params
            params = getattr(signal_gen, "strategy_params", {"short_window":5, "long_window":20, "rsi_period":14})
            dialog = StrategyParamsDialog(params, self)
            if dialog.exec():
                new_params = dialog.get_params()
                # 更新 signal_gen 內的參數
                if hasattr(signal_gen, "strategy_params"):
                    signal_gen.strategy_params.update(new_params)
                else:
                    signal_gen.strategy_params = new_params
                QMessageBox.information(self, "成功", "策略參數已更新")
        except Exception as e:
            QMessageBox.warning(self, "錯誤", f"策略參數設定失敗: {e}")

    def _init_auto_trading_panel(self):
        """初始化自動交易面板"""
        auto_trading_group = QGroupBox("自動交易")
        auto_trading_layout = QVBoxLayout(auto_trading_group)

        strategy_widget = QWidget()
        strategy_layout = QGridLayout(strategy_widget)
        strategy_layout.addWidget(QLabel("策略:"), 0, 0)
        self.strategy_combo = QComboBox() # Define here
        self._init_strategy_list() # Populate
        self.strategy_combo.currentTextChanged.connect(self._change_strategy)
        self.strategy_combo.setToolTip("選擇用於自動交易的策略")
        strategy_layout.addWidget(self.strategy_combo, 0, 1)
        self.custom_strategy_btn = QPushButton("自訂")
        self.custom_strategy_btn.clicked.connect(self._create_custom_strategy)
        self.custom_strategy_btn.setToolTip("創建或修改自定義交易策略參數")
        strategy_layout.addWidget(self.custom_strategy_btn, 0, 2)
        self.auto_trading_checkbox = QCheckBox("啟用自動交易")
        self.auto_trading_checkbox.toggled.connect(self._toggle_auto_trading)
        self.auto_trading_checkbox.setToolTip("勾選以啟用基於當前策略和設置的自動交易")
        strategy_layout.addWidget(self.auto_trading_checkbox, 1, 0)
        settings_btn = QPushButton("設置")
        settings_btn.clicked.connect(self._show_auto_trading_settings)
        settings_btn.setToolTip("配置自動交易的風險控制參數")
        strategy_layout.addWidget(settings_btn, 1, 1, 1, 2)
        auto_trading_layout.addWidget(strategy_widget)

        trading_record_group = QGroupBox("交易記錄")
        trading_record_layout = QVBoxLayout(trading_record_group)
        self.trading_record_table = QTableWidget()
        self.trading_record_table.setColumnCount(8)
        self.trading_record_table.setHorizontalHeaderLabels(["時間", "代碼", "操作", "數量", "價格", "金額", "狀態", "盈虧"])
        self.trading_record_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.trading_record_table.horizontalHeader().setStretchLastSection(True)
        self.trading_record_table.setAlternatingRowColors(True)
        trading_record_layout.addWidget(self.trading_record_table)
        auto_trading_layout.addWidget(trading_record_group)

        # 新增自動交易訊號與日誌顯示區
        self.auto_trading_log = QGroupBox("自動交易訊號與日誌")
        log_layout = QVBoxLayout(self.auto_trading_log)
        from PyQt6.QtWidgets import QTextEdit
        self.auto_trading_log_text = QTextEdit()
        self.auto_trading_log_text.setReadOnly(True)
        self.auto_trading_log_text.setStyleSheet("background-color: #1e1e1e; color: #33ff33; font-family: Consolas;")
        log_layout.addWidget(self.auto_trading_log_text)
        auto_trading_layout.addWidget(self.auto_trading_log)

        self.main_layout.addWidget(auto_trading_group, 2, 1)

        # self._update_trading_records_table(...) # Initial update removed

    def _update_trading_records_table(self, records):
         """更新交易記錄表格的輔助方法"""
         # This should be triggered by EVENT_TRADE or EVENT_ORDER
         # Needs refactoring based on actual event data structure
         pass

    def _update_trading_records_table_with_order(self, order_data: dict):
        """使用委託數據更新交易記錄表"""
        # Find existing row or add new one
        # Update relevant columns (Time, Code, Action, Qty, Price, Status)
        pass

    def _update_trading_records_table_with_trade(self, trade_data: dict):
        """使用成交數據更新交易記錄表"""
        # Find related order row
        # Update relevant columns (Traded Qty, PnL if applicable, Status)
        pass

    def _update_trading_records(self):
        # Obsolete, handled by events
        pass

    def _show_auto_trading_settings(self):
        QMessageBox.information(self, "提示", "自動交易設置功能正在重構中。")

    def _toggle_auto_trading(self, checked):
        print(f"GUI: Requesting auto trading state: {checked}")
        if not self.auto_trader_manager:
            self.status_bar.showMessage("自動交易模組未載入", 5000)
            return

        if checked:
            try:
                self.auto_trader_manager.start()
                self.auto_trading_checkbox.setText("自動交易中")
                self.auto_trading_checkbox.setStyleSheet("color: green; font-weight: bold;")
                self.status_bar.showMessage("自動交易已啟動", 5000)
            except Exception as e:
                print(f"啟動自動交易失敗: {e}")
                self.status_bar.showMessage(f"啟動自動交易失敗: {e}", 5000)
                self.auto_trading_checkbox.setChecked(False)
        else:
            try:
                self.auto_trader_manager.stop()
                self.auto_trading_checkbox.setText("啟用自動交易")
                self.auto_trading_checkbox.setStyleSheet("")
                self.status_bar.showMessage("自動交易已停止", 5000)
            except Exception as e:
                print(f"停止自動交易失敗: {e}")
                self.status_bar.showMessage(f"停止自動交易失敗: {e}", 5000)

    def _init_backtest_panel(self):
        """初始化回測面板"""
        backtest_group = QGroupBox("策略回測")
        backtest_layout = QVBoxLayout(backtest_group)
        # ... (Keep UI elements, functionality needs rework) ...
        settings_widget = QWidget()
        settings_layout = QGridLayout(settings_widget)
        settings_layout.addWidget(QLabel("股票:"), 0, 0)
        self.backtest_stock_combo = QComboBox()
        self.backtest_stock_combo.setEditable(True)
        self.backtest_stock_combo.setToolTip("選擇或輸入要進行回測的股票代碼")
        settings_layout.addWidget(self.backtest_stock_combo, 0, 1)
        settings_layout.addWidget(QLabel("策略:"), 0, 2)
        self.backtest_strategy_combo = QComboBox()
        self.backtest_strategy_combo.setToolTip("選擇用於回測的交易策略")
        settings_layout.addWidget(self.backtest_strategy_combo, 0, 3)
        settings_layout.addWidget(QLabel("開始:"), 1, 0)
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-6))
        self.start_date_edit.setToolTip("設定回測的開始日期")
        settings_layout.addWidget(self.start_date_edit, 1, 1)
        settings_layout.addWidget(QLabel("結束:"), 1, 2)
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setToolTip("設定回測的結束日期")
        settings_layout.addWidget(self.end_date_edit, 1, 3)
        settings_layout.addWidget(QLabel("資金:"), 2, 0)
        self.initial_capital_spin = QSpinBox()
        self.initial_capital_spin.setRange(10000, 10000000)
        self.initial_capital_spin.setSingleStep(10000)
        self.initial_capital_spin.setValue(100000)
        self.initial_capital_spin.setPrefix("NT$ ")
        self.initial_capital_spin.setToolTip("設定回測的初始模擬資金")
        settings_layout.addWidget(self.initial_capital_spin, 2, 1)
        self.run_backtest_btn = QPushButton("執行回測")
        self.run_backtest_btn.clicked.connect(self._run_backtest)
        self.run_backtest_btn.setToolTip("使用選定的股票、策略和參數執行歷史回測")
        settings_layout.addWidget(self.run_backtest_btn, 2, 2, 1, 2)
        backtest_layout.addWidget(settings_widget)

        self.backtest_results_tabs = QTabWidget()

        # 新增委託單分頁
        order_widget = QWidget()
        order_layout = QVBoxLayout(order_widget)
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(8)
        self.order_table.setHorizontalHeaderLabels(["時間", "代碼", "方向", "數量", "價格", "狀態", "委託ID", "操作"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.order_table.horizontalHeader().setStretchLastSection(True)
        self.order_table.setAlternatingRowColors(True)
        order_layout.addWidget(self.order_table)
        self.backtest_results_tabs.addTab(order_widget, "委託單")

        # 新增成交記錄分頁
        trade_widget = QWidget()
        trade_layout = QVBoxLayout(trade_widget)
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(7)
        self.trade_table.setHorizontalHeaderLabels(["時間", "代碼", "方向", "數量", "價格", "成交ID", "委託ID"])
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.trade_table.horizontalHeader().setStretchLastSection(True)
        self.trade_table.setAlternatingRowColors(True)
        trade_layout.addWidget(self.trade_table)
        self.backtest_results_tabs.addTab(trade_widget, "成交記錄")

        # 原有績效指標分頁
        performance_widget = QWidget()
        performance_layout = QVBoxLayout(performance_widget)
        self.performance_table = QTableWidget()
        self.performance_table.setRowCount(5)
        self.performance_table.setColumnCount(2)
        self.performance_table.setHorizontalHeaderLabels(["指標", "數值"])
        self.performance_table.setVerticalHeaderLabels(["總回報率", "年化回報率", "夏普比率", "最大回撤", "勝率"])
        self.performance_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        performance_layout.addWidget(self.performance_table)
        self.backtest_results_tabs.addTab(performance_widget, "績效指標")

        # 原有交易記錄分頁
        trades_widget = QWidget()
        trades_layout = QVBoxLayout(trades_widget)
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(7)
        self.trades_table.setHorizontalHeaderLabels(["日期", "操作", "價格", "數量", "金額", "單筆盈虧", "盈虧%"])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.trades_table.horizontalHeader().setStretchLastSection(True)
        trades_layout.addWidget(self.trades_table)
        self.backtest_results_tabs.addTab(trades_widget, "歷史交易")

        # 權益曲線分頁
        equity_curve_widget = QWidget()
        equity_layout = QVBoxLayout(equity_curve_widget)
        self.equity_curve_label = QLabel("尚未生成權益曲線")
        self.equity_curve_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        equity_layout.addWidget(self.equity_curve_label)
        self.backtest_results_tabs.addTab(equity_curve_widget, "權益曲線")

        backtest_layout.addWidget(self.backtest_results_tabs)
        self.main_layout.addWidget(backtest_group, 2, 2)

        self._update_backtest_stock_list()

    def _update_backtest_stock_list(self):
        """更新回測股票和策略列表"""
        # Needs refactoring
        self.backtest_stock_combo.clear()
        stock_ids = ["AAPL", "GOOG"] # Placeholder
        if stock_ids:
            self.backtest_stock_combo.addItems(stock_ids)
        else:
            self.backtest_stock_combo.addItem("無可用股票")

        self.backtest_strategy_combo.clear()
        strategy_names = ["策略A", "策略B"] # Placeholder
        if strategy_names:
            self.backtest_strategy_combo.addItems(strategy_names)
        else:
            self.backtest_strategy_combo.addItem("無可用策略")

    def _init_valuation_panel(self):
        """初始化左側估值面板"""
        valuation_group = QGroupBox("左側仔特價區估值")
        valuation_layout = QVBoxLayout(valuation_group)

        # 股票選擇
        valuation_input_widget = QWidget()
        valuation_input_layout = QHBoxLayout(valuation_input_widget)
        valuation_input_layout.addWidget(QLabel("估值股票 (從列表選取或手動輸入):"))
        self.valuation_stock_input = QLineEdit()
        self.valuation_stock_input.setPlaceholderText("輸入代碼，用逗號分隔")
        valuation_input_layout.addWidget(self.valuation_stock_input)
        valuation_layout.addWidget(valuation_input_widget)

        # 執行按鈕
        self.valuation_button = QPushButton("執行左側估值")
        self.valuation_button.clicked.connect(self._run_valuation)
        self.valuation_button.setToolTip("使用 valuation_engine.py 執行估值")
        valuation_layout.addWidget(self.valuation_button)

        # 結果顯示區
        from PyQt6.QtWidgets import QTextEdit
        self.valuation_result_text = QTextEdit()
        self.valuation_result_text.setReadOnly(True)
        self.valuation_result_text.setStyleSheet("background-color: #f0f0f0; color: #333;")
        valuation_layout.addWidget(self.valuation_result_text)

        # 將估值面板添加到主佈局
        self.main_layout.addWidget(valuation_group, 0, 2, 2, 1)

    def _init_left_value_zone_panel(self):
        """整合左側價值區 GUI 為主介面子面板"""
        left_value_zone_group = QGroupBox("左側仔特價區（進階版）")
        left_value_zone_layout = QVBoxLayout(left_value_zone_group)
        self.left_value_zone_widget = LeftValueZoneGUI()
        left_value_zone_layout.addWidget(self.left_value_zone_widget)
        self.main_layout.addWidget(left_value_zone_group, 3, 0, 1, 3)

    def _run_valuation(self):
        """執行左側估值"""
        input_codes_str = self.valuation_stock_input.text().strip()
        selected_codes = []
        if input_codes_str:
            selected_codes = [code.strip() for code in input_codes_str.split(',') if code.strip()]
        else:
            selected_items = self.stock_table.selectedItems()
            if selected_items:
                selected_rows = set(item.row() for item in selected_items)
                for row in selected_rows:
                    code_item = self.stock_table.item(row, 0)
                    if code_item:
                        selected_codes.append(code_item.text())
            else:
                QMessageBox.warning(self, "警告", "請至少在上方輸入框輸入股票代碼，或在監視列表中選取股票")
                return

        if not selected_codes:
            QMessageBox.warning(self, "警告", "請至少選擇或輸入一檔股票")
            return

        # 設定路徑
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, ".."))
        template_path = os.path.join(project_root, "..", "..", "工具-估估2.xlsx")
        output_dir = os.path.join(project_root, "..", "..", "outputs")

        self.valuation_result_text.clear()
        self.valuation_result_text.append(f"開始執行左側估值: {', '.join(selected_codes)}")
        self.valuation_result_text.append(f"使用模板: {template_path}")
        self.valuation_result_text.append(f"輸出目錄: {output_dir}")
        QApplication.processEvents()

        try:
            results = calculate_value(selected_codes, template_path, output_dir)
            self.valuation_result_text.append("\n--- 估值結果 ---")
            if results:
                for res in results:
                    self.valuation_result_text.append(f"股票: {res.get('stock_id', 'N/A')}")
                    if res.get("error"):
                        self.valuation_result_text.append(f"  錯誤: {res['error']}")
                    else:
                        self.valuation_result_text.append(f"  現價: {res.get('price', '--')}")
                        self.valuation_result_text.append(f"  EPS: {res.get('eps', '--')}")
                        self.valuation_result_text.append(f"  成長率: {res.get('growth', '--')}%")
                        self.valuation_result_text.append(f"  估算價值: {res.get('stock_value', '--')}")
                        self.valuation_result_text.append(f"  潛在報酬率: {res.get('profit_rate', '--')}%")
                    self.valuation_result_text.append("-" * 15)
            else:
                self.valuation_result_text.append("估值計算未返回結果或失敗。")
        except Exception as e:
            self.valuation_result_text.append(f"\n執行估值時發生未預期錯誤: {e}")
            import traceback
            self.valuation_result_text.append(traceback.format_exc())

    def _run_backtest(self):
        """執行回測"""
        QMessageBox.information(self, "提示", "回測功能正在重構中。")
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
                             QGroupBox, QFormLayout, QDateEdit, QSpinBox, QDoubleSpinBox,
                             QTabWidget, QHeaderView, QMenuBar, QMenu, QMessageBox,
                             QDialog, QLineEdit, QDialogButtonBox, QCheckBox, QApplication,
                             QStatusBar, QStyleFactory, QTimeEdit)
from PyQt6.QtCore import Qt, QTimer, QDate, QDateTime, QTime, pyqtSlot, QObject, QCoreApplication
from PyQt6.QtGui import QColor, QIcon, QAction, QFont, QPixmap, QPainter, QCursor, QImage
from PyQt6.QtCore import pyqtSignal # 導入 pyqtSignal
# import indicators # 指標計算移到策略或 App 中
# from main import TaiwanFuturesTrader # 移除舊導入
from core.engine import MainEngine # 導入新的主引擎
from core.event import EventEngine, Event, EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_POSITION, EVENT_ACCOUNT, EVENT_CONTRACT, EVENT_KBAR, EVENT_LOG, EVENT_CONNECTION_STATUS # 導入事件引擎和事件類型
from login import LoginDialog
from gateway.shioaji_gateway import ShioajiGateway
from gateway.api_gateway import ApiGateway # 確保導入
import os
from dotenv import load_dotenv
from modules.valuation_engine import calculate_value # 導入估值函數
import pandas as pd
from datetime import datetime, time, timedelta
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import mplfinance as mpf
import io
from  typing import Dict, Optional, Any # Import typing for hints

# 檢查 PIL 是否安裝
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL (Pillow) 庫未安裝，權益曲線圖將無法顯示。請使用 'pip install Pillow' 安裝。")


# （下方重複的 TradingWindow class 及其內容已自動移除，僅保留上方唯一正確版本）
    signal_update_futures = pyqtSignal(dict)
    signal_update_kbars = pyqtSignal(str, pd.DataFrame)
    signal_update_stock_table = pyqtSignal(dict) # 用於更新單個股票行或添加新行
    signal_update_log = pyqtSignal(str)
    signal_update_connection_status = pyqtSignal(dict)
    signal_update_trading_records = pyqtSignal(list) # 假設有一個更新交易記錄的信號

    # 修改 __init__ 以接收 main_engine 和 event_engine
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine

        # 新增自動交易管理器
        try:
            from auto_trader_manager import AutoTraderManager
            self.auto_trader_manager = AutoTraderManager()
            # 設定自動交易訊息回呼
            if self.auto_trader_manager and hasattr(self.auto_trader_manager, "trader"):
                self.auto_trader_manager.trader.set_log_callback(self.append_log)
        except Exception as e:
            print(f"載入 AutoTraderManager 失敗: {e}")
            self.auto_trader_manager = None
        self.current_kbars: Dict[str, pd.DataFrame] = { # 用於存儲 GUI 當前顯示的 K 線數據
            '15m': pd.DataFrame(),
            '30m': pd.DataFrame(),
            '1h': pd.DataFrame(),
            '日K': pd.DataFrame()
        }
        self.yesterday_close: Optional[float] = None # 昨收價
        self.stock_data_cache: Dict[str, Dict] = {} # 緩存股票數據以更新表格
        self._init_status_bar_timer() # 初始化狀態欄計時器

        # 設定窗口
        self.setWindowTitle('JoJo 量化交易系統 (重構版)')
        self.setGeometry(100, 100, 1600, 900)

        # 建立中央部件和主佈局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)

        # 初始化狀態欄
        self.status_bar = self.statusBar()
        self.status_bar.showMessage('歡迎使用 JoJo 量化交易系統')

        # 顯示連接狀態 (添加到狀態欄右側)
        self.connection_status = QLabel('API狀態: 未知') # 初始狀態
        self.connection_status.setStyleSheet('color: gray;')
        self.status_bar.addPermanentWidget(self.connection_status)

        # 初始化面板
        self._init_market_data_panel()
        self._init_stock_list()
        self._init_indicator_panel()
        self._init_charts()
        self._init_auto_trading_panel()
        self._init_backtest_panel()
        self._init_valuation_panel() # 初始化新的估值面板

        # 創建工具欄
        self.create_toolbar()

        # 設置時間更新定時器 (僅更新時間顯示)
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time_display)
        self.time_timer.start(1000)

        # 註冊事件處理函數
        self._register_event_handlers()
        # 連接信號到槽函數
        self._connect_signals()

        # 初始化一次UI狀態
        self.update_time_display()
        # self.update_stock_list() # 列表更新由事件觸發

    def _register_event_handlers(self):
        """註冊 GUI 需要處理的事件"""
        # 訂閱特定事件
        self.event_engine.register(EVENT_TICK + "TXF0", self._handle_futures_update) # 假設台指期代碼為 TXF0
        self.event_engine.register(EVENT_KBAR, self._handle_kbars_update)
        self.event_engine.register(EVENT_ORDER, self._handle_order_update)
        self.event_engine.register(EVENT_TRADE, self._handle_trade_update)
        self.event_engine.register(EVENT_POSITION, self._handle_position_update)
        self.event_engine.register(EVENT_ACCOUNT, self._handle_account_update)
        self.event_engine.register(EVENT_LOG, self._handle_log_update)
        self.event_engine.register(EVENT_CONNECTION_STATUS, self._handle_connection_status_change)
        # 訂閱所有 Tick 事件來更新股票列表 (如果需要實時更新所有股票)
        self.event_engine.register(EVENT_TICK, self._handle_stock_tick_update) # Use general tick handler

    def _connect_signals(self):
        """連接 Qt 信號到對應的槽函數"""
        self.signal_update_futures.connect(self._update_futures_ui)
        self.signal_update_kbars.connect(self._update_kbars_ui)
        self.signal_update_stock_table.connect(self._update_stock_table_ui)
        self.signal_update_log.connect(self._update_log_ui)
        self.signal_update_connection_status.connect(self._update_connection_status_ui)
        self.signal_update_trading_records.connect(self._update_trading_records_ui) # 連接交易記錄信號

    def append_log(self, message: str):
        """將自動交易訊息加入日誌區"""
        try:
            self.auto_trading_log_text.append(message)
        except Exception as e:
            print(f"寫入自動交易日誌失敗: {e}")

    # --- 新增的 UI 更新槽函數 ---
    @pyqtSlot(dict)
    def _update_futures_ui(self, data):
        """在主執行緒中更新期貨 UI"""
        price = data.get('last_price')
        volume = data.get('volume')

        if price is not None:
            self.futures_price_label.setText(f"{price:.2f}")
        if volume is not None:
            self.futures_volume_label.setText(f"{volume:,}")

        if price is not None and self.yesterday_close:
            change = price - self.yesterday_close
            change_percent = (change / self.yesterday_close) * 100 if self.yesterday_close else 0
            color = 'green' if change >= 0 else 'red'
            self.futures_change_label.setText(f"{change:+.2f} ({change_percent:+.2f}%)")
            self.futures_change_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        elif price is not None:
             self.futures_change_label.setText("--")
             self.futures_change_label.setStyleSheet("")

    @pyqtSlot(str, pd.DataFrame)
    def _update_kbars_ui(self, timeframe, df):
        """在主執行緒中更新 K 線數據和圖表"""
        self.current_kbars[timeframe] = df
        if self.period_combo.currentText() == timeframe:
            self.update_charts()

    @pyqtSlot(dict)
    def _update_stock_table_ui(self, data):
         """在主執行緒中更新股票表格行"""
         stock_id = data.get("symbol")
         if not stock_id: return

         # 更新緩存
         self.stock_data_cache[stock_id] = data

         # 查找或添加行並更新
         for row in range(self.stock_table.rowCount()):
             if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == stock_id:
                 self._update_stock_table_row(row, data)
                 break
         else: # 如果循環未被 break，表示股票不在表格中
             self._add_stock_to_table(stock_id, data)

    @pyqtSlot(str)
    def _update_log_ui(self, log_message):
        """在主執行緒中更新狀態欄日誌"""
        self.status_bar.showMessage(log_message, 5000)

    @pyqtSlot(dict)
    def _update_connection_status_ui(self, data):
         """在主執行緒中更新連接狀態顯示"""
         connected = data.get("connected", False)
         message = data.get("message", "未知狀態")
         gateway_name = data.get("gateway_name", "未知接口")

         status_text = f"{gateway_name} 狀態: {message}"
         if connected:
             color = "green"
             conn_label_text = "已連接"
         elif "模擬數據" in message or "API密鑰未設置" in message or "登入憑證錯誤" in message:
             color = "orange"
             conn_label_text = message
         else:
             color = "red"
             conn_label_text = "連接失敗"

         if hasattr(self, 'connection_status'):
              self.connection_status.setText(status_text)
              self.connection_status.setStyleSheet(f"color: {color};")
         if hasattr(self, 'connection_status_label'):
              self.connection_status_label.setText(conn_label_text)
              self.connection_status_label.setStyleSheet(f"color: {color};")

    @pyqtSlot(list)
    def _update_trading_records_ui(self, records):
         """在主執行緒中更新交易記錄表格"""
         # TODO: Implement actual table update logic
         print(f"GUI Slot: Updating trading records UI with {len(records)} records")
         # self._update_trading_records_table(records) # Call helper

    def _init_status_bar_timer(self):
        """初始化用於清除狀態欄的計時器"""
        self.status_clear_timer = QTimer(self)
        self.status_clear_timer.setSingleShot(True)
        self.status_clear_timer.timeout.connect(self._clear_status_bar)

    @pyqtSlot()
    def _clear_status_bar(self):
        """清除狀態欄訊息"""
        self.status_bar.clearMessage()

    # --- 原始事件處理函數 (修改為發射信號) ---
    @pyqtSlot(Event)
    def _handle_futures_update(self, event: Event):
        """處理期貨數據更新事件 (發射信號)"""
        # 不直接更新 UI，而是發射信號
        self.signal_update_futures.emit(event.data)

    @pyqtSlot(Event)
    def _handle_kbars_update(self, event: Event):
        """處理K線數據更新事件 (發射信號)"""
        data = event.data
        timeframe = data.get("timeframe")
        df = data.get("dataframe")
        if timeframe and df is not None:
            # 傳遞 DataFrame 的副本以避免潛在的跨線程問題
            self.signal_update_kbars.emit(timeframe, df.copy())

    @pyqtSlot(Event)
    def _handle_stock_tick_update(self, event: Event):
        """處理通用 Tick 事件 (發射信號更新股票列表)"""
        data = event.data
        stock_id = data.get("symbol")
        if stock_id and stock_id != "TXF0": # 確保是股票代碼
            self.signal_update_stock_table.emit(data)

    @pyqtSlot(Event)
    def _handle_order_update(self, event: Event):
        """處理委託更新事件 (發射信號)"""
        # TODO: Decide how to update trading records (e.g., emit single order or fetch full list)
        # For now, just print in the handler is okay, but ideally emit a signal
        # self.signal_update_trading_records.emit([event.data]) # Example: emit single order
        print(f"GUI Event Handler: Order Update - {event.data}") # Keep print for now

    @pyqtSlot(Event)
    def _handle_account_update(self, event: Event):
        """處理賬戶資金更新事件 (發射信號)"""
        # TODO: Implement signal emission for account update
        # self.signal_update_account.emit(event.data) # Example
        # print(f"GUI Event Handler: Account Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_position_update(self, event: Event):
        """處理持倉更新事件 (發射信號)"""
        # TODO: Implement signal emission for position update
        # self.signal_update_position.emit(event.data) # Example
        # print(f"GUI Event Handler: Position Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_account_update(self, event: Event):
        """處理賬戶資金更新事件 (發射信號)"""
        # TODO: Implement signal emission for account update
        # self.signal_update_account.emit(event.data) # Example
        # print(f"GUI Event Handler: Account Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_log_update(self, event: Event):
        """處理日誌事件 (發射信號)"""
        self.signal_update_log.emit(str(event.data))

    @pyqtSlot(Event)
    def _handle_connection_status_change(self, event: Event):
        """處理連接狀態變更事件 (發射信號)"""
        self.signal_update_connection_status.emit(event.data)

    # --- 其他方法 ---
    def initUI(self):
        # 這個方法似乎與 __init__ 重複，可以考慮移除或合併
        pass

    # _connect_api 方法不再需要

    def update_time_display(self):
        """僅更新時間相關的顯示"""
        now = datetime.now()
        current_date = now.date()
        is_trading_day = now.weekday() < 5

        if is_trading_day:
            trading_day_text = f"{current_date.strftime('%Y/%m/%d')}"
        else:
            trading_day_text = f"{current_date.strftime('%Y/%m/%d')} (非交易日)"
        if hasattr(self, 'trading_day_label'):
            self.trading_day_label.setText(trading_day_text)
        if hasattr(self, 'last_update_label'):
            self.last_update_label.setText(f"{now.strftime('%H:%M:%S')}")
        self.update_market_status_display()

    def update_market_status_display(self):
         """僅更新市場狀態顯示（時間除外）"""
         now = datetime.now()
         current_time = now.time()
         is_weekday = now.weekday() < 5
         is_day_session = time(8, 45) <= current_time <= time(13, 45)
         is_night_session = (time(15, 0) <= current_time <= time(23, 59)) or (time(0, 0) <= current_time < time(5, 0))
         is_market_open = is_weekday and (is_day_session or is_night_session)

         if is_market_open:
             status_text = "日盤交易中" if is_day_session else "夜盤交易中"
             color = "#33ff33" if is_day_session else "#3399ff"
         else:
             status_text = "已收盤"
             color = "#ff3333"
         if hasattr(self, 'market_status_label'):
             self.market_status_label.setText(status_text)
             self.market_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _init_market_data_panel(self):
        """初始化市場數據面板"""
        self.market_data_panel = QGroupBox("市場與期貨狀態")
        market_layout = QVBoxLayout(self.market_data_panel)

        market_status_group = QWidget()
        market_status_layout = QGridLayout(market_status_group)
        market_status_layout.setContentsMargins(0, 5, 0, 5)

        market_status_layout.addWidget(QLabel("交易日:"), 0, 0)
        self.trading_day_label = QLabel("--")
        self.trading_day_label.setToolTip("當前或下一個交易日期")
        market_status_layout.addWidget(self.trading_day_label, 0, 1)

        market_status_layout.addWidget(QLabel("市場狀態:"), 0, 2)
        self.market_status_label = QLabel("未知")
        self.market_status_label.setStyleSheet("color: gray;")
        self.market_status_label.setToolTip("顯示當前市場開/收盤狀態")
        market_status_layout.addWidget(self.market_status_label, 0, 3)

        market_status_layout.addWidget(QLabel("連線狀態:"), 1, 0)
        self.connection_status_label = QLabel("未知") # GUI 內部狀態標籤
        self.connection_status_label.setStyleSheet("color: gray;")
        self.connection_status_label.setToolTip("顯示與交易 API 的連接狀態")
        market_status_layout.addWidget(self.connection_status_label, 1, 1)

        market_status_layout.addWidget(QLabel("最後更新:"), 1, 2)
        self.last_update_label = QLabel("--")
        self.last_update_label.setToolTip("介面時間更新")
        market_status_layout.addWidget(self.last_update_label, 1, 3)

        market_layout.addWidget(market_status_group)

        futures_data_group = QWidget()
        futures_data_layout = QGridLayout(futures_data_group)
        futures_data_layout.setContentsMargins(0, 5, 0, 5)

        futures_data_layout.addWidget(QLabel("台指期價格:"), 0, 0)
        self.futures_price_label = QLabel("--")
        self.futures_price_label.setToolTip("最近的台指期貨成交價格")
        futures_data_layout.addWidget(self.futures_price_label, 0, 1)

        futures_data_layout.addWidget(QLabel("成交量:"), 0, 2)
        self.futures_volume_label = QLabel("--")
        self.futures_volume_label.setToolTip("最近一筆台指期貨成交量")
        futures_data_layout.addWidget(self.futures_volume_label, 0, 3)

        futures_data_layout.addWidget(QLabel("漲跌:"), 1, 0)
        self.futures_change_label = QLabel("--")
        self.futures_change_label.setToolTip("台指期貨相較於昨日收盤價的漲跌幅")
        futures_data_layout.addWidget(self.futures_change_label, 1, 1, 1, 3)

        market_layout.addWidget(futures_data_group)
        market_layout.addStretch()

        self.main_layout.addWidget(self.market_data_panel, 0, 0)

    def create_icon_from_text(self, text, color=QColor(255, 255, 255)):
        """從文字創建圖標"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setPen(color)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)

    def _init_indicator_panel(self):
        """初始化指標選擇面板"""
        indicator_group = QGroupBox('技術分析工具')
        indicator_layout = QVBoxLayout(indicator_group)

        period_widget = QWidget()
        period_layout = QHBoxLayout(period_widget)
        period_layout.addWidget(QLabel('K線週期:'))
        self.period_combo = QComboBox()
        self.period_combo.addItems(['15m', '30m', '1h', '日K'])
        self.period_combo.currentTextChanged.connect(self.update_charts)
        self.period_combo.setToolTip("選擇圖表顯示的K線時間週期")
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        indicator_layout.addWidget(period_widget)

        ma_widget = QWidget()
        ma_layout = QHBoxLayout(ma_widget)
        self.ma_combos = []
        for i in range(3):
            ma_combo = QComboBox()
            ma_combo.addItems(['無', 'MA5', 'MA10', 'MA20', 'MA60', 'MA120', 'EMA12', 'EMA26'])
            ma_combo.currentIndexChanged.connect(self.update_charts)
            ma_combo.setToolTip(f"選擇第 {i+1} 條移動平均線")
            self.ma_combos.append(ma_combo)
            ma_layout.addWidget(QLabel(f'MA{i+1}:'))
            ma_layout.addWidget(ma_combo)
        ma_layout.addStretch()
        indicator_layout.addWidget(ma_widget)

        macd_widget = QWidget()
        macd_layout = QHBoxLayout(macd_widget)
        self.macd_enabled = QCheckBox("MACD")
        self.macd_enabled.toggled.connect(self.update_charts)
        self.macd_enabled.setToolTip("啟用/禁用 MACD 指標顯示")
        macd_layout.addWidget(self.macd_enabled)
        macd_layout.addStretch()
        indicator_layout.addWidget(macd_widget)

        rsi_widget = QWidget()
        rsi_layout = QHBoxLayout(rsi_widget)
        self.rsi_enabled = QCheckBox("RSI")
        self.rsi_enabled.toggled.connect(self.update_charts)
        self.rsi_enabled.setToolTip("啟用/禁用 RSI 指標顯示")
        rsi_layout.addWidget(self.rsi_enabled)
        rsi_layout.addStretch()
        indicator_layout.addWidget(rsi_widget)

        sr_widget = QWidget()
        sr_layout = QHBoxLayout(sr_widget)
        self.sr_enabled = QCheckBox("支撐/阻力")
        self.sr_enabled.toggled.connect(self.update_charts)
        self.sr_enabled.setToolTip("啟用/禁用自動計算的支撐與阻力位顯示")
        sr_layout.addWidget(self.sr_enabled)
        sr_layout.addStretch()
        indicator_layout.addWidget(sr_widget)

        indicator_layout.addStretch()
        self.main_layout.addWidget(indicator_group, 0, 1)

    def _init_charts(self):
        """初始化圖表區域"""
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        self.figure = Figure(figsize=(10, 6), facecolor='#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        self.main_layout.addWidget(chart_widget, 1, 1, 1, 2)
        self.update_charts() # Draw initial empty chart

    def update_charts(self):
        """更新K線圖表"""
        self.figure.clear()
        ax1 = self.figure.add_subplot(111)
        ax1.set_facecolor('#1e1e1e')
        ax1.tick_params(axis='x', colors='white')
        ax1.tick_params(axis='y', colors='white')
        ax1.xaxis.label.set_color('white')
        ax1.yaxis.label.set_color('white')

        period_map = {'15m': '15分鐘', '30m': '30分鐘', '1h': '1小時', '日K': '日K'}
        selected_period_key = self.period_combo.currentText()
        selected_period_display = period_map.get(selected_period_key, selected_period_key)

        df = self.current_kbars.get(selected_period_key, pd.DataFrame())

        if df is None or df.empty:
            ax1.text(0.5, 0.5, '無可用數據', horizontalalignment='center',
                     verticalalignment='center', transform=ax1.transAxes, color='white')
            self.canvas.draw_idle()
            return

        if not isinstance(df.index, pd.DatetimeIndex):
             try:
                 df.index = pd.to_datetime(df.index)
             except Exception as e:
                 print(f"轉換索引為 DatetimeIndex 失敗: {e}")
                 ax1.text(0.5, 0.5, '索引格式錯誤', horizontalalignment='center',
                          verticalalignment='center', transform=ax1.transAxes, color='white')
                 self.canvas.draw_idle()
                 return
        try:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        except Exception as e:
            print(f"轉換數據類型失敗: {e}")
            ax1.text(0.5, 0.5, '數據類型錯誤', horizontalalignment='center',
                     verticalalignment='center', transform=ax1.transAxes, color='white')
            self.canvas.draw_idle()
            return

        mc = mpf.make_marketcolors(up='#00b060', down='#fe3032', edge='inherit', wick='inherit', volume='inherit')
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridcolor='#444444',
                               facecolor='#1e1e1e', figcolor='#1e1e1e', y_on_right=False)

        addplots = []
        for ma_combo in self.ma_combos:
            ma_type = ma_combo.currentText()
            if ma_type != '無':
                try:
                    period = int(ma_type[2:]) if ma_type.startswith('MA') else int(ma_type[3:])
                    if ma_type.startswith('MA'):
                        ma_data = df['Close'].rolling(window=period).mean()
                    else: # EMA
                        ma_data = df['Close'].ewm(span=period, adjust=False).mean()
                    addplots.append(mpf.make_addplot(ma_data, ax=ax1))
                except Exception as e:
                    print(f"計算 {ma_type} 失敗: {e}")

        try:
             mpf.plot(df, type='candle', style=s, ax=ax1, volume=False,
                      addplot=addplots, title=f'台指期 {selected_period_display} K線圖')
        except Exception as e:
             print(f"繪製圖表時發生錯誤: {e}")
             ax1.text(0.5, 0.5, f'繪製圖表錯誤: {e}', horizontalalignment='center',
                      verticalalignment='center', transform=ax1.transAxes, color='white')
             if not ax1.lines:
                 try:
                     mpf.plot(df, type='candle', style=s, ax=ax1, volume=False,
                              title=f'台指期 {selected_period_display} K線圖 (無指標)')
                 except Exception as basic_e:
                      print(f"繪製基礎K線圖也失敗: {basic_e}")

        try:
            self.canvas.draw_idle()
        except Exception as e:
            print(f"更新圖表畫布時出錯: {e}")

    # --- 原始事件處理函數 (修改為發射信號) ---
    @pyqtSlot(Event)
    def _handle_futures_update(self, event: Event):
        """處理期貨數據更新事件 (發射信號)"""
        # 不直接更新 UI，而是發射信號
        self.signal_update_futures.emit(event.data)

    @pyqtSlot(Event)
    def _handle_kbars_update(self, event: Event):
        """處理K線數據更新事件 (發射信號)"""
        data = event.data
        timeframe = data.get("timeframe")
        df = data.get("dataframe")
        if timeframe and df is not None:
            # 傳遞 DataFrame 的副本以避免潛在的跨線程問題
            self.signal_update_kbars.emit(timeframe, df.copy())

    @pyqtSlot(Event)
    def _handle_stock_tick_update(self, event: Event):
        """處理通用 Tick 事件 (發射信號更新股票列表)"""
        data = event.data
        stock_id = data.get("symbol")
        if stock_id and stock_id != "TXF0": # 確保是股票代碼
            self.signal_update_stock_table.emit(data)

    @pyqtSlot(Event)
    def _handle_order_update(self, event: Event):
        """處理委託更新事件 (發射信號)"""
        # TODO: Implement signal emission for trading records update
        # self.signal_update_trading_records.emit([event.data]) # Example
        # print(f"GUI Event Handler: Order Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_trade_update(self, event: Event):
        """處理成交更新事件 (發射信號)"""
        # TODO: Implement signal emission for trading records update
        # self.signal_update_trading_records.emit([event.data]) # Example
        # print(f"GUI Event Handler: Trade Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_position_update(self, event: Event):
        """處理持倉更新事件 (發射信號)"""
        # TODO: Implement signal emission for position update
        # self.signal_update_position.emit(event.data) # Example
        # print(f"GUI Event Handler: Position Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_account_update(self, event: Event):
        """處理賬戶資金更新事件 (發射信號)"""
        # TODO: Implement signal emission for account update
        # self.signal_update_account.emit(event.data) # Example
        # print(f"GUI Event Handler: Account Update - {event.data}") # Remove print

    @pyqtSlot(Event)
    def _handle_log_update(self, event: Event):
        """處理日誌事件"""
        log_message = event.data
        self.status_bar.showMessage(str(log_message), 5000)

    @pyqtSlot(Event) # Changed to accept Event object
    def _handle_connection_status_change(self, event: Event):
        """處理連接狀態變更信號"""
        data = event.data
        connected = data.get("connected", False)
        message = data.get("message", "未知狀態")
        gateway_name = data.get("gateway_name", "未知接口")

        status_text = f"{gateway_name} 狀態: {message}"
        if connected:
            color = "green"
            conn_label_text = "已連接"
        elif "模擬數據" in message or "API密鑰未設置" in message or "登入憑證錯誤" in message:
            color = "orange"
            conn_label_text = message
        else:
            color = "red"
            conn_label_text = "連接失敗"

        if hasattr(self, 'connection_status'):
             self.connection_status.setText(status_text)
             self.connection_status.setStyleSheet(f"color: {color};")
        if hasattr(self, 'connection_status_label'):
             self.connection_status_label.setText(conn_label_text)
             self.connection_status_label.setStyleSheet(f"color: {color};")

    @pyqtSlot(str, int)
    def _handle_status_bar_message(self, message, timeout):
        """處理狀態欄消息信號"""
        self.status_bar.showMessage(message, timeout)

    # --- 輔助更新方法 ---
    def _update_market_data_display(self, data):
        """僅更新市場數據面板的顯示 (由信號觸發)"""
        # Needs refactoring based on how market analysis data is structured and sent
        if not data: return
        trend = data.get('trend', '--')
        # ... (rest of the method remains similar) ...

    def _add_stock_to_table(self, stock_id, data):
         """向股票表格添加新行"""
         row_count = self.stock_table.rowCount()
         self.stock_table.insertRow(row_count)
         self._update_stock_table_row(row_count, data)

    def _update_stock_table_row(self, row, data):
         """更新股票表格的指定行"""
         try:
             stock_id = data.get('symbol', data.get('code', '--'))
             self.stock_table.setItem(row, 0, QTableWidgetItem(stock_id))

             price = data.get('last_price', data.get('price'))
             price_text = f"{price:.2f}" if price is not None else "--"
             self.stock_table.setItem(row, 1, QTableWidgetItem(price_text))

             # Calculate change percentage if pre_close is available
             change_ratio = None
             pre_close = data.get('pre_close')
             if price is not None and pre_close is not None and pre_close != 0 and not np.isnan(pre_close):
                 change_ratio = ((price - pre_close) / pre_close) * 100

             change_text = f"{change_ratio:.2f}%" if change_ratio is not None else "--"
             change_item = QTableWidgetItem(change_text)
             if change_ratio is not None:
                 color = QColor(0, 200, 0) if change_ratio > 0 else QColor(200, 0, 0) if change_ratio < 0 else QColor(0,0,0)
                 change_item.setForeground(color)
             self.stock_table.setItem(row, 2, change_item)

             volume = data.get('volume', data.get('total_volume'))
             volume_text = "--"
             if volume is not None:
                 if volume >= 1000000: volume_text = f"{volume/1000000:.2f}M"
                 elif volume >= 1000: volume_text = f"{volume/1000:.1f}K"
                 else: volume_text = str(int(volume))
             self.stock_table.setItem(row, 3, QTableWidgetItem(volume_text))

             # Trend and Signal should come from a strategy app event
             trend = data.get('trend', '--') # Placeholder
             trend_item = QTableWidgetItem(trend)
             # ... (set color based on trend) ...
             self.stock_table.setItem(row, 4, trend_item)

             signal_type = data.get('signal_type', '--') # Placeholder
             signal_item = QTableWidgetItem(signal_type)
             # ... (set color based on signal) ...
             self.stock_table.setItem(row, 5, signal_item)

             update_time = data.get('datetime', data.get('last_update'))
             time_text = update_time.strftime('%H:%M:%S') if isinstance(update_time, datetime) else "--"
             self.stock_table.setItem(row, 6, QTableWidgetItem(time_text))

         except Exception as e:
             print(f"更新股票表格行 {row} (ID: {data.get('symbol', 'N/A')}) 失敗: {e}")
             for col in range(self.stock_table.columnCount()):
                 if self.stock_table.item(row, col) is None:
                     self.stock_table.setItem(row, col, QTableWidgetItem("錯誤"))

    def get_stock_name(self, stock_id):
        # This might need to fetch from main_engine or a dedicated contract management part
        stock_names = {
            '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2412': '中華電',
            '2308': '台達電', '2303': '聯電', '2882': '國泰金', '1301': '台塑',
            '2881': '富邦金', '2002': '中鋼', '2886': '兆豐金', '2891': '中信金',
            '3034': '聯詠', '2327': '國巨', '2884': '玉山金', '2885': '元大金'
        }
        return stock_names.get(stock_id, f'股票{stock_id}')

    def is_market_open(self):
        # This logic might be better placed in the engine or a utility module
        now = datetime.now()
        current_time = now.time()
        is_weekday = now.weekday() < 5
        is_trading_hours = time(9, 0) <= current_time <= time(13, 30) # Simplified, needs refinement for futures
        return is_weekday and is_trading_hours

    def show_stock_table_menu(self, position):
        menu = QMenu()
        selected_row = self.stock_table.currentRow()
        if selected_row >= 0:
            stock_id_item = self.stock_table.item(selected_row, 0)
            if stock_id_item:
                stock_id = stock_id_item.text()
                remove_stock = menu.addAction("取消訂閱") # Corrected indentation
                remove_stock.triggered.connect(lambda: self._unsubscribe_stock(stock_id)) # Corrected indentation
                menu.exec(self.stock_table.viewport().mapToGlobal(position)) # Corrected indentation

    def _unsubscribe_stock(self, stock_id):
        """取消訂閱股票行情"""
        print(f"GUI: Requesting unsubscribe for {stock_id}")
        contract = self.main_engine.get_contract(stock_id, "Shioaji")
        if contract:
            req = {"contract": contract}
            self.main_engine.unsubscribe(req, "Shioaji") # 調用 MainEngine 的 unsubscribe
            self.status_bar.showMessage(f"已發送取消訂閱請求: {stock_id}", 3000)
            # Remove row immediately for now, ideally wait for confirmation event
            for row in range(self.stock_table.rowCount()):
                 if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == stock_id:
                     self.stock_table.removeRow(row)
                     break
        else:
            self.status_bar.showMessage(f"取消訂閱失敗，找不到合約: {stock_id}", 3000)

    def _show_technical_indicators(self, stock_id):
        QMessageBox.information(self, "信息", f"技術指標現在集成在主圖表中。請使用右側面板控制。")

    def _show_signal_history(self, stock_id):
         QMessageBox.information(self, "信息", f"信號歷史功能待整合到策略應用模組中。")

    def _show_advanced_indicators(self):
        QMessageBox.information(self, "信息", f"進階指標功能待整合。")

    def _add_index(self):
        """訂閱大盤指數"""
        print("GUI: Requesting subscribe for 大盤指數 (e.g., TXF)")
        # Need to get the actual contract object for the index futures
        # contract = self.main_engine.get_contract("TXF0") # Example, replace with actual logic
        # if contract:
        #     req = {"contract": contract, "quote_type": sj.constant.QuoteType.Tick}
        #     self.main_engine.subscribe(req, "Shioaji")
        #     self.status_bar.showMessage(f"已發送訂閱大盤指數請求", 3000)
        # else:
        #     self.status_bar.showMessage(f"找不到大盤指數合約", 3000)
        self.status_bar.showMessage(f"訂閱大盤指數功能待實現", 3000) # Placeholder

    def _init_stock_list(self):
        """初始化股票列表"""
        stocks_group = QGroupBox("股票監視清單")
        stocks_layout = QVBoxLayout(stocks_group)

        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        add_button = QPushButton("添加/訂閱股票")
        add_button.clicked.connect(self.add_stock)
        add_button.setToolTip("添加新的股票代碼到監視列表並訂閱行情")
        buttons_layout.addWidget(add_button)
        # refresh_button = QPushButton("刷新列表") # Removed
        self.add_index_button = QPushButton("訂閱大盤")
        self.add_index_button.clicked.connect(self._add_index)
        self.add_index_button.setToolTip("訂閱大盤指數行情")
        buttons_layout.addWidget(self.add_index_button)
        buttons_layout.addStretch()
        stocks_layout.addWidget(buttons_widget)

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(7)
        self.stock_table.setHorizontalHeaderLabels(["代碼", "價格", "漲跌%", "總量", "趨勢", "信號", "更新"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.stock_table.horizontalHeader().setStretchLastSection(True)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stock_table.customContextMenuRequested.connect(self.show_stock_table_menu)
        stocks_layout.addWidget(self.stock_table)

        self.main_layout.addWidget(stocks_group, 1, 0, 2, 1)

        # self.update_stock_list() # Initial load removed

    def _init_strategy_list(self):
        """初始化交易策略列表"""
        # Needs refactoring based on strategy app
        try:
            # Placeholder
            # strategy_names = self.main_engine.get_app("StrategyApp").get_strategy_names()
            strategy_names = ["策略A", "策略B"]
            # Check if self.strategy_combo exists before using it
            if hasattr(self, 'strategy_combo'):
                current_strategy = self.strategy_combo.currentText()
                self.strategy_combo.clear()
                if strategy_names:
                    self.strategy_combo.addItems(strategy_names)
                    index = self.strategy_combo.findText(current_strategy)
                    if index >= 0:
                        self.strategy_combo.setCurrentIndex(index)
                else:
                    self.strategy_combo.addItem("無可用策略")
            else:
                 print("警告: strategy_combo 未在 _init_strategy_list 調用前初始化")
        except Exception as e:
            print(f"初始化策略列表失敗: {str(e)}")
            if hasattr(self, 'strategy_combo'):
                self.strategy_combo.clear()
                self.strategy_combo.addItem("無可用策略")

    def _change_strategy(self, strategy_name):
        """更改當前使用的交易策略"""
        if not strategy_name or strategy_name == "無可用策略": return
        print(f"GUI: Requesting change strategy to {strategy_name}")
        # Example: self.main_engine.get_app("StrategyApp").set_active_strategy(strategy_name)
        self.status_bar.showMessage(f"已請求切換到策略: {strategy_name}", 3000)

    def _create_custom_strategy(self):
        """打開自定義策略對話框"""
        QMessageBox.information(self, "提示", "自定義策略功能正在重構中。")

    def _show_strategy_params_dialog(self):
        try:
            from strategy_params_dialog import StrategyParamsDialog
            # 假設有 self.auto_trader_manager.trader.signal_gen
            signal_gen = None
            if self.auto_trader_manager and hasattr(self.auto_trader_manager, "trader"):
                signal_gen = getattr(self.auto_trader_manager.trader, "signal_gen", None)
            if not signal_gen:
                QMessageBox.warning(self, "錯誤", "找不到策略模組")
                return
            # 假設策略參數存於 signal_gen.strategy_params
            params = getattr(signal_gen, "strategy_params", {"short_window":5, "long_window":20, "rsi_period":14})
            dialog = StrategyParamsDialog(params, self)
            if dialog.exec():
                new_params = dialog.get_params()
                # 更新 signal_gen 內的參數
                if hasattr(signal_gen, "strategy_params"):
                    signal_gen.strategy_params.update(new_params)
                else:
                    signal_gen.strategy_params = new_params
                QMessageBox.information(self, "成功", "策略參數已更新")
        except Exception as e:
            QMessageBox.warning(self, "錯誤", f"策略參數設定失敗: {e}")

    def _init_auto_trading_panel(self):
        """初始化自動交易面板"""
        auto_trading_group = QGroupBox("自動交易")
        auto_trading_layout = QVBoxLayout(auto_trading_group)

        strategy_widget = QWidget()
        strategy_layout = QGridLayout(strategy_widget)
        strategy_layout.addWidget(QLabel("策略:"), 0, 0)
        self.strategy_combo = QComboBox() # Define here
        self._init_strategy_list() # Populate
        self.strategy_combo.currentTextChanged.connect(self._change_strategy)
        self.strategy_combo.setToolTip("選擇用於自動交易的策略")
        strategy_layout.addWidget(self.strategy_combo, 0, 1)
        self.custom_strategy_btn = QPushButton("自訂")
        self.custom_strategy_btn.clicked.connect(self._create_custom_strategy)
        self.custom_strategy_btn.setToolTip("創建或修改自定義交易策略參數")
        strategy_layout.addWidget(self.custom_strategy_btn, 0, 2)
        self.auto_trading_checkbox = QCheckBox("啟用自動交易")
        self.auto_trading_checkbox.toggled.connect(self._toggle_auto_trading)
        self.auto_trading_checkbox.setToolTip("勾選以啟用基於當前策略和設置的自動交易")
        strategy_layout.addWidget(self.auto_trading_checkbox, 1, 0)
        settings_btn = QPushButton("設置")
        settings_btn.clicked.connect(self._show_auto_trading_settings)
        settings_btn.setToolTip("配置自動交易的風險控制參數")
        strategy_layout.addWidget(settings_btn, 1, 1, 1, 2)
        auto_trading_layout.addWidget(strategy_widget)

        trading_record_group = QGroupBox("交易記錄")
        trading_record_layout = QVBoxLayout(trading_record_group)
        self.trading_record_table = QTableWidget()
        self.trading_record_table.setColumnCount(8)
        self.trading_record_table.setHorizontalHeaderLabels(["時間", "代碼", "操作", "數量", "價格", "金額", "狀態", "盈虧"])
        self.trading_record_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.trading_record_table.horizontalHeader().setStretchLastSection(True)
        self.trading_record_table.setAlternatingRowColors(True)
        trading_record_layout.addWidget(self.trading_record_table)
        auto_trading_layout.addWidget(trading_record_group)

        # 新增自動交易訊號與日誌顯示區
        self.auto_trading_log = QGroupBox("自動交易訊號與日誌")
        log_layout = QVBoxLayout(self.auto_trading_log)
        from PyQt6.QtWidgets import QTextEdit
        self.auto_trading_log_text = QTextEdit()
        self.auto_trading_log_text.setReadOnly(True)
        self.auto_trading_log_text.setStyleSheet("background-color: #1e1e1e; color: #33ff33; font-family: Consolas;")
        log_layout.addWidget(self.auto_trading_log_text)
        auto_trading_layout.addWidget(self.auto_trading_log)

        self.main_layout.addWidget(auto_trading_group, 2, 1)

        # self._update_trading_records_table(...) # Initial update removed

    def _update_trading_records_table(self, records):
         """更新交易記錄表格的輔助方法"""
         # This should be triggered by EVENT_TRADE or EVENT_ORDER
         # Needs refactoring based on actual event data structure
         pass

    def _update_trading_records_table_with_order(self, order_data: dict):
        """使用委託數據更新交易記錄表"""
        # Find existing row or add new one
        # Update relevant columns (Time, Code, Action, Qty, Price, Status)
        pass

    def _update_trading_records_table_with_trade(self, trade_data: dict):
        """使用成交數據更新交易記錄表"""
        # Find related order row
        # Update relevant columns (Traded Qty, PnL if applicable, Status)
        pass

    def _update_trading_records(self):
        # Obsolete, handled by events
        pass

    def _show_auto_trading_settings(self):
        QMessageBox.information(self, "提示", "自動交易設置功能正在重構中。")

    def _toggle_auto_trading(self, checked):
        print(f"GUI: Requesting auto trading state: {checked}")
        if not self.auto_trader_manager:
            self.status_bar.showMessage("自動交易模組未載入", 5000)
            return

        if checked:
            try:
                self.auto_trader_manager.start()
                self.auto_trading_checkbox.setText("自動交易中")
                self.auto_trading_checkbox.setStyleSheet("color: green; font-weight: bold;")
                self.status_bar.showMessage("自動交易已啟動", 5000)
            except Exception as e:
                print(f"啟動自動交易失敗: {e}")
                self.status_bar.showMessage(f"啟動自動交易失敗: {e}", 5000)
                self.auto_trading_checkbox.setChecked(False)
        else:
            try:
                self.auto_trader_manager.stop()
                self.auto_trading_checkbox.setText("啟用自動交易")
                self.auto_trading_checkbox.setStyleSheet("")
                self.status_bar.showMessage("自動交易已停止", 5000)
            except Exception as e:
                print(f"停止自動交易失敗: {e}")
                self.status_bar.showMessage(f"停止自動交易失敗: {e}", 5000)

    def _init_backtest_panel(self):
        """初始化回測面板"""
        backtest_group = QGroupBox("策略回測")
        backtest_layout = QVBoxLayout(backtest_group)
        # ... (Keep UI elements, functionality needs rework) ...
        settings_widget = QWidget()
        settings_layout = QGridLayout(settings_widget)
        settings_layout.addWidget(QLabel("股票:"), 0, 0)
        self.backtest_stock_combo = QComboBox()
        self.backtest_stock_combo.setEditable(True)
        self.backtest_stock_combo.setToolTip("選擇或輸入要進行回測的股票代碼")
        settings_layout.addWidget(self.backtest_stock_combo, 0, 1)
        settings_layout.addWidget(QLabel("策略:"), 0, 2)
        self.backtest_strategy_combo = QComboBox()
        self.backtest_strategy_combo.setToolTip("選擇用於回測的交易策略")
        settings_layout.addWidget(self.backtest_strategy_combo, 0, 3)
        settings_layout.addWidget(QLabel("開始:"), 1, 0)
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-6))
        self.start_date_edit.setToolTip("設定回測的開始日期")
        settings_layout.addWidget(self.start_date_edit, 1, 1)
        settings_layout.addWidget(QLabel("結束:"), 1, 2)
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setToolTip("設定回測的結束日期")
        settings_layout.addWidget(self.end_date_edit, 1, 3)
        settings_layout.addWidget(QLabel("資金:"), 2, 0)
        self.initial_capital_spin = QSpinBox()
        self.initial_capital_spin.setRange(10000, 10000000)
        self.initial_capital_spin.setSingleStep(10000)
        self.initial_capital_spin.setValue(100000)
        self.initial_capital_spin.setPrefix("NT$ ")
        self.initial_capital_spin.setToolTip("設定回測的初始模擬資金")
        settings_layout.addWidget(self.initial_capital_spin, 2, 1)
        self.run_backtest_btn = QPushButton("執行回測")
        self.run_backtest_btn.clicked.connect(self._run_backtest)
        self.run_backtest_btn.setToolTip("使用選定的股票、策略和參數執行歷史回測")
        settings_layout.addWidget(self.run_backtest_btn, 2, 2, 1, 2)
        backtest_layout.addWidget(settings_widget)

        self.backtest_results_tabs = QTabWidget()

        # 新增委託單分頁
        order_widget = QWidget()
        order_layout = QVBoxLayout(order_widget)
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(8)
        self.order_table.setHorizontalHeaderLabels(["時間", "代碼", "方向", "數量", "價格", "狀態", "委託ID", "操作"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.order_table.horizontalHeader().setStretchLastSection(True)
        self.order_table.setAlternatingRowColors(True)
        order_layout.addWidget(self.order_table)
        self.backtest_results_tabs.addTab(order_widget, "委託單")

        # 新增成交記錄分頁
        trade_widget = QWidget()
        trade_layout = QVBoxLayout(trade_widget)
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(7)
        self.trade_table.setHorizontalHeaderLabels(["時間", "代碼", "方向", "數量", "價格", "成交ID", "委託ID"])
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.trade_table.horizontalHeader().setStretchLastSection(True)
        self.trade_table.setAlternatingRowColors(True)
        trade_layout.addWidget(self.trade_table)
        self.backtest_results_tabs.addTab(trade_widget, "成交記錄")

        # 原有績效指標分頁
        performance_widget = QWidget()
        performance_layout = QVBoxLayout(performance_widget)
        self.performance_table = QTableWidget()
        self.performance_table.setRowCount(5)
        self.performance_table.setColumnCount(2)
        self.performance_table.setHorizontalHeaderLabels(["指標", "數值"])
        self.performance_table.setVerticalHeaderLabels(["總回報率", "年化回報率", "夏普比率", "最大回撤", "勝率"])
        self.performance_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        performance_layout.addWidget(self.performance_table)
        self.backtest_results_tabs.addTab(performance_widget, "績效指標")

        # 原有交易記錄分頁
        trades_widget = QWidget()
        trades_layout = QVBoxLayout(trades_widget)
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(7)
        self.trades_table.setHorizontalHeaderLabels(["日期", "操作", "價格", "數量", "金額", "單筆盈虧", "盈虧%"])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.trades_table.horizontalHeader().setStretchLastSection(True)
        trades_layout.addWidget(self.trades_table)
        self.backtest_results_tabs.addTab(trades_widget, "歷史交易")

        # 權益曲線分頁
        equity_curve_widget = QWidget()
        equity_layout = QVBoxLayout(equity_curve_widget)
        self.equity_curve_label = QLabel("尚未生成權益曲線")
        self.equity_curve_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        equity_layout.addWidget(self.equity_curve_label)
        self.backtest_results_tabs.addTab(equity_curve_widget, "權益曲線")

        backtest_layout.addWidget(self.backtest_results_tabs)
        self.main_layout.addWidget(backtest_group, 2, 2)

        self._update_backtest_stock_list()

    def _update_backtest_stock_list(self):
        """更新回測股票和策略列表"""
        # Needs refactoring
        self.backtest_stock_combo.clear()
        stock_ids = ["AAPL", "GOOG"] # Placeholder
        if stock_ids:
            self.backtest_stock_combo.addItems(stock_ids)
        else:
            self.backtest_stock_combo.addItem("無可用股票")

        self.backtest_strategy_combo.clear()
        strategy_names = ["策略A", "策略B"] # Placeholder
        if strategy_names:
            self.backtest_strategy_combo.addItems(strategy_names)
        else:
            self.backtest_strategy_combo.addItem("無可用策略")

    def _run_backtest(self):
        """執行回測"""
        QMessageBox.information(self, "提示", "回測功能正在重構中。")

    def _update_backtest_results(self, result):
        """更新回測結果顯示"""
        pass

    def _draw_equity_curve(self, backtest_data):
        """繪製權益曲線"""
        pass

    def _update_parameters_panel(self, strategy_name):
        pass

    def _run_optimization(self):
        QMessageBox.information(self, "提示", "參數優化功能正在重構中。")
        pass

    def _update_optimization_results(self, result):
        pass

    def _apply_selected_parameters(self, item=None):
        pass

    def create_toolbar(self):
        """創建工具欄"""
        toolbar = self.addToolBar("工具")
        add_stock_action = QAction(QIcon.fromTheme("list-add"), "添加/訂閱股票", self)
        add_stock_action.triggered.connect(self.add_stock)
        toolbar.addAction(add_stock_action)

        connect_action = QAction(QIcon.fromTheme("network-connect"), "連接", self)
        connect_action.triggered.connect(self._trigger_connect)
        toolbar.addAction(connect_action)

        disconnect_action = QAction(QIcon.fromTheme("network-disconnect"), "斷開", self)
        disconnect_action.triggered.connect(self._trigger_disconnect)
        toolbar.addAction(disconnect_action)

    def add_stock(self):
        """打開添加股票對話框並觸發訂閱"""
        dialog = AddStockDialog(self)
        if dialog.exec():
            stock_id = dialog.get_stock_id()
            if stock_id:
                print(f"GUI: Requesting subscribe for {stock_id}")
                contract = self.main_engine.get_contract(stock_id, "Shioaji")
                if contract:
                    # 假設 ShioajiGateway 需要 contract 物件
                    # 根據 Gateway 的 subscribe 方法調整 req 結構
                    req = {"contract": contract, "quote_type": "Tick"} # 使用字符串 "Tick" 或 sj.constant.QuoteType.Tick
                    self.main_engine.subscribe(req, "Shioaji")
                    self.status_bar.showMessage(f"已發送訂閱請求: {stock_id}", 3000)
                    # 添加佔位行，等待事件更新數據
                    self._add_stock_to_table(stock_id, {"symbol": stock_id})
                else:
                    self.status_bar.showMessage(f"訂閱失敗，找不到合約: {stock_id}", 3000)
                    QMessageBox.warning(self, "錯誤", f"無法找到股票/期貨合約: {stock_id}")

    def _trigger_connect(self):
        """觸發連接到 Shioaji"""
        shioaji_setting = {} # Load from config file or secure storage
        self.main_engine.connect(shioaji_setting, "Shioaji")

    def _trigger_disconnect(self):
        """觸發斷開 Shioaji 連接"""
        self.main_engine.close() # MainEngine close should handle gateway disconnection

# --- 對話框類別 (保持不變，但內部邏輯可能需要調整以適應新架構) ---
class AddStockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加/訂閱股票')
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        self.stock_id_input = QLineEdit()
        self.stock_id_input.setPlaceholderText('請輸入股票代碼 (例如: 2330) 或期貨代碼 (例如: TXF0)')
        layout.addWidget(QLabel('股票/期貨代碼:'))
        layout.addWidget(self.stock_id_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def get_stock_id(self):
        return self.stock_id_input.text().strip().upper() # Convert to uppercase

class CustomStrategyDialog(QDialog):
    def __init__(self, available_strategies, parent=None):
         super().__init__(parent)
         self.setWindowTitle('自定義交易策略 - (重構中)')
         layout = QVBoxLayout(self)
         layout.addWidget(QLabel("此功能正在重構中"))
         buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
         buttons.rejected.connect(self.reject)
         layout.addWidget(buttons)

class TechnicalIndicatorsDialog(QDialog):
     def __init__(self, stock_id, trader, parent=None): # Still takes old trader for now
         super().__init__(parent)
         self.setWindowTitle(f"{stock_id} - 技術指標詳情 - (重構中)")
         layout = QVBoxLayout(self)
         layout.addWidget(QLabel("技術指標已整合至主圖表"))
         buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
         buttons.accepted.connect(self.accept)
         layout.addWidget(buttons)


class SignalHistoryDialog(QDialog):
     def __init__(self, stock_id, trader, parent=None): # Still takes old trader for now
         super().__init__(parent)
         self.setWindowTitle(f"{stock_id} 交易信號歷史 - (重構中)")
         layout = QVBoxLayout(self)
         layout.addWidget(QLabel("信號歷史功能正在重構中"))
         buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
         buttons.accepted.connect(self.accept)
         layout.addWidget(buttons)


class AutoTradingSettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自動交易設置 - (重構中)")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("自動交易設置功能正在重構中"))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def get_settings(self):
        return {}

# --- Main Execution (使用新引擎) ---
def main():
    """主應用程序入口"""
    qapp = QApplication(sys.argv)

    # 設定全域中文字型
    from PyQt6.QtGui import QFont
    qapp.setFont(QFont("Microsoft JhengHei", 10))

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    # 添加交易接口
    main_engine.add_gateway(ShioajiGateway)

    # 添加應用 (如果有的話)
    # main_engine.add_app(SomeApp)

    # 創建並顯示 GUI
    main_window = TradingWindow(main_engine, event_engine)
    main_window.show()

    # 啟動事件引擎
    event_engine.start()

    # 可以在這裡觸發初始連接，或通過 GUI 按鈕觸發
    # shioaji_setting = {} # 從配置加載
    # main_engine.connect(shioaji_setting, "Shioaji")

    sys.exit(qapp.exec())

if __name__ == "__main__":
    main()
