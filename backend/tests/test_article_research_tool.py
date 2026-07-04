import pytest
import httpx

from app.core.config import Settings
from app.schemas.article import GenerateArticleRequest
from app.services.article_research_tool import ArticleResearchTool


def _request() -> GenerateArticleRequest:
    return GenerateArticleRequest(
        topic="AI SEO automation",
        keywords=["SEO automation", "content workflow"],
        target_audience="marketing teams",
        call_to_action="Request a demo.",
    )


@pytest.mark.asyncio
async def test_research_tool_returns_mock_search_context() -> None:
    tool = ArticleResearchTool(Settings(research_mode="mock"))

    context = await tool.research(_request())

    assert context.provider == "mock"
    assert "AI SEO automation" in context.query
    assert len(context.results) == 2
    assert context.results[0].url == "https://example.com/research/market-overview"
    assert context.error is None


@pytest.mark.asyncio
async def test_research_tool_brave_mode_requires_api_key() -> None:
    tool = ArticleResearchTool(Settings(research_mode="brave", search_api_key=""))

    context = await tool.research(_request())

    assert context.provider == "brave"
    assert context.results == []
    assert context.error == "SEARCH_API_KEY is not configured."


@pytest.mark.asyncio
async def test_research_tool_duckduckgo_mode_parses_html_results(monkeypatch) -> None:
    html = """
    <html>
      <body>
        <div class="result">
          <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fguide">AI SEO guide</a>
          <a class="result__snippet">Practical guide for AI SEO workflows.</a>
        </div>
      </body>
    </html>
    """

    class FakeResponse:
        text = html

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            self.request_args = args
            self.request_kwargs = kwargs

        async def __aenter__(self):  # noqa: ANN204
            return self

        async def __aexit__(self, *args) -> None:  # noqa: ANN002
            return None

        async def get(self, *args, **kwargs) -> FakeResponse:  # noqa: ANN002, ANN003
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    tool = ArticleResearchTool(Settings(research_mode="duckduckgo"))

    context = await tool.research(_request())

    assert context.provider == "duckduckgo"
    assert context.error is None
    assert len(context.results) == 1
    assert context.results[0].title == "AI SEO guide"
    assert context.results[0].url == "https://example.com/guide"
    assert context.results[0].snippet == "Practical guide for AI SEO workflows."
