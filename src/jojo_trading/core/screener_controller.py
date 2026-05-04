"""
Screener Controller
負責將使用者的「白話文選股條件」透過 AI 轉譯為可執行的過濾條件 (字典或查詢語法)，
並從本地 StockDatabase 或即時 API 中篩選出符合條件的股票清單。

掃描時會自動用 yfinance 批量更新候選股票的最新股價，
並以公式 (intrinsic_value / latest_price - 1) 即時重算 potential_return，
確保掃描結果與分析模組的 DCF 估值一致。
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
try:
    import pandas as pd
except ImportError:
    pd = None
from jojo_trading.core.stock_database import StockDatabase
from jojo_trading.utils.ai_client import AIClient

logger = logging.getLogger(__name__)

# 股價快取的有效期 (秒)
PRICE_CACHE_TTL_MARKET = 300     # 盤中: 5 分鐘
PRICE_CACHE_TTL_CLOSED = 86400   # 盤後/假日: 24 小時


def _is_tw_market_open() -> bool:
    """
    判斷目前是否在台股盤中時段。
    台股交易時間: 週一至週五 09:00 ~ 13:30 (台灣時間)
    盤後數據公布約 14:00，故延伸到 14:00。
    """
    now = datetime.now()
    weekday = now.weekday()  # 0=Mon, 6=Sun
    
    if weekday >= 5:  # 週六、週日
        return False
    
    hour_min = now.hour * 100 + now.minute
    return 900 <= hour_min <= 1400


class _PriceCache:
    """
    模組層級的股價快取，智能判斷市場時段。
    盤中 (09:00-14:00): 5 分鐘 TTL
    盤後/假日: 24 小時 TTL (不浪費 API 額度)
    """
    _store: Dict[str, Dict] = {}

    @classmethod
    def get(cls, code: str) -> float | None:
        entry = cls._store.get(code)
        if not entry:
            return None
        
        ttl = PRICE_CACHE_TTL_MARKET if _is_tw_market_open() else PRICE_CACHE_TTL_CLOSED
        if (datetime.now() - entry["ts"]).total_seconds() < ttl:
            return entry["price"]
        return None

    @classmethod
    def set(cls, code: str, price: float):
        cls._store[code] = {"price": price, "ts": datetime.now()}


class ScreenerController:
    def __init__(self):
        self.ai_client = AIClient()
        self.db = StockDatabase()
        
    def scan_by_natural_language(self, user_prompt: str, explicit_sectors: List[str] = None) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
        """
        1. 將 user_prompt 餵給 AI 轉譯成 JSON Filter
        2. 套用 Filter 到候選股票池中
        3. 批量刷新候選股票的最新股價，即時重算 potential_return
        """
        logger.info(f"NLP Screener Request: {user_prompt}, Explicit Sectors: {explicit_sectors}")
        
        # 步驟 1: 讓 AI 從自然語言中粹取出具體的過濾條件
        filter_schema, err = self._translate_prompt_to_filter(user_prompt)
        if err:
            return [], err, {}
            
        logger.info(f"AI Extracted Filters: {filter_schema}")
        
        # 步驟 2: 執行篩選
        try:
            results = self._apply_filter(filter_schema, explicit_sectors)

            # 步驟 3: 用最新股價即時重算 potential_return
            if results:
                results = self._refresh_prices(results)

            return results, "", filter_schema
        except Exception as e:
            logger.error(f"Filter Application Error: {e}")
            return [], f"資料過濾失敗: {str(e)}", filter_schema
            
    def _translate_prompt_to_filter(self, user_prompt: str) -> Tuple[Dict[str, Any], str]:
        """
        使用 AI 將自然語言萃取為可以被程式邏輯看懂的字典。
        """
        available_sectors_str = "半導體, 電子, 航運, 金融"
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL AND sector != ''")
            sectors = [r[0] for r in cursor.fetchall()]
            conn.close()
            if sectors:
                available_sectors_str = ", ".join(sectors)
        except Exception as e:
            logger.error(f"Failed to fetch sectors: {e}")

        system_prompt = f"""
        你是一個量化交易系統的「選股條件轉譯器」。
        請將用戶的自然語言需求，轉換為以下 JSON 格式的過濾條件。
        如果用戶沒有提到的條件，請省略該欄位或填 null。

        【重要指示 - 產業對應】
        資料庫中目前僅支援以下產業板塊：
        [{available_sectors_str}]
        如果用戶提到的產業（例如「科技股」）不在名單中，請根據常識對應到最符合的板塊（如「電子」或「半導體」），可以回傳正則表達式如 "電子|半導體"。

        可用的 JSON 欄位格式：
        {{
            "min_market_cap": 數值 (最低市值, 億),
            "min_potential_return": 數值 (最低潛在報酬率 %),
            "price_range": [min, max] (價格區間),
            "sector": "例如: 電子|半導體",
            "is_active": true | false (是否為活絡股票),
            "tech_ma_cross": "gold" | "death" (技術面：黃金交叉或死亡交叉),
            "tech_above_ma60": true | false (技術面：股價站上季線),
            "tech_kd_cross": "gold" | "death" (技術面：KD 黃金交叉或死亡交叉),
            "tech_volume_surge": true | false (技術面：爆量),
            "chip_foreign_buy_days": 數值 (籌碼面：外資連續買超天數),
            "chip_it_buy": true | false (籌碼面：投信買超),
            "chip_three_institutional_sync": true | false (籌碼面：法人同步買超),
            "reasoning": "簡短解釋你為什麼設定這些過濾條件。若用戶未提及板塊，請直接省略 sector 欄位，且不需要在 reasoning 中解釋「因為沒提到板塊所以留空」，保持說明簡潔專注在有設定的條件上。"
        }}

        用戶輸入：「{user_prompt}」
        
        Output valid JSON only (no markdown, no backticks).
        """
        
        try:
            raw_response = self.ai_client.generate_content(system_prompt)
            if raw_response.startswith("Error:"):
                return {}, f"AI 連線失敗: {raw_response}"
                
            # 強化清洗邏輯
            cleaned_content = raw_response.strip()
            if cleaned_content.startswith("```"):
                lines = cleaned_content.split('\n')
                if len(lines) >= 2:
                    if lines[0].startswith("```"): lines = lines[1:]
                    if lines[-1].strip() == "```": lines = lines[:-1]
                cleaned_content = '\n'.join(lines).strip()
                
            try:
                result_json = json.loads(cleaned_content)
                return result_json, ""
            except json.JSONDecodeError:
                match = re.search(r'\{.*\}', cleaned_content, re.DOTALL)
                if match:
                    return json.loads(match.group(0)), ""
                else:
                    return {}, "無法解析 AI 產生的選股邏輯 (JSON Error)"
        except Exception as e:
            logger.error(f"NLP Translation Failed: {e}")
            return {}, f"NLP 轉譯失敗: {str(e)}"

    def _apply_filter(self, filter_schema: Dict[str, Any], explicit_sectors: List[str] = None) -> List[Dict[str, Any]]:
        """
        套用條件到資料集。在此使用 StockDatabase 的真實資料進行第一階段靜態篩選。
        """
        try:
            # 1. 取得所有股票資料
            df = self.db.get_all_stocks()
            if df.empty:
                return []

            # 2. 套用靜態篩選邏輯
            # 市值過濾
            min_cap = filter_schema.get('min_market_cap')
            if min_cap:
                df = df[df['market_cap'] >= min_cap]

            # 潛在報酬率
            min_ret = filter_schema.get('min_potential_return')
            if min_ret:
                df = df[df['potential_return'] >= min_ret]

            # 價格區間
            p_range = filter_schema.get('price_range')
            if p_range and isinstance(p_range, list) and len(p_range) == 2:
                if p_range[0] is not None: df = df[df['price'] >= p_range[0]]
                if p_range[1] is not None: df = df[df['price'] <= p_range[1]]

            # 板塊概念
            if explicit_sectors:
                df = df[df['sector'].isin(explicit_sectors)]
                filter_schema['explicit_sectors'] = explicit_sectors
            else:
                req_sector = filter_schema.get('sector')
                if req_sector and isinstance(req_sector, str):
                    df = df[df['sector'].str.contains(req_sector, na=False, case=False)]

            # [New] 第一階段結果限制 (保護機制)
            has_dynamic_filters = any([
                filter_schema.get('tech_ma_cross'),
                filter_schema.get('tech_above_ma60'),
                filter_schema.get('tech_kd_cross'),
                filter_schema.get('tech_volume_surge'),
                filter_schema.get('chip_foreign_buy_days'),
                filter_schema.get('chip_it_buy'),
                filter_schema.get('chip_three_institutional_sync')
            ])

            if has_dynamic_filters and len(df) > 100:
                logger.info(f"候選池過大 ({len(df)} 檔)，且包含動態篩選條件，強制縮減至市值前 100 大")
                df = df.nlargest(100, 'market_cap')

            # 3. 轉換為字典列表供第二階段使用或直接 UI 顯示
            results = []
            for _, row in df.head(100 if not has_dynamic_filters else len(df)).iterrows():
                results.append({
                    "code": row.get('code', ''),
                    "name": row.get('name', ''),
                    "price": float(row.get('price', 0.0)),
                    "intrinsic_value": float(row.get('intrinsic_value', 0.0)),
                    "potential_return": float(row.get('potential_return', 0.0)),
                    "market_cap": float(row.get('market_cap', 0.0)),
                    "sector": str(row.get('sector', '')),
                    "last_updated": str(row.get('last_updated', '')),
                })
            
            # 4. 執行第二階段動態篩選
            if has_dynamic_filters and results:
                results = self._apply_dynamic_filters(results, filter_schema)

            return results[:100]

        except Exception as e:
            logger.error(f"Real data filter error: {e}")
            return []

    def _apply_dynamic_filters(self, candidates: List[Dict[str, Any]], filter_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        第二階段：動態篩選技術面與籌碼面條件。
        """
        logger.info(f"開始執行第二階段動態篩選，候選數量: {len(candidates)}")
        filtered = candidates.copy()

        # 1. 技術面篩選 (使用 yfinance 歷史資料)
        tech_ma = filter_schema.get('tech_ma_cross')
        tech_ma60 = filter_schema.get('tech_above_ma60')
        tech_kd = filter_schema.get('tech_kd_cross')
        tech_vol = filter_schema.get('tech_volume_surge')

        if (tech_ma or tech_ma60 or tech_kd or tech_vol) and filtered:
            filtered = self._filter_by_technicals(filtered, tech_ma, tech_ma60, tech_kd, tech_vol)
            logger.info(f"技術面篩選後剩餘: {len(filtered)}")

        # 2. 籌碼面篩選 (使用 FinMind)
        chip_foreign = filter_schema.get('chip_foreign_buy_days')
        chip_it = filter_schema.get('chip_it_buy')
        chip_sync = filter_schema.get('chip_three_institutional_sync')

        if (chip_foreign or chip_it or chip_sync) and filtered:
            filtered = self._filter_by_chips(filtered, chip_foreign, chip_it, chip_sync)
            logger.info(f"籌碼面篩選後剩餘: {len(filtered)}")

        return filtered

    def _filter_by_technicals(self, candidates: List[Dict[str, Any]], ma_cross: str, above_ma60: bool, kd_cross: str, vol_surge: bool) -> List[Dict[str, Any]]:
        try:
            import yfinance as yf
        except ImportError:
            logger.error("未安裝 yfinance，無法執行技術面篩選")
            return candidates

        valid_candidates = []
        for row in candidates:
            code = row['code']
            tw_ticker = f"{code}.TW"
            try:
                # 取得近 4 個月資料以確保能計算 MA60 (季線約 60 個交易日) 與 KD
                ticker = yf.Ticker(tw_ticker)
                hist = ticker.history(period="4mo")
                if len(hist) < 60:
                    continue
                
                # 計算均線
                hist['MA5'] = hist['Close'].rolling(window=5).mean()
                hist['MA20'] = hist['Close'].rolling(window=20).mean()
                hist['MA60'] = hist['Close'].rolling(window=60).mean()
                
                # 計算 KD (9天 RSV, 1/3 平滑)
                low_min = hist['Low'].rolling(window=9).min()
                high_max = hist['High'].rolling(window=9).max()
                hist['RSV'] = (hist['Close'] - low_min) / (high_max - low_min) * 100
                hist['K'] = hist['RSV'].ewm(alpha=1/3, adjust=False).mean()
                hist['D'] = hist['K'].ewm(alpha=1/3, adjust=False).mean()
                
                # 取得最後兩個有效交易日 (T-1, T)
                if len(hist) < 2:
                    continue
                t0 = hist.iloc[-1]
                t1 = hist.iloc[-2]

                pass_ma = True
                if ma_cross == "gold":
                    pass_ma = (t1['MA5'] <= t1['MA20']) and (t0['MA5'] > t0['MA20'])
                elif ma_cross == "death":
                    pass_ma = (t1['MA5'] >= t1['MA20']) and (t0['MA5'] < t0['MA20'])

                pass_ma60 = True
                if above_ma60:
                    pass_ma60 = t0['Close'] > t0['MA60']

                pass_kd = True
                if kd_cross == "gold":
                    pass_kd = (t1['K'] <= t1['D']) and (t0['K'] > t0['D'])
                elif kd_cross == "death":
                    pass_kd = (t1['K'] >= t1['D']) and (t0['K'] < t0['D'])

                pass_vol = True
                if vol_surge:
                    # 爆量: 今日成交量大於 5 日均量的 2 倍
                    vol_ma5 = hist['Volume'].rolling(window=5).mean().iloc[-2] # 前五日均量 (不含今日)
                    if vol_ma5 > 0:
                        pass_vol = t0['Volume'] > (vol_ma5 * 2)
                    else:
                        pass_vol = False
                
                if pass_ma and pass_ma60 and pass_kd and pass_vol:
                    valid_candidates.append(row)

            except Exception as e:
                logger.warning(f"技術面計算失敗 {code}: {e}")
                
        return valid_candidates

    def _filter_by_chips(self, candidates: List[Dict[str, Any]], foreign_days: int, it_buy: bool, sync_buy: bool) -> List[Dict[str, Any]]:
        try:
            from jojo_trading.core.finmind_fetcher import FinMindFetcher
        except ImportError:
            logger.error("無法匯入 FinMindFetcher，無法執行籌碼面篩選")
            return candidates

        fetcher = FinMindFetcher()
        valid_candidates = []
        # 我們只看最近 10 天的籌碼資料，避免抓太多
        
        for row in candidates:
            code = row['code']
            try:
                df = fetcher.get_institutional_data(code, days=10)
                if df.empty:
                    continue
                
                df = df.sort_values('date', ascending=True)
                
                pass_foreign = True
                if foreign_days:
                    # 檢查最後 foreign_days 天是否皆為買超
                    last_n = df.tail(foreign_days)
                    if len(last_n) < foreign_days:
                        pass_foreign = False
                    else:
                        pass_foreign = (last_n['Foreign_Buy'] > 0).all()
                        
                pass_it = True
                if it_buy:
                    # 檢查最後一天投信是否買超
                    pass_it = df.iloc[-1]['IT_Buy'] > 0

                pass_sync = True
                if sync_buy:
                    # 檢查最後一天外資和投信是否同步買超
                    last_row = df.iloc[-1]
                    pass_sync = (last_row['Foreign_Buy'] > 0) and (last_row['IT_Buy'] > 0)
                
                if pass_foreign and pass_it and pass_sync:
                    valid_candidates.append(row)
                    
            except Exception as e:
                logger.warning(f"籌碼面計算失敗 {code}: {e}")
                
        return valid_candidates

    # ------------------------------------------------------------------
    # 即時股價刷新 & DCF 重算
    # ------------------------------------------------------------------
    def _refresh_prices(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量刷新候選股票的最新股價，並重算 potential_return。
        
        策略：
        1. 先檢查快取，只對過期的股票呼叫 yfinance
        2. 用 yfinance 批量取得最新收盤價
        3. 公式: potential_return = (intrinsic_value / latest_price) - 1
        4. 將更新的 price + potential_return 寫回 stocks.db
        """
        import sqlite3

        # 分出需要刷新的和已有快取的
        codes_to_fetch = []
        cached_prices = {}
        for row in results:
            code = str(row["code"])
            cached = _PriceCache.get(code)
            if cached is not None:
                cached_prices[code] = cached
            else:
                codes_to_fetch.append(code)

        # 批量從 yfinance 取得最新股價
        fetched_prices = {}
        if codes_to_fetch:
            fetched_prices = self._batch_fetch_prices(codes_to_fetch)
            # 寫入快取
            for code, price in fetched_prices.items():
                _PriceCache.set(code, price)

        # 合併：快取 + 新取得
        all_prices = {**cached_prices, **fetched_prices}

        if not all_prices:
            logger.warning("Price refresh: 無法取得任何最新股價，使用資料庫舊價格")
            return results

        # 重算 potential_return 並更新結果
        now_iso = datetime.now().isoformat()
        db_updates = []

        for row in results:
            code = str(row["code"])
            latest_price = all_prices.get(code)
            if latest_price and latest_price > 0:
                intrinsic = row.get("intrinsic_value", 0.0)
                old_price = row["price"]
                row["price"] = latest_price

                if intrinsic and intrinsic > 0:
                    row["potential_return"] = round((intrinsic / latest_price - 1) * 100, 1)
                else:
                    row["potential_return"] = 0.0

                row["last_updated"] = now_iso

                # 收集 DB 批量更新
                db_updates.append((
                    latest_price,
                    row["potential_return"],
                    now_iso,
                    code,
                ))

                logger.debug(
                    f"Price refresh: {code} ${old_price:.0f} -> ${latest_price:.0f}, "
                    f"return: {row['potential_return']:.1f}%"
                )

        # 批量寫回 stocks.db
        if db_updates:
            try:
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.executemany(
                    "UPDATE stocks SET price = ?, potential_return = ?, last_updated = ? WHERE code = ?",
                    db_updates,
                )
                conn.commit()
                conn.close()
                logger.info(f"Price refresh: 已更新 {len(db_updates)} 筆股票的最新股價")
            except Exception as e:
                logger.error(f"Price refresh DB write failed: {e}")

        return results

    def _batch_fetch_prices(self, codes: List[str]) -> Dict[str, float]:
        """
        用 yfinance 批量取得台股最新收盤價。
        
        台股在 yfinance 的 ticker 格式為 "2330.TW"。
        使用 fast_info.last_price 取得最新成交價。
        """
        prices = {}
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance 未安裝，無法刷新股價")
            return prices

        logger.info(f"yfinance batch fetch: {len(codes)} stocks")

        # 逐支取得 (fast_info 比 download 更穩定)
        for code in codes:
            try:
                tw_ticker = f"{code}.TW"
                ticker = yf.Ticker(tw_ticker)
                price = ticker.fast_info.last_price
                if price and price > 0:
                    prices[code] = round(float(price), 2)
                else:
                    logger.warning(f"yfinance: {tw_ticker} 無法取得股價")
            except Exception as e:
                logger.warning(f"yfinance: {code}.TW fetch failed: {e}")

        logger.info(f"yfinance batch fetch: 成功取得 {len(prices)}/{len(codes)} 支股票的最新股價")
        return prices
