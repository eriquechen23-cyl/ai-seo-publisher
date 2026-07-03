# AI SEO Publisher Architecture

## 目標

建立一個容易在面試現場展示的全端 Demo：

- React 表單收集 SEO 文章需求。
- FastAPI 接收 JSON、建立背景任務、呼叫 LLM、驗證輸出。
- 驗證失敗時執行一次 reflective repair。
- 清理 HTML 後透過 WordPress REST API 建立 draft。
- SQLite 記錄任務狀態、錯誤與 WordPress post id。

## 非目標

- 不導入 LangGraph、Celery、Redis、Kubernetes 或多個微服務。
- 不讓 FastAPI 直接讀寫 WordPress MySQL。
- 不把 WordPress Application Password 暴露到 React。

## 系統流程

```text
Browser / React
  |
  | POST /api/v1/articles/generate-publish
  v
FastAPI Router
  |
  +--> ArticleJobRepository -> SQLite demo.db
  |       |
  |       v
  |     202 Accepted: job_id + status_url
  |
  +--> FastAPI BackgroundTasks
          |
          v
ArticleWorkflowService
  |
  +--> ArticleJobRepository -> SQLite demo.db
  |
  +--> PromptBuilder
  |
  +--> LLMService
  |
  +--> ArticleValidator / Critic
  |       |
  |       +-- failed once --> Reflective Repair via LLMService
  |
  +--> HTML Sanitizer
  |
  +--> WordPressClient -> /wp-json/wp/v2/posts
  |
  v
SQLite job result / error

Browser / React
  |
  | GET /api/v1/articles/jobs/{job_id}
  v
Job status polling response
```

## 主要模組

### Frontend

- `ArticleForm.tsx`：React Hook Form + Zod 驗證四個必填欄位，送出後輪詢 job 狀態。
- `KeywordInput.tsx`：支援多筆關鍵字輸入。
- `ResultCard.tsx`：顯示 job id、處理進度、錯誤訊息、WordPress post id、draft 狀態與編輯連結。
- `articles.ts`：集中管理 API 呼叫與錯誤解析。

### Backend

- `api/articles.py`：只負責路由、依賴注入、BackgroundTasks enqueue 與 job polling。
- `services/article_workflow.py`：主要流程協調器。
- `services/llm_service.py`：mock 或 OpenAI-compatible chat completions。
- `services/article_validator.py`：rule-based critic，檢查 HTML 結構、關鍵字與危險內容。
- `services/wordpress_client.py`：以 Basic Auth + Application Password 建立 WordPress draft。
- `repositories/article_job_repository.py`：SQLite job 狀態與錯誤追蹤。

## Job 狀態

```text
RECEIVED -> GENERATING -> VALIDATING -> REPAIRING -> PUBLISHING -> COMPLETED
```

失敗狀態：

```text
FAILED_LLM
FAILED_VALIDATION
FAILED_WORDPRESS
```

## 錯誤格式

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "文章生成服務暫時沒有回應，請稍後再試。",
    "retryable": true
  }
}
```

## 非同步處理

`POST /api/v1/articles/generate-publish` 不等待 LLM 與 WordPress 全部完成，而是：

1. 建立 `article_jobs` record。
2. 以 HTTP 202 回傳 `job_id`、初始狀態與 `status_url`。
3. 透過 FastAPI `BackgroundTasks` 執行原本的文章流程。
4. 前端使用 `GET /api/v1/articles/jobs/{job_id}` 每 1.5 秒輪詢一次。
5. 任務進入 `COMPLETED` 或任一 `FAILED_*` 狀態後停止輪詢。

這個做法避免外部 API latency 讓使用者卡在單一 HTTP request，同時保留 Demo 的輕量部署方式。若要進一步產品化，可將 BackgroundTasks 換成 Redis queue + worker，保留同一套 job polling API。

## 關鍵取捨

- SQLite 是本系統的 job log，不是 WordPress 的內容資料庫。
- LLM 輸出採 JSON，再由後端取 `title` 與 `content_html`，避免模型夾帶 Markdown 或解說文字。
- WordPress 建立文章不做無條件 retry，避免 timeout 後重送造成重複文章。
- 目前非同步架構採 FastAPI BackgroundTasks，適合本機 Demo；正式環境可替換為獨立 worker queue。
- 預設 `LLM_MODE=mock`，便於沒有 API key 時先測通前後端；正式 Demo 改為 `openai_compatible`。
