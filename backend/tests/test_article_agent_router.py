from app.schemas.article import GenerateArticleRequest
from app.services.article_agent_router import ArticleAgentRouter


def _request(
    *,
    topic: str = "AI SEO content strategy",
    keywords: list[str] | None = None,
    target_audience: str = "marketing teams",
    call_to_action: str = "Book a workflow review.",
) -> GenerateArticleRequest:
    return GenerateArticleRequest(
        topic=topic,
        keywords=keywords or ["SEO", "AI content"],
        target_audience=target_audience,
        call_to_action=call_to_action,
    )


def test_router_always_uses_research_tool() -> None:
    router = ArticleAgentRouter(mode="always")

    decision = router.route(_request(topic="內部品牌語氣指南"))

    assert decision.use_research_tool is True
    assert decision.matched_rules == ["mode:always"]


def test_router_never_skips_research_tool() -> None:
    router = ArticleAgentRouter(mode="never")

    decision = router.route(_request(topic="2026 最新 AI SEO 趨勢"))

    assert decision.use_research_tool is False
    assert decision.matched_rules == ["mode:never"]


def test_router_auto_uses_research_for_timely_or_research_sensitive_brief() -> None:
    router = ArticleAgentRouter(mode="auto")

    decision = router.route(
        _request(
            topic="2026 最新 AI SEO 趨勢比較",
            keywords=["SEO", "AI 內容", "搜尋排名"],
        )
    )

    assert decision.use_research_tool is True
    assert "content:timely_or_comparative" in decision.matched_rules
    assert "content:research_sensitive" in decision.matched_rules
    assert "keywords:multi_keyword_seo" in decision.matched_rules


def test_router_auto_skips_internal_brand_brief() -> None:
    router = ArticleAgentRouter(mode="auto")

    decision = router.route(
        _request(
            topic="內部品牌語氣指南",
            keywords=["品牌語氣", "內容規範"],
            target_audience="內部內容團隊",
        )
    )

    assert decision.use_research_tool is False
    assert decision.matched_rules == ["content:internal_or_brand_specific"]
