
import os
import json
import logging
from typing import List, Dict, Any
from jojo_trading.data_sources.news_cache import NewsCacheManager
# REPLACED Groq with robust AIClient
from jojo_trading.utils.ai_client import AIClient

# Configure logging
logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """
    Analyzes financial news for market impact using the Centralized AIClient.
    Supports Model Fallback (Gemini 2.0 -> 1.5) and Rate Limit handling.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the analyzer with AIClient.
        """
        # AIClient handles env vars internally, but we keep this for compatibility
        self.ai_client = AIClient() 
        self.cache_manager = NewsCacheManager()

    def analyze_impact_batch(self, news_items: List[Dict], progress_callback=None) -> List[Dict]:
        """
        Analyze a batch of news items with Caching.
        """
        results_map = {} # Map ID -> Item with Analysis
        items_to_analyze = []
        
        # 1. Check Cache
        for item in news_items:
            news_id = item.get('id')
            content = item.get('data', {}).get('content', '') or item.get('content', '')
            
            # Try Cache
            cached_result = self.cache_manager.get_analysis(news_id)
            
            # Check if cache is valid (not an error message)
            is_valid_cache = False
            if cached_result:
                summary = cached_result.get('summary', '')
                if "無法分析" not in summary and "JSON 格式錯誤" not in summary and "AI Error" not in summary:
                    is_valid_cache = True
            
            if is_valid_cache:
                # HIT
                item['analysis'] = cached_result
                results_map[news_id] = item
                logger.info(f"Cache HIT for {news_id}")
            else:
                # MISS or Invalid Cache (Re-analyze)
                if cached_result:
                    logger.info(f"Cache HIT but invalidated (Error detected) for {news_id}")
                
                if content:
                    items_to_analyze.append(item)
                else:
                    item['analysis'] = self._get_mock_analysis("No Content")
                    results_map[news_id] = item

        # 2. Batch Call for Missing Items
        if items_to_analyze:
            logger.info(f"Batch analyzing {len(items_to_analyze)} items...")
            
            try:
                # Since Gemini might not support JSON mode strictly in all fallback models,
                # we will try to analyze them one by one or in smaller batches if needed.
                # For robust fallback, let's simply loop them for now OR construct a big prompt.
                # A big prompt is riskier for JSON parsing on weaker models (like 1.5 flash).
                # Strategy: Use loop for robustness. Rate limit handler in AIClient will manage the speed.
                
                batch_results = []
                total_to_analyze = len(items_to_analyze)
                for i, item in enumerate(items_to_analyze):
                     if progress_callback:
                         progress_callback(i, total_to_analyze, f"AI 分析中... ({i}/{total_to_analyze})")
                     single_res = self._analyze_single(
                         item.get('data', {}).get('content', '') or item.get('content', ''),
                         item.get('time', '')
                     )
                     batch_results.append(single_res)
                     if progress_callback:
                         progress_callback(i + 1, total_to_analyze, f"AI 分析中... ({i+1}/{total_to_analyze})")
                
                # 3. Merge and Save
                for item, analysis in zip(items_to_analyze, batch_results):
                    news_id = item.get('id')
                    item['analysis'] = analysis
                    results_map[news_id] = item
                    
                    # Save Cache
                    self.cache_manager.save_analysis(
                        news_id, 
                        item.get('time', ''), 
                        item.get('data', {}).get('content', '') or item.get('content', ''), 
                        analysis
                    )
            except Exception as e:
                logger.error(f"Analysis Loop Failed: {e}")
                for item in items_to_analyze:
                    item['analysis'] = self._get_mock_analysis(f"Error: {e}")
                    results_map[item.get('id')] = item
        
        # Return in original order
        final_list = []
        for item in news_items:
            final_list.append(results_map.get(item.get('id'), item))
            
        return final_list

    def _get_mock_analysis(self, reason):
        return {
            "sentiment": "Neutral",
            "heat_score": 0,
            "sectors": [],
            "summary": f"⚠️ 無法分析: {reason}",
            "affected_stocks": []
        }

    def _analyze_single(self, content: str, timestamp: str) -> Dict[str, Any]:
        """
        Send a single news item to AIClient.
        """
        prompt = f"""
        You are a financial analyst expert in global markets (Taiwan/US Stocks).
        Analyze the following news impact.
        
        News: "{content}"
        Time: {timestamp}
        
        Output valid JSON only (no markdown, no backticks).
        Valid JSON Structure:
        {{
            "sentiment": "Bullish" | "Bearish" | "Neutral",
            "heat_score": 0-100 (Integer),
            "sectors": ["板塊名稱用繁體中文, e.g. 能源、金融、科技、半導體、國防、汽車"],
            "summary": "Traditional Chinese summary (繁體中文總結)",
            "affected_stocks": [
                {{
                    "ticker": "Stock Code",
                    "name": "Company Name",
                    "market": "TW" or "US",
                    "role": "Direct" or "Supply Chain",
                    "sentiment": "Bullish" or "Bearish" or "Neutral",
                    "correlation_percentage": 0-100
                }}
            ]
        }}
        """
        
        try:
            # Use the Robust Client
            raw_content = self.ai_client.generate_content(prompt)
            
            # Check for empty response
            if not raw_content or not raw_content.strip():
                logger.warning("AI returned empty response")
                return self._get_mock_analysis("AI 無回應 (Empty)")
                
            # Check for AIClient error message
            if raw_content.startswith("Error:"):
                logger.error(f"AI Client Error: {raw_content}")
                return self._get_mock_analysis(f"AI 連線失敗: {raw_content}")
            
            # 增強型 JSON 清洗 (Robust JSON Stripping)
            cleaned_content = raw_content.strip()
            # 移除 markdown 區塊格式 (```json ... ```)
            if cleaned_content.startswith("```"):
                lines = cleaned_content.split('\n')
                if len(lines) >= 2:
                    if lines[0].startswith("```"):
                        lines = lines[1:]  # 去除首行 ```json
                    if lines[-1].strip() == "```":
                        lines = lines[:-1] # 去除尾行 ```
                cleaned_content = '\n'.join(lines).strip()

            import re
            # 嘗試直接解析
            try:
                return json.loads(cleaned_content)
            except json.JSONDecodeError:
                # 若直接解析失敗，嘗試用 Regex 從內容中硬塞出 JSON dictionary 區塊
                match = re.search(r'\{.*\}', cleaned_content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    return json.loads(json_str)
                else:
                    raise ValueError("Cannot extract JSON structure from raw text.")

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"AI Call failed or JSON Parse Error: {error_type} - {e}")
            logger.debug(f"Raw Output causing error: {raw_content if 'raw_content' in locals() else 'N/A'}")
            if "JSONDecodeError" in error_type:
                return self._get_mock_analysis("JSON 格式錯誤，AI 反應不合規律")
            return self._get_mock_analysis(f"{error_type}: {str(e)[:30]}")

    def summarize_market(self, analyzed_news: List[Dict]) -> str:
        """
        Produce a market overview based on the current batch of analyzed news.
        """
        if not analyzed_news:
            return "目前無足夠的新聞資料進行大盤總結。"
            
        # Extract summaries from news to feed the AI
        news_summaries = []
        for i, item in enumerate(analyzed_news):
            # Take only the first 10 items if batch is too large to save tokens
            if i >= 10: break
            summary = item.get('analysis', {}).get('summary', item.get('data', {}).get('content', item.get('content', '')))
            news_summaries.append(f"[{i+1}] {summary}")
            
        news_text = "\n".join(news_summaries)
        
        prompt = f"""
        你是一位資深的金融市場分析師。請根據以下最新的重點新聞，撰寫一份精簡的「AI 市場總結與趨勢前瞻」。
        請務必使用 Markdown 進行排版（例如：使用條列式重點、粗體字強調關鍵字、適當的分段），讓內容易於閱讀，不要只是輸出單一長文字。語氣要客觀專業，抓出最重要的資金流向與市場情緒。

        重點新聞內容：
        {news_text}
        """
        
        try:
            summary = self.ai_client.generate_content(prompt)
            if not summary or summary.startswith("Error:"):
                return "AI 大盤總結產生失敗，或目前選擇的 AI 服務回應異常。"
            return summary.strip()
        except Exception as e:
            logger.error(f"Market Summarization Failed: {e}")
            return "無法產生總覽報告。"

    def summarize_market_with_stats(self, news_items: List[Dict], stats_items: List[Dict] = None) -> Dict[str, Any]:
        """
        Produce a market overview and dashboard stats in one AI call.

        This supports fast-refresh mode: pending raw news can update the
        sentiment distribution without waiting for per-item analysis.
        """
        stats_items = news_items if stats_items is None else stats_items
        if not news_items:
            return {
                "summary": "目前無足夠的新聞資料進行大盤總結。",
                "stats": self._empty_dashboard_stats(),
                "stats_valid": True,
            }

        news_lines = []
        total_items = min(len(news_items), 15)
        for i, item in enumerate(news_items[:total_items]):
            analysis = item.get("analysis", {})
            text = (
                analysis.get("summary")
                or item.get("data", {}).get("content")
                or item.get("content")
                or ""
            )
            if text:
                news_lines.append(f"[{i + 1}] {text}")

        stats_lines = []
        total_stats_items = min(len(stats_items), 15)
        for i, item in enumerate(stats_items[:total_stats_items]):
            text = (
                item.get("data", {}).get("content")
                or item.get("content")
                or item.get("analysis", {}).get("summary")
                or ""
            )
            if text:
                stats_lines.append(f"[{i + 1}] {text}")

        news_text = "\n".join(news_lines)
        stats_text = "\n".join(stats_lines) if stats_lines else "（無未逐則分析快訊，統計請回 0 多 / 0 空 / 中性）"
        prompt = f"""
        你是一位資深金融市場分析師。請根據以下最新快訊，直接做「整體市場總覽」，
        並同時估算左側儀表板需要的多空統計。

        請只輸出 valid JSON，不要 markdown code block，不要額外文字。
        JSON 結構：
        {{
            "summary_markdown": "繁體中文 Markdown，包含趨勢、風險、總結，精簡但有判斷",
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "total_count": 0,
            "heat_score": 0-100,
            "top_sectors": [
                {{"name": "板塊名稱", "count": 1}}
            ]
        }}

        統計規則：
        - summary_markdown 請參考「總覽用快訊內容」的全部資料。
        - bullish_count / bearish_count 只針對「統計用快訊內容」計算。
        - neutral_count 是統計用快訊中沒有明確多空方向、影響有限、或資料不足的則數。
        - total_count 必須等於統計用快訊內容的則數。
        - bullish_count + bearish_count + neutral_count 必須等於 total_count。
        - 統計用快訊內容只包含尚未逐則 AI 分析的快訊；不要把總覽用快訊中的已分析摘要重複計入。
        - 對每則快訊判斷主要影響；未明確偏多或偏空者不要計入多/空，請計入 neutral_count。
        - heat_score 以 50 為中性；越偏多越高，越偏空越低。
        - top_sectors 最多 5 個，板塊名稱請用繁體中文。

        總覽用快訊內容：
        {news_text}

        統計用快訊內容：
        {stats_text}
        """

        try:
            raw_content = self.ai_client.generate_content(prompt)
            if not raw_content or raw_content.startswith("Error:"):
                raise ValueError(raw_content or "AI empty response")

            data = self._parse_json_object(raw_content)
            stats = self._normalize_overview_stats(data, expected_total=total_stats_items)
            summary = data.get("summary_markdown") or data.get("summary") or ""
            if not summary:
                summary = self.summarize_market(news_items)

            return {"summary": summary.strip(), "stats": stats, "stats_valid": True}
        except Exception as e:
            logger.error(f"Market overview with stats failed: {e}")
            return {
                "summary": self.summarize_market(news_items),
                "stats": self._empty_dashboard_stats(),
                "stats_valid": False,
            }

    def _parse_json_object(self, raw_content: str) -> Dict[str, Any]:
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _normalize_overview_stats(self, data: Dict[str, Any], expected_total: int = None) -> Dict[str, Any]:
        def as_int(value, default=0):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return default

        sectors = []
        for item in data.get("top_sectors", []) or []:
            if isinstance(item, dict):
                name = item.get("name") or item.get("sector")
                count = as_int(item.get("count"), 1)
            elif isinstance(item, (list, tuple)) and item:
                name = item[0]
                count = as_int(item[1] if len(item) > 1 else 1, 1)
            else:
                name = str(item)
                count = 1
            if name:
                sectors.append((str(name), max(count, 1)))

        bullish = max(as_int(data.get("bullish_count")), 0)
        bearish = max(as_int(data.get("bearish_count")), 0)
        total = max(as_int(data.get("total_count"), expected_total or 0), 0)
        neutral = max(as_int(data.get("neutral_count"), total - bullish - bearish), 0)

        if expected_total is not None:
            total = expected_total
            neutral = max(total - bullish - bearish, 0)
        elif total < bullish + bearish + neutral:
            total = bullish + bearish + neutral

        return {
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
            "total": total,
            "heat_score": min(max(as_int(data.get("heat_score"), 50), 0), 100),
            "top_sectors": sectors[:5],
        }

    def _empty_dashboard_stats(self) -> Dict[str, Any]:
        return {
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
            "total": 0,
            "heat_score": 50,
            "top_sectors": [],
        }

