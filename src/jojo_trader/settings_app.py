
print("Initializing Settings App...")
import sys
import os
import traceback

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QLabel, QGroupBox, QFormLayout, QLineEdit, QPushButton, QMessageBox
    print("PySide6 imported.")
    from PySide6.QtGui import QIcon, QFont, QColor, QPalette
    from PySide6.QtCore import Qt
    from jojo_trading.core.stock_database import StockDatabase
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    from jojo_trader.ui.profile_dialog import ProfileManagerDialog
    from jojo_trader.ui.settings_tab import GeneralSettingsTab
    print("UI modules imported.")
except ImportError as e:
    print(f"MODULE IMPORT ERROR: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)

# Setup fonts for consistent look
font_path = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Roboto-Regular.ttf')

class ExternalDataTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = StockDatabase()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # FinMind Group
        group = QGroupBox("FinMind (台股歷史資料)")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; padding-top: 15px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        form = QFormLayout()
        
        self.user_edit = QLineEdit(self.db.get_setting("FINMIND_USER_ID", ""))
        self.pass_edit = QLineEdit(self.db.get_setting("FINMIND_PASSWORD", ""))
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.token_edit = QLineEdit(self.db.get_setting("FINMIND_API_TOKEN", ""))
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("Optional (Recommended)")
        
        form.addRow("User ID:", self.user_edit)
        form.addRow("Password:", self.pass_edit)
        form.addRow("API Token:", self.token_edit)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        # Save Button
        btn = QPushButton("儲存設定 (Save)")
        btn.clicked.connect(self.save_settings)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 4px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(btn)
        
        layout.addStretch()
        
    def save_settings(self):
        self.db.set_setting("FINMIND_USER_ID", self.user_edit.text())
        self.db.set_setting("FINMIND_PASSWORD", self.pass_edit.text())
        self.db.set_setting("FINMIND_API_TOKEN", self.token_edit.text())
        QMessageBox.information(self, "Success", "FinMind 設定已儲存！\nSettings saved successfully.")

class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JoJo Trader - System Settings")
        self.resize(1000, 700)
        
        # Apply Dark Theme
        self.setup_theme()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title Header
        title = QLabel("⚙️ 系統設定 (System Settings)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #aaa; padding: 10px 20px; }
            QTabBar::tab:selected { background: #4CAF50; color: white; border-radius: 4px; }
        """)
        
        # Tab 1: Broker Profiles
        self.profile_manager = ProfileManagerDialog()
        self.profile_manager.setWindowFlags(Qt.Widget) # Remove dialog flags to embed
        self.tabs.addTab(self.profile_manager, "券商帳號 (Broker Profiles)")
        
        # Tab 2: General Settings
        self.general_settings = GeneralSettingsTab()
        self.tabs.addTab(self.general_settings, "一般 (General)")

        # Tab 3: External Data (FinMind)
        self.external_tab = ExternalDataTab()
        self.tabs.addTab(self.external_tab, "外部資料 (External Data)")
        
        layout.addWidget(self.tabs)

    def setup_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

def main():
    app = QApplication(sys.argv)
    
    # Global Font Setup
    font = QFont("Microsoft JhengHei UI", 10)
    app.setFont(font)
    
    window = SettingsWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
