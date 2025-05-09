import json
from collections import defaultdict

def analyze_data(file_path="all_companies_basic_data.json"):
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

    # --- 按產業別統計編制財務報表類型 ---
    industry_report_type_stats = defaultdict(lambda: defaultdict(list))
    all_report_types = set()

    for company in all_companies:
        industry_code = company.get("產業別", "未知產業").strip()
        report_type = company.get("編制財務報表類型", "未知類型").strip()
        company_name = company.get("公司簡稱", "N/A")
        company_code = company.get("公司代號", "N/A")

        industry_report_type_stats[industry_code][report_type].append(f"{company_code} {company_name}")
        all_report_types.add(report_type)

    print("--- 各產業別下的編制財務報表類型統計 ---")
    for ic, rt_stats in sorted(industry_report_type_stats.items()):
        print(f"\n產業別代號: '{ic}'")
        for rt, companies in rt_stats.items():
            print(f"  編制財務報表類型 '{rt}': 共 {len(companies)} 家")
            if companies:
                print(f"    範例公司 (最多3家): {', '.join(companies[:3])}")
    
    print(f"\n\n--- 所有出現過的「編制財務報表類型」代號 ---")
    print(sorted(list(all_report_types)))

    # --- 詳細列出金融保險業 (17) 的情況 ---
    print("\n\n--- 金融保險業 (產業代號 '17') 詳細列表 ---")
    financial_companies_found = False
    for company in all_companies:
        industry_code = company.get("產業別", "").strip()
        if industry_code == "17":
            financial_companies_found = True
            print(f"  公司: {company.get('公司代號')} {company.get('公司簡稱')}, "
                  f"產業別: {industry_code}, "
                  f"編制財務報表類型: '{company.get('編制財務報表類型', '').strip()}', "
                  f"公司全名: {company.get('公司名稱','')}")
    if not financial_companies_found:
        print("  未找到產業別為 '17' 的公司。")

    # --- 詳細列出「編制財務報表類型」非 '1' 的公司 ---
    print("\n\n--- 「編制財務報表類型」非 '1' 的公司詳細列表 ---")
    non_type_1_found = False
    for company in all_companies:
        report_type = company.get("編制財務報表類型", "").strip()
        if report_type != '1' and report_type != '': # 排除空值和 '1'
            non_type_1_found = True
            print(f"  公司: {company.get('公司代號')} {company.get('公司簡稱')}, "
                  f"產業別: {company.get('產業別', '').strip()}, "
                  f"編制財務報表類型: '{report_type}', "
                  f"公司全名: {company.get('公司名稱','')}")
    if not non_type_1_found:
        print("  所有公司 (有報表類型記錄的) 的編制財務報表類型皆為 '1' 或資料不完整。")

if __name__ == "__main__":
    analyze_data()
