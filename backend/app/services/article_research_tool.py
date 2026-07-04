from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import Settings
from app.schemas.article import GenerateArticleRequest
from app.schemas.research import ArticleResearchContext, SearchResult


class ArticleResearchTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def research(self, request: GenerateArticleRequest) -> ArticleResearchContext:
        query = self.build_query(request)

        if self.settings.research_mode == "disabled":
            return ArticleResearchContext(query=query, provider="disabled")

        if self.settings.research_mode == "mock":
            return self._mock_context(request, query)

        if self.settings.research_mode == "brave":
            return await self._brave_search(query)

        if self.settings.research_mode == "duckduckgo":
            return await self._duckduckgo_search(query)

        return ArticleResearchContext(
            query=query,
            provider=self.settings.research_mode,
            error="Unsupported research mode.",
        )

    def build_query(self, request: GenerateArticleRequest) -> str:
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

    async def _duckduckgo_search(self, query: str) -> ArticleResearchContext:
        headers = {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "Mozilla/5.0 (compatible; AISEOPublisherResearchBot/1.0; "
                "+https://github.com/eriquechen23-cyl/ai-seo-publisher)"
            ),
        }
        params = {"q": query}

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.search_timeout_seconds,
                follow_redirects=True,
            ) as client:
                response = await client.get(
                    self.settings.duckduckgo_search_url,
                    headers=headers,
                    params=params,
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return ArticleResearchContext(
                query=query,
                provider="duckduckgo",
                error=f"DuckDuckGo search failed: {exc.__class__.__name__}",
            )

        return ArticleResearchContext(
            query=query,
            provider="duckduckgo",
            results=self._parse_duckduckgo_results(response.text),
        )

    def _parse_duckduckgo_results(self, html: str) -> list[SearchResult]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[SearchResult] = []
        max_results = max(1, min(self.settings.search_result_count, 10))

        for result_node in soup.select(".result"):
            title_anchor = result_node.select_one(".result__a")
            if title_anchor is None:
                continue

            title = title_anchor.get_text(" ", strip=True)
            raw_url = title_anchor.get("href", "")
            url = self._normalize_duckduckgo_url(raw_url)
            snippet_node = result_node.select_one(".result__snippet")
            snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

            if not title or not url:
                continue

            results.append(SearchResult(title=title, url=url, snippet=snippet))
            if len(results) >= max_results:
                break

        return results

    @staticmethod
    def _normalize_duckduckgo_url(raw_url: str) -> str:
        if not raw_url:
            return ""

        if raw_url.startswith("//"):
            raw_url = f"https:{raw_url}"

        parsed = urlparse(raw_url)
        query = parse_qs(parsed.query)
        uddg = query.get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)

        return raw_url

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
