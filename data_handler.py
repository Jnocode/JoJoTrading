import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

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
    API_SUFFIX_GENERAL: {"eps": "基本每股盈餘（元）", "revenue": "營業收入"},
    API_SUFFIX_FINANCIAL_HOLDING: {"eps": "基本每股盈餘（元）", "revenue": "淨收益"},
    API_SUFFIX_SECURITIES_FUTURES: {"eps": "基本每股盈餘（元）", "revenue": "收益"},
    API_SUFFIX_INSURANCE: {"eps": "基本每股盈餘（元）", "revenue": "營業收入"},
    API_SUFFIX_BANKING: {"eps": "基本每股盈餘（元）", "revenue": "利息淨收益"},
    API_SUFFIX_OTHER_INDUSTRY: {"eps": "基本每股盈餘（元）", "revenue": "收入"},
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
            
            if stock_code and stock_name:
                industry_stocks_details_list.append({
                    "code": stock_code,
                    "name": stock_name,
                    "full_name": company_full_name_str, 
                    "report_type": report_type.strip(),
                    "industry_code": api_industry_code_val.strip() 
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

def fetch_stock_financials_from_downloaded(stock_code, api_suffix_for_report, downloaded_financial_reports):
    print(f"  (data_handler) 正在為股票代號 '{stock_code}' (API後綴: {api_suffix_for_report}) 從已下載財報中提取數據...")
    latest_statement = None
    latest_year = "000"
    latest_quarter = "0"

    if not downloaded_financial_reports:
        print(f"    (data_handler) 警告：股票 '{stock_code}' 的財報數據集 (API後綴: {api_suffix_for_report}) 為空。")
        return {"eps": None, "revenue": None, "error": f"No income statements for {api_suffix_for_report}"}

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

        eps_str = latest_statement.get(eps_field_name)
        revenue_str = latest_statement.get(revenue_field_name)
        
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

        print(f"    (data_handler) 為股票 '{stock_code}' 找到財報 (年度:{latest_year}, 季度:{latest_quarter}, API後綴:{api_suffix_for_report}): EPS={eps}, 營收={revenue}")
        return {"eps": eps, "revenue": revenue, "year": latest_year, "quarter": latest_quarter, "report_api_suffix": api_suffix_for_report}
    else:
        print(f"    (data_handler) 警告：未在 API後綴 '{api_suffix_for_report}' 的財報數據中找到股票代號 '{stock_code}' 的記錄。")
        return {"eps": None, "revenue": None, "error": f"Data not found for {stock_code} in {api_suffix_for_report} reports"}

def _fetch_stock_financials_simulated(stock_code_name_unused):
    return {"eps": 0.01, "roe": 0.01, "revenue_growth": 0.01, "source": "simulated"}

def calculate_dcf_valuation(stock_code, financials, risk_preference, context):
    """
    執行簡化版 DCF 估值。
    financials: 包含 'eps', 'revenue', 'year', 'quarter', 'report_api_suffix' 的字典
    risk_preference: 使用者選擇的風險補償或折現率相關參數
    context: 狀態機的上下文，可能包含其他全局參數
    返回: 包含估值結果的字典，例如 {"intrinsic_value_per_share": X, "potential_return": Y}
          或 {"error": "訊息"}
    """
    print(f"  (data_handler) 開始為股票 {stock_code} 進行 DCF 估值...")

    if financials.get("error"):
        print(f"    (data_handler) 股票 {stock_code} 缺少財務數據，無法估值: {financials['error']}")
        return {"error": f"Missing financial data: {financials['error']}"}

    current_eps = financials.get("eps")
    # TODO: 需要獲取股票的總股數來從總營收推算每股營收，或直接獲取每股營收
    # current_revenue_per_share = ... 
    # 假設我們暫時用 EPS 作為 FCF 的代理

    if current_eps is None: # 或其他必要數據為 None
        print(f"    (data_handler) 股票 {stock_code} 的 EPS 為空，無法進行簡化估值。")
        return {"error": "EPS is None, cannot perform simplified valuation."}

    # 簡化假設：
    # 1. FCF per share (FCFEps) 約等於 EPS (這是一個非常粗略的假設)
    fcf_eps = current_eps
    # 2. 短期成長率 (例如，未來5年) - 需要更合理的估計方法
    #    可以基於歷史成長、分析師預估，或產業平均。暫時固定。
    short_term_growth_rate = context.get('dcf_short_term_growth_rate', 0.07) # 預設7%
    projection_years = context.get('dcf_projection_years', 5) # 預估5年
    # 3. 長期永續成長率 (Terminal Growth Rate)
    terminal_growth_rate = context.get('dcf_terminal_growth_rate', 0.025) # 預設2.5%
    # 4. 折現率 (Discount Rate / Required Rate of Return)
    #    直接使用使用者選擇的 risk_preference 作為折現率 (這也是簡化)
    #    更複雜的 WACC 計算需要 Beta, 無風險利率, 市場風險溢價等
    discount_rate = risk_preference 
    if discount_rate <= terminal_growth_rate: # 折現率必須大於永續成長率
        print(f"    (data_handler) 警告：股票 {stock_code} 的折現率 ({discount_rate}) 不大於永續成長率 ({terminal_growth_rate})。調整永續成長率為折現率的90%。")
        terminal_growth_rate = discount_rate * 0.9 
        if terminal_growth_rate < 0: terminal_growth_rate = 0 # 避免負成長

    print(f"    (data_handler) 估值參數 for {stock_code}: FCF_EPS (proxy)={fcf_eps:.2f}, g_short={short_term_growth_rate:.2%}, g_long={terminal_growth_rate:.2%}, r={discount_rate:.2%}, N={projection_years}")

    # 計算未來幾年的預期 FCF_EPS 並折現
    projected_fcf_present_values = []
    current_fcf = fcf_eps
    for i in range(1, projection_years + 1):
        current_fcf *= (1 + short_term_growth_rate)
        pv = current_fcf / ((1 + discount_rate) ** i)
        projected_fcf_present_values.append(pv)
        # print(f"      Year {i}: FCF_EPS={current_fcf:.2f}, PV={pv:.2f}")

    # 計算終值 (Terminal Value) 並折現
    # FCF_N+1 = FCF_N * (1 + g_long)
    # Terminal Value at year N = FCF_N+1 / (r - g_long)
    fcf_at_year_n_plus_1 = current_fcf * (1 + terminal_growth_rate)
    terminal_value_at_year_n = fcf_at_year_n_plus_1 / (discount_rate - terminal_growth_rate)
    pv_terminal_value = terminal_value_at_year_n / ((1 + discount_rate) ** projection_years)
    # print(f"      Terminal Value (at year {projection_years}): {terminal_value_at_year_n:.2f}, PV of Terminal Value: {pv_terminal_value:.2f}")
    
    # 計算內在價值
    intrinsic_value_per_share = sum(projected_fcf_present_values) + pv_terminal_value
    print(f"    (data_handler) 股票 {stock_code} 計算出的內在價值: {intrinsic_value_per_share:.2f}")

    # TODO: 需要獲取目前股價來計算潛在報酬率
    # current_market_price = get_current_market_price(stock_code, context) 
    # potential_return = (intrinsic_value_per_share / current_market_price) - 1 if current_market_price else None
    # 暫時不計算潛在報酬

    return {
        "stock_code": stock_code,
        "intrinsic_value_per_share": round(intrinsic_value_per_share, 2),
        "potential_return": None, # 待實現
        "data_year_quarter": f"{financials.get('year')}{financials.get('quarter')}",
        "source_eps": current_eps,
        "used_discount_rate": discount_rate,
        "used_short_term_growth": short_term_growth_rate,
        "used_terminal_growth": terminal_growth_rate
    }
