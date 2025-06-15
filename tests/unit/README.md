# JoJo Trading System - Unit Tests

這個目錄包含所有的單元測試，用於測試個別函數和類別的功能。

## 目錄結構

```
unit/
├── test_dcf/               # DCF 估值模組測試
│   ├── test_dcf_calculator.py
│   ├── test_financial_metrics.py
│   └── test_valuation_models.py
├── test_data/              # 數據處理模組測試
│   ├── test_data_fetcher.py
│   ├── test_data_processor.py
│   └── test_cache_manager.py
├── test_utils/             # 工具函數測試
│   ├── test_helpers.py
│   └── test_validators.py
└── test_models/            # 數據模型測試
    ├── test_stock_model.py
    └── test_financial_model.py
```

## 運行單元測試

```bash
# 運行所有單元測試
pytest tests/unit/

# 運行特定模組測試
pytest tests/unit/test_dcf/

# 運行特定測試文件
pytest tests/unit/test_dcf/test_dcf_calculator.py

# 運行特定測試函數
pytest tests/unit/test_dcf/test_dcf_calculator.py::test_calculate_dcf_value

# 生成覆蓋率報告
pytest tests/unit/ --cov=src --cov-report=html
```

## 測試標準

1. **命名規範**: 測試文件以 `test_` 開頭，測試函數以 `test_` 開頭
2. **文檔化**: 每個測試都應有清楚的 docstring 說明測試目的
3. **獨立性**: 每個測試都應該是獨立的，不依賴其他測試的結果
4. **覆蓋率**: 目標是達到 80% 以上的代碼覆蓋率
5. **斷言清晰**: 使用清楚的斷言訊息，方便調試

## 常用測試模式

### 1. 基本功能測試
```python
def test_function_basic_functionality():
    """測試函數基本功能"""
    # Arrange
    input_data = {"key": "value"}
    expected = "expected_result"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected
```

### 2. 異常處理測試
```python
def test_function_error_handling():
    """測試異常處理"""
    with pytest.raises(ValueError, match="Expected error message"):
        function_under_test(invalid_input)
```

### 3. 參數化測試
```python
@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4),
    (3, 6)
])
def test_function_multiple_inputs(input_value, expected):
    """測試多種輸入情況"""
    result = double_function(input_value)
    assert result == expected
```
