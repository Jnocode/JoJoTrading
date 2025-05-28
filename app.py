# app.py (Streamlit 主應用程式檔案)
import streamlit as st
import pandas as pd # Import pandas
from jojo_state_machine import JoJoStateMachine, JoJoState, State # 確保 State 也導入了 (原 BaseState)
from modules.i18n import t

# --- Helper function to drive state machine ---
def drive_state_machine(machine, target_state=None):
    """
    驅動狀態機直到達到目標狀態或某個等待輸入的狀態。
    如果 target_state 是 None，則執行一步。
    """
    if not machine:
        return

    # 獲取當前狀態的處理物件
    # current_state_handler = machine.states.get(machine.current_state) # 假設 machine.states 存在且是字典
    # 直接在狀態機內部處理狀態對應的執行邏輯，app.py 只調用 machine.execute_state() 或 machine.transition_to()
    # 為了保持現有結構，我們假設 machine.execute_state() 會處理當前狀態的執行
    # 但 drive_state_machine 的設計似乎是外部驅動，這與 JoJoStateMachine 內部的 self.execute_state() 有點衝突
    # 暫時保留 drive_state_machine 的邏輯，但理想情況下應由 JoJoStateMachine 內部管理狀態執行
    
    # 由於 JoJoStateMachine 的 execute_state 已經處理了當前狀態的執行，
    # drive_state_machine 的主要職責應該是觸發狀態機的執行，而不是自己去查找和執行狀態處理器。
    # 但為了最小化修改，我們先修正 current_jojo_state_enum -> current_state
    
    # 獲取當前狀態的處理物件 - 這部分邏輯應該在 JoJoStateMachine 內部
    # current_state_handler = machine.states.get(machine.current_state) 
    # if not current_state_handler:
    #     st.error(f"錯誤：無效的狀態 {machine.current_state}")
    #     machine.current_state = JoJoState.ERROR 
    #     machine.context['error_message'] = f"無效狀態: {machine.current_state}"
    #     return

    try:
        # machine.execute_state() # 讓狀態機自己執行當前狀態
        # 為了保持 drive_state_machine 的現有結構，我們假設它仍然需要知道下一個狀態
        # 但這與 JoJoStateMachine 的 transition_to 和 execute_state 的耦合較高
        # 這裡的 next_state_enum 應該由 machine.execute_state() 返回或通過某種方式獲取
        # 假設 JoJoStateMachine 的 execute_state 返回下一個狀態（如果有的話）
        
        # 簡化：drive_state_machine 的目的是觸發一次狀態執行，狀態轉換由狀態機內部處理
        # machine.execute_state() # 這一行會執行當前狀態的邏輯，並可能在內部調用 transition_to
        
        # 如果 drive_state_machine 的目的是外部控制轉換，那麼它需要知道 execute 的結果
        # 假設 JoJoStateMachine 的 execute_state 方法（或其調用的具體 State 的 execute）
        # 不直接返回 next_state，而是通過 machine.transition_to() 改變 machine.current_state
        # 因此，drive_state_machine 執行後，machine.current_state 就已經是新狀態了。
        
        # 為了修復 AttributeError，我們將 current_jojo_state_enum 改為 current_state
        # 但這揭示了 drive_state_machine 和 JoJoStateMachine 之間職責劃分的問題
        
        # 假設 JoJoStateMachine 的 execute_state 已經處理了狀態的執行和可能的轉換
        # drive_state_machine 只需要調用它
        # machine.execute_state() # 這一行會執行，並可能在內部轉換狀態
        
        # 為了最小化改動並解決眼前的 AttributeError，我們先替換變數名
        # 但長遠來看，drive_state_machine 的邏輯需要與 JoJoStateMachine 的內部工作方式更協調
        
        # 假設 machine.execute_state() 執行了當前狀態，並且如果需要轉換，
        # 它會更新 machine.current_state。drive_state_machine 只是觸發這個過程。
        # 因此，下面的 next_state_enum 賦值和檢查可能不再需要，或者需要調整。
        
        # 暫時的修復：只改名，並假設 JoJoStateMachine 的 execute_state 不返回下一個狀態
        # 而是由各個 State 的 execute 方法調用 self.machine.transition_to()
        
        # 實際上，JoJoStateMachine 的 execute_state 已經調用了具體 State 的 execute。
        # 而具體 State 的 execute 方法會調用 self.machine.transition_to()，
        # transition_to 又會調用 self.execute_state()。這形成了一個遞歸或連續執行的模式。
        
        # drive_state_machine 的角色更像是：如果UI觸發了一個動作，
        # 它將這個動作轉化為對狀態機的某個狀態的轉換請求。
        # 例如，點擊按鈕後，調用 machine.transition_to(JoJoState.DATA_FETCH)
        
        # 鑑於 app.py 中多處調用 drive_state_machine(machine)，
        # 我們假設它的目的是確保狀態機能夠執行到某個穩定點或下一個UI交互點。
        
        # 修正 AttributeError:
        current_state_before_drive = machine.current_state
        
        # 這裡不應該再有 next_state_enum 的邏輯，因為狀態轉換由 JoJoStateMachine 內部處理
        # machine.execute_state() # 這一行就夠了，它會執行當前狀態，並可能轉換到新狀態
        
        # 為了保持原有的 next_state_enum 邏輯（儘管它可能與內部轉換衝突），我們先這樣改：
        # 假設 JoJoStateMachine 的 execute_state 返回了下一個狀態（這與當前實現不符）
        # 或者，我們假設 drive_state_machine 的目的是執行一次當前狀態，然後檢查 machine.current_state
        
        # 讓我們回頭看 JoJoStateMachine 的 execute_state:
        # 它會找到當前狀態的處理器並執行它。
        # 而每個 State 的 execute 方法會調用 self.machine.transition_to(next_state)
        # transition_to 會更新 self.current_state 並再次調用 self.execute_state()
        # 這意味著一次 drive_state_machine(machine) （如果它只是調用 machine.execute_state()）
        # 可能會觸發一連串的狀態轉換，直到達到某個不再自動轉換的狀態（如 UI_INIT 或 IDLE）。
        
        # 因此，drive_state_machine 內部不需要再手動處理 next_state_enum。
        # 它只需要確保狀態機被觸發執行。
        
        # 簡化 drive_state_machine:
        machine.execute_state() # 觸發狀態機執行當前狀態，內部會處理轉換

    except Exception as e:
        print(f"狀態 {machine.current_state} 執行時發生錯誤: {e}") # 使用 machine.current_state
        machine.context['error_message'] = str(e)
        machine.current_state = JoJoState.ERROR # 使用 machine.current_state
        machine.execute_state() # 確保 ErrorState 被執行
    
    # 如果需要連續驅動到某個狀態 (例如非 UI 互動狀態)
    # 這部分邏輯比較複雜，因為 Streamlit 的 rerender 機制
    # 暫時保持單步驅動，由 Streamlit 的 rerun 控制流程

# --- Streamlit App ---

print("--- app.py script execution START ---") # DEBUG PRINT
# 1. 初始化狀態機和開發者模式 (僅在第一次執行或 session state 遺失時)
if 'jojo_machine' not in st.session_state:
    print(">>> 'jojo_machine' NOT in st.session_state. Initializing...") # DEBUG PRINT
    st.session_state.jojo_machine = JoJoStateMachine()
    # 預設開發者模式為 False (從 UI 控制)
    st.session_state.developer_mode_active = False 
    
    machine_init = st.session_state.jojo_machine
    # 將 UI 的開發者模式狀態同步到狀態機 context
    machine_init.context['developer_mode'] = st.session_state.developer_mode_active
    
    # JoJoStateMachine.__init__ 內部已經調用了 self.execute_state()，
    # 這會將狀態從 CONFIG_LOAD 推進到 UI_INIT。
    # 因此，這裡不再需要額外調用 machine_init.execute_state()。
    # 我們只需要確認初始化後的狀態。
    print(f"JoJoStateMachine 初始化完成後 (from app.py IF block)，狀態為: {machine_init.current_state}")
else:
    print(">>> 'jojo_machine' IS ALREADY in st.session_state.") # DEBUG PRINT

# 從 session_state 獲取狀態機實例
machine = st.session_state.jojo_machine
print(f"--- Current machine state (retrieved from session_state): {machine.current_state} ---") # DEBUG PRINT

# --- UI 側邊欄：語言切換與開發者模式切換 ---
# 語言切換
if "language" not in st.session_state:
    st.session_state["language"] = "zh"

lang = st.sidebar.selectbox(
    t("select_language", st.session_state["language"]),
    options=[("zh", t("chinese", "zh")), ("en", t("english", "en"))],
    format_func=lambda x: x[1],
    index=0 if st.session_state["language"] == "zh" else 1
)[0]
st.session_state["language"] = lang

# 確保 developer_mode_active 在 session_state 中存在
if 'developer_mode_active' not in st.session_state:
    st.session_state.developer_mode_active = machine.context.get('developer_mode', False)

developer_mode_ui_switch = st.sidebar.checkbox(
    t("use_simulated_data", lang), 
    value=st.session_state.developer_mode_active,
    key="dev_mode_checkbox"
)

# 如果 UI 上的開關狀態改變，則更新 session_state 和狀態機 context
if developer_mode_ui_switch != st.session_state.developer_mode_active:
    st.session_state.developer_mode_active = developer_mode_ui_switch
    machine.context['developer_mode'] = developer_mode_ui_switch
    print(f"開發者模式已切換為: {machine.context['developer_mode']}")
    st.rerun()

# --- UI 主渲染與狀態機互動 ---
if machine.context.get('developer_mode', False):
    st.sidebar.warning("開發者模式已啟用！將使用模擬數據。")

# === 一次性收益異常檢測控制 ===
st.sidebar.subheader("⚠️ 異常檢測設定")

# 異常檢測開關
enable_anomaly_detection_ui = st.sidebar.checkbox(
    "啟用一次性收益檢測",
    value=machine.context.get('enable_anomaly_detection', True),
    help="檢測並排除疑似有一次性收益的股票，避免估值被扭曲"
)

# 異常檢測閾值控制
anomaly_threshold_ui = st.sidebar.slider(
    "異常檢測閾值",
    min_value=1.1,
    max_value=3.0,
    value=machine.context.get('anomaly_threshold', 1.5),
    step=0.1,
    help="當期FCF_EPS超過歷史平均的倍數視為異常。例如1.5表示超過1.5倍視為異常",
    disabled=not enable_anomaly_detection_ui
)

# 同步到狀態機 context
if (enable_anomaly_detection_ui != machine.context.get('enable_anomaly_detection', True) or 
    abs(anomaly_threshold_ui - machine.context.get('anomaly_threshold', 1.5)) > 0.05):
    machine.context['enable_anomaly_detection'] = enable_anomaly_detection_ui
    machine.context['anomaly_threshold'] = anomaly_threshold_ui
    print(f"異常檢測設定已更新: 啟用={enable_anomaly_detection_ui}, 閾值={anomaly_threshold_ui}x")

# 顯示當前設定狀態
if enable_anomaly_detection_ui:
    st.sidebar.success(f"🛡️ 智能異常檢測已啟用\n📊 檢測閾值: {anomaly_threshold_ui}x 歷史平均\n🎯 檢測模式: 多層檢測算法")
else:
    st.sidebar.warning("⚠️ 異常檢測已停用\n💡 建議開啟以提高估值準確性")

# 根據當前狀態執行特定邏輯 (主要是 UI 渲染和接收輸入)
if machine.current_state == JoJoState.UI_INIT: # 使用 machine.current_state
    st.title("JoJo 特價股篩選器")

    # 從 context 獲取產業中文名稱列表和風險選項
    # 如果是開發者模式且模擬數據中有產業，也可用於預選，但主要列表來自 ConfigLoad
    industry_names_for_ui = machine.context.get('industry_names', ['讀取產業失敗...'])
    if not industry_names_for_ui and machine.context.get('developer_mode'): # 開發者模式下若真實產業列表為空
        sim_data = machine.context.get('simulated_data', {})
        # 這裡可以選擇是否用模擬數據的產業名填充下拉選單，或僅提示
        # 為了測試流程，我們讓下拉選單仍基於 industries.json
        # 但 DataFetchState 會根據 developer_mode 決定是否用模擬數據
        pass


    risk_options_dict = machine.context.get('risk_premium_options', {})
    risk_options_labels = list(risk_options_dict.keys())
    
    # 處理預設選擇
    default_industry_name = industry_names_for_ui[0] if industry_names_for_ui else "N/A"
    current_selected_industry_name = machine.context.get('selected_industry_name', default_industry_name)
    if current_selected_industry_name not in industry_names_for_ui and industry_names_for_ui:
        current_selected_industry_name = industry_names_for_ui[0]

    # 新增：模式切換（產業篩選/個股直查）
    mode = st.radio(
        "選擇模式：",
        options=["產業篩選模式", "個股直查模式"],
        index=0,
        horizontal=True
    )

    selected_industry_name_from_ui = None
    selected_stock_codes = []
    manual_stock_codes = ""

    if mode == "產業篩選模式":
        selected_industry_name_from_ui = st.selectbox(
            "請選擇產業：",
            options=industry_names_for_ui,
            index=industry_names_for_ui.index(current_selected_industry_name) if current_selected_industry_name in industry_names_for_ui and industry_names_for_ui else 0
        )

        # 取得該產業下所有個股清單
        all_companies = machine.context.get('all_companies_openapi_data', [])
        industry_code = None
        for item in machine.context.get('industry_data', {}).get('industries', []):
            if item.get('name') == selected_industry_name_from_ui:
                industry_code = item.get('code')
                break
        stock_options = []
        if industry_code:
            stock_options = [c['code'] for c in all_companies if c.get('industry_code') == str(industry_code)]
        stock_options = sorted(stock_options)
        selected_stock_codes = st.multiselect(
            "（可選）指定個股代號篩選：",
            options=stock_options,
            default=[],
            help="如不選，則篩選整個產業；如選，僅針對這些個股進行分析"
        )
    else:
        manual_stock_codes = st.text_input(
            "請輸入欲查詢的股票代號（可用逗號、空白或換行分隔）：",
            value="",
            help="例如：2330, 2317 或 2330 2317"
        )
        # 解析輸入
        import re
        selected_stock_codes = [code.strip() for code in re.split(r"[,\s]+", manual_stock_codes) if code.strip()]
        selected_industry_name_from_ui = None  # 不選產業

    machine.context['selected_stock_codes'] = selected_stock_codes

    # 新增：財報資料頻率選擇
    freq_options = ["季度", "年度"]
    default_freq = machine.context.get('financial_data_freq', "季度")
    selected_freq_from_ui = st.selectbox(
        "財報資料頻率：",
        options=freq_options,
        index=freq_options.index(default_freq) if default_freq in freq_options else 0
    )
    
    risk_options_labels_with_custom = risk_options_labels + ["自訂"]
    default_risk_label = risk_options_labels_with_custom[2] if len(risk_options_labels_with_custom) > 2 else (risk_options_labels_with_custom[0] if risk_options_labels_with_custom else "N/A")
    current_selected_risk_label = machine.context.get('selected_risk_label', default_risk_label)
    if current_selected_risk_label not in risk_options_labels_with_custom and risk_options_labels_with_custom: # 檢查是否為有效選項
        current_selected_risk_label = default_risk_label


    selected_risk_label_from_ui = st.selectbox(
        "請選擇風險補償：",
        options=risk_options_labels_with_custom,
        index=risk_options_labels_with_custom.index(current_selected_risk_label) if current_selected_risk_label in risk_options_labels_with_custom and risk_options_labels_with_custom else 0
    )

    custom_risk_premium_value = machine.context.get('custom_risk_premium_value', machine.context.get('default_risk_premium', 0.04))
    if selected_risk_label_from_ui == "自訂":
        custom_risk_premium_input = st.number_input(
            "請輸入自訂風險補償 (%)：", 
            min_value=0.0, 
            max_value=100.0, 
            value=custom_risk_premium_value * 100, # 確保初始值正確
            step=0.1,
            key="custom_risk_input" 
        )
        actual_risk_preference = custom_risk_premium_input / 100.0
    elif risk_options_dict and selected_risk_label_from_ui in risk_options_dict: 
         actual_risk_preference = risk_options_dict[selected_risk_label_from_ui]
    else: # Fallback if selected_risk_label_from_ui is not in dict (e.g. "N/A" or other issues)
        actual_risk_preference = machine.context.get('default_risk_premium', 0.04)

    # 新增：最小潛在報酬率篩選輸入（僅產業篩選模式顯示）
    min_potential_return_percentage = None
    if mode == "產業篩選模式":
        min_potential_return_percentage = st.number_input(
            "篩選條件：最小潛在報酬率 (%)",
            min_value=-100.0,
            max_value=1000.0, # 允許較大的正報酬
            value=machine.context.get('min_potential_return_filter_percentage', 20.0), # 預設20%
            step=1.0,
            help="設定篩選股票時，期望的最低潛在報酬率。例如輸入 20 表示至少 20%。"
        )

    if st.button("開始篩選股票"):
        machine.context['selected_industry_name'] = selected_industry_name_from_ui 
        machine.context['risk_preference'] = actual_risk_preference
        machine.context['selected_risk_label'] = selected_risk_label_from_ui 
        if selected_risk_label_from_ui == "自訂":
            machine.context['custom_risk_premium_value'] = actual_risk_preference 

        # 新增：將財報資料頻率寫入 context
        machine.context['financial_data_freq'] = selected_freq_from_ui
        
        # 產業模式才有潛在報酬率篩選
        if mode == "產業篩選模式":
            machine.context['potential_return_threshold'] = min_potential_return_percentage / 100.0 # 統一用這個key
            machine.context['min_potential_return_filter_percentage'] = min_potential_return_percentage # 保存百分比值用於UI回顯
        else:
            # 個股直查模式不做潛在報酬率篩選
            machine.context['potential_return_threshold'] = None
            machine.context['min_potential_return_filter_percentage'] = None

        # 新增：個股代號篩選
        machine.context['selected_stock_codes'] = selected_stock_codes

        machine.context['user_clicked_filter_button'] = True 
        machine.transition_to(JoJoState.INDUSTRY_PROCESS) # 明確轉換到下一個處理狀態
        # drive_state_machine(machine) # 不再需要，transition_to 會觸發 execute_state
        machine.context['user_clicked_filter_button'] = False 
        st.rerun()

elif machine.current_state == JoJoState.INDUSTRY_PROCESS: # 使用 machine.current_state
    st.info(f"接收到產業：{machine.context.get('selected_industry_name')}，風險補償：{machine.context.get('risk_preference')*100:.1f}%") # 使用 selected_industry_name
    machine.execute_state() # 觸發執行
    st.rerun()

elif machine.current_state == JoJoState.DATA_FETCH: # 使用 machine.current_state
    # 創建詳細的進度指示器
    st.subheader("📊 數據抓取進行中...")
    
    # 進度條和狀態顯示
    progress_container = st.container()
    with progress_container:
        # 主進度條
        main_progress = st.progress(0)
        status_text = st.empty()
        
        # 詳細信息
        details_expander = st.expander("📋 詳細進度", expanded=True)
        with details_expander:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("當前階段", "數據抓取")
                if machine.context.get('enable_anomaly_detection', True):
                    st.metric("異常檢測", "✅ 已啟用", f"閾值: {machine.context.get('anomaly_threshold', 1.5)}x")
                else:
                    st.metric("異常檢測", "⚠️ 已停用", "建議開啟")
            with col2:
                st.metric("選定產業", machine.context.get('selected_industry_name', '未知'))
                st.metric("風險補償", f"{machine.context.get('risk_preference', 0)*100:.1f}%")
    
    # 執行數據抓取
    with st.spinner("🔄 正在從 FinMind 抓取最新財務數據... 請稍候..."):
        # 更新狀態
        status_text.text("正在連接 FinMind API...")
        main_progress.progress(20)
        
        machine.execute_state() # 觸發執行
        
        # 完成狀態
        main_progress.progress(100)
        status_text.text("✅ 數據抓取完成！")
    
    st.rerun() # 完成後重新渲染以進入下一狀態或顯示結果/錯誤

elif machine.current_state == JoJoState.VALUATION: # 使用 machine.current_state
    # 創建估值進度指示器
    st.subheader("🧮 DCF 估值計算中...")
    
    progress_container = st.container()
    with progress_container:
        # 估值進度條
        valuation_progress = st.progress(0)
        status_text = st.empty()
        
        # 估值詳細信息
        details_expander = st.expander("📈 估值詳情", expanded=True)
        with details_expander:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("估值模型", "DCF (現金流折現)")
                st.metric("計算方式", "FCFE (股東自由現金流)")
            with col2:
                if machine.context.get('enable_anomaly_detection', True):
                    st.metric("品質控制", "🛡️ 異常檢測中", f"閾值: {machine.context.get('anomaly_threshold', 1.5)}x")
                else:
                    st.metric("品質控制", "⚠️ 標準模式")
                st.metric("成長率模型", "線性衰減至 3%")
            with col3:
                st.metric("折現率", f"無風險利率 + 風險補償")
                st.metric("風險補償", f"{machine.context.get('risk_preference', 0)*100:.1f}%")
    
    with st.spinner("🔢 正在進行 DCF 估值計算... 請稍候..."):
        # 更新進度
        status_text.text("正在計算各股票內在價值...")
        valuation_progress.progress(30)
        
        machine.execute_state() # 觸發執行
        
        # 完成進度
        valuation_progress.progress(100)
        status_text.text("✅ 估值計算完成！")
    
    st.rerun()

elif machine.current_state == JoJoState.FILTERING: # 使用 machine.current_state
    with st.spinner("正在篩選股票... 請稍候..."):
        machine.execute_state() # 觸發執行
    st.rerun()
    
elif machine.current_state == JoJoState.RESULTS_DISPLAY: # 使用 machine.current_state
    st.subheader("篩選結果：")
    filtered_stocks_data = machine.context.get('filtered_results', []) 
      # === 增強的異常檢測統計信息顯示 ===
    valuation_results = machine.context.get('valuation_results', [])
    anomaly_detection_enabled = machine.context.get('enable_anomaly_detection', True)
    anomaly_threshold = machine.context.get('anomaly_threshold', 1.5)
    
    if anomaly_detection_enabled and valuation_results:
        st.markdown("---")
        st.subheader("🛡️ 智能異常檢測報告")
        
        # 統計異常檢測結果
        total_stocks = len(valuation_results)
        anomaly_stocks = [r for r in valuation_results if r.get('error') and '一次性收益異常' in r.get('error', '')]
        normal_stocks = [r for r in valuation_results if not r.get('error') or '一次性收益異常' not in r.get('error', '')]
        other_errors = [r for r in valuation_results if r.get('error') and '一次性收益異常' not in r.get('error', '')]
        
        # 計算檢測效率
        detection_rate = len(anomaly_stocks) / total_stocks * 100 if total_stocks > 0 else 0
        success_rate = len(normal_stocks) / total_stocks * 100 if total_stocks > 0 else 0
        
        # 顯示檢測概要
        st.info(f"🔍 **檢測概要** | 閾值: {anomaly_threshold}x | 檢測算法: 多層智能檢測")
        
        # 四列指標顯示
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("總檢測股票", total_stocks, help="參與異常檢測的股票總數")
        with col2:
            st.metric("✅ 正常股票", len(normal_stocks), 
                     delta=f"{success_rate:.1f}%" if total_stocks > 0 else "0%",
                     help="通過異常檢測的股票數量")
        with col3:
            st.metric("⚠️ 異常股票", len(anomaly_stocks), 
                     delta=f"{detection_rate:.1f}%" if total_stocks > 0 else "0%",
                     delta_color="inverse",
                     help="被檢測為一次性收益異常的股票")
        with col4:
            st.metric("❌ 其他錯誤", len(other_errors), 
                     help="因其他原因無法估值的股票")
        
        # 顯示異常股票詳情
        if anomaly_stocks:
            with st.expander(f"📊 異常檢測詳細報告 - 發現 {len(anomaly_stocks)} 支疑似異常股票", expanded=len(anomaly_stocks) <= 5):
                st.markdown("### 🔍 檢測結果說明")
                st.markdown("""
                以下股票因**疑似存在一次性收益**而被智能排除，以保護您的投資決策：
                - 🎯 **檢測標準**: 多層檢測算法，結合歷史平均、最大值比較
                - 🛡️ **保護機制**: 避免因異常高收益而高估內在價值
                - 📈 **建議**: 這些股票可能存在資產處分、業外收入等一次性項目
                """)
                
                # 創建詳細的異常股票表格
                anomaly_df_data = []
                for i, stock in enumerate(anomaly_stocks, 1):
                    # 計算額外統計資訊
                    current_fcf_eps = stock.get('current_fcf_eps_simple', 0)
                    avg_historical = stock.get('avg_historical_fcf_eps', 0)
                    max_historical = stock.get('max_historical_fcf_eps', 0)
                    anomaly_ratio = stock.get('anomaly_ratio', 0)
                    
                    # 計算異常程度
                    if avg_historical > 0:
                        severity_level = "🔴 極端" if anomaly_ratio > 3.0 else "🟡 中度" if anomaly_ratio > 2.0 else "🟠 輕微"
                    else:
                        severity_level = "❓ 未知"
                    
                    anomaly_df_data.append({
                        '#': i,
                        '股票代號': stock.get('stock_code', 'N/A'),
                        '股票名稱': stock.get('name', 'N/A'),
                        '當期FCF_EPS': f"{current_fcf_eps:.3f}" if current_fcf_eps else 'N/A',
                        '歷史平均': f"{avg_historical:.3f}" if avg_historical else 'N/A',
                        '歷史最大值': f"{max_historical:.3f}" if max_historical else 'N/A',
                        '異常倍數': f"{anomaly_ratio:.2f}x" if anomaly_ratio else 'N/A',
                        '異常程度': severity_level,
                        '歷史期數': stock.get('historical_periods', 'N/A'),
                        '檢測原因': stock.get('anomaly_reason', stock.get('error', 'N/A'))
                    })
                
                if anomaly_df_data:
                    anomaly_df = pd.DataFrame(anomaly_df_data)
                    st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
                    
                    # 額外統計資訊
                    if len(anomaly_stocks) > 1:
                        avg_anomaly_ratio = sum(s.get('anomaly_ratio', 0) for s in anomaly_stocks) / len(anomaly_stocks)
                        max_anomaly_ratio = max(s.get('anomaly_ratio', 0) for s in anomaly_stocks)
                        
                        st.markdown("#### 📈 異常統計摘要")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("平均異常倍數", f"{avg_anomaly_ratio:.2f}x")
                        with col2:
                            st.metric("最大異常倍數", f"{max_anomaly_ratio:.2f}x")
                        with col3:
                            st.metric("檢測準確度", f"{detection_rate:.1f}%")
                    
                    st.success("💡 **建議**: 被排除的股票可單獨分析，確認是否為真正的一次性收益後再考慮投資。")
        else:
            st.success("🎉 **檢測結果優異！** 所有股票均通過一次性收益檢測，數據品質良好。")
        
        st.markdown("---")
    elif not anomaly_detection_enabled:
        st.warning("⚠️ **提醒**: 您已停用異常檢測功能。建議開啟以提高估值準確性。")
        st.markdown("---")
    
    if filtered_stocks_data:
        st.write(f"共篩選出 {len(filtered_stocks_data)} 支潛在特價股：")
        
        df_results = pd.DataFrame(filtered_stocks_data)

        # 中文欄位對應
        column_map = {
            'stock_code': '代號',
            'name': '名稱',
            'intrinsic_value_per_share': '估計內在價值',
            'current_market_price': '目前市價',
            'potential_return_display': '潛在報酬 (%)',
            'source_eps': '來源EPS',
            'calculated_fcf_eps': '計算FCFEps',
            'data_year_quarter': '財報年月',
            'used_discount_rate_display': '折現率 (%)',
            'warning': '警告',
            # 其餘欄位如需顯示可再補充
        }
        # 先處理顯示欄位與順序
        display_columns = [
            'stock_code', 'name', 'intrinsic_value_per_share', 'current_market_price',
            'potential_return_display', 'source_eps', 'calculated_fcf_eps',
            'data_year_quarter', 'used_discount_rate_display', 'warning'
        ]
        # 預先格式化百分比欄位
        if not df_results.empty:
            if 'potential_return' in df_results.columns:
                df_results['potential_return_display'] = df_results['potential_return'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
            if 'used_discount_rate' in df_results.columns:
                df_results['used_discount_rate_display'] = df_results['used_discount_rate'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")

        # 只取要顯示的欄位，並轉中文
        df_display = df_results[[col for col in display_columns if col in df_results.columns]].copy()
        df_display.columns = [column_map.get(col, col) for col in df_display.columns]

        # st.dataframe 顯示
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    else:
        st.info("沒有篩選到符合條件的股票，或仍在處理中。請檢查篩選條件或資料來源。")

    import os
    from datetime import datetime

    col1, col2 = st.columns(2)
    with col1:
        # 合併下載按鈕：直接在結果頁顯示
        if st.button("下載 CSV"):
            export_dir = "export"
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = os.path.join(export_dir, f"jojo_export_{timestamp}.csv")
            df_display.to_csv(csv_path, index=False, encoding="utf-8-sig")
            with open(csv_path, "rb") as f:
                st.download_button(
                    label="點此下載 CSV 檔案",
                    data=f,
                    file_name=os.path.basename(csv_path),
                    mime="text/csv"
                )
        # Excel 下載
        try:
            import openpyxl
            excel_supported = True
        except ImportError:
            excel_supported = False

        if excel_supported:
            if st.button("下載 Excel"):
                export_dir = "export"
                os.makedirs(export_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                excel_path = os.path.join(export_dir, f"jojo_export_{timestamp}.xlsx")
                df_display.to_excel(excel_path, index=False)
                with open(excel_path, "rb") as f:
                    st.download_button(
                        label="點此下載 Excel 檔案",
                        data=f,
                        file_name=os.path.basename(excel_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("如需 Excel 匯出，請安裝 openpyxl 套件。")

    with col2:
        if st.button("重新查詢"):
            machine.context['user_clicked_new_query_button'] = True
            machine.transition_to(JoJoState.UI_INIT) # 明確轉換到 UI_INIT
            machine.context['user_clicked_new_query_button'] = False # 重置標記
            st.rerun()
            
        # 重新篩選按鈕
        if st.button("返回條件設定/重新篩選"):
            machine.transition_to(JoJoState.UI_INIT)
            st.rerun()

elif machine.current_state == JoJoState.EXPORT: # 使用 machine.current_state
    with st.spinner("正在匯出結果..."):
        machine.execute_state() # 觸發執行

    # 匯出完成後，提供下載按鈕
    csv_path = machine.context.get('export_file_path')
    excel_path = machine.context.get('export_file_path_excel')
    st.success("匯出完成！請下載檔案：")
    import os

    if csv_path and os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            st.download_button(
                label="下載 CSV",
                data=f,
                file_name=os.path.basename(csv_path),
                mime="text/csv"
            )
    else:
        st.warning("找不到可下載的 CSV 檔案。")

    if excel_path and os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            st.download_button(
                label="下載 Excel",
                data=f,
                file_name=os.path.basename(excel_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("如需 Excel 匯出，請安裝 openpyxl 套件。")

    # ExportState 應該轉換回 ResultsDisplay 或 UI_INIT
    # st.rerun()  # ← 已移除，讓下載按鈕能顯示

elif machine.current_state == JoJoState.ERROR: # 使用 machine.current_state
    st.error(f"發生錯誤：{machine.context.get('error_message', '未知錯誤')}")
    if st.button("返回主頁並重試"):
        if 'error_message' in machine.context:
            del machine.context['error_message']
        if 'user_clicked_filter_button' in machine.context: 
             del machine.context['user_clicked_filter_button']
        
        machine.transition_to(JoJoState.UI_INIT) # 明確轉換
        # drive_state_machine(machine) 
        st.rerun()

elif machine.current_state == JoJoState.END: # 使用 machine.current_state
    st.success("所有流程已執行完畢。")
    if st.button("重新開始"):
        st.session_state.jojo_machine = JoJoStateMachine() 
        machine_reset = st.session_state.jojo_machine
        if machine_reset.current_state == JoJoState.CONFIG_LOAD: # 使用 machine_reset.current_state
            machine_reset.execute_state() # 觸發執行
            # drive_state_machine(machine_reset)
        st.rerun()

# 调试信息
# st.sidebar.write("--- 狀態機偵錯 ---")
# st.sidebar.write(f"當前狀態 (App): {machine.current_state}") # 使用 machine.current_state
# st.sidebar.write("Context (App):")
# st.sidebar.json(machine.context, expanded=False)
# st.sidebar.write("Session State Keys (App):", list(st.session_state.keys()))
