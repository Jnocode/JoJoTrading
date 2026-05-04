from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QCursor, QColor, QAction

from jojo_trading.core.screener_controller import ScreenerController

class NumericTableWidgetItem(QTableWidgetItem):
    """Custom item to allow proper numerical sorting based on a raw_value attribute."""
    def __lt__(self, other):
        if hasattr(self, 'raw_value') and hasattr(other, 'raw_value'):
            try:
                return self.raw_value < other.raw_value
            except TypeError:
                pass
        return super().__lt__(other)

class ScreenerWorker(QThread):
    finished = Signal(list, str, dict) # results, error_msg, filter_schema

    def __init__(self, prompt: str, explicit_sectors: list = None):
        super().__init__()
        self.prompt = prompt
        self.explicit_sectors = explicit_sectors
        self.controller = ScreenerController()

    def run(self):
        results, err, filter_schema = self.controller.scan_by_natural_language(self.prompt, self.explicit_sectors)
        self.finished.emit(results, err, filter_schema)

class ScreenerTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. NLP Input Panel
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #252525; padding: 10px; border-radius: 6px;")
        input_layout = QVBoxLayout(input_frame)
        
        lbl_hint = QLabel("🤖 告訴 AI 你想找什麼樣的股票？(例如: 幫我找外資連買且均線多頭排列的半導體股票)")
        lbl_hint.setStyleSheet("color: #BB86FC; font-weight: bold;")
        input_layout.addWidget(lbl_hint)
        
        search_box = QHBoxLayout()
        
        self.btn_sector = QPushButton("板塊: 全部")
        self.btn_sector.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_sector.setStyleSheet("""
            QPushButton { background-color: #333; color: white; border: 1px solid #555; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 14px;}
            QPushButton:hover { background-color: #444; }
        """)
        
        self.sector_menu = QMenu(self)
        self.sector_menu.setStyleSheet("""
            QMenu { background-color: #2D2D2D; color: white; border: 1px solid #555; }
            QMenu::item:selected { background-color: #9C27B0; }
        """)
        
        self.sector_actions = []
        temp_controller = ScreenerController()
        sectors = temp_controller.db.get_all_sectors()
        for sec in sectors:
            action = QAction(sec, self)
            action.setCheckable(True)
            action.triggered.connect(self._update_sector_button)
            self.sector_menu.addAction(action)
            self.sector_actions.append(action)
            
        self.btn_sector.setMenu(self.sector_menu)
        search_box.addWidget(self.btn_sector)

        self.txt_prompt = QLineEdit()
        self.txt_prompt.setPlaceholderText("輸入白話文選股條件...")
        self.txt_prompt.setStyleSheet("""
            QLineEdit {
                background-color: #333; color: white; border: 1px solid #555; 
                padding: 10px; border-radius: 4px; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #9C27B0; }
        """)
        self.txt_prompt.returnPressed.connect(self.run_scan)
        
        self.btn_scan = QPushButton("✨ AI 智能掃描")
        self.btn_scan.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_scan.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; font-size: 14px;}
            QPushButton:hover { background-color: #BA68C8; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_scan.clicked.connect(self.run_scan)
        
        search_box.addWidget(self.txt_prompt)
        search_box.addWidget(self.btn_scan)
        input_layout.addLayout(search_box)
        # Quick Filters — 分類篩選條件
        from jojo_trading.ui.ui.flow_layout import FlowLayout
        
        # (label, color, [(prompt, enabled), ...])
        FILTER_CATEGORIES = [
            ("📊 基本面", "#4FC3F7", [
                ("DCF 估值潛在收益超過 5%", True),
                ("市值大於 1000 億", True),
                ("股價低於 50 元", True),
                ("🔒 本益比低於 15", False),
                ("🔒 高殖利率 (>5%)", False),
                ("🔒 股價低於淨值", False),
            ]),
            ("📈 技術面", "#FFB74D", [
                ("股價小於 50 且有潛在報酬", True),
                ("MA5 上穿 MA20 (黃金交叉)", True),
                ("MA5 下穿 MA20 (死亡交叉)", True),
                ("股價站上季線", True),
                ("KD 黃金交叉", True),
                ("成交量突增", True),
            ]),
            ("🏦 籌碼面", "#81C784", [
                ("外資連續買超", True),
                ("投信買超", True),
                ("三大法人同步買超", True),
                ("🔒 主力籌碼集中", False),
            ]),
        ]
        
        self.quick_filter_btns = {}
        
        btn_style_tpl = """
            QPushButton {{ background-color: #333; color: #CCC; border: 1px solid #555; padding: 4px 10px; border-radius: 12px; font-size: 12px; }}
            QPushButton:hover {{ background-color: #555; color: white; border: 1px solid {color}; }}
            QPushButton:checked {{ background-color: {bg}; color: white; border: 1px solid {color}; }}
        """
        btn_disabled_style = """
            QPushButton { background-color: #2A2A2A; color: #666; border: 1px solid #3A3A3A; padding: 4px 10px; border-radius: 12px; font-size: 12px; }
        """
        
        # 每個類別一行
        for cat_label, cat_color, prompts in FILTER_CATEGORIES:
            row_widget = QWidget()
            row_layout = FlowLayout(row_widget, margin=0, spacing=6)
            
            lbl = QLabel(cat_label)
            lbl.setStyleSheet(f"color: {cat_color}; font-size: 12px; font-weight: bold; padding-right: 4px;")
            lbl.setMinimumWidth(80)
            lbl.setMaximumWidth(120)
            row_layout.addWidget(lbl)
            
            checked_bg = {"#4FC3F7": "#1565C0", "#FFB74D": "#E65100", "#81C784": "#2E7D32"}.get(cat_color, "#6A1B9A")
            active_style = btn_style_tpl.format(color=cat_color, bg=checked_bg)
            
            for qp, enabled in prompts:
                btn_q = QPushButton(qp)
                btn_q.setCursor(QCursor(Qt.PointingHandCursor if enabled else Qt.ForbiddenCursor))
                
                if enabled:
                    btn_q.setCheckable(True)
                    btn_q.setStyleSheet(active_style)
                    btn_q.clicked.connect(lambda checked=False, p=qp: self.toggle_prompt(p))
                    self.quick_filter_btns[qp] = btn_q
                else:
                    btn_q.setEnabled(False)
                    btn_q.setStyleSheet(btn_disabled_style)
                    btn_q.setToolTip("即將推出 — 需要技術指標/籌碼數據整合")
                
                row_layout.addWidget(btn_q)
            
            input_layout.addWidget(row_widget)
        
        layout.addWidget(input_frame)
        
        # 1.5 AI Reasoning Panel (Hidden by default)
        self.ai_reasoning_frame = QFrame()
        self.ai_reasoning_frame.setStyleSheet("background-color: #2D2D2D; padding: 10px; border-radius: 6px; border-left: 4px solid #9C27B0;")
        self.ai_reasoning_frame.setVisible(False)
        reasoning_layout = QVBoxLayout(self.ai_reasoning_frame)
        self.lbl_reasoning = QLabel("")
        self.lbl_reasoning.setWordWrap(True)
        self.lbl_reasoning.setStyleSheet("color: #E0E0E0; font-size: 13px; line-height: 1.5;")
        reasoning_layout.addWidget(self.lbl_reasoning)
        layout.addWidget(self.ai_reasoning_frame)

        # 2. Result Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["代號", "名稱", "價格", "潛在報酬 (DCF)", "市值 (億)", "產業", "更新時間"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1E1E1E; gridline-color: #333; border: none; }
            QHeaderView::section { background-color: #333; color: white; padding: 8px; font-weight: bold; border: none; }
            QTableWidget::item { padding: 5px; color: #E0E0E0;}
            QTableWidget::item:hover { background-color: #3A3A3A; }
        """)
        # 雙擊跳轉到分析頁面
        self.table.cellDoubleClicked.connect(self.on_stock_double_clicked)
        
        layout.addWidget(self.table)
        
    def _update_sector_button(self):
        selected = [a.text() for a in self.sector_actions if a.isChecked()]
        if not selected:
            self.btn_sector.setText("板塊: 全部")
        elif len(selected) == 1:
            self.btn_sector.setText(f"板塊: {selected[0]}")
        else:
            self.btn_sector.setText(f"板塊: 已選 {len(selected)} 項")

    def toggle_prompt(self, text: str):
        """快速篩選: 點擊追加條件，再點移除 (toggle 行為)"""
        current = self.txt_prompt.text().strip()
        
        if not current:
            # 空白 → 直接填入
            self.txt_prompt.setText(text)
        elif text in current:
            # 已存在 → 移除 (toggle off)
            parts = [p.strip() for p in current.split("，") if p.strip() and p.strip() != text]
            # 也嘗試英文逗號分隔
            if text in current and len(parts) == 1 and parts[0] == current:
                parts = [p.strip() for p in current.split(",") if p.strip() and p.strip() != text]
            self.txt_prompt.setText("，".join(parts))
        else:
            # 追加新條件
            self.txt_prompt.setText(f"{current}，{text}")
        
        # 同步按鈕 checked 狀態
        final_text = self.txt_prompt.text()
        for btn_text, btn in self.quick_filter_btns.items():
            btn.setChecked(btn_text in final_text)

    def run_scan(self):
        prompt = self.txt_prompt.text().strip()
        
        # 防止重複點擊或觸發導致 QThread 被覆寫銷毀 (閃退的主因)
        if self.worker and self.worker.isRunning():
            return
            
        selected_sectors = [a.text() for a in self.sector_actions if a.isChecked()]
        
        if not prompt and selected_sectors:
            prompt = "找出這些板塊的股票"
        elif not prompt:
            return
            
        self.table.setRowCount(0)
        self.btn_scan.setText("⏳ AI 解析與篩選中...")
        self.btn_scan.setEnabled(False)
        
        self.worker = ScreenerWorker(prompt, selected_sectors)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()
        
    def on_scan_finished(self, results, err, filter_schema):
        self.btn_scan.setText("✨ AI 智能掃描")
        self.btn_scan.setEnabled(True)
        
        if err:
            QMessageBox.warning(self, "掃描錯誤", err)
            return
            
        # 顯示 AI 解析邏輯
        reasoning = filter_schema.get("reasoning", "")
        if reasoning:
            schema_details = []
            for k, v in filter_schema.items():
                if k != "reasoning" and v is not None:
                    schema_details.append(f"{k}: {v}")
            details_str = " | ".join(schema_details)
            self.lbl_reasoning.setText(f"<b>💡 AI 解析邏輯:</b> {reasoning}<br><span style='color:#888; font-size:11px;'>[過濾參數] {details_str}</span>")
            self.ai_reasoning_frame.setVisible(True)
        else:
            self.ai_reasoning_frame.setVisible(False)

        if not results:
            QMessageBox.information(self, "掃描結果", "沒有找到符合條件的股票。")
            return
            
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(results))
        for r, row in enumerate(results):
            code_str = str(row.get('code', ''))
            code_item = NumericTableWidgetItem(code_str)
            code_item.raw_value = code_str # String sort for codes to keep '0050' before '2330'
            self.table.setItem(r, 0, code_item)
            
            self.table.setItem(r, 1, QTableWidgetItem(str(row.get('name', ''))))
            
            p_val = float(row.get('price', 0.0))
            p_item = NumericTableWidgetItem(f"{p_val:.2f}")
            p_item.raw_value = p_val
            p_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 2, p_item)
            
            ret = float(row.get('potential_return', 0.0))
            ret_item = NumericTableWidgetItem(f"{ret:.1f}%")
            ret_item.raw_value = ret
            if ret > 5: ret_item.setForeground(QColor("#FF5252")) # High potential
            elif ret < 0: ret_item.setForeground(QColor("#69F0AE")) # Negative
            ret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 3, ret_item)
            
            cap = float(row.get('market_cap', 0.0))
            cap_item = NumericTableWidgetItem(f"{cap:,.0f}")
            cap_item.raw_value = cap
            cap_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 4, cap_item)
            
            self.table.setItem(r, 5, QTableWidgetItem(str(row.get('sector', ''))))
            
            # 更新時間欄位
            updated_str = str(row.get('last_updated', ''))
            display_time = ''
            time_color = QColor('#888')  # default dim
            try:
                if updated_str:
                    # Handle ISO format with or without microseconds
                    for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
                        try:
                            dt = datetime.strptime(updated_str[:26], fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        dt = None
                    if dt:
                        age = datetime.now() - dt
                        display_time = dt.strftime('%m/%d %H:%M')
                        if age < timedelta(hours=1):
                            time_color = QColor('#69F0AE')  # fresh green
                        elif age < timedelta(hours=24):
                            time_color = QColor('#AAAAAA')  # normal
                        else:
                            time_color = QColor('#666666')  # stale dim
            except Exception:
                display_time = updated_str[:16] if updated_str else '---'
            
            time_item = QTableWidgetItem(display_time)
            time_item.setForeground(time_color)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 6, time_item)
            
        self.table.setSortingEnabled(True)
    
    def on_stock_double_clicked(self, row, col):
        """雙擊股票跳轉到分析頁面"""
        code_item = self.table.item(row, 0)
        if not code_item:
            return
        
        stock_code = code_item.text()
        
        # 跳轉到 Analysis Tab (index 2)
        if hasattr(self.main_window, 'tabs') and hasattr(self.main_window, 'analysis_tab'):
            self.main_window.tabs.setCurrentIndex(2)  # Analysis Tab
            self.main_window.analysis_tab.input_code.setText(stock_code)
            self.main_window.analysis_tab.start_analysis()
