from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

# (保留原有 import 與 class 定義...)

class TradingWindow(QMainWindow):
    def __init__(self, main_engine, event_engine, parent=None):
        super().__init__(parent)
        self.main_engine = main_engine
        self.event_engine = event_engine
        # ...（其餘初始化內容請保留）...

    def _update_stock_table_row(self, row, data):
        """Helper to update a specific row in the stock table"""
        if not hasattr(self, 'stock_table'):
            return
        # Example: Update columns based on data keys
        col_map = {"symbol": 0, "name": 1, "last_price": 2, "change": 3, "volume": 4}  # Adjust column indices
        for key, col in col_map.items():
            value = data.get(key)
            item = self.stock_table.item(row, col)
            if not item:
                item = QTableWidgetItem()
                self.stock_table.setItem(row, col, item)

            if value is not None:
                # Format specific columns
                if key == "last_price":
                    item.setText(f"{value:.2f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif key == "change":  # Assuming 'change' contains percentage
                    try:
                        change_val = float(value)
                        item.setText(f"{change_val:+.2f}%")
                        item.setForeground(QColor('green') if change_val >= 0 else QColor('red'))
                    except (ValueError, TypeError):
                        item.setText(str(value))  # Fallback
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif key == "volume":
                    try:
                        item.setText(f"{int(value):,}")
                    except Exception:
                        item.setText(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setText(str(value))

    # ...（保留後續所有內容）...
