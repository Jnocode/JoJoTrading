"""
AI交易建議引擎
結合DCF估值、財務指標和交易歷史，提供智能交易建議
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from .trade_recorder import TradeRecorder, TradeEntry, SignalType, TradeType
import statistics


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
    
    # DCF分析
    dcf_discount: Optional[float] = None  # 折價幅度
    quality_score: Optional[float] = None
    
    # 技術指標（預留）
    rsi: Optional[float] = None
    macd_signal: Optional[str] = None
    
    # 整體評分
    fundamental_score: float = 50.0  # 基本面評分 (0-100)
    technical_score: float = 50.0   # 技術面評分 (0-100)
    overall_score: float = 50.0     # 綜合評分 (0-100)


class AITradingAdvisor:
    """AI交易建議引擎"""
    
    def __init__(self, trade_recorder: TradeRecorder):
        self.trade_recorder = trade_recorder
        self.min_dcf_discount = 0.15  # 最小DCF折價要求15%
        self.max_pe_ratio = 25.0      # 最大合理PE比率
        self.min_roe = 0.08          # 最小ROE要求8%
        self.max_debt_ratio = 0.6    # 最大負債比率60%
    
    def analyze_stock(self, stock_code: str, financial_data: Dict[str, Any], 
                     current_price: float) -> StockAnalysis:
        """分析單一股票"""
        analysis = StockAnalysis(
            stock_code=stock_code,
            stock_name=financial_data.get('stock_name', stock_code),
            current_price=current_price
        )
        
        # 提取財務指標
        analysis.dcf_intrinsic_value = financial_data.get('intrinsic_value_per_share')
        analysis.pe_ratio = financial_data.get('pe_ratio')
        analysis.pb_ratio = financial_data.get('pb_ratio')
        analysis.roe = financial_data.get('roe')
        analysis.debt_ratio = financial_data.get('debt_ratio')
        analysis.quality_score = financial_data.get('validation_score', 50)
        
        # 計算DCF折價
        if analysis.dcf_intrinsic_value and analysis.dcf_intrinsic_value > 0:
            analysis.dcf_discount = (analysis.dcf_intrinsic_value - current_price) / analysis.dcf_intrinsic_value
        
        # 計算各項評分
        analysis.fundamental_score = self._calculate_fundamental_score(analysis)
        analysis.technical_score = self._calculate_technical_score(analysis)
        analysis.overall_score = (analysis.fundamental_score * 0.7 + analysis.technical_score * 0.3)
        
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
        
        # 數據品質評分 (20分)
        if analysis.quality_score is not None:
            quality_bonus = (analysis.quality_score - 50) / 2.5  # 50分為基準，每2.5分對應1分評分
            score += max(-10, min(20, quality_bonus))
        
        return max(0, min(100, score))
    
    def _calculate_technical_score(self, analysis: StockAnalysis) -> float:
        """計算技術面評分（目前簡化）"""
        # 這裡可以後續添加技術指標分析
        # 目前基於基本面給出簡單技術評分
        base_score = 50.0
        
        # 基於基本面強弱調整技術面評分
        if analysis.fundamental_score > 70:
            base_score += 10
        elif analysis.fundamental_score < 30:
            base_score -= 10
            
        return base_score
    
    def generate_trading_signal(self, analysis: StockAnalysis) -> Optional[TradingSignal]:
        """生成交易信號"""
        # 檢查是否有足夠的分析數據
        if not analysis.dcf_intrinsic_value:
            return None
        
        # 獲取歷史交易績效
        historical_performance = self._get_stock_historical_performance(analysis.stock_code)
        
        # 買入信號條件
        if (analysis.dcf_discount and analysis.dcf_discount > self.min_dcf_discount and 
            analysis.overall_score > 60):
            
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
                risk_level=risk_level
            )
        
        # 賣出信號條件
        elif (analysis.dcf_discount and analysis.dcf_discount < -0.1 and 
              analysis.overall_score < 40):
            
            confidence = min(95, 100 - analysis.overall_score + abs(analysis.dcf_discount * 100))
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
                risk_level=risk_level            )
        
        return None
    
    def _get_stock_historical_performance(self, stock_code: str) -> Dict[str, Any]:
        """獲取股票歷史交易績效"""
        trades = self.trade_recorder.get_trades_by_stock(stock_code)
        closed_trades = [t for t in trades if t.realized_pnl is not None]
        if not closed_trades:
            return {'win_rate': 0, 'avg_return': 0, 'trade_count': 0}
        
        winning_trades = [t for t in closed_trades if t.realized_pnl is not None and t.realized_pnl > 0]
        returns = [t.return_percentage for t in closed_trades if t.return_percentage is not None]
        
        return {
            'win_rate': len(winning_trades) / len(closed_trades) * 100,
            'avg_return': statistics.mean(returns) if returns else 0,
            'trade_count': len(closed_trades),
            'last_trade_days': (datetime.now() - closed_trades[-1].exit_time).days if closed_trades and closed_trades[-1].exit_time else 999
        }
    
    def _generate_buy_reasoning(self, analysis: StockAnalysis, historical: Dict[str, Any]) -> str:
        """生成買入建議理由"""
        reasons = []
        
        if analysis.dcf_discount and analysis.dcf_discount > 0.2:
            reasons.append(f"DCF估值顯示折價{analysis.dcf_discount:.1%}，具有良好安全邊際")
        elif analysis.dcf_discount and analysis.dcf_discount > 0.1:
            reasons.append(f"DCF估值顯示折價{analysis.dcf_discount:.1%}，價格合理")
        
        if analysis.pe_ratio and analysis.pe_ratio < 15:
            reasons.append(f"PE比率{analysis.pe_ratio:.1f}偏低，估值吸引")
        
        if analysis.roe and analysis.roe > 0.12:
            reasons.append(f"ROE為{analysis.roe:.1%}，獲利能力強")
        
        if analysis.quality_score and analysis.quality_score > 70:
            reasons.append(f"財務數據品質良好({analysis.quality_score:.0f}分)")
        
        if historical['win_rate'] > 60 and historical['trade_count'] >= 3:
            reasons.append(f"歷史交易勝率{historical['win_rate']:.0f}%，表現良好")
        
        return "；".join(reasons) if reasons else "基本面指標符合買入條件"
    
    def _generate_sell_reasoning(self, analysis: StockAnalysis, historical: Dict[str, Any]) -> str:
        """生成賣出建議理由"""
        reasons = []
        
        if analysis.dcf_discount and analysis.dcf_discount < -0.15:
            reasons.append(f"DCF估值顯示溢價{abs(analysis.dcf_discount):.1%}，價格偏高")
        
        if analysis.pe_ratio and analysis.pe_ratio > 30:
            reasons.append(f"PE比率{analysis.pe_ratio:.1f}偏高，估值過度")
        
        if analysis.debt_ratio and analysis.debt_ratio > 0.7:
            reasons.append(f"負債比率{analysis.debt_ratio:.1%}過高，財務風險大")
        
        if historical['win_rate'] < 40 and historical['trade_count'] >= 3:
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
    
    def get_portfolio_recommendations(self, portfolio_stocks: List[Dict[str, Any]]) -> List[TradingSignal]:
        """獲取投資組合建議"""
        recommendations = []
        
        for stock_data in portfolio_stocks:
            if 'stock_code' in stock_data and 'current_price' in stock_data:
                analysis = self.analyze_stock(
                    stock_data['stock_code'],
                    stock_data,
                    stock_data['current_price']
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
        recent_trades = [t for t in all_trades if 
                        t.entry_time > datetime.now() - timedelta(days=30)]
        
        signal_analysis = {}
        for trade in recent_trades:
            signal = trade.signal_type.value
            if signal not in signal_analysis:
                signal_analysis[signal] = {'count': 0, 'avg_return': 0, 'returns': []}
            signal_analysis[signal]['count'] += 1
            if trade.return_percentage:
                signal_analysis[signal]['returns'].append(trade.return_percentage)
        
        # 計算各信號平均回報
        for signal, data in signal_analysis.items():
            if data['returns']:
                data['avg_return'] = statistics.mean(data['returns'])
        
        return {
            'overall_performance': performance,
            'recent_activity': {
                'trades_last_30_days': len(recent_trades),
                'signal_analysis': signal_analysis
            },
            'market_sentiment': self._assess_market_sentiment(all_trades),
            'recommendations': {
                'top_strategy': self._identify_best_strategy(signal_analysis),
                'risk_warning': self._generate_risk_warnings(performance)
            }
        }
    
    def _assess_market_sentiment(self, trades: List[TradeEntry]) -> str:
        """評估市場情緒"""
        recent_trades = [t for t in trades if 
                        t.entry_time > datetime.now() - timedelta(days=15)]
        
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
        best_return = -float('inf')
        
        for signal, data in signal_analysis.items():
            if data['count'] >= 3 and data['avg_return'] > best_return:
                best_return = data['avg_return']
                best_signal = signal
        
        return best_signal or "建議多元化策略"
    
    def _generate_risk_warnings(self, performance: Dict[str, Any]) -> List[str]:
        """生成風險警告"""
        warnings = []
        
        if performance['win_rate'] < 40:
            warnings.append("勝率偏低，建議檢視交易策略")
        
        if performance['total_trades'] > 0 and performance['total_pnl'] < 0:
            warnings.append("總體虧損，建議暫停交易並重新評估")
        
        open_trades = self.trade_recorder.get_open_trades()
        if len(open_trades) > 10:
            warnings.append("開倉部位過多，注意資金管理")
        
        return warnings


# 全局AI建議引擎實例  
def create_ai_advisor(trade_recorder: TradeRecorder) -> AITradingAdvisor:
    """創建AI建議引擎實例"""
    return AITradingAdvisor(trade_recorder)
