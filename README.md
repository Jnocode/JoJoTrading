# JoJo Trading 📈

台股期權事件驅動回測系統 — 支援半導體類股分析與多券商 API 整合。

> ⚠️ 此專案曾為私有，首次公開。部分 vendor 套件仍在清理中。

## Live Demo

- GitHub Pages: https://jnocode.github.io/JoJoTrading/
- Cake Portfolio: https://www.cake.me/portfolios/jojotrader-pine-backtester

---

## 功能

- **事件驅動回測引擎** — 以事件驅動架構模擬真實市場行為，支援 tick 級與日線級回測
- **半導體類股分析** — 內建半導體產業分類，支援產業輪動策略驗證
- **多券商 API** — 支援永豐金 Shioaji、FinMind 等資料源
- **策略參數最佳化** — 支援多參數掃描與績效評估
- **桌面應用** — PySide6 圖形化介面

## Quick Start

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定憑證
cp .env.example .env
# 填入你的 API key

# 執行
python -m src.jojo_trading.main
```

## 技術棧

- Python 3.11+ / FastAPI / SQLAlchemy
- Shioaji（永豐金 API）/ FinMind
- PySide6（桌面 UI）
- Docker / PostgreSQL（可選）

## 專案狀態

🛠️ 持續開發中 — 核心回測引擎穩定，UI 仍在迭代。

## License

MIT
