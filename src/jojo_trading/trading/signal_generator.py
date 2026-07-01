"""
交易信號生成器
自動根據DCF估值、技術指標和市場條件生成交易信號
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from .trade_recorder import TradeRecorder, TradeEntry, SignalType, TradeType
from .ai_advisor import AITradingAdvisor, TradingSignal, StockAnalysis
import random

try:
    from ..core.auto_data_fetcher import AutoDataFetcher
except ImportError:
    AutoDataFetcher = None


class SignalGenerator:
    """交易信號生成器"""

    def __init__(
        self,
        trade_recorder: Optional[TradeRecorder] = None,
        ai_advisor: Optional[AITradingAdvisor] = None,
    ):
        self.trade_recorder = trade_recorder or TradeRecorder()
        self.ai_advisor = ai_advisor or AITradingAdvisor(
            trade_recorder=self.trade_recorder
        )

        # 信號生成參數
        self.dcf_buy_threshold = 0.15  # DCF買入折價門檻15%
        self.dcf_sell_threshold = -0.10  # DCF賣出溢價門檻10%
        self.quality_min_threshold = 45  # 最低數據品質要求
        self.confidence_threshold = 60  # 最低信心度要求

        # 初始化自動數據抓取器
        try:
            if AutoDataFetcher:
                self.auto_fetcher = AutoDataFetcher()
            else:
                self.auto_fetcher = None
        except:
            self.auto_fetcher = None

    def scan_stocks_for_signals(
        self, stock_list: List[Dict[str, Any]]
    ) -> List[TradingSignal]:
        """掃描股票列表，生成交易信號"""
        signals = []

        print(f"🔍 開始掃描 {len(stock_list)} 支股票...")

        for stock_data in stock_list:
            try:
                signal = self._evaluate_single_stock(stock_data)
                if signal and signal.confidence >= self.confidence_threshold:
                    signals.append(signal)
                    print(
                        f"📡 發現信號: {signal.stock_code} {signal.action.value} "
                        f"信心度{signal.confidence:.0f}% 目標${signal.target_price:.2f}"
                    )
            except Exception as e:
                print(
                    f"⚠️ 分析股票 {stock_data.get('stock_code', 'Unknown')} 時發生錯誤: {e}"
                )

        # 按信心度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)

        print(f"✅ 共發現 {len(signals)} 個有效交易信號")
        return signals

    def _evaluate_single_stock(
        self, stock_data: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """評估單一股票並生成信號"""
        stock_code = stock_data.get("stock_code")
        current_price = stock_data.get("current_price")

        if not stock_code or not current_price:
            return None

        # 檢查數據品質
        quality_score = stock_data.get("validation_score", 0)
        if quality_score < self.quality_min_threshold:
            return None

        # 使用AI顧問分析
        analysis = self.ai_advisor.analyze_stock(stock_code, stock_data, current_price)
        signal = self.ai_advisor.generate_trading_signal(analysis)

        # 額外的信號過濾和優化
        if signal:
            signal = self._refine_signal(signal, analysis, stock_data)

        return signal

    def _refine_signal(
        self, signal: TradingSignal, analysis: StockAnalysis, stock_data: Dict[str, Any]
    ) -> TradingSignal:
        """優化和細化信號"""

        # 調整信心度基於額外因素
        confidence_adjustment = 0

        # 基於交易歷史調整
        historical_performance = self.ai_advisor._get_stock_historical_performance(
            signal.stock_code
        )
        if historical_performance["trade_count"] > 0:
            if historical_performance["win_rate"] > 70:
                confidence_adjustment += 5
            elif historical_performance["win_rate"] < 30:
                confidence_adjustment -= 10

        # 基於持倉情況調整
        open_positions = len(
            [
                t
                for t in self.trade_recorder.get_open_trades()
                if t.stock_code == signal.stock_code
            ]
        )
        if open_positions > 2:  # 已有多個開倉位置
            confidence_adjustment -= 15

        # 基於市場條件調整（模擬）
        market_condition = self._assess_market_condition()
        if market_condition == "牛市" and signal.action == TradeType.BUY:
            confidence_adjustment += 5
        elif market_condition == "熊市" and signal.action == TradeType.SELL:
            confidence_adjustment += 5

        # 更新信心度
        signal.confidence = max(0, min(100, signal.confidence + confidence_adjustment))

        # 調整目標價格基於波動性
        volatility_factor = self._estimate_volatility(stock_data)
        if volatility_factor > 0.3:  # 高波動性
            if signal.action == TradeType.BUY:
                signal.target_price *= 0.95  # 保守目標
            signal.risk_level = "高"

        return signal

    def _assess_market_condition(self) -> str:
        """評估整體市場狀況（簡化版）"""
        # 基於最近交易活動評估市場
        recent_trades = [
            t
            for t in self.trade_recorder.trades
            if t.entry_time > datetime.now() - timedelta(days=10)
        ]

        if not recent_trades:
            return "中性"

        buy_signals = len([t for t in recent_trades if t.trade_type == TradeType.BUY])
        total_trades = len(recent_trades)

        buy_ratio = buy_signals / total_trades if total_trades > 0 else 0.5

        if buy_ratio > 0.7:
            return "牛市"
        elif buy_ratio < 0.3:
            return "熊市"
        else:
            return "中性"

    def _estimate_volatility(self, stock_data: Dict[str, Any]) -> float:
        """估算股票波動性（簡化版）"""
        # 基於PE比率和行業特性估算波動性
        pe_ratio = stock_data.get("pe_ratio", 20)

        # 高PE通常意味著高波動性
        if pe_ratio > 50:
            return 0.4
        elif pe_ratio > 30:
            return 0.3
        elif pe_ratio > 15:
            return 0.2
        else:
            return 0.15

    def generate_entry_signals(self, watchlist: List[str]) -> List[Dict[str, Any]]:
        """為監視列表生成進場信號"""
        entry_signals = []

        for stock_code in watchlist:
            # 獲取真實數據
            stock_data = self._get_real_stock_data(stock_code)

            if stock_data:
                signal = self._evaluate_single_stock(stock_data)
                if signal and signal.action == TradeType.BUY:
                    entry_signals.append(
                        {
                            "stock_code": stock_code,
                            "signal": signal,
                            "priority": self._calculate_priority(signal),
                            "suggested_position_size": self._calculate_position_size(
                                signal
                            ),
                        }
                    )

        return sorted(entry_signals, key=lambda x: x["priority"], reverse=True)

    def generate_exit_signals(self) -> List[Dict[str, Any]]:
        """為現有持倉生成出場信號"""
        exit_signals = []
        open_trades = self.trade_recorder.get_open_trades()

        for trade in open_trades:
            # 獲取當前價格 (真實)
            current_price = self._get_current_price(trade.stock_code)

            if current_price > 0:
                # 更新未實現損益
                self.trade_recorder.update_unrealized_pnl(
                    trade.stock_code, current_price
                )

                # 檢查是否應該出場
                exit_reason = self._should_exit_position(trade, current_price)
                if exit_reason:
                    exit_signals.append(
                        {
                            "trade_id": trade.trade_id,
                            "stock_code": trade.stock_code,
                            "current_price": current_price,
                            "entry_price": trade.entry_price,
                            "unrealized_pnl": trade.unrealized_pnl,
                            "exit_reason": exit_reason,
                            "urgency": self._assess_exit_urgency(trade, current_price),
                        }
                    )

        return sorted(exit_signals, key=lambda x: x["urgency"], reverse=True)

    def _should_exit_position(
        self, trade: TradeEntry, current_price: float
    ) -> Optional[str]:
        """判斷是否應該出場"""

        # 停損檢查
        if trade.trade_type == TradeType.BUY:
            loss_pct = (current_price - trade.entry_price) / trade.entry_price
            if loss_pct < -0.15:  # 虧損超過15%
                return "停損出場"

            # 獲利了結檢查
            if loss_pct > 0.25:  # 獲利超過25%
                return "獲利了結"

        # 持倉時間檢查
        holding_days = (datetime.now() - trade.entry_time).days
        if holding_days > 90:  # 持倉超過90天
            return "持倉時間過長"

        # DCF重新評估 (使用真實數據)
        stock_data = self._get_real_stock_data(trade.stock_code)
        if stock_data:
            analysis = self.ai_advisor.analyze_stock(
                trade.stock_code, stock_data, current_price
            )

            if analysis.dcf_discount and analysis.dcf_discount < -0.2:  # 溢價超過20%
                return "估值過高"

        return None

    def _assess_exit_urgency(self, trade: TradeEntry, current_price: float) -> int:
        """評估出場緊急程度 (1-10)"""
        urgency = 5  # 基準值

        # 基於虧損程度
        if trade.trade_type == TradeType.BUY:
            loss_pct = (current_price - trade.entry_price) / trade.entry_price
            if loss_pct < -0.20:
                urgency += 4
            elif loss_pct < -0.15:
                urgency += 2

        # 基於持倉時間
        holding_days = (datetime.now() - trade.entry_time).days
        if holding_days > 120:
            urgency += 3
        elif holding_days > 90:
            urgency += 1

        return min(10, urgency)

    def _calculate_priority(self, signal: TradingSignal) -> float:
        """計算信號優先級"""
        base_priority = signal.confidence / 100

        # 基於風險調整
        if signal.risk_level == "低":
            base_priority *= 1.2
        elif signal.risk_level == "高":
            base_priority *= 0.8

        return base_priority

    def _calculate_position_size(self, signal: TradingSignal) -> float:
        """計算建議倉位大小（百分比）"""
        base_size = 0.05  # 基礎5%

        # 基於信心度調整
        confidence_factor = signal.confidence / 100
        size = base_size * confidence_factor

        # 基於風險調整
        if signal.risk_level == "低":
            size *= 1.5
        elif signal.risk_level == "高":
            size *= 0.5

        return min(0.20, size)  # 最大不超過20%

    def _get_current_price(self, stock_code: str) -> float:
        """獲取當前股價 (優先使用真實數據)"""
        if self.auto_fetcher:
            try:
                result = self.auto_fetcher.auto_fetch_stock_data(stock_code)
                if result["success"] and "current_market_price" in result["data"]:
                    price = result["data"]["current_market_price"]
                    if price and price > 0:
                        return float(price)
            except:
                pass
        return 0.0

    def _get_real_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """獲取真實股票數據"""
        if not self.auto_fetcher:
            return None

        try:
            fetch_result = self.auto_fetcher.get_dcf_ready_data(stock_code)
            if fetch_result.get("success"):
                data = fetch_result
                current_price = data.get("current_market_price", 0)

                # 補充計算欄位
                net_income = data.get("net_income_parent", 0)
                shares = data.get("shares_outstanding", 1)
                eps = net_income / shares if shares > 0 else 0

                pe_ratio = current_price / eps if eps > 0 else 0

                equity = data.get("equity_parent", 0)
                bps = equity / shares if shares > 0 else 0
                pb_ratio = current_price / bps if bps > 0 else 0

                roe = net_income / equity if equity > 0 else 0

                # 構建分析所需數據結構
                return {
                    "stock_code": stock_code,
                    "stock_name": data.get("company_name", f"{stock_code}公司"),
                    "current_price": current_price,
                    "intrinsic_value_per_share": (
                        eps * 15 if eps > 0 else 0
                    ),  # 簡單估值替代
                    "pe_ratio": pe_ratio,
                    "pb_ratio": pb_ratio,
                    "roe": roe,
                    "debt_ratio": 0.5,  # 暫無負債數據
                    "validation_score": data.get("data_quality_score", 50),
                }
        except Exception as e:
            print(f"獲取真實數據失敗 {stock_code}: {e}")

        return None

    def _get_mock_stock_data(self, stock_code: str) -> Dict[str, Any]:
        """(已棄用) 生成模擬股票數據"""
        # 保留此方法以防萬一，但不再主動使用
        current_price = 100.0
        return {
            "stock_code": stock_code,
            "stock_name": f"{stock_code}公司",
            "current_price": current_price,
            "intrinsic_value_per_share": current_price * 1.1,
            "pe_ratio": 15,
            "pb_ratio": 1.5,
            "roe": 0.15,
            "debt_ratio": 0.4,
            "validation_score": 60,
        }


class AutoTradingEngine:
    """自動交易引擎"""

    def __init__(
        self, trade_recorder: TradeRecorder, signal_generator: SignalGenerator
    ):
        self.trade_recorder = trade_recorder
        self.signal_generator = signal_generator
        self.auto_trade_enabled = False
        self.max_daily_trades = 3
        self.max_position_size = 0.15  # 最大單一倉位15%

    def enable_auto_trading(self, enabled: bool = True):
        """啟用/停用自動交易"""
        self.auto_trade_enabled = enabled
        status = "啟用" if enabled else "停用"
        print(f"🤖 自動交易已{status}")

    def execute_daily_scan(self, watchlist: List[str]) -> Dict[str, Any]:
        """執行每日掃描和交易"""
        if not self.auto_trade_enabled:
            return {"status": "disabled", "message": "自動交易未啟用"}

        print("🔄 開始每日自動交易掃描...")

        # 生成進場信號
        entry_signals = self.signal_generator.generate_entry_signals(watchlist)

        # 生成出場信號
        exit_signals = self.signal_generator.generate_exit_signals()

        # 執行交易
        executed_trades = []
        daily_trade_count = 0

        # 先處理出場信號
        for exit_signal in exit_signals[:3]:  # 最多處理3個出場信號
            if self._execute_exit_trade(exit_signal):
                executed_trades.append(
                    {
                        "type": "exit",
                        "stock_code": exit_signal["stock_code"],
                        "reason": exit_signal["exit_reason"],
                    }
                )

        # 再處理進場信號
        for entry_signal in entry_signals:
            if daily_trade_count >= self.max_daily_trades:
                break

            if self._execute_entry_trade(entry_signal):
                executed_trades.append(
                    {
                        "type": "entry",
                        "stock_code": entry_signal["stock_code"],
                        "signal": entry_signal["signal"],
                    }
                )
                daily_trade_count += 1

        return {
            "status": "completed",
            "executed_trades": executed_trades,
            "entry_signals_found": len(entry_signals),
            "exit_signals_found": len(exit_signals),
        }

    def _execute_entry_trade(self, entry_signal: Dict[str, Any]) -> bool:
        """執行進場交易"""
        try:
            signal = entry_signal["signal"]
            suggested_size = entry_signal["suggested_position_size"]

            # 檢查倉位限制
            if suggested_size > self.max_position_size:
                suggested_size = self.max_position_size

            # 計算交易數量（假設總資金100萬）
            total_capital = 1000000
            trade_amount = total_capital * suggested_size
            quantity = int(trade_amount / signal.target_price)

            if quantity > 0:
                trade = TradeEntry(
                    stock_code=signal.stock_code,
                    stock_name=f"{signal.stock_code}公司",
                    trade_type=signal.action,
                    entry_price=signal.target_price,
                    quantity=quantity,
                    signal_type=signal.signal_type,
                    market_price_at_entry=signal.target_price,
                    notes=f"自動交易: {signal.reasoning}",
                )

                self.trade_recorder.add_trade(trade)
                print(
                    f"✅ 自動執行進場: {signal.stock_code} {signal.action.value} {quantity}股"
                )
                return True

        except Exception as e:
            print(f"❌ 執行進場交易失敗: {e}")

        return False

    def _execute_exit_trade(self, exit_signal: Dict[str, Any]) -> bool:
        """執行出場交易"""
        try:
            success = self.trade_recorder.close_trade(
                exit_signal["trade_id"], exit_signal["current_price"]
            )

            if success:
                print(
                    f"✅ 自動執行出場: {exit_signal['stock_code']} 原因: {exit_signal['exit_reason']}"
                )

            return success

        except Exception as e:
            print(f"❌ 執行出場交易失敗: {e}")

        return False


# 便利函數
def create_signal_generator(
    trade_recorder: TradeRecorder, ai_advisor: AITradingAdvisor
) -> SignalGenerator:
    """創建信號生成器"""
    return SignalGenerator(trade_recorder, ai_advisor)


def create_auto_trading_engine(
    trade_recorder: TradeRecorder, signal_generator: SignalGenerator
) -> AutoTradingEngine:
    """創建自動交易引擎"""
    return AutoTradingEngine(trade_recorder, signal_generator)
