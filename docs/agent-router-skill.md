# Agent Router Skill

## Purpose

Agent Router 負責在 Producer 與 Critique 執行前，判斷這次文章任務是否需要調用外部 Search Tool。

目前版本採用 rule-based routing，不額外呼叫 LLM。它只做一件事：根據文章 brief、關鍵字與設定，決定是否把任務交給 `ArticleResearchTool`。

## Inputs

- `topic`
- `keywords`
- `target_audience`
- `call_to_action`
- `RESEARCH_ROUTER_MODE`
- `RESEARCH_MODE`

## Output

```text
use_research_tool: true | false
reason: router decision explanation
matched_rules: rule ids that caused the decision
```

執行後端任務時，這個 decision 會被轉成 job metadata，並由狀態 API 回傳給前端：

```json
{
  "tool_status": {
    "research_tool_called": true,
    "router_reason": "The brief benefits from outside context before Producer and Critique run.",
    "router_rules": ["content:research_sensitive", "keywords:multi_keyword_seo"],
    "provider": "duckduckgo",
    "query": "WordPress AI writing REST API ...",
    "result_count": 5,
    "error": null
  }
}
```

前端不需要另外打一支 API；既有的 job polling 會從 `GET /api/v1/articles/jobs/{job_id}` 取得目前狀態與工具狀態。

## Router Modes

```env
RESEARCH_ROUTER_MODE=auto
```

依照規則判斷是否需要 search，適合產品化預設值。

```env
RESEARCH_ROUTER_MODE=always
```

只要有 research tool 就一定調用，適合 Demo 或測試 Search Tool 流程。

```env
RESEARCH_ROUTER_MODE=never
```

永遠不調用 search，適合離線測試或避免外部請求的環境。

## Auto Rules

Router 會在 brief 看起來需要外部資料時調用 Search Tool：

- Timely or comparative intent: 包含最新、趨勢、比較、價格、法規、年份如 `2025` 或 `2026`。
- Research-sensitive topics: 包含 `SEO`、`Google`、`WordPress`、`REST API`、`AI`、`SaaS`、`ESG` 等。
- Multi-keyword SEO intent: 關鍵字數量達 3 個以上。

Router 會在 brief 看起來偏內部資料或品牌專屬內容時跳過 Search Tool。

## Flow

```text
Frontend
  -> POST /articles/generate-publish
  -> poll GET /articles/jobs/{job_id}
       <- status + tool_status

ArticleWorkflowService
  -> ArticleAgentPipeline
      -> Agent Router
          -> use tool: call ArticleResearchTool
          -> skip tool: return router-skip research context
      -> persist tool_status metadata
      -> Producer
      -> Validator
      -> Critique
      -> Revision when needed
  -> Sanitizer
  -> WordPress draft
```

## Safety

- `tool_status` 不包含 API key、HTTP headers 或完整搜尋原始回應。
- Router 只使用使用者提交的文章 brief。
- Search provider 失敗時，任務不會直接中斷；前端會看到 provider 與 error。
- 如果 Router 跳過 search，Producer 仍會收到 `router-skip` research context，讓 LLM 知道本次未使用外部資料。

## Current Implementation

- Router: `backend/app/services/article_agent_router.py`
- Pipeline integration: `backend/app/services/article_agent_pipeline.py`
- Workflow metadata persistence: `backend/app/services/article_workflow.py`
- Job storage: `backend/app/repositories/article_job_repository.py`
- Tool implementation: `backend/app/services/article_research_tool.py`
- API schema: `backend/app/schemas/article.py`
- Frontend status card: `frontend/src/components/ResultCard.tsx`
- Frontend types: `frontend/src/types/article.ts`
