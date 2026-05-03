from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QCursor, QColor

from jojo_trading.core.screener_controller import ScreenerController

class ScreenerWorker(QThread):
    finished = Signal(list, str) # results, error_msg

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
        self.controller = ScreenerController()

    def run(self):
        results, err = self.controller.scan_by_natural_language(self.prompt)
        self.finished.emit(results, err)

class ScreenerTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. NLP Input Panel
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #252525; padding: 10px; border-radius: 6px;")
        input_layout = QVBoxLayout(input_frame)
        
        lbl_hint = QLabel("🤖 告訴 AI 你想找什麼樣的股票？(例如: 幫我找外資連買且均線多頭排列的半導體股票)")
        lbl_hint.setStyleSheet("color: #BB86FC; font-weight: bold;")
        input_layout.addWidget(lbl_hint)
        
        search_box = QHBoxLayout()
        self.txt_prompt = QLineEdit()
        self.txt_prompt.setPlaceholderText("輸入白話文選股條件...")
        self.txt_prompt.setStyleSheet("""
            QLineEdit {
                background-color: #333; color: white; border: 1px solid #555; 
                padding: 10px; border-radius: 4px; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #9C27B0; }
        """)
        self.txt_prompt.returnPressed.connect(self.run_scan)
        
        self.btn_scan = QPushButton("✨ AI 智能掃描")
        self.btn_scan.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_scan.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; font-size: 14px;}
            QPushButton:hover { background-color: #BA68C8; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_scan.clicked.connect(self.run_scan)
        
        search_box.addWidget(self.txt_prompt)
        search_box.addWidget(self.btn_scan)
        input_layout.addLayout(search_box)
        
        # Quick Filters
        quick_filters_layout = QHBoxLayout()
        lbl_quick = QLabel("⚡ 快速篩選:")
        lbl_quick.setStyleSheet("color: #AAA; font-size: 12px; font-weight: bold;")
        quick_filters_layout.addWidget(lbl_quick)
        
        quick_prompts = [
            "DCF 估值潛在收益超過 5%",
            "市值大於 1000 億的半導體",
            "股價小於 50 且有潛在報酬"
        ]
        
        for qp in quick_prompts:
            btn_q = QPushButton(qp)
            btn_q.setCursor(QCursor(Qt.PointingHandCursor))
            btn_q.setStyleSheet("""
                QPushButton { background-color: #333; color: #CCC; border: 1px solid #555; padding: 5px 10px; border-radius: 12px; font-size: 12px;}
                QPushButton:hover { background-color: #555; color: white; border: 1px solid #9C27B0; }
            """)
            btn_q.clicked.connect(lambda checked=False, p=qp: self.set_and_run_prompt(p))
            quick_filters_layout.addWidget(btn_q)
            
        quick_filters_layout.addStretch()
        input_layout.addLayout(quick_filters_layout)
        
        layout.addWidget(input_frame)
        
        # 2. Result Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Price", "Change %", "Volume", "Sector"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1E1E1E; gridline-color: #333; border: none; }
            QHeaderView::section { background-color: #333; color: white; padding: 8px; font-weight: bold; border: none; }
            QTableWidget::item { padding: 5px; color: #E0E0E0;}
            QTableWidget::item:hover { background-color: #3A3A3A; }
        """)
        # 雙擊跳轉到分析頁面
        self.table.cellDoubleClicked.connect(self.on_stock_double_clicked)
        
        layout.addWidget(self.table)
        
    def set_and_run_prompt(self, text: str):
        self.txt_prompt.setText(text)
        self.run_scan()

    def run_scan(self):
        prompt = self.txt_prompt.text().strip()
        if not prompt:
            return
            
        self.table.setRowCount(0)
        self.btn_scan.setText("⏳ AI 解析與篩選中...")
        self.btn_scan.setEnabled(False)
        
        self.worker = ScreenerWorker(prompt)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()
        
    def on_scan_finished(self, results, err):
        self.btn_scan.setText("✨ AI 智能掃描")
        self.btn_scan.setEnabled(True)
        
        if err:
            QMessageBox.warning(self, "掃描錯誤", err)
            return
            
        if not results:
            QMessageBox.information(self, "掃描結果", "沒有找到符合條件的股票。")
            return
            
        self.table.setRowCount(len(results))
        for r, row in enumerate(results):
            self.table.setItem(r, 0, QTableWidgetItem(str(row.get('code', ''))))
            self.table.setItem(r, 1, QTableWidgetItem(str(row.get('name', ''))))
            
            p_item = QTableWidgetItem(str(row.get('price', '')))
            p_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 2, p_item)
            
            chg = row.get('chg', 0)
            c_item = QTableWidgetItem(f"{chg:.2f}%")
            if chg > 0: c_item.setForeground(QColor("#FF5252")) # Red Up in TW
            elif chg < 0: c_item.setForeground(QColor("#69F0AE")) # Green Down
            c_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 3, c_item)
            
            vol = row.get('vol', 0)
            v_item = QTableWidgetItem(f"{vol:,}")
            v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 4, v_item)
            
            self.table.setItem(r, 5, QTableWidgetItem(str(row.get('sector', ''))))
    
    def on_stock_double_clicked(self, row, col):
        """雙擊股票跳轉到分析頁面"""
        code_item = self.table.item(row, 0)
        if not code_item:
            return
        
        stock_code = code_item.text()
        
        # 跳轉到 Analysis Tab (index 2)
        if hasattr(self.main_window, 'tabs') and hasattr(self.main_window, 'analysis_tab'):
            self.main_window.tabs.setCurrentIndex(2)  # Analysis Tab
            self.main_window.analysis_tab.input_code.setText(stock_code)
            self.main_window.analysis_tab.start_analysis()
