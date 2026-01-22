
import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QHBoxLayout, QTabWidget)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont
from datetime import datetime

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
ScreenerTab = None

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
    from jojo_trader.ui.screener_tab import ScreenerTab

    
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("JoJo Trader - Command Center")
        self.resize(450, 650)
        
        # 設定 Always on Top (讓它浮在最上層)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
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
        if ShioajiConnector:
            self.connector = ShioajiConnector()
            QTimer.singleShot(1000, self.auto_connect) # 延遲 1 秒自動連線

    def auto_connect(self):
        """嘗試自動連線到預設帳戶 (Async)"""
        if not self.connector: return
        
        # 1. Check if already connected
        if self.connector.is_connected:
            self.update_status_connected()
            return

        if not BrokerProfileManager: return
        
        try:
            from jojo_trading.core.stock_database import StockDatabase
            db = StockDatabase()
            active_profile_name = db.get_setting("active_profile")
            
            profiles = BrokerProfileManager.get_profiles()
            if not profiles:
                self.status_label.setText("🔴 No Profile")
                self.status_label.setStyleSheet("color: #ff4d4d;")
                return
            
            # Start Worker
            self.status_label.setText("⏳ Connecting...")
            self.status_label.setStyleSheet("color: #FFD700;") # Gold
            
            self.connect_worker = ConnectWorker(self.connector, profiles, active_profile_name)
            self.connect_worker.finished.connect(self.on_connect_finished)
            self.connect_worker.start()
            
        except Exception as e:
            print(f"Auto Connect Start Failed: {e}")
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
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 標題列
        header_layout = QHBoxLayout()
        title = QLabel("🚀 JoJo Trader")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_layout.addWidget(title)
        
        self.status_label = QLabel("⚪ Connecting...")
        self.status_label.setStyleSheet("color: #aaaaaa;")
        header_layout.addWidget(self.status_label, alignment=Qt.AlignRight)
        
        layout.addLayout(header_layout)
        
        # 使用 Tab Widget 分頁
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3d3d3d; top: -1px; }
            QTabBar::tab { background: #2d2d2d; color: #aaa; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #3d3d3d; color: white; border-bottom: 2px solid #2196F3; }
        """) # Slight style tweak for better look
        layout.addWidget(self.tabs)
        
        # --- Tab 0: Dashboard (Home) ---
        if DashboardTab:
            self.dashboard_tab = DashboardTab(self)
            self.tabs.addTab(self.dashboard_tab, "🏠 總覽 (Home)")

        # --- Tab 0.5: Analysis ---
        if AnalysisTab:
            self.analysis_tab = AnalysisTab(self)
            self.tabs.addTab(self.analysis_tab, "📊 分析 (Analysis)")

        # --- Tab 1: Watchlist ---
        if WatchlistTab:
            self.watchlist_tab = WatchlistTab(self)
            self.tabs.addTab(self.watchlist_tab, "👀 監控 (Watch)")
        else:
            self.tabs.addTab(QLabel("Modules Missing"), "Error")

        # --- Tab 1.5: Screener ---
        if ScreenerTab:
            self.screener_tab = ScreenerTab(self)
            self.tabs.addTab(self.screener_tab, "🔍 掃描 (Screener)")

        # --- Tab 2: Orders ---
        if OrdersTab:
            self.orders_tab = OrdersTab(self)
            self.tabs.addTab(self.orders_tab, "📝 委託 (Orders)")

        # --- Tab 3: Positions ---
        if PositionsTab:
            self.positions_tab = PositionsTab(self)
            self.tabs.addTab(self.positions_tab, "🎒 庫存 (Positions)")

        # --- Tab 4: Backtest ---
        if BacktestTab:
            self.backtest_tab = BacktestTab(self)
            self.tabs.addTab(self.backtest_tab, "🧪 回測 (Backtest)")



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
