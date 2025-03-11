from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt6.QtCore import Qt, QTimer
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import mplfinance as mpf
from main import TaiwanFuturesTrader

class TradingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('台指期交易系統')
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建主要部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 創建工具欄
        self.create_toolbar()
        
        # 創建圖表區域
        self.create_charts()
        
        # 初始化交易者實例
        self.trader = TaiwanFuturesTrader()
        
        # 設置定時更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_charts)
        self.timer.start(5000)  # 每5秒更新一次
        
        # 開始接收數據
        self.trader.start_streaming()
    
    def create_toolbar(self):
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        
        # 時間週期選擇
        self.period_combo = QComboBox()
        self.period_combo.addItems(['15分鐘', '30分鐘', '1小時'])
        toolbar_layout.addWidget(QLabel('時間週期:'))
        toolbar_layout.addWidget(self.period_combo)
        
        # 回測按鈕
        backtest_btn = QPushButton('回測')
        backtest_btn.clicked.connect(self.start_backtest)
        toolbar_layout.addWidget(backtest_btn)
        
        toolbar_layout.addStretch()
        self.layout.addWidget(toolbar)
    
    def create_charts(self):
        # 創建圖表容器
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        # 創建子圖
        self.ax1 = self.figure.add_subplot(311)
        self.ax2 = self.figure.add_subplot(312)
        self.ax3 = self.figure.add_subplot(313)
        
        self.figure.tight_layout()
    
    def update_charts(self):
        # 清除現有圖表
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.clear()
        
        # 繪製新的K線圖
        mpf.plot(self.trader.kbars_15m, type='candle', style='charles', 
                 title='15分鐘K線', ax=self.ax1)
        mpf.plot(self.trader.kbars_30m, type='candle', style='charles', 
                 title='30分鐘K線', ax=self.ax2)
        mpf.plot(self.trader.kbars_1h, type='candle', style='charles', 
                 title='1小時K線', ax=self.ax3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def start_backtest(self):
        # TODO: 實現回測功能
        pass

def main():
    app = QApplication(sys.argv)
    window = TradingWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()