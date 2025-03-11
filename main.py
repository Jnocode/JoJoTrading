import shioaji as sj
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import mplfinance as mpf

class TaiwanFuturesTrader:
    def __init__(self):
        self.api = sj.Shioaji()
        self.login()
        self.initialize_kbars()
        self.current_data = {'price': None, 'volume': 0}
        self.last_update = {'15m': None, '30m': None, '1h': None}
        
    def initialize_kbars(self):
        current_time = datetime.now()
        index = pd.date_range(start=current_time - timedelta(days=1), 
                            end=current_time, 
                            freq='15min')
        self.kbars_15m = pd.DataFrame(index=index, 
                                     columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        
        index = pd.date_range(start=current_time - timedelta(days=1), 
                            end=current_time, 
                            freq='30min')
        self.kbars_30m = pd.DataFrame(index=index, 
                                     columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        
        index = pd.date_range(start=current_time - timedelta(days=1), 
                            end=current_time, 
                            freq='1H')
        self.kbars_1h = pd.DataFrame(index=index, 
                                    columns=['Open', 'High', 'Low', 'Close', 'Volume'])

    def login(self):
        self.api.login(
            api_key="XXXXXXXX",
            secret_key="XXXXXXXX",
            contracts_cb=True,
            simulation=True
        )

    def on_tick_callback(self, tick):
        if hasattr(tick, 'price') and hasattr(tick, 'volume'):
            self.current_data['price'] = tick.price
            self.current_data['volume'] = tick.volume
            print(f"收到報價: 價格={tick.price}, 成交量={tick.volume}")
            self.update_kbars()

    def update_kbars(self):
        current_time = datetime.now()
        
        if self.last_update['15m'] is None or (current_time - self.last_update['15m']).seconds >= 900:
            self._add_kbar(self.kbars_15m, '15m')
            
        if self.last_update['30m'] is None or (current_time - self.last_update['30m']).seconds >= 1800:
            self._add_kbar(self.kbars_30m, '30m')
            
        if self.last_update['1h'] is None or (current_time - self.last_update['1h']).seconds >= 3600:
            self._add_kbar(self.kbars_1h, '1h')
            
    def _add_kbar(self, df, timeframe):
        current_time = datetime.now()
        new_bar = {
            'Open': self.current_data['price'],
            'High': self.current_data['price'],
            'Low': self.current_data['price'],
            'Close': self.current_data['price'],
            'Volume': self.current_data['volume']
        }
        df.loc[current_time] = new_bar
        self.last_update[timeframe] = current_time

    def start_streaming(self):
        try:
            contract = self.api.Contracts.Futures.TXFF
            print(f"訂閱合約: {contract.code}")
            self.api.quote.subscribe(contract, quote_type='tick', callback=self.on_tick_callback)
            print("成功訂閱報價")
        except Exception as e:
            print(f"訂閱失敗: {str(e)}")

    def plot_charts(self):
        fig = plt.figure(figsize=(15, 10))
        
        ax1 = fig.add_subplot(311)
        mpf.plot(self.kbars_15m, type='candle', style='charles', title='15分鐘K線', ax=ax1)
        
        ax2 = fig.add_subplot(312)
        mpf.plot(self.kbars_30m, type='candle', style='charles', title='30分鐘K線', ax=ax2)
        
        ax3 = fig.add_subplot(313)
        mpf.plot(self.kbars_1h, type='candle', style='charles', title='1小時K線', ax=ax3)
        
        plt.tight_layout()
        plt.show()

def main():
    trader = TaiwanFuturesTrader()
    print("系統初始化完成")
    
    trader.start_streaming()
    print("開始接收即時數據")
    
    try:
        while True:
            trader.plot_charts()
            print("圖表已更新")
            time.sleep(5)
    except KeyboardInterrupt:
        print("程式結束")

if __name__ == "__main__":
    main()