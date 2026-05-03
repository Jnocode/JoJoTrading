
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QGridLayout, QProgressBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
import json
from datetime import datetime
from jojo_trading.core.stock_database import StockDatabase
from PySide6.QtCore import Qt, QTimer, QThread, Signal

class MarketDataWorker(QThread):
    finished = Signal(dict)
    
    def run(self):
        try:
            import yfinance as yf
            # Tickers: TWSE, S&P500, Nasdaq, SOX, VIX, TSMC
            tickers = {
                'TAIEX': '^TWII',
                'S&P 500': '^GSPC',
                'NASDAQ': '^IXIC',
                'SOX': '^SOX',
                'VIX': '^VIX',
                'TSMC': '2330.TW'
            }
            
            data = {}
            for name, symbol in tickers.items():
                try:
                    t = yf.Ticker(symbol)
                    # Use fast info or history
                    hist = t.history(period="2d")
                    if len(hist) >= 1:
                        close = hist.iloc[-1]['Close']
                        prev = hist.iloc[-2]['Close'] if len(hist) > 1 else close
                        change = ((close - prev) / prev) * 100
                        data[name] = {'price': close, 'change': change}
                except:
                    data[name] = {'price': 0, 'change': 0}
            
            self.finished.emit(data)
        except Exception as e:
            print(f"Market Data Error: {e}")
            self.finished.emit({})

class DashboardTab(QWidget):
    """
    Account Overview Dashboard (Futures Risk + Settlement)
    """
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.market_worker = None
        self.setup_ui()
        
        # Auto Refresh Timer (10s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(10000)
        
        # Initial Refresh
        QTimer.singleShot(1000, self.refresh_data)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("📊 Account Dashboard (戰情室)")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        main_layout.addWidget(title)
        
        # content Layout (Grid 2 columns)
        content_layout = QHBoxLayout()
        
        # --- Card 0: Market Overview (New) ---
        self.card_market = self.create_card("Market Overview (全球行情)")
        m_layout = QVBoxLayout(self.card_market)
        
        # Market Grid
        m_grid = QGridLayout()
        self.market_labels = {}
        row = 0
        col = 0
        for name in ['TAIEX', 'TSMC', 'S&P 500', 'NASDAQ', 'SOX', 'VIX']:
            # Name
            l_name = QLabel(name)
            l_name.setStyleSheet("color: #CCC; font-size: 13px;")
            m_grid.addWidget(l_name, row, col)
            
            # Price/Change
            l_val = QLabel("---")
            l_val.setFont(QFont("Consolas", 14, QFont.Bold))
            l_val.setStyleSheet("color: white;")
            l_val.setAlignment(Qt.AlignmentFlag.AlignRight)
            m_grid.addWidget(l_val, row, col+1)
            
            self.market_labels[name] = l_val
            
            col += 2
            if col >= 4: # 2 items per row
                col = 0
                row += 1
        
        m_layout.addLayout(m_grid)
        m_layout.addStretch()
        content_layout.addWidget(self.card_market)

        # --- Card 1: Futures Risk ---
        self.card_futures = self.create_card("Futures Risk (期貨權益)")
        f_layout = QVBoxLayout(self.card_futures)
        
        # Equity
        self.lbl_equity = QLabel("Equity: -")
        self.lbl_equity.setFont(QFont("Segoe UI", 14))
        self.lbl_equity.setStyleSheet("color: white;")
        f_layout.addWidget(self.lbl_equity)
        
        # Risk Ratio
        self.lbl_risk = QLabel("Risk Ratio: -%")
        self.lbl_risk.setFont(QFont("Segoe UI", 12))
        f_layout.addWidget(self.lbl_risk)
        
        # Progress Bar for Risk
        self.risk_bar = QProgressBar()
        self.risk_bar.setRange(0, 200) # Assuming ratio%
        self.risk_bar.setValue(0)
        self.risk_bar.setTextVisible(False)
        self.risk_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #333;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        f_layout.addWidget(self.risk_bar)
        
        # Margin Details
        self.lbl_margin_avail = QLabel("Available: -")
        self.lbl_margin_avail.setStyleSheet("color: #aaa;")
        f_layout.addWidget(self.lbl_margin_avail)
        
        f_layout.addStretch()
        content_layout.addWidget(self.card_futures)

        # --- Card 2: Cash Settlement ---
        self.card_cash = self.create_card("Cash Settlement (交割試算)")
        c_layout = QVBoxLayout(self.card_cash)
        
        self.lbl_t1 = QLabel("T+1: -")
        self.lbl_t1.setFont(QFont("Segoe UI", 12))
        c_layout.addWidget(self.lbl_t1)
        
        self.lbl_t2 = QLabel("T+2: -")
        self.lbl_t2.setFont(QFont("Segoe UI", 12))
        c_layout.addWidget(self.lbl_t2)
        
        self.lbl_total_pay = QLabel("Total Net: -")
        self.lbl_total_pay.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_total_pay.setStyleSheet("color: #aaa;")
        c_layout.addWidget(self.lbl_total_pay)
        
        c_layout.addStretch()
        content_layout.addWidget(self.card_cash)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()

    def create_card(self, title_text):
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 10px;
                border: 1px solid #3d3d3d;
            }
        """)
        # Specific layout handling usually done by caller content layout, 
        # but here we return widget to add to layout.
        # Ideally we should wrapper content inside.
        return card



    def refresh_data(self):
        # 0. Market Data
        if not getattr(self, 'market_worker', None):
            self.market_worker = MarketDataWorker()
            self.market_worker.finished.connect(self.on_market_data)
        
        if not self.market_worker.isRunning():
            try:
                self.market_worker.start()
            except: pass

        connector = getattr(self.main, 'connector', None)
        if not connector or not connector.is_connected:
            self.lbl_equity.setText("Equity: (Disconnect)")
            return

        db = StockDatabase()
        
        # --- 0. Market Indices ---
        try:
             # TSE001 (Taipei Exchange), OTC101 (TPEx) - Codes depend on Shioaji version/API
             # Snapshots: TSE001, OTC101
             indices = connector.get_snapshot('TSE001') # Index handling might differ
             if not indices:
                 # Fallback attempt if simple string lookup fails (usually list of contracts needed)
                 # Mock for MVP if explicit index contract lookup is complex without Contracts object
                 pass
             else:
                 # Update TAIEX
                 # Note: Real implementation requires fetching Index Contracts specifically
                 pass
                 
             # For MVP: If we can't easily get Index Snapshot without Contracts, 
             # let's try to get it if possible, or leave placeholders.
             # Actually, Shioaji snapshots take Contracts.
             pass
        except: pass
        
        # --- 1. Futures (Margin) ---
        margin_data = None
        try:
            margin = connector.get_account_margin() # returns dict
            # Check validity: Shioaji often returns 0 if no data/holiday/maintenance
            # We consider it valid if equity != 0
            if margin and margin.get('equity', 0) != 0:
                margin_data = margin
                # Save to Cache
                db.set_setting('dashboard_margin_cache', json.dumps(margin))
                db.set_setting('dashboard_margin_ts', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            else:
                # API returned 0 or empty -> Try Cache
                cached = db.get_setting('dashboard_margin_cache')
                if cached:
                    margin_data = json.loads(cached)
                    ts = db.get_setting('dashboard_margin_ts')
                    print(f"Using Cached Margin from {ts}")
        except Exception as e:
            print(f"Dashboard Futures Error: {e}")
            # Try Cache on Error
            try:
                cached = db.get_setting('dashboard_margin_cache')
                if cached: margin_data = json.loads(cached)
            except: pass

        # Display Margin
        if margin_data:
            equity = margin_data.get('equity', 0)
            risk = margin_data.get('risk_ratio', 0) * 100
            avail = margin_data.get('available_margin', 0)
            
            # Check if this is cached data (by checking if it matches what we just got from API?)
            # Actually, simplify: If we fell back to cache, we might want to show a label.
            # But user just said "Should use cache", implied functionality.
            # I will add a small marker if it's potentially stale?
            # User requirement: "應該要以收盤讀取的資料為暫存" (Should use cached data from close)
            # So just displaying it is fine.
            
            self.lbl_equity.setText(f"Equity: ${equity:,.0f}")
            self.lbl_risk.setText(f"Risk Ratio: {risk:.1f}%")
            self.lbl_margin_avail.setText(f"Available: ${avail:,.0f}")
            
            # Colors
            self.risk_bar.setValue(int(min(risk, 200)))
            if risk < 100:
                self.lbl_risk.setStyleSheet("color: #EF5350; font-weight: bold;")
                self.risk_bar.setStyleSheet(self.risk_bar.styleSheet().replace("#4CAF50", "#EF5350").replace("#FFA726", "#EF5350"))
            elif risk < 135:
                 self.lbl_risk.setStyleSheet("color: #FFA726; font-weight: bold;")
                 self.risk_bar.setStyleSheet(self.risk_bar.styleSheet().replace("#4CAF50", "#FFA726").replace("#EF5350", "#FFA726"))
            else:
                 self.lbl_risk.setStyleSheet("color: #66bb6a; font-weight: bold;")
                 self.risk_bar.setStyleSheet(self.risk_bar.styleSheet().replace("#FFA726", "#4CAF50").replace("#EF5350", "#4CAF50"))
        else:
             # Really no data
             self.lbl_equity.setText("Equity: -")

        # --- 2. Settlement (Cash) ---
        settle_data = []
        try:
            settlements = connector.get_settlements()
            if settlements:
                settle_data = settlements
                # Save Cache
                db.set_setting('dashboard_settle_cache', json.dumps(settlements))
                db.set_setting('dashboard_settle_ts', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            else:
                # Try Cache
                cached = db.get_setting('dashboard_settle_cache')
                if cached:
                    settle_data = json.loads(cached)
        except Exception as e:
            print(f"Dashboard Settle Error: {e}")
            try:
                cached = db.get_setting('dashboard_settle_cache')
                if cached: settle_data = json.loads(cached)
            except: pass

        # Display Settlement
        t1_amt = 0
        t2_amt = 0
        if settle_data:
             # Sort
             settle_data.sort(key=lambda x: x.get('date', ''))
             if len(settle_data) > 0:
                 t1_amt = settle_data[0].get('amount', 0)
                 self.lbl_t1.setText(f"T+1 ({settle_data[0]['date']}): {t1_amt:,.0f}")
             if len(settle_data) > 1:
                 t2_amt = settle_data[1].get('amount', 0)
                 self.lbl_t2.setText(f"T+2 ({settle_data[1]['date']}): {t2_amt:,.0f}")
        else:
             self.lbl_t1.setText("T+1: 0")
             self.lbl_t2.setText("T+2: 0")

        total = t1_amt + t2_amt
        self.lbl_total_pay.setText(f"Net: {total:,.0f}")
        if total < 0:
            self.lbl_total_pay.setStyleSheet("color: #66bb6a; font-weight: bold;") 
        else:
            self.lbl_total_pay.setStyleSheet("color: #ff6b6b; font-weight: bold;")

    def on_market_data(self, data):
        for name, info in data.items():
            if name in self.market_labels:
                lbl = self.market_labels[name]
                price = info['price']
                change = info['change']
                
                color = "#F44336" if change > 0 else "#4CAF50" # TW: Red is Up
                if name in ['S&P 500', 'NASDAQ', 'SOX', 'VIX']:
                    color = "#4CAF50" if change > 0 else "#F44336" # US: Green is Up
                
                # Special color for VIX
                if name == 'VIX': color = "#F44336" if change > 0 else "#4CAF50"

                lbl.setText(f"{price:,.2f} ({change:+.2f}%)")
                lbl.setStyleSheet(f"color: {color}; font-family: Consolas; font-weight: bold; font-size: 13px;")
