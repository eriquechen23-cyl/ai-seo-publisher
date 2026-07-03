import pytest

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
