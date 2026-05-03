
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
        你是一位資深的金融市場分析師。請根據以下最新的重點新聞，撰寫一段 100~150 字的「AI 市場總結與趨勢前瞻」。
        請直接輸出一段連貫的繁體中文文字，不要使用複雜的 Markdown，不要條列式，語氣要客觀專業，抓出最重要的資金流向與市場情緒。

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

