import httpx

from app.core.config import Settings
from app.schemas.article import GenerateArticleRequest
from app.schemas.research import ArticleResearchContext, SearchResult


class ArticleResearchTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def research(self, request: GenerateArticleRequest) -> ArticleResearchContext:
        query = self._build_query(request)

        if self.settings.research_mode == "disabled":
            return ArticleResearchContext(query=query, provider="disabled")

        if self.settings.research_mode == "mock":
            return self._mock_context(request, query)

        if self.settings.research_mode == "brave":
            return await self._brave_search(query)

        return ArticleResearchContext(
            query=query,
            provider=self.settings.research_mode,
            error="Unsupported research mode.",
        )

    def _build_query(self, request: GenerateArticleRequest) -> str:
        keywords = " ".join(request.keywords)
        query = f"{request.topic} {keywords} {request.target_audience}".strip()
        return query[:400]

    async def _brave_search(self, query: str) -> ArticleResearchContext:
        if not self.settings.search_api_key:
            return ArticleResearchContext(
                query=query,
                provider="brave",
                error="SEARCH_API_KEY is not configured.",
            )

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.settings.search_api_key,
        }
        params = {
            "q": query,
            "count": max(1, min(self.settings.search_result_count, 10)),
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.search_timeout_seconds) as client:
                response = await client.get(
                    self.settings.search_api_base,
                    headers=headers,
                    params=params,
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return ArticleResearchContext(
                query=query,
                provider="brave",
                error=f"Search request failed: {exc.__class__.__name__}",
            )

        data = response.json()
        raw_results = data.get("web", {}).get("results", [])
        results = [
            SearchResult(
                title=item.get("title", "Untitled result"),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
            )
            for item in raw_results[: self.settings.search_result_count]
            if item.get("url")
        ]
        return ArticleResearchContext(query=query, provider="brave", results=results)

    def _mock_context(
        self,
        request: GenerateArticleRequest,
        query: str,
    ) -> ArticleResearchContext:
        keyword = request.keywords[0]
        return ArticleResearchContext(
            query=query,
            provider="mock",
            results=[
                SearchResult(
                    title=f"{request.topic} market overview",
                    url="https://example.com/research/market-overview",
                    snippet=(
                        f"Mock research context for {request.topic}. It highlights common "
                        f"search intent around {keyword} and practical buyer questions."
                    ),
                ),
                SearchResult(
                    title=f"{request.topic} implementation checklist",
                    url="https://example.com/research/implementation-checklist",
                    snippet=(
                        "Mock source covering comparison criteria, implementation risks, "
                        "and concise next-step guidance for article planning."
                    ),
                ),
            ],
        )
