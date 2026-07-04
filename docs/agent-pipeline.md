# Article Agent Pipeline

## Purpose

The article workflow now uses a controlled Researcher / Producer / Critique pipeline.
The LLM does not browse the web directly. Instead, the backend calls a Search API Tool,
formats the results into a bounded research context, and passes that context into the
Producer and Critique prompts.

## Flow

```text
ArticleWorkflowService
  -> ArticleAgentPipeline
      -> Research Tool: search topic + keywords
      -> Producer: generate_article with research context
      -> Validator: deterministic HTML, structure, keyword, and safety checks
      -> Critique: review article against request + research context
      -> Producer: revise_article when validation or critique fails
      -> Validator + Critique final gate
  -> Sanitizer
  -> Final validation
  -> WordPress draft
```

## Search API Tool Modes

Configure the tool in `backend/.env`:

```env
RESEARCH_MODE=mock
SEARCH_API_KEY=
SEARCH_API_BASE=https://api.search.brave.com/res/v1/web/search
DUCKDUCKGO_SEARCH_URL=https://html.duckduckgo.com/html/
SEARCH_RESULT_COUNT=5
SEARCH_TIMEOUT_SECONDS=10
```

Modes:

- `mock`: default demo mode. Returns local fake search results and does not call the network.
- `disabled`: skips research and tells the LLM no external context is available.
- `brave`: calls Brave Search API with `SEARCH_API_KEY`.
- `duckduckgo`: fetches DuckDuckGo HTML search results without an API key and parses title, URL, and snippet.

## Main Files

- `backend/app/services/article_research_tool.py`: controlled Search API Tool.
- `backend/app/schemas/research.py`: `SearchResult` and `ArticleResearchContext`.
- `backend/app/services/article_agent_pipeline.py`: Researcher / Producer / Critique orchestration.
- `backend/app/services/llm_service.py`: producer, critique, and revision LLM entrypoints.
- `backend/app/services/prompt_builder.py`: prompts that include bounded research context.
- `backend/app/services/article_workflow.py`: job status, sanitizer, and WordPress draft publishing.

## Safety Rules

- The LLM receives only normalized search results: title, URL, snippet, provider, and query.
- The LLM never receives arbitrary network access or executable browser control.
- Search failures are converted into `ArticleResearchContext.error`; article generation can continue,
  but prompts tell the LLM not to invent source-backed facts.
- Result count and timeout are controlled by backend settings.
- DuckDuckGo mode is treated as a best-effort crawler source. If it fails or the HTML changes, generation continues with a research error instead of crashing.
- The deterministic validator and sanitizer still run after agent reflection.

## Verification

Run:

```powershell
$env:PYTHONPATH="$PWD\backend"; backend\.venv\Scripts\python.exe -m pytest backend\tests
```

Current coverage:

- Search tool mock mode returns bounded context.
- Brave mode safely reports missing `SEARCH_API_KEY` without network access.
- Pipeline passes research context to Producer and Critique.
- Critique can still trigger one reflection / revision cycle.
- Existing API, validator, and WordPress client tests still pass.
