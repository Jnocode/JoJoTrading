# JoJoTrading Project Workspace Rules (JoJoTrading 專案工作區規則)

本文件定義 JoJoTrading 專案特定的開發規則，旨在補充或覆蓋位於 `D:/Users/Jun/Documents/Cline/GLOBAL_RULES.md` 中的全域規則。

## 1. 資料處理與安全性 (Data Handling & Security)
- **API 金鑰管理:**
    - 所有 API 金鑰（例如券商 API、市場數據 API）必須儲存在專案根目錄下的 `.env` 檔案中。
    - `.env` 檔案必須被加入到 `.gitignore` 中，確保不會提交到版本控制。
    - 程式碼中應透過讀取環境變數的方式取得 API 金鑰。
- **資料驗證:**
    - 從外部 API 獲取的市場數據（價格、成交量等）在使用前必須進行基本驗證（例如，檢查是否為數字、是否在合理範圍內）。
    - 使用者輸入（若有）必須進行嚴格的驗證與清理，防止潛在的注入風險。
- **錯誤處理:**
    - 所有 API 呼叫都應包含 `try-catch` 區塊，並對可能的錯誤（如網路問題、API 錯誤回應）進行處理。
    - 重要的錯誤應記錄到 `DEVELOPER_LOG.md` 或指定的日誌系統。

## 2. 股票篩選邏輯 (Stock Filtering Logic)
- **文件同步:**
    - 每當 `Stock_filtering/` 目錄下的篩選邏輯有任何修改、新增或移除時，必須同步更新 `Stock_filtering/README.md` 中的相關說明。
    - `Stock_filtering/README.md` 應清楚描述每個篩選條件的目的、參數及使用範例。
- **模組化:**
    - 每個獨立的篩選條件應盡可能模組化，方便單獨測試與重複使用。
- **可配置性:**
    - 篩選條件的參數（如移動平均線天數、成交量閾值）應設計為可配置的，而不是硬編碼在程式中。

## 3. 開發流程與需求 (Development Workflow & Requirements)
- **遵循 `DEV_FLOW_AND_REQUIREMENTS.md`:**
    - 所有開發活動，包括新功能開發、錯誤修復、重構等，都必須遵循 `DEV_FLOW_AND_REQUIREMENTS.md` 中定義的流程。
- **Commit 訊息:**
    - 除了遵循全域 Conventional Commits 格式外，針對 JoJoTrading 的 commit 訊息應更具體描述與交易邏輯或股票分析相關的變更。
    - 例如: `feat(filter): 新增 MACD 黃金交叉篩選條件`, `fix(api): 修正 Shioaji API 連線逾時問題`。
- **日誌記錄:**
    - 參照 `DEVELOPER_LOG.md` 的現有格式與內容，持續記錄開發過程中的重要決策、遇到的問題、解決方案以及實驗結果。
- **程式碼模組化 (Code Modularization):**
    - **職責分離:** 不同功能的程式碼應盡可能分離到獨立的模組或檔案中。例如，資料獲取邏輯 (如 API 串接、原始資料處理) 應與狀態機流程控制、UI 呈現等核心邏輯分開。
    - **可重用性:** 設計模組時應考慮其可重用性，將通用功能封裝成函式或類別。
    - **降低耦合:** 模組之間應盡量降低耦合度，透過清晰的介面 (函式參數、回傳值) 進行互動。
    - **檔案大小管理:** 注意單一 Python 檔案的行數，過於龐大的檔案應考慮拆分為更小的、功能集中的模組。例如，狀態機定義檔案 (`jojo_state_machine.py`) 應主要包含狀態定義和流程控制，而將複雜的狀態執行邏輯（如資料處理、API呼叫）移至輔助模組（如 `data_handler.py`）。

## 4. API 使用 (API Usage - e.g., Shioaji)
- **連線管理:**
    - Shioaji API 的登入與登出應妥善管理，避免不必要的重複登入或忘記登出。
    - 應處理 API 連線中斷或失敗的情況，並有重試機制（需注意 API 頻率限制）。
- **頻率限制:**
    - 嚴格遵守 Shioaji API 及其他外部數據源的請求頻率限制，避免帳戶被暫停。
    - 若有大量請求需求，應考慮批次處理或增加請求間隔。

## 5. 測試 (Testing)
- **模擬交易:**
    - 核心交易邏輯（如下單、停損、停利）應在模擬環境中進行充分測試。
    - 測試案例應包含各種市場情境（如開盤、盤中、收盤、快速波動等）。
- **回測:**
    - 若有回測功能，回測結果應可重現，並記錄回測參數與績效指標。

## 6. 特定文件參考
- **`Stock_filtering/README.md`:** 股票篩選條件的詳細說明。
- **`DEV_FLOW_AND_REQUIREMENTS.md`:** 專案開發流程與需求規格。
- **`DEVELOPER_LOG.md`:** 開發日誌與重要記錄。
- **`shioaji.log`:** Shioaji API 相關的底層日誌（若有啟用）。

## 7. Python 特定規則 (若適用)
- **虛擬環境:** 建議使用虛擬環境 (如 venv, conda) 管理專案依賴。
- **`requirements.txt`:** 專案依賴應記錄在 `requirements.txt` 檔案中。
