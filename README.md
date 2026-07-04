# AI SEO Publisher

React + FastAPI + LLM + WordPress REST API 的本機 Demo 專案。使用者在前端輸入 SEO 文章需求，後端會建立可追蹤的文章任務，透過 Search API Tool、Producer、Critique 與 Validator 產生 HTML 文章，最後用 WordPress REST API 建立 draft 草稿。

![AI SEO Publisher preview](docs/assets/ai-seo-publisher-preview.png)

## 專案特色

- React SPA 表單：支援 Topic、Keywords、Target Audience、Call to Action。
- FastAPI API：送出任務後回傳 `job_id`，前端以 polling 追蹤狀態。
- LLM Agent Pipeline：Search API Tool -> Producer -> Validator -> Critique -> Revision。
- Critic Pattern：由 Critique agent 檢查 SEO、HTML 結構、關鍵字、CTA 與發布品質。
- WordPress REST API：使用 Application Password 建立 `draft` 文章。
- 錯誤韌性：LLM timeout、LLM invalid output、WordPress unavailable 都會轉成可追蹤的 job error。

## 系統流程

```text
React SPA
  -> FastAPI /api/v1/articles/generate-publish
  -> SQLite 建立 job 並回傳 job_id
  -> FastAPI BackgroundTasks 執行 Article Workflow Service
  -> Search API Tool 取得 bounded research context
  -> Producer 生成 WordPress-ready HTML
  -> Validator 檢查 HTML、關鍵字與安全規則
  -> Critique 反思內容品質
  -> Producer 必要時修稿一次
  -> HTML Sanitizer
  -> WordPress REST API 建立 draft post
  -> React polling /api/v1/articles/jobs/{job_id}
```

## 技術棧

- Frontend：React、Vite、TypeScript、Tailwind CSS、React Hook Form、Zod、React Query
- Backend：FastAPI、Pydantic、SQLite、httpx、tenacity
- LLM：OpenAI-compatible Chat Completions API，可接 Gemini / OpenAI-compatible provider
- WordPress：Docker 本機站台、REST API、Application Password

## 快速啟動

請開三個 PowerShell 終端機，分別啟動 WordPress、後端、前端。

### 1. 啟動 WordPress

```powershell
.\scripts\start-wordpress.ps1
```

WordPress 後台：

```text
http://localhost:8080/wp-admin
username: demo_admin
password: demo_password_12345
```

腳本會自動建立 WordPress Application Password，並寫入 `backend/.env`。`backend/.env` 只保存在本機，已被 `.gitignore` 排除，不會推上 GitHub。

### 2. 設定 LLM API key

複製或編輯 `backend/.env`：

```env
LLM_MODE=openai_compatible
LLM_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=你的_Gemini_API_key
LLM_MODEL=gemini-3.5-flash
```

如果只是測試前後端流程，也可以使用 mock 模式：

```env
LLM_MODE=mock
```

### 3. 啟動後端

```powershell
backend\.venv\Scripts\uvicorn.exe app.main:app --app-dir backend --reload --port 8000
```

後端 API：

```text
http://localhost:8000
```

### 4. 啟動前端

```powershell
cd frontend
npm run dev
```

前端網址：

```text
http://127.0.0.1:5173
```

## 首次安裝依賴

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd frontend
npm install
cd ..
```

## 主要網址

- React 前端：`http://127.0.0.1:5173`
- FastAPI 後端：`http://localhost:8000`
- FastAPI health check：`http://localhost:8000/health`
- WordPress 前台：`http://localhost:8080`
- WordPress 後台：`http://localhost:8080/wp-admin`
- WordPress REST API：`http://localhost:8080/wp-json/wp/v2`

## 測試

```powershell
$env:PYTHONPATH="$PWD\backend"
backend\.venv\Scripts\python.exe -m pytest backend\tests
```

目前測試涵蓋：

- API enqueue 與 job polling
- LLM 非 JSON 或缺少結構時不讓系統 crash
- HTML sanitizer 移除不安全標籤
- WordPress 驗證錯誤與連線失敗的錯誤格式
- Search API Tool mock mode 與缺少 API key 的錯誤處理
- Producer / Critique pipeline 的反思修稿路徑

## Demo 流程

1. 啟動 WordPress，確認 Application Password 可用。
2. 啟動 FastAPI。
3. 啟動 React。
4. 前端填入 Topic、Keywords、Target Audience、Call to Action，或使用隨機範例。
5. 點擊「開始生成草稿」。
6. 展示 job polling 狀態：`GENERATING`、`VALIDATING`、`REPAIRING`、`PUBLISHING`、`COMPLETED`。
7. 前端顯示 Toast 與 WordPress draft 結果。
8. 到 WordPress 後台確認文章以 draft 狀態建立。

## Search API Tool

Article generation can use a controlled Search API Tool before the Producer / Critique loop. The LLM does not browse directly; the backend normalizes search results and passes bounded research context into prompts.

Configure `backend/.env`:

```env
RESEARCH_MODE=duckduckgo
RESEARCH_ROUTER_MODE=auto
DUCKDUCKGO_SEARCH_URL=https://html.duckduckgo.com/html/
SEARCH_RESULT_COUNT=5
SEARCH_TIMEOUT_SECONDS=10
```

- `mock`：default demo mode, no network call.
- `disabled`：skip research.
- `duckduckgo`：crawl DuckDuckGo HTML search results without an API key.

Router modes:

- `auto`：根據文章 brief 的規則判斷是否需要 search tool。
- `always`：每次都調用 search tool，適合 Demo。
- `never`：永遠不調用 search tool，適合離線測試。

## 安全注意

不要提交以下檔案：

- `backend/.env`
- `frontend/.env`
- `backend/demo.db`
- `frontend/node_modules/`
- `frontend/dist/`
- `outputs/`
- 本機題目 PDF 或其他私有資料

本 repo 只應提交範例設定檔，例如 `backend/.env.example` 與 `frontend/.env.example`。
