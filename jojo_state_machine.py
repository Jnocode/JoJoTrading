from enum import Enum, auto
import json
import os
from dotenv import load_dotenv
import requests 
import pandas as pd # 新增 Pandas 導入
import data_handler # 確保 data_handler 模組被正確引用
from data_handler import (
    get_all_companies_basic_data, # TWSE
    filter_industry_stocks,       # TWSE
    # get_financial_reports_for_stock, # TWSE - 替換為 FinMind
    # fetch_stock_financials_from_downloaded, # TWSE - 替換為 FinMind
    # get_balance_sheet_data_for_stock, # TWSE - 替換為 FinMind
    # fetch_balance_sheet_items_from_downloaded, # TWSE - 替換為 FinMind
    fetch_finmind_financial_statement_data, # FinMind - 新增
    extract_finmind_items,                 # FinMind - 新增
    _fetch_stock_financials_simulated, 
    calculate_dcf_valuation
)

# FinMind 目標會計科目映射 (根據 test_finmind_api.py 輸出確認)
FINMIND_BALANCE_SHEET_MAP_T0 = {
    'ar_t0': 'AccountsReceivableNet',  # 應收帳款淨額
    'inv_t0': 'Inventories',           # 存貨
    'ap_t0': 'AccountsPayable'         # 應付帳款
}
FINMIND_BALANCE_SHEET_MAP_T1 = { # 用於獲取前一期數據
    'ar_t1': 'AccountsReceivableNet',
    'inv_t1': 'Inventories',
    'ap_t1': 'AccountsPayable'
}
FINMIND_CASH_FLOW_MAP = {
    # 資本支出：'PropertyAndPlantAndEquipment' (取得不動產、廠房及設備) - FinMind中此值通常為負(現金流出)
    # 在FCFE公式中 Capex 通常是正的支出值，所以使用時可能需要取相反數。
    'capex': 'PropertyAndPlantAndEquipment', 
    'depreciation': 'Depreciation',          # 折舊費用
    'amortization': 'AmortizationExpense'    # 攤銷費用
    # 淨舉債 (NetBorrowing) 初期先忽略，設為0
}
FINMIND_INCOME_STATEMENT_MAP = {
    # 歸母淨利: 'EquityAttributableToOwnersOfParent' (淨利（淨損）歸屬於母公司業主)
    # 另一個可能是 'IncomeFromContinuingOperations' (繼續營業單位本期淨利（淨損）)
    # 我們先用 EquityAttributableToOwnersOfParent，因為它更明確是"歸母"
    'net_income_parent': 'EquityAttributableToOwnersOfParent', 
    'revenue': 'Revenue',                    # 營業收入
    'eps_finmind': 'EPS'                     # 基本每股盈餘（元）
}

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
    END = auto()

class BaseState:
    def execute(self, context):
        raise NotImplementedError("每個狀態都必須實現 execute 方法")

    def on_enter(self, context):
        print(f"Entering state: {self.__class__.__name__}")

    def on_exit(self, context):
        pass

class ConfigLoadState(BaseState):
    def execute(self, context):
        print("Executing ConfigLoadState: 載入設定檔...")
        try:
            load_dotenv()
            
            config_file_path = 'industries.json'
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
                industries_data = app_config.get('industries', [])
                context['industries_full_data'] = industries_data 
                context['industry_names'] = [item.get('name') for item in industries_data if item.get('name')] 
                context['industry_name_to_code_map'] = {item.get('name'): item.get('code') for item in industries_data if item.get('name') and item.get('code')}
                context['default_risk_premium'] = app_config.get('default_risk_premium', 0.04)
                context['risk_premium_options'] = app_config.get('risk_premium_options', {})
                context['simulated_data'] = app_config.get('simulated_data', {})
                print(f"  {config_file_path} 已載入。偵測到產業數量: {len(context['industry_names'])}")
            else:
                print(f"  錯誤: {config_file_path} 找不到。將使用預設空值。")
                context['industries_full_data'] = []
                context['industry_names'] = []
                context['industry_name_to_code_map'] = {}
                context['default_risk_premium'] = 0.04
                context['risk_premium_options'] = {}
                context['simulated_data'] = {} 

            context['config_loaded'] = True
            print("ConfigLoadState 完成。")
            return JoJoState.UI_INIT
        except Exception as e:
            print(f"ConfigLoadState 執行時發生錯誤: {e}")
            context['error_message'] = f"設定檔載入失敗: {e}"
            context['config_loaded'] = False
            return JoJoState.ERROR

class UiInitState(BaseState):
    def execute(self, context):
        print("Executing UiInitState: 初始化 Streamlit UI...")
        if 'selected_industry_name' not in context and context.get('industry_names'):
            context['selected_industry_name'] = context['industry_names'][0] 
        if 'risk_preference' not in context:
            context['risk_preference'] = context.get('default_risk_premium', 0.04)
        if 'developer_mode' not in context: 
            context['developer_mode'] = False
            print("  (UiInitState) developer_mode 未在 context 中找到，預設為 False。")

        if context.get('developer_mode', False):
            print("  (UiInitState) 開發者模式已啟用。")
        
        if context.get('user_clicked_filter_button'): 
            return JoJoState.INDUSTRY_PROCESS
        return JoJoState.UI_INIT

class IndustryProcessState(BaseState):
    def execute(self, context):
        print(f"Executing IndustryProcessState: 處理產業 '{context.get('selected_industry_name', '未指定')}'...")
        return JoJoState.DATA_FETCH

class DataFetchState(BaseState):
    def _get_stock_prices(self, context):
        if 'all_stock_day_prices' not in context:
            print("  (DataFetchState) 正在獲取所有上市公司每日股價資料...")
            stock_price_url = f"{data_handler.API_BASE_URL}/exchangeReport/STOCK_DAY_ALL" 
            try:
                print("    (DataFetchState) 警告：將嘗試禁用 SSL 憑證驗證 (verify=False) 來獲取股價。")
                response = requests.get(stock_price_url, timeout=30, verify=False)
                response.raise_for_status()
                context['all_stock_day_prices'] = response.json()
                print(f"    (DataFetchState) 成功獲取 {len(context['all_stock_day_prices'])} 筆股價記錄。")
            except requests.exceptions.RequestException as e_price:
                print(f"    (DataFetchState) 獲取股價資料時發生錯誤: {e_price}")
                context['all_stock_day_prices'] = []
            except json.JSONDecodeError as e_json_price:
                print(f"    (DataFetchState) 解析股價資料 JSON 時發生錯誤: {e_json_price}")
                context['all_stock_day_prices'] = []
        return context.get('all_stock_day_prices', [])

    def execute(self, context):
        print("Executing DataFetchState: 抓取資料...")
        
        all_companies_data = get_all_companies_basic_data(context) 
        if not all_companies_data:
            context['error_message'] = "無法獲取上市公司基本資料。"
            return JoJoState.ERROR

        if context.get('developer_mode', False):
            print("  (DataFetchState) 開發者模式啟用，使用模擬數據。")
            sim_data = context.get('simulated_data', {})
            ui_selected_industry = context.get('selected_industry_name')
            sim_selected_industry = sim_data.get('selected_industry_name', "模擬產業")
            context['selected_industry_name'] = ui_selected_industry if ui_selected_industry and ui_selected_industry != "N/A" else sim_selected_industry
            
            sim_industry_stocks_details_template = sim_data.get('industry_stocks_details', [])
            sim_financial_data_template = sim_data.get('financial_data', {})
            
            temp_sim_industry_stocks_details = []
            for stock_detail_sim_template in sim_industry_stocks_details_template:
                stock_detail_sim = stock_detail_sim_template.copy()
                stock_code_sim = stock_detail_sim['code']
                
                company_basic_info_sim = next((comp for comp in all_companies_data if comp.get("公司代號") == stock_code_sim), None)
                if company_basic_info_sim:
                    shares_outstanding_sim_str = company_basic_info_sim.get("已發行普通股數或TDR原股發行股數", "0")
                    try:
                        stock_detail_sim["shares_outstanding"] = float(str(shares_outstanding_sim_str).replace(",", ""))
                    except ValueError:
                        stock_detail_sim["shares_outstanding"] = 0.0
                else:
                    stock_detail_sim["shares_outstanding"] = 0.0 
                
                stock_sim_financials = sim_financial_data_template.get(stock_code_sim, {})
                stock_detail_sim["current_market_price"] = stock_sim_financials.get("sim_price", 100.0) 
                temp_sim_industry_stocks_details.append(stock_detail_sim)
            
            context['industry_stocks_details_list'] = temp_sim_industry_stocks_details
            context['industry_stocks_list'] = [f"{s['code']} {s['name']}" for s in temp_sim_industry_stocks_details]
            
            final_sim_financial_data = {}
            for stock_detail_final_sim in temp_sim_industry_stocks_details:
                code = stock_detail_final_sim['code']
                financials_entry = sim_financial_data_template.get(code, {}).copy()
                financials_entry["shares_outstanding"] = stock_detail_final_sim.get("shares_outstanding", 0.0)
                financials_entry["current_market_price"] = stock_detail_final_sim.get("current_market_price", 100.0)
                financials_entry["stock_code"] = code
                financials_entry["stock_name"] = stock_detail_final_sim.get("name", "N/A")
                final_sim_financial_data[code] = financials_entry

            context['financial_data'] = final_sim_financial_data
            context['raw_data_fetched'] = True
            print(f"  模擬數據已準備 for industry '{context['selected_industry_name']}': {len(context['industry_stocks_details_list'])} 支股票, {len(context['financial_data'])} 筆財務資料。")
            return JoJoState.VALUATION

        selected_industry_name = context.get('selected_industry_name')
        industry_name_to_code_map = context.get('industry_name_to_code_map', {})

        if not selected_industry_name:
            context['error_message'] = "未選擇產業"
            return JoJoState.ERROR
        try:
            all_stock_prices = self._get_stock_prices(context) 

            print(f"  開始為產業 '{selected_industry_name}' 處理資料...")
            industry_stocks_details = filter_industry_stocks(selected_industry_name, industry_name_to_code_map, all_companies_data)
            context['industry_stocks_details_list'] = industry_stocks_details
            context['industry_stocks_list'] = [f"{s['code']} {s['name']}" for s in industry_stocks_details]
            print(f"  篩選後成分股詳細列表 ({selected_industry_name}):")
            for stock_detail_debug in industry_stocks_details[:3]: 
                print(f"    {stock_detail_debug}")
            
            all_financial_data = {}
            processed_api_suffixes = set() 

            for stock_detail in industry_stocks_details: 
                stock_code = stock_detail['code']
                print(f"  準備為 {stock_code} ({stock_detail['name']}) 從 FinMind 提取財報數據...")
                financials = {
                    "stock_code": stock_code,
                    "stock_name": stock_detail.get("name", "N/A"),
                    "shares_outstanding": stock_detail.get("shares_outstanding", 0.0),
                    "error": None 
                }

                # 獲取財報的起始日期，例如過去三年
                # FinMind 的 date 參數通常指財報發布日或期末日，它會返回該日期點可得的最新數據
                # 我們需要至少兩期資產負債表來計算變動。
                # 假設我們需要 2023-Q4 和 2023-Q3 (或 2022-Q4)
                # FinMind 的 start_date 參數會獲取該日期之後的所有數據，我們再從中挑選
                report_start_date = context.get("finmind_report_start_date", "2022-01-01") # 可在UI設定

                # 1. 獲取資產負債表 (BalanceSheet)
                bs_df = fetch_finmind_financial_statement_data(stock_code, report_start_date, 'BalanceSheet')
                if not bs_df.empty:
                    # 提取最新一期 (T0)
                    bs_items_t0 = extract_finmind_items(bs_df, FINMIND_BALANCE_SHEET_MAP_T0) # 預設取最新
                    financials.update(bs_items_t0)
                    financials['bs_report_date_t0'] = bs_items_t0.get('report_date')

                    # 嘗試提取前一期 (T-1)
                    # 這需要找到 T0 日期之前的一個唯一報表日期
                    if bs_items_t0.get('report_date'):
                        t0_date = pd.to_datetime(bs_items_t0['report_date'])
                        # 獲取所有唯一日期並排序
                        unique_dates_bs = sorted(bs_df['date'].unique(), reverse=True)
                        t0_date_np = pd.Timestamp(t0_date).to_datetime64() # 轉換為 numpy.datetime64
                        
                        if t0_date_np in unique_dates_bs:
                            t0_index = unique_dates_bs.index(t0_date_np)
                            if t0_index + 1 < len(unique_dates_bs):
                                t1_date_np = unique_dates_bs[t0_index + 1]
                                t1_date_str = pd.Timestamp(t1_date_np).strftime('%Y-%m-%d')
                                bs_items_t1 = extract_finmind_items(bs_df, FINMIND_BALANCE_SHEET_MAP_T1, report_date_str=t1_date_str)
                                financials.update(bs_items_t1)
                                financials['bs_report_date_t1'] = bs_items_t1.get('report_date')
                                print(f"    (DataFetchState) 股票 {stock_code} 資產負債表 T0: {financials.get('bs_report_date_t0')}, T-1: {financials.get('bs_report_date_t1')}")
                            else:
                                print(f"    (DataFetchState) 警告：股票 {stock_code} 資產負債表只找到一期數據，無法獲取 T-1 期。")
                        else:
                             print(f"    (DataFetchState) 警告：股票 {stock_code} 最新資產負債表日期 {t0_date_np} 未在唯一日期列表中找到。")
                else:
                    financials["error"] = financials.get("error","") + "無法獲取資產負債表; "
                    print(f"    (DataFetchState) 警告：股票 {stock_code} 未能獲取資產負債表數據。")

                # 2. 獲取現金流量表 (CashFlowsStatement)
                cf_df = fetch_finmind_financial_statement_data(stock_code, report_start_date, 'CashFlowsStatement')
                if not cf_df.empty:
                    cf_items = extract_finmind_items(cf_df, FINMIND_CASH_FLOW_MAP) # 預設取最新
                    financials.update(cf_items)
                    financials['cf_report_date'] = cf_items.get('report_date')
                else:
                    financials["error"] = financials.get("error","") + "無法獲取現金流量表; "
                    print(f"    (DataFetchState) 警告：股票 {stock_code} 未能獲取現金流量表數據。")

                # 3. 獲取綜合損益表 (FinancialStatements)
                is_df = fetch_finmind_financial_statement_data(stock_code, report_start_date, 'FinancialStatements')
                if not is_df.empty:
                    is_items = extract_finmind_items(is_df, FINMIND_INCOME_STATEMENT_MAP) # 預設取最新
                    financials.update(is_items)
                    financials['is_report_date'] = is_items.get('report_date')
                    # 使用 FinMind 的 EPS (通常是年化或季度，需確認 FinMind 如何提供)
                    # TWSE API 的 EPS 是單季，若 FinMind 是年化，則需調整或統一
                    # 暫時先用 FinMind 的 EPS，並在估值時注意其基礎
                    financials['eps'] = financials.get('eps_finmind') # 覆蓋掉可能來自舊 TWSE API 的 eps
                else:
                    financials["error"] = financials.get("error","") + "無法獲取損益表; "
                    print(f"    (DataFetchState) 警告：股票 {stock_code} 未能獲取綜合損益表數據。")
                
                # 移除 financials["error"] 開頭的 None
                if financials.get("error") and financials["error"].startswith("None"):
                    financials["error"] = financials["error"][4:].strip()
                if financials.get("error") and financials["error"].strip() == "":
                    financials["error"] = None


                stock_price_info = next((price_data for price_data in all_stock_prices if price_data.get("Code") == stock_code), None)
                if stock_price_info and stock_price_info.get("ClosingPrice"):
                    try:
                        closing_price_str = str(stock_price_info.get("ClosingPrice")).replace(",","")
                        if closing_price_str and closing_price_str != "---" and closing_price_str.lower() != "nan":
                            financials["current_market_price"] = float(closing_price_str)
                        else:
                            financials["current_market_price"] = None
                            print(f"  (DataFetchState) 警告：股票 {stock_code} 的收盤價為無效字串 '{stock_price_info.get('ClosingPrice')}'。")
                    except ValueError:
                        print(f"  (DataFetchState) 警告：股票 {stock_code} 的收盤價 '{stock_price_info.get('ClosingPrice')}' 無法轉換為數字。")
                        financials["current_market_price"] = None
                else:
                    print(f"  (DataFetchState) 警告：未找到股票 {stock_code} 的股價資訊。")
                    financials["current_market_price"] = None
                
                all_financial_data[stock_code] = financials
            
            context['financial_data'] = all_financial_data
            context['raw_data_fetched'] = True
            
            if industry_stocks_details:
                 print("  已嘗試為所有成分股提取財務數據和股價。")
            else:
                print("  無成分股可供提取財務數據和股價。")
            return JoJoState.VALUATION
        except Exception as e:
            print(f"DataFetchState 執行時發生錯誤: {e}")
            context['error_message'] = f"資料抓取失敗: {e}"
            return JoJoState.ERROR

class ValuationState(BaseState):
    def execute(self, context):
        print("Executing ValuationState: 進行 DCF 估值...")
        financial_data_map = context.get('financial_data', {})
        risk_preference = context.get('risk_preference', 0.04) 
        
        valuation_results = []
        if not financial_data_map:
            print("  (ValuationState) 警告: financial_data 為空，無法進行估值。")
        
        for stock_code, financials in financial_data_map.items():
            stock_name = financials.get("stock_name", stock_code) 

            print(f"  (ValuationState) 正在為股票 {stock_code} ({stock_name}) 進行估值...")
            if financials and not financials.get("error"):
                if "shares_outstanding" not in financials: 
                    print(f"  (ValuationState) 警告: 股票 {stock_code} 的 financials 字典中缺少 'shares_outstanding'。跳過估值。")
                    financials["error"] = "缺少流通股數資料" 
                
                if not financials.get("error"): 
                    valuation_result = calculate_dcf_valuation(stock_code, financials, risk_preference, context)
                    valuation_result['stock_name'] = stock_name 
                    valuation_results.append(valuation_result)
                else: 
                    print(f"  (ValuationState) 股票 {stock_code} ({stock_name}) 因資料問題無法估值: {financials.get('error')}")
                    valuation_results.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "error": financials.get("error", "財務數據不足或錯誤，無法估值")
                    })
            else: 
                print(f"  (ValuationState) 股票 {stock_code} ({stock_name}) 缺少有效的財務數據，跳過估值。錯誤: {financials.get('error', '未知數據問題')}")
                valuation_results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "error": financials.get("error", "財務數據不足或錯誤，無法估值")
                })
        
        context['valuation_results'] = valuation_results
        context['valuation_completed'] = True
        print(f"ValuationState 完成，共處理 {len(valuation_results)} 筆估值結果。")
        return JoJoState.FILTERING

class FilteringState(BaseState):
    def execute(self, context):
        print("Executing FilteringState: 篩選估值後的股票...")
        valuation_results = context.get('valuation_results', [])
        min_potential_return_threshold = context.get('min_potential_return_filter', 0.20) # 從 context 獲取，預設 0.20
        
        filtered_stocks = []
        if not valuation_results:
            print("  (FilteringState) 警告: valuation_results 為空，無法進行篩選。")
        else:
            print(f"  (FilteringState) 收到 {len(valuation_results)} 筆估值結果準備篩選。篩選潛在報酬 > {min_potential_return_threshold*100:.1f}%")
            for result in valuation_results:
                if result and not result.get("error"):
                    intrinsic_value = result.get("intrinsic_value_per_share") 
                    eps_to_check = result.get("source_eps") 
                    potential_return = result.get("potential_return")
                    current_market_price = result.get("current_market_price")
                    
                    valid_intrinsic = isinstance(intrinsic_value, (int, float))
                    valid_eps_to_check = isinstance(eps_to_check, (int, float))
                    
                    # 潛在報酬率檢查邏輯
                    passes_potential_return_check = False # 預設不通過，除非明確滿足條件
                    if current_market_price is None or not isinstance(current_market_price, (int, float)) or current_market_price <= 0:
                        # 如果沒有市價或市價無效，則無法計算潛在報酬，視為不滿足此篩選條件
                        print(f"  (FilteringState) 股票 {result.get('stock_code')} ({result.get('stock_name')}) 因缺少有效市價，無法進行潛在報酬率篩選。")
                    elif isinstance(potential_return, (int, float)):
                        if potential_return > min_potential_return_threshold:
                            passes_potential_return_check = True
                    
                    if valid_intrinsic and valid_eps_to_check and intrinsic_value > 0 and eps_to_check > 0 and passes_potential_return_check:
                        filtered_stocks.append({
                            "股票代號": result.get("stock_code"),
                            "股票名稱": result.get("stock_name", "N/A"), 
                            "內在價值": result.get("intrinsic_value_per_share"),
                            "目前市價": result.get("current_market_price", "N/A"), 
                            "潛在報酬": f"{potential_return*100:.1f}%" if isinstance(potential_return, (int, float)) else "N/A",
                            "EPS (來源)": result.get("source_eps"),
                            "FCFEps (計算)": result.get("calculated_fcf_eps"),
                            "估值年度/季度": result.get("data_year_quarter"),
                            "使用折現率": f"{result.get('used_discount_rate', 0)*100:.1f}%"
                        })
                    else:
                        reason = []
                        if not (valid_intrinsic and intrinsic_value > 0): reason.append(f"內在價值 ({intrinsic_value})")
                        if not (valid_eps_to_check and eps_to_check > 0): reason.append(f"EPS ({eps_to_check})")
                        if not passes_potential_return_check: reason.append(f"潛在報酬 ({potential_return if isinstance(potential_return, (int, float)) else 'N/A'}) 未達標 (> {min_potential_return_threshold*100:.1f}%)")
                        print(f"  (FilteringState) 股票 {result.get('stock_code')} ({result.get('stock_name')}) 因 {', '.join(reason)} 不符條件而未被選入。")
                else:
                    print(f"  (FilteringState) 股票 {result.get('stock_code')} ({result.get('stock_name')}) 存在估值錯誤，已跳過: {result.get('error')}")
            
            print(f"  (FilteringState) 篩選完成，選出 {len(filtered_stocks)} 支股票。")

        context['filtered_stocks'] = filtered_stocks
        return JoJoState.RESULTS_DISPLAY

class ResultsDisplayState(BaseState):
    def execute(self, context):
        print(f"Executing ResultsDisplayState: 顯示結果 {context.get('filtered_stocks')}...")
        if context.get('user_clicked_export_button'):
            return JoJoState.EXPORT
        elif context.get('user_clicked_new_query_button'):
            return JoJoState.UI_INIT
        return JoJoState.RESULTS_DISPLAY

class ExportState(BaseState):
    def execute(self, context):
        print("Executing ExportState: 匯出結果...")
        context['export_completed'] = True
        return JoJoState.RESULTS_DISPLAY 

class ErrorState(BaseState):
    def execute(self, context):
        error_msg = context.get('error_message', "發生未知錯誤")
        print(f"Executing ErrorState: {error_msg}")
        return JoJoState.UI_INIT

class EndState(BaseState):
    def execute(self, context):
        print("Executing EndState: 流程結束。")
        return JoJoState.END

class JoJoStateMachine:
    def __init__(self):
        self.current_jojo_state_enum = JoJoState.CONFIG_LOAD
        self.context = {} 
        self.states = {
            JoJoState.CONFIG_LOAD: ConfigLoadState(),
            JoJoState.UI_INIT: UiInitState(),
            JoJoState.INDUSTRY_PROCESS: IndustryProcessState(),
            JoJoState.DATA_FETCH: DataFetchState(),
            JoJoState.VALUATION: ValuationState(),
            JoJoState.FILTERING: FilteringState(),
            JoJoState.RESULTS_DISPLAY: ResultsDisplayState(),
            JoJoState.EXPORT: ExportState(),
            JoJoState.ERROR: ErrorState(),
            JoJoState.END: EndState()
        }
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5

    def run(self):
        while self.current_jojo_state_enum != JoJoState.END:
            current_state_obj = self.states.get(self.current_jojo_state_enum)
            if not current_state_obj:
                print(f"錯誤：找不到狀態 {self.current_jojo_state_enum} 的對應物件。")
                self.context['error_message'] = f"無效狀態: {self.current_jojo_state_enum}"
                self.current_jojo_state_enum = JoJoState.ERROR
                continue
            try:
                current_state_obj.on_enter(self.context)
                next_state_enum = current_state_obj.execute(self.context)
                current_state_obj.on_exit(self.context)
                
                if next_state_enum == self.current_jojo_state_enum and next_state_enum not in [JoJoState.UI_INIT, JoJoState.RESULTS_DISPLAY]:
                    print(f"警告：狀態 {self.current_jojo_state_enum} 執行後未改變，可能導致死循環。")
                    self.consecutive_failures +=1
                else:
                    self.consecutive_failures = 0
                self.current_jojo_state_enum = next_state_enum
            except Exception as e:
                print(f"狀態 {self.current_jojo_state_enum} 執行時發生錯誤: {e}")
                self.context['error_message'] = str(e)
                self.current_jojo_state_enum = JoJoState.ERROR
                self.consecutive_failures += 1
            
            if self.consecutive_failures >= self.max_consecutive_failures:
                print(f"連續 {self.max_consecutive_failures} 次失敗，狀態機停止。")
                self.current_jojo_state_enum = JoJoState.END
        
        final_state_obj = self.states.get(JoJoState.END)
        if final_state_obj:
            final_state_obj.on_enter(self.context)
            final_state_obj.execute(self.context)
        print("JoJoTrading State Machine 已停止。")

if __name__ == "__main__":
    print("開始 JoJoStateMachine 簡易測試...")
    machine = JoJoStateMachine()
    
    machine.context['user_clicked_filter_button'] = False
    machine.context['user_clicked_export_button'] = False
    machine.context['user_clicked_new_query_button'] = False
    machine.context['developer_mode'] = False 

    # --- 模擬完整流程 ---
    # 1. Config Load
    machine.current_jojo_state_enum = machine.states[JoJoState.CONFIG_LOAD].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")
    
    if machine.context.get('developer_mode'):
        sim_data = machine.context.get('simulated_data', {})
        machine.context['selected_industry_name'] = sim_data.get('selected_industry_name', "模擬-電子零組件")
        machine.context['risk_preference'] = machine.context.get('default_risk_premium', 0.04)
        print(f"  開發者模式：使用模擬產業 '{machine.context['selected_industry_name']}'")
    else: 
        machine.context['selected_industry_name'] = machine.context['industry_names'][24] # 電子零組件業
        machine.context['risk_preference'] = 0.05 
        print(f"  模擬UI選擇：產業 '{machine.context['selected_industry_name']}', 風險偏好 {machine.context['risk_preference']}")

    # 2. UI Init (假設使用者點擊了篩選) -> IndustryProcess
    machine.context['user_clicked_filter_button'] = True
    machine.current_jojo_state_enum = machine.states[JoJoState.UI_INIT].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")
    machine.context['user_clicked_filter_button'] = False 

    # 3. Industry Process -> Data Fetch
    machine.current_jojo_state_enum = machine.states[JoJoState.INDUSTRY_PROCESS].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")

    # 4. Data Fetch -> Valuation
    machine.current_jojo_state_enum = machine.states[JoJoState.DATA_FETCH].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")

    # 5. Valuation -> Filtering
    machine.current_jojo_state_enum = machine.states[JoJoState.VALUATION].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")

    # 6. Filtering -> Results Display
    machine.current_jojo_state_enum = machine.states[JoJoState.FILTERING].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")
    print(f"  篩選結果 (共 {len(machine.context.get('filtered_stocks', []))} 筆):")
    for stock_info in machine.context.get('filtered_stocks', [])[:5]: # 最多顯示5筆
        print(f"    {stock_info}")
    
    # 7. Results Display (假設使用者點擊匯出) -> Export
    machine.context['user_clicked_export_button'] = True
    machine.current_jojo_state_enum = machine.states[JoJoState.RESULTS_DISPLAY].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")
    machine.context['user_clicked_export_button'] = False

    # 8. Export -> Results Display
    machine.current_jojo_state_enum = machine.states[JoJoState.EXPORT].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")

    # 9. Results Display (假設使用者點擊新查詢) -> UI_INIT
    machine.context['user_clicked_new_query_button'] = True
    machine.current_jojo_state_enum = machine.states[JoJoState.RESULTS_DISPLAY].execute(machine.context)
    print(f"  -> 測試轉換到狀態: {machine.current_jojo_state_enum}")
    machine.context['user_clicked_new_query_button'] = False 

    print("JoJoStateMachine 簡易測試結束。")
