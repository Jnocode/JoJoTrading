
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QPushButton, QMessageBox, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QAction

import json
from datetime import datetime
from jojo_trading.core.stock_database import StockDatabase

try:
    from jojo_trader.ui.profile_dialog import ProfileManagerDialog
except ImportError:
    ProfileManagerDialog = None

class OrdersTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.setup_ui()
        # Initial Load (from cache if not connected yet)
        self.refresh_orders()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(5)
        self.order_table.setHorizontalHeaderLabels(["單號", "代號", "買賣", "價格", "狀態"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) # 自適應寬度
        self.order_table.verticalHeader().setVisible(False)
        
        # 啟用右鍵選單
        self.order_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.order_table.customContextMenuRequested.connect(self.show_order_menu)
        
        layout.addWidget(self.order_table)
        
        btn_layout = QHBoxLayout()
        
        btn_refresh = QPushButton("🔄 刷新委託")
        btn_refresh.setFixedHeight(30)
        btn_refresh.setStyleSheet("background-color: #5c6bc0;")
        btn_refresh.clicked.connect(self.refresh_orders)
        
        btn_check = QPushButton("🔍 檢查連線")
        btn_check.setFixedHeight(30)
        btn_check.setStyleSheet("background-color: #78909c;")
        btn_check.clicked.connect(self.check_connection_status)

        btn_manage = QPushButton("⚙️ 帳號管理")
        btn_manage.setFixedHeight(30)
        btn_manage.setStyleSheet("background-color: #f06292;")
        btn_manage.clicked.connect(self.open_profile_manager)
        
        btn_layout.addWidget(btn_refresh, 1)
        btn_layout.addWidget(btn_check, 1)
        btn_layout.addWidget(btn_manage, 1)
        
        layout.addLayout(btn_layout)

    def open_profile_manager(self):
        """Open Profile Dialog"""
        if not ProfileManagerDialog:
            QMessageBox.warning(self, "Error", "組件載入失敗")
            return
            
        dlg = ProfileManagerDialog(self)
        dlg.exec()

    def refresh_orders(self):
        """刷新委託單列表"""
        connector = getattr(self.main, 'connector', None)
        
        orders = []
        caching_success = False
        
        # 1. Try Fetch from API
        if connector and connector.is_connected:
            try:
                orders = connector.get_orders()
                # Save Cache
                try:
                    db = StockDatabase()
                    db.set_setting('orders_cache', json.dumps(orders))
                    db.set_setting('orders_ts', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    caching_success = True
                except Exception as e:
                    print(f"Order Cache Save Error: {e}")
            except Exception as e:
                print(f"Refresh Orders API Error: {e}")
        
        # 2. If no data (or disconnected), Try Load Cache
        if not orders and not caching_success:
            try:
                db = StockDatabase()
                cached = db.get_setting('orders_cache')
                if cached:
                    orders = json.loads(cached)
                    ts = db.get_setting('orders_ts')
                    print(f"Loaded Cached Orders from {ts}")
            except Exception as e:
                print(f"Order Cache Load Error: {e}")

        # 3. Update Table
        try:
            # Sort by ID desc
            orders.sort(key=lambda x: str(x.get('id', '')), reverse=True)
            
            self.order_table.setRowCount(0)
            for order in orders:
                row = self.order_table.rowCount()
                self.order_table.insertRow(row)
                
                # ["單號", "代號", "買賣", "價格", "狀態"]
                oid = str(order.get('id', 'Unknown'))
                display_id = oid[-5:] if len(oid) > 5 else oid
                
                id_item = QTableWidgetItem(display_id) 
                id_item.setData(Qt.UserRole, oid) # 數據用: 完整ID
                self.order_table.setItem(row, 0, id_item)
                
                self.order_table.setItem(row, 1, QTableWidgetItem(str(order.get('code', ''))))
                
                action = str(order.get('action', ''))
                action_item = QTableWidgetItem(action)
                if 'Buy' in action or 'B' == action:
                    action_item.setForeground(QBrush(QColor("#ff6b6b"))) # Pastel Red
                elif 'Sell' in action or 'S' == action:
                    action_item.setForeground(QBrush(QColor("#66bb6a"))) # Pastel Green
                self.order_table.setItem(row, 2, action_item)
                
                self.order_table.setItem(row, 3, QTableWidgetItem(str(order.get('price', 0))))
                self.order_table.setItem(row, 4, QTableWidgetItem(str(order.get('status', ''))))
                
        except Exception as e:
            print(f"Update Order Table Error: {e}")

    def check_connection_status(self):
        """跳出視窗顯示詳細連線資訊"""
        connector = getattr(self.main, 'connector', None)
        if not connector or not connector.is_connected:
            QMessageBox.warning(self, "未連線", "目前尚未連線到 API")
            return
            
        try:
            api = connector.api
            
            # 1. 檢查模式
            is_sim = getattr(api, 'simulation', False)
            mode_text = "⚠️ 模擬環境 (SIM)" if is_sim else "✅ 正式環境 (REAL)"
            
            # 2. 檢查帳號
            stock_acc = getattr(api, 'stock_account', None)
            acc_text = f"{stock_acc.person_id} ({stock_acc.broker_id}-{stock_acc.account_id})" if stock_acc else "無證券帳號"
            
            # 3. 檢查憑證
            cert_status = "已啟用" if stock_acc and stock_acc.signed else "未簽署 (只能看盤)"
            
            msg = (
                f"連線模式: {mode_text}\n"
                f"登入帳號: {acc_text}\n"
                f"憑證狀態: {cert_status}\n\n"
                "如果模式為 '模擬環境'，委託單將【不會】出現在您的券商 App。\n"
                "如果帳號與手機 App 不同，請檢查登入設定。"
            )
            
            QMessageBox.information(self, "連線診斷", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "診斷失敗", f"無法讀取狀態: {e}")

    def show_order_menu(self, position):
        """顯示委託單右鍵選單"""
        menu = QMenu()
        cancel_action = QAction("❌ 刪單 (Cancel Order)", self)
        menu.addAction(cancel_action)
        
        action = menu.exec(self.order_table.viewport().mapToGlobal(position))
        
        if action == cancel_action:
            rows = sorted(set(index.row() for index in self.order_table.selectedIndexes()))
            if not rows: return
            
            row = rows[0]
            stock = self.order_table.item(row, 1).text()
            full_id = self.order_table.item(row, 0).data(Qt.UserRole)
            
            if not full_id:
                QMessageBox.warning(self, "錯誤", "無法取得完整單號")
                return
                
            confirm = QMessageBox.question(self, "確認刪單", f"確定要刪除委託 {stock} (ID: {full_id}) 嗎?", 
                                         QMessageBox.Yes | QMessageBox.No)
            
            if confirm == QMessageBox.Yes:
                connector = getattr(self.main, 'connector', None)
                if not connector: return
                
                res = connector.cancel_order(full_id)
                if res['status'] == 'success':
                    QMessageBox.information(self, "成功", "刪單請求已送出")
                    self.refresh_orders()
                else:
                    QMessageBox.warning(self, "失敗", res['msg'])
