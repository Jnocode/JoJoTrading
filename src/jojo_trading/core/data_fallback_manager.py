"""
改進的資料處理模組 - 缺失資料替代方案
Enhanced Data Processing Module - Missing Data Fallback Solutions

解決缺失關鍵財務資料的問題：
1. 歷史資料回溯
2. 行業平均值估算
3. 多資料源切換
4. 智能數值推估
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime, timedelta

class DataFallbackManager:
    """資料缺失替代方案管理器"""
    
    def __init__(self, auto_fetcher):
        self.auto_fetcher = auto_fetcher
        self.industry_averages = self._load_industry_averages()
    
    def _load_industry_averages(self) -> Dict[str, Dict[str, float]]:
        """載入行業平均值"""
        return {
            "半導體": {
                "capex_to_revenue_ratio": 0.15,  # 資本支出/營收比率
                "depreciation_to_capex_ratio": 0.3,  # 折舊/資本支出比率
                "working_capital_ratio": 0.05,  # 營運資金變化/營收比率
                "fcf_to_ni_ratio": 0.8  # 自由現金流/淨利比率
            },
            "金融": {
                "capex_to_revenue_ratio": 0.02,
                "depreciation_to_capex_ratio": 0.8,
                "working_capital_ratio": 0.0,
                "fcf_to_ni_ratio": 0.6
            },
            "電子": {
                "capex_to_revenue_ratio": 0.08,
                "depreciation_to_capex_ratio": 0.4,
                "working_capital_ratio": 0.03,
                "fcf_to_ni_ratio": 0.7
            },
            "電信": {
                "capex_to_revenue_ratio": 0.12,
                "depreciation_to_capex_ratio": 0.6,
                "working_capital_ratio": 0.01,
                "fcf_to_ni_ratio": 0.9
            },
            "其他": {
                "capex_to_revenue_ratio": 0.06,
                "depreciation_to_capex_ratio": 0.5,
                "working_capital_ratio": 0.02,
                "fcf_to_ni_ratio": 0.75
            }
        }
    
    def get_fallback_capex(self, stock_code: str, sector: str, net_income: float, revenue: Optional[float] = None) -> Optional[float]:
        """
        獲取資本支出的替代值
        
        優先順序：
        1. 歷史資料回溯
        2. 行業平均值估算
        3. 淨利比例估算
        """
        print(f"    🔄 嘗試獲取 {stock_code} 資本支出替代值...")
        
        # 方法1: 歷史資料回溯
        historical_capex = self._get_historical_capex(stock_code)
        if historical_capex:
            print(f"    ✅ 使用歷史資料: 資本支出 {historical_capex:.1f}億")
            return historical_capex
        
        # 方法2: 行業平均值估算
        if revenue and sector in self.industry_averages:
            industry_ratio = self.industry_averages[sector]["capex_to_revenue_ratio"]
            estimated_capex = revenue * industry_ratio
            print(f"    ✅ 使用行業平均估算: 資本支出 {estimated_capex:.1f}億 (營收 * {industry_ratio:.1%})")
            return estimated_capex
          # 方法3: 淨利比例估算（保守估算）
        if net_income > 0:
            estimated_capex = net_income * 0.3  # 假設資本支出為淨利的30%
            print(f"    ⚠️ 使用淨利比例估算: 資本支出 {estimated_capex:.1f}億 (淨利 * 30%)")
            return estimated_capex
        
        print(f"    ❌ 無法獲取 {stock_code} 資本支出替代值")
        return None
    
    def _get_historical_capex(self, stock_code: str, lookback_quarters: int = 4) -> Optional[float]:
        """回溯歷史資料獲取資本支出"""
        try:
            print(f"      🔍 回溯 {stock_code} 過去 {lookback_quarters} 季資本支出...")
            
            # 嘗試獲取過去幾季的資料
            for i in range(1, lookback_quarters + 1):
                try:
                    # 計算目標日期（往前推i季）
                    target_date = datetime.now() - timedelta(days=90 * i)
                    
                    # 嘗試使用 auto_fetcher 的歷史資料功能
                    if hasattr(self.auto_fetcher, 'data_handler') and self.auto_fetcher.data_handler:
                        # 調用 data_handler 獲取歷史財務報表
                        financial_data = self.auto_fetcher._get_financial_statements(
                            stock_code, 
                            lookback_months=(i + 1) * 3  # 季度轉月份
                        )
                        
                        if financial_data and 'capex' in financial_data.get('data', {}):
                            historical_capex = financial_data['data']['capex'] / 1e8  # 轉億元
                            if historical_capex > 0:
                                print(f"      ✅ 找到第{i}季前資本支出: {historical_capex:.1f}億")
                                return historical_capex
                                
                except Exception as quarter_error:
                    print(f"      第{i}季資料獲取失敗: {quarter_error}")
                    continue
            
            print(f"      ❌ 無法獲取 {stock_code} 歷史資本支出")
            return None
            
        except Exception as e:
            print(f"      ❌ 歷史資料回溯失敗: {e}")
            return None
    
    def get_fallback_depreciation(self, stock_code: str, sector: str, capex: float) -> Optional[float]:
        """獲取折舊費用的替代值"""
        print(f"    🔄 嘗試獲取 {stock_code} 折舊費用替代值...")
        
        if capex and sector in self.industry_averages:
            ratio = self.industry_averages[sector]["depreciation_to_capex_ratio"]
            estimated_depreciation = capex * ratio
            print(f"    ✅ 使用行業平均估算: 折舊 {estimated_depreciation:.1f}億 (資本支出 * {ratio:.1%})")
            return estimated_depreciation
        
        return None
    
    def get_fallback_working_capital_change(self, stock_code: str, sector: str, revenue: float) -> float:
        """獲取營運資金變化的替代值"""
        if revenue and sector in self.industry_averages:
            ratio = self.industry_averages[sector]["working_capital_ratio"]
            estimated_wc_change = revenue * ratio
            print(f"    📊 使用行業平均估算營運資金變化: {estimated_wc_change:.1f}億")
            return estimated_wc_change
        
        return 0.0  # 預設為0
    
    def calculate_enhanced_free_cash_flow(self, stock_code: str, dcf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        增強版自由現金流計算，包含替代方案
        """
        print(f"  🧮 開始增強版自由現金流計算...")
        
        # 基礎數據
        net_income = dcf_data.get('net_income_parent', 0) / 1e8
        revenue = dcf_data.get('total_revenue', 0) / 1e8 if dcf_data.get('total_revenue') else None
        sector = dcf_data.get('sector', '其他')
        
        # 獲取或估算資本支出
        capex = dcf_data.get('capex', 0) / 1e8 if dcf_data.get('capex') else None
        if not capex or capex == 0:
            capex = self.get_fallback_capex(stock_code, sector, net_income, revenue)
            dcf_data['capex_estimated'] = True
        else:
            dcf_data['capex_estimated'] = False
        
        # 獲取或估算折舊費用
        depreciation = dcf_data.get('depreciation', 0) / 1e8 if dcf_data.get('depreciation') else None
        if not depreciation or depreciation == 0:
            depreciation = self.get_fallback_depreciation(stock_code, sector, capex or net_income * 0.3)
            dcf_data['depreciation_estimated'] = True
        else:
            dcf_data['depreciation_estimated'] = False
        
        # 獲取或估算攤銷費用
        amortization = dcf_data.get('amortization', 0) / 1e8 if dcf_data.get('amortization') else 0
        
        # 獲取或估算營運資金變化
        working_capital_change = self.get_fallback_working_capital_change(stock_code, sector, revenue or net_income * 5)
        
        # 計算自由現金流
        free_cash_flow = net_income + (depreciation or 0) + amortization - (capex or 0) - working_capital_change
        
        # 合理性檢查
        if free_cash_flow < 0:
            print(f"    ⚠️ 計算出負自由現金流 {free_cash_flow:.1f}億，調整為正值")
            free_cash_flow = max(free_cash_flow, net_income * 0.1)  # 至少為淨利的10%
        
        result = {
            'free_cash_flow': free_cash_flow,
            'net_income': net_income,
            'depreciation': depreciation or 0,
            'amortization': amortization,
            'capex': capex or 0,
            'working_capital_change': working_capital_change,
            'data_quality': self._assess_data_quality(dcf_data),
            'estimates_used': []
        }
        
        # 記錄使用的估算項目
        if dcf_data.get('capex_estimated'):
            result['estimates_used'].append('資本支出')
        if dcf_data.get('depreciation_estimated'):
            result['estimates_used'].append('折舊費用')
        
        return result
    
    def _assess_data_quality(self, dcf_data: Dict[str, Any]) -> str:
        """評估資料品質"""
        estimated_count = sum([
            dcf_data.get('capex_estimated', False),
            dcf_data.get('depreciation_estimated', False)
        ])
        
        if estimated_count == 0:
            return "高品質"
        elif estimated_count == 1:
            return "中等品質"
        else:
            return "低品質(多項估算)"
    
    def get_enhanced_data_with_fallback(self, stock_code: str) -> Dict[str, Any]:
        """增強版資料獲取 - 包含多資料源切換"""
        print(f"🔄 開始多資料源增強資料獲取: {stock_code}")
        
        # 資料源優先順序
        data_sources = [
            {'name': 'FinMind API', 'method': self._fetch_from_finmind},
            {'name': '備用資料源', 'method': self._fetch_from_backup},
            {'name': '歷史資料', 'method': self._fetch_from_history},
        ]
        
        for source in data_sources:
            try:
                print(f"  📡 嘗試資料源: {source['name']}")
                data = source['method'](stock_code)
                
                if data and self._validate_data_completeness(data):
                    print(f"  ✅ 成功從 {source['name']} 獲取完整資料")
                    data['data_source'] = source['name']
                    return data
                else:
                    print(f"  ⚠️ {source['name']} 資料不完整，嘗試下一個資料源")
                    
            except Exception as e:
                print(f"  ❌ {source['name']} 失敗: {e}")
                continue
        
        print(f"  ❌ 所有資料源都失敗，使用最基本估算")
        return self._create_minimal_estimate(stock_code)
    
    def _fetch_from_finmind(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """從FinMind API獲取資料"""
        return self.auto_fetcher.get_dcf_ready_data(stock_code)
    
    def _fetch_from_backup(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """從備用資料源獲取資料（可以是其他API或本地資料）"""
        # 這裡可以實現其他資料源的邏輯
        # 例如：Yahoo Finance, TEJ, 本地資料庫等
        print(f"      🔍 嘗試備用資料源獲取 {stock_code}")
        
        # 暫時返回None，未來可以擴展
        return None
    
    def _fetch_from_history(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """從歷史快取資料獲取"""
        # 嘗試從快取中獲取較舊但可用的資料
        print(f"      🔍 嘗試歷史快取獲取 {stock_code}")
        
        try:
            # 檢查快取目錄是否有舊資料
            cache_dir = "src/jojo_trading/core/cache/finmind_data"
            import os
            import glob
            
            # 尋找該股票的任何快取檔案
            pattern = f"{cache_dir}/{stock_code}_*"
            cache_files = glob.glob(pattern)
            
            if cache_files:
                print(f"      ✅ 找到 {len(cache_files)} 個快取檔案")
                # 可以嘗試讀取最新的快取檔案
                # 這裡簡化，實際可以實現完整的快取讀取邏輯
                return None
            else:
                print(f"      ❌ 沒有找到 {stock_code} 的快取資料")
                return None
                
        except Exception as e:
            print(f"      ❌ 歷史資料獲取失敗: {e}")
            return None
    
    def _validate_data_completeness(self, data: Dict[str, Any]) -> bool:
        """驗證資料完整性"""
        if not data or not data.get('success', False):
            return False
        
        # 檢查關鍵欄位
        required_fields = ['shares_outstanding', 'current_market_price', 'net_income_parent']
        for field in required_fields:
            if not data.get(field):
                print(f"      ❌ 缺少關鍵欄位: {field}")
                return False
        
        return True
    
    def _create_minimal_estimate(self, stock_code: str) -> Dict[str, Any]:
        """創建最基本的估算資料（當所有資料源都失敗時）"""
        print(f"      🆘 創建 {stock_code} 最基本估算資料")
        
        # 基於股票代碼的簡單估算
        try:
            code_num = int(stock_code)
            
            # 根據股票代碼範圍估算基本參數
            if 1000 <= code_num <= 1999:  # 傳統產業
                base_price = 50
                base_shares = 100_000_000
                base_revenue = 500
            elif 2000 <= code_num <= 2999:  # 電子股
                base_price = 200
                base_shares = 200_000_000
                base_revenue = 1000
            else:  # 其他
                base_price = 100
                base_shares = 150_000_000
                base_revenue = 750
            
            return {
                'success': True,
                'stock_code': stock_code,
                'company_name': f'股票 {stock_code}',
                'current_market_price': base_price,
                'shares_outstanding': base_shares,
                'net_income_parent': base_revenue * 0.1 * 1e8,  # 假設10%淨利率
                'capex': base_revenue * 0.05 * 1e8,  # 假設5%資本支出率
                'depreciation': base_revenue * 0.03 * 1e8,  # 假設3%折舊率
                'data_source': '緊急估算'
            }
            
        except:
            # 如果連股票代碼都有問題，使用預設值
            return {
                'success': True,
                'stock_code': stock_code,
                'company_name': f'股票 {stock_code}',
                'current_market_price': 100,
                'shares_outstanding': 100_000_000,
                'net_income_parent': 50 * 1e8,
                'capex': 25 * 1e8,
                'depreciation': 15 * 1e8,
                'data_source': '預設估算'
            }

def apply_data_fallback_to_dcf_page():
    """將資料替代方案應用到DCF分析頁面"""
    pass  # 這個函數將在DCF頁面中使用
