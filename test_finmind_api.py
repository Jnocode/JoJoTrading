import pandas as pd
from FinMind.data import DataLoader

# FinMind API token (如果需要，請替換成您的 token)
# 根據文件，未驗證信箱 token 為 ""，驗證後可至官網個人頁面複製 token
# 匿名用戶(token="") 每小時限制 300 次，註冊驗證後(有token) 每小時限制 600 次
FINMIND_API_TOKEN = "" 

# 股票代號和日期 (範例)
STOCK_ID = "2330" # 台積電
START_DATE = "2022-01-01" # 可以嘗試獲取一個較近的年份開始的數據
# 如果只想獲取最新一期，FinMind 的 date 參數可能可以直接用 YYYY-MM-DD，它會找該日期前的最新財報
# 或者，如果 FinMind 的 API 設計是按期別（如 YYYYQ1）獲取，則需要查閱其具體用法
# 暫時先用一個起始日期，看它返回什麼

api = DataLoader()
if FINMIND_API_TOKEN:
    api.login(token=FINMIND_API_TOKEN) # 如果有 token，則登入

def fetch_and_print_statement(dataset_name, stock_id, start_date):
    print(f"\n--- Fetching {dataset_name} for {stock_id} from {start_date} ---")
    try:
        # 嘗試獲取從 start_date 到最新的數據
        # FinMind 的 Load.FinData() 似乎已棄用，新版建議用 DataLoader().taiwan_stock_financial_statement() 等
        # 但我們先基於之前看到的 Load.FinData 範例來嘗試，如果不行再調整
        # 或者直接使用更底層的 api.get_data 功能
        
        # 根據 FinMind GitHub 上的說明，獲取財務報表更推薦的方式是使用 DataLoader 的特定方法
        # 例如：api.taiwan_stock_financial_statement(stock_id=stock_id, start_date=start_date, statement_type='BalanceSheet')
        # 但 dataset 名稱仍然是關鍵。
        # 我們先用通用的 data 方法，並嘗試推測的 dataset 名稱

        # 查閱 FinMind 文件，dataset 名稱似乎是:
        # 'TaiwanStockBalanceSheet', 'TaiwanStockCashFlowsStatement', 'TaiwanStockFinancialStatements' (綜合損益)
        # 或者有時文件會用 'BalanceSheet', 'CashFlowStatement', 'FinancialStatements' (不帶 TaiwanStock 前綴)
        
        # 為了更準確，我們應該使用 FinMind 提供的特定函式（如果存在）
        # 根據 FinMind/data/finmind_api.py 原始碼，有 taiwan_stock_balance_sheet, taiwan_stock_cash_flows_statement, taiwan_stock_financial_statement
        
        df = None
        if dataset_name == 'TaiwanStockBalanceSheet':
            df = api.taiwan_stock_balance_sheet(stock_id=stock_id, start_date=start_date)
        elif dataset_name == 'TaiwanStockCashFlowsStatement':
            df = api.taiwan_stock_cash_flows_statement(stock_id=stock_id, start_date=start_date)
        elif dataset_name == 'TaiwanStockFinancialStatement': # 這是綜合損益表
            df = api.taiwan_stock_financial_statement(stock_id=stock_id, start_date=start_date)
        else:
            print(f"Dataset name '{dataset_name}' not specifically handled by a direct function.")
            # 後備：嘗試通用 data 方法 (如果上述特定函式不存在或想用通用方法)
            # df = api.get_data(dataset=dataset_name, data_id=stock_id, start_date=start_date)


        if df is not None and not df.empty:
            print(f"Successfully fetched {dataset_name}.")
            print("Columns:", df.columns.tolist())
            print("Head:\n", df.head().to_string()) # 使用 to_string() 避免截斷
            
            print("\nUnique 'type' and 'origin_name' combinations:")
            if 'type' in df.columns and 'origin_name' in df.columns:
                unique_types = df[['type', 'origin_name']].drop_duplicates().sort_values(by='type')
                for index, row in unique_types.iterrows():
                    print(f"  type: {row['type']:<60} origin_name: {row['origin_name']}")
            else:
                print("  'type' or 'origin_name' column not found in DataFrame.")

        elif df is not None and df.empty:
            print(f"Fetched {dataset_name}, but it's an empty DataFrame.")
        else:
            print(f"Failed to fetch {dataset_name} or no specific function was called.")
            
    except Exception as e:
        print(f"Error fetching {dataset_name}: {e}")

if __name__ == "__main__":
    # 測試獲取資產負債表
    fetch_and_print_statement(dataset_name='TaiwanStockBalanceSheet', stock_id=STOCK_ID, start_date=START_DATE)
    
    # 測試獲取現金流量表
    fetch_and_print_statement(dataset_name='TaiwanStockCashFlowsStatement', stock_id=STOCK_ID, start_date=START_DATE)

    # 測試獲取綜合損益表 (可以和我們現有的 TWSE API 結果比較)
    fetch_and_print_statement(dataset_name='TaiwanStockFinancialStatement', stock_id=STOCK_ID, start_date=START_DATE)

    print("\n--- FinMind API Test Script Finished ---")
    print("Please check the output above for column names and sample data.")
    print("You might need to adjust the 'required_cols' in the script based on actual FinMind output.")
    print("Also, check if a FinMind API token is required for more frequent access or for certain datasets.")
