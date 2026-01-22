
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QCheckBox, QGroupBox, 
                             QPushButton, QMessageBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt
try:
    from jojo_trading.core.stock_database import StockDatabase
except ImportError:
    StockDatabase = None

class GeneralSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = StockDatabase() if StockDatabase else None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # --- Appearance ---
        grp_appearance = QGroupBox("🎨 外觀與顯示 (Appearance)")
        grp_appearance.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #4CAF50; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_app = QVBoxLayout(grp_appearance)
        
        # Font Size
        row_font = QHBoxLayout()
        row_font.addWidget(QLabel("字體大小 (Font Size):"))
        self.combo_font = QComboBox()
        self.combo_font.addItems(["10 (Small)", "12 (Medium)", "14 (Large)", "16 (Extra Large)"])
        row_font.addWidget(self.combo_font)
        row_font.addStretch()
        layout_app.addLayout(row_font)
        
        # Theme
        row_theme = QHBoxLayout()
        row_theme.addWidget(QLabel("主題顏色 (Theme):"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Dark (預設)", "Light (開發中)"])
        row_theme.addWidget(self.combo_theme)
        row_theme.addStretch()
        layout_app.addLayout(row_theme)
        
        grp_appearance.setLayout(layout_app)
        layout.addWidget(grp_appearance)
        
        # --- Trading & Data ---
        grp_trading = QGroupBox("📈 交易與數據 (Trading & Data)")
        grp_trading.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #2196F3; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_trade = QVBoxLayout(grp_trading)
        
        # Default Qty
        row_qty = QHBoxLayout()
        row_qty.addWidget(QLabel("預設下單口數 (Default Qty):"))
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 100)
        row_qty.addWidget(self.spin_qty)
        row_qty.addStretch()
        layout_trade.addLayout(row_qty)
        
        # Update Rate
        row_rate = QHBoxLayout()
        row_rate.addWidget(QLabel("行情更新頻率 (Update Rate):"))
        self.combo_rate = QComboBox()
        self.combo_rate.addItems(["Realtime (不限制)", "Fast (0.5s)", "Normal (1.0s)", "Slow (2.0s)"])
        row_rate.addWidget(self.combo_rate)
        row_rate.addStretch()
        layout_trade.addLayout(row_rate)
        
        grp_trading.setLayout(layout_trade)
        layout.addWidget(grp_trading)
        
        # --- System & Notifications ---
        grp_sys = QGroupBox("🔔 系統通知 (System)")
        grp_sys.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #FF9800; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_sys = QVBoxLayout(grp_sys)
        
        self.chk_sound = QCheckBox("啟用成交音效 (Enable Trade Sound)")
        self.chk_autoconnect = QCheckBox("啟動時自動連線 (Auto Connect on Launch)")
        
        layout_sys.addWidget(self.chk_sound)
        layout_sys.addWidget(self.chk_autoconnect)
        
        grp_sys.setLayout(layout_sys)
        layout.addWidget(grp_sys)
        
        layout.addStretch()
        
        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 儲存設定 (Save Settings)")
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet("background-color: #4CAF50; font-weight: bold; font-size: 14px;")
        btn_save.clicked.connect(self.save_settings)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def load_settings(self):
        if not self.db: return
        
        # Font
        font_size = self.db.get_setting("font_size", "10")
        index = self.combo_font.findText(f"{font_size} ", Qt.MatchStartsWith)
        if index >= 0: self.combo_font.setCurrentIndex(index)
        
        # Theme
        theme = self.db.get_setting("theme", "Dark")
        index = self.combo_theme.findText(theme, Qt.MatchStartsWith)
        if index >= 0: self.combo_theme.setCurrentIndex(index)
        
        # Qty
        qty = self.db.get_setting("default_qty", "1")
        self.spin_qty.setValue(int(qty))
        
        # Rate
        rate = self.db.get_setting("update_rate", "Fast")
        index = self.combo_rate.findText(rate, Qt.MatchStartsWith)
        if index >= 0: self.combo_rate.setCurrentIndex(index)
        
        # Bools
        sound = self.db.get_setting("enable_sound", "True") == "True"
        self.chk_sound.setChecked(sound)
        
        auto = self.db.get_setting("auto_connect", "True") == "True"
        self.chk_autoconnect.setChecked(auto)

    def save_settings(self):
        if not self.db: return
        
        try:
            # Font: Extract number "10" from "10 (Small)"
            font_txt = self.combo_font.currentText()
            font_val = font_txt.split()[0]
            self.db.set_setting("font_size", font_val)
            
            # Theme
            theme_txt = self.combo_theme.currentText()
            theme_val = theme_txt.split()[0]
            self.db.set_setting("theme", theme_val)
            
            # Qty
            self.db.set_setting("default_qty", str(self.spin_qty.value()))
            
            # Rate
            rate_txt = self.combo_rate.currentText()
            rate_val = rate_txt.split()[0] # Store "Fast", "Realtime" etc. or maybe store full string
            # Let's store full string or first word. Store first word is cleaner for logic.
            # Actually, let's store the whole thing or a key?
            # Storing "Fast" is fine if we match it later.
            # But "Fast (0.5s)" is what we loaded.
            # Let's simple store what is loaded to match next time.
            # But for logic, "Fast" is better.
            # We implemented `findText(rate, MatchStartsWith)` so storing "Fast" works.
            self.db.set_setting("update_rate", rate_txt.split()[0]) 
            
            self.db.set_setting("enable_sound", str(self.chk_sound.isChecked()))
            self.db.set_setting("auto_connect", str(self.chk_autoconnect.isChecked()))
            
            QMessageBox.information(self, "Success", "設定已儲存！\n請重啟交易主程式以套用變更 (部分設定可能需重啟生效)。")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"儲存失敗: {e}")
