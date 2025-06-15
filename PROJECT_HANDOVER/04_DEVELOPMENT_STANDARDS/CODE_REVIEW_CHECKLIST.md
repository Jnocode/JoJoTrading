# 👀 JoJo Trading System - 代碼審查檢查清單

**版本**: 1.0  
**制定日期**: 2025年6月13日  
**適用範圍**: 所有 Pull Request 審查

---

## 📋 目錄

- [1. 概述](#1-概述)
- [2. 審查流程](#2-審查流程)
- [3. 檢查清單](#3-檢查清單)
- [4. 審查回饋指南](#4-審查回饋指南)
- [5. 特殊情況處理](#5-特殊情況處理)
- [6. 工具和自動化](#6-工具和自動化)

---

## 1. 概述

### 1.1 代碼審查目標
- 🎯 **提高代碼品質**: 發現潛在錯誤和改善機會
- 🤝 **知識分享**: 促進團隊成員間的技術交流
- 📚 **維護標準**: 確保代碼符合專案標準
- 🛡️ **降低風險**: 在上線前發現和修復問題
- 🚀 **性能優化**: 識別性能改善機會

### 1.2 審查原則
- **建設性**: 提供具體、可行的改善建議
- **及時性**: 24小時內完成審查
- **尊重性**: 對事不對人，保持專業態度
- **學習性**: 互相學習，共同成長
- **平衡性**: 區分"必須修改"和"建議修改"

---

## 2. 審查流程

### 2.1 審查者準備 🔴

#### 開始審查前
```markdown
## 審查前檢查
- [ ] 理解 PR 的目的和背景
- [ ] 檢查相關 Issue 或需求文檔
- [ ] 確認 CI/CD 檢查已通過
- [ ] 準備充足的時間進行審查
- [ ] 切換到相應的分支進行本地測試
```

#### 環境準備
```bash
# 拉取 PR 分支進行本地測試
git fetch origin
git checkout -b pr-123 origin/feature/new-dcf-calculator

# 安裝依賴並運行測試
pip install -r requirements.txt
python run_tests.py --all

# 啟動應用進行功能測試
python -m streamlit run main_app.py
```

### 2.2 審查順序 🔴

#### 推薦的審查順序
1. **📝 PR 描述**: 檢查變更說明是否清楚
2. **🎯 整體架構**: 理解變更的影響範圍
3. **🔧 核心邏輯**: 重點審查業務邏輯代碼
4. **🧪 測試代碼**: 確保測試覆蓋和品質
5. **📚 文檔更新**: 檢查相關文檔是否更新
6. **🔍 細節檢查**: 代碼風格、命名等細節

---

## 3. 檢查清單

### 3.1 功能性檢查 🔴

#### 核心功能
```markdown
## 📋 功能性檢查

### 需求實現
- [ ] 變更是否符合原始需求？
- [ ] 是否解決了相關的 Issue？
- [ ] 功能是否完整實現？
- [ ] 是否有遺漏的邊界情況？

### 業務邏輯
- [ ] DCF 計算邏輯是否正確？
- [ ] 財務數據處理是否準確？
- [ ] 股票分析邏輯是否合理？
- [ ] 用戶輸入驗證是否完善？

### 邊界情況處理
- [ ] 零值或負值的處理
- [ ] 空值或缺失數據的處理
- [ ] 極大或極小數值的處理
- [ ] 無效輸入的處理
```

### 3.2 代碼品質檢查 🔴

#### 代碼結構
```markdown
## 🏗️ 代碼結構檢查

### 設計原則
- [ ] 是否遵循單一職責原則？
- [ ] 函數是否過長（建議 < 20 行）？
- [ ] 類是否職責明確？
- [ ] 是否避免代碼重複？

### 命名規範
- [ ] 變數名稱是否清楚描述其用途？
- [ ] 函數名稱是否表達其功能？
- [ ] 類名稱是否遵循 PascalCase？
- [ ] 常數是否使用 UPPER_SNAKE_CASE？

### 代碼風格
- [ ] 是否遵循 PEP 8 標準？
- [ ] 是否使用 Black 格式化？
- [ ] 導入順序是否正確？
- [ ] 註釋是否適當且有用？
```

#### 具體檢查項目
```python
# ✅ 好的例子
def calculate_dcf_intrinsic_value(
    free_cash_flows: List[float],
    discount_rate: float,
    terminal_growth_rate: float,
    projection_years: int = 5
) -> Dict[str, float]:
    """
    計算 DCF 內在價值
    
    Args:
        free_cash_flows: 歷史自由現金流（千元）
        discount_rate: 折現率（小數形式）
        terminal_growth_rate: 終期成長率（小數形式）
        projection_years: 預測年數
    
    Returns:
        包含內在價值和相關計算結果的字典
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    # 參數驗證
    if not free_cash_flows:
        raise ValueError("自由現金流數據不能為空")
    
    # 業務邏輯...
    return result

# ❌ 需要改善的例子
def calc(x, y, z):  # 函數名不清楚
    # 沒有文檔字串
    if x:  # 沒有參數驗證
        return x/y  # 可能除零錯誤
```

### 3.3 安全性檢查 🔴

#### 安全考量
```markdown
## 🔒 安全性檢查

### 輸入驗證
- [ ] 是否驗證所有用戶輸入？
- [ ] 是否防範注入攻擊？
- [ ] 股票代碼格式是否驗證？
- [ ] 數值範圍是否合理？

### 數據保護
- [ ] 敏感信息是否適當保護？
- [ ] API 金鑰是否安全存儲？
- [ ] 日誌中是否包含敏感信息？
- [ ] 錯誤訊息是否洩露過多信息？

### 權限控制
- [ ] 是否有適當的存取控制？
- [ ] 文件操作是否安全？
- [ ] 網路請求是否使用 HTTPS？
- [ ] 是否有速率限制保護？
```

#### 安全代碼示例
```python
# ✅ 安全的輸入驗證
def validate_stock_symbol(symbol: str) -> str:
    """驗證股票代碼"""
    if not isinstance(symbol, str):
        raise ValueError("股票代碼必須是字符串")
    
    # 清理輸入
    symbol = symbol.strip().upper()
    
    # 格式驗證
    if not re.match(r'^\d{4}$', symbol):
        raise ValueError("台股代碼必須是4位數字")
    
    return symbol

# ✅ 安全的 API 金鑰處理
def get_api_key() -> str:
    """安全地獲取 API 金鑰"""
    api_key = os.getenv('FINMIND_API_KEY')
    if not api_key:
        raise ValueError("API 金鑰未設置")
    return api_key

# ❌ 不安全的做法
def get_stock_data(symbol):
    # 直接使用用戶輸入，沒有驗證
    url = f"https://api.example.com/stock/{symbol}"
    return requests.get(url)
```

### 3.4 性能檢查 🟡

#### 性能考量
```markdown
## ⚡ 性能檢查

### 數據處理
- [ ] 是否使用高效的 Pandas 操作？
- [ ] 是否避免不必要的循環？
- [ ] 大數據集處理是否優化？
- [ ] 是否使用適當的數據結構？

### 記憶體使用
- [ ] 是否有記憶體洩漏風險？
- [ ] 大對象是否及時釋放？
- [ ] 是否重複創建不必要的對象？
- [ ] 緩存策略是否合理？

### API 調用
- [ ] 是否有不必要的 API 調用？
- [ ] 是否實現了適當的緩存？
- [ ] 是否有速率限制保護？
- [ ] 錯誤重試機制是否合理？
```

#### 性能優化示例
```python
# ✅ 高效的數據處理
def calculate_financial_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """計算財務比率（向量化操作）"""
    # 使用向量化操作
    df['pe_ratio'] = df['price'] / df['eps']
    df['pb_ratio'] = df['price'] / df['book_value']
    df['roe'] = df['net_income'] / df['shareholders_equity']
    
    return df

# ❌ 低效的數據處理
def calculate_ratios_slow(df: pd.DataFrame) -> pd.DataFrame:
    """低效的比率計算"""
    # 避免使用 iterrows
    for idx, row in df.iterrows():
        df.at[idx, 'pe_ratio'] = row['price'] / row['eps']
    return df

# ✅ 緩存優化
@lru_cache(maxsize=128)
def get_industry_beta(industry: str) -> float:
    """獲取行業 Beta 值（帶緩存）"""
    return calculate_industry_beta(industry)
```

### 3.5 測試檢查 🔴

#### 測試覆蓋
```markdown
## 🧪 測試檢查

### 測試完整性
- [ ] 是否有對應的單元測試？
- [ ] 測試覆蓋率是否足夠（≥80%）？
- [ ] 是否測試了邊界情況？
- [ ] 是否測試了錯誤處理？

### 測試品質
- [ ] 測試是否獨立且可重複？
- [ ] 測試命名是否清楚？
- [ ] 測試是否有清楚的 AAA 結構？
- [ ] 測試斷言是否明確？

### 測試類型
- [ ] 單元測試：測試個別函數
- [ ] 整合測試：測試模組互動
- [ ] 系統測試：測試端到端流程
- [ ] 性能測試：測試關鍵操作性能
```

#### 測試代碼示例
```python
# ✅ 好的測試結構
class TestDCFCalculator:
    """DCF 計算器測試"""
    
    def test_calculate_dcf_with_valid_inputs(self, sample_financial_data):
        """測試有效輸入的 DCF 計算"""
        # Arrange
        calculator = DCFCalculator(sample_financial_data)
        discount_rate = 0.10
        terminal_growth_rate = 0.03
        
        # Act
        result = calculator.calculate_dcf(discount_rate, terminal_growth_rate)
        
        # Assert
        assert result > 0
        assert isinstance(result, float)
        assert 'intrinsic_value' in calculator.last_calculation
    
    def test_calculate_dcf_with_invalid_discount_rate(self):
        """測試無效折現率應拋出異常"""
        # Arrange
        calculator = DCFCalculator({})
        invalid_rate = -0.05  # 負值
        
        # Act & Assert
        with pytest.raises(ValueError, match="折現率必須大於 0"):
            calculator.calculate_dcf(invalid_rate, 0.03)

# ❌ 需要改善的測試
def test_dcf():  # 名稱不清楚
    calc = DCFCalculator()  # 沒有明確的測試數據
    result = calc.calculate()  # 沒有參數
    assert result  # 斷言不明確
```

### 3.6 文檔檢查 🟡

#### 文檔完整性
```markdown
## 📚 文檔檢查

### 代碼文檔
- [ ] 函數是否有清楚的 docstring？
- [ ] 複雜邏輯是否有註釋說明？
- [ ] 類和模組是否有說明文檔？
- [ ] API 文檔是否更新？

### 外部文檔
- [ ] README 是否需要更新？
- [ ] CHANGELOG 是否記錄變更？
- [ ] 用戶指南是否需要更新？
- [ ] 部署文檔是否準確？

### 文檔品質
- [ ] 文檔內容是否準確？
- [ ] 是否包含使用示例？
- [ ] 是否說明參數和回傳值？
- [ ] 是否記錄已知限制？
```

---

## 4. 審查回饋指南

### 4.1 回饋分類 🔴

#### 優先級分類
```markdown
## 📊 回饋優先級

### 🔴 必須修改 (Must Fix)
- 功能錯誤或邏輯問題
- 安全性漏洞
- 性能嚴重問題
- 測試失敗或覆蓋率不足

### 🟡 建議修改 (Should Fix)
- 代碼風格不一致
- 命名不夠清楚
- 可讀性改善
- 小幅性能優化

### 🟢 輕微建議 (Nice to Have)
- 更好的實現方式
- 額外的測試案例
- 文檔改善
- 程式碼優化建議
```

### 4.2 回饋格式 🔴

#### 建設性回饋模板
```markdown
## 📝 代碼審查回饋

### 整體評價
簡要總結對這個 PR 的整體印象。

### 🔴 必須修改 (Must Fix)

#### 1. 安全性問題 - `src/dcf/calculator.py:45`
```python
# 當前代碼
def calculate_dcf(user_input):
    return eval(user_input)  # 危險！

# 建議修改
def calculate_dcf(discount_rate: float):
    if not 0 < discount_rate < 1:
        raise ValueError("折現率必須在 0 到 1 之間")
    return calculate_result(discount_rate)
```
**原因**: 使用 `eval()` 存在代碼注入風險

#### 2. 邏輯錯誤 - `src/data/processor.py:78`
```python
# 問題代碼
if eps == 0:
    pe_ratio = price / eps  # 除零錯誤！

# 建議修改  
if eps <= 0:
    pe_ratio = None  # 或適當的默認值
    logger.warning(f"EPS 為 {eps}，無法計算 PE 比率")
else:
    pe_ratio = price / eps
```
**原因**: 未處理除零情況會導致程式崩潰

### 🟡 建議修改 (Should Fix)

#### 1. 命名改善 - `src/utils/helpers.py:23`
```python
# 當前代碼
def calc_stuff(x, y):
    return x * y

# 建議修改
def calculate_total_value(price: float, quantity: int) -> float:
    """計算總價值"""
    return price * quantity
```
**原因**: 函數名稱應該清楚表達其功能

#### 2. 性能優化 - `src/analysis/ratios.py:15-25`
建議使用 Pandas 向量化操作來取代循環，可以提升性能約 10x。

### 🟢 輕微建議 (Nice to Have)

#### 1. 測試改善
考慮添加更多邊界情況的測試，例如極大數值的處理。

#### 2. 文檔完善
函數 `calculate_wacc()` 可以添加更詳細的計算公式說明。

### ✅ 讚賞
- 很好的錯誤處理實現！
- 測試覆蓋率很完整
- 代碼結構清晰易懂

### 📋 檢查清單
- [ ] 解決所有 "必須修改" 項目
- [ ] 考慮 "建議修改" 項目
- [ ] 更新相關測試
- [ ] 更新文檔（如需要）
```

### 4.3 積極溝通 🟡

#### 有效的審查溝通
```markdown
## 💬 審查溝通技巧

### ✅ 好的回饋方式
- "建議使用 `calculate_dcf_value()` 而非 `calc_dcf()`，名稱更清楚"
- "這個算法很聰明！考慮添加註釋說明計算邏輯"
- "測試覆蓋很完整，建議再加一個邊界情況測試"

### ❌ 避免的回饋方式  
- "這個代碼不好"（太泛泛）
- "你為什麼這樣寫？"（質疑語氣）
- "錯誤"（沒有說明原因）

### 💡 提問技巧
- "能否說明選擇這個算法的原因？"
- "是否考慮過使用緩存來優化性能？"
- "這個函數是否可以拆分為更小的部分？"
```

---

## 5. 特殊情況處理

### 5.1 大型 PR 審查 🟡

#### 大型變更的審查策略
```markdown
## 📏 大型 PR 審查

### 分階段審查
1. **架構層面**: 先審查整體設計和架構變更
2. **核心邏輯**: 重點審查業務邏輯代碼
3. **測試代碼**: 確保測試覆蓋完整
4. **文檔更新**: 檢查相關文檔更新
5. **細節檢查**: 最後檢查代碼風格和細節

### 建議作法
- [ ] 要求將大型 PR 拆分為較小的部分
- [ ] 重點關注高風險和核心變更
- [ ] 安排多人參與審查
- [ ] 進行額外的整合測試
- [ ] 考慮漸進式部署
```

### 5.2 緊急修復審查 🔴

#### 熱修復的快速審查
```markdown
## 🚨 緊急修復審查

### 快速檢查重點
- [ ] 修復是否針對根本原因？
- [ ] 是否會引入新的問題？
- [ ] 測試是否涵蓋修復的情況？
- [ ] 是否有適當的錯誤處理？
- [ ] 回滾計劃是否準備好？

### 加速流程
- 指派最熟悉相關代碼的審查者
- 並行進行審查和測試
- 重點關注修復邏輯，次要關注代碼風格
- 確保有詳細的修復說明
- 安排修復後的監控
```

### 5.3 新人代碼審查 🟡

#### 對新團隊成員的特殊考量
```markdown
## 👋 新人代碼審查

### 額外支持
- [ ] 提供更詳細的解釋和示例
- [ ] 指出專案特定的最佳實踐
- [ ] 推薦相關的學習資源
- [ ] 安排配對程式設計會議
- [ ] 鼓勵提問和討論

### 教學重點
- 專案架構和設計模式
- 特定的業務邏輯（如 DCF 計算）
- 測試策略和工具
- 代碼風格和慣例
- Git 工作流程
```

---

## 6. 工具和自動化

### 6.1 自動化檢查 🔴

#### CI/CD 整合
```yaml
# .github/workflows/pr-checks.yml
name: PR 檢查

on:
  pull_request:
    branches: [ develop, main ]

jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: 設置 Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: 安裝依賴
      run: |
        pip install -r requirements.txt
        pip install flake8 black mypy pytest-cov
    
    - name: 代碼風格檢查
      run: |
        black --check src/ tests/
        flake8 src/ tests/
        mypy src/
    
    - name: 運行測試
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: 上傳覆蓋率報告
      uses: codecov/codecov-action@v3
```

### 6.2 審查工具 🟡

#### GitHub PR 模板
```markdown
<!-- .github/pull_request_template.md -->
## 🎯 變更描述
簡要描述這個 PR 的目的和變更內容。

## 📋 變更類型
- [ ] 新功能 (feat)
- [ ] 錯誤修復 (fix)
- [ ] 重構 (refactor)
- [ ] 文檔更新 (docs)
- [ ] 性能優化 (perf)
- [ ] 測試 (test)
- [ ] 其他 (chore)

## 🧪 測試檢查
- [ ] 所有現有測試通過
- [ ] 新增了相應的測試
- [ ] 手動測試完成
- [ ] 測試覆蓋率 ≥ 80%

## 📋 審查清單
- [ ] 代碼遵循專案標準
- [ ] 函數有適當的 docstring
- [ ] 錯誤處理完善
- [ ] 性能考量合理
- [ ] 安全性檢查完成

## 🔗 相關 Issue
Closes #123

## 📝 審查注意事項
特別需要審查的地方或注意事項。

## 📸 測試截圖
如果有 UI 變更，請提供截圖。
```

### 6.3 審查指標 🟡

#### 追蹤審查品質
```markdown
## 📊 審查指標

### 量化指標
- 平均審查時間: < 24 小時
- 審查參與率: > 90%
- 發現問題率: 記錄每次審查發現的問題數量
- 修復效率: 問題修復的平均時間

### 定性指標  
- 審查回饋的建設性
- 團隊學習和知識分享
- 代碼品質改善趨勢
- 開發者滿意度

### 改善建議
- 定期審查審查流程本身
- 收集團隊回饋意見
- 持續優化審查工具和流程
- 分享最佳實踐案例
```

---

## 📋 快速檢查清單

### 審查者快速檢查 🔴
```markdown
## ⚡ 5分鐘快速檢查

### 必要檢查 (2分鐘)
- [ ] CI/CD 檢查是否通過？
- [ ] PR 描述是否清楚？
- [ ] 變更是否符合需求？
- [ ] 是否有明顯的邏輯錯誤？

### 重點檢查 (3分鐘)
- [ ] 核心業務邏輯是否正確？
- [ ] 錯誤處理是否完善？
- [ ] 測試是否足夠？
- [ ] 是否有安全性問題？
- [ ] 性能是否合理？
```

### 提交者自檢清單 🔴
```markdown
## ✅ 提交前自檢

### 代碼品質
- [ ] 代碼通過所有自動化檢查
- [ ] 函數有清楚的 docstring
- [ ] 變數命名清楚有意義
- [ ] 沒有多餘的代碼或註釋

### 測試
- [ ] 新功能有對應的測試
- [ ] 所有測試通過
- [ ] 測試覆蓋率足夠
- [ ] 手動測試完成

### 文檔
- [ ] PR 描述清楚完整
- [ ] 相關文檔已更新
- [ ] API 變更有文檔說明
- [ ] 破壞性變更有遷移指南
```

---

**最後更新**: 2025年6月13日  
**下次審查**: 2025年9月13日

這份檢查清單是活文檔，請根據專案需求和團隊經驗持續更新和改善。
