from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox
from PyQt6.QtCore import pyqtSlot
from typing import Optional

class MarketDataPanel(QGroupBox):
    """市場數據與期貨狀態面板"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("市場與期貨狀態", parent)
        self._init_ui()

    def _init_ui(self):
        """初始化 UI 元件"""
        layout = QVBoxLayout(self)

        # --- 市場狀態組 ---
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

        layout.addWidget(market_status_group)

        # --- 期貨數據組 ---
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

        layout.addWidget(futures_data_group)
        layout.addStretch()

    # --- 更新 UI 的方法 ---
    # 這些方法需要從主視窗接收數據來更新標籤

    @pyqtSlot(str)
    def update_trading_day(self, text: str):
        self.trading_day_label.setText(text)

    @pyqtSlot(str, str)
    def update_market_status(self, text: str, color: str):
        self.market_status_label.setText(text)
        self.market_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    @pyqtSlot(str, str)
    def update_connection_status(self, text: str, color: str):
        self.connection_status_label.setText(text)
        self.connection_status_label.setStyleSheet(f"color: {color};")

    @pyqtSlot(str)
    def update_last_update_time(self, text: str):
        self.last_update_label.setText(text)

    @pyqtSlot(str)
    def update_futures_price(self, text: str):
        self.futures_price_label.setText(text)

    @pyqtSlot(str)
    def update_futures_volume(self, text: str):
        self.futures_volume_label.setText(text)

    @pyqtSlot(str, str)
    def update_futures_change(self, text: str, style_sheet: str):
        self.futures_change_label.setText(text)
        self.futures_change_label.setStyleSheet(style_sheet)
