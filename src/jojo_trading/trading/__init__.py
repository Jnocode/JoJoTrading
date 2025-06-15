"""
JoJo Trading 交易系統模組

這個模組包含了智能交易系統的所有核心組件：
- TradingSystemUI: 交易系統用戶介面
- TradeRecorder: 交易記錄管理器
- AITradingAdvisor: AI 交易顧問
- SignalGenerator: 交易信號生成器
- AutoTradingEngine: 自動交易引擎
"""

from .trading_ui import TradingSystemUI
from .trade_recorder import TradeRecorder, TradeEntry, TradeType, TradeStatus, SignalType
from .ai_advisor import AITradingAdvisor, TradingSignal, create_ai_advisor
from .signal_generator import SignalGenerator, AutoTradingEngine, create_signal_generator, create_auto_trading_engine

__all__ = [
    'TradingSystemUI',
    'TradeRecorder', 
    'TradeEntry', 
    'TradeType', 
    'TradeStatus', 
    'SignalType',
    'AITradingAdvisor', 
    'TradingSignal', 
    'create_ai_advisor',
    'SignalGenerator', 
    'AutoTradingEngine', 
    'create_signal_generator', 
    'create_auto_trading_engine'
]
