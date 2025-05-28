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
            "error_message": None,
            "dcf_short_term_growth_rate": 0.07, # 7% default
            "dcf_projection_years": 5,          # 5 years default
            "dcf_terminal_growth_rate": 0.025,  # 2.5% default
            # === 一次性收益異常檢測參數 ===
            "enable_anomaly_detection": True,   # 啟用異常檢測，預設開啟
            "anomaly_threshold": 1.5             # 異常檢測閾值，當期FCF_EPS超過歷史平均1.5倍視為異常
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

        # 移除暫時的筆數限制，完整處理所有成分股
        processed_count = 0

        for stock_detail in self.context['industry_stocks_details']: # Iterate over the original full list
            stock_code = stock_detail['code']
            print(f"  準備為 {stock_code} ({stock_detail['name']}) 從 FinMind 提取財報數據... (Processing {processed_count + 1}/{len(self.context['industry_stocks_details'])})")
            
            financial_data_for_stock = stock_detail.copy() # Start with basic info
            financial_data_for_stock['error'] = [] # Initialize error list

            # Fetch Balance Sheet (BS)
            df_bs = data_handler.fetch_finmind_financial_statement_data(stock_code, start_date_finmind, 'BalanceSheet')
            freq = self.context.get('financial_data_freq', '季度')
            # --- 新增：自動回退機制 ---
            bs_items_map = {
                'ar_t0': 'AccountsReceivableNet', 
                'inv_t0': 'Inventories', 
                'ap_t0': 'AccountsPayable',
                'ar_t1': 'AccountsReceivableNet', # Will be handled by lookback
                'inv_t1': 'Inventories',          # Will be handled by lookback
                'ap_t1': 'AccountsPayable'        # Will be handled by lookback
            }
            available_dates_in_bs = sorted(pd.to_datetime(df_bs['date'].unique()), reverse=True) if not df_bs.empty else []
            report_date_t0 = None
            report_date_t1 = None
            extracted_bs_items_t0 = {}
            extracted_bs_items_t1_temp = None
            if available_dates_in_bs:
                # 先嘗試最新一期
                report_date_t0 = available_dates_in_bs[0].strftime('%Y-%m-%d')
                extracted_bs_items_t0 = data_handler.extract_finmind_items(df_bs, bs_items_map, report_date_str=report_date_t0, max_lookback_periods=2)
                # 若主欄位皆為 None，則自動回退一期
                if all(extracted_bs_items_t0.get(k) is None for k in ['ar_t0', 'inv_t0', 'ap_t0']):
                    if len(available_dates_in_bs) > 1:
                        report_date_t0 = available_dates_in_bs[1].strftime('%Y-%m-%d')
                        extracted_bs_items_t0 = data_handler.extract_finmind_items(df_bs, bs_items_map, report_date_str=report_date_t0, max_lookback_periods=2)
                # T-1
                if len(available_dates_in_bs) > 1:
                    report_date_t1 = available_dates_in_bs[1].strftime('%Y-%m-%d')
                    extracted_bs_items_t1_temp = data_handler.extract_finmind_items(df_bs, bs_items_map, report_date_str=report_date_t1, max_lookback_periods=2)
                    # 若主欄位皆為 None，則再回退一期
                    if all(extracted_bs_items_t1_temp.get(k) is None for k in ['ar_t0', 'inv_t0', 'ap_t0']) and len(available_dates_in_bs) > 2:
                        report_date_t1 = available_dates_in_bs[2].strftime('%Y-%m-%d')
                        extracted_bs_items_t1_temp = data_handler.extract_finmind_items(df_bs, bs_items_map, report_date_str=report_date_t1, max_lookback_periods=2)
            else:
                extracted_bs_items_t0 = {}
            if extracted_bs_items_t0:
                financial_data_for_stock.update(extracted_bs_items_t0)
                financial_data_for_stock['bs_report_date_t0'] = extracted_bs_items_t0.get('report_date')
            if extracted_bs_items_t1_temp:
                for item_key in ['ar_t0', 'inv_t0', 'ap_t0']:
                    t1_key = item_key.replace('_t0', '_t1')
                    financial_data_for_stock[t1_key] = extracted_bs_items_t1_temp.get(item_key)
                financial_data_for_stock['bs_report_date_t1'] = extracted_bs_items_t1_temp.get('report_date')
            if extracted_bs_items_t0:
                print(f"    (DataFetchState) 股票 {stock_code} 資產負債表 T0: {financial_data_for_stock.get('bs_report_date_t0')}, T-1: {financial_data_for_stock.get('bs_report_date_t1')}")
            else:
                financial_data_for_stock['error'].append("無法獲取資產負債表")


            # Fetch Cash Flow Statement (CF)
            df_cf = data_handler.fetch_finmind_financial_statement_data(stock_code, start_date_finmind, 'CashFlowsStatement')
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
            available_dates_in_cf = sorted(pd.to_datetime(df_cf['date'].unique()), reverse=True) if not df_cf.empty else []
            cf_report_date = financial_data_for_stock.get('bs_report_date_t0')
            extracted_cf_items = {}
            if available_dates_in_cf:
                # 先嘗試與資產負債表同日期
                if cf_report_date and pd.to_datetime(cf_report_date) in available_dates_in_cf:
                    extracted_cf_items = data_handler.extract_finmind_items(df_cf, cf_items_map, report_date_str=cf_report_date, max_lookback_periods=2)
                else:
                    # 若沒有，則用最新一期
                    cf_report_date = available_dates_in_cf[0].strftime('%Y-%m-%d')
                    extracted_cf_items = data_handler.extract_finmind_items(df_cf, cf_items_map, report_date_str=cf_report_date, max_lookback_periods=2)
                    # 若主欄位皆為 None，則自動回退一期
                    if all(extracted_cf_items.get(k) is None for k in ['capex', 'depreciation', 'amortization']) and len(available_dates_in_cf) > 1:
                        cf_report_date = available_dates_in_cf[1].strftime('%Y-%m-%d')
                        extracted_cf_items = data_handler.extract_finmind_items(df_cf, cf_items_map, report_date_str=cf_report_date, max_lookback_periods=2)
            if extracted_cf_items:
                financial_data_for_stock.update(extracted_cf_items)
                financial_data_for_stock['cf_report_date'] = extracted_cf_items.get('report_date')
            else:
                financial_data_for_stock['error'].append("無法獲取現金流量表")

            # Fetch Income Statement (IS) - FinancialStatements in FinMind
            df_is = data_handler.fetch_finmind_financial_statement_data(stock_code, start_date_finmind, 'FinancialStatements')
            is_items_map = {'net_income_parent': 'EquityAttributableToOwnersOfParent', 'eps_finmind': 'EPS'}
            available_dates_in_is = sorted(pd.to_datetime(df_is['date'].unique()), reverse=True) if not df_is.empty else []
            is_report_date = financial_data_for_stock.get('bs_report_date_t0')
            extracted_is_items = {}
            if available_dates_in_is:
                # 先嘗試與資產負債表同日期
                if is_report_date and pd.to_datetime(is_report_date) in available_dates_in_is:
                    extracted_is_items = data_handler.extract_finmind_items(df_is, is_items_map, report_date_str=is_report_date, max_lookback_periods=2)
                else:
                    # 若沒有，則用最新一期
                    is_report_date = available_dates_in_is[0].strftime('%Y-%m-%d')
                    extracted_is_items = data_handler.extract_finmind_items(df_is, is_items_map, report_date_str=is_report_date, max_lookback_periods=2)
                    # 若主欄位皆為 None，則自動回退一期
                    if all(extracted_is_items.get(k) is None for k in ['net_income_parent', 'eps_finmind']) and len(available_dates_in_is) > 1:
                        is_report_date = available_dates_in_is[1].strftime('%Y-%m-%d')
                        extracted_is_items = data_handler.extract_finmind_items(df_is, is_items_map, report_date_str=is_report_date, max_lookback_periods=2)
            if extracted_is_items:
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

            # --- shares_outstanding 自動補全 ---
            if not financial_data_for_stock.get("shares_outstanding"):
                # 1. 先從 stock_detail 補
                so = stock_detail.get("shares_outstanding")
                if so:
                    financial_data_for_stock["shares_outstanding"] = so
                else:
                    # 2. 嘗試對齊財報期末自動下載/解析證交所股本異動表
                    try:
                        import data_fetching
                        # 優先用資產負債表 T0 日期
                        report_date = financial_data_for_stock.get('bs_report_date_t0') or \
                                      financial_data_for_stock.get('is_report_date') or \
                                      financial_data_for_stock.get('cf_report_date')
                        so_csv = None
                        if report_date:
                            so_csv = data_fetching.get_shares_outstanding_from_twse_csv(stock_code, report_date)
                        if so_csv:
                            financial_data_for_stock["shares_outstanding"] = so_csv
                        else:
                            # 3. 再從 all_companies_openapi_data 補
                            all_companies = self.context.get("all_companies_openapi_data", [])
                            so_found = None
                            for comp in all_companies:
                                if str(comp.get("公司代號")) == str(stock_code):
                                    so_str = comp.get("已發行普通股數或TDR原股發行股數")
                                    try:
                                        so_found = float(str(so_str).replace(",", ""))
                                    except Exception:
                                        so_found = None
                                    break
                            if so_found:
                                financial_data_for_stock["shares_outstanding"] = so_found
                    except Exception as e:
                        print(f"[jojo_state_machine] shares_outstanding 多來源補全失敗: {e}")

            # Consolidate errors
            if financial_data_for_stock['error']:
                financial_data_for_stock['error'] = "; ".join(financial_data_for_stock['error'])
            else:
                del financial_data_for_stock['error'] # Remove if no errors

            all_financial_data_for_stock[stock_code] = financial_data_for_stock
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
        threshold = self.context.get('potential_return_threshold')
        if threshold is None:
            threshold = 0.15 # Default 15%
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
                # 直接排除EPS為負或過低的股票
                if source_eps is None or source_eps < min_eps:
                    print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 近期會計EPS ({source_eps}) 為負或過低，已排除。")
                    continue
                filtered_results.append(res)
            else:
                # 即使EPS為正，如果潛在回報不足，也不選入
                print(f"  (FilteringState) 股票 {res.get('stock_code')} ({res.get('name', '')}) 因潛在報酬 ({potential_return:.1%}) 未達標 (> {threshold*100:.1f}%) 而未被選入 (內在價值: {intrinsic_value:.2f}, 會計EPS: {source_eps}).")

        self.context['filtered_results'] = filtered_results
        print(f"FilteringState 完成，共篩選出 {len(filtered_results)} 筆符合條件的股票。")
        self.machine.transition_to(JoJoState.RESULTS_DISPLAY)
        print("FilteringState 完成。")


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
        # It could also trigger periodic updates or checks
        # For now, it just transitions to CONFIG_LOAD to demonstrate a cycle
        self.machine.transition_to(JoJoState.CONFIG_LOAD)
        print("IdleState 完成。")
