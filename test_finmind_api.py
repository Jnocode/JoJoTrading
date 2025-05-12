import os
import pandas as pd
from dotenv import load_dotenv
from FinMind.data import DataLoader

# Load environment variables from .env file
load_dotenv()

# Initialize FinMind DataLoader
FINMIND_USER_ID = os.getenv("FINMIND_USER_ID", "")
FINMIND_PASSWORD = os.getenv("FINMIND_PASSWORD", "")
FINMIND_API_TOKEN = os.getenv("FINMIND_API_TOKEN", "")

api = DataLoader()
login_successful = False

if FINMIND_USER_ID and FINMIND_PASSWORD:
    try:
        api.login(user_id=FINMIND_USER_ID, password=FINMIND_PASSWORD)
        print(f"Logged in to FinMind with User ID: {FINMIND_USER_ID}")
        login_successful = True
    except Exception as e:
        print(f"Failed to login with User ID/Password: {e}")
        if FINMIND_API_TOKEN:
            print("Attempting login with API Token...")
            try:
                api = DataLoader(token=FINMIND_API_TOKEN)
                # Test with a simple call if token login doesn't confirm itself
                api.taiwan_stock_info() 
                print("Logged in to FinMind with API Token.")
                login_successful = True
            except Exception as e_token:
                print(f"Failed to login with API Token: {e_token}")
                print("Proceeding with anonymous access.")
        else:
            print("No API Token found. Proceeding with anonymous access.")
elif FINMIND_API_TOKEN:
    print("Attempting login with API Token...")
    try:
        api = DataLoader(token=FINMIND_API_TOKEN)
        api.taiwan_stock_info()
        print("Logged in to FinMind with API Token.")
        login_successful = True
    except Exception as e_token:
        print(f"Failed to login with API Token: {e_token}")
        print("Proceeding with anonymous access.")
else:
    print("No credentials found. Proceeding with anonymous access.")

def get_financial_statement_fields(stock_ids, start_date="2022-01-01"):
    """
    Fetches the latest financial statement (綜合損益表) for given stock IDs
    and prints unique 'type' and 'origin_name' fields.
    """
    if not login_successful:
        print("\nWarning: Not logged in. API requests will be limited.")

    if isinstance(stock_ids, str):
        stock_ids = [stock_ids]

    for stock_id in stock_ids:
        print(f"\n--- Fields for Stock ID: {stock_id} (FinancialStatements) ---")
        try:
            df = api.taiwan_stock_financial_statement(stock_id=stock_id, start_date=start_date)
            if df is not None and not df.empty:
                # Ensure date column is datetime and sort to get the latest report easily
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(by='date', ascending=False)
                
                latest_report_date = df['date'].iloc[0]
                print(f"Latest report date for {stock_id}: {latest_report_date.strftime('%Y-%m-%d')}")
                
                df_latest = df[df['date'] == latest_report_date]
                
                unique_fields = df_latest[['type', 'origin_name']].drop_duplicates().reset_index(drop=True)
                print("Unique 'type' (FinMind Normalized) and 'origin_name' (Original Report Name):")
                for _, row in unique_fields.iterrows():
                    print(f"  Type: {row['type']:<50} Origin Name: {row['origin_name']}")
                
                # Specifically check for fields related to net income
                print("\n  Checking for common net income related fields:")
                common_income_fields = [
                    'EquityAttributableToOwnersOfParent', # 歸屬於母公司業主之權益
                    'ProfitLoss', # 本期淨利（淨損）
                    'NetIncome', # (Often a synonym or a more general term)
                    'IncomeAfterTax', # 稅後淨利
                    'ProfitLossFromContinuingOperations', # 繼續營業單位本期淨利（淨損）
                    'ComprehensiveIncomeAttributableToOwnersOfParent' # 歸屬於母公司業主之綜合損益總額
                ]
                for field_type in common_income_fields:
                    if field_type in unique_fields['type'].values:
                        value_row = df_latest[df_latest['type'] == field_type]
                        if not value_row.empty:
                             print(f"    Found '{field_type}': Value = {value_row['value'].iloc[0]}, Origin Name = '{value_row['origin_name'].iloc[0]}'")
                    else:
                        print(f"    '{field_type}' not found in this report's 'type' column.")

            else:
                print(f"No financial statement data found for {stock_id} from {start_date}.")
        except Exception as e:
            print(f"Error fetching financial statement for {stock_id}: {e}")

def get_cash_flows_statement_fields(stock_ids, start_date="2022-01-01"):
    """
    Fetches the latest cash flows statement for given stock IDs
    and prints unique 'type' and 'origin_name' fields.
    """
    if not login_successful:
        print("\nWarning: Not logged in. API requests will be limited.")

    if isinstance(stock_ids, str):
        stock_ids = [stock_ids]

    for stock_id in stock_ids:
        print(f"\n--- Fields for Stock ID: {stock_id} (CashFlowsStatement) ---")
        try:
            df = api.taiwan_stock_cash_flows_statement(stock_id=stock_id, start_date=start_date)
            if df is not None and not df.empty:
                # Ensure date column is datetime and sort to get the latest report easily
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(by='date', ascending=False)
                
                latest_report_date = df['date'].iloc[0]
                print(f"Latest report date for {stock_id}: {latest_report_date.strftime('%Y-%m-%d')}")
                
                df_latest = df[df['date'] == latest_report_date]
                
                unique_fields = df_latest[['type', 'origin_name']].drop_duplicates().reset_index(drop=True)
                print("Unique 'type' (FinMind Normalized) and 'origin_name' (Original Report Name):")
                for _, row in unique_fields.iterrows():
                    print(f"  Type: {row['type']:<50} Origin Name: {row['origin_name']}")
                
                # Specifically check for fields related to capex
                print("\n  Checking for common capex related fields:")
                common_capex_fields = [
                    'AcquisitionOfPropertyPlantAndEquipment', # 購置不動產、廠房及設備
                    'FixedAssetsPurchases', # 購置固定資產
                    'PurchaseOfPropertyPlantAndEquipment', # 購置不動產、廠房及設備
                    'CashOutflowForAcquisitionOfPropertyPlantAndEquipment', # 購置不動產、廠房及設備的現金流出
                    'IncreaseInPropertyPlantAndEquipment', # 不動產、廠房及設備的增加
                    'AcquisitionOfIntangibleAssetsOtherThanGoodwill', # 購置無形資產（不含商譽）
                    'CashOutflowForAcquisitionOfIntangibleAssets', # 購置無形資產的現金流出
                    'InvestmentInPropertyPlantAndEquipment', # 投資於不動產、廠房及設備
                    'PurchaseOfFixedAssets', # 購置固定資產
                    'PurchaseOfIntangibleAssets', # 購置無形資產
                    'CashSpentOnPropertyPlantAndEquipment', # 用於不動產、廠房及設備的現金支出
                    'CashSpentOnIntangibleAssets', # 用於無形資產的現金支出
                    'CapitalExpenditures', # 資本支出
                    'CapitalSpending', # 資本支出
                    'CapitalExpenditure', # 資本支出
                    'Capex', # 資本支出
                    'InvestmentInFixedAssets', # 投資於固定資產
                    'InvestmentInIntangibleAssets', # 投資於無形資產
                    'ExpenditureOnPropertyPlantAndEquipment', # 用於不動產、廠房及設備的支出
                    'ExpenditureOnIntangibleAssets', # 用於無形資產的支出
                    'PurchaseOfLongTermAssets', # 購置長期資產
                    'InvestmentInLongTermAssets', # 投資於長期資產
                    'CashSpentOnLongTermAssets', # 用於長期資產的現金支出
                    'ExpenditureOnLongTermAssets', # 用於長期資產的支出
                    'PurchaseOfCapitalAssets', # 購置資本資產
                    'InvestmentInCapitalAssets', # 投資於資本資產
                    'CashSpentOnCapitalAssets', # 用於資本資產的現金支出
                    'ExpenditureOnCapitalAssets', # 用於資本資產的支出
                    'PurchaseOfNonCurrentAssets', # 購置非流動資產
                    'InvestmentInNonCurrentAssets', # 投資於非流動資產
                    'CashSpentOnNonCurrentAssets', # 用於非流動資產的現金支出
                    'ExpenditureOnNonCurrentAssets', # 用於非流動資產的支出
                ]
                for field_type in common_capex_fields:
                    if field_type in unique_fields['type'].values:
                        value_row = df_latest[df_latest['type'] == field_type]
                        if not value_row.empty:
                            print(f"    Found '{field_type}': Value = {value_row['value'].iloc[0]}, Origin Name = '{value_row['origin_name'].iloc[0]}'")
                    else:
                        print(f"    '{field_type}' not found in this report's 'type' column.")

            else:
                print(f"No cash flows statement data found for {stock_id} from {start_date}.")
        except Exception as e:
            print(f"Error fetching cash flows statement for {stock_id}: {e}")

if __name__ == "__main__":
    # Example usage: Test a few stocks that previously had issues
    test_stock_ids = ["2314", "2330", "2317"] # 台揚, 台積電, 鴻海
    
    # Or prompt user for input
    # stock_input = input("Enter stock ID(s) to test, separated by comma (e.g., 2330,2317): ")
    # test_stock_ids = [s.strip() for s in stock_input.split(',')]
    
    if test_stock_ids and test_stock_ids[0]: # Check if not empty list or list with empty string
        get_financial_statement_fields(test_stock_ids)
        get_cash_flows_statement_fields(test_stock_ids)
    else:
        print("No stock IDs entered. Exiting.")

    # You can also test other FinMind functions here if needed
    # For example, to see all available datasets:
    # print(api.list_data_id(dataset="TaiwanStockInfo"))
    # print(api.get_dataset_info(dataset_name="TaiwanStockFinancialStatement"))
