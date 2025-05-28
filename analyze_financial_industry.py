import json

def analyze_financial_data(file_path="all_companies_basic_data.json"):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_companies = json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}")
        return
    except json.JSONDecodeError:
        print(f"錯誤：無法解析 JSON 檔案 {file_path}")
        return

    print(f"成功讀取 {len(all_companies)} 筆公司資料。\n")

    financial_industry_code = "17"
    
    print(f"--- 金融保險業 (產業代號 '{financial_industry_code}') 公司列表 ---")
    print("格式：公司代號 公司簡稱 (編制財務報表類型代號) -- 公司全名")
    print("-" * 60)

    financial_companies_count = 0
    for company in all_companies:
        industry_code = company.get("產業別", "").strip()
        if industry_code == financial_industry_code:
            financial_companies_count += 1
            company_code = company.get("公司代號", "N/A")
            company_short_name = company.get("公司簡稱", "N/A")
            report_type = company.get("編制財務報表類型", "N/A").strip()
            company_full_name = company.get("公司名稱", "N/A")
            print(f"{company_code} {company_short_name} (報表類型: {report_type}) -- {company_full_name}")
            
    if financial_companies_count == 0:
        print(f"未找到產業別為 '{financial_industry_code}' 的公司。")
    else:
        print(f"\n共找到 {financial_companies_count} 家金融保險業公司。")

if __name__ == "__main__":
    analyze_financial_data()
