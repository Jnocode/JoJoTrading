from enum import Enum, auto
import json
import os
from dotenv import load_dotenv
    # import requests # requests 的使用已移至 data_handler.py
from data_handler import (
    get_all_companies_basic_data,
    filter_industry_stocks,
    get_financial_reports_for_stock, 
    fetch_stock_financials_from_downloaded,
    _fetch_stock_financials_simulated, # 如果需要備援模擬
    calculate_dcf_valuation # 新增匯入
)

class JoJoState(Enum):
    CONFIG_LOAD = auto()
    UI_INIT = auto()
    INDUSTRY_PROCESS = auto()
    DATA_FETCH = auto()
    VALUATION = auto()
    FILTERING = auto()
    RESULTS_DISPLAY = auto()
    EXPORT = auto()
    ERROR = auto()
    END = auto() # 新增一個結束狀態

class BaseState:
    def execute(self, context):
        """
        執行此狀態的邏輯。
        應返回下一個狀態的 JoJoState 枚舉成員。
        context 是一個字典或物件，用於在狀態之間傳遞資料。
        """
        raise NotImplementedError("每個狀態都必須實現 execute 方法")

    def on_enter(self, context):
        """
        進入此狀態時執行的邏輯 (可選)。
        """
        print(f"Entering state: {self.__class__.__name__}")

    def on_exit(self, context):
        """
        離開此狀態時執行的邏輯 (可選)。
        """
        pass

# --- 狀態類別定義 (初步骨架) ---
class ConfigLoadState(BaseState):
    def execute(self, context):
        print("Executing ConfigLoadState: 載入設定檔...")
        try:
            # 載入 .env 檔案
            load_dotenv()
            # 這裡可以讀取環境變數，例如 API 金鑰
            # context['api_key_shioaji'] = os.getenv('SHIOAJI_API_KEY')
            # context['api_secret_shioaji'] = os.getenv('SHIOAJI_SECRET_KEY')
            # print("  .env 檔案已載入。")

            # 載入 industries.json
            config_file_path = 'industries.json'
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
                industries_data = app_config.get('industries', [])
                context['industries_full_data'] = industries_data # 儲存包含名稱和代號的完整列表
                context['industry_names'] = [item.get('name') for item in industries_data if item.get('name')] # 僅名稱列表，用於UI
                context['industry_name_to_code_map'] = {item.get('name'): item.get('code') for item in industries_data if item.get('name') and item.get('code')}
                
                context['default_risk_premium'] = app_config.get('default_risk_premium', 0.04)
                context['risk_premium_options'] = app_config.get('risk_premium_options', {})
                print(f"  {config_file_path} 已載入。")
                print(f"  偵測到產業數量: {len(context['industry_names'])}")
            else:
                print(f"  錯誤: {config_file_path} 找不到。將使用預設空值。")
                context['industries_full_data'] = []
                context['industry_names'] = []
                context['industry_name_to_code_map'] = {}
                context['default_risk_premium'] = 0.04
                context['risk_premium_options'] = {}
                # 也可以選擇在此處觸發錯誤狀態
                # context['error_message'] = f"{config_file_path} 找不到。"
                # return JoJoState.ERROR

            context['config_loaded'] = True
            print("ConfigLoadState 完成。")
            return JoJoState.UI_INIT
        except Exception as e:
            print(f"ConfigLoadState 執行時發生錯誤: {e}")
            context['error_message'] = f"設定檔載入失敗: {e}"
            context['config_loaded'] = False
            return JoJoState.ERROR

class UiInitState(BaseState):
    def execute(self, context):
        print("Executing UiInitState: 初始化 Streamlit UI...")
        # TODO: 實作 UI 初始化，等待使用者輸入
        # selected_industry_name 將由 app.py 中的 UI 設定到 context
        # risk_preference 也將由 app.py 中的 UI 設定到 context
        # 此處的範例值主要用於非 Streamlit 的簡易測試
        if 'selected_industry_name' not in context and context.get('industry_names'):
            context['selected_industry_name'] = context['industry_names'][0] # 預設選第一個
        if 'risk_preference' not in context:
            context['risk_preference'] = context.get('default_risk_premium', 0.04)
        
        # 這裡的邏輯會比較複雜，因為 Streamlit 是事件驅動的
        # 狀態機可能需要與 Streamlit 的 session state 互動
        # 暫時假設使用者已互動並觸發下一步
        if context.get('user_clicked_filter_button'): # 假設這個由 Streamlit callback 設定
            return JoJoState.INDUSTRY_PROCESS
        return JoJoState.UI_INIT # 保持在 UI 狀態等待互動

class IndustryProcessState(BaseState):
    def execute(self, context):
        print(f"Executing IndustryProcessState: 處理產業 '{context.get('selected_industry')}'...")
        # TODO: 根據選擇的產業進行初步處理 (如果需要)
        return JoJoState.DATA_FETCH

class DataFetchState(BaseState):
    # _get_all_companies_basic_data, _fetch_industry_stocks, _fetch_stock_financials
    # 這三個方法已移至 data_handler.py

    def execute(self, context):
        print("Executing DataFetchState: 抓取資料...")
        selected_industry_name = context.get('selected_industry_name')
        industry_name_to_code_map = context.get('industry_name_to_code_map', {})

        if not selected_industry_name:
            context['error_message'] = "未選擇產業"
            return JoJoState.ERROR

        try:
            # 0. 一次性獲取所有上市公司基本資料
            all_companies_data = get_all_companies_basic_data(context) # 使用匯入的函式
            if not all_companies_data:
                context['error_message'] = "無法獲取上市公司基本資料。"
                return JoJoState.ERROR

            print(f"  開始為產業 '{selected_industry_name}' 處理資料...")
            # 1. 從已下載的完整公司列表中篩選出特定產業的成分股詳細資訊
            industry_stocks_details = filter_industry_stocks(selected_industry_name, industry_name_to_code_map, all_companies_data) # 使用匯入的函式
            context['industry_stocks_details_list'] = industry_stocks_details
            
            context['industry_stocks_list'] = [f"{s['code']} {s['name']}" for s in industry_stocks_details]
            print(f"  篩選後成分股詳細列表 ({selected_industry_name}):")
            for stock_detail_debug in industry_stocks_details[:3]: 
                print(f"    {stock_detail_debug}")
            
            # 2. 為每個成分股提取財務數據
            all_financial_data = {}
            processed_report_types = set() # 用於記錄已下載過的報表類型，避免重複下載

            for stock_detail in industry_stocks_details: 
                stock_code = stock_detail['code']
                report_type = stock_detail['report_type']
                
                print(f"  準備為 {stock_code} ({stock_detail['name']}) 提取財報，其報表類型為: {report_type}")

                # 根據 report_type 獲取對應的財報數據集 (如果尚未下載)
                # get_financial_reports_for_stock 會處理下載並存入 context
                # TODO: data_handler.py 中的 get_financial_reports_for_stock 內的映射表和判斷邏輯仍需完善
                
                # 呼叫 data_handler 中的函式，它會返回財報數據和使用的api_suffix
                downloaded_reports, used_api_suffix = get_financial_reports_for_stock(stock_detail, context) # 修正呼叫的函式名稱，並傳入 stock_detail
                                
                if report_type not in processed_report_types and downloaded_reports: 
                    processed_report_types.add(report_type) # 或者用 used_api_suffix 做記錄
                
                financials = fetch_stock_financials_from_downloaded(stock_code, used_api_suffix, downloaded_reports)
                all_financial_data[stock_code] = financials
            
            context['financial_data'] = all_financial_data
            context['raw_data_fetched'] = True
            
            if industry_stocks_details:
                 print("  已嘗試為所有成分股提取財務數據。")
            else:
                print("  無成分股可供提取財務數據。")

            return JoJoState.VALUATION

        except Exception as e:
            print(f"DataFetchState 執行時發生錯誤: {e}")
            context['error_message'] = f"資料抓取失敗: {e}"
            return JoJoState.ERROR

class ValuationState(BaseState):
    def execute(self, context):
        print("Executing ValuationState: 進行 DCF 估值...")
        financial_data_map = context.get('financial_data', {})
        risk_preference = context.get('risk_preference', 0.04) # 使用預設值以防萬一
        
        valuation_results = []
        
        if not financial_data_map:
            print("  (ValuationState) 警告: financial_data 為空，無法進行估值。")
        
        for stock_code, financials in financial_data_map.items():
            print(f"  (ValuationState) 正在為股票 {stock_code} 進行估值...")
            if financials and not financials.get("error"):
                # 傳遞 stock_code, financials, risk_preference, 和完整的 context 給估值函式
                # context 可能包含 dcf_short_term_growth_rate 等參數
                valuation_result = calculate_dcf_valuation(stock_code, financials, risk_preference, context)
                valuation_results.append(valuation_result)
            else:
                print(f"  (ValuationState) 股票 {stock_code} 缺少有效的財務數據，跳過估值。錯誤: {financials.get('error', '未知數據問題')}")
                valuation_results.append({
                    "stock_code": stock_code,
                    "error": financials.get("error", "財務數據不足或錯誤，無法估值")
                })
        
        context['valuation_results'] = valuation_results
        context['valuation_completed'] = True
        print(f"ValuationState 完成，共處理 {len(valuation_results)} 筆估值結果。")
        return JoJoState.FILTERING

class FilteringState(BaseState):
    def execute(self, context):
        print("Executing FilteringState: 篩選股票...")
        # TODO: 實作基於估值結果的篩選邏輯
        context['filtered_stocks'] = ["股票A", "股票B"] # 範例
        return JoJoState.RESULTS_DISPLAY

class ResultsDisplayState(BaseState):
    def execute(self, context):
        print(f"Executing ResultsDisplayState: 顯示結果 {context.get('filtered_stocks')}...")
        # TODO: 在 Streamlit UI 上顯示結果
        # 假設使用者選擇匯出或新查詢
        if context.get('user_clicked_export_button'):
            return JoJoState.EXPORT
        elif context.get('user_clicked_new_query_button'):
            return JoJoState.UI_INIT
        return JoJoState.RESULTS_DISPLAY # 保持顯示，或設定超時返回 UI_INIT

class ExportState(BaseState):
    def execute(self, context):
        print("Executing ExportState: 匯出結果...")
        # TODO: 實作匯出邏輯
        context['export_completed'] = True
        # 匯出後通常返回結果顯示或初始UI
        return JoJoState.RESULTS_DISPLAY 

class ErrorState(BaseState):
    def execute(self, context):
        error_msg = context.get('error_message', "發生未知錯誤")
        print(f"Executing ErrorState: {error_msg}")
        # TODO: 在 UI 上顯示錯誤訊息
        # 這裡可以決定是結束還是返回初始狀態
        return JoJoState.UI_INIT # 例如，讓使用者可以重試

class EndState(BaseState):
    def execute(self, context):
        print("Executing EndState: 流程結束。")
        return JoJoState.END # 保持在結束狀態

# --- 主狀態機 ---
class JoJoStateMachine:
    def __init__(self):
        self.current_jojo_state_enum = JoJoState.CONFIG_LOAD
        self.context = {} # 用於在狀態間傳遞資料
        self.states = {
            JoJoState.CONFIG_LOAD: ConfigLoadState(),
            JoJoState.UI_INIT: UiInitState(),
            JoJoState.INDUSTRY_PROCESS: IndustryProcessState(),
            JoJoState.DATA_FETCH: DataFetchState(),
            JoJoState.VALUATION: ValuationState(),
            JoJoState.FILTERING: FilteringState(),
            JoJoState.RESULTS_DISPLAY: ResultsDisplayState(),
            JoJoState.EXPORT: ExportState(),
            JoJoState.ERROR: ErrorState(),
            JoJoState.END: EndState()
        }
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5

    def run(self):
        """
        執行狀態機。
        注意：對於 Streamlit 這種 Web UI，狀態機的驅動方式可能需要調整，
        例如，每次使用者互動後執行一次狀態轉換，而不是一個連續的 while 迴圈。
        這裡的 run 方法是一個簡化的示意。
        """
        while self.current_jojo_state_enum != JoJoState.END:
            current_state_obj = self.states.get(self.current_jojo_state_enum)
            if not current_state_obj:
                print(f"錯誤：找不到狀態 {self.current_jojo_state_enum} 的對應物件。")
                self.context['error_message'] = f"無效狀態: {self.current_jojo_state_enum}"
                self.current_jojo_state_enum = JoJoState.ERROR
                continue

            try:
                current_state_obj.on_enter(self.context)
                next_state_enum = current_state_obj.execute(self.context)
                current_state_obj.on_exit(self.context)
                
                if next_state_enum == self.current_jojo_state_enum and next_state_enum not in [JoJoState.UI_INIT, JoJoState.RESULTS_DISPLAY]:
                    # 避免在非互動等待狀態下死循環，如果狀態未改變且不是等待使用者輸入的狀態
                    # 這裡的判斷可能需要根據實際情況調整
                    print(f"警告：狀態 {self.current_jojo_state_enum} 執行後未改變，可能導致死循環。")
                    self.consecutive_failures +=1
                else:
                    self.consecutive_failures = 0

                self.current_jojo_state_enum = next_state_enum

            except Exception as e:
                print(f"狀態 {self.current_jojo_state_enum} 執行時發生錯誤: {e}")
                self.context['error_message'] = str(e)
                self.current_jojo_state_enum = JoJoState.ERROR
                self.consecutive_failures += 1
            
            if self.consecutive_failures >= self.max_consecutive_failures:
                print(f"連續 {self.max_consecutive_failures} 次失敗，狀態機停止。")
                self.current_jojo_state_enum = JoJoState.END # 強制結束

        # 最終結束狀態的處理
        final_state_obj = self.states.get(JoJoState.END)
        if final_state_obj:
            final_state_obj.on_enter(self.context)
            final_state_obj.execute(self.context)
        print("JoJoTrading State Machine 已停止。")

if __name__ == "__main__":
    # 簡易測試 (非 Streamlit 環境)
    print("開始 JoJoStateMachine 簡易測試...")
    machine = JoJoStateMachine()
    
    # 模擬 Streamlit UI 互動觸發
    # 第一次執行到 UI_INIT 後會停在那裡，因為 run 假設是連續的
    # 為了測試，我們手動推進一下
    
    # 初始執行，應該會停在 UI_INIT 等待 'user_clicked_filter_button'
    # machine.run() # 如果直接跑，會因為 UI_INIT 一直返回自身而可能觸發死循環警告
    
    # 讓我們模擬一個完整的流程
    machine.context['user_clicked_filter_button'] = False
    machine.context['user_clicked_export_button'] = False
    machine.context['user_clicked_new_query_button'] = False

    # 1. Config Load -> UI Init
    machine.current_jojo_state_enum = JoJoState.CONFIG_LOAD
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")

    # 2. UI Init (假設使用者點擊了篩選)
    machine.context['user_clicked_filter_button'] = True
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")
    machine.context['user_clicked_filter_button'] = False # 重置

    # 3. Industry Process -> Data Fetch
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")

    # 4. Data Fetch -> Valuation
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")

    # 5. Valuation -> Filtering
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")

    # 6. Filtering -> Results Display
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")
    
    # 7. Results Display (假設使用者點擊匯出)
    machine.context['user_clicked_export_button'] = True
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")
    machine.context['user_clicked_export_button'] = False # 重置

    # 8. Export -> Results Display
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")

    # 9. Results Display (假設使用者點擊新查詢)
    machine.context['user_clicked_new_query_button'] = True
    current_state = machine.states[machine.current_jojo_state_enum]
    machine.current_jojo_state_enum = current_state.execute(machine.context)
    print(f"  -> 轉換到狀態: {machine.current_jojo_state_enum}")
    machine.context['user_clicked_new_query_button'] = False # 重置

    print("JoJoStateMachine 簡易測試結束。")
    print("注意：實際 Streamlit 應用中，狀態機的驅動方式會不同。")
