
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QPushButton, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QBrush, QFont

import json
from datetime import datetime
from jojo_trading.core.stock_database import StockDatabase

# Import core
try:
    from jojo_trading.core.yfinance_fetcher import YFinanceFetcher
except ImportError:
    YFinanceFetcher = None

class PositionWorker(QThread):
    """後台線程：更新庫存與損益"""
    data_updated = Signal(list) # [{code, qty, cost, price, pnl, pnl_pct}, ...]

    def __init__(self, main_window):
        super().__init__()
        self.main = main_window

    def run(self):
        while True:
            try:
                connector = getattr(self.main, 'connector', None)
                if not connector or not connector.is_connected:
                    self.sleep(2)
                    continue

                # 1. Get Positions
                positions = connector.get_positions() # [{'code': '2330', 'qty': 1000, 'cost': 500}, ...]
                
                updates = []
                for pos in positions:
                    code = pos['code']
                    qty = pos['qty']
                    cost = pos['cost']
                    broker_pnl = pos.get('pnl', 0.0)
                    broker_price = pos.get('last_price', 0.0)
                    
                    # 2. Get Real-time Price
                    current_price = broker_price
                    
                    # If broker didn't give price (e.g. some APIs), fallback to YFinance
                    if current_price <= 0 and YFinanceFetcher:
                        candidates = [code, f"{code}.TW", f"{code}.TWO"]
                        for c in candidates:
                            p = YFinanceFetcher.get_stock_price(c)
                            if p and p > 0:
                                current_price = p
                                break
                    
                    # Final Fallback
                    current_price = current_price if current_price > 0 else cost
                    
                    # 3. Calculate P&L
                    unrealized_pnl = broker_pnl
                    
                    # Calculate %
                    # Using Cost Value = Cost * Qty
                    cost_val = cost * qty
                    pnl_pct = 0.0
                    if cost_val != 0:
                        pnl_pct = (unrealized_pnl / cost_val) * 100
                    
                    updates.append({
                        'code': code,
                        'qty': qty,
                        'cost': cost,
                        'price': current_price,
                        'pnl': unrealized_pnl,
                        'pnl_pct': pnl_pct
                    })
                
                self.data_updated.emit(updates)
                
                # Save Cache (Create DB instance inside thread for safety)
                try:
                    db = StockDatabase()
                    db.set_setting('positions_cache', json.dumps(updates))
                    db.set_setting('positions_ts', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                except Exception as db_e:
                    print(f"Cache Save Error: {db_e}")

            except Exception as e:
                # print(f"Position Worker Error: {e}")
                pass
            
            self.sleep(5)

class PositionsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.setup_ui()
        
        # 啟動 Worker
        self.worker = PositionWorker(main_window)
        self.worker.data_updated.connect(self.update_positions_ui)
        
        # Try Load Cache (Init)
        try:
            db = StockDatabase()
            cached = db.get_setting('positions_cache')
            if cached:
                data = json.loads(cached)
                ts = db.get_setting('positions_ts')
                self.update_positions_ui(data)
                current_text = self.lbl_total_pnl.text()
                self.lbl_total_pnl.setText(f"{current_text} (Cached: {ts})")
        except Exception as e:
            print(f"Cache Load Error: {e}")
            
        self.worker.start()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 總損益概覽
        self.lbl_total_pnl = QLabel("總損益: $0")
        self.lbl_total_pnl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_total_pnl.setStyleSheet("background-color: #2d2d2d; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.lbl_total_pnl)
        
        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(7)
        self.pos_table.setHorizontalHeaderLabels(["代號", "股數", "成本", "現價", "損益", "報酬率", "操作"])
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.pos_table.verticalHeader().setVisible(False)
        layout.addWidget(self.pos_table)

    def update_positions_ui(self, data):
        """更新庫存表格"""
        try:
            # Sort by P&L (Loss first? or Profit first? Let's sort by Code for stability)
            # Or P&L descending
            data.sort(key=lambda x: x['pnl'], reverse=True)
            
            self.pos_table.setRowCount(0)
            
            total_pnl = 0.0
            
            for item in data:
                row = self.pos_table.rowCount()
                self.pos_table.insertRow(row)
                
                # ["代號", "股數", "成本", "現價", "損益", "報酬率"]
                self.pos_table.setItem(row, 0, QTableWidgetItem(str(item['code'])))
                
                qty_item = QTableWidgetItem(f"{item['qty']:,}")
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.pos_table.setItem(row, 1, qty_item)
                
                cost_item = QTableWidgetItem(f"{item['cost']:.2f}")
                cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.pos_table.setItem(row, 2, cost_item)
                
                price_item = QTableWidgetItem(f"{item['price']:.2f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.pos_table.setItem(row, 3, price_item)
                
                # P&L Color
                pnl = item['pnl']
                total_pnl += pnl
                
                pnl_item = QTableWidgetItem(f"{pnl:+.2f}")
                if pnl > 0:
                    pnl_item.setForeground(QBrush(QColor("#ff6b6b")))
                elif pnl < 0:
                    pnl_item.setForeground(QBrush(QColor("#66bb6a")))
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.pos_table.setItem(row, 4, pnl_item)
                
                # % Color
                pct = item['pnl_pct']
                pct_item = QTableWidgetItem(f"{pct:+.2f}%")
                if pct > 0:
                    pct_item.setForeground(QBrush(QColor("#ff6b6b")))
                elif pct < 0:
                    pct_item.setForeground(QBrush(QColor("#66bb6a")))
                pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.pos_table.setItem(row, 5, pct_item)
                
                # Close Button
                btn_close = QPushButton("⚡ 平倉")
                btn_close.setStyleSheet("background-color: #F44336; color: white; border-radius: 4px; padding: 2px;")
                btn_close.clicked.connect(lambda checked, c=item['code'], q=item['qty']: self.close_position(c, q))
                self.pos_table.setCellWidget(row, 6, btn_close)
            
            # Update Total Label
            color = "#ff4d4d" if total_pnl > 0 else "#00cc00" if total_pnl < 0 else "white"
            self.lbl_total_pnl.setText(f"總未實現損益: ${total_pnl:,.2f}")
            self.lbl_total_pnl.setStyleSheet(f"background-color: #2d2d2d; padding: 10px; border-radius: 5px; color: {color};")
                
        except Exception as e:
            print(f"Pos Update Error: {e}")

    def close_position(self, code, qty):
        """快速平倉"""
        reply = QMessageBox.question(self, "平倉確認", f"確定要平倉 {code} ({qty}股) 嗎?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return
        
        connector = getattr(self.main, 'connector', None)
        if not connector or not connector.is_connected:
            QMessageBox.warning(self, "錯誤", "未連線")
            return
            
        # Determine Sell Quantity (handle negative qty for short positions if applicable, but usually absolute here)
        action = "Sell" if qty > 0 else "Buy" # If long, sell. If short, buy cover.
        abs_qty = abs(qty)
        
        # Place Market Order (ROD or maybe IOC/FOK? Default ROD Limit is safer, but "Quick Close" usually implies Market/Better Price)
        # For safety, let's assume Limit Price = Current Market Price (approx) or let user input?
        # User requested "Quick Close", usually means "Get me out".
        # Since we don't have real-time quote reliably here to peg limit price, 
        # let's pop a dialog for price or assume a safe limit?
        # Actually, let's open the Quick Order Dialog from Watchlist? No, logical separation.
        # Let's use a simple input dialog for Price.
        
        price_str, ok = QInputDialog.getText(self, "平倉價格", f"請輸入 {code} 平倉價格:", text="")
        if not ok or not price_str: return
        
        try:
            price = float(price_str)
        except:
            QMessageBox.warning(self, "錯誤", "價格格式錯誤")
            return
            
        try:
            res = connector.place_order(
                stock_code=code,
                action=action,
                quantity=abs_qty,
                price=price,
                price_type="LMT",
                order_type="ROD"
            )
            if res['status'] == 'success':
                QMessageBox.information(self, "成功", f"平倉委託已送出: {res['order_id']}")
            else:
                 QMessageBox.warning(self, "失敗", f"API 錯誤: {res['msg']}")
        except Exception as e:
             QMessageBox.critical(self, "錯誤", str(e))
