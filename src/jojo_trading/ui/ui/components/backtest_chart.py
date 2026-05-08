
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QLabel

# Safe Import for WebEngine
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False
    print("⚠️ QtWebEngineWidgets not available. Charts will be disabled.")
    
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from PySide6.QtGui import QColor
import tempfile
import os
import re

class BacktestChart(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = QHBoxLayout()
        self.toolbar.addWidget(QLabel("⏳ 時間級別 (Timeframe):"))
        self.combo_tf = QComboBox()
        self.combo_tf.addItems(["Daily (日)", "Weekly (週)", "Monthly (月)"])
        self.combo_tf.currentIndexChanged.connect(self.update_plot)
        self.toolbar.addWidget(self.combo_tf)
        self.toolbar.addStretch()
        
        self.layout.addLayout(self.toolbar)
        
        if WEB_ENGINE_AVAILABLE:
            try:
                self.web_view = QWebEngineView()
                self.web_view.page().setBackgroundColor(QColor('#1E1E1E'))
                self.web_view.setHtml('<body style="background-color: #1E1E1E; color: #888; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif;">等待載入技術線圖... (Waiting for chart data)</body>')
                self.layout.addWidget(self.web_view)
            except Exception as e:
                print(f"⚠️ WebEngineView initialization failed: {e}")
                self.web_view = None
                lbl = QLabel("❌ Charts Not Available (WebEngine Error)")
                lbl.setStyleSheet("color: orange; font-size: 16px; font-weight: bold; padding: 20px;")
                self.layout.addWidget(lbl)
        else:
            self.web_view = None
            lbl = QLabel("❌ Charts Not Available (WebEngine Missing)")
            lbl.setStyleSheet("color: red; font-size: 16px; font-weight: bold; padding: 20px;")
            self.layout.addWidget(lbl)
        
        self.raw_df = None
        self.trades = []

    def plot(self, df: pd.DataFrame, trades: list):
        """
        Store data and render initial plot.
        """
        self.raw_df = df
        self.trades = trades
        self.update_plot()

    def update_plot(self):
        if self.raw_df is None or self.raw_df.empty:
            return
            
        tf_map = {0: 'D', 1: 'W', 2: 'M'}
        tf = tf_map[self.combo_tf.currentIndex()]
        
        # Resample Data if needed
        if tf == 'D':
            plot_df = self.raw_df.copy()
        else:
            plot_df = self._resample(self.raw_df, tf)
            
        self._render_plotly(plot_df, self.trades)

    def _resample(self, df, rule):
        # Ensure date index
        d = df.set_index('date')
        
        # Resample OHLCV
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Also resample Indicators (MA*) using 'last' value approximation or mean?
        # Usually Mean for MA is technically correct but if we visualize Monthly MA on Monthly Candle,
        # we strictly should re-calculate MA on Monthly Close.
        # But for simple visualization, let's take 'last' of the MA value to show where it ended up.
        for col in df.columns:
            if col not in agg_dict and col != 'date':
                 agg_dict[col] = 'last'
                 
        res = d.resample(rule).agg(agg_dict).dropna()
        return res.reset_index()

    def _render_plotly(self, df, trades):
        # Create Subplots
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, subplot_titles=('Price', 'Volume'),
                            row_width=[0.2, 0.7])

        # 1. Candlestick
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K-Line',
            increasing_line_color='#FF3333', increasing_fillcolor='#FF3333',
            decreasing_line_color='#00FF00', decreasing_fillcolor='#00FF00'
        ), row=1, col=1)

        # 2. Price Overlay Indicators
        # 僅繪製真正價格相關技術指標，避免 Dealer_Buy 等籌碼欄位拉爆價格軸。
        colors = ['orange', 'purple', 'blue', 'brown']
        ma_cols = self._get_price_overlay_columns(df)
        for idx, col in enumerate(ma_cols):
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df[col],
                line=dict(width=1.5, color=colors[idx % len(colors)]),
                name=col
            ), row=1, col=1)

        # 3. Trade Markers
        buy_x, buy_y = [], []
        sell_x, sell_y = [], []
        
        for t in trades:
            # For Weekly/Monthly, we need to map exact trade date to nearest candle date?
            # Or just plot on exact date (Plotly handles it if X-axis is time)
            if t['type'] == 'buy':
                buy_x.append(t['date'])
                buy_y.append(t['price'])
            elif t['type'] == 'sell':
                sell_x.append(t['date'])
                sell_y.append(t['price'])

        if buy_x:
            fig.add_trace(go.Scatter(
                x=buy_x, y=buy_y,
                mode='markers',
                marker=dict(symbol='triangle-up', size=12, color='#00FF00', line=dict(width=2, color='black')),
                name='Buy Signal'
            ), row=1, col=1)
            
        if sell_x:
            fig.add_trace(go.Scatter(
                x=sell_x, y=sell_y,
                mode='markers',
                marker=dict(symbol='triangle-down', size=12, color='#FF0000', line=dict(width=2, color='black')),
                name='Sell Signal'
            ), row=1, col=1)

        # 4. Volume
        vol_colors = ['#FF3333' if c >= o else '#00FF00' for c, o in zip(df['close'], df['open'])]
        fig.add_trace(go.Bar(
            x=df['date'], y=df['volume'],
            name='Volume',
            marker_color=vol_colors
        ), row=2, col=1)

        # Layout Settings
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            xaxis_rangeslider_visible=False,
            height=600,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified'
        )

        fig.update_yaxes(title_text='Price', row=1, col=1)
        fig.update_yaxes(title_text='Volume', row=2, col=1)

        # Save to temp HTML and Load (Embed Plotly JS to avoid blank screens due to slow CDN)
        raw_html = fig.to_html(include_plotlyjs=True)
        
        if self.web_view:
             from PySide6.QtCore import QUrl
             import uuid
             
             # QWebEngineView.setHtml() has a size limit which drops large strings silently.
             # Since include_plotlyjs=True creates a >3MB string, we must save to a temp file and load via URL.
             temp_dir = tempfile.gettempdir()
             temp_filename = f"jojo_chart_{uuid.uuid4().hex}.html"
             temp_filepath = os.path.join(temp_dir, temp_filename)
             
             with open(temp_filepath, 'w', encoding='utf-8') as f:
                 f.write(raw_html)
                 
             self.web_view.setUrl(QUrl.fromLocalFile(temp_filepath))
        else:
             print("Skipping Chart Render: WebEngine not available")

    def _get_price_overlay_columns(self, df: pd.DataFrame) -> list[str]:
        """
        挑出可疊在價格圖上的技術指標欄位。
        避免把 Foreign_Buy / Dealer_Buy / Revenue 等非價格欄位畫進來。
        """
        indicator_patterns = [
            r"^MA\d+$",
            r"^EMA\d+$",
            r"^SMA\d+$",
            r"^WMA\d+$",
            r"^VWAP$",
            r"^BB_(UPPER|MID|LOWER)$",
            r"^(DIF|DEA|MACD)$"
        ]

        overlays = []
        for col in df.columns:
            if col in {'date', 'open', 'high', 'low', 'close', 'volume'}:
                continue

            if any(re.match(pattern, col, flags=re.IGNORECASE) for pattern in indicator_patterns):
                overlays.append(col)

        return overlays
