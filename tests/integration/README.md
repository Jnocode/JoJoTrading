# JoJo Trading System - Integration Tests

這個目錄包含整合測試，用於測試不同模組之間的互動和數據流。

## 目錄結構

```
integration/
├── test_api_integration/      # API 整合測試
│   ├── test_finmind_api.py
│   ├── test_twse_api.py
│   └── test_external_apis.py
├── test_data_pipeline/        # 數據管道測試
│   ├── test_data_flow.py
│   ├── test_cache_integration.py
│   └── test_data_validation.py
├── test_dcf_integration/      # DCF 估值整合測試
│   ├── test_full_dcf_process.py
│   └── test_sector_analysis.py
└── test_ui_backend/           # 前後端整合測試
    ├── test_streamlit_integration.py
    └── test_page_functionality.py
```

## 運行整合測試

```bash
# 運行所有整合測試
pytest tests/integration/

# 運行特定整合測試模組
pytest tests/integration/test_api_integration/

# 運行需要網路連接的測試
pytest tests/integration/ -m "not slow"

# 運行慢速測試（需要外部資源）
pytest tests/integration/ -m "slow"
```

## 測試分類

### 1. API 整合測試
- 測試與外部 API 的連接和數據獲取
- 驗證數據格式和完整性
- 測試錯誤處理和重試機制

### 2. 數據管道測試
- 測試從數據獲取到處理的完整流程
- 驗證緩存機制的正確性
- 測試數據轉換和清理過程

### 3. 業務邏輯整合測試
- 測試 DCF 估值的端到端流程
- 驗證不同模組間的數據傳遞
- 測試計算結果的一致性

### 4. UI 整合測試
- 測試 Streamlit 頁面功能
- 驗證用戶操作流程
- 測試數據展示的正確性

## 測試配置

### 環境設置
```python
# 測試環境變數
TESTING=true
API_TIMEOUT=30
CACHE_TTL=300
LOG_LEVEL=DEBUG
```

### 外部依賴模擬
```python
# 使用 mock 來模擬外部 API
@patch('src.data.finmind_api.requests.get')
def test_api_integration_with_mock(mock_get):
    mock_get.return_value.json.return_value = mock_data
    # 測試邏輯
```

## 測試數據管理

### 測試數據集
- 提供標準的測試數據集
- 包含各種邊界情況和異常數據
- 定期更新以反映真實數據結構

### 數據隔離
- 每個測試使用獨立的數據環境
- 測試後自動清理生成的數據
- 避免測試間的數據污染

## 性能監控

### 執行時間監控
```python
@pytest.mark.slow
def test_full_dcf_calculation_performance():
    """測試完整 DCF 計算的性能"""
    start_time = time.time()
    result = perform_dcf_calculation(large_dataset)
    execution_time = time.time() - start_time
    
    assert execution_time < 30  # 應在30秒內完成
    assert result is not None
```

### 記憶體使用監控
- 監控大數據集處理時的記憶體使用
- 檢查是否有記憶體洩漏
- 驗證緩存機制的效率
