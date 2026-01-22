"""
JoJotrading 狀態機核心模組

此模組實現了基於 DCF 估值的台股篩選系統的狀態機架構，
通過不同狀態的轉換來完成完整的股票篩選和估值流程。

狀態轉換流程：
CONFIG_LOAD -> UI_INIT -> INDUSTRY_PROCESS -> DATA_FETCH -> VALUATION -> FILTERING -> RESULTS_DISPLAY

主要類別：
- JoJoState: 定義所有系統狀態的枚舉
- State: 狀態基礎類別，提供狀態執行的統一介面
- JoJoStateMachine: 狀態機管理器，控制狀態轉換和執行
- 各種狀態類別: ConfigLoadState, UIInitState, IndustryProcessState 等

每個狀態負責特定的業務邏輯：
- 產業資料處理、財務資料獲取、DCF 估值計算
- 成長股篩選、異常檢測、結果展示等

系統特色：
- 支援多語介面 (中文/英文)
- 整合成長股判定邏輯
- 具備異常檢測機制
- 可匯出 Excel 報告
"""

import streamlit as st
import pandas as pd
from enum import Enum, auto
import json # For loading industries.json
import requests # Added to resolve NameError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from ..utils.helpers import api_request_with_retry
import sys
from pathlib import Path
import concurrent.futures

# 添加專案根目錄到 Python 跊
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.jojo_trading.core import data_handler
from src.jojo_trading.analysis.growth_analyzer import evaluate_growth_potential, GrowthCriterion
from src.jojo_trading.core.auto_data_fetcher import AutoDataFetcher

class JoJoState(Enum):
    CONFIG_LOAD = auto()
    UI_INIT = auto()
    INDUSTRY_PROCESS = auto()
    DATA_FETCH = auto()
    VALUATION = auto()
    FILTERING = auto()
    RESULTS_DISPLAY = auto()
    EXPORT = auto()
    ERROR = auto()
    IDLE = auto()

class JoJoStateMachine:
    def __init__(self):
        self.current_state = JoJoState.CONFIG_LOAD
        self.context = {
            "selected_industry_name": None, # Changed from selected_industry
            "risk_preference": 0.10, # Default discount rate
            "potential_return_threshold": 0.15, # Default threshold for potential return
            "industry_data": None,
            "all_companies_openapi_data": None, # Cache for all companies basic data from OpenAPI
            "all_stock_prices_openapi_data": None, # Cache for all stock prices from OpenAPI
            "industry_stocks_details": [], # List of dicts for stocks in selected industry
            "processed_data": {}, # Dict to store financial data for each stock
            "valuation_results": [],
            "filtered_results": [],
            "error_message": None,            "dcf_short_term_growth_rate": 0.07, # 7% default
            "dcf_projection_years": 5,          # 5 years default
            "dcf_terminal_growth_rate": 0.025,  # 2.5% default
            # === Phase 1 Enhancement Parameters ===
            "use_enhanced_dcf": True,            # 使用增強版 DCF 估值
            "enable_data_validation": True,      # 啟用數據品質驗證
            "data_quality_threshold": 0.7,       # 數據品質閾值
            "min_data_quality_score": 60,       # 最低數據品質分數閾值
            "enable_scenario_analysis": True,    # 啟用情境分析
            "enable_monte_carlo": False,         # 蒙地卡羅模擬 (預設關閉以提升速度)
            "monte_carlo_simulations": 1000,     # 蒙地卡羅模擬次數
            "monte_carlo_iterations": 1000,     # 蒙地卡羅模擬次數 (別名)
            "scenario_volatility": 0.15,        # 情境分析波動率
            "enable_anomaly_detection": True,   # 啟用異常檢測
            "anomaly_threshold": 1.5,           # 異常檢測閾值，當期FCF_EPS超過歷史平均1.5倍視為異常
            "risk_free_rate": 0.01,            # 無風險利率 (台灣10年期公債)
            "market_premium": 0.06,             # 市場風險溢價
            "beta_default": 1.0                  # 預設 Beta 值
        }
        # Initialize FinMind API DataLoader (moved from data_handler to be instance-specific if needed)
        # self.finmind_api = data_handler.finmind_api # Use the one initialized in data_handler
        print("JoJoStateMachine initialized, starting in CONFIG_LOAD state.")
        self.execute_state() # Initial execution

    def transition_to(self, next_state):
        print(f"Transitioning from {self.current_state.name} to {next_state.name}")
        self.current_state = next_state
        # self.execute_state() # Removed to allow Streamlit UI loop to handle state transitions

    def execute_state(self):
        print(f"Entering state: {self.current_state.name}")
        if self.current_state == JoJoState.CONFIG_LOAD:
            ConfigLoadState(self.context, self).execute()
        elif self.current_state == JoJoState.UI_INIT:
            UiInitState(self.context, self).execute()
        elif self.current_state == JoJoState.INDUSTRY_PROCESS:
            IndustryProcessState(self.context, self).execute()
        elif self.current_state == JoJoState.DATA_FETCH:
            DataFetchState(self.context, self).execute()
        elif self.current_state == JoJoState.VALUATION:
            ValuationState(self.context, self).execute()
        elif self.current_state == JoJoState.FILTERING:
            FilteringState(self.context, self).execute()
        elif self.current_state == JoJoState.RESULTS_DISPLAY:
            ResultsDisplayState(self.context, self).execute()
        elif self.current_state == JoJoState.EXPORT:
            ExportState(self.context, self).execute()
        elif self.current_state == JoJoState.ERROR:
            ErrorState(self.context, self).execute()
        elif self.current_state == JoJoState.IDLE:
            IdleState(self.context, self).execute()
        print(f"{self.current_state.name} finished.")


class State:
    def __init__(self, context, machine):
        self.context = context
        self.machine = machine

    def execute(self):
        raise NotImplementedError

class ConfigLoadState(State):
    def execute(self):
        print("Executing ConfigLoadState: 載入設定檔...")
        try:
            # 修正檔案路徑，使用專案根目錄下的 data 資料夾
            industries_file = project_root / 'data' / 'industries.json'
            with open(industries_file, 'r', encoding='utf-8') as f:
                self.context['industry_data'] = json.load(f)
            print(f"  industries.json 已載入。偵測到產業數量: {len(self.context['industry_data'].get('industries', []))}")
            
            # 從 industry_data 提取產業名稱列表和風險選項
            industries_list = self.context['industry_data'].get('industries', []) # 'industries' is a list
            self.context['industry_names'] = [item['name'] for item in industries_list if isinstance(item, dict) and 'name' in item]
            if not self.context['industry_names']:
                 self.context['industry_names'] = ['無可用產業'] # Fallback
            
            # risk_premium_options is correctly a dictionary
            risk_premiums_config = self.context['industry_data'].get('risk_premium_options', {})
            self.context['risk_premium_options'] = risk_premiums_config
            
            # default_risk_premium is a top-level key in industries.json
            self.context['default_risk_premium'] = self.context['industry_data'].get('default_risk_premium', 0.04)

            # === Phase 1 Enhancement: Configure DCF method ===
            # Set data_handler to use enhanced DCF based on context setting
            data_handler.USE_ENHANCED_DCF = self.context.get('use_enhanced_dcf', True)
            print(f"  DCF 方法設定: {'增強版' if data_handler.USE_ENHANCED_DCF else '原始版'}")

            # Load OpenAPI company basic data if not already loaded
            if not self.context.get('all_companies_openapi_data'):
                self.context['all_companies_openapi_data'] = data_handler.get_all_companies_basic_data(self.context)

            self.machine.transition_to(JoJoState.UI_INIT)
        except FileNotFoundError:
            self.context['error_message'] = "錯誤：找不到 industries.json 設定檔。"
            self.machine.transition_to(JoJoState.ERROR)
        except json.JSONDecodeError:
            self.context['error_message'] = "錯誤：industries.json 設定檔格式錯誤。"
            self.machine.transition_to(JoJoState.ERROR)
        except Exception as e:
            self.context['error_message'] = f"載入設定時發生未預期錯誤: {e}"
            self.machine.transition_to(JoJoState.ERROR)
        print("ConfigLoadState 完成。")


class UiInitState(State):
    def execute(self):
        print("Executing UiInitState: 初始化 Streamlit UI...")
        # This state is primarily for UI setup in app.py
        # Transition to IDLE to avoid infinite loop in UI
        self.machine.transition_to(JoJoState.IDLE)
        print("UiInitState 完成，轉換到 IDLE 狀態等待用戶操作。")

class IndustryProcessState(State):
    def execute(self):
        # Use selected_industry_name from context, which is set by app.py
        selected_industry = self.context.get('selected_industry_name')
        selected_stock_codes = self.context.get('selected_stock_codes', [])
        print(f"Executing IndustryProcessState: 處理產業 '{selected_industry}'...")

        # 修正：個股直查模式（未選產業但有個股代號）可直接進入 DATA_FETCH
        if not selected_industry and not selected_stock_codes:
            self.context['error_message'] = "錯誤：未選擇產業，也未輸入個股代號。"
            self.machine.transition_to(JoJoState.ERROR)
            return

        self.machine.transition_to(JoJoState.DATA_FETCH)
        print("IndustryProcessState 完成。")

class DataFetchState(State):
    def execute(self):
        print("Executing DataFetchState: 抓取資料...")
        selected_industry_name = self.context.get('selected_industry_name') # Use the correct context key
        selected_stock_codes = self.context.get('selected_stock_codes', [])

        # Ensure all companies basic data is loaded (should be from ConfigLoadState)
        if not self.context.get('all_companies_openapi_data'):
            self.context['all_companies_openapi_data'] = data_handler.get_all_companies_basic_data(self.context)
            if not self.context.get('all_companies_openapi_data'): # Still none after trying
                self.context['error_message'] = "無法獲取所有上市公司基本資料。"
                self.machine.transition_to(JoJoState.ERROR)
                return

        # 支援個股直查模式
        if selected_stock_codes and not selected_industry_name:
            # 個股直查模式：只用「公司代號」欄位比對，並標準化欄位名稱
            all_companies = self.context['all_companies_openapi_data']
            self.context['industry_stocks_details'] = [
                {
                    "code": str(c.get("公司代號")),
                    "name": c.get("公司名稱"),
                    **c
                }
                for c in all_companies
                if isinstance(c, dict) and str(c.get('公司代號')) in [str(code) for code in selected_stock_codes]
            ]
        else:
            # 產業模式（維持原本 code 欄位邏輯）
            industries_list = self.context['industry_data'].get('industries', [])
            industry_name_to_code_map = {
                item['name']: item['code'] 
                for item in industries_list if isinstance(item, dict) and 'name' in item and 'code' in item
            }
            self.context['industry_stocks_details'] = [
                {
                    "code": str(s.get("公司代號", s.get("code"))),
                    "name": s.get("公司名稱", s.get("name")),
                    **s
                }
                for s in data_handler.filter_industry_stocks(
                    selected_industry_name,
                    industry_name_to_code_map,
                    self.context['all_companies_openapi_data']
                )
            ]
            if selected_stock_codes: # 產業模式下，若有選個股，再篩一次
                self.context['industry_stocks_details'] = [
                    s for s in self.context['industry_stocks_details'] if s['code'] in selected_stock_codes
                ]

        if not self.context['industry_stocks_details']:
            print(f"  (DataFetchState) 查無任何待處理股票（產業: '{selected_industry_name}', 個股: {selected_stock_codes}）。")
            self.context['processed_data'] = {} # Ensure it's empty
            self.machine.transition_to(JoJoState.VALUATION) # Proceed to valuation, which will handle empty data
            return

        print(f"  (DataFetchState) 正在獲取所有上市公司每日股價資料...")
        if not self.context.get('all_stock_prices_openapi_data'):
            try:
                print(f"    (DataFetchState) 使用智能重試機制獲取股價...")
                response = api_request_with_retry(f"{data_handler.API_BASE_URL}/t187ap03_L", timeout=30, verify=False)
                self.context['all_stock_prices_openapi_data'] = response.json()
                print(f"    (DataFetchState) 成功獲取 {len(self.context['all_stock_prices_openapi_data'])} 筆股價記錄。")
            except Exception as e:
                print(f"    (DataFetchState) 獲取股價時發生錯誤: {e}")
                self.context['all_stock_prices_openapi_data'] = []

        print(f"  開始為產業 '{selected_industry_name}' 處理資料...")
        print(f"  篩選後成分股詳細列表 ({selected_industry_name}):")
        for stock_detail in self.context['industry_stocks_details'][:3]: # Print first 3 for brevity
            print(f"    {stock_detail}")

        all_financial_data_for_stock = {}
        
        # 使用 AutoDataFetcher 進行自動化資料抓取
        fetcher = AutoDataFetcher()
        processed_count = 0
        
        # 獲取最大處理數量限制
        max_stocks = self.context.get('max_stocks', 0)
        if max_stocks > 0:
            target_stocks = self.context['industry_stocks_details'][:max_stocks]
        else:
            target_stocks = self.context['industry_stocks_details']
            
        total_stocks = len(target_stocks)
        
        print(f"  (DataFetchState) 預計處理 {total_stocks} 支股票 (上限: {'無限制' if max_stocks == 0 else max_stocks})...")
        progress_callback = self.context.get('progress_callback')

        # 定義單一股票抓取函數
        def fetch_single_stock(stock_detail):
            stock_code = stock_detail['code']
            stock_name = stock_detail['name']
            # 使用 AutoDataFetcher 獲取 DCF 就緒數據
            dcf_data = fetcher.get_dcf_ready_data(stock_code)
            return stock_code, stock_name, dcf_data, stock_detail

        # 使用 ThreadPoolExecutor 進行並行處理
        # 限制最大線程數為 20 或 股票總數，避免過多請求
        max_workers = min(20, total_stocks) if total_stocks > 0 else 1
        print(f"  (DataFetchState) 啟動並行處理 (Threads: {max_workers})...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任務
            future_to_stock = {executor.submit(fetch_single_stock, stock): stock for stock in target_stocks}
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_stock)):
                try:
                    stock_code, stock_name, dcf_data, original_detail = future.result()
                    
                    # 更新進度
                    if progress_callback:
                        progress_callback(i + 1, total_stocks, stock_code, stock_name)
                    
                    if dcf_data['success']:
                        financial_data_for_stock = dcf_data.copy()
                        # 確保名稱被保留
                        financial_data_for_stock['name'] = stock_name
                        
                        # 補充一些 ValuationState 可能需要的額外欄位
                        if 'eps_finmind' not in financial_data_for_stock:
                             try:
                                 ni = financial_data_for_stock.get('net_income_parent', 0)
                                 shares = financial_data_for_stock.get('shares_outstanding', 1)
                                 if shares > 0:
                                     financial_data_for_stock['eps_finmind'] = ni / shares
                             except:
                                 pass
                        
                        all_financial_data_for_stock[stock_code] = financial_data_for_stock
                        print(f"    (DataFetchState) 成功獲取 {stock_code} 數據")
                    else:
                        # 處理錯誤情況
                        error_msg = dcf_data.get('error', '未知錯誤')
                        print(f"    (DataFetchState) 獲取 {stock_code} 數據失敗: {error_msg}")
                        
                        financial_data_for_stock = original_detail.copy()
                        financial_data_for_stock['error'] = error_msg
                        all_financial_data_for_stock[stock_code] = financial_data_for_stock

                    processed_count += 1
                    
                except Exception as e:
                    print(f"    (DataFetchState) 處理線程發生異常: {e}")

        self.context['processed_data'] = all_financial_data_for_stock
        print(f"  已嘗試為 {processed_count} 支成分股提取財務數據和股價。")
        self.machine.transition_to(JoJoState.VALUATION)
        print("DataFetchState 完成。")


class ValuationState(State):
    def execute(self):
        print("Executing ValuationState: 進行 DCF 估值...")
        valuation_results = []
        risk_preference = self.context.get('risk_preference', 0.10) # Default if not set
        
        for stock_code, financials in self.context.get('processed_data', {}).items():
            # Check if essential data was fetched successfully before attempting valuation
            if financials.get("error") and "無法獲取" in financials.get("error"): # Check for specific fetch errors
                print(f"  (ValuationState) 股票 {stock_code} ({financials.get('name', '')}) 缺少有效的財務數據，跳過估值。錯誤: {financials.get('error')}")
                valuation_results.append({
                    "stock_code": stock_code, 
                    "name": financials.get('name', stock_code), 
                    "error": financials.get("error", "數據提取失敗導致無法估值")
                })
                continue

            valuation_result = data_handler.calculate_dcf_valuation(stock_code, financials, risk_preference, self.context)
            valuation_result['name'] = financials.get('name', stock_code) # Add stock name for display
            valuation_results.append(valuation_result)

        self.context['valuation_results'] = valuation_results
        print(f"ValuationState 完成，共處理 {len(valuation_results)} 筆估值結果。")
        self.machine.transition_to(JoJoState.FILTERING)
        print("ValuationState 完成。")


class FilteringState(State):
    def execute(self):
        print("Executing FilteringState: 篩選估值後的股票...")
        results = self.context.get('valuation_results', [])
        threshold = self.context.get('potential_return_threshold')
        if threshold is None:
            threshold = 0.15 # Default 15%
        min_eps = self.context.get('min_eps_threshold', 0.01) # Default minimum EPS > 0

        # 成長股篩選設定
        enable_growth_filter = self.context.get('enable_growth_filter', False)
        print(f"  (FilteringState) 收到 {len(results)} 筆估值結果準備篩選。篩選潛在報酬 > {threshold*100:.1f}%")
        if enable_growth_filter:
            print("  (FilteringState) 成長股篩選已啟用")

        filtered_results = []
        excluded_results = [] # 儲存被排除的股票詳細資訊
        growth_filtered_count = 0
        
        # 初始化排除原因統計
        exclusion_summary = {
            'valuation_error': 0,
            'missing_data': 0,
            'intrinsic_value_zero_or_negative': 0,
            'eps_negative_or_low': 0,
            'growth_filter_failed': 0,
            'potential_return_low': 0,
            'total_excluded': 0
        }
        
        for res in results:
            if res.get("error"):
                print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 存在估值錯誤，已跳過: {res['error']}")
                exclusion_summary['valuation_error'] += 1
                exclusion_summary['total_excluded'] += 1
                excluded_results.append({
                    'stock_code': res.get('stock_code'),
                    'name': res.get('name', ''),
                    'reason': f"估值錯誤: {res.get('error')}",
                    'category': 'valuation_error'
                })
                continue

            intrinsic_value = res.get("intrinsic_value_per_share")
            current_price = res.get("current_market_price")
            potential_return = res.get("potential_return")
            source_eps = res.get("source_eps") # EPS from FinMind (or other source)

            if intrinsic_value is None or current_price is None or potential_return is None:
                print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 缺少估值或市價數據，已跳過。")
                exclusion_summary['missing_data'] += 1
                exclusion_summary['total_excluded'] += 1
                excluded_results.append({
                    'stock_code': res.get('stock_code'),
                    'name': res.get('name', ''),
                    'reason': "數據缺失 (無法計算內在價值)",
                    'category': 'missing_data'
                })
                continue
            # 主要篩選條件：潛在回報和內在價值
            # 根據模式決定是否篩選
            is_ranking_mode = self.context.get('screening_mode') == 'ranking'

            if intrinsic_value <= 0:
                if not is_ranking_mode:
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 因 內在價值 ({intrinsic_value:.2f}) <= 0 不符條件而未被選入。")
                    exclusion_summary['intrinsic_value_zero_or_negative'] += 1
                    exclusion_summary['total_excluded'] += 1
                    excluded_results.append({
                        'stock_code': res.get('stock_code'),
                        'name': res.get('name', ''),
                        'reason': f"內在價值異常 ({intrinsic_value:.2f} <= 0)",
                        'category': 'intrinsic_value_zero_or_negative'
                    })
                    continue
                else:
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 內在價值 ({intrinsic_value:.2f}) <= 0，但在排行模式下保留。")
            
            
            # 檢查 EPS (無論模式如何，通常都應該過濾掉虧損股，除非用戶特別想要看)
            # 這裡假設排行模式下，我們還是希望看到有基本獲利的股票，或者我們可以放寬
            # 為了符合"排行"的直覺，我們只在篩選模式下嚴格過濾 EPS，或者在排行模式下標記
            # 但原邏輯是直接 continue，我們保持原邏輯但記錄原因
            if source_eps is None or source_eps < min_eps:
                if not is_ranking_mode:
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 近期會計EPS ({source_eps}) 為負或過低，已排除。")
                    exclusion_summary['eps_negative_or_low'] += 1
                    exclusion_summary['total_excluded'] += 1
                    excluded_results.append({
                        'stock_code': res.get('stock_code'),
                        'name': res.get('name', ''),
                        'reason': f"EPS 過低或虧損 ({source_eps})",
                        'category': 'eps_negative_or_low'
                    })
                    continue
                else:
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 近期會計EPS ({source_eps}) 為負或過低，但在排行模式下保留。")

            # 成長股篩選檢查
            if enable_growth_filter:
                growth_result = self._evaluate_growth_stock(res)
                if not growth_result['is_growth_stock']:
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 未通過成長股條件，已篩除。")
                    growth_filtered_count += 1
                    exclusion_summary['growth_filter_failed'] += 1
                    exclusion_summary['total_excluded'] += 1
                    excluded_results.append({
                        'stock_code': res.get('stock_code'),
                        'name': res.get('name', ''),
                        'reason': "未通過成長股條件",
                        'category': 'growth_filter_failed'
                    })
                    continue
                else:
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 通過成長股條件檢查。")
                    # 將成長股分析結果添加到結果中
                    res['growth_analysis'] = growth_result
            
            if potential_return >= threshold or is_ranking_mode:
                filtered_results.append(res)
            else:
                # 即使EPS為正，如果潛在回報不足，也不選入
                print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 因潛在報酬 ({potential_return:.1%}) 未達標 (> {threshold*100:.1f}%) 而未被選入 (內在價值: {intrinsic_value:.2f}, 會計EPS: {source_eps}).")
                exclusion_summary['potential_return_low'] += 1
                exclusion_summary['total_excluded'] += 1
                excluded_results.append({
                    'stock_code': res.get('stock_code'),
                    'name': res.get('name', ''),
                    'reason': f"潛在報酬不足 ({potential_return:.1%} < {threshold:.1%})",
                    'category': 'potential_return_low'
                })

        # 如果是排行模式，按潛在回報排序
        if self.context.get('screening_mode') == 'ranking':
            filtered_results.sort(key=lambda x: x.get('potential_return', -999), reverse=True)

        self.context['filtered_results'] = filtered_results
        self.context['excluded_results'] = excluded_results
        self.context['exclusion_summary'] = exclusion_summary
        
        if enable_growth_filter:
            print(f"FilteringState 完成，成長股篩選排除了 {growth_filtered_count} 筆股票，最終篩選出 {len(filtered_results)} 筆符合條件的股票。")
        else:
            print(f"FilteringState 完成，共篩選出 {len(filtered_results)} 筆符合條件的股票。")
        self.machine.transition_to(JoJoState.RESULTS_DISPLAY)
        print("FilteringState 完成。")
    
    def _evaluate_growth_stock(self, stock_result):
        """評估單一股票是否符合成長股條件"""
        try:
            # 從context取得成長股設定
            revenue_cagr_enabled = self.context.get('revenue_cagr_enabled', False)
            revenue_cagr_threshold = self.context.get('revenue_cagr_threshold', 15.0) / 100.0  # 轉換為小數
            
            eps_cagr_enabled = self.context.get('eps_cagr_enabled', False)
            eps_cagr_threshold = self.context.get('eps_cagr_threshold', 15.0) / 100.0  # 轉換為小數
            
            roe_enabled = self.context.get('roe_enabled', True)
            roe_threshold = self.context.get('roe_threshold', 15.0) / 100.0  # 轉換為小數
            
            logic_operator = self.context.get('growth_logic_operator', 'AND')
            
            # 構建成長條件列表
            criteria = []
            
            if revenue_cagr_enabled:
                criteria.append(GrowthCriterion(
                    metric_name='revenue_cagr',
                    period_years=3,
                    threshold=revenue_cagr_threshold,
                    operator='>',
                    label=f'近3年營收CAGR > {revenue_cagr_threshold*100:.1f}%'
                ))
            
            if eps_cagr_enabled:
                criteria.append(GrowthCriterion(
                    metric_name='eps_cagr',
                    period_years=3,
                    threshold=eps_cagr_threshold,
                    operator='>',
                    label=f'近3年EPS CAGR > {eps_cagr_threshold*100:.1f}%'
                ))
            
            if roe_enabled:
                criteria.append(GrowthCriterion(
                    metric_name='roe',
                    period_years=None,
                    threshold=roe_threshold,
                    operator='>',
                    label=f'最新ROE > {roe_threshold*100:.1f}%'
                ))
            
            # 如果沒有啟用任何條件，視為通過
            if not criteria:
                return {
                    "is_growth_stock": True,
                    "details": []
                }
            
            # 執行成長股評估
            return evaluate_growth_potential(
                financial_data=stock_result,
                criteria_config=criteria,
                logic_operator=logic_operator
            )
            
        except Exception as e:
            print(f"  (FilteringState) 成長股評估過程發生錯誤: {e}")
            # 如果評估失敗，預設為不通過
            return {
                "is_growth_stock": False,
                "details": [{"criterion": "評估錯誤", "value": None, "status": f"錯誤: {e}"}]
            }


class ResultsDisplayState(State):
    def execute(self):
        print("Executing ResultsDisplayState: 顯示篩選後的結果...")
        # 僅顯示結果，不自動 transition，不呼叫 st.rerun()
        # 由 UI 端按鈕觸發 transition
        pass

class ExportState(State):
    def execute(self):
        print("Executing ExportState: 匯出結果...")
        # This state would handle exporting the results to a file or other medium
        # For now, it just transitions to IDLE
        self.machine.transition_to(JoJoState.IDLE)
        print("ExportState 完成。")

class ErrorState(State):
    def execute(self):
        print("Executing ErrorState: 處理錯誤...")
        # This state would handle any errors that occurred in the process
        # For now, it just transitions to IDLE after displaying the error
        error_message = self.context.get('error_message', '發生未知錯誤')
        print(f"  錯誤訊息: {error_message}")
        st.error(error_message) # Display the error in Streamlit
        self.machine.transition_to(JoJoState.IDLE)
        print("ErrorState 完成。")

class IdleState(State):
    def execute(self):
        print("Executing IdleState: 等待操作...")
        # This state represents the idle state, waiting for user action or input
        # Do not auto-transition to avoid infinite loops
        # User actions in UI will trigger appropriate state transitions
        print("IdleState: 系統就緒，等待用戶操作。")


class MachineContext:
    """狀態機上下文類 - 向後兼容性"""
    
    def __init__(self):
        self.state = "idle"
        self.data = {}
        self.config = {}
    
    def set_state(self, new_state):
        """設置新狀態"""
        self.state = new_state
    
    def get_state(self):
        """獲取當前狀態"""
        return self.state
    
    def set_data(self, key, value):
        """設置數據"""
        self.data[key] = value
    
    def get_data(self, key, default=None):
        """獲取數據"""
        return self.data.get(key, default)
