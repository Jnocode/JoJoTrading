# 📁 JoJo Trading 根目錄整理計畫

## 🎯 整理目標
優化根目錄結構，移除重複檔案，提升專案組織性

## 📊 當前問題
- 根目錄有 60+ 檔案，過於雜亂
- 重複的主程式檔案 (4個)
- 測試檔案散布在根目錄 (15個)
- 報告檔案過多 (12個)

## 🗂️ 整理方案

### 階段 1: 移除重複檔案
```bash
# 移除舊版本主程式
rm main_app_fixed_v2.py
rm main_app_v3.py

# 移除重複的簡單測試
rm simple_*.py
```

### 階段 2: 分類現有檔案

#### 📄 報告檔案 → docs/reports/
```
AUTO_DATA_FETCHER_FIX_COMPLETION_REPORT.md
BATCH_FILE_FIX_REPORT.md
BATCH_STARTUP_COMPLETION_REPORT.md
BATCH_STARTUP_FIX_COMPLETE.md
DCF_FIX_COMPLETION_REPORT.md
DCF_SECTOR_SCREENING_COMPLETION_REPORT.md
ERROR_FIX_COMPLETION_REPORT.md
FINAL_COMPLETION_REPORT.md
INFINITE_LOOP_FIX_REPORT.md
MODULE_INTEGRATION_COMPLETION_REPORT.md
PROJECT_CLEANUP_AND_OPTIMIZATION_REPORT.md
PROJECT_REFACTORING_COMPLETION_REPORT.md
SYSTEM_COMPREHENSIVE_ANALYSIS.md
SYSTEM_REFACTORING_COMPLETE.md
TRADING_UI_UNIFIED_FIX_COMPLETION_REPORT.md
SOLUTION_SUMMARY.md
```

#### 🧪 測試檔案 → tests/
```
# 整合測試
comprehensive_functionality_test.py    → tests/integration/
comprehensive_status_check.py          → tests/integration/
module_integration_test.py             → tests/integration/
monitor_integration_test.py            → tests/integration/

# 單元測試
test_*.py                              → tests/unit/

# 功能測試
functionality_test.py                  → tests/functional/
final_dcf_verification.py             → tests/validation/
final_system_check.py                 → tests/validation/
final_system_validation.py            → tests/validation/

# 性能測試
performance_test.py                    → tests/performance/
optimized_performance_test.py          → tests/performance/

# 狀態檢查
quick_*.py                             → tests/health/
module_status_check.py                 → tests/health/
quick_status_check.py                  → tests/health/
```

#### 🔧 工具腳本 → scripts/
```
cleanup_project.*                      → scripts/maintenance/
migrate_to_refactored.py              → scripts/migration/
performance_optimizer.py              → scripts/optimization/
```

### 階段 3: 保留的核心檔案

#### ✅ 根目錄核心檔案 (僅保留9個)
```
main_app.py              # 主應用程式入口
main.py                  # 備用入口
start_app.py             # 啟動腳本
README.md                # 專案說明
requirements.txt         # 依賴清單
pyproject.toml          # 專案配置
pytest.ini              # 測試配置
setup.py                # 安裝配置
.env                     # 環境變數
```

#### 📁 啟動腳本整理
```
start.bat               # 主要啟動腳本 (保留)
quick_start.bat         # 快速啟動 (移到 scripts/start/)
```

## 🎯 預期效果

### 整理前 (60+ 檔案)
```
jojo_trading/
├── main_app.py
├── main_app_fixed_v2.py    ❌ 重複
├── main_app_v3.py          ❌ 重複
├── test_*.py (15個)        ❌ 錯位
├── *_REPORT.md (12個)      ❌ 雜亂
└── ... 其他檔案
```

### 整理後 (9個核心檔案)
```
jojo_trading/
├── main_app.py             ✅ 唯一入口
├── main.py                 ✅ 備用入口
├── start_app.py            ✅ 啟動腳本
├── README.md               ✅ 說明文件
├── requirements.txt        ✅ 依賴清單
├── pyproject.toml          ✅ 專案配置
├── pytest.ini             ✅ 測試配置
├── setup.py                ✅ 安裝配置
└── .env                    ✅ 環境變數
```

## 🚀 實施步驟

1. **備份重要檔案**
2. **執行分類移動**
3. **更新引用路徑**
4. **測試系統功能**
5. **更新文檔**

## ⚠️ 注意事項

- 移動前先測試所有功能正常
- 保留一份完整備份
- 更新所有檔案的引用路徑
- 確保測試通過後再刪除舊檔案
