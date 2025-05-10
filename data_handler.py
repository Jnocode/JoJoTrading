import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://openapi.twse.com.tw/v1/opendata"
INCOME_STATEMENT_API_PATH_PREFIX = "t187ap06_L"
BALANCE_SHEET_API_PATH_PREFIX = "t187ap07_L" # 資產負債表 API 路徑前綴

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
    # 其他行業別的資產負債表欄位可能不同，後續補充
    API_SUFFIX_FINANCIAL_HOLDING: { # 假設與一般業類似，需核實
        "accounts_receivable": "應收票據及帳款淨額", 
        "inventories": "存貨", # 金控業是否有存貨？需確認
        "accounts_payable": "應付票據及帳款"
    },
     API_SUFFIX_BANKING: { # 銀行業的資產負債表結構差異較大
        "accounts_receivable": "貼現及放款", # 銀行業的"應收款"可能是放款
        "inventories": None, # 銀行業通常沒有存貨
        "accounts_payable": "存款及匯款" # 銀行業的"應付款"可能是存款
    },
    # ... 其他行業別的映射 ...
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

def get_financial_reports_for_stock(stock_detail, context):
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
        print(f"  (data_handler) 股票 {stock_code_for_debug} ({stock_name}) 依特定規則 (ind:{industry_code}, rep_type:{report_type_code}) 使用 {report_name_for_log}")
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
            print(f"  (data_handler) 金融業公司 {stock_code_for_debug} ({company_full_name_str}) 未匹配特定子類關鍵字，使用產業預設 ({report_name_for_log})。")
    elif report_type_code == '2' and industry_code != "17": 
        print(f"  (data_handler) 非金融產業 {industry_code} 公司 {stock_code_for_debug} ({stock_name}) report_type '{report_type_code}' (個體財報)，使用其產業預設API ({report_name_for_log})。")
    
    api_url = f"{API_BASE_URL}/{INCOME_STATEMENT_API_PATH_PREFIX}{api_suffix}"
    context_key = f"financial_reports{api_suffix}"

    if context_key not in context or not context.get(context_key):
        print(f"  (data_handler) 正在獲取 {report_name_for_log} ({api_url}) 並存入 context['{context_key}']...")
        try:
            print(f"    (data_handler) 警告：將嘗試禁用 SSL 憑證驗證 (verify=False) 來獲取 {report_name_for_log}。")
            response = requests.get(api_url, timeout=30, verify=False)
            response.raise_for_status()
            context[context_key] = response.json()
            print(f"    (data_handler) 成功獲取 {len(context[context_key])} 筆 {report_name_for_log} 記錄。")
        except requests.exceptions.RequestException as e:
            print(f"    (data_handler) 獲取 {report_name_for_log} 時發生錯誤: {e}")
            context[context_key] = []
        except json.JSONDecodeError as e:
            print(f"    (data_handler) 解析 {report_name_for_log} JSON 時發生錯誤: {e}")
            context[context_key] = []
            
    return context.get(context_key, []), api_suffix

# 新增：獲取資產負債表數據的函式
def get_balance_sheet_data_for_stock(stock_detail, context):
    industry_code = stock_detail.get('industry_code')
    report_type_code = stock_detail.get('report_type') 
    stock_name = stock_detail.get('name', '') 
    company_full_name_str = stock_detail.get('full_name', stock_name) 
    stock_code_for_debug = stock_detail.get('code', 'N/A')

    # 沿用損益表的 API 後綴選擇邏輯，資產負債表通常與損益表使用相同的行業分類後綴
    # 但仍需注意，TWSE OpenAPI 是否為各行業提供獨立的資產負債表 API
    api_config = INDUSTRY_TO_API_INFO.get(industry_code, INDUSTRY_TO_API_INFO["DEFAULT"])
    api_suffix = api_config["income_suffix"] # 暫用 income_suffix, 後續可能需要 balance_sheet_suffix
    report_name_for_log = f"{api_config.get('report_name','一般業')}資產負債表"


    # 與 get_financial_reports_for_stock 類似的特殊行業判斷邏輯
    specific_config_key = (industry_code, report_type_code)
    if specific_config_key in SPECIFIC_REPORT_API_MAP: # 假設 SPECIFIC_REPORT_API_MAP 也適用於資產負債表
        api_config_bs = SPECIFIC_REPORT_API_MAP[specific_config_key]
        api_suffix = api_config_bs.get("balance_sheet_suffix", api_config_bs["income_suffix"]) # 優先用 bs_suffix
        report_name_for_log = api_config_bs.get("report_name_bs", f"{api_config_bs['report_name']}資產負債表")
        print(f"  (data_handler) 股票 {stock_code_for_debug} ({stock_name}) 依特定規則使用 {report_name_for_log} (資產負債表)")
    elif industry_code == "17": # 金融業特殊處理
        # ... (此處可複製或重構 get_financial_reports_for_stock 中金融業的判斷邏輯) ...
        # 簡化：暫時假設金融業也用其損益表的 API 後綴對應的資產負債表
        if "金融控股" in company_full_name_str or "金控" in stock_name:
            api_suffix = API_SUFFIX_FINANCIAL_HOLDING
            report_name_for_log = "金控業資產負債表"
        elif "證券" in company_full_name_str or "期貨" in company_full_name_str:
            api_suffix = API_SUFFIX_SECURITIES_FUTURES # 假設證券期貨業有對應的資產負債表後綴
            report_name_for_log = "證券期貨業資產負債表"
        elif "銀行" in company_full_name_str:
            api_suffix = API_SUFFIX_BANKING
            report_name_for_log = "銀行業資產負債表"
        elif "產險" in company_full_name_str or "產物保險" in company_full_name_str or "人壽" in company_full_name_str or "再保" in company_full_name_str:
            api_suffix = API_SUFFIX_INSURANCE # 假設保險業有對應的資產負債表後綴
            report_name_for_log = "保險業資產負債表"
        elif "票券" in company_full_name_str:
             api_suffix = API_SUFFIX_BANKING 
             report_name_for_log = "票券金融(用銀行API)資產負債表"
        else: 
            print(f"  (data_handler) 金融業公司 {stock_code_for_debug} ({company_full_name_str}) 未匹配特定子類關鍵字，使用產業預設 ({report_name_for_log}) (資產負債表)。")
    elif report_type_code == '2' and industry_code != "17": 
        print(f"  (data_handler) 非金融產業 {industry_code} 公司 {stock_code_for_debug} ({stock_name}) report_type '{report_type_code}' (個體財報)，使用其產業預設API ({report_name_for_log}) (資產負債表)。")

    api_url = f"{API_BASE_URL}/{BALANCE_SHEET_API_PATH_PREFIX}{api_suffix}"
    context_key = f"balance_sheet_reports{api_suffix}"

    if context_key not in context or not context.get(context_key):
        print(f"  (data_handler) 正在獲取 {report_name_for_log} ({api_url}) 並存入 context['{context_key}']...")
        try:
            print(f"    (data_handler) 警告：將嘗試禁用 SSL 憑證驗證 (verify=False) 來獲取 {report_name_for_log}。")
            response = requests.get(api_url, timeout=30, verify=False)
            response.raise_for_status()
            context[context_key] = response.json()
            print(f"    (data_handler) 成功獲取 {len(context[context_key])} 筆 {report_name_for_log} 記錄。")
        except requests.exceptions.RequestException as e:
            print(f"    (data_handler) 獲取 {report_name_for_log} 時發生錯誤: {e}")
            context[context_key] = []
        except json.JSONDecodeError as e:
            print(f"    (data_handler) 解析 {report_name_for_log} JSON 時發生錯誤: {e}")
            context[context_key] = []
            
    return context.get(context_key, []), api_suffix


def fetch_stock_financials_from_downloaded(stock_code, api_suffix_for_report, downloaded_financial_reports):
    print(f"  (data_handler) 正在為股票代號 '{stock_code}' (API後綴: {api_suffix_for_report}) 從已下載財報中提取數據...")
    latest_statement = None
    latest_year = "000"
    latest_quarter = "0"
    
    if not downloaded_financial_reports:
        print(f"    (data_handler) 警告：股票 '{stock_code}' 的財報數據集 (API後綴: {api_suffix_for_report}) 為空。")
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
            print(f"    (data_handler) 警告：股票 '{stock_code}' 的EPS '{eps_str}' (欄位: {eps_field_name}) 無法轉換為浮點數。")

        revenue = None
        try:
            if revenue_str is not None and str(revenue_str).strip() != "": revenue = float(revenue_str)
        except ValueError:
            print(f"    (data_handler) 警告：股票 '{stock_code}' 的營收 '{revenue_str}' (欄位: {revenue_field_name}) 無法轉換為浮點數。")
        
        net_income_to_parent = None
        try:
            if net_income_to_parent_val_str is not None and str(net_income_to_parent_val_str).strip() != "":
                net_income_to_parent = float(net_income_to_parent_val_str) * 1000 # 轉換為元
        except ValueError:
            print(f"    (data_handler) 警告：股票 '{stock_code}' 的淨利歸母 '{net_income_to_parent_val_str}' (欄位: {net_income_parent_field}) 無法轉換為浮點數。")
        
        # 營收也需要乘以1000，如果它是以千元為單位的話 (通常財報中的金額單位是一致的)
        if revenue is not None:
            revenue *= 1000

        print(f"    (data_handler) 為股票 '{stock_code}' 找到財報 (年度:{latest_year}, 季度:{latest_quarter}, API後綴:{api_suffix_for_report}): EPS={eps}, 營收(元)={revenue}, 淨利歸母(元)={net_income_to_parent}")
        return {"eps": eps, "revenue": revenue, "net_income_to_parent": net_income_to_parent, "year": latest_year, "quarter": latest_quarter, "report_api_suffix": api_suffix_for_report}
    else:
        print(f"    (data_handler) 警告：未在 API後綴 '{api_suffix_for_report}' 的財報數據中找到股票代號 '{stock_code}' 的記錄。")
        return {"eps": None, "revenue": None, "net_income_to_parent": None, "error": f"Data not found for {stock_code} in {api_suffix_for_report} reports"}

def _fetch_stock_financials_simulated(stock_detail): 
    stock_code = stock_detail.get("code", "N/A_sim")
    print(f"  (data_handler) 為股票 {stock_code} 返回預設模擬財務數據。")
    # 模擬數據應包含所有 calculate_dcf_valuation 需要的欄位
    return {
        "eps": stock_detail.get("sim_eps", 0.01), 
        "revenue": stock_detail.get("sim_revenue", 100000.0), 
        "net_income_to_parent": stock_detail.get("sim_net_income", 5000.0), 
        "shares_outstanding": stock_detail.get("sim_shares", 1000000.0),
        "current_market_price": stock_detail.get("sim_price", 100.0),
        "year": "sim", "quarter": "sim", "report_api_suffix": "_sim", "source": "simulated"
    }

def calculate_dcf_valuation(stock_code, financials, risk_preference, context):
    print(f"  (data_handler) 開始為股票 {stock_code} 進行 DCF 估值...")

    if financials.get("error"):
        print(f"    (data_handler) 股票 {stock_code} 缺少財務數據，無法估值: {financials['error']}")
        return {"stock_code": stock_code, "error": f"Missing financial data: {financials['error']}"}

    net_income_to_parent = financials.get("net_income_to_parent")
    shares_outstanding = financials.get("shares_outstanding") 
    current_eps_for_reference = financials.get("eps") 
    current_market_price = financials.get("current_market_price")

    required_fields_present = True
    missing_fields = []
    if net_income_to_parent is None:
        missing_fields.append("淨利歸母 (net_income_to_parent)")
        required_fields_present = False
    if shares_outstanding is None:
        missing_fields.append("流通股數 (shares_outstanding)")
        required_fields_present = False
    
    if not required_fields_present:
        error_msg = f"缺少必要數據: {', '.join(missing_fields)}，無法進行估值。"
        print(f"    (data_handler) 股票 {stock_code}: {error_msg}")
        return {"stock_code": stock_code, "error": error_msg, "source_eps": current_eps_for_reference, "current_market_price": current_market_price}

    if shares_outstanding == 0:
        print(f"    (data_handler) 股票 {stock_code} 的流通股數為0，無法計算每股價值。")
        return {"stock_code": stock_code, "error": "流通股數為0", "source_eps": current_eps_for_reference, "current_market_price": current_market_price}

    # 由於目前資產負債表API數據粒度不足，暫時無法精確計算營運資本變動。
    # 因此，FCFEps 的代理計算明確退回到基於「每股淨利」。
    fcf_eps = net_income_to_parent / shares_outstanding
    print(f"    (data_handler) 股票 {stock_code}: 使用簡化版 FCF_EPS (基於淨利/股數) = {fcf_eps:.4f}")
    
    short_term_growth_rate = context.get('dcf_short_term_growth_rate', 0.07) 
    projection_years = context.get('dcf_projection_years', 5) 
    terminal_growth_rate = context.get('dcf_terminal_growth_rate', 0.025) 
    discount_rate = risk_preference 
    
    if discount_rate <= terminal_growth_rate: 
        print(f"    (data_handler) 警告：股票 {stock_code} 的折現率 ({discount_rate:.2%}) 不大於永續成長率 ({terminal_growth_rate:.2%})。調整永續成長率為折現率的90%。")
        new_terminal_growth_rate = discount_rate * 0.9 
        if new_terminal_growth_rate <= 0: new_terminal_growth_rate = 0.0001 
        elif new_terminal_growth_rate >= discount_rate: new_terminal_growth_rate = discount_rate * 0.99 
        terminal_growth_rate = new_terminal_growth_rate

    print(f"    (data_handler) 估值參數 for {stock_code}: FCF_EPS (from NI/shares)={fcf_eps:.2f}, g_short={short_term_growth_rate:.2%}, g_long={terminal_growth_rate:.2%}, r={discount_rate:.2%}, N={projection_years}")

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
        terminal_value_at_year_n = current_fcf * 20 
    elif denominator < 0:
        print(f"    (data_handler) 警告：股票 {stock_code} 的折現率 ({discount_rate:.2%}) 小於永續成長率 ({terminal_growth_rate:.2%})，終值計算無效。將終值設為0。")
        terminal_value_at_year_n = 0 # 或返回錯誤
    else:
        terminal_value_at_year_n = fcf_at_year_n_plus_1 / denominator
        
    pv_terminal_value = terminal_value_at_year_n / ((1 + discount_rate) ** projection_years)
    
    intrinsic_value_per_share = sum(projected_fcf_present_values) + pv_terminal_value
    print(f"    (data_handler) 股票 {stock_code} 計算出的內在價值: {intrinsic_value_per_share:.2f}")

    potential_return = None
    if current_market_price is not None and current_market_price > 0 and isinstance(intrinsic_value_per_share, (int, float)):
        potential_return = (intrinsic_value_per_share / current_market_price) - 1
    
    return {
        "stock_code": stock_code,
        "intrinsic_value_per_share": round(intrinsic_value_per_share, 2) if isinstance(intrinsic_value_per_share, (int, float)) else None,
        "current_market_price": current_market_price,
        "potential_return": round(potential_return, 4) if potential_return is not None else None, 
        "data_year_quarter": f"{financials.get('year')}{financials.get('quarter')}",
        "source_eps": current_eps_for_reference, 
        "calculated_fcf_eps": round(fcf_eps, 2), 
        "used_discount_rate": discount_rate,
        "used_short_term_growth": short_term_growth_rate,
        "used_terminal_growth": terminal_growth_rate
    }

# 新增：從已下載的資產負債表中提取關鍵欄位 (嘗試獲取最新兩期)
def fetch_balance_sheet_items_from_downloaded(stock_code, api_suffix_for_bs_report, downloaded_balance_sheets):
    print(f"  (data_handler) 正在為股票代號 '{stock_code}' (API後綴: {api_suffix_for_bs_report}) 從已下載資產負債表中提取最新兩期數據...")
    
    statements_for_stock = []
    if not downloaded_balance_sheets:
        print(f"    (data_handler) 警告：股票 '{stock_code}' 的資產負債表數據集 (API後綴: {api_suffix_for_bs_report}) 為空。")
        return {"error": f"No balance sheets for {api_suffix_for_bs_report}"}

    for stmt in downloaded_balance_sheets:
        if stmt.get("公司代號") == stock_code:
            statements_for_stock.append(stmt)
    
    if not statements_for_stock:
        print(f"    (data_handler) 警告：未在 API後綴 '{api_suffix_for_bs_report}' 的資產負債表數據中找到股票代號 '{stock_code}' 的記錄。")
        return {"error": f"Balance sheet data not found for {stock_code} in {api_suffix_for_bs_report} reports"}

    # 按年度和季度排序，最新的在前
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
                print(f"    (data_handler) 警告：股票 '{stock_code}' ({period_label}) 的資產負債表欄位 '{field_name_for_log}' 值 '{value_str}' 無法轉換為浮點數。")
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
        print(f"    (data_handler) 為股票 '{stock_code}' 找到最新資產負債表 (T0: {result_data.get('bs_year_t0')}Q{result_data.get('bs_quarter_t0')}): AR={result_data.get('accounts_receivable_t0')}, INV={result_data.get('inventories_t0')}, AP={result_data.get('accounts_payable_t0')}")
    else: # 理論上不會執行到這裡，因為前面有檢查 statements_for_stock 是否為空
        return {"error": f"Unexpected: No statements found for {stock_code} after initial check."}

    if len(statements_for_stock) > 1:
        latest_bs_statement_t1 = statements_for_stock[1]
        items_t1 = extract_items_from_statement(latest_bs_statement_t1, field_map_bs_to_use, "t1")
        result_data.update(items_t1)
        print(f"    (data_handler) 為股票 '{stock_code}' 找到前一期資產負債表 (T-1: {result_data.get('bs_year_t1')}Q{result_data.get('bs_quarter_t1')}): AR={result_data.get('accounts_receivable_t1')}, INV={result_data.get('inventories_t1')}, AP={result_data.get('accounts_payable_t1')}")
    else:
        print(f"    (data_handler) 警告：股票 '{stock_code}' 只找到一期資產負債表數據，無法計算營運資本變動。")
        result_data.update({
            "accounts_receivable_t1": None, "inventories_t1": None, "accounts_payable_t1": None,
            "bs_year_t1": None, "bs_quarter_t1": None
        })
        
    return result_data
