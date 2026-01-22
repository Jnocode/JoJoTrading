
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt
import random

class ScreenerTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Filter Panel
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: #252525; padding: 10px; border-radius: 6px;")
        filter_layout = QHBoxLayout(filter_frame)
        
        self.chk_vol = QCheckBox("成交量 >")
        self.chk_vol.setChecked(True)
        self.spin_vol = QSpinBox()
        self.spin_vol.setRange(0, 100000)
        self.spin_vol.setValue(1000)
        self.spin_vol.setSuffix(" 張")
        
        self.chk_price_up = QCheckBox("今日上漲 (Change > 0%)")
        self.chk_price_up.setChecked(True)
        
        self.chk_ma_bull = QCheckBox("均線多頭排 (MA5 > MA20 > MA60)")
        
        filter_layout.addWidget(self.chk_vol)
        filter_layout.addWidget(self.spin_vol)
        filter_layout.addWidget(self.chk_price_up)
        filter_layout.addWidget(self.chk_ma_bull)
        
        self.btn_scan = QPushButton("🔍 開始掃描 (Scan)")
        self.btn_scan.setStyleSheet("background-color: #9C27B0; color: white; border: none; padding: 8px 20px; border-radius: 4px; font-weight: bold;")
        self.btn_scan.clicked.connect(self.run_scan)
        filter_layout.addWidget(self.btn_scan)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # 2. Result Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Price", "Change %", "Volume"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1E1E1E; gridline-color: #333; }
            QHeaderView::section { background-color: #333; color: white; padding: 5px; }
            QTableWidget::item { padding: 5px; }
        """)
        
        layout.addWidget(self.table)
        
    def run_scan(self):
        # Mock Scan for Demo (Since full DB scan is expensive individually)
        self.table.setRowCount(0)
        self.btn_scan.setText("掃描中...")
        self.btn_scan.setEnabled(False)
        
        # Simulated Results
        mock_data = [
            {"code": "2330", "name": "台積電", "price": 1050, "chg": 1.5, "vol": 35000},
            {"code": "2454", "name": "聯發科", "price": 1200, "chg": 2.1, "vol": 5600},
            {"code": "2317", "name": "鴻海", "price": 205, "chg": -0.5, "vol": 89000},
            {"code": "2603", "name": "長榮", "price": 185, "chg": 0.8, "vol": 45000},
            {"code": "2609", "name": "陽明", "price": 65, "chg": 3.2, "vol": 120000},
            {"code": "3231", "name": "緯創", "price": 123, "chg": 1.1, "vol": 23000},
        ]
        
        # Apply Filter (Fake logic)
        filtered = []
        min_vol = self.spin_vol.value()
        req_up = self.chk_price_up.isChecked()
        
        for d in mock_data:
            if d['vol'] < min_vol: continue
            if req_up and d['chg'] <= 0: continue
            filtered.append(d)
            
        self.table.setRowCount(len(filtered))
        for r, row in enumerate(filtered):
            self.table.setItem(r, 0, QTableWidgetItem(row['code']))
            self.table.setItem(r, 1, QTableWidgetItem(row['name']))
            
            p_item = QTableWidgetItem(str(row['price']))
            p_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 2, p_item)
            
            c_item = QTableWidgetItem(f"{row['chg']:.2f}%")
            if row['chg'] > 0: c_item.setForeground(Qt.red)
            elif row['chg'] < 0: c_item.setForeground(Qt.green)
            c_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 3, c_item)
            
            v_item = QTableWidgetItem(f"{row['vol']:,}")
            v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 4, v_item)
            
        self.btn_scan.setText("🔍 開始掃描 (Scan)")
        self.btn_scan.setEnabled(True)
