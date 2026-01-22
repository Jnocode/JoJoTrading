
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox, QGridLayout, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from jojo_trader.ui.components.backtest_chart import BacktestChart
from jojo_trader.ui.components.dcf_widget import DCFWidget
from jojo_trading.analysis.backtest.data_adapter import BacktestDataAdapter
import pandas as pd

class AnalysisWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, code):
        super().__init__()
        self.code = code
        
    def run(self):
        try:
            # Fetch Price Data
            # Use data adapter to get standardized DF
            data_map = BacktestDataAdapter.get_kline_data(self.code, period="1y", interval="1d")
            
            if not data_map or 'daily' not in data_map or data_map['daily'].empty:
                self.error.emit(f"No data found for {self.code}")
                return
                
            df = data_map['daily']
            
            # Fetch Fundamental Data (Mock or partial if adapter merges it)
            # data_adapter already tries to merge 'Revenue_YOY', 'EPS', 'Foreign_Buy'
            
            last_row = df.iloc[-1]
            
            info = {
                'price': last_row['close'],
                'change': 0.0, # Need prev close
                'vol': last_row['volume'],
                'rev_yoy': last_row.get('Revenue_YOY', 0),
                'eps': last_row.get('EPS', 0),
                'foreign': last_row.get('Foreign_Buy', 0),
                'trust': last_row.get('IT_Buy', 0)
            }
            
            # Calculate Change
            if len(df) > 1:
                prev = df.iloc[-2]['close']
                info['change'] = ((last_row['close'] - prev) / prev) * 100
            
            self.finished.emit({'df': df, 'info': info})
            
        except Exception as e:
            self.error.emit(str(e))

class AnalysisTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        self.worker = None
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        # 1. Top Bar
        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: #252525; border-bottom: 1px solid #444;")
        top_layout = QHBoxLayout(top_frame)
        
        top_layout.addWidget(QLabel("🔍 股票代號:"))
        self.input_code = QLineEdit("2330")
        self.input_code.setFixedWidth(100)
        self.input_code.setStyleSheet("background: #000; color: white; padding: 4px; border: 1px solid #555;")
        top_layout.addWidget(self.input_code)
        
        self.btn_search = QPushButton("搜尋 (Search)")
        self.btn_search.setStyleSheet("background-color: #007ACC; color: white; padding: 5px 15px; border: none; border-radius: 3px;")
        self.btn_search.clicked.connect(self.start_analysis)
        top_layout.addWidget(self.btn_search)
        
        self.btn_sector = QPushButton("類股快篩 (Sector)")
        self.btn_sector.setStyleSheet("background-color: #9C27B0; color: white; padding: 5px 15px; border: none; border-radius: 3px; margin-left: 10px;")
        self.btn_sector.clicked.connect(self.open_sector_scan)
        top_layout.addWidget(self.btn_sector)
        
        top_layout.addStretch()
        layout.addWidget(top_frame)
        
        # 2. Main Content (Splitter)
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.main_splitter)
        
        # --- Top Section: Info + DCF (Horizontal Splitter) ---
        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Info Panel
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #1E1E1E;")
        info_layout = QGridLayout(info_frame)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        def make_lbl(text, size=14, color="#AAA"):
            l = QLabel(text)
            l.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: bold;")
            return l
            
        self.lbl_price = make_lbl("---", 24, "white")
        self.lbl_change = make_lbl("0.00%", 16)
        
        info_layout.addWidget(QLabel("價格 (Price)"), 0, 0)
        info_layout.addWidget(self.lbl_price, 1, 0)
        info_layout.addWidget(self.lbl_change, 1, 1)
        
        self.lbl_rev = make_lbl("---")
        self.lbl_eps = make_lbl("---")
        
        info_layout.addWidget(QLabel("營收年增 (Rev YoY)"), 2, 0)
        info_layout.addWidget(self.lbl_rev, 3, 0)
        
        info_layout.addWidget(QLabel("EPS"), 2, 1)
        info_layout.addWidget(self.lbl_eps, 3, 1)
        
        self.lbl_chip = make_lbl("---")
        info_layout.addWidget(QLabel("外資 (Foreign)"), 4, 0)
        info_layout.addWidget(self.lbl_chip, 5, 0)
        
        self.top_splitter.addWidget(info_frame)
        
        # Right: DCF Widget
        self.dcf_widget = DCFWidget()
        self.top_splitter.addWidget(self.dcf_widget)
        self.top_splitter.setStretchFactor(0, 4)
        self.top_splitter.setStretchFactor(1, 6)
        
        self.main_splitter.addWidget(self.top_splitter)
        
        # --- Bottom Section: Chart ---
        self.chart = BacktestChart()
        self.main_splitter.addWidget(self.chart)
        self.main_splitter.setStretchFactor(0, 4) # 40%
        self.main_splitter.setStretchFactor(1, 6) # 60%
        
    def open_sector_scan(self):
        # Redirect to Screener Tab for now
        if hasattr(self.main_window, 'tabs'):
             # Index 3 is usually Screener
             self.main_window.tabs.setCurrentIndex(3)
             QMessageBox.information(self, "Info", "已切換至篩選器 (Screener) 分頁進行類股篩選。")
        
    def start_analysis(self):
        code = self.input_code.text().strip()
        if not code: return
        
        self.btn_search.setEnabled(False)
        self.btn_search.setText("載入中...")
        
        self.worker = AnalysisWorker(code)
        self.worker.finished.connect(self.on_data_ready)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_data_ready(self, result):
        self.btn_search.setEnabled(True)
        self.btn_search.setText("搜尋 (Search)")
        
        info = result['info']
        df = result['df']
        
        # Update Labels
        self.lbl_price.setText(f"{info['price']:.2f}")
        
        chg = info['change']
        chg_color = "#FF0000" if chg > 0 else "#00FF00" # TW Colors
        self.lbl_change.setText(f"{chg:.2f}%")
        self.lbl_change.setStyleSheet(f"color: {chg_color}; font-size: 16px; font-weight: bold;")
        
        rev = info['rev_yoy']
        self.lbl_rev.setText(f"{rev:.2f}%")
        self.lbl_rev.setStyleSheet(f"color: {'#FF0000' if rev > 0 else '#00FF00'}; font-size: 14px;")
        
        self.lbl_eps.setText(f"{info['eps']:.2f}")
        
        f_buy = info['foreign']
        self.lbl_chip.setText(f"{f_buy:,.0f} 張")
        self.lbl_chip.setStyleSheet(f"color: {'#FF0000' if f_buy > 0 else '#00FF00'}; font-size: 14px;")
        
        # Update Chart
        self.chart.plot(df, []) # No trades
        
        # Update DCF Data
        # Try to estimate Net Income if EPS and Price available
        # Shares = MarketCap / Price? Or Income / EPS?
        try:
             price = info['price']
             eps = info['eps']
             
             # Mock values if not available in basic info
             # Real implementation would need 'shares_outstanding' from API
             shares = 10.0 # Default 10億
             net_income = shares * eps if eps else 10.0
             
             self.dcf_widget.set_data(price, net_income, shares)
        except: pass
        
    def on_error(self, msg):
        self.btn_search.setEnabled(True)
        self.btn_search.setText("搜尋 (Search)")
        QMessageBox.warning(self, "Error", msg)
