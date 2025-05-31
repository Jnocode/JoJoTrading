# JoJo Trading Makefile
# 提供便利的開發和部署命令

.PHONY: help install install-dev test lint format clean run build docs

# 預設目標
help:
	@echo "JoJo Trading 可用命令:"
	@echo ""
	@echo "  install       安裝基礎依賴"
	@echo "  install-dev   安裝開發依賴"
	@echo "  test          執行所有測試"
	@echo "  test-unit     執行單元測試"
	@echo "  test-int      執行整合測試"
	@echo "  lint          代碼檢查"
	@echo "  format        代碼格式化"
	@echo "  clean         清理臨時檔案"
	@echo "  run           啟動 Web UI"
	@echo "  run-cli       啟動 CLI 模式"
	@echo "  build         建置套件"
	@echo "  docs          生成文檔"
	@echo ""

# 安裝依賴
install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt
	pip install -r requirements/test.txt
	pip install -e .

# 測試
test:
	python -m pytest tests/ -v --cov=src/jojo_trading --cov-report=html --cov-report=term

test-unit:
	python -m pytest tests/unit/ -v

test-int:
	python -m pytest tests/integration/ -v

# 代碼品質
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

# 清理
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

# 執行
run:
	python main.py

run-cli:
	python main.py --cli

# 建置
build:
	python -m build

# 文檔 (需要安裝 sphinx)
docs:
	@echo "文檔生成功能待實現"

# 開發環境設置
setup-dev: install-dev
	pre-commit install
	@echo "開發環境設置完成"
