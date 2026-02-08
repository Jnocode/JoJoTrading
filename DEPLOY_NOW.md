# 🚀 Render.com 一鍵部署指令

## 📋 部署前檢查清單

- [ ] GitHub Repository 已建立：`https://github.com/xiujiang1987/jojo-trading`
- [ ] Repository 設為 Public
- [ ] 最新程式碼已推送
- [ ] Dockerfile 已準備
- [ ] requirements.txt 已準備

---

## 🔑 環境變數設定（Render.com）

進入 Render Dashboard → Environment 頁籤，新增以下環境變數：

```bash
# Streamlit 核心設定
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Demo 模式（讓 HR 可以試用但不連接真實 API）
DEMO_MODE=true

# 應用設定
PYTHONUNBUFFERED=1
```

**選用（如果需要實際 API）**：
```bash
SHIOAJI_API_KEY=your_api_key_here
SHIOAJI_SECRET=your_secret_here
```

---

## 🌐 Render.com 部署步驟

### 方法 1：Web UI（推薦，簡單）

1. **前往 Render.com**
   ```
   https://dashboard.render.com
   ```

2. **登入帳號**
   - 使用 GitHub 帳號登入（最快）

3. **創建 Web Service**
   - 點擊「New +」→「Web Service」
   - 選擇「Connect a repository」
   - 選擇 `jojo-trading` Repository

4. **基本設定**
   ```
   Name: jojo-trading
   Region: Singapore (最接近台灣)
   Branch: main
   Runtime: Docker
   Instance Type: Free
   ```

5. **Build 設定**
   ```
   Dockerfile Path: ./Dockerfile
   Docker Context: .
   Auto-Deploy: Yes
   ```

6. **新增環境變數**
   - 點擊「Environment」頁籤
   - 複製上方「環境變數設定」區塊的內容
   - 逐一新增

7. **點擊「Create Web Service」**
   - 等待 Build（約 5-10 分鐘）
   - 等待 Deploy

8. **取得 URL**
   ```
   https://jojo-trading.onrender.com
   ```

9. **測試部署**
   - 開啟 URL
   - 使用 Demo 帳號登入：`demo` / `demo123`
   - 測試所有功能

---

### 方法 2：Render CLI（進階）

#### 安裝 Render CLI
```bash
npm install -g @render-apps/cli
```

#### 登入
```bash
render login
```

#### 創建服務
```bash
render create web \
  --name jojo-trading \
  --repo https://github.com/xiujiang1987/jojo-trading \
  --branch main \
  --region singapore \
  --plan free \
  --runtime docker
```

#### 設定環境變數
```bash
render env set STREAMLIT_SERVER_PORT=8501
render env set STREAMLIT_SERVER_ADDRESS=0.0.0.0
render env set STREAMLIT_SERVER_HEADLESS=true
render env set DEMO_MODE=true
```

#### 觸發部署
```bash
render deploy
```

---

### 方法 3：Render API（完全自動化）

#### 取得 API Token
1. 前往：https://dashboard.render.com/u/settings/api-keys
2. 點擊「Create API Key」
3. 複製 Token

#### 使用 API 部署
```bash
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web_service",
    "name": "jojo-trading",
    "repo": "https://github.com/xiujiang1987/jojo-trading",
    "branch": "main",
    "region": "singapore",
    "plan": "free",
    "autoDeploy": "yes",
    "dockerfilePath": "./Dockerfile",
    "envVars": [
      {"key": "STREAMLIT_SERVER_PORT", "value": "8501"},
      {"key": "STREAMLIT_SERVER_ADDRESS", "value": "0.0.0.0"},
      {"key": "STREAMLIT_SERVER_HEADLESS", "value": "true"},
      {"key": "DEMO_MODE", "value": "true"}
    ]
  }'
```

---

## ✅ 部署後檢查

### 1. 健康檢查
```bash
curl https://jojo-trading.onrender.com/_stcore/health
```

**預期回應**：HTTP 200 OK

### 2. 功能測試
- [ ] 網站可以開啟
- [ ] 登入功能正常（demo / demo123）
- [ ] DCF 估值功能正常
- [ ] Monte Carlo 模擬正常
- [ ] 回測引擎正常
- [ ] 圖表顯示正常

### 3. 效能監控
前往 Render Dashboard → Metrics 查看：
- CPU 使用率 < 80%
- 記憶體使用率 < 512MB
- 回應時間 < 3s

---

## 🐛 常見問題排查

### 問題 1：Build 失敗
```
ERROR: Could not find a version that satisfies the requirement xxx
```

**解決方法**：
1. 檢查 `requirements/base.txt` 版本號
2. 移除重複的依賴（例如 plotly、yfinance 出現兩次）
3. 本機測試：`pip install -r requirements.txt`

### 問題 2：應用無法啟動
```
ModuleNotFoundError: No module named 'streamlit'
```

**解決方法**：
1. 確認 Dockerfile 的 `COPY requirements.txt` 路徑正確
2. 檢查 `RUN pip install -r requirements.txt` 是否執行成功

### 問題 3：Port 錯誤
```
OSError: [Errno 98] Address already in use
```

**解決方法**：
1. 確認 Dockerfile 的 `CMD` 使用 `--server.port=8501`
2. 確認環境變數 `STREAMLIT_SERVER_PORT=8501`

### 問題 4：Streamlit 入口檔案錯誤
**錯誤訊息**：
```
FileNotFoundError: [Errno 2] No such file or directory: 'app.py'
```

**解決方法**：
Dockerfile 中的 `CMD` 應該是：
```dockerfile
CMD ["streamlit", "run", "main_app.py", ...]
```

**立即修正**（如果需要）：
```bash
# 編輯 Dockerfile，將 app.py 改為 main_app.py
sed -i 's/app.py/main_app.py/g' Dockerfile
git add Dockerfile
git commit -m "修正 Streamlit 入口檔案名稱"
git push
```

---

## 📝 部署完成後的待辦事項

- [ ] 取得實際 URL（例如：https://jojo-trading-xxxx.onrender.com）
- [ ] 建立 Demo 帳號（demo / demo123）
- [ ] 測試所有功能
- [ ] 更新履歷中的 URL
- [ ] 更新 4 封 Cover Letter
- [ ] 更新 GitHub README.md

---

## 🎯 預期結果

**部署成功後，你會得到**：
```
✅ 線上 Demo URL: https://jojo-trading.onrender.com
✅ Demo 帳號: demo / demo123
✅ 所有功能可正常運作
✅ HR 可以直接試用系統
```

**這是最強的成果證明！比影片和 GitHub 更有說服力！** 💪

---

## 📌 重要提醒

### 免費方案限制
- **休眠機制**：15 分鐘無活動後休眠
- **喚醒時間**：30-60 秒
- **記憶體限制**：512 MB
- **CPU 限制**：0.1 vCPU

### 避免休眠的方法
使用 **UptimeRobot** 每 5 分鐘 Ping 一次：
1. 前往：https://uptimerobot.com
2. 新增監控：`https://jojo-trading.onrender.com/_stcore/health`
3. 間隔：5 分鐘

### 升級方案（選用）
如果免費方案不穩定，可以升級到：
- **Starter**: $7/月
- 無休眠
- 更多記憶體（512 MB → 2 GB）

---

**現在就開始部署！祝成功！** 🚀
