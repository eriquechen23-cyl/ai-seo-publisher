# Agent Router Skill

## Purpose

The Agent Router decides whether an article request should call an external tool before the Producer and Critique agents run.

The first version is intentionally rule-based. It does not call an LLM and does not browse by itself. It only decides whether the pipeline should call the configured research tool.

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
reason: human-readable explanation
matched_rules: rule ids that caused the decision
```

## Router Modes

```env
RESEARCH_ROUTER_MODE=auto
```

Use simple rules to decide whether search is useful.

```env
RESEARCH_ROUTER_MODE=always
```

Always call the research tool when it exists. Useful for demos where the presenter wants to show tool usage every time.

```env
RESEARCH_ROUTER_MODE=never
```

Never call the research tool. Useful for offline tests or when external calls should be avoided.

## Auto Rules

The router calls the research tool when the brief appears to need outside context:

- Timely or comparative intent: `最新`, `近期`, `趨勢`, `新聞`, `市場`, `價格`, `成本`, `比較`, `排名`, `法規`, `政策`, year terms such as `2025` or `2026`.
- Research-sensitive topics: `SEO`, `搜尋`, `Google`, `WordPress`, `REST API`, `AI`, `生成式 AI`, `資安`, `ESG`, `金融`, `醫療`, `製造`, `SaaS`.
- Multi-keyword SEO intent: 3 or more keywords.

The router skips the research tool when the brief looks internal or brand-specific:

- `內部`
- `公司內訓`
- `品牌語氣`
- `個人心得`
- `團隊公告`
- `會議紀錄`

## Flow

```text
ArticleWorkflowService
  -> ArticleAgentPipeline
      -> Agent Router
          -> use tool: call ArticleResearchTool
          -> skip tool: return router-skip research context
      -> Producer
      -> Validator
      -> Critique
      -> Revision when needed
  -> Sanitizer
  -> WordPress draft
```

## Safety

- The router never sends secrets to external services.
- The router only uses the article brief text already submitted by the user.
- If the router skips search, the Producer still receives a research context explaining that no external search was used.
- If a search provider fails, the pipeline continues with a research error instead of crashing.

## Current Implementation

- Router: `backend/app/services/article_agent_router.py`
- Pipeline integration: `backend/app/services/article_agent_pipeline.py`
- Tool implementation: `backend/app/services/article_research_tool.py`
- Configuration: `backend/app/core/config.py`
