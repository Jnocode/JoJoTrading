"""
交易記錄系統 - 點位進出模擬單紀錄
用於記錄和管理模擬交易，並提供AI建議功能
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import uuid
import pandas as pd
from pathlib import Path


class TradeType(Enum):
    """交易類型"""

    BUY = "買入"
    SELL = "賣出"


class TradeStatus(Enum):
    """交易狀態"""

    OPEN = "開倉"
    CLOSED = "平倉"
    PARTIAL = "部分平倉"


class SignalType(Enum):
    """交易信號類型"""

    DCF_UNDERVALUED = "DCF低估"
    DCF_OVERVALUED = "DCF高估"
    TECHNICAL_BUY = "技術面買入"
    TECHNICAL_SELL = "技術面賣出"
    MANUAL = "手動交易"


@dataclass
class TradeEntry:
    """單筆交易紀錄"""

    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stock_code: str = ""
    stock_name: str = ""
    trade_type: TradeType = TradeType.BUY

    # 交易基本資訊
    entry_price: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    quantity: int = 0

    # 平倉資訊（選填）
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_quantity: Optional[int] = None

    # 交易狀態
    status: TradeStatus = TradeStatus.OPEN
    signal_type: SignalType = SignalType.MANUAL

    # 基本面資訊
    dcf_intrinsic_value: Optional[float] = None
    market_price_at_entry: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None

    # 績效計算
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    return_percentage: Optional[float] = None

    # 備註和標籤
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    # Backward-compatible aliases used by legacy verification tests.
    symbol: Optional[str] = None
    price: Optional[float] = None
    timestamp: Optional[Any] = None

    def __post_init__(self) -> None:
        """Normalize legacy constructor aliases to canonical fields."""
        if self.symbol and not self.stock_code:
            self.stock_code = self.symbol
        if self.price is not None and not self.entry_price:
            self.entry_price = self.price
        if self.timestamp is not None and isinstance(self.timestamp, str):
            self.entry_time = datetime.fromisoformat(self.timestamp)
        elif self.timestamp is not None and isinstance(self.timestamp, datetime):
            self.entry_time = self.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "trade_id": self.trade_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "trade_type": self.trade_type.value,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
            "quantity": self.quantity,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_quantity": self.exit_quantity,
            "status": self.status.value,
            "signal_type": self.signal_type.value,
            "dcf_intrinsic_value": self.dcf_intrinsic_value,
            "market_price_at_entry": self.market_price_at_entry,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "return_percentage": self.return_percentage,
            "notes": self.notes,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeEntry":
        """從字典創建交易記錄"""
        entry = cls()
        entry.trade_id = data.get("trade_id", str(uuid.uuid4()))
        entry.stock_code = data.get("stock_code", "")
        entry.stock_name = data.get("stock_name", "")
        entry.trade_type = TradeType(data.get("trade_type", TradeType.BUY.value))
        entry.entry_price = data.get("entry_price", 0.0)
        entry.entry_time = datetime.fromisoformat(
            data.get("entry_time", datetime.now().isoformat())
        )
        entry.quantity = data.get("quantity", 0)
        entry.exit_price = data.get("exit_price")
        entry.exit_time = (
            datetime.fromisoformat(data["exit_time"]) if data.get("exit_time") else None
        )
        entry.exit_quantity = data.get("exit_quantity")
        entry.status = TradeStatus(data.get("status", TradeStatus.OPEN.value))
        entry.signal_type = SignalType(data.get("signal_type", SignalType.MANUAL.value))
        entry.dcf_intrinsic_value = data.get("dcf_intrinsic_value")
        entry.market_price_at_entry = data.get("market_price_at_entry")
        entry.pe_ratio = data.get("pe_ratio")
        entry.pb_ratio = data.get("pb_ratio")
        entry.realized_pnl = data.get("realized_pnl")
        entry.unrealized_pnl = data.get("unrealized_pnl")
        entry.return_percentage = data.get("return_percentage")
        entry.notes = data.get("notes", "")
        entry.tags = data.get("tags", [])
        return entry


class TradeRecorder:
    """交易記錄管理器"""

    def __init__(self, data_file: str = "trade_records.json"):
        self.data_file = Path(data_file)
        self.trades: List[TradeEntry] = []
        self.load_trades()

    def add_trade(self, trade: TradeEntry) -> str:
        """新增交易記錄"""
        self.trades.append(trade)
        self.save_trades()
        print(
            f"📝 新增交易記錄: {trade.stock_code} {trade.trade_type.value} {trade.quantity}股 @ ${trade.entry_price}"
        )
        return trade.trade_id

    def close_trade(
        self, trade_id: str, exit_price: float, exit_quantity: Optional[int] = None
    ) -> bool:
        """平倉交易"""
        for trade in self.trades:
            if trade.trade_id == trade_id and trade.status == TradeStatus.OPEN:
                trade.exit_price = exit_price
                trade.exit_time = datetime.now()
                trade.exit_quantity = exit_quantity or trade.quantity

                # 計算盈虧
                if trade.trade_type == TradeType.BUY:
                    trade.realized_pnl = (
                        exit_price - trade.entry_price
                    ) * trade.exit_quantity
                else:
                    trade.realized_pnl = (
                        trade.entry_price - exit_price
                    ) * trade.exit_quantity

                trade.return_percentage = (
                    trade.realized_pnl / (trade.entry_price * trade.exit_quantity)
                ) * 100

                # 更新狀態
                if trade.exit_quantity == trade.quantity:
                    trade.status = TradeStatus.CLOSED
                else:
                    trade.status = TradeStatus.PARTIAL

                self.save_trades()
                print(
                    f"💰 平倉交易: {trade.stock_code} 盈虧: ${trade.realized_pnl:.2f} ({trade.return_percentage:.2f}%)"
                )
                return True
        return False

    def update_unrealized_pnl(self, stock_code: str, current_price: float):
        """更新未實現損益"""
        for trade in self.trades:
            if trade.stock_code == stock_code and trade.status == TradeStatus.OPEN:
                if trade.trade_type == TradeType.BUY:
                    trade.unrealized_pnl = (
                        current_price - trade.entry_price
                    ) * trade.quantity
                else:
                    trade.unrealized_pnl = (
                        trade.entry_price - current_price
                    ) * trade.quantity

    def get_all_trades(self) -> List[TradeEntry]:
        """獲取所有交易記錄（legacy compatibility）。"""
        return list(self.trades)

    def get_trades_by_stock(self, stock_code: str) -> List[TradeEntry]:
        """獲取特定股票的交易記錄"""
        return [trade for trade in self.trades if trade.stock_code == stock_code]

    def get_open_trades(self) -> List[TradeEntry]:
        """獲取所有開倉交易"""
        return [trade for trade in self.trades if trade.status == TradeStatus.OPEN]

    def get_closed_trades(self) -> List[TradeEntry]:
        """獲取所有已平倉交易"""
        return [trade for trade in self.trades if trade.status == TradeStatus.CLOSED]

    def calculate_portfolio_performance(self) -> Dict[str, Any]:
        """計算投資組合績效"""
        closed_trades = self.get_closed_trades()

        if not closed_trades:
            return {
                "total_trades": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "avg_return": 0,
                "max_return": 0,
                "min_return": 0,
            }

        total_pnl = sum(
            trade.realized_pnl for trade in closed_trades if trade.realized_pnl
        )
        winning_trades = [
            trade
            for trade in closed_trades
            if trade.realized_pnl and trade.realized_pnl > 0
        ]
        returns = [
            trade.return_percentage
            for trade in closed_trades
            if trade.return_percentage
        ]

        return {
            "total_trades": len(closed_trades),
            "total_pnl": total_pnl,
            "win_rate": (
                len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
            ),
            "avg_return": sum(returns) / len(returns) if returns else 0,
            "max_return": max(returns) if returns else 0,
            "min_return": min(returns) if returns else 0,
            "winning_trades": len(winning_trades),
            "losing_trades": len(closed_trades) - len(winning_trades),
        }

    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame格式"""
        if not self.trades:
            return pd.DataFrame()

        data = [trade.to_dict() for trade in self.trades]
        return pd.DataFrame(data)

    def save_trades(self):
        """保存交易記錄到文件"""
        try:
            data = [trade.to_dict() for trade in self.trades]
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存交易記錄失敗: {e}")

    def load_trades(self):
        """從文件載入交易記錄"""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.trades = [TradeEntry.from_dict(trade_data) for trade_data in data]
                print(f"📂 載入 {len(self.trades)} 筆交易記錄")
            else:
                print("📂 未找到交易記錄文件，創建新的記錄")
        except Exception as e:
            print(f"⚠️ 載入交易記錄失敗: {e}")
            self.trades = []


# 全局交易記錄器實例
trade_recorder = TradeRecorder()
