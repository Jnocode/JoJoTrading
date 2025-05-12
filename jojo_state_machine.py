import streamlit as st
import pandas as pd
from enum import Enum, auto
import data_handler # Import the refactored data_handler
import json # For loading industries.json
import requests # Added to resolve NameError

class JoJoState(Enum):
    CONFIG_LOAD = auto()
    UI_INIT = auto()
    INDUSTRY_PROCESS = auto()
    DATA_FETCH = auto()
    VALUATION = auto()
    FILTERING = auto()
    RESULTS_DISPLAY = auto()
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
            "error_message": None,
            "dcf_short_term_growth_rate": 0.07, # 7% default
            "dcf_projection_years": 5,          # 5 years default
            "dcf_terminal_growth_rate": 0.025   # 2.5% default
        }
        # Initialize FinMind API DataLoader (moved from data_handler to be instance-specific if needed)
        # self.finmind_api = data_handler.finmind_api # Use the one initialized in data_handler
        print("JoJoStateMachine initialized, starting in CONFIG_LOAD state.")
        self.execute_state() # Initial execution

    def transition_to(self, next_state):
        print(f"Transitioning from {self.current_state.name} to {next_state.name}")
        self.current_state = next_state
        self.execute_state()

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
            with open('industries.json', 'r', encoding='utf-8') as f:
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
        # For now, it just transitions. If UI elements trigger state changes,
        # those will be handled by callbacks in app.py that call machine.transition_to()
        # self.machine.transition_to(JoJoState.IDLE) # Or to another state if auto-processing
        print("UiInitState 完成。") # No automatic transition from here, wait for UI interaction

class IndustryProcessState(State):
    def execute(self):
        # Use selected_industry_name from context, which is set by app.py
        selected_industry = self.context.get('selected_industry_name')
        print(f"Executing IndustryProcessState: 處理產業 '{selected_industry}'...")
        if not selected_industry: # Check the correct context key
            self.context['error_message'] = "錯誤：未選擇產業。"
            self.machine.transition_to(JoJoState.ERROR)
            return

        self.machine.transition_to(JoJoState.DATA_FETCH)
        print("IndustryProcessState 完成。")

class DataFetchState(State):
    def execute(self):
        print("Executing DataFetchState: 抓取資料...")
        selected_industry_name = self.context.get('selected_industry_name') # Use the correct context key
        
        # The way industries.json is structured, 'industries' is a list of dicts, not a dict itself.
        # We need to build industry_name_to_code_map from this list.
        industries_list = self.context['industry_data'].get('industries', [])
        industry_name_to_code_map = {
            item['name']: item['code'] 
            for item in industries_list if isinstance(item, dict) and 'name' in item and 'code' in item
        }
        
        # Ensure all companies basic data is loaded (should be from ConfigLoadState)
        if not self.context.get('all_companies_openapi_data'):
            self.context['all_companies_openapi_data'] = data_handler.get_all_companies_basic_data(self.context)
            if not self.context.get('all_companies_openapi_data'): # Still none after trying
                self.context['error_message'] = "無法獲取所有上市公司基本資料。"
                self.machine.transition_to(JoJoState.ERROR)
                return

        # Filter stocks for the selected industry
        self.context['industry_stocks_details'] = data_handler.filter_industry_stocks(
            selected_industry_name,
            industry_name_to_code_map,
            self.context['all_companies_openapi_data']
        )

        if not self.context['industry_stocks_details']:
            print(f"  (DataFetchState) 產業 '{selected_industry_name}' 中沒有找到任何股票。")
            self.context['processed_data'] = {} # Ensure it's empty
            self.machine.transition_to(JoJoState.VALUATION) # Proceed to valuation, which will handle empty data
            return

        print(f"  (DataFetchState) 正在獲取所有上市公司每日股價資料...")
        if not self.context.get('all_stock_prices_openapi_data'):
            try:
                print(f"    (DataFetchState) 警告：將嘗試禁用 SSL 憑證驗證 (verify=False) 來獲取股價。")
                response = requests.get(f"{data_handler.API_BASE_URL}/t187ap03_L", timeout=20, verify=False) # Re-using the all companies endpoint for prices for now
                response.raise_for_status()
                self.context['all_stock_prices_openapi_data'] = response.json() # This needs to be actual price data endpoint
                print(f"    (DataFetchState) 成功獲取 {len(self.context['all_stock_prices_openapi_data'])} 筆股價記錄。") # This log might be misleading
            except Exception as e:
                print(f"    (DataFetchState) 獲取股價時發生錯誤: {e}")
                self.context['all_stock_prices_openapi_data'] = [] # Ensure it's an empty list on error

        print(f"  開始為產業 '{selected_industry_name}' 處理資料...")
        print(f"  篩選後成分股詳細列表 ({selected_industry_name}):")
        for stock_detail in self.context['industry_stocks_details'][:3]: # Print first 3 for brevity
            print(f"    {stock_detail}")

        all_financial_data_for_stock = {}
        start_date_finmind = "2022-01-01" # For FinMind, fetch a longer history

        # TEMPORARY: Limit the number of stocks processed to avoid API rate limits during testing
        processed_count = 0
        limit_stocks = 3 # Reduce further to be safer with API limits
        print(f"  (DataFetchState) DEBUG: Processing up to {limit_stocks} stocks to avoid API rate limits.")

        for stock_detail in self.context['industry_stocks_details']: # Iterate over the original full list
            if processed_count >= limit_stocks:
                print(f"  (DataFetchState) DEBUG: Reached processing limit of {limit_stocks} stocks.")
                break # Exit the loop
            
            stock_code = stock_detail['code']
            print(f"  準備為 {stock_code} ({stock_detail['name']}) 從 FinMind 提取財報數據... (Processing {processed_count + 1}/{limit_stocks})")
            
            financial_data_for_stock = stock_detail.copy() # Start with basic info
            financial_data_for_stock['error'] = [] # Initialize error list

            # Fetch Balance Sheet (BS)
            df_bs = data_handler.fetch_finmind_financial_statement_data(stock_code, start_date_finmind, 'BalanceSheet')
            if not df_bs.empty:
                bs_items_map = {
                    'ar_t0': 'AccountsReceivableNet', 
                    'inv_t0': 'Inventories', 
                    'ap_t0': 'AccountsPayable',
                    'ar_t1': 'AccountsReceivableNet', # Will be handled by lookback
                    'inv_t1': 'Inventories',          # Will be handled by lookback
                    'ap_t1': 'AccountsPayable'        # Will be handled by lookback
                }
                # Extract T0 (latest)
                extracted_bs_items_t0 = data_handler.extract_finmind_items(df_bs, bs_items_map, max_lookback_periods=0)
                # Extract T-1 (one period before latest)
                if extracted_bs_items_t0.get('report_date'):
                    latest_report_date_dt = pd.to_datetime(extracted_bs_items_t0['report_date'])
                    available_dates_in_bs = sorted(pd.to_datetime(df_bs['date'].unique()), reverse=True)
                    if latest_report_date_dt in available_dates_in_bs:
                        idx_latest = available_dates_in_bs.index(latest_report_date_dt)
                        if idx_latest + 1 < len(available_dates_in_bs):
                            prev_report_date_str = available_dates_in_bs[idx_latest + 1].strftime('%Y-%m-%d')
                            extracted_bs_items_t1_temp = data_handler.extract_finmind_items(df_bs, bs_items_map, report_date_str=prev_report_date_str, max_lookback_periods=0)
                            # Rename keys for T-1
                            for item_key in ['ar_t0', 'inv_t0', 'ap_t0']: # these are the keys in bs_items_map for T0
                                t1_key = item_key.replace('_t0', '_t1')
                                financial_data_for_stock[t1_key] = extracted_bs_items_t1_temp.get(item_key) # Use original key to get value
                            financial_data_for_stock['bs_report_date_t1'] = extracted_bs_items_t1_temp.get('report_date')
                financial_data_for_stock.update(extracted_bs_items_t0) 
                # Ensure bs_report_date_t0 is explicitly set from the 'report_date' key of extracted_bs_items_t0
                financial_data_for_stock['bs_report_date_t0'] = extracted_bs_items_t0.get('report_date')

                # For T-1, if extracted_bs_items_t1_temp was populated
                if 'extracted_bs_items_t1_temp' in locals() and extracted_bs_items_t1_temp:
                     financial_data_for_stock['bs_report_date_t1'] = extracted_bs_items_t1_temp.get('report_date')
                
                print(f"    (DataFetchState) 股票 {stock_code} 資產負債表 T0: {financial_data_for_stock.get('bs_report_date_t0')}, T-1: {financial_data_for_stock.get('bs_report_date_t1')}")

            else:
                financial_data_for_stock['error'].append("無法獲取資產負債表")


            # Fetch Cash Flow Statement (CF)
            df_cf = data_handler.fetch_finmind_financial_statement_data(stock_code, start_date_finmind, 'CashFlowsStatement')
            if not df_cf.empty:
                # Add more candidates for capex and depreciation based on common FinMind types
                cf_items_map = {
                    'capex': [
                        'PropertyAndPlantAndEquipment',                 # Found in test_finmind_api.py output
                        'AcquisitionOfPropertyPlantAndEquipment',       # Primary
                        'FixedAssetsPurchases',                         # Common alternative
                        'PurchaseOfPropertyPlantAndEquipment',          # Another alternative
                        'CashOutflowForAcquisitionOfPropertyPlantAndEquipment', # More descriptive
                        'IncreaseInPropertyPlantAndEquipment',          # Change in PPE
                        'AcquisitionOfIntangibleAssetsOtherThanGoodwill', # Intangible assets
                        'CashOutflowForAcquisitionOfIntangibleAssets'   # Cash outflow for intangibles
                    ],
                    'depreciation': [ # This will cover both depreciation and amortization
                        'DepreciationExpense',                          # Primary for IS, but sometimes in CF
                        'DepreciationAndAmortizationExpense',           # Common in CF (covers both)
                        'DepreciationAmortization',                     # Short form (covers both)
                        'DepreciationAndAmortization',                  # Another common form (covers both)
                        'Depreciation',                                 # Depreciation only
                        'Amortization',                                 # Amortization only (if separate)
                        'PropertyPlantAndEquipmentDepreciation'         # Specific depreciation
                    ],
                    'amortization': [ # Keep separate if needed, but usually covered by 'depreciation' list
                        'AmortizationExpense',
                        'Amortization'
                    ]
                }
                extracted_cf_items = data_handler.extract_finmind_items(df_cf, cf_items_map, report_date_str=financial_data_for_stock.get('bs_report_date_t0')) # Use BS T0 date as target
                financial_data_for_stock.update(extracted_cf_items)
                financial_data_for_stock['cf_report_date'] = extracted_cf_items.get('report_date')
            else:
                financial_data_for_stock['error'].append("無法獲取現金流量表")

            # Fetch Income Statement (IS) - FinancialStatements in FinMind
            df_is = data_handler.fetch_finmind_financial_statement_data(stock_code, start_date_finmind, 'FinancialStatements')
            if not df_is.empty:
                is_items_map = {'net_income_parent': 'EquityAttributableToOwnersOfParent', 'eps_finmind': 'EPS'} # 'revenue' can also be added if needed
                extracted_is_items = data_handler.extract_finmind_items(df_is, is_items_map, report_date_str=financial_data_for_stock.get('bs_report_date_t0')) # Use BS T0 date as target
                financial_data_for_stock.update(extracted_is_items)
                financial_data_for_stock['is_report_date'] = extracted_is_items.get('report_date')
            else:
                financial_data_for_stock['error'].append("無法獲取損益表")

            # Get current market price using the new FinMind price fetching function
            # Use the latest available financial report date as the target date for the price,
            # or None to get the absolute latest price if no report dates are available.
            price_target_date = financial_data_for_stock.get('is_report_date') or \
                                financial_data_for_stock.get('cf_report_date') or \
                                financial_data_for_stock.get('bs_report_date_t0')
                                
            current_price = data_handler.fetch_finmind_stock_price(stock_code, target_date_str=price_target_date)
            
            financial_data_for_stock['current_market_price'] = current_price
            if current_price is None:
                 financial_data_for_stock['error'].append(f"無法從FinMind獲取股票 {stock_code} 的目前股價 (目標日期: {price_target_date})")

            # Consolidate errors
            if financial_data_for_stock['error']:
                financial_data_for_stock['error'] = "; ".join(financial_data_for_stock['error'])
            else:
                del financial_data_for_stock['error'] # Remove if no errors

            all_financial_data_for_stock[stock_code] = financial_data_for_stock
            # DEBUG print for the first few stocks
            # if len(all_financial_data_for_stock) < 4:
            #    print(f"    (DataFetchState) [DEBUG] Stock {stock_code} - Final financial_data_for_stock: NI={financial_data_for_stock.get('net_income_parent')}, SourceField={financial_data_for_stock.get('net_income_parent_source_field')}")
            
            processed_count += 1

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
            # DEBUG: Print the financials dictionary being passed to DCF
            # print(f"  (ValuationState) [DEBUG] Valuating {stock_code}, Data before DCF: {financials}")
            
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
        threshold = self.context.get('potential_return_threshold', 0.15) # Default 15%
        min_eps = self.context.get('min_eps_threshold', 0.01) # Default minimum EPS > 0

        print(f"  (FilteringState) 收到 {len(results)} 筆估值結果準備篩選。篩選潛在報酬 > {threshold*100:.1f}%")
        
        filtered_results = []
        for res in results:
            if res.get("error"):
                print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 存在估值錯誤，已跳過: {res['error']}")
                continue

            intrinsic_value = res.get("intrinsic_value_per_share")
            current_price = res.get("current_market_price")
            potential_return = res.get("potential_return")
            source_eps = res.get("source_eps") # EPS from FinMind (or other source)

            if intrinsic_value is None or current_price is None or potential_return is None:
                print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 缺少估值或市價數據，已跳過。")
                continue
            
            if intrinsic_value <= 0:
                 print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 因 內在價值 ({intrinsic_value:.2f}) <= 0 不符條件而未被選入。")
                 continue

            # 主要篩選條件：潛在回報和內在價值
            if potential_return >= threshold:
                # 檢查近期會計EPS，如果為負，則添加警告，而不是直接過濾
                if source_eps is None or source_eps < min_eps:
                    res['warning'] = f"近期會計EPS ({source_eps}) 為負或過低。"
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')})近期會計EPS ({source_eps}) 為負或過低，已加入警告。")
                filtered_results.append(res)
            else:
                # 即使EPS為正，如果潛在回報不足，也不選入
                print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 因潛在報酬 ({potential_return:.1%}) 未達標 (> {threshold*100:.1f}%) 而未被選入 (內在價值: {intrinsic_value:.2f}, 會計EPS: {source_eps}).")

        # Convert np.float64 to native Python floats for better compatibility (e.g., JSON serialization)
        cleaned_filtered_results = []
        for result_item in filtered_results:
            cleaned_item = {}
            for key, value in result_item.items():
                if isinstance(value, pd.Series): # Handle potential Series if a key returns multiple rows by mistake
                    cleaned_item[key] = value.tolist() if not value.empty else None
                elif hasattr(value, 'item') and callable(getattr(value, 'item')): # Check for numpy types like np.float64
                    try:
                        cleaned_item[key] = value.item() # Convert to Python native type
                    except: # Fallback if item() fails for some reason
                        cleaned_item[key] = value 
                else:
                    cleaned_item[key] = value
            cleaned_filtered_results.append(cleaned_item)

        self.context['filtered_results'] = cleaned_filtered_results
        print(f"  (FilteringState) 篩選完成，選出 {len(cleaned_filtered_results)} 支股票。")
        self.machine.transition_to(JoJoState.RESULTS_DISPLAY)
        print("FilteringState 完成。")


class ResultsDisplayState(State):
    def execute(self):
        print(f"Executing ResultsDisplayState: 準備顯示結果 {self.context.get('filtered_results')}...")
        # Actual display logic is in app.py. This state remains active 
        # until a UI action (e.g., "New Query" button) triggers a transition.
        # No automatic transition from here.
        print("ResultsDisplayState 完成。 (等待UI操作)")

class ErrorState(State):
    def execute(self):
        print(f"Executing ErrorState: 錯誤 - {self.context.get('error_message', '未知錯誤')}")
        # Error display logic is in app.py
        # Could transition to IDLE or UI_INIT to allow user to retry/reconfigure
        self.machine.transition_to(JoJoState.UI_INIT) 
        print("ErrorState 完成。")

class IdleState(State):
    def execute(self):
        print("Executing IdleState: 系統閒置，等待使用者操作。")
        # System waits for user interaction which will trigger transitions from app.py
        print("IdleState 完成。")
