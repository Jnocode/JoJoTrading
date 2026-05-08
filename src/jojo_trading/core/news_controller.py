"""
News Controller

作為前端 (Streamlit / PySide6 Desktop) 獲取新聞流、整合 AI 分析與即時股價的單一入口。
嚴格遵守 MVC 模式，確保 UI 層不再依賴具體的爬蟲與運算邏輯。
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from jojo_trading.data_sources.jin10_mcp import Jin10MCPClient
from jojo_trading.analysis.news_ai import NewsAnalyzer

logger = logging.getLogger(__name__)

class NewsController:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if NewsController._initialized:
            return
        self.client = Jin10MCPClient()
        self.analyzer = NewsAnalyzer()
        NewsController._initialized = True
        logger.info("NewsController singleton created.")

    def get_analyzed_news_batch(self, limit: int = 5, since_dt: Optional[datetime] = None, progress_callback=None) -> Tuple[List[Dict[str, Any]], str]:
        """
        獲取最新新聞，透過 AI 分析，並附加上 Yahoo Finance 即時股價
        
        Returns:
            Tuple[List[Dict], str]: (被處理後的新聞列表, 錯誤訊息字串(若為空代表成功))
        """
        error_msg = ""
        raw_news = []
        try:
            if since_dt:
                logger.info(f"NewsController: Fetching news since {since_dt}.")
                raw_news = self.client.fetch_news_since(since_dt)
            else:
                logger.info(f"NewsController: Fetching top {limit} news raw data.")
                raw_news = self.client.fetch_latest_news(limit=limit)
        except Exception as e:
            error_msg = f"News Fetch Error: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

        if not raw_news:
            return [], "No news fetched."

        # 調用 AI 做情緒與影響分析 (內建快取與 Batch 邏輯)
        analyzed_news = []
        try:
            logger.info("NewsController: Requesting AI impact analysis.")
            if progress_callback:
                progress_callback(0, 0, "比對快取與準備分析清單...")
            analyzed_news = self.analyzer.analyze_impact_batch(raw_news, progress_callback=progress_callback)
        except Exception as e:
            error_msg = f"AI Analysis Failed: {str(e)}"
            logger.error(error_msg)
            # 退後防守: 吐出沒有額外分析內容的 raw_news
            analyzed_news = raw_news

        # 結合股票即時報價
        logger.info("NewsController: Fetching price snapshots for affected stocks.")
        analyzed_news = self._enrich_price_data(analyzed_news)

        return analyzed_news, error_msg

    def _normalize_yf_ticker(self, ticker: str, market: str) -> str:
        """
        將 AI 回傳的 ticker 正規化為 yfinance 可識別的格式。
        
        AI 常見的格式問題：
        - 帶交易所前綴: "TPE:2330", "US:MSFT", "TW:2379", "TYO:9001", "OTC:USGAF"
        - 純代碼但無後綴: "2330" (TW stock), "9988" (HK stock)
        - 指數格式不對: "^TWII", "^DXI", "SPX"
        - 外匯/非股票: "USDCNH", "TWGHY2021"
        """
        if not ticker:
            return ""
        
        # 0. 常見別名映射 (AI 常犯的錯誤)
        TICKER_ALIASES = {
            'SPX': '^GSPC',      # S&P 500
            'DXI': '^DXY',       # US Dollar Index
            'TDI': '',           # 無效指數, 跳過
            'TWII': '^TWII',     # 台灣加權指數
            'RTN': 'RTX',        # Raytheon → RTX (合併後)
        }
        
        # AI 回傳為 US ADR 但標 market=TW 的常見錯誤
        US_ADR_TICKERS = {
            'TSM', 'UMC', 'ASX', 'CHT', 'HIMX',  # 台灣 ADR
            'BABA', 'JD', 'PDD', 'NIO', 'BIDU',   # 中國 ADR
        }
            
        # 1. 去除交易所前綴 (TPE:, US:, TW:, TYO:, OTC:, HK:, NYSE:, NASDAQ: 等)
        if ':' in ticker:
            ticker = ticker.split(':')[-1]
        
        # 去除 ^ 後查別名 (^DXI → DXI → ^DXY)
        bare = ticker.lstrip('^')
        if bare.upper() in TICKER_ALIASES:
            mapped = TICKER_ALIASES[bare.upper()]
            return mapped  # 空字串 = 跳過
        
        # 2. 跳過明顯的非股票代碼
        skip_patterns = ['USD', 'EUR', 'GBP', 'JPY', 'CNH', 'CNY', 'GHY', 'XAU', 'XAG', 'TWG']
        ticker_upper = ticker.upper()
        for pat in skip_patterns:
            if ticker_upper.startswith(pat) and len(ticker_upper) >= 6:
                return ""  # 可能是外匯對 (USDCNH) 或非標準代碼
        
        # 3. 修正 AI 常見的 market 誤標 (如 TSM 標為 TW，但實際是美股 ADR)
        market_upper = (market or "").upper()
        if ticker_upper in US_ADR_TICKERS:
            return ticker  # 直接回傳純 ticker (美股不加後綴)
        
        # 4. 已有正確後綴的直接回傳
        if ticker.endswith(('.TW', '.TWO', '.HK', '.T', '.L', '.SS', '.SZ')):
            return ticker
            
        # 指數類 (^TWII, ^GSPC 等) 不加後綴
        if ticker.startswith('^'):
            return ticker
        
        # 5. 智慧判斷：純數字 6 位開頭 → 中國 A 股 (.SS/.SZ)
        if ticker.isdigit() and len(ticker) == 6:
            if ticker.startswith(('6',)):
                return f"{ticker}.SS"  # 上海
            elif ticker.startswith(('0', '3')):
                return f"{ticker}.SZ"  # 深圳
        
        # 6. 根據 market 欄位加上正確後綴   
        if market_upper == 'TW':
            return f"{ticker}.TW"
        elif market_upper == 'HK':
            return f"{ticker}.HK"
        elif market_upper in ('US', 'NYSE', 'NASDAQ', ''):
            return ticker
        elif market_upper in ('JP', 'TYO'):
            # 日股：.T
            return f"{ticker}.T"
        else:
            return ticker

    def _enrich_price_data(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用 yfinance 為新聞受影響的個股加上最新價格
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance parsing missing, skipping price enrichment.")
            return items
            
        for item in items:
            analysis = item.get('analysis', {})
            affected = analysis.get('affected_stocks', [])
            for stock in affected:
                ticker = stock.get('ticker')
                market = stock.get('market', '')
                if ticker:
                    yf_ticker = self._normalize_yf_ticker(ticker, market)
                    if not yf_ticker:
                        logger.debug(f"Skipped non-stock ticker: {ticker}")
                        continue
                    try:
                        stock_info = yf.Ticker(yf_ticker).fast_info
                        price = stock_info.last_price
                        prev_close = stock_info.previous_close
                        
                        if price and prev_close:
                            change_pct = ((price - prev_close) / prev_close) * 100
                            stock['price_data'] = {
                                "price": price,
                                "change_pct": change_pct
                            }
                    except Exception as e:
                        logger.debug(f"Failed to fetch price for {yf_ticker} (raw: {ticker}): {e}")
        
        return items

    def calculate_dashboard_stats(self, analyzed_news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        匯總這些新聞，產出大盤熱點儀表板所需的數據
        """
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        total_heat = 0
        analyzed_count = 0
        top_sectors = {}

        for item in analyzed_news:
            analysis_result = item.get('analysis', {})
            if analysis_result:
                sent = analysis_result.get('sentiment', 'Neutral')
                if sent == 'Bullish': bullish_count += 1
                elif sent == 'Bearish': bearish_count += 1
                else: neutral_count += 1
                
                score = analysis_result.get('heat_score', 0)
                if isinstance(score, int):
                    # 將 0-100 絕對熱度轉為 0-100 多空情緒力道 (50為中立基準)
                    if sent == 'Bullish':
                        fg_score = 50 + int(score / 2)
                    elif sent == 'Bearish':
                        fg_score = 50 - int(score / 2)
                    else:
                        fg_score = 50
                        
                    total_heat += fg_score
                    analyzed_count += 1
                
                sectors = analysis_result.get('sectors', [])
                for s in sectors:
                    top_sectors[s] = top_sectors.get(s, 0) + 1

        avg_heat = int(total_heat / analyzed_count) if analyzed_count > 0 else 50
        
        return {
            'bullish': bullish_count,
            'bearish': bearish_count,
            'neutral': neutral_count,
            'total': bullish_count + bearish_count + neutral_count,
            'heat_score': avg_heat,
            'top_sectors': sorted(top_sectors.items(), key=lambda x: x[1], reverse=True)[:3]
        }

    def fetch_raw_news(self, limit: int = 10, since_dt: Optional[datetime] = None, important_only: bool = False) -> Tuple[List[Dict[str, Any]], str]:
        """
        Phase 1: 只抓取原始新聞，不做任何 AI 分析。供 UI 立即顯示。
        important_only=True 時改為抓取編輯精選文章 (list_news)。
        """
        error_msg = ""
        raw_news = []
        try:
            if important_only:
                logger.info(f"NewsController: Fetching important articles (list_news).")
                raw_news = self.client.fetch_articles(limit=limit)
            elif since_dt:
                logger.info(f"NewsController: Fetching raw news since {since_dt}.")
                raw_news = self.client.fetch_news_since(since_dt)
            else:
                logger.info(f"NewsController: Fetching top {limit} raw news.")
                raw_news = self.client.fetch_latest_news(limit=limit)
        except Exception as e:
            error_msg = f"News Fetch Error: {str(e)}"
            logger.error(error_msg)
        return raw_news, error_msg

    def analyze_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: 對單一新聞做 AI 分析 + 股價附加。利用快取避免重複分析。
        """
        try:
            analyzed = self.analyzer.analyze_impact_batch([item])
            if analyzed:
                item = analyzed[0]
        except Exception as e:
            logger.error(f"Single item analysis failed: {e}")
            item['analysis'] = {
                "sentiment": "Neutral", "heat_score": 0, "sectors": [],
                "summary": f"⚠️ 分析失敗: {e}", "affected_stocks": []
            }
        self._enrich_price_data([item])
        return item

    def get_market_summary(self, analyzed_news: List[Dict[str, Any]]) -> str:
        """
        呼叫 AI Analyzer 進行整個大盤的重點總結
        """
        try:
            logger.info("NewsController: Generating market summary.")
            return self.analyzer.summarize_market(analyzed_news)
        except Exception as e:
            logger.error(f"NewsController: Error generating market summary - {e}")
            return "無法產生大盤總覽。"

    def get_market_summary_with_stats(
        self,
        summary_items: List[Dict[str, Any]],
        fallback_stats_items: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Generate the AI overview and let the overview AI update dashboard stats.

        If the structured overview cannot produce meaningful stats, fall back to
        the existing per-item analyzed-news aggregation.
        """
        fallback_stats_items = fallback_stats_items or []
        try:
            logger.info("NewsController: Generating market summary with dashboard stats.")
            pending_stats_items = [
                item for item in summary_items
                if not item.get("analysis")
            ]
            overview = self.analyzer.summarize_market_with_stats(
                summary_items,
                stats_items=pending_stats_items,
            )
            summary = overview.get("summary") or "無法產生大盤總覽。"
            exact_stats = self.calculate_dashboard_stats(fallback_stats_items)

            if not overview.get("stats_valid", False):
                return exact_stats, summary

            estimated_stats = overview.get("stats") if pending_stats_items else {}
            return self._combine_dashboard_stats(
                exact_stats,
                estimated_stats or {},
            ), summary
        except Exception as e:
            logger.error(f"NewsController: Error generating summary stats - {e}")
            return self.calculate_dashboard_stats(fallback_stats_items), "無法產生大盤總覽。"

    def _combine_dashboard_stats(
        self,
        exact_stats: Dict[str, Any],
        estimated_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        bullish = int(exact_stats.get("bullish", 0)) + int(estimated_stats.get("bullish", 0))
        bearish = int(exact_stats.get("bearish", 0)) + int(estimated_stats.get("bearish", 0))
        neutral = int(exact_stats.get("neutral", 0)) + int(estimated_stats.get("neutral", 0))
        total = int(exact_stats.get("total", 0)) + int(estimated_stats.get("total", 0))
        if total < bullish + bearish + neutral:
            total = bullish + bearish + neutral

        sectors = {}
        for source in (exact_stats.get("top_sectors", []), estimated_stats.get("top_sectors", [])):
            for item in source:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("sector")
                    count = item.get("count", 1)
                elif isinstance(item, (list, tuple)) and item:
                    name = item[0]
                    count = item[1] if len(item) > 1 else 1
                else:
                    name = str(item)
                    count = 1
                if not name:
                    continue
                try:
                    count = int(count)
                except (TypeError, ValueError):
                    count = 1
                sectors[str(name)] = sectors.get(str(name), 0) + max(count, 1)

        if total:
            heat_score = int(50 + ((bullish - bearish) / total) * 50)
        else:
            heat_score = 50

        return {
            "bullish": max(bullish, 0),
            "bearish": max(bearish, 0),
            "neutral": max(neutral, 0),
            "total": max(total, 0),
            "heat_score": min(max(heat_score, 0), 100),
            "top_sectors": sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:5],
        }

