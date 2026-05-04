# JoJo Trading - 編碼風格指南

## 語言與框架

- **Python 3.11+**，Type Hints 必須
- Web UI：Streamlit
- API：FastAPI
- 異步：AsyncIO + aiohttp
- 數據：Pandas, NumPy, SciPy

## 命名規範

| 類型 | 規範 | 範例 |
|------|------|------|
| 類別 | PascalCase | `BacktestEngine`, `DataFetcher` |
| 函式 | snake_case | `fetch_financial_data()`, `calculate_dcf()` |
| 常數 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_TIMEOUT` |
| 模組 | snake_case | `dcf_engine.py`, `risk_analysis.py` |

## 金融領域特殊慣例

- 所有金額使用 `Decimal` 而非 `float`（避免浮點精度問題）
- 股票代碼統一使用字串型態（台灣市場：`"2330"`, `"2317"`）
- 日期統一使用 `pd.Timestamp` 或 `datetime`，禁止字串日期比較

## 錯誤處理

- API 調用必須使用指數退避重試 (Exponential Backoff)
- 所有外部調用使用 `try/except`，錯誤記錄至 `logging`
- 資料丟失時使用 `Optional` 型態標記，禁止隱性 `None`

## 套件結構

- 核心邏輯放在 `src/jojo_trading/`
- 桌面端入口放在 `src/jojo_trader/`
- 策略放在 `src/jojo_trading/strategies/`
- 散落的腳本歸入 `scripts/` 或 `scripts/legacy/`
