from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
from PyQt6.QtCore import QTimer, Qt

class MarketDataPanel(QWidget):
    def __init__(self, main_engine, parent=None):
        super().__init__(parent)
        self.main_engine = main_engine
        self.layout = QVBoxLayout(self)
        self.label = QLabel("即時行情報價")
        self.layout.addWidget(self.label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["商品", "最新價", "漲跌", "成交量"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)

        # 定時刷新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_table)
        self.timer.start(1000)  # 每秒刷新

    def refresh_table(self):
        # 從 MarketDataApp 取得行情資料
        app = self.main_engine.get_app("MarketData")
        if not app:
            return
        ticks = app.ticks if hasattr(app, "ticks") else {}

        self.table.setRowCount(len(ticks))
        for row, (symbol, tick) in enumerate(ticks.items()):
            price = tick.get("last_price", "")
            change = tick.get("change", "")
            volume = tick.get("volume", "")

            self.table.setItem(row, 0, QTableWidgetItem(str(symbol)))
            self.table.setItem(row, 1, QTableWidgetItem(str(price)))
            self.table.setItem(row, 2, QTableWidgetItem(str(change)))
            self.table.setItem(row, 3, QTableWidgetItem(str(volume)))
