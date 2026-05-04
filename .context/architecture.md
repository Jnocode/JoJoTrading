# JoJo Trading - 架構概覽

## 定位

Python 量化交易系統，涵蓋 DCF 估值、策略回測、風險分析、Smart Money Concepts。

## 分層架構

```
┌──────────────────────────────────────────────────────┐
│  Frontend (src/jojo_trading/ui/)                     │
│  └── Streamlit Web App                               │
├──────────────────────────────────────────────────────┤
│  API Layer (api/)                                    │
│  └── FastAPI REST Endpoints                          │
├──────────────────────────────────────────────────────┤
│  Core Services (src/jojo_trading/core/)              │
│  ├── dcf_engine.py     ├── backtest_engine.py        │
│  ├── risk_analysis.py  └── data_fetcher.py           │
├──────────────────────────────────────────────────────┤
│  Strategies (src/jojo_trading/strategies/)            │
│  ├── supertrend_smc.py └── smc_strategy.py           │
├──────────────────────────────────────────────────────┤
│  Analysis (src/jojo_trading/analysis/)               │
│  ├── indicators.py     └── monte_carlo.py            │
├──────────────────────────────────────────────────────┤
│  Data Layer                                          │
│  ├── SQLite (stocks.db)  ├── Cache (LRU)             │
│  └── External APIs: Shioaji, Yahoo Finance           │
├──────────────────────────────────────────────────────┤
│  Desktop App (src/jojo_trader/)                      │
│  └── main_desktop.py (PyInstaller 打包入口)          │
└──────────────────────────────────────────────────────┘
```

## 關鍵設計決策

### 1. 雙套件結構

- `jojo_trading` — 核心 library（Web、API、策略邏輯）
- `jojo_trader` — 桌面端入口（PyInstaller 打包用）

### 2. God Classes (待重構)

- `modules/data_handler.py` (53KB) — 巨型資料處理層，集中了抓取、清洗、快取、儲存
- `modules/jojo_state_machine.py` (33KB) — 交易狀態機

### 3. 已整理的目錄結構

- `scripts/` — 所有 .bat 和工具腳本
- `scripts/legacy/` — 開發過程中的實驗性腳本
- `docs/dev_logs/` — 開發階段文件 (STAGE6, DEPLOY_NOW 等)

## 外部依賴

- Shioaji API (永豐金證券)
- Yahoo Finance / yfinance
- DCF 估值 API
