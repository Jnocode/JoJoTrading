import shioaji as sj
import os
import time
from dotenv import load_dotenv

# --- Shioaji API 初始化與登入 ---
dotenv_path = os.path.join(os.path.dirname(__file__), 'credentials', '.env')
load_dotenv(dotenv_path=dotenv_path)
api = sj.Shioaji()
api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")
if not api_key or not secret_key:
    print("錯誤：找不到 API_KEY 或 SECRET_KEY。")
    exit()
try:
    api.login(api_key=api_key, secret_key=secret_key)
    print("Shioaji API 登入成功！")
except Exception as e:
    print(f"Shioaji API 登入失敗: {e}")
    exit()

# --- 回呼函式定義 ---
def unified_quote_callback(exchange, data):
    """統一處理行情的回呼函式"""
    print(f"收到行情: {data}") # 簡化輸出，先確認能收到東西
    # 後續再加入類型判斷
    # if hasattr(data, 'bid_price') and hasattr(data, 'ask_price'):
    #     print(f"五檔更新 - 代碼: {data.code}, 時間: {data.datetime}, 買一: {data.bid_price[0]}, 賣一: {data.ask_price[0]}")
    # elif hasattr(data, 'tick_type'):
    #      print(f"成交明細 - 代碼: {data.code}, 時間: {data.datetime}, 價格: {data.close}, 量: {data.volume}")
    # elif hasattr(data, 'close') and hasattr(data, 'volume'):
    #     print(f"報價更新 - 代碼: {data.code}, 時間: {data.datetime}, 成交價: {data.close}, 量: {data.volume}")
    # else:
    #     print(f"收到未知行情數據類型: {data}")

# --- 設定回呼函式 ---
try:
    api.quote.set_quote_callback(unified_quote_callback)
    print("已設定統一的行情回呼函式。")
except AttributeError:
    print("錯誤：無法設定 quote callback (api.quote.set_quote_callback 不存在?)")
    api.logout()
    exit()
except Exception as e:
    print(f"設定回呼函式時發生錯誤: {e}")
    api.logout()
    exit()


# --- 行情訂閱 ---
stock_contract_to_subscribe = None
try:
    print("正在下載所有可用合約...") # 修改提示訊息
    api.fetch_contracts() # 移除 contract_type 參數
    print("合約下載完成。") # 修改提示訊息

    # --- 嘗試獲取一個合約物件 ---
    # 這是最不確定的部分，需要根據實際 API 調整
    print("嘗試獲取合約物件...")
    # 可能性 1: 合約存在於 api.Contracts.STK (如果 Contracts 存在但 Stocks 不存在)
    if hasattr(api, 'Contracts') and hasattr(api.Contracts, 'STK') and api.Contracts.STK:
         print("嘗試從 api.Contracts.STK 獲取...")
         # 獲取第一個合約作為範例
         stock_contract_to_subscribe = next(iter(api.Contracts.STK.values()), None)
    # 可能性 2: 合約直接存在於 api.stk
    elif hasattr(api, 'stk') and api.stk:
         print("嘗試從 api.stk 獲取...")
         stock_contract_to_subscribe = next(iter(api.stk.values()), None)
    # 可能性 3: 需要使用 list_contracts 或類似方法
    elif hasattr(api, 'list_contracts'):
         print("嘗試使用 api.list_contracts()...")
         all_contracts = api.list_contracts(contract_type="STK")
         if all_contracts:
             stock_contract_to_subscribe = all_contracts[0] # 取第一個
         else:
             print("api.list_contracts() 未返回任何股票合約。")
    else:
        print("警告：無法找到已知的方法來獲取下載後的合約物件。")

    # --- 訂閱 ---
    if stock_contract_to_subscribe:
        contract_code = getattr(stock_contract_to_subscribe, 'code', 'N/A')
        contract_name = getattr(stock_contract_to_subscribe, 'name', 'N/A')
        print(f"找到合約: {contract_name} ({contract_code})")
        print(f"準備訂閱 {contract_code} 的行情 (Quote & BidAsk)...")

        # 訂閱報價 (Quote)
        api.quote.subscribe(
            stock_contract_to_subscribe,
            quote_type = sj.QuoteType.Quote,
        )
        print(f"已訂閱 {contract_code} 的即時報價 (Quote)。")

        # 訂閱五檔 (BidAsk)
        api.quote.subscribe(
            stock_contract_to_subscribe,
            quote_type = sj.QuoteType.BidAsk,
        )
        print(f"已訂閱 {contract_code} 的即時五檔 (BidAsk)。")

    else:
        print("錯誤：無法獲取任何股票合約物件進行訂閱。")
        api.logout()
        exit()

except AttributeError as ae:
     print(f"獲取或訂閱合約時發生屬性錯誤: {ae}")
     api.logout()
     exit()
except Exception as e:
    print(f"處理合約或訂閱行情時發生錯誤: {e}")
    api.logout()
    exit()

# --- 保持程式運行以接收行情 ---
print("程式運行中，按 Ctrl+C 結束...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n收到結束指令，正在取消訂閱並登出...")
    if stock_contract_to_subscribe: # 確保有合約才取消
        try:
            api.quote.unsubscribe(stock_contract_to_subscribe, quote_type=sj.QuoteType.Quote)
            api.quote.unsubscribe(stock_contract_to_subscribe, quote_type=sj.QuoteType.BidAsk)
        except Exception as unsub_e:
            print(f"取消訂閱時發生錯誤: {unsub_e}")
    api.logout()
    print("已登出 Shioaji API。")
except Exception as main_loop_e:
    print(f"主循環發生錯誤: {main_loop_e}")
    api.logout()
    print("已登出 Shioaji API。")
