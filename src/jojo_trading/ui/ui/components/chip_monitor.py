from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QSpinBox, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Slot
import datetime

class ChipMonitorWidget(QWidget):
    """
    Real-time Chip Monitor Logic:
    - Filters ticks based on volume threshold (Big Orders)
    - Classifies as Buy/Sell based on tick price vs bid/ask logic (approximate)
    - Updates UI table and summary stats
    """
    
    def __init__(self, bridge=None):
        super().__init__()
        self.bridge = bridge
        self.code = None
        
        # Data
        self.big_buy_vol = 0
        self.big_sell_vol = 0
        
        self.total_processed = 0
        
        self.setup_ui()
        
        if self.bridge:
            self.bridge.tick_received.connect(self.on_tick)
            
    def set_bridge(self, bridge):
        if self.bridge:
            try:
                self.bridge.tick_received.disconnect(self.on_tick)
            except: pass
            
        self.bridge = bridge
        if self.bridge:
            self.bridge.tick_received.connect(self.on_tick)
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 1. Control Bar
        control_layout = QHBoxLayout()
        
        lbl_thresh = QLabel("大單門檻 (Threshold):")
        lbl_thresh.setStyleSheet("color: #DDD;")
        control_layout.addWidget(lbl_thresh)
        
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(1, 499)
        self.spin_threshold.setValue(20) # Default 20 lots
        self.spin_threshold.setSuffix(" 張")
        self.spin_threshold.setStyleSheet("background: #333; color: white; padding: 3px;")
        control_layout.addWidget(self.spin_threshold)
        
        # Reset Button
        btn_reset = QPushButton("重置 (Reset)")
        btn_reset.setStyleSheet("background: #444; color: white; border: none; padding: 4px 8px;")
        btn_reset.clicked.connect(self.reset_stats_only)
        control_layout.addWidget(btn_reset)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Summary Labels (Horizontal)
        summary_layout = QHBoxLayout()
        
        self.lbl_buy = QLabel("🔴 大戶買盤: 0")
        self.lbl_buy.setStyleSheet("color: #FF4444; font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.lbl_buy)
        
        self.lbl_sell = QLabel("🟢 大戶賣盤: 0")
        self.lbl_sell.setStyleSheet("color: #44FF44; font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.lbl_sell)
        
        self.lbl_net = QLabel("淨流向: 0")
        self.lbl_net.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.lbl_net)
        
        layout.addLayout(summary_layout)
        
        # 2. Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["時間", "價格", "單量", "性質"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1E1E1E; color: white; gridline-color: #333; border: 1px solid #444; }
            QHeaderView::section { background-color: #2D2D2D; color: #AAA; padding: 4px; border: none; }
            QTableWidget::item { padding: 2px; }
        """)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
    def reset(self, code):
        """Reset for new stock code"""
        self.code = code
        self.reset_stats_only()
        
    def reset_stats_only(self):
        self.big_buy_vol = 0
        self.big_sell_vol = 0
        self.total_processed = 0
        self.table.setRowCount(0)
        self.update_summary()
        
    @Slot(str, dict)
    def on_tick(self, code, tick_data):
        # Filter Code
        if code != self.code: return
        
        try:
            vol = int(tick_data.get('volume', 0))
            threshold = self.spin_threshold.value()
            
            # Filter Logic
            # Note: Ticks sometimes come in packets, volume is for that specific match
            if vol < threshold:
                return 
                
            price = float(tick_data.get('close', 0))
            # tick_type: 1 = Buy (Ask Match), 2 = Sell (Bid Match)
            # Default to 0 (Unknown)
            tick_type = int(tick_data.get('tick_type', 0)) 
            
            # Determine Side
            is_buy = False # Default Sell
            
            # Logic from Shioaji: 1=Buy(Ask), 2=Sell(Bid)
            if tick_type == 1: 
                is_buy = True
            elif tick_type == 2:
                is_buy = False
            else:
                 # If tick_type is 0, we might need price movement heuristic
                 # But Shioaji usually sends 1 or 2 for active markets
                 pass
                 
            # Update Stats
            if is_buy:
                self.big_buy_vol += vol
            else:
                self.big_sell_vol += vol
                
            self.total_processed += 1
            self.update_summary()
            
            # Add to Table (Insert Top)
            self.table.insertRow(0)
            
            # Time String Handling
            ts_raw = tick_data.get('ts')
            ts_str = "00:00:00"
            if isinstance(ts_raw, str):
                if " " in ts_raw:
                     ts_str = ts_raw.split(" ")[-1] # 2023-01-01 09:00:00 -> 09:00:00
                else:
                    ts_str = ts_raw
            
            # 1. Time
            self.table.setItem(0, 0, QTableWidgetItem(str(ts_str)))
            
            # 2. Price
            item_price = QTableWidgetItem(f"{price:.2f}")
            item_price.setForeground(Qt.GlobalColor.white)
            self.table.setItem(0, 1, item_price)
            
            # 3. Vol
            item_vol = QTableWidgetItem(str(vol))
            item_vol.setForeground(Qt.GlobalColor.yellow) # Highlight large
            self.table.setItem(0, 2, item_vol)
            
            # 4. Side
            side_str = "外盤買進" if is_buy else "內盤賣出"
            item_side = QTableWidgetItem(side_str)
            item_side.setForeground(Qt.GlobalColor.red if is_buy else Qt.GlobalColor.green)
            self.table.setItem(0, 3, item_side)
            
            # Limit rows
            if self.table.rowCount() > 50:
                self.table.removeRow(50)
                
        except Exception as e:
            print(f"ChipMonitor Error: {e}")
            
    def update_summary(self):
        self.lbl_buy.setText(f"🔴 大戶買盤: {self.big_buy_vol}")
        self.lbl_sell.setText(f"🟢 大戶賣盤: {self.big_sell_vol}")
        
        net = self.big_buy_vol - self.big_sell_vol
        net_text = f"淨流向: {net}"
        if net > 0:
            net_color = "#FF4444"
            net_text = f"淨流向: +{net}"
        elif net < 0:
            net_color = "#44FF44"
        else:
            net_color = "#AAAAAA"
            
        self.lbl_net.setText(net_text)
        self.lbl_net.setStyleSheet(f"color: {net_color}; font-weight: bold; font-size: 14px;")
