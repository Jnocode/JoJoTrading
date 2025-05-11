import json
import os
import requests
from dotenv import load_dotenv
import pandas as pd # 新增
from FinMind.data import DataLoader # 新增

load_dotenv()

# FinMind API Token (可選，用於提高使用上限)
# 匿名用戶(token="") 每小時限制 300 次，註冊驗證後(有token) 每小時限制 600 次
FINMIND_API_TOKEN = os.getenv("FINMIND_API_TOKEN", "") # 從 .env 讀取或預設為空
finmind_api = DataLoader()
if FINMIND_API_TOKEN:
    try:
        finmind_api.login(token=FINMIND_API_TOKEN)
        print("  (data_handler) FinMind API token login successful.")
    except Exception as e:
        print(f"  (data_handler) FinMind API token login failed: {e}. Using anonymous access.")
else:
    print("  (data_handler) No FinMind API token found. Using anonymous access (300 requests/hr limit).")


# TWSE OpenAPI 相關設定 (目前可能部分不再主要使用，但保留)
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

# 資產負債表欄位名稱映射 (初步假設，可能需要根據實際 API 調整)
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
            response = requests.get(api_url, timeout=30, verify=False) # 實際的 requests.get
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
    """
    從 FinMind 獲取指定股票、起始日期、報表類型的財務報表數據。
    statement_type 可以是 'BalanceSheet', 'CashFlowsStatement', 'FinancialStatements' (綜合損益表)
    返回 Pandas DataFrame。
    """
    print(f"  (data_handler) Fetching FinMind {statement_type} for {stock_id} from {start_date}...")
    df = None
    try:
        if statement_type == 'BalanceSheet':
            df = finmind_api.taiwan_stock_balance_sheet(stock_id=stock_id, start_date=start_date)
        elif statement_type == 'CashFlowsStatement':
            df = finmind_api.taiwan_stock_cash_flows_statement(stock_id=stock_id, start_date=start_date)
        elif statement_type == 'FinancialStatements': # 綜合損益表
            df = finmind_api.taiwan_stock_financial_statement(stock_id=stock_id, start_date=start_date)
        else:
            print(f"    (data_handler) Unknown FinMind statement_type: {statement_type}")
            return pd.DataFrame()

        if df is not None and not df.empty:
            print(f"    (data_handler) Successfully fetched FinMind {statement_type} for {stock_id}. Shape: {df.shape}")
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(by='date', ascending=False)
            return df
        elif df is not None and df.empty:
            print(f"    (data_handler) Fetched FinMind {statement_type} for {stock_id}, but it's an empty DataFrame.")
            return pd.DataFrame()
        else:
            print(f"    (data_handler) Failed to fetch FinMind {statement_type} for {stock_id} (returned None).")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"    (data_handler) Error fetching FinMind {statement_type} for {stock_id}: {e}")
        return pd.DataFrame()

def extract_finmind_items(df: pd.DataFrame, target_items_map: dict, report_date_str: str = None):
    """
    從 FinMind 返回的 DataFrame (特定日期) 中提取目標會計科目的值。
    target_items_map: {'our_key_name': 'finmind_type_value', ...}
    report_date_str: 'YYYY-MM-DD', 如果為 None，則取 DataFrame 中最新的日期。
    """
    extracted_values = {key: None for key in target_items_map.keys()}
    if df.empty:
        extracted_values['report_date'] = None 
        return extracted_values

    target_date = None
    if report_date_str:
        try:
            target_date = pd.to_datetime(report_date_str)
        except ValueError:
            print(f"    (data_handler) Invalid report_date_str: {report_date_str}")
            extracted_values['report_date'] = None
            return extracted_values
        df_period = df[df['date'] == target_date].copy()
    else: 
        if df['date'].empty:
            print(f"    (data_handler) DataFrame has no 'date' column or is empty, cannot determine latest date.")
            extracted_values['report_date'] = None
            return extracted_values
        latest_date = df['date'].max()
        if pd.isna(latest_date):
             print(f"    (data_handler) Could not determine latest date from FinMind DataFrame (all dates are NaT).")
             extracted_values['report_date'] = None
             return extracted_values
        df_period = df[df['date'] == latest_date].copy()
        report_date_str = latest_date.strftime('%Y-%m-%d')

    if df_period.empty:
        print(f"    (data_handler) No data found for date {report_date_str} in FinMind DataFrame.")
        extracted_values['report_date'] = report_date_str if report_date_str else (latest_date.strftime('%Y-%m-%d') if 'latest_date' in locals() and pd.notna(latest_date) else None)
        return extracted_values
    
    df_period.set_index('type', inplace=True)
    
    for key, finmind_type in target_items_map.items():
        if finmind_type in df_period.index:
            value = df_period.loc[finmind_type, 'value']
            extracted_values[key] = float(value) if pd.notna(value) else None
        else:
            print(f"    (data_handler) FinMind type '{finmind_type}' for key '{key}' not found in report for {report_date_str}.")
            
    extracted_values['report_date'] = report_date_str
    return extracted_values

# --- End FinMind Data Fetching Functions ---


def fetch_stock_financials_from_downloaded(stock_code, api_suffix_for_report, downloaded_financial_reports): # 保留此函式以兼容舊的 TWSE API 邏輯 (如果需要)
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
                net_income_to_parent = float(net_income_to_parent_val_str) * 1000 # 轉換為元
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

def calculate_dcf_valuation(stock_code, financials, risk_preference, context):
    print(f"  (data_handler) 開始為股票 {stock_code} 進行 DCF 估值 (使用 FinMind 數據基礎)...")

    if financials.get("error"):
        error_message = financials['error']
        if error_message and all(e.strip().startswith("無法獲取") for e in error_message.split(';') if e.strip()):
             print(f"    (data_handler) 股票 {stock_code} 因 FinMind 資料獲取不完整 ({error_message.strip()})，無法進行精確 FCFE 估值。")
             return {"stock_code": stock_code, "error": f"FinMind 資料不完整: {error_message.strip()}", 
                     "source_eps": financials.get("eps_finmind"), "current_market_price": financials.get("current_market_price")}
        elif error_message: 
            print(f"    (data_handler) 股票 {stock_code} 缺少財務數據，無法估值: {error_message}")
            return {"stock_code": stock_code, "error": f"Missing financial data: {error_message}",
                     "source_eps": financials.get("eps_finmind"), "current_market_price": financials.get("current_market_price")}

    net_income_to_parent = financials.get("net_income_parent") 
    shares_outstanding = financials.get("shares_outstanding") 
    current_eps_for_reference = financials.get("eps_finmind") 
    current_market_price = financials.get("current_market_price")

    required_fields_for_fcfe = {
        "net_income_parent": net_income_to_parent,
        "shares_outstanding": shares_outstanding,
    }
    missing_core_fields = [k for k, v in required_fields_for_fcfe.items() if v is None]
    if missing_core_fields:
        error_msg = f"缺少核心數據: {', '.join(missing_core_fields)}，無法進行估值。"
        print(f"    (data_handler) 股票 {stock_code}: {error_msg}")
        return {"stock_code": stock_code, "error": error_msg, "source_eps": current_eps_for_reference, "current_market_price": current_market_price}

    if not isinstance(shares_outstanding, (int, float)) or shares_outstanding == 0:
        print(f"    (data_handler) 股票 {stock_code} 的流通股數無效或為0 ({shares_outstanding})，無法計算每股價值。")
        return {"stock_code": stock_code, "error": "流通股數無效或為0", "source_eps": current_eps_for_reference, "current_market_price": current_market_price}

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
        print(f"    (data_handler) 警告：股票 {stock_code} 的淨利 (net_income_to_parent) 不是有效數字 ({net_income_to_parent})。無法計算 FCFE。")
        return {"stock_code": stock_code, "error": "淨利數據無效", "source_eps": current_eps_for_reference, "current_market_price": current_market_price}

    fcfe = net_income_to_parent - net_capex - delta_wc + net_borrowing
    fcf_eps = fcfe / shares_outstanding
    
    print(f"    (data_handler) 股票 {stock_code}: NI={net_income_to_parent:.0f}, Capex={capex:.0f}, D&A={depreciation_amortization:.0f}, NetCapex={net_capex:.0f}, ΔWC={delta_wc:.0f}, NetBorrowing={net_borrowing:.0f}")
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
        "used_terminal_growth": terminal_growth_rate
    }

# 新增：從已下載的資產負債表中提取關鍵欄位 (嘗試獲取最新兩期)
def fetch_balance_sheet_items_from_downloaded(stock_code, api_suffix_for_bs_report, downloaded_balance_sheets): # TWSE API (舊，備用)
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
        # ... (此函式剩餘部分與 FinMind 版本中的類似輔助函式相同) ...
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
