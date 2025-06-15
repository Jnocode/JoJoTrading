# 📅 JoJo Trading 早期開發歷史記錄 (2025年4-5月)

**文檔類型**: 開發者日誌整合版  
**時間範圍**: 2025年4月30日 - 2025年5月16日  
**階段**: 原型開發期  
**狀態**: 歷史記錄保存

---

## 📋 開發時間軸總覽

| 日期 | 階段 | 主要成果 | 技術里程碑 |
|------|------|---------|-----------|
| **2025-04-30** | 需求確認 | 專案目標設定、技術選型 | Python + Streamlit 確定 |
| **2025-05-05** | 架構設計 | 需求摘要、開發流程規劃 | 技術方案最終確認 |
| **2025-05-09/10** | 核心開發 | 狀態機、資料處理、UI搭建 | 核心架構實現 |
| **2025-05-16** | 功能完善 | 多語介面、DCF優化、除錯模組 | 功能基本完成 |

---

## 🎯 2025年4月30日 - 專案啟動

### **詳細設計會議結論**

#### **模組分工規劃**
- **資料抓取模組**: 整合永豐API，備援Yahoo/公開資料
- **估值模組**: Excel DCF公式轉Python函式
- **UI模組**: Streamlit介面（產業選擇、風險補償下拉選單）
- **匯出模組**: 支援Excel/Word/PDF/圖片

#### **風險補償設計**
- **下拉選單選項**: 
  - 2.5% 過度樂觀
  - 3% 樂觀
  - 4% 正常
  - 5% 悲觀
  - 6% 極度悲觀
  - 自訂（支援手動輸入百分比）

#### **UI原型設計**
- **主畫面**: 產業選擇 + 風險補償選單 + [開始篩選] 按鈕
- **結果頁面**: 表格顯示股票資訊 + 多格式匯出按鈕

#### **匯出格式支援**
- **Excel**: pandas.to_excel()
- **Word**: python-docx 建立表格
- **PDF**: pdfkit 將HTML轉PDF
- **圖片**: matplotlib 繪製表格後存圖

### **下一步計劃**
- 確認模組分工與技術選型
- 開發資料抓取模組（永豐API）
- 設計Streamlit UI元件原型

---

## 🔧 2025年5月5日 - 專案需求確認與技術選型

### **專案需求最終版本**

#### **核心目標**
- 以折現估價法（DCF）自動計算台股各產業成分股合理價值
- 過濾出潛在報酬率高的特價股，推薦給一般投資人
- 流程: 產業選擇 → 自動抓取成分股與財報 → 批次估值 → 過濾推薦 → 顯示/匯出清單

#### **介面需求**
- 極簡單頁操作，適合一般投資人
- 公式透明，可後續擴充

### **技術選型最終決策**

#### **選定技術棧**
- **主體**: Python + Streamlit
- **資料處理**: pandas、requests、openpyxl/xlwings
- **介面**: Streamlit 實現單頁極簡Web介面，支援桌面與手機

#### **其他選項評估**
- JS/TS、Excel VBA、R等評估後不如 Python + Streamlit 適合本專案

### **開發流程規劃**
1. 專案初始化（資料夾、Git、requirements.txt等）
2. API串接模組（TPEx/TWSE OpenAPI）
3. 資料處理與DCF估值邏輯
4. Excel自動化或pandas批次估值
5. Streamlit前端介面
6. 測試與優化
7. 文件與部署

---

## 🏗️ 2025年5月9-10日 - 核心架構實現

### **1. 開發環境建立**

#### **Cline Rules 設定**
- 建立全域規則檔案 `GLOBAL_RULES.md`
- 建立專案工作區規則檔案 `JoJoTrading/.clinerules/JoJoTrading_RULES.md`

#### **專案初始化**
- 建立 `requirements.txt` (streamlit, python-dotenv, requests)
- 完成虛擬環境 `.venv` 的建立與依賴安裝

### **2. 核心狀態機開發** (`jojo_state_machine.py`)

#### **狀態設計**
- 設計包含設定載入、UI互動、資料抓取、估值、篩選、結果顯示、匯出的主要狀態流程
- 建立 `BaseState` 及各狀態類別骨架:
  - `ConfigLoadState` - 配置載入
  - `UiInitState` - UI初始化
  - `IndustryProcessState` - 產業處理
  - `DataFetchState` - 資料抓取
  - `ValuationState` - 估值計算
  - `FilteringState` - 篩選邏輯
  - `ResultsDisplayState` - 結果顯示
  - `ExportState` - 匯出功能
  - `ErrorState` - 錯誤處理
  - `EndState` - 結束狀態

#### **實現功能**
- **ConfigLoadState**: 載入 `.env` 和 `industries.json` (產業列表、風險溢價選項)
- **DataFetchState**: 調用 `data_handler` 中函式獲取公司基本資料、篩選產業成分股、下載財報並提取財務數據
- **ValuationState**: 調用 `calculate_dcf_valuation` 的基本流程框架

### **3. 資料處理模組開發** (`data_handler.py`)

#### **核心函式實現**
- **`get_all_companies_basic_data`**: 從 TWSE OpenAPI 獲取所有上市公司基本資料，緩存至 `all_companies_basic_data.json`
- **`filter_industry_stocks`**: 根據產業中文名篩選成分股，記錄 `code`, `name`, `full_name`, `report_type`, `industry_code`
- **`get_financial_reports_for_stock`**: 智能判斷損益表 API 後綴，下載及緩存對應財報 JSON
- **`fetch_stock_financials_from_downloaded`**: 從已下載財報數據中提取特定股票最新的 EPS 和主要營收數據
- **`calculate_dcf_valuation`**: DCF 計算函式初步骨架

#### **技術細節**
- **FINANCIAL_FIELD_NAMES_MAP**: 根據實際財報 API JSON 結構進行校驗和確認
- 解決多次 `NameError` 和 SSL 憑證驗證問題 (`verify=False`)

### **4. UI 介面開發** (`app.py`)

#### **Streamlit 應用框架**
- 建立 Streamlit 應用程式初步框架，能夠驅動狀態機
- 實現狀態機在 `st.session_state` 中的持久化
- `UI_INIT` 狀態正確顯示從 `industries.json` 載入的產業下拉選單和風險補償選項
- 修正 `st.experimental_rerun` 為 `st.rerun`

#### **功能驗證**
- Streamlit 應用成功啟動並根據使用者選擇執行到資料獲取和（模擬的）估值、篩選、結果顯示流程

### **5. 設定檔建立**

#### **industries.json**
- 建立並完善包含產業中文名稱、TWSE產業代號、預設風險溢價和選項的設定檔

### **6. 架構圖生成**

#### **文檔產出**
- 在 `STREAMLIT_ARCH_DIAGRAM.md` 中編寫類圖和序列圖的 Mermaid 語法
- 提取到 `class_diagram.mmd` 和 `sequence_diagram.mmd`
- 成功生成 `class_diagram.svg` 和 `sequence_diagram.svg`

### **7. 已知問題與待辦**

#### **數據源問題**
- TWSE OpenAPI 的各類財報 API（尤其金融子行業）可能不包含所有公司的最新季度財報
- 部分股票無法獲取財務數據，`ValuationState` 需能處理此情況

#### **金融業API細化**
- 對金融保險業 (17) 的子行業判斷邏輯（基於公司名稱關鍵字）需要微調
- `SPECIFIC_REPORT_API_MAP` 需要進一步填充

#### **功能待完成**
- **DCF估值邏輯**: `calculate_dcf_valuation` 需實作完整的DCF計算公式
- **後續狀態**: `FilteringState`, `ResultsDisplayState`, `ExportState` 仍為模擬邏輯
- **錯誤處理**: 需要增強各狀態的錯誤處理和用戶友好反饋

---

## 🎉 2025年5月16日 - 功能收尾與優化

### **本週期重點目標**
- 專案收尾、功能總結、文件與架構圖同步、除錯與最佳化

### **1. 主要成果達成**

#### **多語介面實現**
- ✅ 完成多語介面（中/英）切換
- ✅ 所有自訂UI元件即時反映語言設定
- ✅ 於app.py側邊欄加入selectbox，所有UI文字用i18n模組t(key, lang)管理

#### **成長股過濾建立**
- ✅ 成長股過濾邏輯建立
- ✅ 支援依CAGR、ROE、毛利率等指標自訂過濾
- ✅ 於jojo_state_machine.py新增CAGR、ROE等指標計算與過濾流程

#### **DCF估值優化**
- ✅ DCF估值流程優化，支援多階段成長率、折現率自動/手動設定
- ✅ 敏感度分析功能
- ✅ data_handler.py支援多階段成長率、折現率自動化，並於UI顯示參數來源

#### **除錯模組化**
- ✅ 除錯模式模組化（debug_tools）
- ✅ 支援快取清理、API延遲調整、模擬數據測試
- ✅ debug_tools模組集中管理快取清理、API延遲、模擬數據，狀態機統一調用

#### **參數自動化**
- ✅ 無風險利率、通膨率、永續成長率可自動API獲取或手動輸入
- ✅ 來源明確標示

#### **結果匯出完善**
- ✅ 結果匯出支援CSV/Excel
- ✅ 所有參數與來源可記錄於報表

#### **文檔同步更新**
- ✅ 完成README、開發日誌、架構圖（Mermaid mmd/svg）等文件同步更新

### **2. 技術實作詳情**

#### **核心模組修改**
- **app.py**: 語言切換界面
- **jojo_state_machine.py**: 成長股過濾流程
- **data_handler.py**: DCF優化和參數自動化
- **data_fetching.py**: 數據抓取優化
- **modules/debug_tools.py**: 除錯模組化
- **modules/i18n.py**: 多語支援

#### **文檔更新**
- **README.md**: 專案說明更新
- **DEVELOPER_LOG.md**: 開發記錄同步
- **class_diagram.mmd/svg**: 類圖更新
- **sequence_diagram.mmd/svg**: 序列圖更新

### **3. 問題解決記錄**

#### **篩選條件傳遞修正**
- UI設定的最小潛在報酬率正確傳遞至context
- FilteringState正確讀取篩選參數

#### **程式碼品質提升**
- 補齊所有模組docstring與關鍵註解
- 移除暫時性debug print
- requirements.txt補全依賴
- .gitignore覆蓋快取與敏感資料

### **4. 測試與驗證**
- ✅ 完整測試所有功能流程（多語、成長股過濾、DCF、debug、匯出）
- ✅ 所有核心功能運行正常

### **5. Git 版本控制**

#### **修改文件清單**
- app.py
- jojo_state_machine.py
- data_handler.py
- data_fetching.py
- modules/debug_tools.py
- modules/i18n.py
- README.md
- DEVELOPER_LOG.md
- class_diagram.mmd
- class_diagram.svg
- sequence_diagram.mmd
- sequence_diagram.svg

#### **建議 Git 操作**
```bash
git add app.py jojo_state_machine.py data_handler.py data_fetching.py modules/debug_tools.py modules/i18n.py README.md DEVELOPER_LOG.md class_diagram.mmd class_diagram.svg sequence_diagram.mmd sequence_diagram.svg
```

#### **建議 Commit Message**
```
feat(core): 完成多語介面、成長股過濾、DCF優化與debug模組化
docs: 更新README、開發日誌與架構圖，反映最新專案狀態
fix: 修正篩選條件傳遞與狀態機邏輯
```

### **6. 後續優化建議**

#### **FinMind API 優化**
- 制定更穩健的FinMind API速率限制應對策略
- 在 `data_handler.py` 中為API調用實現帶有指數退避的重試邏輯

#### **Streamlit 性能優化**
- 進一步優化 Streamlit 腳本執行流程
- 減少不必要的日誌打印或計算，提升整體流暢度和日誌清晰度

---

## 📊 早期開發階段總結

### **✅ 主要成就**
1. **完整技術架構** - 狀態機驅動的模組化設計
2. **核心功能實現** - DCF估值、產業篩選、數據抓取
3. **用戶介面完成** - Streamlit多語界面
4. **數據處理完善** - TWSE API整合、財報數據提取
5. **除錯工具建立** - 完整的開發和測試工具

### **🎯 技術選型驗證**
- **Python + Streamlit** - 證明是正確的技術選擇
- **狀態機架構** - 有效管理複雜的業務流程
- **模組化設計** - 良好的代碼結構和可維護性

### **🚀 為後續開發奠定基礎**
這個早期開發階段為後續的系統演進提供了堅實的基礎：
- 建立了完整的開發工作流程
- 驗證了核心技術方案的可行性
- 形成了標準化的開發文檔習慣

---

## 📋 與後續開發的銜接

### **開發歷史連續性**
- **2025年4-5月**: 原型開發期（本文檔）
- **2025年5-6月**: 架構重構期
- **2025年6月**: 增強功能實現期

### **演進軌跡**
1. **功能演進**: 從類股篩選到個股DCF分析
2. **技術演進**: 從狀態機架構到模組化企業級系統
3. **用戶體驗演進**: 從基礎界面到專業級分析工具

### **經驗傳承**
這個早期開發記錄為後續開發提供了重要的經驗參考：
- 技術決策的思考過程
- 問題解決的方法論
- 開發流程的最佳實踐

---

*文檔整理: 2025-06-13*  
*原始開發期間: 2025-04-30 至 2025-05-16*  
*開發階段: 原型開發期*  
*後續銜接: 參見 [2025-06-05_Critical_System_Fixes.md](2025-06-05_Critical_System_Fixes.md)*
