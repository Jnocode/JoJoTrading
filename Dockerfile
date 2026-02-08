# 🐳 JoJo Trading - 生產級 Docker 映像
# 基於官方 Python 3.11 slim 映像，優化體積與安全性
FROM python:3.11-slim

# 設置維護者資訊
LABEL maintainer="JoJo Trading Team"
LABEL version="3.0.0"
LABEL description="Professional Investment Analysis Platform"

# 設置環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt pyproject.toml ./

# 升級 pip 並安裝 Python 依賴
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 創建非 root 用戶以提高安全性
RUN useradd --create-home --shell /bin/bash jojo && \
    chown -R jojo:jojo /app
USER jojo

# 複製應用程式代碼
COPY --chown=jojo:jojo . .

# 暴露 Streamlit 默認端口
EXPOSE 8501

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 啟動命令
CMD ["streamlit", "run", "main_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
