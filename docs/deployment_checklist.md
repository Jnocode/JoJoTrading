# 🚀 Render.com 部署檢查清單

> **目標**: 將 JoJo Trading Platform 部署到 Render.com 免費方案  
> **預計時間**: 1-2 小時  
> **難度**: ⭐⭐⭐ (中等)

---

## 📋 部署前準備

### ✅ 1. 確認專案已 Push 到 GitHub

```bash
# 確認 Git 狀態
git status

# 提交所有變更
git add .
git commit -m "準備部署到 Render.com"

# 推送到 GitHub
git push origin main
```

**檢查項目**：
- [ ] GitHub Repository 是 Public（或 Render 可以存取）
- [ ] 最新的程式碼已推送
- [ ] README.md 已更新
- [ ] .gitignore 正確設定（不包含敏感資料）

---

### ✅ 2. 清理敏感資料

**必須移除的檔案**：
- [ ] API Keys（Shioaji、Yahoo Finance）
- [ ] 密碼、Token
- [ ] 本機路徑（例如：`D:\Workspace\...`）
- [ ] 個人資訊

**方法**：使用環境變數
```python
# ❌ 錯誤寫法
API_KEY = "your_secret_key_here"

# ✅ 正確寫法
import os
API_KEY = os.getenv("SHIOAJI_API_KEY")
```

**檢查清單**：
- [ ] 檢查 `src/` 目錄下所有 `.py` 檔案
- [ ] 檢查 `config/settings.py`
- [ ] 確認 `.env` 檔案已加入 `.gitignore`

---

## 📦 必要檔案檢查

### ✅ 3. Dockerfile（必須）

**檔案路徑**: `Dockerfile`

```dockerfile
# 使用官方 Python 映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製依賴清單
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 暴露 Streamlit 預設 Port
EXPOSE 8501

# 設定健康檢查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 啟動應用
CMD ["streamlit", "run", "main_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**檢查項目**：
- [ ] `FROM python:3.11-slim` 版本正確
- [ ] `requirements.txt` 路徑正確
- [ ] `main_app.py` 入口檔案存在
- [ ] Port 設定為 `8501`（Streamlit 預設）

---

### ✅ 4. requirements.txt（必須）

**檔案路徑**: `requirements.txt`

**必要依賴**：
```txt
streamlit==1.45.1
pandas==2.2.0
numpy==1.26.3
matplotlib==3.8.2
plotly==5.18.0
aiohttp==3.9.1
yfinance==0.2.35
requests==2.31.0
```

**檢查項目**：
- [ ] 版本號已鎖定（避免相容性問題）
- [ ] 移除本機開發依賴（pytest、black 等）
- [ ] 檔案大小合理（< 50 KB）

**生成方法**：
```bash
# 從虛擬環境生成
pip freeze > requirements.txt

# 手動編輯，只保留生產環境依賴
```

---

### ✅ 5. .dockerignore（建議）

**檔案路徑**: `.dockerignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp

# Git
.git/
.gitignore

# 測試
tests/
.pytest_cache/
.coverage

# 文件
docs/
*.md
!README.md

# 數據
data/
*.db
*.sqlite

# 日誌
*.log
logs/

# 環境變數
.env
.env.local
```

**檢查項目**：
- [ ] 排除不必要的檔案（減少映像大小）
- [ ] 保留 README.md（文件重要）

---

## 🌐 Render.com 設定

### ✅ 6. 註冊 Render.com 帳號

1. **前往**: [https://render.com](https://render.com)
2. **註冊方式**:
   - GitHub 帳號登入（推薦）
   - Google 帳號登入
   - Email 註冊

**檢查項目**：
- [ ] 帳號註冊完成
- [ ] Email 驗證完成
- [ ] 連結 GitHub 帳號

---

### ✅ 7. 建立 Web Service

#### Step 1: 選擇 Repository
1. 點擊「New +」→「Web Service」
2. 選擇「Connect a repository」
3. 授權 Render 存取 GitHub
4. 選擇 `jojo-trading` Repository

#### Step 2: 基本設定
| 欄位 | 設定值 |
|-----|-------|
| **Name** | `jojo-trading` (或自訂) |
| **Region** | Singapore (離台灣最近) |
| **Branch** | `main` |
| **Runtime** | Docker |
| **Instance Type** | Free (免費方案) |

#### Step 3: Build 設定
| 欄位 | 設定值 |
|-----|-------|
| **Dockerfile Path** | `./Dockerfile` |
| **Docker Context** | `.` (根目錄) |
| **Auto-Deploy** | Yes (自動部署) |

**檢查項目**：
- [ ] Repository 連結正確
- [ ] Runtime 選擇「Docker」
- [ ] Instance Type 選擇「Free」

---

### ✅ 8. 環境變數設定

**必要環境變數**：

| 變數名稱 | 說明 | 範例值 |
|---------|------|--------|
| `STREAMLIT_SERVER_PORT` | Streamlit Port | `8501` |
| `STREAMLIT_SERVER_ADDRESS` | 監聽地址 | `0.0.0.0` |
| `STREAMLIT_SERVER_HEADLESS` | Headless 模式 | `true` |
| `DEMO_MODE` | Demo 模式 | `true` |

**選用環境變數**（如果需要實際 API）：

| 變數名稱 | 說明 |
|---------|------|
| `SHIOAJI_API_KEY` | 永豐金 API Key |
| `SHIOAJI_SECRET` | 永豐金 Secret |
| `YAHOO_FINANCE_API_KEY` | Yahoo Finance Key |

**設定方式**：
1. 進入「Environment」頁籤
2. 點擊「Add Environment Variable」
3. 填入變數名稱與值
4. 點擊「Save Changes」

**檢查項目**：
- [ ] `STREAMLIT_SERVER_PORT=8501`
- [ ] `STREAMLIT_SERVER_ADDRESS=0.0.0.0`
- [ ] `STREAMLIT_SERVER_HEADLESS=true`
- [ ] 敏感資料未暴露在程式碼中

---

### ✅ 9. Demo 模式設定

**目的**：讓 HR 可以試用，但不連接真實交易 API

**實作方式**：

#### 方法 1：使用環境變數
```python
# src/jojo_trading/config/settings.py
import os

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

if DEMO_MODE:
    # 使用假資料
    def fetch_data(stock_id):
        return load_mock_data(stock_id)
else:
    # 使用真實 API
    def fetch_data(stock_id):
        return api.get_data(stock_id)
```

#### 方法 2：建立 Demo 帳號
```python
# src/jojo_trading/auth.py
DEMO_ACCOUNTS = {
    "demo": {
        "password": "demo123",
        "permissions": ["view", "analyze"],  # 不包含 "trade"
    }
}
```

**檢查項目**：
- [ ] Demo 模式已實作
- [ ] Demo 帳號已建立（demo / demo123）
- [ ] 敏感功能已停用（實際下單）

---

## 🚀 部署流程

### ✅ 10. 開始部署

1. **點擊「Create Web Service」**
2. **等待 Build**（約 5-10 分鐘）
   - 顯示 Build Logs
   - 檢查是否有錯誤

3. **Build 成功後自動部署**
   - 顯示 Deploy Logs
   - 檢查啟動是否成功

**Build Logs 檢查**：
```
✓ Building Docker image
✓ Installing dependencies
✓ Copying application files
✓ Image built successfully
```

**Deploy Logs 檢查**：
```
✓ Starting service
✓ Streamlit is running on port 8501
✓ Health check passed
```

**檢查項目**：
- [ ] Build 成功（綠色勾勾）
- [ ] Deploy 成功
- [ ] Health Check 通過

---

### ✅ 11. 測試部署

**取得 URL**：
```
https://jojo-trading.onrender.com
```

**測試項目**：
- [ ] 網站可以開啟
- [ ] 登入功能正常（demo / demo123）
- [ ] DCF 估值功能正常
- [ ] Monte Carlo 模擬正常
- [ ] 回測引擎正常
- [ ] 圖表顯示正常
- [ ] 沒有錯誤訊息

**常見問題排查**：

| 問題 | 可能原因 | 解決方法 |
|-----|---------|---------|
| 網站無法開啟 | Port 設定錯誤 | 檢查 Dockerfile 的 Port 設定 |
| 502 Bad Gateway | 應用未啟動 | 檢查 Deploy Logs |
| 功能異常 | 環境變數缺失 | 檢查 Environment 設定 |
| 圖表不顯示 | 依賴缺失 | 檢查 requirements.txt |

---

## 📝 部署後優化

### ✅ 12. 設定自訂網域（選用）

**如果有網域**：
1. 進入「Settings」→「Custom Domain」
2. 新增 CNAME 記錄：
   ```
   CNAME trading.your-domain.com → jojo-trading.onrender.com
   ```
3. 等待 DNS 生效（約 10-30 分鐘）

**檢查項目**：
- [ ] CNAME 記錄設定正確
- [ ] SSL 憑證自動生成

---

### ✅ 13. 效能監控

**Render 提供的監控**：
- CPU 使用率
- 記憶體使用率
- 請求數量
- 錯誤率

**檢查項目**：
- [ ] CPU 使用率 < 80%
- [ ] 記憶體使用率 < 512MB（免費方案限制）
- [ ] 錯誤率 < 1%

**如果超過限制**：
- 升級到 Starter 方案（$7/月）
- 優化程式碼（減少記憶體使用）

---

### ✅ 14. 自動部署設定

**預設已開啟**：每次 Push 到 GitHub 會自動觸發部署

**停用方式**（如果需要）：
1. 進入「Settings」→「Build & Deploy」
2. 取消勾選「Auto-Deploy」

**檢查項目**：
- [ ] Auto-Deploy 已開啟
- [ ] 每次 Push 都會觸發部署
- [ ] Build 時間 < 10 分鐘

---

## 📤 更新履歷連結

### ✅ 15. 更新所有文件

**需要更新的檔案**：

#### 1. README.md
```markdown
🌐 **線上 Demo**: [jojo-trading.onrender.com](https://jojo-trading.onrender.com)
```

#### 2. 履歷 (`姜鈞_Python後端工程師_2026.md`)
```markdown
- 🌐 **線上 Demo**: [jojo-trading.onrender.com](https://jojo-trading.onrender.com)（Demo 帳號可試用）
```

#### 3. Cover Letter（4 封）
```markdown
🌐 **線上 Demo**: [jojo-trading.onrender.com](https://jojo-trading.onrender.com)
```

**檢查項目**：
- [ ] README.md 已更新
- [ ] 履歷已更新
- [ ] 4 封 Cover Letter 已更新
- [ ] 連結可以正常開啟

---

## 🐛 常見問題排查

### 問題 1：Build 失敗

**錯誤訊息**：
```
ERROR: Could not find a version that satisfies the requirement xxx
```

**解決方法**：
1. 檢查 `requirements.txt` 版本號
2. 移除不必要的依賴
3. 使用 `pip install -r requirements.txt` 本機測試

---

### 問題 2：應用啟動失敗

**錯誤訊息**：
```
ModuleNotFoundError: No module named 'xxx'
```

**解決方法**：
1. 確認依賴已加入 `requirements.txt`
2. 檢查 Dockerfile 的 COPY 指令
3. 檢查 Python 版本是否匹配

---

### 問題 3：Port 綁定錯誤

**錯誤訊息**：
```
OSError: [Errno 98] Address already in use
```

**解決方法**：
1. 確認 Dockerfile 的 `--server.port=8501`
2. 確認環境變數 `STREAMLIT_SERVER_PORT=8501`
3. 重新部署

---

### 問題 4：資料庫連接失敗

**錯誤訊息**：
```
OperationalError: unable to open database file
```

**解決方法**：
1. 確認 SQLite 檔案路徑
2. 使用相對路徑（不要用絕對路徑）
3. 檢查寫入權限

**建議**：
```python
# ❌ 錯誤
DB_PATH = "D:/Workspace/data/stocks.db"

# ✅ 正確
import os
DB_PATH = os.path.join(os.getcwd(), "data", "stocks.db")
```

---

## ✅ 最終檢查清單

### 部署前
- [ ] GitHub Repository 已建立（Public）
- [ ] 敏感資料已移除
- [ ] Dockerfile 已準備
- [ ] requirements.txt 已準備
- [ ] .dockerignore 已準備
- [ ] Demo 模式已實作

### 部署中
- [ ] Render.com 帳號已註冊
- [ ] Web Service 已建立
- [ ] 環境變數已設定
- [ ] Auto-Deploy 已開啟

### 部署後
- [ ] Build 成功
- [ ] Deploy 成功
- [ ] Health Check 通過
- [ ] 網站可以開啟
- [ ] Demo 帳號可以登入
- [ ] 所有功能正常運作
- [ ] 履歷連結已更新
- [ ] Cover Letter 已更新

---

## 📌 備註

### 免費方案限制
- **記憶體**: 512 MB
- **CPU**: 0.1 vCPU
- **休眠**: 15 分鐘無活動後休眠
- **喚醒時間**: 約 30-60 秒

**解決方案**：
1. **定期 Ping**（避免休眠）：
   ```bash
   # 使用 UptimeRobot 每 5 分鐘 Ping 一次
   https://uptimerobot.com
   ```

2. **優化啟動速度**：
   - 減少依賴數量
   - 使用輕量級映像（slim）

---

## 🎯 預計完成時間

- **準備階段**: 30 分鐘
- **檔案準備**: 30 分鐘
- **Render 設定**: 15 分鐘
- **部署等待**: 10 分鐘
- **測試與優化**: 15 分鐘

**總計**: 1.5 - 2 小時

---

## 🚀 下一步

部署完成後：
1. ✅ 測試線上 Demo
2. ✅ 更新履歷連結
3. ✅ 準備 Demo 影片
4. ✅ Week 2 開始投遞履歷

**加油！部署上線是最強的成果證明！** 💪

---

> **注意**: 免費方案的休眠問題可能影響 HR 試用體驗，建議在投遞前一天檢查網站狀態，或考慮升級到 Starter 方案（$7/月）。
