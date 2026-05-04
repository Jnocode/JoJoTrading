
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox, QGridLayout, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from jojo_trading.ui.ui.components.backtest_chart import BacktestChart
from jojo_trading.ui.ui.components.dcf_widget import DCFWidget
from jojo_trading.ui.ui.components.chip_monitor import ChipMonitorWidget
from jojo_trading.analysis.backtest.data_adapter import BacktestDataAdapter
import pandas as pd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox, QGridLayout, QSplitter, QTabWidget, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from jojo_trading.ui.ui.components.backtest_chart import BacktestChart
from jojo_trading.ui.ui.components.dcf_widget import DCFWidget
from jojo_trading.ui.ui.components.chip_monitor import ChipMonitorWidget

from jojo_trading.core.analysis_controller import AnalysisController

class AnalysisWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, code):
        super().__init__()
        self.code = code
        self.controller = AnalysisController()
        
    def run(self):
        try:
            # 使用 Controller 統一獲取全部報價與 AI 分析
            result_bundle, err_msg = self.controller.fetch_data_and_analyze(self.code)
            
            if err_msg:
                self.error.emit(err_msg)
            else:
                self.finished.emit(result_bundle)
                
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
        self.input_code.setMinimumWidth(80)
        self.input_code.setMaximumWidth(150)
        self.input_code.setStyleSheet("background: #000; color: white; padding: 4px; border: 1px solid #555;")
        self.input_code.returnPressed.connect(self.start_analysis)
        top_layout.addWidget(self.input_code)
        
        self.btn_search = QPushButton("🤖 深度分析 (Deep Analysis)")
        self.btn_search.setStyleSheet("background-color: #007ACC; color: white; padding: 5px 15px; border: none; border-radius: 3px; font-weight: bold;")
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
        
        # --- Top Section: Info + AI Radar + DCF (Horizontal Splitter) ---
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
            
        self.lbl_name = make_lbl("---", 18, "#00B4D8")
        self.lbl_price = make_lbl("---", 24, "white")
        self.lbl_change = make_lbl("0.00%", 16)
        
        info_layout.addWidget(self.lbl_name, 0, 0, 1, 2)
        info_layout.addWidget(QLabel("價格 (Price)"), 1, 0)
        info_layout.addWidget(self.lbl_price, 2, 0)
        info_layout.addWidget(self.lbl_change, 2, 1)
        
        self.lbl_rev = make_lbl("---")
        self.lbl_eps = make_lbl("---")
        
        info_layout.addWidget(QLabel("營收年增 (Rev YoY)"), 3, 0)
        info_layout.addWidget(self.lbl_rev, 4, 0)
        
        info_layout.addWidget(QLabel("EPS"), 3, 1)
        info_layout.addWidget(self.lbl_eps, 4, 1)
        
        self.lbl_chip = make_lbl("---")
        info_layout.addWidget(QLabel("外資 (Foreign)"), 5, 0)
        info_layout.addWidget(self.lbl_chip, 6, 0)
        
        self.top_splitter.addWidget(info_frame)
        
        # Middle: AI Radar Report
        radar_frame = QFrame()
        radar_frame.setStyleSheet("background-color: #2D2D2D; border-radius: 6px;")
        radar_layout = QVBoxLayout(radar_frame)
        radar_layout.setContentsMargins(5, 5, 5, 5)
        
        radar_title = QLabel("🧭 AI 技術籌碼共振雷達")
        radar_title.setStyleSheet("color: #BB86FC; font-weight: bold; font-size: 14px;")
        radar_layout.addWidget(radar_title)
        
        self.txt_ai_report = QTextEdit()
        self.txt_ai_report.setReadOnly(True)
        self.txt_ai_report.setStyleSheet("""
            background-color: #1E1E1E; color: #E0E0E0; font-family: Consolas, 'Courier New'; 
            font-size: 13px; border: 1px solid #444; border-radius: 4px; padding: 8px;
        """)
        self.txt_ai_report.setPlaceholderText("等待分析...")
        radar_layout.addWidget(self.txt_ai_report)
        
        self.top_splitter.addWidget(radar_frame)
        
        # Right: DCF Widget
        self.dcf_widget = DCFWidget()
        self.top_splitter.addWidget(self.dcf_widget)
        
        # Set Top Splitter Sizes (20% Info, 40% AI, 40% DCF)
        self.top_splitter.setStretchFactor(0, 20)
        self.top_splitter.setStretchFactor(1, 40)
        self.top_splitter.setStretchFactor(2, 40)
        
        self.main_splitter.addWidget(self.top_splitter)
        
        # --- Bottom Section: Tab Component (Chart + Chips) ---
        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #2D2D2D; color: #AAA; padding: 6px; }
            QTabBar::tab:selected { background: #1E1E1E; color: white; border-top: 2px solid #007ACC; }
        """)
        
        # Tab 1: Chart
        self.chart = BacktestChart()
        self.bottom_tabs.addTab(self.chart, "📈 技術線圖 (Chart)")
        
        # Tab 2: Chip Monitor
        # Get Bridge from MainWindow
        bridge = None
        if hasattr(self.main_window, 'bridge'):
            bridge = getattr(self.main_window, 'bridge')
            
        self.chip_monitor = ChipMonitorWidget(bridge)
        self.bottom_tabs.addTab(self.chip_monitor, "⚡ 即時籌碼 (Chip Monitor)")
        
        self.main_splitter.addWidget(self.bottom_tabs)
        self.main_splitter.setStretchFactor(0, 3) # 30% Top
        self.main_splitter.setStretchFactor(1, 7) # 70% Bottom
        
    def open_sector_scan(self):
        # Redirect to Screener Tab (index 4)
        if hasattr(self.main_window, 'tabs'):
             self.main_window.tabs.setCurrentIndex(4)
             QMessageBox.information(self, "類股篩選", "已切換至掃描器 (Screener)。\n\n💡 試著告訴 AI 您的篩選邏輯吧！")
        
    def start_analysis(self):
        code = self.input_code.text().strip()
        if not code: return
        
        self.btn_search.setEnabled(False)
        self.btn_search.setText("🤖 AI 推演中...")
        self.txt_ai_report.setPlainText("系統正在抓取歷史價量與籌碼，並交由 AI 分析師推演多空邏輯...\n\n請稍候...")
        
        self.worker = AnalysisWorker(code)
        self.worker.finished.connect(self.on_data_ready)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
        # Reset Chip Monitor
        if hasattr(self, 'chip_monitor'):
            self.chip_monitor.reset(code)
            
            # Auto Subscribe if Connected
            if self.main_window and hasattr(self.main_window, 'connector'):
                connector = self.main_window.connector
                if connector and connector.is_connected:
                     connector.subscribe_contract(code, quote_type='tick')
                     connector.subscribe_contract(code, quote_type='bidask')
        
    def on_data_ready(self, result_bundle):
        self.btn_search.setEnabled(True)
        self.btn_search.setText("🤖 深度分析 (Deep Analysis)")
        
        info = result_bundle['info']
        df = result_bundle['df']
        ai_msg = result_bundle['ai_report']
        
        # Update AI Report
        self.txt_ai_report.setPlainText(ai_msg)
        
        # Update Labels
        self.lbl_name.setText(f"{info.get('name', info['symbol'])}")
        self.lbl_price.setText(f"{info['price']:.2f}")
        
        chg = info['change']
        chg_color = "#FF0000" if chg > 0 else "#00FF00" # TW Colors
        self.lbl_change.setText(f"{chg:.2f}%")
        self.lbl_change.setStyleSheet(f"color: {chg_color}; font-size: 16px; font-weight: bold;")
        
        rev = info['rev_yoy']
        self.lbl_rev.setText(f"{rev:.2f}%")
        self.lbl_rev.setStyleSheet(f"color: {'#FF0000' if rev > 0 else '#00FF00'}; font-size: 14px;")
        
        self.lbl_eps.setText(f"{info['eps']:.2f}")
        
        f_buy = info.get('foreign_buy', 0)
        f_buy_lots = f_buy / 1000 if f_buy else 0
        self.lbl_chip.setText(f"{f_buy_lots:,.0f} 張")
        self.lbl_chip.setStyleSheet(f"color: {'#FF0000' if f_buy_lots > 0 else '#00FF00'}; font-size: 14px;")
        
        # Update Chart
        self.chart.plot(df, []) # No trades
        
        # Update DCF Data — 使用 stocks.db 的統一資料源
        try:
             price = info['price']
             shares = info.get('shares', 10.0)
             net_income = info.get('net_income', 10.0)
             intrinsic_value = info.get('intrinsic_value', 0.0)
             data_source = info.get('data_source', '')
             
             self.dcf_widget.set_data(price, net_income, shares, intrinsic_value, data_source)
        except: pass
        
    def on_error(self, msg):
        self.btn_search.setEnabled(True)
        self.btn_search.setText("🤖 深度分析 (Deep Analysis)")
        self.txt_ai_report.setPlainText(f"⚠️ 發生錯誤:\n\n{msg}")
        QMessageBox.warning(self, "Error", msg)
