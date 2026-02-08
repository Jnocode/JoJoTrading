
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

    def analyze_impact_batch(self, news_items: List[Dict]) -> List[Dict]:
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
            
            if cached_result:
                # HIT
                item['analysis'] = cached_result
                results_map[news_id] = item
                logger.info(f"Cache HIT for {news_id}")
            else:
                # MISS, add to queue
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
                for item in items_to_analyze:
                     single_res = self._analyze_single(
                         item.get('data', {}).get('content', '') or item.get('content', ''),
                         item.get('time', '')
                     )
                     batch_results.append(single_res)
                
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
            "sectors": ["Sector1", "Sector2"],
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
            
            # Robust JSON extraction using Regex
            import re
            match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                # Fallback: try raw parse if regex fails (unlikely if it contains JSON)
                return json.loads(raw_content)

        except Exception as e:
            logger.error(f"AI Call failed or Parse failed: {e}")
            return self._get_mock_analysis(f"AI Error: {str(e)[:20]}")
