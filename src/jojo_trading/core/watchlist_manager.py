import sqlite3
import pandas as pd
from datetime import datetime
import os
from typing import List, Dict, Any, Optional

class WatchlistManager:
    """管理自選股清單 (SQLite)"""
    
    def __init__(self, db_path: str = "src/jojo_trading/data/watchlist.db"):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()
        
    def _ensure_db_dir(self):
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
    def _init_db(self):
        """初始化資料庫表結構"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 建立 watchlist 表
        c.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                date_added TEXT,
                analysis_date TEXT,
                model_type TEXT,
                target_price REAL,
                current_price REAL,
                upside REAL,
                wacc REAL,
                terminal_growth REAL,
                note TEXT,
                params_json TEXT,
                shares_held INTEGER DEFAULT 0,
                average_cost REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self._migrate_db()
        
        self._migrate_db()

    def _migrate_db(self):
        """檢查並更新資料庫結構 (Migration)"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Check if columns exist
            c.execute("PRAGMA table_info(watchlist)")
            columns = [info[1] for info in c.fetchall()]
            
            if 'shares_held' not in columns:
                print("📦 Migrating DB: Adding 'shares_held' column...")
                c.execute("ALTER TABLE watchlist ADD COLUMN shares_held INTEGER DEFAULT 0")
                
            if 'average_cost' not in columns:
                print("📦 Migrating DB: Adding 'average_cost' column...")
                c.execute("ALTER TABLE watchlist ADD COLUMN average_cost REAL DEFAULT 0.0")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ DB Migration Failed: {e}")
        
    def add_entry(self, 
                 stock_code: str,
                 stock_name: str,
                 target_price: float,
                 current_price: float,
                 model_type: str = "DCF",
                 wacc: float = 0.0,
                 terminal_growth: float = 0.0,
                 note: str = "",
                 params_json: str = "{}") -> bool:
        """新增一筆紀錄"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            upside = (target_price - current_price) / current_price if current_price > 0 else 0
            
            c.execute('''
                INSERT INTO watchlist (
                    stock_code, stock_name, date_added, analysis_date,
                    model_type, target_price, current_price, upside,
                    wacc, terminal_growth, note, params_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock_code, stock_name, now, now,
                model_type, target_price, current_price, upside,
                wacc, terminal_growth, note, params_json
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False

    def batch_add_entries(self, codes: List[str]) -> int:
        """批量新增 (僅代號)"""
        if not codes: return 0
        
        count = 0
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for code in codes:
                code = code.strip()
                if not code: continue
                
                # Check exist
                c.execute("SELECT id FROM watchlist WHERE stock_code = ?", (code,))
                if c.fetchone(): continue
                
                c.execute('''
                    INSERT INTO watchlist (
                        stock_code, stock_name, date_added, analysis_date,
                        model_type, target_price, current_price, upside,
                        wacc, terminal_growth, note, params_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code, code, now, now,
                    "Imported", 0, 0, 0,
                    0, 0, "Batch Import", "{}"
                ))
                count += 1
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Batch add error: {e}")
            
        return count
            
    def get_all_entries(self) -> pd.DataFrame:
        """獲取所有自選股"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM watchlist ORDER BY date_added DESC", conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error reading watchlist: {e}")
            return pd.DataFrame()
            
    def delete_entry(self, entry_id: int) -> bool:
        """刪除紀錄"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM watchlist WHERE id = ?", (entry_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting from watchlist: {e}")
            return False

    def delete_entry_by_code(self, stock_code: str) -> bool:
        """根據代號刪除"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM watchlist WHERE stock_code = ?", (stock_code,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting {stock_code}: {e}")
            return False

    def clear_all(self) -> bool:
        """清空所有"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM watchlist")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing watchlist: {e}")
            return False

    def _migrate_db(self):
        """檢查並更新資料庫結構 (Migration)"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Check if columns exist
            c.execute("PRAGMA table_info(watchlist)")
            columns = [info[1] for info in c.fetchall()]
            
            if 'shares_held' not in columns:
                print("📦 Migrating DB: Adding 'shares_held' column...")
                c.execute("ALTER TABLE watchlist ADD COLUMN shares_held INTEGER DEFAULT 0")
                
            if 'average_cost' not in columns:
                print("📦 Migrating DB: Adding 'average_cost' column...")
                c.execute("ALTER TABLE watchlist ADD COLUMN average_cost REAL DEFAULT 0.0")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ DB Migration Failed: {e}")

    def update_holding(self, stock_code: str, shares: int, cost: float) -> bool:
        """更新持股資訊"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # 檢查是否存在
            c.execute("SELECT id FROM watchlist WHERE stock_code = ?", (stock_code,))
            row = c.fetchone()
            
            if row:
                # Update existing
                c.execute('''
                    UPDATE watchlist 
                    SET shares_held = ?, average_cost = ?
                    WHERE stock_code = ?
                ''', (shares, cost, stock_code))
            else:
                # Insert new (Basic info only)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute('''
                    INSERT INTO watchlist (
                        stock_code, stock_name, date_added, analysis_date,
                        shares_held, average_cost,
                        model_type, target_price, current_price, upside,
                        wacc, terminal_growth, note, params_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, '', '{}')
                ''', (stock_code, stock_code, now, now, shares, cost, 'Inventory', 0, 0, 0))
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating holding: {e}")
            return False

    def sync_portfolio(self, positions: List[Dict[str, Any]]) -> Dict[str, int]:
        """批量同步庫存"""
        stats = {'updated': 0, 'inserted': 0, 'failed': 0}
        for pos in positions:
            code = pos.get('code')
            qty = pos.get('qty', 0)
            cost = pos.get('cost', 0.0)
            
            if code:
                if self.update_holding(code, qty, cost):
                    stats['updated'] += 1
                else:
                    stats['failed'] += 1
        return stats

# 測試用
if __name__ == "__main__":
    wm = WatchlistManager("test_watchlist.db")
    wm.add_entry("2330", "台積電", 800, 750, "DCF", 0.1, 0.03, "測試筆記")
    print(wm.get_all_entries())
    os.remove("test_watchlist.db")
