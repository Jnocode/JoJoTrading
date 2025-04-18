"""
下載 Shioaji 股票合約資料並存成本地檔案（JSON/CSV）
請用 LIVE 模式執行，確保 .env 憑證正確
"""

import shioaji as sj
import os
import json
import csv
from dotenv import load_dotenv

def download_and_save_contracts(output_json="shioaji_stock_contracts.json", output_csv="shioaji_stock_contracts.csv"):
    # 載入憑證
    load_dotenv(os.path.join(os.path.dirname(__file__), "../credentials/.env"))
    api = sj.Shioaji()
    api.login(api_key=os.getenv("API_KEY"), secret_key=os.getenv("SECRET_KEY"))

    print("登入成功，下載股票合約...")
    contracts = list(api.Contracts.Stocks)
    print(f"共取得 {len(contracts)} 檔股票合約")

    # 整理資料
    contracts_data = []
    for c in contracts:
        try:
            contracts_data.append({
                "code": getattr(c, "code", ""),
                "name": getattr(c, "name", ""),
                "category": getattr(c, "category", ""),
                "exchange": getattr(c, "exchange", ""),
                "type": getattr(c, "type", ""),
            })
        except Exception as e:
            print(f"合約解析錯誤: {e}")

    # 存成 JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(contracts_data, f, ensure_ascii=False, indent=2)
    print(f"已存成 {output_json}")

    # 存成 CSV
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "name", "category", "exchange", "type"])
        writer.writeheader()
        for row in contracts_data:
            writer.writerow(row)
    print(f"已存成 {output_csv}")

if __name__ == "__main__":
    download_and_save_contracts()
