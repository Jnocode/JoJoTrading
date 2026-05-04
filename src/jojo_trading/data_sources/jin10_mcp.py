import logging
import json
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Jin10MCPClient:
    """
    MCP Client wrapper for Jin10 data.
    Uses HTTP transport to communicate with the Jin10 MCP server.
    """
    def __init__(self):
        self.server_url = "https://mcp.jin10.com/mcp"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-6CW6gbuJOisYpoe4eqCSn_NGiiy1c72HqhSo98WYz0s"
        }
        self.session_id = None
        self._initialize_session()

    def _initialize_session(self):
        """Perform MCP initialization handshake."""
        try:
            # 1. Initialize
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "jojo-trading-client", "version": "1.0"}
                }
            }
            resp = requests.post(self.server_url, json=init_payload, headers=self.headers, timeout=10)
            resp.raise_for_status()
            
            # Extract session ID from headers
            self.session_id = resp.headers.get("mcp-session-id")
            if not self.session_id:
                logger.error("Failed to get mcp-session-id from Jin10 MCP server")
                return

            # Update headers with session ID
            self.headers["Mcp-Session-Id"] = self.session_id

            # 2. Notifications/initialized
            requests.post(self.server_url, json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }, headers=self.headers, timeout=5)
            
            logger.info("Jin10 MCP session initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Jin10 MCP session: {e}")

    def _call_tool(self, tool_name: str, arguments: dict, max_retries: int = 2) -> Any:
        for attempt in range(max_retries):
            if not self.session_id:
                self._initialize_session()
                if not self.session_id:
                    if attempt < max_retries - 1:
                        continue
                    return None
                    
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            try:
                resp = requests.post(self.server_url, json=payload, headers=self.headers, timeout=15)
                resp.raise_for_status()
                resp.encoding = 'utf-8'
                
                text = resp.text
                data_prefix = "data: "
                
                json_str = None
                for line in text.split("\n"):
                    if line.startswith(data_prefix):
                        json_str = line[len(data_prefix):]
                        break
                        
                if not json_str:
                    logger.warning("No JSON data found in MCP response, possibly expired session. Retrying...")
                    self.session_id = None
                    continue
                    
                result_json = json.loads(json_str)
                
                if "error" in result_json:
                    logger.error(f"MCP Tool {tool_name} error: {result_json['error']}")
                    return None
                    
                result_obj = result_json.get("result", {})
                
                structured_content = result_obj.get("structuredContent")
                if structured_content:
                    return structured_content
                    
                return result_obj.get("content", [])
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to call MCP tool {tool_name}: {e}")
                self.session_id = None
                if attempt == max_retries - 1:
                    logger.error(f"Failed to call MCP tool {tool_name} after {max_retries} attempts.")
                    return None

    @staticmethod
    def _inject_ids(items: List[Dict]) -> List[Dict]:
        """Inject stable 'id' into each item from its URL or timestamp."""
        for i, item in enumerate(items):
            if 'id' not in item or not item['id']:
                url = item.get('url', '')
                if '/detail/' in url:
                    item['id'] = url.split('/detail/')[-1]
                else:
                    item['id'] = f"jin10_{item.get('time', i)}"
        return items

    def fetch_latest_news(self, limit: int = 20) -> List[Dict]:
        """
        Fetch latest flash news (backward compatible).
        """
        try:
            logger.info(f"Fetching Jin10 news via MCP: list_flash (limit={limit})")
            all_news = []
            cursor = None
            
            while len(all_news) < limit:
                args = {}
                if cursor:
                    args["cursor"] = cursor
                    
                data = self._call_tool("list_flash", args)
                if not data or "data" not in data or "items" not in data["data"]:
                    logger.warning(f"MCP response missing expected structure: {data}")
                    break
                
                resp_data = data["data"]
                items = resp_data.get("items", [])
                if not items:
                    break
                    
                all_news.extend(items)
                
                if resp_data.get("has_more") and resp_data.get("next_cursor"):
                    cursor = resp_data["next_cursor"]
                else:
                    break
                    
            return self._inject_ids(all_news[:limit])
        except Exception as e:
            logger.exception(f"Error fetching Jin10 news via MCP: {e}")
            return []

    def fetch_articles(self, limit: int = 10) -> List[Dict]:
        """
        Fetch curated articles (list_news). These are editor-selected important items.
        Normalizes fields to match flash news structure for downstream compatibility.
        """
        try:
            logger.info("Fetching Jin10 articles via MCP: list_news")
            data = self._call_tool("list_news", {})
            if not data or "data" not in data or "items" not in data["data"]:
                logger.warning(f"MCP list_news response missing expected structure: {data}")
                return []
            
            items = data["data"].get("items", [])[:limit]
            # Normalize: map title+introduction -> content for downstream compatibility
            for item in items:
                title = item.get('title', '')
                intro = item.get('introduction', '')
                item['content'] = f"【{title}】{intro}" if title else intro
                item['is_article'] = True
            return self._inject_ids(items)
        except Exception as e:
            logger.exception(f"Error fetching Jin10 articles via MCP: {e}")
            return []

    def fetch_news_since(self, since_dt: datetime) -> List[Dict]:
        """
        Fetch all news items occurring after since_dt.
        """
        all_news = []
        cursor = None
        
        # Ensure since_dt has timezone info if we're comparing against timezone-aware datetimes
        if since_dt.tzinfo is None:
            # Assume local timezone if naive, or just UTC depending on your app's standard
            since_dt = since_dt.astimezone()
            
        while True:
            args = {}
            if cursor:
                args["cursor"] = cursor
                
            try:
                data = self._call_tool("list_flash", args)
                if not data or "data" not in data or "items" not in data["data"]:
                    break
                    
                resp_data = data["data"]
                items = resp_data.get("items", [])
                
                if not items:
                    break
                
                batch_valid = []
                reached_limit = False
                
                for item in items:
                    t_str = item.get("time")
                    if not t_str: continue
                    
                    try:
                        # Parse ISO 8601 with timezone (e.g. 2026-05-02T16:13:34+08:00)
                        item_dt = datetime.fromisoformat(t_str)
                        if item_dt > since_dt:
                            batch_valid.append(item)
                        else:
                            reached_limit = True
                            break
                    except Exception as e:
                        logger.error(f"Error parsing date {t_str}: {e}")
                        continue
                        
                all_news.extend(batch_valid)
                
                if reached_limit:
                    break
                    
                # Setup next page
                if resp_data.get("has_more") and resp_data.get("next_cursor"):
                    cursor = resp_data["next_cursor"]
                else:
                    break
                    
                if len(all_news) > 200:
                    break
                    
            except Exception as e:
                logger.error(f"Error in fetch_since via MCP: {e}")
                break
                
        return self._inject_ids(all_news)
