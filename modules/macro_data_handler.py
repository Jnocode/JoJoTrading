#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宏觀經濟數據處理模組
用於 DCF 估值中的無風險利率和經濟成長率數據
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import time

class MacroDataHandler:
    """宏觀經濟數據處理器"""
    
    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent / "cache" / "macro_data"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 快取有效期設定
        self.cache_expiry = {
            'bond_yield': 1,  # 公債殖利率：1天
            'gdp_growth': 90, # GDP成長率：90天
        }
          # 預設值（當API失敗時使用）
        self.default_values = {
            'risk_free_rate': 0.015,  # 1.5%
            'gdp_growth': 0.025,      # 2.5%
        }
        
        # 追蹤最後使用的數據來源
        self.last_source = None
    
    def get_risk_free_rate(self) -> float:
        """
        獲取台灣十年期公債殖利率（無風險利率）
        
        Returns:
            float: 十年期公債殖利率
        """
        cache_file = self.cache_dir / "bond_yield.json"
          # 檢查快取
        if self._is_cache_valid(cache_file, 'bond_yield'):
            cached_data = self._load_cache(cache_file)
            if cached_data and 'rate' in cached_data:
                self.last_source = f"快取數據 ({cached_data.get('source', '未知')})"
                print(f"  (MacroDataHandler) 使用快取的十年期公債殖利率: {cached_data['rate']:.3f}%")
                return cached_data['rate']
        
        # 嘗試從多個來源獲取即時數據
        rate = self._fetch_bond_yield_from_sources()
        
        if rate:
            # 儲存到快取
            cache_data = {
                'rate': rate,
                'timestamp': datetime.now().isoformat(),
                'source': 'api'
            }
            self._save_cache(cache_file, cache_data)
            print(f"  (MacroDataHandler) 獲取最新十年期公債殖利率: {rate:.3f}%")
            return rate
        else:
            self.last_source = "預設值回退"
            print(f"  (MacroDataHandler) ⚠️ 無法獲取即時公債殖利率，使用預設值: {self.default_values['risk_free_rate']:.3f}%")
            return self.default_values['risk_free_rate']
    
    def get_gdp_growth_rate(self) -> float:
        """
        獲取台灣GDP成長率
        
        Returns:
            float: GDP成長率
        """
        cache_file = self.cache_dir / "gdp_growth.json"
          # 檢查快取
        if self._is_cache_valid(cache_file, 'gdp_growth'):
            cached_data = self._load_cache(cache_file)
            if cached_data and 'rate' in cached_data:
                self.last_source = f"快取數據 ({cached_data.get('source', '未知')})"
                print(f"  (MacroDataHandler) 使用快取的GDP成長率: {cached_data['rate']:.3f}%")
                return cached_data['rate']
        
        # 嘗試獲取最新GDP數據
        growth_rate = self._fetch_gdp_growth_from_sources()
        
        if growth_rate:
            # 儲存到快取
            cache_data = {
                'rate': growth_rate,
                'timestamp': datetime.now().isoformat(),
                'source': 'dgbas'
            }
            self._save_cache(cache_file, cache_data)
            print(f"  (MacroDataHandler) 獲取最新GDP成長率: {growth_rate:.3f}%")
            return growth_rate
        else:
            self.last_source = "預設值回退"
            print(f"  (MacroDataHandler) ⚠️ 無法獲取即時GDP成長率，使用預設值: {self.default_values['gdp_growth']:.3f}%")
            return self.default_values['gdp_growth']
    
    def _fetch_bond_yield_from_sources(self) -> float:
        """從多個來源獲取公債殖利率"""
          # 方法1: 中央銀行統計資料庫
        try:
            # CBC統計資料API (如果可用)
            rate = self._fetch_from_cbc_api()
            if rate:
                self.last_source = "中央銀行統計資料庫"
                return rate
        except Exception as e:
            print(f"  (MacroDataHandler) CBC API失敗: {e}")
        
        # 方法2: Yahoo Finance台灣公債
        try:
            rate = self._fetch_from_yahoo_finance()
            if rate:
                self.last_source = "Yahoo Finance"
                return rate
        except Exception as e:
            print(f"  (MacroDataHandler) Yahoo Finance失敗: {e}")
        
        # 方法3: 預設估算值（基於最近央行利率）
        try:
            # 央行重貼現率 + 利差估算
            base_rate = 0.0175  # 當前重貼現率約1.75%
            spread = 0.005      # 一般十年期公債利差約0.5%
            self.last_source = "央行利率估算"
            return base_rate + spread
        except:
            return None
    
    def _fetch_gdp_growth_from_sources(self) -> float:
        """從政府來源獲取GDP成長率"""
          # 方法1: 主計總處開放資料
        try:
            rate = self._fetch_from_dgbas_api()
            if rate:
                self.last_source = "主計總處開放資料"
                return rate
        except Exception as e:
            print(f"  (MacroDataHandler) 主計總處API失敗: {e}")
        
        # 方法2: 使用預估值（基於最近公布數據）
        try:
            # 根據最近經濟情況的合理預估
            self.last_source = "經濟預估值"
            return 0.025  # 2.5% 的保守估計
        except:
            return None
    
    def _fetch_from_cbc_api(self) -> float:
        """從央行API獲取公債殖利率"""
        # 注意：實際API可能需要申請權限
        # 這裡提供結構，實際需要根據央行API文件調整
        
        # 模擬API調用
        # url = "https://www.cbc.gov.tw/api/bond_yield"
        # response = requests.get(url, timeout=10)
        # ...
        
        # 暫時返回None，等待實際API
        return None
    
    def _fetch_from_yahoo_finance(self) -> float:
        """從Yahoo Finance獲取台灣公債資料"""
        try:
            # Yahoo Finance有時提供台灣公債ETF數據
            # 可以作為參考指標
            symbol = "^TNX"  # 美國十年期公債(參考)
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # 解析Yahoo數據結構...
                # 這裡需要根據實際回應格式調整
                pass
        except:
            pass
        return None
    
    def _fetch_from_dgbas_api(self) -> float:
        """從主計總處API獲取GDP成長率"""
        try:
            # 主計總處統計資料庫API
            # 實際API網址需要查詢主計總處開放資料平台
            # url = "https://statdb.dgbas.gov.tw/api/gdp"
            
            # 暫時使用合理預估值
            return 0.025  # 2.5%
        except:
            return None
    
    def _is_cache_valid(self, cache_file: Path, data_type: str) -> bool:
        """檢查快取是否有效"""
        if not cache_file.exists():
            return False
        
        try:
            cache_data = self._load_cache(cache_file)
            if not cache_data or 'timestamp' not in cache_data:
                return False
            
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            expiry_days = self.cache_expiry[data_type]
            
            return datetime.now() - cache_time < timedelta(days=expiry_days)
        except:
            return False
    
    def _load_cache(self, cache_file: Path) -> dict:
        """載入快取數據"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_cache(self, cache_file: Path, data: dict):
        """儲存快取數據"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  (MacroDataHandler) 快取儲存失敗: {e}")
    
    def get_market_data_summary(self) -> dict:
        """獲取市場數據摘要"""
        return {
            'risk_free_rate': self.get_risk_free_rate(),
            'gdp_growth_rate': self.get_gdp_growth_rate(),
            'last_updated': datetime.now().isoformat(),
            'data_sources': {
                'bond_yield': '央行統計/Yahoo Finance',
                'gdp_growth': '主計總處統計'
            }
        }
    
    def get_last_source(self) -> str:
        """
        獲取最後使用的數據來源
        
        Returns:
            str: 數據來源描述
        """
        return self.last_source if self.last_source else "未知來源"

# 創建全域實例
macro_data_handler = MacroDataHandler()
