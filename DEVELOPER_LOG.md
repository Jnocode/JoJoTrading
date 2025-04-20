# JoJoTrading 開發者日誌

## 2025-04-20

- **會議總結與需求確認：**
    - 討論標準軟體開發流程（SDLC）。
    - 明確專案目標：聚焦「台股類股 + 左側折現特價股篩選」，以DCF估值找出便宜股，服務一般投資人。
    - 分析用戶提供的 Excel 估值公式（DCF）。
    - 依「簡單易用」原則精簡需求，暫不納入進階狀態機、回測、通知等。
    - 確認核心功能：類股選擇、自動抓成分股、自動抓資料（現價/EPS/成長率）、Excel批次估值、潛在報酬率過濾、表格顯示、匯出。
    - 確認技術選型：GUI 採用 Streamlit（支援桌面/手機瀏覽器）。
    - 確認需自動化資料抓取、參數（利率/通膨/成長率）自動取得、支援樂觀/悲觀情境。
    - 確認需 Docker/自動部署。
    - 更新需求文件 `DEV_FLOW_AND_REQUIREMENTS.md`。
- **下一步：** 進入「詳細設計」階段，規劃模組、資料流、UI原型。

---

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
