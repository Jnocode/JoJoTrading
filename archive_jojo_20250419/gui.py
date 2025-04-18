from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QListWidget, QListWidgetItem, QSplitter
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from widgets.market_data_panel import MarketDataPanel
from modules.left_value_zone_gui import LeftValueZoneGUI

# ...（保留原有 import 與 class 定義）...

class TradingWindow(QMainWindow):
    def __init__(self, main_engine, event_engine, parent=None):
        super().__init__(parent)
        self.main_engine = main_engine
        self.event_engine = event_engine

        # --- 新增：主視窗分割器與左側側邊欄 ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 左側側邊欄
        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_widget.setFixedWidth(180)
        self._init_app_sidebar()  # 初始化功能模組切換區

        # 右側主內容區（原本的主佈局）
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        # ...這裡可以把原本 main_layout 的內容都加到 self.content_layout...

        # 將側邊欄與主內容區加入主佈局
        self.main_layout.addWidget(self.sidebar_widget)
        self.main_layout.addWidget(self.content_widget)
        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 1)

        # ...（其餘初始化內容請保留）...

    def _init_app_sidebar(self):
        """初始化左側功能模組切換區塊"""
        self.sidebar_layout.addWidget(QLabel("功能模組"))
        self.app_list_widget = QListWidget()
        self.sidebar_layout.addWidget(self.app_list_widget)
        self.sidebar_layout.addStretch(1)

        # 自動列出所有已註冊 App
        self.refresh_app_sidebar()

        # 點擊切換 App
        self.app_list_widget.itemClicked.connect(self._on_app_item_clicked)

    def refresh_app_sidebar(self):
        """刷新側邊欄 App 清單"""
        self.app_list_widget.clear()
        for app_name in self.main_engine.apps.keys():
            item = QListWidgetItem(app_name)
            self.app_list_widget.addItem(item)

    def _on_app_item_clicked(self, item):
        """點擊 App 清單項目時啟用/停用 App，並顯示狀態或面板"""
        app_name = item.text()
        app = self.main_engine.get_app(app_name)
        # 先移除主內容區所有 widget
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # 根據 app_name 顯示對應面板
        if app_name == "MarketData":
            panel = MarketDataPanel(self.main_engine)
            self.content_layout.addWidget(panel)
        elif app_name == "LeftValueZone":
            panel = LeftValueZoneGUI(self.main_engine)
            self.content_layout.addWidget(panel)
        else:
            # 預設顯示狀態訊息
            if app:
                if hasattr(app, "_subscribed") and getattr(app, "_subscribed", False):
                    self.main_engine.stop_app(app_name)
                    self._show_app_status(f"{app_name} 已停止")
                else:
                    self.main_engine.start_app(app_name)
                    self._show_app_status(f"{app_name} 已啟動")
            else:
                self._show_app_status(f"找不到 App: {app_name}")

    def _show_app_status(self, msg):
        """在主內容區顯示 App 狀態訊息"""
        # 這裡簡單用 QLabel 顯示，可擴充為專屬面板
        label = QLabel(msg)
        self.content_layout.addWidget(label)

    # ...（保留原有 TradingWindow 其他方法與內容）...
