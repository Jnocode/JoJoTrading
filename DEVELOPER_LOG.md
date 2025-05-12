# JoJoTrading 開發者日誌

## 2025-05-12

**本日重點：** 解決 FinMind API 數據提取（特別是 `capex`）、篩選邏輯、UI顯示及狀態機初始化等核心問題。

**詳細記錄：**

1.  **目標設定：**
    *   提高 FinMind API 數據提取的穩定性與完整性，特別是資本支出 (`capex`) 和折舊攤銷 (`depreciation`)。
    *   根據使用者回饋調整股票篩選邏輯，特別是針對近期會計EPS為負但DCF估值良好的情況。
    *   修復 Streamlit UI 結果頁面不顯示以及「重新查詢」按鈕導航錯誤的問題。
    *   解決狀態機重複實例化的問題。

2.  **FinMind API 數據提取優化：**
    *   **應對速率限制（臨時措施）**：
        *   在 `jojo_state_machine.py` 的 `DataFetchState` 中，將處理股票數量 (`limit_stocks`) 臨時限制為 3 支。
        *   在 `data_handler.py` 的 `fetch_finmind_financial_statement_data` 和 `fetch_finmind_stock_price` 函數中，將 API 調用前的 `time.sleep()` 延遲增加到 2.0 秒。
        *   測試表明，這些措施有助於在等待一段時間後成功請求，但並非根本解決方案。
    *   **`capex` 和 `depreciation` 提取修正**：
        *   通過 `test_finmind_api.py` 腳本分析了 '2314', '2330', '2317' 等股票的現金流量表，發現 `type` 為 `'PropertyAndPlantAndEquipment'` 且 `origin_name` 為「取得不動產、廠房及設備」的條目是 `capex` 的主要來源。
        *   在 `jojo_state_machine.py` 的 `DataFetchState` 中，更新了 `cf_items_map['capex']` 列表，將 `'PropertyAndPlantAndEquipment'` 作為首選候選欄位，並增加了其他相關備選欄位。
        *   同時擴充了 `cf_items_map['depreciation']` 的候選欄位列表。
        *   經過測試，`capex` 和 `depreciation` 的提取成功率顯著提高，使得後續的 FCFE 計算更為準確。

3.  **股票篩選邏輯調整：**
    *   根據使用者指示「保留近期會計EPS為正的要求，但作為次要考量或顯示警告」。
    *   修改了 `jojo_state_machine.py` 中的 `FilteringState`：
        *   主要篩選條件依然是潛在回報（Potential Return） >= 設定閾值（預設15%）**且** 內在價值（Intrinsic Value） > 0。
        *   對於滿足上述主要條件的股票，如果其最近報告的會計EPS（`source_eps`）為負或低於設定的最小EPS閾值（預設0.01），該股票**仍會被選入**最終結果列表，但在其結果數據中會新增一個 `warning` 欄位，內容為類似「近期會計EPS (X.XX) 為負或過低。」的提示。

4.  **UI 結果顯示與導航修復：**
    *   **問題**：先前UI在篩選完成後未正確跳轉到結果頁面，或結果頁面顯示不正確。
    *   **解決方案**：
        *   修改了 `jojo_state_machine.py` 中的 `ResultsDisplayState`，移除了其內部自動轉換回 `UI_INIT` 狀態的邏輯，使其保持在 `RESULTS_DISPLAY` 狀態，直到用戶通過UI操作觸發新的狀態轉換。
        *   修改了 `app.py` 中處理 `RESULTS_DISPLAY` 狀態的UI渲染邏輯：
            *   確保導入 `pandas as pd`。
            *   將 `filtered_results`（字典列表）轉換為 Pandas DataFrame 以便於使用 `st.dataframe`。
            *   動態生成 `column_config`，使其鍵與 DataFrame 的實際欄位名（如 `stock_code`, `name`, `warning` 等）匹配。
            *   對 `potential_return` 和 `used_discount_rate` 等百分比數據進行格式化處理，以便在表格中更友好地顯示。
            *   為新增的 `warning` 欄位添加了顯示配置。
        *   修改了 `app.py` 中「重新查詢」按鈕的事件處理邏輯，使其在點擊後明確調用 `machine.transition_to(JoJoState.UI_INIT)`，確保正確返回初始選擇界面。
    *   **驗證**：使用者已確認 UI 現在能夠正確顯示篩選結果（包括帶警告的股票），並且「重新查詢」按鈕功能恢復正常。

5.  **狀態機重複實例化問題解決：**
    *   **問題**：日誌顯示 `JoJoStateMachine initialized...` 訊息多次出現。
    *   **解決方案與驗證**：在 `app.py` 中圍繞狀態機初始化（`st.session_state['jojo_machine'] = JoJoStateMachine()`）的 `if 'jojo_machine' not in st.session_state:` 條件塊加入了調試打印語句。
    *   最新的日誌分析表明，`JoJoStateMachine()` 構造函數（即 `__init__` 方法）現在只在 `st.session_state` 中確實不存在 `jojo_machine` 實例時被調用一次。Streamlit 腳本本身的多次執行（例如，由於UI交互或 `st.rerun()`）現在會正確地從 `st.session_state` 中獲取已存在的狀態機實例，從而避免了重複創建。

**當前狀態：**

*   應用程式的核心流程——數據獲取（包括 `capex`）、DCF估值（基於FCFE）、股票篩選（帶有EPS警告機制）、UI結果展示和重新查詢導航——在目前限制處理3支股票的條件下運行通暢且符合預期。
*   主要的數據提取問題和UI顯示問題已得到解決。

**待辦事項/未來方向（優先級可能需要與使用者討論）：**

1.  **實現年度計算選項**：允許使用者選擇基於年度財務數據進行DCF估值。
2.  **移除/調整股票處理數量限制**：在實現更穩健的API速率限制處理策略後。
3.  **制定更穩健的FinMind API速率限制應對策略**：例如，在 `data_handler.py` 中為API調用實現帶有指數退避的重試邏輯。
4.  **（次要）進一步優化 Streamlit 腳本執行流程**：減少不必要的日誌打印或計算，以提升整體流暢度和日誌清晰度。

---

## 2025-05-09/10 深夜 - 狀態機、資料處理與UI初步搭建

### 1. Cline Rules 設定
- 建立了全域規則檔案 `GLOBAL_RULES.md`。
- 建立了專案工作區規則檔案 `JoJoTrading/.clinerules/JoJoTrading_RULES.md` 並更新引用。

### 2. 專案初始化與環境
- 建立 `requirements.txt` (streamlit, python-dotenv, requests)。
- 完成虛擬環境 `.venv` 的建立與依賴安裝。

### 3. 核心狀態機 (`jojo_state_machine.py`)
- 設計了包含設定載入、UI互動、資料抓取、估值、篩選、結果顯示、匯出的主要狀態流程。
- 建立了 `BaseState` 及各狀態類別骨架 (`ConfigLoadState`, `UiInitState`, `IndustryProcessState`, `DataFetchState`, `ValuationState`, `FilteringState`, `ResultsDisplayState`, `ExportState`, `ErrorState`, `EndState`)。
- `ConfigLoadState`: 實作載入 `.env` (預留) 和 `industries.json` (產業列表、風險溢價選項)。
- `DataFetchState`: 實作了調用 `data_handler` 中函式的邏輯，以獲取公司基本資料、篩選產業成分股、下載財報並提取財務數據。
- `ValuationState`: 加入了調用 `calculate_dcf_valuation` 的基本流程框架。

### 4. 資料處理模組 (`data_handler.py`)
- `get_all_companies_basic_data`: 從 TWSE OpenAPI 獲取所有上市公司基本資料，並緩存至 `all_companies_basic_data.json`。
- `filter_industry_stocks`: 根據選擇的產業中文名（透過 `industry_name_to_code_map` 轉為代號）篩選成分股，並記錄其 `code`, `name`, `full_name`, `report_type`, `industry_code`。
- `get_financial_reports_for_stock`: 根據股票的 `industry_code`, `report_type`, `name` (公司簡稱/全名)，智能判斷應使用的損益表 API 後綴 (`_ci`, `_fh`, `_bd`, `_ins`, `_basi`, `_mim`)，並按需下載及緩存對應的完整財報 JSON。
- `fetch_stock_financials_from_downloaded`: 從已下載的財報數據中，根據 `api_suffix` 和 `FINANCIAL_FIELD_NAMES_MAP` 提取特定股票最新的 EPS 和主要營收數據。
- `FINANCIAL_FIELD_NAMES_MAP`: 已根據實際查閱各類財報 API JSON 結構進行了校驗和確認。
- `calculate_dcf_valuation`: 新增了此函式的初步骨架，包含簡化的 DCF 計算假設。
- 解決了多次 `NameError` 和 SSL 憑證驗證問題 (`verify=False`)。

### 5. UI 介面 (`app.py`)
- 建立了 Streamlit 應用程式的初步框架，能夠驅動狀態機。
- 實現了狀態機在 `st.session_state` 中的持久化。
- `UI_INIT` 狀態能正確顯示從 `industries.json` 載入的產業下拉選單和風險補償選項。
- 修正了 `st.experimental_rerun` 為 `st.rerun`。
- Streamlit 應用可成功啟動並根據使用者選擇執行到資料獲取和（模擬的）估值、篩選、結果顯示流程。

### 6. 設定檔
- `industries.json`: 建立並完善了包含產業中文名稱、TWSE產業代號、預設風險溢價和選項的設定檔。

### 7. 待辦事項與已知問題
- **數據源覆蓋率**：TWSE OpenAPI 的各類財報 API（尤其金融子行業）可能不包含所有公司的最新季度財報，導致部分股票無法獲取財務數據。`ValuationState` 需能處理此情況。
- **金融業API選擇細化**：`data_handler.get_financial_reports_for_stock` 中對金融保險業 (17) 的子行業判斷邏輯（基於公司名稱關鍵字）可能仍需根據更多測試結果進行微調，或通過 `SPECIFIC_REPORT_API_MAP` 進行特例管理。
- **`SPECIFIC_REPORT_API_MAP` 填充**：需要進一步分析 `all_companies_basic_data.json`，將不適用一般判斷規則的公司加入此映射表。
- **DCF估值邏輯**：`calculate_dcf_valuation` 目前僅為骨架，需實作完整的DCF計算公式，並考慮如何獲取或估算 FCF、成長率、WACC 等參數。
- **後續狀態實作**：`FilteringState`, `ResultsDisplayState` (真實數據展示), `ExportState` 仍為模擬邏輯。
- **錯誤處理與UI反饋**：需要增強各狀態的錯誤處理和在 Streamlit UI 上的用戶友好反饋。

### 8. 架構圖生成
- 在 `STREAMLIT_ARCH_DIAGRAM.md` 中編寫了類圖和序列圖的 Mermaid 語法。
- 將 Mermaid 語法分別提取到 `class_diagram.mmd` 和 `sequence_diagram.mmd`。
- 指導了如何使用線上 Mermaid 編輯器將 `.mmd` 檔案轉換為 SVG 圖片。
- 使用者已成功生成 `class_diagram.svg` 和 `sequence_diagram.svg` 並存放於專案根目錄。

---

## 2025-05-05 專案需求確認與技術選型討論紀錄

### 1. 專案需求摘要

- 目標：以折現估價法（DCF）自動計算台股各產業成分股合理價值，過濾出潛在報酬率高的特價股，推薦給一般投資人。
- 流程：產業選擇 → 自動抓取成分股與財報 → 批次估值 → 過濾推薦 → 顯示/匯出清單。
- 介面：極簡單頁操作，適合一般投資人，公式透明，可後續擴充。

### 2. 技術選型討論

- 綜合需求（API串接、資料處理、Excel自動化、極簡GUI、批次估值、匯出等）後，決定採用：

  - __Python + Streamlit__ 為主體
  - 輔以 pandas、requests、openpyxl/xlwings 等套件
  - Streamlit 實現單頁極簡Web介面，支援桌面與手機

- 其他選項（JS/TS、Excel VBA、R等）評估後不如 Python + Streamlit 適合本專案

### 3. 開發流程規劃

1. 專案初始化（資料夾、Git、requirements.txt等）
2. API串接模組（TPEx/TWSE OpenAPI）
3. 資料處理與DCF估值邏輯
4. Excel自動化或pandas批次估值
5. Streamlit前端介面
6. 測試與優化
7. 文件與部署

## 2025-04-30

- **詳細設計會議結論：**
    - **模組分工**：
        - 資料抓取模組：整合永豐API，備援Yahoo/公開資料
        - 估值模組：Excel DCF公式轉Python函式
        - UI模組：Streamlit介面（產業選擇、風險補償下拉選單）
        - 匯出模組：支援Excel/Word/PDF/圖片
    - **風險補償設計**：
        - 下拉選單選項：2.5%過度樂觀、3%樂觀、4%正常、5%悲觀、6%極度悲觀、自訂
        - 自訂時支援手動輸入百分比
    - **UI原型**：
        - 主畫面：產業選擇 + 風險補償選單 + [開始篩選] 按鈕
        - 結果頁面：表格顯示股票資訊 + 多格式匯出按鈕
    - **匯出格式**：
        - Excel：pandas.to_excel()
        - Word：python-docx 建立表格
        - PDF：pdfkit 將HTML轉PDF
        - 圖片：matplotlib 繪製表格後存圖

- **下一步：**
    - 確認模組分工與技術選型
    - 開發資料抓取模組（永豐API）
    - 設計Streamlit UI元件原型

---
