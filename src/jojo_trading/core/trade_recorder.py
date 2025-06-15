"""
交易記錄器 - 暫時的模擬實現
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

class TradeType(Enum):
    BUY = "買入"
    SELL = "賣出"

class TradeStatus(Enum):
    OPEN = "開倉"
    CLOSED = "平倉"

class TradeEntry:
    """交易記錄項目"""
    
    def __init__(self, stock_code: str, stock_name: str, trade_type: TradeType, 
                 entry_price: float, quantity: int, signal_type=None):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.trade_type = trade_type
        self.entry_price = entry_price
        self.quantity = quantity
        self.entry_time = datetime.now()
        self.exit_price: Optional[float] = None
        self.exit_time: Optional[datetime] = None
        self.status = TradeStatus.OPEN
        self.realized_pnl: Optional[float] = None
        self.unrealized_pnl: Optional[float] = None
        self.signal_type = signal_type

class TradeRecorder:
    """交易記錄器類別"""
    
    def __init__(self):
        """初始化交易記錄器"""
        self.trades: List[TradeEntry] = []
    
    def get_all_trades(self) -> List[TradeEntry]:
        """獲取所有交易記錄"""
        return self.trades
    
    def add_trade(self, trade: TradeEntry):
        """添加交易記錄"""
        self.trades.append(trade)
    
    def save_trades(self):
        """保存交易記錄"""
        pass
    
    def load_trades(self):
        """載入交易記錄"""
        pass
