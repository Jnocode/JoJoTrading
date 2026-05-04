"""
Analysis Controller
統整個股的詳細技術面 (K線、均線) 與基本、籌碼面資訊。
將這些硬資料 (Raw Data) 轉化為結構化的 Prompt，交給 AI 產生「技術籌碼共振雷達」診斷報告。
"""

import logging
from typing import Dict, Any, Optional, Tuple
from jojo_trading.utils.ai_client import AIClient
from jojo_trading.analysis.backtest.data_adapter import BacktestDataAdapter
from jojo_trading.core.stock_database import StockDatabase
try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger(__name__)

class AnalysisController:
    def __init__(self):
        self.db = StockDatabase()
        self.ai_client = AIClient()
        
    def fetch_data_and_analyze(self, stock_code: str) -> Tuple[Dict[str, Any], str]:
        """
        1. 撈取 K 線與籌碼歷史資料 (BacktestDataAdapter)
        2. 撈取基本面 (yfinance)
        3. 彙整資料並請 AI 進行綜合診斷
        回傳: (綜合資料字典, 錯誤訊息)
        """
        logger.info(f"AnalysisController starting fetch for {stock_code}")
        
        # 1. Fetch Price & Flow Data
        try:
            data_map = BacktestDataAdapter.get_kline_data(stock_code, period="1y", interval="1d")
            if not data_map or 'daily' not in data_map or data_map['daily'].empty:
                return {}, f"找不到 {stock_code} 的歷史行情資料"
            
            df = data_map['daily']
        except Exception as e:
            logger.error(f"K-line fetch error: {e}")
            return {}, f"資料拉取失敗: {str(e)}"
            
        # 2. Fetch Fundamental Data — 優先從 stocks.db 讀取，確保與掃描模組資料源一致
        shares = 10.0
        net_income = 10.0
        company_name = stock_code
        intrinsic_value = 0.0
        db_data_source = None
        
        # 2a. 先從 stocks.db 讀取 (與掃描模組相同資料源)
        try:
            db_record = self.db.get_stock(stock_code)
            if db_record:
                company_name = db_record.get('name', stock_code)
                intrinsic_value = float(db_record.get('intrinsic_value', 0) or 0)
                db_data_source = db_record.get('data_source', '')
                
                # FCF -> 反推 net_income (億元)
                fcf_raw = float(db_record.get('fcf', 0) or 0)
                if fcf_raw > 0:
                    net_income = fcf_raw  # auto_fetcher 已以「億」為單位存儲
                
                # 市值 -> 反推流通股數 (億股)
                market_cap = float(db_record.get('market_cap', 0) or 0)
                price_db = float(db_record.get('price', 0) or 0)
                if market_cap > 0 and price_db > 0:
                    shares = market_cap / price_db  # 市值(億) / 股價 = 億股
                
                logger.info(f"DB data loaded for {stock_code}: intrinsic={intrinsic_value:.1f}, fcf={fcf_raw:.1f}")
        except Exception as e:
            logger.warning(f"stocks.db read failed for {stock_code}: {e}")
        
        # 2b. 如果 DB 沒有資料，退回 yfinance (Fallback)
        if intrinsic_value == 0 and yf:
            ticker_symbol = stock_code
            if stock_code.isdigit():
                ticker_symbol = f"{stock_code}.TW"
            
            try:
                ticker = yf.Ticker(ticker_symbol)
                yf_info = ticker.info
                
                if not company_name or company_name == stock_code:
                    company_name = yf_info.get('shortName', stock_code)
                shares_raw = yf_info.get('sharesOutstanding', 1000000000)
                shares = shares_raw / 100000000.0 if shares_raw else 10.0
                
                income_raw = yf_info.get('netIncomeToCommon', 1000000000)
                net_income = income_raw / 100000000.0 if income_raw else 10.0
                db_data_source = 'yfinance_fallback'
                logger.info(f"yfinance fallback for {stock_code}: net_income={net_income:.1f}")
            except Exception as e:
                logger.warning(f"yfinance fundamental fetch failed for {stock_code}: {e}")
        
        # 3. Compile Info Dictionary
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else last_row
        
        # If today's chips are 0 (likely missing intraday), use yesterday's
        f_buy = last_row.get('Foreign_Buy', 0)
        t_buy = last_row.get('IT_Buy', 0)
        if f_buy == 0 and t_buy == 0 and len(df) > 1:
            f_buy = prev_row.get('Foreign_Buy', 0)
            t_buy = prev_row.get('IT_Buy', 0)
            
        import math
        rev_yoy = last_row.get('Revenue_YOY', 0)
        eps = last_row.get('EPS', 0)
        if pd.isna(rev_yoy): rev_yoy = 0
        if pd.isna(eps): eps = 0
        
        if (eps == 0 or rev_yoy == 0) and yf:
            try:
                ticker_symbol = f"{stock_code}.TW" if stock_code.isdigit() else stock_code
                tk = yf.Ticker(ticker_symbol)
                tk_info = tk.info
                if eps == 0:
                    eps = tk_info.get('trailingEps', 0) or tk_info.get('forwardEps', 0) or 0
                if rev_yoy == 0:
                    yoy = tk_info.get('revenueGrowth', 0)
                    if yoy:
                        rev_yoy = yoy * 100
            except Exception as e:
                logger.warning(f"Failed to fetch EPS/YoY from yfinance for {stock_code}: {e}")
        
        info = {
            'symbol': stock_code,
            'name': company_name,
            'price': last_row['close'],
            'change': ((last_row['close'] - prev_row['close']) / prev_row['close']) * 100 if len(df) > 1 else 0.0,
            'vol': last_row['volume'],
            'rev_yoy': rev_yoy,
            'eps': eps,
            'foreign_buy': f_buy,
            'trust_buy': t_buy,
            'shares': shares,
            'net_income': net_income,
            'intrinsic_value': intrinsic_value,
            'data_source': db_data_source,
        }
        
        # 4. Generate AI Diagnosis
        # 我們只取最近 5 天的資料給 AI 看趨勢，避免 Token 過多
        recent_df = df.tail(5).copy()
        import pandas as pd
        if 'date' in recent_df.columns:
            date_strs = pd.to_datetime(recent_df['date']).dt.strftime('%Y-%m-%d').tolist()
        else:
            date_strs = recent_df.index.strftime('%Y-%m-%d').tolist()
            
        closes = recent_df['close'].tolist()
        vols = recent_df['volume'].tolist()
        
        ai_prompt_data = {
            "Symbol": stock_code,
            "Latest Price": info['price'],
            "Daily Change %": f"{info['change']:.2f}%",
            "Recent 5 Days Close": list(zip(date_strs, closes)),
            "Recent 5 Days Vol": list(zip(date_strs, vols)),
            "Foreign Buy/Sell (Last 1Day)": info['foreign_buy'],
            "Investment Trust Buy/Sell": info['trust_buy'],
            "Revenue YOY %": info['rev_yoy'],
        }
        
        ai_report = self._get_technical_ai_insight(ai_prompt_data)
        
        result_bundle = {
            'df': df,
            'info': info,
            'ai_report': ai_report
        }
        
        return result_bundle, ""
        
    def _get_technical_ai_insight(self, market_data: Dict[str, Any]) -> str:
        """
        將技術與籌碼數據餵給 AI，產生「主力心理學」與「多空交戰」研判。
        """
        prompt = f"""
        你是一位縱橫台股市場二十年的「資深自營部主管」兼「量化交易架構師」。
        請根據以下提供的個股【價量數據、法人籌碼與基本面】，給出一份具備「主力思維、嚴謹推演、且不廢話」的共振雷達報告。

        【個股數據集】
        {market_data}

        【分析任務】
        1. **📊 盤面共振 (Technique Confluence)**: 分析目前的價量排列。是強勢噴發、末跌段反彈、還是高檔出貨？結合 5 日趨勢判斷支撐壓力位。
        2. **🧐 主力心理學 (Whale Psychology)**: 解析外資與投信的同步性。他們是在「對作」、「同步拉抬」還是在「底部承接」？投信是否在進行季底作帳或結帳？
        3. **🎯 核心行動決策 (Actionable Execution)**: 以 Tech Lead 的角度，給出一個勝率最高的操作策略 (例如：回測月線不破試單、突破轉折點進場、或持股減碼)。

        【報告要求】
        - 限制在 250 字內，直接輸出純文本。
        - 語氣要專業、冷靜、充滿實戰感。
        - 對於數據中明顯的異動 (如暴量、法人大買大賣) 必須點出原因。
        - 使用繁體中文回答。
        """
        
        try:
            response = self.ai_client.generate_content(prompt)
            if response.startswith("Error:"):
                return "⚠️ AI 分析服務異常，無法產生雷達報告。"
            return response.strip()
        except Exception as e:
            logger.error(f"Analysis AI Error: {e}")
            return f"⚠️ 產生共振報告時發生錯誤: {str(e)}"
