# JoJoTrading 開發者日誌

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
