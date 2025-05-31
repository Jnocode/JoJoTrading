"""
JoJotrading Streamlit 主應用程式

這是基於 DCF 估值模型的台股篩選系統的主要使用者介面，
採用 Streamlit 框架建立互動式 Web 應用程式。

系統架構：
- 狀態機驅動的應用程式流程控制
- 多語言支援 (中文/英文)
- 響應式 Web 介面設計
- 即時資料處理與結果展示

主要功能模組：

1. 使用者介面控制
   - drive_state_machine(): 狀態機流程驅動器
   - render_ui(): 主要介面渲染邏輯
   - 側邊欄參數設定與控制面板

2. 產業與股票選擇
   - 支援產業分類篩選
   - 個股代碼直接輸入
   - 動態股票清單管理

3. DCF 估值參數設定
   - 無風險利率與風險溢價調整
   - 終端成長率設定
   - 估值方法選擇 (FCF/EPS)

4. 成長股篩選條件
   - 營收 CAGR 篩選
   - EPS CAGR 篩選  
   - ROE 表現評估
   - 可自訂閾值與評估期間

5. 結果展示與匯出
   - 動態篩選結果表格
   - 詳細估值指標展示
   - Excel 匯出功能
   - 成長股評估詳情

狀態流程：
CONFIG_LOAD → UI_INIT → INDUSTRY_PROCESS → DATA_FETCH → 
VALUATION → FILTERING → RESULTS_DISPLAY → EXPORT

技術特色：
- 狀態機模式確保流程的穩定性與可維護性
- 即時快取機制減少 API 呼叫延遲
- 響應式設計支援多種螢幕尺寸
- 異常檢測機制提升估值準確度

使用方式：
1. 選擇產業或輸入個股代碼
2. 調整 DCF 估值參數
3. 設定成長股篩選條件
4. 執行分析並查看結果
5. 匯出詳細報告

環境需求：
- Python 3.8+
- Streamlit 1.28+
- 有效的 FinMind API 憑證
- 穩定的網路連線以存取即時股價
"""

# app.py (Streamlit 主應用程式檔案)
import streamlit as st
import pandas as pd # Import pandas
import data_handler  # Import data_handler for enhanced DCF settings
from jojo_state_machine import JoJoStateMachine, JoJoState, State # 確保 State 也導入了 (原 BaseState)
from modules.i18n import t
from modules.growth_analyzer import DEFAULT_CRITERIA, evaluate_growth_potential, GrowthCriterion
from dcf_optimized_config import DCF_OPTIMIZED_CONFIG  # Import optimized DCF configuration
# 新增：導入台灣市場預設配置和用戶配置管理
from taiwan_market_presets import (
    get_all_taiwan_growth_presets, 
    get_all_taiwan_dcf_presets,
    get_all_taiwan_industry_presets,
    apply_taiwan_growth_preset,
    apply_taiwan_dcf_preset,
    apply_taiwan_industry_preset
)
from user_config_manager import (
    UserConfigManager,
    UserGrowthConfig,
    UserDCFConfig,
    UserIntegratedConfig,
    UserConfigMetadata
)
import json

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
        # 為了保持 drive_state_machine 的現有構造，我們假設它仍然需要知道下一個狀態
        # 但這與 JoJoStateMachine 的 transition_to 和 execute_state 的耦合較高
        # 這裡的 next_state_enum 應該由 machine.execute_state() 返回或通過某种方式獲取
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

# --- Streamlit App ---

# 1. 初始化狀態機和開發者模式 (僅在第一次執行或 session state 遺失時)
if 'jojo_machine' not in st.session_state:
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
    
else:
    pass

# 從 session_state 獲取狀態機實例
machine = st.session_state.jojo_machine

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
    help="當期FCF_EPS超過歷史平均多少倍時視為異常"
)

# === Phase 1 Enhancement Controls ===
st.sidebar.subheader("🚀 Phase 1 增強功能")

# Enhanced DCF toggle
use_enhanced_dcf_ui = st.sidebar.checkbox(
    "使用增強版 DCF 估值",
    value=machine.context.get('use_enhanced_dcf', True),
    help="啟用數據驗證、情境分析和動態折現率的增強 DCF 模型"
)

# Data validation toggle
enable_data_validation_ui = st.sidebar.checkbox(
    "啟用數據品質驗證",
    value=machine.context.get('enable_data_validation', True),
    help="執行財務數據完整性和一致性檢查"
)

# Minimum data quality score
min_data_quality_score_ui = st.sidebar.slider(
    "最低數據品質分數",
    min_value=40,
    max_value=90,
    value=machine.context.get('min_data_quality_score', 60),
    step=5,
    help="低於此分數的股票將使用標準 DCF 或跳過"
)

# Scenario analysis toggle
enable_scenario_analysis_ui = st.sidebar.checkbox(
    "啟用情境分析",
    value=machine.context.get('enable_scenario_analysis', True),
    help="計算樂觀、基準和保守三種情境的估值"
)

# Monte Carlo simulation toggle
enable_monte_carlo_ui = st.sidebar.checkbox(
    "啟用蒙地卡羅模擬",
    value=machine.context.get('enable_monte_carlo', False),
    help="使用蒙地卡羅模擬量化估值不確定性 (較耗時)"
)

# Monte Carlo iterations (only show if Monte Carlo is enabled)
if enable_monte_carlo_ui:
    monte_carlo_iterations_ui = st.sidebar.slider(
        "蒙地卡羅模擬次數",
        min_value=100,
        max_value=5000,
        value=machine.context.get('monte_carlo_iterations', 1000),
        step=100,
        help="更多次數提供更精確結果但需要更長時間"
    )
else:
    monte_carlo_iterations_ui = machine.context.get('monte_carlo_iterations', 1000)

# Update context if any settings changed
settings_changed = False
if enable_anomaly_detection_ui != machine.context.get('enable_anomaly_detection'):
    machine.context['enable_anomaly_detection'] = enable_anomaly_detection_ui
    settings_changed = True

if anomaly_threshold_ui != machine.context.get('anomaly_threshold'):
    machine.context['anomaly_threshold'] = anomaly_threshold_ui
    settings_changed = True

if use_enhanced_dcf_ui != machine.context.get('use_enhanced_dcf'):
    machine.context['use_enhanced_dcf'] = use_enhanced_dcf_ui
    data_handler.USE_ENHANCED_DCF = use_enhanced_dcf_ui  # Update data_handler setting
    settings_changed = True
    print(f"DCF 方法切換為: {'增強版' if use_enhanced_dcf_ui else '原始版'}")

if enable_data_validation_ui != machine.context.get('enable_data_validation'):
    machine.context['enable_data_validation'] = enable_data_validation_ui
    settings_changed = True

if min_data_quality_score_ui != machine.context.get('min_data_quality_score'):
    machine.context['min_data_quality_score'] = min_data_quality_score_ui
    settings_changed = True

if enable_scenario_analysis_ui != machine.context.get('enable_scenario_analysis'):
    machine.context['enable_scenario_analysis'] = enable_scenario_analysis_ui
    settings_changed = True

if enable_monte_carlo_ui != machine.context.get('enable_monte_carlo'):
    machine.context['enable_monte_carlo'] = enable_monte_carlo_ui
    settings_changed = True

if monte_carlo_iterations_ui != machine.context.get('monte_carlo_iterations'):
    machine.context['monte_carlo_iterations'] = monte_carlo_iterations_ui
    settings_changed = True

if settings_changed:
    print("設定已更新，將在下次計算時生效")

# === 初始化配置管理器 ===
if 'config_manager' not in st.session_state:
    st.session_state.config_manager = UserConfigManager()

# 側邊欄配置選項
st.sidebar.title("⚙️ 配置管理")

# 配置選項卡
config_tab = st.sidebar.radio(
    "配置方式",
    ["使用預設配置", "自定義配置", "台股預設自訂", "保存/載入配置"],
    help="選擇配置方式：使用台灣市場專業預設、創建自定義配置、自訂台股預設或管理保存的配置"
)

# === 台灣市場預設配置與用戶自定義配置管理 ===
if config_tab == "使用預設配置":
    st.sidebar.subheader("🏭 台灣市場配置預設")
    
    # 台灣市場預設配置選擇
    preset_category = st.sidebar.selectbox(
        "預設配置類型",
        ["成長股篩選", "DCF 估值", "產業特定"],
        help="選擇要應用的預設配置類型"
    )
    
    if preset_category == "成長股篩選":
        growth_presets = get_all_taiwan_growth_presets()
        preset_names = [preset.name for preset in growth_presets.values()]
        
        if preset_names:
            selected_preset_name = st.sidebar.selectbox(
                "選擇成長股預設",
                preset_names,            help="選擇適合的成長股篩選預設配置"
            )
            
            selected_preset = next(p for p in growth_presets.values() if p.name == selected_preset_name)
            selected_preset_key = next(k for k, p in growth_presets.items() if p.name == selected_preset_name)
            
            # 顯示預設配置詳情
            with st.sidebar.expander("📋 配置詳情"):
                st.write(f"**描述:** {selected_preset.description}")
                st.write(f"**適用於:** {selected_preset.recommended_for}")
                st.write(f"**營收CAGR閾值:** {selected_preset.revenue_cagr_threshold:.1%}")
                st.write(f"**EPS CAGR閾值:** {selected_preset.eps_cagr_threshold:.1%}")
                st.write(f"**ROE閾值:** {selected_preset.roe_threshold:.1%}")
                st.write(f"**最小市值:** {selected_preset.min_market_cap:.0f}億")
            
            if st.sidebar.button("🚀 應用成長股預設", help="將選擇的預設配置應用到系統"):
                try:
                    apply_taiwan_growth_preset(selected_preset_key, machine.context)
                    st.sidebar.success(f"✅ 已應用預設：{selected_preset_name}")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"❌ 應用預設失敗：{str(e)}")
                    st.sidebar.info("💡 請檢查預設配置是否正確或聯繫技術支援")
    
    elif preset_category == "DCF 估值":
        dcf_presets = get_all_taiwan_dcf_presets()
        preset_names = [preset.name for preset in dcf_presets.values()]
        
        if preset_names:
            selected_preset_name = st.sidebar.selectbox(
                "選擇DCF預設",
                preset_names,
                help="選擇適合的DCF估值預設配置"
            )
            
            selected_preset = next(p for p in dcf_presets.values() if p.name == selected_preset_name)
            selected_preset_key = next(k for k, p in dcf_presets.items() if p.name == selected_preset_name)
              # 顯示預設配置詳情
            with st.sidebar.expander("📋 配置詳情"):
                st.write(f"**描述:** {selected_preset.description}")
                st.write(f"**適用於:** {selected_preset.recommended_for}")
                st.write(f"**短期成長率:** {selected_preset.short_term_growth_rate:.1%}")
                st.write(f"**終端成長率:** {selected_preset.terminal_growth_rate:.1%}")
                st.write(f"**風險偏好:** {selected_preset.risk_preference:.1%}")
                st.write(f"**預測年數:** {selected_preset.projection_years}年")
                st.write(f"**篩選閾值:** {selected_preset.screening_threshold:.1%}")
            
            if st.sidebar.button("🚀 應用DCF預設", help="將選擇的預設配置應用到系統"):
                try:
                    apply_taiwan_dcf_preset(selected_preset_key, machine.context)
                    st.sidebar.success(f"✅ 已應用預設：{selected_preset_name}")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"❌ 應用預設失敗：{str(e)}")
                    st.sidebar.info("💡 請檢查預設配置是否正確或聯繫技術支援")
    
    else:  # 產業特定
        industry_presets = get_all_taiwan_industry_presets()
        preset_names = [preset.name for preset in industry_presets.values()]
        
        if preset_names:
            selected_preset_name = st.sidebar.selectbox(
                "選擇產業特定預設",
                preset_names,
                help="選擇針對特定產業優化的預設配置"
            )
            
            selected_preset = next(p for p in industry_presets.values() if p.name == selected_preset_name)
            selected_preset_key = next(k for k, p in industry_presets.items() if p.name == selected_preset_name)
            
            # 顯示預設配置詳情
            with st.sidebar.expander("📋 配置詳情"):
                st.write(f"**描述:** {selected_preset.description}")
                st.write(f"**適用於:** {selected_preset.recommended_for}")
            
            if st.sidebar.button("🚀 應用產業預設", help="將選擇的預設配置應用到系統"):
                apply_taiwan_industry_preset(selected_preset_key, machine.context)
                st.sidebar.success(f"✅ 已應用預設：{selected_preset_name}")
                st.rerun()

elif config_tab == "自定義配置":
    st.sidebar.write("🎨 **創建自定義配置**")
    
    # 配置名稱和描述
    config_name = st.sidebar.text_input(
        "配置名稱",
        placeholder="例如：我的成長股配置",
        help="為你的自定義配置命名"
    )
    
    config_description = st.sidebar.text_area(
        "配置描述",
        placeholder="描述這個配置的特點和適用情況...",
        help="詳細描述配置的特點和使用場景",
        height=60
    )
    
    # 配置類型選擇
    custom_config_type = st.sidebar.selectbox(
        "配置類型",
        ["成長股篩選", "DCF估值", "整合配置"],
        help="選擇要創建的自定義配置類型"
    )
    
    if custom_config_type == "成長股篩選":
        st.sidebar.write("**成長股篩選參數**")
        
        # 營收CAGR設定
        revenue_cagr_enabled = st.sidebar.checkbox("啟用營收CAGR篩選", value=True)
        revenue_cagr_threshold = st.sidebar.slider(
            "營收CAGR閾值 (%)", 0.0, 50.0, 15.0, 1.0
        ) if revenue_cagr_enabled else 0.0
        revenue_cagr_years = st.sidebar.selectbox(
            "營收CAGR評估年數", [3, 5, 7], index=1
        ) if revenue_cagr_enabled else 5
        
        # EPS CAGR設定
        eps_cagr_enabled = st.sidebar.checkbox("啟用EPS CAGR篩選", value=True)
        eps_cagr_threshold = st.sidebar.slider(
            "EPS CAGR閾值 (%)", 0.0, 50.0, 20.0, 1.0
        ) if eps_cagr_enabled else 0.0
        eps_cagr_years = st.sidebar.selectbox(
            "EPS CAGR評估年數", [3, 5, 7], index=1
        ) if eps_cagr_enabled else 5
        
        # ROE設定
        roe_enabled = st.sidebar.checkbox("啟用ROE篩選", value=True)
        roe_threshold = st.sidebar.slider(
            "ROE閾值 (%)", 0.0, 50.0, 15.0, 1.0
        ) if roe_enabled else 0.0
        
        # 邏輯運算子
        logic_operator = st.sidebar.selectbox(
            "篩選邏輯", ["AND", "OR"], 
            help="AND: 所有條件都要滿足, OR: 滿足任一條件即可"
        )
        
        if st.sidebar.button("💾 保存成長股配置"):
            if config_name.strip():
                custom_growth_config = UserGrowthConfig(
                    name=config_name,
                    description=config_description,
                    revenue_cagr_enabled=revenue_cagr_enabled,
                    revenue_cagr_threshold=revenue_cagr_threshold/100,
                    revenue_cagr_years=revenue_cagr_years,
                    eps_cagr_enabled=eps_cagr_enabled,
                    eps_cagr_threshold=eps_cagr_threshold/100,
                    eps_cagr_years=eps_cagr_years,
                    roe_enabled=roe_enabled,
                    roe_threshold=roe_threshold/100,
                    debt_ratio_enabled=False,
                    debt_ratio_threshold=0.5,
                    margin_enabled=False,
                    margin_threshold=0.1,
                    logic_operator=logic_operator,
                    min_market_cap=None,
                    exclude_industries=[],
                    custom_conditions=[]
                )
                
                success = st.session_state.config_manager.save_growth_config(custom_growth_config)
                if success:
                    st.sidebar.success(f"✅ 成長股配置已保存：{config_name}")
                else:
                    st.sidebar.error("❌ 保存配置失敗")
            else:
                st.sidebar.error("❌ 請輸入配置名稱")
    
    elif custom_config_type == "DCF估值":
        st.sidebar.write("**DCF估值參數**")
        
        # DCF 參數設定
        custom_short_growth = st.sidebar.slider("短期成長率 (%)", 5.0, 25.0, 10.0, 0.5)
        custom_terminal_growth = st.sidebar.slider("終端成長率 (%)", 1.0, 8.0, 3.5, 0.1)
        custom_risk_pref = st.sidebar.slider("風險偏好 (%)", 5.0, 15.0, 7.0, 0.1)
        custom_proj_years = st.sidebar.selectbox("預測年數", [3, 4, 5, 6, 7], index=2)
        custom_screening_threshold = st.sidebar.slider("篩選閾值 (%)", 5.0, 50.0, 15.0, 1.0)
        
        # 進階設定
        custom_enable_anomaly = st.sidebar.checkbox("啟用異常檢測", value=True)
        custom_anomaly_threshold = st.sidebar.slider("異常檢測閾值", 1.0, 3.0, 1.5, 0.1)
        
        if st.sidebar.button("💾 保存DCF配置"):
            if config_name.strip():
                custom_dcf_config = UserDCFConfig(
                    name=config_name,
                    description=config_description,
                    short_term_growth_rate=custom_short_growth/100,
                    terminal_growth_rate=custom_terminal_growth/100,
                    risk_preference=custom_risk_pref/100,
                    projection_years=custom_proj_years,
                    screening_threshold=custom_screening_threshold/100,
                    enable_anomaly_detection=custom_enable_anomaly,
                    anomaly_threshold=custom_anomaly_threshold,
                    calculation_method="enhanced",
                    fcf_optimization={
                        "maintenance_capex_ratio": 0.6,
                        "working_capital_limit": 0.3,
                        "heavy_asset_threshold": 0.15
                    },
                    industry_adjustments={}
                )
                
                success = st.session_state.config_manager.save_dcf_config(custom_dcf_config)
                if success:
                    st.sidebar.success(f"✅ DCF配置已保存：{config_name}")
                else:
                    st.sidebar.error("❌ 保存配置失敗")
            else:
                st.sidebar.error("❌ 請輸入配置名稱")

elif config_tab == "台股預設自訂":
    st.sidebar.write("🛠️ **台股預設自訂**")
    
    # 讓使用者選擇要自訂的預設
    all_growth_presets = get_all_taiwan_growth_presets()
    all_dcf_presets = get_all_taiwan_dcf_presets()
    all_industry_presets = get_all_taiwan_industry_presets()
    
    preset_options = {
        "成長股篩選": all_growth_presets,
        "DCF 估值": all_dcf_presets,
        "產業特定": all_industry_presets
    }
    
    # 讓使用者選擇預設類型
    preset_type = st.sidebar.selectbox(
        "選擇預設類型",
        list(preset_options.keys()),
        help="選擇要自訂的預設類型"
    )
    
    selected_preset = None
    selected_preset_name = None
    selected_preset_key = None
    
    if preset_type and preset_type in preset_options:
        presets = preset_options[preset_type]
        
        # 讓使用者選擇具體的預設
        preset_names = [preset.name for preset in presets.values()]
        selected_preset_name = st.sidebar.selectbox(
            f"選擇{preset_type}預設",
            preset_names,
            help=f"選擇要自訂的{preset_type}預設配置"
        )
        
        # 根據選擇的預設名稱獲取對應的預設物件
        selected_preset = next((p for p in presets.values() if p.name == selected_preset_name), None)
        selected_preset_key = next((k for k, p in presets.items() if p.name == selected_preset_name), None)
        
        if selected_preset:
            # 顯示當前預設的詳細參數
            st.sidebar.write("**當前預設參數**")
            for key, value in selected_preset.__dict__.items():
                if not key.startswith("_"):  # 排除私有屬性
                    st.sidebar.write(f"**{key}:** {value}")
            
            # 讓使用者修改預設參數
            st.sidebar.write("**修改預設參數**")
              # 根據預設類型顯示對應的參數欄位
            if preset_type == "成長股篩選":
                st.sidebar.write("**自訂成長股篩選參數**")
                
                # 營收CAGR設定（預設啟用）
                revenue_cagr_enabled = st.sidebar.checkbox("啟用營收CAGR篩選", value=True)
                revenue_cagr_threshold = st.sidebar.slider(
                    "營收CAGR閾值 (%)",
                    0.0, 50.0,
                    selected_preset.revenue_cagr_threshold * 100,  # 轉換為百分比顯示
                    1.0
                ) if revenue_cagr_enabled else 0.0
                revenue_cagr_years = st.sidebar.selectbox(
                    "營收CAGR評估年數",
                    [3, 5, 7],
                    index=1  # 預設選擇5年
                ) if revenue_cagr_enabled else 5
                
                # EPS CAGR設定（預設啟用）
                eps_cagr_enabled = st.sidebar.checkbox("啟用EPS CAGR篩選", value=True)
                eps_cagr_threshold = st.sidebar.slider(
                    "EPS CAGR閾值 (%)",
                    0.0, 50.0,
                    selected_preset.eps_cagr_threshold * 100,  # 轉換為百分比顯示
                    1.0
                ) if eps_cagr_enabled else 0.0
                eps_cagr_years = st.sidebar.selectbox(
                    "EPS CAGR評估年數",
                    [3, 5, 7],
                    index=1  # 預設選擇5年
                ) if eps_cagr_enabled else 5
                
                # ROE設定（預設啟用）
                roe_enabled = st.sidebar.checkbox("啟用ROE篩選", value=True)
                roe_threshold = st.sidebar.slider(
                    "ROE閾值 (%)",
                    0.0, 50.0,
                    selected_preset.roe_threshold * 100,  # 轉換為百分比顯示
                    1.0
                ) if roe_enabled else 0.0
                
                # 最小市值設定
                min_market_cap = st.sidebar.slider(
                    "最小市值 (億台幣)",
                    0.0, 1000.0,
                    selected_preset.min_market_cap,
                    10.0
                )
                
                # 邏輯運算子
                logic_operator = st.sidebar.selectbox(
                    "篩選邏輯",
                    ["AND", "OR"],
                    index=["AND", "OR"].index(selected_preset.logic_operator)
                )                
                # 輸入自訂配置名稱
                custom_config_name = st.sidebar.text_input(
                    "自訂配置名稱",
                    value=f"自訂_{selected_preset_name}",
                    help="輸入您的自訂配置名稱"
                )
                
                # 保存自訂預設
                if st.sidebar.button("💾 保存自訂預設"):
                    if custom_config_name.strip():
                        try:
                            custom_growth_config = UserGrowthConfig(
                                name=custom_config_name,
                                description=f"基於 {selected_preset_name} 的自訂配置",
                                revenue_cagr_enabled=revenue_cagr_enabled,
                                revenue_cagr_threshold=revenue_cagr_threshold/100,
                                revenue_cagr_years=revenue_cagr_years,
                                eps_cagr_enabled=eps_cagr_enabled,
                                eps_cagr_threshold=eps_cagr_threshold/100,
                                eps_cagr_years=eps_cagr_years,
                                roe_enabled=roe_enabled,
                                roe_threshold=roe_threshold/100,
                                debt_ratio_enabled=False,
                                debt_ratio_threshold=0.5,
                                margin_enabled=False,
                                margin_threshold=0.1,
                                logic_operator=logic_operator,
                                min_market_cap=min_market_cap,
                                exclude_industries=list(selected_preset.exclude_industries),
                                custom_conditions=[]
                            )
                              # 嘗試保存自訂配置
                            success = st.session_state.config_manager.save_growth_config(custom_growth_config)
                            if success:
                                st.sidebar.success(f"✅ 自訂預設已保存：{custom_growth_config.name}")
                                st.sidebar.info("💡 您可以在「保存/載入配置」分頁中管理已保存的配置")
                            else:
                                st.sidebar.error("❌ 保存自訂預設失敗")
                        except Exception as e:
                            st.sidebar.error(f"❌ 保存自訂預設時發生錯誤：{str(e)}")
                    else:
                        st.sidebar.error("❌ 請輸入配置名稱")
        
            elif preset_type == "DCF 估值":
                st.sidebar.write("**自訂DCF估值參數**")
                
                # DCF 參數設定
                custom_short_growth = st.sidebar.slider("短期成長率 (%)", 5.0, 25.0, selected_preset.short_term_growth_rate * 100, 0.5)
                custom_terminal_growth = st.sidebar.slider("終端成長率 (%)", 1.0, 8.0, selected_preset.terminal_growth_rate * 100, 0.1)
                custom_risk_pref = st.sidebar.slider("風險偏好 (%)", 5.0, 15.0, selected_preset.risk_preference * 100, 0.1)
                custom_proj_years = st.sidebar.selectbox("預測年數", [3, 4, 5, 6, 7], index=selected_preset.projection_years - 3)
                custom_screening_threshold = st.sidebar.slider("篩選閾值 (%)", 5.0, 50.0, selected_preset.screening_threshold * 100, 1.0)
                
                # 進階設定
                custom_enable_anomaly = st.sidebar.checkbox("啟用異常檢測", value=selected_preset.enable_anomaly_detection)
                custom_anomaly_threshold = st.sidebar.slider("異常檢測閾值", 1.0, 3.0, 1.5, 0.1) if custom_enable_anomaly else 1.5
                
                # 輸入自訂配置名稱
                custom_dcf_config_name = st.sidebar.text_input(
                    "自訂DCF配置名稱",
                    value=f"自訂_{selected_preset_name}",
                    help="輸入您的自訂DCF配置名稱"
                )
                
                if st.sidebar.button("💾 保存自訂DCF預設"):
                    if custom_dcf_config_name.strip():
                        try:
                            custom_dcf_config = UserDCFConfig(
                                name=custom_dcf_config_name,
                                description=f"基於 {selected_preset_name} 的自訂DCF配置",
                                short_term_growth_rate=custom_short_growth/100,
                                terminal_growth_rate=custom_terminal_growth/100,
                                risk_preference=custom_risk_pref/100,
                                projection_years=custom_proj_years,
                                screening_threshold=custom_screening_threshold/100,
                                enable_anomaly_detection=custom_enable_anomaly,
                                anomaly_threshold=custom_anomaly_threshold,
                                calculation_method="enhanced",
                                fcf_optimization={
                                    "maintenance_capex_ratio": 0.6,
                                    "working_capital_limit": 0.3,
                                    "heavy_asset_threshold": 0.15
                                },
                                industry_adjustments={}
                            )
                            
                            # 嘗試保存自訂配置
                            success = st.session_state.config_manager.save_dcf_config(custom_dcf_config)
                            if success:
                                st.sidebar.success(f"✅ 自訂DCF預設已保存：{custom_dcf_config.name}")
                                st.sidebar.info("💡 您可以在「保存/載入配置」分頁中管理已保存的配置")
                            else:
                                st.sidebar.error("❌ 保存自訂DCF預設失敗")
                        except Exception as e:
                            st.sidebar.error(f"❌ 保存自訂DCF預設時發生錯誤：{str(e)}")
                    else:
                        st.sidebar.error("❌ 請輸入DCF配置名稱")            
            else:  # 產業特定
                st.sidebar.write("**產業特定預設配置**")
                st.sidebar.info("💡 產業特定預設配置主要用於應用，目前暫不支援自訂功能")
                
                # 顯示當前選擇的產業特定預設詳情
                with st.sidebar.expander("📋 當前預設詳情"):
                    st.write(f"**名稱:** {selected_preset.name}")
                    st.write(f"**描述:** {selected_preset.description}")
                    st.write(f"**推薦用於:** {selected_preset.recommended_for}")
                    st.write(f"**適用產業:** {', '.join(selected_preset.industry_names)}")
                
                # 可以選擇直接應用此預設
                if st.sidebar.button("🚀 直接應用此產業預設"):
                    try:
                        apply_taiwan_industry_preset(selected_preset_key, machine.context)
                        st.sidebar.success(f"✅ 已應用產業預設：{selected_preset_name}")
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"❌ 應用預設失敗：{str(e)}")

# === 保存/載入配置 ===
elif config_tab == "保存/載入配置":
    st.sidebar.write("📂 **配置檔案管理**")
    
    # 載入保存的配置
    saved_configs = st.session_state.config_manager.list_all_configs()
    
    if saved_configs:
        config_names = [config["name"] for config in saved_configs]
        
        selected_config_name = st.sidebar.selectbox(
            "選擇保存的配置",
            ["選擇配置..."] + config_names,
            help="選擇要載入的已保存配置"
        )
        
        if selected_config_name != "選擇配置...":
            selected_config = next(c for c in saved_configs if c["name"] == selected_config_name)
            
            # 顯示配置詳情
            with st.sidebar.expander("📋 配置詳情"):
                st.write(f"**名稱:** {selected_config['name']}")
                st.write(f"**描述:** {selected_config.get('description', 'N/A')}")
                st.write(f"**類型:** {selected_config['category']}")
                st.write(f"**創建時間:** {selected_config.get('created_at', 'N/A')}")
                st.write(f"**使用次數:** {selected_config.get('usage_count', 0)}")
            
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if st.button("📥 載入配置", help="載入選擇的配置到系統"):
                    try:
                        success = st.session_state.config_manager.load_and_apply_config(
                            selected_config["id"], machine.context
                        )
                        if success:
                            st.sidebar.success(f"✅ 已載入配置：{selected_config_name}")
                            st.rerun()
                        else:
                            st.sidebar.error("❌ 載入配置失敗：配置檔案可能已損壞")
                            st.sidebar.info("💡 請嘗試重新創建配置或聯繫技術支援")
                    except Exception as e:
                        st.sidebar.error(f"❌ 載入配置時發生錯誤：{str(e)}")
                        st.sidebar.info("💡 請檢查配置檔案完整性")
            
            with col2:
                if st.button("🗑️ 刪除配置", help="刪除選擇的配置"):
                    try:
                        success = st.session_state.config_manager.delete_config(selected_config["id"])
                        if success:
                            st.sidebar.success(f"✅ 已刪除配置：{selected_config_name}")
                            st.rerun()
                        else:
                            st.sidebar.error("❌ 刪除配置失敗：找不到指定的配置檔案")
                            st.sidebar.info("💡 配置可能已被刪除或檔案系統存在問題")
                    except Exception as e:
                        st.sidebar.error(f"❌ 刪除配置時發生錯誤：{str(e)}")
                        st.sidebar.info("💡 請檢查檔案權限或聯繫技術支援")
    
    else:
        st.sidebar.info("📝 尚未保存任何配置")
    
    # 匯出/匯入配置
    st.sidebar.write("**配置檔案分享**")
    
    if saved_configs:
        # 匯出配置
        export_config_name = st.sidebar.selectbox(
            "選擇要匯出的配置",
            ["選擇配置..."] + [config["name"] for config in saved_configs],
            help="選擇要匯出分享的配置"
        )
        
        if export_config_name != "選擇配置..." and st.sidebar.button("📤 匯出配置"):
            export_config = next(c for c in saved_configs if c["name"] == export_config_name)
            config_json = st.session_state.config_manager.export_config(export_config["id"])
            if config_json:
                st.sidebar.download_button(
                    label="💾 下載配置檔案",
                    data=config_json,
                    file_name=f"{export_config_name}_config.json",
                    mime="application/json",
                    help="下載配置檔案以分享給其他用戶"
            )
    
    # 匯入配置
    uploaded_config = st.sidebar.file_uploader(
        "📁 匯入配置檔案",
        type=['json'],
        help="上傳其他用戶分享的配置檔案"
    )
    
    if uploaded_config is not None:
        try:
            config_data = json.load(uploaded_config)
            success = st.session_state.config_manager.import_config(config_data)
            if success:
                st.sidebar.success("✅ 配置匯入成功")
                st.rerun()
            else:
                st.sidebar.error("❌ 配置匯入失敗：格式不正確或配置不相容")
                st.sidebar.info("💡 請確認上傳的是有效的JoJoTrading配置檔案")
        except json.JSONDecodeError:
            st.sidebar.error("❌ 配置匯入失敗：檔案不是有效的JSON格式")
            st.sidebar.info("💡 請確認上傳的檔案是正確的配置JSON檔案")
        except UnicodeDecodeError:
            st.sidebar.error("❌ 配置匯入失敗：檔案編碼錯誤")
            st.sidebar.info("💡 請確認檔案使用UTF-8編碼")
        except Exception as e:
            st.sidebar.error(f"❌ 配置匯入失敗：{str(e)}")
            st.sidebar.info("💡 請檢查檔案完整性或聯繫技術支援")

# 顯示當前使用的配置資訊
current_config_info = st.sidebar.container()
with current_config_info:
    st.markdown("---")
    st.write("**📊 當前配置狀態**")
    
    # 檢查是否使用預設配置
    if machine.context.get('applied_preset_name'):
        st.info(f"🏭 使用預設：{machine.context['applied_preset_name']}")
    elif machine.context.get('applied_custom_config'):
        st.info(f"🎨 自定義配置：{machine.context['applied_custom_config']}")
    else:
        st.info("🔧 使用系統默認配置")
    
    # 快速重置按鈕
    if st.button("🔄 重置為系統默認", help="重置所有配置為系統默認值"):
        # 重置為 DCF_OPTIMIZED_CONFIG 默認值
        machine.context.update({
            'dcf_short_term_growth_rate': DCF_OPTIMIZED_CONFIG['dcf_short_term_growth_rate'],
            'dcf_terminal_growth_rate': DCF_OPTIMIZED_CONFIG['dcf_terminal_growth_rate'],
            'risk_preference': DCF_OPTIMIZED_CONFIG['risk_preference'],
            'dcf_projection_years': DCF_OPTIMIZED_CONFIG['dcf_projection_years'],
            'screening_threshold': DCF_OPTIMIZED_CONFIG['screening_threshold'],
            'applied_preset_name': None,
            'applied_custom_config': None
        })
        st.sidebar.success("✅ 已重置為系統默認配置")
        st.rerun()

# 顯示當前設定狀態
if machine.context.get('use_enhanced_dcf', True):
    st.sidebar.success("🚀 增強版 DCF 已啟用")
else:
    st.sidebar.info("📊 使用標準版 DCF")

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
        actual_risk_preference = machine.context.get('default_risk_premium', 0.04)    # 新增：最小潛在報酬率篩選輸入（僅產業篩選模式顯示）
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

    # 新增：成長股判定設定
    st.subheader("🚀 成長股判定設定")
    
    enable_growth_filter = st.checkbox(
        "啟用成長股過濾 (僅對成長股進行DCF估值)",
        value=machine.context.get('enable_growth_filter', True),
        help="開啟後，系統將先判定成長股，再進行DCF估值"
    )
    if enable_growth_filter:
        # 快速配置選項
        st.write("**📊 快速配置：**")
        
        config_options = {
            "自訂設定": "custom",
            "推薦配置 (平衡型)": "recommended", 
            "積極成長型": "aggressive",
            "穩健保守型": "conservative",
            "科技股專用": "tech_focused"
        }
        
        selected_config = st.selectbox(
            "選擇預設配置",
            options=list(config_options.keys()),
            index=0,
            help="選擇預設配置可快速套用優化參數，或選擇自訂設定手動調整"
        )
        
        # 如果選擇了預設配置，應用配置
        if selected_config != "自訂設定":
            try:
                from growth_stock_optimization_config import apply_config_to_context, get_optimized_config
                config_name = config_options[selected_config]
                machine.context = apply_config_to_context(machine.context, config_name)
                
                # 顯示配置描述
                config = get_optimized_config(config_name)
                st.info(f"✅ 已套用「{config.name}」配置\n\n{config.description}")
                st.write(f"**適用情境：** {config.recommended_for}")
                
                # 顯示配置詳情
                with st.expander("查看配置詳情"):
                    st.write(f"**邏輯運算：** {config.criteria_set.logic_operator}")
                    for criterion in config.criteria_set.criteria:
                        threshold_pct = criterion.threshold * 100
                        st.write(f"• {criterion.label.replace(f'> {threshold_pct:.0f}%', f'> {threshold_pct:.1f}%')}")
            except ImportError:
                st.warning("優化配置模組載入失敗，請使用自訂設定")
        
        st.write("**📋 成長股判定條件：**")
        
        # 營收CAGR條件
        revenue_cagr_enabled = st.checkbox(
            "近3年營收CAGR",
            value=machine.context.get('revenue_cagr_enabled', True)
        )
        revenue_cagr_threshold = 15.0
        if revenue_cagr_enabled:
            revenue_cagr_threshold = st.number_input(
                "營收CAGR閾值 (%)",
                min_value=0.0,
                max_value=100.0,
                value=machine.context.get('revenue_cagr_threshold', 15.0),
                step=1.0
            )
        
        # EPS CAGR條件
        eps_cagr_enabled = st.checkbox(
            "近3年EPS CAGR",
            value=machine.context.get('eps_cagr_enabled', True)
        )
        eps_cagr_threshold = 15.0
        if eps_cagr_enabled:
            eps_cagr_threshold = st.number_input(
                "EPS CAGR閾值 (%)",
                min_value=0.0,
                max_value=100.0,
                value=machine.context.get('eps_cagr_threshold', 15.0),
                step=1.0
            )
        
        # ROE條件
        roe_enabled = st.checkbox(
            "最新ROE",
            value=machine.context.get('roe_enabled', True)
        )
        roe_threshold = 15.0
        if roe_enabled:
            roe_threshold = st.number_input(
                "ROE閾值 (%)",
                min_value=0.0,
                max_value=100.0,
                value=machine.context.get('roe_threshold', 15.0),
                step=1.0
            )
        
        # 邏輯運算符
        growth_logic_operator = st.radio(
            "條件組合邏輯：",
            options=["AND (所有條件都要符合)", "OR (任一條件符合即可)"],
            index=0 if machine.context.get('growth_logic_operator', 'AND') == 'AND' else 1,
            horizontal=True
        )
        
        # 保存成長股設定到context
        machine.context['enable_growth_filter'] = enable_growth_filter
        machine.context['revenue_cagr_enabled'] = revenue_cagr_enabled
        machine.context['revenue_cagr_threshold'] = revenue_cagr_threshold
        machine.context['eps_cagr_enabled'] = eps_cagr_enabled
        machine.context['eps_cagr_threshold'] = eps_cagr_threshold
        machine.context['roe_enabled'] = roe_enabled
        machine.context['roe_threshold'] = roe_threshold
        machine.context['growth_logic_operator'] = 'AND' if 'AND' in growth_logic_operator else 'OR'

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
        df_display.columns = [column_map.get(col, col) for col in df_display.columns]        # st.dataframe 顯示
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # 下載功能 - 只在有結果時才顯示
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
                with open(csv_path, "rb") as f:                    st.download_button(
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

    else:
        st.info("沒有篩選到符合條件的股票，或仍在處理中。請檢查篩選條件或資料來源。")

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
