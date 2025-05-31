# JoJo Trading - 基於 DCF 估值的台股篩選系統

[![Streamlit](https://img.shields.io/badge/Streamlit-1.45.1-FF6B6B.svg)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)](https://github.com)

## 🚀 系統特色

### 核心功能
- **🔍 數據質量驗證系統**：智能評估財務數據可靠度，確保估值準確性
- **📊 增強型 DCF 模型**：集成 CAPM 動態折現率、情景分析與蒙地卡羅模擬
- **🤖 智能方法選擇**：根據數據質量自動選擇最適合的估值方法
- **📈 風險量化分析**：提供 VaR、標準差等全面風險評估指標

### 主要功能
- **多語介面**：支援中文/英文切換，所有自訂UI皆可即時切換語言
- **產業/個股篩選**：可依產業或自選個股進行財報與估值分析
- **成長股過濾**：可依營收/盈餘CAGR、ROE、毛利率等指標自訂過濾成長股
- **智能 DCF 估值**：支援標準與增強型雙模式，含情景分析與蒙地卡羅模擬
- **參數自動化**：無風險利率、通膨率、永續成長率可自動API獲取或手動輸入
- **除錯模式**：模組化debug_tools，支援清除快取、API延遲調整、模擬數據測試
- **結果匯出**：支援CSV/Excel下載，所有參數與來源可記錄於報表

## 📁 專案結構

```
jojo_trading/
├── src/jojo_trading/           # 主要模組套件
│   ├── __init__.py            # 套件初始化文件 (v1.0.0)
│   ├── core/                  # 核心功能模組
│   │   ├── __init__.py
│   │   ├── state_machine.py   # 狀態機流程控制
│   │   ├── data_handler.py    # 資料處理引擎
│   │   ├── dcf_calculator.py  # DCF 計算器
│   │   └── integrated_dcf_handler.py  # 智能DCF整合處理器
│   ├── config/                # 設定管理模組
│   │   ├── __init__.py
│   │   ├── taiwan_presets.py  # 台股預設配置
│   │   ├── user_config.py     # 用戶配置管理
│   │   └── optimization_config.py  # 優化參數配置
│   ├── ui/                    # 用戶介面模組
│   │   ├── __init__.py
│   │   └── app.py            # Streamlit 主介面
│   ├── analysis/              # 分析功能模組
│   │   ├── __init__.py
│   │   ├── industry_analysis.py      # 產業分析
│   │   ├── financial_analysis.py     # 財務分析
│   │   └── growth_analyzer.py        # 成長分析器
│   └── utils/                 # 工具模組
│       ├── __init__.py
│       ├── data_fetching.py   # 數據獲取工具
│       ├── data_validator.py  # 數據驗證工具
│       └── helpers.py         # 輔助工具函數
├── main.py                    # 主程式入口點
├── streamlit_app.py           # 優化版Web UI啟動器
├── start_web.py               # Web UI啟動腳本
├── pyproject.toml             # 現代化專案配置
├── Makefile                   # 便利開發指令 (Unix/Linux)
├── make.ps1                   # 便利開發指令 (Windows PowerShell)
├── start.bat                  # Windows 啟動腳本
├── requirements/              # 依賴管理
│   ├── base.txt              # 基礎依賴
│   ├── dev.txt               # 開發依賴
│   ├── test.txt              # 測試依賴
│   └── prod.txt              # 生產環境依賴
└── requirements.txt           # 主要依賴文件

## 📊 DCF與成長股邏輯

### Phase 1 增強型 DCF 流程
1. **數據質量評估**：自動檢測財務數據的一致性、完整性、準確性
2. **智能方法選擇**：
   - 高質量數據（≥閾值）→ 增強型 DCF
   - 低質量數據（<閾值）→ 標準 DCF 備援
3. **增強型計算特色**：
   - CAPM 動態折現率調整
   - 三情景分析（樂觀/基準/悲觀）
   - 蒙地卡羅模擬（1000次）
   - VaR 風險評估

## 🛠️ 快速開始

### 系統需求
- Python 3.11+
- Windows 10/11, macOS, Linux
- 8GB RAM 推薦

### 安裝步驟

#### 1. 克隆專案
```bash
git clone <repository-url>
cd jojo_trading
```

#### 2. 建立虛擬環境
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux  
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. 安裝依賴
```bash
# 生產環境
pip install -r requirements.txt

# 開發環境
pip install -r requirements/dev.txt

# 使用 Makefile (推薦)
make install          # Unix/Linux
# 或
./make.ps1 install    # Windows PowerShell
```

### 🚀 啟動應用

#### 方法 1: 主程式入口 (推薦)
```bash
# Web UI 模式 (預設)
python main.py

# CLI 模式
python main.py --cli

# 顯示版本
python main.py --version
```

#### 方法 2: 直接啟動 Streamlit
```bash
# 優化版 (推薦)
streamlit run streamlit_app.py

# 基本版
streamlit run start_web.py
```

#### 方法 3: 使用便利腳本
```bash
# Windows
start.bat
# 或
start_web.bat

# Unix/Linux/macOS
make run
```

### 🎮 使用說明

#### 基本操作流程
1. **啟動系統**：執行 `python main.py` 或 `streamlit run streamlit_app.py`
2. **選擇分析範圍**：在側邊欄選擇產業或個股分析
3. **設定篩選條件**：配置成長股過濾參數（CAGR、ROE、毛利率等）
4. **配置估值參數**：設定DCF模型參數或使用自動API獲取
5. **執行分析**：點擊「開始篩選股票」進行分析
6. **檢視結果**：查看估值結果、風險指標、情景分析
7. **匯出報告**：下載 CSV/Excel 格式的分析報表

#### 主要功能介紹
- **多語支援**：中文/英文介面即時切換
- **智能估值**：系統自動選擇最佳估值方法
- **風險分析**：VaR、標準差、情景分析
- **除錯模式**：清除快取、調整API延遲、模擬數據測試

## 📊 DCF與成長股分析邏輯

### 增強型 DCF 流程
1. **數據質量評估**：自動檢測財務數據的一致性、完整性、準確性
2. **智能方法選擇**：
   - 高質量數據（≥閾值）→ 增強型 DCF
   - 低質量數據（<閾值）→ 標準 DCF 備援
3. **增強型計算特色**：
   - CAPM 動態折現率調整
   - 三情景分析（樂觀/基準/悲觀）
   - 蒙地卡羅模擬（1000次）

### 成長股篩選邏輯
- 先過濾成長股（如CAGR>10%、ROE提升等）
- 取得FCFE現金流、成長率、折現率（無風險利率+風險溢酬）
- 支援多階段成長率與敏感度分析
- 非成長股可用其他估值法（如股息折現、PE/PB等）

### 參數來源
- 無風險利率：台灣10年期公債殖利率（央行/債券資訊網API）
- 通膨率：主計總處CPI年增率（政府開放資料）
- 永續成長率：GDP、產業平均或通膨率
- 風險溢酬：CAPM 模型動態計算

## 🔧 開發工具

### 使用 Makefile / make.ps1
```bash
# 安裝依賴
make install         # Unix/Linux
./make.ps1 install   # Windows PowerShell

# 啟動開發服務
make dev             # Unix/Linux  
./make.ps1 dev       # Windows PowerShell

# 運行測試
make test            # Unix/Linux
./make.ps1 test      # Windows PowerShell

# 清理環境
make clean           # Unix/Linux
./make.ps1 clean     # Windows PowerShell
```

## 📋 API 與配置

### 環境變數設定
建立 `.env` 文件：
```env
FINMIND_USER_ID=your_user_id
FINMIND_PASSWORD=your_password
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### 重要配置文件
- `src/jojo_trading/config/taiwan_presets.py` - 台股預設參數
- `src/jojo_trading/config/user_config.py` - 用戶客製化設定
- `src/jojo_trading/config/optimization_config.py` - 優化參數配置

## 🧪 測試與驗證

### 執行測試套件
```bash
# 基本功能測試
python -m pytest tests/

# 模組導入測試
python -c "from src.jojo_trading import __version__; print(f'Version: {__version__}')"

# CLI 功能測試
python main.py --cli
```

### 常見問題排除
1. **模組導入錯誤**：確認已啟動虛擬環境且安裝所有依賴
2. **API 連接失敗**：檢查網路連接和 `.env` 配置
3. **數據獲取異常**：嘗試清除快取 `rm -rf cache/`

## 🚀 部署建議

### 生產環境部署
```bash
# 安裝生產依賴
pip install -r requirements/prod.txt

# 設定環境變數
export FINMIND_USER_ID=your_id
export FINMIND_PASSWORD=your_password

# 啟動服務
streamlit run streamlit_app.py --server.port 8501
```

### Docker 部署 (可選)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501"]
```

## 📞 技術支援與貢獻

### 獲取幫助
- 📖 查看 `docs/` 目錄中的詳細文檔
- 🐛 報告問題請提交 Issue
- 💡 功能建議歡迎提交 Pull Request

### 貢獻指南
1. Fork 專案到您的 GitHub
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT License - 詳見 [LICENSE](LICENSE) 文件

---

**JoJo Trading v1.0.0 - 基於 DCF 估值的專業台股分析工具** 🚀

*支援智能估值、風險分析、成長股篩選的一站式投資分析平台*
