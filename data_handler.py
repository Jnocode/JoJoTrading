"""
JoJotrading 資料處理核心模組

此模組負責台股篩選系統的所有資料獲取、處理和整合功能，
結合多個資料來源提供完整的股票財務資訊和估值計算支援。

主要資料來源：
- FinMind API: 財務報表、每日股價、基本面數據
- 台灣證券交易所 OpenAPI: 上市公司基本資料、即時股價
- 本地快取系統: 優化 API 呼叫效率

核心功能：
1. 財務資料獲取與快取管理
   - get_financial_data_cached(): 取得快取財務數據
   - fetch_and_cache_financial_data(): 獲取並快取 FinMind 數據
   - get_all_companies_basic_data(): 獲取上市公司基本資料

2. 產業分類與股票篩選
   - filter_industry_stocks(): 根據產業代碼篩選股票
   - 支援個股直查模式與產業群組篩選

3. DCF 估值計算
   - calculate_dcf_valuation(): 現金流量折現估值模型
   - 支援自由現金流與盈餘現金流兩種模式
   - 包含一次性收益異常檢測功能

4. 資料清洗與驗證
   - 財務數據完整性檢查
   - 異常值檢測與處理
   - 多年期財務趨勢分析

快取機制：
- 24小時快取期限，減少 API 重複呼叫
- 自動建立與管理 cache/finmind_data 目錄
- 支援快取失效與強制更新

環境變數配置：
- FINMIND_API_TOKEN: FinMind API 認證令牌
- FINMIND_USER_ID: FinMind 用戶 ID
- FINMIND_PASSWORD: FinMind 密碼

使用範例：
    # 獲取財務數據
    financial_data = get_financial_data_cached(stock_code="2330", dataset="TaiwanStockFinancialStatements")
    
    # 計算 DCF 估值
    valuation = calculate_dcf_valuation(
        stock_code="2330",
        financial_data=financial_data,
        risk_free_rate=0.01,
        risk_premium=0.06
    )
    
    # 產業股票篩選
    stocks = filter_industry_stocks("半導體業", industry_code_map, all_companies_data)

注意事項：
- 需要有效的 FinMind API 憑證才能存取完整數據
- 建議設定適當的 API 呼叫間隔以避免限制
- DCF 模型假設適用於穩定成長的企業
"""

import json
import os
import requests
from dotenv import load_dotenv
import pandas as pd
from FinMind.data import DataLoader
import time # For cache freshness
from pathlib import Path # For creating cache directory

# Import new modules for Phase 1 optimization
from modules.data_validator import FinancialDataValidator
from modules.enhanced_dcf import EnhancedDCFModel
from modules.integrated_dcf_handler import calculate_enhanced_dcf_valuation

load_dotenv()

# Get the directory of the current script
SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_DIR = SCRIPT_DIR / "cache" / "finmind_data"
CACHE_EXPIRY_SECONDS = 24 * 60 * 60 # 24 hours

# FinMind API 憑證 (Token 或 UserID/Password)
FINMIND_API_TOKEN = os.getenv("FINMIND_API_TOKEN", "")
FINMIND_USER_ID = os.getenv("FINMIND_USER_ID", "")
FINMIND_PASSWORD = os.getenv("FINMIND_PASSWORD", "")

# Create cache directory if it doesn't exist
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  (data_handler) Cache directory ensured at: {CACHE_DIR}")
except Exception as e_mkdir:
    print(f"  (data_handler) ERROR: Could not create cache directory at {CACHE_DIR}: {e_mkdir}")

# Initialize new modules for Phase 1 optimization
financial_validator = FinancialDataValidator()
enhanced_dcf_model = EnhancedDCFModel()
print("  (data_handler) Initialized financial data validator and enhanced DCF model")

# DCF calculation method selector
USE_ENHANCED_DCF = True  # Set to False to use original DCF implementation

finmind_api = DataLoader() 
login_method_used = "anonymous_default"

try:
    if FINMIND_USER_ID and FINMIND_PASSWORD:
        print("  (data_handler) Attempting FinMind login with User ID and Password...")
        try:
            finmind_api.login(user_id=FINMIND_USER_ID, password=FINMIND_PASSWORD)
            print("  (data_handler) FinMind API login successful with User ID and Password.")
            login_method_used = "user_pass"
        except Exception as e_user_pass:
            print(f"  (data_handler) FinMind API login with User ID and Password failed: {e_user_pass}.")
            if FINMIND_API_TOKEN:
                print("  (data_handler) Attempting FinMind login with API Token as fallback...")
                try:
                    finmind_api = DataLoader(token=FINMIND_API_TOKEN) 
                    print("  (data_handler) FinMind DataLoader re-initialized with token (after user/pass fail).")
                    login_method_used = "token_after_user_pass_fail"
                except Exception as e_token_init_fallback:
                    print(f"  (data_handler) FinMind DataLoader initialization with token (fallback) also failed: {e_token_init_fallback}. Using anonymous access.")
                    finmind_api = DataLoader() 
                    login_method_used = "anonymous_after_all_fails"
            else:
                print("  (data_handler) No API Token available as fallback. Using anonymous access.")
                finmind_api = DataLoader() 
                login_method_used = "anonymous_after_user_pass_fail_no_token"

    elif FINMIND_API_TOKEN: 
        print("  (data_handler) Attempting FinMind login with API Token (no User ID/Password provided)...")
        try:
            finmind_api = DataLoader(token=FINMIND_API_TOKEN)
            print("  (data_handler) FinMind DataLoader initialized with token.")
            login_method_used = "token_only"
        except Exception as e_token_init_only:
            print(f"  (data_handler) FinMind DataLoader initialization with token failed: {e_token_init_only}. Using anonymous access.")
            finmind_api = DataLoader() 
            login_method_used = "anonymous_after_token_fail"
    else:
        print("  (data_handler) No FinMind credentials (.env: TOKEN, USER_ID, PASSWORD) found. Using anonymous access (300 requests/hr limit).")
        login_method_used = "anonymous_no_creds"

except Exception as e_init_critical:
    print(f"  (data_handler) Critical error during FinMind DataLoader initialization/login attempts: {e_init_critical}. Using anonymous access.")
    finmind_api = DataLoader() 
    login_method_used = "anonymous_critical_fail"

print(f"  (data_handler) Final FinMind API access method: {login_method_used}")


# TWSE OpenAPI 相關設定
API_BASE_URL = "https://openapi.twse.com.tw/v1/opendata"
INCOME_STATEMENT_API_PATH_PREFIX = "t187ap06_L"
BALANCE_SHEET_API_PATH_PREFIX = "t187ap07_L" 

API_SUFFIX_GENERAL = "_ci"
API_SUFFIX_FINANCIAL_HOLDING = "_fh"
API_SUFFIX_SECURITIES_FUTURES = "_bd"
API_SUFFIX_INSURANCE = "_ins"
API_SUFFIX_BANKING = "_basi"
API_SUFFIX_OTHER_INDUSTRY = "_mim"

INDUSTRY_TO_API_INFO = {
    "01": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "02": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "03": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "04": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "05": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "06": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "08": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "09": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "10": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "11": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "12": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "13": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "14": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "15": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "16": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "17": {"income_suffix": API_SUFFIX_FINANCIAL_HOLDING, "report_name": "金融控股業損益表"}, 
    "18": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "19": {"income_suffix": API_SUFFIX_OTHER_INDUSTRY, "report_name": "綜合類損益表"},   
    "20": {"income_suffix": API_SUFFIX_OTHER_INDUSTRY, "report_name": "其他業損益表"},   
    "21": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "22": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "23": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "24": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "25": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "26": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "27": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "28": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "29": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "30": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "31": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "32": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "33": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "34": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "35": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "36": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "37": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "38": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}, 
    "DEFAULT": {"income_suffix": API_SUFFIX_GENERAL, "report_name": "一般業損益表"}
}

SPECIFIC_REPORT_API_MAP = {
}

FINANCIAL_FIELD_NAMES_MAP = {
    API_SUFFIX_GENERAL: {"eps": "基本每股盈餘（元）", "revenue": "營業收入", "net_income_parent": "淨利（淨損）歸屬於母公司業主"},
    API_SUFFIX_FINANCIAL_HOLDING: {"eps": "基本每股盈餘（元）", "revenue": "淨收益", "net_income_parent": "淨利（淨損）歸屬於母公司業主"},
    API_SUFFIX_SECURITIES_FUTURES: {"eps": "基本每股盈餘（元）", "revenue": "收益", "net_income_parent": "淨利（損）歸屬於母公司業主"}, 
    API_SUFFIX_INSURANCE: {"eps": "基本每股盈餘（元）", "revenue": "營業收入", "net_income_parent": "淨利（淨損）歸屬於母公司業主"},
    API_SUFFIX_BANKING: {"eps": "基本每股盈餘（元）", "revenue": "利息淨收益", "net_income_parent": "淨利（損）歸屬於母公司業主"}, 
    API_SUFFIX_OTHER_INDUSTRY: {"eps": "基本每股盈餘（元）", "revenue": "收入", "net_income_parent": "淨利（淨損）歸屬於母公司業主"},
}

BALANCE_SHEET_FIELD_NAMES_MAP = {
    API_SUFFIX_GENERAL: {
        "accounts_receivable": "應收票據及帳款淨額", 
        "inventories": "存貨", 
        "accounts_payable": "應付票據及帳款"
    },
    API_SUFFIX_FINANCIAL_HOLDING: { 
        "accounts_receivable": "應收票據及帳款淨額", 
        "inventories": "存貨", 
        "accounts_payable": "應付票據及帳款"
    },
     API_SUFFIX_BANKING: { 
        "accounts_receivable": "貼現及放款", 
        "inventories": None, 
        "accounts_payable": "存款及匯款" 
    },
}


def get_all_companies_basic_data(context):
    if 'all_companies_openapi_data' in context and context['all_companies_openapi_data']:
        print("  (data_handler) 已從 context 獲取所有上市公司基本資料。")
        return context['all_companies_openapi_data']
    api_url = f"{API_BASE_URL}/t187ap03_L"
    print(f"  (data_handler) 首次從 TWSE OpenAPI 抓取所有上市公司基本資料: {api_url}")
    try:
        print("  (data_handler) 警告：將嘗試禁用 SSL 憑證驗證 (verify=False)。")
        response = requests.get(api_url, timeout=20, verify=False)
        response.raise_for_status()
        all_data = response.json()
        context['all_companies_openapi_data'] = all_data
        print(f"  (data_handler) 成功獲取 {len(all_data)} 家上市公司基本資料。")
        output_filename = "all_companies_basic_data.json"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(f"  (data_handler) 已將所有上市公司基本資料保存到 {output_filename}")
        except IOError as e_io:
            print(f"  (data_handler) 保存上市公司基本資料到檔案時發生錯誤: {e_io}")
        return all_data
    except Exception as e:
        print(f"  (data_handler) 抓取或處理所有上市公司基本資料時發生錯誤: {e}")
        context['all_companies_openapi_data'] = []
        return []

def filter_industry_stocks(selected_industry_name, industry_name_to_code_map, all_companies_data):
    target_industry_code = industry_name_to_code_map.get(selected_industry_name)
    if not target_industry_code:
        print(f"  (data_handler) 錯誤：在映射表中找不到產業 '{selected_industry_name}' 的代號。")
        return []
    print(f"  (data_handler) 正在從 {len(all_companies_data)} 筆公司資料中篩選產業 '{selected_industry_name}' (代號: {target_industry_code})...")
    industry_stocks_details_list = []
    for company in all_companies_data:
        api_industry_code_val = company.get("產業別")
        if api_industry_code_val and api_industry_code_val.strip() == target_industry_code:
            stock_code = company.get("公司代號", "")
            stock_name = company.get("公司簡稱", "")
            report_type = company.get("編制財務報表類型", "未知類型")
            company_full_name_str = stock_name 
            if all_companies_data: 
                for comp_data_detail in all_companies_data: 
                    if comp_data_detail.get("公司代號") == stock_code:
                        company_full_name_str = comp_data_detail.get("公司名稱", stock_name)
                        break
            
            shares_outstanding_str = company.get("已發行普通股數或TDR原股發行股數", "0")
            shares_outstanding = 0.0
            try:
                shares_outstanding = float(str(shares_outstanding_str).replace(",", ""))
                if shares_outstanding < 0: shares_outstanding = 0.0 
            except ValueError:
                print(f"  (data_handler) 警告：股票 {stock_code} 的流通股數 '{shares_outstanding_str}' 無法轉換為數字。設為0。")

            if stock_code and stock_name:
                industry_stocks_details_list.append({
                    "code": stock_code,
                    "name": stock_name,
                    "full_name": company_full_name_str, 
                    "report_type": report_type.strip(),
                    "industry_code": api_industry_code_val.strip(),
                    "shares_outstanding": shares_outstanding 
                })
    if not industry_stocks_details_list:
        print(f"  (data_handler) 警告：在產業 '{selected_industry_name}' (代號: {target_industry_code}) 下未找到任何上市公司。")
    else:
        print(f"  (data_handler) 在產業 '{selected_industry_name}' (代號: {target_industry_code}) 下找到 {len(industry_stocks_details_list)} 家公司。")
    return industry_stocks_details_list

def get_financial_reports_for_stock(stock_detail, context): # TWSE API (舊，備用)
    industry_code = stock_detail.get('industry_code')
    report_type_code = stock_detail.get('report_type') 
    stock_name = stock_detail.get('name', '') 
    company_full_name_str = stock_detail.get('full_name', stock_name) 
    stock_code_for_debug = stock_detail.get('code', 'N/A')

    api_config = INDUSTRY_TO_API_INFO.get(industry_code, INDUSTRY_TO_API_INFO["DEFAULT"])
    api_suffix = api_config["income_suffix"]
    report_name_for_log = api_config["report_name"]

    specific_config_key = (industry_code, report_type_code)
    if specific_config_key in SPECIFIC_REPORT_API_MAP:
        api_config = SPECIFIC_REPORT_API_MAP[specific_config_key]
        api_suffix = api_config["income_suffix"]
        report_name_for_log = api_config["report_name"]
        print(f"  (data_handler) [TWSE] 股票 {stock_code_for_debug} ({stock_name}) 依特定規則使用 {report_name_for_log}")
    elif industry_code == "17": 
        if "金融控股" in company_full_name_str or "金控" in stock_name:
            api_suffix = API_SUFFIX_FINANCIAL_HOLDING
            report_name_for_log = "金控業損益表"
        elif "證券" in company_full_name_str or "期貨" in company_full_name_str:
            api_suffix = API_SUFFIX_SECURITIES_FUTURES
            report_name_for_log = "證券期貨業損益表"
        elif "銀行" in company_full_name_str:
            api_suffix = API_SUFFIX_BANKING
            report_name_for_log = "銀行業損益表"
        elif "產險" in company_full_name_str or "產物保險" in company_full_name_str or "人壽" in company_full_name_str or "再保" in company_full_name_str:
            api_suffix = API_SUFFIX_INSURANCE
            report_name_for_log = "保險業損益表"
        elif "票券" in company_full_name_str:
             api_suffix = API_SUFFIX_BANKING 
             report_name_for_log = "票券金融(用銀行API)損益表"
        else: 
            print(f"  (data_handler) [TWSE] 金融業公司 {stock_code_for_debug} ({company_full_name_str}) 未匹配特定子類關鍵字，使用產業預設 ({report_name_for_log})。")
    elif report_type_code == '2' and industry_code != "17": 
        print(f"  (data_handler) [TWSE] 非金融產業 {industry_code} 公司 {stock_code_for_debug} ({stock_name}) report_type '{report_type_code}' (個體財報)，使用其產業預設API ({report_name_for_log})。")
    
    api_url = f"{API_BASE_URL}/{INCOME_STATEMENT_API_PATH_PREFIX}{api_suffix}"
    context_key = f"financial_reports{api_suffix}"

    if context_key not in context or not context.get(context_key):
        print(f"  (data_handler) [TWSE] 正在獲取 {report_name_for_log} ({api_url}) 並存入 context['{context_key}']...")
        try:
            print(f"    (data_handler) [TWSE] 警告：將嘗試禁用 SSL 憑證驗證 (verify=False) 來獲取 {report_name_for_log}。")
            response = requests.get(api_url, timeout=30, verify=False)
            response.raise_for_status()
            context[context_key] = response.json()
            print(f"    (data_handler) [TWSE] 成功獲取 {len(context[context_key])} 筆 {report_name_for_log} 記錄。")
        except requests.exceptions.RequestException as e:
            print(f"    (data_handler) [TWSE] 獲取 {report_name_for_log} 時發生錯誤: {e}")
            context[context_key] = []
        except json.JSONDecodeError as e:
            print(f"    (data_handler) [TWSE] 解析 {report_name_for_log} JSON 時發生錯誤: {e}")
            context[context_key] = []
            
    return context.get(context_key, []), api_suffix

def get_balance_sheet_data_for_stock(stock_detail, context): # TWSE API (舊，備用)
    industry_code = stock_detail.get('industry_code')
    report_type_code = stock_detail.get('report_type') 
    stock_name = stock_detail.get('name', '') 
    company_full_name_str = stock_detail.get('full_name', stock_name) 
    stock_code_for_debug = stock_detail.get('code', 'N/A')
    api_config = INDUSTRY_TO_API_INFO.get(industry_code, INDUSTRY_TO_API_INFO["DEFAULT"])
    api_suffix = api_config["income_suffix"] 
    report_name_for_log = f"{api_config.get('report_name','一般業')}資產負債表"
    api_url = f"{API_BASE_URL}/{BALANCE_SHEET_API_PATH_PREFIX}{api_suffix}" 
    context_key = f"balance_sheet_reports{api_suffix}" 
    if context_key not in context or not context.get(context_key):
        print(f"  (data_handler) [TWSE] 正在獲取 {report_name_for_log} ({api_url}) 並存入 context['{context_key}']...")
        try:
            print(f"    (data_handler) [TWSE] 警告：將嘗試禁用 SSL 憑證驗證 (verify=False) 來獲取 {report_name_for_log}。")
            response = requests.get(api_url, timeout=30, verify=False) 
            response.raise_for_status()
            context[context_key] = response.json()
            print(f"    (data_handler) [TWSE] 成功獲取 {len(context[context_key])} 筆 {report_name_for_log} 記錄。")
        except requests.exceptions.RequestException as e:
            print(f"    (data_handler) [TWSE] 獲取 {report_name_for_log} 時發生錯誤: {e}")
            context[context_key] = []
        except json.JSONDecodeError as e:
            print(f"    (data_handler) [TWSE] 解析 {report_name_for_log} JSON 時發生錯誤: {e}")
            context[context_key] = []
    return context.get(context_key, []), api_suffix

# --- FinMind Data Fetching Functions ---

def fetch_finmind_financial_statement_data(stock_id: str, start_date: str, statement_type: str):
    cache_file_name = f"{stock_id}_{statement_type}_{start_date.replace('-', '')}.parquet"
    cache_file_path = CACHE_DIR / cache_file_name

    if cache_file_path.exists():
        try:
            file_mod_time = cache_file_path.stat().st_mtime
            if (time.time() - file_mod_time) < CACHE_EXPIRY_SECONDS:
                print(f"  (data_handler) CACHE HIT: Reading {statement_type} for {stock_id} from {cache_file_path}")
                df = pd.read_parquet(str(cache_file_path)) 
                if 'date' in df.columns: 
                     df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                print(f"  (data_handler) CACHE STALE: {cache_file_path} expired. Fetching from API.")
        except Exception as e_cache_read:
            print(f"  (data_handler) CACHE READ ERROR for {cache_file_path}: {e_cache_read}. Fetching from API.")

    print(f"  (data_handler) CACHE MISS/STALE: Fetching FinMind {statement_type} for {stock_id} from {start_date} via API...")
    df = None
    try:
        # 已移除API呼叫延遲，請注意API速率限制
        if statement_type == 'BalanceSheet':
            df = finmind_api.taiwan_stock_balance_sheet(stock_id=stock_id, start_date=start_date)
        elif statement_type == 'CashFlowsStatement':
            df = finmind_api.taiwan_stock_cash_flows_statement(stock_id=stock_id, start_date=start_date)
        elif statement_type == 'FinancialStatements': 
            df = finmind_api.taiwan_stock_financial_statement(stock_id=stock_id, start_date=start_date)
        else:
            print(f"    (data_handler) Unknown FinMind statement_type: {statement_type}")
            return pd.DataFrame()

        if df is not None and not df.empty:
            print(f"    (data_handler) Successfully fetched FinMind {statement_type} for {stock_id}. Shape: {df.shape}")
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(by='date', ascending=False)
            try:
                cache_file_path.parent.mkdir(parents=True, exist_ok=True) 
                df.to_parquet(str(cache_file_path)) 
                print(f"    (data_handler) CACHE SAVED: {statement_type} for {stock_id} to {cache_file_path}")
            except Exception as e_cache_write:
                print(f"    (data_handler) CACHE WRITE ERROR for {str(cache_file_path)}: {e_cache_write}")
            return df
        elif df is not None and df.empty:
            print(f"    (data_handler) Fetched FinMind {statement_type} for {stock_id}, but it's an empty DataFrame. Not caching.")
            return pd.DataFrame()
        else:
            print(f"    (data_handler) Failed to fetch FinMind {statement_type} for {stock_id} (returned None).")
            return pd.DataFrame()
    except Exception as e:
        print(f"    (data_handler) Error fetching FinMind {statement_type} for {stock_id}: {e}")
        return pd.DataFrame()

def extract_finmind_items(df: pd.DataFrame, target_items_map: dict, report_date_str: str = None, max_lookback_periods: int = 1):
    extracted_values = {key: None for key in target_items_map.keys()}
    for key in target_items_map.keys(): # Initialize all potential keys
        extracted_values[f"{key}_actual_date"] = None
        extracted_values[f"{key}_source_field"] = None

    if df.empty:
        extracted_values['report_date'] = report_date_str # If a date was passed, use it, else None
        return extracted_values

    all_available_dates_in_df = sorted(pd.to_datetime(df['date'].unique()), reverse=True)
    if not all_available_dates_in_df:
        print(f"    (data_handler) No valid dates found in the provided DataFrame for extraction.")
        extracted_values['report_date'] = report_date_str # If a date was passed, use it, else None
        return extracted_values

    target_date_dt = None
    processed_report_date_str = None # This will be the date string corresponding to target_date_dt

    if report_date_str:
        try:
            target_date_dt = pd.to_datetime(report_date_str)
            processed_report_date_str = report_date_str
        except ValueError:
            print(f"    (data_handler) Invalid report_date_str: {report_date_str}. Will use latest available date from DataFrame if possible.")
            # Fall through to use latest from df if report_date_str is invalid
            target_date_dt = all_available_dates_in_df[0]
            processed_report_date_str = target_date_dt.strftime('%Y-%m-%d')
    else: # No specific date passed, use the latest from the dataframe
        target_date_dt = all_available_dates_in_df[0]
        processed_report_date_str = target_date_dt.strftime('%Y-%m-%d')
    
    extracted_values['report_date'] = processed_report_date_str # Set the report date that will be processed/targeted

    try:
        # Ensure target_date_dt is not None before proceeding
        if target_date_dt is None: # Should not happen if logic above is correct
            print(f"    (data_handler) CRITICAL: target_date_dt is None before processing items. This should not occur.")
            return extracted_values

        if target_date_dt.tzinfo is not None and all_available_dates_in_df[0].tzinfo is None:
            target_date_dt = target_date_dt.tz_localize(None)
        target_date_index = all_available_dates_in_df.index(target_date_dt)
    except ValueError:
        print(f"    (data_handler) Target date {report_date_str} not found in available dates. Will try to look back from nearest earlier date if possible.")
        earlier_dates = [d for d in all_available_dates_in_df if d < target_date_dt]
        if not earlier_dates:
            print(f"    (data_handler) No dates available before {report_date_str} to start lookback.")
            return extracted_values
        target_date_index = all_available_dates_in_df.index(earlier_dates[0])

    for key, finmind_type_or_list in target_items_map.items():
        found_value_for_key = None
        actual_date_for_key = None
        used_finmind_type_for_key = None
        
        finmind_types_to_try_with_conditions = []
        if key == 'net_income_parent':
            finmind_types_to_try_with_conditions = [
                ('EquityAttributableToOwnersOfParent', lambda origin_name: "綜合損益" not in str(origin_name) and ("淨利" in str(origin_name) or "純益" in str(origin_name))),
                ('ProfitLoss', None), 
                ('IncomeFromContinuingOperations', None), 
                ('IncomeAfterTax', None) 
            ]
        elif isinstance(finmind_type_or_list, list):
            finmind_types_to_try_with_conditions = [(ft, None) for ft in finmind_type_or_list]
        else: 
            finmind_types_to_try_with_conditions = [(finmind_type_or_list, None)]
        
        logged_skip_for_primary_candidate_this_key_for_period = False

        for lookback_attempt in range(max_lookback_periods + 1):
            if found_value_for_key is not None: break 

            current_date_index_to_try = target_date_index + lookback_attempt
            if current_date_index_to_try < len(all_available_dates_in_df):
                current_processing_date_dt = all_available_dates_in_df[current_date_index_to_try]
                current_processing_date_str = current_processing_date_dt.strftime('%Y-%m-%d')
                
                df_current_period = df[df['date'] == current_processing_date_dt].copy()
                
                if not df_current_period.empty:
                    temp_df_indexed = df_current_period.set_index('type', drop=False)
                    
                    # Reset skip log for new lookback period
                    if lookback_attempt > 0: logged_skip_for_primary_candidate_this_key_for_period = False


                    for finmind_type_candidate, condition_func in finmind_types_to_try_with_conditions:
                        if found_value_for_key is not None: break # Already found for this key in this lookback period

                        if finmind_type_candidate in temp_df_indexed.index:
                            matched_rows = temp_df_indexed.loc[[finmind_type_candidate]]
                            
                            for _, row_data in matched_rows.iterrows(): 
                                value = row_data['value']
                                origin_name = row_data.get('origin_name', '') 

                                if pd.notna(value):
                                    passes_condition = True
                                    if condition_func:
                                        passes_condition = condition_func(origin_name)
                                    
                                    if passes_condition:
                                        found_value_for_key = float(value)
                                        actual_date_for_key = current_processing_date_str
                                        used_finmind_type_for_key = finmind_type_candidate
                                        
                                        is_primary_attempt_for_net_income = (key == 'net_income_parent' and finmind_type_candidate == finmind_types_to_try_with_conditions[0][0])
                                        if lookback_attempt > 0 or (key == 'net_income_parent' and not is_primary_attempt_for_net_income) :
                                             print(f"    (data_handler) Item '{key}' (target date: {report_date_str}): Found using FinMind type '{used_finmind_type_for_key}' (Origin: '{origin_name}') from date {actual_date_for_key}, Value: {found_value_for_key}.")
                                        break 
                                    elif key == 'net_income_parent' and finmind_type_candidate == 'EquityAttributableToOwnersOfParent' and not logged_skip_for_primary_candidate_this_key_for_period:
                                        print(f"    (data_handler) Item '{key}' (target date: {report_date_str}): Skipped '{finmind_type_candidate}' (Origin: '{origin_name}') for date {current_processing_date_str} due to condition fail.")
                                        logged_skip_for_primary_candidate_this_key_for_period = True 
                            if found_value_for_key is not None: break 
            if found_value_for_key is not None: break 
        
        if found_value_for_key is not None:
            extracted_values[key] = found_value_for_key
            extracted_values[f"{key}_actual_date"] = actual_date_for_key
            extracted_values[f"{key}_source_field"] = used_finmind_type_for_key
        else:
            print(f"    (data_handler) Item '{key}' (tried: {[ft[0] for ft in finmind_types_to_try_with_conditions]}) not found for target date {report_date_str} even after {max_lookback_periods} lookback period(s).")

    return extracted_values

def fetch_finmind_stock_price(stock_id: str, target_date_str: str = None):
    """
    Fetches the latest stock price for a given stock_id up to the target_date.
    If target_date_str is None, fetches the most recent price.
    Uses caching.
    """
    # Determine date range for fetching; we want the price on or before target_date_str
    # If target_date_str is None, we fetch for a recent period to get the latest.
    if target_date_str:
        end_date_dt = pd.to_datetime(target_date_str)
        start_date_dt = end_date_dt - pd.Timedelta(days=14) # Look back 14 days
    else:
        end_date_dt = pd.Timestamp.today()
        start_date_dt = end_date_dt - pd.Timedelta(days=14)

    start_date_api_str = start_date_dt.strftime('%Y-%m-%d')
    end_date_api_str = end_date_dt.strftime('%Y-%m-%d') # FinMind end_date is inclusive

    cache_file_name = f"{stock_id}_daily_price_{end_date_api_str.replace('-', '')}.parquet"
    cache_file_path = CACHE_DIR.parent / "finmind_price_cache" / cache_file_name # Separate cache for prices
    
    try:
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e_mkdir_price:
        print(f"  (data_handler) ERROR: Could not create price cache directory at {cache_file_path.parent}: {e_mkdir_price}")


    if cache_file_path.exists():
        try:
            file_mod_time = cache_file_path.stat().st_mtime
            # Price data changes daily, so a shorter expiry, e.g., 12 hours or check if date is today
            is_today = end_date_dt.date() == pd.Timestamp.today().date()
            cache_duration = 12 * 3600 if is_today else 24 * 3600 # 12 hours if today, else 24 hours
            if (time.time() - file_mod_time) < cache_duration:
                print(f"  (data_handler) PRICE CACHE HIT: Reading daily prices for {stock_id} from {cache_file_path}")
                df_price = pd.read_parquet(str(cache_file_path))
                if not df_price.empty and 'date' in df_price.columns:
                    df_price['date'] = pd.to_datetime(df_price['date'])
                    # Filter for the target_date_str or latest if None
                    if target_date_str:
                        df_price_filtered = df_price[df_price['date'] <= pd.to_datetime(target_date_str)].sort_values(by='date', ascending=False)
                    else:
                        df_price_filtered = df_price.sort_values(by='date', ascending=False)
                    
                    if not df_price_filtered.empty:
                        return df_price_filtered.iloc[0]['close'] # Return the closing price of the most recent day found
                return None # Cache hit but no valid data
            else:
                print(f"  (data_handler) PRICE CACHE STALE: {cache_file_path} expired. Fetching from API.")
        except Exception as e_cache_read_price:
            print(f"  (data_handler) PRICE CACHE READ ERROR for {cache_file_path}: {e_cache_read_price}. Fetching from API.")

    print(f"  (data_handler) PRICE CACHE MISS/STALE: Fetching FinMind daily price for {stock_id} from {start_date_api_str} to {end_date_api_str} via API...")
    try:
        # 已移除API呼叫延遲，請注意API速率限制
        df_price = finmind_api.taiwan_stock_daily(stock_id=stock_id, start_date=start_date_api_str, end_date=end_date_api_str)
        if df_price is not None and not df_price.empty:
            print(f"    (data_handler) Successfully fetched FinMind daily price for {stock_id}. Shape: {df_price.shape}")
            if 'date' in df_price.columns:
                df_price['date'] = pd.to_datetime(df_price['date'])
                df_price = df_price.sort_values(by='date', ascending=False)
                try:
                    df_price.to_parquet(str(cache_file_path))
                    print(f"    (data_handler) PRICE CACHE SAVED: Daily price for {stock_id} to {cache_file_path}")
                except Exception as e_cache_write_price:
                    print(f"    (data_handler) PRICE CACHE WRITE ERROR for {str(cache_file_path)}: {e_cache_write_price}")

                # Filter again after fetching for the target_date_str or latest if None
                if target_date_str:
                    df_price_filtered = df_price[df_price['date'] <= pd.to_datetime(target_date_str)].sort_values(by='date', ascending=False)
                else:
                    df_price_filtered = df_price # Already sorted
                
                if not df_price_filtered.empty:
                    return df_price_filtered.iloc[0]['close']
            return None # No date column or data after sort
        elif df_price is not None and df_price.empty:
            print(f"    (data_handler) Fetched FinMind daily price for {stock_id}, but it's an empty DataFrame. Not caching.")
            return None
        else:
            print(f"    (data_handler) Failed to fetch FinMind daily price for {stock_id} (returned None).")
            return None
    except Exception as e:
        print(f"    (data_handler) Error fetching FinMind daily price for {stock_id}: {e}")
        return None

# --- End FinMind Data Fetching Functions ---


def fetch_stock_financials_from_downloaded(stock_code, api_suffix_for_report, downloaded_financial_reports): 
    print(f"  (data_handler) [TWSE API] 正在為股票代號 '{stock_code}' (API後綴: {api_suffix_for_report}) 從已下載財報中提取數據...")
    latest_statement = None
    latest_year = "000"
    latest_quarter = "0"
    
    if not downloaded_financial_reports:
        print(f"    (data_handler) [TWSE API] 警告：股票 '{stock_code}' 的財報數據集 (API後綴: {api_suffix_for_report}) 為空。")
        return {"eps": None, "revenue": None, "net_income_to_parent": None, "error": f"No income statements for {api_suffix_for_report}"}

    for statement in downloaded_financial_reports:
        if statement.get("公司代號") == stock_code:
            current_year = statement.get("年度", "000")
            current_quarter = statement.get("季別", "0")
            if current_year > latest_year:
                latest_year = current_year
                latest_quarter = current_quarter
                latest_statement = statement
            elif current_year == latest_year and current_quarter > latest_quarter:
                latest_quarter = current_quarter
                latest_statement = statement
    
    if latest_statement:
        field_map = FINANCIAL_FIELD_NAMES_MAP.get(api_suffix_for_report, FINANCIAL_FIELD_NAMES_MAP[API_SUFFIX_GENERAL])
        eps_field_name = field_map.get("eps", "基本每股盈餘（元）")
        revenue_field_name = field_map.get("revenue", "營業收入")
        net_income_parent_field = field_map.get("net_income_parent", "淨利（淨損）歸屬於母公司業主")

        eps_str = latest_statement.get(eps_field_name)
        revenue_str = latest_statement.get(revenue_field_name)
        net_income_to_parent_val_str = latest_statement.get(net_income_parent_field)
        
        eps = None
        try:
            if eps_str is not None and str(eps_str).strip() != "": eps = float(eps_str)
        except ValueError:
            print(f"    (data_handler) [TWSE API] 警告：股票 '{stock_code}' 的EPS '{eps_str}' (欄位: {eps_field_name}) 無法轉換為浮點數。")

        revenue = None
        try:
            if revenue_str is not None and str(revenue_str).strip() != "": revenue = float(revenue_str)
        except ValueError:
            print(f"    (data_handler) [TWSE API] 警告：股票 '{stock_code}' 的營收 '{revenue_str}' (欄位: {revenue_field_name}) 無法轉換為浮點數。")
        
        net_income_to_parent = None
        try:
            if net_income_to_parent_val_str is not None and str(net_income_to_parent_val_str).strip() != "":
                net_income_to_parent = float(net_income_to_parent_val_str) * 1000 
        except ValueError:
            print(f"    (data_handler) [TWSE API] 警告：股票 '{stock_code}' 的淨利歸母 '{net_income_to_parent_val_str}' (欄位: {net_income_parent_field}) 無法轉換為浮點數。")
        
        if revenue is not None:
            revenue *= 1000

        print(f"    (data_handler) [TWSE API] 為股票 '{stock_code}' 找到財報 (年度:{latest_year}, 季度:{latest_quarter}, API後綴:{api_suffix_for_report}): EPS={eps}, 營收(元)={revenue}, 淨利歸母(元)={net_income_to_parent}")
        return {"eps": eps, "revenue": revenue, "net_income_to_parent": net_income_to_parent, "year": latest_year, "quarter": latest_quarter, "report_api_suffix": api_suffix_for_report}
    else:
        print(f"    (data_handler) [TWSE API] 警告：未在 API後綴 '{api_suffix_for_report}' 的財報數據中找到股票代號 '{stock_code}' 的記錄。")
        return {"eps": None, "revenue": None, "net_income_to_parent": None, "error": f"Data not found for {stock_code} in {api_suffix_for_report} reports"}

def _fetch_stock_financials_simulated(stock_detail): 
    stock_code = stock_detail.get("code", "N/A_sim")
    print(f"  (data_handler) 為股票 {stock_code} 返回預設模擬財務數據。")
    return {
        "eps": stock_detail.get("sim_eps", 0.01), 
        "revenue": stock_detail.get("sim_revenue", 100000.0), 
        "net_income_to_parent": stock_detail.get("sim_net_income", 5000.0), 
        "shares_outstanding": stock_detail.get("sim_shares", 1000000.0),
        "current_market_price": stock_detail.get("sim_price", 100.0),
        "year": "sim", "quarter": "sim", "report_api_suffix": "_sim", "source": "simulated",
        'ar_t0': 10000.0, 'inv_t0': 5000.0, 'ap_t0': 3000.0,
        'ar_t1': 9000.0, 'inv_t1': 4500.0, 'ap_t1': 2500.0,
        'capex': 2000.0, 'depreciation': 500.0, 'amortization': 100.0,
    }

def calculate_historical_fcf_eps(stock_code, stock_detail, context, periods=4):
    """
    計算歷史多期FCF_EPS，用於檢測一次性收益異常
    增強版本包含智能缓存和性能優化
    
    Args:
        stock_code: 股票代碼
        stock_detail: 股票詳細資訊
        context: 上下文物件
        periods: 要計算的歷史期數，預設4期
        
    Returns:
        dict: 包含歷史FCF_EPS列表和統計資訊
    """
    print(f"  (data_handler) 🔍 智能計算股票 {stock_code} 歷史 {periods} 期 FCF_EPS...")
    
    # 檢查缓存
    cache_key = f"historical_fcf_eps_{stock_code}_{periods}"
    cached_result = context.get('calculation_cache', {}).get(cache_key)
    if cached_result:
        print(f"    (data_handler) ⚡ 使用缓存數據 (股票 {stock_code})")
        return cached_result
    
    try:
        # 批量獲取歷史財務數據（優化：設定適當的日期範圍）
        start_date = "2020-01-01"  # 優化：減少不必要的歷史數據
        print(f"    (data_handler) 📊 從 {start_date} 開始獲取財務數據...")
        
        df_is = fetch_finmind_financial_statement_data(stock_code, start_date, "TaiwanStockFinancialStatements")
        df_cf = fetch_finmind_financial_statement_data(stock_code, start_date, "TaiwanStockCashFlowsStatement") 
        df_bs = fetch_finmind_financial_statement_data(stock_code, start_date, "TaiwanStockBalanceSheet")
        
        if df_is is None or df_cf is None or df_bs is None:
            error_msg = "歷史財務數據獲取失敗"
            print(f"    (data_handler) ❌ 警告：股票 {stock_code} {error_msg}")
            result = {"error": error_msg, "historical_fcf_eps": []}
        elif df_is.empty or df_cf.empty or df_bs.empty:
            error_msg = "歷史財務數據為空"
            print(f"    (data_handler) ❌ 警告：股票 {stock_code} {error_msg}")
            result = {"error": error_msg, "historical_fcf_eps": []}
        else:
            result = _calculate_historical_fcf_eps_core(stock_code, df_is, df_cf, df_bs, periods)
        
        # 缓存結果
        if 'calculation_cache' not in context:
            context['calculation_cache'] = {}
        context['calculation_cache'][cache_key] = result
        
        return result
        
    except Exception as e:
        error_msg = f"計算錯誤: {str(e)}"
        print(f"    (data_handler) ❌ 計算股票 {stock_code} 歷史FCF_EPS時發生錯誤: {e}")
        result = {"error": error_msg, "historical_fcf_eps": []}
        
        # 即使出錯也缓存，避免重複嘗試
        if 'calculation_cache' not in context:
            context['calculation_cache'] = {}
        context['calculation_cache'][cache_key] = result
        
        return result

def _calculate_historical_fcf_eps_core(stock_code, df_is, df_cf, df_bs, periods):
    """
    歷史FCF_EPS計算的核心邏輯
    """
    # 取得可用日期列表，確保按季度排序
    all_dates = sorted(df_is['date'].unique(), reverse=True)  # 最新的在前面
    historical_fcf_eps = []
    
    # 定義要提取的項目（優化：預定義以提高性能）
    target_items_map = {
        'net_income_parent': 'EquityAttributableToOwnersOfParent',
        'shares_outstanding': 'WeightedAverageNumberOfOutstandingShares', 
        'capex': ['CashFlowFromAcquisitionOfPropertyPlantAndEquipment', 'PurchaseOfPropertyPlantAndEquipment'],
        'depreciation': ['DepreciationAndAmortization', 'Depreciation'],
        'amortization': 'Amortization'
    }
    
    # 平衡表項目（用於營運資本計算）
    bs_items_map = {
        'accounts_receivable': 'NotesAndAccountsReceivableNet',
        'inventories': 'Inventory', 
        'accounts_payable': 'NotesAndAccountsPayable'
    }
    
    # 計算每期FCF_EPS（改進：更穩定的錯誤處理）
    valid_periods = 0
    for i, report_date in enumerate(all_dates[:periods * 2]):  # 多取一些日期以確保有足夠的有效期數
        if valid_periods >= periods:
            break
            
        try:
            report_date_str = report_date.strftime('%Y-%m-%d')
            print(f"    (data_handler) 📅 處理第 {valid_periods+1} 期: {report_date_str}")
            
            # 提取損益表和現金流量表數據
            period_data = extract_finmind_items(df_is, target_items_map, report_date_str, max_lookback_periods=1)
            period_data.update(extract_finmind_items(df_cf, target_items_map, report_date_str, max_lookback_periods=1))
            
            # 提取平衡表數據（當期和前期）
            bs_current = extract_finmind_items(df_bs, bs_items_map, report_date_str, max_lookback_periods=1)
            
            # 尋找前一期資料（改進：更穩定的前期查找）
            prev_date_str = None
            for j in range(i + 1, min(i + 5, len(all_dates))):  # 查找前5期內的有效數據
                candidate_date = all_dates[j].strftime('%Y-%m-%d')
                temp_bs = extract_finmind_items(df_bs, bs_items_map, candidate_date, max_lookback_periods=1)
                if any(temp_bs.values()):  # 如果找到有效的前期數據
                    prev_date_str = candidate_date
                    break
                    
            bs_previous = extract_finmind_items(df_bs, bs_items_map, prev_date_str, max_lookback_periods=1) if prev_date_str else {}
            
            # 檢查關鍵數據完整性
            net_income = period_data.get('net_income_parent')
            shares_outstanding = period_data.get('shares_outstanding')
            
            if net_income is None or shares_outstanding is None or shares_outstanding == 0:
                print(f"    (data_handler) ⏭️ 第 {valid_periods+1} 期關鍵數據缺失，跳過此期")
                continue
            
            # 計算FCFE組件
            capex_raw = period_data.get('capex')
            depreciation = period_data.get('depreciation', 0.0) or 0.0
            amortization = period_data.get('amortization', 0.0) or 0.0
            
            # 處理資本支出（通常為負數）
            capex = -capex_raw if capex_raw is not None and capex_raw < 0 else (capex_raw if capex_raw is not None else 0.0)
            depreciation_amortization = depreciation + amortization
            net_capex = max(0, capex - depreciation_amortization)  # 避免負數淨資本支出
            
            # 計算營運資本變動（改進：更穩定的預設值處理）
            ar_current = bs_current.get('accounts_receivable') or 0.0
            inv_current = bs_current.get('inventories') or 0.0 
            ap_current = bs_current.get('accounts_payable') or 0.0
            wc_current = ar_current + inv_current - ap_current
            
            ar_previous = bs_previous.get('accounts_receivable') or ar_current  # 如果沒有前期數據，使用當期
            inv_previous = bs_previous.get('inventories') or inv_current
            ap_previous = bs_previous.get('accounts_payable') or ap_current
            wc_previous = ar_previous + inv_previous - ap_previous
            
            delta_wc = wc_current - wc_previous
            
            # 計算FCFE和FCF_EPS（改進：限制極端值）
            fcfe = net_income - net_capex - delta_wc  # 假設淨借款為0
            fcf_eps = fcfe / shares_outstanding
            
            # 數據合理性檢查（過濾明顯異常的數據）
            if abs(fcf_eps) > 1000:  # FCF_EPS過大，可能是數據錯誤
                print(f"    (data_handler) ⚠️ 第 {valid_periods+1} 期 FCF_EPS 異常 ({fcf_eps:.2f})，跳過")
                continue
            
            historical_fcf_eps.append({
                'period': report_date_str,
                'fcf_eps': fcf_eps,
                'net_income': net_income,
                'shares_outstanding': shares_outstanding,
                'fcfe': fcfe,
                'capex': capex,
                'delta_wc': delta_wc
            })
            
            print(f"    (data_handler) ✅ 第 {valid_periods+1} 期 ({report_date_str}): FCF_EPS={fcf_eps:.3f}")
            valid_periods += 1
            
        except Exception as e:
            print(f"    (data_handler) ⚠️ 處理第 {valid_periods+1} 期時發生錯誤: {e}")
            continue
    
    if not historical_fcf_eps:
        return {"error": "無法計算任何歷史期FCF_EPS", "historical_fcf_eps": []}
    
    # 計算增強的統計資訊
    fcf_eps_values = [item['fcf_eps'] for item in historical_fcf_eps]
    avg_fcf_eps = sum(fcf_eps_values) / len(fcf_eps_values)
    max_fcf_eps = max(fcf_eps_values)
    min_fcf_eps = min(fcf_eps_values)
    
    # 計算變異係數 (CV) 以評估穩定性
    if avg_fcf_eps != 0:
        variance = sum((x - avg_fcf_eps) ** 2 for x in fcf_eps_values) / len(fcf_eps_values)
        std_dev = variance ** 0.5
        cv = std_dev / abs(avg_fcf_eps)
    else:
        cv = float('inf')
    
    print(f"    (data_handler) 📈 股票 {stock_code} 歷史FCF_EPS統計:")
    print(f"    (data_handler)    平均={avg_fcf_eps:.3f}, 最大={max_fcf_eps:.3f}, 最小={min_fcf_eps:.3f}")
    print(f"    (data_handler)    變異係數={cv:.2f} ({'穩定' if cv < 0.5 else '不穩定' if cv < 1.0 else '極不穩定'})")
    
    return {
        "historical_fcf_eps": historical_fcf_eps,
        "avg_fcf_eps": avg_fcf_eps,
        "max_fcf_eps": max_fcf_eps,  
        "min_fcf_eps": min_fcf_eps,
        "std_dev": std_dev if 'std_dev' in locals() else 0,
        "cv": cv,
        "periods_count": len(historical_fcf_eps),
        "quality_score": 1.0 / (1.0 + cv) if cv != float('inf') else 0.1  # 數據品質評分
    }

def calculate_dcf_valuation(stock_code, financials, risk_preference, context):
    """
    Main DCF valuation function with option to use enhanced or original implementation
    """
    if USE_ENHANCED_DCF:
        # Use enhanced DCF with validation and advanced features
        print(f"  (data_handler) 使用增強版 DCF 進行估值...")
        return calculate_enhanced_dcf_valuation(stock_code, financials, risk_preference, context)
    else:
        # Use original DCF implementation
        print(f"  (data_handler) 使用原始版 DCF 進行估值...")
        return calculate_original_dcf_valuation(stock_code, financials, risk_preference, context)

def calculate_original_dcf_valuation(stock_code, financials, risk_preference, context):
    """
    Enhanced DCF valuation with integrated data validation and advanced features
    """
    print(f"  (data_handler) 開始為股票 {stock_code} 進行增強版 DCF 估值...")
    
    # Phase 1: Data Validation
    print(f"  (data_handler) 🔍 Phase 1: 執行財務數據品質驗證...")
    validation_result = financial_validator.validate_dcf_inputs(financials, stock_code)
    
    # Log validation results
    print(f"    (data_handler) 驗證品質分數: {validation_result.overall_quality_score:.1f}/100")
    print(f"    (data_handler) 錯誤數量: {validation_result.error_count}, 警告數量: {validation_result.warning_count}")
    
    # Check for critical errors that would prevent DCF calculation
    critical_errors = [issue for issue in validation_result.issues if issue.level == 'ERROR']
    if critical_errors:
        error_messages = [f"{issue.field}: {issue.message}" for issue in critical_errors]
        print(f"    (data_handler) ❌ 嚴重錯誤阻止 DCF 計算: {'; '.join(error_messages)}")
        return {
            "stock_code": stock_code,
            "error": f"數據驗證失敗: {'; '.join(error_messages)}",
            "validation_score": validation_result.overall_quality_score,
            "data_quality": "POOR"
        }
    
    # Continue with enhanced DCF if validation passes
    if validation_result.overall_quality_score >= 60:  # Minimum quality threshold
        print(f"  (data_handler) 🚀 Phase 2: 執行增強版 DCF 估值計算...")
        
        # Prepare enhanced DCF inputs
        enhanced_inputs = {
            'stock_code': stock_code,
            'net_income': financials.get("net_income_parent"),
            'shares_outstanding': financials.get("shares_outstanding"),
            'capex': financials.get("capex"),
            'depreciation': financials.get("depreciation", 0) + financials.get("amortization", 0),
            'working_capital_change': calculate_working_capital_change(financials),
            'current_market_price': financials.get("current_market_price"),
            'risk_free_rate': context.get('risk_free_rate', 0.01),
            'market_premium': context.get('market_premium', 0.06),
            'beta': context.get('beta', 1.0),  # Default beta if not provided
            'growth_rate_short': context.get('dcf_short_term_growth_rate', 0.07),
            'growth_rate_terminal': context.get('dcf_terminal_growth_rate', 0.025),
            'projection_years': context.get('dcf_projection_years', 5)
        }
        
        # Execute enhanced DCF with scenario analysis
        dcf_result = enhanced_dcf_model.calculate_dcf_with_scenarios(enhanced_inputs)
        
        # Add validation metrics to result
        dcf_result.update({
            'validation_score': validation_result.overall_quality_score,
            'data_quality': get_quality_rating(validation_result.overall_quality_score),
            'validation_warnings': [issue.message for issue in validation_result.issues if issue.level == 'WARNING']
        })
        
        print(f"    (data_handler) ✅ 增強版 DCF 完成，內在價值: {dcf_result.get('intrinsic_value_per_share', 'N/A')}")
        return dcf_result
    
    else:
        # Fall back to standard DCF if quality is moderate
        print(f"  (data_handler) ⚠️ 數據品質中等({validation_result.overall_quality_score:.1f})，使用標準 DCF...")
        return calculate_standard_dcf_valuation(stock_code, financials, risk_preference, context, validation_result)

def calculate_working_capital_change(financials):
    """Calculate working capital change for DCF"""
    ar_t0 = financials.get('ar_t0', 0) or 0
    inv_t0 = financials.get('inv_t0', 0) or 0
    ap_t0 = financials.get('ap_t0', 0) or 0
    ar_t1 = financials.get('ar_t1', 0) or 0
    inv_t1 = financials.get('inv_t1', 0) or 0
    ap_t1 = financials.get('ap_t1', 0) or 0
    
    wc_t0 = ar_t0 + inv_t0 - ap_t0
    wc_t1 = ar_t1 + inv_t1 - ap_t1
    
    return wc_t0 - wc_t1

def get_quality_rating(score):
    """Convert quality score to rating"""
    if score >= 85:
        return "EXCELLENT"
    elif score >= 70:
        return "GOOD"
    elif score >= 55:
        return "FAIR"
    else:
        return "POOR"

def calculate_standard_dcf_valuation(stock_code, financials, risk_preference, context, validation_result=None):
    """
    Standard DCF calculation (original implementation) with validation integration
    """
    print(f"  (data_handler) 開始為股票 {stock_code} 進行標準 DCF 估值 (使用 FinMind 數據基礎)...")
    # print(f"    (data_handler) [DEBUG] Financials for {stock_code} in DCF: {financials}") # DEBUG Line

    if financials.get("error"):
        error_message = financials['error']
        if isinstance(error_message, str) and any(msg.strip().startswith("無法獲取") for msg in error_message.split(';') if msg.strip()): 
             print(f"    (data_handler) 股票 {stock_code} 因 FinMind 資料獲取不完整 ({error_message.strip()})，無法進行精確 FCFE 估值。")
             return {"stock_code": stock_code, "error": f"FinMind 資料不完整: {error_message.strip()}", 
                     "source_eps": financials.get("eps_finmind"), "current_market_price": financials.get("current_market_price")}
        elif isinstance(error_message, str) and error_message.strip(): 
            print(f"    (data_handler) 股票 {stock_code} 缺少財務數據，無法估值: {error_message}")
            return {"stock_code": stock_code, "error": f"Missing financial data: {error_message}",
                     "source_eps": financials.get("eps_finmind"), "current_market_price": financials.get("current_market_price")}
      # === 增強的一次性收益檢測機制 ===
    enable_anomaly_detection = context.get('enable_anomaly_detection', True)
    anomaly_threshold = context.get('anomaly_threshold', 1.5)  # FCF_EPS超過歷史平均1.5倍視為異常
    
    if enable_anomaly_detection:
        print(f"  (data_handler) 🔍 開始智能檢測股票 {stock_code} 是否存在一次性收益異常...")
        
        # 先快速計算當期FCF_EPS用於比較
        net_income_to_parent = financials.get("net_income_parent")
        shares_outstanding = financials.get("shares_outstanding")
        
        if net_income_to_parent is not None and shares_outstanding is not None and shares_outstanding > 0:
            # 簡化計算當期FCF_EPS（基於淨利潤）
            current_fcf_eps_simple = net_income_to_parent / shares_outstanding
            
            # 計算歷史FCF_EPS統計資料
            stock_detail = context.get('stock_details', {}).get(stock_code, {})
            historical_result = calculate_historical_fcf_eps(stock_code, stock_detail, context, periods=4)
            
            if not historical_result.get("error") and historical_result.get("periods_count", 0) >= 2:
                avg_historical_fcf_eps = historical_result.get("avg_fcf_eps", 0)
                max_historical_fcf_eps = historical_result.get("max_fcf_eps", 0)
                min_historical_fcf_eps = historical_result.get("min_fcf_eps", 0)
                periods_count = historical_result.get("periods_count")
                
                # 改進的異常檢測邏輯
                anomaly_detected = False
                anomaly_reason = ""
    print(f"  (data_handler) 開始為股票 {stock_code} 進行 DCF 估值 (使用 FinMind 數據基礎)...")
    # print(f"    (data_handler) [DEBUG] Financials for {stock_code} in DCF: {financials}") # DEBUG Line

    if financials.get("error"):
        error_message = financials['error']
        if isinstance(error_message, str) and any(msg.strip().startswith("無法獲取") for msg in error_message.split(';') if msg.strip()): 
             print(f"    (data_handler) 股票 {stock_code} 因 FinMind 資料獲取不完整 ({error_message.strip()})，無法進行精確 FCFE 估值。")
             return {"stock_code": stock_code, "error": f"FinMind 資料不完整: {error_message.strip()}", 
                     "source_eps": financials.get("eps_finmind"), "current_market_price": financials.get("current_market_price")}
        elif isinstance(error_message, str) and error_message.strip(): 
            print(f"    (data_handler) 股票 {stock_code} 缺少財務數據，無法估值: {error_message}")
            return {"stock_code": stock_code, "error": f"Missing financial data: {error_message}",
                     "source_eps": financials.get("eps_finmind"), "current_market_price": financials.get("current_market_price")}
      # === 增強的一次性收益檢測機制 ===
    enable_anomaly_detection = context.get('enable_anomaly_detection', True)
    anomaly_threshold = context.get('anomaly_threshold', 1.5)  # FCF_EPS超過歷史平均1.5倍視為異常
    
    if enable_anomaly_detection:
        print(f"  (data_handler) 🔍 開始智能檢測股票 {stock_code} 是否存在一次性收益異常...")
        
        # 先快速計算當期FCF_EPS用於比較
        net_income_to_parent = financials.get("net_income_parent")
        shares_outstanding = financials.get("shares_outstanding")
        
        if net_income_to_parent is not None and shares_outstanding is not None and shares_outstanding > 0:
            # 簡化計算當期FCF_EPS（基於淨利潤）
            current_fcf_eps_simple = net_income_to_parent / shares_outstanding
            
            # 計算歷史FCF_EPS統計資料
            stock_detail = context.get('stock_details', {}).get(stock_code, {})
            historical_result = calculate_historical_fcf_eps(stock_code, stock_detail, context, periods=4)
            
            if not historical_result.get("error") and historical_result.get("periods_count", 0) >= 2:
                avg_historical_fcf_eps = historical_result.get("avg_fcf_eps", 0)
                max_historical_fcf_eps = historical_result.get("max_fcf_eps", 0)
                min_historical_fcf_eps = historical_result.get("min_fcf_eps", 0)
                periods_count = historical_result.get("periods_count")
                
                # 改進的異常檢測邏輯
                anomaly_detected = False
                anomaly_reason = ""
                
                if avg_historical_fcf_eps > 0:
                    # 主要檢測：與歷史平均比較
                    ratio_to_avg = current_fcf_eps_simple / avg_historical_fcf_eps
                    
                    # 副檢測：與歷史最大值比較（防止極端值誤判）
                    ratio_to_max = current_fcf_eps_simple / max_historical_fcf_eps if max_historical_fcf_eps > 0 else 0
                    
                    # 多層檢測邏輯
                    if ratio_to_avg > anomaly_threshold:
                        if periods_count >= 3 and ratio_to_max > 1.2:  # 嚴格模式：需要超過歷史最大值20%
                            anomaly_detected = True
                            anomaly_reason = f"超過歷史平均{ratio_to_avg:.1f}倍且超過歷史最大值{ratio_to_max:.1f}倍"
                        elif periods_count < 3 and ratio_to_avg > anomaly_threshold * 1.3:  # 寬鬆模式：歷史數據少時提高閾值
                            anomaly_detected = True
                            anomaly_reason = f"歷史數據較少({periods_count}期)但超過加嚴閾值{ratio_to_avg:.1f}倍"
                        elif ratio_to_avg > anomaly_threshold * 2.0:  # 極端模式：超過2倍閾值直接排除
                            anomaly_detected = True
                            anomaly_reason = f"大幅超過歷史平均{ratio_to_avg:.1f}倍(極端異常)"
                
                if anomaly_detected:
                    print(f"    (data_handler) ⚠️ 警告：股票 {stock_code} 疑似存在一次性收益！")
                    print(f"    (data_handler) 當期FCF_EPS: {current_fcf_eps_simple:.3f}, 歷史平均: {avg_historical_fcf_eps:.3f}")
                    print(f"    (data_handler) 檢測結果: {anomaly_reason}")
                    print(f"    (data_handler) 為保護估值準確性，已排除此股票。")
                    
                    return {
                        "stock_code": stock_code,
                        "error": f"疑似一次性收益異常 ({anomaly_reason})",
                        "source_eps": financials.get("eps_finmind"),
                        "current_market_price": financials.get("current_market_price"),
                        "current_fcf_eps_simple": round(current_fcf_eps_simple, 3),
                        "avg_historical_fcf_eps": round(avg_historical_fcf_eps, 3),
                        "max_historical_fcf_eps": round(max_historical_fcf_eps, 3),
                        "anomaly_ratio": round(current_fcf_eps_simple / avg_historical_fcf_eps, 2) if avg_historical_fcf_eps > 0 else 0,
                        "historical_periods": periods_count,
                        "anomaly_reason": anomaly_reason
                    }
                else:
                    print(f"    (data_handler) ✅ 股票 {stock_code} FCF_EPS正常。當期: {current_fcf_eps_simple:.3f}, 歷史平均: {avg_historical_fcf_eps:.3f}")
            else:
                print(f"    (data_handler) ⏭️ 股票 {stock_code} 歷史數據不足({historical_result.get('periods_count', 0)}期)，跳過異常檢測。")
                if historical_result.get("error"):
                    print(f"    (data_handler) 數據獲取問題: {historical_result.get('error')}")
        else:
            print(f"    (data_handler) ⏭️ 股票 {stock_code} 當期財務數據不足，無法進行異常檢測。")
    # === 一次性收益檢測結束 ===

    net_income_to_parent = financials.get("net_income_parent") 
    net_income_source_field = financials.get('net_income_parent_source_field', '未知') 
    shares_outstanding = financials.get("shares_outstanding") 
    current_eps_for_reference = financials.get("eps_finmind") 
    current_market_price = financials.get("current_market_price")

    required_fields_for_fcfe = {
        "net_income_parent": net_income_to_parent,
        "shares_outstanding": shares_outstanding,
    }
    missing_core_fields = [k for k, v in required_fields_for_fcfe.items() if v is None]
    if missing_core_fields:
        error_msg = f"缺少核心數據: {', '.join(missing_core_fields)} (淨利嘗試來源欄位: {net_income_source_field})，無法進行估值。"
        print(f"    (data_handler) 股票 {stock_code}: {error_msg}")
        return {"stock_code": stock_code, "error": error_msg, "source_eps": current_eps_for_reference, "current_market_price": current_market_price, "net_income_source_field": net_income_source_field}

    if not isinstance(shares_outstanding, (int, float)) or shares_outstanding == 0:
        print(f"    (data_handler) 股票 {stock_code} 的流通股數無效或為0 ({shares_outstanding})，無法計算每股價值。")
        return {"stock_code": stock_code, "error": "流通股數無效或為0", "source_eps": current_eps_for_reference, "current_market_price": current_market_price, "net_income_source_field": net_income_source_field}

    capex_raw = financials.get('capex') 
    capex = -capex_raw if capex_raw is not None and capex_raw < 0 else (capex_raw if capex_raw is not None else 0.0)
    
    depreciation = financials.get('depreciation') 
    amortization = financials.get('amortization') 
    depreciation_amortization = (depreciation if depreciation is not None else 0.0) + \
                                (amortization if amortization is not None else 0.0)

    ar_t0 = financials.get('ar_t0')
    inv_t0 = financials.get('inv_t0')
    ap_t0 = financials.get('ap_t0')
    ar_t1 = financials.get('ar_t1')
    inv_t1 = financials.get('inv_t1')
    ap_t1 = financials.get('ap_t1')

    wc_t0 = None
    if all(v is not None for v in [ar_t0, inv_t0, ap_t0]):
        wc_t0 = (ar_t0 or 0.0) + (inv_t0 or 0.0) - (ap_t0 or 0.0)
    
    wc_t1 = None
    if all(v is not None for v in [ar_t1, inv_t1, ap_t1]):
        wc_t1 = (ar_t1 or 0.0) + (inv_t1 or 0.0) - (ap_t1 or 0.0)
        
    delta_wc = 0.0 
    if wc_t0 is not None and wc_t1 is not None:
        delta_wc = wc_t0 - wc_t1 
        print(f"    (data_handler) 股票 {stock_code}: WC_T0={wc_t0:.2f}, WC_T-1={wc_t1:.2f}, ΔWC={delta_wc:.2f}")
    else:
        missing_wc_periods = []
        if wc_t0 is None: missing_wc_periods.append("T0")
        if wc_t1 is None: missing_wc_periods.append("T-1")
        print(f"    (data_handler) 警告：股票 {stock_code} 因缺少 {', '.join(missing_wc_periods)} 期的完整營運資本數據，無法計算精確ΔWC。將假設ΔWC為0。")

    net_borrowing = 0.0 
    net_capex = capex - depreciation_amortization
    
    if not isinstance(net_income_to_parent, (int, float)):
        print(f"    (data_handler) 警告：股票 {stock_code} 的淨利 (net_income_to_parent from {net_income_source_field}) 不是有效數字 ({net_income_to_parent})。無法計算 FCFE。")
        return {"stock_code": stock_code, "error": "淨利數據無效", "source_eps": current_eps_for_reference, "current_market_price": current_market_price, "net_income_source_field": net_income_source_field}

    fcfe = net_income_to_parent - net_capex - delta_wc + net_borrowing
    fcf_eps = fcfe / shares_outstanding
    
    print(f"    (data_handler) 股票 {stock_code}: NI(from {net_income_source_field})={net_income_to_parent:.0f}, Capex={capex:.0f}, D&A={depreciation_amortization:.0f}, NetCapex={net_capex:.0f}, ΔWC={delta_wc:.0f}, NetBorrowing={net_borrowing:.0f}")
    print(f"    (data_handler) 股票 {stock_code}: Calculated FCFE={fcfe:.0f}, FCF_EPS={fcf_eps:.4f}")
    
    short_term_growth_rate = context.get('dcf_short_term_growth_rate', 0.07) 
    projection_years = context.get('dcf_projection_years', 5) 
    terminal_growth_rate = context.get('dcf_terminal_growth_rate', 0.025) 
    
    if not isinstance(risk_preference, (int, float)) or risk_preference <= 0:
        print(f"    (data_handler) 警告：股票 {stock_code} 的風險偏好/折現率 ({risk_preference}) 無效。使用預設值 0.10。")
        discount_rate = 0.10
    else:
        discount_rate = risk_preference
        
    if not isinstance(terminal_growth_rate, (int, float)): 
        print(f"    (data_handler) 警告：股票 {stock_code} 的永續成長率 ({terminal_growth_rate}) 無效。使用預設值 0.025。")
        terminal_growth_rate = 0.025

    if discount_rate <= terminal_growth_rate: 
        print(f"    (data_handler) 警告：股票 {stock_code} 的折現率 ({discount_rate:.2%}) 不大於永續成長率 ({terminal_growth_rate:.2%})。調整永續成長率為折現率的90%。")
        new_terminal_growth_rate = discount_rate * 0.9 
        if new_terminal_growth_rate <= 0: new_terminal_growth_rate = 0.0001 
        elif new_terminal_growth_rate >= discount_rate: new_terminal_growth_rate = discount_rate * 0.99 
        terminal_growth_rate = new_terminal_growth_rate

    print(f"    (data_handler) 估值參數 for {stock_code}: FCF_EPS={fcf_eps:.2f}, g_short={short_term_growth_rate:.2%}, g_long={terminal_growth_rate:.2%}, r={discount_rate:.2%}, N={projection_years}")

    projected_fcf_present_values = []
    current_fcf = fcf_eps
    for i in range(1, projection_years + 1):
        current_fcf *= (1 + short_term_growth_rate)
        pv = current_fcf / ((1 + discount_rate) ** i)
        projected_fcf_present_values.append(pv)
    
    fcf_at_year_n_plus_1 = current_fcf * (1 + terminal_growth_rate)
    
    denominator = discount_rate - terminal_growth_rate
    if denominator == 0: 
        print(f"    (data_handler) 警告：股票 {stock_code} 的折現率等於永續成長率 (皆為 {discount_rate:.2%})，終值計算不穩定。使用FCF的20倍作為終值。")
        terminal_value_at_year_n = current_fcf * 20.0 
    elif denominator < 0:
        print(f"    (data_handler) 警告：股票 {stock_code} 的折現率 ({discount_rate:.2%}) 小於永續成長率 ({terminal_growth_rate:.2%})，終值計算無效。將終值設為0。")
        terminal_value_at_year_n = 0.0 
    else:
        terminal_value_at_year_n = fcf_at_year_n_plus_1 / denominator
        
    pv_terminal_value = terminal_value_at_year_n / ((1 + discount_rate) ** projection_years)
    
    intrinsic_value_per_share = sum(projected_fcf_present_values) + pv_terminal_value
    print(f"    (data_handler) 股票 {stock_code} 計算出的內在價值: {intrinsic_value_per_share:.2f}")

    potential_return = None
    if current_market_price is not None and isinstance(current_market_price, (int,float)) and current_market_price > 0 and isinstance(intrinsic_value_per_share, (int, float)):
        potential_return = (intrinsic_value_per_share / current_market_price) - 1
    
    data_year_quarter = financials.get('is_report_date', 'N/A') 
    if data_year_quarter == 'N/A' and financials.get('bs_report_date_t0'): 
        data_year_quarter = financials.get('bs_report_date_t0')
    if data_year_quarter == 'N/A' and financials.get('cf_report_date'): 
        data_year_quarter = financials.get('cf_report_date')

    return {
        "stock_code": stock_code,
        "intrinsic_value_per_share": round(intrinsic_value_per_share, 2) if isinstance(intrinsic_value_per_share, (int, float)) else None,
        "current_market_price": current_market_price,
        "potential_return": round(potential_return, 4) if potential_return is not None else None, 
        "data_year_quarter": data_year_quarter, 
        "source_eps": current_eps_for_reference, 
        "calculated_fcf_eps": round(fcf_eps, 2), 
        "used_discount_rate": discount_rate,
        "used_short_term_growth": short_term_growth_rate,
        "used_terminal_growth": terminal_growth_rate,
        "net_income_source_field": net_income_source_field
    }

def fetch_balance_sheet_items_from_downloaded(stock_code, api_suffix_for_bs_report, downloaded_balance_sheets): 
    print(f"  (data_handler) [TWSE API] 正在為股票代號 '{stock_code}' (API後綴: {api_suffix_for_bs_report}) 從已下載資產負債表中提取最新兩期數據...")
    
    statements_for_stock = []
    if not downloaded_balance_sheets:
        print(f"    (data_handler) [TWSE API] 警告：股票 '{stock_code}' の資產負債表數據集 (API後綴: {api_suffix_for_bs_report}) 為空。")
        return {"error": f"No balance sheets for {api_suffix_for_bs_report}"}

    for stmt in downloaded_balance_sheets:
        if stmt.get("公司代號") == stock_code:
            statements_for_stock.append(stmt)
    
    if not statements_for_stock:
        print(f"    (data_handler) [TWSE API] 警告：未在 API後綴 '{api_suffix_for_bs_report}' の資產負債表數據中找到股票代號 '{stock_code}' の記錄。")
        return {"error": f"Balance sheet data not found for {stock_code} in {api_suffix_for_bs_report} reports"}

    statements_for_stock.sort(key=lambda x: (x.get("年度", "0"), x.get("季別", "0")), reverse=True)

    def extract_items_from_statement(statement, field_map_bs, period_label):
        ar_field = field_map_bs.get("accounts_receivable", "應收票據及帳款淨額")
        inv_field = field_map_bs.get("inventories", "存貨")
        ap_field = field_map_bs.get("accounts_payable", "應付票據及帳款")
        accounts_receivable_str = statement.get(ar_field)
        inventories_str = statement.get(inv_field)
        accounts_payable_str = statement.get(ap_field)

        def safe_float_conversion(value_str, field_name_for_log):
            if value_str is None or str(value_str).strip() == "" or str(value_str).strip().lower() == "nan" or str(value_str).strip() == "---":
                return None
            try:
                return float(str(value_str).replace(",", ""))
            except ValueError:
                print(f"    (data_handler) [TWSE API] 警告：股票 '{stock_code}' ({period_label}) の資產負債表欄位 '{field_name_for_log}' 值 '{value_str}' 無法轉換為浮點數。")
                return None
        
        return {
            f"accounts_receivable_{period_label}": safe_float_conversion(accounts_receivable_str, ar_field),
            f"inventories_{period_label}": safe_float_conversion(inventories_str, inv_field),
            f"accounts_payable_{period_label}": safe_float_conversion(accounts_payable_str, ap_field),
            f"bs_year_{period_label}": statement.get("年度"),
            f"bs_quarter_{period_label}": statement.get("季別")
        }
        
    field_map_bs_to_use = BALANCE_SHEET_FIELD_NAMES_MAP.get(api_suffix_for_bs_report, BALANCE_SHEET_FIELD_NAMES_MAP.get(API_SUFFIX_GENERAL, {}))
    result_data = {"bs_report_api_suffix": api_suffix_for_bs_report}

    if len(statements_for_stock) > 0:
        latest_bs_statement_t0 = statements_for_stock[0]
        items_t0 = extract_items_from_statement(latest_bs_statement_t0, field_map_bs_to_use, "t0")
        result_data.update(items_t0)
        print(f"    (data_handler) [TWSE API] 為股票 '{stock_code}' 找到最新資產負債表 (T0: {result_data.get('bs_year_t0')}Q{result_data.get('bs_quarter_t0')}): AR={result_data.get('accounts_receivable_t0')}, INV={result_data.get('inventories_t0')}, AP={result_data.get('accounts_payable_t0')}")
    else: 
        return {"error": f"Unexpected: No statements found for {stock_code} after initial check."}

    if len(statements_for_stock) > 1:
        latest_bs_statement_t1 = statements_for_stock[1]
        items_t1 = extract_items_from_statement(latest_bs_statement_t1, field_map_bs_to_use, "t1")
        result_data.update(items_t1)
        print(f"    (data_handler) [TWSE API] 為股票 '{stock_code}' 找到前一期資產負債表 (T-1: {result_data.get('bs_year_t1')}Q{result_data.get('bs_quarter_t1')}): AR={result_data.get('accounts_receivable_t1')}, INV={result_data.get('inventories_t1')}, AP={result_data.get('accounts_payable_t1')}")
    else:
        print(f"    (data_handler) [TWSE API] 警告：股票 '{stock_code}' 只找到一期資產負債表數據，無法計算營運資本變動。")
        result_data.update({
            "accounts_receivable_t1": None, "inventories_t1": None, "accounts_payable_t1": None,
            "bs_year_t1": None, "bs_quarter_t1": None
        })
        
    return result_data
