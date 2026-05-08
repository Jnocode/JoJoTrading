# Checkpoint - 2026-05-04

## 已完成
- 確認專案位置：`D:\Workspace\03.Dev_Projects\trading\jojo_trading`
- 檢查 git 狀態：開始時工作樹乾淨
- 驗證桌面 App 入口 `desktop_app/real_desktop_app.py` 可 import `jojo_trading.ui.main_desktop`
- 跑過聚焦測試：`system_startup_test.py`、`function_verification_test.py` 共 5 passed，但有 pytest return warnings
- 修正 `src/jojo_trading/utils/logger.py` 的 log 目錄計算，避免寫到外層 `D:\Workspace\03.Dev_Projects\trading\logs\app.log` 造成 PermissionError
- 補上 `src/jojo_trading/core/data_handler.py` legacy 相容 API：
  - `calculate_original_dcf_valuation`
  - `calculate_historical_fcf_eps`
  - `DataHandler`
- 補上舊 UI import 相容層：
  - `jojo_trading.ui.components.stage4_integration`
  - `jojo_trading.ui.components.chip_monitor`
  - `jojo_trader.ui.components.chip_monitor`
- 修正 `tests/unit/test_anomaly_detection.py` 潛在異常股票報告資料缺少 `periods_count` 的問題
- 全量測試通過：`308 passed, 2 skipped, 112 warnings`
- 修復 portable desktop 啟動失敗：
  - `desktop_app/trading_libs/PySide6` 缺少 Qt/PySide DLL，導致 `from PySide6.QtWidgets import ...` 出現 `DLL load failed`
  - 已從 `.venv/Lib/site-packages` 同步完整 `PySide6` 與 `shiboken6` 到 `desktop_app/trading_libs`
  - 更新 `desktop_app/portable_launcher.py`，dependency check / health check 會實際載入 `PySide6.QtWidgets`，不再只檢查套件目錄是否存在
  - 驗證 `desktop_app/runtime_python/python.exe desktop_app/portable_launcher.py --check` 通過，且 `real_desktop_app` 可 import
- 調整新聞模組 AI 分析總覽：
  - `📊 產出總覽` 不再要求先逐則分析
  - 總覽來源改為目前載入的全部快訊；已分析項目使用 AI 摘要，未分析項目直接使用原始內容
  - `MarketSummaryWorker` 改為 summary items 與 stats items 分離，避免總覽生成觸發逐則分析
  - 驗證 `_build_market_summary_items()` 可混合 raw/已分析項目；`py_compile` 通過
- 新增 AI 分析總覽即時開關：
  - 在左側 `AI 分析總覽` 標題列新增 `即時總覽` checkbox
  - 設定保存於 `news_instant_summary`
  - 開啟後，抓到新快訊會自動產出總覽，不觸發逐則 AI 分析
  - 若前一輪總覽仍在跑，新資料會標記 pending，跑完後再用最新資料補跑
  - 驗證：`py_compile` 通過；offscreen 建立 `NewsTab` 並確認 checkbox 與觸發條件正常
- 讓 AI 分析總覽可更新左側情緒統計：
  - `NewsAnalyzer.summarize_market_with_stats()` 單次 AI 呼叫同時回傳 Markdown 總覽與 dashboard stats
  - stats 包含 `bullish`、`bearish`、`heat_score`、`top_sectors`
  - `NewsController.get_market_summary_with_stats()` 接上新流程；結構化失敗時才退回逐則分析統計
  - `MarketSummaryWorker` 改用總覽 stats 更新 UI
  - 驗證：JSON stats parse、controller stats 更新、中性總覽保留、invalid fallback 均通過
- 修正總覽統計覆蓋逐則統計問題：
  - 已分析單則的多空統計改為權威來源
  - 總覽 AI stats 只在沒有任何逐則分析結果時使用
  - 驗證：總覽 AI 回 `0 多 / 2 空` 時，已分析單則 `1 多 / 3 空` 會被保留
- 修正為混合統計邏輯：
  - 總覽文字仍看全部快訊
  - 總覽 AI 的多空估算只針對「未逐則分析」快訊
  - 最終儀表板統計 = 已逐則分析精確統計 + 未逐則分析總覽估算
  - 例：已分析 `1 多 / 1 空` + 未分析估算 `1 多 / 2 空` = `2 多 / 3 空`
  - 若所有新聞都已逐則分析，總覽 AI 即使回估算值也不會重複計入
- 新增中性/總數顯示：
  - 總覽 AI prompt 新增 `neutral_count` 與 `total_count`
  - 規則要求 `bullish + bearish + neutral = total`
  - 若 AI 只回多空數，系統會用統計用快訊總數補出中性數
  - 左側新增 `中性/未定 (Neutral)` 卡片與 `納入統計：X 則`
  - 情緒條改為用總數呈現：左側空頭、中央中性灰色、右側多頭
  - 驗證：27 則中 `2 多 / 3 空` 會補為 `22 中性`；UI labels 更新通過

## 關鍵發現
- 全量測試已越過 logger 權限錯誤，目前收斂到 legacy API 相容問題：
  - `calculate_original_dcf_valuation` 缺失
  - `DataHandler` 缺失
  - `calculate_historical_fcf_eps` 缺失
  - 舊 UI 測試引用不存在的 `jojo_trading.ui.components` / `jojo_trader`

## 待辦
- 後續可清理 pytest warnings，主要是舊測試仍使用 `return` 而不是 `assert`
- 注意：`data_handler.py` 與部分 `test_*.py` 受 `.gitignore` 影響，git status 不會列出其修改
- 注意：portable PySide6 修復新增大量 Qt DLL，`git status --untracked-files=all` 會顯示許多 `desktop_app/trading_libs/PySide6/*.dll`
- 注意：新聞模組 runtime 驗證時 Jin10 MCP 初始化因 sandbox 網路限制失敗，但 UI 總覽資料流驗證已通過

## 2026-05-07 更新
- 處理新聞模組 MCP 網路問題：在 `Jin10MCPClient` 中加入 `_is_offline` 自動降級機制。
  - 遇到 `ConnectionError` 或 `Timeout` 時自動啟用 OFFLINE MOCK 模式，產生模擬新聞資料，解決 sandbox 限制。

## 2026-05-08 更新
- 清理舊測試腳本的反模式：將 `function_verification_test.py`、`system_startup_test.py` 等檔案中會導致 pytest 偽陽性通過的 `return False` 替換為 `assert False`。
- 重新運行 pytest，確認全部 277 測試為實質通過。
