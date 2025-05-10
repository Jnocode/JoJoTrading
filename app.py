# app.py (Streamlit 主應用程式檔案)
import streamlit as st
from jojo_state_machine import JoJoStateMachine, JoJoState, BaseState # 確保 BaseState 也導入了

# --- Helper function to drive state machine ---
def drive_state_machine(machine, target_state=None):
    """
    驅動狀態機直到達到目標狀態或某個等待輸入的狀態。
    如果 target_state 是 None，則執行一步。
    """
    if not machine:
        return

    # 獲取當前狀態的處理物件
    current_state_handler = machine.states.get(machine.current_jojo_state_enum)
    if not current_state_handler:
        st.error(f"錯誤：無效的狀態 {machine.current_jojo_state_enum}")
        machine.current_jojo_state_enum = JoJoState.ERROR 
        machine.context['error_message'] = f"無效狀態: {machine.current_jojo_state_enum}"
        return

    try:
        current_state_handler.on_enter(machine.context)
        next_state_enum = current_state_handler.execute(machine.context)
        current_state_handler.on_exit(machine.context)
        
        # 更新狀態，除非是特殊情況（例如，狀態內部邏輯決定不立即轉換）
        if isinstance(next_state_enum, JoJoState):
             machine.current_jojo_state_enum = next_state_enum
        elif next_state_enum is not None: # 如果返回了非預期的東西
            print(f"警告: 狀態 {current_state_handler.__class__.__name__} 返回了非 JoJoState: {next_state_enum}")


    except Exception as e:
        print(f"狀態 {machine.current_jojo_state_enum} 執行時發生錯誤: {e}")
        machine.context['error_message'] = str(e)
        machine.current_jojo_state_enum = JoJoState.ERROR
    
    # 如果需要連續驅動到某個狀態 (例如非 UI 互動狀態)
    # 這部分邏輯比較複雜，因為 Streamlit 的 rerender 機制
    # 暫時保持單步驅動，由 Streamlit 的 rerun 控制流程

# --- Streamlit App ---

# 1. 初始化狀態機和開發者模式 (僅在第一次執行或 session state 遺失時)
if 'jojo_machine' not in st.session_state:
    st.session_state.jojo_machine = JoJoStateMachine()
    # 預設開發者模式為 False (從 UI 控制)
    st.session_state.developer_mode_active = False 
    
    machine_init = st.session_state.jojo_machine
    # 將 UI 的開發者模式狀態同步到狀態機 context
    machine_init.context['developer_mode'] = st.session_state.developer_mode_active
    
    if machine_init.current_jojo_state_enum == JoJoState.CONFIG_LOAD:
        print("首次執行：驅動 CONFIG_LOAD 狀態")
        drive_state_machine(machine_init) 
        print(f"CONFIG_LOAD 後狀態為: {machine_init.current_jojo_state_enum}")

# 從 session_state 獲取狀態機實例
machine = st.session_state.jojo_machine

# --- UI 側邊欄：開發者模式切換 ---
# 確保 developer_mode_active 在 session_state 中存在
if 'developer_mode_active' not in st.session_state:
    st.session_state.developer_mode_active = machine.context.get('developer_mode', False)

developer_mode_ui_switch = st.sidebar.checkbox(
    "啟用開發者模式 (使用模擬數據)", 
    value=st.session_state.developer_mode_active,
    key="dev_mode_checkbox" # 給予 key
)

# 如果 UI 上的開關狀態改變，則更新 session_state 和狀態機 context
if developer_mode_ui_switch != st.session_state.developer_mode_active:
    st.session_state.developer_mode_active = developer_mode_ui_switch
    machine.context['developer_mode'] = developer_mode_ui_switch
    print(f"開發者模式已切換為: {machine.context['developer_mode']}")
    # 可能需要重置某些狀態或重新執行 CONFIG_LOAD 以便模擬數據正確加載
    # 簡單起見，這裡只更新 context，DataFetchState 會在執行時檢查此標誌
    st.rerun() # 重新執行以讓 UI 和狀態機響應模式變化

# --- UI 主渲染與狀態機互動 ---
if machine.context.get('developer_mode', False):
    st.sidebar.warning("開發者模式已啟用！將使用模擬數據。")

# 根據當前狀態執行特定邏輯 (主要是 UI 渲染和接收輸入)
if machine.current_jojo_state_enum == JoJoState.UI_INIT:
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

    selected_industry_name_from_ui = st.selectbox(
        "請選擇產業：",
        options=industry_names_for_ui,
        index=industry_names_for_ui.index(current_selected_industry_name) if current_selected_industry_name in industry_names_for_ui and industry_names_for_ui else 0
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

    # 新增：最小潛在報酬率篩選輸入
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
        
        machine.context['min_potential_return_filter'] = min_potential_return_percentage / 100.0 # 轉換為小數
        machine.context['min_potential_return_filter_percentage'] = min_potential_return_percentage # 保存百分比值用於UI回顯

        machine.context['user_clicked_filter_button'] = True 
        drive_state_machine(machine) 
        machine.context['user_clicked_filter_button'] = False 
        st.rerun()

elif machine.current_jojo_state_enum == JoJoState.INDUSTRY_PROCESS:
    st.info(f"接收到產業：{machine.context.get('selected_industry_name')}，風險補償：{machine.context.get('risk_preference')*100:.1f}%") # 使用 selected_industry_name
    drive_state_machine(machine)
    st.rerun()

elif machine.current_jojo_state_enum == JoJoState.DATA_FETCH:
    with st.spinner("正在抓取資料... 請稍候..."):
        drive_state_machine(machine)
    st.rerun() # 完成後重新渲染以進入下一狀態或顯示結果/錯誤

elif machine.current_jojo_state_enum == JoJoState.VALUATION:
    with st.spinner("正在進行 DCF 估值... 請稍候..."):
        drive_state_machine(machine)
    st.rerun()

elif machine.current_jojo_state_enum == JoJoState.FILTERING:
    with st.spinner("正在篩選股票... 請稍候..."):
        drive_state_machine(machine)
    st.rerun()
    
elif machine.current_jojo_state_enum == JoJoState.RESULTS_DISPLAY:
    st.subheader("篩選結果：")
    filtered_stocks_data = machine.context.get('filtered_stocks', [])
    
    if filtered_stocks_data:
        # 為了更好的表格顯示，可以考慮將字典列表轉換為 pandas DataFrame
        # import pandas as pd
        # df = pd.DataFrame(filtered_stocks_data)
        # st.dataframe(df)
        # 或者直接使用 st.table() 或 st.json() 進行簡單顯示
        
        # 顯示選出的股票數量
        st.write(f"共篩選出 {len(filtered_stocks_data)} 支潛在特價股：")
        
        # 為了更美觀的表格，我們可以指定欄位順序和標題
        # 首先獲取所有可能的鍵，以處理某些股票可能缺少某些鍵的情況
        if filtered_stocks_data:
            all_keys = set()
            for item in filtered_stocks_data:
                if isinstance(item, dict): # 確保 item 是字典
                    all_keys.update(item.keys())
            
            # 定義我們希望的欄位順序和中文標題
            column_config = {
                "股票代號": st.column_config.TextColumn("代號", width="small"),
                "股票名稱": st.column_config.TextColumn("名稱", width="medium"),
                "內在價值": st.column_config.NumberColumn("估計內在價值", format="%.2f", width="small"),
                "目前市價": st.column_config.NumberColumn("目前市價", format="%.2f", width="small"),
                "潛在報酬": st.column_config.TextColumn("潛在報酬 (%)", width="small"),
                "EPS (來源)": st.column_config.NumberColumn("來源EPS", format="%.2f", width="small"),
                "FCFEps (計算)": st.column_config.NumberColumn("計算FCFEps", format="%.2f", width="small"),
                "估值年度/季度": st.column_config.TextColumn("財報年月", width="small"),
                "使用折現率": st.column_config.TextColumn("折現率", width="small")
            }
            # 確保只選擇 filtered_stocks_data 中實際存在的鍵來配置
            active_column_config = {k: v for k, v in column_config.items() if k in all_keys}

            st.dataframe(filtered_stocks_data, column_config=active_column_config, use_container_width=True)

    else:
        st.info("沒有篩選到符合條件的股票，或仍在處理中。請檢查篩選條件或資料來源。")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("匯出結果"):
            machine.context['user_clicked_export_button'] = True
            drive_state_machine(machine)
            machine.context['user_clicked_export_button'] = False
            st.rerun()
    with col2:
        if st.button("重新查詢"):
            machine.context['user_clicked_new_query_button'] = True
            drive_state_machine(machine) # ResultsDisplayState 內部會轉換到 UI_INIT
            machine.context['user_clicked_new_query_button'] = False
            st.rerun()
            
elif machine.current_jojo_state_enum == JoJoState.EXPORT:
    with st.spinner("正在匯出結果..."):
        drive_state_machine(machine)
    st.success("匯出完成！(模擬)") # 假設匯出成功
    # 匯出後，通常我們希望停在結果頁或返回主頁，這裡我們讓它停留在 EXPORT 後由 ResultsDisplayState 決定
    # 或者直接轉換: machine.current_jojo_state_enum = JoJoState.RESULTS_DISPLAY
    st.rerun() # 重新渲染以回到 ResultsDisplay (因為 ExportState 會返回 ResultsDisplay)

elif machine.current_jojo_state_enum == JoJoState.ERROR:
    st.error(f"發生錯誤：{machine.context.get('error_message', '未知錯誤')}")
    if st.button("返回主頁並重試"):
        # 清理 context 中的錯誤訊息，避免下次直接跳到 ERROR
        if 'error_message' in machine.context:
            del machine.context['error_message']
        if 'user_clicked_filter_button' in machine.context: # 清理可能導致問題的觸發器
             del machine.context['user_clicked_filter_button']
        
        drive_state_machine(machine) # ErrorState 應該返回 UI_INIT
        st.rerun()

elif machine.current_jojo_state_enum == JoJoState.END:
    st.success("所有流程已執行完畢。")
    if st.button("重新開始"):
        st.session_state.jojo_machine = JoJoStateMachine() # 完全重置狀態機
        # 驅動 CONFIG_LOAD
        machine_reset = st.session_state.jojo_machine
        if machine_reset.current_jojo_state_enum == JoJoState.CONFIG_LOAD:
            drive_state_machine(machine_reset)
        st.rerun()

# 调试信息
# st.sidebar.write("--- 狀態機偵錯 ---")
# st.sidebar.write(f"當前狀態 (App): {machine.current_jojo_state_enum}")
# st.sidebar.write("Context (App):")
# st.sidebar.json(machine.context, expanded=False)
# st.sidebar.write("Session State Keys (App):", list(st.session_state.keys()))
