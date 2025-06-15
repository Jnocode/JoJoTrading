# 📁 JoJo Trading 進階整理計劃 v2.0

## 🎯 第二階段整理目標
在第一階段基礎上，進一步優化專案結構，提升專業度和維護性

## 📊 當前問題分析

### 🚨 高優先級問題
1. **根目錄文檔過多** - 4個.md檔案可歸類到docs/
2. **匯出檔案累積** - export/有12個舊檔案需清理
3. **日誌檔案散亂** - logs/有6個檔案需歸檔
4. **臨時檔案殘留** - temp/有開發臨時檔案
5. **Python快取檔案** - 多個__pycache__目錄

### 🟡 中優先級問題
1. **模組結構不標準** - modules/應該移入src/
2. **快取目錄混亂** - cache/結構需優化
3. **測試檔案分散** - 部分測試檔案位置不當

## 🗂️ 進階整理方案

### Phase 1: 根目錄文檔整理

#### 📄 移動文檔檔案到docs/
```powershell
# 移動計劃和報告類文檔
Move-Item "CLEANUP_PLAN.md" "docs/reports/"
Move-Item "CLEANUP_COMPLETION_REPORT.md" "docs/reports/"
Move-Item "REFACTORING_PLAN.md" "docs/plans/"
Move-Item "PROJECT_STRUCTURE.md" "docs/"
```

#### ✅ 預期根目錄檔案 (10個)
```
📁 jojo_trading/
├── 📄 main_app.py             # 主應用程式
├── 📄 main.py                 # 備用入口
├── 📄 start_app.py            # 啟動腳本
├── 📄 start.bat               # 批次啟動
├── 📄 README.md               # 專案說明
├── 📄 requirements.txt        # 依賴清單
├── 📄 pyproject.toml          # 專案配置
├── 📄 pytest.ini             # 測試配置
├── 📄 setup.py                # 安裝配置
└── 📄 .env                    # 環境變數
```

### Phase 2: 數據檔案清理

#### 📤 匯出檔案歸檔
```powershell
# 建立歷史匯出目錄
New-Item -ItemType Directory -Path "export/history/2025-05" -Force

# 移動舊檔案
Move-Item "export/jojo_export_202505*.csv" "export/history/2025-05/"
Move-Item "export/jojo_export_202505*.xlsx" "export/history/2025-05/"

# 保留最新的範例檔案
# (保留最新的1-2個檔案作為格式範例)
```

#### 📝 日誌檔案歸檔
```powershell
# 建立歷史日誌目錄
New-Item -ItemType Directory -Path "logs/history/2025-06" -Force

# 移動歷史日誌
Move-Item "logs/*_20250609*" "logs/history/2025-06/"
Move-Item "logs/*_20250610*" "logs/history/2025-06/"
Move-Item "logs/system_fix.log" "logs/history/2025-06/"

# 保留當前日誌
# jojo_trading_app.log (保留)
```

### Phase 3: 開發檔案清理

#### 🗑️ 清理Python快取
```powershell
# 遞迴刪除所有__pycache__目錄
Get-ChildItem -Recurse -Name "__pycache__" | Remove-Item -Recurse -Force
```

#### 🧹 清理臨時檔案
```powershell
# 清理temp目錄中的開發檔案
Remove-Item "temp/debug_import.py" -Force
Remove-Item "temp/fix_indentation.py" -Force

# 保留misc目錄結構
```

### Phase 4: 模組結構標準化

#### 📦 移動modules到標準位置
```powershell
# 移動核心模組到src內
Move-Item "modules/data_validator.py" "src/jojo_trading/utils/"
Move-Item "modules/enhanced_dcf.py" "src/jojo_trading/core/"
Move-Item "modules/growth_analyzer.py" "src/jojo_trading/analysis/"
Move-Item "modules/integrated_dcf_handler.py" "src/jojo_trading/core/"
Move-Item "modules/macro_data_handler.py" "src/jojo_trading/data/"
Move-Item "modules/i18n.py" "src/jojo_trading/utils/"
Move-Item "modules/xbrl_etl/" "src/jojo_trading/data/"

# 移除空的modules目錄
Remove-Item "modules/" -Recurse -Force
```

### Phase 5: 目錄結構優化

#### 📁 建立標準目錄結構
```
📁 jojo_trading/                  # 根目錄 (10個檔案)
├── 📂 src/jojo_trading/          # 核心源碼 (標準Python包結構)
│   ├── 📂 core/                  # 核心業務邏輯
│   ├── 📂 ui/                    # 用戶介面
│   ├── 📂 data/                  # 數據處理
│   ├── 📂 analysis/              # 分析模組
│   ├── 📂 trading/               # 交易系統
│   ├── 📂 config/                # 配置管理
│   └── 📂 utils/                 # 工具函數
├── 📂 tests/                     # 測試系統
├── 📂 docs/                      # 文檔系統
│   ├── 📂 plans/                 # 計劃文檔
│   ├── 📂 reports/               # 報告文檔
│   └── 📂 api/                   # API文檔
├── 📂 data/                      # 數據檔案
├── 📂 export/                    # 匯出檔案
│   └── 📂 history/               # 歷史匯出
├── 📂 logs/                      # 日誌系統
│   └── 📂 history/               # 歷史日誌
├── 📂 scripts/                   # 腳本工具
├── 📂 config/                    # 全域配置
├── 📂 cache/                     # 快取系統
├── 📂 archive/                   # 歷史歸檔
└── 📂 temp/                      # 臨時檔案
```

## 📈 預期效果

### ✅ 整理前後對比

| 項目 | 整理前 | 整理後 | 改善 |
|------|--------|--------|------|
| 根目錄檔案 | 14個 | 10個 | ↓29% |
| 文檔組織 | 分散 | 集中在docs/ | ✅ |
| 模組結構 | 非標準 | Python標準 | ✅ |
| 匯出檔案 | 12個累積 | 2個範例 | ↓83% |
| 日誌管理 | 6個散亂 | 1個當前+歷史 | ✅ |

### 🎯 達成目標

1. **📁 標準化結構** - 符合Python PEP標準
2. **🧹 檔案精簡** - 減少不必要檔案
3. **📚 文檔集中** - 所有文檔歸類到docs/
4. **🗂️ 歷史歸檔** - 舊檔案有序歸檔
5. **⚡ 效能提升** - 清理快取和臨時檔案

## ⚠️ 執行注意事項

### 🛡️ 安全措施
1. **完整備份** - 執行前完整備份專案
2. **測試驗證** - 移動後測試應用程式功能
3. **逐步執行** - 分階段執行，每階段後測試
4. **路徑更新** - 檢查並更新所有模組引用路徑

### 🔧 執行順序
1. 備份專案 → 2. 清理臨時檔案 → 3. 移動文檔 → 4. 歸檔歷史檔案 → 5. 重構模組 → 6. 測試功能

## 🚀 執行腳本

```powershell
# 一鍵執行進階整理
.\scripts\cleanup_tools\advanced_cleanup.ps1
```

---
**計劃版本**: v2.0  
**預計執行時間**: 30-45分鐘  
**風險等級**: 🟡 中等 (需要更新模組引用)  
**預期收益**: 🟢 高 (大幅提升專案專業度)
