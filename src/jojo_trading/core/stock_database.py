import sqlite3
import pandas as pd
from datetime import datetime
import os
import json
from pathlib import Path

class StockDatabase:
    def __init__(self, db_path=None):
        import sys
        if db_path is None:
            if getattr(sys, 'frozen', False):
                # Running as compiled exe - DB is next to executable
                current_dir = Path(sys.executable).parent
            else:
                # Default to a file in the same directory (Dev)
                current_dir = Path(__file__).parent
            self.db_path = current_dir / "stocks.db"
            self.db_path = current_dir / "stocks.db"
            
            # DEBUG LOGGING (Temporary)
            try:
                with open(current_dir / "debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now()}] DB Path: {self.db_path}\n")
            except: pass

        else:
            self.db_path = Path(db_path)
            
        self.init_db()

    def init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create stocks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            code TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            price REAL,
            intrinsic_value REAL,
            potential_return REAL,
            market_cap REAL,
            fcf REAL,
            data_quality_score REAL,
            last_updated TIMESTAMP,
            data_source TEXT,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # 2. Check and Create Futures Margins Table
        self.init_futures_margins()
        
        # 3. Check and Create Users Table (Kept for basic app auth if needed)
        self.init_users()
        
        # 5. System Settings
        self.init_system_settings()

        # 6. Broker Profiles (Fix: Ensure table exists)
        try:
            with open(self.db_path.parent / "debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] calling init_broker_profiles...\n")
        except: pass
        self.init_broker_profiles()

    def init_system_settings(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP
        )
        ''')
        
        # Default Settings
        defaults = {
            "font_size": "10",
            "default_qty": "1",
            "update_rate": "Fast (0.5s)",
            "enable_sound": "True",
            "auto_connect": "True",
            "theme": "Dark",
            "ai_provider": "Gemini"
        }
        
        for k, v in defaults.items():
            cursor.execute("INSERT OR IGNORE INTO system_settings (key, value, updated_at) VALUES (?, ?, ?)", 
                           (k, v, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_setting(self, key, default=None):
        """Get a system setting value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key, value):
        """Set a system setting value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO system_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ''', (key, str(value), datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def init_broker_profiles(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # profile_name is PK (e.g. 'Simulation', 'Main Account')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS broker_profiles (
            profile_name TEXT PRIMARY KEY,
            api_key TEXT,
            secret_key TEXT,
            person_id TEXT,
            cert_path TEXT,
            cert_pass TEXT, 
            is_simulation BOOLEAN DEFAULT 0,
            allowed_ip TEXT,
            vpn_user TEXT,
            vpn_pass TEXT,
            created_at TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # Migration: Check if column exists, if not add it
        self._migrate_broker_profiles_ip()
        self._migrate_broker_profiles_vpn()

        try:
            with open(self.db_path.parent / "debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] init_broker_profiles completed. Table should exist.\n")
        except: pass

    def _migrate_broker_profiles_ip(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT allowed_ip FROM broker_profiles LIMIT 1")
        except:
            print("🔧 Migrating DB: Adding allowed_ip column...")
            try:
                cursor.execute("ALTER TABLE broker_profiles ADD COLUMN allowed_ip TEXT")
                conn.commit()
            except Exception as e:
                print(f"Migration Failed: {e}")
        finally:
            conn.close()

    def _migrate_broker_profiles_vpn(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT vpn_user FROM broker_profiles LIMIT 1")
        except:
            print("🔧 Migrating DB: Adding VPN columns...")
            try:
                cursor.execute("ALTER TABLE broker_profiles ADD COLUMN vpn_user TEXT")
                cursor.execute("ALTER TABLE broker_profiles ADD COLUMN vpn_pass TEXT")
                conn.commit()
            except Exception as e:
                print(f"VPN Migration Failed: {e}")
        finally:
            conn.close()

    def init_users(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def init_futures_margins(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS futures_margins (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            initial_margin REAL,
            maintenance_margin REAL,
            multiplier REAL,
            currency TEXT DEFAULT 'TWD',
            last_updated TIMESTAMP
        )
        ''')
        
        # Check if empty, populate defaults
        cursor.execute("SELECT count(*) FROM futures_margins")
        if cursor.fetchone()[0] == 0:
            defaults = [
                ('TXF', '台指期 (Big)', 229000, 176000, 200),
                ('MXF', '小型台指 (Small)', 57250, 44000, 50),
                ('ZEF', '微型台指 (Micro)', 11450, 8800, 10)
            ]
            
            cursor.executemany('''
            INSERT INTO futures_margins (symbol, name, initial_margin, maintenance_margin, multiplier, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', [(d[0], d[1], d[2], d[3], d[4], datetime.now().isoformat()) for d in defaults])
            print("✅ Initialized default Futures Margins.")
            
        conn.commit()
        conn.close()

    def update_stock(self, data):
        """Update a single stock record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO stocks (
            code, name, sector, price, intrinsic_value, 
            potential_return, market_cap, fcf, 
            data_quality_score, last_updated, data_source, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('code'),
            data.get('name'),
            data.get('sector'),
            data.get('price'),
            data.get('intrinsic_value'),
            data.get('potential_return'),
            data.get('market_cap'),
            data.get('fcf'),
            data.get('data_quality_score'),
            datetime.now().isoformat(),
            data.get('data_source'),
            1
        ))
        
        conn.commit()
        conn.close()

    def get_all_stocks(self):
        """Get all stocks as a DataFrame"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM stocks", conn)
        conn.close()
        return df

    def get_stocks_by_sector(self, sector):
        """Get stocks filtered by sector"""
        conn = sqlite3.connect(self.db_path)
        if sector == "全部":
            query = "SELECT * FROM stocks WHERE is_active = 1"
            params = ()
        else:
            query = "SELECT * FROM stocks WHERE sector = ? AND is_active = 1"
            params = (sector,)
            
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def get_top_potential_stocks(self, limit=50, min_market_cap=0):
        """Get top stocks by potential return"""
        conn = sqlite3.connect(self.db_path)
        query = '''
        SELECT * FROM stocks 
        WHERE is_active = 1 AND market_cap >= ?
        ORDER BY potential_return DESC
        LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=(min_market_cap, limit))
        conn.close()
        return df

    def get_stock(self, code):
        """Get a single stock record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stocks WHERE code = ?", (code,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    def get_all_margins(self):
        """Get all futures margins"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM futures_margins", conn)
        conn.close()
        return df

    def get_margin(self, symbol):
        """Get margin for a specific symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM futures_margins WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    def update_margin(self, symbol, initial_margin, maintenance_margin):
        """Update margin requirements for a symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE futures_margins 
        SET initial_margin = ?, maintenance_margin = ?, last_updated = ?
        WHERE symbol = ?
        ''', (initial_margin, maintenance_margin, datetime.now().isoformat(), symbol))
        
        conn.commit()
        conn.close()

    def create_user(self, username, password_hash, role='user'):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (?, ?, ?, ?)
            ''', (username, password_hash, role, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # User exists
        finally:
            conn.close()

    def get_user(self, username):
        """Get user by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None


    def create_broker_profile(self, profile_name, api_key, secret_key, person_id, cert_path, cert_pass="", is_simulation=False, allowed_ip="", vpn_user="", vpn_pass=""):
        """Create or Update a broker profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Upsert logic (Replace)
        cursor.execute('''
        INSERT OR REPLACE INTO broker_profiles 
        (profile_name, api_key, secret_key, person_id, cert_path, cert_pass, is_simulation, allowed_ip, vpn_user, vpn_pass, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (profile_name, api_key, secret_key, person_id, cert_path, cert_pass, is_simulation, allowed_ip, vpn_user, vpn_pass, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True

    def get_broker_profiles(self):
        """Get all broker profiles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM broker_profiles")
        rows = cursor.fetchall()
        
        results = []
        if rows:
            columns = [d[0] for d in cursor.description]
            for r in rows:
                results.append(dict(zip(columns, r)))
        
        conn.close()
        return results

    def delete_broker_profile(self, profile_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM broker_profiles WHERE profile_name = ?", (profile_name,))
        conn.commit()
        conn.close()
