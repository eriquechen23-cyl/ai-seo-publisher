# AI SEO Publisher 啟動指南

這份文件是本機 Demo 的完整啟動流程。建議照順序做：先 WordPress，再後端，最後前端。

## 一、整體服務

```text
React frontend
  http://127.0.0.1:5173

FastAPI backend
  http://localhost:8000

WordPress
  http://localhost:8080
```

資料流：

```text
React 表單
  -> FastAPI /api/v1/articles/generate-publish
  -> Gemini LLM
  -> 文章驗證與修復
  -> WordPress REST API 建立 draft
```

## 二、第一次安裝相依套件

只需要做一次。

### 1. 後端 Python 套件

在專案根目錄執行：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

如果 `backend/.venv` 已經存在，通常不用重做這一步。

### 2. 前端 Node 套件

在專案根目錄執行：

```powershell
cd frontend
npm install
cd ..
```

如果 `frontend/node_modules` 已經存在，通常不用重做這一步。

## 三、啟動 WordPress

本專案使用 Docker 啟動 WordPress + MariaDB，不需要 Docker Compose。

在專案根目錄執行：

```powershell
.\scripts\start-wordpress.ps1
```

腳本會自動完成：

- 建立 Docker network
- 建立 MariaDB container
- 建立 WordPress container
- 安裝 WordPress core
- 建立 WordPress 管理員帳號
- 建立 WordPress Application Password
- 寫入 `backend/.env`

如果 `backend/.env` 已經有 Gemini 設定，腳本會保留 `LLM_API_KEY`、`LLM_MODEL` 和 `LLM_API_BASE`，只更新 WordPress 連線資訊。

預設 WordPress 資訊：

```text
Site:  http://localhost:8080
Admin: http://localhost:8080/wp-admin
User:  demo_admin
Pass:  demo_password_12345
```

確認 REST API：

```powershell
Invoke-RestMethod http://localhost:8080/wp-json/wp/v2
```

## 四、設定 Gemini API Key

WordPress 腳本會建立 `backend/.env`。請打開 `backend/.env`，填入你的 Gemini API key：

```env
LLM_MODE=openai_compatible
LLM_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=你的_Gemini_API_key
LLM_MODEL=gemini-3.5-flash
```

不要把 Gemini API key 放到 `frontend/.env`，前端環境變數會進入瀏覽器 bundle。

## 五、啟動後端 FastAPI

另開一個 PowerShell 終端機，在專案根目錄執行：

```powershell
backend\.venv\Scripts\uvicorn.exe app.main:app --app-dir backend --reload --port 8000
```

看到類似訊息代表成功：

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

確認後端健康狀態：

```powershell
Invoke-RestMethod http://localhost:8000/health
```

預期回應：

```json
{
  "status": "ok"
}
```

## 六、啟動前端 React

再開一個 PowerShell 終端機，執行：

```powershell
cd frontend
npm run dev
```

看到類似訊息代表成功：

```text
VITE ready
Local: http://127.0.0.1:5173/
```

打開：

```text
http://127.0.0.1:5173
```

## 七、Demo 操作順序

1. 確認 WordPress 開著：`http://localhost:8080/wp-admin`
2. 確認後端開著：`http://localhost:8000/health`
3. 打開前端：`http://127.0.0.1:5173`
4. 填入表單：
   - Topic
   - Keywords
   - Target Audience
   - Call to Action
5. 點擊「生成並發布」
6. 前端顯示 loading
7. 成功後顯示 WordPress draft 結果
8. 到 WordPress 後台確認文章是 draft

## 八、測試命令

後端測試：

```powershell
$env:PYTHONPATH="$PWD\backend"
backend\.venv\Scripts\python.exe -m pytest backend\tests
```

前端 build：

```powershell
cd frontend
npm run build
```

## 九、停止服務

停止前端或後端：

```text
在對應終端機按 Ctrl + C
```

停止 WordPress Docker containers：

```powershell
docker --config .docker stop ai-seo-wordpress ai-seo-wordpress-db
```

再次啟動 WordPress：

```powershell
docker --config .docker start ai-seo-wordpress-db ai-seo-wordpress
```

或直接重跑：

```powershell
.\scripts\start-wordpress.ps1
```

## 十、常見錯誤

### WordPress 站台暫時無法連線

原因通常是 WordPress 沒啟動，或 `backend/.env` 的 `WORDPRESS_URL` 不正確。

檢查：

```powershell
Invoke-RestMethod http://localhost:8080/wp-json/wp/v2
```

修復：

```powershell
.\scripts\start-wordpress.ps1
```

### WordPress 驗證失敗

原因通常是 Application Password 不正確。重跑 WordPress 腳本會重新建立 Application Password 並寫入 `backend/.env`：

```powershell
.\scripts\start-wordpress.ps1
```

然後重啟 FastAPI。

### LLM 回傳錯誤或 LLM_API_KEY 未設定

確認 `backend/.env`：

```env
LLM_MODE=openai_compatible
LLM_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=你的_Gemini_API_key
LLM_MODEL=gemini-3.5-flash
```

修改後要重啟 FastAPI。

### 前端送出後打不到後端

確認後端有啟動：

```powershell
Invoke-RestMethod http://localhost:8000/health
```

確認 `frontend/.env.example` 的 API base：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

如果有建立 `frontend/.env`，也要確認內容一致。
