
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QCheckBox, QWidget, QSplitter, QFormLayout, QFileDialog, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QIcon, QFont
import requests

try:
    from jojo_trading.core.auth.broker_manager import BrokerProfileManager
except ImportError:
    BrokerProfileManager = None

class ProfileManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Broker Profile Manager (券商帳號管理)")
        self.resize(800, 550) # Increased height
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: white; }
            QLabel { color: white; }
            QLineEdit { background-color: #3d3d3d; color: white; padding: 5px; border: 1px solid #555; }
            QTableWidget { background-color: #2d2d2d; color: white; border: 1px solid #555; }
            QHeaderView::section { background-color: #3d3d3d; color: white; }
            QPushButton { background-color: #2196F3; color: white; padding: 6px; border-radius: 4px; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton#btn_del { background-color: #f44336; }
            QPushButton#btn_del:hover { background-color: #d32f2f; }
            QLabel#help_icon { color: #aaa; font-weight: bold; border: 1px solid #aaa; border-radius: 10px; padding: 0px 4px; }
            QLabel#help_icon:hover { color: white; border-color: white; background-color: #555; }
        """)
        
        self.current_profile_name = None
        self.setup_ui()
        self.load_profiles()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- Left: Profile List ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_list = QLabel("📋 設定檔列表")
        lbl_list.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(lbl_list)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["名稱", "模式"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemClicked.connect(self.on_profile_selected)
        left_layout.addWidget(self.table)
        
        btn_new = QPushButton("➕ 新增設定檔")
        btn_new.clicked.connect(self.new_profile)
        left_layout.addWidget(btn_new)

        # --- Import/Export Buttons ---
        io_layout = QHBoxLayout()
        btn_import_env = QPushButton("📥 Import .env")
        btn_import_env.setToolTip("從 .env 檔案匯入")
        btn_import_env.clicked.connect(self.import_from_env)
        
        btn_json_io = QPushButton("🔄 JSON I/O")
        btn_json_io.setToolTip("匯出/匯入 JSON 備份")
        btn_json_io.clicked.connect(self.json_io_menu)

        io_layout.addWidget(btn_import_env)
        io_layout.addWidget(btn_json_io)
        left_layout.addLayout(io_layout)
        
        # --- Right: Detail Form ---
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #2b2b2b; border-radius: 8px;")
        right_layout = QVBoxLayout(right_panel)
        
        lbl_detail = QLabel("✏️ 編輯詳細資訊")
        lbl_detail.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        right_layout.addWidget(lbl_detail)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.in_name = QLineEdit()
        self.in_api = QLineEdit()
        self.in_secret = QLineEdit()
        self.in_secret.setEchoMode(QLineEdit.EchoMode.Password) # Hide Secret Info
        self.in_person = QLineEdit()
        
        # Cert Path + Browse
        cert_widget = QWidget()
        cert_layout = QHBoxLayout(cert_widget)
        cert_layout.setContentsMargins(0,0,0,0)
        self.in_cert_path = QLineEdit()
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(30)
        btn_browse.clicked.connect(self.browse_cert)
        cert_layout.addWidget(self.in_cert_path)
        cert_layout.addWidget(btn_browse)
        
        self.in_cert_pass = QLineEdit()
        self.in_cert_pass.setEchoMode(QLineEdit.EchoMode.Password)
        
        # IP Address + Detect + Help
        ip_widget = QWidget()
        ip_layout = QHBoxLayout(ip_widget)
        ip_layout.setContentsMargins(0,0,0,0)
        
        self.in_ip = QLineEdit()
        self.in_ip.setPlaceholderText("例如: 61.220.x.x (留空則不限制)")
        
        btn_detect = QPushButton("偵測 (Detect)")
        btn_detect.setStyleSheet("background-color: #795548; padding: 4px;")
        btn_detect.setFixedWidth(80)
        btn_detect.clicked.connect(self.detect_ip)
        
        lbl_help = QLabel("?")
        lbl_help.setObjectName("help_icon")
        lbl_help.setFixedSize(20, 20)
        lbl_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_help.setToolTip("連線 IP 設定：\n\n部份券商 API 要求綁定固定 IP 白名單。\n若有需求，請在此輸入您申請的固定 IP。\n點擊「偵測」可自動填入目前對外 IP。")
        
        ip_layout.addWidget(self.in_ip)
        ip_layout.addWidget(btn_detect)
        ip_layout.addWidget(lbl_help)
        
        # VPN / PPPoE Settings
        vpn_widget = QWidget()
        vpn_layout = QHBoxLayout(vpn_widget)
        vpn_layout.setContentsMargins(0,0,0,0)
        
        self.in_vpn_user = QLineEdit()
        self.in_vpn_user.setPlaceholderText("寬頻連線帳號 (例如: 7xx@ip.hinet.net)")
        
        self.in_vpn_pass = QLineEdit()
        self.in_vpn_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_vpn_pass.setPlaceholderText("寬頻連線密碼")
        
        lbl_vpn_help = QLabel("?")
        lbl_vpn_help.setObjectName("help_icon")
        lbl_vpn_help.setFixedSize(20, 20)
        lbl_vpn_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_vpn_help.setToolTip("PPPoE / VPN 自動連線設定：\n\n若您的固定 IP 需要透過 PPPoE撥號 或 VPN取得，\n請在此填入連線帳密。\n當 IP 不符時，系統將嘗試透過此帳號自動重連。")
        
        vpn_layout.addWidget(self.in_vpn_user)
        vpn_layout.addWidget(lbl_vpn_help)

        self.chk_sim = QCheckBox("啟用模擬環境 (Simulation)")
        self.chk_sim.setStyleSheet("color: white;")
        
        self.chk_save_pass = QCheckBox("儲存憑證密碼 (不建議在公用電腦使用)")
        self.chk_save_pass.setStyleSheet("color: #ccc; font-size: 12px;")
        self.chk_save_pass.setChecked(True)

        form_layout.addRow("設定檔名稱:", self.in_name)
        form_layout.addRow("API Key:", self.in_api)
        form_layout.addRow("Secret Key:", self.in_secret)
        form_layout.addRow("身分證號 (ID):", self.in_person)
        form_layout.addRow("憑證路徑 (.pfx):", cert_widget)
        form_layout.addRow("憑證密碼:", self.in_cert_pass)
        form_layout.addRow("連線 IP:", ip_widget)
        form_layout.addRow("PPPoE 帳號:", vpn_widget)
        form_layout.addRow("PPPoE 密碼:", self.in_vpn_pass)
        form_layout.addRow("", self.chk_sim)
        form_layout.addRow("", self.chk_save_pass)
        
        right_layout.addLayout(form_layout)
        right_layout.addStretch()
        
        # Action Buttons
        action_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 儲存 (Save)")
        self.btn_save.clicked.connect(self.save_current)
        self.btn_save.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
        
        self.btn_active = QPushButton("⭐ 設為預設 (Set Default)")
        self.btn_active.clicked.connect(self.set_active_profile)
        self.btn_active.setStyleSheet("background-color: #FF9800; font-weight: bold; color: white;")
        self.btn_active.setEnabled(False)

        self.btn_del = QPushButton("❌ 刪除 (Delete)")
        self.btn_del.setObjectName("btn_del")
        self.btn_del.clicked.connect(self.delete_current)
        self.btn_del.setEnabled(False) # Enable only when selecting existing
        
        action_layout.addWidget(self.btn_del)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_active)
        action_layout.addWidget(self.btn_save)
        
        right_layout.addLayout(action_layout)
        
        # Add to main
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

    def set_active_profile(self):
        if not self.current_profile_name: return
        try:
            from jojo_trading.core.stock_database import StockDatabase
            db = StockDatabase()
            db.set_setting("active_profile", self.current_profile_name)
            QMessageBox.information(self, "Success", f"已將 [{self.current_profile_name}] 設為預設交易帳號")
            self.load_profiles()
            # Restore selection
            self.on_profile_selected_by_name(self.current_profile_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"設定失敗: {e}")

    def on_profile_selected_by_name(self, name):
        # Helper to re-select
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            data = item.data(Qt.UserRole)
            if data['profile_name'] == name:
                self.table.selectRow(i)
                self.on_profile_selected(item)
                break

    def detect_ip(self):
        """Fetch external IP"""
        try:
            self.in_ip.setText("偵測中...")
            QApplication.processEvents()
            
            # Use reliable IP echo service
            resp = requests.get('https://api.ipify.org', timeout=5)
            if resp.status_code == 200:
                ip = resp.text.strip()
                self.in_ip.setText(ip)
                QMessageBox.information(self, "IP 偵測與填入", f"偵測到您的對外 IP 為:\n{ip}")
            else:
                self.in_ip.clear()
                QMessageBox.warning(self, "失敗", "無法取得 IP")
        except Exception as e:
            self.in_ip.clear()
            QMessageBox.warning(self, "失敗", f"偵測失敗: {e}")

    def load_profiles(self):
        """Reload list from DB"""
        self.table.setRowCount(0)
        if not BrokerProfileManager: return
        
        try:
            # Get Active Profile
            from jojo_trading.core.stock_database import StockDatabase
            db = StockDatabase()
            active_profile = db.get_setting("active_profile")
            
            profiles = BrokerProfileManager.get_profiles()
            for p in profiles:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                name = p['profile_name']
                is_sim = p.get('is_simulation', False)
                is_active = (name == active_profile)
                
                # Name Column
                display_name = f"⭐ {name}" if is_active else name
                item_name = QTableWidgetItem(display_name)
                item_name.setData(Qt.UserRole, p) # Store full data
                if is_active:
                    item_name.setForeground(QBrush(QColor("#FFD700"))) # Gold
                    item_name.setFont(QFont("Arial", 10, QFont.Bold))
                self.table.setItem(row, 0, item_name)
                
                # Mode Column
                item_mode = QTableWidgetItem("SIM" if is_sim else "REAL")
                if is_sim:
                    item_mode.setForeground(QBrush(QColor("#ff9800")))
                else:
                    item_mode.setForeground(QBrush(QColor("#4CAF50")))
                self.table.setItem(row, 1, item_mode)
                
            self.new_profile() # Reset form
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load Failed: {e}")

    def on_profile_selected(self, item):
        row = item.row()
        name_item = self.table.item(row, 0)
        data = name_item.data(Qt.UserRole)
        
        self.current_profile_name = data['profile_name']
        
        # Decrypt for editing
        full = BrokerProfileManager.get_decrypted_profile(self.current_profile_name)
        if full:
            self.in_name.setText(full['profile_name'])
            self.in_name.setReadOnly(True) # PK cannot change name directly
            
            self.in_api.setText(full['api_key'])
            self.in_secret.setText(full['secret_key'])
            self.in_person.setText(full['person_id'])
            self.in_cert_path.setText(full['cert_path'])
            self.in_cert_pass.setText(full['cert_pass'])
            self.in_ip.setText(full.get('allowed_ip', ''))
            self.in_vpn_user.setText(full.get('vpn_user', ''))
            self.in_vpn_pass.setText(full.get('vpn_pass', ''))
            self.chk_sim.setChecked(bool(full['is_simulation']))
            
            self.btn_del.setEnabled(True)
            self.btn_active.setEnabled(True)

    def new_profile(self):
        self.current_profile_name = None
        self.table.clearSelection()
        
        self.in_name.clear()
        self.in_name.setReadOnly(False)
        self.in_api.clear()
        self.in_secret.clear()
        self.in_person.clear()
        self.in_cert_path.clear()
        self.in_cert_pass.clear()
        self.in_ip.clear()
        self.in_vpn_user.clear()
        self.in_vpn_pass.clear()
        self.chk_sim.setChecked(False)
        
        self.btn_del.setEnabled(False)
        self.in_name.setFocus()

    def browse_cert(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select Certificate", "", "PFX Files (*.pfx)")
        if fname:
            self.in_cert_path.setText(fname)

    def save_current(self):
        name = self.in_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "名稱不能為空")
            return
            
        if not BrokerProfileManager: return
        
        # Save
        try:
            BrokerProfileManager.save_profile(
                name=name,
                api_key=self.in_api.text().strip(),
                secret_key=self.in_secret.text().strip(),
                person_id=self.in_person.text().strip(),
                cert_path=self.in_cert_path.text().strip(),
                cert_pass=self.in_cert_pass.text(),
                is_sim=self.chk_sim.isChecked(),
                save_cert_pass=self.chk_save_pass.isChecked(),
                allowed_ip=self.in_ip.text().strip(),
                vpn_user=self.in_vpn_user.text().strip(),
                vpn_pass=self.in_vpn_pass.text()
            )
            QMessageBox.information(self, "Success", "設定檔已儲存")
            self.load_profiles()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"儲存失敗: {e}")

    def delete_current(self):
        if not self.current_profile_name: return
        
        confirm = QMessageBox.question(self, "Delete", f"確定刪除 {self.current_profile_name}?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes and BrokerProfileManager:
            BrokerProfileManager.delete_profile(self.current_profile_name)
            self.load_profiles()

    def import_from_env(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select .env File", "", "Env Files (*.env);;All Files (*)")
        if fname and BrokerProfileManager:
            success, msg = BrokerProfileManager.import_from_env(fname)
            if success:
                QMessageBox.information(self, "Import", msg)
                self.load_profiles()
            else:
                QMessageBox.warning(self, "Import Failed", msg)

    def json_io_menu(self):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        act_export = menu.addAction("📤 匯出到 JSON (Export)")
        act_import = menu.addAction("📥 從 JSON 匯入 (Import)")
        
        action = menu.exec(self.cursor().pos())
        
        if action == act_export:
            self.export_json()
        elif action == act_import:
            self.import_json()

    def export_json(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export Profiles", "profiles_backup.json", "JSON Files (*.json)")
        if fname and BrokerProfileManager:
            success, msg = BrokerProfileManager.export_to_json(fname)
            if success:
                QMessageBox.information(self, "Export", msg)
            else:
                QMessageBox.warning(self, "Export Failed", msg)

    def import_json(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Import Profiles", "", "JSON Files (*.json)")
        if fname and BrokerProfileManager:
            success, msg = BrokerProfileManager.import_from_json(fname)
            if success:
                QMessageBox.information(self, "Import", msg)
                self.load_profiles()
            else:
                QMessageBox.warning(self, "Import Failed", msg)
