"""
AI交易建議引擎
結合DCF估值、財務指標和交易歷史，提供智能交易建議
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from .trade_recorder import TradeRecorder, TradeEntry, SignalType, TradeType
import statistics
import pandas as pd
from ..core.technical_analysis import TechnicalAnalysis


@dataclass
class TradingSignal:
    """交易信號"""

    stock_code: str
    signal_type: SignalType
    action: TradeType
    confidence: float  # 信心度 (0-100)
    target_price: float
    stop_loss: Optional[float] = None
    reasoning: str = ""
    risk_level: str = "中等"  # 低, 中等, 高


@dataclass
class StockAnalysis:
    """股票分析結果"""

    stock_code: str
    stock_name: str
    current_price: float
    dcf_intrinsic_value: Optional[float] = None

    # 估值指標
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_ratio: Optional[float] = None

    # [Phase 4 New] 量化指標
    piotroski_f_score: int = 0  # 0-9分

    # DCF分析
    dcf_discount: Optional[float] = None  # 折價幅度
    quality_score: Optional[float] = None

    # 技術指標
    rsi: Optional[float] = None
    macd: Optional[dict] = None
    ma_trend: str = "Neutral"  # Bullish/Bearish/Neutral
    technical_indicators: Optional[Dict[str, Any]] = None

    # 整體評分
    fundamental_score: float = 50.0  # 基本面評分 (0-100)
    technical_score: float = 50.0  # 技術面評分 (0-100)
    overall_score: float = 50.0  # 綜合評分 (0-100)


class AITradingAdvisor:
    """AI交易建議引擎"""

    def __init__(self, trade_recorder: Optional[TradeRecorder] = None):
        self.trade_recorder = trade_recorder or TradeRecorder()
        self.min_dcf_discount = 0.15  # 最小DCF折價要求15%
        self.max_pe_ratio = 25.0  # 最大合理PE比率
        self.min_roe = 0.08  # 最小ROE要求8%
        self.max_debt_ratio = 0.6  # 最大負債比率60%

    def analyze_stock(
        self,
        stock_code: str,
        financial_data: Dict[str, Any],
        current_price: float,
        price_history: Optional[pd.Series] = None,
    ) -> StockAnalysis:
        """分析單一股票"""
        analysis = StockAnalysis(
            stock_code=stock_code,
            stock_name=financial_data.get("stock_name", stock_code),
            current_price=current_price,
        )

        # 提取財務指標
        analysis.dcf_intrinsic_value = financial_data.get("intrinsic_value_per_share")
        analysis.pe_ratio = financial_data.get("pe_ratio")
        analysis.pb_ratio = financial_data.get("pb_ratio")
        analysis.roe = financial_data.get("roe")
        analysis.debt_ratio = financial_data.get("debt_ratio")
        analysis.quality_score = financial_data.get("validation_score", 50)

        # [Phase 4] 計算 Piotroski F-Score
        analysis.piotroski_f_score = self._calculate_piotroski_score(financial_data)

        # [Phase 4] 計算技術指標
        if price_history is not None and not price_history.empty:
            self._analyze_technical(analysis, price_history)

        # 計算DCF折價
        if analysis.dcf_intrinsic_value and analysis.dcf_intrinsic_value > 0:
            analysis.dcf_discount = (
                analysis.dcf_intrinsic_value - current_price
            ) / analysis.dcf_intrinsic_value

        # 計算各項評分
        analysis.fundamental_score = self._calculate_fundamental_score(analysis)
        analysis.technical_score = self._calculate_technical_score(analysis)
        analysis.overall_score = (
            analysis.fundamental_score * 0.7 + analysis.technical_score * 0.3
        )

        return analysis

    def _calculate_fundamental_score(self, analysis: StockAnalysis) -> float:
        """計算基本面評分"""
        score = 50.0  # 基礎分數

        # DCF估值評分 (40分)
        if analysis.dcf_discount is not None:
            if analysis.dcf_discount > 0.3:  # 折價30%以上
                score += 20
            elif analysis.dcf_discount > 0.15:  # 折價15-30%
                score += 15
            elif analysis.dcf_discount > 0:  # 有折價
                score += 10
            elif analysis.dcf_discount > -0.15:  # 溢價在15%內
                score += 5
            else:  # 溢價超過15%
                score -= 15

        # PE比率評分 (15分)
        if analysis.pe_ratio is not None:
            if analysis.pe_ratio <= 15:
                score += 15
            elif analysis.pe_ratio <= 25:
                score += 10
            elif analysis.pe_ratio <= 35:
                score += 5
            else:
                score -= 10

        # ROE評分 (15分)
        if analysis.roe is not None:
            if analysis.roe >= 0.15:  # 15%以上
                score += 15
            elif analysis.roe >= 0.10:  # 10-15%
                score += 10
            elif analysis.roe >= 0.05:  # 5-10%
                score += 5
            else:
                score -= 10

        # 負債比率評分 (10分)
        if analysis.debt_ratio is not None:
            if analysis.debt_ratio <= 0.3:
                score += 10
            elif analysis.debt_ratio <= 0.5:
                score += 5
            elif analysis.debt_ratio <= 0.7:
                score += 0
            else:
                score -= 15

        # 數據品質評分 (10分 - 權重降低)
        if analysis.quality_score is not None:
            quality_bonus = (analysis.quality_score - 50) / 2.5
            score += max(-5, min(10, quality_bonus))

        # [Phase 4] Piotroski F-Score 評分 (30分 - 高權重)
        # F-Score 7-9 為極優
        if analysis.piotroski_f_score >= 8:
            score += 30
        elif analysis.piotroski_f_score >= 7:
            score += 25
        elif analysis.piotroski_f_score >= 5:
            score += 15
        elif analysis.piotroski_f_score >= 4:
            score += 5
        elif analysis.piotroski_f_score <= 2:
            score -= 20

        return max(0, min(100, score))

    def _calculate_piotroski_score(self, data: Dict[str, Any]) -> int:
        """計算 Piotroski F-Score (0-9分)"""
        f_score = 0

        # 1. ROA > 0 (資產報酬率為正)
        if data.get("roe", 0) > 0:  # 暫用 ROE 代替 ROA
            f_score += 1

        # 2. CFO > 0 (營業現金流為正)
        # 如果有 FCF, 通常 CFO 也是正的，這裡用估算
        # FCF = CFO - Capex => CFO = FCF + Capex
        fcf = data.get("fcf") or 0
        capex = data.get("capex") or 0
        cfo = fcf - capex  # Capex 是負數，所以 CFO = FCF - (-Capex) ?
        # DataAdapter: standardized["capex"] = yf_data.get("capex") -> Yahoo Capex 是負數
        # FCF = CFO + Capex  => CFO = FCF - Capex
        if cfo > 0:
            f_score += 1

        # 3. Accrual: CFO > ROA (淨利品質: 營業現金流 > 淨利)
        net_income = data.get("net_income_parent") or 0
        if cfo > net_income:  # 簡單比較金額，忽略資產規模標準化
            f_score += 1

        # 4-6. 槓桿流動性 (需前後期比較，暫時使用靜態指標)
        debt_ratio = data.get("debt_ratio") or 0.5
        if debt_ratio < 0.4:  # 負債比低
            f_score += 1

        current_ratio = data.get("current_ratio")  # 假設有此欄位
        if current_ratio and current_ratio > 1.5:
            f_score += 1

        # 7-9. 營運效率 (暫時使用簡單指標)
        gross_margin = data.get("gross_margin")
        if gross_margin and gross_margin > 0.2:  # 毛利 > 20%
            f_score += 1

        # 由於數據限制，部分分數先給基本分
        # 待未來引入完整歷史數據後完善
        f_score += 1  # 假設股本未增加

        return min(9, f_score)

    def _analyze_technical(self, analysis: StockAnalysis, prices: pd.Series):
        """執行技術分析"""
        try:
            ta = TechnicalAnalysis()

            # RSI
            analysis.rsi = ta.calculate_rsi(prices)

            # MACD
            analysis.macd = ta.calculate_macd(prices)

            # MA Trend (20MA vs 60MA)
            ma20 = ta.calculate_ma(prices, 20)
            ma60 = ta.calculate_ma(prices, 60)

            if ma20 > ma60:
                analysis.ma_trend = "Bullish"
            elif ma20 < ma60:
                analysis.ma_trend = "Bearish"
            else:
                analysis.ma_trend = "Neutral"

            analysis.technical_indicators = {
                "rsi": analysis.rsi,
                "macd": analysis.macd,
                "ma20": ma20,
                "ma60": ma60,
            }

        except Exception as e:
            print(f"Technical Analysis Error: {e}")
            analysis.technical_score = 50.0

    def _calculate_technical_score(self, analysis: StockAnalysis) -> float:
        """計算技術面評分"""
        score = 50.0

        # RSI 評分 (30分)
        if analysis.rsi is not None:
            if 30 <= analysis.rsi <= 70:
                score += 10  # 健康區間
            elif analysis.rsi < 30:  # 超賣 -> 反彈機會
                score += 20
            elif analysis.rsi > 70:  # 超買 -> 回檔風險
                score -= 20

        # MACD 評分 (30分)
        if analysis.macd:
            hist = analysis.macd.get("hist", 0)
            if hist > 0:  # 多頭動能
                score += 15
            else:
                score -= 15

        # 趨勢評分 (40分)
        if analysis.ma_trend == "Bullish":
            score += 20
        elif analysis.ma_trend == "Bearish":
            score -= 20

        return max(0, min(100, score))

    def generate_trading_signal(
        self, analysis: StockAnalysis
    ) -> Optional[TradingSignal]:
        """生成交易信號"""
        # 檢查是否有足夠的分析數據
        if not analysis.dcf_intrinsic_value:
            return None

        # 獲取歷史交易績效
        historical_performance = self._get_stock_historical_performance(
            analysis.stock_code
        )

        # 買入信號條件
        if (
            analysis.dcf_discount
            and analysis.dcf_discount > self.min_dcf_discount
            and analysis.overall_score > 60
        ):

            confidence = min(95, analysis.overall_score + (analysis.dcf_discount * 100))
            target_price = analysis.dcf_intrinsic_value * 0.95  # 目標價設為內在價值95%
            stop_loss = analysis.current_price * 0.85  # 停損設為15%

            reasoning = self._generate_buy_reasoning(analysis, historical_performance)
            risk_level = self._assess_risk_level(analysis)

            return TradingSignal(
                stock_code=analysis.stock_code,
                signal_type=SignalType.DCF_UNDERVALUED,
                action=TradeType.BUY,
                confidence=confidence,
                target_price=target_price,
                stop_loss=stop_loss,
                reasoning=reasoning,
                risk_level=risk_level,
            )

        # 賣出信號條件
        elif (
            analysis.dcf_discount
            and analysis.dcf_discount < -0.1
            and analysis.overall_score < 40
        ):

            confidence = min(
                95, 100 - analysis.overall_score + abs(analysis.dcf_discount * 100)
            )
            target_price = analysis.dcf_intrinsic_value * 1.05  # 目標價設為內在價值105%

            reasoning = self._generate_sell_reasoning(analysis, historical_performance)
            risk_level = self._assess_risk_level(analysis)

            return TradingSignal(
                stock_code=analysis.stock_code,
                signal_type=SignalType.DCF_OVERVALUED,
                action=TradeType.SELL,
                confidence=confidence,
                target_price=target_price,
                reasoning=reasoning,
                risk_level=risk_level,
            )

        return None

    def _get_stock_historical_performance(self, stock_code: str) -> Dict[str, Any]:
        """獲取股票歷史交易績效"""
        trades = self.trade_recorder.get_trades_by_stock(stock_code)
        closed_trades = [t for t in trades if t.realized_pnl is not None]
        if not closed_trades:
            return {"win_rate": 0, "avg_return": 0, "trade_count": 0}

        winning_trades = [
            t
            for t in closed_trades
            if t.realized_pnl is not None and t.realized_pnl > 0
        ]
        returns = [
            t.return_percentage
            for t in closed_trades
            if t.return_percentage is not None
        ]

        return {
            "win_rate": len(winning_trades) / len(closed_trades) * 100,
            "avg_return": statistics.mean(returns) if returns else 0,
            "trade_count": len(closed_trades),
            "last_trade_days": (
                (datetime.now() - closed_trades[-1].exit_time).days
                if closed_trades and closed_trades[-1].exit_time
                else 999
            ),
        }

    def _generate_buy_reasoning(
        self, analysis: StockAnalysis, historical: Dict[str, Any]
    ) -> str:
        """生成買入建議理由"""
        reasons = []

        if analysis.dcf_discount and analysis.dcf_discount > 0.2:
            reasons.append(
                f"DCF估值顯示折價{analysis.dcf_discount:.1%}，具有良好安全邊際"
            )
        elif analysis.dcf_discount and analysis.dcf_discount > 0.1:
            reasons.append(f"DCF估值顯示折價{analysis.dcf_discount:.1%}，價格合理")

        if analysis.pe_ratio and analysis.pe_ratio < 15:
            reasons.append(f"PE比率{analysis.pe_ratio:.1f}偏低，估值吸引")

        if analysis.roe and analysis.roe > 0.12:
            reasons.append(f"ROE為{analysis.roe:.1%}，獲利能力強")

        if analysis.quality_score and analysis.quality_score > 70:
            reasons.append(f"財務數據品質良好({analysis.quality_score:.0f}分)")

        if historical["win_rate"] > 60 and historical["trade_count"] >= 3:
            reasons.append(f"歷史交易勝率{historical['win_rate']:.0f}%，表現良好")

        return "；".join(reasons) if reasons else "基本面指標符合買入條件"

    def _generate_sell_reasoning(
        self, analysis: StockAnalysis, historical: Dict[str, Any]
    ) -> str:
        """生成賣出建議理由"""
        reasons = []

        if analysis.dcf_discount and analysis.dcf_discount < -0.15:
            reasons.append(f"DCF估值顯示溢價{abs(analysis.dcf_discount):.1%}，價格偏高")

        if analysis.pe_ratio and analysis.pe_ratio > 30:
            reasons.append(f"PE比率{analysis.pe_ratio:.1f}偏高，估值過度")

        if analysis.debt_ratio and analysis.debt_ratio > 0.7:
            reasons.append(f"負債比率{analysis.debt_ratio:.1%}過高，財務風險大")

        if historical["win_rate"] < 40 and historical["trade_count"] >= 3:
            reasons.append(f"歷史交易勝率僅{historical['win_rate']:.0f}%，表現不佳")

        return "；".join(reasons) if reasons else "基本面指標建議賣出"

    def _assess_risk_level(self, analysis: StockAnalysis) -> str:
        """評估風險等級"""
        risk_score = 0

        # 估值風險
        if analysis.dcf_discount and abs(analysis.dcf_discount) > 0.3:
            risk_score += 1

        # 財務風險
        if analysis.debt_ratio and analysis.debt_ratio > 0.6:
            risk_score += 1

        # 數據品質風險
        if analysis.quality_score and analysis.quality_score < 50:
            risk_score += 1

        # PE風險
        if analysis.pe_ratio and analysis.pe_ratio > 35:
            risk_score += 1

        if risk_score >= 3:
            return "高"
        elif risk_score >= 1:
            return "中等"
        else:
            return "低"

    def get_portfolio_recommendations(
        self, portfolio_stocks: List[Dict[str, Any]]
    ) -> List[TradingSignal]:
        """獲取投資組合建議"""
        recommendations = []

        for stock_data in portfolio_stocks:
            if "stock_code" in stock_data and "current_price" in stock_data:
                analysis = self.analyze_stock(
                    stock_data["stock_code"], stock_data, stock_data["current_price"]
                )

                signal = self.generate_trading_signal(analysis)
                if signal:
                    recommendations.append(signal)

        # 按信心度排序
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        return recommendations

    def generate_market_insight(self) -> Dict[str, Any]:
        """生成市場洞察報告"""
        all_trades = self.trade_recorder.trades
        performance = self.trade_recorder.calculate_portfolio_performance()

        # 分析交易模式
        recent_trades = [
            t for t in all_trades if t.entry_time > datetime.now() - timedelta(days=30)
        ]

        signal_analysis = {}
        for trade in recent_trades:
            signal = trade.signal_type.value
            if signal not in signal_analysis:
                signal_analysis[signal] = {"count": 0, "avg_return": 0, "returns": []}
            signal_analysis[signal]["count"] += 1
            if trade.return_percentage:
                signal_analysis[signal]["returns"].append(trade.return_percentage)

        # 計算各信號平均回報
        for signal, data in signal_analysis.items():
            if data["returns"]:
                data["avg_return"] = statistics.mean(data["returns"])

        return {
            "overall_performance": performance,
            "recent_activity": {
                "trades_last_30_days": len(recent_trades),
                "signal_analysis": signal_analysis,
            },
            "market_sentiment": self._assess_market_sentiment(all_trades),
            "recommendations": {
                "top_strategy": self._identify_best_strategy(signal_analysis),
                "risk_warning": self._generate_risk_warnings(performance),
            },
        }

    def _assess_market_sentiment(self, trades: List[TradeEntry]) -> str:
        """評估市場情緒"""
        recent_trades = [
            t for t in trades if t.entry_time > datetime.now() - timedelta(days=15)
        ]

        if not recent_trades:
            return "中性"

        buy_trades = len([t for t in recent_trades if t.trade_type == TradeType.BUY])
        sell_trades = len(recent_trades) - buy_trades

        if buy_trades > sell_trades * 1.5:
            return "樂觀"
        elif sell_trades > buy_trades * 1.5:
            return "謹慎"
        else:
            return "中性"

    def _identify_best_strategy(self, signal_analysis: Dict[str, Any]) -> str:
        """識別最佳策略"""
        best_signal = None
        best_return = -float("inf")

        for signal, data in signal_analysis.items():
            if data["count"] >= 3 and data["avg_return"] > best_return:
                best_return = data["avg_return"]
                best_signal = signal

        return best_signal or "建議多元化策略"

    def _generate_risk_warnings(self, performance: Dict[str, Any]) -> List[str]:
        """生成風險警告"""
        warnings = []

        if performance["win_rate"] < 40:
            warnings.append("勝率偏低，建議檢視交易策略")

        if performance["total_trades"] > 0 and performance["total_pnl"] < 0:
            warnings.append("總體虧損，建議暫停交易並重新評估")

        open_trades = self.trade_recorder.get_open_trades()
        if len(open_trades) > 10:
            warnings.append("開倉部位過多，注意資金管理")

        return warnings


# 全局AI建議引擎實例
def create_ai_advisor(trade_recorder: TradeRecorder) -> AITradingAdvisor:
    """創建AI建議引擎實例"""
    return AITradingAdvisor(trade_recorder)
