
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QProgressBar, 
    QScrollArea, QFrame, QSplitter, QFileDialog, QMessageBox,
    QSizePolicy, QGroupBox, QRadioButton, QButtonGroup, 
    QCheckBox, QTabWidget, QGridLayout, QDateEdit, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QDate
from jojo_trading.core.backtest_controller import BacktestController

class BacktestResultWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("回測結果詳細報告 (Backtest Results)")
        self.resize(1200, 800)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("詳細回測報告 (Standard Report)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # --- Metrics Cards (TradingView Style) ---
        metrics_container = QWidget()
        metrics_layout = QHBoxLayout(metrics_container)
        metrics_layout.setSpacing(10)
        metrics_layout.setContentsMargins(0, 5, 0, 10)
        
        # Helper to create card
        def create_card(title, value, subtext="", color="#FFFFFF", subcolor="#AAAAAA"):
            card = QFrame()
            card.setStyleSheet("background-color: #2D2D2D; border-radius: 6px;")
            l = QVBoxLayout(card)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #AAAAAA; font-size: 12px;")
            v_lbl = QLabel(value)
            v_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
            s_lbl = QLabel(subtext)
            s_lbl.setStyleSheet(f"color: {subcolor}; font-size: 11px;")
            l.addWidget(t_lbl)
            l.addWidget(v_lbl)
            l.addWidget(s_lbl)
            return card, v_lbl, s_lbl

        self.cards = {}
        # 1. Net Profit
        c1, self.lbl_profit, self.lbl_profit_pct = create_card("總損益 (Net Profit)", "$0", "0.00%")
        metrics_layout.addWidget(c1)
        # 2. Max Drawdown
        c2, self.lbl_mdd, self.lbl_mdd_pct = create_card("最大回撤 (Max Drawdown)", "$0", "0.00%")
        metrics_layout.addWidget(c2)
        # 3. Benchmark
        c3, self.lbl_bench, self.lbl_bench_pct = create_card("買入持有 (Buy & Hold)", "$0", "0.00%")
        metrics_layout.addWidget(c3)
        # 4. Profit Factor
        c4, self.lbl_pf, _ = create_card("獲利因子 (PF)", "0.00")
        metrics_layout.addWidget(c4)
        # 5. Sharpe Ratio
        c5, self.lbl_sharpe, _ = create_card("夏普值 (Sharpe)", "0.00")
        metrics_layout.addWidget(c5)
        # 6. Win Rate
        c6, self.lbl_win, self.lbl_trades = create_card("勝率 (Win Rate)", "0.00%", "0 Trades")
        metrics_layout.addWidget(c6)
        
        layout.addWidget(metrics_container)
        
        # Splitter for Results & Chart
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Text Results
        result_container = QWidget()
        result_layout = QVBoxLayout(result_container)
        result_layout.setContentsMargins(0,0,0,0)
        
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setStyleSheet("""
            background-color: #1E1E1E;
            color: #00FF00;
            font-family: Consolas;
            font-size: 14px;
            border-radius: 8px;
            padding: 10px;
        """)
        result_layout.addWidget(QLabel("📊 回測結果與 AI 診斷 (Results & AI Doctor)"))
        result_layout.addWidget(self.result_area)
        
        splitter.addWidget(result_container)
        
        # Right: Chart
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0,0,0,0)
        
        self.chart = BacktestChart()
        self.chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        chart_layout.addWidget(QLabel("📈 技術線圖 (Chart)"))
        chart_layout.addWidget(self.chart)
        
        splitter.addWidget(chart_container)
        
        # Set splitter sizes (35% Left, 65% Right)
        splitter.setStretchFactor(0, 35)
        splitter.setStretchFactor(1, 65)
        
        layout.addWidget(splitter)

    def update_data(self, result):
        # 1. Update Metrics Cards
        pnl = result['final_equity'] - result['initial_capital']
        pnl_color = "#00FF00" if pnl >= 0 else "#FF0000"
        self.lbl_profit.setText(f"${pnl:,.0f}")
        self.lbl_profit.setStyleSheet(f"color: {pnl_color}; font-size: 20px; font-weight: bold;")
        self.lbl_profit_pct.setText(f"{result['total_return_pct']:.2f}%")
        
        mdd = result.get('max_drawdown_pct', 0)
        self.lbl_mdd.setText(f"{mdd:.2f}%")
        self.lbl_mdd.setStyleSheet("color: #FF0000; font-size: 20px; font-weight: bold;")
        
        bench = result.get('benchmark_return', 0)
        bench_color = "#00FF00" if bench >= 0 else "#FF0000"
        self.lbl_bench.setText(f"{bench:.2f}%")
        self.lbl_bench.setStyleSheet(f"color: {bench_color}; font-size: 20px; font-weight: bold;")
        
        pf = result.get('profit_factor', 0)
        self.lbl_pf.setText(f"{pf:.2f}")

        sharpe = result.get('sharpe_ratio', 0)
        self.lbl_sharpe.setText(f"{sharpe:.2f}")
        
        self.lbl_win.setText(f"{result['win_rate']:.2f}%")
        self.lbl_trades.setText(f"共 {result['total_trades']} 筆交易")

        # 3. Update Text Report (including AI Diagnosis)
        report = "👨‍⚕️ 策略健檢報告 (AI Strategy Doctor)\n"
        report += f"{'='*40}\n"
        if 'ai_diagnosis' in result:
            report += f"{result['ai_diagnosis']}\n\n"
        else:
            report += "⚠️ AI 診斷未能生成。\n\n"
            
        report += "✅ 詳細交易紀錄\n"
        report += f"{'-'*40}\n"
        report += "最近 5 筆交易 (Last 5 Trades):\n"
        
        for t in result['trades'][-5:]:
            action = t['type'].upper()
            date = t['date'].strftime('%Y-%m-%d')
            price = t['price']
            qty = t['qty']
            pnl_val = f", 損益: {t['pnl']:,.0f}" if 'pnl' in t else ""
            color = "🟢" if action == "BUY" else "🔴"
            cmd_chn = "買入" if action == "BUY" else "賣出"
            report += f"{color} [{date}] {cmd_chn} {qty}股 @ {price}{pnl_val}\n"
            
        self.result_area.setText(report)
        
        # 2. Update Chart
        if 'df' in result:
            self.chart.plot(result['df'], result['trades'])

class BacktestWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, stock_code, buy_strat, sell_strat, initial_capital, start_date, end_date, interval):
        super().__init__()
        self.stock_code = stock_code
        self.buy_strat = buy_strat
        self.sell_strat = sell_strat
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.controller = BacktestController()
        
    def run(self):
        try:
            self.progress.emit(0)
            
            # 使用包含 AI 的新 Controller 執行回測進程
            result = self.controller.run_backtest_with_diagnosis(
                self.stock_code, 
                self.buy_strat, 
                self.sell_strat, 
                initial_capital=self.initial_capital,
                start_date=self.start_date,
                end_date=self.end_date,
                interval=self.interval,
                progress_callback=self.update_progress
            )
            
            if 'error' in result:
                self.error.emit(result['error'])
            else:
                self.finished.emit(result)
                
        except Exception as e:
            self.error.emit(str(e))
            
    def update_progress(self, val):
        self.progress.emit(val)

class BacktestTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        self.worker = None
        self.result_window = None

    def setup_ui(self):
        # --- Main Layout (Vertical) ---
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # =================================================
        # 1. Top Toolbar (Settings & Actions)
        # =================================================
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame { background-color: #2D2D2D; border-bottom: 1px solid #444; }
            QLabel { color: #DDD; font-weight: bold; }
            QLineEdit, QDateEdit, QComboBox {
                background-color: #1E1E1E; color: white; border: 1px solid #555; border-radius: 4px; padding: 4px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(10, 8, 10, 8)
        toolbar_layout.setSpacing(12)
        
        # Title/Icon
        title = QLabel("🧪 回測實驗室")
        title.setStyleSheet("font-size: 16px; color: #00B4D8; margin-right: 10px;")
        toolbar_layout.addWidget(title)
        
        # Inputs (Compact)
        self.input_code = QLineEdit("2330")
        self.input_code.setFixedWidth(80)
        self.input_code.setPlaceholderText("Code")
        
        self.input_capital = QLineEdit("1000000")
        self.input_capital.setFixedWidth(100)
        self.input_capital.setPlaceholderText("Capital")
        
        toolbar_layout.addWidget(QLabel("代號:"))
        toolbar_layout.addWidget(self.input_code)
        toolbar_layout.addWidget(QLabel("本金:"))
        toolbar_layout.addWidget(self.input_capital)
        
        # Date Range
        self.input_start = QDateEdit()
        self.input_start.setCalendarPopup(True)
        self.input_start.setDate(QDate.currentDate().addYears(-1))
        self.input_start.setDisplayFormat("yyyy-MM-dd")
        self.input_start.setFixedWidth(100)
        
        self.input_end = QDateEdit()
        self.input_end.setCalendarPopup(True)
        self.input_end.setDate(QDate.currentDate())
        self.input_end.setDisplayFormat("yyyy-MM-dd")
        self.input_end.setFixedWidth(100)
        
        toolbar_layout.addWidget(QLabel("期間:"))
        toolbar_layout.addWidget(self.input_start)
        toolbar_layout.addWidget(QLabel("➜"))
        toolbar_layout.addWidget(self.input_end)
        
        # Timeframe
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["Daily (1d)", "Weekly (1wk)", "Monthly (1mo)", "60 Min", "30 Min", "15 Min", "5 Min"])
        self.combo_interval.setFixedWidth(110)
        toolbar_layout.addWidget(self.combo_interval)
        
        toolbar_layout.addStretch() # Push buttons to the right
        
        # Action Buttons (Run & Export)
        self.btn_run = QPushButton("🚀 執行 (RUN)")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #00B4D8; color: white; font-weight: bold; padding: 6px 15px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #0096C7; }
            QPushButton:disabled { background-color: #555; }
        """)
        self.btn_run.clicked.connect(self.start_backtest)
        
        self.btn_export = QPushButton("💾 匯出")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #444; color: white; padding: 6px 15px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #555; border: 1px solid #777; }
        """)
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        
        self.btn_monitor = QPushButton("🔔 加入監控")
        self.btn_monitor.setCursor(Qt.PointingHandCursor)
        self.btn_monitor.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0; color: white; padding: 6px 15px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #AB47BC; border: 1px solid #E1BEE7; }
        """)
        self.btn_monitor.clicked.connect(self.add_to_monitor)
        
        toolbar_layout.addWidget(self.btn_run)
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addWidget(self.btn_monitor)
        
        toolbar_frame.setMinimumSize(1, 1)
        main_layout.addWidget(toolbar_frame)
        
        # =================================================
        # 2. Main Content Splitter (Left Sidebar | Right Editor)
        # =================================================
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: #444; }")
        
        # --- Left Sidebar: Strategy Wizard ---
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("background-color: #252525;")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0,0,0,0)
        sidebar_layout.setSpacing(0)
        
        # Wizard Header
        wiz_header = QLabel("🧙‍♂️ 策略產生器 (Wizard)")
        wiz_header.setStyleSheet("background-color: #333; color: #DDD; padding: 8px; font-weight: bold; border-bottom: 1px solid #444;")
        sidebar_layout.addWidget(wiz_header)
        
        # Wizard Scroll Area
        wizard_scroll = QScrollArea()
        wizard_scroll.setWidgetResizable(True)
        wizard_scroll.setFrameShape(QFrame.NoFrame)
        
        wizard_content = QWidget()
        wizard_layout = QVBoxLayout(wizard_content)
        wizard_layout.setContentsMargins(10, 10, 10, 10)
        wizard_layout.setSpacing(10)
        
        # Tabs for Wizard
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0px solid #444; }
            QTabBar::tab { background: #333; color: #AAA; padding: 6px 10px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #444; color: white; font-weight: bold; }
        """)
        
        # --- Tech Tab ---
        tab_tech = QWidget()
        grid_tech = QGridLayout(tab_tech)
        for i, h in enumerate(["📈 多方 (Long)", "📉 空方 (Short)"]):
            hl = QLabel(h)
            hl.setStyleSheet(f"color: {'#00FF00' if i==0 else '#FF0000'}; border-bottom: 1px solid #555;")
            grid_tech.addWidget(hl, 0, i)

        self.chk_tech_bull = QCheckBox("站上月線 (>MA20)")
        self.chk_tech_gold = QCheckBox("黃金交叉 (MA5>MA20)")
        self.chk_tech_rsi  = QCheckBox("RSI強勢 (>50)")
        self.chk_tech_bear = QCheckBox("跌破月線 (<MA20)")
        self.chk_tech_dead = QCheckBox("死亡交叉 (MA5<MA20)")
        self.chk_tech_rsi_weak = QCheckBox("RSI弱勢 (<50)")
        
        grid_tech.addWidget(self.chk_tech_bull, 1, 0); grid_tech.addWidget(self.chk_tech_bear, 1, 1)
        grid_tech.addWidget(self.chk_tech_gold, 2, 0); grid_tech.addWidget(self.chk_tech_dead, 2, 1)
        
        # New KD
        self.chk_tech_kd_gold = QCheckBox("KD 黃金交叉 (K>D)")
        self.chk_tech_kd_dead = QCheckBox("KD 死亡交叉 (K<D)")

        # New MACD
        self.chk_tech_macd_bull = QCheckBox("MACD 黃金交叉")
        self.chk_tech_macd_bear = QCheckBox("MACD 死亡交叉")
        
        # New Bollinger Bands
        self.chk_tech_bb_break = QCheckBox("布林通道突破 (上緣)")
        self.chk_tech_bb_break_bear = QCheckBox("布林通道跌破 (下緣)")
        
        grid_tech.addWidget(self.chk_tech_kd_gold, 9, 0);    grid_tech.addWidget(self.chk_tech_kd_dead, 9, 1)
        grid_tech.addWidget(self.chk_tech_macd_bull, 10, 0); grid_tech.addWidget(self.chk_tech_macd_bear, 10, 1)
        grid_tech.addWidget(self.chk_tech_bb_break, 11, 0);  grid_tech.addWidget(self.chk_tech_bb_break_bear, 11, 1)
        
        # New OpenClaw SuperTrend + SMC
        self.chk_tech_supertrend = QCheckBox("SuperTrend AI (Bull)")
        self.chk_tech_smc_break = QCheckBox("SMC 結構突破 (Bull)")
        self.chk_tech_risk_radar = QCheckBox("🛡️ 風險雷達過濾 (Risk<6)")
        
        self.chk_tech_supertrend_bear = QCheckBox("SuperTrend AI (Bear)")
        self.chk_tech_smc_break_bear = QCheckBox("SMC 結構跌破 (Bear)")
        
        grid_tech.addWidget(self.chk_tech_supertrend, 12, 0); grid_tech.addWidget(self.chk_tech_supertrend_bear, 12, 1)
        grid_tech.addWidget(self.chk_tech_smc_break, 13, 0); grid_tech.addWidget(self.chk_tech_smc_break_bear, 13, 1)
        grid_tech.addWidget(self.chk_tech_risk_radar, 14, 0, 1, 2)
        grid_tech.addWidget(self.chk_tech_rsi, 3, 0);  grid_tech.addWidget(self.chk_tech_rsi_weak, 3, 1)
        
        # --- Chips Tab ---
        tab_chip = QWidget()
        grid_chip = QGridLayout(tab_chip)
        for i, h in enumerate(["📈 多方 (Long)", "📉 空方 (Short)"]):
            hl = QLabel(h)
            hl.setStyleSheet(f"color: {'#00FF00' if i==0 else '#FF0000'}; border-bottom: 1px solid #555;")
            grid_chip.addWidget(hl, 0, i)
            
        self.chk_chip_foreign = QCheckBox("外資買 (>1000)")
        self.chk_chip_trust   = QCheckBox("投信買 (>0)")
        self.chk_chip_dealer  = QCheckBox("自營買 (>500)")
        self.chk_chip_foreign_sell = QCheckBox("外資賣 (<-1000)")
        self.chk_chip_trust_sell   = QCheckBox("投信賣 (<0)")
        self.chk_chip_dealer_sell  = QCheckBox("自營賣 (<-500)")
        
        grid_chip.addWidget(self.chk_chip_foreign, 1, 0); grid_chip.addWidget(self.chk_chip_foreign_sell, 1, 1)
        grid_chip.addWidget(self.chk_chip_trust, 2, 0);   grid_chip.addWidget(self.chk_chip_trust_sell, 2, 1)
        grid_chip.addWidget(self.chk_chip_dealer, 3, 0);  grid_chip.addWidget(self.chk_chip_dealer_sell, 3, 1)
        
        # --- Fund Tab ---
        tab_fund = QWidget()
        grid_fund = QGridLayout(tab_fund)
        for i, h in enumerate(["📈 多方 (Long)", "📉 空方 (Short)"]):
            hl = QLabel(h)
            hl.setStyleSheet(f"color: {'#00FF00' if i==0 else '#FF0000'}; border-bottom: 1px solid #555;")
            grid_fund.addWidget(hl, 0, i)
            
        self.chk_fund_revenue = QCheckBox("營收成長 (>15%)")
        self.chk_fund_eps     = QCheckBox("公司獲利 (EPS>0)")
        self.chk_fund_rev_drop = QCheckBox("營收衰退 (<0%)")
        self.chk_fund_loss     = QCheckBox("公司虧損 (EPS<0)")
        
        grid_fund.addWidget(self.chk_fund_revenue, 1, 0); grid_fund.addWidget(self.chk_fund_rev_drop, 1, 1)
        grid_fund.addWidget(self.chk_fund_eps, 2, 0);     grid_fund.addWidget(self.chk_fund_loss, 2, 1)
        
        self.tabs.addTab(tab_tech, "⚡ 技術")
        self.tabs.addTab(tab_chip, "💰 籌碼")
        self.tabs.addTab(tab_fund, "📊 基本")
        wizard_layout.addWidget(self.tabs)
        
        # Wizard Logic
        logic_group = QGroupBox("🔗 組合邏輯")
        logic_group.setStyleSheet("QGroupBox { border: 1px solid #444; padding-top: 10px; margin-top: 10px; color: #AAA; font-weight: bold; }")
        logic_layout = QVBoxLayout(logic_group)
        
        self.radio_and = QRadioButton("AND (所有條件同時符合)")
        self.radio_or = QRadioButton("OR (任一條件符合)")
        self.radio_and.setChecked(True); self.radio_and.setStyleSheet("color: #DDD;")
        self.radio_or.setStyleSheet("color: #DDD;")
        self.logic_group = QButtonGroup(self)
        self.logic_group.addButton(self.radio_and); self.logic_group.addButton(self.radio_or)
        
        logic_layout.addWidget(self.radio_and)
        logic_layout.addWidget(self.radio_or)
        wizard_layout.addWidget(logic_group)
        
        # Apply Buttons
        btn_apply_buy = QPushButton("⬇️ 套用至買入策略")
        btn_apply_sell = QPushButton("⬇️ 套用至賣出策略")
        btn_start_style = "background-color: #444; color: white; padding: 8px; border-radius: 4px; margin-top: 5px;"
        btn_apply_buy.setStyleSheet(btn_start_style)
        btn_apply_sell.setStyleSheet(btn_start_style)
        btn_apply_buy.clicked.connect(lambda: self.apply_wizard(self.input_buy))
        btn_apply_sell.clicked.connect(lambda: self.apply_wizard(self.input_sell))
        
        wizard_layout.addWidget(btn_apply_buy)
        wizard_layout.addWidget(btn_apply_sell)
        wizard_layout.addStretch()
        
        wizard_scroll.setWidget(wizard_content)
        sidebar_layout.addWidget(wizard_scroll)
        
        # Add Sidebar to Splitter
        self.main_splitter.addWidget(sidebar_widget)
        
        # --- Right Panel: Editor Tabs ---
        editor_widget = QWidget()
        editor_widget.setStyleSheet("background-color: #1E1E1E;")
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0,0,0,0)
        editor_layout.setSpacing(0)
        
        # Editor Tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setStyleSheet("""
            QTabWidget::pane { border: 0px; }
            QTabBar::tab { background: #252525; color: #888; padding: 8px 20px; border-right: 1px solid #333; }
            QTabBar::tab:selected { background: #1E1E1E; color: white; border-top: 2px solid #00B4D8; }
        """)
        
        # Buy Editor
        self.input_buy = QTextEdit()
        self.input_buy.setPlaceholderText("close > MA20")
        self.input_buy.setPlainText("close > MA20")
        self.input_buy.setStyleSheet("background-color: #1E1E1E; color: #66bb6a; font-family: Consolas, 'Courier New', monospace; font-size: 14px; border: none; padding: 10px;")
        
        # Sell Editor
        self.input_sell = QTextEdit()
        self.input_sell.setPlaceholderText("close < MA20")
        self.input_sell.setPlainText("close < MA20")
        self.input_sell.setStyleSheet("background-color: #1E1E1E; color: #ff6b6b; font-family: Consolas, 'Courier New', monospace; font-size: 14px; border: none; padding: 10px;")

        self.editor_tabs.addTab(self.input_buy, "📈 買入策略 (Buy Strategy)")
        self.editor_tabs.addTab(self.input_sell, "📉 賣出策略 (Sell Strategy)")
        
        editor_layout.addWidget(self.editor_tabs)
        
        # Add Editor to Splitter
        self.main_splitter.addWidget(editor_widget)
        
        # Set Splitter Ratio
        self.main_splitter.setStretchFactor(0, 30) # 30% Sidebar
        self.main_splitter.setStretchFactor(1, 70) # 70% Editor
        
        main_layout.addWidget(self.main_splitter)
        
        # =================================================
        # 3. Bottom Status Bar
        # =================================================
        status_frame = QFrame()
        status_frame.setFixedHeight(25) # Slim Height
        status_frame.setStyleSheet("background-color: #007ACC; border-top: 1px solid #005F9E;")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 0, 10, 0) # Zero vertical margins
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: white; font-size: 10px; font-weight: bold;") # Small compact font
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: #005F9E; color: white; text-align: center; } QProgressBar::chunk { background: #00B4D8; }")
        self.progress_bar.hide()
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        # Mapping (Re-mapped to new checkboxes)
        self.wizard_map = {
            self.chk_tech_bull: "close > MA20", self.chk_tech_gold: "MA5 > MA20", self.chk_tech_rsi: "RSI14 > 50",
            self.chk_tech_bear: "close < MA20", self.chk_tech_dead: "MA5 < MA20", self.chk_tech_rsi_weak: "RSI14 < 50",
            # OpenClaw Recommended
            self.chk_tech_kd_gold: "K > D",
            self.chk_tech_kd_dead: "K < D",
            self.chk_tech_macd_bull: "MACD_OSC > 0",
            self.chk_tech_macd_bear: "MACD_OSC < 0",
            
            # SuperTrend AI + SMC
            self.chk_tech_supertrend: "SuperTrend_Trend == 1",
            self.chk_tech_supertrend_bear: "SuperTrend_Trend == -1",
            self.chk_tech_smc_break: "close > SMC_SwingHigh",
            self.chk_tech_smc_break_bear: "close < SMC_SwingLow",
            self.chk_tech_risk_radar: "Risk_Allowed == True",
            
            self.chk_tech_bb_break: "close > BB_Upper",
            self.chk_tech_bb_break_bear: "close < BB_Lower",
            self.chk_chip_foreign: "Foreign_Buy > 1000", self.chk_chip_trust: "IT_Buy > 0", self.chk_chip_dealer: "Dealer_Buy > 500",
            self.chk_chip_foreign_sell: "Foreign_Buy < -1000", self.chk_chip_trust_sell: "IT_Buy < 0", self.chk_chip_dealer_sell: "Dealer_Buy < -500",
            self.chk_fund_revenue: "Revenue_YOY > 15", self.chk_fund_eps: "EPS > 0",
            self.chk_fund_rev_drop: "Revenue_YOY < 0", self.chk_fund_loss: "EPS < 0"
        }
        for c in self.wizard_map: c.setStyleSheet("color: #DDD;")



    def export_report(self):
        if not hasattr(self, 'last_result') or not self.last_result:
             QMessageBox.warning(self, "Export", "無回測資料可匯出")
             return
             
        # Generate HTML Report
        res = self.last_result
        
        # CSS Style (Using single quotes to avoid confusion)
        css_style = '''
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }
                h1 { color: #333; }
                .summary { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .trade-table { width: 100%; border-collapse: collapse; background: white; }
                .trade-table th, .trade-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .trade-table th { background-color: #00B4D8; color: white; }
                .win { color: green; font-weight: bold; }
                .loss { color: red; font-weight: bold; }
            </style>
        </head>
        '''
        
        # Body (F-String)
        html_body = f'''
        <body>
            <h1>🧪 JoJo Trader Backtest Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Stock Code:</strong> {self.input_code.text()}</p>
                <p><strong>Strategy (Buy):</strong> {self.input_buy.toPlainText()}</p>
                <p><strong>Final Equity:</strong> ${res['final_equity']:,.0f}</p>
                <p><strong>Total Return:</strong> {res['total_return_pct']:.2f}%</p>
                <p><strong>Win Rate:</strong> {res['win_rate']:.2f}% ({res['total_trades']} Trades)</p>
            </div>
            <div class="summary">
                <h2>Trade History</h2>
                <table class="trade-table">
                    <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Price</th>
                        <th>Shares</th>
                        <th>Value</th>
                        <th>PnL</th>
                    </tr>
        '''
        
        # Combine
        html_content = css_style + html_body
        
        # Add Rows
        for t in res['trades']:
            pnl_class = "win" if t['pnl'] > 0 else "loss"
            pnl_str = f"<span class='{pnl_class}'>${t['pnl']:,.0f}</span>" if t['pnl'] != 0 else "-"
            
            # Use explicit concatenation to avoid triple quote risks
            row = (
                "<tr>"
                f"<td>{t['date'].strftime('%Y-%m-%d')}</td>"
                f"<td>{t['type']}</td>"
                f"<td>{t['price']:.2f}</td>"
                f"<td>{t['size']}</td>"
                f"<td>{t['value']:.0f}</td>"
                f"<td>{pnl_str}</td>"
                "</tr>"
            )
            html_content += row
            
        # Closing HTML
        html_content += (
            "</table>"
            "</div>"
            "</body>"
            "</html>"
        )
        
        # Save File
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", f"Backtest_{self.input_code.text()}.html", "HTML Files (*.html)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            QMessageBox.information(self, "Export", "報告已匯出!")
            

    def start_backtest(self):
        code = self.input_code.text().strip()
        buy = self.input_buy.toPlainText().strip()
        sell = self.input_sell.toPlainText().strip()
        
        # Get Dates
        start_date = self.input_start.date().toString("yyyy-MM-dd")
        end_date = self.input_end.date().toString("yyyy-MM-dd")
        
        # Map Interval
        int_map = {
            "Daily (1d)": "1d", "Weekly (1wk)": "1wk", "Monthly (1mo)": "1mo",
            "60 Min": "60m", "30 Min": "30m", "15 Min": "15m", "5 Min": "5m"
        }
        interval = int_map.get(self.combo_interval.currentText(), "1d")
        
        try:
            capital = float(self.input_capital.text())
        except:
            capital = 1000000
            
        if not code:
            QMessageBox.warning(self, "Input Error", "請輸入股票代號 (Stock Code)")
            return

        # UI State
        self.btn_run.setEnabled(False)
        self.btn_run.setText("執行中 (Running)...")
        self.btn_export.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("⏳ 回測進行中...")
        self.status_label.setStyleSheet("color: #00B4D8; font-weight: bold;")

        # Start Worker
        self.worker = BacktestWorker(code, buy, sell, capital, start_date, end_date, interval)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, result):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("🚀 執行回測 (Run)")
        self.btn_export.setEnabled(True)
        self.last_result = result # Store for export
        self.progress_bar.hide()
        
        self.status_label.setText(f"✅ 完成! 報酬率: {result['total_return_pct']:.2f}% (詳見彈出視窗)")
        self.status_label.setStyleSheet("color: #00FF00; font-weight: bold;")
        
        # Open Result Window
        if self.result_window is None:
            self.result_window = BacktestResultWindow()
            
        self.result_window.update_data(result)
        self.result_window.show()
        self.result_window.raise_() # Bring to front

    def apply_wizard(self, target_input):
        # Generates strategy string from checked boxes and applies to target input
        conditions = []
        for chk, code in self.wizard_map.items():
            if chk.isChecked():
                conditions.append(code)
        
        if not conditions:
            # If nothing checked, maybe define a default or do nothing?
            # Let's clean the input if nothing checked? Or just return
            return
            
        joiner = " and " if self.radio_and.isChecked() else " or "
        strategy_str = joiner.join(conditions)
        
        target_input.setPlainText(strategy_str)
        # Optional: uncheck all after apply? No, user might want to edit slightly.

    def on_error(self, msg):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("🚀 執行回測 (Run)")
        self.progress_bar.hide()
        self.status_label.setText(f"❌ 錯誤: {msg}")
        self.status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
        QMessageBox.critical(self, "Backtest Error", msg)

    def add_to_monitor(self):
        code = self.input_code.text().strip()
        buy = self.input_buy.toPlainText().strip()
        sell = self.input_sell.toPlainText().strip()
        
        if not code: 
             QMessageBox.warning(self, "Error", "請輸入代號")
             return
             
        if not WatchlistManager or not StockDatabase:
            QMessageBox.warning(self, "Error", "Core modules missing")
            return
            
        try:
            # 1. Add to Watchlist (Ignore result if already exists)
            wm = WatchlistManager()
            wm.batch_add_entries([code])
            
            # 2. Update Strategy Config
            db = StockDatabase()
            raw = db.get_setting('strategies_config')
            try:
                config = json.loads(raw) if raw else {}
            except:
                config = {}
            
            # Use current input as config
            config[code] = {
                'active': True,
                'buy': buy,
                'sell': sell
            }
            
            db.set_setting('strategies_config', json.dumps(config))
            
            # 3. Refresh Watchlist Tab
            if self.main_window and hasattr(self.main_window, 'watchlist_tab') and self.main_window.watchlist_tab:
                # Reload Logic
                self.main_window.watchlist_tab.load_strategies()
                if hasattr(self.main_window.watchlist_tab, 'strat_worker'):
                    self.main_window.watchlist_tab.strat_worker.update_strategies(self.main_window.watchlist_tab.strategies_config)
                # Refresh table rows (re-init)
                self.main_window.watchlist_tab.load_watchlist_initial()
                
            QMessageBox.information(self, "Success", f"已將 {code} 加入監控清單並啟動策略!\n(請切換至監控分頁查看)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Deploy Failed: {str(e)}")

