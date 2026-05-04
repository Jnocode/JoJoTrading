"""
Backtest Controller
負責統整回測引擎 (BacktestEngine) 的邏輯，並將回測產生的績效指標餵給 AI，
產生一份「策略健檢診斷書 (Strategy Doctor Report)」，最後一併回傳給 UI 層。
"""

import logging
from typing import Dict, Any, Optional, Callable
from jojo_trading.analysis.backtest.engine import BacktestEngine
from jojo_trading.utils.ai_client import AIClient

logger = logging.getLogger(__name__)

class BacktestController:
    def __init__(self):
        self.ai_client = AIClient()
        
    def run_backtest_with_diagnosis(
        self,
        stock_code: str,
        buy_strat: str,
        sell_strat: str,
        initial_capital: float,
        start_date: str,
        end_date: str,
        interval: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        執行回測並附加 AI 診斷。
        1. 呼叫原始 BacktestEngine 進行回測計算。
        2. 若回測成功，將統計數據抽離餵給 Gemini 撰寫診斷。
        3. 將診斷結果附加到回傳字典中 ('ai_diagnosis')。
        """
        logger.info(f"Starting Backtest & Diagnosis for {stock_code}")
        
        # 1. 執行核心回測引擎
        engine = BacktestEngine(initial_capital=initial_capital)
        result = engine.run(
            stock_code,
            buy_strat,
            sell_strat,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            progress_callback=progress_callback
        )
        
        if 'error' in result:
            return result
            
        # 2. 準備給 AI 的統計數據
        metrics = {
            "Symbol": stock_code,
            "Total Trades": result.get('total_trades', 0),
            "Win Rate": f"{result.get('win_rate', 0):.2f}%",
            "Total Return": f"{result.get('total_return_pct', 0):.2f}%",
            "Max Drawdown": f"{result.get('max_drawdown_pct', 0):.2f}%",
            "Sharpe Ratio": f"{result.get('sharpe_ratio', 0):.2f}",
            "Profit Factor": f"{result.get('profit_factor', 0):.2f}",
            "Buy Logic": buy_strat,
            "Sell Logic": sell_strat
        }
        
        # 通知 UI 回測算完了，開始問 AI (佔用最後的進度條)
        if progress_callback:
            progress_callback(90)
            
        # 3. 呼叫 AI 醫生進行診斷
        diagnosis = self._get_ai_diagnosis(metrics)
        result['ai_diagnosis'] = diagnosis
        
        if progress_callback:
            progress_callback(100)
            
        return result
        
    def _get_ai_diagnosis(self, metrics: Dict[str, Any]) -> str:
        """
        將回測數據轉為 Prompt，請 AI 擔任量化分析師提供診斷與優化建議。
        """
        prompt = f"""
        你是一位華爾街頂尖的「量化交易策略健檢醫生 (Strategy Doctor)」。
        請根據以下客戶提供的【歷史回測績效指標】與【進出場邏輯】，給予一份「無情、直接、強調實戰風險」的健檢報告。

        【回測數據與邏輯】
        {metrics}

        【報告要求格式】 (請勿使用 markdown code blocks, 直接純文本輸出)
        1. **🩺 綜合診斷 (Overall Verdict)**: (一句話總結這個策略的可用性，例如：風險過高、表現平庸、具備潛力等)
        2. **⚠️ 致命盲點 (Critical Flaws)**: (點出勝率、回撤或進出場條件中最危險的問題所在)
        3. **💡 優化處方箋 (Optimization Prescription)**: (給出具體建議，例如：加入停損、改變均線參數、加入籌碼濾網過濾假突破等)

        請注意：
        - 如果交易次數 (Total Trades) 低於 5 次，請嚴厲指出樣本數不足，結果不具參考價值。
        - 如果最大回撤 (Max Drawdown) > 20%，請警告這會讓投資人抱不住。
        - 如果獲利因子 (Profit Factor) < 1.0，直接宣判此策略為無效策略。
        - 使用繁體中文回答。
        """
        
        try:
            response = self.ai_client.generate_content(prompt)
            if response.startswith("Error:"):
                logger.error(f"AI Diagnosis Failed: {response}")
                return "⚠️ AI 診斷服務暫時不可用，請稍後再試。"
            return response.strip()
        except Exception as e:
            logger.error(f"Exception during AI diagnosis: {e}")
            return f"⚠️ 產生診斷報告時發生錯誤: {str(e)}"
