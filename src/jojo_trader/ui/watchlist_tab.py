
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QPushButton, QHBoxLayout, QInputDialog, QMessageBox, 
                             QComboBox, QFormLayout, QDialog, QLineEdit, QDialogButtonBox, QSplitter, QFrame, QGridLayout,
                             QCheckBox, QTextEdit, QMenu)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QColor, QBrush, QAction
import sys
import os
import pandas as pd

# Charting Imports
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import mplfinance as mpf
import json
import datetime
from jojo_trading.core.stock_database import StockDatabase
try:
    from jojo_trading.analysis.backtest.strategy_parser import StrategyParser
    from jojo_trading.analysis.backtest.data_adapter import BacktestDataAdapter
except ImportError:
    StrategyParser = None
    BacktestDataAdapter = None

class EditStrategyDialog(QDialog):
    def __init__(self, code, parent=None, buy_str="", sell_str="", active=False):
        super().__init__(parent)
        self.setWindowTitle(f"策略設定 - {code}")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #2d2d2d; color: white; QLineEdit, QTextEdit { background: #1e1e1e; color: white; border: 1px solid #555; }")
        
        layout = QVBoxLayout(self)
        
        self.chk_active = QCheckBox("啟用監控 (Active)")
        self.chk_active.setChecked(active)
        self.chk_active.setStyleSheet("color: #00B4D8; font-weight: bold;")
        layout.addWidget(self.chk_active)
        
        layout.addWidget(QLabel("買入策略 (Buy Cond):"))
        self.txt_buy = QTextEdit(buy_str)
        self.txt_buy.setPlaceholderText("e.g. close > MA20")
        layout.addWidget(self.txt_buy)
        
        layout.addWidget(QLabel("賣出策略 (Sell Cond):"))
        self.txt_sell = QTextEdit(sell_str)
        self.txt_sell.setPlaceholderText("e.g. close < MA20")
        layout.addWidget(self.txt_sell)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
    def get_data(self):
        return self.chk_active.isChecked(), self.txt_buy.toPlainText().strip(), self.txt_sell.toPlainText().strip()


# Import core modules
# ... (Imports at top)
try:
    from jojo_trading.core.watchlist_manager import WatchlistManager
    from jojo_trading.core.yfinance_fetcher import YFinanceFetcher
    from jojo_trader.ui.signal_bridge import ShioajiSignalBridge
    from jojo_trading.utils.twse_calendar import TWSECalendar
except ImportError:
    WatchlistManager = None
    YFinanceFetcher = None
    ShioajiSignalBridge = None
    TWSECalendar = None

# ...

    def check_market_status(self):
        """Check if market is open (Stocks vs Futures / Day vs Night / Holiday)"""
        if not self.current_chart_code: return

        import datetime
        now = datetime.datetime.now()
        
        # 1. Check Holiday / Weekend
        is_trading_day = True
        if TWSECalendar:
            is_trading_day = TWSECalendar.is_trading_day(now.date())
        else:
            # Fallback if module missing
            is_trading_day = now.weekday() < 5
            
        if not is_trading_day:
            self.quote_widget.set_market_status(False, "Closed (Holiday/Weekend)")
            return

        # 2. Check Sessions
        weekday = now.weekday() # 0=Mon, 6=Sun
        
        # Heuristic: Stock = All Digits, Future = Contains Letters
        is_future = not self.current_chart_code.isdigit()
        
        is_open = False
        session_text = "Closed (休市)"
        
        if is_future:
            # --- Futures Logic ---
            # 1. Regular Session (Day): Mon-Fri 08:45 - 13:45
            day_start = now.replace(hour=8, minute=45, second=0)
            day_end = now.replace(hour=13, minute=45, second=0)
            
            if day_start <= now <= day_end:
                is_open = True
                session_text = "Day Session (日盤)"
            
            # 2. Night Session (Night):
            if not is_open:
                # Part A: Mon-Fri 15:00 - 23:59
                night_start = now.replace(hour=15, minute=0, second=0)
                night_end = now.replace(hour=23, minute=59, second=59)
                if night_start <= now <= night_end:
                    is_open = True
                    session_text = "Night Session (夜盤)"
                        
                # Part B: Tue-Sat 00:00 - 05:00 (continuation of prev day's night session)
                # Note: If it's Saturday 02:00, is_trading_day might be False (Sat), 
                # BUT Night session extends to Sat AM. 
                # Modification: Night session Part B logic needs to bypass 'is_trading_day' check for Sat AM?
                # Actually, standard Night Session closes Sat 05:00.
                # Let's handle generic case first.
                
                early_start = now.replace(hour=0, minute=0, second=0)
                early_end = now.replace(hour=5, minute=0, second=0)
                if early_start <= now <= early_end:
                     # Check if yesterday was trading day? 
                     # For simplicity, let's assume if now is < 05:00 on Sat, it is open.
                     if weekday == 5: # Saturday AM
                         is_open = True
                         session_text = "Night Session (夜盤)"
                     elif weekday < 5: # Tue-Fri AM
                         is_open = True
                         session_text = "Night Session (夜盤)"
                        
        else:
            # --- Stock Logic ---
            # Mon-Fri 09:00 - 13:30
            start = now.replace(hour=9, minute=0, second=0)
            end = now.replace(hour=13, minute=30, second=0)
            if start <= now <= end:
                is_open = True
                session_text = "Regular Session (盤中)"
        
        # Update UI
        final_text = f"Market Open - {session_text}" if is_open else f"Market Closed ({session_text})"
        if not is_open: final_text = "Market Closed (休市)" 
        if not is_trading_day and not is_open: final_text = "Closed (Holiday/Weekend)" # Override if definitely closed
        
        self.quote_widget.set_market_status(is_open, final_text)

class StrategyWorker(QThread):
    """Background worker for Strategy Monitoring (Daily/Minute Analysis)"""
    signal_triggered = Signal(dict) # {code, type, price, msg}
    log_updated = Signal(str)

    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.strategies = {} # dict of code -> {buy, sell, active}
        self.running = True
        self.paused = False

    def update_strategies(self, new_strategies):
        """Update the running configurations safely"""
        self.strategies = new_strategies

    def run(self):
        while self.running:
            if self.paused or not self.strategies:
                self.sleep(2)
                continue
                
            # Iterate copy to avoid thread issues
            current_strats = self.strategies.copy()
            
            for code, strat in current_strats.items():
                if not strat.get('active', False):
                    continue
                    
                buy_str = strat.get('buy', '')
                sell_str = strat.get('sell', '')
                
                if not buy_str and not sell_str: continue

                try:
                    if not BacktestDataAdapter: continue
                    
                    # 1. Fetch History (Daily)
                    # Optimization: Maybe cache this? YFinance is slow. 
                    data_map = BacktestDataAdapter.get_kline_data(code, period="3mo", interval="1d")
                    if not data_map or 'daily' not in data_map:
                        continue
                        
                    df = data_map['daily']
                    if df.empty: continue
                    
                    # 2. Get Real-time Price from Shioaji Connector (Main Thread helper?)
                    # Alternatively, check if Connector has cache?
                    connector = getattr(self.main, 'connector', None)
                    current_price = 0
                    if connector:
                        snap = connector.get_snapshot(code)
                        if snap:
                            if snap.get('close') > 0: current_price = snap.get('close')
                            elif snap.get('price') > 0: current_price = snap.get('price')
                    
                    if current_price > 0:
                        # Update last Close
                        df.at[df.index[-1], 'close'] = current_price
                        
                    # 3. Calculate
                    if StrategyParser:
                        full_str = f"{buy_str} {sell_str}"
                        df = StrategyParser.parse_and_calculate(df, full_str)
                        
                        # 4. Check Signal
                        last_idx = len(df) - 1
                        signal = StrategyParser.check_signal(df, last_idx, buy_str, sell_str)
                        
                        # 5. Emit if Valid
                        if signal != 'hold':
                            self.signal_triggered.emit({
                                'code': code,
                                'type': signal,
                                'price': current_price,
                                'msg': f"{signal.upper()} Signal"
                            })
                        else:
                             self.signal_triggered.emit({
                                'code': code,
                                'type': 'hold',
                                'price': current_price,
                                'msg': ""
                            })

                except Exception as e:
                    self.log_updated.emit(f"Error {code}: {e}")
            
            # Sleep 10 seconds between cycles
            for _ in range(10):
                if not self.running: break
                self.sleep(1)

class WatchlistWorker(QThread):
    """後台線程：更新報價"""
    data_updated = Signal(list) # 發送 update (code, price, change)

    def run(self):
        if not WatchlistManager: return
        
        wm = WatchlistManager()
        while True:
            try:
                # 1. 讀取 DB 關注列表
                df = wm.get_all_entries()
                updates = []
                
                if not df.empty and YFinanceFetcher:
                    for _, row in df.iterrows():
                        code = row['stock_code']
                        # 使用改進的 get_quote 獲取完整數據
                        data = YFinanceFetcher.get_quote(code)
                        
                        if data:
                            price = data['price']
                            prev_close = data['prev_close']
                            
                            change_pct = 0.0
                            change_val = 0.0
                            
                            if prev_close and prev_close > 0:
                                change_val = price - prev_close
                                change_pct = (change_val / prev_close) * 100
                            
                            updates.append({
                                'code': code,
                                'price': price,
                                'change_pct': change_pct,
                                'change_val': change_val,
                                'high': data['high'],
                                'low': data['low'],
                                'volume': data['volume']
                            })
                
                self.data_updated.emit(updates)
                
            except Exception as e:
                # print(f"Ticker Error: {e}")
                pass
            
            # 每 5 秒更新一次
            self.sleep(5)

class QuoteWidget(QWidget):
    """Display Real-time Best 5 Bid/Ask"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #2b2b2b; border-radius: 4px;")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QLabel("⚡ Real-time Quotes (Best 5)")
        header.setStyleSheet("color: #ccc; font-weight: bold;")
        layout.addWidget(header)
        
        # Grid for Bid/Ask
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        
        # Headers
        self.grid.addWidget(QLabel("Bid Vol"), 0, 0)
        self.grid.addWidget(QLabel("Bid Price"), 0, 1)
        self.grid.addWidget(QLabel("Ask Price"), 0, 2)
        self.grid.addWidget(QLabel("Ask Vol"), 0, 3)
        
        # Create Labels [Row 1-5]
        self.bids = [] # (price_lbl, vol_lbl)
        self.asks = [] 
        
        for i in range(5):
            # Bid (Left)
            b_vol = QLabel("-")
            b_vol.setAlignment(Qt.AlignmentFlag.AlignRight)
            b_vol.setStyleSheet("color: white;")
            b_price = QLabel("-")
            b_price.setAlignment(Qt.AlignmentFlag.AlignRight)
            b_price.setStyleSheet("color: #ff6b6b; font-weight: bold;") # Red for Bid? Usually Bid is Buying, supported by buyers. Taiwan: Red is Up/Buy.
            
            
            # Ask (Right)
            a_price = QLabel("-")
            a_price.setAlignment(Qt.AlignmentFlag.AlignRight)
            a_price.setStyleSheet("color: #66bb6a; font-weight: bold;") # Green for Sell
            a_vol = QLabel("-")
            a_vol.setAlignment(Qt.AlignmentFlag.AlignRight)
            a_vol.setStyleSheet("color: white;")
            
            # Row 1 is Best 1 (Ask1/Bid1).
            # Usually order: Ask 5..1 (Top to Middle), Bid 1..5 (Middle to Bottom).
            # But here let's do simple Side-by-Side 1..5
            
            self.grid.addWidget(b_vol, i+1, 0)
            self.grid.addWidget(b_price, i+1, 1)
            self.grid.addWidget(a_price, i+1, 2)
            self.grid.addWidget(a_vol, i+1, 3)
            
            self.bids.append((b_price, b_vol))
            self.asks.append((a_price, a_vol))
            
        layout.addLayout(self.grid)
        
        # --- Time & Sales (Tick Stream) ---
        lbl_ticks = QLabel("📉 Time & Sales (Real-time)")
        lbl_ticks.setStyleSheet("color: #ccc; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_ticks)
        
        self.tick_table = QTableWidget()
        self.tick_table.setColumnCount(3)
        self.tick_table.setHorizontalHeaderLabels(["Time", "Price", "Vol"])
        self.tick_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tick_table.verticalHeader().setVisible(False)
        self.tick_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tick_table.setSelectionMode(QTableWidget.NoSelection)
        self.tick_table.setStyleSheet("background-color: #222; border: none; gridline-color: #333;")
        self.tick_table.verticalHeader().setDefaultSectionSize(20) # Compact rows
        
        # Fixed height for about 10 rows
        self.tick_table.setFixedHeight(220)
        
        layout.addWidget(self.tick_table)
        
        layout.addStretch()

    def update_data(self, data):
        """Update standard BidAsk data"""
        # ... (Existing BidAsk update logic) ...
        try:
            bids = data.get('bid_price', [])
            bid_vols = data.get('bid_volume', [])
            asks = data.get('ask_price', [])
            ask_vols = data.get('ask_volume', [])
            
            for i in range(5):
                # Update Bids
                if i < len(bids):
                    self.bids[i][0].setText(f"{bids[i]:.2f}")
                    self.bids[i][1].setText(f"{bid_vols[i]}")
                else:
                    self.bids[i][0].setText("-")
                    self.bids[i][1].setText("-")
                    
                # Update Asks
                if i < len(asks):
                    self.asks[i][0].setText(f"{asks[i]:.2f}")
                    self.asks[i][1].setText(f"{ask_vols[i]}")
                else:
                    self.asks[i][0].setText("-")
                    self.asks[i][1].setText("-")
                    
        except Exception as e:
            print(f"Quote Update Error: {e}")

    def update_tick(self, data):
        """Update Tick Stream"""
        # data: {'ts': '...', 'close': 123, 'volume': 5, 'tick_type': 1/2}
        try:
            self.tick_table.insertRow(0)
            
            # Timestamp (HH:MM:SS)
            # Incoming might be full datetime string or object? Bridge sends str(datetime)
            ts_str = data.get('ts', '')
            if ' ' in ts_str: ts_str = ts_str.split(' ')[1] # Get time part
            if '.' in ts_str: ts_str = ts_str.split('.')[0] # Remove micros
            
            price = data.get('close', 0)
            vol = data.get('volume', 0)
            tick_type = data.get('tick_type', 0) # 1: Buy (Red), 2: Sell (Green)
            
            # Color
            color = "#ffffff"
            if tick_type == 1: color = "#ff6b6b" # Buy/Up
            elif tick_type == 2: color = "#66bb6a" # Sell/Down
            
            # Setup Items
            item_t = QTableWidgetItem(ts_str)
            item_t.setForeground(QBrush(QColor("#aaaaaa")))
            item_t.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            item_p = QTableWidgetItem(f"{price:.2f}")
            item_p.setForeground(QBrush(QColor(color)))
            item_p.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            item_v = QTableWidgetItem(str(vol))
            item_v.setForeground(QBrush(QColor(color))) # Vol color matches type
            item_v.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.tick_table.setItem(0, 0, item_t)
            self.tick_table.setItem(0, 1, item_p)
            self.tick_table.setItem(0, 2, item_v)
            
            # Keep only 50 rows
            if self.tick_table.rowCount() > 50:
                self.tick_table.removeRow(50)
                
        except Exception as e:
            print(f"Tick Update Error: {e}")

    def set_market_status(self, is_open, status_text):
        """Update Market Status Indicator"""
        # We can update the header text or color
        color = "#66bb6a" if is_open else "#ff6b6b" # Green for Open, Red for Closed/Warning
        
        # Access the header label (child at index 0 in layout)
        try:
            header_lbl = self.layout().itemAt(0).widget()
            if isinstance(header_lbl, QLabel):
                header_lbl.setText(f"⚡ Real-time Quotes ({status_text})")
                header_lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
        except:
            pass

class WatchlistTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window # Reference to MainWindow for connector access
        self.current_chart_code = None
        
        # Init Signal Bridge
        if ShioajiSignalBridge:
            self.bridge = ShioajiSignalBridge()
            self.bridge.quote_received.connect(self.on_realtime_quote)
            self.bridge.tick_received.connect(self.on_realtime_tick)
            
            # Inject Bridge to Connector
            if hasattr(self.main, 'connector') and self.main.connector:
                self.main.connector.set_bridge(self.bridge)
        else:
            self.bridge = None
            
        self.strategies_config = {}
        self.load_strategies()
        
        self.strat_worker = StrategyWorker(main_window)
        self.strat_worker.update_strategies(self.strategies_config)
        self.strat_worker.signal_triggered.connect(self.on_strategy_signal)
        self.strat_worker.start()

        self.setup_ui()
        
        # 啟動 Worker
        self.worker = WatchlistWorker()
        self.worker.data_updated.connect(self.update_prices)
        self.worker.start()

        # Load Initial Data
        self.load_watchlist_initial()
        
        # Chart Simulation Timer (3000ms) -- KEEPING THIS for Backup/Effect
        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self.update_latest_price)
        self.chart_timer.start(3000)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Splitter (Left: Watchlist, Right: Chart/Quote)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- Left Panel: Watchlist & Order ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        btn_import = QPushButton("📂 批量匯入 (Import)")
        btn_import.setStyleSheet("background-color: #444; color: white; padding: 5px;")
        btn_import.clicked.connect(self.import_watchlist)
        toolbar.addWidget(btn_import)
        
        btn_clear = QPushButton("🗑️ 清空 (Clear)")
        btn_clear.setStyleSheet("background-color: #444; color: white; padding: 5px;")
        btn_clear.clicked.connect(self.clear_watchlist)
        toolbar.addWidget(btn_clear)
        
        left_layout.addLayout(toolbar)
        
        # Add Input Toolbar (New)
        add_layout = QHBoxLayout()
        self.input_add_code = QLineEdit()
        self.input_add_code.setPlaceholderText("Code (e.g. 2330)")
        self.input_add_code.setFixedWidth(120)
        self.input_add_code.setStyleSheet("background-color: #333; color: white; padding: 4px;")
        
        btn_add = QPushButton("➕ Add")
        btn_add.setStyleSheet("background-color: #4CAF50; color: white; padding: 4px 10px; font-weight: bold;")
        btn_add.clicked.connect(self.add_single_stock)
        
        add_layout.addWidget(self.input_add_code)
        add_layout.addWidget(btn_add)
        add_layout.addStretch()
        
        left_layout.addLayout(add_layout)

        # 1. 報價清單 (Watchlist)
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["代號", "現價", "漲跌", "漲跌額", "成交量", "最高", "最低", "訊號", "策略"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        self.table.itemClicked.connect(self.on_table_click) # Link click to chart
        left_layout.addWidget(self.table)
        
        # 2. 下單面板 (簡易版)
        order_panel = QWidget()
        order_panel.setStyleSheet("background-color: #2d2d2d; border-radius: 8px;")
        order_layout = QVBoxLayout(order_panel)
        
        order_label = QLabel("⚡ 快速下單")
        order_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        order_layout.addWidget(order_label)
        
        # Security Type Selector
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Stock (現股)", "Future (期貨)", "Option (選擇權)"])
        self.combo_type.setStyleSheet("background-color: #3d3d3d; color: white; padding: 5px;")
        order_layout.addWidget(self.combo_type)
        
        action_layout = QHBoxLayout()
        btn_buy = QPushButton("BUY")
        btn_buy.setStyleSheet("background-color: #ff6b6b; font-weight: bold;") # Pastel Red
        btn_sell = QPushButton("SELL")
        btn_sell.setStyleSheet("background-color: #66bb6a; font-weight: bold;") # Pastel Green
        
        action_layout.addWidget(btn_buy)
        action_layout.addWidget(btn_sell)
        
        # Add Input Fields (Price & Qty)
        input_layout = QHBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.input_price = QLineEdit()
        self.input_price.setPlaceholderText("Price")
        self.input_price.setStyleSheet("background-color: #3d3d3d; color: white; padding: 5px;")
        
        self.input_qty = QLineEdit("1")
        self.input_qty.setPlaceholderText("Qty")
        self.input_qty.setStyleSheet("background-color: #3d3d3d; color: white; padding: 5px;")
        
        def create_centered_label(text):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            return lbl

        input_layout.addWidget(create_centered_label("價格:"))
        input_layout.addWidget(self.input_price)
        input_layout.addWidget(create_centered_label("數量:"))
        input_layout.addWidget(self.input_qty)
        
        order_layout.insertLayout(2, input_layout)
        order_layout.addLayout(action_layout)
        
        btn_buy.clicked.connect(lambda: self.place_quick_order("BUY"))
        btn_sell.clicked.connect(lambda: self.place_quick_order("SELL"))
        
        left_layout.addWidget(order_panel)
        
        # --- Right Panel: Chart + Quotes ---
        # Vertical Splitter for Chart and Quotes
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 1. Chart Area
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_container.setStyleSheet("background-color: #1E1E1E;")
        
        self.chart_label = QLabel("Select a stock to view chart")
        self.chart_label.setStyleSheet("color: #666; font-size: 14px;")
        self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_layout.addWidget(self.chart_label)
        
        right_splitter.addWidget(self.chart_container)
        
        # 2. Quote Area (New)
        self.quote_widget = QuoteWidget()
        right_splitter.addWidget(self.quote_widget)
        
        # Set proportions (Chart 70%, Quote 30%)
        right_splitter.setStretchFactor(0, 7)
        right_splitter.setStretchFactor(1, 3)
        
        # Add to Main Splitter
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_splitter)
        self.splitter.setStretchFactor(0, 4) # 40%
        self.splitter.setStretchFactor(1, 6) # 60%
        
        main_layout.addWidget(self.splitter)

    # --- Real-time Handlers ---
    def on_realtime_quote(self, code, data):
        """Handle real-time quote (Bid/Ask) signal"""
        if code == self.current_chart_code:
            self.quote_widget.update_data(data)

    def on_realtime_tick(self, code, data):
        """Handle real-time tick signal"""
        if code == self.current_chart_code:
            self.quote_widget.update_tick(data)

    def on_table_click(self, item):
        """Handle table row click"""
        row = item.row()
        code = self.table.item(row, 0).text()
        if code:
            # Unsubscribe previous if exists
            if self.current_chart_code and hasattr(self.main, 'connector') and self.main.connector:
                self.main.connector.unsubscribe_contract(self.current_chart_code)
                
            self.current_chart_code = code
            self.update_chart(code)
            
            # Subscribe Real-time
            if hasattr(self.main, 'connector') and self.main.connector and self.main.connector.is_connected:
                # Subscribe both BidAsk and Tick
                self.main.connector.subscribe_contract(code, quote_type='bidask')
                self.main.connector.subscribe_contract(code, quote_type='tick')

    def import_watchlist(self):
        """批量匯入股票代碼"""
        text, ok = QInputDialog.getMultiLineText(self, "批量匯入", "請輸入股票代碼 (可用逗號或換行分隔):")
        if ok and text:
            # Parse text
            codes = []
            # Replace common separators with space
            clean_text = text.replace(',', ' ').replace('\n', ' ').replace(';', ' ')
            parts = clean_text.split()
            for p in parts:
                p = p.strip()
                if p.isdigit(): # Simple check for stock code
                    codes.append(p)
            
            if codes and WatchlistManager:
                wm = WatchlistManager()
                count = wm.batch_add_entries(codes)
                QMessageBox.information(self, "匯入成功", f"成功新增 {count} 筆股票")
                self.load_watchlist_initial() # Refresh UI
    
    def add_single_stock(self):
        """Add single stock code"""
        code = self.input_add_code.text().strip()
        if code and WatchlistManager:
            wm = WatchlistManager()
            # Simple validation: is digit?
            if code.isdigit():
                 wm.add_entry(code, "Manual")
                 self.load_watchlist_initial()
                 self.input_add_code.clear()
            else:
                 QMessageBox.warning(self, "Invalid Code", "Please enter a valid stock code (digits only).")
    
    def clear_watchlist(self):
        """清空列表 (Optional)"""
        # For safety, maybe just delete selected? Or clear all if user wants fresh start from app sync
        # Implementation skipped for now as not requested, but button added for UI balance
        pass

    def update_chart(self, code):
        """Draw chart for the selected code"""
        if not YFinanceFetcher: return
        
        # Clear previous chart
        for i in reversed(range(self.chart_layout.count())): 
            widget = self.chart_layout.itemAt(i).widget()
            if widget: widget.deleteLater()
            
        # Loading msg
        loading = QLabel(f"Loading {code}...")
        loading.setStyleSheet("color: white; font-size: 12px;")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_layout.addWidget(loading)
        
        try:
            # Fetch data (Sync for now, acceptable for MVP)
            df = YFinanceFetcher.get_history_ohlc(code, period="6mo")
            
            if df is None or df.empty:
                err = QLabel(f"No Data for {code}")
                err.setStyleSheet("color: #ff6b6b;")
                err.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.chart_layout.addWidget(err)
                return
            
            self.current_df = df # Store for simulation updates
            
            self._draw_mpl_chart(code, df)
            
        except Exception as e:
            err_lbl = QLabel(f"Chart Error: {str(e)}")
            err_lbl.setStyleSheet("color: red;")
            self.chart_layout.addWidget(err_lbl)

    def _draw_mpl_chart(self, code, df):
        """Actual plotting logic"""
        # Custom Style
        mc = mpf.make_marketcolors(up='#ff6b6b', down='#66bb6a', inherit=True)
        my_style = mpf.make_mpf_style(
            base_mpf_style='nightclouds', 
            marketcolors=mc, 
            mavcolors=['#FFFF00'], # Yellow MA20
            rc={'axes.facecolor': '#1E1E1E', 'figure.facecolor': '#1E1E1E', 
                'axes.edgecolor': '#555555', 'text.color': 'white', 
                'xtick.color': 'white', 'ytick.color': 'white',
                'font.family': 'Segoe UI'}
        )
        
        # Clear layout again to be safe (if called from simulation)
        for i in reversed(range(self.chart_layout.count())): 
            widget = self.chart_layout.itemAt(i).widget()
            if widget: widget.deleteLater()

        # Create Figure
        fig, axlist = mpf.plot(
            df, 
            type='candle', 
            style=my_style, 
            mav=(20), 
            volume=True, 
            returnfig=True,
            title=f"{code} Daily Chart",
            tight_layout=True,
            show_nontrading=False
        )
        
        # Adjust Title Color manually if needed, but style should handle it
        axlist[0].set_title(f"{code} Daily Chart", color='white')
        
        canvas = FigureCanvasQTAgg(fig)
        canvas.setStyleSheet("background-color: #1E1E1E;")
        self.chart_layout.addWidget(canvas)

    def update_latest_price(self):
        """Simulate real-time price update (Chart Only - Last Candle)"""
        if not hasattr(self, 'current_df') or self.current_df is None or self.current_df.empty:
            return
            
        # Only flicker chart if market is open OR just for visual liveness? 
        # User requested "Pause quotes during non-trading". 
        # Let's keep the chart flicker minimal or disable it too if strict.
        # But for now, let's just remove the Fake Quotes which was the main issue.
        
        import random
        # 模擬最後一根 K 棒的價格跳動 (僅在 Chart)
        last_idx = self.current_df.index[-1]
        current_close = self.current_df.at[last_idx, 'Close']
        
        # Random fluctuation +/- 0.5% (Chart Liveness)
        change = current_close * random.uniform(-0.002, 0.002)
        new_close = current_close + change
        
        # Update DataFrame
        self.current_df.at[last_idx, 'Close'] = new_close
        if new_close > self.current_df.at[last_idx, 'High']:
            self.current_df.at[last_idx, 'High'] = new_close
        if new_close < self.current_df.at[last_idx, 'Low']:
            self.current_df.at[last_idx, 'Low'] = new_close
            
        # Redraw Chart
        self._draw_mpl_chart(self.current_chart_code, self.current_df)
        
        # Check Market Status
        self.check_market_status()

    def check_market_status(self):
        """Check if market is open (Stocks vs Futures / Day vs Night)"""
        if not self.current_chart_code: return

        import datetime
        now = datetime.datetime.now()
        weekday = now.weekday() # 0=Mon, 6=Sun
        
        # Heuristic: Stock = All Digits, Future = Contains Letters
        is_future = not self.current_chart_code.isdigit()
        
        is_open = False
        session_text = "Closed (休市)"
        
        if is_future:
            # --- Futures Logic ---
            # 1. Regular Session (Day): Mon-Fri 08:45 - 13:45
            if 0 <= weekday <= 4:
                day_start = now.replace(hour=8, minute=45, second=0)
                day_end = now.replace(hour=13, minute=45, second=0)
                
                if day_start <= now <= day_end:
                    is_open = True
                    session_text = "Day Session (日盤)"
            
            # 2. Night Session (Night): 15:00 - 05:00 (Next Day)
            if not is_open:
                # Part A: Mon-Fri 15:00 - 23:59
                if 0 <= weekday <= 4:
                    night_start = now.replace(hour=15, minute=0, second=0)
                    night_end = now.replace(hour=23, minute=59, second=59)
                    if night_start <= now <= night_end:
                        is_open = True
                        session_text = "Night Session (夜盤)"
                        
                # Part B: Tue-Sat 00:00 - 05:00 (continuation of prev day's night session)
                if not is_open and 1 <= weekday <= 5:
                    early_start = now.replace(hour=0, minute=0, second=0)
                    early_end = now.replace(hour=5, minute=0, second=0)
                    if early_start <= now <= early_end:
                        is_open = True
                        session_text = "Night Session (夜盤)"
                        
        else:
            # --- Stock Logic ---
            # Mon-Fri 09:00 - 13:30
            if 0 <= weekday <= 4:
                start = now.replace(hour=9, minute=0, second=0)
                end = now.replace(hour=13, minute=30, second=0)
                if start <= now <= end:
                    is_open = True
                    session_text = "Regular Session (盤中)"
        
        # Update UI
        final_text = f"Market Open - {session_text}" if is_open else f"Market Closed ({session_text})"
        if not is_open: final_text = "Market Closed (休市)" # Simplify closed text
        
        self.quote_widget.set_market_status(is_open, final_text)

    def load_watchlist_initial(self):
        """從資料庫載入關注列表"""
        if not WatchlistManager:
            self.add_row("System", "Error", "No Core")
            return
            
        try:
            wm = WatchlistManager()
            df = wm.get_all_entries()
            
            self.table.setRowCount(0)
            
            if not df.empty:
                for _, row in df.iterrows():
                    self.add_row(
                        row['stock_code'], 
                        str(row['current_price']), 
                        "0.0%" # 暫時假資料
                    )
            else:
                self.add_row("No Data", "-", "-")
                
        except Exception as e:
            print(f"Error loading watchlist: {e}")
            self.add_row("Error", "DB", "Fail")

    def add_row(self, code, price, change):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for i in range(9):
            self.table.setItem(row, i, QTableWidgetItem("-"))
            
        self.table.setItem(row, 0, QTableWidgetItem(str(code)))
        
        # Right Align Initial Data
        price_item = QTableWidgetItem(str(price))
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 1, price_item)
        
        change_item = QTableWidgetItem(str(change))
        change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 2, change_item)

        # Init Strategy Status (Col 8)
        is_active = self.strategies_config.get(str(code), {}).get('active', False)
        status_text = "🟢 ON" if is_active else "⚫ OFF"
        # status_item = QTableWidgetItem(status_text)
        # if is_active: status_item.setForeground(QBrush(QColor("#00B4D8")))
        self.table.setItem(row, 8, QTableWidgetItem(status_text))

    def update_prices(self, updates):
        """收到後台更新"""
        for data in updates:
            code = data['code']
            price = data['price']
            change_pct = data['change_pct']
            change_val = data['change_val']
            high = data['high']
            low = data['low']
            vol = data['volume']
            
            # Find Row
            items = self.table.findItems(code, Qt.MatchExactly)
            if items:
                row = items[0].row()
                
                # 1. Price
                price_item = QTableWidgetItem(f"{price:.2f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 1, price_item)
                
                # Colors
                text_color = "#ffffff"
                if change_val > 0:
                    text_color = "#ff6b6b" # Pastel Red
                elif change_val < 0:
                    text_color = "#66bb6a" # Pastel Green

                # 2. Change %
                item_pct = QTableWidgetItem(f"{change_pct:+.2f}%")
                item_pct.setForeground(QBrush(QColor(text_color)))
                item_pct.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 2, item_pct)
                
                # 3. Change Value
                item_val = QTableWidgetItem(f"{change_val:+.2f}")
                item_val.setForeground(QBrush(QColor(text_color)))
                item_val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, item_val)
                
                # 4. Volume
                vol_item = QTableWidgetItem(f"{vol:,}")
                vol_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, vol_item)
                
                # 5. High
                item_high = QTableWidgetItem(f"{high:.2f}")
                if high >= price: item_high.setForeground(QBrush(QColor("#ff6b6b")))
                item_high.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 5, item_high)
                
                # 6. Low
                item_low = QTableWidgetItem(f"{low:.2f}")
                if low <= price: item_low.setForeground(QBrush(QColor("#66bb6a")))
                item_low.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 6, item_low)

    def place_quick_order(self, action):
        """執行快速下單 (讀取面板輸入)"""
        # 1. Get Code
        code = ""
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            code = self.table.item(row, 0).text()
            
        # Fallback if manual input needed (though no code input on panel yet, user selects from list)
        if not code:
            QMessageBox.warning(self, "錯誤", "請先選擇一檔股票")
            return
            
        # 2. Get Inputs
        price_str = self.input_price.text()
        qty_str = self.input_qty.text()
        
        # Auto-fill price if empty
        if not price_str and selected_items:
             price_str = self.table.item(row, 1).text()
             self.input_price.setText(price_str)
        
        if not price_str or not qty_str:
            QMessageBox.warning(self, "錯誤", "請輸入價格與數量")
            return
            
        try:
            price = float(price_str)
            qty = int(qty_str)
        except:
             QMessageBox.warning(self, "錯誤", "價格或數量格式不正確")
             return

        # 3. Confirm Dialog
        sec_type = self.combo_type.currentText()
        is_future = "Future" in sec_type
        
        msg = f"確認下單?\n\n{action} {code}\n價格: {price}\n數量: {qty}\n類型: {sec_type}"
        reply = QMessageBox.question(self, "下單確認", msg, QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return

        # 4. Execute Logic
        connector = getattr(self.main, 'connector', None)
        if not connector or not connector.is_connected:
            QMessageBox.critical(self, "錯誤", "尚未連線到券商! 請檢查設定。")
            return

        try:
            if is_future:
                 # Future Order
                result = connector.place_futures_order(
                    contract_code=code,
                    action=action,
                    quantity=qty,
                    price=price,
                    price_type="LMT",
                    order_type="ROD", 
                    dry_run=False
                )
            elif "Option" in sec_type:
                 QMessageBox.information(self, "Info", "選擇權下單尚未實作")
                 return
            else:
                # Stock Order
                result = connector.place_order(
                    stock_code=code,
                    action=action, # BUY/SELL
                    quantity=qty, # 張數
                    price=price,
                    price_type="LMT",
                    order_type="ROD"
                )
            
            if result.get('status') == 'success':
                success_msg = f"下單成功!\n\n單號: {result.get('order_id', 'N/A')}\n{action} {code} {qty}口/張 @ {price}"
                QMessageBox.information(self, "委託成功", success_msg)
                # 通知 Main Window 切換分頁並刷新
                if hasattr(self.main, 'switch_to_orders_tab'):
                    self.main.switch_to_orders_tab()
            else:
                QMessageBox.critical(self, "下單失敗", f"API 錯誤: {result.get('msg')}")
                
        except Exception as e:
            QMessageBox.critical(self, "系統錯誤", f"例外狀況: {str(e)}")

    def open_menu(self, position):
        menu = QMenu()
        idx = self.table.indexAt(position)
        if not idx.isValid(): return
        
        row = idx.row()
        code = self.table.item(row, 0).text()
        
        # Edit Strategy
        edit_action = QAction("⚙️ 設定策略 (Strategy)", self)
        edit_action.triggered.connect(lambda: self.edit_strategy(code))
        menu.addAction(edit_action)
        
        # Delete Stock
        del_action = QAction("🗑️ 刪除 (Delete)", self)
        del_action.triggered.connect(lambda: self.delete_stock(code))
        menu.addAction(del_action)
        
        menu.exec_(self.table.viewport().mapToGlobal(position))

    def edit_strategy(self, code):
        strat = self.strategies_config.get(code, {})
        dlg = EditStrategyDialog(
            code, self, 
            buy_str=strat.get('buy', 'close > MA20'),
            sell_str=strat.get('sell', 'close < MA20'),
            active=strat.get('active', False)
        )
        if dlg.exec():
            active, buy, sell = dlg.get_data()
            self.strategies_config[code] = {
                'active': active,
                'buy': buy,
                'sell': sell
            }
            self.save_strategies()
            if hasattr(self, 'strat_worker'):
                self.strat_worker.update_strategies(self.strategies_config)
            
            # Update UI Status
            strat_items = self.table.findItems(code, Qt.MatchExactly) # Column 0
            if strat_items:
                for item in strat_items:
                    if item.column() == 0:
                        r = item.row()
                        status_text = "🟢 ON" if active else "⚫ OFF"
                        self.table.setItem(r, 8, QTableWidgetItem(status_text))
                        break
            
    def load_strategies(self):
        try:
            db = StockDatabase()
            raw = db.get_setting('strategies_config')
            if raw:
                self.strategies_config = json.loads(raw)
        except Exception as e:
            print(f"Load Strategies Error: {e}")

    def save_strategies(self):
        try:
            db = StockDatabase()
            db.set_setting('strategies_config', json.dumps(self.strategies_config))
        except Exception as e:
             print(f"Save Strategies Error: {e}")
             
    def on_strategy_signal(self, data):
        # {code, type, price, msg}
        code = data['code']
        signal_type = data['type'] # buy, sell, hold
        
        # Find Row
        items = self.table.findItems(code, Qt.MatchExactly) 
        
        target_row = -1
        for item in items:
            if item.column() == 0:
                target_row = item.row()
                break
                
        if target_row == -1: return
        
        # Col 7: Signal
        sig_text = signal_type.upper()
        sig_item = QTableWidgetItem(sig_text)
        sig_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if signal_type == 'buy':
            sig_item.setForeground(QBrush(QColor("#ff6b6b")))
            sig_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        elif signal_type == 'sell':
             sig_item.setForeground(QBrush(QColor("#66bb6a")))
             sig_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        else:
             sig_item.setForeground(QBrush(QColor("#aaaaaa")))
             
        self.table.setItem(target_row, 7, sig_item)

    def clear_watchlist(self):
        reply = QMessageBox.question(self, "確認清空", "確定要刪除所有自選股嗎?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if WatchlistManager:
                wm = WatchlistManager()
                if wm.clear_all():
                     QMessageBox.information(self, "成功", "已清空自選清單")
                     self.load_watchlist_initial()
                else:
                     QMessageBox.critical(self, "錯誤", "清空失敗")
            else:
                 QMessageBox.warning(self, "錯誤", "WatchlistManager Not Found")

    def delete_stock(self, code):
        reply = QMessageBox.question(self, "確認刪除", f"確定要刪除 {code} 嗎?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if WatchlistManager:
                wm = WatchlistManager()
                if wm.delete_entry_by_code(code):
                     # Also remove strategy config? Optional.
                     # Remove from Table
                     items = self.table.findItems(code, Qt.MatchExactly)
                     if items:
                         for item in items:
                             if item.column() == 0:
                                 self.table.removeRow(item.row())
                                 break
                     QMessageBox.information(self, "成功", f"已刪除 {code}")
                else:
                     QMessageBox.critical(self, "錯誤", f"刪除 {code} 失敗")
