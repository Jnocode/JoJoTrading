
import sys
import os
import logging
import webbrowser
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QPushButton, QSplitter, 
    QProgressBar, QGridLayout, QMessageBox, QSizePolicy, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QColor, QFont, QCursor, QPainter, QLinearGradient

from jojo_trading.core.news_controller import NewsController
from jojo_trading.core.stock_database import StockDatabase

logger = logging.getLogger(__name__)

def get_sentiment_color(score):
    if score <= 20: return "#388E3C"
    elif score <= 40: return "#66BB6A"
    elif score <= 60: return "#9E9E9E"
    elif score <= 80: return "#F57C00"
    else: return "#D32F2F"

class SentimentRatioBar(QWidget):
    """A simple horizontal bar showing the ratio of Bullish vs Bearish news"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self._bull_pct = 50
        
    def set_ratio(self, bull_count, bear_count):
        total = bull_count + bear_count
        if total == 0:
            self._bull_pct = 50
        else:
            self._bull_pct = int((bull_count / total) * 100)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        radius = 4
        
        # Base background (Bearish / Green)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#388E3C"))
        painter.drawRoundedRect(0, 0, w, h, radius, radius)
        
        # Bullish overlay (Red)
        if self._bull_pct > 0:
            bull_w = int(w * (self._bull_pct / 100.0))
            painter.setBrush(QColor("#D32F2F"))
            # If 100%, round all corners, else only round left
            if self._bull_pct == 100:
                painter.drawRoundedRect(0, 0, w, h, radius, radius)
            else:
                painter.drawRoundedRect(0, 0, bull_w, h, radius, radius)
                # Fix right corners to be square so they align with the bear background
                painter.drawRect(bull_w - radius, 0, radius, h)
                
        # Center line
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRect(w // 2, 0, 2, h)
        
        painter.end()

def _get_news_id(item, fallback_index=0):
    """Stable ID: prefer item['id'] (injected from URL), else fallback."""
    nid = item.get('id')
    if nid:
        return str(nid)
    url = item.get('url', '')
    if '/detail/' in url:
        return url.split('/detail/')[-1]
    return f"idx_{fallback_index}"


class FetchWorker(QThread):
    """Background thread: fetch raw news only (no AI analysis)."""
    items_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, important_only=False, limit=20, since_dt=None):
        super().__init__()
        self.important_only = important_only
        self.limit = limit
        self.since_dt = since_dt
        self.controller = NewsController()

    def run(self):
        try:
            raw_news, error_msg = self.controller.fetch_raw_news(
                limit=self.limit, since_dt=self.since_dt, important_only=self.important_only
            )
            if error_msg:
                self.error_occurred.emit(error_msg)
            self.items_ready.emit(raw_news or [])
        except Exception as e:
            logger.error(f"[FetchWorker] Error fetching news: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
            self.items_ready.emit([])


class AnalyzeSequentialWorker(QThread):
    """Background thread: sequentially analyze multiple news items."""
    item_done = Signal(str, dict)  # (news_id, analyzed_item)
    all_done = Signal()
    error_occurred = Signal(str)

    def __init__(self, pending_items):
        super().__init__()
        self.pending_items = pending_items  # list of (news_id, item_data)
        self.controller = NewsController()
        self._is_cancelled = False

    def run(self):
        for news_id, item_data in self.pending_items:
            if self._is_cancelled:
                break
            try:
                result = self.controller.analyze_single_item(item_data)
                self.item_done.emit(news_id, result)
            except Exception as e:
                logger.error(f"[AnalyzeSequentialWorker] Failed to analyze {news_id}: {e}", exc_info=True)
                self.error_occurred.emit(f"Failed {news_id}: {str(e)}")
        self.all_done.emit()

    def cancel(self):
        self._is_cancelled = True

class MarketSummaryWorker(QThread):
    """Background thread: generate market summary from analyzed items."""
    done = Signal(dict, str)  # (stats, summary_text)
    error_occurred = Signal(str)

    def __init__(self, analyzed_items):
        super().__init__()
        self.analyzed_items = analyzed_items
        self.controller = NewsController()

    def run(self):
        try:
            stats = self.controller.calculate_dashboard_stats(self.analyzed_items)
            summary = self.controller.get_market_summary(self.analyzed_items)
            self.done.emit(stats, summary)
        except Exception as e:
            logger.error(f"[MarketSummaryWorker] Error generating summary: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

class AnalyzeItemWorker(QThread):
    """Background thread: analyze a single news item on demand."""
    done = Signal(str, dict)  # (news_id, analyzed_item)
    error_occurred = Signal(str)

    def __init__(self, news_id, item_data):
        super().__init__()
        self.news_id = news_id
        self.item_data = item_data
        self.controller = NewsController()

    def run(self):
        try:
            result = self.controller.analyze_single_item(self.item_data)
            self.done.emit(self.news_id, result)
        except Exception as e:
            logger.error(f"[AnalyzeItemWorker] Error analyzing {self.news_id}: {e}", exc_info=True)
            self.error_occurred.emit(str(e))


class NewsItemWidget(QFrame):
    """
    A single news card that supports two states:
    - Pending: shows raw content + 'AI 分析' button
    - Analyzed: shows sentiment badge, heat, AI summary, affected stocks
    """
    analyze_requested = Signal(str)  # Emits news_id when user clicks analyze

    def __init__(self, news_data, news_id="", pending=False):
        super().__init__()
        self.news_data = news_data
        self.news_id = news_id
        self.setFrameShape(QFrame.NoFrame)
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
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        
        # --- Row 1: Badges + Time ---
        r1_layout = QHBoxLayout()
        r1_layout.setSpacing(10)
        
        time_str = news_data.get('time', '')
        
        # Sentiment Badge (updatable)
        self.lbl_sent = QLabel()
        r1_layout.addWidget(self.lbl_sent)
        
        # Heat Badge (updatable)
        self.lbl_heat = QLabel()
        r1_layout.addWidget(self.lbl_heat)
        
        r1_layout.addStretch()
        
        # Time Label
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("color: #9E9E9E; font-family: Consolas, monospace; font-size: 13px;")
        r1_layout.addWidget(lbl_time)
        
        self.main_layout.addLayout(r1_layout)
        
        # --- Row 2: Raw Content (always visible) ---
        raw_content = news_data.get('data', {}).get('content', '') or news_data.get('content', '')
        lbl_raw = QLabel(raw_content)
        lbl_raw.setWordWrap(True)
        lbl_raw.setStyleSheet("color: #E0E0E0; font-size: 15px; line-height: 1.5; font-family: 'Segoe UI', sans-serif;")
        lbl_raw.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.main_layout.addWidget(lbl_raw)
        
        # --- Row 3: Analysis section (updatable) ---
        self.analysis_container = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_container)
        self.analysis_layout.setContentsMargins(0, 5, 0, 0)
        self.analysis_layout.setSpacing(6)
        self.main_layout.addWidget(self.analysis_container)
        
        # Set initial state
        if pending:
            self._show_pending()
        else:
            analysis = news_data.get('analysis', {})
            self._apply_analysis(analysis)

    def _show_pending(self):
        """Show AI analyze button instead of auto-analyzing."""
        self.lbl_sent.setVisible(False)
        self.lbl_heat.setVisible(False)
        
        self.btn_analyze = QPushButton("🤖 AI 分析")
        self.btn_analyze.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_analyze.setFixedHeight(28)
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #0E639C; color: white; border: none;
                border-radius: 4px; font-size: 12px; font-weight: bold;
                padding: 2px 12px; max-width: 120px;
            }
            QPushButton:hover { background-color: #1177BB; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_analyze.clicked.connect(self._on_analyze_clicked)
        self.analysis_layout.addWidget(self.btn_analyze)

    def _on_analyze_clicked(self):
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText("⏳ 分析中...")
        self.analyze_requested.emit(self.news_id)


    def update_analysis(self, analysis):
        """Called when AI analysis completes for this item."""
        # Clear analysis container
        while self.analysis_layout.count():
            child = self.analysis_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.btn_analyze = None
        self._apply_analysis(analysis)

    def _apply_analysis(self, analysis):
        """Apply analysis data to the badges and analysis section."""
        if not analysis:
            return
            
        sentiment = analysis.get('sentiment', 'Neutral')
        heat = analysis.get('heat_score', 0)
        
        # Update Sentiment Badge
        sent_bg = "#555"
        if sentiment == 'Bullish': sent_bg = "#D32F2F"
        elif sentiment == 'Bearish': sent_bg = "#388E3C"
        elif sentiment == 'RateLimit': sent_bg = "#F57F17"
        
        display_sent = sentiment
        if sentiment == 'RateLimit': display_sent = "⚠️ AI LIMIT"
        
        self.lbl_sent.setText(f" {display_sent} ")
        self.lbl_sent.setStyleSheet(
            f"background-color: {sent_bg}; color: white; border-radius: 4px; "
            f"padding: 4px 8px; font-weight: bold; font-size: 12px;"
        )
        self.lbl_sent.setVisible(True)
        # AI Sentiment Ratio (Instead of heat index)
        self.lbl_heat.setText(f" AI熱度: {heat} ")
        self.lbl_heat.setStyleSheet(
            f"color: white; background-color: #424242; border: 1px solid #757575; "
            f"border-radius: 4px; padding: 3px 6px; font-size: 12px; font-weight: bold;"
        )
        self.lbl_heat.setVisible(True)
        
        # AI Summary (below raw content)
        summary = analysis.get('summary', '')
        if summary:
            lbl_summary = QLabel(f"💡 {summary}")
            lbl_summary.setWordWrap(True)
            lbl_summary.setStyleSheet(
                "color: #B0BEC5; font-size: 13px; line-height: 1.4; "
                "font-family: 'Segoe UI', sans-serif; padding: 6px 8px; "
                "background-color: #2A2D2E; border-radius: 4px; border-left: 3px solid #007ACC;"
            )
            lbl_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.analysis_layout.addWidget(lbl_summary)
        
        # Affected Stocks Tags
        affected = analysis.get('affected_stocks', [])
        if affected:
            tags_widget = QWidget()
            tags_layout = QHBoxLayout(tags_widget)
            tags_layout.setContentsMargins(0, 2, 0, 0)
            tags_layout.setSpacing(6)
            
            lbl_tag_icon = QLabel("🔗")
            tags_layout.addWidget(lbl_tag_icon)
            
            for stock in affected:
                ticker = stock.get('ticker', '')
                role = stock.get('role', '')
                corr = stock.get('correlation_percentage', '')
                mkt = stock.get('market', '')
                
                if mkt == 'TW':
                    bg = "#005a9e"
                    border = "#42a5f5"
                else: 
                    bg = "#424242"
                    border = "#757575"
                
                tag_text = f"<b>{ticker}</b> {role} <span style='font-size:10px; color:#ddd;'>{corr}%</span>"
                
                price_data = stock.get('price_data')
                if price_data:
                    p = price_data['price']
                    pct = price_data['change_pct']
                    # TW: Red = Up, Green = Down
                    color = "#FF5252" if pct > 0 else "#69F0AE"
                    arrow = "▲" if pct > 0 else "▼"
                    tag_text += f" <span style='color:{color}; font-weight:bold;'>{p:.1f} {arrow}{abs(pct):.1f}%</span>"

                tag = QLabel(tag_text)
                tag.setStyleSheet(
                    f"background-color: {bg}; color: white; padding: 4px 8px; "
                    f"border: 1px solid {border}; border-radius: 12px; font-size: 12px;"
                )
                tags_layout.addWidget(tag)
                
            tags_layout.addStretch()
            self.analysis_layout.addWidget(tags_widget)


class NewsTab(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.fetch_worker = None
        self.controller = NewsController()
        self.analyze_workers = []  # Track active analyze workers
        self.summary_font_size = 13
        self.news_widgets = {}  # Track widgets by news_id
        self.news_raw_data = {}  # Track raw data by news_id for on-demand analysis
        self.news_analyzed_data = {} # Track analyzed data
        self.seen_ids = set()   # Avoid duplicates on incremental refresh
        
        # Load persisted settings
        try:
            self._db = StockDatabase()
            saved_important = self._db.get_setting("news_important_only", "False")
            self.important_only = saved_important == "True"
            saved_font = self._db.get_setting("news_summary_font_size", "13")
            self.summary_font_size = int(saved_font)
        except Exception:
            self._db = None
            self.important_only = False
            self.summary_font_size = 13
            
        self.is_loading_more = False
        
        self.setup_ui()
        
        # Apply persisted toggle state to button
        self.btn_important.setChecked(self.important_only)
        self.btn_important.setText("★ 僅顯示重要" if self.important_only else "☆ 僅顯示重要")
        
        # Auto-refresh timer
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._auto_fetch)
        refresh_sec = self._get_auto_refresh_sec()
        self._auto_timer.start(refresh_sec * 1000)
        
        # First fetch
        QTimer.singleShot(300, self._auto_fetch)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Use Splitter (使用者可自由拖曳分配左右面板比例)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(True)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3E3E42;
                margin: 0 1px;
            }
            QSplitter::handle:hover {
                background-color: #007ACC;
            }
            QSplitter::handle:pressed {
                background-color: #1177BB;
            }
        """)
        
        # --- Left Panel: Dashboard Stats ---
        stats_widget = QWidget()
        stats_widget.setMinimumSize(1, 1)

        stats_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        stats_widget.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E; 
            }
        """)
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        stats_layout.setSpacing(12)
        
        # Title
        lbl_title = QLabel("MARKET  INTELLIGENCE")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_title.setStyleSheet("color: #666; letter-spacing: 2px;")
        stats_layout.addWidget(lbl_title)
        
        # Sentiment Ratio Section
        heat_title = QLabel("⚖️ AI 新聞情緒分佈 (多空比例)")
        heat_title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        stats_layout.addWidget(heat_title)
        
        self.heat_gauge = SentimentRatioBar()
        stats_layout.addWidget(self.heat_gauge)
        
        # Gauge legend
        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(0, 0, 0, 0)
        lbl_bear_legend = QLabel("◀ 看空")
        lbl_bear_legend.setStyleSheet("color: #66BB6A; font-size: 10px;")
        lbl_bull_legend = QLabel("看多 ▶")
        lbl_bull_legend.setStyleSheet("color: #F57C00; font-size: 10px;")
        lbl_bull_legend.setAlignment(Qt.AlignRight)
        legend_layout.addWidget(lbl_bear_legend)
        legend_layout.addStretch()
        legend_layout.addWidget(lbl_bull_legend)
        stats_layout.addLayout(legend_layout)
        
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
            v = QLabel("—")
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
        lbl_sector_title = QLabel("📊 熱門板塊")
        lbl_sector_title.setStyleSheet("color: #AAA; font-size: 13px; font-weight: bold;")
        stats_layout.addWidget(lbl_sector_title)
        self.lbl_sectors = QLabel("👆 點擊「一鍵分析」後顯示")
        self.lbl_sectors.setStyleSheet("color: #777; font-size: 14px; line-height: 1.6; padding-left: 5px;")
        stats_layout.addWidget(self.lbl_sectors)
        
        # AI Market Summary Title & Controls
        title_layout = QHBoxLayout()
        lbl_summary_title = QLabel("🤖 AI 分析總覽")
        lbl_summary_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_layout.addWidget(lbl_summary_title)
        
        title_layout.addStretch()
        
        self.btn_generate_summary = QPushButton("📊 產出總覽")
        self.btn_generate_summary.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_generate_summary.setStyleSheet("background-color: #D4A017; color: #000; border: none; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
        self.btn_generate_summary.clicked.connect(self._generate_market_summary)
        title_layout.addWidget(self.btn_generate_summary)
        
        btn_font_dec = QPushButton("A-")
        btn_font_dec.setFixedSize(28, 24)
        btn_font_dec.setCursor(Qt.PointingHandCursor)
        btn_font_dec.setStyleSheet("background-color: #3E3E42; color: white; border: none; border-radius: 3px;")
        btn_font_dec.clicked.connect(self.decrease_summary_font)
        title_layout.addWidget(btn_font_dec)
        
        btn_font_inc = QPushButton("A+")
        btn_font_inc.setFixedSize(28, 24)
        btn_font_inc.setCursor(Qt.PointingHandCursor)
        btn_font_inc.setStyleSheet("background-color: #3E3E42; color: white; border: none; border-radius: 3px;")
        btn_font_inc.clicked.connect(self.increase_summary_font)
        title_layout.addWidget(btn_font_inc)
        
        title_layout.setContentsMargins(0, 10, 0, 0)
        stats_layout.addLayout(title_layout)
        
        self.lbl_summary = QLabel("👆 分析新聞後，點擊「📊 產出總覽」即可產生 AI 市場摘要")
        self.lbl_summary.setTextFormat(Qt.MarkdownText)
        self.lbl_summary.setOpenExternalLinks(True)
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_summary.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByMouse)
        self.update_summary_style()
        
        summary_scroll = QScrollArea()
        summary_scroll.setWidgetResizable(True)
        summary_scroll.setFrameShape(QFrame.NoFrame)
        summary_scroll.setWidget(self.lbl_summary)
        summary_scroll.setStyleSheet("background: transparent;")
        stats_layout.addWidget(summary_scroll, stretch=1)

        # Important-Only Toggle (value loaded in __init__)
        self.btn_important = QPushButton("☆ 僅顯示重要")
        self.btn_important.setToolTip("僅顯示金十快訊編輯精選的重大新聞")
        self.btn_important.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_important.setFixedHeight(32)
        self.btn_important.setCheckable(True)
        self.btn_important.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #AAA;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 12px;
                padding: 4px 12px;
            }
            QPushButton:checked {
                background-color: #D4A017;
                color: #000;
                border: 1px solid #FFD700;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #FFD700;
            }
        """)
        self.btn_important.clicked.connect(self._toggle_important)
        stats_layout.addWidget(self.btn_important)

        # Auto-refresh status label (replaces refresh button)
        refresh_sec = self._get_auto_refresh_sec()
        self.lbl_auto_status = QLabel(f"🔄 自動刷新中 ({refresh_sec}s)")
        self.lbl_auto_status.setStyleSheet(
            "color: #888; font-size: 11px; padding: 4px 0;"
        )
        stats_layout.addWidget(self.lbl_auto_status)
        
        # Error status bar (P2 #4)
        self.lbl_error_bar = QLabel("")
        self.lbl_error_bar.setStyleSheet(
            "color: #FFD54F; background-color: #3E2723; font-size: 11px; "
            "padding: 4px 8px; border-radius: 4px;"
        )
        self.lbl_error_bar.setVisible(False)
        self.lbl_error_bar.setWordWrap(True)
        stats_layout.addWidget(self.lbl_error_bar)
        self._error_timer = QTimer(self)
        self._error_timer.setSingleShot(True)
        self._error_timer.timeout.connect(lambda: self.lbl_error_bar.setVisible(False))
        
        splitter.addWidget(stats_widget)
        
        # --- Right Panel: News Feed ---
        feed_widget = QWidget()
        feed_widget.setMinimumSize(1, 1)

        feed_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        feed_widget.setStyleSheet("background-color: #1e1e1e;")
        feed_layout = QVBoxLayout(feed_widget)
        feed_layout.setContentsMargins(0, 0, 0, 0)
        
        feed_header_layout = QHBoxLayout()
        feed_header_layout.setContentsMargins(10, 10, 10, 5)
        feed_title = QLabel("📰 最新動態")
        feed_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        feed_header_layout.addWidget(feed_title)
        
        feed_header_layout.addStretch()
        
        self.chk_instant_analyze = QCheckBox("即時分析")
        self.chk_instant_analyze.setStyleSheet("color: #E0E0E0; font-weight: bold; margin-right: 10px;")
        self.chk_instant_analyze.toggled.connect(self._on_instant_analyze_toggled)
        try:
            if self._db:
                saved_instant = self._db.get_setting("news_instant_analyze", "False")
                self.chk_instant_analyze.blockSignals(True)
                self.chk_instant_analyze.setChecked(saved_instant == "True")
                self.chk_instant_analyze.blockSignals(False)
        except:
            pass
        feed_header_layout.addWidget(self.chk_instant_analyze)

        self.btn_analyze_all = QPushButton("⚡ 一鍵分析未處理")
        self.btn_analyze_all.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_analyze_all.setStyleSheet("background-color: #007ACC; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_analyze_all.clicked.connect(self._analyze_all_pending)
        feed_header_layout.addWidget(self.btn_analyze_all)
        
        self.btn_refresh = QPushButton("🔄 重新整理")
        self.btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_refresh.setStyleSheet("background-color: #3E3E42; color: #E0E0E0; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_refresh.clicked.connect(self._manual_refresh)
        feed_header_layout.addWidget(self.btn_refresh)
        
        feed_layout.addLayout(feed_header_layout)
        
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
        self.vbox_news.setContentsMargins(20, 20, 20, 20)
        
        # Loading spinner (P2 #5)
        self.lbl_loading = QLabel("⏳ 正在載入最新快訊...")
        self.lbl_loading.setAlignment(Qt.AlignCenter)
        self.lbl_loading.setStyleSheet("color: #888; font-size: 14px; padding: 40px 0;")
        self.vbox_news.addWidget(self.lbl_loading)
        
        self.scroll.setWidget(self.scroll_content)
        feed_layout.addWidget(self.scroll)
        
        # --- Load More Button ---
        self.btn_load_more = QPushButton("載入更多新聞")
        self.btn_load_more.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_load_more.setStyleSheet("""
            QPushButton {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                margin: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3E3E42;
                border: 1px solid #007ACC;
            }
        """)
        self.btn_load_more.clicked.connect(self._on_load_more)
        feed_layout.addWidget(self.btn_load_more)
        
        splitter.addWidget(feed_widget)
        
        # Ratio (使用者可自由拖曳調整)
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(splitter)

    def increase_summary_font(self):
        if self.summary_font_size < 24:
            self.summary_font_size += 1
            self.update_summary_style()
            try:
                if self._db: self._db.set_setting("news_summary_font_size", str(self.summary_font_size))
            except Exception: pass

    def decrease_summary_font(self):
        if self.summary_font_size > 10:
            self.summary_font_size -= 1
            self.update_summary_style()
            try:
                if self._db: self._db.set_setting("news_summary_font_size", str(self.summary_font_size))
            except Exception: pass

    def update_summary_style(self):
        self.lbl_summary.setStyleSheet(f"""
            background-color: #2D2D30;
            color: #E0E0E0; 
            font-size: {self.summary_font_size}px; 
            line-height: 1.5; 
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #3E3E42;
        """)

    def _get_news_settings(self):
        try:
            scope_type = self._db.get_setting("news_scope_type", "則")
            scope_value = int(self._db.get_setting("news_scope_value", "20"))
        except Exception:
            scope_type = "則"
            scope_value = 20
        return scope_type, scope_value

    def _get_auto_refresh_sec(self):
        try:
            if self._db:
                return int(self._db.get_setting("news_auto_refresh", "60"))
        except:
            pass
        return 60

    def _get_load_amount(self):
        try:
            return int(self._db.get_setting("news_load_amount", "5"))
        except:
            return 5

    def _auto_fetch(self):
        """Auto-fetch latest news (called by timer and on init)."""
        if self.fetch_worker and self.fetch_worker.isRunning():
            return  # Skip if already fetching
            
        scope_type, scope_value = self._get_news_settings()
        limit = 20
        since_dt = None
        
        if "小時" in scope_type:
            since_dt = datetime.now() - timedelta(hours=scope_value)
        elif "天" in scope_type:
            since_dt = datetime.now() - timedelta(days=scope_value)
        else:
            limit = scope_value
        
        # Update timer if setting changed
        refresh_sec = self._get_auto_refresh_sec()
        if self._auto_timer.interval() != refresh_sec * 1000:
            self._auto_timer.setInterval(refresh_sec * 1000)
            
        self.is_loading_more = False
        self.lbl_auto_status.setText("🔄 抓取中...")
        self.fetch_worker = FetchWorker(important_only=self.important_only, limit=limit, since_dt=since_dt)
        self.fetch_worker.items_ready.connect(self._on_items_fetched)
        self.fetch_worker.error_occurred.connect(self.on_error)
        self.fetch_worker.start()

    def _on_load_more(self):
        """Fetch older news by increasing the limit beyond currently seen items."""
        if self.fetch_worker and self.fetch_worker.isRunning():
            return
            
        self.is_loading_more = True
        self.btn_load_more.setText("⏳ 載入中...")
        self.btn_load_more.setEnabled(False)
        
        # To get older items, we bypass time limits and just fetch N items,
        # where N is our current loaded count + the load amount.
        target_limit = len(self.seen_ids) + self._get_load_amount()
        if target_limit < 10: target_limit = 10
        
        self.fetch_worker = FetchWorker(important_only=self.important_only, limit=target_limit, since_dt=None)
        self.fetch_worker.items_ready.connect(self._on_items_fetched)
        self.fetch_worker.error_occurred.connect(self.on_error)
        self.fetch_worker.start()

    def _on_items_fetched(self, items):
        """Incremental update: Check cache directly to skip pending state for cached items."""
        now_str = datetime.now().strftime("%H:%M:%S")
        
        new_items = []
        for i, item in enumerate(items):
            news_id = _get_news_id(item, i)
            if news_id not in self.seen_ids:
                new_items.append((news_id, item))
                self.seen_ids.add(news_id)
                self.news_raw_data[news_id] = item

        # Refresh Load More Button
        if hasattr(self, 'btn_load_more'):
            self.btn_load_more.setEnabled(True)
            self.btn_load_more.setText("載入更多新聞")

        # Hide loading spinner once items arrive
        if hasattr(self, 'lbl_loading') and self.lbl_loading.isVisible():
            self.lbl_loading.setVisible(False)
        
        if not new_items:
            self.lbl_auto_status.setText(f"🔄 上次更新 {now_str}")
            self.is_loading_more = False
            return
            
        # For auto-refresh (new items), reverse the list to prepend newest at the top correctly
        if not self.is_loading_more:
            new_items.reverse()
            
        for news_id, item in new_items:
            # CHECK CACHE
            cached_result = self.controller.analyzer.cache_manager.get_analysis(news_id)
            is_valid_cache = False
            if cached_result:
                summary = cached_result.get('summary', '')
                if "無法分析" not in summary and "JSON 格式錯誤" not in summary and "AI Error" not in summary:
                    is_valid_cache = True
                    
            if is_valid_cache:
                item['analysis'] = cached_result
                self.news_analyzed_data[news_id] = item
                w = NewsItemWidget(item, news_id=news_id, pending=False)
            else:
                w = NewsItemWidget(item, news_id=news_id, pending=True)
                w.analyze_requested.connect(self._request_analyze)
                
            self.news_widgets[news_id] = w
            
            # Place widget
            if self.is_loading_more:
                self.vbox_news.addWidget(w)
            else:
                self.vbox_news.insertWidget(0, w)
        
        status = f"🔄 上次更新 {now_str}"
        if new_items:
            status += f" (+{len(new_items)} 則新聞)"
        self.lbl_auto_status.setText(status)
        self.is_loading_more = False
        
        # Update dashboard if any cached items were loaded
        self._update_realtime_stats()

        # Auto-analyze if Instant Analysis is enabled
        if hasattr(self, 'chk_instant_analyze') and self.chk_instant_analyze.isChecked() and not self.is_loading_more:
            self._analyze_all_pending()

    def _request_analyze(self, news_id):
        """On-demand: user clicked AI analyze on a specific card."""
        item_data = self.news_raw_data.get(news_id)
        if not item_data:
            return
        worker = AnalyzeItemWorker(news_id, item_data)
        worker.done.connect(self._on_item_analyzed)
        worker.error_occurred.connect(self.on_error)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self.analyze_workers.append(worker)
        worker.start()

    def _analyze_all_pending(self):
        pending_items = []
        for news_id, w in self.news_widgets.items():
            if news_id not in self.news_analyzed_data and getattr(w, 'btn_analyze', None) and w.btn_analyze.isEnabled():
                pending_items.append((news_id, self.news_raw_data[news_id]))
                w.btn_analyze.setEnabled(False)
                w.btn_analyze.setText("⏳ 佇列中...")
        
        if not pending_items:
            QMessageBox.information(self, "提示", "目前沒有未分析的新聞。")
            return
            
        self.btn_analyze_all.setText("⏳ 批次分析中...")
        self.btn_analyze_all.setEnabled(False)
        
        worker = AnalyzeSequentialWorker(pending_items)
        worker.item_done.connect(self._on_item_analyzed)
        worker.all_done.connect(lambda: self._on_analyze_all_done(worker))
        worker.error_occurred.connect(self.on_error)
        self.analyze_workers.append(worker)
        worker.start()

    def _on_analyze_all_done(self, worker):
        self.btn_analyze_all.setText("⚡ 一鍵分析未處理")
        self.btn_analyze_all.setEnabled(True)
        self._cleanup_worker(worker)

    def _generate_market_summary(self):
        analyzed_items = list(self.news_analyzed_data.values())
                
        if not analyzed_items:
            QMessageBox.information(self, "提示", "請先分析至少一則新聞，才能產出總覽。")
            return
            
        self.btn_generate_summary.setText("⏳ 產生中...")
        self.btn_generate_summary.setEnabled(False)
        self.lbl_summary.setText("🤖 正在統合分析已處理的新聞，請稍候...")
        
        worker = MarketSummaryWorker(analyzed_items)
        worker.done.connect(self._on_summary_done)
        worker.error_occurred.connect(self._on_summary_error)
        self.summary_worker = worker 
        worker.start()

    def _on_summary_done(self, stats, summary):
        self.btn_generate_summary.setText("📊 產出總覽")
        self.btn_generate_summary.setEnabled(True)
        
        self.lbl_bull_count.setText(str(stats.get('bullish', 0)))
        self.lbl_bear_count.setText(str(stats.get('bearish', 0)))
        self._set_heat_bar_score(stats.get('bullish', 0), stats.get('bearish', 0))
        sectors = [f"{s} ({c})" for s, c in stats.get('top_sectors', [])]
        self.lbl_sectors.setText("、".join(sectors) if sectors else "無集中板塊")
        
        self.lbl_summary.setText(summary)

    def _on_summary_error(self, err):
        self.btn_generate_summary.setText("📊 產出總覽")
        self.btn_generate_summary.setEnabled(True)
        self.lbl_summary.setText(f"❌ 總覽產生失敗: {err}")
        self.on_error(err)

    def _on_item_analyzed(self, news_id, analyzed_item):
        """Single item analysis complete: update its card."""
        self.news_analyzed_data[news_id] = analyzed_item
        w = self.news_widgets.get(news_id)
        if w:
            analysis = analyzed_item.get('analysis', {})
            w.update_analysis(analysis)
        self._update_realtime_stats()

    def _update_realtime_stats(self):
        analyzed_items = list(self.news_analyzed_data.values())
        if not analyzed_items:
            return
            
        controller = NewsController()
        try:
            stats = controller.calculate_dashboard_stats(analyzed_items)
            self.lbl_bull_count.setText(str(stats.get('bullish', 0)))
            self.lbl_bear_count.setText(str(stats.get('bearish', 0)))
            self._set_heat_bar_score(stats.get('bullish', 0), stats.get('bearish', 0))
            sectors = [f"{s} ({c})" for s, c in stats.get('top_sectors', [])]
            self.lbl_sectors.setText("、".join(sectors) if sectors else "無集中板塊")
        except Exception as e:
            logger.error(f"Error updating realtime stats: {e}", exc_info=True)

    def _set_heat_bar_score(self, bull_count: int, bear_count: int):
        self.heat_gauge.set_ratio(bull_count, bear_count)

    def _cleanup_worker(self, worker):
        if worker in self.analyze_workers:
            self.analyze_workers.remove(worker)

    def _manual_refresh(self):
        """User clicked refresh: clear all and re-fetch."""
        self._clear_all()
        self._auto_fetch()

    def _toggle_important(self, checked):
        """Toggle important-only: switches data source and refreshes."""
        self.important_only = checked
        self.btn_important.setText("★ 僅顯示重要" if checked else "☆ 僅顯示重要")
        # Persist state
        try:
            if self._db:
                self._db.set_setting("news_important_only", str(checked))
        except Exception:
            pass
        # Full clear + re-fetch with new data source
        self._clear_all()
        self._auto_fetch()

    def _on_instant_analyze_toggled(self, checked):
        if checked:
            provider = "Gemini"
            try:
                if self._db:
                    provider = self._db.get_setting("ai_provider", "Gemini")
            except:
                pass
            
            if provider == "Ollama":
                reply = QMessageBox.warning(
                    self,
                    "警告：本地模型運算",
                    "您目前設定的 AI Provider 為本地模型 (Ollama)。\n"
                    "開啟「即時分析」將會在每次抓取到新新聞時，自動調用本地資源進行運算。\n\n"
                    "若新聞數量過多，可能會導致系統嚴重卡頓或資源耗盡。\n"
                    "您確定要開啟此功能嗎？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    self.chk_instant_analyze.blockSignals(True)
                    self.chk_instant_analyze.setChecked(False)
                    self.chk_instant_analyze.blockSignals(False)
                    return
                    
        try:
            if self._db:
                self._db.set_setting("news_instant_analyze", str(checked))
        except:
            pass
            
        # If enabled and we have pending news, immediately analyze
        if checked:
            self._analyze_all_pending()


    def _clear_all(self):
        """Clear all cards and tracking state."""
        self.news_widgets = {}
        self.news_raw_data = {}
        self.news_analyzed_data = {}
        self.seen_ids = set()
        for i in reversed(range(self.vbox_news.count())):
            w = self.vbox_news.itemAt(i).widget()
            if w:
                w.setParent(None)

    def on_error(self, msg):
        logger.error(f"News Error UI Signal: {msg}")
        # Show error in status bar for 5 seconds
        if hasattr(self, 'lbl_error_bar'):
            self.lbl_error_bar.setText(f"⚠️ {msg}")
            self.lbl_error_bar.setVisible(True)
            self._error_timer.start(5000)

