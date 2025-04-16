# JoJoTrading shioaji 合約為 0 處理紀錄

## 問題描述
- shioaji Python API 登入後，`api.Contracts.Stocks` 長度為 0，無法取得任何台股標的，導致主程式所有自動化功能失效。

---

## 已嘗試處理步驟

### 1. 本地端環境檢查與升級
- 確認 Python venv 正確啟動
- pip 安裝/升級 shioaji、pysolace 至最新版
- pip show shioaji 確認版本（1.2.5/最新版）

### 2. 憑證啟用
- 下載永豐金官方憑證（pfx），確認路徑與密碼
- 用 shioaji activate_ca 正確啟用憑證（順序：login → activate_ca）
- 憑證密碼正確（多次確認）

### 3. API 金鑰與權限
- API_KEY/SECRET_KEY 正確（從 credentials/.env 複製）
- 帳號已開通「行情／資料」權限
- IP 白名單正確

### 4. 快取清理
- 刪除 `%USERPROFILE%\.shioaji\contracts` 合約快取資料夾
- 多次重試下載合約

### 5. 官方建議排查
- 等待 10~30 分鐘後重試（伺服器同步異常時常會自動恢復）
- 多次重啟、重試

### 6. 其他語言測試
- 嘗試 C# 版本 Sinopac.OpenAPI，但官方 GitHub/NuGet 已下架，無法取得

### 7. 官方文件查證
- 參考 https://sinotrade.github.io/zh_tw/faq.html 官方 FAQ
- 官方建議如仍為 0，需聯絡客服協助伺服器端同步

---

## 結論
- 目前所有本地端能做的設定、升級、憑證、權限、快取清理都已完成
- 問題為 shioaji 官方伺服器端同步或權限異常，需由永豐金官方客服協助處理
- C# 版本暫時無法使用，因官方已下架套件

---

## 建議
- 聯絡永豐金 shioaji 官方客服，提供 API_KEY、帳號、IP、錯誤訊息與 log 檔案，請求協助伺服器端同步
- 等官方修復後，主程式即可恢復正常
