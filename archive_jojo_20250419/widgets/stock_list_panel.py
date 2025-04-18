import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
                             QGroupBox, QHeaderView, QMenu, QMessageBox, QDialog, QLineEdit,
                             QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
from core.engine import MainEngine # 假設 MainEngine 在 core 目錄
from datetime import datetime
import numpy as np # 需要 numpy 來處理 np.isnan
from typing import Dict, Optional, Any

class AddStockDialog(QDialog):
    """添加股票的對話框"""
    def __init__(self, parent: Optional[QWidget] = None):
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
        return self.stock_id_input.text().strip().upper()

class StockListPanel(QGroupBox):
    """股票監視清單面板"""
    signal_status_message = pyqtSignal(str, int) # 信號：發送狀態欄消息 (訊息, 持續時間ms)

    def __init__(self, main_engine: MainEngine, parent: Optional[QWidget] = None):
        super().__init__("股票監視清單", parent)
        self.main_engine = main_engine
        self.stock_data_cache: Dict[str, Dict] = {} # 緩存股票數據
        self._init_ui()

    def _init_ui(self):
        """初始化 UI 元件"""
        layout = QVBoxLayout(self)

        # --- 按鈕區域 ---
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        add_button = QPushButton("添加/訂閱股票")
        add_button.clicked.connect(self.add_stock) # 連接到此類的方法
        add_button.setToolTip("添加新的股票代碼到監視列表並訂閱行情")
        buttons_layout.addWidget(add_button)
        self.add_index_button = QPushButton("訂閱大盤")
        self.add_index_button.clicked.connect(self._add_index) # 連接到此類的方法
        self.add_index_button.setToolTip("訂閱大盤指數行情")
        buttons_layout.addWidget(self.add_index_button)
        buttons_layout.addStretch()
        layout.addWidget(buttons_widget)

        # --- 股票表格 ---
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(7)
        self.stock_table.setHorizontalHeaderLabels(["代碼", "價格", "漲跌%", "總量", "趨勢", "信號", "更新"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.stock_table.horizontalHeader().setStretchLastSection(True)
        self.stock_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stock_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stock_table.customContextMenuRequested.connect(self.show_stock_table_menu) # 連接到此類的方法
        layout.addWidget(self.stock_table)

    # --- 添加/訂閱股票 ---
    @pyqtSlot()
    def add_stock(self):
        """打開添加股票對話框並觸發訂閱"""
        dialog = AddStockDialog(self)
        if dialog.exec():
            stock_id = dialog.get_stock_id()
            if stock_id:
                print(f"StockListPanel: Requesting subscribe for {stock_id}")
                contract = None
                try:
                    if hasattr(self.main_engine, 'get_contract'):
                         contract = self.main_engine.get_contract(stock_id, "Shioaji")
                except Exception as e:
                    print(f"獲取合約物件時出錯: {e}")
                    contract = None

                if contract:
                    req = {"contract": contract, "quote_type": "Tick"}
                    try:
                        self.main_engine.subscribe(req, "Shioaji")
                        self.signal_status_message.emit(f"已發送訂閱請求: {stock_id}", 3000)
                        self._add_stock_to_table(stock_id, {"symbol": stock_id}) # 添加佔位行
                    except Exception as sub_e:
                         print(f"訂閱 {stock_id} 時發生錯誤: {sub_e}")
                         self.signal_status_message.emit(f"訂閱失敗: {stock_id} ({sub_e})", 5000)
                         QMessageBox.warning(self, "錯誤", f"訂閱股票/期貨 {stock_id} 失敗:\n{sub_e}")
                else:
                    self.signal_status_message.emit(f"訂閱失敗，找不到合約: {stock_id}", 3000)
                    QMessageBox.warning(self, "錯誤", f"無法找到股票/期貨合約: {stock_id}")

    @pyqtSlot()
    def _add_index(self):
        """訂閱大盤指數"""
        print("StockListPanel: Requesting subscribe for 大盤指數 (e.g., TXF)")
        # TODO: 實現訂閱大盤指數的邏輯，可能需要不同的合約類型
        self.signal_status_message.emit(f"訂閱大盤指數功能待實現", 3000)

    @pyqtSlot(QPoint)
    def show_stock_table_menu(self, position):
        """顯示右鍵選單"""
        menu = QMenu()
        selected_row = self.stock_table.currentRow()
        if selected_row >= 0:
            stock_id_item = self.stock_table.item(selected_row, 0)
            if stock_id_item:
                stock_id = stock_id_item.text()
                remove_stock_action = menu.addAction("取消訂閱")
                remove_stock_action.triggered.connect(lambda: self._unsubscribe_stock(stock_id))
                menu.exec(self.stock_table.viewport().mapToGlobal(position))

    def _unsubscribe_stock(self, stock_id):
        """取消訂閱股票行情"""
        print(f"StockListPanel: Requesting unsubscribe for {stock_id}")
        contract = None
        try:
            if hasattr(self.main_engine, 'get_contract'):
                contract = self.main_engine.get_contract(stock_id, "Shioaji")
        except Exception as e:
            print(f"獲取合約物件時出錯: {e}")

        if contract:
            req = {"contract": contract}
            try:
                self.main_engine.unsubscribe(req, "Shioaji")
                self.signal_status_message.emit(f"已發送取消訂閱請求: {stock_id}", 3000)
                # 從表格移除行
                for row in range(self.stock_table.rowCount()):
                     if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == stock_id:
                         self.stock_table.removeRow(row)
                         # 同時從緩存移除
                         if stock_id in self.stock_data_cache:
                             del self.stock_data_cache[stock_id]
                         break
            except Exception as unsub_e:
                print(f"取消訂閱 {stock_id} 時發生錯誤: {unsub_e}")
                self.signal_status_message.emit(f"取消訂閱失敗: {stock_id} ({unsub_e})", 5000)
