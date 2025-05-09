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
    *   **財務數據提取**: 從已下載的財報中，根據預先校驗的欄位名稱映射 (`FINANCIAL_FIELD_NAMES_MAP`)，提取特定股票最新的 EPS 和主要營收數據。
    *   **DCF 估值函式骨架**: 包含 `calculate_dcf_valuation` 函式的初步簡化版 DCF 計算邏輯。
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
-   `.venv/`: (自動生成) Python 虛擬環境。

---

## 目前進度與待辦事項 (截至 2025-05-10)

-   **已完成**:
    *   核心狀態機流程搭建。
    *   上市公司基本資料、產業成分股獲取。
    *   多種類型損益表 API 的智能選擇與下載框架。
    *   從損益表中提取 EPS 和主要營收。
    *   初步的 Streamlit UI 框架，可驅動流程。
    *   DCF 估值函式的初步骨架。
-   **待辦事項**:
    *   **完善 DCF 估值邏輯**: 在 `data_handler.calculate_dcf_valuation` 中實現完整的 DCF 計算，包括更合理的 FCF 估算、成長率假設、WACC（或折現率）的計算。
    *   **獲取更多財務數據**: 根據 DCF 模型需求，可能需要從資產負債表、現金流量表獲取更多數據，需擴充 `data_handler.py`。
    *   **實作 `FilteringState`**: 根據估值結果篩選股票。
    *   **實作 `ResultsDisplayState`**: 在 Streamlit UI 中美觀地展示估值和篩選結果。
    *   **實作 `ExportState`**: 實現結果匯出功能。
    *   **數據源覆蓋率問題**: TWSE OpenAPI 的財報數據可能不完整，需在估值時處理數據缺失情況，或未來考慮備援數據源。
    *   **金融業 API 選擇細化**: 持續優化 `data_handler.get_financial_reports_for_stock` 中對金融保險業子公司的判斷，或填充 `SPECIFIC_REPORT_API_MAP`。
    *   **錯誤處理與 UI 反饋**: 增強各狀態的錯誤處理和用戶界面反饋。

---

## 聯絡與貢獻

歡迎 issue、pull request 或聯絡作者 xiujiang1987@gmail.com  
如需協作、功能客製、策略開發請來信洽詢。

---
