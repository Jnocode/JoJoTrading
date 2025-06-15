# 🌿 JoJo Trading System - Git 工作流程規範

**版本**: 1.0  
**制定日期**: 2025年6月13日  
**適用範圍**: JoJo Trading System 所有開發成員

---

## 📋 目錄

- [1. 概述](#1-概述)
- [2. 分支策略](#2-分支策略)
- [3. 提交規範](#3-提交規範)
- [4. 合併流程](#4-合併流程)
- [5. 版本管理](#5-版本管理)
- [6. 發布流程](#6-發布流程)
- [7. 熱修復流程](#7-熱修復流程)
- [8. 最佳實踐](#8-最佳實踐)

---

## 1. 概述

### 1.1 目標
- 確保代碼版本控制的一致性和可追溯性
- 建立清晰的功能開發和發布流程
- 減少合併衝突和集成問題
- 提高團隊協作效率

### 1.2 分支策略選擇
本專案採用 **Git Flow** 策略的簡化版本，適合中小型團隊：

```
main (生產環境)
├── develop (開發主線)
│   ├── feature/功能分支
│   ├── bugfix/錯誤修復分支
│   └── chore/維護分支
├── release/發布分支
└── hotfix/熱修復分支
```

---

## 2. 分支策略

### 2.1 主要分支 🔴

#### `main` 分支
- **用途**: 生產環境代碼
- **特點**: 永遠保持穩定，可直接部署
- **保護**: 禁止直接推送，只能通過 PR 合併
- **命名**: `main`

```bash
# main 分支應該永遠是穩定的
git checkout main
git pull origin main
```

#### `develop` 分支  
- **用途**: 開發主線，集成所有功能
- **特點**: 最新的開發進度
- **保護**: 禁止直接推送，只能通過 PR 合併
- **命名**: `develop`

```bash
# 從 develop 創建新功能分支
git checkout develop
git pull origin develop
git checkout -b feature/dcf-optimization
```

### 2.2 功能分支 🔴

#### `feature/` 分支
- **用途**: 開發新功能
- **生命週期**: 功能完成後刪除
- **命名規範**: `feature/功能描述`
- **基於**: `develop` 分支
- **合併到**: `develop` 分支

```bash
# 創建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/stock-sector-analysis

# 功能開發完成後
git checkout develop
git merge --no-ff feature/stock-sector-analysis
git branch -d feature/stock-sector-analysis
git push origin --delete feature/stock-sector-analysis
```

#### 功能分支命名示例
```bash
feature/dcf-calculator-optimization     # DCF 計算器優化
feature/taiwan-stock-data-integration   # 台股數據整合
feature/portfolio-analysis              # 投資組合分析
feature/streamlit-ui-enhancement        # Streamlit UI 增強
bugfix/dcf-calculation-error           # DCF 計算錯誤修復
chore/update-dependencies              # 依賴更新
docs/api-documentation                 # API 文檔更新
```

### 2.3 發布分支 🟡

#### `release/` 分支
- **用途**: 準備新版本發布
- **生命週期**: 發布完成後刪除
- **命名規範**: `release/版本號`
- **基於**: `develop` 分支
- **合併到**: `main` 和 `develop` 分支

```bash
# 創建發布分支
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# 版本號更新和最後測試
# 修復發布相關的小錯誤

# 發布完成
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"

git checkout develop  
git merge --no-ff release/v1.2.0
git branch -d release/v1.2.0
```

### 2.4 熱修復分支 🔴

#### `hotfix/` 分支
- **用途**: 緊急修復生產環境問題
- **生命週期**: 修復完成後刪除
- **命名規範**: `hotfix/問題描述`
- **基於**: `main` 分支
- **合併到**: `main` 和 `develop` 分支

```bash
# 創建熱修復分支
git checkout main
git pull origin main
git checkout -b hotfix/dcf-division-by-zero

# 修復問題並測試

# 合併到 main
git checkout main
git merge --no-ff hotfix/dcf-division-by-zero
git tag -a v1.2.1 -m "Hotfix: Fix DCF division by zero error"

# 合併到 develop
git checkout develop
git merge --no-ff hotfix/dcf-division-by-zero
git branch -d hotfix/dcf-division-by-zero
```

---

## 3. 提交規範

### 3.1 提交訊息格式 🔴

#### 基本格式
```
<類型>(<範圍>): <描述>

<詳細說明>

<頁腳>
```

#### 提交類型 🔴
```bash
feat:     新功能
fix:      錯誤修復  
docs:     文檔更新
style:    代碼格式調整（不影響功能）
refactor: 重構代碼（不增加功能也不修復錯誤）
perf:     性能優化
test:     測試相關
chore:    構建過程或輔助工具的變動
revert:   撤銷之前的提交
```

#### 範圍示例
```bash
dcf:      DCF 估值相關
data:     數據處理相關
ui:       用戶界面相關
api:      API 相關
config:   配置相關
test:     測試相關
docs:     文檔相關
```

### 3.2 提交訊息示例 🔴

#### 好的提交訊息
```bash
# 新功能
feat(dcf): 添加行業 Beta 值自動計算功能

實現基於同行業股票的 Beta 值自動計算，提高 DCF 估值準確性。
- 添加行業分類數據獲取
- 實現行業平均 Beta 計算
- 集成到 DCF 計算流程中

Closes #123

# 錯誤修復
fix(data): 修復財務數據缺失時的處理邏輯

當某些季度財務數據缺失時，系統會崩潰。現在改為：
- 使用前一年同期數據補全
- 在 UI 中顯示數據來源說明
- 記錄補全操作日誌

Fixes #456

# 文檔更新
docs(api): 更新 DCF 計算 API 文檔

- 添加新的參數說明
- 更新回傳值格式
- 增加使用示例

# 重構
refactor(dcf): 簡化 DCF 計算器類結構

將複雜的計算邏輯拆分為更小的方法：
- extract_cash_flow_projection()
- calculate_terminal_value()  
- calculate_present_value()

提高代碼可讀性和可測試性。
```

#### 避免的提交訊息
```bash
# ❌ 太簡略
"fix bug"
"update"
"小改動"

# ❌ 沒有類型前綴
"修復 DCF 計算錯誤"

# ❌ 描述不清楚
"feat: 新增功能"
"fix: 修復問題"
```

### 3.3 原子性提交 🔴

#### 提交應該是原子性的
```bash
# ✅ 好的提交 - 一個提交只做一件事
git add src/dcf/calculator.py
git commit -m "feat(dcf): 添加終值計算方法"

git add tests/unit/test_dcf_calculator.py  
git commit -m "test(dcf): 添加終值計算方法的單元測試"

git add docs/api/dcf.md
git commit -m "docs(dcf): 更新 DCF API 文檔"

# ❌ 避免的提交 - 一個提交做多件事
git add src/ tests/ docs/
git commit -m "feat: 添加 DCF 功能、測試和文檔"
```

---

## 4. 合併流程

### 4.1 Pull Request 流程 🔴

#### 創建 PR 前的檢查
```bash
# 1. 確保分支是最新的
git checkout develop
git pull origin develop
git checkout feature/your-feature
git rebase develop

# 2. 執行測試
python run_tests.py --all

# 3. 代碼檢查
flake8 src/ tests/
black --check src/ tests/
mypy src/

# 4. 提交並推送
git push origin feature/your-feature
```

#### PR 模板 🔴
```markdown
## 🎯 變更描述
簡要描述這個 PR 的目的和變更內容。

## 📋 變更類型
- [ ] 新功能 (feature)
- [ ] 錯誤修復 (bugfix) 
- [ ] 重構 (refactor)
- [ ] 文檔更新 (docs)
- [ ] 性能優化 (perf)
- [ ] 測試 (test)
- [ ] 其他 (chore)

## 🧪 測試
- [ ] 所有現有測試通過
- [ ] 新增了相應的測試
- [ ] 手動測試完成

## 📸 截圖/Demo
如果有 UI 變更，請提供截圖或 GIF。

## 🔗 相關 Issue
Closes #123
Fixes #456

## 📝 檢查清單
- [ ] 代碼通過 linting 檢查
- [ ] 代碼通過所有測試
- [ ] 更新了相關文檔
- [ ] 遵循編程規範
- [ ] 變更已進行適當的安全檢查

## 📋 審查說明
特別需要審查的地方或注意事項。
```

### 4.2 代碼審查 🔴

#### 審查檢查項目
```markdown
## 代碼品質
- [ ] 代碼遵循專案編程規範
- [ ] 命名清晰且有意義
- [ ] 函數和類職責單一
- [ ] 適當的錯誤處理
- [ ] 沒有代碼重複

## 功能性
- [ ] 實現符合需求
- [ ] 邊界情況處理完善
- [ ] 性能考量合理
- [ ] 沒有明顯的邏輯錯誤

## 測試
- [ ] 測試覆蓋率足夠
- [ ] 測試案例合理
- [ ] 測試通過

## 文檔
- [ ] API 文檔完整
- [ ] 註釋清楚
- [ ] README 更新（如需要）
```

#### 審查回饋格式
```markdown
## 整體評價
代碼品質良好，邏輯清晰。

## 必須修改 (Must Fix)
1. **安全性問題**: L45 沒有驗證用戶輸入，可能導致注入攻擊
2. **功能錯誤**: L78 除零錯誤未處理

## 建議修改 (Should Fix)  
1. **性能**: L23-30 可以使用向量化操作提高性能
2. **可讀性**: L56 函數名稱不夠清楚，建議改為 `calculate_annual_return`

## 輕微建議 (Nice to Have)
1. L15 可以考慮添加類型註解
2. L89 註釋可以更詳細

## 讚賞
很好的錯誤處理實現！L67-72 的緩存策略很聰明。
```

### 4.3 合併方式 🔴

#### 合併策略
```bash
# 使用 --no-ff 確保保留分支歷史
git checkout develop
git merge --no-ff feature/stock-analysis

# 或者使用 rebase 保持線性歷史（適合小型功能）
git checkout feature/stock-analysis
git rebase develop
git checkout develop
git merge feature/stock-analysis
```

#### Squash 合併 🟡
對於小型功能或多個小提交，考慮使用 squash 合併：

```bash
# 將功能分支的多個提交合併為一個
git checkout develop
git merge --squash feature/small-ui-fix
git commit -m "feat(ui): 修復股票列表顯示問題

- 修復表格排序功能
- 改善響應式佈局
- 更新樣式文件

Closes #234"
```

---

## 5. 版本管理

### 5.1 語義化版本 🔴

#### 版本號格式: `MAJOR.MINOR.PATCH`
```
1.2.3
│ │ │
│ │ └── PATCH: 向後兼容的錯誤修復
│ └──── MINOR: 向後兼容的新功能
└────── MAJOR: 不向後兼容的重大變更
```

#### 版本號示例
```bash
1.0.0    # 首次穩定版本
1.1.0    # 新增 DCF 分析功能
1.1.1    # 修復 DCF 計算錯誤
1.2.0    # 新增投資組合分析功能
2.0.0    # 重大架構變更，不向後兼容
```

### 5.2 標籤管理 🔴

#### 創建標籤
```bash
# 創建帶註釋的標籤
git tag -a v1.2.0 -m "Release version 1.2.0

新功能:
- DCF 估值計算器
- 台股數據整合
- Streamlit 用戶界面

錯誤修復:
- 修復數據緩存問題
- 改善錯誤處理

性能改善:
- 優化 API 調用效率
- 改善記憶體使用"

# 推送標籤
git push origin v1.2.0

# 推送所有標籤
git push origin --tags
```

#### 標籤命名規範
```bash
v1.2.0           # 正式版本
v1.2.0-alpha.1   # Alpha 版本
v1.2.0-beta.2    # Beta 版本  
v1.2.0-rc.1      # Release Candidate
```

### 5.3 CHANGELOG 維護 🔴

#### CHANGELOG.md 格式
```markdown
# 變更日誌

本檔案記錄了專案的所有重要變更。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [未發布]

### 新增
- DCF 估值計算器優化功能

### 變更  
- 改善 UI 響應速度

### 修復
- 修復數據緩存過期問題

## [1.2.0] - 2025-06-13

### 新增
- DCF (折現現金流) 估值計算功能
- 台股財務數據自動獲取
- Streamlit 交互式用戶界面
- 投資組合分析功能
- 多股票比較分析

### 變更
- 重構數據處理模組，提高性能 30%
- 更新 UI 設計，改善用戶體驗
- 調整 API 回應格式，增加更多資訊

### 修復
- 修復 DCF 計算中的除零錯誤
- 解決數據緩存偶爾失效的問題
- 修正股票代碼驗證邏輯

### 移除
- 移除舊版數據格式支援
- 刪除不再使用的工具函數

### 安全性
- 加強 API 金鑰保護
- 改善輸入驗證機制

## [1.1.0] - 2025-05-15

### 新增
- 基本股票數據獲取功能
- 簡單財務比率計算

### 修復
- 修復數據解析錯誤

## [1.0.0] - 2025-04-30

### 新增
- 專案初始版本
- 基本專案架構
- 開發環境設置
```

---

## 6. 發布流程

### 6.1 發布準備 🔴

#### 發布前檢查清單
```markdown
## 🚀 發布檢查清單

### 代碼品質
- [ ] 所有測試通過（單元、整合、系統）
- [ ] 代碼覆蓋率 ≥ 80%
- [ ] 代碼通過 linting 檢查
- [ ] 沒有已知的嚴重錯誤

### 文檔
- [ ] CHANGELOG.md 已更新
- [ ] README.md 已更新（如需要）
- [ ] API 文檔已更新
- [ ] 部署指南已更新

### 版本管理
- [ ] 版本號已更新（setup.py, __init__.py）
- [ ] Git 標籤已創建
- [ ] 發布分支已創建

### 部署
- [ ] 生產環境部署測試完成
- [ ] 備份策略已確認
- [ ] 回滾計劃已準備

### 溝通
- [ ] 發布說明已準備
- [ ] 團隊已通知
- [ ] 用戶通知已準備（如需要）
```

### 6.2 發布步驟 🔴

#### 1. 創建發布分支
```bash
# 從 develop 創建發布分支
git checkout develop
git pull origin develop
git checkout -b release/v1.3.0
```

#### 2. 更新版本信息
```bash
# 更新 setup.py
version = "1.3.0"

# 更新 src/__init__.py
__version__ = "1.3.0"

# 更新 CHANGELOG.md
# 將 [未發布] 改為 [1.3.0] - 2025-06-13
```

#### 3. 最終測試
```bash
# 執行完整測試套件
python run_tests.py --all

# 代碼品質檢查
python run_tests.py --lint

# 手動測試關鍵功能
python -m streamlit run main_app.py
```

#### 4. 合併和標籤
```bash
# 合併到 main
git checkout main
git pull origin main
git merge --no-ff release/v1.3.0

# 創建標籤
git tag -a v1.3.0 -m "Release version 1.3.0"

# 合併回 develop
git checkout develop
git merge --no-ff release/v1.3.0

# 推送所有變更
git push origin main develop --tags

# 清理發布分支
git branch -d release/v1.3.0
git push origin --delete release/v1.3.0
```

### 6.3 發布後步驟 🟡

#### 發布說明模板
```markdown
# 🚀 JoJo Trading System v1.3.0 發布

我們很高興宣布 JoJo Trading System v1.3.0 的發布！

## ✨ 主要新功能

### DCF 估值優化
- 新增行業 Beta 值自動計算
- 改善現金流預測準確性
- 支援敏感性分析

### 用戶界面改善
- 全新的股票比較頁面
- 響應式設計優化
- 新增深色主題支援

## 🐛 錯誤修復
- 修復 DCF 計算中的除零錯誤
- 解決數據緩存問題
- 修正股票代碼驗證

## 📈 性能改善
- API 響應速度提升 40%
- 記憶體使用減少 25%
- 數據載入時間縮短

## 🔧 技術改善
- 升級到 Python 3.9
- 更新相依套件至最新版本
- 改善錯誤處理機制

## 📥 下載
- [Source Code (zip)](https://github.com/jojo-trading/releases/tag/v1.3.0)
- [Source Code (tar.gz)](https://github.com/jojo-trading/releases/tag/v1.3.0)

## 📚 文檔
- [升級指南](docs/deployment/UPGRADE_GUIDE.md)
- [API 文檔](docs/api/)
- [用戶指南](docs/user_guides/)

## 💬 回饋
如有任何問題或建議，請在 [GitHub Issues](https://github.com/jojo-trading/issues) 提出。

感謝所有貢獻者的努力！ 🎉
```

---

## 7. 熱修復流程

### 7.1 緊急修復流程 🔴

#### 何時使用熱修復
- 生產環境出現嚴重錯誤
- 安全性漏洞需要緊急修復
- 數據丟失或損壞風險
- 用戶無法正常使用核心功能

#### 熱修復步驟
```bash
# 1. 從 main 創建熱修復分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-dcf-error

# 2. 快速修復並測試
# 編輯相關文件
git add .
git commit -m "hotfix: 修復 DCF 計算中的除零錯誤

當 EPS 為 0 時會導致程式崩潰，現在改為:
- 檢查 EPS 是否為零
- 提供友善的錯誤訊息  
- 記錄異常情況

Fixes #789"

# 3. 執行關鍵測試
python -m pytest tests/unit/test_dcf_calculator.py::test_zero_eps_handling
python run_tests.py --smoke

# 4. 合併到 main
git checkout main
git merge --no-ff hotfix/critical-dcf-error

# 5. 創建補丁版本標籤
git tag -a v1.2.1 -m "Hotfix v1.2.1: 修復 DCF 計算錯誤"

# 6. 合併到 develop
git checkout develop
git merge --no-ff hotfix/critical-dcf-error

# 7. 推送和清理
git push origin main develop --tags
git branch -d hotfix/critical-dcf-error
```

### 7.2 熱修復溝通 🔴

#### 緊急通知模板
```markdown
🚨 **緊急修復通知**

**問題**: DCF 計算功能在特定條件下崩潰
**影響**: 影響所有使用 DCF 分析的用戶
**修復版本**: v1.2.1
**部署時間**: 2025-06-13 14:30

**修復內容**:
- 修復 EPS 為零時的除零錯誤
- 改善錯誤提示訊息
- 增加額外的輸入驗證

**用戶操作**:
- 無需額外操作
- 系統將自動更新
- 如仍遇到問題請聯繫技術支援

**技術團隊**: JoJo Trading Dev Team
```

---

## 8. 最佳實踐

### 8.1 日常開發 🔴

#### 分支命名最佳實踐
```bash
# ✅ 好的分支名稱
feature/dcf-sector-analysis
feature/user-authentication  
bugfix/portfolio-calculation-error
chore/upgrade-dependencies
docs/api-reference-update

# ❌ 避免的分支名稱
feature/new-stuff
fix/bug
temp
test-branch
john-dev
```

#### 提交頻率建議
```bash
# ✅ 適當的提交頻率
git commit -m "feat(dcf): 添加現金流預測基礎結構"
git commit -m "feat(dcf): 實現成長率計算邏輯"  
git commit -m "feat(dcf): 集成折現率計算"
git commit -m "test(dcf): 添加現金流預測測試"

# ❌ 避免的提交方式
# 太少：一次提交包含整個功能
# 太多：每改一行就提交一次
```

### 8.2 團隊協作 🟡

#### 衝突解決
```bash
# 當出現合併衝突時
git checkout feature/your-feature
git rebase develop

# 解決衝突後
git add .
git rebase --continue

# 強制推送（小心使用）
git push origin feature/your-feature --force-with-lease
```

#### 代碼審查最佳實踐
```markdown
## 審查者指南
1. **及時回應**: 24小時內完成審查
2. **建設性回饋**: 提供具體的改善建議
3. **學習態度**: 從他人代碼中學習
4. **平衡要求**: 區分"必須修改"和"建議修改"

## 提交者指南  
1. **自我審查**: 提交前先自己檢查一遍
2. **小幅變更**: 避免單次提交過多變更
3. **清楚描述**: PR 描述要清楚說明變更原因
4. **積極回應**: 及時回應審查意見
```

### 8.3 工具和自動化 🟡

#### Git Hooks 設置
```bash
# .git/hooks/pre-commit
#!/bin/sh
echo "執行 pre-commit 檢查..."

# 代碼格式檢查
python -m black --check src/ tests/
if [ $? -ne 0 ]; then
    echo "❌ Black 格式檢查失敗"
    exit 1
fi

# 代碼風格檢查  
python -m flake8 src/ tests/
if [ $? -ne 0 ]; then
    echo "❌ Flake8 檢查失敗"
    exit 1
fi

# 快速測試
python -m pytest tests/unit/ -x
if [ $? -ne 0 ]; then
    echo "❌ 單元測試失敗"
    exit 1
fi

echo "✅ 所有檢查通過"
```

#### Git 別名設置
```bash
# ~/.gitconfig
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    ca = commit -a
    cm = commit -m
    cam = commit -am
    
    # 日誌相關
    lg = log --oneline --graph --decorate
    lga = log --oneline --graph --decorate --all
    
    # 分支操作
    new = checkout -b
    del = branch -d
    
    # 快速操作
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = !gitk
```

---

## 📋 快速參考

### 常用命令 🔴
```bash
# 創建新功能分支
git checkout develop && git pull && git checkout -b feature/new-feature

# 更新分支到最新
git checkout develop && git pull && git checkout feature/your-feature && git rebase develop

# 查看分支狀態
git status && git log --oneline -5

# 提交變更
git add . && git commit -m "feat(scope): 描述變更"

# 推送分支
git push origin feature/your-feature

# 合併分支（在 develop）
git checkout develop && git merge --no-ff feature/your-feature

# 清理已合併的分支
git branch --merged | grep -v "\*\|develop\|main" | xargs -n 1 git branch -d
```

### 緊急情況處理 🔴
```bash
# 撤銷最後一次提交（但保留變更）
git reset --soft HEAD~1

# 撤銷最後一次提交（丟棄變更）
git reset --hard HEAD~1

# 暫存當前變更
git stash push -m "暫存描述"

# 恢復暫存的變更
git stash pop

# 查看文件變更歷史
git log --follow -p -- filename

# 恢復已刪除的文件
git checkout HEAD~1 -- filename
```

---

**最後更新**: 2025年6月13日  
**下次審查**: 2025年9月13日

如有任何關於 Git 工作流程的問題，請聯繫開發團隊或查閱 [Git 官方文檔](https://git-scm.com/doc)。
