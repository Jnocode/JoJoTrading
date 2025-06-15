# 測試報告目錄

這個目錄包含系統生成的各種測試和分析報告。

## 目錄結構

```
reports/
├── coverage/           # 測試覆蓋率報告
│   ├── index.html     # HTML 覆蓋率報告
│   └── coverage.xml   # XML 格式覆蓋率報告
├── test_report.html   # 詳細測試執行報告
├── lint_report.txt    # 代碼檢查報告
└── performance/       # 性能測試報告
    ├── benchmark.html
    └── memory_usage.txt
```

## 報告說明

### 測試覆蓋率報告
- **檔案**: `coverage/index.html`
- **說明**: 顯示測試對代碼的覆蓋程度
- **目標**: 整體覆蓋率 ≥ 80%，核心業務邏輯 ≥ 95%

### 測試執行報告
- **檔案**: `test_report.html`
- **說明**: 詳細的測試執行結果，包括通過/失敗統計
- **更新**: 每次運行測試時自動更新

### 代碼品質報告
- **檔案**: `lint_report.txt`
- **說明**: 代碼風格和品質檢查結果
- **工具**: flake8, black, mypy

### 性能測試報告
- **目錄**: `performance/`
- **說明**: 性能基準測試和記憶體使用分析
- **頻率**: 每週生成一次

## 使用方式

### 生成所有報告
```bash
python run_tests.py --coverage
```

### 查看覆蓋率報告
```bash
# Windows
start reports/coverage/index.html

# macOS
open reports/coverage/index.html

# Linux
xdg-open reports/coverage/index.html
```

### 生成自定義報告
```bash
# 只運行快速測試並生成報告
pytest tests/unit/ --html=reports/unit_test_report.html

# 生成 XML 格式的報告（用於 CI/CD）
pytest tests/ --junit-xml=reports/junit.xml
```

## CI/CD 整合

這些報告可以整合到 CI/CD 流程中：

```yaml
# GitHub Actions 示例
- name: 生成測試報告
  run: python run_tests.py --coverage

- name: 上傳覆蓋率報告
  uses: codecov/codecov-action@v3
  with:
    file: reports/coverage.xml

- name: 發布測試報告
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: reports/
```

## 注意事項

- 此目錄下的文件都是自動生成的，不應手動編輯
- 報告文件可能會很大，不建議提交到 Git 倉庫
- 定期清理舊的報告文件以節省磁碟空間

## 報告歷史

可以保留歷史報告用於趨勢分析：

```bash
# 創建帶時間戳的報告
python run_tests.py --coverage
cp reports/coverage.xml reports/coverage_$(date +%Y%m%d_%H%M%S).xml
```
