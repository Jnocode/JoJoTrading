# JoJoTrading - Phase 1 優化版本

[![Streamlit](https://img.shields.io/badge/Streamlit-1.45.1-FF6B6B.svg)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Phase](https://img.shields.io/badge/Phase-1%20Complete-green.svg)](https://github.com)

## 🚀 Phase 1 新增功能

### 核心優化特色
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

## 主要模組

### 核心系統
- `app.py`：Streamlit主介面，包含 Phase 1 增強功能控制面板
- `jojo_state_machine.py`：狀態機流程控制，支援動態參數配置
- `data_handler.py`：資料抓取、財報解析、智能估值計算選擇器

### Phase 1 新增模組
- `modules/data_validator.py`：財務數據質量驗證與評分系統
- `modules/enhanced_dcf.py`：增強型 DCF 模型（CAPM、情景分析、蒙地卡羅）
- `modules/integrated_dcf_handler.py`：智能集成處理器

### 支援模組
- `data_fetching.py`：FinMind API 資料獲取
- `modules/debug_tools.py`：除錯與開發者工具
- `modules/i18n.py`：多語訊息管理

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

## 🎮 使用說明

### 基本操作
1. 啟動 `streamlit run app.py`，於側邊欄選擇語言、設定除錯選項
2. 選擇產業或個股，設定篩選條件與估值參數
3. 點擊「開始篩選股票」，系統自動抓取資料、過濾成長股、進行DCF估值
4. 結果可於主畫面檢視並下載報表
5. 除錯模式可清除快取、調整API延遲、啟用模擬數據

### Phase 1 增強功能操作
1. **啟用增強型 DCF**：側邊欄切換「使用增強型 DCF」
2. **調整質量閾值**：設定數據質量要求（建議 0.7）
3. **情景分析**：啟用後可檢視樂觀/基準/悲觀三種估值
4. **蒙地卡羅模擬**：設定模擬次數與波動率參數
5. **異常檢測**：調整敏感度以識別數據異常

### 新增控制面板功能
- 📊 數據質量即時評分顯示
- 🎛️ 增強功能一鍵切換
- 📈 風險參數動態調整
- 🔍 異常檢測敏感度控制
- 📋 當前配置狀態指示

## 📁 檔案結構

```
jojo_trading/
├── app.py                           # 主應用程式
├── jojo_state_machine.py           # 狀態機控制
├── data_handler.py                 # 數據處理核心
├── data_fetching.py                # 資料獲取
├── modules/
│   ├── data_validator.py           # 數據質量驗證
│   ├── enhanced_dcf.py             # 增強型 DCF 模型
│   ├── integrated_dcf_handler.py   # 集成處理器
│   ├── debug_tools.py              # 除錯工具
│   └── i18n.py                     # 多語言支援
├── docs/
│   ├── PHASE1_COMPLETION_REPORT.md # Phase 1 完成報告
│   ├── USER_GUIDE_PHASE1.md        # 使用者指南
│   └── PHASE1_VALIDATION_REPORT.md # 驗證報告
└── requirements.txt                # 依賴套件
```

## 🔧 安裝與依賴

```bash
pip install streamlit pandas numpy scipy yfinance requests finmind
```

## 📋 收尾建議

### Phase 1 完成項目
- ✅ 數據質量驗證系統
- ✅ 增強型 DCF 模型
- ✅ 智能集成處理器
- ✅ UI 控制面板優化
- ✅ 風險評估與量化
- ✅ 完整文檔與測試

### Phase 2 發展建議
- 🔄 並行處理多股票分析
- 🤖 機器學習預測模型集成
- 📊 高級視覺化圖表
- 💼 投資組合優化功能
- ☁️ 雲端部署與API開發

---

## 📞 技術支援

如需進一步協助或有新需求：
- 📖 詳細文檔：`docs/` 目錄
- 🧪 功能演示：`python demo_phase1.py`
- 🔧 整合測試：`python test_phase1_integration.py`

**Phase 1 優化版本已準備投入生產使用！** 🚀
