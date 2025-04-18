# JoJoTrading 開發者日誌

## 2025-04-19

- 補充軟體開發流程建議，包含需求分析、架構設計、模組開發、測試、文件、部署與持續優化等步驟。
- 類圖（CLASS_DIAGRAM.md）已產生，方便團隊理解架構與模組關聯。
- 下一步將與用戶討論具體需求，進行功能細化與規格確認。

---

## 2025-04-18

- 完成主程式模組化（MainEngine/App/Gateway 架構）。
- MarketDataApp、LeftValueZoneApp 皆已模組化，可動態註冊/啟動/切換。
- GUI 左側側邊欄支援 App 切換，主畫面可顯示即時行情報價面板、左側仔特價區介面。
- 左側仔特價區支援 fallback 假股票資料，模擬模式下也可測試 UI。
- left_value_zone.py 增加 fallback 機制，現價/EPS/成長率抓不到時自動給預設值，CLI 輸出明確標示。
- 修正 CLI 相對 import 問題，支援直接 python 執行。
- 啟動主程式 .bat 已整合所有功能，無需額外啟動特價區介面。
- 開始建立開發者日誌（本檔案）。

---

## 2025-04-17

- 修正 QMainWindow 傳參數錯誤，GUI 支援 main_engine/event_engine 注入。
- 修正 ApiGateway FastAPI 路由型別錯誤，支援主引擎注入。
- LeftValueZoneApp 移除不存在的 check_left_value_zone import。
- gui.py 支援自動列出所有 App，側邊欄可啟動/停止 App。
- 測試與推送 GitHub 完成。

---

## 2025-04-16

- 初步完成 JoJoTrading 專案主架構與基本 GUI。
- 支援 Shioaji/SIMULATION gateway 切換。
- 完成左側仔特價區 CLI/GUI prototype。

---

> 本日誌由 AI 助理自動生成，請持續補充重要開發紀錄與心得。
