# 🐍 JoJo Trading System - 編程標準規範

**版本**: 1.0  
**制定日期**: 2025年6月13日  
**適用範圍**: JoJo Trading System 所有 Python 代碼

---

## 📋 目錄

- [1. 概述](#1-概述)
- [2. 代碼風格](#2-代碼風格)
- [3. 命名規範](#3-命名規範)
- [4. 註釋和文檔](#4-註釋和文檔)
- [5. 函數和類設計](#5-函數和類設計)
- [6. 錯誤處理](#6-錯誤處理)
- [7. 性能考量](#7-性能考量)
- [8. 安全性](#8-安全性)
- [9. 測試標準](#9-測試標準)
- [10. 工具配置](#10-工具配置)

---

## 1. 概述

### 1.1 目標
- 確保代碼一致性和可讀性
- 提高代碼品質和維護性
- 促進團隊協作效率
- 減少代碼審查時間

### 1.2 適用範圍
本標準適用於 JoJo Trading System 的所有 Python 代碼，包括：
- 核心業務邏輯代碼 (`src/`)
- 測試代碼 (`tests/`)
- 工具腳本 (`scripts/`)
- 配置文件

### 1.3 強制性規則 vs 建議性規則
- 🔴 **強制性**: 必須遵守，CI/CD 會檢查
- 🟡 **建議性**: 強烈建議遵守，有助於代碼品質

---

## 2. 代碼風格

### 2.1 基本原則 🔴
- 遵循 **PEP 8** 標準
- 使用 **Black** 進行代碼格式化
- 行長度限制為 **88 字符**（Black 默認）
- 使用 **4 個空格** 縮排，不使用 Tab

### 2.2 導入規範 🔴

#### 導入順序
```python
# 1. 標準庫導入
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 2. 第三方庫導入
import pandas as pd
import numpy as np
import streamlit as st
from loguru import logger

# 3. 本地導入
from src.models.stock import Stock
from src.utils.helpers import format_currency
from .dcf_calculator import DCFCalculator
```

#### 導入格式化 🔴
```python
# ✅ 正確
from typing import Dict, List, Optional, Union

# ❌ 錯誤
from typing import *

# ✅ 正確 - 長導入使用括號
from some_very_long_module_name import (
    very_long_function_name,
    another_long_function_name,
    yet_another_function
)
```

### 2.3 空白和換行 🔴

#### 類和函數間隔
```python
# 頂級類和函數間用 2 行空行
class StockAnalyzer:
    pass


class DCFCalculator:
    pass


def main():
    pass
```

#### 類內方法間隔
```python
class StockAnalyzer:
    def __init__(self):
        pass
    
    def analyze(self):  # 方法間用 1 行空行
        pass
    
    def calculate(self):
        pass
```

---

## 3. 命名規範

### 3.1 命名風格 🔴

| 元素類型 | 命名風格 | 示例 |
|---------|---------|------|
| **變數/函數** | snake_case | `stock_price`, `calculate_dcf()` |
| **類別** | PascalCase | `StockAnalyzer`, `DCFCalculator` |
| **常數** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_TIMEOUT` |
| **模組/套件** | snake_case | `data_fetcher.py`, `utils/` |
| **私有屬性** | _leading_underscore | `_private_method()`, `_internal_var` |

### 3.2 描述性命名 🔴

#### ✅ 好的命名
```python
def calculate_dcf_value(
    free_cash_flows: List[float],
    discount_rate: float,
    terminal_growth_rate: float
) -> float:
    """計算 DCF 估值"""
    pass

class TaiwanStockAnalyzer:
    """台股分析器"""
    def __init__(self, stock_symbol: str):
        self.stock_symbol = stock_symbol
        self.financial_data = None
        self.dcf_result = None
```

#### ❌ 避免的命名
```python
def calc(x, y, z):  # 不清楚的函數名和參數
    pass

class SA:  # 縮寫不清楚
    def __init__(self, s):  # 參數名不清楚
        self.d = None  # 屬性名不清楚
```

### 3.3 特殊命名規則 🟡

#### 金融術語標準化
```python
# ✅ 使用標準金融術語
free_cash_flow = calculate_fcf()
earnings_per_share = get_eps()
price_to_earnings_ratio = calculate_pe_ratio()
discounted_cash_flow = calculate_dcf()

# 常用縮寫對照表
# FCF = Free Cash Flow (自由現金流)
# DCF = Discounted Cash Flow (折現現金流)
# EPS = Earnings Per Share (每股盈餘)
# ROE = Return on Equity (股東權益報酬率)
# WACC = Weighted Average Cost of Capital (加權平均資本成本)
```

---

## 4. 註釋和文檔

### 4.1 文檔字串 (Docstrings) 🔴

#### 模組層級文檔
```python
"""
JoJo Trading System - DCF 估值計算模組

這個模組提供 DCF (Discounted Cash Flow) 估值計算功能，
包括自由現金流預測、折現率計算和終值估算。

主要類別:
    DCFCalculator: 主要的 DCF 計算器
    CashFlowProjector: 現金流預測器

主要函數:
    calculate_dcf_value: 計算 DCF 估值
    project_cash_flows: 預測未來現金流

作者: JoJo Trading Development Team
創建日期: 2025-06-13
版本: 1.0
"""
```

#### 類別文檔 🔴
```python
class DCFCalculator:
    """
    DCF (折現現金流) 估值計算器
    
    這個類別實現了完整的 DCF 估值模型，包括：
    - 自由現金流預測
    - 折現率計算 (WACC)
    - 終值計算
    - 敏感性分析
    
    Attributes:
        stock_symbol (str): 股票代號
        discount_rate (float): 折現率
        terminal_growth_rate (float): 終期成長率
        projection_years (int): 預測年數
    
    Example:
        >>> calculator = DCFCalculator("2330")
        >>> calculator.set_parameters(discount_rate=0.10)
        >>> result = calculator.calculate()
        >>> print(f"估值: {result.intrinsic_value}")
    """
```

#### 函數文檔 🔴
```python
def calculate_dcf_value(
    free_cash_flows: List[float],
    discount_rate: float,
    terminal_growth_rate: float,
    projection_years: int = 5
) -> Dict[str, float]:
    """
    計算 DCF 估值
    
    使用折現現金流模型計算公司的內在價值。
    
    Args:
        free_cash_flows: 歷史自由現金流列表 (單位: 千元)
        discount_rate: 折現率 (小數形式, 例如 0.10 代表 10%)
        terminal_growth_rate: 終期成長率 (小數形式)
        projection_years: 預測年數，默認為 5 年
    
    Returns:
        包含以下鍵值的字典:
            - 'intrinsic_value': 內在價值 (千元)
            - 'terminal_value': 終值 (千元)
            - 'pv_projection': 預測期現值 (千元)
            - 'pv_terminal': 終值現值 (千元)
    
    Raises:
        ValueError: 當輸入參數無效時
        ZeroDivisionError: 當折現率為負值時
    
    Example:
        >>> fcf_history = [1000, 1100, 1200, 1300, 1400]
        >>> result = calculate_dcf_value(fcf_history, 0.10, 0.03)
        >>> print(f"內在價值: {result['intrinsic_value']:,.0f} 千元")
        內在價值: 15,234 千元
    
    Note:
        - 假設自由現金流以複利成長
        - 終值使用 Gordon Growth Model 計算
        - 所有金額單位為千元台幣
    """
```

### 4.2 行內註釋 🟡

#### 何時使用行內註釋
```python
def calculate_wacc(debt_ratio: float, tax_rate: float) -> float:
    """計算加權平均資本成本"""
    
    # 無風險利率使用 10 年期政府公債殖利率
    risk_free_rate = get_government_bond_yield(years=10)
    
    # 市場風險溢價參考台股歷史數據
    market_risk_premium = 0.08  # 8% 基於 20 年歷史平均
    
    # Beta 值使用過去 3 年的計算結果
    beta = calculate_beta(period_years=3)
    
    equity_cost = risk_free_rate + beta * market_risk_premium
    debt_cost = get_corporate_bond_yield() * (1 - tax_rate)  # 稅後債務成本
    
    # WACC = E/V * Re + D/V * Rd * (1-T)
    wacc = (1 - debt_ratio) * equity_cost + debt_ratio * debt_cost
    
    return wacc
```

### 4.3 TODO 和 FIXME 註釋 🟡

```python
# TODO(johndoe): 實現更精確的 Beta 計算方法
# FIXME: 處理除零錯誤的邊界情況
# NOTE: 這個算法基於 Graham 和 Dodd 的價值投資理論
# WARNING: 這個函數在市場極端波動時可能不準確
```

---

## 5. 函數和類設計

### 5.1 函數設計原則 🔴

#### 單一職責原則
```python
# ✅ 好的設計 - 每個函數只做一件事
def fetch_financial_data(stock_symbol: str) -> Dict:
    """獲取財務數據"""
    pass

def calculate_financial_ratios(financial_data: Dict) -> Dict:
    """計算財務比率"""
    pass

def generate_analysis_report(ratios: Dict) -> str:
    """生成分析報告"""
    pass

# ❌ 不好的設計 - 函數做太多事情
def analyze_stock_everything(stock_symbol: str) -> str:
    """獲取數據、計算比率、生成報告"""  # 違反單一職責
    pass
```

#### 函數長度 🟡
```python
# ✅ 函數應該簡潔明了（建議 < 20 行）
def calculate_pe_ratio(price: float, eps: float) -> float:
    """計算本益比"""
    if eps <= 0:
        raise ValueError("EPS 必須大於 0")
    
    return price / eps

# ❌ 過長的函數應該拆分
def complex_analysis(data):  # 50+ 行的函數
    # ... 過多邏輯
    pass
```

### 5.2 類設計原則 🔴

#### 類的職責劃分
```python
# ✅ 職責清晰的類設計
class StockDataFetcher:
    """專門負責股票數據獲取"""
    
    def fetch_price_data(self, symbol: str) -> pd.DataFrame:
        pass
    
    def fetch_financial_statements(self, symbol: str) -> Dict:
        pass

class DCFCalculator:
    """專門負責 DCF 計算"""
    
    def __init__(self, financial_data: Dict):
        self.financial_data = financial_data
    
    def calculate_dcf(self) -> float:
        pass

class ReportGenerator:
    """專門負責報告生成"""
    
    def generate_dcf_report(self, dcf_result: Dict) -> str:
        pass
```

#### 類的屬性管理 🔴
```python
class Stock:
    """股票類別"""
    
    def __init__(self, symbol: str, name: str):
        # 公開屬性
        self.symbol = symbol
        self.name = name
        
        # 私有屬性使用下劃線前綴
        self._price_data = None
        self._financial_data = None
        
        # 緩存屬性
        self._dcf_value_cache = None
        self._cache_timestamp = None
    
    @property
    def current_price(self) -> Optional[float]:
        """當前股價（只讀屬性）"""
        if self._price_data is None:
            self._fetch_price_data()
        return self._price_data.iloc[-1]['close']
    
    @property
    def dcf_value(self) -> float:
        """DCF 估值（帶緩存）"""
        if self._dcf_value_cache is None or self._cache_expired():
            self._dcf_value_cache = self._calculate_dcf()
            self._cache_timestamp = datetime.now()
        return self._dcf_value_cache
```

### 5.3 參數設計 🔴

#### 使用類型提示
```python
from typing import List, Dict, Optional, Union
from decimal import Decimal

# ✅ 完整的類型提示
def calculate_portfolio_value(
    holdings: Dict[str, int],  # 股票代號 -> 持股數量
    prices: Dict[str, float],  # 股票代號 -> 當前價格
    currency: str = "TWD"
) -> Decimal:
    """計算投資組合價值"""
    pass

# ✅ 複雜類型使用 TypedDict
from typing_extensions import TypedDict

class StockInfo(TypedDict):
    symbol: str
    name: str
    sector: str
    market_cap: float

def analyze_stocks(stocks: List[StockInfo]) -> Dict[str, float]:
    """分析股票列表"""
    pass
```

#### 參數驗證 🔴
```python
def calculate_dcf_value(
    free_cash_flows: List[float],
    discount_rate: float,
    terminal_growth_rate: float
) -> float:
    """計算 DCF 估值"""
    
    # 參數驗證
    if not free_cash_flows:
        raise ValueError("自由現金流列表不能為空")
    
    if len(free_cash_flows) < 3:
        raise ValueError("至少需要 3 年的現金流數據")
    
    if not 0 < discount_rate < 1:
        raise ValueError("折現率必須在 0 到 1 之間")
    
    if not -0.1 <= terminal_growth_rate <= 0.1:
        raise ValueError("終期成長率應在 -10% 到 10% 之間")
    
    # 實際計算邏輯
    return calculated_value
```

---

## 6. 錯誤處理

### 6.1 異常處理原則 🔴

#### 具體異常處理
```python
# ✅ 捕獲具體異常
try:
    financial_data = fetch_financial_data(stock_symbol)
except requests.RequestException as e:
    logger.error(f"API 請求失敗: {e}")
    raise DataFetchError(f"無法獲取 {stock_symbol} 的財務數據")
except KeyError as e:
    logger.error(f"數據格式錯誤: {e}")
    raise DataParsingError("API 返回的數據格式不正確")

# ❌ 捕獲太泛泛的異常
try:
    financial_data = fetch_financial_data(stock_symbol)
except Exception:  # 太泛泛
    pass  # 沒有處理
```

#### 自定義異常 🔴
```python
# 定義業務邏輯相關的異常
class JojoTradingError(Exception):
    """JoJo Trading 系統基礎異常"""
    pass

class DataFetchError(JojoTradingError):
    """數據獲取異常"""
    pass

class CalculationError(JojoTradingError):
    """計算異常"""
    pass

class ValidationError(JojoTradingError):
    """數據驗證異常"""
    pass

# 使用自定義異常
def calculate_dcf(financial_data: Dict) -> float:
    if not financial_data:
        raise ValidationError("財務數據不能為空")
    
    try:
        return perform_dcf_calculation(financial_data)
    except ZeroDivisionError:
        raise CalculationError("計算過程中出現除零錯誤，請檢查數據完整性")
```

### 6.2 日誌記錄 🔴

#### 使用結構化日誌
```python
from loguru import logger

# ✅ 結構化日誌記錄
def fetch_stock_data(symbol: str) -> Dict:
    logger.info("開始獲取股票數據", symbol=symbol)
    
    try:
        data = api_client.get_stock_data(symbol)
        logger.info(
            "成功獲取股票數據",
            symbol=symbol,
            data_points=len(data),
            last_update=data.get('last_update')
        )
        return data
        
    except requests.Timeout:
        logger.warning(
            "API 請求超時",
            symbol=symbol,
            timeout_seconds=30
        )
        raise DataFetchError(f"獲取 {symbol} 數據超時")
        
    except Exception as e:
        logger.error(
            "獲取股票數據失敗",
            symbol=symbol,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise
```

#### 日誌級別使用 🟡
```python
# DEBUG: 詳細的調試信息
logger.debug("計算 DCF 中間結果", fcf_growth_rate=0.15, wacc=0.10)

# INFO: 一般信息記錄
logger.info("開始分析股票", symbol="2330")

# WARNING: 警告但不影響執行
logger.warning("現金流數據可能不完整", missing_years=2)

# ERROR: 錯誤但程序可以繼續
logger.error("API 調用失敗，使用緩存數據", api="finmind")

# CRITICAL: 嚴重錯誤，程序可能無法繼續
logger.critical("資料庫連接失敗", database="stock_data")
```

---

## 7. 性能考量

### 7.1 數據處理優化 🟡

#### 使用 Pandas 最佳實踐
```python
# ✅ 高效的 Pandas 操作
def process_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """處理價格數據"""
    
    # 使用向量化操作而不是循環
    df['returns'] = df['close'].pct_change()
    df['ma_20'] = df['close'].rolling(window=20).mean()
    df['volatility'] = df['returns'].rolling(window=30).std()
    
    # 使用 .loc 進行條件選擇
    high_volume_days = df.loc[df['volume'] > df['volume'].quantile(0.8)]
    
    return df

# ❌ 避免的低效操作
def inefficient_processing(df: pd.DataFrame) -> pd.DataFrame:
    """低效的數據處理"""
    
    # 避免 iterrows()
    for idx, row in df.iterrows():  # 慢
        df.at[idx, 'returns'] = (row['close'] / df.at[idx-1, 'close']) - 1
    
    return df
```

#### 緩存策略 🔴
```python
from functools import lru_cache
import pickle
from pathlib import Path

class DataCache:
    """數據緩存管理器"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_path(self, key: str) -> Path:
        """獲取緩存文件路徑"""
        return self.cache_dir / f"{key}.pkl"
    
    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """獲取緩存數據"""
        cache_file = self.get_cache_path(key)
        
        if not cache_file.exists():
            return None
        
        # 檢查緩存是否過期
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age > max_age_hours * 3600:
            cache_file.unlink()  # 刪除過期緩存
            return None
        
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    def set(self, key: str, data: Any) -> None:
        """設置緩存數據"""
        cache_file = self.get_cache_path(key)
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

# 使用緩存裝飾器
@lru_cache(maxsize=128)
def calculate_financial_ratios(
    revenue: float,
    net_income: float,
    total_assets: float
) -> Dict[str, float]:
    """計算財務比率（帶記憶體緩存）"""
    return {
        'profit_margin': net_income / revenue,
        'roa': net_income / total_assets
    }
```

### 7.2 API 調用優化 🟡

#### 批量請求和重試機制
```python
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

class StockDataAPI:
    """股票數據 API 客戶端"""
    
    def __init__(self):
        self.session = None
        self.rate_limit = 10  # 每秒最多 10 個請求
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch_stock_data(self, symbol: str) -> Dict:
        """獲取單一股票數據（帶重試）"""
        async with self.session.get(f"/api/stock/{symbol}") as response:
            response.raise_for_status()
            return await response.json()
    
    async def fetch_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量獲取股票數據"""
        semaphore = asyncio.Semaphore(self.rate_limit)
        
        async def fetch_with_limit(symbol: str):
            async with semaphore:
                try:
                    return symbol, await self.fetch_stock_data(symbol)
                except Exception as e:
                    logger.warning(f"獲取 {symbol} 數據失敗: {e}")
                    return symbol, None
        
        # 並行請求
        tasks = [fetch_with_limit(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        return {symbol: data for symbol, data in results if data is not None}
```

---

## 8. 安全性

### 8.1 輸入驗證 🔴

#### 數據驗證
```python
import re
from typing import Pattern

# 股票代號驗證
TAIWAN_STOCK_PATTERN: Pattern = re.compile(r'^\d{4}$')

def validate_taiwan_stock_symbol(symbol: str) -> str:
    """驗證台股代號"""
    if not isinstance(symbol, str):
        raise ValueError("股票代號必須是字符串")
    
    symbol = symbol.strip()
    
    if not TAIWAN_STOCK_PATTERN.match(symbol):
        raise ValueError("台股代號必須是 4 位數字")
    
    return symbol

def validate_financial_data(data: Dict) -> Dict:
    """驗證財務數據"""
    required_fields = ['revenue', 'net_income', 'total_assets']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"缺少必要字段: {field}")
        
        value = data[field]
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{field} 必須是非負數")
    
    return data
```

### 8.2 API 金鑰管理 🔴

#### 環境變數使用
```python
import os
from typing import Optional

def get_api_key(service: str) -> str:
    """安全地獲取 API 金鑰"""
    env_var = f"{service.upper()}_API_KEY"
    api_key = os.getenv(env_var)
    
    if not api_key:
        raise ValueError(f"未找到 {service} API 金鑰，請設置環境變數 {env_var}")
    
    return api_key

# 配置類
class APIConfig:
    """API 配置管理"""
    
    def __init__(self):
        self.finmind_api_key = get_api_key("finmind")
        self.twse_api_key = get_api_key("twse")
        
    @property
    def headers(self) -> Dict[str, str]:
        """獲取 API 請求標頭"""
        return {
            "Authorization": f"Bearer {self.finmind_api_key}",
            "User-Agent": "JoJo-Trading-System/1.0"
        }
```

### 8.3 數據脫敏 🟡

#### 敏感信息處理
```python
def sanitize_financial_data(data: Dict) -> Dict:
    """脫敏財務數據用於日誌記錄"""
    sensitive_fields = ['api_key', 'user_id', 'account_number']
    
    sanitized = data.copy()
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "***REDACTED***"
    
    return sanitized

def log_api_request(url: str, params: Dict) -> None:
    """安全地記錄 API 請求"""
    safe_params = sanitize_financial_data(params)
    logger.info("API 請求", url=url, params=safe_params)
```

---

## 9. 測試標準

### 9.1 測試分類 🔴

#### 測試命名規範
```python
# 測試文件命名: test_[模組名].py
# tests/unit/test_dcf_calculator.py
# tests/integration/test_data_pipeline.py
# tests/system/test_complete_workflow.py

class TestDCFCalculator:
    """DCF 計算器測試類"""
    
    def test_calculate_dcf_with_valid_inputs(self):
        """測試有效輸入的 DCF 計算"""
        pass
    
    def test_calculate_dcf_with_zero_growth_rate(self):
        """測試零成長率的邊界情況"""
        pass
    
    def test_calculate_dcf_raises_error_with_invalid_discount_rate(self):
        """測試無效折現率應拋出異常"""
        pass
```

#### 測試結構 (Arrange-Act-Assert) 🔴
```python
def test_calculate_pe_ratio():
    """測試本益比計算"""
    # Arrange (準備)
    price = 100.0
    eps = 5.0
    expected_pe = 20.0
    
    # Act (執行)
    actual_pe = calculate_pe_ratio(price, eps)
    
    # Assert (驗證)
    assert actual_pe == expected_pe
    assert isinstance(actual_pe, float)
```

### 9.2 測試覆蓋率 🔴

#### 覆蓋率目標
- **單元測試**: 90% 以上
- **整合測試**: 80% 以上  
- **關鍵業務邏輯**: 95% 以上

#### 測試夾具 (Fixtures) 🟡
```python
import pytest
from decimal import Decimal

@pytest.fixture
def sample_financial_data():
    """樣本財務數據夾具"""
    return {
        'revenue': [1000000, 1100000, 1200000],
        'net_income': [100000, 110000, 120000],
        'free_cash_flow': [80000, 88000, 96000],
        'shares_outstanding': 1000000
    }

@pytest.fixture
def dcf_calculator(sample_financial_data):
    """DCF 計算器夾具"""
    return DCFCalculator(sample_financial_data)

def test_dcf_calculation(dcf_calculator):
    """使用夾具測試 DCF 計算"""
    result = dcf_calculator.calculate(discount_rate=0.10)
    assert result > 0
    assert isinstance(result, Decimal)
```

---

## 10. 工具配置

### 10.1 開發工具配置 🔴

#### `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.8
        
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
        
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

#### `pyproject.toml`
```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src", "tests"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 10.2 IDE 配置 🟡

#### VS Code 設置
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "editor.formatOnSave": true
}
```

---

## 📝 檢查清單

### 提交前檢查 🔴
- [ ] 代碼通過 Black 格式化
- [ ] 代碼通過 Flake8 檢查
- [ ] 代碼通過 MyPy 類型檢查
- [ ] 所有測試通過
- [ ] 新功能有對應的測試
- [ ] 文檔字串完整
- [ ] 沒有 TODO 或 FIXME 標記（除非有對應的 issue）

### 代碼審查檢查 🔴
- [ ] 命名清晰且有意義
- [ ] 函數職責單一
- [ ] 錯誤處理適當
- [ ] 性能考量合理
- [ ] 安全性檢查完成
- [ ] 文檔和註釋充分

---

**最後更新**: 2025年6月13日  
**下次審查**: 2025年9月13日
