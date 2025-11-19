# 🤖 DCF 參數自動化抓取能力分析報告

## 📋 四大參數自動化現況評估

### 1. 🎯 風險補償（折現率）
**自動化程度：⭐⭐⭐⭐☆ (80%)**

#### ✅ 已自動化部分
- **無風險利率**：可從 `macro_data_handler.py` 自動抓取台灣10年期公債殖利率
- **數據來源**：央行統計資料庫、Yahoo Finance
- **快取機制**：1天快取，多來源備援
- **預設回退值**：1.5%（當API失敗時）

#### 🔄 可進一步自動化
```python
# 已實現的無風險利率抓取
def get_risk_free_rate(self) -> float:
    """獲取台灣十年期公債殖利率（無風險利率）"""
    # 可自動抓取：1.5% - 2.0%
    
# 可增加的功能
def calculate_risk_premium(self, stock_code: str) -> float:
    """計算股票風險溢酬"""
    # 基於 Beta 值、產業風險、市值等自動計算
    # 風險補償 = 無風險利率 + 風險溢酬
```

#### 💡 自動化建議
- **基礎折現率**：無風險利率 (1.5%) + 市場風險溢酬 (4-6%)
- **個股調整**：可根據 Beta 值、產業別、市值大小自動調整
- **台股建議範圍**：6-12%（自動根據市況調整）

---

### 2. 🎯 篩選閾值
**自動化程度：⭐⭐☆☆☆ (40%)**

#### ❌ 主要為策略參數
篩選閾值屬於**投資策略參數**，通常需要**手動設定**：
- 保守型投資者：20-25%
- 平衡型投資者：15-20%
- 積極型投資者：10-15%

#### 🔄 可部分自動化
```python
def suggest_screening_threshold(self, market_condition: str, risk_profile: str) -> float:
    """根據市場環境和風險偏好建議篩選閾值"""
    suggestions = {
        ("bull_market", "aggressive"): 0.10,    # 牛市 + 積極型：10%
        ("bull_market", "balanced"): 0.15,     # 牛市 + 平衡型：15%
        ("bear_market", "conservative"): 0.25, # 熊市 + 保守型：25%
    }
    return suggestions.get((market_condition, risk_profile), 0.15)
```

---

### 3. 🎯 短期成長率
**自動化程度：⭐⭐⭐⭐⭐ (90%)**

#### ✅ 高度自動化
系統已具備完整的歷史成長率計算功能：

```python
# 已實現的自動計算功能
def get_revenue_cagr(financial_data: Dict, years: int) -> Optional[float]:
    """計算近N年營收CAGR"""
    
def get_eps_cagr(financial_data: Dict, years: int) -> Optional[float]:
    """計算近N年EPS CAGR"""

# 產業平均成長率參考
INDUSTRY_GROWTH_RATES = {
    "半導體": {"short_term": 10.0, "range": (5.0, 20.0)},
    "金融服務": {"short_term": 5.0, "range": (2.0, 10.0)},
    "傳統製造": {"short_term": 4.0, "range": (0.0, 8.0)},
    # ...更多產業
}
```

#### 🔄 可自動建議
```python
def auto_suggest_growth_rate(self, stock_code: str) -> float:
    """自動建議短期成長率"""
    # 1. 計算近3-5年營收/EPS CAGR
    historical_growth = get_eps_cagr(financial_data, 3)
    
    # 2. 參考產業平均
    industry_avg = get_industry_growth_rate(stock_code)
    
    # 3. 加權平均
    return (historical_growth * 0.7) + (industry_avg * 0.3)
```

---

### 4. 🎯 永續成長率
**自動化程度：⭐⭐⭐⭐☆ (80%)**

#### ✅ 已自動化部分
- **GDP成長率**：可從 `macro_data_handler.py` 自動抓取
- **數據來源**：主計總處統計資料
- **快取機制**：90天快取
- **預設值**：2.5%

#### 🔄 已實現功能
```python
def get_gdp_growth_rate(self) -> float:
    """獲取台灣GDP成長率"""
    # 可自動抓取：2.0% - 3.0%
    # 非常適合作為永續成長率參考
```

#### 💡 自動化建議
- **基準值**：GDP成長率 (2.5%)
- **保守調整**：GDP成長率 - 0.5% = 2.0%
- **樂觀情境**：GDP成長率 + 0.5% = 3.0%

---

## 🎯 自動化整合建議

### 自動參數建議系統設計
```python
class AutoDCFParameterSuggester:
    """DCF參數自動建議器"""
    
    def __init__(self):
        self.macro_handler = MacroDataHandler()
        self.growth_analyzer = GrowthAnalyzer()
    
    def get_auto_parameters(self, stock_code: str, risk_profile: str) -> dict:
        """獲取自動建議的DCF參數"""
        
        # 1. 風險補償（自動）
        risk_free_rate = self.macro_handler.get_risk_free_rate()
        risk_premium = self._calculate_risk_premium(stock_code)
        discount_rate = risk_free_rate + risk_premium
        
        # 2. 篩選閾值（半自動）
        screening_threshold = self._suggest_threshold(risk_profile)
        
        # 3. 短期成長率（自動）
        short_growth = self._calculate_auto_growth_rate(stock_code)
        
        # 4. 永續成長率（自動）
        terminal_growth = self.macro_handler.get_gdp_growth_rate()
        
        return {
            'discount_rate': discount_rate,
            'screening_threshold': screening_threshold,
            'short_term_growth': short_growth,
            'terminal_growth': terminal_growth,
            'data_sources': {
                'risk_free_rate': self.macro_handler.get_last_source(),
                'gdp_growth': self.macro_handler.get_last_source(),
                'historical_growth': '財報分析',
                'screening_threshold': '策略設定'
            }
        }
```

### UI 整合建議
```python
# 在 DCF 分析頁面新增"自動建議"按鈕
if st.button("🤖 使用智能參數建議"):
    auto_params = auto_suggester.get_auto_parameters(stock_code, risk_profile)
    
    st.info(f"""
    📊 **智能參數建議**：
    - 風險補償: {auto_params['discount_rate']:.1%} 
      (無風險利率 {risk_free_rate:.1%} + 風險溢酬 {risk_premium:.1%})
    - 篩選閾值: {auto_params['screening_threshold']:.1%}
    - 短期成長率: {auto_params['short_term_growth']:.1%}
    - 永續成長率: {auto_params['terminal_growth']:.1%}
    
    🔗 **數據來源**：
    - 無風險利率：{auto_params['data_sources']['risk_free_rate']}
    - GDP成長率：{auto_params['data_sources']['gdp_growth']}
    """)
```

---

## 📊 總結評估

### 自動化程度排名
1. **短期成長率** ⭐⭐⭐⭐⭐ (90%) - 已可完全自動計算
2. **風險補償** ⭐⭐⭐⭐☆ (80%) - 無風險利率可自動抓取
3. **永續成長率** ⭐⭐⭐⭐☆ (80%) - GDP成長率可自動抓取
4. **篩選閾值** ⭐⭐☆☆☆ (40%) - 主要依賴策略設定

### 🎯 下一步行動建議

#### 立即可實現（1週內）
- [ ] 在 DCF 頁面新增"智能參數建議"按鈕
- [ ] 整合現有的宏觀數據和成長率計算功能
- [ ] 顯示參數來源和更新時間

#### 中期優化（1個月內）
- [ ] 增加產業 Beta 值計算風險溢酬
- [ ] 建立市場情緒指標調整篩選閾值
- [ ] 加入分析師預測整合（如果有 API）

#### 長期目標（3個月內）
- [ ] 機器學習模型預測成長率
- [ ] 動態市場環境參數調整
- [ ] 多重情境分析自動化

---

**結論**：目前系統已具備 3/4 參數的高度自動化能力，只需簡單整合即可實現智能參數建議功能。
