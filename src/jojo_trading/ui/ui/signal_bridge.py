
from PySide6.QtCore import QObject, Signal
import datetime

class ShioajiSignalBridge(QObject):
    """
    Bridge between Shioaji's background thread callbacks and Qt's Main Thread.
    """
    # Signal arguments: (code, data_dict)
    quote_received = Signal(str, dict) # Best 5 Bid/Ask
    tick_received = Signal(str, dict)  # Deal/match info
    
    def __init__(self):
        super().__init__()
        
    def handle_bidask(self, bidask):
        """
        Callback from Shioaji thread for Bid/Ask updates.
        """
        try:
            # Parse Shioaji object into Python native dict for safety across threads
            # bidask object usually contains: code, datetime, bid_price, bid_volume, diff_bid_vol, ask_price...
            
            data = {
                'code': bidask.code,
                'ts': str(bidask.datetime),
                'bid_price': list(bidask.bid_price),
                'bid_volume': list(bidask.bid_volume),
                'ask_price': list(bidask.ask_price),
                'ask_volume': list(bidask.ask_volume)
            }
            # Emit to UI Thread
            self.quote_received.emit(bidask.code, data)
            
        except Exception as e:
            print(f"Bridge BidAsk Error: {e}")

    def handle_tick(self, tick):
        """
        Callback from Shioaji thread for Tick updates.
        """
        try:
            # tick object: code, datetime, close, volume, tick_type, simtrace...
            data = {
                'code': tick.code,
                'ts': str(tick.datetime),
                'close': float(tick.close),
                'volume': int(tick.volume),
                'tick_type': int(tick.tick_type), # 1: Buy, 2: Sell (Use enum usually)
                'simtrace': getattr(tick, 'simtrace', 0)
            }
            # Emit to UI Thread
            self.tick_received.emit(tick.code, data)
            
        except Exception as e:
            print(f"Bridge Tick Error: {e}")
