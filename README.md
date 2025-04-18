# JoJoTrading

JoJoTrading 是一套模組化的量化交易系統，支援台灣證券/期貨自動化交易、估值分析、策略回測與自訂擴充。  
本專案採用 Python + PyQt6 + Shioaji + FastAPI 架構，適合個人投資者、量化開發者與自動化交易愛好者。

---

## 主要特色

- **模組化主引擎**：支援 Gateway（券商/模擬）、App（策略/功能）、動態註冊與切換。
- **多功能 GUI**：PyQt6 介面，左側側邊欄可切換各功能模組。
- **即時行情報價面板**：支援多商品監看。
- **左側仔特價區**：批次估值、產業分類、推薦清單、CLI/GUI 一鍵執行。
- **API Gateway**：RESTful API，支援外部系統串接。
- **自動 fallback**：模擬模式/資料抓取失敗時自動給預設值，方便測試。
- **開發者日誌**：所有重大變更自動記錄於 `DEVELOPER_LOG.md`。

---

## 安裝與啟動

1. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   ```

2. **設定 Shioaji 憑證**
   - 請將 API_KEY/SECRET_KEY 寫入 `credentials/.env` 檔案。

3. **啟動主程式**
   - Windows 使用 `啟動JoJoTrading主程式.bat`
   - 或直接執行：
     ```bash
     python main.py --mode simulation
     # 或
     python main.py --mode live
     ```

---

## 主要目錄結構

- `main.py`                主程式入口
- `gui.py`                 PyQt6 主視窗
- `modules/`               各功能模組（App、估值、特價區等）
- `widgets/`               GUI 子元件（報價表、清單等）
- `gateway/`               券商/模擬/API Gateway
- `core/`                  主引擎、事件引擎
- `outputs/`               估值結果、推薦清單
- `DEVELOPER_LOG.md`       開發者日誌
- `requirements.txt`       依賴套件清單

---

## 常見問題

- **模擬模式下無法取得真實股票合約？**
  - 已自動載入假資料供測試。
- **CLI/GUI 執行出現 ImportError？**
  - 已修正為絕對 import，請確保從專案根目錄執行。
- **估值結果為 0 或 None？**
  - 若資料抓取失敗會自動 fallback，請參考 CLI 輸出提示。

---

## 聯絡與貢獻

歡迎 issue、pull request 或聯絡作者 xiujiang1987@gmail.com  
如需協作、功能客製、策略開發請來信洽詢。

---
