
import sys
import os
import webbrowser
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QPushButton, QSplitter, 
    QProgressBar, QGridLayout, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QColor, QFont, QCursor

from jojo_trading.data_sources.jin10 import Jin10Scraper
from jojo_trading.analysis.news_ai import NewsAnalyzer
try:
    import yfinance as yf
except ImportError:
    yf = None

class PriceFetcher:
    @staticmethod
    def get_price_snapshot(ticker):
        """Fetch simplified price data for a single ticker"""
        if not yf: return None
        try:
            # Add suffix for TW stocks if needed (AI usually returns 2330.TW)
            # If AI returns just '2330', we might need to guess. 
            # But the current prompt asks for '2330.TW'.
            
            stock = yf.Ticker(ticker)
            # Get fast info
            info = stock.fast_info
            price = info.last_price
            prev_close = info.previous_close
            
            if price and prev_close:
                change_pct = ((price - prev_close) / prev_close) * 100
                return {
                    "price": price,
                    "change_pct": change_pct
                }
        except Exception as e:
            print(f"Price Fetch Fail ({ticker}): {e}")
        return None

    @staticmethod
    def enrich_news_items(items):
        """Process a list of news items and add price data to affected_stocks"""
        if not yf: return items
        
        # Collect all unique tickers to potentially batch (yfinance simple batching?)
        # For now, do simple loop as volume is low (5 items * 2-3 stocks)
        
        for item in items:
            analysis = item.get('analysis', {})
            affected = analysis.get('affected_stocks', [])
            for stock in affected:
                ticker = stock.get('ticker')
                if ticker:
                    data = PriceFetcher.get_price_snapshot(ticker)
                    if data:
                        stock['price_data'] = data
        return items

class NewsWorker(QThread):
    """Background thread to fetch and analyze news"""
    item_ready = Signal(dict) # Emit single item when analyzed
    stats_ready = Signal(dict) # Emit stats when done
    progress_update = Signal(str) # Status message
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.scraper = Jin10Scraper()
        self.analyzer = NewsAnalyzer()
        self.running = True

    def run(self):
        try:
            # 1. Fetch News
            self.progress_update.emit("Connecting to Jin10...")
            try:
                raw_news = self.scraper.fetch_latest_news(limit=5)
            except Exception as e:
                self.error_occurred.emit(f"News Fetch Error: {str(e)}")
                return # Stop if no news
                
            self.progress_update.emit(f"Fetched {len(raw_news)} items. Analyzing...")
            
            # 2. Batch Analyze (Cache + Batch Call)
            analyzed_news = []
            try:
                self.progress_update.emit(f"Analyzing {len(raw_news)} items (Batch/Cache)...")
                # This calls the NEW optimized method in news_ai.py
                analyzed_news = self.analyzer.analyze_impact_batch(raw_news)
            except Exception as e:
                 print(f"AI Analysis Failed: {e}")
                 # Fallback: Just show raw news without AI
                 analyzed_news = raw_news
                 self.progress_update.emit("AI Failed, showing raw news...")

            # 2.5 Fetch Prices (NEW) - Robust
            try:
                self.progress_update.emit("Fetching Market Prices...")
                analyzed_news = PriceFetcher.enrich_news_items(analyzed_news)
            except Exception as e:
                print(f"Price Fetch Warning: {e}")
                # Continue without prices
            
            # 3. Process & Emit
            bullish_count = 0
            bearish_count = 0
            total_heat = 0
            analyzed_count = 0
            top_sectors = {}

            for idx, item in enumerate(analyzed_news):
                if not self.running: break
                
                # Emit Item
                self.item_ready.emit(item)
                
                # Update Stats if analysis exists
                analysis_result = item.get('analysis', {})
                if analysis_result:
                    sent = analysis_result.get('sentiment', 'Neutral')
                    if sent == 'Bullish': bullish_count += 1
                    elif sent == 'Bearish': bearish_count += 1
                    
                    score = analysis_result.get('heat_score', 0)
                    if isinstance(score, int):
                        total_heat += score
                        analyzed_count += 1
                    
                    sectors = analysis_result.get('sectors', [])
                    for s in sectors:
                        top_sectors[s] = top_sectors.get(s, 0) + 1

            # Calculate Avg Heat
            avg_heat = int(total_heat / analyzed_count) if analyzed_count > 0 else 50
            
            stats = {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'heat_score': avg_heat,
                'top_sectors': sorted(top_sectors.items(), key=lambda x: x[1], reverse=True)[:3]
            }
            
            self.stats_ready.emit(stats)
            self.progress_update.emit("Done.")
            
        except Exception as e:
            self.error_occurred.emit(str(e)) # Global Catch
            self.progress_update.emit("Error.")

class NewsItemWidget(QFrame):
    def __init__(self, news_data):
        super().__init__()
        self.setFrameShape(QFrame.NoFrame)
        # Card Style with Shadow and Border
        self.setStyleSheet("""
            NewsItemWidget {
                background-color: #252526;
                border: 1px solid #3E3E42;
                border-radius: 8px;
                margin-bottom: 12px;
                margin-right: 12px;
            }
            NewsItemWidget:hover {
                background-color: #2D2D30;
                border: 1px solid #007ACC;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # --- Row 1: Badges + Time ---
        r1_layout = QHBoxLayout()
        r1_layout.setSpacing(10)
        
        # Analysis Data
        analysis = news_data.get('analysis', {})
        sentiment = analysis.get('sentiment', 'Neutral')
        heat = analysis.get('heat_score', 0)
        time_str = news_data.get('time', '')
        
        # Sentiment Badge
        # TW: Red=Bullish, Green=Bearish
        sent_bg = "#555"
        if sentiment == 'Bullish': sent_bg = "#D32F2F" # Red
        elif sentiment == 'Bearish': sent_bg = "#388E3C" # Green
        elif sentiment == 'RateLimit': sent_bg = "#F57F17" # Orange/Yellow Warning
        
        display_sent = sentiment
        if sentiment == 'RateLimit': display_sent = "⚠️ AI LIMIT"
        
        lbl_sent = QLabel(f" {display_sent} ")
        lbl_sent.setStyleSheet(f"""
            background-color: {sent_bg}; 
            color: white; 
            border-radius: 4px; 
            padding: 4px 8px; 
            font-weight: bold; 
            font-size: 12px;
        """)
        r1_layout.addWidget(lbl_sent)
        
        # Heat Badge
        heat_color = "#FFA726" if heat > 80 else "#B0BEC5"
        lbl_heat = QLabel(f" 🔥 {heat} ")
        lbl_heat.setStyleSheet(f"""
            color: {heat_color}; 
            border: 1px solid {heat_color};
            border-radius: 4px; 
            padding: 3px 6px; 
            font-size: 12px;
            font-weight: bold;
        """)
        r1_layout.addWidget(lbl_heat)
        
        r1_layout.addStretch()
        
        # Time Label
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("color: #9E9E9E; font-family: Consolas, monospace; font-size: 13px;")
        r1_layout.addWidget(lbl_time)
        
        layout.addLayout(r1_layout)
        
        # --- Row 2: Content Summary ---
        summary = analysis.get('summary', news_data.get('content', ''))
        lbl_content = QLabel(summary)
        lbl_content.setWordWrap(True)
        # Premium readable text
        lbl_content.setStyleSheet("color: #E0E0E0; font-size: 15px; line-height: 1.5; font-family: 'Segoe UI', sans-serif;")
        # Allow selection?
        lbl_content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(lbl_content)
        
        # --- Row 3: Supply Chain Tags (Pills) ---
        affected = analysis.get('affected_stocks', [])
        if affected:
            # Separator line
            # line = QFrame()
            # line.setFrameShape(QFrame.HLine)
            # line.setStyleSheet("color: #444;")
            # layout.addWidget(line)
            
            tags_container = QWidget()
            tags_layout = QHBoxLayout(tags_container)
            tags_layout.setContentsMargins(0, 5, 0, 0)
            tags_layout.setSpacing(6)
            
            lbl_tag_icon = QLabel("🔗")
            tags_layout.addWidget(lbl_tag_icon)
            
            for stock in affected:
                ticker = stock.get('ticker', '')
                role = stock.get('role', '')
                corr = stock.get('correlation_percentage', '')
                mkt = stock.get('market', '')
                
                # Style distinction
                # TW Stocks: Bright Blue pill
                # US Stocks: Purple pill (or standard)
                if mkt == 'TW':
                    bg = "#005a9e"
                    border = "#42a5f5"
                else: 
                    bg = "#424242"
                    border = "#757575"
                
                tag_text = f"<b>{ticker}</b> {role} <span style='font-size:10px; color:#ddd;'>{corr}%</span>"
                
                # Check for Price Data
                price_data = stock.get('price_data')
                if price_data:
                    p = price_data['price']
                    pct = price_data['change_pct']
                    color = "#FF5252" if pct < 0 else "#69F0AE" # Red for drop, Green for rise (TW style check?)
                    # Wait, TW: Red = Up, Green = Down. US: Green = Up, Red = Down.
                    # Let's stick to user preference or TW standard since app is TW focused?
                    # Previous code said: "TW: Red=Bullish". So Red is UP.
                    color = "#FF5252" if pct > 0 else "#69F0AE"
                    arrow = "▲" if pct > 0 else "▼"
                    
                    tag_text += f" <span style='color:{color}; font-weight:bold;'>{p:.1f} {arrow}{abs(pct):.1f}%</span>"

                tag = QLabel(tag_text)
                tag.setStyleSheet(f"""
                    background-color: {bg}; 
                    color: white; 
                    padding: 4px 8px; 
                    border: 1px solid {border};
                    border-radius: 12px;
                    font-size: 12px;
                """)
                tags_layout.addWidget(tag)
                
            tags_layout.addStretch()
            layout.addWidget(tags_container)

class NewsTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.setup_ui()
        
        # Start immediately
        QTimer.singleShot(300, self.refresh_news)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        # Use Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3E3E42;
            }
        """)
        
        # --- Left Panel: Dashboard Stats ---
        stats_widget = QWidget()
        stats_widget.setMinimumWidth(280)
        # Gradient Background for "Pro" feel
        stats_widget.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E; 
            }
        """)
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(10, 10, 20, 10)
        stats_layout.setSpacing(15)
        
        # Title
        lbl_title = QLabel("MARKET  INTELLIGENCE")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_title.setStyleSheet("color: #666; letter-spacing: 2px;")
        stats_layout.addWidget(lbl_title)
        
        # Heat Section
        heat_title = QLabel("AI 投資熱度")
        heat_title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        stats_layout.addWidget(heat_title)
        
        self.heat_bar = QProgressBar()
        self.heat_bar.setRange(0, 100)
        self.heat_bar.setValue(0)
        self.heat_bar.setTextVisible(True)
        self.heat_bar.setFixedHeight(25)
        self.heat_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #333;
                border-radius: 12px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                border-radius: 12px;
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #444, stop:1 #FFA726);
            }
        """)
        stats_layout.addWidget(self.heat_bar)
        
        # Cards for Counts
        grid = QGridLayout()
        grid.setSpacing(10)
        
        def make_stat_card(title, color):
            frame = QFrame()
            frame.setStyleSheet(f"background-color: #252526; border-left: 4px solid {color}; border-radius: 4px;")
            l = QVBoxLayout(frame)
            l.setContentsMargins(10, 10, 10, 10)
            t = QLabel(title)
            t.setStyleSheet("color: #AAA; font-size: 12px;")
            v = QLabel("---")
            v.setStyleSheet(f"color: white; font-size: 24px; font-weight: bold;")
            l.addWidget(t)
            l.addWidget(v)
            return frame, v
            
        card_bull, self.lbl_bull_count = make_stat_card("多頭 (Bullish)", "#D32F2F")
        card_bear, self.lbl_bear_count = make_stat_card("空頭 (Bearish)", "#388E3C")
        
        grid.addWidget(card_bull, 0, 0)
        grid.addWidget(card_bear, 0, 1)
        stats_layout.addLayout(grid)
        
        # Top Sectors
        stats_layout.addWidget(QLabel("🔥 熱門板塊"))
        self.lbl_sectors = QLabel("等待分析...")
        self.lbl_sectors.setStyleSheet("color: #CCC; font-size: 14px; line-height: 1.6; padding-left: 5px;")
        stats_layout.addWidget(self.lbl_sectors)
        
        stats_layout.addStretch()
        
        # Refresh Button
        self.btn_refresh = QPushButton("⚡  REFRESH")
        self.btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_refresh.setFixedHeight(40)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0098FF;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.btn_refresh.clicked.connect(self.refresh_news)
        stats_layout.addWidget(self.btn_refresh)
        
        splitter.addWidget(stats_widget)
        
        # --- Right Panel: News Feed ---
        feed_widget = QWidget()
        feed_widget.setStyleSheet("background-color: #1e1e1e;")
        feed_layout = QVBoxLayout(feed_widget)
        feed_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #2D2D30;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #1e1e1e;")
        self.vbox_news = QVBoxLayout(self.scroll_content)
        self.vbox_news.setAlignment(Qt.AlignTop)
        self.vbox_news.setContentsMargins(20, 20, 20, 20) # More padding
        
        self.scroll.setWidget(self.scroll_content)
        feed_layout.addWidget(self.scroll)
        
        splitter.addWidget(feed_widget)
        
        # Ratio
        splitter.setCollapsible(0, False) # Can't hide stats
        splitter.setStretchFactor(0, 3) # 30%
        splitter.setStretchFactor(1, 7) # 70%
        
        main_layout.addWidget(splitter)

    def refresh_news(self):
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("⏳ 分析中 (Analyzing)...")
        
        # Clear
        for i in reversed(range(self.vbox_news.count())): 
            w = self.vbox_news.itemAt(i).widget()
            if w: w.setParent(None)
            
        self.worker = NewsWorker()
        self.worker.item_ready.connect(self.on_item_ready)
        self.worker.stats_ready.connect(self.on_stats_ready)
        self.worker.progress_update.connect(self.on_progress)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_progress(self, msg):
        self.btn_refresh.setText(f"⏳ {msg}")

    def on_item_ready(self, item):
        w = NewsItemWidget(item)
        self.vbox_news.addWidget(w)
        
    def on_stats_ready(self, stats):
        heat = stats['heat_score']
        self.heat_bar.setValue(heat)
        
        # Color coding
        # >50 = Hot (Bullish?), or just momentum?
        # Let's use simple heatmap colors
        
        self.lbl_bull_count.setText(str(stats['bullish']))
        self.lbl_bear_count.setText(str(stats['bearish']))
        
        sectors = stats['top_sectors']
        if sectors:
            # Styled text
            html = ""
            for k, v in sectors:
                html += f"<div style='margin-bottom:4px;'>• <b style='color:#FFF;'>{k}</b> <span style='color:#888;'>({v})</span></div>"
            self.lbl_sectors.setText(html)
        else:
            self.lbl_sectors.setText("無顯著板塊")
            
    def on_error(self, msg):
        print(f"News Error: {msg}")
        
    def on_worker_finished(self):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("⚡  REFRESH")
