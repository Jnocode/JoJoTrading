# JoJoTrading (Streamlit Version)

本專案旨在開發一套以折現估價法（DCF）自動計算台股各產業成分股合理價值，並篩選出潛在報酬率高之特價股的工具，最終以 Streamlit Web 應用程式呈現給一般投資人。

---

## 核心功能與架構

-   **狀態機驅動流程 (`jojo_state_machine.py`)**:
    *   應用程式核心邏輯由狀態機管理，包含設定載入、UI 互動、資料抓取、估值計算、結果篩選、結果展示與匯出等狀態。
    *   有利於流程控制、錯誤處理及未來擴充。
-   **資料處理模組 (`data_handler.py`)**:
    *   **上市公司資料獲取**: 自動從臺灣證券交易所 (TWSE) OpenAPI 下載並緩存所有上市公司基本資料 (`all_companies_basic_data.json`)。
    *   **產業成分股篩選**: 根據使用者選擇的產業，從基本資料中篩選出該產業的成分股，並記錄其代號、名稱、公司全名、財報編制類型及產業代號。
    *   **智能財報 API 選擇與下載**:
        *   根據股票的產業別、公司名稱關鍵字（特別是金融業）等，動態選擇對應的 TWSE 損益表 API 端點 (一般業 `_ci`, 金控業 `_fh`, 證券期貨業 `_bd`, 保險業 `_ins`, 銀行業 `_basi`, 異業 `_mim`)。
    *   實現按需下載並緩存各類財報 JSON 數據。
    *   **財務數據提取**: 從已下載的財報中，根據預先校驗的欄位名稱映射 (`FINANCIAL_FIELD_NAMES_MAP`)，提取特定股票最新的 EPS、主要營收及淨利歸母數據。已修正財報金額單位問題（千元轉為元）。
    *   **DCF 估值函式**: `calculate_dcf_valuation` 函式目前實現了基於「每股淨利」作為自由現金流（FCFEps）代理的簡化版DCF計算邏輯。
-   **Streamlit 使用者介面 (`app.py`)**:
    *   提供一個易於操作的 Web 介面。
    *   使用者可選擇目標產業及風險偏好參數。
    *   狀態機實例透過 `st.session_state` 在使用者互動間保持狀態。
    *   逐步展示處理進度，並最終呈現篩選結果。
-   **設定檔 (`industries.json`)**:
    *   包含台股產業分類的中文名稱與 TWSE 代號的映射。
    *   定義預設的風險溢價及多個風險偏好選項供使用者選擇。
-   **開發規範與日誌**:
    *   遵循專案定義的 Cline Rules (`.clinerules/`)。
    *   開發進度記錄於 `DEVELOPER_LOG.md`。

---

## 安裝與啟動

1.  **建立虛擬環境並安裝依賴**：
    ```bash
    # (在專案根目錄下)
    py -m venv .venv
    .\.venv\Scripts\activate  # Windows PowerShell，其他系統請用對應指令
    pip install -r requirements.txt
    ```
    (目前 `requirements.txt` 包含 `streamlit`, `python-dotenv`, `requests`)

2.  **設定環境變數 (可選)**：
    *   如果未來串接需要 API 金鑰的服務 (例如券商 API)，請將金鑰資訊寫入專案根目錄下的 `.env` 檔案。`ConfigLoadState` 會嘗試載入。

3.  **啟動 Streamlit 應用程式**：
    ```bash
    # (確保虛擬環境已啟用)
    streamlit run app.py
    ```
    應用程式將在瀏覽器中打開 (通常是 `http://localhost:8501`)。

---

## 主要檔案結構 (Streamlit 版本)

-   `app.py`: Streamlit Web 應用程式主檔案。
-   `jojo_state_machine.py`: 核心狀態機及各狀態邏輯定義。
-   `data_handler.py`: 負責所有資料獲取、處理、API 串接及估值計算的模組。
-   `industries.json`: 產業分類及風險偏好等設定檔。
-   `all_companies_basic_data.json`: (自動生成) 緩存的上市公司基本資料。
-   `requirements.txt`: Python 依賴套件列表。
-   `DEVELOPER_LOG.md`: 開發日誌。
-   `.clinerules/`: 專案特定的 Cline 開發規則。
-   `STREAMLIT_ARCH_DIAGRAM.md`: 包含整體架構圖 (類圖、序列圖) 的 Mermaid 原始碼。
-   `class_diagram.mmd`: 類圖的獨立 Mermaid 原始碼檔案。
-   `sequence_diagram.mmd`: 序列圖的獨立 Mermaid 原始碼檔案。
-   `class_diagram.svg`: (手動生成) 類圖的 SVG 圖片檔案。
-   `sequence_diagram.svg`: (手動生成) 序列圖的 SVG 圖片檔案。
-   `.venv/`: (自動生成) Python 虛擬環境。

---

## 目前進度與待辦事項 (截至 2025-05-12)

-   **已完成**:
    *   核心狀態機流程搭建 (`jojo_state_machine.py`)。
    *   **數據獲取與處理 (`data_handler.py`)**:
        *   整合 TWSE OpenAPI 獲取上市公司基本資料及產業分類。
        *   整合 FinMind API 以獲取個股財務報表（資產負債表、現金流量表、綜合損益表）及每日股價。
        *   實現了本地數據快取機制 (`cache/`) 以減少重複 API 調用。
        *   解決了資本支出 (`capex`) 和折舊攤銷 (`depreciation`) 的提取問題，能夠從 FinMind 數據中獲取這些關鍵財務指標。
        *   修正了從 TWSE OpenAPI 提取財報時的金額單位問題（千元轉元）。
    *   **DCF 估值邏輯 (FCFE)**:
        *   `data_handler.calculate_dcf_valuation` 函式現在基於從 FinMind 獲取的數據（淨利、資本支出、折舊攤銷、營運資本變動等）來計算自由現金流量給股東 (FCFE) 並進行估值。
    *   **股票篩選邏輯 (`FilteringState`)**:
        *   根據 DCF 估值結果（潛在回報率、內在價值）進行篩選。
        *   調整了篩選邏輯：對於近期會計EPS為負但DCF估值良好的股票，不再直接過濾，而是在結果中加入警告信息。
    *   **Streamlit UI (`app.py`)**:
        *   提供了產業選擇、風險偏好設定等用戶輸入界面。
        *   修復了結果頁面不顯示以及「重新查詢」按鈕導航錯誤的問題。UI 現在能正確顯示篩選結果表格（包括帶警告的股票）並支持重新查詢。
    *   **狀態機初始化改進**:
        *   解決了 `JoJoStateMachine` 重複實例化的問題，確保狀態機實例在 Streamlit 的 session 中正確持久化。
    *   產生了專案架構的類圖和序列圖 (Mermaid 原始碼及 SVG 圖片)。

-   **待辦事項**:
    *   **實現年度計算選項**: 允許使用者選擇基於年度財務數據進行DCF估值（使用者提出的新功能）。
    *   **FinMind API 速率限制處理**:
        *   制定更穩健的應對策略（例如，在 `data_handler.py` 中為API調用實現帶有指數退避的重試邏輯）。
        *   在解決此問題後，移除或調整目前為測試而設的處理少量股票的臨時限制 (`limit_stocks` in `DataFetchState`)。
    *   **狀態機日誌與執行優化**: 雖然實例化問題已解決，但可進一步優化 Streamlit 腳本執行流程，減少不必要的日誌打印或計算，以提升整體流暢度和日誌清晰度。
    *   **數據完整性與備援**: 持續關注 FinMind API 數據的完整性（例如，某些股票仍可能缺少特定財務欄位），並考慮未來是否需要備援數據源或更完善的數據缺失處理機制。
    *   **實作 `ExportState`**: 實現將篩選結果匯出到檔案（如 CSV 或 Excel）的功能。
    *   **錯誤處理與 UI 反饋**: 持續增強各狀態的錯誤處理機制，並在用戶界面上提供更友好的錯誤提示和進度反饋。
    *   **擴展估值模型與篩選條件**: 未來可考慮加入更多估值模型（如股利折現模型 DDM）或更豐富的篩選條件。

---

## 聯絡與貢獻

歡迎 issue、pull request 或聯絡作者 xiujiang1987@gmail.com  
如需協作、功能客製、策略開發請來信洽詢。

---
