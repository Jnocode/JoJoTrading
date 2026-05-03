
import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QHBoxLayout, QTabWidget, QScrollArea, QDockWidget)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QScreen
from PySide6.QtGui import QFont
from datetime import datetime
from dotenv import load_dotenv

# Load Env Vars (API Keys)
load_dotenv()

# 添加專案根目錄到 path 以便導入 core 模組
# 添加專案 src 目錄到 path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir) 
sys.path.append(src_dir)

print(f"Debug: Added {src_dir} to sys.path") # Debug info

# Initialize modules as None
ShioajiConnector = None
BrokerProfileManager = None
DashboardTab = None
WatchlistTab = None
OrdersTab = None
PositionsTab = None
BacktestTab = None
AnalysisTab = None
AnalysisTab = None
ScreenerTab = None
NewsTab = None

try:
    from jojo_trading.core.shioaji_connector import ShioajiConnector
    from jojo_trading.core.auth.broker_manager import BrokerProfileManager
    
    # Import Modular Tabs
    from jojo_trader.ui.dashboard_tab import DashboardTab
    from jojo_trader.ui.watchlist_tab import WatchlistTab
    from jojo_trader.ui.orders_tab import OrdersTab
    from jojo_trader.ui.positions_tab import PositionsTab
    from jojo_trader.ui.backtest_tab import BacktestTab
    from jojo_trader.ui.analysis_tab import AnalysisTab
    from jojo_trader.ui.analysis_tab import AnalysisTab
    from jojo_trader.ui.screener_tab import ScreenerTab
    from jojo_trader.ui.news_tab import NewsTab

    
except Exception as e:
    # Critical Debug: Show error in windowed mode
    app = QApplication.instance() or QApplication(sys.argv)
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.critical(None, "Startup Error", f"Failed to import modules:\n{str(e)}")

    print(f"Import Error: {e}")
    sys.exit(1)





class ConnectWorker(QThread):
    finished = Signal(bool, str, str) # success, profile_name, error_msg

    def __init__(self, connector, profiles, active_profile_name):
        super().__init__()
        self.connector = connector
        self.profiles = profiles
        self.active_profile_name = active_profile_name

    def run(self):
        try:
            # Decide which profile to use
            target_profile = self.profiles[0] # Default Fallback
            if self.active_profile_name:
                for p in self.profiles:
                    if p['profile_name'] == self.active_profile_name:
                        target_profile = p
                        break
            
            name = target_profile['profile_name']
            
            # Decrypt (Expensive operation potentially)
            if BrokerProfileManager:
                full_prof = BrokerProfileManager.get_decrypted_profile(name)
                if full_prof:
                    # Connect (Blocking network call)
                    self.connector.connect(
                        api_key=full_prof['api_key'],
                        secret_key=full_prof['secret_key'],
                        cert_path=full_prof['cert_path'],
                        cert_pass=full_prof['cert_pass'],
                        person_id=full_prof['person_id'],
                        is_simulation=full_prof['is_simulation'],
                        allowed_ip=full_prof.get('allowed_ip'),
                        vpn_user=full_prof.get('vpn_user'),
                        vpn_pass=full_prof.get('vpn_pass')
                    )
                    
                    if self.connector.is_connected:
                        self.finished.emit(True, name, "")
                    else:
                        err = self.connector.last_error if hasattr(self.connector, 'last_error') else "Unknown Error"
                        self.finished.emit(False, name, err)
                else:
                    self.finished.emit(False, name, "Failed to decrypt profile")
            else:
                 self.finished.emit(False, "?", "BrokerProfileManager missing")
                 
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, "Error", str(e))


class ResponsiveTabWidget(QTabWidget):
    def minimumSizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(10, 10) # 允許無限縮小，無視子元件建議大小

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("JoJo Trader - Command Center")
        self.setMinimumSize(1, 1)
        
        # 根據螢幕大小自適應初始尺寸 (85% 螢幕寬高)
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            w = int(screen_geo.width() * 0.85)
            h = int(screen_geo.height() * 0.85)
            self.resize(w, h)
            # 置中顯示
            x = screen_geo.x() + (screen_geo.width() - w) // 2
            y = screen_geo.y() + (screen_geo.height() - h) // 2
            self.move(x, y)
        else:
            self.resize(1280, 800)
        
        # 主樣式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: white;
                gridline-color: #3d3d3d;
                border: none;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: white;
                padding: 4px;
                border: none;
            }
            QTabWidget::pane { /* The tab widget frame */
                border-top: 2px solid #C2C7CB;
            }
            QTabWidget::tab-bar {
                left: 5px; /* move to the right by 5px */
            }
            QTabBar::tab {
                background: #3d3d3d;
                color: #C2C7CB;
                border: 1px solid #C4C4C3;
                border-bottom-color: #C2C7CB;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: #1976D2;
                color: white;
            }
        """)
        
        self.setup_ui()
        
        # 初始化 Connector
        self.connector = None
        self.bridge = None 
        
        # Init Bridge (Global)
        try:
            from jojo_trader.ui.signal_bridge import ShioajiSignalBridge
            self.bridge = ShioajiSignalBridge()
        except ImportError:
            print("⚠️ Signal Bridge Import Failed")

        if ShioajiConnector:
            self.connector = ShioajiConnector()
            if self.bridge:
                self.connector.set_bridge(self.bridge)
            
            QTimer.singleShot(1000, self.auto_connect) # 延遲 1 秒自動連線

    def auto_connect(self):
        """嘗試自動連線到預設帳戶 (Async)"""
        if not self.connector: return
        
        # 1. Check if already connected
        if self.connector.is_connected:
            self.update_status_connected()
            return

        if not BrokerProfileManager: 
            print("AutoConnect Aborted: BrokerProfileManager not loaded.")
            return
        
        try:
            from jojo_trading.core.stock_database import StockDatabase
            db = StockDatabase()
            
            # Check System Setting first
            if db.get_setting("auto_connect", "True") != "True":
                self.status_label.setText("⚪ Auto-Connect Disabled")
                return

            active_profile_name = db.get_setting("active_profile")
            
            profiles = BrokerProfileManager.get_profiles()
            if not profiles:
                self.status_label.setText("🔴 No Profile")
                self.status_label.setStyleSheet("color: #ff4d4d;")
                return
            
            # Smart Default: If no active profile set, but only 1 profile exists, use it.
            if not active_profile_name and len(profiles) == 1:
                active_profile_name = profiles[0]['profile_name']
                print(f"AutoConnect: Defaulting to single profile '{active_profile_name}'")
            
            if not active_profile_name:
                self.status_label.setText("⚪ Select Profile")
                return

            # Start Worker
            self.status_label.setText(f"⏳ Connecting ({active_profile_name})...")
            self.status_label.setStyleSheet("color: #FFD700;") # Gold
            
            self.connect_worker = ConnectWorker(self.connector, profiles, active_profile_name)
            self.connect_worker.finished.connect(self.on_connect_finished)
            self.connect_worker.start()
            
        except Exception as e:
            print(f"Auto Connect Start Failed: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText("🔴 Connect Error")

    def on_connect_finished(self, success, name, error_msg):
        if success:
            self.status_label.setText(f"🟢 Connected ({name})")
            self.status_label.setStyleSheet("color: #4CAF50;")
            self.update_status_connected() # Update UI specifics
        else:
            self.status_label.setText(f"🔴 Connect Fail ({name})")
            self.status_label.setToolTip(f"Error: {error_msg}")
            
            # Log error
            try:
                with open("debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now()}] ConnectWorker Failed: {error_msg}\n")
            except: pass

    def update_status_connected(self):
        is_sim = getattr(self.connector.api, 'simulation', False)
        mode_str = "SIM" if is_sim else "REAL"
        color = "#f44336" if is_sim else "#4CAF50"
        self.status_label.setText(f"🟢 Connected ({mode_str})")
        style = f"color: {color}; font-weight: bold;"
        self.status_label.setStyleSheet(style)

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setMinimumSize(1, 1)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSizeConstraint(QVBoxLayout.SetNoConstraint)
        
        # 標題列
        header_layout = QHBoxLayout()
        title = QLabel("🚀 JoJo Trader")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(title)
        
        # 加入 Pop Out 按鈕到標題列
        from PySide6.QtWidgets import QPushButton
        from PySide6.QtGui import QCursor
        self.btn_pop_out = QPushButton("↗ 獨立視窗 (Pop Out)")
        self.btn_pop_out.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                color: #2196F3; 
                font-weight: bold; 
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 4px 12px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #2196F3;
                color: white;
            }
        """)
        self.btn_pop_out.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_pop_out.clicked.connect(self.pop_out_current_tab)
        header_layout.addWidget(self.btn_pop_out)
        
        # Spacer to push status label to the right
        header_layout.addStretch()
        
        self.status_label = QLabel("⚪ Connecting...")
        self.status_label.setStyleSheet("color: #aaaaaa;")
        header_layout.addWidget(self.status_label, alignment=Qt.AlignRight)
        
        layout.addLayout(header_layout)
        
        # 使用 Tab Widget 分頁 (可捲動，窄視窗自適應)
        self.tabs = ResponsiveTabWidget()
        self.tabs.setMinimumSize(1, 1)
        self.tabs.setTabBarAutoHide(False)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3d3d3d; top: -1px; }
            QTabBar::tab { background: #2d2d2d; color: #aaa; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #3d3d3d; color: white; border-bottom: 2px solid #2196F3; }
        """) # Slight style tweak for better look
        
        layout.addWidget(self.tabs)
        
        # Helper for wrapping tabs in scroll area to allow extreme shrinking
        def wrap_in_scroll(widget, order_id):
            scroll = QScrollArea()
            scroll.setMinimumSize(1, 1)
            scroll.setWidgetResizable(True)
            scroll.setWidget(widget)
            scroll.setFrameShape(QScrollArea.NoFrame)
            scroll._original_order = order_id
            return scroll
            
        # --- Tab 0: Dashboard (Home) ---
        if DashboardTab:
            self.dashboard_tab = DashboardTab(self)
            self.tabs.addTab(wrap_in_scroll(self.dashboard_tab, 0), "🏠 總覽 (Home)")

        # --- Tab 0.2: News (NEW) ---
        if NewsTab:
            self.news_tab = NewsTab(self)
            self.tabs.addTab(wrap_in_scroll(self.news_tab, 1), "📰 新聞 (News)")

        # --- Tab 0.5: Analysis ---
        if AnalysisTab:
            self.analysis_tab = AnalysisTab(self)
            self.tabs.addTab(wrap_in_scroll(self.analysis_tab, 2), "📊 分析 (Analysis)")

        # --- Tab 1: Watchlist ---
        if WatchlistTab:
            self.watchlist_tab = WatchlistTab(self)
            self.tabs.addTab(wrap_in_scroll(self.watchlist_tab, 3), "👀 監控 (Watch)")
        else:
            err_lbl = QLabel("Modules Missing")
            err_lbl._original_order = 3
            self.tabs.addTab(err_lbl, "Error")

        # --- Tab 1.5: Screener ---
        if ScreenerTab:
            self.screener_tab = ScreenerTab(self)
            self.tabs.addTab(wrap_in_scroll(self.screener_tab, 4), "🔍 掃描 (Screener)")

        # --- Tab 2: Orders ---
        if OrdersTab:
            self.orders_tab = OrdersTab(self)
            self.tabs.addTab(wrap_in_scroll(self.orders_tab, 5), "📝 委託 (Orders)")

        # --- Tab 3: Positions ---
        if PositionsTab:
            self.positions_tab = PositionsTab(self)
            self.tabs.addTab(wrap_in_scroll(self.positions_tab, 6), "🎒 庫存 (Positions)")

        # --- Tab 4: Backtest ---
        if BacktestTab:
            self.backtest_tab = BacktestTab(self)
            self.tabs.addTab(wrap_in_scroll(self.backtest_tab, 7), "🧪 回測 (Backtest)")

    def pop_out_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx < 0: return
        widget = self.tabs.widget(idx)
        title = self.tabs.tabText(idx)
        
        # Don't pop out if it's the only tab left
        if self.tabs.count() <= 1:
            return
            
        self.tabs.removeTab(idx)
        
        # Ensure widget is visible after removing from tab widget
        widget.show()
        
        from PySide6.QtWidgets import QMainWindow
        from PySide6.QtCore import Qt
        
        # Create detached window
        detached = QMainWindow(self)
        detached.setWindowTitle(f"{title} - 獨立視窗")
        detached.setCentralWidget(widget)
        detached.resize(800, 600)
        # Don't delete on close so we can put it back
        detached.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # Keep a Python reference so it doesn't get garbage collected
        if not hasattr(self, 'detached_windows'):
            self.detached_windows = []
        self.detached_windows.append(detached)
        
        # Handle close event to put it back
        def closeEvent(event):
            # Find the correct index based on _original_order
            insert_idx = 0
            if hasattr(widget, '_original_order'):
                for i in range(self.tabs.count()):
                    w = self.tabs.widget(i)
                    if hasattr(w, '_original_order') and w._original_order > widget._original_order:
                        break
                    insert_idx += 1
            else:
                insert_idx = self.tabs.count()
                
            # Put it back to tabs
            self.tabs.insertTab(insert_idx, widget, title)
            # Re-select it
            self.tabs.setCurrentWidget(widget)
            
            if detached in self.detached_windows:
                self.detached_windows.remove(detached)
                
            event.accept()
            # Defer deletion
            detached.deleteLater()
            
        detached.closeEvent = closeEvent
        detached.show()


    def switch_to_orders_tab(self):
        """Helper to switch to orders tab (index 2)"""
        # Orders Tab index depends on if Dashboard exists
        idx = 2 if DashboardTab else 1
        self.tabs.setCurrentIndex(idx)
        # 並觸發刷新
        if hasattr(self, 'orders_tab'):
            self.orders_tab.refresh_orders()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
