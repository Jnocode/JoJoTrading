
import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class Jin10Scraper:
    """
    Scraper for Jin10 Flash News.
    """
    BASE_URL = "https://flash-api.jin10.com/get_flash_list"
    
    # Typical headers to mimic a browser/app
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.jin10.com/",
        "x-app-id": "bVBF4FyRTn5NJF5n",
        "x-version": "1.0.0"
    }

    def __init__(self):
        pass

    def fetch_latest_news(self, limit: int = 20, channel: int = -2) -> List[Dict]:
        """
        Fetch latest flash news.
        
        Args:
            limit: Number of items to return (approximate).
            channel: News channel ID. -2 is often used for 'Important/All'.
                     Try 1 for 'All' if -2 returns empty.
        
        Returns:
            List of news items (dicts).
        """
        params = {
            "channel": str(channel),
            "max_time": "", # Start from latest
            # "limit": limit  # API might not support limit directly in all versions, but we can filter
        }
        
        # Try fetching
        try:
            logger.info(f"Fetching Jin10 news from {self.BASE_URL} with channel={channel}")
            logger.info(f"Fetching Jin10 news from {self.BASE_URL} with channel={channel}")
            response = requests.get(self.BASE_URL, headers=self.HEADERS, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch news. Status: {response.status_code}, Body: {response.text}")
                return []
                
            data = response.json()
            
            if "data" not in data:
                logger.warning(f"Unexpected response structure: {data.keys()}")
                return []
                
            news_list = data["data"]
            
            # If empty, maybe try another channel? 
            if not news_list and channel == -2:
                 logger.info("Channel -2 returned empty. Retrying with channel 1 (All)...")
                 return self.fetch_latest_news(limit, channel=1)

            # Filter/Process
            # We assume the API returns sorted by time desc (latest first)
            return news_list[:limit]

        except Exception as e:
            logger.exception(f"Error fetching Jin10 news: {e}")
            return []

    def fetch_news_since(self, since_dt: datetime) -> List[Dict]:
        """
        Fetch all news items occurring after since_dt.
        """
        all_news = []
        max_time = ""
        channel_to_use = "-2"
        
        # Check if channel -2 works, else fallback to 1 logic?
        # Only check on first page.
        
        while True:
            params = {
                "channel": channel_to_use, 
                "max_time": max_time
            }
            
            try:
                response = requests.get(self.BASE_URL, headers=self.HEADERS, params=params, timeout=10)
                if response.status_code != 200: break
                
                data = response.json()
                news_list = data.get("data", [])
                
                # Fallback Logic (First page only)
                if not news_list and not all_news and channel_to_use == "-2":
                    logger.info("Channel -2 empty in since-fetch. Retrying Channel 1.")
                    channel_to_use = "1"
                    continue
                
                if not news_list: break
                
                # Check item times
                batch_valid = []
                for item in news_list:
                    # Parse time: "2023-10-27 15:30:00"
                    t_str = item.get("time")
                    if not t_str: continue
                    
                    try:
                        item_dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
                        if item_dt > since_dt:
                            batch_valid.append(item)
                        else:
                            # Reached time limit
                            all_news.extend(batch_valid)
                            return all_news
                    except:
                        continue
                
                all_news.extend(batch_valid)
                
                # Setup next page
                # max_time for next request is the time of the last item
                last_item = news_list[-1]
                max_time = last_item.get("time")
                
                # Safety break for infinite loop
                if len(all_news) > 200: break
                
                # Sleep briefly to be polite
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in fetch_since: {e}")
                break
                
        return all_news

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    scraper = Jin10Scraper()
    news = scraper.fetch_latest_news()
    print(f"Fetched {len(news)} items.")
    for item in news[:3]:
        print(f"- [{item.get('time')}] {item.get('data', {}).get('content', 'No content')}")
