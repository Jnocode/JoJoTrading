
import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class NewsCacheManager:
    """
    Manages caching of News AI analysis results using SQLite.
    Path: src/jojo_trading/cache/news_cache.db
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to src/jojo_trading/cache/news_cache.db
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            self.db_path = os.path.join(cache_dir, 'news_cache.db')
        else:
            self.db_path = db_path
            
        self._init_db()

    def _init_db(self):
        """Create table if not exists."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table: analyzed_news
            # id: News ID (string)
            # time_str: News time
            # content: News content
            # analysis_json: The Full AI result
            # created_at: Timestamp
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyzed_news (
                    id TEXT PRIMARY KEY,
                    time_str TEXT,
                    content TEXT,
                    analysis_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to init News Cache DB: {e}")

    def get_analysis(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis if exists."""
        if not news_id: return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT analysis_json FROM analyzed_news WHERE id = ?", (str(news_id),))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
            
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            return None

    def save_analysis(self, news_id: str, time_str: str, content: str, analysis: Dict[str, Any]):
        """Save analysis result."""
        if not news_id or not analysis: return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Upsert (Replace if exists)
            cursor.execute("""
                INSERT OR REPLACE INTO analyzed_news (id, time_str, content, analysis_json)
                VALUES (?, ?, ?, ?)
            """, (str(news_id), time_str, content, json.dumps(analysis, ensure_ascii=False)))
            
            conn.commit()
            conn.close()
            logger.info(f"Cached analysis for news {news_id}")
            
        except Exception as e:
            logger.error(f"Cache SAVE error: {e}")

    def clear_all(self) -> int:
        """Delete all cached analysis records. Returns number of rows deleted."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analyzed_news")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM analyzed_news")
            conn.commit()
            conn.close()
            logger.info(f"Cleared {count} cached news analyses.")
            return count
        except Exception as e:
            logger.error(f"Cache CLEAR error: {e}")
            return 0

    def get_count(self) -> int:
        """Return number of cached analysis records."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analyzed_news")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Cache COUNT error: {e}")
            return 0
